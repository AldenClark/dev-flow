# Dev Flow 2.0 stable implementation

> Status: source-candidate for `2.0.0`; integrated implementation and independent static review are complete, qualification is in progress.

<!-- dev-flow-workstream-contract: v1 -->

Scope and accepted design: [stable master plan](../dev-flow-2.0/stable-master-plan.md), v5. Implement its 17 findings and required foundational decisions, qualify the final candidate, publish immutable `v2.0.0`, then update this computer's Dev Flow installation. The user authorized this complete sequence on 2026-10-03, including normal commit/push, exact-SHA hosted checks, release artifacts, publication and installation. Historical RC.9 waivers do not qualify stable.

Preserve explicit permission, secret/untrusted-content boundaries, user-owned edits, independent evidence, safe resource ownership and protected behavior. Optional route reuse is not a stable requirement; retain per-dispatch routing unless a simple measured benefit emerges. No new dependencies or general state/scheduler/ledger framework.

| Slice | Outcome | Write prefixes | Protected paths | Evidence | Status | Decision |
|---|---|---|---|---|---|---|
| S1 | A1–A5 and B0–B3 implemented and integrated | `skills/`, `governance/`, `evals/`, `tools/`, `docs/`, `.github/`, `.codex-plugin/`, `README.md`, `CHANGELOG.md`, `.agents/` | - | Focused sensitive regression tests and actual diff inspection | complete | Approved master plan |
| S2 | Final cumulative semantic/static review and five actual functional journeys | `skills/`, `governance/`, `evals/`, `tools/`, `docs/`, `.github/`, `.codex-plugin/`, `README.md`, `CHANGELOG.md`, `.agents/`, `benchmarks/dev_flow_bench_executor.py` | - | Exact candidate loading, observable native outcomes, negative controls, full deterministic suite | in-progress | Thin stable qualification; preserve first failures; narrow executor repair for the verified event-observability gap |
| S3 | Immutable source candidate has hosted compatibility and verified artifact evidence | `docs/`, `governance/`, `README.md`, `CHANGELOG.md` | - | Exact-SHA CI; archive, manifest, SBOM, checksums and attestations | pending | Hosted artifacts reused for publication |
| S4 | Stable is publicly released and primary local installation is updated | `docs/`, `governance/`, `README.md`, `CHANGELOG.md` | - | Public stable tag/release/assets; isolated public-tag install lifecycle; primary plugin version/path/content identity | pending | Record external facts immediately and qualify each action separately |

Implementation dependencies and detailed behavioral oracles are in the master plan. S1 contains disjoint local owners; shared contract/projection files are integrated by the root. Each child may edit/test its named files only and may not commit, push, publish, install, spend through an external model service, or delegate further. The root handles final integration and delivery.

Publication readiness requires the final relevant bytes, applicable hosted gates, risk-triggered independent review and verified artifacts. Installation completion requires actual listing, pinned tag and manifest/content identity. Existing conversations may retain old loaded content: installed state and current-session activation remain distinct observations.
