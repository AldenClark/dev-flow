#!/usr/bin/env python3
"""Adapt bounded Codex CLI sessions to the paired-evaluation JSON contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "evals" / "schemas"
ALLOWED_ROLES = {"assembler", "executor", "grader", "inventory"}
ALLOWED_EFFORTS = {"low", "medium", "high", "xhigh"}
USAGE_RECEIPT = "model-usage.json"
MAX_CONTRACT_ITEMS = 100
MAX_CONTRACT_ITEM_CHARACTERS = 2000
MODEL_RESULT_SCHEMA_VERSION = "1.3"
INVENTORY_RESULT_SCHEMA_VERSION = "1.0"
ASSEMBLER_RESULT_SCHEMA_VERSION = "1.0"
CLAIM_VOCABULARY_LIMIT = 200
LEGACY_OBLIGATION_KEYS = {"id", "owner", "criticality", "action", "evidence_kind"}
OBLIGATION_KEYS = LEGACY_OBLIGATION_KEYS | {"kind"}
WORK_UNIT_KEYS = {
    "id",
    "owner",
    "claim_routes",
    "criticality",
    "protected_behavior",
    "facets",
}
WORK_UNIT_ROUTE_KEYS = {"kind"}
WORK_UNIT_FACET_KEYS = {"id", "action"}
SUPPORT_REF_FIELDS = {
    "action",
    "protected_behavior",
    "oracle_or_evidence",
    "limitation",
}
KIND_ID_RE = re.compile(r"^[a-z][a-z0-9.-]{0,127}$")
CLAIM_KIND_FAMILIES = (
    "analysis",
    "artifact",
    "decision",
    "interaction",
    "limitation",
    "test",
)
EVIDENCE_FAMILIES = CLAIM_KIND_FAMILIES
GRADER_REQUEST_KEYS = {
    "schema_version",
    "case_id",
    "attempt",
    "fixture",
    "executor_result",
    "deterministic_oracle",
}
GRADER_EXECUTOR_KEYS = {
    "schema_version",
    "case_id",
    "attempt",
    "claimed_outcome",
    "actions",
    "evidence",
    "claims",
    "interactions",
}
GRADER_CLAIM_KEYS = {
    "claim_id",
    "owner",
    "kind",
    "action",
    "protected_behavior",
    "oracle_or_evidence",
    "status",
    "limitation",
}
GRADER_INTERACTION_KEYS = {
    "user_questions",
    "user_corrections",
    "reminders",
    "blocks",
}
ASSEMBLER_COMMON_REQUEST_KEYS = {
    "schema_version",
    "case_id",
    "attempt",
    "capabilities",
    "capability_sources",
    "claim_owner_vocabulary",
    "claim_kind_vocabulary",
    "fixture",
    "task_prompt",
}
LEGACY_ASSEMBLER_REQUEST_KEYS = ASSEMBLER_COMMON_REQUEST_KEYS | {"draft_result"}
ASSEMBLER_V2_REQUEST_KEYS = ASSEMBLER_COMMON_REQUEST_KEYS | {"inventory_result"}
INVENTORY_REQUEST_KEYS = {
    "schema_version",
    "case_id",
    "attempt",
    "capabilities",
    "capability_sources",
    "fixture",
    "task_prompt",
}
INVENTORY_RESULT_KEYS = {
    "schema_version",
    "case_id",
    "attempt",
    "claimed_outcome",
    "inventory_items",
    "interactions",
}
INVENTORY_ITEM_KEYS = {
    "item_id",
    "evidence_family",
    "action",
    "protected_behavior",
    "oracle_or_evidence",
    "status",
    "limitation",
    "evidence_refs",
}
EVIDENCE_REF_KEYS = {"source", "quote"}
INTERACTION_KEYS = {"user_questions", "user_corrections", "reminders", "blocks"}
INVENTORY_ID_RE = re.compile(r"^IT-[A-Za-z0-9][A-Za-z0-9._-]*$")
TOKEN_USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)
DISABLED_FEATURES = (
    "plugins",
    "hooks",
    "multi_agent",
    "multi_agent_v2",
    "shell_tool",
    "unified_exec",
    "browser_use",
    "browser_use_external",
    "browser_use_full_cdp_access",
    "in_app_browser",
    "computer_use",
    "apps",
    "enable_mcp_apps",
    "image_generation",
    "view_image",
    "workspace_dependencies",
    "goals",
    "tool_suggest",
    "skill_search",
    "skill_mcp_dependency_install",
    "auth_elicitation",
    "request_permissions_tool",
    "tool_call_mcp_elicitation",
    "network_proxy",
    "standalone_web_search",
    "code_mode_host",
    "shell_snapshot",
    "memories",
    "external_agent_memory_import",
    "recommended_plugins",
    "remote_plugin",
    "plugin_sharing",
    "current_time_reminder",
    "mentions_v2",
    "personality",
    "in_app_updates",
    "workspace_owner_usage_nudge",
)
ENVIRONMENT_ALLOWLIST = {
    "PATH",
    "CODEX_HOME",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
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
}


class AdapterError(RuntimeError):
    """A controlled model-adapter failure."""

    def __init__(self, message: str, *, error_kind: str | None = None) -> None:
        super().__init__(message)
        self.error_kind = error_kind


def codex_failure_kind(diagnostic: str, *, exit_code: int | None = None) -> str | None:
    """Classify bounded transport/service diagnostics without retrying content failures."""
    lowered = diagnostic.lower()
    markers = (
        "failed to connect to websocket",
        "tls handshake eof",
        "connection reset",
        "connection refused",
        "name resolution",
        "temporarily unavailable",
        "service unavailable",
        "http 502",
        "http 503",
        "http 504",
    )
    if any(marker in lowered for marker in markers):
        return "infrastructure"
    if exit_code not in {None, 0} and not diagnostic.strip():
        return "environment"
    return None


def codex_failure_diagnostic(stdout: str, stderr: str) -> str:
    parts = [stderr.strip()]
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        event_type = str(event.get("type", "")).lower()
        if "fail" not in event_type and "error" not in event_type:
            continue
        error = event.get("error")
        if isinstance(error, str):
            parts.append(error)
        elif isinstance(error, dict) and isinstance(error.get("message"), str):
            parts.append(error["message"])
        if isinstance(event.get("message"), str):
            parts.append(event["message"])
    return "\n".join(part for part in parts if part)


def codex_failure_summary(stdout: str, stderr: str, exit_code: int) -> dict[str, Any]:
    diagnostic = codex_failure_diagnostic(stdout, stderr)
    kind = codex_failure_kind(diagnostic, exit_code=exit_code) or "process"
    return {
        "kind": kind,
        "exit_code": exit_code,
        "stdout_bytes": len(stdout.encode("utf-8")),
        "stderr_bytes": len(stderr.encode("utf-8")),
        "stdout_sha256": "sha256:" + hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
        "stderr_sha256": "sha256:" + hashlib.sha256(stderr.encode("utf-8")).hexdigest(),
        "diagnostic_sha256": "sha256:" + hashlib.sha256(diagnostic.encode("utf-8")).hexdigest(),
    }


def require_object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AdapterError(f"{label} must be a JSON object")
    return value


def capability_material(request: dict[str, Any]) -> str:
    capabilities = request.get("capabilities")
    sources = request.get("capability_sources")
    if not isinstance(capabilities, list) or not isinstance(sources, dict):
        raise AdapterError("executor capabilities and snapshotted sources must be provided")
    if set(sources) != set(capabilities):
        raise AdapterError("executor capability sources must exactly match requested capabilities")
    sections: list[str] = []
    for capability in capabilities:
        if not isinstance(capability, str) or not capability or Path(capability).name != capability:
            raise AdapterError(f"unsafe capability name: {capability!r}")
        source = sources.get(capability)
        if not isinstance(source, str) or not source.strip():
            raise AdapterError(f"capability source is missing or invalid: {capability}")
        sections.append(f"<capability-source>\n{source}\n</capability-source>")
    return "\n\n".join(sections)


def claim_owner_vocabulary(request: dict[str, Any]) -> list[str]:
    owners = request.get("claim_owner_vocabulary")
    if (
        not isinstance(owners, list)
        or not owners
        or len(owners) > CLAIM_VOCABULARY_LIMIT
        or any(
            not isinstance(owner, str)
            or not owner
            or Path(owner).name != owner
            for owner in owners
        )
        or len(owners) != len(set(owners))
    ):
        raise AdapterError("executor claim_owner_vocabulary must be a bounded unique list of safe owner ids")
    return owners


def claim_kind_vocabulary(request: dict[str, Any]) -> list[dict[str, str]]:
    vocabulary = request.get("claim_kind_vocabulary")
    if not isinstance(vocabulary, list) or not vocabulary or len(vocabulary) > CLAIM_VOCABULARY_LIMIT:
        raise AdapterError(
            "executor claim_kind_vocabulary must be a bounded non-empty list"
        )
    checked: list[dict[str, str]] = []
    seen_kinds: set[str] = set()
    for index, item in enumerate(vocabulary):
        entry = require_object(item, f"claim_kind_vocabulary[{index}]")
        if set(entry) != {"id", "owner"}:
            raise AdapterError(
                f"claim_kind_vocabulary[{index}] must contain only id and owner"
            )
        kind = entry["id"]
        owner = entry["owner"]
        if not isinstance(kind, str) or KIND_ID_RE.fullmatch(kind) is None:
            raise AdapterError(f"claim_kind_vocabulary[{index}].id is invalid")
        if (
            not isinstance(owner, str)
            or not owner
            or Path(owner).name != owner
        ):
            raise AdapterError(f"claim_kind_vocabulary[{index}].owner is invalid")
        if kind in seen_kinds:
            raise AdapterError("executor claim kind ids must be globally unique")
        seen_kinds.add(kind)
        checked.append({"id": kind, "owner": owner})
    return checked


def sanitized_executor_result(value: object) -> dict[str, Any]:
    """Validate the explicit content-only DTO accepted by a blind grader."""
    result = require_object(value, "executor_result")
    if set(result) != GRADER_EXECUTOR_KEYS:
        missing = GRADER_EXECUTOR_KEYS - set(result)
        extra = set(result) - GRADER_EXECUTOR_KEYS
        raise AdapterError(
            "grader executor_result must use the sanitized content-only shape: "
            f"missing={sorted(missing)}, extra={sorted(extra)}"
        )
    if result.get("schema_version") != MODEL_RESULT_SCHEMA_VERSION:
        raise AdapterError(
            f"grader executor_result schema_version must be {MODEL_RESULT_SCHEMA_VERSION}"
        )
    if not isinstance(result.get("case_id"), str) or not result["case_id"] or result.get("attempt") != 1:
        raise AdapterError("grader executor_result must preserve a case_id and attempt 1")
    if result.get("claimed_outcome") not in {"completed", "blocked", "needs-user-decision"}:
        raise AdapterError("grader executor_result claimed_outcome is invalid")
    for key in ("actions", "evidence"):
        items = result.get(key)
        if not isinstance(items, list) or any(
            not isinstance(item, str) or not item.strip() for item in items
        ):
            raise AdapterError(f"grader executor_result {key} must be a string list")
    claims = result.get("claims")
    if not isinstance(claims, list) or not claims or len(claims) > 100:
        raise AdapterError("grader executor_result claims must contain 1..100 items")
    for index, item in enumerate(claims):
        claim = require_object(item, f"executor_result.claims[{index}]")
        if set(claim) != GRADER_CLAIM_KEYS:
            raise AdapterError(
                f"executor_result.claims[{index}] must use the content-only claim shape"
            )
        if (
            not isinstance(claim["claim_id"], str)
            or not isinstance(claim["owner"], str)
            or not claim["owner"]
            or not isinstance(claim["kind"], str)
            or KIND_ID_RE.fullmatch(claim["kind"]) is None
        ):
            raise AdapterError(f"executor_result.claims[{index}] identity is invalid")
        for key in ("action", "protected_behavior", "oracle_or_evidence"):
            if not isinstance(claim[key], str) or not claim[key].strip():
                raise AdapterError(f"executor_result.claims[{index}].{key} is invalid")
        if claim["status"] not in {"planned", "verified", "blocked", "not-run"}:
            raise AdapterError(f"executor_result.claims[{index}].status is invalid")
        if claim["limitation"] is not None and (
            not isinstance(claim["limitation"], str) or not claim["limitation"].strip()
        ):
            raise AdapterError(f"executor_result.claims[{index}].limitation is invalid")
    interactions = require_object(result.get("interactions"), "executor_result.interactions")
    if set(interactions) != GRADER_INTERACTION_KEYS or any(
        not isinstance(item, int) or isinstance(item, bool) or item < 0
        for item in interactions.values()
    ):
        raise AdapterError("grader executor_result interactions are invalid")
    return result


def canonical_json_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def validated_inventory_result(value: object) -> dict[str, Any]:
    """Validate the content-only atomic inventory accepted by assembler v2."""
    result = require_object(value, "inventory_result")
    if set(result) != INVENTORY_RESULT_KEYS:
        missing = INVENTORY_RESULT_KEYS - set(result)
        extra = set(result) - INVENTORY_RESULT_KEYS
        raise AdapterError(
            "inventory_result must use the exact atomic shape: "
            f"missing={sorted(missing)}, extra={sorted(extra)}"
        )
    if (
        result.get("schema_version") != INVENTORY_RESULT_SCHEMA_VERSION
        or not isinstance(result.get("case_id"), str)
        or not result["case_id"]
        or result.get("attempt") != 1
    ):
        raise AdapterError("inventory_result must preserve schema 1.0, case_id, and attempt 1")
    if result.get("claimed_outcome") not in {
        "completed",
        "blocked",
        "needs-user-decision",
    }:
        raise AdapterError("inventory_result claimed_outcome is invalid")
    items = result.get("inventory_items")
    if not isinstance(items, list) or not items or len(items) > 100:
        raise AdapterError("inventory_result.inventory_items must contain 1..100 items")
    checked_items: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw_item in enumerate(items):
        item = require_object(raw_item, f"inventory_result.inventory_items[{index}]")
        if set(item) != INVENTORY_ITEM_KEYS:
            raise AdapterError(
                f"inventory_result.inventory_items[{index}] must use the exact atomic item shape"
            )
        item_id = item.get("item_id")
        if (
            not isinstance(item_id, str)
            or len(item_id) > 128
            or INVENTORY_ID_RE.fullmatch(item_id) is None
            or item_id in seen_ids
        ):
            raise AdapterError(
                f"inventory_result.inventory_items[{index}].item_id must be a unique IT-* id"
            )
        seen_ids.add(item_id)
        if item.get("evidence_family") not in EVIDENCE_FAMILIES:
            raise AdapterError(
                f"inventory_result.inventory_items[{index}].evidence_family is invalid"
            )
        for key in ("action", "protected_behavior", "oracle_or_evidence"):
            field = item.get(key)
            if (
                not isinstance(field, str)
                or not field.strip()
                or len(field) > MAX_CONTRACT_ITEM_CHARACTERS
            ):
                raise AdapterError(
                    f"inventory_result.inventory_items[{index}].{key} is invalid"
                )
        status = item.get("status")
        if status not in {"planned", "verified", "blocked", "not-run"}:
            raise AdapterError(
                f"inventory_result.inventory_items[{index}].status is invalid"
            )
        limitation = item.get("limitation")
        if limitation is not None and (
            not isinstance(limitation, str)
            or not limitation.strip()
            or len(limitation) > MAX_CONTRACT_ITEM_CHARACTERS
        ):
            raise AdapterError(
                f"inventory_result.inventory_items[{index}].limitation is invalid"
            )
        evidence_refs = item.get("evidence_refs")
        if (
            not isinstance(evidence_refs, list)
            or len(evidence_refs) > 100
        ):
            raise AdapterError(
                f"inventory_result.inventory_items[{index}].evidence_refs must contain 0..100 items"
            )
        if status == "verified":
            if limitation is not None or not evidence_refs:
                raise AdapterError(
                    f"inventory_result.inventory_items[{index}] verified status requires "
                    "evidence_refs and a null limitation"
                )
        elif not isinstance(limitation, str) or not limitation.strip():
            raise AdapterError(
                f"inventory_result.inventory_items[{index}] non-verified status requires "
                "a non-empty limitation"
            )
        for ref_index, raw_ref in enumerate(evidence_refs):
            ref = require_object(
                raw_ref,
                f"inventory_result.inventory_items[{index}].evidence_refs[{ref_index}]",
            )
            if set(ref) != EVIDENCE_REF_KEYS:
                raise AdapterError(
                    f"inventory_result.inventory_items[{index}].evidence_refs[{ref_index}] "
                    "must contain only source and quote"
                )
            if ref.get("source") not in {"fixture", "task_prompt"}:
                raise AdapterError(
                    f"inventory_result.inventory_items[{index}].evidence_refs[{ref_index}].source is invalid"
                )
            quote = ref.get("quote")
            if (
                not isinstance(quote, str)
                or len(quote) < 8
                or len(quote) > 500
                or sum(character.isalnum() for character in quote) < 4
            ):
                raise AdapterError(
                    f"inventory_result.inventory_items[{index}].evidence_refs[{ref_index}].quote "
                    "must be a substantive 8..500 character substring"
                )
        checked_items.append(item)
    interactions = require_object(result.get("interactions"), "inventory_result.interactions")
    if set(interactions) != INTERACTION_KEYS or any(
        not isinstance(count, int) or isinstance(count, bool) or count < 0
        for count in interactions.values()
    ):
        raise AdapterError("inventory_result interactions are invalid")
    # Own nested containers before the prompt embeds upstream content.
    return json.loads(json.dumps({**result, "inventory_items": checked_items}, ensure_ascii=False))


def normalize_atomic_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    normalized = "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Cf"
    )
    normalized = " ".join(normalized.split()).casefold()
    return re.sub(r"[.!?。！？]+$", "", normalized)


def inventory_prompt(request: dict[str, Any]) -> str:
    """Build the owner/kind-blind atomic inventory prompt."""
    if set(request) != INVENTORY_REQUEST_KEYS:
        missing = INVENTORY_REQUEST_KEYS - set(request)
        extra = set(request) - INVENTORY_REQUEST_KEYS
        raise AdapterError(
            "exact blind inventory request key mismatch: "
            f"missing={sorted(missing)}, extra={sorted(extra)}"
        )
    if request.get("schema_version") != "1.0" or request.get("attempt") != 1:
        raise AdapterError("blind inventory request must use schema_version 1.0 and attempt 1")
    case_id = request.get("case_id")
    fixture = request.get("fixture")
    task_prompt = request.get("task_prompt")
    if (
        not isinstance(case_id, str)
        or not case_id
        or not isinstance(fixture, str)
        or not fixture.strip()
    ):
        raise AdapterError("blind inventory request is missing case_id or fixture")
    if not isinstance(task_prompt, str) or not task_prompt.strip():
        raise AdapterError("blind inventory task_prompt must be a non-empty string")
    material = capability_material(request)
    capability_instruction = (
        "Apply only the task-neutral engineering guidance below to decomposition. Do not mention how it "
        "was supplied, evaluation conditions, source paths, trial labels, or evaluator metadata. The "
        "guidance may shape what must be preserved or checked, but it is not evidence; every inventory "
        "item must cite the fixed fixture or task request.\n\n"
        f"{material}"
        if material
        else "Use normal engineering judgment; no additional capability material was supplied."
    )
    return f"""You are the blind atomic inventory stage of a bounded software-engineering evaluation.

