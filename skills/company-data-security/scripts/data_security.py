#!/usr/bin/env python3
"""Bounded local detection and redaction for the data-security Skill.

The public result types never contain matched values. This module is a
high-confidence guardrail, not a legal classifier or complete DLP engine.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import re
import secrets
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, replace
from typing import Any, Iterable, Iterator


MAX_TEXT_BYTES = 1_048_576
MAX_VALUE_BYTES = 2_097_152
MAX_REDACTED_BYTES = 1_048_576
MAX_FINDINGS = 64
MAX_DEPTH = 12
MAX_BASE64_BYTES = 16_384


class InspectionLimit(ValueError):
    """Raised when content cannot be inspected inside the V1 safety bounds."""


@dataclass(frozen=True)
class Finding:
    rule_id: str
    category: str
    data_class: str
    severity: str
    start: int
    end: int
    path: str = "$"

    def safe_dict(self) -> dict[str, str]:
        """Return metadata only; never add the matched substring here."""
        return {
            "rule_id": self.rule_id,
            "category": self.category,
            "data_class": self.data_class,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class _Rule:
    rule_id: str
    category: str
    data_class: str
    severity: str
    pattern: re.Pattern[str]
    value_group: int = 0


_HIGH_RULES = (
    _Rule(
        "C4-PRIVATE-KEY",
        "private_key",
        "C4",
        "secret",
        re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----[\s\S]{24,}?-----END (?:[A-Z0-9 ]+ )?PRIVATE KEY-----"),
    ),
    _Rule("C4-AWS-ACCESS-KEY", "access_key", "C4", "secret", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    _Rule("C4-GITHUB-TOKEN", "access_token", "C4", "secret", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,255}\b")),
    _Rule("C4-OPENAI-TOKEN", "access_token", "C4", "secret", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,255}\b")),
    _Rule("C4-SLACK-TOKEN", "access_token", "C4", "secret", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,255}\b")),
    _Rule(
        "C4-JWT",
        "session_token",
        "C4",
        "secret",
        re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    ),
    _Rule(
        "C4-AUTHORIZATION",
        "authorization",
        "C4",
        "secret",
        re.compile(r"\b(?:proxy-)?authorization\s*[:=]\s*(?:bearer|basic)\s+([A-Za-z0-9+/_=.:-]{12,})", re.IGNORECASE),
        1,
    ),
    _Rule(
        "C4-CREDENTIALED-URL",
        "credentialed_url",
        "C4",
        "secret",
        re.compile(r"\b[a-z][a-z0-9+.-]{1,20}://[^\s/:@]+:([^\s/@]{8,})@[^\s/]+", re.IGNORECASE),
        1,
    ),
    _Rule(
        "C4-SENSITIVE-ASSIGNMENT",
        "secret_assignment",
        "C4",
        "secret",
        re.compile(
            r"\b(?:password|passwd|pwd|secret|api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret)\b"
            r"\s*[:=]\s*[\"']?([^\s\"',;}{]{8,})",
            re.IGNORECASE,
        ),
        1,
    ),
)

_IDENTIFIER_RULES = (
    _Rule(
        "C3-EMAIL",
        "email",
        "C3",
        "restricted",
        re.compile(r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.-]+\.[A-Za-z]{2,24}(?![A-Za-z0-9.-])"),
    ),
    _Rule(
        "C3-PHONE",
        "phone",
        "C3",
        "restricted",
        re.compile(r"(?<!\w)(?:\+?\d[\s().-]*){10,15}(?!\w)"),
    ),
)

_BASE64_RE = re.compile(r"(?<![A-Za-z0-9+/_=-])[A-Za-z0-9+/_-]{32,2048}={0,2}(?![A-Za-z0-9+/_=-])")
_PLACEHOLDER_RE = re.compile(
    r"(?:\$\{?[A-Z_][A-Z0-9_]*\}?|\{\{[^{}]{1,80}\}\}|<[^<>]{1,80}>|"
    r"\b(?:redacted|placeholder|example|sample|dummy|fake|test|testing|changeme|replace[_-]?me|your[_-]?[a-z0-9_-]*)\b|"
    r"^(?:x+|\*+|-+)$)",
    re.IGNORECASE,
)
_SENSITIVE_PATH_RE = re.compile(
    r"(?:^|[/\\])(?:"
    r"\.env(?:\.[A-Za-z0-9_-]+)?|\.npmrc|\.pypirc|\.netrc|"
    r"\.aws[/\\]credentials|\.kube[/\\]config|\.docker[/\\]config\.json|"
    r"\.ssh[/\\](?:id_[^/\\]+|config)|"
    r"(?:auth|credentials?|service[-_]?account)\.json|"
    r"[^/\\]+\.(?:pem|key|p12|pfx)"
    r")(?:$|[\s\"'])",
    re.IGNORECASE,
)
_SAFE_SENSITIVE_PATH_RE = re.compile(r"(?:\.env\.(?:example|sample|template)|dummy|fixture|synthetic)", re.IGNORECASE)


def _is_placeholder(value: str) -> bool:
    stripped = value.strip().strip("\"'")
    return not stripped or bool(_PLACEHOLDER_RE.search(stripped))


def _assignment_value_is_confident(value: str) -> bool:
    stripped = value.strip().strip("\"'")
    if len(stripped) < 12 or len(set(stripped)) < 6:
        return False
    classes = sum(
        (
            any(character.islower() for character in stripped),
            any(character.isupper() for character in stripped),
            any(character.isdigit() for character in stripped),
            any(not character.isalnum() for character in stripped),
        )
    )
    return classes >= 2 or (len(stripped) >= 24 and len(set(stripped)) >= 10)


def _overlaps(left: Finding, right: Finding) -> bool:
    return left.start < right.end and right.start < left.end


def _direct_findings(text: str, rules: Iterable[_Rule]) -> list[Finding]:
    found: list[Finding] = []
    for rule in rules:
        for match in rule.pattern.finditer(text):
            value = match.group(rule.value_group)
            if _is_placeholder(value):
                continue
            if rule.rule_id == "C4-SENSITIVE-ASSIGNMENT" and not _assignment_value_is_confident(value):
                continue
            start, end = match.span(rule.value_group)
            candidate = Finding(rule.rule_id, rule.category, rule.data_class, rule.severity, start, end)
            if not any(_overlaps(candidate, existing) for existing in found):
                found.append(candidate)
            if len(found) >= MAX_FINDINGS:
                return sorted(found, key=lambda item: (item.start, item.end, item.rule_id))
    return sorted(found, key=lambda item: (item.start, item.end, item.rule_id))


def _decoded_text(candidate: str) -> str | None:
    if len(candidate) > MAX_BASE64_BYTES * 2:
        return None
    raw = candidate.encode("ascii", errors="ignore")
    padding = b"=" * ((4 - len(raw) % 4) % 4)
    try:
        decoded = base64.urlsafe_b64decode(raw + padding)
    except (ValueError, base64.binascii.Error):
        return None
    if not decoded or len(decoded) > MAX_BASE64_BYTES:
        return None
    try:
        text = decoded.decode("utf-8")
    except UnicodeDecodeError:
        return None
    printable = sum(character.isprintable() or character.isspace() for character in text)
    return text if printable / max(len(text), 1) >= 0.9 else None


def scan_text(text: str, *, include_identifiers: bool = True, decode_base64: bool = True) -> list[Finding]:
    if len(text.encode("utf-8")) > MAX_TEXT_BYTES:
        raise InspectionLimit("text exceeds the local inspection limit")
    findings = _direct_findings(text, _HIGH_RULES)
    normalized = unicodedata.normalize("NFKC", text)
    if normalized != text and len(findings) < MAX_FINDINGS:
        normalized_high = _direct_findings(normalized, _HIGH_RULES)
        for item in normalized_high:
            if len(normalized) == len(text):
                candidate = replace(item, rule_id="C4-NORMALIZED-SECRET", category="obfuscated_secret")
            else:
                candidate = Finding("C4-NORMALIZED-SECRET", "obfuscated_secret", "C4", "secret", 0, len(text))
            if not any(_overlaps(candidate, existing) for existing in findings):
                findings.append(candidate)
            if len(findings) >= MAX_FINDINGS:
                break
    if include_identifiers and len(findings) < MAX_FINDINGS:
        for item in _direct_findings(text, _IDENTIFIER_RULES):
            if not any(_overlaps(item, existing) for existing in findings):
                findings.append(item)
            if len(findings) >= MAX_FINDINGS:
                break
    if decode_base64 and len(findings) < MAX_FINDINGS:
        for match in _BASE64_RE.finditer(text):
            decoded = _decoded_text(match.group(0))
            if decoded is None or not _direct_findings(decoded, _HIGH_RULES):
                continue
            candidate = Finding(
                "C4-ENCODED-SECRET",
                "encoded_secret",
                "C4",
                "secret",
                match.start(),
                match.end(),
            )
            if not any(_overlaps(candidate, existing) for existing in findings):
                findings.append(candidate)
            if len(findings) >= MAX_FINDINGS:
                break
    return sorted(findings, key=lambda item: (item.start, item.end, item.rule_id))


def _derive_label(value: str, finding: Finding, salt: bytes) -> str:
    digest = hmac.new(salt, f"{finding.category}\0{value}".encode("utf-8"), hashlib.sha256).hexdigest()[:8]
    return f"{{{{DLP:{finding.category.upper()}:{digest}}}}}"


def _replacement(value: str, finding: Finding, salt: bytes) -> str:
    if finding.data_class != "C4":
        return _derive_label(value, finding, salt)
    digest = hmac.new(salt, f"secret\0{value}".encode("utf-8"), hashlib.sha256).hexdigest()[:8]
    return f"{{{{DLP:SECRET:{digest}}}}}"


def redact_text(text: str, *, salt: bytes | None = None) -> tuple[str, list[Finding]]:
    findings = scan_text(text)
    local_salt = salt or secrets.token_bytes(32)
    output = text
    for finding in sorted(findings, key=lambda item: (item.start, item.end), reverse=True):
        value = text[finding.start:finding.end]
        replacement = _replacement(value, finding, local_salt)
        output = output[:finding.start] + replacement + output[finding.end:]
    if len(output.encode("utf-8")) > MAX_REDACTED_BYTES:
        raise InspectionLimit("redacted output exceeds the local output limit")
    return output, findings


def _json_size(value: Any) -> int:
    try:
        return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    except (TypeError, ValueError) as exc:
        raise InspectionLimit("value is not bounded JSON") from exc


def _iter_strings(value: Any, *, path: str = "$", depth: int = 0) -> Iterator[tuple[str, str]]:
    if depth > MAX_DEPTH:
        raise InspectionLimit("value exceeds the inspection depth limit")
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for index, (key, nested) in enumerate(value.items()):
            if isinstance(key, str):
                yield f"{path}/@key/{index}", key
            yield from _iter_strings(nested, path=f"{path}/@item/{index}", depth=depth + 1)
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from _iter_strings(nested, path=f"{path}/{index}", depth=depth + 1)


def scan_value(value: Any, *, include_identifiers: bool = True) -> list[Finding]:
    if _json_size(value) > MAX_VALUE_BYTES:
        raise InspectionLimit("value exceeds the local inspection limit")
    findings: list[Finding] = []
    for path, text in _iter_strings(value):
        for finding in scan_text(text, include_identifiers=include_identifiers):
            findings.append(replace(finding, path=path))
            if len(findings) >= MAX_FINDINGS:
                return findings
    return findings


def redact_value(value: Any, *, salt: bytes | None = None) -> tuple[Any, list[Finding]]:
    if _json_size(value) > MAX_VALUE_BYTES:
        raise InspectionLimit("value exceeds the local inspection limit")
    local_salt = salt or secrets.token_bytes(32)
    findings: list[Finding] = []

    def transform(current: Any, path: str, depth: int) -> Any:
        if depth > MAX_DEPTH:
            raise InspectionLimit("value exceeds the inspection depth limit")
        if isinstance(current, str):
            redacted, local = redact_text(current, salt=local_salt)
            findings.extend(replace(item, path=path) for item in local[: max(0, MAX_FINDINGS - len(findings))])
            return redacted
        if isinstance(current, dict):
            transformed: dict[Any, Any] = {}
            for index, (key, nested) in enumerate(current.items()):
                next_key = key
                if isinstance(key, str):
                    next_key, key_findings = redact_text(key, salt=local_salt)
                    findings.extend(
                        replace(item, path=f"{path}/@key/{index}")
                        for item in key_findings[: max(0, MAX_FINDINGS - len(findings))]
                    )
                    if next_key in transformed and next_key != key:
                        next_key = f"{next_key}#{index}"
                transformed[next_key] = transform(nested, f"{path}/@item/{index}", depth + 1)
            return transformed
        if isinstance(current, list):
            return [transform(nested, f"{path}/{index}", depth + 1) for index, nested in enumerate(current)]
        return current

    redacted = transform(value, "$", 0)
    if _json_size(redacted) > MAX_REDACTED_BYTES:
        raise InspectionLimit("redacted output exceeds the local output limit")
    return redacted, findings[:MAX_FINDINGS]


def contains_high_confidence(findings: Iterable[Finding]) -> bool:
    return any(finding.data_class == "C4" and finding.severity == "secret" for finding in findings)


def sensitive_path_categories(value: Any) -> list[str]:
    categories: set[str] = set()
    for _, text in _iter_strings(value):
        for match in _SENSITIVE_PATH_RE.finditer(text):
            candidate = match.group(0)
            if _SAFE_SENSITIVE_PATH_RE.search(candidate):
                continue
            categories.add("credential_store_path")
    return sorted(categories)


def finding_summary(findings: Iterable[Finding]) -> dict[str, Any]:
    material = list(findings)
    by_class = Counter(item.data_class for item in material)
    by_category = Counter(item.category for item in material)
    return {
        "finding_count": len(material),
        "classes": dict(sorted(by_class.items())),
        "categories": dict(sorted(by_category.items())),
        "findings": [item.safe_dict() for item in material],
    }


def _read_stdin() -> str:
    raw = sys.stdin.buffer.read(MAX_TEXT_BYTES + 1)
    if len(raw) > MAX_TEXT_BYTES:
        raise InspectionLimit("stdin exceeds the local inspection limit")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InspectionLimit("stdin must be UTF-8 text") from exc


def _salt_from_argument(value: str | None) -> bytes | None:
    if value is None:
        return None
    raw = value.encode("utf-8")
    if len(raw) < 16:
        raise InspectionLimit("pseudonym salt must contain at least 16 UTF-8 bytes")
    return hashlib.sha256(raw).digest()


def _run_scan() -> int:
    text = _read_stdin()
    print(json.dumps({"status": "ok", **finding_summary(scan_text(text))}, ensure_ascii=False, sort_keys=True))
    return 0


def _run_redact(salt_text: str | None) -> int:
    redacted, findings = redact_text(_read_stdin(), salt=_salt_from_argument(salt_text))
    if not findings:
        sys.stdout.write(redacted)
        return 0
    sys.stdout.write(redacted)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local, bounded confidentiality inspection and redaction")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("scan", help="read UTF-8 text from stdin and emit finding metadata only")
    redact_parser = subparsers.add_parser("redact", help="read UTF-8 text from stdin and emit redacted text")
    redact_parser.add_argument("--salt", help="optional local correlation salt; never emitted or persisted")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "scan":
            return _run_scan()
        if args.command == "redact":
            return _run_redact(args.salt)
    except InspectionLimit as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, sort_keys=True))
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
