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
CAPABILITIES = ROOT / "skills" / "dev-flow-maintainer" / "references" / "capability-registry.json"


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


def quality_profile_text(capability_id: str, fallback: str | None) -> str:
    fallback_line = f'fallbacks = ["{fallback}"]\n' if fallback else ""
    return f'''schema_version = "1.0"
id = "project.quality"
layer = "project"
owner = "test-owner"
version = "1.0"
status = "active"

[[preferences]]
key = "quality.test"
kind = "quality-policy"
strength = "must"
outcome = "The applicable outcome receives qualified review."
required_capabilities = ["{capability_id}"]
{fallback_line}required_evidence = ["security-owner-check"]
rationale = "The repository owner accepted this bounded fallback."
exception_policy = "record-owner-waiver"
review_trigger = "capability-or-scope-change"
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


class ReadinessTests(unittest.TestCase):
    def test_explicit_tier_cannot_downgrade_governed_security_work(self) -> None:
        selected, reasons = ec.select_tier("security", {"security"}, "T0")
        self.assertEqual(selected, "T3")
        self.assertIn("explicit-tier-raised-to-minimum", reasons)

    def test_t0_has_no_setup_reminder(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = ec.assess_context(
                root,
                task_type="spike",
                codex_home=root / "codex",
                capability_registry=CAPABILITIES,
            )
            self.assertEqual((result["tier"], result["outcome"]), ("T0", "not_applicable"))
            self.assertFalse(result["recommendations"])

    def test_t0_does_not_turn_optional_profile_conflict_into_a_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            codex_home = root / "codex"
            personal = codex_home / "dev-flow" / "profiles"
            personal.mkdir(parents=True)
            (personal / "must.toml").write_text(profile_text("personal.must", "personal", "security.mode", "strict", strength="must"), encoding="utf-8")
            profiles = root / ".dev-flow" / "profiles"
            profiles.mkdir(parents=True)
            (profiles / "project.toml").write_text(profile_text("project.default", "project", "security.mode", "relaxed"), encoding="utf-8")
            result = ec.assess_context(root, task_type="spike", codex_home=codex_home, capability_registry=CAPABILITIES)
            self.assertEqual(result["outcome"], "not_applicable")
            self.assertFalse(result["blockers"])
            self.assertTrue(result["conflicts"])

    def test_missing_agents_never_blocks_complete_t1_native_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "pyproject.toml").write_text("[project]\nname='sample'\nversion='0.1.0'\n", encoding="utf-8")
            tests = root / "tests"
            tests.mkdir()
            (tests / "test_app.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
            result = ec.assess_context(
                root,
                task_type="routine",
                codex_home=root / "codex",
                capability_registry=CAPABILITIES,
            )
            self.assertNotEqual(result["outcome"], "blocked")
            instruction = next(item for item in result["checks"] if item["dimension"] == "instructions")
            self.assertEqual(instruction["status"], "absent-optional")

    def test_agents_discovery_preserves_global_root_nested_and_override_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            codex_home = root / "codex"
            codex_home.mkdir()
            (codex_home / "AGENTS.md").write_text("global\n", encoding="utf-8")
            (root / "AGENTS.md").write_text("root\n", encoding="utf-8")
            nested = root / "src" / "feature"
            nested.mkdir(parents=True)
            (root / "src" / "AGENTS.md").write_text("nested\n", encoding="utf-8")
            (root / "src" / "AGENTS.override.md").write_text("override\n", encoding="utf-8")
            instructions = ec.discover_agent_instructions(root, codex_home=codex_home, working_directory=nested)
            paths = {item["path"] for item in instructions}
            self.assertIn(str((codex_home / "AGENTS.md").resolve()), paths)
            self.assertIn(str((root / "AGENTS.md").resolve()), paths)
            self.assertIn(str((root / "src" / "AGENTS.override.md").resolve()), paths)
            self.assertNotIn(str((root / "src" / "AGENTS.md").resolve()), paths)

    def test_codex_instruction_fallback_empty_skip_and_byte_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            codex_home = root / "codex"
            codex_home.mkdir()
            (codex_home / "AGENTS.override.md").write_text("\n", encoding="utf-8")
            (codex_home / "AGENTS.md").write_text("global\n", encoding="utf-8")
            (codex_home / "config.toml").write_text(
                'project_doc_fallback_filenames = ["TEAM.md"]\nproject_doc_max_bytes = 12\n', encoding="utf-8"
            )
            (root / "AGENTS.md").write_text("", encoding="utf-8")
            (root / "TEAM.md").write_text("root\n", encoding="utf-8")
            nested = root / "src"
            nested.mkdir()
            (nested / "AGENTS.md").write_text("nested-long\n", encoding="utf-8")
            adapter = ec.CodexHostAdapter(root, codex_home=codex_home, working_directory=nested)
            instructions = adapter.instruction_chain()
            self.assertEqual([Path(item["path"]).name for item in instructions], ["AGENTS.md", "TEAM.md"])
            self.assertTrue(any("budget exhausted" in item for item in adapter.errors))

    def test_codex_instruction_fallback_cannot_escape_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "repo"
            root.mkdir()
            codex_home = root / "codex"
            codex_home.mkdir()
            (codex_home / "config.toml").write_text(
                'project_doc_fallback_filenames = ["../outside.md"]\n', encoding="utf-8"
            )
            (workspace / "outside.md").write_text("outside\n", encoding="utf-8")
            adapter = ec.CodexHostAdapter(root, codex_home=codex_home)
            self.assertFalse(adapter.instruction_chain())
            self.assertTrue(any("only non-empty filenames" in item for item in adapter.errors))

    def test_codex_skill_roots_include_repo_user_system_and_legacy_locations(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            nested = root / "src"
            nested.mkdir()
            codex_home = root / "codex"
            roots = ec.CodexHostAdapter(root, codex_home=codex_home, working_directory=nested).skill_roots()
            rendered = {str(item) for item in roots}
            self.assertIn(str((codex_home / "skills").resolve()), rendered)
            self.assertIn(str((root / ".agents" / "skills").resolve()), rendered)
            self.assertIn(str((nested / ".agents" / "skills").resolve()), rendered)
            self.assertIn(str((Path.home() / ".agents" / "skills").resolve()), rendered)
            self.assertIn(str(Path("/etc/codex/skills").resolve()), rendered)

    def test_codex_plugin_skill_root_is_discovered_only_from_bounded_cache_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            codex_home = Path(temp) / "codex"
            plugin_skills = codex_home / "plugins" / "cache" / "sample-plugin" / "sample-package" / "2.4.1" / "skills"
            skill = plugin_skills / "sample-review"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: sample-review\ndescription: bounded plugin candidate\n---\n# Review\n",
                encoding="utf-8",
            )
            adapter = ec.CodexHostAdapter(root, codex_home=codex_home)
            records = adapter.skill_root_records()
            plugin = next(item for item in records if item["provenance"] == "codex-plugin-cache")
            self.assertEqual(plugin["path"], plugin_skills.resolve())
            self.assertEqual((plugin["namespace"], plugin["package"], plugin["version"]), ("sample-plugin", "sample-package", "2.4.1"))
            candidate = next(item for item in ec.discover_skills(records) if item["name"] == "sample-review")
            self.assertEqual((candidate["root_provenance"], candidate["version"]), ("codex-plugin-cache", "2.4.1"))

    def test_same_name_skill_collision_requires_unique_admission_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            codex_home = Path(temp) / "codex"
            first = codex_home / "skills" / "review-a"
            second = codex_home / "plugins" / "cache" / "plugin-a" / "package-a" / "1.0.0" / "skills" / "review-a"
            for path, marker in ((first, "first"), (second, "second")):
                path.mkdir(parents=True)
                (path / "SKILL.md").write_text(
                    f"---\nname: review-a\ndescription: {marker}\n---\n# {marker}\n",
                    encoding="utf-8",
                )
            registry = root / "registry.json"
            registry.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "capabilities": [
                            {
                                "id": "quality.test",
                                "outcome": "test outcome",
                                "selectors": [],
                                "native_evidence": [],
                                "route_names": ["review-a"],
                                "manual_fallback": "manual-review",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            admission_dir = codex_home / "dev-flow"
            admission_dir.mkdir(parents=True)
            admission = {
                "skill": "review-a",
                "capability_ids": ["quality.test"],
                "status": "approved",
                "owner": "user",
                "reviewed_at": "2026-08-13T00:00:00Z",
                "recheck_trigger": "digest-change",
            }
            admission_file = admission_dir / "capabilities.json"
            admission_file.write_text(
                json.dumps({"schema_version": "1.0", "host": "codex", "admissions": [admission]}),
                encoding="utf-8",
            )
            ambiguous = ec.assess_context(
                root,
                task_type="routine",
                codex_home=codex_home,
                capability_registry=registry,
                detail="full",
            )
            route = ambiguous["quality_coverage"]["routes"][0]
            self.assertEqual((route["status"], route["candidate_count"], route["candidate_bound"]), ("conflicting", 2, False))
            self.assertIsNone(ambiguous["quality_coverage"]["obligations"][0]["selected_route"])
            self.assertIn("review-a", {item["name"] for item in ambiguous["skill_catalog"]["collisions"]})

            admission["digest"] = ec.sha256_file(first / "SKILL.md")
            admission_file.write_text(
                json.dumps({"schema_version": "1.0", "host": "codex", "admissions": [admission]}),
                encoding="utf-8",
            )
            bound = ec.assess_context(
                root,
                task_type="routine",
                codex_home=codex_home,
                capability_registry=registry,
                detail="full",
            )
            selected = bound["quality_coverage"]["obligations"][0]["selected_route"]
            self.assertEqual(selected["path"], str(first.resolve()))
            self.assertTrue(bound["quality_coverage"]["skill_name_collisions"][0]["resolved_by_admission_binding"])

    def test_unobserved_plugin_route_is_not_reported_as_uninstalled(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            registry = root / "registry.json"
            registry.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "capabilities": [
                            {
                                "id": "quality.plugin",
                                "outcome": "plugin-neutral outcome",
                                "selectors": [],
                                "native_evidence": [],
                                "route_names": ["plugin-review"],
                                "manual_fallback": "qualified-manual-review",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            result = ec.assess_context(
                root,
                task_type="routine",
                codex_home=root / "codex",
                capability_registry=registry,
                detail="full",
            )
            route = result["quality_coverage"]["routes"][0]
            self.assertEqual(route["status"], "not-observed")
            self.assertFalse(route["observed"])
            self.assertIsNone(route["installed"])
            self.assertNotIn("missing", route["status"])

    def test_artifact_facts_and_skill_digest_are_bound_into_context_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            source = root / "backend" / "api.py"
            source.parent.mkdir(parents=True)
            source.write_text("VALUE = 1\n", encoding="utf-8")
            (root / "pyproject.toml").write_text(
                "[project]\nname='sample'\nversion='0.1.0'\nrequires-python='>=3.12'\n",
                encoding="utf-8",
            )
            codex_home = Path(temp) / "codex"
            skill = codex_home / "skills" / "local-review"
            skill.mkdir(parents=True)
            skill_file = skill / "SKILL.md"
            skill_file.write_text(
                "---\nname: local-review\ndescription: first\n---\n# Review\n",
                encoding="utf-8",
            )
            first = ec.assess_context(
                root,
                task_type="routine",
                task_paths=["backend/api.py"],
                facts=["phase=implementation", "boundary=public-interface"],
                risks=["concurrency"],
                codex_home=codex_home,
                capability_registry=CAPABILITIES,
            )
            artifact = first["scope"]["artifacts"][0]
            self.assertTrue(
                {"phase", "role", "boundary", "language", "framework", "version", "path", "component", "risk"}
                <= set(artifact)
            )
            self.assertEqual(artifact["language"], ["python"])
            self.assertEqual(artifact["component"], ["backend"])
            self.assertIn("python@>=3.12", artifact["version"])

            phase_changed = ec.assess_context(
                root,
                task_type="routine",
                task_paths=["backend/api.py"],
                facts=["phase=verification", "boundary=public-interface"],
                risks=["concurrency"],
                codex_home=codex_home,
                capability_registry=CAPABILITIES,
            )
            self.assertNotEqual(first["fingerprint"], phase_changed["fingerprint"])
            skill_file.write_text(
                "---\nname: local-review\ndescription: second\n---\n# Review\n",
                encoding="utf-8",
            )
            skill_changed = ec.assess_context(
                root,
                task_type="routine",
                task_paths=["backend/api.py"],
                facts=["phase=verification", "boundary=public-interface"],
                risks=["concurrency"],
                codex_home=codex_home,
                capability_registry=CAPABILITIES,
            )
            self.assertNotEqual(
                phase_changed["engineering_context_binding"]["skill_catalog_fingerprint"],
                skill_changed["engineering_context_binding"]["skill_catalog_fingerprint"],
            )

    def test_personal_skill_admission_does_not_satisfy_project_quality_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            codex_home = Path(temp) / "codex"
            skill = codex_home / "skills" / "review-a"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: review-a\ndescription: personal route\n---\n# Review\n",
                encoding="utf-8",
            )
            admission_dir = codex_home / "dev-flow"
            admission_dir.mkdir(parents=True)
            (admission_dir / "capabilities.json").write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "host": "codex",
                        "admissions": [
                            {
                                "skill": "review-a",
                                "capability_ids": ["quality.test"],
                                "status": "approved",
                                "owner": "user",
                                "reviewed_at": "2026-08-13T00:00:00Z",
                                "recheck_trigger": "digest-change",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            registry = root / "registry.json"
            registry.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "capabilities": [
                            {
                                "id": "quality.test",
                                "outcome": "shared quality outcome",
                                "selectors": [],
                                "native_evidence": [],
                                "route_names": ["review-a"],
                                "manual_fallback": "qualified-review",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            profiles = root / ".dev-flow" / "profiles"
            profiles.mkdir(parents=True)
            (profiles / "project.toml").write_text(
                '''schema_version = "1.0"