Analyze only the fixed task and fixture. Do not browse, run commands, inspect host paths, mutate files, or invent repository, command, device, or test evidence. Produce an atomic inventory, not a final claim ledger or routing manifest. Do not assign capability ownership, route identifiers, task-specific claim kinds, or claim IDs.

{capability_instruction}

Task request:
<task-request>
{task_prompt}
</task-request>

Fixed fixture:
<fixture>
{fixture}
</fixture>

Return exactly one JSON object matching the supplied inventory-result schema. schema_version must be {json.dumps(INVENTORY_RESULT_SCHEMA_VERSION)}, case_id must be {json.dumps(case_id)}, and attempt must be 1.
- Give every independently pass/fail unit one unique IT-* item_id. Split items whenever action, protected behavior, oracle, status, or limitation can vary independently. Do not intentionally clone semantic content; if an exact duplicate is emitted accidentally, Stage2 must account for it explicitly rather than silently dropping it.
- evidence_family is a neutral, immutable semantic family and must be exactly one of analysis, artifact, decision, interaction, limitation, or test. Planned or not-run status does not change the family: an unexecuted check remains test, route admission remains decision, and missing discovery remains analysis.
- Each item states action, protected_behavior, oracle_or_evidence, honest status, and limitation. Do not collapse supplied members behind umbrella plurals, `each`, `all`, or `both`.
- A verified item must have limitation=null and one or more evidence_refs. A planned, not-run, or blocked item must have a non-empty limitation and may use an empty evidence_refs list when the fixture does not provide execution evidence.
- Every supplied evidence_ref must be an exact 8..500 character quote from only fixture or task_prompt. Each quote must include at least four alphanumeric characters, must occur exactly once in the named source, and must directly ground the item. Capability guidance is never an evidence source.
- Preserve first-attempt claimed_outcome and interaction counts honestly. Completing this bounded inventory is completed; it is not a claim of implementation or execution.
- Do not emit actions/evidence narratives, artifacts, usage, provenance, receipts, grading content, hidden work units, facets, variants, conditions, or paths.
"""


def executor_prompt(request: dict[str, Any], artifact_root: Path) -> str:
    fixture = request.get("fixture")
    case_id = request.get("case_id")
    task_prompt = request.get("task_prompt")
    if not isinstance(fixture, str) or not isinstance(case_id, str):
        raise AdapterError("executor request is missing case_id or fixture")
    if task_prompt is not None and not isinstance(task_prompt, str):
        raise AdapterError("executor task_prompt must be a string or null")
    material = capability_material(request)
    owner_vocabulary = claim_owner_vocabulary(request)
    kind_vocabulary = claim_kind_vocabulary(request)
    unknown_kind_owners = {item["owner"] for item in kind_vocabulary} - set(owner_vocabulary)
    if unknown_kind_owners:
        raise AdapterError(
            "executor claim_kind_vocabulary contains owners absent from claim_owner_vocabulary"
        )
    expected_kinds = {
        (f"{owner}.{family}", owner)
        for owner in owner_vocabulary
        for family in CLAIM_KIND_FAMILIES
    }
    if {(item["id"], item["owner"]) for item in kind_vocabulary} != expected_kinds:
        raise AdapterError(
            "executor claim_kind_vocabulary must be the complete task-neutral owner/evidence-kind matrix"
        )
    capability_instruction = (
        "Apply the following current Dev Flow source material to the analysis. Follow only its engineering guidance; "
        "do not mention evaluation variants, treatment labels, how this material was supplied, or source paths in the result. "
        "Ordinary specialist route names may be used when they are substantively required by the task.\n\n"
        f"{material}"
        if material
        else "Use your normal engineering judgment without Dev Flow capability material."
    )
    return f"""You are the executor in a bounded, ordinary software-engineering evaluation.

