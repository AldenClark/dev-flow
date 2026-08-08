# Task playbooks

Every playbook inherits the core lifecycle and documentation contract. Risk modifiers compose with, rather than replace, the selected playbook.

## Micro change

Inspect the exact file, caller, test, and repository instructions. Create the compact packet before editing. Record one observable AC, direct/protected/delivery scope, one design decision, progress, narrow verification, diff-based blue review, and the most relevant failure hypothesis. Do not delegate. Escalate when scope, uncertainty, compatibility, or dependency need grows.

## Routine change

Scan the subsystem and a working analogue; confirm material UX/API behavior; use the complete packet when work spans files/phases. Implement bounded slices, run affected unit/integration plus static gates, perform a scoped blue review, and add red depth for active risks. Use at most one child.

## Bug fix

Capture symptom, environment, input, logs, stack, and reproduction reliability. Trace the bad state backward across boundaries; state one causal hypothesis and run the smallest discriminating experiment. Prove a regression test fails without the fix when practical. Implement one root-cause correction, not bundled cleanup. Re-run original reproduction and nearby regressions. Preserve failed hypotheses; trigger the three-attempt breaker.

## Read-only diagnosis or audit

Record exact authority and keep product/repository state unchanged. Establish repository/runtime facts before findings. Separate observed facts, inference, and recommendations; verify every reportable finding against the current source and call path. Use independent blue/red perspectives for broad or high-risk audits. The evidence document is the deliverable; remediation requires new authority.

## Spike or prototype

Define the learning question, time/effort box, throwaway boundary, success evidence, and decision it will unblock. Prefer isolated artifacts or a temporary branch/worktree when available. Do not silently ship the prototype. Close with results, limitations, dependency implications, and adopt/reject/follow-up recommendation.

## Dependency or supply-chain change

Inventory current capability and graph. Compare standard library/platform, existing dependency, local implementation, and viable maintained candidates. Verify current versions, security, license, compatibility, graph/build/runtime costs, feature policy, rollback, and exact usage from primary sources. Write separate DEP cards and obtain approval before manifest/lockfile/tool/service edits. Validate graph diff, duplicate/native/build-script changes, lockfile integrity, advisories, licenses, and removal path.

## Large feature

Map user/system flow, domain, contracts, state, data, failures, operations, documentation, rollout, and telemetry. Confirm design sections and complete scope before implementation. Build vertical slices with early integration. Require contract, integration, compatibility, UX/accessibility, and operational evidence plus whole-change blue/red audits.

## Large refactor

Establish a green behavioral baseline and consumer inventory. State invariants and separate intended behavior change from structural movement. Prefer incremental seams or branch-by-abstraction for risky cutovers. Compare outputs, performance, public API, generated artifacts, and operations. Keep dual paths only with an owner and removal condition.

## Migration

Inventory source/target versions, consumers, persisted data, deployment order, CI, generated code, and platform/toolchain matrix. Define coexistence, compatibility direction, checkpoints, resumability/idempotency, cutover, rollback rehearsal, observation, and cleanup. Missing required compatibility, rollback, or target-platform evidence blocks full acceptance.

## Security change

Record assets, trust boundaries, attacker capabilities, abuse cases, privacy, and invariants. Minimize new capability and dependencies. Run focused static analysis, adversarial tests, secret/log review, authorization matrix, and rollback review. Require independently verified findings and a clean red disposition; retain exploit detail only to defensive need.

## Performance change

Define metric, workload, dataset, hardware, build profile, baseline, target, and variance. Profile before optimizing. Preserve correctness and portable fallback for SIMD, unsafe, native tuning, or specialized layout. Compare distributions and resource tradeoffs; keep the change only with repeatable evidence.

## Rollback or revert

Identify the exact bad change, dependent changes, data/protocol effects, current runtime state, and recovery authority. Prefer a narrow, recoverable inverse change. Do not erase unrelated user work. Test restoration of the old contract, forward compatibility of data, cleanup, and redeploy/observation steps. Record what cannot be reversed and the reapplication path.

## Release or hotfix

Freeze scope, versions, roots, artifacts, signing, deployment target, observation, and rollback owner. Reproduce impact, choose the smallest safe containment/fix, and execute mandatory platform/protocol/data/security gates. Separate implementation, commit, push, PR, tag, publish, deploy, and post-deploy states. Never report waived or missing environment checks as passed.
