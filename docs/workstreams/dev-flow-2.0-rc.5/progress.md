<!-- dev-flow-workstream-contract: v1 -->
# Dev Flow 2.0 RC.5 progress

## Status

- State: implementation-complete
- Current slice: S4
- Terminal condition: S0-S4 complete; implementation hard conditions and independent clean-context review pass on final local bytes; hosted, live-model, artifact, install, tag, push, and publication evidence remains explicitly not-run.
- Updated: 2026-08-31

## Completed outcomes

- Audited the RC.4 source, public CLI, routing output, context budgets, test system, release truth, local state growth, DLP confirmation design, trust provenance, preference scoping, dispatch policy, and CI compatibility lane.
- Confirmed RC.5 outcome and local implementation authority with the version owner.
- Froze an implementation-ready design with explicit compatibility, rollback, privacy, failure, and claim boundaries.
- Established one validated product-state owner and aligned the manifest, public release truth, rollback, docs, and CI projection with RC.5 source-candidate semantics.
- Contracted the public CLI to 17 commands, reduced compact routing to decisions and identifiers, and added conservative digest-only incremental comparison plus target context budgets.
- Added read-only runtime diagnosis and private bounded outcome observation with no raw content, stable identity, upload, or score.
- Hardened untrusted-content provenance, personal-profile scope/expiry, exact user-event DLP confirmation, and single-agent dispatch defaults.
- Integrated compatibility ownership and bidirectional RC.5 traceability, then completed focused, full-regression, static, security, plugin, compile, and final-diff checks on current local bytes. Independent red-team review found and closed target-root code execution, parent-symlink read/write/enumeration escapes, missing cache directory bounds, and an unsatisfiable published/rollback lifecycle.

## Current

Local implementation and independent review are complete. Strict discovery ran 687 tests in 120.939 seconds and finished `OK` with one explicitly skipped hosted-Windows integration test. The 39 structural contracts, product-state validator, 77-path RC.5 trace, historical RC.4 static scan, method/knowledge/plugin/suite/security checks, compilation, final worktree review, and independent clean-context review pass on the recorded implementation bytes.

## Next

Remaining qualification and delivery require fresh evidence: hosted Ubuntu/macOS/Windows compatibility, live R4 model-semantic qualification, exact commit identity, artifact/SBOM/attestation, isolated-profile installation, tag, push, and publication. Primary-profile mutation remains out of scope.

## Hard conditions

| ID | Condition | Gate | Status | Closure/decision |
|---|---|---|---|---|
| HC1 | RC.5 requirements and design are confirmed and traceable | implementation | passed | Version owner request on 2026-08-31 and D1-D8 |
| HC2 | Canonical product state matches manifest and maintained release surfaces | implementation | passed | Product-state validator and release-surface contract tests passed on final local bytes |
| HC3 | Supported CLI, compact routing, and context budgets pass compatibility and negative controls | implementation | passed | Public CLI, route, incremental basis, and context-budget tests passed |
| HC4 | Doctor and outcome observation pass bounded privacy and claim-limit checks | implementation | passed | Read-only doctor and bounded concurrent private-store tests passed |
| HC5 | Trust, DLP user-event confirmation, memory, and dispatch boundaries pass adversarial tests | implementation | passed | Trust/profile/DLP/dispatch positive and negative controls passed |
| HC6 | Final local regression and same-context final-diff review pass | implementation | passed | 687 local tests, validators, compilation, and diff review passed; one hosted-Windows test remains not-run |
| HC7 | Independent clean-context review | qualification | passed | P5 independent reviewer found four trust/lifecycle blocker families; final repairs and negative controls were re-reviewed with no remaining code finding |
| HC8 | Hosted compatibility and live model-semantic qualification | qualification | not-run | Authorized on 2026-08-31; pending immutable candidate identity and external execution |
| HC9 | Exact commit, artifact, install, tag, push, and publication | qualification | not-run | Authorized on 2026-08-31; pending HC8 and exact candidate evidence |

## Active convergence checkpoint

None.

## Worktree boundary

- Active Git root: `/Users/ethan/Repo/dev-flow`
- Baseline: `main` at `v2.0.0-rc.4` (`bbd65d42a23be2f091d07a2d14d35ce791e1b886`).
- Pre-existing user changes: confidentiality Hook, policy, approval state, doctor, tests, references, traceability, documentation, and changelog paths shown by the initial Git status.
- Current task may integrate those exact paths plus the S0-S4 write prefixes; it must not reset or attribute unrelated changes.

## Evidence limits

- This workstream records local implementation plus independent clean-context review evidence; it is not hosted runtime, installation, or release evidence.
- Model-semantic observations remain separate from the independent source/diff review and must retain their own assessment provenance.
- Live Codex Hook loading, real Windows Job Object integration, cross-platform hosted execution, real personal outcome effects, live model qualification, and every delivery action remain `NOT RUN` unless separately exercised.