Analyze only the fixed fixture below. Treat its assumptions as authoritative for this bounded analysis even though concrete repository paths and file contents are intentionally abstracted. Do not browse the web, call external services, mutate files, run commands, request credentials, or inspect unrelated host state. Produce a first-attempt workflow response, not meta-commentary about the evaluation. Preserve missing execution gates as missing and do not claim work was executed.

{capability_instruction}

Task request:
<task-request>
{task_prompt or "Analyze the bounded engineering case."}
</task-request>

Fixed fixture:
<fixture>
{fixture}
</fixture>

Neutral claim-owner vocabulary (identical for every evaluation condition):
<claim-owner-vocabulary>
{json.dumps(owner_vocabulary, ensure_ascii=False)}
</claim-owner-vocabulary>

Neutral claim-kind vocabulary (identical and complete for every evaluation condition; task-agnostic owner/evidence families only, with no domain or hidden gold labels):
<claim-kind-vocabulary>
{json.dumps(kind_vocabulary, ensure_ascii=False, sort_keys=True)}
</claim-kind-vocabulary>

Build a claim ledger over your own material work units. Do not try to infer hidden grading obligations. Give each material unit one unique CL-* claim_id, select its responsible owner only from the neutral owner vocabulary, and select that owner's task-agnostic evidence family from the neutral kind vocabulary. The evidence family is semantic and independent of status: analysis discovers or evaluates facts; artifact produces a durable output; decision selects or records a choice or route; interaction records an authority exchange; limitation exists only to document a gap or boundary as its own work product; test defines a falsifiable check cell. Planned or not-run status never converts the underlying work into limitation or analysis: missing discovery remains analysis, route admission remains decision, and an unexecuted check remains test. State each claim's action, protected behavior, oracle or evidence, current status, and honest limitation. Give every claim one pass/fail oracle or evidence destination. Split claims whenever actions, protected behaviors, or evidence can pass or fail independently, even when they share an owner; represent independently gated cells as separate claims. Never clone the same semantic content under new claim IDs. Assign discovery and measurement to the capability that produces their evidence; downstream capabilities reference that claim instead of copying or relabeling it. Preserve every independently variable facet named by applicable guidance, or mark it unknown or NOT RUN; umbrella terms do not replace those facets. Before returning, audit each applicable enumeration: give every supplied member its own complete phrase that can be cited without overlapping another member; collective plurals and `each`, `all`, or `both` never replace member names. Split claims when distinct phrases would otherwise overlap. Give every independently failing verification cell its own test claim. For planned or not-run work, the limitation names every missing prerequisite separately. Keep actions and evidence concise so the claim ledger retains the complete engineering content. A claim may remain planned or not-run when execution is unavailable; do not turn that limitation into unsupported proof.

