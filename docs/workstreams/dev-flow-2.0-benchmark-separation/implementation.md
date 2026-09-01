<!-- dev-flow-workstream-contract: v1 -->
# Dev Flow 2.0 release validation and benchmark separation

## Outcome

Remove repeated model qualification from the stable-release contract, replace it with cumulative semantic review, deeper static methodology review, and bounded real-function acceptance, and expose the former R4 machinery only through an independent research benchmark.

## Slice plan

| Slice | Outcome | Write prefixes | Protected paths | Evidence | Status | Decision |
|---|---|---|---|---|---|---|
| S0 | Align the release contract and product-state validator | `docs/`, `README.md`, `CHANGELOG.md`, `governance/`, `tools/`, `evals/`, `skills/` | `docs/workstreams/dev-flow-2.0-rc.2/`, `docs/workstreams/dev-flow-2.0-rc.3/`, `docs/workstreams/dev-flow-2.0-rc.4/` | focused release/state tests | complete | user-confirmed design on 2026-09-01 |
| S1 | Add the independent Dev Flow Bench surface | `benchmarks/`, `evals/`, `docs/`, `README.md` | `skills/dev-flow/scripts/dev-flow.py` | suite audit, plan, grading, and negative controls | complete | user-confirmed design on 2026-09-01 |
| S2 | Simulate the stronger stable validation without publishing | `tools/`, `docs/`, `evals/` | `.codex-plugin/` | baseline inventory, static audit, deterministic checks, no-spend plans | complete | no stable delivery or model-spend authority |
| S3 | Reconcile current truth and final evidence | `benchmarks/`, `docs/`, `evals/`, `governance/`, `skills/`, `tools/`, `README.md`, `CHANGELOG.md` | `.codex-plugin/` | workstream, validators, compilation, diff review | complete | same-context review only |
| S4 | Migrate all benchmark assets and retire active R4 qualification machinery | `.github/`, `benchmarks/`, `docs/`, `evals/`, `governance/`, `skills/`, `tools/` | `docs/workstreams/dev-flow-2.0-rc.2/`, `docs/workstreams/dev-flow-2.0-rc.3/`, `docs/workstreams/dev-flow-2.0-rc.4/` | native catalog/executor/contracts tests, active-reference scan, full deterministic suite | complete | user-authorized next stage on 2026-09-01 |

## Acceptance

- Stable validation has no R4 or complete repeated-model gate.
- Stable validation reviews the complete public-stable-to-candidate semantic delta, applies a deeper but consolidated static audit, and uses bounded real-function journeys.
- `dev-flow-bench` runs independently of product-state and release commands, defaults to non-spending planning, and separates case health, execution, assessment, comparison, and cost.
- Existing historical R4 evidence remains historical and cannot become current release truth.
- The simulation performs no model calls, commit, tag, push, publication, or primary-profile installation.
