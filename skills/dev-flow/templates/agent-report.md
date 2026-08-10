# Agent report: <change-id> / <task-id>

This is an optional durable projection when the task brief explicitly requests it. The native final result remains primary, and failure to write this file must not delay child stop.

- Outcome: <completed, blocked, or needs revision>
- Owned scope respected: <yes or exact deviation>
- Files and symbols read: <paths>
- Files and symbols changed: <paths or none>
- Commands and evidence: <exact command, root/environment, time, exit, artifact>
- Findings: <verified facts separated from inference; classify each as implementation defect, design defect, evidence gap, scope change, or candidate requirement ambiguity>
- Acceptance, scope, instruction, ambiguity, and UX mapping: <AC, SC, VO, INS, AMB IDs, bound requirement revision/digest, and applicable product constraints>
- Semantic drift: <none, or competing interpretations and affected IDs returned to root without resolving user-owned meaning>
- New dependency or scope need: <none or stop reason>
- Residual risks and unrun checks: <explicit list>
- Recommended root disposition: <accept, scoped revision, reject, or user decision>