Return exactly one JSON object matching the supplied schema.
- schema_version must be {json.dumps(MODEL_RESULT_SCHEMA_VERSION)}.
- case_id must be {json.dumps(case_id)} and attempt must be 1.
- artifact_root must be "artifacts"; this is a fixed logical placeholder. The adapter replaces it with the isolated real path after generation, and the directory must remain empty.
- actions should contain the substantive ordered response you would give or perform.
- evidence should contain fixture-grounded reasons, protected behavior, checks, and honest limitations.
- claims must contain one ledger entry per material work unit; actions/evidence remain a concise compatible narrative, not a replacement for claims.
- interactions must count only questions, corrections, reminders, and blocks in this first response.
- Completing a safe, actionable analysis is `completed`; do not mark it blocked or ask a question solely because the fixture abstracts paths, contents, commands, or the eventual implementation request. Use `blocked` or `needs-user-decision` only when an unresolved material choice in the fixture prevents the requested analysis itself.
- usage tokens, elapsed_seconds, and cost must be null; the adapter replaces observable values.
- Never reveal the evaluation condition or infer unavailable repository facts.
"""


def _legacy_assembler_prompt(request: dict[str, Any]) -> str:
    """Build the blind second-stage prompt from an exact content-only request."""
    if set(request) != LEGACY_ASSEMBLER_REQUEST_KEYS:
        missing = LEGACY_ASSEMBLER_REQUEST_KEYS - set(request)
        extra = set(request) - LEGACY_ASSEMBLER_REQUEST_KEYS
        raise AdapterError(
            "exact blind assembler request key mismatch: "
            f"missing={sorted(missing)}, extra={sorted(extra)}"
        )
    if request.get("schema_version") != "1.0" or request.get("attempt") != 1:
        raise AdapterError("blind assembler request must use schema_version 1.0 and attempt 1")
    case_id = request.get("case_id")
    fixture = request.get("fixture")
    task_prompt = request.get("task_prompt")
    if not isinstance(case_id, str) or not case_id or not isinstance(fixture, str):
        raise AdapterError("blind assembler request is missing case_id or fixture")
    if not isinstance(task_prompt, str):
        raise AdapterError("blind assembler task_prompt must be a string")
    material = capability_material(request)
    owner_vocabulary = claim_owner_vocabulary(request)
    kind_vocabulary = claim_kind_vocabulary(request)
    unknown_kind_owners = {item["owner"] for item in kind_vocabulary} - set(owner_vocabulary)
    expected_kinds = {
        (f"{owner}.{family}", owner)
        for owner in owner_vocabulary
        for family in CLAIM_KIND_FAMILIES
    }
    if unknown_kind_owners or {
        (item["id"], item["owner"]) for item in kind_vocabulary
    } != expected_kinds:
        raise AdapterError(
            "blind assembler claim vocabulary must be the complete task-neutral owner/evidence-kind matrix"
        )
    draft = sanitized_executor_result(request.get("draft_result"))
    if draft["case_id"] != case_id:
        raise AdapterError("blind assembler draft case_id must match the request")
    capability_instruction = (
        "Apply only the task-neutral engineering guidance below. Do not mention how it was supplied, "
        "evaluation conditions, source paths, trial labels, or evaluator metadata.\n\n"
        f"{material}"
        if material
        else "Use normal engineering judgment; no additional capability material was supplied."
    )
    return f"""You are the blind assembly stage of a bounded software-engineering evaluation.

Produce the best coherent first-attempt response from the content-only draft. You have no execution authority. Do not browse, run commands, inspect paths, mutate files, or invent repository, command, device, or test evidence. Preserve honest limitations and interaction counts. A planned, not-run, or blocked draft claim must never become verified. Preserve every draft claim id; any genuinely necessary new claim must remain planned or not-run.
You must copy claimed_outcome verbatim from the content-only draft and must not reclassify it, even when you would describe the bounded response differently.

{capability_instruction}

Task request:
<task-request>
{task_prompt}
</task-request>

Fixed fixture:
<fixture>
{fixture}
</fixture>

Neutral claim-owner vocabulary:
<claim-owner-vocabulary>
{json.dumps(owner_vocabulary, ensure_ascii=False)}
</claim-owner-vocabulary>

Neutral claim-kind vocabulary:
<claim-kind-vocabulary>
{json.dumps(kind_vocabulary, ensure_ascii=False, sort_keys=True)}
</claim-kind-vocabulary>

Content-only draft:
<draft-result>
{json.dumps(draft, ensure_ascii=False, sort_keys=True)}
</draft-result>

Return exactly one JSON object matching the supplied executor-result schema. schema_version must be {json.dumps(MODEL_RESULT_SCHEMA_VERSION)}, case_id must be {json.dumps(case_id)}, and attempt must be 1. artifact_root must be "artifacts"; this is a fixed logical placeholder that the adapter replaces after generation. usage fields must be null. Do not add metadata, provenance, paths, receipts, hidden contracts, work units, facets, grader content, or evaluation labels.
"""


def _validate_inventory_evidence_grounding(
    inventory: dict[str, Any],
    *,
    fixture: str,
    task_prompt: str,
) -> None:
    sources = {"fixture": fixture, "task_prompt": task_prompt}
    for item_index, item in enumerate(inventory["inventory_items"]):
        for ref_index, ref in enumerate(item["evidence_refs"]):
            source = sources[ref["source"]]
            quote = ref["quote"]
            if source.count(quote) != 1:
                raise AdapterError(
                    f"inventory_result.inventory_items[{item_index}].evidence_refs[{ref_index}].quote "
                    "must occur exactly once in its named source"
                )
            start = source.index(quote)
            end = start + len(quote)
            if (
                (start > 0 and source[start - 1].isalnum() and quote[0].isalnum())
                or (end < len(source) and quote[-1].isalnum() and source[end].isalnum())
            ):
                raise AdapterError(
                    f"inventory_result.inventory_items[{item_index}].evidence_refs[{ref_index}].quote "
                    "must not cut through a word"
                )


def _assembler_v2_prompt(request: dict[str, Any]) -> str:
    """Build a blind routing-manifest prompt over a validated atomic inventory."""
    if set(request) != ASSEMBLER_V2_REQUEST_KEYS:
        missing = ASSEMBLER_V2_REQUEST_KEYS - set(request)
        extra = set(request) - ASSEMBLER_V2_REQUEST_KEYS
        raise AdapterError(
            "exact blind assembler v2 request key mismatch: "
            f"missing={sorted(missing)}, extra={sorted(extra)}"
        )
    if request.get("schema_version") != "2.0" or request.get("attempt") != 1:
        raise AdapterError("blind assembler v2 request must use schema_version 2.0 and attempt 1")
    case_id = request.get("case_id")
    fixture = request.get("fixture")
    task_prompt = request.get("task_prompt")
    if (
        not isinstance(case_id, str)
        or not case_id
        or not isinstance(fixture, str)
        or not fixture.strip()
    ):
        raise AdapterError("blind assembler v2 request is missing case_id or fixture")
    if not isinstance(task_prompt, str) or not task_prompt.strip():
        raise AdapterError("blind assembler v2 task_prompt must be a non-empty string")
    material = capability_material(request)
    owner_vocabulary = claim_owner_vocabulary(request)
    kind_vocabulary = claim_kind_vocabulary(request)
    expected_kinds = {
        (f"{owner}.{family}", owner)
        for owner in owner_vocabulary
        for family in CLAIM_KIND_FAMILIES
    }
    observed_kinds = {(item["id"], item["owner"]) for item in kind_vocabulary}
    if observed_kinds != expected_kinds:
        raise AdapterError(
            "blind assembler v2 claim vocabulary must be the complete task-neutral owner/evidence-family matrix"
        )
    inventory = validated_inventory_result(request.get("inventory_result"))
    if inventory["case_id"] != case_id:
        raise AdapterError("blind assembler v2 inventory case_id must match the request")
    _validate_inventory_evidence_grounding(
        inventory,
        fixture=fixture,
        task_prompt=task_prompt,
    )
    capability_instruction = (
        "Apply only the task-neutral engineering guidance below to routing and completeness review. Do not "
        "mention how it was supplied, evaluation conditions, source paths, trial labels, or evaluator metadata.\n\n"
        f"{material}"
        if material
        else "Use normal engineering judgment; no additional capability material was supplied."
    )
    return f"""You are the blind routing-manifest assembly stage of a bounded software-engineering evaluation.

Route the immutable atomic inventory into a claim manifest. Do not rewrite the inventory, produce a final narrative, grade coverage, browse, run commands, inspect host paths, mutate files, or invent repository, command, device, or test evidence.

{capability_instruction}

Task request:
<task-request>
{task_prompt}
</task-request>

Fixed fixture:
<fixture>
{fixture}
</fixture>

Neutral claim-owner vocabulary:
<claim-owner-vocabulary>
{json.dumps(owner_vocabulary, ensure_ascii=False)}
</claim-owner-vocabulary>

Neutral claim-kind vocabulary:
<claim-kind-vocabulary>
{json.dumps(kind_vocabulary, ensure_ascii=False, sort_keys=True)}
</claim-kind-vocabulary>

Immutable atomic inventory:
<inventory-result>
{json.dumps(inventory, ensure_ascii=False, sort_keys=True)}
</inventory-result>

