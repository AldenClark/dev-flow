from __future__ import annotations

import json
import multiprocessing as mp
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "dev-flow" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def acquire_worker(root: str, start: object, queue: object) -> None:
    import resource_coordination

    start.wait()
    queue.put(resource_coordination.acquire(Path(root), "port", "8080", 30, "worker"))


def guard_holder_worker(root: str, ready: object, release: object) -> None:
    import resource_coordination

    runtime = resource_coordination.validate_runtime_root(Path(root))
    _, guard = resource_coordination._paths(runtime, "port", "7070")
    with resource_coordination._Guard(runtime, guard, 1.0):
        ready.set()
        release.wait(10)


def crash_during_guard_publish_worker(root: str) -> None:
    import resource_coordination

    runtime = resource_coordination.validate_runtime_root(Path(root))
    _, guard = resource_coordination._paths(runtime, "port", "6060")
    descriptor = os.open(guard, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(descriptor)
    os._exit(0)


class ResourceLeaseTests(unittest.TestCase):
    def test_public_cli_acquire_inspect_release_round_trip(self) -> None:
        flow = ROOT / "skills" / "dev-flow" / "scripts" / "dev-flow.py"
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary) / "runtime"
            acquire_result = subprocess.run(
                [sys.executable, str(flow), "resource-lease", "--runtime-root", str(runtime), "acquire", "--kind", "device", "--resource", "synthetic-1", "--ttl-seconds", "30"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            acquired = json.loads(acquire_result.stdout)
            self.assertEqual(acquire_result.returncode, 0, acquired)
            inspected = subprocess.run(
                [sys.executable, str(flow), "resource-lease", "--runtime-root", str(runtime), "inspect", "--kind", "device", "--resource", "synthetic-1"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(json.loads(inspected.stdout)["status"], "leased")
            released = subprocess.run(
                [sys.executable, str(flow), "resource-lease", "--runtime-root", str(runtime), "release", "--kind", "device", "--resource", "synthetic-1", "--token", acquired["token"]],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                released.returncode,
                0,
                f"release failed with return code {released.returncode}: {released.stderr or released.stdout}",
            )
            self.assertEqual(json.loads(released.stdout)["status"], "released")

    def test_cli_exit_status_never_turns_conflict_or_expiry_into_success(self) -> None:
        flow = ROOT / "skills" / "dev-flow" / "scripts" / "dev-flow.py"
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary) / "runtime"
            acquired = subprocess.run(
                [sys.executable, str(flow), "resource-lease", "--runtime-root", str(runtime), "acquire", "--kind", "port", "--resource", "9091", "--ttl-seconds", "30"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(acquired.returncode, 0, acquired.stderr or acquired.stdout)
            conflict = subprocess.run(
                [sys.executable, str(flow), "resource-lease", "--runtime-root", str(runtime), "acquire", "--kind", "port", "--resource", "9091", "--ttl-seconds", "30"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(json.loads(conflict.stdout)["status"], "conflict")
            self.assertNotEqual(conflict.returncode, 0)
            forbidden = subprocess.run(
                [sys.executable, str(flow), "resource-lease", "--runtime-root", str(runtime), "renew", "--kind", "port", "--resource", "9091", "--ttl-seconds", "30", "--token", "wrong"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(json.loads(forbidden.stdout)["status"], "forbidden")
            self.assertNotEqual(forbidden.returncode, 0)

    def test_concurrent_acquire_has_one_winner_and_no_raw_values_at_rest(self) -> None:
        import resource_coordination

        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary) / "runtime"
            context = mp.get_context("fork" if os.name != "nt" else "spawn")
            start = context.Event()
            queue = context.Queue()
            processes = [context.Process(target=acquire_worker, args=(str(runtime), start, queue)) for _ in range(12)]
            for process in processes:
                process.start()
            start.set()
            for process in processes:
                process.join(10)
            results = [queue.get(timeout=2) for _ in processes]
            self.assertEqual(sum(item["status"] in {"acquired", "expired-recovered"} for item in results), 1)
            self.assertEqual(sum(item["status"] == "conflict" for item in results), 11)
            stored = "".join(path.read_text(encoding="utf-8") for path in runtime.glob("*.json"))
            self.assertNotIn("8080", stored)
            self.assertNotIn("worker", stored)
            winner = next(item for item in results if item["status"] in {"acquired", "expired-recovered"})
            self.assertNotIn(winner["token"], stored)
            inspected = resource_coordination.inspect(runtime, "port", "8080")
            self.assertNotIn("token", inspected)

    def test_wrong_token_cannot_renew_or_release_and_expiry_recovers(self) -> None:
        import resource_coordination

        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary) / "runtime"
            first = resource_coordination.acquire(runtime, "simulator", "ios-1", 10, "owner", now=100.0)
            self.assertEqual(first["status"], "acquired")
            self.assertEqual(resource_coordination.renew(runtime, "simulator", "ios-1", "wrong", 10, now=101.0)["status"], "forbidden")
            self.assertEqual(resource_coordination.release(runtime, "simulator", "ios-1", "wrong", now=101.0)["status"], "forbidden")
            recovered = resource_coordination.acquire(runtime, "simulator", "ios-1", 10, "new", now=111.0)
            self.assertEqual(recovered["status"], "expired-recovered")
            self.assertGreater(recovered["generation"], first["generation"])

    def test_corruption_and_clock_rollback_fail_closed(self) -> None:
        import resource_coordination

        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary) / "runtime"
            acquired = resource_coordination.acquire(runtime, "build-cache", "main", 10, "owner", now=100.0)
            self.assertEqual(acquired["status"], "acquired")
            rollback = resource_coordination.renew(runtime, "build-cache", "main", acquired["token"], 10, now=99.0)
            self.assertEqual(rollback["status"], "unavailable")
            state = next(runtime.glob("*.json"))
            state.write_text("{}", encoding="utf-8")
            corrupt = resource_coordination.inspect(runtime, "build-cache", "main", now=101.0)
            self.assertEqual(corrupt["status"], "unavailable")

    def test_stale_guard_record_is_reused_under_one_os_lock(self) -> None:
        import resource_coordination

        with tempfile.TemporaryDirectory() as temporary:
            runtime = resource_coordination.validate_runtime_root(Path(temporary) / "runtime")
            _, guard = resource_coordination._paths(runtime, "port", "9090")
            guard.write_text(
                json.dumps(
                    {
                        "schema": resource_coordination.SCHEMA,
                        "created_at": 1.0,
                        "nonce": "0" * 32,
                    }
                ),
                encoding="utf-8",
            )
            guard.chmod(0o600)
            barrier = threading.Barrier(8)
            results: list[dict[str, object]] = []

            def contender() -> None:
                barrier.wait()
                results.append(
                    resource_coordination.acquire(
                        runtime, "port", "9090", 30, "worker", now=100.0
                    )
                )

            threads = [threading.Thread(target=contender) for _ in range(8)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(5)
            self.assertEqual(sum(item["status"] == "acquired" for item in results), 1)
            self.assertEqual(sum(item["status"] == "conflict" for item in results), 7)
            self.assertTrue(guard.exists())
            metadata = json.loads(guard.read_text(encoding="utf-8"))
            self.assertEqual(metadata["schema"], resource_coordination.SCHEMA)

    def test_live_guard_cannot_be_stolen_by_a_far_future_contender(self) -> None:
        import resource_coordination

        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary) / "runtime"
            context = mp.get_context("fork" if os.name != "nt" else "spawn")
            ready = context.Event()
            release = context.Event()
            holder = context.Process(
                target=guard_holder_worker, args=(str(runtime), ready, release)
            )
            holder.start()
            self.assertTrue(ready.wait(5))
            contender = resource_coordination.acquire(
                runtime, "port", "7070", 30, "contender", now=10**9
            )
            release.set()
            holder.join(5)
            self.assertEqual(contender["status"], "conflict")
            self.assertEqual(holder.exitcode, 0)

    def test_crash_before_guard_json_does_not_block_future_transition(self) -> None:
        import resource_coordination

        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary) / "runtime"
            context = mp.get_context("fork" if os.name != "nt" else "spawn")
            crashed = context.Process(
                target=crash_during_guard_publish_worker, args=(str(runtime),)
            )
            crashed.start()
            crashed.join(5)
            self.assertEqual(crashed.exitcode, 0)
            recovered = resource_coordination.acquire(
                runtime, "port", "6060", 30, "next", now=100.0
            )
            self.assertEqual(recovered["status"], "acquired")

    def test_preflight_never_invents_budget_and_cleans_probe(self) -> None:
        import resource_coordination

        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            observed = resource_coordination.preflight(target, None, None, True)
            self.assertEqual(observed["status"], "observed")
            self.assertEqual(list(target.iterdir()), [])
            passed = resource_coordination.preflight(target, 0, 0, False)
            self.assertEqual(passed["status"], "passed")
            blocked = resource_coordination.preflight(target, 2**63, 0, False)
            self.assertEqual(blocked["status"], "blocked")

    def test_inputs_are_bounded_and_runtime_root_is_not_cwd(self) -> None:
        import resource_coordination

        self.assertEqual(
            resource_coordination.acquire(Path.cwd(), "port", "1", 10, "owner")["status"],
            "unavailable",
        )
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(resource_coordination.ResourceInputError):
                resource_coordination.acquire(Path(temporary) / "r", "unknown", "1", 10, "owner")
            with self.assertRaises(resource_coordination.ResourceInputError):
                resource_coordination.acquire(Path(temporary) / "r", "port", "x" * 300, 10, "owner")
            with self.assertRaises(resource_coordination.ResourceInputError):
                resource_coordination.acquire(Path(temporary) / "r", "port", "1", 10, "owner", now=float("nan"))

    def test_allowlist_and_cli_invalid_status_match_public_contract(self) -> None:
        import resource_coordination

        self.assertEqual(
            resource_coordination.KINDS,
            {"build-cache", "container", "device", "disk", "emulator", "port", "simulator"},
        )
        flow = ROOT / "skills" / "dev-flow" / "scripts" / "dev-flow.py"
        result = subprocess.run(
            [
                sys.executable,
                str(flow),
                "resource-lease",
                "acquire",
                "--kind",
                "unknown",
                "--resource",
                "1",
                "--ttl-seconds",
                "10",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["status"], "invalid")

    def test_unsafe_runtime_roots_fail_closed(self) -> None:
        import resource_coordination

        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            target = base / "target"
            target.mkdir()
            link = base / "link"
            link.symlink_to(target, target_is_directory=True)
            self.assertEqual(
                resource_coordination.acquire(link, "port", "1", 10, "owner")["status"],
                "unavailable",
            )
            with mock.patch.object(resource_coordination, "_filesystem_type", return_value="network"):
                self.assertEqual(
                    resource_coordination.acquire(base / "network", "port", "1", 10, "owner")["status"],
                    "unavailable",
                )

    def test_corrupt_identity_and_non_finite_timestamps_fail_closed(self) -> None:
        import resource_coordination

        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary) / "runtime"
            acquired = resource_coordination.acquire(runtime, "device", "phone", 10, "owner", now=10.0)
            self.assertEqual(acquired["status"], "acquired")
            state = next(runtime.glob("*.json"))
            payload = json.loads(state.read_text(encoding="utf-8"))
            payload["token_digest"] = 4
            state.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(resource_coordination.inspect(runtime, "device", "phone", now=11.0)["status"], "unavailable")
            payload["token_digest"] = resource_coordination._digest(acquired["token"])
            payload["renewed_at"] = float("nan")
            state.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(resource_coordination.inspect(runtime, "device", "phone", now=11.0)["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
