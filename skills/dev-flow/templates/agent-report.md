# Agent report: <change-id> / <task-id>

> Legacy packet compatibility template. Do not use for direct or managed 2.0 work.

This is an optional durable projection when the task brief explicitly requests it. The native final result remains primary, and failure to write this file must not delay child stop.

- Outcome: <completed, blocked, or needs revision>
- Owned scope respected: <yes or exact deviation>
- Bound baseline recheck: <base commit/worktree, requirement revision/digest, design revision/digest, and whether each still matches>
- Effective engineering context recheck: <instruction/profile/capability fingerprint and whether it still matches>
- Dispatch receipt: <workload, selected profile, selection source, requested/effective model and reasoning effort, fork, fallback reason, duration, token/tool observations, and whether runtime substitution occurred>
- Files and symbols read: <paths>
- Files and symbols changed: <paths or none>
- Commands and evidence: <exact command, root/environment, time, exit, artifact>
- Black-box and white-box accountability: <separate obligations, mapped VO/TM IDs, executed status, and concrete reason for any N/A>
- Test-oracle validity: <negative control, pre-fix failure, mutation/perturbation, assertion-path inspection, or cross-oracle evidence; unresolved weakness is an evidence gap>
- Slice closeout: <diff/generated/dependency/secret/comment/doc/test audit, narrow plus module/smoke results, and commit-ready status without stage/commit/push authority>
- Findings: <verified facts separated from inference; classify each as implementation defect, design defect, evidence gap, scope change, or candidate requirement ambiguity>
- Acceptance, scope, instruction, ambiguity, and UX mapping: <AC, SC, VO, INS, AMB IDs, bound requirement and design revisions/digests, and applicable product constraints>
- Semantic drift: <none, or competing interpretations and affected IDs returned to root without resolving user-owned meaning>
- New dependency or scope need: <none or stop reason>
- Resource lease and teardown: <released/transferred status and evidence>
- Residual risks and unrun checks: <explicit list>
- Recommended root disposition: <accept, scoped revision, reject, or user decision; root must independently recheck diff, baselines, context, tests/oracles, integration, and teardown>