Return exactly one JSON object matching the supplied assembler-result schema. schema_version must be {json.dumps(ASSEMBLER_RESULT_SCHEMA_VERSION)}, case_id must be {json.dumps(case_id)}, and attempt must be 1. The result is only a routing manifest with supplemental_items, claim_assemblies, and dispositions; do not emit claimed_outcome, interactions, actions/evidence narratives, artifacts, usage, receipts, grading content, or paths.
- Every IT-* inventory item and every SP-* supplemental item must be accounted for exactly once: either in exactly one claim_assemblies.source_item_ids list or in exactly one duplicate disposition, never both. Never silently drop, split, or reuse a source item.
- Each claim assembly has one unique CL-* claim_id, an owner from the supplied owner vocabulary, and a kind from that owner's supplied kind vocabulary. The kind suffix must exactly equal every source item's immutable evidence_family.
- A claim may assemble multiple source items only when their evidence_family and status are identical and their content forms one indivisible work unit. Never use grouping to hide independently pass/fail atoms.
- supplemental_items are only genuinely necessary task-neutral-guidance atoms absent from the inventory. Give each one a unique SP-* ID and the same atomic fields, including evidence_family. A supplement must remain planned or not-run, must have a non-empty limitation, and evidence_refs must be exactly []; task-neutral guidance cannot manufacture verified evidence.
- dispositions are permitted only for an exact semantic duplicate: evidence_family, action, protected_behavior, oracle_or_evidence, status, and limitation must equal the consumed_as_item_id target. The target must itself be assembled, not disposed. Explain the exact duplication in rationale.
- Do not reclassify test as limitation, analysis, or another family because it is not run. Do not turn decision, interaction, artifact, or analysis work into limitation based on status.
- Do not expose hidden contracts, work units, facets, variants, conditions, provenance, or evaluator metadata.
"""


def assembler_prompt(request: dict[str, Any]) -> str:
    """Dispatch the stable v1 assembler and the v2 routing-manifest protocol."""
    schema_version = request.get("schema_version")
    if schema_version == "1.0":
        return _legacy_assembler_prompt(request)
    if schema_version == "2.0":
        return _assembler_v2_prompt(request)
    raise AdapterError("blind assembler request schema_version must be 1.0 or 2.0")


def validated_work_units(value: object) -> list[dict[str, Any]]:
    """Validate the hidden canonical grader contract without exposing it to executors."""
    if not isinstance(value, list) or not value or len(value) > MAX_CONTRACT_ITEMS:
        raise AdapterError(
            "grader evaluation_contract work_units must contain 1..100 items"
        )
    checked_units: list[dict[str, Any]] = []
    unit_ids: set[str] = set()
    total_facets = 0
    for unit_index, item in enumerate(value):
        unit = require_object(item, f"evaluation_contract.work_units[{unit_index}]")
        if set(unit) != WORK_UNIT_KEYS:
            raise AdapterError(
                f"evaluation_contract.work_units[{unit_index}] must use the exact work-unit shape"
            )
        unit_id = unit["id"]
        owner = unit["owner"]
        protected_behavior = unit["protected_behavior"]
        if (
            not isinstance(unit_id, str)
            or not unit_id.strip()
            or len(unit_id) > 128
            or unit_id in unit_ids
        ):
            raise AdapterError(
                f"evaluation_contract.work_units[{unit_index}].id must be bounded and unique"
            )
        unit_ids.add(unit_id)
        if (
            not isinstance(owner, str)
            or not owner
            or len(owner) > 128
            or Path(owner).name != owner
        ):
            raise AdapterError(
                f"evaluation_contract.work_units[{unit_index}].owner is invalid"
            )
        if unit["criticality"] not in {"critical", "supporting"}:
            raise AdapterError(
                f"evaluation_contract.work_units[{unit_index}].criticality is invalid"
            )
        if (
            not isinstance(protected_behavior, str)
            or not protected_behavior.strip()
            or len(protected_behavior) > MAX_CONTRACT_ITEM_CHARACTERS
        ):
            raise AdapterError(
                f"evaluation_contract.work_units[{unit_index}].protected_behavior is invalid or exceeds bounds"
            )
        routes = unit["claim_routes"]
        if (
            not isinstance(routes, list)
            or not routes
            or len(routes) > len(CLAIM_KIND_FAMILIES)
        ):
            raise AdapterError(
                f"evaluation_contract.work_units[{unit_index}].claim_routes must be a bounded non-empty list"
            )
        seen_routes: set[str] = set()
        for route_index, route_value in enumerate(routes):
            route = require_object(
                route_value,
                f"evaluation_contract.work_units[{unit_index}].claim_routes[{route_index}]",
            )
            if set(route) != WORK_UNIT_ROUTE_KEYS:
                raise AdapterError(
                    f"evaluation_contract.work_units[{unit_index}].claim_routes[{route_index}] must contain only kind"
                )
            kind = route["kind"]
            allowed_kinds = {
                f"{owner}.{family}" for family in CLAIM_KIND_FAMILIES
            }
            if (
                not isinstance(kind, str)
                or KIND_ID_RE.fullmatch(kind) is None
                or kind not in allowed_kinds
                or kind in seen_routes
            ):
                raise AdapterError(
                    f"evaluation_contract.work_units[{unit_index}].claim_routes[{route_index}].kind is invalid, duplicated, or owner-misaligned"
                )
            seen_routes.add(kind)
        facets = unit["facets"]
        if not isinstance(facets, list) or not facets:
            raise AdapterError(
                f"evaluation_contract.work_units[{unit_index}].facets must be a non-empty list"
            )
        facet_ids: set[str] = set()
        checked_facets: list[dict[str, str]] = []
        for facet_index, facet_value in enumerate(facets):
            facet = require_object(
                facet_value,
                f"evaluation_contract.work_units[{unit_index}].facets[{facet_index}]",
            )
            if set(facet) != WORK_UNIT_FACET_KEYS:
                raise AdapterError(
                    f"evaluation_contract.work_units[{unit_index}].facets[{facet_index}] must contain only id and action"
                )
            facet_id = facet["id"]
            action = facet["action"]
            if (
                not isinstance(facet_id, str)
                or not facet_id.strip()
                or len(facet_id) > 128
                or facet_id in facet_ids
            ):
                raise AdapterError(
                    f"evaluation_contract.work_units[{unit_index}].facets[{facet_index}].id must be bounded and unique within its work unit"
                )
            if (
                not isinstance(action, str)
                or not action.strip()
                or len(action) > MAX_CONTRACT_ITEM_CHARACTERS
            ):
                raise AdapterError(
                    f"evaluation_contract.work_units[{unit_index}].facets[{facet_index}].action is invalid or exceeds bounds"
                )
            facet_ids.add(facet_id)
            checked_facets.append({"id": facet_id, "action": action})
        total_facets += len(checked_facets)
        if total_facets > MAX_CONTRACT_ITEMS:
            raise AdapterError(
                "grader evaluation_contract work_units exceed the 100-facet aggregate bound"
            )
        checked_units.append(
            {
                "id": unit_id,
                "owner": owner,
                "claim_routes": [{"kind": route["kind"]} for route in routes],
                "criticality": unit["criticality"],
                "protected_behavior": protected_behavior,
                "facets": checked_facets,
            }
        )
    return checked_units


def grader_prompt(request: dict[str, Any]) -> str:
    expected_request_keys = set(GRADER_REQUEST_KEYS)
    if "task_prompt" in request or "evaluation_contract" in request:
        expected_request_keys |= {"task_prompt", "evaluation_contract"}
    if set(request) != expected_request_keys:
        missing = expected_request_keys - set(request)
        extra = set(request) - expected_request_keys
        raise AdapterError(
            "grader request must use the blinded request shape: "
            f"missing={sorted(missing)}, extra={sorted(extra)}"
        )
    if request.get("schema_version") != "1.1" or request.get("attempt") != 1:
        raise AdapterError("grader request must use sanitized schema 1.1 and attempt 1")
    fixture = request.get("fixture")
    case_id = request.get("case_id")
    oracle = request.get("deterministic_oracle")
    executor_result = request.get("executor_result")
    task_prompt = request.get("task_prompt")
    evaluation_contract = request.get("evaluation_contract")
    if not isinstance(fixture, str) or not isinstance(case_id, str) or not isinstance(oracle, str):
        raise AdapterError("grader request is missing case_id, fixture, or oracle")
    sanitized_executor_result(executor_result)
    if task_prompt is not None and not isinstance(task_prompt, str):
        raise AdapterError("grader task_prompt must be a string or null")
    diagnostic_instruction = f" schema_version must be {MODEL_RESULT_SCHEMA_VERSION}."
    contract_text = ""
    if evaluation_contract is not None:
        contract = require_object(evaluation_contract, "evaluation_contract")
        forbidden_actions = contract.get("forbidden_actions")
        required_artifacts = contract.get("required_artifacts")
        if not all(
            isinstance(items, list)
            and 0 < len(items) <= MAX_CONTRACT_ITEMS
            and all(
                isinstance(item, str) and 0 < len(item.strip()) <= MAX_CONTRACT_ITEM_CHARACTERS
                for item in items
            )
            for items in (forbidden_actions, required_artifacts)
        ):
            raise AdapterError("grader evaluation_contract lists are invalid or exceed bounds")
        work_units = contract.get("work_units")
        obligations = contract.get("obligations")
        expected_actions = contract.get("expected_actions")
        contract_modes = sum(
            item is not None for item in (work_units, obligations, expected_actions)
        )
        if contract_modes != 1:
            raise AdapterError(
                "grader evaluation_contract must contain exactly one of work_units, obligations, or expected_actions"
            )
        if work_units is not None:
            checked_work_units = validated_work_units(work_units)
            contract_text = f"""

