"""Bounded cross-platform child-process ownership for live evaluations.

POSIX ``SIGTERM``/``SIGINT`` and Python-delivered Windows console signals are
coordinated while at least one owner call runs on the main thread; Python does
not permit worker-only code to install or restore process signal handlers.
Windows service-stop callbacks must enter normal Python cancellation/exception
cleanup; a forced ``TerminateProcess`` cannot run Python handlers. POSIX
``SIGKILL`` is likewise uncatchable, so neither forced termination mechanism can
promise active cleanup. Evaluator commands run with the caller's OS authority,
not in a security sandbox. POSIX teardown owns the inherited process group and
also snapshots live descendants that changed groups or sessions before bounded
termination; an untrusted instant double-fork remains outside that contract.
"""

from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from types import FrameType
from typing import BinaryIO


DEFAULT_OUTPUT_LIMIT = 1024 * 1024
_GRACEFUL_JOIN_SECONDS = 0.5
_FORCED_JOIN_SECONDS = 1.0


@dataclass(frozen=True)
class OwnedProcessResult:
    returncode: int | None
    stdout: str
    stderr: str
    elapsed_seconds: float
    error: str | None
    error_kind: str | None


class _BoundedCapture:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.data = bytearray()
        self.exceeded = False

    def drain(self, stream: BinaryIO) -> None:
        while chunk := stream.read(65536):
            remaining = self.limit - len(self.data)
            if remaining > 0:
                self.data.extend(chunk[:remaining])
            if len(chunk) > remaining:
                self.exceeded = True

    def text(self) -> str:
        return bytes(self.data).decode("utf-8", errors="replace")


