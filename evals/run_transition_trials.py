#!/usr/bin/env python3
"""Run explicitly authorized, isolated multi-turn Dev Flow transition trials.

The runner executes the candidate and preserves bounded synthetic first-attempt
evidence. It never classifies the candidate. Assessment remains a separate manual
observation manifest evaluated by the public ``flow-metrics`` transition lane.
Raw session events and fixture repositories are removed after each attempt.
"""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import candidate_identity  # noqa: E402

try:
    import resource
except ImportError:  # pragma: no cover - Windows compatibility
    resource = None


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "dev-flow" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from flow_metrics import (  # noqa: E402
    ActivationContractError,
    TRANSITION_FIXTURE_MAX_FILE_BYTES,
    TRANSITION_FIXTURE_MAX_FILES,
    TRANSITION_FIXTURE_MAX_TOTAL_BYTES,
    TRANSITION_REPOSITORY_MAX_FILE_BYTES,
    TRANSITION_REPOSITORY_MAX_FILES,
    TRANSITION_REPOSITORY_MAX_TOTAL_BYTES,
    run_transition_catalog,
    transition_fixture_evidence_bytes,
    transition_fixture_path_is_safe,
    validate_transition_repository_fixture,
    validate_transition_catalog,
)


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
MAX_REPOSITORY_FILE_BYTES = TRANSITION_REPOSITORY_MAX_FILE_BYTES
MAX_REPOSITORY_DELTA_BYTES = TRANSITION_FIXTURE_MAX_TOTAL_BYTES
MAX_REPOSITORY_TOTAL_BYTES = TRANSITION_REPOSITORY_MAX_TOTAL_BYTES
MAX_REPOSITORY_FILES = TRANSITION_REPOSITORY_MAX_FILES
MAX_CANDIDATE_FILE_BYTES = 16 * 1024 * 1024
MAX_CANDIDATE_TOTAL_BYTES = 64 * 1024 * 1024
MAX_CANDIDATE_FILES = 4096
MAX_IDENTITY_FILE_BYTES = 512 * 1024 * 1024
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
    "mcp",
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


CAMPAIGN_BUDGET_SCHEMA = "flow.transition.campaign-budget.v1"
CAMPAIGN_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
CAMPAIGN_STATUSES = {
    "reserved",
    "running",
    "failed",
    "interrupted",
    "awaiting-manual-assessment",
}
MAX_CAMPAIGN_LEDGER_BYTES = 1024 * 1024


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


