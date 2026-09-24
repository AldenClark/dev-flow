from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "dev-flow" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import engineering_context as ec  # noqa: E402


FLOW = SCRIPTS / "dev-flow.py"
PROFILE_TOOL = ROOT / "skills" / "manage-engineering-profiles" / "scripts" / "profile-tool.py"
BASELINE = ROOT / "skills" / "dev-flow" / "references" / "neutral-baseline.toml"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=False, capture_output=True, text=True)


def profile_text(
    profile_id: str,
    layer: str,
    key: str,
    value: str,
    *,
    strength: str = "should",
    applies_when: tuple[str, ...] = (),
    exception_id: str | None = None,
) -> str:
    selectors = ""
    if applies_when:
        rendered = ", ".join(json.dumps(item) for item in applies_when)
        selectors = f"applies_when = [{rendered}]\n"
    exception = f'exception_id = "{exception_id}"\n' if exception_id else ""
    governance = '''provenance = "explicit-user"
scope = ["**"]
expires_at = "2999-01-01T00:00:00Z"
correction_policy = "edit-or-retire-profile"
deletion_policy = "delete-profile-file"
''' if layer == "personal" else ""
    return f'''schema_version = "1.0"
id = "{profile_id}"
layer = "{layer}"
owner = "test-owner"
version = "1.0"
status = "active"
{governance}

[[preferences]]
key = "{key}"
kind = "preference"
strength = "{strength}"
value = "{value}"
{selectors}{exception}rationale = "test rationale"
alternatives = ["other"]
exception_policy = "record-reason"
review_trigger = "test-change"
'''


