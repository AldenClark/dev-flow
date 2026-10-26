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
import io
import json
import re
import secrets
import shlex
import string
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
MAX_SHELL_LEXEME_CHARS = 65_536


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
    _Rule("C4-AWS-ACCESS-KEY", "access_key", "C4", "secret", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    _Rule("C4-GITHUB-TOKEN", "access_token", "C4", "secret", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,255}\b")),
    _Rule("C4-GITHUB-FINE-GRAINED", "access_token", "C4", "secret", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{30,255}\b")),
    _Rule("C4-GITHUB-INSTALLATION-JWT", "access_token", "C4", "secret", re.compile(r"\bghs_[A-Za-z0-9]+_eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")),
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
        re.compile(r"\b(?:proxy-)?authorization[\"']?[ \t\r\n]*[:=][ \t\r\n]*[\"']?(?:bearer|basic)[ \t]+([A-Za-z0-9+/_=.~:-]{12,})", re.IGNORECASE),
        1,
    ),
    _Rule(
        "C4-CREDENTIALED-URL",
        "credentialed_url",
        "C4",
        "secret",
        re.compile(r"\b[a-z][a-z0-9+.-]{1,20}://[^\s/:@]+:([^\s/@]{8,})@[^\s/\"'`]+", re.IGNORECASE),
        1,
    ),
)

_SENSITIVE_NAME = r"(?:(?:[A-Za-z][A-Za-z0-9]*_)*(?:password|passwd|pwd|secret|api[_-]?(?:key|token)|access[_-]?token|refresh[_-]?token|session[_-]?token|client[_-]?secret)|aws_secret_access_key|x-api-key)"
_SENSITIVE_NAME_RE = re.compile(_SENSITIVE_NAME, re.IGNORECASE)
_STRING_LITERAL_PATTERN = (
    r'"""(?:\\[\s\S]|(?!""")[\s\S])*(?:"""|$)'
    r"|'''(?:\\[\s\S]|(?!''')[\s\S])*(?:'''|$)"
    r'|"(?:[^"\\\r\n]|\\[^\r\n])*"'
    r"|'(?:[^'\\\r\n]|\\[^\r\n])*'"
)
_ASSIGNMENT_RE = re.compile(
    r"\b" + _SENSITIVE_NAME + r"\b[\"']?[ \t\r\n]*[:=](?!=)[ \t\r\n]*"
    r"(" + _STRING_LITERAL_PATTERN + r"""|[^\s"',;}{]+)""",
    re.IGNORECASE,
)
_QUOTED_LITERAL_RE = re.compile(r"[ \t\r\n]*(?P<literal>" + _STRING_LITERAL_PATTERN + r")")
_RUST_RAW_LITERAL_PATTERN = r'\b(?:br|r)(?P<raw_hashes>\#{1,8})"(?P<raw_body>[\s\S]*?)"(?P=raw_hashes)'
_RUST_RAW_LITERAL_RE = re.compile(_RUST_RAW_LITERAL_PATTERN)
_EXPRESSION_LITERAL_RE = re.compile(
    r"(?P<rust_raw>" + _RUST_RAW_LITERAL_PATTERN + r")"
    r"|(?P<comment>//[^\r\n]*|\#[^\r\n]*|/\*[\s\S]*?(?:\*/|$))"
    r"|(?P<literal>" + _STRING_LITERAL_PATTERN + r")|(?P<delimiter>[();])"
)
_SOURCE_ARGUMENT_REFERENCE_RE = re.compile(
    r"\(*(?P<root>[&*]*(?:r#)?[A-Za-z_]\w*|\.[A-Za-z_]\w*|\$\d+)"
    r"(?:(?:::|->|\?\.|\.)[A-Za-z_]\w*|\[(?:[A-Za-z_]\w*|\d+)\])*"
    r"(?:!{1,2}|\?)?[)\]]*(?:\.[A-Za-z_]\w*\(\)[)\]]*)*"
)
_SOURCE_CALL_PREFIX_RE = re.compile(r"\b[A-Za-z_]\w*\s*\([^;]*$")
_FORMAT_FIELD_REFERENCE_RE = re.compile(
    r"(?:[A-Za-z_]\w*|\d+)(?:\.[A-Za-z_]\w*|\[(?:[A-Za-z_]\w*|\d+)\])*"
)
_FORMATTED_STRING_RE = re.compile(r"(?P<prefix>\b(?:f|fr|rf))?(?P<literal>" + _STRING_LITERAL_PATTERN + r")", re.IGNORECASE)
_FORMAT_SPEC_RE = re.compile(r"(?:(?:[^\r\n{}])?[<>=^])?[+\- ]?#?0?\d{0,4}[,_]?(?:\.\d{1,3})?[bcdeEfFgGnosxX%]?")

