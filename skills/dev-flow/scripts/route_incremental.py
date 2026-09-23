"""Stateless, privacy-minimized route identity and recalibration."""

from __future__ import annotations

import hashlib
import json
import re
import stat
from pathlib import Path
from typing import Any


ROUTE_BASIS_SCHEMA = "dev-flow.route-basis.v1"
ROUTER_SEMANTICS_VERSION = "dev-flow.route-semantics.rc8.v1"
MAX_PREVIOUS_ROUTE_BYTES = 512 * 1024
MAX_BASIS_LIST_ITEMS = 64
MAX_BASIS_VALUE_CHARS = 256
ROUTE_BASIS_OPTION_DIMENSIONS = {
    "intent": {"intent_task"},
    "target_revision": {"intent_task"},
    "task_type": {"intent_task"},
    "risk": {"capabilities"},
    "need": {"capabilities"},
    "ui_impact": {"requirement", "scope_owners"},
    "ambiguity": {"requirement"},
    "material_exposure": {"review"},
    "repo_fact": {"repository_readiness"},
    "effective_skill": {"repository_readiness"},
    "method_signal": {"method"},
    "method_prerequisite": {"method"},
    "method_depth": {"method"},
    "requirement_class": {"requirement"},
    "understanding_confirmed": {"requirement"},
    "waive_understanding_confirmation": {"requirement"},
    "user_choice_open": {"requirement"},
    "profile_operation": {"scope_owners"},
    "suite_maintenance": {"scope_owners"},
    "mutation": {"scope_owners"},
    "unknown": {"scope_owners"},
    "work_mode": {"continuity"},
    "multi_session": {"continuity"},
    "multi_slice": {"continuity"},
    "cross_module": {"continuity"},
    "coordination": {"continuity"},
    "material_tradeoff": {"requirement", "continuity"},
    "durable_plan": {"continuity"},
    "knowledge_impact": {"knowledge"},
    "overlay": {"scope_owners"},
}
ROUTE_BASIS_OPTION_DESTS = tuple(ROUTE_BASIS_OPTION_DIMENSIONS)
INVALIDATIONS = {
    "router_identity": {"requirement-understanding", "work-mode", "routes", "risk-overlays", "specialist-readiness", "method-selection", "independent-review", "knowledge-disposition", "terminal-evidence", "descendant-results"},
    "intent_task": {"requirement-understanding", "work-mode", "routes", "method-selection", "terminal-evidence", "descendant-results"},
    "requirement": {"requirement-understanding", "routes", "terminal-evidence", "descendant-results"},
    "continuity": {"work-mode", "routes", "knowledge-disposition", "terminal-evidence", "descendant-results"},
    "scope_owners": {"routes", "risk-overlays", "knowledge-disposition", "terminal-evidence", "descendant-results"},
    "capabilities": {"routes", "risk-overlays", "specialist-readiness", "method-selection", "independent-review", "terminal-evidence", "descendant-results"},
    "repository_readiness": {"routes", "specialist-readiness", "method-selection", "terminal-evidence", "descendant-results"},
    "method": {"method-selection", "terminal-evidence", "descendant-results"},
    "review": {"independent-review", "routes", "terminal-evidence", "descendant-results"},
    "knowledge": {"knowledge-disposition"},
}


class RouteBasisError(ValueError):
    """Raised when a caller-supplied prior route is unsafe or malformed."""


def compact_basis(basis: dict[str, Any]) -> dict[str, str]:
    """Return the privacy-minimized identity sufficient for unchanged reuse."""
    return {
        "schema": str(basis["schema"]),
        "router_semantics": ROUTER_SEMANTICS_VERSION,
        "digest": str(basis["digest"]),
    }


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(value)).hexdigest()


def _normalized(values: list[str]) -> list[str]:
    if len(values) > MAX_BASIS_LIST_ITEMS:
        raise RouteBasisError("route basis input exceeds the bounded item count")
    if any(
        not isinstance(value, str)
        or len(value) > MAX_BASIS_VALUE_CHARS
        or any(ord(character) < 32 for character in value)
        for value in values
    ):
        raise RouteBasisError("route basis values must be bounded printable strings")
    return sorted({value.strip() for value in values if value.strip()})


