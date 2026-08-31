#!/usr/bin/env python3
"""Personal/strict DLP policy and secret-free continuation guidance."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from typing import Any, Iterable


_TEST_DECLARATION_RE = re.compile(
    r"(?:\b(?:test|testing|sandbox|development|dev|staging|dummy|fake|synthetic|fixture|non[- ]?production)\b|"
    r"测试(?:用|类|环境|数据|密钥|秘钥)?|沙箱|开发环境|非生产|假(?:的|数据|密钥|秘钥))",
    re.IGNORECASE,
)
_HARD_BLOCK_CATEGORIES = frozenset(
    {
        "private_key",
        "authorization",
        "credentialed_url",
        "encoded_secret",
        "obfuscated_secret",
    }
)
_ENV_NAMES = {
    "access_key": "TEST_ACCESS_KEY",
    "access_token": "TEST_API_KEY",
    "secret_assignment": "TEST_SECRET",
    "session_token": "TEST_SESSION_TOKEN",
}


@dataclass(frozen=True)
class StorageAdvice:
    env_name: str
    service_name: str
    save_command: str
    use_pattern: str
    caution: str


def _iter_text(value: Any, depth: int = 0) -> Iterable[str]:
    if depth > 12:
        return
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, nested in value.items():
            if isinstance(key, str):
                yield key
            yield from _iter_text(nested, depth + 1)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_text(nested, depth + 1)


def declares_test_data(value: Any) -> bool:
    """Treat a test declaration as context only, never as proof or authorization."""
    return any(_TEST_DECLARATION_RE.search(text) is not None for text in _iter_text(value))


def finding_categories(findings: Iterable[Any]) -> list[str]:
    return sorted({str(item.category) for item in findings})


def requires_hard_block(findings: Iterable[Any], path_categories: Iterable[str] = ()) -> bool:
    categories = set(finding_categories(findings))
    return bool(set(path_categories) or categories.intersection(_HARD_BLOCK_CATEGORIES))


def primary_category(findings: Iterable[Any]) -> str:
    categories = finding_categories(findings)
    return categories[0] if categories else "secret"


def storage_advice(category: str, *, platform: str | None = None) -> StorageAdvice:
    target_platform = sys.platform if platform is None else platform
    env_name = _ENV_NAMES.get(category, "TEST_SECRET")
    service_name = f"dev-flow/test-{category.replace('_', '-')}"
    if target_platform == "darwin":
        save_command = (
            f'/usr/bin/security add-generic-password -a "$USER" -s "{service_name}" -U -w'
        )
        use_pattern = (
            f'{env_name}="$(/usr/bin/security find-generic-password '
            f'-a "$USER" -s "{service_name}" -w)" your-test-command'
        )
        caution = "Enter the value only at the interactive prompt; do not use -A or print the retrieved value."
    else:
        save_command = f"Store the value in the OS or CI secret store under {env_name}."
        use_pattern = f"Expose {env_name} only to the consuming process; pass the variable name, not its value."
        caution = "Do not place the value in command arguments, repository files, logs, or chat."
    return StorageAdvice(env_name, service_name, save_command, use_pattern, caution)


def safe_summary(findings: Iterable[Any], path_categories: Iterable[str] = ()) -> str:
    categories = sorted(set(finding_categories(findings)).union(str(item) for item in path_categories))
    return ",".join(categories) if categories else "secret"
