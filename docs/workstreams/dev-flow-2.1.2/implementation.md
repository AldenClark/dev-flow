# Dev Flow 2.1.2 DLP release

> Status: `2.1.2` published; isolated lifecycle and primary installation verified

<!-- dev-flow-workstream-contract: v1 -->

Release the complete accepted [DLP repair and audit](../../dlp-code-false-positive-audit.md). The user authorized commit as 2.1.2, formal release and local Dev Flow installation update on 2026-10-26. Necessary push, immutable tag, hosted/public assets and isolated lifecycle belong to that request. Prior no-additional-model-evaluation scope persists; no existing release waiver or model outcome transfers. Rollback target is public v2.1.1. Preserve unrelated plugins, user settings and old Hook caches for existing chats.

| Slice | Outcome | Write prefixes | Protected paths | Evidence | Status | Decision |
|---|---|---|---|---|---|---|
| S1 | Qualify, commit and publish the DLP batch as stable 2.1.2, verify isolated lifecycle and update the primary local installation | `.codex-plugin/plugin.json`, `.github/workflows/release-candidate.yml`, `.github/workflows/ci.yml`, `governance/product-state.json`, `README.md`, `CHANGELOG.md`, `docs/`, `skills/company-data-security/scripts/data_security.py`, `skills/company-data-security/references/control-baseline.json`, `evals/test_dlp_code_false_positives.py` | `hooks/`, `skills/dev-flow/scripts/`, `tools/`, `benchmarks/` | Cumulative static review, final native regression and validators, exact-SHA CI/artifacts, public-byte comparison, installed-source identity and synthetic Hook controls | complete | No new model campaign, dependency, protocol or runtime-state migration; no claim of existing-chat reload |

Keep this plan stable; progress owns changing observations. Tagged candidate and attested/public bytes remain immutable; a separate truth commit records actual publication and installation.
