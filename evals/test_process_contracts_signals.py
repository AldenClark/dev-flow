#!/usr/bin/env python3
"""Real-signal regressions for evaluator process-tree ownership."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from collections.abc import Callable
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
PYTHON = sys.executable
sys.path.insert(0, str(EVALS))

import process_contracts as process_eval  # noqa: E402


@unittest.skipUnless(os.name == "posix", "POSIX signal semantics are required")
class OwnedProcessSignalTests(unittest.TestCase):
    marker_delay = 1.2

    def _write_tree_programs(self, root: Path) -> tuple[Path, Path]:
        descendant = root / "descendant.py"
        descendant.write_text(
            "import os,pathlib,sys,time\n"
            "marker = pathlib.Path(sys.argv[1])\n"
            "pathlib.Path(sys.argv[2]).write_text(str(os.getpid()), encoding='utf-8')\n"
            f"time.sleep({self.marker_delay!r})\n"
            "marker.write_text('leaked', encoding='utf-8')\n"
            "time.sleep(30)\n",
            encoding="utf-8",
        )
        child = root / "child.py"
        child.write_text(
            "import os,pathlib,subprocess,sys,time\n"
            "descendant,marker,child_pid,descendant_pid,ready = map(pathlib.Path, sys.argv[1:])\n"
            "subprocess.Popen([sys.executable, str(descendant), str(marker), str(descendant_pid)])\n"
            "child_pid.write_text(str(os.getpid()), encoding='utf-8')\n"
            "deadline = time.monotonic() + 5\n"
            "while not descendant_pid.exists():\n"
            "    if time.monotonic() >= deadline:\n"
            "        raise RuntimeError('descendant did not start')\n"
            "    time.sleep(0.01)\n"
            "ready.write_text('ready', encoding='utf-8')\n"
            "time.sleep(30)\n",
            encoding="utf-8",
        )
        return child, descendant

    def _tree_paths(self, root: Path, label: str) -> dict[str, Path]:
        return {
            "marker": root / f"{label}.marker",
            "child_pid": root / f"{label}.child.pid",
            "descendant_pid": root / f"{label}.descendant.pid",
            "ready": root / f"{label}.ready",
        }

    def _tree_command(self, child: Path, descendant: Path, paths: dict[str, Path]) -> list[str]:
        return [
            PYTHON,
            str(child),
            str(descendant),
            str(paths["marker"]),
            str(paths["child_pid"]),
            str(paths["descendant_pid"]),
            str(paths["ready"]),
        ]

    def _wait_for(self, predicate: Callable[[], bool], *, timeout: float = 5) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return True
            time.sleep(0.02)
        return predicate()

    def _read_pid(self, path: Path) -> int | None:
        try:
            pid = int(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return pid if pid > 1 else None

    def _pid_exists(self, pid: int | None) -> bool:
        if pid is None:
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    def _tree_pids(self, paths: dict[str, Path]) -> tuple[int | None, int | None]:
        return self._read_pid(paths["child_pid"]), self._read_pid(paths["descendant_pid"])

    def _tree_is_absent(self, paths: dict[str, Path]) -> bool:
        return not any(self._pid_exists(pid) for pid in self._tree_pids(paths))

    def _cleanup_tree(self, paths: dict[str, Path]) -> None:
        child_pid, descendant_pid = self._tree_pids(paths)
        for witness_pid in (child_pid, descendant_pid):
            if witness_pid is None:
                continue
            try:
                owned_session = os.getsid(witness_pid)
                owned_group = os.getpgid(witness_pid)
            except ProcessLookupError:
                continue
            if child_pid is not None and owned_session == child_pid and owned_group == child_pid:
                try:
                    os.killpg(child_pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                return

    def _stop_owner(self, owner: subprocess.Popen[str]) -> None:
        if owner.poll() is None:
            os.kill(owner.pid, signal.SIGKILL)
        try:
            owner.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            self.fail(f"test owner {owner.pid} did not stop after SIGKILL")

    def _spawn_owner(self, root: Path, body: str) -> subprocess.Popen[str]:
        owner_script = root / "owner.py"
        owner_script.write_text(body, encoding="utf-8")
        return subprocess.Popen(
            [PYTHON, str(owner_script)],
            cwd=root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )

    def _single_owner_body(self, command: list[str]) -> str:
        return (
            "import pathlib,sys\n"
            f"sys.path.insert(0, {str(EVALS)!r})\n"
            "from process_contracts import run_owned_process\n"
            f"run_owned_process({command!r}, '', cwd=pathlib.Path({command[2]!r}).parent, timeout=30)\n"
        )

    def test_sigterm_and_sigint_reap_child_and_descendant_before_owner_exits(self) -> None:
        for selected_signal in (signal.SIGTERM, signal.SIGINT):
            with self.subTest(signal=signal.Signals(selected_signal).name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                child, descendant = self._write_tree_programs(root)
                paths = self._tree_paths(root, "single")
                command = self._tree_command(child, descendant, paths)
                owner = self._spawn_owner(root, self._single_owner_body(command))
                signalled_at = 0.0
                try:
                    self.assertTrue(self._wait_for(paths["ready"].exists), "owned process tree did not start")
                    self.assertTrue(all(pid is not None for pid in self._tree_pids(paths)))
                    signalled_at = time.monotonic()
                    os.kill(owner.pid, selected_signal)
                    stdout, stderr = owner.communicate(timeout=3)
                    self.assertLess(time.monotonic() - signalled_at, 3)
                    self.assertEqual(owner.returncode, -selected_signal, (stdout, stderr))
                    self.assertTrue(
                        self._wait_for(lambda: self._tree_is_absent(paths), timeout=2),
                        f"owned tree survived {signal.Signals(selected_signal).name}",
                    )
                    remaining = self.marker_delay + 0.3 - (time.monotonic() - signalled_at)
                    if remaining > 0:
                        time.sleep(remaining)
                    self.assertFalse(paths["marker"].exists(), "cancelled descendant wrote its delayed marker")
                finally:
                    self._stop_owner(owner)
                    self._cleanup_tree(paths)

    def test_sigterm_reaps_multiple_concurrent_owned_process_trees(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            child, descendant = self._write_tree_programs(root)
            first = self._tree_paths(root, "first")
            second = self._tree_paths(root, "second")
            first_command = self._tree_command(child, descendant, first)
            second_command = self._tree_command(child, descendant, second)
            owner_body = (
                "import pathlib,sys,threading,time\n"
                f"sys.path.insert(0, {str(EVALS)!r})\n"
                "from process_contracts import run_owned_process\n"
                f"root = pathlib.Path({str(root)!r})\n"
                f"first = {first_command!r}\n"
                f"second = {second_command!r}\n"
                "def run_second():\n"
                "    time.sleep(0.1)\n"
                "    run_owned_process(second, '', cwd=root, timeout=30)\n"
                "worker = threading.Thread(target=run_second)\n"
                "worker.start()\n"
                "run_owned_process(first, '', cwd=root, timeout=30)\n"
                "worker.join()\n"
            )
            owner = self._spawn_owner(root, owner_body)
            signalled_at = 0.0
            try:
                self.assertTrue(
                    self._wait_for(lambda: first["ready"].exists() and second["ready"].exists()),
                    "concurrent owned process trees did not start",
                )
                signalled_at = time.monotonic()
                os.kill(owner.pid, signal.SIGTERM)
                owner.communicate(timeout=3)
                self.assertEqual(owner.returncode, -signal.SIGTERM)
                self.assertTrue(
                    self._wait_for(lambda: self._tree_is_absent(first) and self._tree_is_absent(second), timeout=2),
                    "a concurrent owned process tree survived SIGTERM",
                )
                remaining = self.marker_delay + 0.3 - (time.monotonic() - signalled_at)
                if remaining > 0:
                    time.sleep(remaining)
                self.assertFalse(first["marker"].exists())
                self.assertFalse(second["marker"].exists())
            finally:
                self._stop_owner(owner)
                self._cleanup_tree(first)
                self._cleanup_tree(second)

    def test_returning_caller_handler_runs_after_teardown_and_is_restored(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            child, descendant = self._write_tree_programs(root)
            paths = self._tree_paths(root, "controlled")
            state = root / "handler-state.json"
            command = self._tree_command(child, descendant, paths)
            owner_body = (
                "import json,pathlib,signal,sys\n"
                f"sys.path.insert(0, {str(EVALS)!r})\n"
                "from process_contracts import run_owned_process\n"
                f"root = pathlib.Path({str(root)!r})\n"
                f"state = pathlib.Path({str(state)!r})\n"
                "calls = []\n"
                "original_sigint = signal.getsignal(signal.SIGINT)\n"
                "def caller_handler(signum, frame):\n"
                "    calls.append(signum)\n"
                "signal.signal(signal.SIGTERM, caller_handler)\n"
                f"result = run_owned_process({command!r}, '', cwd=root, timeout=30)\n"
                "state.write_text(json.dumps({\n"
                "    'calls': calls,\n"
                "    'restored': signal.getsignal(signal.SIGTERM) is caller_handler,\n"
                "    'sigint_restored': signal.getsignal(signal.SIGINT) is original_sigint,\n"
                "    'returncode': result.returncode,\n"
                "    'error_kind': result.error_kind,\n"
                "}), encoding='utf-8')\n"
            )
            owner = self._spawn_owner(root, owner_body)
            try:
                self.assertTrue(self._wait_for(paths["ready"].exists), "owned process tree did not start")
                os.kill(owner.pid, signal.SIGTERM)
                stdout, stderr = owner.communicate(timeout=3)
                self.assertEqual(owner.returncode, 0, (stdout, stderr))
                handler_state = json.loads(state.read_text(encoding="utf-8"))
                self.assertEqual(handler_state["calls"], [signal.SIGTERM])
                self.assertTrue(handler_state["restored"])
                self.assertTrue(handler_state["sigint_restored"])
                self.assertLess(handler_state["returncode"], 0)
                self.assertEqual(handler_state["error_kind"], "cancelled")
                self.assertTrue(self._wait_for(lambda: self._tree_is_absent(paths), timeout=2))
                time.sleep(self.marker_delay + 0.3)
                self.assertFalse(paths["marker"].exists())
            finally:
                self._stop_owner(owner)
                self._cleanup_tree(paths)

    def test_main_scope_restores_handlers_while_a_worker_only_call_finishes(self) -> None:
        previous_sigterm = signal.getsignal(signal.SIGTERM)
        previous_sigint = signal.getsignal(signal.SIGINT)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ready = root / "worker.ready"
            worker_result: list[process_eval.OwnedProcessResult] = []

            def run_worker() -> None:
                worker_result.append(
                    process_eval.run_owned_process(
                        [
                            PYTHON,
                            "-c",
                            "import pathlib,sys,time; "
                            "pathlib.Path(sys.argv[1]).write_text('ready', encoding='utf-8'); "
                            "time.sleep(0.8)",
                            str(ready),
                        ],
                        "",
                        cwd=root,
                        timeout=3,
                    )
                )

            worker = threading.Thread(target=run_worker)
            worker.start()
            try:
                self.assertTrue(self._wait_for(ready.exists), "worker-only owned process did not start")
                result = process_eval.run_owned_process(
                    [PYTHON, "-c", "pass"],
                    "",
                    cwd=root,
                    timeout=2,
                )
                self.assertEqual(result.returncode, 0)
                self.assertTrue(worker.is_alive())
                self.assertIs(signal.getsignal(signal.SIGTERM), previous_sigterm)
                self.assertIs(signal.getsignal(signal.SIGINT), previous_sigint)
            finally:
                worker.join(timeout=3)
            self.assertFalse(worker.is_alive())
            self.assertEqual(len(worker_result), 1)
            self.assertEqual(worker_result[0].returncode, 0)

    def test_timeout_and_sigterm_reap_a_descendant_that_starts_a_new_session(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            marker = root / "detached.marker"
            detached_pid = root / "detached.pid"
            ready = root / "launcher.ready"
            detached = root / "detached.py"
            detached.write_text(
                "import os,pathlib,sys,time\n"
                "pathlib.Path(sys.argv[2]).write_text(str(os.getpid()), encoding='utf-8')\n"
                "time.sleep(1.0)\n"
                "pathlib.Path(sys.argv[1]).write_text('leaked', encoding='utf-8')\n"
                "time.sleep(30)\n",
                encoding="utf-8",
            )
            launcher = root / "launcher.py"
            launcher.write_text(
                "import pathlib,subprocess,sys,time\n"
                "subprocess.Popen([sys.executable, sys.argv[1], sys.argv[2], sys.argv[3]], start_new_session=True)\n"
                "deadline = time.monotonic() + 5\n"
                "pid_path = pathlib.Path(sys.argv[3])\n"
                "while not pid_path.exists():\n"
                "    if time.monotonic() >= deadline: raise RuntimeError('detached child did not start')\n"
                "    time.sleep(0.01)\n"
                "pathlib.Path(sys.argv[4]).write_text('ready', encoding='utf-8')\n"
                "time.sleep(30)\n",
                encoding="utf-8",
            )
            try:
                result = process_eval.run_owned_process(
                    [PYTHON, str(launcher), str(detached), str(marker), str(detached_pid), str(ready)],
                    "",
                    cwd=root,
                    timeout=0.3,
                )
                self.assertEqual(result.error_kind, "timeout")
                pid = self._read_pid(detached_pid)
                self.assertTrue(self._wait_for(lambda: not self._pid_exists(pid), timeout=2))
                time.sleep(1.1)
                self.assertFalse(marker.exists(), "detached descendant survived timeout teardown")
            finally:
                pid = self._read_pid(detached_pid)
                if self._pid_exists(pid):
                    os.kill(pid, signal.SIGKILL)

            signal_marker = root / "detached-signal.marker"
            signal_pid = root / "detached-signal.pid"
            signal_ready = root / "launcher-signal.ready"
            command = [
                PYTHON,
                str(launcher),
                str(detached),
                str(signal_marker),
                str(signal_pid),
                str(signal_ready),
            ]
            owner = self._spawn_owner(root, self._single_owner_body(command))
            try:
                self.assertTrue(self._wait_for(signal_ready.exists), "detached signal tree did not start")
                os.kill(owner.pid, signal.SIGTERM)
                stdout, stderr = owner.communicate(timeout=4)
                self.assertEqual(owner.returncode, -signal.SIGTERM, (stdout, stderr))
                pid = self._read_pid(signal_pid)
                self.assertTrue(self._wait_for(lambda: not self._pid_exists(pid), timeout=2))
                time.sleep(1.1)
                self.assertFalse(signal_marker.exists(), "detached descendant survived SIGTERM teardown")
            finally:
                self._stop_owner(owner)
                pid = self._read_pid(signal_pid)
                if self._pid_exists(pid):
                    os.kill(pid, signal.SIGKILL)


if __name__ == "__main__":
    unittest.main()