class _WindowsJob:
    """Best-effort Job Object ownership with taskkill fallback handled by the caller."""

    def __init__(self, process: subprocess.Popen[bytes]) -> None:
        self.handle = None
        if os.name != "nt":
            return
        import ctypes
        from ctypes import wintypes

        class IoCounters(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_ulonglong),
                ("WriteOperationCount", ctypes.c_ulonglong),
                ("OtherOperationCount", ctypes.c_ulonglong),
                ("ReadTransferCount", ctypes.c_ulonglong),
                ("WriteTransferCount", ctypes.c_ulonglong),
                ("OtherTransferCount", ctypes.c_ulonglong),
            ]

        class BasicLimitInformation(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_longlong),
                ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class ExtendedLimitInformation(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", BasicLimitInformation),
                ("IoInfo", IoCounters),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        kernel32.SetInformationJobObject.restype = wintypes.BOOL
        kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        kernel32.TerminateJobObject.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        handle = kernel32.CreateJobObjectW(None, None)
        if not handle:
            return
        info = ExtendedLimitInformation()
        info.BasicLimitInformation.LimitFlags = 0x00002000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel32.SetInformationJobObject(handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
            kernel32.CloseHandle(handle)
            return
        if not kernel32.AssignProcessToJobObject(handle, wintypes.HANDLE(process._handle)):
            kernel32.CloseHandle(handle)
            return
        self.handle = handle
        self._kernel32 = kernel32

    def terminate(self) -> bool:
        if self.handle is None:
            return False
        return bool(self._kernel32.TerminateJobObject(self.handle, 1))

    def close(self) -> None:
        if self.handle is not None:
            self._kernel32.CloseHandle(self.handle)
            self.handle = None


def _terminate_windows_fallback(process: subprocess.Popen[bytes]) -> None:
    try:
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        process.kill()


def _terminate_owned_tree(process: subprocess.Popen[bytes], job: _WindowsJob, *, force: bool) -> None:
    if os.name == "nt":
        if not job.terminate():
            _terminate_windows_fallback(process)
        return
    selected_signal = signal.SIGKILL if force else signal.SIGTERM
    try:
        os.killpg(process.pid, selected_signal)
    except ProcessLookupError:
        pass


def _posix_detached_descendants(root_pid: int) -> set[int]:
    """Snapshot descendants that no longer share the owner's process group."""
    if os.name == "nt":
        return set()
    try:
        completed = subprocess.run(
            ["ps", "-axo", "pid=,ppid="],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return set()
    children: dict[int, list[int]] = {}
    for line in completed.stdout.splitlines():
        fields = line.split()
        if len(fields) != 2:
            continue
        try:
            pid, parent = (int(field) for field in fields)
        except ValueError:
            continue
        children.setdefault(parent, []).append(pid)
    descendants: set[int] = set()
    pending = list(children.get(root_pid, ()))
    while pending:
        pid = pending.pop()
        if pid in descendants or pid <= 1:
            continue
        descendants.add(pid)
        pending.extend(children.get(pid, ()))
    detached: set[int] = set()
    for pid in descendants:
        try:
            if os.getpgid(pid) != root_pid:
                detached.add(pid)
        except ProcessLookupError:
            pass
    return detached


def _signal_posix_pids(pids: set[int], selected_signal: int) -> None:
    for pid in sorted(pids, reverse=True):
        try:
            os.kill(pid, selected_signal)
        except ProcessLookupError:
            pass


@dataclass(frozen=True)
class _ActiveOwnedProcess:
    process: subprocess.Popen[bytes]
    job: _WindowsJob


class _OwnedProcessSignal(BaseException):
    def __init__(self, signum: int, frame: FrameType | None, previous_handler: object) -> None:
        super().__init__(signum)
        self.signum = signum
        self.frame = frame
        self.previous_handler = previous_handler


_signal_state_lock = threading.RLock()
_active_owned_processes: dict[int, _ActiveOwnedProcess] = {}
_previous_signal_handlers: dict[int, object] = {}
_main_signal_scopes = 0
_main_cancellable_scopes = 0
_spawning_processes = 0
_pending_signal: tuple[int, FrameType | None] | None = None
_signal_dispatch_in_progress = False


def _owned_process_signals() -> tuple[int, ...]:
    selected = [signal.SIGTERM, signal.SIGINT]
    if os.name == "nt" and hasattr(signal, "SIGBREAK"):
        selected.append(signal.SIGBREAK)
    return tuple(dict.fromkeys(int(item) for item in selected))


def _restore_signal_handlers_locked() -> None:
    for signum, previous_handler in tuple(_previous_signal_handlers.items()):
        if signal.getsignal(signum) is _handle_owned_process_signal:
            signal.signal(signum, previous_handler)
        del _previous_signal_handlers[signum]


def _enter_signal_scope() -> bool:
    global _main_signal_scopes
    is_main_thread = threading.current_thread() is threading.main_thread()
    with _signal_state_lock:
        if is_main_thread:
            _main_signal_scopes += 1
            for signum in _owned_process_signals():
                current_handler = signal.getsignal(signum)
                if current_handler is _handle_owned_process_signal:
                    continue
                if signum in _previous_signal_handlers:
                    # The caller deliberately replaced a handler while work was active.
                    continue
                _previous_signal_handlers[signum] = current_handler
                signal.signal(signum, _handle_owned_process_signal)
    return is_main_thread


def _leave_signal_scope(*, is_main_thread: bool) -> None:
    global _main_signal_scopes
    with _signal_state_lock:
        if is_main_thread:
            _main_signal_scopes -= 1
            if _main_signal_scopes == 0:
                _restore_signal_handlers_locked()


def _set_main_cancellable(enabled: bool) -> None:
    global _main_cancellable_scopes
    with _signal_state_lock:
        _main_cancellable_scopes += 1 if enabled else -1


def _begin_process_spawn() -> None:
    global _spawning_processes
    with _signal_state_lock:
        _spawning_processes += 1


def _finish_process_spawn(
    process: subprocess.Popen[bytes] | None,
    job: _WindowsJob | None,
) -> tuple[int, FrameType | None] | None:
    global _pending_signal, _spawning_processes
    with _signal_state_lock:
        if process is not None and job is not None:
            _active_owned_processes[id(process)] = _ActiveOwnedProcess(process, job)
        _spawning_processes -= 1
        if _spawning_processes != 0:
            return None
        pending = _pending_signal
        _pending_signal = None
        return pending


def _unregister_owned_process(process: subprocess.Popen[bytes]) -> None:
    with _signal_state_lock:
        _active_owned_processes.pop(id(process), None)


def _wait_for_owned_processes(records: list[_ActiveOwnedProcess], timeout: float) -> None:
    deadline = time.monotonic() + timeout
    for record in records:
        if record.process.returncode is not None:
            continue
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        try:
            record.process.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            pass


def _terminate_and_join_owned_processes(records: list[_ActiveOwnedProcess]) -> None:
    detached = {
        id(record.process): _posix_detached_descendants(record.process.pid)
        for record in records
    }
    # Signal every tree before waiting so concurrent evaluators share one bound.
    for record in records:
        _terminate_owned_tree(record.process, record.job, force=False)
        if os.name != "nt":
            _signal_posix_pids(detached[id(record.process)], signal.SIGTERM)
    _wait_for_owned_processes(records, _GRACEFUL_JOIN_SECONDS)
    for record in records:
        detached[id(record.process)].update(
            _posix_detached_descendants(record.process.pid)
        )
        _terminate_owned_tree(record.process, record.job, force=True)
        if os.name != "nt":
            _signal_posix_pids(detached[id(record.process)], signal.SIGKILL)
    _wait_for_owned_processes(records, _FORCED_JOIN_SECONDS)
    if os.name != "nt":
        # A direct child can exit just before creating a final descendant. The
        # process group remains addressable after its leader has been reaped.
        time.sleep(0.05)
        for record in records:
            _terminate_owned_tree(record.process, record.job, force=True)


def _terminate_all_active_owned_processes() -> None:
    with _signal_state_lock:
        records = list(_active_owned_processes.values())
    _terminate_and_join_owned_processes(records)


def _dispatch_previous_signal(
    signum: int,
    frame: FrameType | None,
    previous_handler: object,
) -> None:
    if previous_handler == signal.SIG_IGN:
        return
    if previous_handler == signal.SIG_DFL:
        with _signal_state_lock:
            if signal.getsignal(signum) is _handle_owned_process_signal:
                signal.signal(signum, signal.SIG_DFL)
            _previous_signal_handlers.pop(signum, None)
        if os.name == "nt":
            signal.raise_signal(signum)
        else:
            os.kill(os.getpid(), signum)
        raise SystemExit(128 + signum)
    if callable(previous_handler):
        previous_handler(signum, frame)


def _complete_signal_dispatch() -> None:
    global _signal_dispatch_in_progress
    with _signal_state_lock:
        _signal_dispatch_in_progress = False


def _handle_owned_process_signal(signum: int, frame: FrameType | None) -> None:
    global _pending_signal, _signal_dispatch_in_progress
    with _signal_state_lock:
        if _signal_dispatch_in_progress:
            return
        if _spawning_processes:
            if _pending_signal is None:
                _pending_signal = (signum, frame)
            return
        previous_handler = _previous_signal_handlers.get(signum, signal.SIG_DFL)
        _signal_dispatch_in_progress = True
        interrupt_main_call = _main_cancellable_scopes > 0
    if interrupt_main_call:
        # Raising first unwinds Popen.wait's non-reentrant waitpid lock. The
        # run_owned_process boundary then terminates and joins every registered
        # tree before forwarding the caller's original signal semantics.
        raise _OwnedProcessSignal(signum, frame, previous_handler)
    try:
        _terminate_all_active_owned_processes()
        _dispatch_previous_signal(signum, frame, previous_handler)
    finally:
        _complete_signal_dispatch()


def _replay_pending_signal(pending: tuple[int, FrameType | None]) -> None:
    signum, frame = pending
    if threading.current_thread() is threading.main_thread():
        _handle_owned_process_signal(signum, frame)
    elif os.name == "posix":
        os.kill(os.getpid(), signum)
    else:
        signal.raise_signal(signum)


def run_owned_process(
    command: list[str],
    input_text: str,
    *,
    cwd: Path,
    timeout: float,
    output_limit: int = DEFAULT_OUTPUT_LIMIT,
    forward_signals: bool = True,
) -> OwnedProcessResult:
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    if output_limit < 1:
        raise ValueError("output_limit must be positive")
    started = time.monotonic()
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    process: subprocess.Popen[bytes] | None = None
    job: _WindowsJob | None = None
    spawn_error: OSError | None = None
    stdout_capture = _BoundedCapture(output_limit)
    stderr_capture = _BoundedCapture(output_limit)
    stdout_thread: threading.Thread | None = None
    stderr_thread: threading.Thread | None = None
    input_thread: threading.Thread | None = None
    timed_out = False
    cancelled_signal: int | None = None
    interrupted_signal: _OwnedProcessSignal | None = None
    input_errors: list[str] = []
    is_main_thread = _enter_signal_scope()

    def write_input() -> None:
        assert process is not None
        assert process.stdin is not None
        try:
            process.stdin.write(input_text.encode("utf-8"))
        except (BrokenPipeError, OSError) as exc:
            input_errors.append(f"cannot write program input: {exc}")
        finally:
            try:
                process.stdin.close()
            except OSError as exc:
                input_errors.append(f"cannot close program input: {exc}")

    try:
        try:
            if is_main_thread:
                _set_main_cancellable(True)
            pending_signal: tuple[int, FrameType | None] | None
            _begin_process_spawn()
            try:
                try:
                    process = subprocess.Popen(
                        command,
                        cwd=cwd,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        start_new_session=os.name != "nt",
                        creationflags=creationflags,
                    )
                except OSError as exc:
                    spawn_error = exc
                else:
                    job = _WindowsJob(process)
            finally:
                pending_signal = _finish_process_spawn(process, job)
                if pending_signal is not None:
                    _replay_pending_signal(pending_signal)

            if process is not None and job is not None:
                assert process.stdout is not None
                assert process.stderr is not None
                stdout_thread = threading.Thread(target=stdout_capture.drain, args=(process.stdout,), daemon=True)
                stderr_thread = threading.Thread(target=stderr_capture.drain, args=(process.stderr,), daemon=True)
                stdout_thread.start()
                stderr_thread.start()
                input_thread = threading.Thread(target=write_input, daemon=True)
                input_thread.start()
                active_record = _ActiveOwnedProcess(process, job)
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    if os.name == "nt":
                        # Walk the PID tree while the parent still exists; a fast child can
                        # otherwise spawn before the parent is assigned to the Job Object.
                        _terminate_windows_fallback(process)
                    _terminate_and_join_owned_processes([active_record])
                except _OwnedProcessSignal:
                    raise
                except BaseException:
                    _terminate_and_join_owned_processes([active_record])
                    raise
                else:
                    # The direct child may exit after detaching descendants; the owner closes the whole tree.
                    _terminate_and_join_owned_processes([active_record])
        except _OwnedProcessSignal as exc:
            interrupted_signal = exc
            cancelled_signal = exc.signum
            _terminate_all_active_owned_processes()
            if forward_signals:
                _dispatch_previous_signal(exc.signum, exc.frame, exc.previous_handler)
        finally:
            if is_main_thread:
                _set_main_cancellable(False)
    finally:
        try:
            if process is not None:
                if process.poll() is None and job is not None:
                    _terminate_and_join_owned_processes([_ActiveOwnedProcess(process, job)])
                if input_thread is not None and input_thread.ident is not None:
                    input_thread.join(timeout=1)
                if process.stdin is not None and not process.stdin.closed:
                    process.stdin.close()
                if stdout_thread is not None and stdout_thread.ident is not None:
                    stdout_thread.join(timeout=1)
                if stderr_thread is not None and stderr_thread.ident is not None:
                    stderr_thread.join(timeout=1)
                if process.stdout is not None:
                    process.stdout.close()
                if process.stderr is not None:
                    process.stderr.close()
                _unregister_owned_process(process)
            if job is not None:
                job.close()
        finally:
            _leave_signal_scope(is_main_thread=is_main_thread)
            if interrupted_signal is not None:
                _complete_signal_dispatch()
    if process is None:
        if cancelled_signal is not None:
            signal_name = signal.Signals(cancelled_signal).name
            return OwnedProcessResult(
                None,
                "",
                "",
                time.monotonic() - started,
                f"program cancelled by {signal_name}",
                "cancelled",
            )
        assert spawn_error is not None
        return OwnedProcessResult(None, "", "", time.monotonic() - started, str(spawn_error), "spawn")
    stdout = stdout_capture.text()
    stderr = stderr_capture.text()
    error: str | None = None
    error_kind: str | None = None
    if cancelled_signal is not None:
        signal_name = signal.Signals(cancelled_signal).name
        error = f"program cancelled by {signal_name}"
        error_kind = "cancelled"
    elif timed_out:
        error = f"program timed out after {timeout:g} seconds"
        error_kind = "timeout"
    elif input_errors:
        error = input_errors[0]
        error_kind = "input"
    elif stdout_capture.exceeded or stderr_capture.exceeded:
        error = f"program output exceeded {output_limit} bytes per stream"
        error_kind = "output-limit"
    return OwnedProcessResult(
        process.returncode,
        stdout,
        stderr,
        time.monotonic() - started,
        error,
        error_kind,
    )
