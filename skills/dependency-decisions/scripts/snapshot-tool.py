#!/usr/bin/env python3
"""Validate freshness and safe offline use of Dev Flow ecosystem snapshots."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


SELECTOR_RE = re.compile(r"^[a-z][a-z0-9_.-]*!?=[^=]+$")
MAX_AGE_DAYS = {"low": 180, "medium": 90, "high": 30}
MATURITY = {"stable", "preview", "experimental", "deprecated", "unknown"}


def parse_time(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed


def validate_snapshot(data: Any, *, source: str, as_of: dt.datetime) -> dict[str, Any]:
    errors: list[str] = []
    stale: list[dict[str, str]] = []
    if not isinstance(data, dict):
        return {"status": "invalid", "errors": [f"{source}: top-level value must be an object"]}
    if data.get("schema_version") != "1.0":
        errors.append(f"{source}: unsupported schema_version {data.get('schema_version')!r}")
    if not isinstance(data.get("id"), str) or not data["id"]:
        errors.append(f"{source}: id must be a non-empty string")
    declared_status = data.get("status")
    if declared_status not in {"current", "stale", "refresh-required"}:
        errors.append(f"{source}: invalid status {declared_status!r}")
    checked_at: dt.datetime | None = None
    if data.get("checked_at") is not None:
        try:
            checked_at = parse_time(str(data["checked_at"]))
        except ValueError as exc:
            errors.append(f"{source}: invalid checked_at: {exc}")
    if declared_status == "current" and checked_at is None:
        errors.append(f"{source}: current snapshot requires checked_at")
    if checked_at is not None and checked_at.astimezone(dt.timezone.utc) > as_of + dt.timedelta(minutes=5):
        errors.append(f"{source}: checked_at cannot be in the future relative to --as-of")
    observations = data.get("observations")
    if not isinstance(observations, list) or not observations:
        errors.append(f"{source}: observations must be a non-empty list")
        observations = []
    required_text = ("capability", "candidate", "refresh_trigger", "migration", "fallback")
    required_lists = ("sources", "applies_when", "avoid_when", "alternatives")
    for index, observation in enumerate(observations):
        label = f"{source}: observations[{index}]"
        if not isinstance(observation, dict):
            errors.append(f"{label} must be an object")
            continue
        for field in required_text:
            if not isinstance(observation.get(field), str) or not observation[field]:
                errors.append(f"{label}.{field} must be a non-empty string")
        for field in required_lists:
            value = observation.get(field)
            if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
                errors.append(f"{label}.{field} must be a list of non-empty strings")
        for field in ("applies_when", "avoid_when"):
            for selector in observation.get(field, []) if isinstance(observation.get(field), list) else []:
                if isinstance(selector, str) and not SELECTOR_RE.fullmatch(selector):
                    errors.append(f"{label}.{field} contains invalid selector {selector!r}")
        volatility = observation.get("volatility")
        if volatility not in MAX_AGE_DAYS:
            errors.append(f"{label}.volatility must be low, medium, or high")
        if observation.get("maturity") not in MATURITY:
            errors.append(f"{label}.maturity is invalid")
        if declared_status == "current" and not observation.get("sources"):
            errors.append(f"{label}.sources must be non-empty for current evidence")
        if checked_at is not None and volatility in MAX_AGE_DAYS:
            age = as_of - checked_at.astimezone(dt.timezone.utc)
            if age > dt.timedelta(days=MAX_AGE_DAYS[volatility]):
                stale.append(
                    {
                        "capability": str(observation.get("capability", index)),
                        "reason": f"{volatility} volatility evidence is {age.days} days old",
                        "refresh_trigger": str(observation.get("refresh_trigger", "refresh before use")),
                        "fallback": str(observation.get("fallback", "preserve the current repository choice")),
                    }
                )
    if errors:
        status = "invalid"
    elif declared_status == "refresh-required":
        status = "refresh-required"
    elif declared_status == "stale" or stale:
        status = "stale"
    else:
        status = "current"
    return {
        "status": status,
        "snapshot_id": data.get("id"),
        "checked_at": data.get("checked_at"),
        "as_of": as_of.isoformat(),
        "stale_observations": stale,
        "errors": errors,
        "offline_rule": "Use only current evidence for a new recommendation; otherwise follow the recorded fallback.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("snapshot", type=Path)
    validate.add_argument("--as-of", help="Timezone-aware ISO date/time; defaults to current UTC time")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        data = json.loads(args.snapshot.read_text(encoding="utf-8"))
        as_of = parse_time(args.as_of) if args.as_of else dt.datetime.now(dt.timezone.utc)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        result = {"status": "invalid", "errors": [str(exc)]}
    else:
        result = validate_snapshot(data, source=str(args.snapshot.resolve()), as_of=as_of.astimezone(dt.timezone.utc))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "current" else 2


if __name__ == "__main__":
    sys.exit(main())
