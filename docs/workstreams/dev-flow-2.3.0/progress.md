# Dev Flow 2.3.0 release progress

<!-- dev-flow-workstream-contract: v1 -->

- State: implementation-complete
- Current slice: S1
- Published source: `2.3.0`
- Terminal condition: verify the public stable release and local Codex installation on the exact candidate.

## Current truth

- Published stable/workspace base: `v2.3.0`. Rollback target: `v2.2.0`.
- Immutable candidate: `b95ccb03715c67be3d078d5be6080cf85dd4a8ca`.

Delivery state: commit=passed; hosted_ci=passed; cross_platform=passed; independent_review=passed; tag=passed; artifact=passed; publication=passed; isolated_install=passed.

## Release observations

| ID | Condition | Gate | Status | Closure/decision |
|---|---|---|---|---|
| HC1 | Exact candidate regression and review | qualification | passed | Local 836 tests, including two platform skips, and independent finding recheck. Hosted semantic plus five compatibility cells passed |
| HC2 | Exact-source artifact and public release | qualification | passed | Verified checksums, exact-source provenance, SPDX attestation, annotated tag and formal release |
| HC3 | Isolated lifecycle and primary installation | qualification | passed | See exact-source delivery below |

## Native functional journeys

Five isolated native subagent journeys exercised the candidate Skill guidance. The owner independently checked the repaired bugfix, confirmed first-run behavior with preserved explicit limits, diagnose-only and later repair turns, the native check without unrelated connector invocation, and continued local repair without delivery. The confirmation was a separate fixture-owner turn over collaboration messaging. The MCP journey checked an available unrelated connector's inventory and did not invoke it. Primary Codex chat question rendering and live account policy remain unobserved. The later router correction did not change the guidance, and the journeys did not exercise the amended router.

## Exact-source delivery

- [CI 44205324628](https://github.com/AldenClark/dev-flow/actions/runs/44205324628) and [artifact run 44205835872](https://github.com/AldenClark/dev-flow/actions/runs/44205835872) passed on `b95ccb03715c67be3d078d5be6080cf85dd4a8ca`.
- [Public stable release](https://github.com/AldenClark/dev-flow/releases/tag/v2.3.0) was published at 2026-11-18T00:13:28Z.
- All four public downloads matched the hosted assets. Public-tag isolated install, three installed CLI controls, and native uninstall passed. The primary profile reports enabled dev-flow@dev-flow 2.3.0; all 482 release files match, the same CLI controls pass, and the required data-security doctor checks pass. The 2.2.0 cache was preserved, and unrelated plugin/marketplace records were checked. Effective loading in an existing chat remains unobserved.

Local evidence directory: `/tmp/dev-flow-v230-release.8qFfEr`.