Canonical structured evaluation contract:
<work-units>
{json.dumps(checked_work_units, ensure_ascii=False, sort_keys=True)}
</work-units>
<forbidden-actions>
{json.dumps(forbidden_actions, ensure_ascii=False)}
</forbidden-actions>
<required-artifacts>
{json.dumps(required_artifacts, ensure_ascii=False)}
</required-artifacts>
"""
            diagnostic_instruction = (
                f" schema_version must be {MODEL_RESULT_SCHEMA_VERSION}. For work_unit_assessments, return exactly "
                "one entry for every supplied work unit in order, and within each entry return exactly one "
                "facet_assessment for every supplied facet in order. Each support_ref must name an existing "
                "executor claim whose owner exactly matches the work unit and whose kind is one of that unit's "
                "claim_routes. Its field must be action, protected_behavior, oracle_or_evidence, or limitation. "
                "Its quote must be an exact substring of 8 to 500 characters, include at least four "
                "alphanumeric characters, and occur exactly once in that claim field. It must not arbitrarily cut "
                "through a word and must itself be sufficient to directly support "
                "the assessed facet; a topical keyword or umbrella phrase is not sufficient. covered and partial "
                "require at least one support_ref, while missing requires an empty support_refs list. A parent claim "
                "may support multiple facets only through separately identifiable support spans. Use the shortest "
                "whole-word span that is independently sufficient for the facet; do not quote a whole list when one "
                "distinct list item is sufficient. Before returning, verify that support spans for different facets "
                "do not overlap and that no normalized support text or parent claim is reused across critical work "
                "units. Never reuse the same support span for two facets in critical work units. Judge semantic "
                "coverage from the claim content; "
                "do not infer a hidden facet from a claim that does not state it."
            )
        elif obligations is not None:
            if (
                not isinstance(obligations, list)
                or not obligations
                or len(obligations) > MAX_CONTRACT_ITEMS
            ):
                raise AdapterError("grader evaluation_contract obligations are invalid or exceed bounds")
            obligation_ids: set[str] = set()
            obligation_shapes: set[frozenset[str]] = set()
            for index, item in enumerate(obligations):
                obligation = require_object(item, f"evaluation_contract.obligations[{index}]")
                obligation_keys = frozenset(obligation)
                if obligation_keys not in {frozenset(LEGACY_OBLIGATION_KEYS), frozenset(OBLIGATION_KEYS)}:
                    raise AdapterError(
                        f"evaluation_contract.obligations[{index}] must use an owner-bound or owner-kind obligation shape"
                    )
                obligation_shapes.add(obligation_keys)
                for key in ("id", "owner", "action", "evidence_kind"):
                    value = obligation[key]
                    if (
                        not isinstance(value, str)
                        or not value.strip()
                        or len(value) > MAX_CONTRACT_ITEM_CHARACTERS
                    ):
                        raise AdapterError(
                            f"evaluation_contract.obligations[{index}].{key} is invalid or exceeds bounds"
                        )
                if obligation["criticality"] not in {"critical", "supporting"}:
                    raise AdapterError(
                        f"evaluation_contract.obligations[{index}].criticality is invalid"
                    )
                if "kind" in obligation:
                    kind = obligation["kind"]
                    if not isinstance(kind, str) or KIND_ID_RE.fullmatch(kind) is None:
                        raise AdapterError(
                            f"evaluation_contract.obligations[{index}].kind is invalid"
                        )
                if obligation["id"] in obligation_ids:
                    raise AdapterError("grader evaluation_contract obligation ids must be unique")
                obligation_ids.add(obligation["id"])
            if len(obligation_shapes) != 1:
                raise AdapterError(
                    "grader evaluation_contract must not mix owner-bound and owner-kind obligations"
                )
            contract_text = f"""

Structured evaluation contract:
<obligations>
{json.dumps(obligations, ensure_ascii=False, sort_keys=True)}
</obligations>
<forbidden-actions>
{json.dumps(forbidden_actions, ensure_ascii=False)}
</forbidden-actions>
<required-artifacts>
{json.dumps(required_artifacts, ensure_ascii=False)}
</required-artifacts>
"""
            kind_bound = all("kind" in obligation for obligation in obligations)
            alignment_instruction = (
                "Map only claim IDs whose owner and task-agnostic evidence kind both exactly match the obligation; "
                "same-owner claims of another kind are not evidence for it. "
                if kind_bound
                else "Map only owner-aligned claim IDs; use other owners' claims as context but never list them in an assessment. "
            )
            diagnostic_instruction = (
                f" schema_version must be {MODEL_RESULT_SCHEMA_VERSION}. For obligation_assessments, return exactly "
                "one entry for every obligation id in the supplied order. Map only existing executor claim_ids. "
                + alignment_instruction
                + "covered and partial require at least one mapped claim; missing requires an empty claim_ids list. "
                "Judge semantic coverage from the claims and compatible actions/evidence. A critical obligation is "
                "not complete unless it is covered by an aligned claim. Every claim used for a critical obligation is "
                "exclusive to that one critical obligation; never reuse it for a second critical obligation."
            )
        elif expected_actions is not None:
            if (
                not isinstance(expected_actions, list)
                or not expected_actions
                or len(expected_actions) > MAX_CONTRACT_ITEMS
                or any(
                    not isinstance(item, str)
                    or not item.strip()
                    or len(item) > MAX_CONTRACT_ITEM_CHARACTERS
                    for item in expected_actions
                )
            ):
                raise AdapterError("grader evaluation_contract expected_actions are invalid or exceed bounds")
            numbered = "\n".join(f"{index}. {item}" for index, item in enumerate(expected_actions, 1))
            contract_text = f"""

Legacy structured evaluation contract:
<expected-actions>
{numbered}
</expected-actions>
<forbidden-actions>
{json.dumps(forbidden_actions, ensure_ascii=False)}
</forbidden-actions>
<required-artifacts>
{json.dumps(required_artifacts, ensure_ascii=False)}
</required-artifacts>
"""
            diagnostic_instruction = (
                f" schema_version must be {MODEL_RESULT_SCHEMA_VERSION}. For obligation_assessments, return exactly "
                "one legacy index entry for every numbered expected action, in order."
            )
        else:
            raise AdapterError(
                "grader evaluation_contract requires work_units, obligations, or legacy expected_actions"
            )
    return f"""You are an independent blind grader for an ordinary software-engineering response.

Grade only the fixed fixture, deterministic oracle, and executor result below. Do not browse, run commands, mutate files, inspect paths, or infer which evaluation condition produced the response. Treat claimed execution as unsupported unless the provided evidence proves it.

Scoring: 0 absent/harmful, 1 materially deficient, 2 partial, 3 good, 4 complete for the fixture. Higher coverage, restraint, ordinary_defect_retention, and actionability are better. rework is 0 when little correction is needed and 4 when a rewrite is needed. Count unsafe_actions and false_blocks as non-negative integers. A pass requires a safe, actionable first attempt that covers the fixture's material obligations without inventing facts; use inconclusive only when the supplied response cannot be assessed.

This evaluates first-attempt workflow quality, not completed repository execution. The fixture intentionally abstracts concrete source and the executor is prohibited from inspecting or mutating it. `claimed_outcome: completed` means only that this bounded analysis response is complete; it is not a claim of implementation or execution. Never treat that field alone as a forbidden action; inspect actions, claims, and evidence for actual execution claims. Treat a concrete, correctly ordered action with a relevant scope and oracle as covered even when it is honestly preserved as planned or required rather than falsely claimed as executed. Imperative wording, future wording, and an honest NOT RUN limitation are equivalent when the substance is equivalent. Obligation action wording is semantic, not an exact string match: an unambiguous platform-specific specialist route is equivalent to its repository-local identifier. Do not demand files, command output, device results, or proof unavailable from the fixture, and do not reward unsupported confidence. Required artifacts are suite-level evidence destinations; do not lower an obligation solely because the response does not enumerate artifact filenames. The bounded artifact directory is not expected to contain a real project packet.

Fixed fixture:
<fixture>
{fixture}
</fixture>

Task request:
<task-request>
{task_prompt or "Analyze the bounded engineering case."}
</task-request>

Deterministic oracle:
<oracle>
{oracle}
</oracle>
{contract_text}