def _validate_campaign_ledger(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version",
        "campaign_id",
        "maximum_tokens",
        "allocated_tokens",
        "runs",
    }:
        raise TrialError("campaign budget ledger must use the exact schema")
    if payload["schema_version"] != CAMPAIGN_BUDGET_SCHEMA:
        raise TrialError("campaign budget ledger schema is invalid")
    campaign_id = payload["campaign_id"]
    if not isinstance(campaign_id, str) or CAMPAIGN_ID_PATTERN.fullmatch(campaign_id) is None:
        raise TrialError("campaign budget id is invalid")
    maximum = payload["maximum_tokens"]
    allocated = payload["allocated_tokens"]
    if (
        not isinstance(maximum, int)
        or isinstance(maximum, bool)
        or maximum < 1
        or not isinstance(allocated, int)
        or isinstance(allocated, bool)
        or allocated < 0
        or allocated > maximum
    ):
        raise TrialError("campaign budget totals are invalid")
    runs = payload["runs"]
    if not isinstance(runs, list):
        raise TrialError("campaign budget runs must be a list")
    run_ids: set[str] = set()
    computed_allocated = 0
    for run in runs:
        if not isinstance(run, dict) or set(run) != {
            "run_id",
            "semantic_runtime_sha256",
            "qualification_execution_sha256",
            "authorized_tokens",
            "known_consumed_tokens",
            "status",
        }:
            raise TrialError("campaign budget run must use the exact schema")
        run_id = run["run_id"]
        if (
            not isinstance(run_id, str)
            or re.fullmatch(r"sha256:[0-9a-f]{64}|[A-Za-z0-9][A-Za-z0-9._-]{0,127}", run_id)
            is None
            or run_id in run_ids
        ):
            raise TrialError("campaign budget run id is invalid or duplicated")
        run_ids.add(run_id)
        for key in ("semantic_runtime_sha256", "qualification_execution_sha256"):
            value = run[key]
            if not isinstance(value, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None:
                raise TrialError(f"campaign budget {key} is invalid")
        authorized = run["authorized_tokens"]
        consumed = run["known_consumed_tokens"]
        if (
            not isinstance(authorized, int)
            or isinstance(authorized, bool)
            or authorized < 1
            or not isinstance(consumed, int)
            or isinstance(consumed, bool)
            or consumed < 0
            or consumed > authorized
            or run["status"] not in CAMPAIGN_STATUSES
        ):
            raise TrialError("campaign budget run totals or status are invalid")
        computed_allocated += authorized
    if computed_allocated != allocated:
        raise TrialError("campaign budget allocated total is inconsistent")
    return payload


def _read_campaign_ledger(path: Path) -> dict[str, Any] | None:
    if path.is_symlink():
        raise TrialError("campaign budget ledger must not be a symlink")
    if not path.exists():
        return None
    try:
        content = bounded_file_bytes(
            path, MAX_CAMPAIGN_LEDGER_BYTES, "campaign budget ledger"
        ).decode("utf-8")
        payload = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TrialError(f"campaign budget ledger is unreadable: {exc}") from exc
    return _validate_campaign_ledger(payload)


def _write_campaign_ledger(path: Path, payload: dict[str, Any]) -> None:
    _validate_campaign_ledger(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    if temporary.exists() or temporary.is_symlink():
        raise TrialError("campaign budget temporary path already exists")
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if len(encoded) > MAX_CAMPAIGN_LEDGER_BYTES:
        raise TrialError("campaign budget ledger exceeded its bounded size")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _with_campaign_guard(path: Path, operation: Any) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    guard = path.with_name(path.name + ".guard")
    if guard.is_symlink():
        raise TrialError("campaign budget guard must not be a symlink")
    try:
        descriptor = os.open(guard, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise TrialError("campaign budget ledger is locked by another or interrupted writer") from exc
    except PermissionError as exc:
        # Windows can report sharing violations for an existing O_EXCL guard as
        # EACCES rather than EEXIST.  Keep the admission path fail-closed while
        # allowing bounded contenders to classify the condition as lock
        # contention and retry it.
        raise TrialError("campaign budget ledger is locked or inaccessible") from exc
    try:
        os.close(descriptor)
        return operation()
    finally:
        try:
            guard.unlink()
        except FileNotFoundError:
            pass


def reserve_campaign_budget(
    path: Path,
    *,
    campaign_id: str,
    maximum_tokens: int,
    run_id: str,
    requested_tokens: int,
    semantic_runtime_sha256: str,
    qualification_execution_sha256: str,
) -> dict[str, Any]:
    if not isinstance(campaign_id, str) or CAMPAIGN_ID_PATTERN.fullmatch(campaign_id) is None:
        raise TrialError("campaign budget id is invalid")
    if (
        not isinstance(maximum_tokens, int)
        or isinstance(maximum_tokens, bool)
        or not isinstance(requested_tokens, int)
        or isinstance(requested_tokens, bool)
        or maximum_tokens < 1
        or requested_tokens < 1
        or requested_tokens > maximum_tokens
    ):
        raise TrialError("campaign token budget request is invalid")

    def reserve() -> dict[str, Any]:
        ledger = _read_campaign_ledger(path)
        if ledger is None:
            ledger = {
                "schema_version": CAMPAIGN_BUDGET_SCHEMA,
                "campaign_id": campaign_id,
                "maximum_tokens": maximum_tokens,
                "allocated_tokens": 0,
                "runs": [],
            }
        if ledger["campaign_id"] != campaign_id or ledger["maximum_tokens"] != maximum_tokens:
            raise TrialError("campaign budget identity or maximum changed")
        if any(run["run_id"] == run_id for run in ledger["runs"]):
            raise TrialError("campaign budget run id already exists")
        if any(
            run["semantic_runtime_sha256"] == semantic_runtime_sha256
            and run["qualification_execution_sha256"]
            == qualification_execution_sha256
            for run in ledger["runs"]
        ):
            raise TrialError(
                "candidate identities already have campaign evidence; reuse it instead of rerunning"
            )
        if ledger["allocated_tokens"] + requested_tokens > maximum_tokens:
            raise TrialError("campaign token budget would be exceeded")
        ledger["runs"].append(
            {
                "run_id": run_id,
                "semantic_runtime_sha256": semantic_runtime_sha256,
                "qualification_execution_sha256": qualification_execution_sha256,
                "authorized_tokens": requested_tokens,
                "known_consumed_tokens": 0,
                "status": "reserved",
            }
        )
        ledger["allocated_tokens"] += requested_tokens
        _write_campaign_ledger(path, ledger)
        return ledger

    return _with_campaign_guard(path, reserve)


def update_campaign_budget(
    path: Path,
    *,
    run_id: str,
    known_consumed_tokens: int,
    status: str,
) -> dict[str, Any]:
    if status not in CAMPAIGN_STATUSES - {"reserved"}:
        raise TrialError("campaign budget update status is invalid")
    if not isinstance(known_consumed_tokens, int) or isinstance(
        known_consumed_tokens, bool
    ):
        raise TrialError("campaign known consumption is invalid")

    def update() -> dict[str, Any]:
        ledger = _read_campaign_ledger(path)
        if ledger is None:
            raise TrialError("campaign budget ledger is missing")
        matches = [run for run in ledger["runs"] if run["run_id"] == run_id]
        if len(matches) != 1:
            raise TrialError("campaign budget run is missing or duplicated")
        run = matches[0]
        if (
            known_consumed_tokens < run["known_consumed_tokens"]
            or known_consumed_tokens > run["authorized_tokens"]
        ):
            raise TrialError("campaign known consumption is non-monotonic or exceeds authority")
        run["known_consumed_tokens"] = known_consumed_tokens
        run["status"] = status
        _write_campaign_ledger(path, ledger)
        return ledger

    return _with_campaign_guard(path, update)


def campaign_reservation_was_persisted(path: Path, run_id: str) -> bool:
    guard = path.with_name(path.name + ".guard")
    if guard.exists() or guard.is_symlink():
        raise TrialError("campaign reservation state is still guarded or requires recovery")
    ledger = _read_campaign_ledger(path)
    if ledger is None:
        return False
    return any(run["run_id"] == run_id for run in ledger["runs"])


def file_sha256(path: Path) -> str:
    if path.stat().st_size > MAX_IDENTITY_FILE_BYTES:
        raise TrialError("qualification identity file exceeded its bounded size")
    digest = hashlib.sha256()
    total = 0
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            total += len(chunk)
            if total > MAX_IDENTITY_FILE_BYTES:
                raise TrialError("qualification identity file exceeded its bounded size")
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


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
        validate_transition_repository_fixture(files)
    except ActivationContractError as exc:
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


def sanitized_trajectory(events: Path) -> list[dict[str, Any]]:
    def bounded_event_identity(value: Any) -> str:
        if (
            isinstance(value, str)
            and 0 < len(value) <= 128
            and all(character.isalnum() or character in "._:-" for character in value)
        ):
            return value
        return "unavailable"

    trajectory: list[dict[str, Any]] = []
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
        if any(marker in lowered for marker in PROHIBITED_TRAJECTORY_MARKERS):
            raise TrialError("candidate emitted a prohibited external tool event")
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
    if "one-justified-retry" in expected and fixture_delta:
        fixture_paths = {
            entry["path"]
            for entry in fixture_delta
            if isinstance(entry.get("path"), str)
        }
        if any(not transition_fixture_path_is_safe(path) for path in fixture_paths):
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
    if len(files) > TRANSITION_FIXTURE_MAX_FILES:
        raise TrialError("pre-turn fixture exceeds its file-count bound")
    if transition_fixture_evidence_bytes(files) > MAX_REPOSITORY_DELTA_BYTES:
        raise TrialError("pre-turn fixture exceeds its assessment evidence byte bound")
    before = repository_state(repository)
    total_bytes = 0
    for relative, content in sorted(files.items()):
        path = Path(relative)
        encoded = content.encode("utf-8")
        total_bytes += len(encoded)
        if (
            not transition_fixture_path_is_safe(relative)
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


def qualification_identity(
    *,
    plugin_root: Path,
    catalog: Path,
    codex: str,
    model: str,
    reasoning_effort: str,
    execution_policy: dict[str, Any],
) -> dict[str, Any]:
    codex_path = shutil.which(codex)
    if codex_path is None:
        raise TrialError("Codex executable is unavailable")
    git_status = command_output(
        ["git", "status", "--porcelain=v1", "-z"], "candidate Git status", plugin_root
    )
    executable_sha256 = file_sha256(Path(codex_path).resolve())
    rc4_identities = candidate_identity.build_identities(
        plugin_root,
        runner=Path(__file__).resolve(),
        catalog=catalog,
        codex_executable_sha256=executable_sha256,
        model=model,
        reasoning_effort=reasoning_effort,
        environment_policy=SHELL_ENVIRONMENT_POLICY,
        execution_policy=execution_policy,
    )
    return {
        "schema_version": "flow.transition.qualification-identity.v2",
        "candidate_tree_sha256": candidate_source_sha256(plugin_root),
        "candidate_git_head": command_output(
            ["git", "rev-parse", "HEAD"], "candidate Git HEAD", plugin_root
        ),
        "candidate_git_status_sha256": sha256_text(git_status),
        "catalog_sha256": file_sha256(catalog),
        "runner_sha256": file_sha256(Path(__file__).resolve()),
        "codex_path_sha256": sha256_text(str(Path(codex_path).resolve())),
        "codex_executable_sha256": executable_sha256,
        "codex_version": command_output([codex_path, "--version"], "Codex version"),
        "semantic_runtime_identity": rc4_identities["semantic_runtime"],
        "qualification_execution_identity": rc4_identities[
            "qualification_execution"
        ],
    }


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
            "schema_version": "flow.transition.usage.v1",
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
                    "schema_version": "flow.transition.first-attempt-evidence.v1",
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

    with tempfile.TemporaryDirectory(prefix="dev-flow-transition-") as temporary:
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
                trajectory = sanitized_trajectory(events)
                if "child-scope-subset" in turn["expected"]:
                    trajectory.extend(
                        sanitized_rollout_collaboration(codex_home, session_id)
                    )
                evidence = {
                    "schema_version": "flow.transition.turn-evidence.v1",
                    "case_id": case["id"],
                    "turn": turn_number,
                    "prompt_sha256": sha256_text(turn["prompt"]),
                    "response_text": response_text,
                    "trajectory": trajectory,
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
            "schema_version": "flow.transition.first-attempt-evidence.v1",
            "cases": cases_evidence,
        },
        usage_summary(),
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--catalog",
        type=Path,
        default=ROOT / "evals" / "flow-transition-semantic-cases.json",
    )
    parser.add_argument("--case", action="append", dest="case_ids")
    parser.add_argument("--attempts", type=int, default=1)
    parser.add_argument("--model")
    parser.add_argument("--reasoning-effort", choices=("low", "medium", "high", "xhigh"))
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--plugin-root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--max-total-tokens", type=int)
    parser.add_argument("--campaign-budget-file", type=Path)
    parser.add_argument("--campaign-id")
    parser.add_argument("--campaign-max-total-tokens", type=int)
    parser.add_argument("--per-call-token-limit", type=int)
    parser.add_argument("--per-call-timeout-seconds", type=int)
    parser.add_argument(
        "--qualification",
        action="store_true",
        help="require the complete R4 catalog and its minimum independent first attempts",
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--acknowledge-model-spend", action="store_true")
    return parser.parse_args(argv)


def close_campaign_run_after_failure(
    *,
    campaign_budget_file: Path,
    run_id: str,
    output_dir: Path,
    attempt: int,
    consumed_tokens: int,
    pending_usage_tokens: int,
    attempt_usage_committed: bool,
    interrupted: bool,
    error: BaseException,
) -> dict[str, Any]:
    failure: dict[str, Any] = {
        "status": "interrupted" if interrupted else "failed",
        "phase": "pre-attempt" if attempt < 1 else "attempt",
        "attempt": attempt,
        "first_failure": "user interrupt" if interrupted else str(error)[:512],
        "retry_performed": False,
    }
    partial_tokens = 0
    if attempt >= 1 and not attempt_usage_committed:
        checkpoint = output_dir / f"usage-in-progress-{attempt:03d}.json"
        if checkpoint.is_file() and not checkpoint.is_symlink():
            failure["usage_checkpoint"] = checkpoint.name
            try:
                checkpoint_payload = json.loads(
                    bounded_file_bytes(
                        checkpoint, MAX_IDENTITY_FILE_BYTES, "usage checkpoint"
                    ).decode("utf-8")
                )
                observed = checkpoint_payload.get("consumed_tokens")
                if isinstance(observed, int) and not isinstance(observed, bool) and observed >= 0:
                    partial_tokens = observed
                    failure["known_consumed_tokens"] = observed
                failure["usage_complete"] = checkpoint_payload.get("usage_complete")
            except (TrialError, UnicodeDecodeError, json.JSONDecodeError):
                failure["usage_complete"] = False
        evidence_checkpoint = output_dir / f"evidence-in-progress-{attempt:03d}.json"
        if evidence_checkpoint.is_file() and not evidence_checkpoint.is_symlink():
            failure["evidence_checkpoint"] = evidence_checkpoint.name
    known_campaign_tokens = consumed_tokens + max(partial_tokens, pending_usage_tokens)
    failure["campaign_known_consumed_tokens"] = known_campaign_tokens
    try:
        update_campaign_budget(
            campaign_budget_file,
            run_id=run_id,
            known_consumed_tokens=known_campaign_tokens,
            status="interrupted" if interrupted else "failed",
        )
        failure["campaign_ledger_closed"] = True
    except BaseException as ledger_error:
        failure["campaign_ledger_closed"] = False
        failure["campaign_recovery_required"] = True
        failure["campaign_ledger_error"] = (
            f"{type(ledger_error).__name__}: {str(ledger_error)[:256]}"
        )
    try:
        (output_dir / "first-failure.json").write_text(
            json.dumps(failure, indent=2) + "\n", encoding="utf-8"
        )
    except BaseException as record_error:
        failure["failure_record_written"] = False
        failure["failure_record_error"] = type(record_error).__name__
    else:
        failure["failure_record_written"] = True
    return failure


def emit_json(payload: dict[str, Any]) -> None:
    try:
        print(json.dumps(payload, indent=2))
    except (BrokenPipeError, OSError):
        pass


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    campaign_budget_file: Path | None = None
    run_id: str | None = None
    campaign_reservation_started = False
    campaign_reserved = False
    output_dir: Path | None = None
    current_attempt = 0
    consumed_tokens = 0
    pending_usage_tokens = 0
    attempt_usage_committed = False
    try:
        catalog = validate_transition_catalog(
            json.loads(args.catalog.resolve().read_text(encoding="utf-8"))
        )
        if args.attempts < 1:
            raise TrialError("--attempts must be positive")
        if args.max_total_tokens is not None and args.max_total_tokens < 1:
            raise TrialError("--max-total-tokens must be positive")
        if (
            args.campaign_max_total_tokens is not None
            and args.campaign_max_total_tokens < 1
        ):
            raise TrialError("--campaign-max-total-tokens must be positive")
        if args.per_call_token_limit is not None and args.per_call_token_limit < 1:
            raise TrialError("--per-call-token-limit must be positive")
        if args.per_call_timeout_seconds is not None and args.per_call_timeout_seconds < 1:
            raise TrialError("--per-call-timeout-seconds must be positive")
        qualification = catalog["qualification"]
        selected = catalog["cases"]
        if args.case_ids:
            requested = set(args.case_ids)
            known = {case["id"] for case in selected}
            unknown = sorted(requested - known)
            if unknown:
                raise TrialError(f"unknown --case values: {unknown}")
            selected = [case for case in selected if case["id"] in requested]
        if args.qualification:
            if args.case_ids:
                raise TrialError("--qualification requires the complete catalog; omit --case")
            minimum_attempts = qualification["minimum_first_attempts_per_case"]
            if args.attempts < minimum_attempts:
                raise TrialError(
                    f"--qualification requires at least {minimum_attempts} independent first attempts"
                )
        category_coverage = {
            category: sum(category in case["categories"] for case in selected)
            for category in qualification["categories"]
        }
        plan = {
            "status": "ready" if args.execute else "planned",
            "executes_model": args.execute,
            "cases": [case["id"] for case in selected],
            "attempts": args.attempts,
            "qualification_requested": args.qualification,
            "qualification_eligible": (
                args.qualification
                and not args.case_ids
                and args.attempts >= qualification["minimum_first_attempts_per_case"]
                and all(
                    count >= qualification["minimum_cases_per_category"]
                    for count in category_coverage.values()
                )
            ),
            "qualification_contract": qualification,
            "category_coverage": category_coverage,
            "lineages": sorted({case["lineage"] for case in selected}),
            "candidate_model": args.model,
            "candidate_reasoning_effort": args.reasoning_effort,
            "raw_transcripts_retained": False,
            "first_attempt_responses_retained": True,
            "self_grading": False,
            "assessment": "manual-observation-manifest",
            "assessment_command": (
                "python3 skills/dev-flow/scripts/dev-flow.py flow-metrics "
                "--lane transition --observations /absolute/path/to/observations.json"
            ),
            "token_budget": {
                "maximum_total_tokens": args.max_total_tokens,
                "per_call_token_limit": args.per_call_token_limit,
                "per_call_timeout_seconds": args.per_call_timeout_seconds,
                "campaign_maximum_total_tokens": args.campaign_max_total_tokens,
            },
        }
        if not args.execute:
            print(json.dumps(plan, indent=2))
            return 0
        if not args.acknowledge_model_spend:
            raise TrialError("--execute requires --acknowledge-model-spend")
        if not args.model or not args.reasoning_effort:
            raise TrialError("--execute requires --model and --reasoning-effort")
        if (
            args.max_total_tokens is None
            or args.per_call_token_limit is None
            or args.per_call_timeout_seconds is None
        ):
            raise TrialError(
                "--execute requires --max-total-tokens, --per-call-token-limit, "
                "and --per-call-timeout-seconds"
            )
        if args.per_call_token_limit > args.max_total_tokens:
            raise TrialError("--per-call-token-limit cannot exceed --max-total-tokens")
        if args.output_dir is None:
            raise TrialError("--execute requires --output-dir")
        if (
            args.campaign_budget_file is None
            or args.campaign_id is None
            or args.campaign_max_total_tokens is None
        ):
            raise TrialError(
                "--execute requires --campaign-budget-file, --campaign-id, "
                "and --campaign-max-total-tokens"
            )
        if args.max_total_tokens > args.campaign_max_total_tokens:
            raise TrialError(
                "--max-total-tokens cannot exceed --campaign-max-total-tokens"
            )
        plugin_root = args.plugin_root.resolve()
        output_dir = args.output_dir.resolve()
        if output_dir == plugin_root or plugin_root in output_dir.parents:
            raise TrialError("--output-dir must be outside --plugin-root")
        if args.output_dir.exists() and any(args.output_dir.iterdir()):
            raise TrialError("--output-dir must be absent or empty")
        args.output_dir.mkdir(parents=True, exist_ok=True)
        execution_policy = {
            "qualification_requested": args.qualification,
            "case_ids": [case["id"] for case in selected],
            "attempts": args.attempts,
            "maximum_total_tokens": args.max_total_tokens,
            "per_call_token_limit": args.per_call_token_limit,
            "per_call_timeout_seconds": args.per_call_timeout_seconds,
            "campaign_id": args.campaign_id,
            "campaign_maximum_total_tokens": args.campaign_max_total_tokens,
        }
        identity = qualification_identity(
            plugin_root=plugin_root,
            catalog=args.catalog.resolve(),
            codex=args.codex,
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            execution_policy=execution_policy,
        )
        reservation_nonce = secrets.token_hex(16)
        run_id = sha256_text(
            json.dumps(
                {
                    "output_dir_sha256": sha256_text(str(output_dir)),
                    "reservation_nonce": reservation_nonce,
                    "semantic_runtime_sha256": identity["semantic_runtime_identity"][
                        "sha256"
                    ],
                    "qualification_execution_sha256": identity[
                        "qualification_execution_identity"
                    ]["sha256"],
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        campaign_budget_file = args.campaign_budget_file.resolve()
        campaign_reservation_started = True
        reserve_campaign_budget(
            campaign_budget_file,
            campaign_id=args.campaign_id,
            maximum_tokens=args.campaign_max_total_tokens,
            run_id=run_id,
            requested_tokens=args.max_total_tokens,
            semantic_runtime_sha256=identity["semantic_runtime_identity"]["sha256"],
            qualification_execution_sha256=identity[
                "qualification_execution_identity"
            ]["sha256"],
        )
        campaign_reserved = True
        (args.output_dir / "qualification-identity.json").write_text(
            json.dumps(identity, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        usage_results: list[dict[str, Any]] = []
        evidence_results: list[dict[str, Any]] = []
        for attempt in range(1, args.attempts + 1):
            current_attempt = attempt
            pending_usage_tokens = 0
            attempt_usage_committed = False
            try:
                remaining_tokens = args.max_total_tokens - consumed_tokens
                if remaining_tokens <= 0:
                    raise TrialError("authorized aggregate token budget is exhausted")
                evidence, usage = run_attempt(
                    cases=selected,
                    codex=args.codex,
                    plugin_root=plugin_root,
                    model=args.model,
                    effort=args.reasoning_effort,
                    maximum_tokens=remaining_tokens,
                    per_call_token_limit=args.per_call_token_limit,
                    per_call_timeout_seconds=args.per_call_timeout_seconds,
                    usage_checkpoint=args.output_dir
                    / f"usage-in-progress-{attempt:03d}.json",
                    evidence_checkpoint=args.output_dir
                    / f"evidence-in-progress-{attempt:03d}.json",
                )
                observed_usage = usage.get("consumed_tokens")
                if (
                    not isinstance(observed_usage, int)
                    or isinstance(observed_usage, bool)
                    or observed_usage < 0
                ):
                    raise TrialError("attempt usage is invalid")
                pending_usage_tokens = observed_usage
                if qualification_identity(
                    plugin_root=plugin_root,
                    catalog=args.catalog.resolve(),
                    codex=args.codex,
                    model=args.model,
                    reasoning_effort=args.reasoning_effort,
                    execution_policy=execution_policy,
                ) != identity:
                    raise TrialError("qualification identity changed during execution")
            except (OSError, TrialError, KeyboardInterrupt) as exc:
                failure = close_campaign_run_after_failure(
                    campaign_budget_file=campaign_budget_file,
                    run_id=run_id,
                    output_dir=output_dir,
                    attempt=current_attempt,
                    consumed_tokens=consumed_tokens,
                    pending_usage_tokens=pending_usage_tokens,
                    attempt_usage_committed=attempt_usage_committed,
                    interrupted=isinstance(exc, KeyboardInterrupt),
                    error=exc,
                )
                emit_json(failure)
                return 130 if isinstance(exc, KeyboardInterrupt) else 1
            target = args.output_dir / f"attempt-{attempt:03d}-evidence.json"
            target.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
            consumed_tokens += usage["consumed_tokens"]
            pending_usage_tokens = 0
            attempt_usage_committed = True
            usage["attempt"] = attempt
            usage["aggregate_maximum_tokens"] = args.max_total_tokens
            usage["aggregate_consumed_tokens"] = consumed_tokens
            usage["aggregate_remaining_tokens"] = args.max_total_tokens - consumed_tokens
            usage_target = args.output_dir / f"usage-{attempt:03d}.json"
            usage_target.write_text(json.dumps(usage, indent=2) + "\n", encoding="utf-8")
            checkpoint = args.output_dir / f"usage-in-progress-{attempt:03d}.json"
            if checkpoint.exists():
                checkpoint.unlink()
            evidence_checkpoint = (
                args.output_dir / f"evidence-in-progress-{attempt:03d}.json"
            )
            if evidence_checkpoint.exists():
                evidence_checkpoint.unlink()
            usage_results.append(usage)
            update_campaign_budget(
                campaign_budget_file,
                run_id=run_id,
                known_consumed_tokens=consumed_tokens,
                status="running",
            )
            evidence_results.append(
                {
                    "attempt": attempt,
                    "path": target.name,
                    "sha256": file_sha256(target),
                }
            )
        result = {
            **plan,
            "status": "awaiting-manual-assessment",
            "output_dir": str(args.output_dir),
            "evidence_results": evidence_results,
            "usage_results": usage_results,
            "consumed_tokens": consumed_tokens,
            "remaining_tokens": args.max_total_tokens - consumed_tokens,
            "qualification_identity": identity,
        }
        summary = args.output_dir / "qualification-summary.json"
        summary.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        update_campaign_budget(
            campaign_budget_file,
            run_id=run_id,
            known_consumed_tokens=consumed_tokens,
            status="awaiting-manual-assessment",
        )
        emit_json(result)
        return 0
    except (Exception, KeyboardInterrupt) as exc:
        admission_recovery_error: BaseException | None = None
        if (
            campaign_reservation_started
            and not campaign_reserved
            and not isinstance(exc, TrialError)
            and campaign_budget_file is not None
            and run_id is not None
        ):
            try:
                campaign_reserved = campaign_reservation_was_persisted(
                    campaign_budget_file, run_id
                )
            except BaseException as recovery_error:
                admission_recovery_error = recovery_error
        if (
            campaign_reserved
            and campaign_budget_file is not None
            and run_id is not None
            and output_dir is not None
        ):
            failure = close_campaign_run_after_failure(
                campaign_budget_file=campaign_budget_file,
                run_id=run_id,
                output_dir=output_dir,
                attempt=current_attempt,
                consumed_tokens=consumed_tokens,
                pending_usage_tokens=pending_usage_tokens,
                attempt_usage_committed=attempt_usage_committed,
                interrupted=isinstance(exc, KeyboardInterrupt),
                error=exc,
            )
            emit_json(failure)
            return 130 if isinstance(exc, KeyboardInterrupt) else 1
        if admission_recovery_error is not None and output_dir is not None:
            failure = {
                "status": "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed",
                "phase": "campaign-admission",
                "attempt": 0,
                "first_failure": "user interrupt"
                if isinstance(exc, KeyboardInterrupt)
                else str(exc)[:512],
                "retry_performed": False,
                "campaign_ledger_closed": False,
                "campaign_recovery_required": True,
                "campaign_ledger_error": (
                    f"{type(admission_recovery_error).__name__}: "
                    f"{str(admission_recovery_error)[:256]}"
                ),
            }
            try:
                (output_dir / "first-failure.json").write_text(
                    json.dumps(failure, indent=2) + "\n", encoding="utf-8"
                )
            except BaseException as record_error:
                failure["failure_record_written"] = False
                failure["failure_record_error"] = type(record_error).__name__
            else:
                failure["failure_record_written"] = True
            emit_json(failure)
            return 130 if isinstance(exc, KeyboardInterrupt) else 1
        if isinstance(exc, KeyboardInterrupt):
            emit_json({"status": "interrupted", "model_spend_started": False})
            return 130
        emit_json({"status": "invalid", "errors": [str(exc)]})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
