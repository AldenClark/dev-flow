from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "skills" / "dependency-decisions" / "scripts" / "snapshot-tool.py"
EXAMPLE = ROOT / "skills" / "dependency-decisions" / "references" / "ecosystem-snapshot.example.json"


class EcosystemSnapshotTests(unittest.TestCase):
    def test_refresh_required_example_cannot_support_a_recommendation(self) -> None:
        result = subprocess.run([sys.executable, str(TOOL), "validate", str(EXAMPLE), "--as-of", "2026-08-09T00:00:00Z"], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["status"], "refresh-required")

    def test_current_snapshot_expires_by_observation_volatility(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            snapshot = Path(temp) / "snapshot.json"
            data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
            data.update({"id": "test.current", "checked_at": "2026-01-01T00:00:00Z", "status": "current"})
            data["observations"][0].update({"sources": ["https://primary.example/release"], "volatility": "high"})
            snapshot.write_text(json.dumps(data), encoding="utf-8")
            fresh = subprocess.run([sys.executable, str(TOOL), "validate", str(snapshot), "--as-of", "2026-01-15T00:00:00Z"], capture_output=True, text=True, check=False)
            stale = subprocess.run([sys.executable, str(TOOL), "validate", str(snapshot), "--as-of", "2026-03-15T00:00:00Z"], capture_output=True, text=True, check=False)
            self.assertEqual((fresh.returncode, json.loads(fresh.stdout)["status"]), (0, "current"))
            self.assertEqual((stale.returncode, json.loads(stale.stdout)["status"]), (2, "stale"))
            self.assertTrue(json.loads(stale.stdout)["stale_observations"][0]["fallback"])


if __name__ == "__main__":
    unittest.main()