_RELATIVE_DOC_LINK_RE = re.compile(r"\[[a-z]+(?:[ -][a-z]+)*\]\(docs/(?:[a-z0-9-]+/)*[a-z0-9-]+\.md\)")

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
        re.compile(r"(?<![\w.+-])\+?\d(?:[\d ().-]*\d)?(?![\w.+-])"),
    ),
)

_BASE64_RE = re.compile(r"(?<![A-Za-z0-9+/_=-])[A-Za-z0-9+/_-]{32," + str(4 * ((MAX_BASE64_BYTES + 2) // 3)) + r"}={0,2}(?![A-Za-z0-9+/_=-])")
_PRIVATE_KEY_MARKER_RE = re.compile(r"-----(BEGIN|END) ((?:[A-Z0-9 ]{1,64} )?PRIVATE KEY)-----")
_PRIVATE_KEY_BODY_RE = re.compile(
    r"[ \t]*\r?\n(?:(?:Proc-Type|DEK-Info):[^\r\n]{1,256}\r?\n)*(?:\r?\n)?"
    r"(?P<body>[ \t]*[A-Za-z0-9+/=]+(?:[ \t]*\r?\n[ \t]*[A-Za-z0-9+/=]+)*[ \t]*)"
)
_PLACEHOLDER_RE = re.compile(
    r"(?:\{\{DLP:(?:SECRET|EMAIL|PHONE):[0-9a-f]{8}\}\})|"
    r"\[REDACTED_SECRET\]|"
    r"(?:\$(?:\{[A-Z_][A-Z0-9_]*\}|[A-Z_][A-Z0-9_]*)|\{\{[A-Z_][A-Z0-9_]{0,79}\}\}|"
    r"<(?:redacted|placeholder|secret|token|password)>|(?-i:<[A-Z_][A-Z0-9_]{0,79}>)|"
    r"\b(?:redacted|placeholder|example|sample|dummy|fake|test|testing|changeme|replace[_-]?me|your[_-](?:api[_-]key|token|password|secret|access[_-]token|client[_-]secret|key))\b|"
    r"^(?:x+|\*+|-+)$)",
    re.IGNORECASE,
)
_SENSITIVE_PATH_RE = re.compile(
    # Unquoted path components cannot absorb source code or later lines. A bare
    # sensitive filename must occupy the whole value; quoted filenames may
    # contain spaces, but cannot cross a quote or newline boundary.
    r"(?:^|[/\\]|^[A-Za-z]:)(?:"
    r"\.env(?:\.[A-Za-z0-9_-]+)*|\.npmrc|\.pypirc|\.netrc|"
    r"\.aws[/\\]credentials|\.kube[/\\]config|\.docker[/\\]config\.json|"
    r"\.ssh[/\\](?:id_[^/\\\s\"']+|config)|"
    r"(?:auth|credentials?|service[-_]?account)\.json"
    r")(?:$|[\s\"'])|"
    r"^[^/\\\s\"']+\.(?:pem|key|p12|pfx)$|"
    r"[/\\][^/\\\s\"'`<>|;(){}\[\]=]+\.(?:pem|key|p12|pfx)(?:$|[\s\"'])|"
    r"\"[^\"\r\n]+\.(?:pem|key|p12|pfx)\"|"
    r"'[^'\r\n]+\.(?:pem|key|p12|pfx)'",
    re.IGNORECASE,
)
_SAFE_ENV_TEMPLATE_RE = re.compile(r"\.env\.(?:example|sample|template)", re.IGNORECASE)


def _is_placeholder(value: str) -> bool:
    stripped = value.strip().strip("\"'")
    return not stripped or bool(_PLACEHOLDER_RE.fullmatch(stripped))


def _source_reference(value: str) -> bool:
    if re.fullmatch(r"[&*]+(?:r#)?[A-Za-z_]\w*(?:(?:::|->|[?!]?\.)[A-Za-z_]\w*)*", value):
        return True
    if re.fullmatch(r"(?:r#)?[A-Za-z_][A-Za-z_]*", value):
        return True
    if re.fullmatch(r"[A-Za-z_]+(?:_[A-Za-z0-9]+)+|[a-z]+(?:[A-Z][a-z]+)+[0-9]*", value):
        return True
    return re.match(r"[A-Za-z_]\w*(?:::|\(|[?!]?\.|->|<)", value) is not None


def _assignment_value_is_confident(value: str, *, literal: bool = False) -> bool:
    stripped = value.strip().strip("\"'")
    if _is_placeholder(stripped):
        return False
    if not literal:
        # An unquoted reference/expression is not itself a secret. Independent
        # token rules still inspect literals nested inside source expressions.
        if _source_reference(stripped):
            return False
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


def _source_argument_reference(text: str, start: int, value: str) -> bool:
    """Recognize complete unquoted references in a bounded named-argument context.

    Keep the original value/span for literal detection and redaction. Trimming
    delimiters globally would also exempt ordinary unquoted credential values.
    """
    prefix = text[max(0, start - 1024):start].rstrip()
    if not prefix.endswith(("(", ",")) or not _SOURCE_CALL_PREFIX_RE.search(prefix):
        return False
    reference = _SOURCE_ARGUMENT_REFERENCE_RE.fullmatch(value)
    if reference is None:
        return False
    root = reference.group("root")
    return _source_reference(root) or root.startswith(".") or bool(re.fullmatch(r"\$\d+", root))


def _formatted_literal_is_confident(value: str) -> bool:
    """References alone are not literal material; literal fragments still are."""
    try:
        return any(
            _assignment_value_is_confident(literal, literal=True)
            for literal, _, _, _ in string.Formatter().parse(_literal_content(value)[0])
        )
    except ValueError:
        return _assignment_value_is_confident(value, literal=True)


def _literal_content(value: str) -> tuple[str, int, int]:
    width = 3 if value.startswith(('"""', "'''")) else 1
    closing = width if len(value) >= 2 * width and value.endswith(value[:width]) else 0
    return value[width:len(value) - closing if closing else len(value)], width, closing


def _wrapper_literal_findings(text: str, opening: int) -> tuple[list[Finding], int]:
    """Inspect literal arguments without executing the assigned expression."""
    found: list[Finding] = []

    def inspect_literal(value: str, start: int, end: int) -> None:
        prefix = text[max(opening + 1, start - 3):start]
        content, left, right = _literal_content(value)
        confident = _formatted_literal_is_confident(value) if re.search(r"\b(?:f|fr|rf)$", prefix, re.IGNORECASE) else _assignment_value_is_confident(content, literal=True)
        if confident:
            _add_finding(found, Finding("C4-SENSITIVE-ASSIGNMENT", "secret_assignment", "C4", "secret", start + left, end - right))

    depth = 1
    for token in _EXPRESSION_LITERAL_RE.finditer(text, opening + 1):
        value = token.group("literal")
        if token.group("rust_raw") is not None:
            if _assignment_value_is_confident(token.group("raw_body"), literal=True):
                _add_finding(found, Finding("C4-SENSITIVE-ASSIGNMENT", "secret_assignment", "C4", "secret", token.start("raw_body"), token.end("raw_body")))
        elif value is not None:
            inspect_literal(value, token.start(), token.end())
        elif token.group("comment") is not None:
            # Comment punctuation cannot close the surrounding call, but
            # quoted material inside comments can still disclose a credential.
            for literal in _QUOTED_LITERAL_RE.finditer(token.group("comment")):
                inspect_literal(literal.group("literal"), token.start() + literal.start("literal"), token.start() + literal.end("literal"))
        elif token.group("delimiter") == "(":
            depth += 1
        elif token.group("delimiter") == ")":
            depth -= 1
            if depth == 0:
                return found, token.end()
        else:
            return found, token.end()
    return found, len(text)


def _url_reference_field(value: str) -> bool:
    try:
        parts = list(string.Formatter().parse(value))
    except ValueError:
        return False
    if len(parts) != 1:
        return False
    literal, field, spec, conversion = parts[0]
    return (
        not literal and field is not None
        and _FORMAT_FIELD_REFERENCE_RE.fullmatch(field) is not None
        and conversion in (None, "s", "r", "a")
        and _FORMAT_SPEC_RE.fullmatch(spec) is not None
    )


def _formatted_string_ranges(text: str) -> Iterator[tuple[int, int]]:
    for token in _FORMATTED_STRING_RE.finditer(text):
        if token.group("prefix") or re.match(r"[ \t]*\.format\s*\(", text[token.end():token.end() + 128]):
            yield token.start("literal"), token.end()


def _overlaps(left: Finding, right: Finding) -> bool:
    return left.path == right.path and left.start < right.end and right.start < left.end


def _add_finding(found: list[Finding], candidate: Finding) -> None:
    # Wider overlapping matches must not be dropped: doing so leaves the rest
    # of a password or an obfuscated value visible after redaction.
    overlaps = [item for item in found if _overlaps(candidate, item)]
    if overlaps:
        all_items = [candidate, *overlaps]
        strongest = min(all_items, key=lambda item: (
            item.data_class != "C4",
            item.category not in {"private_key", "authorization", "credentialed_url", "encoded_secret", "obfuscated_secret"},
            -(item.end - item.start),
        ))
        candidate = replace(strongest, start=min(item.start for item in all_items), end=max(item.end for item in all_items))
        found[:] = [item for item in found if item not in overlaps]
    found.append(candidate)
    if len(found) > MAX_FINDINGS:
        raise InspectionLimit("findings exceed the local inspection limit")


def _phone_is_confident(value: str, prefix: str = "") -> bool:
    digits = re.sub(r"\D", "", value)
    if not 10 <= len(digits) <= 15:
        return False
    if re.search(r"\b\d{4}[-.]\d{2}[-.]\d{2}\b", value):
        return False
    groups = re.findall(r"\d+", value)
    if re.search(r"(?:version|ver|build|revision)[\"']?[ \t]*[:=][ \t]*[\"']?$", prefix, re.IGNORECASE):
        return False
    if len(groups) == 4 and ".".join(groups) == value and all(int(group) <= 255 for group in groups):
        return False
    if value.startswith("+"):
        return len(groups) == 1 or (2 <= len(groups) <= 5 and len(groups[0]) <= 3)
    # Unlabelled epoch counters and dotted version sequences are not phones.
    labelled = re.search(r"(?:phone|telephone|mobile|tel|手机|电话)[\"']?[ \t]*[:=]?[ \t]*[\"']?$", prefix, re.IGNORECASE)
    if "." in value and not labelled:
        return False
    return len(digits) in (10, 11) and ((len(groups) == 1 and bool(labelled)) or (3 <= len(groups) <= 4 and all(2 <= len(group) <= 4 for group in groups)))


def _assignment_findings(text: str) -> list[Finding]:
    found: list[Finding] = []
    wrapper_checked_until = 0
    for match in _ASSIGNMENT_RE.finditer(text):
        value = match.group(1)
        quoted = value.startswith(("\"", "'")) and value[-1:] == value[:1]
        start, end = match.span(1)
        # A wrapper around a literal does not make that literal a reference.
        # Inspect its first literal argument without executing or parsing code.
        if not quoted:
            raw = _RUST_RAW_LITERAL_RE.match(text, start)
            if raw:
                if _assignment_value_is_confident(raw.group("raw_body"), literal=True):
                    _add_finding(found, Finding("C4-SENSITIVE-ASSIGNMENT", "secret_assignment", "C4", "secret", raw.start("raw_body"), raw.end("raw_body")))
                continue
            opening = text.find("(", start, end) if _source_reference(value) else -1
            if opening < 0 and _source_reference(value):
                spaced = re.match(r"[ \t\r\n]+\(", text[end:])
                if spaced:
                    opening = end + spaced.end() - 1
            if opening >= wrapper_checked_until and opening >= 0:
                literals, wrapper_checked_until = _wrapper_literal_findings(text, opening)
                for literal in literals:
                    _add_finding(found, literal)
            literal_start = end if value.endswith("(") or value in {"&", "*"} else None
            prefixed = re.fullmatch(r"(?:r\#{0,8}|br|rb|fr|rf|[buf])", value, re.IGNORECASE)
            if prefixed:
                literal_start = end
            elif _source_reference(value):
                spaced_call = re.match(r"[ \t\r\n]+\(", text[end:])
                if spaced_call:
                    literal_start = end + spaced_call.end()
            nested = _QUOTED_LITERAL_RE.match(text, literal_start) if literal_start is not None else None
            if nested:
                value = nested.group("literal")
                if prefixed and "f" in match.group(1).lower() and not _formatted_literal_is_confident(value):
                    continue
                quoted = True
                start, end = nested.span("literal")
        if not quoted and _source_argument_reference(text, match.start(), value):
            continue
        if not _assignment_value_is_confident(value, literal=quoted):
            continue
        # A complete, simple relative Markdown reference to a docs/*.md page
        # is report prose. Keep the grammar deliberately narrow: arbitrary
        # brackets, external links, malformed links, and mixed-case/token-like
        # labels or paths remain subject to the ordinary assignment scan.
        link = _RELATIVE_DOC_LINK_RE.match(text, start) if not quoted else None
        if link and (link.end() == len(text) or text[link.end()] in " \t\r\n\"',;}{"):
            continue
        left, right = _literal_content(value)[1:] if quoted else (0, 0)
        _add_finding(found, Finding("C4-SENSITIVE-ASSIGNMENT", "secret_assignment", "C4", "secret", start + left, end - right))
    return found


def _direct_findings(text: str, rules: Iterable[_Rule]) -> list[Finding]:
    found: list[Finding] = []
    for rule in rules:
        format_ranges: Iterator[tuple[int, int]] | None = None
        format_range: tuple[int, int] | None = None
        for match in rule.pattern.finditer(text):
            value = match.group(rule.value_group)
            if _is_placeholder(value):
                continue
            if rule.category == "credentialed_url" and _url_reference_field(value):
                # Only an entire reference in an actual formatting expression
                # is source. Mixed literal/reference credentials stay protected.
                if format_ranges is None:
                    format_ranges = iter(_formatted_string_ranges(text))
                    format_range = next(format_ranges, None)
                while format_range is not None and format_range[1] <= match.start():
                    format_range = next(format_ranges, None)
                if format_range is not None and format_range[0] <= match.start() and match.end() <= format_range[1]:
                    continue
            if rule.category == "phone" and not _phone_is_confident(value, text[max(0, match.start() - 32):match.start()]):
                continue
            start, end = match.span(rule.value_group)
            candidate = Finding(rule.rule_id, rule.category, rule.data_class, rule.severity, start, end)
            _add_finding(found, candidate)
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


def _utf8_size(text: str) -> int:
    try:
        return len(text.encode("utf-8"))
    except UnicodeError as exc:
        raise InspectionLimit("text must be valid UTF-8") from exc


def _high_findings(text: str) -> list[Finding]:
    found = _direct_findings(text, _HIGH_RULES)
    # Pair markers in one pass. A lazy wildcard from every BEGIN is quadratic
    # on incomplete/malformed bundles containing many BEGIN markers.
    pending: dict[str, tuple[int, int | None]] = {}
    for match in _PRIVATE_KEY_MARKER_RE.finditer(text):
        kind, label = match.groups()
        if kind == "BEGIN":
            body = _PRIVATE_KEY_BODY_RE.match(text, match.end())
            if body and len(re.sub(r"\s", "", body.group("body"))) < 32:
                body = None
            pending[label] = (match.start(), body.end() if body else None)
            if body:
                _add_finding(found, Finding("C4-PRIVATE-KEY", "private_key", "C4", "secret", match.start(), body.end()))
        elif label in pending:
            start, body_end = pending.pop(label)
            if body_end is not None and not text[body_end:match.start()].strip():
                _add_finding(found, Finding("C4-PRIVATE-KEY", "private_key", "C4", "secret", start, match.end()))
    for item in _assignment_findings(text):
        _add_finding(found, item)
    return found


def scan_text(text: str, *, include_identifiers: bool = True, decode_base64: bool = True) -> list[Finding]:
    if _utf8_size(text) > MAX_TEXT_BYTES:
        raise InspectionLimit("text exceeds the local inspection limit")
    findings = _high_findings(text)
    normalized = unicodedata.normalize("NFKC", text)
    if normalized != text:
        normalized_high = _high_findings(normalized)
        # Unrelated fullwidth prose must not turn an already detected ASCII
        # test token into an obfuscated secret and remove its policy option.
        preserves_offsets = len(normalized) == len(text) and all(len(unicodedata.normalize("NFKC", char)) == 1 for char in text)
        direct_spans: set[tuple[int, int, str]] = set()
        for direct in findings:
            value = text[direct.start:direct.end]
            if preserves_offsets:
                start, end = direct.start, direct.end
            else:
                # At most MAX_FINDINGS spans need mapping. Normalize prefixes
                # to retain source identity when earlier characters expand or
                # compose; matching by value alone confuses equal credentials.
                start = len(unicodedata.normalize("NFKC", text[:direct.start]))
                end = len(unicodedata.normalize("NFKC", text[:direct.end]))
            if normalized[start:end] == value:
                direct_spans.add((start, end, value))
        for item in normalized_high:
            normalized_value = normalized[item.start:item.end]
            if (item.start, item.end, normalized_value) in direct_spans:
                continue
            if preserves_offsets:
                candidate = replace(item, rule_id="C4-NORMALIZED-SECRET", category="obfuscated_secret")
            else:
                candidate = Finding("C4-NORMALIZED-SECRET", "obfuscated_secret", "C4", "secret", 0, len(text))
            _add_finding(findings, candidate)
    if include_identifiers:
        for item in _direct_findings(text, _IDENTIFIER_RULES):
            _add_finding(findings, item)
    if decode_base64:
        for match in _BASE64_RE.finditer(text):
            decoded = _decoded_text(match.group(0))
            if decoded is None or not _high_findings(unicodedata.normalize("NFKC", decoded)):
                continue
            candidate = Finding(
                "C4-ENCODED-SECRET",
                "encoded_secret",
                "C4",
                "secret",
                match.start(),
                match.end(),
            )
            _add_finding(findings, candidate)
    return sorted(findings, key=lambda item: (item.start, item.end, item.rule_id))


def _derive_label(value: str, finding: Finding, salt: bytes) -> str:
    digest = hmac.new(salt, f"{finding.category}\0{value}".encode("utf-8"), hashlib.sha256).hexdigest()[:8]
    return f"{{{{DLP:{finding.category.upper()}:{digest}}}}}"


def _replacement(value: str, finding: Finding, salt: bytes) -> str:
    if finding.data_class != "C4":
        return _derive_label(value, finding, salt)
    digest = hmac.new(salt, f"secret\0{value}".encode("utf-8"), hashlib.sha256).hexdigest()[:8]
    return f"{{{{DLP:SECRET:{digest}}}}}"


def _literal_assignment(value: str) -> Finding | None:
    if _assignment_value_is_confident(value, literal=True):
        return Finding("C4-SENSITIVE-ASSIGNMENT", "secret_assignment", "C4", "secret", 0, len(value))
    return None


_PHONE_CONTEXT_KEYS = frozenset({"phone", "telephone", "mobile", "tel", "手机", "电话"})


def _is_phone_key(key: str) -> bool:
    return unicodedata.normalize("NFKC", key).lower() in _PHONE_CONTEXT_KEYS


def _is_context_key(key: str) -> bool:
    normalized = unicodedata.normalize("NFKC", key)
    return bool(_SENSITIVE_NAME_RE.fullmatch(normalized)) or normalized.lower() in {"authorization", "proxy-authorization"} or _is_phone_key(normalized)


def _context_findings(key: str, value: str, *, include_identifiers: bool = True) -> list[Finding]:
    normalized = unicodedata.normalize("NFKC", key)
    if _SENSITIVE_NAME_RE.fullmatch(normalized):
        literal = _literal_assignment(value)
        findings = [literal] if literal else []
    else:
        prefix = normalized + ": "
        findings = [replace(item, start=max(0, item.start - len(prefix)), end=item.end - len(prefix))
                    for item in scan_text(prefix + value, include_identifiers=include_identifiers)
                    if item.end > len(prefix)]
    if normalized != key:
        findings = [replace(item, rule_id="C4-NORMALIZED-SECRET", category="obfuscated_secret")
                    if item.data_class == "C4" else item for item in findings]
    return findings


def redact_text(text: str, *, salt: bytes | None = None, context_key: str | None = None) -> tuple[str, list[Finding]]:
    findings = scan_text(text)
    if context_key is not None:
        for item in _context_findings(context_key, text):
            _add_finding(findings, item)
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
    def validate(current: Any, depth: int = 0) -> None:
        if depth > MAX_DEPTH:
            raise InspectionLimit("value exceeds the inspection depth limit")
        if isinstance(current, dict):
            if not all(isinstance(key, str) for key in current):
                raise InspectionLimit("JSON object keys must be strings")
            for nested in current.values():
                validate(nested, depth + 1)
        elif isinstance(current, list):
            for nested in current:
                validate(nested, depth + 1)
        elif current is not None and not isinstance(current, (str, int, float, bool)):
            raise InspectionLimit("value must contain only JSON types")
    validate(value)
    try:
        return _utf8_size(json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")))
    except (TypeError, ValueError, RecursionError) as exc:
        raise InspectionLimit("value is not bounded JSON") from exc


class _ShellLexemeStream(io.StringIO):
    """Bound shlex's repeated token concatenation before it becomes quadratic."""

    def __init__(self, value: str):
        super().__init__(value)
        self.remaining = MAX_SHELL_LEXEME_CHARS

    def read(self, size: int = -1) -> str:
        value = super().read(size)
        self.remaining -= len(value)
        if self.remaining < 0:
            raise InspectionLimit("shell lexeme exceeds the local inspection limit")
        return value


def _shell_path_strings(command: str, *, depth: int = 0) -> Iterator[tuple[str, bool]]:
    """Separate a few established source/pattern operands from file operands."""
    if depth > MAX_DEPTH:
        raise InspectionLimit("shell nesting exceeds the inspection depth limit")
    if _utf8_size(command) > MAX_TEXT_BYTES:
        raise InspectionLimit("shell command exceeds the local inspection limit")
    for posix in (False, True):
        stream = _ShellLexemeStream(command)
        lexer = shlex.shlex(stream, posix=posix, punctuation_chars="();<>|&")
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens: list[str] = []
        try:
            for token in lexer:
                tokens.append(token)
                stream.remaining = MAX_SHELL_LEXEME_CHARS
        except InspectionLimit:
            raise
        except ValueError:
            yield command, False
            continue
        executable = ""
        subcommand = ""
        next_role = ""
        pattern_seen = False
        explicit_pattern = False
        options_done = False
        implicit_pattern_known = True
        python_options = True
        for token in tokens:
            candidate = token
            if len(candidate) >= 2 and candidate[0] in "\"'" and candidate[-1] == candidate[0]:
                candidate = candidate[1:-1]
            if next_role:
                role, next_role = next_role, ""
                if role == "shell":
                    yield from _shell_path_strings(candidate, depth=depth + 1)
                elif role == "source":
                    # Keep quoted/opened path references inspectable, without
                    # interpreting a final member expression as a filename.
                    yield "source: " + candidate, False
                    python_options = False
                elif role == "pattern":
                    pattern_seen = True
                else:
                    yield candidate, True
                continue
            if candidate and all(char in "<>" for char in candidate):
                next_role = "literal"
                continue
            if candidate and all(char in ";|&()" for char in candidate):
                executable = subcommand = ""
                pattern_seen = explicit_pattern = options_done = False
                implicit_pattern_known = True
                python_options = True
                continue
            if not executable:
                if re.fullmatch(r"[A-Za-z_]\w*=.*", candidate, re.DOTALL):
                    yield candidate.split("=", 1)[1], True
                    continue
                executable = candidate.rsplit("/", 1)[-1]
                yield candidate, True
            elif executable in {"sh", "bash", "zsh", "dash"} and candidate in {"-c", "-lc"}:
                next_role = "shell"
            elif re.fullmatch(r"python(?:[23](?:\.\d+)?)?", executable) and python_options and candidate == "-c":
                next_role = "source"
            elif executable == "rg" and not options_done and candidate in {"-e", "--regexp"}:
                next_role = "pattern"
                explicit_pattern = True
            elif executable == "rg" and not options_done and candidate.startswith("--regexp="):
                pattern_seen = explicit_pattern = True
            elif executable == "rg" and not options_done and candidate == "--":
                options_done = True
            elif executable == "rg" and not options_done and candidate in {"-f", "--file", "-g", "--glob", "--iglob", "-t", "--type", "-T", "--type-not", "--encoding", "--threads", "-j", "--max-count", "-m"}:
                # These operands are not regexes. In particular, -f opens a
                # file and glob operands can select sensitive input files.
                if candidate in {"-f", "--file"}:
                    explicit_pattern = True
                next_role = "literal"
            elif executable == "rg" and not options_done and candidate.startswith("-"):
                # Unknown option operands must not accidentally become an
                # exempt implicit pattern. Explicit -e remains unambiguous.
                if candidate not in {"-n", "--line-number", "-i", "--ignore-case", "-s", "--case-sensitive", "-F", "--fixed-strings", "-w", "--word-regexp", "-x", "--line-regexp", "--hidden", "-l", "--files-with-matches", "-q", "--quiet", "--no-heading", "--heading"}:
                    implicit_pattern_known = False
                assignment = re.fullmatch(r"--?[A-Za-z][\w-]*=(.*)", candidate, re.DOTALL)
                yield assignment[1] if assignment else candidate, True
            elif executable == "rg" and implicit_pattern_known and not candidate.startswith("-") and not pattern_seen and not explicit_pattern:
                pattern_seen = True
            elif executable == "git" and not subcommand and not candidate.startswith("-"):
                subcommand = candidate
                yield candidate, True
            elif executable == "git" and subcommand == "log" and not options_done and candidate == "--grep":
                next_role = "pattern"
            elif executable == "git" and subcommand == "log" and not options_done and candidate.startswith("--grep="):
                continue
            else:
                if re.fullmatch(r"python(?:[23](?:\.\d+)?)?", executable) and (candidate in {"--", "-m"} or not candidate.startswith("-")):
                    python_options = False
                if candidate == "--":
                    options_done = True
                assignment = re.fullmatch(r"(?:[A-Za-z_]\w*|--?[A-Za-z][\w-]*)=(.*)", candidate, re.DOTALL)
                candidate = assignment[1] if assignment else candidate
                complete = posix or all(candidate.count(quote) % 2 == 0 for quote in "\"'")
                yield candidate, complete


def _iter_strings(value: Any, *, path: str = "$", depth: int = 0, command_tokens: bool = False) -> Iterator[tuple[str, str, bool]]:
    if depth > MAX_DEPTH:
        raise InspectionLimit("value exceeds the inspection depth limit")
    if isinstance(value, str):
        yield path, value, False
    elif isinstance(value, dict):
        for index, (key, nested) in enumerate(value.items()):
            if isinstance(key, str):
                yield f"{path}/@key/{index}", key, False
            if command_tokens and key in ("cmd", "command") and isinstance(nested, str):
                for token_index, (candidate, complete) in enumerate(_shell_path_strings(nested)):
                    yield f"{path}/@command/{index}/{token_index}", candidate, complete
            else:
                yield from _iter_strings(nested, path=f"{path}/@item/{index}", depth=depth + 1, command_tokens=command_tokens)
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from _iter_strings(nested, path=f"{path}/{index}", depth=depth + 1, command_tokens=command_tokens)


def scan_value(value: Any, *, include_identifiers: bool = True) -> list[Finding]:
    if _json_size(value) > MAX_VALUE_BYTES:
        raise InspectionLimit("value exceeds the local inspection limit")
    findings: list[Finding] = []
    for path, text, _ in _iter_strings(value):
        for finding in scan_text(text, include_identifiers=include_identifiers):
            _add_finding(findings, replace(finding, path=path))
    for path, key, text in _iter_sensitive_values(value):
        for item in _context_findings(key, text, include_identifiers=include_identifiers):
            _add_finding(findings, replace(item, path=path))
    return findings


def _iter_sensitive_values(value: Any, path: str = "$", depth: int = 0) -> Iterator[tuple[str, str, str]]:
    if depth > MAX_DEPTH:
        raise InspectionLimit("value exceeds the inspection depth limit")
    if isinstance(value, dict):
        for index, (key, nested) in enumerate(value.items()):
            next_path = f"{path}/@item/{index}"
            if _is_context_key(key):
                if isinstance(nested, str):
                    yield next_path, key, nested
                elif type(nested) is int and _is_phone_key(key):
                    yield next_path, key, str(nested)
            yield from _iter_sensitive_values(nested, next_path, depth + 1)
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from _iter_sensitive_values(nested, f"{path}/{index}", depth + 1)


def redact_value(value: Any, *, salt: bytes | None = None) -> tuple[Any, list[Finding]]:
    if _json_size(value) > MAX_VALUE_BYTES:
        raise InspectionLimit("value exceeds the local inspection limit")
    local_salt = salt or secrets.token_bytes(32)
    findings: list[Finding] = []

    def transform(current: Any, path: str, depth: int, context_key: str | None = None) -> Any:
        if depth > MAX_DEPTH:
            raise InspectionLimit("value exceeds the inspection depth limit")
        numeric_phone = type(current) is int and context_key is not None and _is_phone_key(context_key)
        if isinstance(current, str) or numeric_phone:
            redacted, local = redact_text(str(current), salt=local_salt, context_key=context_key)
            for item in local:
                _add_finding(findings, replace(item, path=path))
            return current if numeric_phone and not local else redacted
        if isinstance(current, dict):
            transformed: dict[Any, Any] = {}
            for index, (key, nested) in enumerate(current.items()):
                next_key = key
                if isinstance(key, str):
                    next_key, key_findings = redact_text(key, salt=local_salt)
                    for item in key_findings:
                        _add_finding(findings, replace(item, path=f"{path}/@key/{index}"))
                    while next_key in transformed:
                        next_key = f"{next_key}#{index}"
                context = key if isinstance(key, str) and _is_context_key(key) else None
                transformed[next_key] = transform(nested, f"{path}/@item/{index}", depth + 1, context)
            return transformed
        if isinstance(current, list):
            return [transform(nested, f"{path}/{index}", depth + 1) for index, nested in enumerate(current)]
        return current

    redacted = transform(value, "$", 0)
    if _json_size(redacted) > MAX_REDACTED_BYTES:
        raise InspectionLimit("redacted output exceeds the local output limit")
    return redacted, findings


def contains_high_confidence(findings: Iterable[Finding]) -> bool:
    return any(finding.data_class == "C4" and finding.severity == "secret" for finding in findings)


def _safe_file_path(candidate: str) -> bool:
    candidate = re.sub(r"^[A-Za-z]:", "", candidate)
    basename = re.split(r"[/\\]", candidate)[-1]
    return bool(
        _SAFE_ENV_TEMPLATE_RE.fullmatch(basename)
        or re.search(r"(?:^|[/\\])\.ssh[/\\]id_[^/\\]+\.pub$", candidate, re.IGNORECASE)
    )


def sensitive_path_categories(value: Any, *, command_tokens: bool = True, literal_paths: bool = False) -> list[str]:
    if _json_size(value) > MAX_VALUE_BYTES:
        raise InspectionLimit("value exceeds the local inspection limit")
    categories: set[str] = set()
    for _, text, shell_literal in _iter_strings(value, command_tokens=command_tokens):
        if _utf8_size(text) > MAX_TEXT_BYTES:
            raise InspectionLimit("text exceeds the local inspection limit")
        if literal_paths or shell_literal:
            # Once the boundary supplies a whole filename, a prefix match must
            # never grant a safe-basename exemption to a different filename.
            if shell_literal and len(text) >= 2 and text[0] in "\"'" and text[-1] == text[0]:
                text = text[1:-1]
            if not _safe_file_path(text) and (
                _SENSITIVE_PATH_RE.search(text)
                or re.search(r"\.(?:pem|key|p12|pfx)$", text, re.IGNORECASE)
            ):
                categories.add("credential_store_path")
            continue
        for match in _SENSITIVE_PATH_RE.finditer(text):
            candidate = match.group(0).strip().strip("\"'")
            if _safe_file_path(candidate):
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