class ProfileContractTests(unittest.TestCase):
    def test_personal_scaffold_requires_and_projects_explicit_governance(self) -> None:
        missing = run(
            sys.executable,
            str(PROFILE_TOOL),
            "scaffold",
            "--id",
            "personal.example",
            "--layer",
            "personal",
            "--owner",
            "owner",
        )
        self.assertEqual(missing.returncode, 2)
        self.assertIn("explicit --scope and --expires-at", missing.stdout)

        proposed = run(
            sys.executable,
            str(PROFILE_TOOL),
            "scaffold",
            "--id",
            "personal.example",
            "--layer",
            "personal",
            "--owner",
            "owner",
            "--scope",
            "src/**",
            "--expires-at",
            "2999-01-01T00:00:00Z",
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr or proposed.stdout)
        payload = json.loads(proposed.stdout)
        self.assertEqual(payload["status"], "proposal")
        self.assertIn('provenance = "explicit-user"', payload["content"])
        self.assertIn('scope = ["src/**"]', payload["content"])
        self.assertIn('deletion_policy = "delete-profile-file"', payload["content"])

    def test_personal_profile_rejects_inferred_or_expired_persistence(self) -> None:
        inferred = ec.tomllib.loads(
            profile_text("personal.inferred", "personal", "ui.density", "compact").replace(
                'provenance = "explicit-user"', 'provenance = "inferred-from-history"'
            )
        )
        self.assertTrue(any("inferred or imported" in item for item in ec.validate_profile_data(inferred)))

        expired = ec.tomllib.loads(
            profile_text("personal.expired", "personal", "ui.density", "compact").replace(
                '2999-01-01T00:00:00Z', '2020-01-01T00:00:00Z'
            )
        )
        self.assertTrue(any("future timezone-aware" in item for item in ec.validate_profile_data(expired)))

    def test_personal_profile_scope_and_provenance_survive_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            codex_home = root / "codex"
            personal = codex_home / "dev-flow" / "profiles"
            personal.mkdir(parents=True)
            text_value = profile_text("personal.scoped", "personal", "ui.density", "compact").replace(
                'scope = ["**"]', 'scope = ["src/**"]'
            )
            (personal / "scoped.toml").write_text(text_value, encoding="utf-8")
            outside = ec.resolve_profiles(
                root, baseline=BASELINE, codex_home=codex_home, task_paths=["docs/readme.md"]
            )
            inside = ec.resolve_profiles(
                root, baseline=BASELINE, codex_home=codex_home, task_paths=["src/app.py"]
            )
            self.assertNotIn("ui.density", {item["key"] for item in outside["winners"]})
            winner = next(item for item in inside["winners"] if item["key"] == "ui.density")
            self.assertEqual(winner["provenance"], "explicit-user")
            self.assertEqual(winner["profile_scope"], ["src/**"])

    def test_repository_profile_cannot_self_assert_personal_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = root / ".dev-flow" / "profiles"
            profiles.mkdir(parents=True)
            spoofed = profile_text(
                "project.spoofed", "project", "ui.density", "compact"
            ).replace('status = "active"', 'status = "active"\nprovenance = "explicit-user"')
            (profiles / "project.toml").write_text(spoofed, encoding="utf-8")
            snapshot = ec.resolve_profiles(
                root, baseline=BASELINE, codex_home=root / "codex"
            )
        source = next(item for item in snapshot["sources"] if item["id"] == "project.spoofed")
        winner = next(item for item in snapshot["winners"] if item["key"] == "ui.density")
        self.assertEqual(source["provenance"], "repository-implicit")
        self.assertEqual(winner["provenance"], "repository-implicit")

    def test_implicit_project_profile_rejects_symlink_outside_dev_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = root / ".dev-flow" / "profiles"
            profiles.mkdir(parents=True)
            outside = root / "outside.toml"
            outside.write_text(
                profile_text("project.outside", "project", "security.mode", "relaxed"),
                encoding="utf-8",
            )
            try:
                (profiles / "project.toml").symlink_to(outside)
            except OSError as exc:
                self.skipTest(f"symlinks are unavailable: {exc}")
            snapshot = ec.resolve_profiles(root, baseline=BASELINE, codex_home=root / "codex")
            self.assertNotIn("security.mode", {item["key"] for item in snapshot["winners"]})
            self.assertTrue(any("must not traverse a symlink" in item for item in snapshot["errors"]))

    def test_no_optional_profile_resolves_neutral_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            snapshot = ec.resolve_profiles(root, baseline=BASELINE, codex_home=root / "codex")
            self.assertEqual(snapshot["outcome"], "resolved")
            self.assertFalse(snapshot["conflicts"])
            self.assertIn("engineering.repository-evidence-first", {item["key"] for item in snapshot["winners"]})

    def test_language_selector_prevents_cross_language_leakage(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            codex_home = root / "codex"
            personal = codex_home / "dev-flow" / "profiles"
            personal.mkdir(parents=True)
            (personal / "rust.toml").write_text(
                profile_text("personal.rust", "personal", "rust.time.library", "jiff", applies_when=("language=rust",)),
                encoding="utf-8",
            )
            typescript = ec.resolve_profiles(root, baseline=BASELINE, codex_home=codex_home, facts=["language=typescript"])
            rust = ec.resolve_profiles(root, baseline=BASELINE, codex_home=codex_home, facts=["language=rust"])
            self.assertNotIn("rust.time.library", {item["key"] for item in typescript["winners"]})
            self.assertEqual(next(item["value"] for item in rust["winners"] if item["key"] == "rust.time.library"), "jiff")

    def test_team_overrides_personal_should(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            codex_home = root / "codex"
            personal = codex_home / "dev-flow" / "profiles"
            personal.mkdir(parents=True)
            (personal / "default.toml").write_text(profile_text("personal.default", "personal", "ui.density", "compact"), encoding="utf-8")
            profile_dir = root / ".dev-flow" / "profiles"
            profile_dir.mkdir(parents=True)
            (profile_dir / "team.toml").write_text(profile_text("team.shared", "team", "ui.density", "comfortable"), encoding="utf-8")
            (root / ".dev-flow" / "preferences.toml").write_text(
                '''schema_version = "1.0"
include_personal = true

[[profile_sources]]
id = "team.shared"
path = "profiles/team.toml"
layer = "team"
scope = ["**"]
required = true
''',
                encoding="utf-8",
            )
            snapshot = ec.resolve_profiles(root, baseline=BASELINE, codex_home=codex_home, task_paths=["src/app.ts"])
            winner = next(item for item in snapshot["winners"] if item["key"] == "ui.density")
            self.assertEqual((winner["value"], winner["layer"]), ("comfortable", "team"))

    def test_reproducible_modes_exclude_personal_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            codex_home = root / "codex"
            personal = codex_home / "dev-flow" / "profiles"
            personal.mkdir(parents=True)
            (personal / "default.toml").write_text(
                profile_text("personal.default", "personal", "ui.density", "compact"), encoding="utf-8"
            )
            interactive = ec.resolve_profiles(root, baseline=BASELINE, codex_home=codex_home)
            team = ec.resolve_profiles(
                root, baseline=BASELINE, codex_home=codex_home, profile_mode="team-reproducible"
            )
            ci = ec.resolve_profiles(root, baseline=BASELINE, codex_home=codex_home, profile_mode="ci")
            self.assertIn("ui.density", {item["key"] for item in interactive["winners"]})
            self.assertNotIn("ui.density", {item["key"] for item in team["winners"]})
            self.assertNotIn("ui.density", {item["key"] for item in ci["winners"]})
            self.assertEqual(team["profile_mode"], "team-reproducible")

    def test_unexcepted_must_conflict_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            codex_home = root / "codex"
            personal = codex_home / "dev-flow" / "profiles"
            personal.mkdir(parents=True)
            (personal / "must.toml").write_text(
                profile_text("personal.must", "personal", "security.mode", "strict", strength="must"), encoding="utf-8"
            )
            profile_dir = root / ".dev-flow" / "profiles"
            profile_dir.mkdir(parents=True)
            (profile_dir / "project.toml").write_text(
                profile_text("project.default", "project", "security.mode", "relaxed"), encoding="utf-8"
            )
            snapshot = ec.resolve_profiles(root, baseline=BASELINE, codex_home=codex_home)
            self.assertEqual(snapshot["outcome"], "blocked")
            self.assertEqual(snapshot["conflicts"][0]["key"], "security.mode")

    def test_authorized_scoped_exception_can_override_lower_must(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            codex_home = root / "codex"
            personal = codex_home / "dev-flow" / "profiles"
            personal.mkdir(parents=True)
            (personal / "must.toml").write_text(profile_text("personal.must", "personal", "security.mode", "strict", strength="must"), encoding="utf-8")
            profiles = root / ".dev-flow" / "profiles"
            decisions = root / ".dev-flow" / "decisions"
            profiles.mkdir(parents=True)
            decisions.mkdir()
            (profiles / "project.toml").write_text(profile_text("project.default", "project", "security.mode", "relaxed", exception_id="PREF-1"), encoding="utf-8")
            (decisions / "PREF-1.json").write_text(json.dumps({"schema_version": "1.0", "id": "PREF-1", "status": "active", "approved_by": "owner", "keys": ["security.mode"], "scope": ["src/**"], "reason": "bounded project exception", "residual_risk": "reduced local strictness", "expires_at": "2999-01-01T00:00:00Z"}), encoding="utf-8")
            snapshot = ec.resolve_profiles(root, baseline=BASELINE, codex_home=codex_home, task_paths=["src/app.py"])
            self.assertEqual(snapshot["outcome"], "resolved")
            winner = next(item for item in snapshot["winners"] if item["key"] == "security.mode")
            self.assertEqual(winner["value"], "relaxed")

    def test_component_profile_applies_only_to_matching_task_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = root / ".dev-flow" / "profiles"
            profiles.mkdir(parents=True)
            (profiles / "frontend.toml").write_text(profile_text("component.frontend", "component", "component.model", "react"), encoding="utf-8")
            (root / ".dev-flow" / "preferences.toml").write_text('''schema_version = "1.0"
[[profile_sources]]
id = "component.frontend"
path = "profiles/frontend.toml"
layer = "component"
scope = ["frontend/**"]
''', encoding="utf-8")
            frontend = ec.resolve_profiles(root, baseline=BASELINE, codex_home=root / "codex", task_paths=["frontend/src/app.tsx"])
            frontend_directory = ec.resolve_profiles(root, baseline=BASELINE, codex_home=root / "codex", task_paths=["frontend"])
            backend = ec.resolve_profiles(root, baseline=BASELINE, codex_home=root / "codex", task_paths=["backend/src/app.rs"])
            self.assertIn("component.model", {item["key"] for item in frontend["winners"]})
            self.assertIn("component.model", {item["key"] for item in frontend_directory["winners"]})
            self.assertNotIn("component.model", {item["key"] for item in backend["winners"]})

    def test_same_layer_disagreement_blocks_instead_of_using_file_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = root / ".dev-flow" / "profiles"
            profiles.mkdir(parents=True)
            (profiles / "a.toml").write_text(profile_text("project.a", "project", "api.style", "a"), encoding="utf-8")
            (profiles / "b.toml").write_text(profile_text("project.b", "project", "api.style", "b"), encoding="utf-8")
            (root / ".dev-flow" / "preferences.toml").write_text(
                '''schema_version = "1.0"
[[profile_sources]]
id = "project.a"
path = "profiles/a.toml"
layer = "project"
[[profile_sources]]
id = "project.b"
path = "profiles/b.toml"
layer = "project"
''', encoding="utf-8")
            snapshot = ec.resolve_profiles(root, baseline=BASELINE, codex_home=root / "codex")
            self.assertEqual(snapshot["outcome"], "blocked")
            self.assertEqual(snapshot["conflicts"][0]["reason"], "same-layer disagreement")

    def test_manifest_cannot_escape_repository_policy_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".dev-flow").mkdir()
            (root / ".dev-flow" / "preferences.toml").write_text(
                '''schema_version = "1.0"
[[profile_sources]]
id = "escape"
path = "../outside.toml"
layer = "project"
''',
                encoding="utf-8",
            )
            snapshot = ec.resolve_profiles(root, baseline=BASELINE, codex_home=root / "codex")
            self.assertEqual(snapshot["outcome"], "blocked")
            self.assertTrue(any("escapes" in error for error in snapshot["errors"]))

    def test_symlinked_manifest_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            policy = root / ".dev-flow"
            policy.mkdir()
            outside = root / "outside.toml"
            outside.write_text('schema_version = "1.0"\n', encoding="utf-8")
            try:
                (policy / "preferences.toml").symlink_to(outside)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            snapshot = ec.resolve_profiles(root, baseline=BASELINE, codex_home=root / "codex")
            self.assertEqual(snapshot["outcome"], "blocked")
            self.assertTrue(any("must not be a symlink" in error for error in snapshot["errors"]))

    def test_resolution_fingerprint_is_deterministic_offline(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = ec.resolve_profiles(root, baseline=BASELINE, codex_home=root / "codex", facts=["language=rust"])
            second = ec.resolve_profiles(root, baseline=BASELINE, codex_home=root / "codex", facts=["language=rust"])
            self.assertEqual(first["fingerprint"], second["fingerprint"])

    def test_profile_tool_is_review_first(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "project.toml"
            proposal = run(
                sys.executable,
                str(PROFILE_TOOL),
                "scaffold",
                "--id",
                "project.sample",
                "--layer",
                "project",
                "--owner",
                "team",
                "--output",
                str(target),
            )
            self.assertEqual(proposal.returncode, 0, proposal.stderr or proposal.stdout)
            self.assertFalse(target.exists())
            written = run(
                sys.executable,
                str(PROFILE_TOOL),
                "scaffold",
                "--id",
                "project.sample",
                "--layer",
                "project",
                "--owner",
                "team",
                "--output",
                str(target),
                "--write",
            )
            self.assertEqual(written.returncode, 0, written.stderr or written.stdout)
            self.assertTrue(target.is_file())

    def test_manifest_scaffold_rejects_escaping_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = run(
                sys.executable,
                str(PROFILE_TOOL),
                "scaffold-manifest",
                "--root",
                temp,
                "--profile-path",
                "../outside.toml",
                "--profile-id",
                "project.sample",
                "--layer",
                "project",
            )
            self.assertEqual(result.returncode, 2)

    def test_packet_readiness_and_inert_suppression_are_not_exposed(self) -> None:
        self.assertFalse(hasattr(ec, "assess_context"))
        self.assertFalse(hasattr(ec, "select_packet_waiver"))
        self.assertFalse((SCRIPTS / "dependency_contracts.py").exists())
        help_result = run(sys.executable, str(PROFILE_TOOL), "--help")
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        self.assertNotIn("suppress", help_result.stdout)
        retired = run(sys.executable, str(PROFILE_TOOL), "suppress")
        self.assertEqual(retired.returncode, 2)


class RoutingTests(unittest.TestCase):
    def test_declared_routing_cases(self) -> None:
        cases = json.loads((ROOT / "evals" / "skill-routing-cases.json").read_text(encoding="utf-8"))["cases"]
        for case in cases:
            with self.subTest(case=case["id"]):
                result = run(sys.executable, str(FLOW), "route-task", *case["args"])
                self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
                payload = json.loads(result.stdout)
                ordered_routes = [item["skill"] for item in payload["routes"]]
                routes = set(ordered_routes)
                self.assertEqual(ordered_routes, case["expected"])
                self.assertEqual(payload["work_mode"], case["work_mode"])
                self.assertTrue(set(case["required"]) <= routes)
                self.assertFalse(set(case["forbidden"]) & routes)

    def test_risk_reroute_adds_specialists_without_changing_continuity_mode(self) -> None:
        initial = run(sys.executable, str(FLOW), "route-task", "--task-type", "routine")
        discovered = run(
            sys.executable,
            str(FLOW),
            "route-task",
            "--task-type",
            "routine",
            "--risk",
            "public-api",
        )
        self.assertEqual(initial.returncode, 0, initial.stderr or initial.stdout)
        self.assertEqual(discovered.returncode, 0, discovered.stderr or discovered.stdout)
        initial_payload = json.loads(initial.stdout)
        discovered_payload = json.loads(discovered.stdout)
        initial_routes = {item["skill"] for item in initial_payload["routes"]}
        discovered_routes = {item["skill"] for item in discovered_payload["routes"]}
        self.assertEqual(initial_payload["work_mode"], "direct")
        self.assertEqual(discovered_payload["work_mode"], "direct")
        self.assertNotIn("requirements-design", initial_routes)
        self.assertEqual(discovered_routes - initial_routes, {"architecture-decisions"})
        control_plane = (ROOT / "skills" / "dev-flow" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Reconsider routing only when intent, semantics, scope, platform, authority, principal risk", control_plane)
        self.assertIn("quality-calibration.md", control_plane)
        lifecycle = (
            ROOT / "skills" / "dev-flow" / "references" / "core-lifecycle.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Escalation adds the specific missing control", lifecycle)

    def test_routing_fixture_covers_specialist_owners_without_artifact_protocol(self) -> None:
        routing = json.loads(
            (ROOT / "evals" / "skill-routing-cases.json").read_text(encoding="utf-8")
        )
        self.assertEqual(routing["schema_version"], "2.0")
        self.assertTrue(all("workflow" not in case for case in routing["cases"]))
        expected = {
            skill
            for case in routing["cases"]
            for skill in case["expected"]
        }
        self.assertTrue(
            {
                "repo-context",
                "requirements-design",
                "product-ux-discovery",
                "architecture-decisions",
                "systematic-debugging",
                "dependency-decisions",
                "verification",
                "change-review",
                "delivery-readiness",
            }
            <= expected
        )


if __name__ == "__main__":
    unittest.main()
