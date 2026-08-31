<!-- dev-flow-workstream-contract: v1 -->
# Dev Flow 2.0 RC.5 progress

## Status

- State: implementation-complete
- Current slice: S4
- Terminal condition: frontmatter activation, full regression, truth projections, and independent final-byte review pass; R4, hosted, artifact, install, tag, push, and publication remain separate qualification/delivery gates.
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

Candidates `7472128` and `d5222bd` are rejected for release. The first exposed an external-tool boundary violation without exact event identity; the second preserved and reported `event_type=item.started, item_type=mcp_tool_call`. The explicit inner Skill boundary therefore did not activate early enough. The current repair adds optional capability/scanner failure to the main Skill frontmatter so the boundary is loaded before discovery. Fresh full regression passed 689 tests in 136.475 seconds with one hosted-Windows skip; P6 independent review found no remaining P0-P2. A repeat of the same MCP event on the next exact identity is terminal and will not receive a third semantic repair.

## Next

Freeze a new exact candidate commit and run one fresh R4 qualification. Only then proceed to hosted Ubuntu/macOS/Windows compatibility, artifact/SBOM/attestation, isolated-profile installation, tag, push, and publication. Primary-profile mutation remains out of scope.

## Hard conditions

| ID | Condition | Gate | Status | Closure/decision |
|---|---|---|---|---|
| HC1 | RC.5 requirements and design are confirmed and traceable | implementation | passed | Version owner request on 2026-08-31 and D1-D8 |
| HC2 | Canonical product state matches manifest and maintained release surfaces | implementation | passed | Product-state validator and release-surface contract tests passed on final local bytes |
| HC3 | Supported CLI, compact routing, and context budgets pass compatibility and negative controls | implementation | passed | Public CLI, route, incremental basis, and context-budget tests passed |
| HC4 | Doctor and outcome observation pass bounded privacy and claim-limit checks | implementation | passed | Read-only doctor and bounded concurrent private-store tests passed |
| HC5 | Trust, DLP user-event confirmation, memory, and dispatch boundaries pass adversarial tests | implementation | passed | Trust/profile/DLP/dispatch positive and negative controls passed |
| HC6 | Final local regression and same-context final-diff review pass | implementation | passed | Frontmatter activation bytes passed 689 tests in 136.475 seconds; one hosted-Windows integration remains not-run; focused validators and diff checks pass |
| HC7 | Independent clean-context review | qualification | passed | P6/xhigh final-byte review confirmed frontmatter trigger, implicit invocation, body boundary, truth projections, and test oracle; no remaining P0-P2 finding |
| HC8 | Hosted compatibility and live model-semantic qualification | qualification | not-run | Candidate `d5222bd` failed R4 with `item_type=mcp_tool_call`; the corrected activation bytes are a new, not-yet-qualified candidate |
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
