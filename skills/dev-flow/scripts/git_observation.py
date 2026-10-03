"""Focused read-only Git boundary shared by repository diagnostics."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any


GIT_TIMEOUT_SECONDS = 15
SAFE_GIT_PREFIX = [
    "git", "-c", "core.fsmonitor=false", "-c", f"core.hooksPath={os.devnull}",
]


class GitObservationError(RuntimeError):
    def __init__(self, status: str, reason: str) -> None:
        self.observation: dict[str, Any] = {"status": status, "reason": reason}
        super().__init__(reason)


def run_git(
    root: Path, arguments: list[str], *, text: bool = True,
) -> subprocess.CompletedProcess:
    """Run a caller-owned Git query without inherited Git routing or executable monitors."""
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update({
        "GIT_OPTIONAL_LOCKS": "0", "GIT_PAGER": "cat", "GIT_TERMINAL_PROMPT": "0",
        "LC_ALL": "C",
    })
    try:
        return subprocess.run(
            [*SAFE_GIT_PREFIX, *arguments], cwd=root, capture_output=True,
            check=False, text=text, env=environment, timeout=GIT_TIMEOUT_SECONDS,
            **({"encoding": "utf-8", "errors": "replace"} if text else {}),
        )
    except subprocess.TimeoutExpired as exc:
        raise GitObservationError("timeout", "git-command-timed-out") from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise GitObservationError("unavailable", "git-command-unavailable") from exc


def command_failure(completed: subprocess.CompletedProcess, operation: str) -> dict[str, Any]:
    return {
        "status": "failed", "reason": "git-command-failed",
        "operation": operation, "returncode": completed.returncode,
    }


def _text(value: str | bytes) -> str:
    return value.decode("utf-8", "replace") if isinstance(value, bytes) else value


def probe_worktree(root: Path) -> dict[str, Any]:
    operation = "repository-probe"
    try:
        completed = run_git(root, ["rev-parse", "--is-inside-work-tree"])
        if completed.returncode == 0:
            value = _text(completed.stdout).strip()
            if value == "true":
                operation = "repository-root"
                top_level = run_git(root, ["rev-parse", "--show-toplevel"])
                if top_level.returncode != 0:
                    return command_failure(top_level, operation)
                selected = root.resolve(strict=True)
                discovered = Path(_text(top_level.stdout).removesuffix("\n"))
                if not discovered.is_absolute():
                    return {"status": "failed", "reason": "git-repository-root-invalid", "operation": operation}
                if discovered.resolve(strict=True) != selected:
                    return {
                        "status": "not-applicable", "reason": "selected-root-is-not-git-worktree-root",
                        "repository_kind": "ancestor-worktree",
                    }
                return {"status": "observed"}
            if value == "false":
                return {
                    "status": "not-applicable", "reason": "root-is-not-a-git-worktree",
                    "repository_kind": "without-worktree",
                }
            return {"status": "failed", "reason": "git-repository-probe-invalid"}
        # A canonical negative discovery result is N/A only when no enclosing Git
        # marker exists. Corrupt metadata must not become an ordinary non-repository.
        stderr = _text(completed.stderr).strip()
        if completed.returncode == 128 and stderr.startswith("fatal: not a git repository"):
            absolute = root.resolve(strict=True)
            for parent in (absolute, *absolute.parents):
                try:
                    (parent / ".git").lstat()
                except FileNotFoundError:
                    continue
                else:
                    return command_failure(completed, "repository-probe")
            return {"status": "not-applicable", "reason": "root-is-not-a-git-worktree"}
        return command_failure(completed, "repository-probe")
    except GitObservationError as exc:
        return {**exc.observation, "operation": operation}
    except OSError:
        return {"status": "unavailable", "reason": "git-metadata-could-not-be-inspected"}