id = "project.quality"
layer = "project"
owner = "team"
version = "1.0"
status = "active"

[[preferences]]
key = "quality.shared"
kind = "quality-policy"
strength = "must"
outcome = "Shared work receives the required review outcome."
required_capabilities = ["quality.test"]
rationale = "A personal route is not team policy."
exception_policy = "team-owner-waiver"
review_trigger = "capability-or-authority-change"
''',
                encoding="utf-8",
            )
            result = ec.assess_context(
                root,
                task_type="routine",
                codex_home=codex_home,
                capability_registry=registry,
                detail="full",
            )
            obligation = result["quality_coverage"]["obligations"][0]
            policy = next(item for item in result["quality_coverage"]["policy_assessments"] if item["key"] == "quality.shared")
            self.assertEqual(obligation["coverage"], "approved-specialist")
            self.assertEqual(obligation["shared_policy_coverage"], "uncovered")
            self.assertEqual(policy["coverage"], "uncovered")
            self.assertIn("quality.test", policy["missing_capabilities"])

    def test_named_skill_absence_is_not_a_gap_when_native_outcome_is_covered(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "pyproject.toml").write_text("[project]\nname='sample'\nversion='0.1.0'\n", encoding="utf-8")
            registry = root / "registry.json"
            registry.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "capabilities": [
                            {
                                "id": "quality.native",
                                "outcome": "native outcome",
                                "selectors": [],
                                "native_evidence": ["pyproject.toml"],
                                "route_names": ["optional-review"],
                                "manual_fallback": "qualified-review",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            result = ec.assess_context(
                root,
                task_type="routine",
                codex_home=root / "codex",
                capability_registry=registry,
                detail="full",
            )
            obligation = result["quality_coverage"]["obligations"][0]
            route = result["quality_coverage"]["routes"][0]
            self.assertEqual(obligation["coverage"], "native-control")
            self.assertEqual(route["status"], "not-observed")
            self.assertFalse(result["quality_coverage"]["uncovered"])
            self.assertNotIn("governed-quality-outcome-uncovered", result["blockers"])

    def test_repository_tests_cover_obligation_outside_selected_task_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "src"
            tests = root / "tests"
            source.mkdir()
            tests.mkdir()
            (source / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            (tests / "test_app.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
            result = ec.assess_context(
                root,
                task_type="routine",
                task_paths=["src/app.py"],
                codex_home=root / "codex",
                capability_registry=CAPABILITIES,
                detail="full",
            )
            obligation = next(
                item for item in result["quality_coverage"]["obligations"] if item["id"] == "quality.verification.tests"
            )
            self.assertEqual(obligation["coverage"], "native-control")
            self.assertEqual(obligation["task_mapping"], "verification-required")
            self.assertTrue(obligation["native_evidence"])
            self.assertFalse(obligation["task_native_evidence"])

    def test_compact_readiness_is_default_and_full_retains_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            compact = ec.assess_context(root, task_type="routine", codex_home=root / "codex", capability_registry=CAPABILITIES)
            full = ec.assess_context(
                root, task_type="routine", codex_home=root / "codex", capability_registry=CAPABILITIES, detail="full"
            )
            self.assertEqual(compact["detail"], "compact")
            self.assertNotIn("profile_snapshot", compact)
            self.assertEqual(full["detail"], "full")
            self.assertIn("profile_snapshot", full)
            self.assertLess(len(json.dumps(compact)), len(json.dumps(full)))

    def test_t2_missing_native_operations_is_checkpoint_not_block(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = ec.assess_context(root, task_type="large-feature", codex_home=root / "codex", capability_registry=CAPABILITIES)
            self.assertEqual((result["tier"], result["outcome"]), ("T2", "checkpoint"))
            self.assertIn("native-operations", {item["id"] for item in result["recommendations"]})

    def test_baseline_security_policy_fallback_is_assessed_and_covers_the_gap(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "pyproject.toml").write_text("[project]\nname='sample'\nversion='0.1.0'\n", encoding="utf-8")
            tests = root / "tests"
            tests.mkdir()
            (tests / "test_auth.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
            result = ec.assess_context(
                root,
                task_type="security",
                risks=["security"],
                codex_home=root / "codex",
                capability_registry=CAPABILITIES,
                detail="full",
            )
            baseline = next(
                item for item in result["quality_coverage"]["policy_assessments"]
                if item["key"] == "quality.governed-security-review"
            )
            security = next(
                item for item in result["quality_coverage"]["obligations"]
                if item["id"] == "quality.security.review"
            )
            self.assertEqual((baseline["layer"], baseline["coverage"]), ("baseline", "owned-policy-fallback"))
            self.assertEqual(security["coverage"], "owned-policy-fallback")
            self.assertNotIn("governed-quality-outcome-uncovered", result["blockers"])

    def test_security_scanner_combines_with_baseline_contextual_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".semgrep.yml").write_text("rules: []\n", encoding="utf-8")
            result = ec.assess_context(root, task_type="security", risks=["security"], codex_home=root / "codex", capability_registry=CAPABILITIES, detail="full")
            security = next(item for item in result["quality_coverage"]["obligations"] if item["id"] == "quality.security.review")
            self.assertTrue(security["native_evidence"])
            self.assertEqual(security["coverage"], "native-plus-owned-policy-fallback")
            verification = next(item for item in result["quality_coverage"]["obligations"] if item["id"] == "quality.verification.tests")
            self.assertEqual(verification["coverage"], "uncovered")
            self.assertEqual(result["outcome"], "blocked")

    def test_unsafe_rust_and_swift_accessibility_derive_distinct_contextual_obligations(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            rust_root = Path(temp) / "rust"
            rust_root.mkdir()
            (rust_root / "Cargo.toml").write_text("[package]\nname='sample'\nversion='0.1.0'\n", encoding="utf-8")
            (rust_root / "lib.rs").write_text("pub unsafe fn sample() {}\n", encoding="utf-8")
            rust = ec.assess_context(rust_root, task_type="routine", risks=["unsafe"], codex_home=rust_root / "codex", capability_registry=CAPABILITIES, detail="full")
            unsafe = next(item for item in rust["quality_coverage"]["obligations"] if item["id"] == "quality.rust.unsafe")
            self.assertTrue(unsafe["contextual_review_required"])
            self.assertEqual(unsafe["coverage"], "uncovered")

            swift_root = Path(temp) / "swift"
            swift_root.mkdir()
            (swift_root / "Package.swift").write_text("// swift-tools-version: 6.0\n", encoding="utf-8")
            (swift_root / "View.swift").write_text("struct View {}\n", encoding="utf-8")
            swift = ec.assess_context(swift_root, task_type="routine", risks=["accessibility"], codex_home=swift_root / "codex", capability_registry=CAPABILITIES)
            ids = {item["id"] for item in swift["quality_coverage"]["obligations"]}
            self.assertIn("quality.swift.correctness", ids)
            self.assertIn("quality.accessibility.review", ids)

    def test_t3_waiver_must_cover_scope_blocker_risk_and_expiry(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            packet = root / "packet"
            packet.mkdir()
            valid = {
                "id": "WAIVER-1",
                "by": "owner",
                "note": "accept bounded residual risk",
                "scope": ["src/**"],
                "blockers": ["governed-quality-outcome-uncovered"],
                "residual_risk": "manual review may miss a defect",
                "expires_at": "2999-01-01T00:00:00Z",
                "recheck_trigger": "security-control-added",
            }
            (packet / "packet.json").write_text(json.dumps({"approvals": {"waivers": [valid]}}), encoding="utf-8")
            waived = ec.assess_context(root, task_type="security", risks=["security"], task_paths=["src/auth.py"], codex_home=root / "codex", capability_registry=CAPABILITIES, packet=packet)
            self.assertEqual(waived["outcome"], "waived")
            valid["scope"] = ["docs/**"]
            (packet / "packet.json").write_text(json.dumps({"approvals": {"waivers": [valid]}}), encoding="utf-8")
            blocked = ec.assess_context(root, task_type="security", risks=["security"], task_paths=["src/auth.py"], codex_home=root / "codex", capability_registry=CAPABILITIES, packet=packet)
            self.assertEqual(blocked["outcome"], "blocked")

    def test_approved_route_is_selected_but_incompatible_route_is_not(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            codex_home = root / "codex"
            skills = codex_home / "skills"
            for name in ("review-a", "review-b"):
                directory = skills / name
                directory.mkdir(parents=True)
                (directory / "SKILL.md").write_text(f"---\nname: {name}\ndescription: test route\n---\n# Test\n", encoding="utf-8")
            capability_registry = root / "registry.json"
            capability_registry.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "capabilities": [
                            {
                                "id": "quality.test.review",
                                "outcome": "test outcome",
                                "selectors": [],
                                "native_evidence": [],
                                "route_names": ["review-a", "review-b"],
                                "preferred_route": "review-a",
                                "manual_fallback": "manual",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            admissions = codex_home / "dev-flow"
            admissions.mkdir(parents=True)
            (admissions / "capabilities.json").write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "host": "codex",
                        "admissions": [
                            {"skill": "review-a", "capability_ids": ["quality.test.review"], "status": "approved", "owner": "team", "reviewed_at": "2026-08-09T00:00:00Z", "recheck_trigger": "digest-change"},
                            {"skill": "review-b", "capability_ids": ["quality.test.review"], "status": "incompatible", "owner": "team", "reviewed_at": "2026-08-09T00:00:00Z", "recheck_trigger": "host-change"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            result = ec.assess_context(
                root,
                task_type="routine",
                codex_home=codex_home,
                capability_registry=capability_registry,
                detail="full",
            )
            obligation = result["quality_coverage"]["obligations"][0]
            self.assertEqual(obligation["selected_route"]["skill"], "review-a")
            self.assertEqual(next(item["status"] for item in result["quality_coverage"]["routes"] if item["skill"] == "review-b"), "incompatible")

    def test_admission_digest_drift_disables_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            codex_home = root / "codex"
            skill = codex_home / "skills" / "review-a"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: review-a\ndescription: test\n---\n", encoding="utf-8")
            registry = root / "registry.json"
            registry.write_text(json.dumps({"schema_version": "1.0", "capabilities": [{"id": "quality.test", "outcome": "x", "selectors": [], "native_evidence": [], "route_names": ["review-a"], "manual_fallback": "manual"}]}), encoding="utf-8")
            admissions = codex_home / "dev-flow"
            admissions.mkdir(parents=True)
            (admissions / "capabilities.json").write_text(json.dumps({"schema_version": "1.0", "host": "codex", "admissions": [{"skill": "review-a", "capability_ids": ["quality.test"], "status": "approved", "owner": "team", "reviewed_at": "2026-08-09T00:00:00Z", "recheck_trigger": "digest-change", "digest": "sha256:" + "0" * 64}]}), encoding="utf-8")
            result = ec.assess_context(root, task_type="routine", codex_home=codex_home, capability_registry=registry, detail="full")
            route = result["quality_coverage"]["routes"][0]
            self.assertEqual(route["status"], "stale")
            self.assertIsNone(result["quality_coverage"]["obligations"][0]["selected_route"])

    def test_multiple_approved_routes_without_preference_create_collision(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            codex_home = root / "codex"
            for name in ("review-a", "review-b"):
                skill = codex_home / "skills" / name
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text(f"---\nname: {name}\ndescription: test\n---\n", encoding="utf-8")
            registry = root / "registry.json"
            registry.write_text(json.dumps({"schema_version": "1.0", "capabilities": [{"id": "quality.test", "outcome": "x", "selectors": [], "native_evidence": [], "route_names": ["review-a", "review-b"], "manual_fallback": "manual"}]}), encoding="utf-8")
            admission_dir = codex_home / "dev-flow"
            admission_dir.mkdir(parents=True)
            shared = {"capability_ids": ["quality.test"], "status": "approved", "owner": "team", "reviewed_at": "2026-08-09T00:00:00Z", "recheck_trigger": "route-change"}
            (admission_dir / "capabilities.json").write_text(json.dumps({"schema_version": "1.0", "host": "codex", "admissions": [{"skill": "review-a", **shared}, {"skill": "review-b", **shared}]}), encoding="utf-8")
            result = ec.assess_context(root, task_type="routine", codex_home=codex_home, capability_registry=registry)
            self.assertIn("approved-route-collision", result["blockers"])
            self.assertEqual(len(result["quality_coverage"]["conflicts"]), 1)

    def test_react_capability_is_selected_only_from_manifest_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "package.json").write_text(json.dumps({"dependencies": {"react": "19.0.0"}}), encoding="utf-8")
            (root / "src.ts").write_text("export const value = 1;\n", encoding="utf-8")
            result = ec.assess_context(root, task_type="routine", codex_home=root / "codex", capability_registry=CAPABILITIES)
            ids = {item["id"] for item in result["quality_coverage"]["obligations"]}
            self.assertIn("quality.react.performance", ids)
            self.assertIn("react", result["scope"]["frameworks"])

    def test_rust_and_java_framework_versions_are_scoped_to_canonical_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            rust = root / "rust-service"
            java = root / "java-service"
            rust.mkdir()
            java.mkdir()
            (rust / "Cargo.toml").write_text(
                '''[package]
