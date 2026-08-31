<!-- dev-flow-workstream-contract: v1 -->
# Dev Flow 2.0 RC.5 implementation

## Outcome

Implement the confirmed RC.5 contraction, observability, trust, privacy, and release-truth changes on the current local worktree while preserving user-owned DLP work and RC.4 as rollback.

## Slice plan

| Slice | Outcome | Write prefixes | Protected paths | Evidence | Status | Decision |
|---|---|---|---|---|---|---|
| S0 | Freeze requirements, architecture, product state, and workstream | `docs/`, `governance/`, `.codex-plugin/`, `README.md`, `CHANGELOG.md`, `AGENTS.md` | `docs/workstreams/dev-flow-2.0-rc.4/` | state validator and workstream checker | complete | D1, D8 |
| S1 | Contract public CLI and route context | `skills/dev-flow/`, `evals/`, `skills/dev-flow-maintainer/` | `skills/dev-flow/scripts/resource_coordination.py`, `skills/dev-flow/scripts/workstream_contract.py` | CLI inventory, route compatibility, compact-size, budget tests | complete | D2, D3 |
| S2 | Add read-only diagnostics and private outcome observation | `skills/dev-flow/`, `evals/`, `docs/` | - | privacy, permission, bounded-input, no-score, doctor claim tests | complete | D4 |
| S3 | Harden trust, DLP confirmation, memory, and dispatch boundaries | `skills/`, `hooks/`, `evals/`, `governance/`, `docs/`, `CHANGELOG.md` | - | adversarial trust and exact user-event confirmation tests | complete | D5, D6, D7 |
| S4 | Integrate CI, release surfaces, compatibility ownership, and final local evidence | `.github/`, `tools/`, `evals/`, `governance/`, `docs/`, `README.md`, `CHANGELOG.md`, `.codex-plugin/`, `skills/`, `hooks/`, `AGENTS.md` | `docs/workstreams/dev-flow-2.0-rc.4/` | focused and full regression, validators, compile, diff review | complete | D1-D8 |

## Acceptance

- Every required behavior in `requirements.md` has an implementation owner and failure-sensitive test.
- Public help contains only the supported RC.5 command allowlist.
- Compact route output is materially smaller and remains incrementally comparable.
- Product-state, suite-budget, confidentiality, trust-boundary, outcome, doctor, and compatibility checks pass on final local bytes.
- Existing user-owned changes are preserved and incorporated; unrelated work is not reverted.
- Final report distinguishes local evidence, `NOT RUN` delivery/live-model gates, and same-context common-mode risk.