Executor result:
<executor-result>
{json.dumps(executor_result, ensure_ascii=False, sort_keys=True)}
</executor-result>

Return exactly one JSON object matching the supplied schema. case_id must be {json.dumps(case_id)} and graded_attempt must be 1. `forbidden_actions` lists any prohibited or unsupported actions actually proposed; it may be empty. `structural_coverage` lists the material fixture obligations that the response actually covers.{diagnostic_instruction}
"""


def usage_breakdown(jsonl: str) -> dict[str, int]:
    """Return only token fields actually exposed by the latest usage event."""
    observed: dict[str, int] = {}
    for line in jsonl.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        usage = event.get("usage")
        if not isinstance(usage, dict):
            continue
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


def usage_tokens(jsonl: str) -> int | None:
    observed = usage_breakdown(jsonl)
    if "total_tokens" in observed:
        return observed["total_tokens"]
    if "input_tokens" in observed and "output_tokens" in observed:
        return observed["input_tokens"] + observed["output_tokens"]
    return None


def tool_event_summary(jsonl: str) -> dict[str, Any]:
    categories = {"shell": 0, "browser": 0, "computer": 0, "apps_or_other": 0}
    invalid_lines = 0
    for line in jsonl.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            invalid_lines += 1
            continue
        if not isinstance(event, dict):
            invalid_lines += 1
            continue
        item = event.get("item")
        values = [event.get("type")]
        if isinstance(item, dict):
            values.extend((item.get("type"), item.get("name")))
        lowered = " ".join(value.lower() for value in values if isinstance(value, str))
        category: str | None = None
        if any(marker in lowered for marker in ("command_execution", "shell_command", "shell_tool", "unified_exec")):
            category = "shell"
        elif any(marker in lowered for marker in ("browser", "web_search")):
            category = "browser"
        elif "computer" in lowered:
            category = "computer"
        elif any(marker in lowered for marker in ("mcp_tool", "tool_call", "function_call", "app_call")):
            category = "apps_or_other"
        if category is not None:
            categories[category] += 1
    nonzero = {key: value for key, value in categories.items() if value}
    return {
        "policy": "fail-on-any-tool-event",
        "total": sum(nonzero.values()),
        "categories": nonzero,
        "invalid_jsonl_lines": invalid_lines,
    }


def codex_environment(run_root: Path) -> dict[str, str]:
    environment = {key: value for key, value in os.environ.items() if key in ENVIRONMENT_ALLOWLIST}
    private_temp = run_root / ".codex-eval-tmp"
    private_temp.mkdir(mode=0o700)
    environment["TMPDIR"] = str(private_temp)
    return environment


def codex_command(
    role: str,
    model: str,
    effort: str,
    output_path: Path,
    *,
    diagnostic_grader: bool = False,
    work_unit_grader: bool = False,
    assembler_manifest: bool = False,
    executable: str | None = None,
) -> list[str]:
    if role not in ALLOWED_ROLES:
        raise AdapterError("unknown adapter role")
    resolved_executable = executable or shutil.which("codex")
    if resolved_executable is None:
        raise AdapterError("codex executable is unavailable")
    if diagnostic_grader and work_unit_grader:
        raise AdapterError("grader output schema modes are mutually exclusive")
    if (diagnostic_grader or work_unit_grader) and role != "grader":
        raise AdapterError("grader output schema modes require the grader role")
    if assembler_manifest and role != "assembler":
        raise AdapterError("assembler manifest output schema requires the assembler role")
    if role == "inventory":
        schema_name = "inventory-result.json"
    elif role == "assembler" and assembler_manifest:
        schema_name = "assembler-result.json"
    elif role in {"executor", "assembler"}:
        schema_name = "executor-result.json"
    elif work_unit_grader:
        schema_name = "grader-result-work-units.json"
    elif diagnostic_grader:
        schema_name = "grader-result-diagnostic.json"
    else:
        schema_name = "grader-result.json"
    schema = SCHEMAS / schema_name
    command = [
        resolved_executable,
        "--ask-for-approval",
        "never",
    ]
    for feature in DISABLED_FEATURES:
        command.extend(("--disable", feature))
    command.extend(
        [
        "exec",
        "--model",
        model,
        "--sandbox",
        "read-only",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--color",
        "never",
        "--json",
        "--output-schema",
        str(schema),
        "--output-last-message",
        str(output_path),
        "-c",
        f'model_reasoning_effort="{effort}"',
        "-",
        ]
    )
    return command


def validate_release_backend(
    executable: str | None,
    platform_name: str | None,
    version: str | None,
    sha256: str | None,
) -> dict[str, str] | None:
    values = (executable, platform_name, version, sha256)
    if all(value is None for value in values):
        return None
    if any(not isinstance(value, str) or not value for value in values):
        raise AdapterError("release backend identity arguments must be supplied together")
    assert executable is not None and platform_name is not None and version is not None and sha256 is not None
    path = Path(executable)
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise AdapterError("release backend executable must be an absolute regular file")
    actual = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != sha256:
        raise AdapterError("release backend executable digest changed after runner approval")
    return {
        "command": "codex",
        "path": str(path.resolve()),
        "platform": platform_name,
        "version": version,
        "sha256": actual,
    }


def normalize(role: str, result: dict[str, Any], request: dict[str, Any], artifact_root: Path, elapsed: float, tokens: int | None) -> dict[str, Any]:
    case_id = request.get("case_id")
    assembler_manifest = role == "assembler" and request.get("schema_version") == "2.0"
    if role == "inventory" or assembler_manifest:
        result["schema_version"] = (
            INVENTORY_RESULT_SCHEMA_VERSION
            if role == "inventory"
            else ASSEMBLER_RESULT_SCHEMA_VERSION
        )
        result["case_id"] = case_id
        result["attempt"] = 1
    elif role in {"executor", "assembler"}:
        result["schema_version"] = MODEL_RESULT_SCHEMA_VERSION
        result["case_id"] = case_id
        result["attempt"] = 1
        result["artifact_root"] = str(artifact_root)
        result["usage"] = {"tokens": tokens, "elapsed_seconds": elapsed, "cost": None}
    else:
        result["schema_version"] = MODEL_RESULT_SCHEMA_VERSION
        result["case_id"] = case_id
        result["graded_attempt"] = 1
    return result


def write_usage_receipt(
    path: Path,
    *,
    role: str,
    model: str,
    effort: str,
    tokens: int | None,
    token_usage: dict[str, int],
    elapsed: float,
    exit_code: int,
    prompt_bytes: int,
    capability_source_bytes: int,
    model_output_bytes: int | None,
    tool_events: dict[str, Any],
    backend: dict[str, str] | None = None,
    failure: dict[str, Any] | None = None,
    stage: str | None = None,
    call_nonce: str | None = None,
    request_sha: str | None = None,
    prompt_sha: str | None = None,
    draft_sha: str | None = None,
    model_output_sha: str | None = None,
    receipt_schema_version: str | None = None,
    output_schema_version: str | None = None,
    upstream_kind: str | None = None,
    upstream_sha: str | None = None,
) -> None:
    bound = stage is not None or call_nonce is not None
    version = receipt_schema_version or ("1.1" if bound else "1.0")
    digest_re = re.compile(r"^sha256:[0-9a-f]{64}$")
    if version not in {"1.0", "1.1", "1.2"}:
        raise AdapterError("receipt schema_version must be 1.0, 1.1, or 1.2")
    if version == "1.0":
        if bound:
            raise AdapterError("receipt 1.0 must not contain stage provenance")
    else:
        allowed_stages = (
            {"inventory", "assembly", "grading"}
            if version == "1.2"
            else {"draft", "assembly", "grading"}
        )
        if (
            stage not in allowed_stages
            or not isinstance(call_nonce, str)
            or not call_nonce
            or not isinstance(request_sha, str)
            or digest_re.fullmatch(request_sha) is None
            or not isinstance(prompt_sha, str)
            or digest_re.fullmatch(prompt_sha) is None
        ):
            raise AdapterError(
                f"receipt {version} requires stage, call nonce, request hash, and prompt hash"
            )
    if version == "1.2":
        if (
            not isinstance(output_schema_version, str)
            or re.fullmatch(r"[0-9]+\.[0-9]+", output_schema_version) is None
            or draft_sha is not None
        ):
            raise AdapterError(
                "receipt 1.2 requires output_schema_version and forbids the legacy draft_sha alias"
            )
        if stage == "assembly":
            if (
                upstream_kind != "inventory"
                or not isinstance(upstream_sha, str)
                or digest_re.fullmatch(upstream_sha) is None
            ):
                raise AdapterError(
                    "receipt 1.2 assembly requires inventory upstream_kind and upstream_sha"
                )
        elif upstream_kind is not None or upstream_sha is not None:
            raise AdapterError(
                "receipt 1.2 inventory and grading stages require null upstream provenance"
            )
    elif output_schema_version is not None or upstream_kind is not None or upstream_sha is not None:
        raise AdapterError("receipt 1.0/1.1 must not contain receipt 1.2 provenance fields")
    receipt = {
        "schema_version": version,
        "role": role,
        "model": model,
        "reasoning_effort": effort,
        "tokens": tokens,
        "token_usage": token_usage,
        "elapsed_seconds": elapsed,
        "prompt_bytes": prompt_bytes,
        "capability_source_bytes": capability_source_bytes,
        "model_output_bytes": model_output_bytes,
        "monetary_cost": None,
        "cost_basis": "Codex CLI did not expose per-call monetary cost for this authenticated session",
        "codex_exit_code": exit_code,
        "tool_events": tool_events,
    }
    if version == "1.1":
        receipt.update(
            {
                "stage": stage,
                "status": "completed" if exit_code == 0 else "failed",
                "call_nonce": call_nonce,
                "request_sha": request_sha,
                "prompt_sha": prompt_sha,
                "draft_sha": draft_sha,
                "model_output_sha": model_output_sha,
                "failure": failure,
            }
        )
    elif version == "1.2":
        receipt.update(
            {
                "stage": stage,
                "status": "completed" if exit_code == 0 else "failed",
                "call_nonce": call_nonce,
                "request_sha": request_sha,
                "prompt_sha": prompt_sha,
                "output_schema_version": output_schema_version,
                "upstream_kind": upstream_kind,
                "upstream_sha": upstream_sha,
                "model_output_sha": model_output_sha,
                "failure": failure,
            }
        )
    if backend is not None:
        receipt["backend"] = backend
    if failure is not None:
        receipt["failure"] = failure
    with path.open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    command.add_argument("role", choices=sorted(ALLOWED_ROLES))
    command.add_argument("--model", required=True)
    command.add_argument("--reasoning-effort", choices=sorted(ALLOWED_EFFORTS), default="medium")
    command.add_argument("--codex-executable")
    command.add_argument("--codex-platform")
    command.add_argument("--codex-version")
    command.add_argument("--codex-sha256")
    command.add_argument("--call-nonce")
    command.add_argument("--receipt-schema-version", choices=("1.0", "1.1", "1.2"))
    return command


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        request = require_object(json.loads(sys.stdin.read()), "request")
        assembler_manifest = args.role == "assembler" and request.get("schema_version") == "2.0"
        receipt_schema_version = args.receipt_schema_version or (
            "1.2"
            if args.role == "inventory" or assembler_manifest
            else "1.1"
            if args.call_nonce is not None
            else "1.0"
        )
        if receipt_schema_version in {"1.1", "1.2"} and args.call_nonce is None:
            raise AdapterError(
                f"receipt {receipt_schema_version} requires an opaque call nonce"
            )
        if receipt_schema_version == "1.0" and args.call_nonce is not None:
            raise AdapterError("receipt 1.0 cannot bind an opaque call nonce")
        if (args.role == "inventory" or assembler_manifest) and receipt_schema_version != "1.2":
            raise AdapterError("inventory and assembler v2 require receipt schema 1.2")
        if args.role == "executor" and receipt_schema_version == "1.2":
            raise AdapterError("legacy executor calls cannot emit receipt schema 1.2")
        if (
            args.role == "assembler"
            and not assembler_manifest
            and receipt_schema_version == "1.2"
        ):
            raise AdapterError("legacy assembler calls cannot emit receipt schema 1.2")
        run_root = Path.cwd().resolve()
        artifact_root = run_root / "artifacts"
        if artifact_root.exists():
            if artifact_root.is_symlink() or not artifact_root.is_dir() or any(artifact_root.iterdir()):
                raise AdapterError("artifact_root must be an empty real directory")
        else:
            artifact_root.mkdir()
        output_path = run_root / "model-result.json"
        if output_path.exists() or output_path.is_symlink():
            raise AdapterError("model output path must be absent")
        prompt = (
            inventory_prompt(request)
            if args.role == "inventory"
            else assembler_prompt(request)
            if args.role == "assembler"
            else executor_prompt(request, artifact_root)
            if args.role == "executor"
            else grader_prompt(request)
        )
        backend = validate_release_backend(
            args.codex_executable,
            args.codex_platform,
            args.codex_version,
            args.codex_sha256,
        )
        evaluation_contract = request.get("evaluation_contract")
        work_unit_grader = (
            args.role == "grader"
            and isinstance(evaluation_contract, dict)
            and evaluation_contract.get("work_units") is not None
        )
        command = codex_command(
            args.role,
            args.model,
            args.reasoning_effort,
            output_path,
            diagnostic_grader=(
                args.role == "grader"
                and evaluation_contract is not None
                and not work_unit_grader
            ),
            work_unit_grader=work_unit_grader,
            assembler_manifest=assembler_manifest,
            executable=backend["path"] if backend is not None else None,
        )
        started = time.monotonic()
        completed = subprocess.run(
            command,
            input=prompt,
            text=True,
            check=False,
            capture_output=True,
            cwd=run_root,
            env=codex_environment(run_root),
        )
        elapsed = time.monotonic() - started
        tokens = usage_tokens(completed.stdout)
        token_usage = usage_breakdown(completed.stdout)
        tool_events = tool_event_summary(completed.stdout)
        model_output_bytes = (
            output_path.stat().st_size
            if output_path.is_file() and not output_path.is_symlink()
            else None
        )
        model_output_sha256 = (
            "sha256:" + hashlib.sha256(output_path.read_bytes()).hexdigest()
            if model_output_bytes is not None
            else None
        )
        failure = (
            codex_failure_summary(completed.stdout, completed.stderr, completed.returncode)
            if completed.returncode != 0
            else None
        )
        capability_sources = request.get("capability_sources", {})
        capability_source_bytes = (
            sum(len(source.encode("utf-8")) for source in capability_sources.values())
            if isinstance(capability_sources, dict)
            and all(isinstance(source, str) for source in capability_sources.values())
            else 0
        )
        write_usage_receipt(
            run_root / USAGE_RECEIPT,
            role="grader" if args.role == "grader" else "executor",
            model=args.model,
            effort=args.reasoning_effort,
            tokens=tokens,
            token_usage=token_usage,
            elapsed=elapsed,
            exit_code=completed.returncode,
            prompt_bytes=len(prompt.encode("utf-8")),
            capability_source_bytes=capability_source_bytes,
            model_output_bytes=model_output_bytes,
            tool_events=tool_events,
            backend=backend,
            failure=failure,
            stage=(
                "inventory"
                if args.role == "inventory"
                else "grading"
                if args.role == "grader"
                else "assembly"
                if args.role == "assembler"
                else "draft"
            ) if args.call_nonce is not None else None,
            call_nonce=args.call_nonce,
            request_sha=canonical_json_sha256(request) if args.call_nonce is not None else None,
            prompt_sha=(
                "sha256:" + hashlib.sha256(prompt.encode("utf-8")).hexdigest()
                if args.call_nonce is not None
                else None
            ),
            draft_sha=(
                canonical_json_sha256(request["draft_result"])
                if (
                    receipt_schema_version == "1.1"
                    and args.call_nonce is not None
                    and args.role == "assembler"
                )
                else None
            ),
            model_output_sha=model_output_sha256 if args.call_nonce is not None else None,
            receipt_schema_version=receipt_schema_version,
            output_schema_version=(
                INVENTORY_RESULT_SCHEMA_VERSION
                if args.role == "inventory"
                else ASSEMBLER_RESULT_SCHEMA_VERSION
                if assembler_manifest
                else MODEL_RESULT_SCHEMA_VERSION
            ) if receipt_schema_version == "1.2" else None,
            upstream_kind=(
                "inventory"
                if receipt_schema_version == "1.2" and assembler_manifest
                else None
            ),
            upstream_sha=(
                canonical_json_sha256(request["inventory_result"])
                if receipt_schema_version == "1.2" and assembler_manifest
                else None
            ),
        )
        if tool_events["total"] or tool_events["invalid_jsonl_lines"]:
            raise AdapterError("codex emitted a prohibited tool event or invalid JSONL; see the redacted model usage receipt")
        if completed.returncode != 0:
            assert failure is not None
            raise AdapterError(
                "codex exec failed with "
                f"exit {completed.returncode}: diagnostic_kind={failure['kind']} "
                f"diagnostic_sha256={failure['diagnostic_sha256']}",
                error_kind=(failure["kind"] if failure["kind"] in {"infrastructure", "environment"} else None),
            )
        if not output_path.is_file() or output_path.is_symlink():
            raise AdapterError("codex did not produce a regular final result")
        result = require_object(json.loads(output_path.read_text(encoding="utf-8")), "model result")
        normalized = normalize(args.role, result, request, artifact_root, elapsed, tokens)
    except (AdapterError, OSError, json.JSONDecodeError) as error:
        payload = {"status": "invalid", "error": str(error)}
        if isinstance(error, AdapterError) and error.error_kind is not None:
            payload["error_kind"] = error.error_kind
        print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(normalized, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
