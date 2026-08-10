"""Bounded cross-platform child-process ownership for live evaluations."""

from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO


DEFAULT_OUTPUT_LIMIT = 1024 * 1024


@dataclass(frozen=True)
class OwnedProcessResult:
    returncode: int | None
    stdout: str
    stderr: str
    elapsed_seconds: float
    error: str | None


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
        self._kernel32.TerminateJobObject(self.handle, 1)
        return True

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


def run_owned_process(
    command: list[str],
    input_text: str,
    *,
    cwd: Path,
    timeout: float,
    output_limit: int = DEFAULT_OUTPUT_LIMIT,
) -> OwnedProcessResult:
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    if output_limit < 1:
        raise ValueError("output_limit must be positive")
    started = time.monotonic()
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
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
        return OwnedProcessResult(None, "", "", time.monotonic() - started, str(exc))
    job = _WindowsJob(process)
    stdout_capture = _BoundedCapture(output_limit)
    stderr_capture = _BoundedCapture(output_limit)
    stdout_thread = threading.Thread(target=stdout_capture.drain, args=(process.stdout,), daemon=True)
    stderr_thread = threading.Thread(target=stderr_capture.drain, args=(process.stderr,), daemon=True)
    stdout_thread.start()
    stderr_thread.start()
    timed_out = False
    input_errors: list[str] = []

    def write_input() -> None:
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

    input_thread = threading.Thread(target=write_input, daemon=True)
    input_thread.start()
    try:
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            _terminate_owned_tree(process, job, force=False)
            try:
                process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                _terminate_owned_tree(process, job, force=True)
                process.wait(timeout=1)
            finally:
                if os.name != "nt":
                    time.sleep(0.05)
                    _terminate_owned_tree(process, job, force=True)
        else:
            # The direct child may exit after detaching descendants; the owner closes the whole tree.
            _terminate_owned_tree(process, job, force=False)
            if os.name != "nt":
                time.sleep(0.05)
                _terminate_owned_tree(process, job, force=True)
    finally:
        job.close()
        input_thread.join(timeout=1)
        if process.stdin is not None and not process.stdin.closed:
            process.stdin.close()
        stdout_thread.join(timeout=1)
        stderr_thread.join(timeout=1)
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()
        if process.poll() is None:
            process.kill()
            process.wait(timeout=1)
    stdout = stdout_capture.text()
    stderr = stderr_capture.text()
    error: str | None = None
    if timed_out:
        error = f"program timed out after {timeout:g} seconds"
    elif input_errors:
        error = input_errors[0]
    elif stdout_capture.exceeded or stderr_capture.exceeded:
        error = f"program output exceeded {output_limit} bytes per stream"
    return OwnedProcessResult(process.returncode, stdout, stderr, time.monotonic() - started, error)
