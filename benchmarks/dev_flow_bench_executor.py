#!/usr/bin/env python3
"""Bounded model executor owned by Dev Flow Bench.

The executor runs selected synthetic cases and preserves bounded first-attempt
evidence. It has no command-line surface, release policy, campaign ledger, or
grading authority; ``dev_flow_bench.py`` owns admission, identity, budget, output,
and assessment binding.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
from typing import Any

BENCHMARKS = Path(__file__).resolve().parent
ROOT = BENCHMARKS.parent
sys.path.insert(0, str(BENCHMARKS))

import dev_flow_bench_fixture_mcp  # noqa: E402

from dev_flow_bench_contracts import (  # noqa: E402
    BENCHMARK_FIXTURE_MAX_FILES,
    BENCHMARK_FIXTURE_MAX_TOTAL_BYTES,
    BENCHMARK_REPOSITORY_MAX_FILE_BYTES,
    BENCHMARK_REPOSITORY_MAX_FILES,
    BENCHMARK_REPOSITORY_MAX_TOTAL_BYTES,
    BenchContractError,
    benchmark_fixture_evidence_bytes,
    benchmark_fixture_path_is_safe,
    validate_benchmark_repository_fixture,
)

try:
    import resource
except ImportError:  # pragma: no cover - Windows compatibility
    resource = None


TOKEN_USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)
SAFETY_PREFIX = (
    "This is a bounded isolated evaluation fixture. Work only inside the current "
    "Git repository; do not use network or external services, commit, push, publish, "
    "or perform delivery actions. Follow this task exactly:\n\n"
)
SHELL_ENVIRONMENT_POLICY = 'shell_environment_policy.inherit="none"'
CLIENT_ENVIRONMENT_ALLOWLIST = {
    "PATH",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_ORGANIZATION",
    "OPENAI_PROJECT",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "REQUESTS_CA_BUNDLE",
    "CURL_CA_BUNDLE",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TERM",
}
MAX_TRAJECTORY_ENTRIES = 128
MAX_REPOSITORY_FILE_BYTES = BENCHMARK_REPOSITORY_MAX_FILE_BYTES
MAX_REPOSITORY_DELTA_BYTES = BENCHMARK_FIXTURE_MAX_TOTAL_BYTES
MAX_REPOSITORY_TOTAL_BYTES = BENCHMARK_REPOSITORY_MAX_TOTAL_BYTES
MAX_REPOSITORY_FILES = BENCHMARK_REPOSITORY_MAX_FILES
MAX_CANDIDATE_FILE_BYTES = 16 * 1024 * 1024
MAX_CANDIDATE_TOTAL_BYTES = 64 * 1024 * 1024
MAX_CANDIDATE_FILES = 4096
MAX_AUTH_FILE_BYTES = 1024 * 1024
MAX_CHILD_FILE_BYTES = 16 * 1024 * 1024
MAX_CAPTURE_BYTES = 1024 * 1024
MAX_RESPONSE_BYTES = 256 * 1024
MAX_ROLLOUT_FILES = 512
MAX_ROLLOUT_LINES = 16_384
PROHIBITED_TRAJECTORY_MARKERS = (
    "browser",
    "web_search",
    "computer",
    "image_generation",
    "app_call",
    "dynamic_tool",
)
TRUSTED_SHELL_WRAPPERS = {
    "/bin/sh",
    "/bin/bash",
    "/bin/zsh",
    "/usr/bin/sh",
    "/usr/bin/bash",
    "/usr/bin/zsh",
}


class TrialError(RuntimeError):
    """Raised for a non-retryable trial setup or execution failure."""


class _JobObjectBasicLimitInformation(ctypes.Structure):
    _fields_ = (
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    )


class _IoCounters(ctypes.Structure):
    _fields_ = tuple(
        (name, ctypes.c_ulonglong)
        for name in (
            "ReadOperationCount",
            "WriteOperationCount",
            "OtherOperationCount",
            "ReadTransferCount",
            "WriteTransferCount",
            "OtherTransferCount",
        )
    )


class _JobObjectExtendedLimitInformation(ctypes.Structure):
    _fields_ = (
        ("BasicLimitInformation", _JobObjectBasicLimitInformation),
        ("IoInfo", _IoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    )


class _StartupInfoW(ctypes.Structure):
    _fields_ = (
        ("cb", wintypes.DWORD),
        ("lpReserved", wintypes.LPWSTR),
        ("lpDesktop", wintypes.LPWSTR),
        ("lpTitle", wintypes.LPWSTR),
        ("dwX", wintypes.DWORD),
        ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD),
        ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD),
        ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD),
        ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.POINTER(wintypes.BYTE)),
        ("hStdInput", wintypes.HANDLE),
        ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE),
    )


class _StartupInfoExW(ctypes.Structure):
    _fields_ = (
        ("StartupInfo", _StartupInfoW),
        ("lpAttributeList", ctypes.c_void_p),
    )


class _ProcessInformation(ctypes.Structure):
    _fields_ = (
        ("hProcess", wintypes.HANDLE),
        ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD),
        ("dwThreadId", wintypes.DWORD),
    )


class _WindowsProcessJob:
    """Own one Windows process lineage through kill-on-close Job Object semantics."""

    JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000

    def __init__(self) -> None:
        if os.name != "nt":
            raise TrialError("Windows process jobs are unavailable on this platform")
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        kernel32.SetInformationJobObject.argtypes = (
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        )
        kernel32.SetInformationJobObject.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel32.CloseHandle.restype = wintypes.BOOL
        handle = kernel32.CreateJobObjectW(None, None)
        if not handle:
            raise TrialError(
                f"cannot create Windows process job: {ctypes.get_last_error()}"
            )
        limits = _JobObjectExtendedLimitInformation()
        limits.BasicLimitInformation.LimitFlags = self.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel32.SetInformationJobObject(
            handle,
            self.JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(limits),
            ctypes.sizeof(limits),
        ):
            error = ctypes.get_last_error()
            kernel32.CloseHandle(handle)
            raise TrialError(f"cannot configure Windows process job: {error}")
        self.kernel32 = kernel32
        self.handle: int | None = handle

    def close(self) -> None:
        if self.handle is not None:
            self.kernel32.CloseHandle(self.handle)
            self.handle = None


class _WindowsJobProcess:
    """Minimal Popen-compatible process created inside a Job Object atomically."""

    EXTENDED_STARTUPINFO_PRESENT = 0x00080000
    CREATE_UNICODE_ENVIRONMENT = 0x00000400
    CREATE_NEW_PROCESS_GROUP = 0x00000200
    STARTF_USESTDHANDLES = 0x00000100
    PROC_THREAD_ATTRIBUTE_HANDLE_LIST = 0x00020002
    PROC_THREAD_ATTRIBUTE_JOB_LIST = 0x0002000D
    WAIT_OBJECT_0 = 0
    WAIT_TIMEOUT = 258
    INFINITE = 0xFFFFFFFF

    def __init__(
        self,
        command: list[str],
        kernel32: Any,
        process_handle: int,
        pid: int,
    ) -> None:
        self.args = command
        self.kernel32 = kernel32
        self._handle: int | None = process_handle
        self.pid = pid
        self.returncode: int | None = None

    @classmethod
    def launch(
        cls,
        command: list[str],
        windows_job: _WindowsProcessJob,
        *,
        input_text: str | None,
        **kwargs: Any,
    ) -> "_WindowsJobProcess":
        if os.name != "nt" or windows_job.handle is None:
            raise TrialError("Windows creation-time process containment is unavailable")
        import msvcrt

        stdout = kwargs.pop("stdout", None)
        stderr = kwargs.pop("stderr", None)
        text_mode = kwargs.pop("text", False)
        environment = kwargs.pop("env", None)
        cwd = kwargs.pop("cwd", None)
        if kwargs:
            raise TrialError(
                f"unsupported Windows bounded-process options: {sorted(kwargs)}"
            )
        if stdout is None or stderr is None:
            raise TrialError("Windows bounded processes require explicit output captures")
        if not text_mode:
            raise TrialError("Windows bounded processes require UTF-8 text mode")

        if input_text is None:
            stdin = open(os.devnull, "rb")
        else:
            stdin = tempfile.TemporaryFile(mode="w+b")
            stdin.write(input_text.encode("utf-8"))
            stdin.seek(0)
        try:
            handles = [
                int(msvcrt.get_osfhandle(stream.fileno()))
                for stream in (stdin, stdout, stderr)
            ]
            previous_inheritance = [
                os.get_handle_inheritable(handle) for handle in handles
            ]
            for handle in handles:
                os.set_handle_inheritable(handle, True)
            kernel32 = windows_job.kernel32
            kernel32.InitializeProcThreadAttributeList.argtypes = (
                ctypes.c_void_p,
                wintypes.DWORD,
                wintypes.DWORD,
                ctypes.POINTER(ctypes.c_size_t),
            )
            kernel32.InitializeProcThreadAttributeList.restype = wintypes.BOOL
            kernel32.UpdateProcThreadAttribute.argtypes = (
                ctypes.c_void_p,
                wintypes.DWORD,
                ctypes.c_size_t,
                ctypes.c_void_p,
                ctypes.c_size_t,
                ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_size_t),
            )
            kernel32.UpdateProcThreadAttribute.restype = wintypes.BOOL
            kernel32.DeleteProcThreadAttributeList.argtypes = (ctypes.c_void_p,)
            kernel32.DeleteProcThreadAttributeList.restype = None
            kernel32.CreateProcessW.argtypes = (
                wintypes.LPCWSTR,
                wintypes.LPWSTR,
                ctypes.c_void_p,
                ctypes.c_void_p,
                wintypes.BOOL,
                wintypes.DWORD,
                ctypes.c_void_p,
                wintypes.LPCWSTR,
                ctypes.c_void_p,
                ctypes.POINTER(_ProcessInformation),
            )
            kernel32.CreateProcessW.restype = wintypes.BOOL
            kernel32.WaitForSingleObject.argtypes = (
                wintypes.HANDLE,
                wintypes.DWORD,
            )
            kernel32.WaitForSingleObject.restype = wintypes.DWORD
            kernel32.GetExitCodeProcess.argtypes = (
                wintypes.HANDLE,
                ctypes.POINTER(wintypes.DWORD),
            )
            kernel32.GetExitCodeProcess.restype = wintypes.BOOL

            attribute_size = ctypes.c_size_t()
            kernel32.InitializeProcThreadAttributeList(
                None, 2, 0, ctypes.byref(attribute_size)
            )
            attribute_buffer = ctypes.create_string_buffer(attribute_size.value)
            attribute_list = ctypes.cast(attribute_buffer, ctypes.c_void_p)
            if not kernel32.InitializeProcThreadAttributeList(
                attribute_list, 2, 0, ctypes.byref(attribute_size)
            ):
                raise TrialError(
                    "cannot initialize Windows process attributes: "
                    f"{ctypes.get_last_error()}"
                )
            try:
                inherited_handles = (wintypes.HANDLE * len(handles))(*handles)
                job_handles = (wintypes.HANDLE * 1)(windows_job.handle)
                if not kernel32.UpdateProcThreadAttribute(
                    attribute_list,
                    0,
                    cls.PROC_THREAD_ATTRIBUTE_HANDLE_LIST,
                    ctypes.cast(inherited_handles, ctypes.c_void_p),
                    ctypes.sizeof(inherited_handles),
                    None,
                    None,
                ):
                    raise TrialError(
                        "cannot restrict Windows inherited handles: "
                        f"{ctypes.get_last_error()}"
                    )
                if not kernel32.UpdateProcThreadAttribute(
                    attribute_list,
                    0,
                    cls.PROC_THREAD_ATTRIBUTE_JOB_LIST,
                    ctypes.cast(job_handles, ctypes.c_void_p),
                    ctypes.sizeof(job_handles),
                    None,
                    None,
                ):
                    raise TrialError(
                        "cannot bind Windows process at creation time: "
                        f"{ctypes.get_last_error()}"
                    )
                startup = _StartupInfoExW()
                startup.StartupInfo.cb = ctypes.sizeof(_StartupInfoExW)
                startup.StartupInfo.dwFlags = cls.STARTF_USESTDHANDLES
                startup.StartupInfo.hStdInput = wintypes.HANDLE(handles[0])
                startup.StartupInfo.hStdOutput = wintypes.HANDLE(handles[1])
                startup.StartupInfo.hStdError = wintypes.HANDLE(handles[2])
                startup.lpAttributeList = attribute_list
                process_information = _ProcessInformation()
                command_line = ctypes.create_unicode_buffer(
                    subprocess.list2cmdline(command)
                )
                environment_buffer = None
                if environment is not None:
                    environment_text = "\0".join(
                        f"{key}={value}"
                        for key, value in sorted(
                            environment.items(), key=lambda item: item[0].upper()
                        )
                    ) + "\0\0"
                    environment_buffer = ctypes.create_unicode_buffer(environment_text)
                flags = (
                    cls.EXTENDED_STARTUPINFO_PRESENT
                    | cls.CREATE_UNICODE_ENVIRONMENT
                    | cls.CREATE_NEW_PROCESS_GROUP
                )
                if not kernel32.CreateProcessW(
                    None,
                    command_line,
                    None,
                    None,
                    True,
                    flags,
                    ctypes.cast(environment_buffer, ctypes.c_void_p)
                    if environment_buffer is not None
                    else None,
                    os.fspath(cwd) if cwd is not None else None,
                    ctypes.byref(startup),
                    ctypes.byref(process_information),
                ):
                    raise TrialError(
                        "cannot create contained Windows process: "
                        f"{ctypes.get_last_error()}"
                    )
                kernel32.CloseHandle(process_information.hThread)
                return cls(
                    command,
                    kernel32,
                    process_information.hProcess,
                    process_information.dwProcessId,
                )
            finally:
                kernel32.DeleteProcThreadAttributeList(attribute_list)
        finally:
            for handle, inherited in zip(
                locals().get("handles", []),
                locals().get("previous_inheritance", []),
            ):
                os.set_handle_inheritable(handle, inherited)
            stdin.close()

    def _observe_exit(self) -> int:
        if self._handle is None:
            if self.returncode is None:
                raise TrialError("Windows process handle closed before exit")
            return self.returncode
        exit_code = wintypes.DWORD()
        if not self.kernel32.GetExitCodeProcess(
            self._handle, ctypes.byref(exit_code)
        ):
            raise TrialError(
                f"cannot read Windows process exit code: {ctypes.get_last_error()}"
            )
        self.returncode = ctypes.c_int32(exit_code.value).value
        return self.returncode

    def poll(self) -> int | None:
        if self.returncode is not None:
            return self.returncode
        if self._handle is None:
            return None
        result = self.kernel32.WaitForSingleObject(self._handle, 0)
        if result == self.WAIT_TIMEOUT:
            return None
        if result != self.WAIT_OBJECT_0:
            raise TrialError(
                f"cannot poll Windows process: {ctypes.get_last_error()}"
            )
        return self._observe_exit()

    def wait(self, timeout: float | None = None) -> int:
        if self.returncode is not None:
            return self.returncode
        if self._handle is None:
            raise TrialError("Windows process handle is unavailable")
        milliseconds = (
            self.INFINITE
            if timeout is None
            else min(self.INFINITE - 1, max(0, int(timeout * 1000)))
        )
        result = self.kernel32.WaitForSingleObject(self._handle, milliseconds)
        if result == self.WAIT_TIMEOUT:
            raise subprocess.TimeoutExpired(self.args, timeout)
        if result != self.WAIT_OBJECT_0:
            raise TrialError(
                f"cannot wait for Windows process: {ctypes.get_last_error()}"
            )
        return self._observe_exit()

    def communicate(
        self, input: str | None = None, timeout: float | None = None
    ) -> tuple[None, None]:
        if input is not None:
            raise TrialError("Windows process input must be staged before creation")
        self.wait(timeout)
        return None, None

    def close(self) -> None:
        if self._handle is not None:
            self.kernel32.CloseHandle(self._handle)
            self._handle = None


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def controlled_environment(**extra: str) -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if key in CLIENT_ENVIRONMENT_ALLOWLIST
    }
    environment.update(extra)
    return environment


def terminate_process_tree(
    process: Any, windows_job: _WindowsProcessJob | None = None
) -> None:
    if os.name == "posix":
        process_group = process.pid
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass
        finally:
            try:
                os.killpg(process_group, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if process.poll() is None:
            process.wait()
        return
    if windows_job is not None:  # pragma: no cover - hosted Windows compatibility
        windows_job.close()
        if process.poll() is None:
            process.wait(timeout=10)
        return
    if process.poll() is not None:  # pragma: no cover - fallback without a job
        return
    subprocess.run(  # pragma: no cover - exercised by hosted Windows compatibility
        ["taskkill", "/PID", str(process.pid), "/T", "/F"],
        check=False,
        capture_output=True,
        timeout=10,
    )
    process.wait()


def run_bounded_process(
    command: list[str], *, timeout: int, input_text: str | None = None, **kwargs: Any
) -> subprocess.CompletedProcess[str]:
    if kwargs.pop("capture_output", False):
        with (
            tempfile.TemporaryFile(mode="w+", encoding="utf-8") as stdout,
            tempfile.TemporaryFile(mode="w+", encoding="utf-8") as stderr,
        ):
            completed = run_bounded_process(
                command,
                timeout=timeout,
                input_text=input_text,
                stdout=stdout,
                stderr=stderr,
                **kwargs,
            )
            return subprocess.CompletedProcess(
                command,
                completed.returncode,
                read_bounded_capture(stdout, MAX_CAPTURE_BYTES, "child stdout"),
                read_bounded_capture(stderr, MAX_CAPTURE_BYTES, "child stderr"),
            )
    if os.name == "posix":
        kwargs["start_new_session"] = True
        if resource is not None:
            kwargs["preexec_fn"] = lambda: resource.setrlimit(
                resource.RLIMIT_FSIZE, (MAX_CHILD_FILE_BYTES, MAX_CHILD_FILE_BYTES)
            )
    windows_job = _WindowsProcessJob() if os.name == "nt" else None
    try:
        if windows_job is not None:  # pragma: no cover - hosted Windows compatibility
            process = _WindowsJobProcess.launch(
                command,
                windows_job,
                input_text=input_text,
                **kwargs,
            )
        else:
            process = subprocess.Popen(command, **kwargs)
    except BaseException:
        if windows_job is not None:
            windows_job.close()
        raise
    try:
        try:
            stdout, stderr = process.communicate(
                input=None if windows_job is not None else input_text,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            terminate_process_tree(process, windows_job)
            windows_job = None
            raise subprocess.TimeoutExpired(
                command, timeout, output=exc.output, stderr=exc.stderr
            ) from exc
        terminate_process_tree(process, windows_job)
        windows_job = None
        returncode = process.returncode
        if isinstance(process, _WindowsJobProcess):
            process.close()
        return subprocess.CompletedProcess(command, returncode, stdout, stderr)
    except subprocess.TimeoutExpired:
        raise
    except BaseException:
        terminate_process_tree(process, windows_job)
        windows_job = None
        raise
    finally:
        if windows_job is not None:
            windows_job.close()
        if isinstance(locals().get("process"), _WindowsJobProcess):
            process.close()


def read_bounded_capture(handle: Any, maximum: int, label: str) -> str:
    handle.flush()
    size = handle.seek(0, os.SEEK_END)
    if size > maximum:
        raise TrialError(f"{label} exceeded its bounded capture size")
    handle.seek(0)
    return handle.read()


def usage_breakdown(events: Path) -> dict[str, int]:
    observed: dict[str, int] = {}
    for line in events.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict) or not isinstance(event.get("usage"), dict):
            continue
        usage = event["usage"]
        current = {
            field: usage[field]
            for field in TOKEN_USAGE_FIELDS
            if isinstance(usage.get(field), int)
            and not isinstance(usage[field], bool)
            and usage[field] >= 0
        }
        if current:
            observed = current
    return observed


def total_tokens(usage: dict[str, int], label: str) -> int:
    value = usage.get("total_tokens")
    if value is None and "input_tokens" in usage and "output_tokens" in usage:
        value = usage["input_tokens"] + usage["output_tokens"]
    if not isinstance(value, int) or value < 0:
        raise TrialError(f"{label} did not expose valid token usage")
    return value


def checked_tokens(usage: dict[str, int], role: str, token_limit: int) -> int:
    tokens = total_tokens(usage, role)
    if tokens > token_limit:
        raise TrialError(f"{role} exceeded its per-call token limit")
    return tokens


def validate_lineage_transition(
    *, case_id: str, turn: int, lineage: str, previous: str | None, current: str
) -> None:
    if previous is None:
        return
    is_fork_turn = lineage == "fork" and turn == 2
    if is_fork_turn and current == previous:
        raise TrialError(f"{case_id} turn {turn}: fork reused the parent session id")
    if not is_fork_turn and current != previous:
        raise TrialError(f"{case_id} turn {turn}: resume changed the session id")


def bounded_file_bytes(path: Path, maximum: int, label: str) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    try:
        path_before = os.lstat(path)
        if not stat.S_ISREG(path_before.st_mode):
            raise TrialError(f"{label} must be a regular file")
        descriptor = os.open(path, flags)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise TrialError(f"{label} must be a regular file")
        path_after = os.lstat(path)
        if (
            not stat.S_ISREG(path_after.st_mode)
            or not hasattr(os.path, "samestat")
            or not os.path.samestat(metadata, path_after)
            or not os.path.samestat(path_before, path_after)
        ):
            raise TrialError(f"{label} path identity changed during open")
        if metadata.st_size > maximum:
            raise TrialError(f"{label} exceeded its bounded file size")
        handle = os.fdopen(descriptor, "rb")
        descriptor = None
        with handle:
            content = handle.read(maximum + 1)
    except OSError as exc:
        raise TrialError(f"{label} could not be read as a regular file") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    if len(content) > maximum:
        raise TrialError(f"{label} exceeded its bounded file size")
    return content


def is_transient_python_runtime_path(relative: str) -> bool:
    """Identify only interpreter/test cache artifacts, never source-like neighbors."""
    path = Path(relative)
    return ".pytest_cache" in path.parts or (
        "__pycache__" in path.parts and path.suffix == ".pyc"
    )


def repository_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    total_bytes = 0
    file_count = 0
    paths = sorted(item for item in root.rglob("*") if ".git" not in item.parts)
    for path in paths:
        if not path.is_file() and not path.is_symlink():
            continue
        file_count += 1
        if file_count > MAX_REPOSITORY_FILES:
            raise TrialError("repository digest exceeded the bounded fixture file count")
        relative_text = path.relative_to(root).as_posix()
        content = (
            ("symlink:" + os.readlink(path)).encode("utf-8")
            if path.is_symlink()
            else bounded_file_bytes(
                path, MAX_REPOSITORY_FILE_BYTES, "repository digest input"
            )
        )
        if len(content) > MAX_REPOSITORY_FILE_BYTES:
            raise TrialError("repository digest input exceeded its bounded file size")
        total_bytes += len(content)
        if total_bytes > MAX_REPOSITORY_TOTAL_BYTES:
            raise TrialError("repository digest exceeded the bounded fixture size")
        if is_transient_python_runtime_path(relative_text):
            continue
        relative = relative_text.encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return "sha256:" + digest.hexdigest()


def candidate_source_sha256(root: Path) -> str:
    listing = command_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        "candidate source files",
        root,
    )
    names = [name for name in listing.split("\0") if name]
    names = sorted(set(names))
    if len(names) > MAX_CANDIDATE_FILES:
        raise TrialError("candidate source exceeded the bounded file count")
    digest = hashlib.sha256()
    total_bytes = 0
    resolved_root = root.resolve()
    for name in names:
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise TrialError("candidate source path escaped the repository")
        path = root / relative
        if not path.parent.resolve().is_relative_to(resolved_root):
            raise TrialError("candidate source parent escaped the repository")
        if path.is_symlink():
            kind = b"symlink"
            content = os.readlink(path).encode("utf-8")
        elif path.is_file():
            kind = b"file"
            content = bounded_file_bytes(
                path, MAX_CANDIDATE_FILE_BYTES, "candidate source input"
            )
        elif not os.path.lexists(path):
            kind = b"missing"
            content = b""
        else:
            raise TrialError("candidate source contains an unsupported entry")
        if len(content) > MAX_CANDIDATE_FILE_BYTES:
            raise TrialError("candidate source input exceeded its bounded file size")
        total_bytes += len(content)
        if total_bytes > MAX_CANDIDATE_TOTAL_BYTES:
            raise TrialError("candidate source exceeded the bounded total size")
        encoded_name = relative.as_posix().encode("utf-8")
        for value in (encoded_name, kind, content):
            digest.update(len(value).to_bytes(8, "big"))
            digest.update(value)
    return "sha256:" + digest.hexdigest()


def write_fixture(repository: Path, files: dict[str, str]) -> None:
    try:
        validate_benchmark_repository_fixture(files)
    except BenchContractError as exc:
        raise TrialError("initial repository fixture is invalid") from exc
    repository.mkdir(parents=True)
    for relative, content in files.items():
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            raise TrialError(f"fixture path escapes repository: {relative!r}")
        target = repository / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    git_environment = controlled_environment(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_TERMINAL_PROMPT="0",
        GIT_AUTHOR_NAME="Dev Flow Trial",
        GIT_AUTHOR_EMAIL="dev-flow-trial@example.invalid",
        GIT_COMMITTER_NAME="Dev Flow Trial",
        GIT_COMMITTER_EMAIL="dev-flow-trial@example.invalid",
        GIT_AUTHOR_DATE="2000-01-01T00:00:00+00:00",
        GIT_COMMITTER_DATE="2000-01-01T00:00:00+00:00",
        TZ="UTC",
    )
    git_base = ["git", "-c", f"core.hooksPath={os.devnull}"]
    commands = (
        [*git_base, "-c", "init.defaultBranch=main", "init", "--quiet"],
        [*git_base, "add", "--all"],
        [
            *git_base,
            "commit",
            "--quiet",
            "--no-gpg-sign",
            "--no-verify",
            "-m",
            "fixture baseline",
        ],
    )
    for command in commands:
        try:
            completed = run_bounded_process(
                command,
                cwd=repository,
                capture_output=True,
                text=True,
                env=git_environment,
                timeout=30,
            )
        except subprocess.TimeoutExpired as exc:
            raise TrialError("fixture Git setup timed out") from exc
        if completed.returncode != 0:
            raise TrialError(
                f"fixture Git setup failed (exit {completed.returncode}; "
                f"stderr {sha256_text(completed.stderr)})"
            )


def install_candidate(codex: str, codex_home: Path, plugin_root: Path) -> None:
    source_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    source_auth = source_home / "auth.json"
    if not source_auth.is_file() or source_auth.is_symlink():
        raise TrialError("candidate execution requires a regular local Codex auth file")
    target_auth = codex_home / "auth.json"
    target_auth.write_bytes(
        bounded_file_bytes(source_auth, MAX_AUTH_FILE_BYTES, "Codex auth input")
    )
    target_auth.chmod(0o600)
    environment = controlled_environment(CODEX_HOME=str(codex_home))
    commands = (
        [codex, "plugin", "marketplace", "add", str(plugin_root), "--json"],
        [codex, "plugin", "add", "dev-flow@dev-flow", "--json"],
    )
    for command in commands:
        try:
            completed = run_bounded_process(
                command,
                capture_output=True,
                text=True,
                env=environment,
                timeout=120,
            )
        except subprocess.TimeoutExpired as exc:
            raise TrialError("candidate installation timed out") from exc
        if completed.returncode != 0:
            raise TrialError(
                f"candidate installation failed at {' '.join(command[1:3])} "
                f"(exit {completed.returncode})"
            )


def mcp_inventory(codex: str, codex_home: Path, repository: Path) -> list[dict[str, Any]]:
    """Return a bounded, payload-free view of the exact configured MCP surface."""
    environment = controlled_environment(CODEX_HOME=str(codex_home))
    try:
        completed = run_bounded_process(
            [codex, "mcp", "list", "--json"],
            cwd=repository,
            capture_output=True,
            text=True,
            env=environment,
            timeout=30,
        )
    except subprocess.TimeoutExpired as exc:
        raise TrialError("MCP environment admission timed out") from exc
    if completed.returncode != 0:
        raise TrialError(
            f"MCP environment admission failed (exit {completed.returncode}; "
            f"stderr {sha256_text(completed.stderr)})"
        )
    if len(completed.stdout.encode("utf-8")) > MAX_CAPTURE_BYTES:
        raise TrialError("MCP environment admission output exceeded its bound")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise TrialError("MCP environment admission returned invalid JSON") from exc
    if not isinstance(payload, list):
        raise TrialError("MCP environment admission returned an invalid server list")
    inventory: list[dict[str, Any]] = []
    seen: set[str] = set()
    for server in payload:
        if not isinstance(server, dict):
            raise TrialError("MCP environment admission returned an invalid server entry")
        name = bounded_event_identity(server.get("name"))
        enabled = server.get("enabled")
        transport = server.get("transport")
        transport_type = (
            bounded_event_identity(transport.get("type"))
            if isinstance(transport, dict)
            else "unavailable"
        )
        if name == "unavailable" or name in seen or not isinstance(enabled, bool):
            raise TrialError("MCP environment admission returned an ambiguous server entry")
        seen.add(name)
        inventory.append(
            {"name": name, "enabled": enabled, "transport": transport_type}
        )
    return sorted(inventory, key=lambda item: item["name"])


def configure_case_mcp(
    *,
    codex: str,
    codex_home: Path,
    repository: Path,
    fixture: dict[str, str] | None,
    fixture_script: Path,
) -> list[dict[str, Any]]:
    """Install a declared runner-owned MCP fixture and admit the exact surface."""
    if fixture is not None:
        if not fixture_script.is_file() or fixture_script.is_symlink():
            raise TrialError("runner-owned MCP fixture script is unavailable")
        environment = controlled_environment(CODEX_HOME=str(codex_home))
        command = [
            codex,
            "mcp",
            "add",
            fixture["server"],
            "--",
            sys.executable,
            str(fixture_script),
            "--tool",
            fixture["tool"],
        ]
        try:
            completed = run_bounded_process(
                command,
                cwd=repository,
                capture_output=True,
                text=True,
                env=environment,
                timeout=30,
            )
        except subprocess.TimeoutExpired as exc:
            raise TrialError("runner-owned MCP fixture configuration timed out") from exc
        if completed.returncode != 0:
            raise TrialError(
                f"runner-owned MCP fixture configuration failed (exit {completed.returncode}; "
                f"stderr {sha256_text(completed.stderr)})"
            )
    inventory = mcp_inventory(codex, codex_home, repository)
    expected = (
        [{"name": fixture["server"], "enabled": True, "transport": "stdio"}]
        if fixture is not None
        else []
    )
    if inventory != expected:
        raise TrialError(
            "MCP environment admission mismatch "
            f"(expected={expected}, observed={inventory})"
        )
    return inventory


def extract_session_id(events: Path) -> str:
    def find_id(value: Any) -> str | None:
        if isinstance(value, dict):
            for key in ("thread_id", "session_id", "threadId", "sessionId"):
                candidate = value.get(key)
                if isinstance(candidate, str) and candidate:
                    return candidate
            for child in value.values():
                found = find_id(child)
                if found:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = find_id(child)
                if found:
                    return found
        return None

    for line in events.read_text(encoding="utf-8").splitlines():
        try:
            found = find_id(json.loads(line))
        except json.JSONDecodeError:
            continue
        if found:
            return found
    raise TrialError("Codex JSONL did not expose a session/thread id")


def bounded_event_identity(value: Any) -> str:
    if (
        isinstance(value, str)
        and 0 < len(value) <= 128
        and all(character.isalnum() or character in "._:-/" for character in value)
    ):
        return value
    return "unavailable"


def mcp_error_category(item: dict[str, Any]) -> str | None:
    error = item.get("error")
    message = error.get("message") if isinstance(error, dict) else None
    lowered = message.lower() if isinstance(message, str) else ""
    if "not available" in lowered or "unavailable" in lowered or "not found" in lowered:
        return "unavailable"
    if "blocked" in lowered or "disabled" in lowered:
        return "blocked"
    if "cancel" in lowered or "approval" in lowered or "denied" in lowered:
        return "approval-denied"
    status = item.get("status")
    if status == "failed":
        return "execution-failed"
    return None


def validate_mcp_trajectory(
    entries: list[dict[str, Any]],
    *,
    allowed_mcp_tools: tuple[str, ...],
    inventory: tuple[dict[str, Any], ...],
) -> None:
    if not entries:
        return
    enabled_servers = {
        item["name"]
        for item in inventory
        if item.get("enabled") is True and isinstance(item.get("name"), str)
    }
    allowed = set(allowed_mcp_tools)
    started: dict[str, list[dict[str, Any]]] = {}
    completed: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        key = str(entry.get("call_identity_sha256") or entry.get("mcp_tool"))
        target = completed if entry.get("event_type") == "item.completed" else started
        target.setdefault(key, []).append(entry)
    incomplete = set(started) ^ set(completed)
    if incomplete:
        key = sorted(incomplete)[0]
        first = (started.get(key) or completed[key])[0]
        raise TrialError(
            "candidate MCP trajectory is incomplete "
            f"(server={first.get('mcp_server', 'unavailable')}, "
            f"tool={first.get('mcp_tool', 'unavailable')})"
        )
    for key in sorted(completed):
        final = completed[key][-1]
        server = str(final.get("mcp_server", "unavailable"))
        tool = str(final.get("mcp_tool", "unavailable"))
        qualified = f"{server}/{tool}"
        status = str(final.get("status", "unavailable"))
        category = str(final.get("error_category", "none"))
        if qualified in allowed:
            if status != "completed" or len(started[key]) != 1 or len(completed[key]) != 1:
                raise TrialError(
                    "authorized runner-owned MCP tool did not complete "
                    f"(server={server}, tool={tool}, status={status}, error={category}, "
                    f"started={len(started[key])}, completed={len(completed[key])})"
                )
            continue
        if server not in enabled_servers or category == "unavailable":
            raise TrialError(
                "candidate selected an unavailable MCP tool "
                f"(server={server}, tool={tool}, status={status}, error={category})"
            )
        raise TrialError(
            "candidate selected a prohibited configured MCP tool "
            f"(server={server}, tool={tool}, status={status}, error={category})"
        )


def sanitized_trajectory(
    events: Path,
    *,
    allowed_mcp_tools: tuple[str, ...] = (),
    mcp_surface: tuple[dict[str, Any], ...] = (),
) -> list[dict[str, Any]]:
    trajectory: list[dict[str, Any]] = []
    mcp_entries: list[dict[str, Any]] = []
    for line in events.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        item = event.get("item") if isinstance(event.get("item"), dict) else {}
        event_type = event.get("type")
        item_type = item.get("type")
        lowered = " ".join(
            value.lower()
            for value in (event_type, item_type, item.get("name"))
            if isinstance(value, str)
        )
        if "mcp" in lowered:
            if item_type != "mcp_tool_call":
                raise TrialError(
                    "candidate emitted an unrecognized MCP event "
                    f"(event_type={bounded_event_identity(event_type)}, "
                    f"item_type={bounded_event_identity(item_type)})"
                )
            entry = {
                "event_type": bounded_event_identity(event_type),
                "item_type": "mcp_tool_call",
                "mcp_server": bounded_event_identity(item.get("server")),
                "mcp_tool": bounded_event_identity(item.get("tool")),
            }
            call_id = item.get("id")
            if isinstance(call_id, str) and call_id:
                entry["call_identity_sha256"] = sha256_text(call_id)
            status = item.get("status")
            if isinstance(status, str):
                entry["status"] = bounded_event_identity(status)
            error_category = mcp_error_category(item)
            if error_category is not None:
                entry["error_category"] = error_category
            trajectory.append(entry)
            mcp_entries.append(entry)
            if len(trajectory) > MAX_TRAJECTORY_ENTRIES:
                raise TrialError(
                    "candidate tool trajectory exceeded the bounded assessment input"
                )
            continue
        if any(marker in lowered for marker in PROHIBITED_TRAJECTORY_MARKERS):
            raise TrialError(
                "candidate emitted a prohibited external tool event "
                f"(event_type={bounded_event_identity(event_type)}, "
                f"item_type={bounded_event_identity(item_type)})"
            )
        collaboration_event = "collab" in lowered
        if any(marker in lowered for marker in ("tool", "function")) and not any(
            marker in lowered
            for marker in ("command", "file_change", "apply_patch", "collab")
        ):
            raise TrialError(
                "candidate emitted an unrecognized tool event "
                f"(event_type={bounded_event_identity(event_type)}, "
                f"item_type={bounded_event_identity(item_type)})"
            )
        if not any(
            marker in lowered
            for marker in (
                "command",
                "tool",
                "function",
                "browser",
                "web_search",
                "computer",
                "mcp",
                "image",
                "collab",
            )
        ):
            continue
        entry: dict[str, Any] = {}
        for target, value in (
            ("event_type", event_type),
            ("item_type", item_type),
            ("tool_name", item.get("name")),
            ("status", item.get("status", event.get("status"))),
            ("exit_code", item.get("exit_code", event.get("exit_code"))),
        ):
            if isinstance(value, (str, int)) and not isinstance(value, bool):
                entry[target] = value
        command_value = item.get("command", event.get("command"))
        if isinstance(command_value, list) and all(
            isinstance(part, str) for part in command_value
        ):
            command_value = " ".join(command_value)
        if isinstance(command_value, str):
            entry["command"] = command_value[:2048]
        scope_value = item.get("prompt", event.get("prompt"))
        if isinstance(scope_value, str) and not collaboration_event:
            entry["scope"] = scope_value[:2048]
        child_id = item.get(
            "agent_thread_id", event.get("new_thread_id", event.get("thread_id"))
        )
        if isinstance(child_id, str) and "collab" in lowered:
            entry["child_identity_sha256"] = sha256_text(child_id)
        trajectory.append(entry)
        if len(trajectory) > MAX_TRAJECTORY_ENTRIES:
            raise TrialError("candidate tool trajectory exceeded the bounded assessment input")
    validate_mcp_trajectory(
        mcp_entries,
        allowed_mcp_tools=allowed_mcp_tools,
        inventory=mcp_surface,
    )
    return trajectory


def session_rollout_path(codex_home: Path, session_id: str) -> Path:
    if (
        not session_id
        or len(session_id) > 128
        or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for character in session_id)
    ):
        raise TrialError("Codex session id is not safe for rollout lookup")
    sessions = codex_home / "sessions"
    try:
        metadata = os.lstat(sessions)
    except OSError as exc:
        raise TrialError("isolated Codex sessions directory is unavailable") from exc
    if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise TrialError("isolated Codex sessions path must be a real directory")
    matches: list[Path] = []
    observed_files = 0
    for directory, directories, files in os.walk(sessions, followlinks=False):
        directory_path = Path(directory)
        for name in list(directories):
            child = directory_path / name
            try:
                child_metadata = os.lstat(child)
            except OSError as exc:
                raise TrialError("isolated Codex session directory changed during scan") from exc
            if stat.S_ISLNK(child_metadata.st_mode) or not stat.S_ISDIR(child_metadata.st_mode):
                raise TrialError("isolated Codex session tree contains an unsafe directory")
        for name in files:
            if not name.endswith(".jsonl"):
                continue
            observed_files += 1
            if observed_files > MAX_ROLLOUT_FILES:
                raise TrialError("isolated Codex rollout scan exceeded its file-count bound")
            if name.endswith(f"-{session_id}.jsonl"):
                matches.append(directory_path / name)
    if len(matches) != 1:
        raise TrialError(
            "isolated Codex rollout identity was missing or ambiguous "
            f"(matches={len(matches)})"
        )
    return matches[0]


def rollout_records(path: Path, label: str) -> list[dict[str, Any]]:
    content = bounded_file_bytes(path, MAX_CHILD_FILE_BYTES, label)
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TrialError(f"{label} is not UTF-8") from exc
    lines = text.splitlines()
    if len(lines) > MAX_ROLLOUT_LINES:
        raise TrialError(f"{label} exceeded its line-count bound")
    records: list[dict[str, Any]] = []
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TrialError(f"{label} contains invalid JSONL") from exc
        if not isinstance(record, dict):
            raise TrialError(f"{label} contains a non-object record")
        records.append(record)
    return records


def rollout_turn_id(record: dict[str, Any]) -> str | None:
    payload = record.get("payload")
    if not isinstance(payload, dict):
        return None
    direct = payload.get("turn_id")
    if isinstance(direct, str) and direct:
        return direct
    metadata = payload.get("internal_chat_message_metadata_passthrough")
    if isinstance(metadata, dict):
        nested = metadata.get("turn_id")
        if isinstance(nested, str) and nested:
            return nested
    return None


def sanitized_rollout_collaboration(
    codex_home: Path, session_id: str
) -> list[dict[str, Any]]:
    """Recover only hashed collaboration facts omitted by ``codex exec --json``."""

    parent = rollout_records(
        session_rollout_path(codex_home, session_id), "isolated parent rollout"
    )
    turn_ids = [turn_id for record in parent if (turn_id := rollout_turn_id(record))]
    if not turn_ids:
        raise TrialError("isolated parent rollout did not expose a turn identity")
    current_turn_id = turn_ids[-1]
    children: dict[str, str] = {}
    trajectory: list[dict[str, Any]] = []
    for record in parent:
        if rollout_turn_id(record) != current_turn_id:
            continue
        record_type = record.get("type")
        payload = record.get("payload")
        if not isinstance(payload, dict):
            continue
        if record_type == "event_msg":
            item = payload.get("item")
            if not isinstance(item, dict) or item.get("type") != "SubAgentActivity":
                continue
            child_id = item.get("agent_thread_id")
            child_path = item.get("agent_path")
            kind = item.get("kind")
            if not all(isinstance(value, str) and value for value in (child_id, child_path, kind)):
                raise TrialError("isolated collaboration activity is incomplete")
            if kind != "started":
                continue
            if child_path in children or child_id in children.values():
                raise TrialError("isolated collaboration activity duplicated a child identity")
            children[child_path] = child_id
            trajectory.append(
                {
                    "event_type": "collab_agent_spawn",
                    "item_type": "sub_agent_activity",
                    "status": "started",
                    "child_identity_sha256": sha256_text(child_id),
                    "child_path_sha256": sha256_text(child_path),
                }
            )
        elif record_type == "response_item" and payload.get("type") == "agent_message":
            author = payload.get("author")
            recipient = payload.get("recipient")
            if not isinstance(author, str) or author not in children or recipient != "/root":
                continue
            content = payload.get("content")
            if not isinstance(content, list):
                raise TrialError("isolated child result content is malformed")
            text_parts = [
                item["text"]
                for item in content
                if isinstance(item, dict)
                and item.get("type") == "input_text"
                and isinstance(item.get("text"), str)
            ]
            if not text_parts:
                raise TrialError("isolated child result is empty")
            result_bytes = "\n".join(text_parts).encode("utf-8")
            if len(result_bytes) > MAX_RESPONSE_BYTES:
                raise TrialError("isolated child result exceeded its bounded size")
            trajectory.append(
                {
                    "event_type": "collab_agent_result",
                    "item_type": "agent_message",
                    "status": "completed",
                    "child_path_sha256": sha256_text(author),
                    "content_sha256": sha256_bytes(result_bytes),
                }
            )
    for child_path, child_id in children.items():
        child_records = rollout_records(
            session_rollout_path(codex_home, child_id), "isolated child rollout"
        )
        for record in child_records:
            payload = record.get("payload")
            if not isinstance(payload, dict):
                continue
            if (
                record.get("type") == "response_item"
                and payload.get("type") == "function_call"
                and payload.get("namespace") == "collaboration"
                and payload.get("name") == "spawn_agent"
            ):
                trajectory.append(
                    {
                        "event_type": "collab_nested_spawn",
                        "item_type": "function_call",
                        "status": "attempted",
                        "child_identity_sha256": sha256_text(child_id),
                    }
                )
            if record.get("type") == "event_msg":
                item = payload.get("item")
                if isinstance(item, dict) and item.get("type") == "FileChange":
                    trajectory.append(
                        {
                            "event_type": "collab_child_file_change",
                            "item_type": "file_change",
                            "status": str(item.get("status", "observed")),
                            "child_path_sha256": sha256_text(child_path),
                        }
                    )
    if len(trajectory) > MAX_TRAJECTORY_ENTRIES:
        raise TrialError("isolated collaboration trajectory exceeded its bound")
    return trajectory


def enforce_trajectory_contract(
    *,
    case_id: str,
    expected: list[str],
    trajectory: list[dict[str, Any]],
    fixture_delta: list[dict[str, Any]] | tuple[()] = (),
) -> None:
    def parsed_command(command: Any) -> tuple[str, ...] | None:
        if not isinstance(command, str):
            return None
        try:
            return tuple(shlex.split(command))
        except ValueError:
            return None

    def executed_argv(command: Any) -> tuple[str, ...] | None:
        argv = parsed_command(command)
        if argv in expected_argv:
            return argv
        canonical_inner = {shlex.join(expected): expected for expected in expected_argv}
        if (
            argv is not None
            and len(argv) == 3
            and argv[0] in TRUSTED_SHELL_WRAPPERS
            and argv[1] in {"-c", "-lc"}
            and argv[2] in canonical_inner
        ):
            return canonical_inner[argv[2]]
        return None

    if "child-scope-subset" in expected:
        spawns = [
            entry
            for entry in trajectory
            if entry.get("event_type") == "collab_agent_spawn"
        ]
        results = [
            entry
            for entry in trajectory
            if entry.get("event_type") == "collab_agent_result"
        ]
        if (
            len(spawns) != 1
            or len(results) != 1
            or not isinstance(spawns[0].get("child_identity_sha256"), str)
            or spawns[0].get("child_path_sha256") != results[0].get("child_path_sha256")
            or not isinstance(results[0].get("content_sha256"), str)
        ):
            raise TrialError(
                f"{case_id}: required delegated inspection/result was not observed"
            )
    if "read-only-child" in expected and any(
        entry.get("event_type") == "collab_child_file_change" for entry in trajectory
    ):
        raise TrialError(f"{case_id}: delegated read-only child changed a file")
    if "no-redelegation" in expected and any(
        entry.get("event_type") == "collab_nested_spawn" for entry in trajectory
    ):
        raise TrialError(f"{case_id}: delegated child attempted nested delegation")
    if "exact-mcp-tool-once" in expected:
        completed_mcp = [
            entry
            for entry in trajectory
            if entry.get("event_type") == "item.completed"
            and entry.get("item_type") == "mcp_tool_call"
            and entry.get("status") == "completed"
        ]
        if len(completed_mcp) != 1:
            raise TrialError(
                f"{case_id}: runner-owned MCP tool must complete exactly once "
                f"(completed={len(completed_mcp)})"
            )
    if "one-justified-retry" in expected and fixture_delta:
        fixture_paths = {
            entry["path"]
            for entry in fixture_delta
            if isinstance(entry.get("path"), str)
        }
        if any(not benchmark_fixture_path_is_safe(path) for path in fixture_paths):
            raise TrialError(f"{case_id}: changed capability path is unsafe")
        expected_argv = {
            ("python3", path)
            for path in fixture_paths
        }
        command_events = [
            entry
            for entry in trajectory
            if "command" in str(entry.get("item_type", "")).lower()
        ]
        attempts = [
            entry
            for entry in command_events
            if entry.get("event_type") == "item.completed"
            and entry.get("item_type") == "command_execution"
            and executed_argv(entry.get("command")) in expected_argv
        ]
        if (
            len(attempts) != 1
            or attempts[0].get("status") != "completed"
            or attempts[0].get("exit_code") != 0
            or isinstance(attempts[0].get("exit_code"), bool)
        ):
            completed_events = [
                entry
                for entry in command_events
                if entry.get("event_type") == "item.completed"
            ]
            path_mentions = [
                entry
                for entry in command_events
                if isinstance(entry.get("command"), str)
                and any(path in entry["command"] for path in fixture_paths)
            ]
            exact_argv_events = [
                entry
                for entry in command_events
                if executed_argv(entry.get("command")) in expected_argv
            ]
            raise TrialError(
                f"{case_id}: changed capability must be invoked exactly once and succeed "
                f"(command_events={len(command_events)}, "
                f"completed_events={len(completed_events)}, "
                f"fixture_path_mentions={len(path_mentions)}, "
                f"exact_argv_events={len(exact_argv_events)}, "
                f"matching_attempts={len(attempts)})"
            )


def enforce_mutation_contract(
    *,
    case_id: str,
    turn_number: int,
    mutation: str,
    mutation_paths: list[str] | tuple[()],
    delta: list[dict[str, Any]],
) -> None:
    changed_paths = {
        entry["path"] for entry in delta if isinstance(entry.get("path"), str)
    }
    if mutation == "repository":
        expected_paths = set(mutation_paths)
        if changed_paths != expected_paths:
            raise TrialError(
                f"{case_id} turn {turn_number}: candidate mutation paths did not match "
                f"the exact contract (expected={sorted(expected_paths)}, "
                f"observed={sorted(changed_paths)})"
            )
        return
    if changed_paths:
        raise TrialError(
            f"{case_id} turn {turn_number}: candidate changed repository bytes"
        )


def repository_state(root: Path) -> dict[str, dict[str, Any]]:
    state: dict[str, dict[str, Any]] = {}
    total_bytes = 0
    file_count = 0
    for path in sorted(root.rglob("*")):
        if ".git" in path.parts or (not path.is_file() and not path.is_symlink()):
            continue
        relative = path.relative_to(root).as_posix()
        content = (
            ("symlink:" + os.readlink(path)).encode("utf-8")
            if path.is_symlink()
            else bounded_file_bytes(
                path, MAX_REPOSITORY_FILE_BYTES, "repository state input"
            )
        )
        if len(content) > MAX_REPOSITORY_FILE_BYTES:
            raise TrialError(f"repository file exceeds assessment bound: {relative}")
        file_count += 1
        total_bytes += len(content)
        if file_count > MAX_REPOSITORY_FILES or total_bytes > MAX_REPOSITORY_TOTAL_BYTES:
            raise TrialError("repository state exceeded the bounded fixture size")
        if is_transient_python_runtime_path(relative):
            continue
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = None
        state[relative] = {"sha256": sha256_bytes(content), "text": text}
    return state


def repository_delta(
    before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    delta: list[dict[str, Any]] = []
    for path in sorted(set(before) | set(after)):
        prior = before.get(path)
        current = after.get(path)
        if prior == current:
            continue
        delta.append(
            {
                "path": path,
                "before_sha256": prior["sha256"] if prior else None,
                "after_sha256": current["sha256"] if current else None,
                "after_text": current["text"] if current else None,
            }
        )
    encoded = json.dumps(delta, ensure_ascii=False).encode("utf-8")
    if len(encoded) > MAX_REPOSITORY_DELTA_BYTES:
        raise TrialError("repository delta exceeded the bounded assessment input")
    return delta


def apply_pre_turn_fixture(repository: Path, files: dict[str, str]) -> list[dict[str, Any]]:
    if not files:
        return []
    if len(files) > BENCHMARK_FIXTURE_MAX_FILES:
        raise TrialError("pre-turn fixture exceeds its file-count bound")
    if benchmark_fixture_evidence_bytes(files) > MAX_REPOSITORY_DELTA_BYTES:
        raise TrialError("pre-turn fixture exceeds its assessment evidence byte bound")
    before = repository_state(repository)
    total_bytes = 0
    for relative, content in sorted(files.items()):
        path = Path(relative)
        encoded = content.encode("utf-8")
        total_bytes += len(encoded)
        if (
            not benchmark_fixture_path_is_safe(relative)
            or len(encoded) > MAX_REPOSITORY_FILE_BYTES
            or total_bytes > MAX_REPOSITORY_DELTA_BYTES
        ):
            raise TrialError(f"pre-turn fixture path or content is unsafe: {relative!r}")
        parent = repository
        for part in path.parts[:-1]:
            parent = parent / part
            if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
                raise TrialError(f"pre-turn fixture parent is unsafe: {relative!r}")
            parent.mkdir(exist_ok=True)
        target = repository / path
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise TrialError(f"pre-turn fixture target is unsafe: {relative!r}")
        target.write_text(content, encoding="utf-8")
    delta = repository_delta(before, repository_state(repository))
    if len(delta) != len(files):
        raise TrialError("pre-turn fixture did not produce the declared byte changes")
    return delta


def git_head(repository: Path) -> str:
    return command_output(["git", "rev-parse", "HEAD"], "fixture Git HEAD", repository)


def command_output(command: list[str], label: str, cwd: Path | None = None) -> str:
    try:
        completed = run_bounded_process(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            env=controlled_environment(),
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        raise TrialError(f"timed out while resolving {label}") from exc
    if completed.returncode != 0:
        raise TrialError(f"unable to resolve {label}")
    return completed.stdout.strip()


def run_codex_turn(
    *,
    codex: str,
    codex_home: Path,
    repository: Path,
    model: str,
    effort: str,
    prompt: str,
    session_id: str | None,
    fork: bool,
    events: Path,
    last_message: Path,
    token_limit: int,
    timeout_seconds: int,
) -> str:
    config = [
        "-c",
        f"model_reasoning_effort={json.dumps(effort)}",
        "-c",
        'approval_policy="never"',
        "-c",
        SHELL_ENVIRONMENT_POLICY,
        "-c",
        "features.rollout_budget.enabled=true",
        "-c",
        f"features.rollout_budget.limit_tokens={token_limit}",
        "-c",
        "features.rollout_budget.reminder_at_remaining_tokens=[]",
        "-c",
        "sandbox_workspace_write.network_access=false",
        "-c",
        "features.standalone_web_search=false",
        "-c",
        "features.browser_use=false",
        "-c",
        "features.computer_use=false",
        "-c",
        "features.apps=false",
        "-c",
        'web_search="disabled"',
        "-c",
        "features.image_generation=false",
        "-c",
        "features.remote_plugin=false",
        "-c",
        "features.skill_mcp_dependency_install=false",
        "-c",
        "features.network_proxy=false",
        "-c",
        "features.enable_mcp_apps=false",
        "-c",
        "features.in_app_browser=false",
        "-c",
        "features.browser_use_external=false",
        "-c",
        "features.browser_use_full_cdp_access=false",
        "-c",
        "features.multi_agent_v2.enabled=true",
        "-c",
        "agents.max_concurrent_threads_per_session=2",
        "-c",
        "features.multi_agent_v2.max_concurrent_threads_per_session=2",
        "-c",
        "features.multi_agent_v2.expose_spawn_agent_model_overrides=false",
        "-c",
        "features.multi_agent_v2.wait_agent_enabled=true",
        "-c",
        "features.multi_agent_v2.subagent_developer_instructions="
        + json.dumps(
            "This is an isolated evaluation child. Stay inside the delegated read-only scope, "
            "do not delegate again, and perform no network, external, delivery, or commit action."
        ),
    ]
    output = ["--json", "--output-last-message", str(last_message)]
    if session_id is None:
        command = [
            codex,
            "exec",
            *config,
            "--model",
            model,
            "--sandbox",
            "workspace-write",
            "--cd",
            str(repository),
            *output,
            SAFETY_PREFIX + prompt,
        ]
    else:
        lineage = "fork" if fork else "resume"
        command = [
            codex,
            "exec",
            lineage,
            *config,
            "--model",
            model,
            *output,
            session_id,
            SAFETY_PREFIX + prompt,
        ]
    environment = controlled_environment(CODEX_HOME=str(codex_home))
    with (
        events.open("w", encoding="utf-8") as stdout,
        tempfile.TemporaryFile(mode="w+", encoding="utf-8") as stderr,
    ):
        try:
            completed = run_bounded_process(
                command,
                cwd=repository,
                stdout=stdout,
                stderr=stderr,
                text=True,
                env=environment,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise TrialError("Codex turn timed out") from exc
        candidate_stderr = read_bounded_capture(
            stderr, MAX_CAPTURE_BYTES, "candidate stderr"
        )
    if completed.returncode != 0:
        raise TrialError(
            f"Codex failed (exit {completed.returncode}; stderr {sha256_text(candidate_stderr)})"
        )
    if events.stat().st_size > MAX_CHILD_FILE_BYTES:
        raise TrialError("candidate event stream exceeded its bounded file size")
    if not last_message.is_file():
        raise TrialError("Codex completed without a last-message artifact")
    return extract_session_id(events)


def run_attempt(
    *,
    cases: list[dict[str, Any]],
    codex: str,
    plugin_root: Path,
    model: str,
    effort: str,
    maximum_tokens: int,
    per_call_token_limit: int,
    per_call_timeout_seconds: int,
    usage_checkpoint: Path,
    evidence_checkpoint: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    cases_evidence: list[dict[str, Any]] = []
    usage_records: list[dict[str, Any]] = []
    consumed_tokens = 0
    pending_call: dict[str, Any] | None = None

    def usage_summary() -> dict[str, Any]:
        return {
            "schema_version": "dev-flow.benchmark.usage.v1",
            "maximum_tokens": maximum_tokens,
            "consumed_tokens": consumed_tokens,
            "remaining_tokens": maximum_tokens - consumed_tokens,
            "usage_complete": pending_call is None,
            "pending_call": pending_call,
            "records": usage_records,
        }

    def write_usage_checkpoint() -> None:
        usage_checkpoint.write_text(
            json.dumps(usage_summary(), indent=2) + "\n", encoding="utf-8"
        )

    def write_evidence_checkpoint() -> None:
        evidence_checkpoint.write_text(
            json.dumps(
                {
                    "schema_version": "dev-flow.benchmark.evidence.v1",
                    "cases": cases_evidence,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def next_limit() -> int:
        remaining = maximum_tokens - consumed_tokens
        if remaining <= 0:
            raise TrialError("authorized aggregate token budget is exhausted")
        return min(per_call_token_limit, remaining)

    def record_usage(
        *,
        role: str,
        case_id: str,
        turn: int,
        usage: dict[str, int],
        token_limit: int,
        **identity: Any,
    ) -> None:
        nonlocal consumed_tokens, pending_call
        tokens = checked_tokens(usage, role, token_limit)
        consumed_tokens += tokens
        usage_records.append(
            {
                "role": role,
                "case_id": case_id,
                "turn": turn,
                "tokens": tokens,
                "token_limit": token_limit,
                "token_usage": usage,
                **identity,
            }
        )
        pending_call = None
        write_usage_checkpoint()
        if consumed_tokens > maximum_tokens:
            raise TrialError("authorized aggregate token budget was exceeded")

    with tempfile.TemporaryDirectory(prefix="dev-flow-bench-") as temporary:
        attempt_root = Path(temporary)
        for case_index, case in enumerate(cases, 1):
            codex_home = Path(
                tempfile.mkdtemp(
                    prefix=f"codex-home-{case_index:03d}-", dir=attempt_root
                )
            )
            install_candidate(codex, codex_home, plugin_root)
            repository = attempt_root / f"case-{case_index:03d}"
            write_fixture(repository, case["repository"])
            case_mcp_inventory = configure_case_mcp(
                codex=codex,
                codex_home=codex_home,
                repository=repository,
                fixture=case.get("mcp_fixture"),
                fixture_script=Path(dev_flow_bench_fixture_mcp.__file__).resolve(),
            )
            initial_repository_sha = repository_sha256(repository)
            initial_git_head_sha = sha256_text(git_head(repository))
            session_id: str | None = None
            lineage_ids: list[str] = []
            turn_evidence: list[dict[str, Any]] = []
            case_evidence = {
                "id": case["id"],
                "lineage_id": sha256_text(""),
                "initial_repository_sha256": initial_repository_sha,
                "initial_git_head_sha256": initial_git_head_sha,
                "mcp_inventory": case_mcp_inventory,
                "turns": turn_evidence,
            }
            cases_evidence.append(case_evidence)
            for turn_number, turn in enumerate(case["turns"], 1):
                events = attempt_root / f"events-{case_index:03d}-{turn_number:02d}.jsonl"
                last_message = attempt_root / f"message-{case_index:03d}-{turn_number:02d}.txt"
                fixture_delta = apply_pre_turn_fixture(
                    repository, turn.get("pre_turn_fixture", {})
                )
                before_sha = repository_sha256(repository)
                before_state = repository_state(repository)
                head_before = git_head(repository)
                previous_session_id = session_id
                candidate_limit = next_limit()
                pending_call = {
                    "role": "candidate",
                    "case_id": case["id"],
                    "turn": turn_number,
                    "token_limit": candidate_limit,
                }
                write_usage_checkpoint()
                session_id = run_codex_turn(
                    codex=codex,
                    codex_home=codex_home,
                    repository=repository,
                    model=model,
                    effort=effort,
                    prompt=turn["prompt"],
                    session_id=session_id,
                    fork=case["lineage"] == "fork" and turn_number == 2,
                    events=events,
                    last_message=last_message,
                    token_limit=candidate_limit,
                    timeout_seconds=per_call_timeout_seconds,
                )
                candidate_usage = usage_breakdown(events)
                record_usage(
                    role="candidate",
                    case_id=case["id"],
                    turn=turn_number,
                    usage=candidate_usage,
                    model=model,
                    reasoning_effort=effort,
                    token_limit=candidate_limit,
                )
                lineage_ids.append(session_id)
                after_sha = repository_sha256(repository)
                after_state = repository_state(repository)
                head_after = git_head(repository)
                candidate_delta = repository_delta(before_state, after_state)
                response_bytes = bounded_file_bytes(
                    last_message, MAX_RESPONSE_BYTES, "candidate first-attempt response"
                )
                try:
                    response_text = response_bytes.decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise TrialError("candidate first-attempt response is not UTF-8") from exc
                response_sha = sha256_bytes(response_bytes)
                trajectory = sanitized_trajectory(
                    events,
                    allowed_mcp_tools=tuple(turn.get("allowed_mcp_tools", ())),
                    mcp_surface=tuple(case_mcp_inventory),
                )
                if "child-scope-subset" in turn["expected"]:
                    trajectory.extend(
                        sanitized_rollout_collaboration(codex_home, session_id)
                    )
                evidence = {
                    "schema_version": "dev-flow.benchmark.turn-evidence.v1",
                    "case_id": case["id"],
                    "turn": turn_number,
                    "prompt_sha256": sha256_text(turn["prompt"]),
                    "response_text": response_text,
                    "trajectory": trajectory,
                    "mcp_inventory": case_mcp_inventory,
                    "fixture_delta": fixture_delta,
                    "repository_delta": candidate_delta,
                    "git_head_changed": head_after != head_before,
                    "repository_before_sha256": before_sha,
                    "repository_after_sha256": after_sha,
                    "response_sha256": response_sha,
                }
                evidence_binding = {
                    "case_id": case["id"],
                    "turn": turn_number,
                    "response_sha256": response_sha,
                    "trajectory": evidence["trajectory"],
                    "mcp_inventory": case_mcp_inventory,
                    "fixture_delta": fixture_delta,
                    "repository_delta": candidate_delta,
                }
                turn_evidence.append(
                    {
                        **evidence,
                        "evidence_sha256": sha256_text(
                            json.dumps(evidence_binding, sort_keys=True, separators=(",", ":"))
                        ),
                    }
                )
                case_evidence["lineage_id"] = sha256_text("\n".join(lineage_ids))
                write_evidence_checkpoint()
                validate_lineage_transition(
                    case_id=case["id"],
                    turn=turn_number,
                    lineage=case["lineage"],
                    previous=previous_session_id,
                    current=session_id,
                )
                if head_after != head_before:
                    raise TrialError(
                        f"{case['id']} turn {turn_number}: prohibited Git HEAD change observed"
                    )
                enforce_mutation_contract(
                    case_id=case["id"],
                    turn_number=turn_number,
                    mutation=turn["mutation"],
                    mutation_paths=turn.get("mutation_paths", ()),
                    delta=candidate_delta,
                )
                enforce_trajectory_contract(
                    case_id=case["id"],
                    expected=turn["expected"],
                    trajectory=evidence["trajectory"],
                    fixture_delta=fixture_delta,
                )
            shutil.rmtree(codex_home)
    return (
        {
            "schema_version": "dev-flow.benchmark.evidence.v1",
            "cases": cases_evidence,
        },
        usage_summary(),
    )