def build_basis(args: Any, context: dict[str, Any]) -> dict[str, Any]:
    revision = args.target_revision
    if revision is not None and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", revision) is None:
        raise RouteBasisError("target revision must be an opaque 1-64 character identifier")
    facts = _normalized(list(args.repo_fact))
    method = context["capability_activation"].get("method", {})
    normalization = method.get("signal_normalization", {})
    selection = method.get("selection")
    guidance = selection.get("guidance", []) if isinstance(selection, dict) else []
    dimensions = {
        "router_identity": {
            "basis_schema": ROUTE_BASIS_SCHEMA,
            "router_semantics": ROUTER_SEMANTICS_VERSION,
        },
        "intent_task": {
            "intent": context["intent"],
            "intent_source": context["intent_source"],
            "legacy_task_type": args.task_type,
            "target_revision_present": revision is not None,
            "target_revision_sha256": _digest(revision) if revision is not None else None,
        },
        "requirement": {
            "class": context["understanding"]["class"],
            "confirmed": bool(args.understanding_confirmed),
            "waived": bool(args.waive_understanding_confirmation),
            "user_choice_open": bool(args.user_choice_open),
            "ambiguity": bool(args.ambiguity),
            "ui_impact": args.ui_impact,
            "material_tradeoff": bool(args.material_tradeoff),
        },
        "continuity": {
            "requested_work_mode": args.work_mode,
            "resolved_work_mode": context["work_mode"],
            "multi_session": bool(args.multi_session),
            "multi_slice": bool(args.multi_slice),
            "cross_module": bool(args.cross_module),
            "coordination": bool(args.coordination),
            "material_tradeoff": bool(args.material_tradeoff),
            "durable_plan": bool(args.durable_plan),
        },
        "scope_owners": {
            "mutation": context["mutation_intent"],
            "ui_impact": args.ui_impact,
            "profile_operation": bool(args.profile_operation),
            "suite_maintenance": bool(args.suite_maintenance),
            "unknown": _normalized(list(args.unknown)),
            "overlay": _normalized(list(args.overlay)),
        },
        "capabilities": {
            "needs": sorted(context["needs"]),
            "risks": sorted(context["risks"]),
        },
        "repository_readiness": {
            "repository_facts_sha256": _digest(facts),
            "repository_fact_count": len(facts),
            "effective_skills": _normalized(list(args.effective_skill)),
        },
        "method": {
            "signals": sorted(normalization.get("canonical", [])),
            "prerequisites": _normalized(list(args.method_prerequisite)),
            "depth": args.method_depth,
            "selected": [
                item.get("method") or item.get("id")
                for item in guidance
                if isinstance(item, dict)
            ],
        },
        "review": {
            "material_exposure": bool(args.material_exposure),
            "required": bool(context["capability_activation"].get("independent_review", {}).get("required")),
        },
        "knowledge": {
            "requested": _normalized(list(args.knowledge_impact)),
            "disposition": list(context["knowledge"].get("disposition", [])),
        },
    }
    return {"schema": ROUTE_BASIS_SCHEMA, "digest": _digest(dimensions), "dimensions": dimensions}


def load_previous(path: Path) -> dict[str, Any]:
    try:
        info = path.lstat()
    except OSError as exc:
        raise RouteBasisError(f"cannot inspect previous route: {exc}") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise RouteBasisError("previous route must be a regular non-symlink file")
    if info.st_size > MAX_PREVIOUS_ROUTE_BYTES:
        raise RouteBasisError("previous route exceeds the bounded file size")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise RouteBasisError(f"previous route is not bounded UTF-8 JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise RouteBasisError("previous route must be a JSON object")
    basis = payload.get("route_basis")
    if not isinstance(basis, dict):
        return {"compatible": False, "reason": "missing-route-basis"}
    if basis.get("schema") != ROUTE_BASIS_SCHEMA:
        return {"compatible": False, "reason": "incompatible-route-basis-schema"}
    digest = basis.get("digest")
    if not isinstance(digest, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None:
        raise RouteBasisError("previous route basis digest is invalid")
    dimensions = basis.get("dimensions")
    if dimensions is None:
        if basis.get("router_semantics") != ROUTER_SEMANTICS_VERSION:
            return {"compatible": False, "reason": "incompatible-router-semantics"}
        if set(basis) != {"schema", "router_semantics", "digest"}:
            return {"compatible": False, "reason": "invalid-compact-route-basis"}
        return {"compatible": True, "basis": basis, "detail": "digest-only"}
    if not isinstance(dimensions, dict):
        return {"compatible": False, "reason": "incompatible-route-basis-schema"}
    if set(dimensions) != set(INVALIDATIONS):
        return {"compatible": False, "reason": "incompatible-route-basis-dimensions"}
    if digest != _digest(dimensions):
        raise RouteBasisError("previous route basis digest does not match its dimensions")
    return {"compatible": True, "basis": basis, "detail": "complete"}


def compare(current: dict[str, Any], previous: dict[str, Any]) -> dict[str, Any]:
    if not previous.get("compatible"):
        return {
            "status": "incompatible-prior-route",
            "reason": previous.get("reason", "incompatible-prior-route"),
            "changed_dimensions": [],
            "invalidated_decisions": [],
            "descendant_result_disposition": "reject-until-rebased",
            "next_action": "use-complete-current-route",
        }
    prior = previous["basis"]
    if prior["digest"] == current["digest"]:
        revision_bound = current["dimensions"]["intent_task"]["target_revision_present"]
        return {
            "status": "unchanged",
            "changed_dimensions": [],
            "invalidated_decisions": [],
            "descendant_result_disposition": (
                "retain" if revision_bound else "reconcile-objective-before-retain"
            ),
            "next_action": (
                "continue-without-reloading" if revision_bound else "reconcile-current-objective"
            ),
        }
    if previous.get("detail") == "digest-only":
        return {
            "status": "changed-digest-only",
            "reason": "compact-prior-route-omits-dimension-details",
            "changed_dimensions": [],
            "invalidated_decisions": sorted(
                {decision for decisions in INVALIDATIONS.values() for decision in decisions}
            ),
            "descendant_result_disposition": "reject-until-rebased",
            "next_action": "use-complete-current-route",
        }
    changed = sorted(
        name
        for name in INVALIDATIONS
        if prior["dimensions"].get(name) != current["dimensions"].get(name)
    )
    invalidated = sorted({item for name in changed for item in INVALIDATIONS[name]})
    return {
        "status": "changed",
        "changed_dimensions": changed,
        "invalidated_decisions": invalidated,
        "descendant_result_disposition": (
            "reject-until-rebased" if "descendant-results" in invalidated else "retain-unaffected"
        ),
        "next_action": "recalibrate-invalidated-decisions",
    }
