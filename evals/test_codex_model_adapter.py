#!/usr/bin/env python3
"""Deterministic tests for the bounded Codex model adapter."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import codex_model_adapter as adapter  # noqa: E402
import run_paired_evaluations as paired_eval  # noqa: E402


def kind_vocabulary(*owners: str) -> list[dict[str, str]]:
    return [
        {"id": f"{owner}.{family}", "owner": owner}
        for owner in owners
        for family in adapter.CLAIM_KIND_FAMILIES
    ]


def sanitized_executor(
    *,
    case_id: str,
    claims: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "schema_version": "1.3",
        "case_id": case_id,
        "attempt": 1,
        "claimed_outcome": "completed",
        "actions": ["bounded"],
        "evidence": ["fixture-grounded"],
        "claims": claims,
        "interactions": {
            "user_questions": 0,
            "user_corrections": 0,
            "reminders": 0,
            "blocks": 0,
        },
    }


class CodexModelAdapterTests(unittest.TestCase):
    def test_inventory_prompt_and_schema_are_atomic_and_routing_blind(self) -> None:
        request = {
            "schema_version": "1.0",
            "case_id": "PAIR-INVENTORY",
            "attempt": 1,
            "capabilities": ["verification"],
            "capability_sources": {"verification": "Task-neutral verification guidance."},
            "fixture": "Preserve both independently failing checks.",
            "task_prompt": "Analyze the bounded change without executing it.",
        }
        prompt = adapter.inventory_prompt(request)
        self.assertIn("atomic inventory", prompt)
        self.assertIn("evidence_family", prompt)
        self.assertIn("evidence_refs", prompt)
        self.assertIn("Preserve both independently failing checks.", prompt)
        self.assertNotIn("claim-owner-vocabulary", prompt)
        self.assertNotIn("claim-kind-vocabulary", prompt)
        self.assertNotIn("evaluation_contract", prompt)

        with self.assertRaisesRegex(adapter.AdapterError, "exact blind inventory request"):
            adapter.inventory_prompt({**request, "claim_owner_vocabulary": ["verification"]})

        schema = json.loads(
            (adapter.SCHEMAS / "inventory-result.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            set(schema["properties"]),
            {
                "schema_version", "case_id", "attempt", "claimed_outcome",
                "inventory_items", "interactions",
            },
        )
        item = schema["properties"]["inventory_items"]["items"]
        self.assertEqual(
            set(item["properties"]),
            {
                "item_id", "evidence_family", "action", "protected_behavior",
                "oracle_or_evidence", "status", "limitation", "evidence_refs",
            },
        )
        self.assertEqual(
            item["properties"]["evidence_family"]["enum"],
            ["analysis", "artifact", "decision", "interaction", "limitation", "test"],
        )
        self.assertNotIn("owner", item["properties"])
        self.assertNotIn("kind", item["properties"])
        evidence_ref = item["properties"]["evidence_refs"]["items"]
        self.assertEqual(set(evidence_ref["properties"]), {"source", "quote"})
        self.assertEqual(evidence_ref["properties"]["source"]["enum"], ["fixture", "task_prompt"])

        base_item = {
            "item_id": "IT-1",
            "evidence_family": "test",
            "action": "define the independent failure check",
            "protected_behavior": "preserve the existing successful path",
            "oracle_or_evidence": "the check fails before repair and passes after repair",
            "status": "planned",
            "limitation": "repository execution is unavailable",
            "evidence_refs": [],
        }
        base_result = {
            "schema_version": "1.0",
            "case_id": "PAIR-INVENTORY",
            "attempt": 1,
            "claimed_outcome": "completed",
            "inventory_items": [base_item],
            "interactions": {
                "user_questions": 0, "user_corrections": 0,
                "reminders": 0, "blocks": 0,
            },
        }
        adapter.validated_inventory_result(base_result)
        verified = {
            **base_result,
            "inventory_items": [{
                **base_item,
                "status": "verified",
                "limitation": None,
                "evidence_refs": [{"source": "fixture", "quote": "bounded fixture"}],
            }],
        }
        adapter.validated_inventory_result(verified)
        with self.assertRaisesRegex(adapter.AdapterError, "verified status requires"):
            adapter.validated_inventory_result({
                **verified,
                "inventory_items": [{**verified["inventory_items"][0], "evidence_refs": []}],
            })
        with self.assertRaisesRegex(adapter.AdapterError, "non-verified status requires"):
            adapter.validated_inventory_result({
                **base_result,
                "inventory_items": [{**base_item, "limitation": None}],
            })
        duplicate = adapter.validated_inventory_result({
            **base_result,
            "inventory_items": [base_item, {**base_item, "item_id": "IT-2"}],
        })
        self.assertEqual(len(duplicate["inventory_items"]), 2)

    def test_v2_assembler_prompt_and_schema_are_routing_manifest_only(self) -> None:
        inventory_result = {
            "schema_version": "1.0",
            "case_id": "PAIR-INVENTORY",
            "attempt": 1,
            "claimed_outcome": "completed",
            "inventory_items": [{
                "item_id": "IT-1",
                "evidence_family": "test",
                "action": "define the independent failure check",
                "protected_behavior": "preserve the existing successful path",
                "oracle_or_evidence": "the check fails before repair and passes after repair",
                "status": "planned",
                "limitation": "repository execution is unavailable",
                "evidence_refs": [{
                    "source": "fixture",
                    "quote": "independently failing checks",
                }],
            }],
            "interactions": {
                "user_questions": 0, "user_corrections": 0,
                "reminders": 0, "blocks": 0,
            },
        }
        request = {
            "schema_version": "2.0",
            "case_id": "PAIR-INVENTORY",
            "attempt": 1,
            "capabilities": ["verification"],
            "capability_sources": {"verification": "Task-neutral verification guidance."},
            "claim_owner_vocabulary": ["verification"],
            "claim_kind_vocabulary": kind_vocabulary("verification"),
            "fixture": "Preserve both independently failing checks.",
            "task_prompt": "Analyze the bounded change without executing it.",
            "inventory_result": inventory_result,
        }
        prompt = adapter.assembler_prompt(request)
        self.assertIn("routing manifest", prompt)
        self.assertIn("IT-1", prompt)
        self.assertIn("exact semantic duplicate", prompt)
        self.assertIn("kind suffix", prompt)
        self.assertIn("supplemental_items", prompt)
        self.assertNotIn("draft-result", prompt)
        self.assertNotIn("evaluation_contract", prompt)

        with self.assertRaisesRegex(adapter.AdapterError, "exact blind assembler v2 request"):
            adapter.assembler_prompt({**request, "draft_result": {}})
        absent_quote = json.loads(json.dumps(request))
        absent_quote["inventory_result"]["inventory_items"][0]["evidence_refs"][0]["quote"] = (
            "this quote does not occur in either input"
        )
        with self.assertRaisesRegex(adapter.AdapterError, "occur exactly once"):
            adapter.assembler_prompt(absent_quote)

        schema = json.loads(
            (adapter.SCHEMAS / "assembler-result.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            set(schema["properties"]),
            {
                "schema_version", "case_id", "attempt", "supplemental_items",
                "claim_assemblies", "dispositions",
            },
        )
        supplement = schema["properties"]["supplemental_items"]["items"]
        self.assertEqual(supplement["properties"]["item_id"]["pattern"], "^SP-[A-Za-z0-9][A-Za-z0-9._-]*$")
        self.assertEqual(supplement["properties"]["status"]["enum"], ["planned", "not-run"])
        self.assertEqual(supplement["properties"]["limitation"]["type"], "string")
        self.assertEqual(supplement["properties"]["evidence_refs"]["maxItems"], 0)
        self.assertEqual(
            set(schema["properties"]["claim_assemblies"]["items"]["properties"]),
            {"claim_id", "owner", "kind", "source_item_ids"},
        )
        disposition = schema["properties"]["dispositions"]["items"]
        self.assertEqual(
            set(disposition["properties"]),
            {"item_id", "disposition", "consumed_as_item_id", "rationale"},
        )
        self.assertEqual(disposition["properties"]["disposition"]["const"], "duplicate")

    def test_blind_assembler_prompt_accepts_only_content_request_and_logical_artifacts(self) -> None:
        request = {
            "schema_version": "1.0",
            "case_id": "PAIR-BLIND",
            "attempt": 1,
            "capabilities": ["repo-context"],
            "capability_sources": {"repo-context": "Task-neutral guidance only."},
            "claim_owner_vocabulary": ["repo-context"],
            "claim_kind_vocabulary": kind_vocabulary("repo-context"),
            "fixture": "bounded fixture",
            "task_prompt": "analyze the bounded fixture",
            "draft_result": sanitized_executor(
                case_id="PAIR-BLIND",
                claims=[{
                    "claim_id": "CL-1",
                    "owner": "repo-context",
                    "kind": "repo-context.analysis",
                    "action": "inspect repository state",
                    "protected_behavior": "preserve local changes",
                    "oracle_or_evidence": "record the inspected state",
                    "status": "planned",
                    "limitation": "repository access is not available",
                }],
            ),
        }
        prompt = adapter.assembler_prompt(request)
        self.assertIn("bounded fixture", prompt)
        self.assertIn("CL-1", prompt)
        self.assertIn('artifact_root must be "artifacts"', prompt)
        self.assertIn("copy claimed_outcome verbatim", prompt)
        self.assertIn("must not reclassify", prompt)
        for forbidden in ("trial-7", "candidate", "evaluation_contract", "work_units", "/private/tmp"):
            self.assertNotIn(forbidden, prompt)

        poisoned = {**request, "variant": "candidate"}
        with self.assertRaisesRegex(adapter.AdapterError, "exact blind assembler request"):
            adapter.assembler_prompt(poisoned)

    def test_receipt_1_1_binds_stage_request_prompt_draft_output_and_nonce(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / adapter.USAGE_RECEIPT
            adapter.write_usage_receipt(
                path,
                role="executor",
                stage="assembly",
                call_nonce="opaque-call-123",
                request_sha="sha256:" + "1" * 64,
                prompt_sha="sha256:" + "2" * 64,
                draft_sha="sha256:" + "3" * 64,
                model_output_sha="sha256:" + "4" * 64,
                model="gpt-5.6-sol",
                effort="medium",
                tokens=12,
                token_usage={"input_tokens": 10, "output_tokens": 2},
                elapsed=1.0,
                exit_code=0,
                prompt_bytes=100,
                capability_source_bytes=20,
                model_output_bytes=30,
                tool_events={
                    "policy": "fail-on-any-tool-event",
                    "total": 0,
                    "categories": {},
                    "invalid_jsonl_lines": 0,
                },
            )
            receipt = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["schema_version"], "1.1")
        self.assertEqual(receipt["stage"], "assembly")
        self.assertEqual(receipt["call_nonce"], "opaque-call-123")
        self.assertEqual(receipt["draft_sha"], "sha256:" + "3" * 64)
        self.assertEqual(receipt["model_output_sha"], "sha256:" + "4" * 64)

    def test_receipt_1_2_binds_output_schema_and_typed_upstream_without_draft_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inventory_path = root / "inventory.json"
            adapter.write_usage_receipt(
                inventory_path,
                role="executor",
                stage="inventory",
                call_nonce="inventory-call",
                request_sha="sha256:" + "1" * 64,
                prompt_sha="sha256:" + "2" * 64,
                model_output_sha="sha256:" + "3" * 64,
                receipt_schema_version="1.2",
                output_schema_version="1.0",
                upstream_kind=None,
                upstream_sha=None,
                model="gpt-5.6-sol",
                effort="medium",
                tokens=12,
                token_usage={"input_tokens": 10, "output_tokens": 2},
                elapsed=1.0,
                exit_code=0,
                prompt_bytes=100,
                capability_source_bytes=20,
                model_output_bytes=30,
                tool_events={
                    "policy": "fail-on-any-tool-event",
                    "total": 0,
                    "categories": {},
                    "invalid_jsonl_lines": 0,
                },
            )
            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
            assembly_path = root / "assembly.json"
            adapter.write_usage_receipt(
                assembly_path,
                role="executor",
                stage="assembly",
                call_nonce="assembly-call",
                request_sha="sha256:" + "4" * 64,
                prompt_sha="sha256:" + "5" * 64,
                model_output_sha="sha256:" + "6" * 64,
                receipt_schema_version="1.2",
                output_schema_version="1.0",
                upstream_kind="inventory",
                upstream_sha="sha256:" + "7" * 64,
                model="gpt-5.6-sol",
                effort="high",
                tokens=15,
                token_usage={"input_tokens": 12, "output_tokens": 3},
                elapsed=1.5,
                exit_code=0,
                prompt_bytes=120,
                capability_source_bytes=20,
                model_output_bytes=40,
                tool_events={
                    "policy": "fail-on-any-tool-event",
                    "total": 0,
                    "categories": {},
                    "invalid_jsonl_lines": 0,
                },
            )
            assembly = json.loads(assembly_path.read_text(encoding="utf-8"))

        self.assertEqual(inventory["schema_version"], "1.2")
        self.assertEqual(inventory["stage"], "inventory")
        self.assertEqual(inventory["output_schema_version"], "1.0")
        self.assertIsNone(inventory["upstream_kind"])
        self.assertIsNone(inventory["upstream_sha"])
        self.assertNotIn("draft_sha", inventory)
        self.assertEqual(assembly["upstream_kind"], "inventory")
        self.assertEqual(assembly["upstream_sha"], "sha256:" + "7" * 64)
        self.assertNotIn("draft_sha", assembly)

        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(adapter.AdapterError, "receipt 1.2"):
                adapter.write_usage_receipt(
                    Path(temp) / "invalid.json",
                    role="executor",
                    stage="assembly",
                    call_nonce="assembly-call",
                    request_sha="sha256:" + "4" * 64,
                    prompt_sha="sha256:" + "5" * 64,
                    model_output_sha="sha256:" + "6" * 64,
                    receipt_schema_version="1.2",
                    output_schema_version="1.0",
                    upstream_kind=None,
                    upstream_sha=None,
                    model="gpt-5.6-sol",
                    effort="high",
                    tokens=15,
                    token_usage={"input_tokens": 12, "output_tokens": 3},
                    elapsed=1.5,
                    exit_code=0,
                    prompt_bytes=120,
                    capability_source_bytes=20,
                    model_output_bytes=40,
                    tool_events={
                        "policy": "fail-on-any-tool-event", "total": 0,
                        "categories": {}, "invalid_jsonl_lines": 0,
                    },
                )

    def test_model_output_schemas_use_the_strict_structured_output_subset(self) -> None:
        forbidden = {"oneOf", "allOf", "not", "if", "then", "else", "uniqueItems"}

        def inspect(value: object, path: str) -> None:
            if isinstance(value, dict):
                self.assertFalse(forbidden & set(value), f"unsupported keyword at {path}")
                if "const" in value or "enum" in value:
                    self.assertIn("type", value, f"typed const/enum required at {path}")
                if value.get("type") == "object":
                    properties = value.get("properties")
                    self.assertIsInstance(properties, dict, f"object properties required at {path}")
                    self.assertEqual(value.get("additionalProperties"), False, path)
                    self.assertEqual(set(value.get("required", [])), set(properties), path)
                for key, item in value.items():
                    inspect(item, f"{path}.{key}")
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    inspect(item, f"{path}[{index}]")

        for name in (
            "executor-result.json",
            "inventory-result.json",
            "assembler-result.json",
            "grader-result.json",
            "grader-result-diagnostic.json",
            "grader-result-work-units.json",
        ):
            schema = json.loads((adapter.SCHEMAS / name).read_text(encoding="utf-8"))
            self.assertEqual(schema.get("type"), "object")
            self.assertNotIn("anyOf", schema)
            inspect(schema, name)

        work_unit_schema = json.loads(
            (adapter.SCHEMAS / "grader-result-work-units.json").read_text(encoding="utf-8")
        )
        assessment = work_unit_schema["properties"]["work_unit_assessments"]["items"]
        self.assertEqual(
            set(assessment["properties"]),
            {"work_unit_id", "facet_assessments"},
        )
        facet = assessment["properties"]["facet_assessments"]["items"]
        self.assertEqual(
            set(facet["properties"]),
            {"facet_id", "status", "evidence", "support_refs"},
        )
        support = facet["properties"]["support_refs"]["items"]
        self.assertEqual(set(support["properties"]), {"claim_id", "field", "quote"})
        self.assertEqual(support["properties"]["quote"]["minLength"], 8)
        self.assertEqual(support["properties"]["quote"]["maxLength"], 500)
        self.assertEqual(
            support["properties"]["field"]["enum"],
            ["action", "protected_behavior", "oracle_or_evidence", "limitation"],
        )

    def test_failure_summary_is_diagnostic_without_retaining_raw_error_text(self) -> None:
        stdout = json.dumps(
            {"type": "turn.failed", "error": {"message": "HTTP 503 service unavailable secret-detail"}}
        )
        summary = adapter.codex_failure_summary(stdout, "", 1)
        self.assertEqual(summary["kind"], "infrastructure")
        self.assertEqual(summary["exit_code"], 1)
        self.assertEqual(summary["stdout_bytes"], len(stdout.encode("utf-8")))
        self.assertRegex(summary["stdout_sha256"], r"^sha256:[0-9a-f]{64}$")
        self.assertNotIn("secret-detail", json.dumps(summary))

    def test_usage_parser_uses_latest_complete_turn(self) -> None:
        events = "\n".join(
            (
                json.dumps(
                    {
                        "type": "turn.completed",
                        "usage": {
                            "input_tokens": 10,
                            "cached_input_tokens": 4,
                            "output_tokens": 5,
                        },
                    }
                ),
                "not-json",
                json.dumps(
                    {
                        "type": "turn.completed",
                        "usage": {
                            "input_tokens": 30,
                            "output_tokens": 12,
                            "total_tokens": 42,
                        },
                    }
                ),
            )
        )
        self.assertEqual(adapter.usage_tokens(events), 42)
        self.assertEqual(
            adapter.usage_breakdown(events),
            {"input_tokens": 30, "output_tokens": 12, "total_tokens": 42},
        )

    def test_tool_event_summary_is_redacted_and_detects_every_prohibited_category(self) -> None:
        events = "\n".join(
            (
                json.dumps({"type": "item.completed", "item": {"type": "command_execution", "command": "secret"}}),
                json.dumps({"type": "item.started", "item": {"type": "web_search", "query": "private"}}),
                json.dumps({"type": "item.completed", "item": {"type": "computer_tool_call"}}),
                json.dumps({"type": "item.completed", "item": {"type": "mcp_tool_call", "name": "private-server"}}),
            )
        )
        summary = adapter.tool_event_summary(events)
        self.assertEqual(summary["total"], 4)
        self.assertEqual(summary["invalid_jsonl_lines"], 0)
        self.assertEqual(set(summary["categories"]), {"shell", "browser", "computer", "apps_or_other"})
        self.assertNotIn("secret", json.dumps(summary))
        self.assertNotIn("private-server", json.dumps(summary))

        malformed = adapter.tool_event_summary("not-json\n[]\n")
        self.assertEqual(malformed["invalid_jsonl_lines"], 2)

    def test_executor_prompt_blinds_condition_labels_and_embeds_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            prompt = adapter.executor_prompt(
                {
                    "case_id": "PAIR-PROFILE-PRECEDENCE",
                    "fixture": "ordinary repository instructions",
                    "condition": "with-capabilities",
                    "capabilities": ["repo-context"],
                    "capability_sources": {"repo-context": "---\nname: repo-context\n---\nBounded source."},
                    "claim_owner_vocabulary": ["repo-context", "verification"],
                    "claim_kind_vocabulary": kind_vocabulary("repo-context", "verification"),
                },
                Path(temp) / "artifacts",
            )
        self.assertIn("name: repo-context", prompt)
        self.assertNotIn("with-capabilities", prompt)
        self.assertIn("do not mention evaluation variants, treatment labels", prompt)
        self.assertIn("Ordinary specialist route names may be used", prompt)
        self.assertIn("do not mark it blocked", prompt)
        self.assertIn('"repo-context", "verification"', prompt)
        self.assertIn("claim ledger", prompt)
        self.assertIn("claim-kind-vocabulary", prompt)
        self.assertIn(
            "Give every claim one pass/fail oracle or evidence destination. Split claims whenever actions, protected behaviors, or evidence can pass or fail independently, even when they share an owner; represent independently gated cells as separate claims.",
            prompt,
        )
        self.assertIn(
            "Planned or not-run status never converts the underlying work into limitation or analysis: missing discovery remains analysis, route admission remains decision, and an unexecuted check remains test.",
            prompt,
        )
        self.assertIn(
            "give every supplied member its own complete phrase that can be cited without overlapping another member; collective plurals and `each`, `all`, or `both` never replace member names",
            prompt,
        )
        self.assertIn(
            "For planned or not-run work, the limitation names every missing prerequisite separately.",
            prompt,
        )

    def test_release_backend_path_is_explicit_and_does_not_fall_back_to_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "result.json"
            with mock.patch.object(adapter.shutil, "which", return_value="/tmp/fake-codex"):
                command = adapter.codex_command(
                    "executor",
                    "test-model",
                    "medium",
                    output,
                    executable="/approved/codex",
                )
        self.assertEqual(command[0], "/approved/codex")

    def test_v2_commands_select_stage_specific_output_schemas(self) -> None:
        with mock.patch.object(adapter.shutil, "which", return_value="/usr/local/bin/codex"):
            inventory = adapter.codex_command(
                "inventory", "test-model", "medium", Path("/tmp/inventory.json")
            )
            assembly = adapter.codex_command(
                "assembler", "test-model", "high", Path("/tmp/assembly.json"),
                assembler_manifest=True,
            )
            legacy = adapter.codex_command(
                "assembler", "test-model", "high", Path("/tmp/legacy.json")
            )
        self.assertIn(str(adapter.SCHEMAS / "inventory-result.json"), inventory)
        self.assertIn(str(adapter.SCHEMAS / "assembler-result.json"), assembly)
        self.assertIn(str(adapter.SCHEMAS / "executor-result.json"), legacy)

    def test_v2_roles_fail_closed_before_model_without_receipt_1_2_binding(self) -> None:
        inventory_request = {
            "schema_version": "1.0",
            "case_id": "PAIR-INVENTORY",
            "attempt": 1,
            "capabilities": [],
            "capability_sources": {},
            "fixture": "bounded fixture",
            "task_prompt": "bounded task",
        }
        with (
            mock.patch.object(sys, "stdin", io.StringIO(json.dumps(inventory_request))),
            mock.patch.object(adapter.subprocess, "run") as run_model,
            mock.patch.object(sys, "stderr", io.StringIO()),
        ):
            status = adapter.main([
                "inventory", "--model", "test-model", "--reasoning-effort", "medium",
            ])
        self.assertEqual(status, 2)
        run_model.assert_not_called()

        legacy_request = {
            "schema_version": "1.0",
            "case_id": "PAIR-LEGACY",
            "attempt": 1,
        }
        with (
            mock.patch.object(sys, "stdin", io.StringIO(json.dumps(legacy_request))),
            mock.patch.object(adapter.subprocess, "run") as run_model,
            mock.patch.object(sys, "stderr", io.StringIO()),
        ):
            status = adapter.main([
                "assembler", "--model", "test-model", "--reasoning-effort", "medium",
                "--call-nonce", "opaque", "--receipt-schema-version", "1.2",
            ])
        self.assertEqual(status, 2)
        run_model.assert_not_called()

    def test_assembler_request_schema_keeps_v1_and_adds_exact_v2(self) -> None:
        schema = json.loads(
            (adapter.SCHEMAS / "assembler-request.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(schema["oneOf"]), 2)
        by_version = {
            branch["properties"]["schema_version"]["const"]: branch
            for branch in schema["oneOf"]
        }
        self.assertEqual(set(by_version), {"1.0", "2.0"})
        self.assertIn("draft_result", by_version["1.0"]["required"])
        self.assertNotIn("inventory_result", by_version["1.0"]["properties"])
        self.assertIn("inventory_result", by_version["2.0"]["required"])
        self.assertNotIn("draft_result", by_version["2.0"]["properties"])

    def test_capability_material_uses_only_the_supplied_snapshot(self) -> None:
        material = adapter.capability_material(
            {"capabilities": ["repo-context"], "capability_sources": {"repo-context": "IMMUTABLE\n"}}
        )
        self.assertIn("IMMUTABLE", material)
        with self.assertRaisesRegex(adapter.AdapterError, "exactly match"):
            adapter.capability_material(
                {"capabilities": ["repo-context"], "capability_sources": {"other": "wrong"}}
            )

    def test_grader_prompt_uses_structured_contract_without_condition_labels(self) -> None:
        prompt = adapter.grader_prompt(
            {
                "schema_version": "1.1",
                "case_id": "PAIR-FFI",
                "attempt": 1,
                "fixture": "bounded ffi case",
                "task_prompt": "evolve callback",
                "deterministic_oracle": "boundary tests",
                "evaluation_contract": {
                    "work_units": [
                        {
                            "id": "WU-ROUTE",
                            "owner": "architecture-decisions",
                            "claim_routes": [
                                {"kind": "architecture-decisions.decision"}
                            ],
                            "criticality": "critical",
                            "protected_behavior": "both consumer boundaries receive specialist guidance",
                            "facets": [
                                {"id": "FT-SWIFT", "action": "load the Swift specialist route"},
                                {"id": "FT-KOTLIN", "action": "load the Kotlin specialist route"},
                            ],
                        },
                        {
                            "id": "WU-CONSUMERS",
                            "owner": "verification",
                            "claim_routes": [{"kind": "verification.test"}],
                            "criticality": "supporting",
                            "protected_behavior": "both generated consumers remain compatible",
                            "facets": [
                                {"id": "FT-BOTH", "action": "verify both consumers"}
                            ],
                        },
                        {
                            "id": "WU-REVIEW",
                            "owner": "change-review",
                            "claim_routes": [
                                {"kind": "change-review.limitation"},
                                {"kind": "change-review.analysis"},
                            ],
                            "criticality": "supporting",
                            "protected_behavior": "review admission remains distinct from executed review analysis",
                            "facets": [
                                {"id": "FT-ADMISSION", "action": "record missing review evidence"},
                                {"id": "FT-ANALYSIS", "action": "conduct the admitted review"},
                            ],
                        },
                    ],
                    "forbidden_actions": ["review one side only"],
                    "required_artifacts": ["evidence.md"],
                },
                "executor_result": sanitized_executor(
                    case_id="PAIR-FFI",
                    claims=[
                        {
                            "claim_id": "CL-1",
                            "owner": "architecture-decisions",
                            "kind": "architecture-decisions.decision",
                            "action": "route specialists",
                            "protected_behavior": "both consumers remain safe",
                            "oracle_or_evidence": "ordered route ledger",
                            "status": "planned",
                            "limitation": "repository execution is not available",
                        }
                    ],
                ),
            }
        )
        self.assertIn('"id": "WU-ROUTE"', prompt)
        self.assertIn('"id": "FT-SWIFT"', prompt)
        self.assertIn('"kind": "change-review.limitation"', prompt)
        self.assertIn('"kind": "change-review.analysis"', prompt)
        self.assertIn('"criticality": "critical"', prompt)
        self.assertIn("work_unit_assessments", prompt)
        self.assertIn("facet_assessment", prompt)
        self.assertIn("support_ref", prompt)
        self.assertIn("exact substring of 8 to 500 characters", prompt)
        self.assertIn("occur exactly once", prompt)
        self.assertIn("must not arbitrarily cut through a word", prompt)
        self.assertIn("missing requires an empty support_refs list", prompt)
        self.assertIn("at least four alphanumeric characters", prompt)
        self.assertIn("Never reuse the same support span", prompt)
        self.assertIn("shortest whole-word span", prompt)
        self.assertIn("do not overlap", prompt)
        self.assertIn("hard-gated critical or required work units", prompt)
        self.assertIn("first-attempt workflow quality, not completed repository execution", prompt)
        self.assertIn(
            "`claimed_outcome: completed` means only that this bounded analysis response is complete",
            prompt,
        )
        self.assertIn("Never treat that field alone as a forbidden action", prompt)
        self.assertIn("do not reward unsupported confidence", prompt)
        self.assertIn("semantic, not an exact string match", prompt)
        self.assertIn(
            "owner exactly matches the work unit and whose kind is one of that unit's claim_routes",
            prompt,
        )
        self.assertIn("does not enumerate artifact filenames", prompt)
        self.assertNotIn("candidate", prompt)
        self.assertNotIn("with-capabilities", prompt)

    def test_work_unit_contract_validation_is_exact_and_owner_aligned(self) -> None:
        work_units = [
            {
                "id": "WU-REVIEW",
                "owner": "change-review",
                "claim_routes": [
                    {"kind": "change-review.limitation"},
                    {"kind": "change-review.analysis"},
                ],
                "criticality": "supporting",
                "protected_behavior": "review admission and executed analysis stay distinct",
                "facets": [
                    {"id": "FT-ADMIT", "action": "record unavailable evidence"},
                    {"id": "FT-REVIEW", "action": "perform the admitted review"},
                ],
            }
        ]
        self.assertEqual(adapter.validated_work_units(work_units), work_units)

        extra = json.loads(json.dumps(work_units))
        extra[0]["gold_hint"] = "not allowed"
        with self.assertRaisesRegex(adapter.AdapterError, "exact work-unit shape"):
            adapter.validated_work_units(extra)

        wrong_owner = json.loads(json.dumps(work_units))
        wrong_owner[0]["claim_routes"][0]["kind"] = "verification.test"
        with self.assertRaisesRegex(adapter.AdapterError, "owner-misaligned"):
            adapter.validated_work_units(wrong_owner)

        duplicate_facet = json.loads(json.dumps(work_units))
        duplicate_facet[0]["facets"][1]["id"] = "FT-ADMIT"
        with self.assertRaisesRegex(adapter.AdapterError, "unique within its work unit"):
            adapter.validated_work_units(duplicate_facet)

    def test_legacy_grader_prompt_preserves_numbered_expected_actions(self) -> None:
        request = {
            "schema_version": "1.1",
            "case_id": "PAIR-LEGACY",
            "attempt": 1,
            "fixture": "bounded legacy case",
            "task_prompt": "inspect and verify the bounded legacy case",
            "deterministic_oracle": "ordered legacy actions",
            "evaluation_contract": {
                "expected_actions": ["inspect first", "verify second"],
                "forbidden_actions": ["invent evidence"],
                "required_artifacts": ["evidence.md"],
            },
            "executor_result": sanitized_executor(
                case_id="PAIR-LEGACY",
                claims=[
                    {
                        "claim_id": "CL-1",
                        "owner": "verification",
                        "kind": "legacy.verification",
                        "action": "inspect and verify",
                        "protected_behavior": "legacy compatibility",
                        "oracle_or_evidence": "ordered actions",
                        "status": "planned",
                        "limitation": None,
                    }
                ],
            ),
        }
        prompt = adapter.grader_prompt(request)
        self.assertIn("1. inspect first", prompt)
        self.assertIn("2. verify second", prompt)
        self.assertIn("one legacy index entry", prompt)
        self.assertIn("schema_version must be 1.3", prompt)

        mixed = json.loads(json.dumps(request))
        mixed["evaluation_contract"]["obligations"] = []
        with self.assertRaisesRegex(adapter.AdapterError, "exactly one"):
            adapter.grader_prompt(mixed)

    def test_executor_prompt_allows_substantive_specialist_route_names_without_treatment_labels(self) -> None:
        prompt = adapter.executor_prompt(
            {
                "case_id": "PAIR-FFI",
                "fixture": "bounded ffi case",
                "task_prompt": "evolve callback",
                "capabilities": ["architecture-decisions"],
                "capability_sources": {"architecture-decisions": "route through rust-swift-ffi"},
                "claim_owner_vocabulary": ["architecture-decisions", "verification"],
                "claim_kind_vocabulary": kind_vocabulary("architecture-decisions", "verification"),
            },
            Path("/tmp/artifacts"),
        )
        self.assertIn("Ordinary specialist route names may be used", prompt)
        self.assertNotIn("with-capabilities", prompt)
        self.assertNotIn("without-capabilities", prompt)

    def test_executor_prompt_gets_equal_owner_vocabulary_without_gold_obligation_leakage(self) -> None:
        common = {
            "case_id": "PAIR-FAIR",
            "fixture": "bounded case",
            "task_prompt": "preserve behavior",
            "claim_owner_vocabulary": ["architecture-decisions", "verification"],
            "claim_kind_vocabulary": kind_vocabulary("architecture-decisions", "verification"),
            "evaluation_contract": {
                "work_units": [
                    {
                        "id": "WU-SECRET-GOLD",
                        "owner": "verification",
                        "claim_routes": [{"kind": "verification.test"}],
                        "criticality": "critical",
                        "protected_behavior": "SECRET PROTECTED BEHAVIOR",
                        "facets": [
                            {"id": "FT-SECRET-GOLD", "action": "SECRET EXPECTED ACTION"}
                        ],
                    }
                ]
            },
        }
        baseline = adapter.executor_prompt(
            {**common, "capabilities": [], "capability_sources": {}},
            Path("/tmp/baseline-artifacts"),
        )
        candidate = adapter.executor_prompt(
            {
                **common,
                "capabilities": ["architecture-decisions"],
                "capability_sources": {"architecture-decisions": "bounded source"},
            },
            Path("/tmp/candidate-artifacts"),
        )
        vocabulary = '["architecture-decisions", "verification"]'
        self.assertIn(vocabulary, baseline)
        self.assertIn(vocabulary, candidate)
        self.assertIn(
            "Assign discovery and measurement to the capability that produces their evidence; downstream capabilities reference that claim instead of copying or relabeling it.",
            candidate,
        )
        self.assertIn(
            "Preserve every independently variable facet named by applicable guidance, or mark it unknown or NOT RUN; umbrella terms do not replace those facets.",
            candidate,
        )
        for secret in (
            "WU-SECRET-GOLD",
            "FT-SECRET-GOLD",
            "SECRET EXPECTED ACTION",
            "SECRET PROTECTED BEHAVIOR",
            "criticality",
        ):
            self.assertNotIn(secret, baseline)
            self.assertNotIn(secret, candidate)

    def test_claim_kind_vocabulary_is_strict_and_globally_unique(self) -> None:
        request = {
            "claim_kind_vocabulary": [
                {"id": "architecture-decisions.decision", "owner": "architecture-decisions"},
                {"id": "verification.test", "owner": "verification"},
            ]
        }
        self.assertEqual(adapter.claim_kind_vocabulary(request), request["claim_kind_vocabulary"])

        duplicate = json.loads(json.dumps(request))
        duplicate["claim_kind_vocabulary"][1]["id"] = duplicate["claim_kind_vocabulary"][0]["id"]
        with self.assertRaisesRegex(adapter.AdapterError, "globally unique"):
            adapter.claim_kind_vocabulary(duplicate)

        invalid = json.loads(json.dumps(request))
        invalid["claim_kind_vocabulary"][0]["id"] = "FFI/Unsafe"
        with self.assertRaisesRegex(adapter.AdapterError, "invalid"):
            adapter.claim_kind_vocabulary(invalid)

    def test_grader_request_is_content_only_and_usage_invariant(self) -> None:
        claims = [
            {
                "claim_id": "CL-1",
                "owner": "architecture-decisions",
                "kind": "architecture-decisions.decision",
                "action": "preserve the ABI boundary",
                "protected_behavior": "FFI ownership",
                "oracle_or_evidence": "boundary matrix",
                "status": "planned",
                "limitation": None,
            }
        ]
        semantic = sanitized_executor(case_id="PAIR-BLIND", claims=claims)
        baseline_executor = {
            **semantic,
            "artifact_root": "/private/baseline-real-root",
            "usage": {"tokens": 1, "elapsed_seconds": 0.1, "cost": 0.01},
            "condition_proxy": "baseline",
        }
        candidate_executor = {
            **semantic,
            "artifact_root": "/private/candidate-real-root",
            "usage": {"tokens": 999999, "elapsed_seconds": 999.0, "cost": 99.0},
            "condition_proxy": "candidate",
        }
        baseline = paired_eval.build_grader_request(
            pair_id="PAIR-BLIND",
            fixture="bounded FFI case",
            deterministic_oracle="boundary matrix",
            executor=baseline_executor,
            contract=None,
        )
        candidate = paired_eval.build_grader_request(
            pair_id="PAIR-BLIND",
            fixture="bounded FFI case",
            deterministic_oracle="boundary matrix",
            executor=candidate_executor,
            contract=None,
        )
        self.assertEqual(baseline, candidate)
        self.assertEqual(
            paired_eval.canonical_json_sha256(baseline),
            paired_eval.canonical_json_sha256(candidate),
        )
        rendered = json.dumps(candidate, sort_keys=True)
        for prohibited in (
            "artifact_root",
            "usage",
            "condition_proxy",
            "candidate-real-root",
            "999999",
        ):
            self.assertNotIn(prohibited, rendered)
        self.assertEqual(adapter.grader_prompt(baseline), adapter.grader_prompt(candidate))

        raw = json.loads(json.dumps(candidate))
        raw["executor_result"]["usage"] = candidate_executor["usage"]
        with self.assertRaisesRegex(adapter.AdapterError, "sanitized content-only shape"):
            adapter.grader_prompt(raw)

    def test_owner_kind_alignment_and_critical_claim_exclusivity_are_hard_gates(self) -> None:
        obligations = [
            {
                "id": "OB-FFI-ABI",
                "owner": "architecture-decisions",
                "kind": "architecture-decisions.decision",
                "criticality": "critical",
                "action": "define the ABI representation",
                "evidence_kind": "decision",
            },
            {
                "id": "OB-FFI-LIFETIME",
                "owner": "architecture-decisions",
                "kind": "architecture-decisions.decision",
                "criticality": "critical",
                "action": "define ABI lifetime ownership",
                "evidence_kind": "decision",
            },
        ]
        claims = [
            {
                "claim_id": "CL-ABI",
                "owner": "architecture-decisions",
                "kind": "architecture-decisions.decision",
                "action": "define ABI types",
                "protected_behavior": "stable representation",
                "oracle_or_evidence": "ABI contract",
                "status": "planned",
                "limitation": None,
            },
            {
                "claim_id": "CL-LIFETIME",
                "owner": "architecture-decisions",
                "kind": "architecture-decisions.decision",
                "action": "define ownership",
                "protected_behavior": "callback lifetime",
                "oracle_or_evidence": "lifetime contract",
                "status": "planned",
                "limitation": None,
            },
            {
                "claim_id": "CL-WRONG-KIND",
                "owner": "architecture-decisions",
                "kind": "architecture-decisions.analysis",
                "action": "analyze ABI context",
                "protected_behavior": "context completeness",
                "oracle_or_evidence": "analysis record",
                "status": "planned",
                "limitation": None,
            },
            {
                "claim_id": "CL-CLONE",
                "owner": "architecture-decisions",
                "kind": "architecture-decisions.decision",
                "action": "define ABI types",
                "protected_behavior": "stable representation",
                "oracle_or_evidence": "ABI contract",
                "status": "planned",
                "limitation": None,
            },
        ]
        base = {
            "schema_version": "1.3",
            "case_id": "PAIR-KIND",
            "graded_attempt": 1,
            "requirement_fidelity": 4,
            "scope_discipline": 4,
            "evidence_quality": 4,
            "forbidden_actions": [],
            "structural_coverage": ["ABI representation", "lifetime ownership"],
            "obligation_assessments": [
                {
                    "obligation_id": "OB-FFI-ABI",
                    "status": "covered",
                    "evidence": "ABI claim",
                    "claim_ids": ["CL-ABI"],
                },
                {
                    "obligation_id": "OB-FFI-LIFETIME",
                    "status": "covered",
                    "evidence": "lifetime claim",
                    "claim_ids": ["CL-LIFETIME"],
                },
            ],
            "metrics": {
                "coverage": 4,
                "restraint": 4,
                "ordinary_defect_retention": 4,
                "actionability": 4,
                "rework": 0,
                "unsafe_actions": 0,
                "false_blocks": 0,
            },
            "verdict": "pass",
        }
        accepted = paired_eval.validate_grader(
            json.loads(json.dumps(base)), "PAIR-KIND", obligations, claims
        )
        self.assertEqual(accepted["verdict"], "pass")
        self.assertTrue(accepted["policy_verdict_checks"]["critical_claim_exclusive"])
        self.assertTrue(accepted["policy_verdict_checks"]["claim_kind_alignment"])

        wrong_kind = json.loads(json.dumps(base))
        wrong_kind["obligation_assessments"][0]["claim_ids"] = ["CL-WRONG-KIND"]
        rejected = paired_eval.validate_grader(wrong_kind, "PAIR-KIND", obligations, claims)
        self.assertEqual(rejected["verdict"], "fail")
        self.assertTrue(rejected["policy_verdict_checks"]["claim_owner_alignment"])
        self.assertFalse(rejected["policy_verdict_checks"]["claim_kind_alignment"])

        reused = json.loads(json.dumps(base))
        reused["obligation_assessments"][1]["claim_ids"] = ["CL-ABI"]
        rejected = paired_eval.validate_grader(reused, "PAIR-KIND", obligations, claims)
        self.assertEqual(rejected["verdict"], "fail")
        self.assertFalse(rejected["policy_verdict_checks"]["critical_claim_exclusive"])

        cloned = json.loads(json.dumps(base))
        cloned["obligation_assessments"][1]["claim_ids"] = ["CL-CLONE"]
        rejected = paired_eval.validate_grader(cloned, "PAIR-KIND", obligations, claims)
        self.assertEqual(rejected["verdict"], "fail")
        self.assertFalse(rejected["policy_verdict_checks"]["critical_claim_exclusive"])

    def test_executor_claim_owner_must_match_registered_kind_owner_in_1_5_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_root = Path(temp)
            artifact_root = run_root / "artifacts"
            artifact_root.mkdir()
            result = {
                **sanitized_executor(
                    case_id="PAIR-EXECUTOR-KIND",
                    claims=[
                        {
                            "claim_id": "CL-ABI",
                            "owner": "architecture-decisions",
                            "kind": "architecture-decisions.decision",
                            "action": "define ABI types",
                            "protected_behavior": "stable representation",
                            "oracle_or_evidence": "ABI contract",
                            "status": "planned",
                            "limitation": None,
                        }
                    ],
                ),
                "artifact_root": str(artifact_root),
                "usage": {"tokens": 1, "elapsed_seconds": 0.1, "cost": None},
            }
            vocabulary = [
                {
                    "id": "architecture-decisions.decision",
                    "owner": "architecture-decisions",
                },
                {"id": "verification.test", "owner": "verification"},
            ]
            paired_eval.validate_executor(
                json.loads(json.dumps(result)),
                run_root,
                "PAIR-EXECUTOR-KIND",
                ["architecture-decisions", "verification"],
                vocabulary,
                enforce_kind_alignment=True,
            )

            mismatched = json.loads(json.dumps(result))
            mismatched["claims"][0]["kind"] = "verification.test"
            with self.assertRaisesRegex(paired_eval.EvaluationError, "registry owner"):
                paired_eval.validate_executor(
                    mismatched,
                    run_root,
                    "PAIR-EXECUTOR-KIND",
                    ["architecture-decisions", "verification"],
                    vocabulary,
                    enforce_kind_alignment=True,
                )

    def test_schema_1_5_snapshot_binds_complete_equal_kind_vocabulary(self) -> None:
        config = paired_eval.validate_config(
            json.loads(paired_eval.DEVELOPMENT_CONFIG.read_text(encoding="utf-8"))
        )
        inputs, snapshot = paired_eval.evaluation_input_snapshot(config, None)
        registry_path = paired_eval.ROOT / config["case_contract"]["kind_registry"]
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        expected_vocabulary = registry["kinds"]
        self.assertTrue(snapshot["kind_alignment_enforced"])
        self.assertIn(
            config["case_contract"]["kind_registry"],
            {item["path"] for item in snapshot["entries"]},
        )
        self.assertEqual(
            len({item["claim_kind_vocabulary_sha256"] for item in snapshot["assignments"]}),
            1,
        )

        first_pair = config["pairs"][0]
        input_value = inputs[first_pair["id"]]
        self.assertEqual(input_value["claim_kind_vocabulary"], expected_vocabulary)
        baseline = paired_eval.executor_request(
            pair_id=first_pair["id"],
            trial=1,
            variant="baseline",
            pair_capabilities=first_pair["capabilities"],
            input_value=input_value,
        )
        candidate = paired_eval.executor_request(
            pair_id=first_pair["id"],
            trial=1,
            variant="candidate",
            pair_capabilities=first_pair["capabilities"],
            input_value=input_value,
        )
        self.assertEqual(
            baseline["claim_kind_vocabulary"],
            candidate["claim_kind_vocabulary"],
        )
        self.assertEqual(baseline["claim_kind_vocabulary"], expected_vocabulary)
        self.assertNotIn("evaluation_contract", baseline)
        self.assertNotIn("evaluation_contract", candidate)

    def test_normalize_owns_identity_artifact_and_observed_usage(self) -> None:
        result = {
            "case_id": "wrong",
            "attempt": 9,
            "artifact_root": "/wrong",
            "claimed_outcome": "completed",
            "actions": ["inspect"],
            "evidence": ["fixture"],
            "claims": [
                {
                    "claim_id": "CL-1",
                    "owner": "repo-context",
                    "kind": "legacy.repo-context",
                    "action": "inspect",
                    "protected_behavior": "bounded behavior",
                    "oracle_or_evidence": "fixture",
                    "status": "planned",
                    "limitation": None,
                }
            ],
            "interactions": {"user_questions": 0, "user_corrections": 0, "reminders": 0, "blocks": 0},
            "usage": {"tokens": None, "elapsed_seconds": None, "cost": None},
        }
        normalized = adapter.normalize(
            "executor",
            result,
            {"case_id": "PAIR-1"},
            Path("/bounded/artifacts"),
            1.25,
            42,
        )
        self.assertEqual(normalized["case_id"], "PAIR-1")
        self.assertEqual(normalized["attempt"], 1)
        self.assertEqual(normalized["artifact_root"], str(Path("/bounded/artifacts")))
        self.assertEqual(normalized["usage"], {"tokens": 42, "elapsed_seconds": 1.25, "cost": None})

    def test_normalize_v2_stage_results_does_not_manufacture_executor_fields(self) -> None:
        inventory = adapter.normalize(
            "inventory",
            {"schema_version": "wrong", "case_id": "wrong", "attempt": 9, "inventory_items": []},
            {"case_id": "PAIR-1"},
            Path("/bounded/artifacts"),
            1.25,
            42,
        )
        self.assertEqual(
            {key: inventory[key] for key in ("schema_version", "case_id", "attempt")},
            {"schema_version": "1.0", "case_id": "PAIR-1", "attempt": 1},
        )
        self.assertNotIn("artifact_root", inventory)
        self.assertNotIn("usage", inventory)

        manifest = adapter.normalize(
            "assembler",
            {"schema_version": "wrong", "case_id": "wrong", "attempt": 9, "claim_assemblies": []},
            {"schema_version": "2.0", "case_id": "PAIR-1"},
            Path("/bounded/artifacts"),
            1.25,
            42,
        )
        self.assertEqual(
            {key: manifest[key] for key in ("schema_version", "case_id", "attempt")},
            {"schema_version": "1.0", "case_id": "PAIR-1", "attempt": 1},
        )
        self.assertNotIn("artifact_root", manifest)
        self.assertNotIn("usage", manifest)

    @mock.patch("codex_model_adapter.shutil.which", return_value="/usr/local/bin/codex")
    def test_command_disables_mutating_or_context_leaking_surfaces(self, _which: mock.Mock) -> None:
        command = adapter.codex_command("grader", "gpt-5.6-sol", "medium", Path("/tmp/result.json"))
        rendered = " ".join(command)
        for token in adapter.DISABLED_FEATURES:
            self.assertIn(token, command)
        self.assertIn("read-only", command)
        self.assertIn("--ephemeral", command)
        self.assertIn("--ignore-user-config", command)
        self.assertIn('model_reasoning_effort="medium"', command)
        self.assertNotIn("dangerously-bypass", rendered)
        diagnostic = adapter.codex_command(
            "grader",
            "gpt-5.6-sol",
            "medium",
            Path("/tmp/result.json"),
            diagnostic_grader=True,
        )
        self.assertIn(str(adapter.SCHEMAS / "grader-result-diagnostic.json"), diagnostic)
        work_units = adapter.codex_command(
            "grader",
            "gpt-5.6-sol",
            "medium",
            Path("/tmp/result.json"),
            work_unit_grader=True,
        )
        self.assertIn(str(adapter.SCHEMAS / "grader-result-work-units.json"), work_units)
        with self.assertRaisesRegex(adapter.AdapterError, "mutually exclusive"):
            adapter.codex_command(
                "grader",
                "gpt-5.6-sol",
                "medium",
                Path("/tmp/result.json"),
                diagnostic_grader=True,
                work_unit_grader=True,
            )
        with self.assertRaisesRegex(adapter.AdapterError, "require the grader role"):
            adapter.codex_command(
                "inventory",
                "gpt-5.6-sol",
                "medium",
                Path("/tmp/result.json"),
                work_unit_grader=True,
            )

    def test_usage_receipt_is_minimal_and_records_unavailable_cost(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / adapter.USAGE_RECEIPT
            adapter.write_usage_receipt(
                path,
                role="grader",
                model="gpt-5.6-sol",
                effort="medium",
                tokens=123,
                token_usage={"input_tokens": 100, "output_tokens": 23, "total_tokens": 123},
                elapsed=1.5,
                exit_code=0,
                prompt_bytes=456,
                capability_source_bytes=78,
                model_output_bytes=321,
                tool_events={
                    "policy": "fail-on-any-tool-event",
                    "total": 0,
                    "categories": {},
                    "invalid_jsonl_lines": 0,
                },
            )
            receipt = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["tokens"], 123)
        self.assertEqual(receipt["token_usage"]["input_tokens"], 100)
        self.assertEqual(receipt["prompt_bytes"], 456)
        self.assertEqual(receipt["capability_source_bytes"], 78)
        self.assertEqual(receipt["model_output_bytes"], 321)
        self.assertIsNone(receipt["monetary_cost"])
        self.assertEqual(receipt["tool_events"]["total"], 0)
        self.assertNotIn("prompt", receipt)
        self.assertNotIn("response", receipt)

    def test_environment_is_allowlisted_and_uses_private_temp(self) -> None:
        with tempfile.TemporaryDirectory() as temp, mock.patch.dict(
            adapter.os.environ,
            {"PATH": "/bin", "CODEX_HOME": "/auth", "UNRELATED_SECRET": "must-not-pass"},
            clear=True,
        ):
            environment = adapter.codex_environment(Path(temp))
        self.assertEqual(environment["PATH"], "/bin")
        self.assertEqual(environment["CODEX_HOME"], "/auth")
        self.assertNotIn("UNRELATED_SECRET", environment)
        self.assertTrue(environment["TMPDIR"].endswith(".codex-eval-tmp"))


if __name__ == "__main__":
    unittest.main()
