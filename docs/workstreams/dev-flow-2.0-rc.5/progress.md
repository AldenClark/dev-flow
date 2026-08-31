<!-- dev-flow-workstream-contract: v1 -->
# Dev Flow 2.0 RC.5 progress

## Status

- State: implementation-complete
- Current slice: S4
- Terminal condition: implementation and independent review are complete; formal release is blocked by failed R4 until the version owner explicitly accepts a bounded waiver or authorizes a materially new candidate design.
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

Candidates `7472128`, `d5222bd`, `cd6be41`, and `46076015c2d75a8f25a304b8c723d0ff635f20ab` are rejected for release. The final candidate passes 690 tests in 116.092 seconds with one hosted-Windows integration skip, focused validators, and P6 independent review with no remaining P0-P2. Its R4 run-006 failed on an iCloud dataless checkpoint after one 96,049-token turn and was conservatively recovered/closed. Local-storage run-007 then timed out on the optional-capability turn after 434,198 known tokens. The single 1,800-second timeout adjustment in run-008 completed that call but recorded the same prohibited `event_type=item.started, item_type=mcp_tool_call` at 747,228 known tokens. The ledger closed and the runner did not retry.

## Next

Stop unchanged-identity R4 retries and make no further prompt, timeout, budget, or evaluator tweaks. Formal release requires an explicit version-owner decision between a bounded R4 waiver and a materially new candidate/version design. Push, hosted CI, artifact/SBOM/attestation, isolated-profile installation, signing/tag, and publication remain blocked pending that decision; primary-profile mutation remains out of scope.

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
| HC8 | Hosted compatibility and live model-semantic qualification | qualification | failed | Candidate `4607601` failed R4 after emitting prohibited `item_type=mcp_tool_call`; no unchanged-identity retry or further auxiliary tweak is allowed |
| HC9 | Exact commit, artifact, install, tag, push, and publication | qualification | blocked | Candidate commit exists locally; all external delivery actions are blocked by HC8 pending explicit version-owner disposition |

## Active convergence checkpoint

The final candidate retained a 2,000,000 single-call token ceiling and 30,000,000 total ceiling. After migrating evidence off iCloud, one bounded timeout adjustment from 900 to 1,800 seconds exposed a semantic external-tool violation rather than another resource failure. No further prompt, timeout, budget, evaluator, or unchanged-semantic retry is allowed. Progress requires an explicit bounded waiver or a materially new candidate/version design.

## Worktree boundary

- Active Git root: `/Users/ethan/Repo/dev-flow`
- Baseline: `main` at `v2.0.0-rc.4` (`bbd65d42a23be2f091d07a2d14d35ce791e1b886`).
- Pre-existing user changes: confidentiality Hook, policy, approval state, doctor, tests, references, traceability, documentation, and changelog paths shown by the initial Git status.
- Current task may integrate those exact paths plus the S0-S4 write prefixes; it must not reset or attribute unrelated changes.

## Evidence limits

- This workstream records local implementation plus independent clean-context review evidence; it is not hosted runtime, installation, or release evidence.
- Model-semantic observations remain separate from the independent source/diff review and must retain their own assessment provenance.
- Live Codex Hook loading, real Windows Job Object integration, cross-platform hosted execution, real personal outcome effects, and every external delivery action remain `NOT RUN`; local commit and independent review passed, while live model qualification failed.