name = "rust-service"
version = "0.1.0"

[dependencies]
axum = "0.8"
serde = { version = "1", features = ["derive"] }
''',
                encoding="utf-8",
            )
            (java / "pom.xml").write_text(
                '''<project><parent>
<artifactId>spring-boot-starter-parent</artifactId><version>4.0.1</version>
</parent></project>
''',
                encoding="utf-8",
            )
            rust_result = ec.assess_context(
                root,
                task_type="routine",
                task_paths=["rust-service"],
                codex_home=root / "codex",
                capability_registry=CAPABILITIES,
            )
            self.assertEqual(rust_result["scope"]["languages"], ["rust"])
            self.assertEqual(rust_result["scope"]["frameworks"], ["axum", "serde"])
            self.assertTrue(
                {"axum@0.8", "serde@1"}
                <= set(rust_result["scope"]["artifacts"][0]["version"])
            )

            java_result = ec.assess_context(
                root,
                task_type="routine",
                task_paths=["java-service"],
                codex_home=root / "codex",
                capability_registry=CAPABILITIES,
            )
            self.assertEqual(java_result["scope"]["languages"], ["java"])
            self.assertEqual(java_result["scope"]["frameworks"], ["spring-boot"])
            self.assertIn("spring-boot@4.0.1", java_result["scope"]["artifacts"][0]["version"])

    def test_monorepo_task_scope_does_not_import_unrelated_language_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            frontend = root / "frontend"
            backend = root / "backend"
            frontend.mkdir()
            backend.mkdir()
            (frontend / "package.json").write_text(json.dumps({"dependencies": {"react": "19.0.0"}}), encoding="utf-8")
            (frontend / "app.tsx").write_text("export const App = () => null;\n", encoding="utf-8")
            (backend / "Cargo.toml").write_text("[package]\nname='backend'\nversion='0.1.0'\n", encoding="utf-8")
            result = ec.assess_context(root, task_type="routine", task_paths=["frontend"], codex_home=root / "codex", capability_registry=CAPABILITIES)
            self.assertEqual(result["scope"]["languages"], ["typescript"])
            self.assertEqual(result["scope"]["frameworks"], ["react"])

    def test_owned_quality_policy_fallback_covers_governed_gap(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "pyproject.toml").write_text("[project]\nname='sample'\nversion='0.1.0'\n", encoding="utf-8")
            tests = root / "tests"
            tests.mkdir()
            (tests / "test_auth.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
            profiles = root / ".dev-flow" / "profiles"
            profiles.mkdir(parents=True)
            (profiles / "project.toml").write_text(quality_profile_text("quality.security.review", "qualified-security-owner-review"), encoding="utf-8")
            result = ec.assess_context(root, task_type="security", risks=["security"], codex_home=root / "codex", capability_registry=CAPABILITIES, detail="full")
            security = next(item for item in result["quality_coverage"]["obligations"] if item["id"] == "quality.security.review")
            self.assertEqual(security["coverage"], "owned-policy-fallback")
            self.assertNotIn("governed-quality-outcome-uncovered", result["blockers"])

    def test_owned_must_quality_policy_without_evidence_or_fallback_blocks_t3(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profiles = root / ".dev-flow" / "profiles"
            profiles.mkdir(parents=True)
            (profiles / "project.toml").write_text(quality_profile_text("quality.security.review", None), encoding="utf-8")
            result = ec.assess_context(
                root,
                task_type="security",
                risks=["security"],
                codex_home=root / "codex",
                capability_registry=CAPABILITIES,
                detail="full",
            )
            assessment = next(
                item for item in result["quality_coverage"]["policy_assessments"]
                if item["key"] == "quality.test"
            )
            self.assertEqual(assessment["coverage"], "uncovered")
            self.assertIn("security-owner-check", assessment["missing_evidence"])
            self.assertEqual(result["outcome"], "blocked")

    def test_matching_suppression_is_fingerprinted_and_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = ec.assess_context(root, task_type="routine", codex_home=root / "codex", capability_registry=CAPABILITIES)
            ledger = root / ".dev-flow"
            ledger.mkdir()
            (ledger / "suppressions.json").write_text(json.dumps({"schema_version": "1.0", "suppressions": [{"fingerprint": first["fingerprint"], "owner": "user", "reason": "known lean repository", "tiers": ["T1"], "expires_at": None}]}), encoding="utf-8")
            second = ec.assess_context(root, task_type="routine", codex_home=root / "codex", capability_registry=CAPABILITIES)
            self.assertEqual(second["suppression"]["fingerprint"], first["fingerprint"])

    def test_capability_registry_change_invalidates_readiness_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            registry = root / "registry.json"
            base = {"schema_version": "1.0", "capabilities": [{"id": "quality.test", "outcome": "first", "selectors": [], "native_evidence": [], "route_names": [], "manual_fallback": "manual"}]}
            registry.write_text(json.dumps(base), encoding="utf-8")
            first = ec.assess_context(root, task_type="routine", codex_home=root / "codex", capability_registry=registry)
            base["capabilities"][0]["outcome"] = "second"
            registry.write_text(json.dumps(base), encoding="utf-8")
            second = ec.assess_context(root, task_type="routine", codex_home=root / "codex", capability_registry=registry)
            self.assertNotEqual(first["fingerprint"], second["fingerprint"])


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
        self.assertIn("Risk overlays", control_plane)
        self.assertIn("An overlay adds only its relevant controls", control_plane)
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
