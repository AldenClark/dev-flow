<!-- dev-flow-workstream-contract: v1 -->
# Dev Flow 2.0 RC.5 progress

## Status

- State: implementation-complete
- Current slice: S4
- Terminal condition: root-reconciliation scope repair, full regression, truth projections, and independent final-byte review pass; R4, hosted, artifact, install, tag, push, and publication remain separate qualification/delivery gates.
- Updated: 2026-08-31

## Completed outcomes

- Audited the RC.4 source, public CLI, routing output, context budgets, test system, release truth, local state growth, DLP confirmation design, trust provenance, preference scoping, dispatch policy, and CI compatibility lane.
- Confirmed RC.5 outcome and local implementation authority with the version owner.
- Froze an implementation-ready design with explicit compatibility, rollback, privacy, failure, and claim boundaries.
- Established one validated product-state owner and aligned the manifest, public release truth, rollback, docs, and CI projection with RC.5 source-candidate semantics.
- Contracted the public CLI to 17 commands, reduced compact routing to decisions and identifiers, and added conservative digest-only incremental comparison plus target context budgets.
- Added read-only runtime diagnosis and private bounded outcome observation with no raw content, stable identity, upload, or score.
- Hardened untrusted-content provenance, personal-profile scope/expiry, exact user-event DLP confirmation, and single-agent dispatch defaults.
- Integrated compatibility ownership and bidirectional RC.5 traceability, then completed focused, full-regression, static, security, plugin, compile, and final-diff checks on rejected candidate `7472128`. Independent red-team review found and closed target-root code execution, parent-symlink read/write/enumeration escapes, missing cache directory bounds, and an unsatisfiable published/rollback lifecycle on that earlier identity.

## Current

Candidates `7472128`, `d5222bd`, and `cd6be41` are rejected for release. The first two exposed and then identified the optional-capability `mcp_tool_call`; the frontmatter repair closed that boundary across all three turns on `cd6be41`. The same run then found a distinct semantic defect: at `DELEGATION-MONOTONIC-NARROWING` turn 2 the root implemented a useful out-of-scope child proposal and changed `outside.py`. The current repair makes root reconciliation reject and defer such proposals unless the exact expansion receives renewed user authority. Candidate `cd6be41` stopped without retry at 3,982,499 known tokens with a closed campaign ledger. The repaired bytes pass 690 tests in 116.092 seconds with one hosted-Windows integration skip, plus focused contracts, product-state, traceability, suite-budget, workstream, and diff checks.

## Next

Freeze a new exact candidate and run fresh R4 qualification. Only then proceed to hosted Ubuntu/macOS/Windows compatibility, artifact/SBOM/attestation, isolated-profile installation, tag, push, and publication. Primary-profile mutation remains out of scope.

## Hard conditions

| ID | Condition | Gate | Status | Closure/decision |
|---|---|---|---|---|
| HC1 | RC.5 requirements and design are confirmed and traceable | implementation | passed | Version owner request on 2026-08-31 and D1-D8 |
| HC2 | Canonical product state matches manifest and maintained release surfaces | implementation | passed | Product-state validator and release-surface contract tests passed on final local bytes |
| HC3 | Supported CLI, compact routing, and context budgets pass compatibility and negative controls | implementation | passed | Public CLI, route, incremental basis, and context-budget tests passed |
| HC4 | Doctor and outcome observation pass bounded privacy and claim-limit checks | implementation | passed | Read-only doctor and bounded concurrent private-store tests passed |
| HC5 | Trust, DLP user-event confirmation, memory, and dispatch boundaries pass adversarial tests | implementation | passed | Trust/profile/DLP/dispatch positive and negative controls passed |
| HC6 | Final local regression and same-context final-diff review pass | implementation | passed | Repaired bytes passed 690 tests in 116.092 seconds with one hosted-Windows integration skip; focused validators and diff checks pass |
| HC7 | Independent clean-context review | qualification | passed | P6/xhigh final-byte review confirmed user-only renewed authority, exact RC5-TRUST oracle ownership, and no remaining P0-P2 finding |
| HC8 | Hosted compatibility and live model-semantic qualification | qualification | not-run | Candidate `cd6be41` closed the optional-capability boundary but failed R4 after an out-of-scope root mutation; repaired bytes are not yet qualified |
| HC9 | Exact commit, artifact, install, tag, push, and publication | qualification | not-run | Authorized on 2026-08-31; pending HC8 and exact candidate evidence |

## Active convergence checkpoint

Two incremental per-call budget adjustments failed without advancing R4. The final budget disposition replaced them with a 2,000,000 single-call hard ceiling and retained the 30,000,000 total ceiling; it exposed a semantic external-tool violation rather than another resource failure. No further budget tuning is allowed for the rejected candidate. Progress now requires the material semantic repair and a new candidate identity.

## Worktree boundary

- Active Git root: `/Users/ethan/Repo/dev-flow`
- Baseline: `main` at `v2.0.0-rc.4` (`bbd65d42a23be2f091d07a2d14d35ce791e1b886`).
- Pre-existing user changes: confidentiality Hook, policy, approval state, doctor, tests, references, traceability, documentation, and changelog paths shown by the initial Git status.
- Current task may integrate those exact paths plus the S0-S4 write prefixes; it must not reset or attribute unrelated changes.

## Evidence limits

- This workstream records local implementation plus independent clean-context review evidence; it is not hosted runtime, installation, or release evidence.
- Model-semantic observations remain separate from the independent source/diff review and must retain their own assessment provenance.
- Live Codex Hook loading, real Windows Job Object integration, cross-platform hosted execution, real personal outcome effects, live model qualification, and every delivery action remain `NOT RUN` unless separately exercised.
