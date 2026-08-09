# Trace packet contract

Use one packet per change under `<repo>/.codex/dev-flow/<change-id>/`. The packet is the recovery and audit record. Keep it local by default through `.git/info/exclude`; commit or publish it only with explicit user authority.

## Machine-readable state

`packet.json` is the identity and state source of truth. New packets use schema 1.1; the validator must continue to accept schema 1.0 packets under their original contract. Require:

- `schema_version`, `skill_version`, `change_id`, `task_type`, `documentation_profile`, timestamps, repository roots, base Git state, authority, compatibility, and risk modifiers;
- for schema 1.1, `collaboration_profile` (`execute`, `checkpointed`, or `co-design`) and `ui_impact` (`none`, `preserve`, or `material`);
- declared `acceptance_ids`, `scope_ids`, `verification_ids`, and dependency changes;
- requirement, conditional UX, design, dependency, waiver, and delivery approvals;
- append-only state history.

Use only these states and transitions:

```text
discovering -> awaiting-approval -> approved -> implementing -> verifying -> accepted -> archived
      |                |              |              |             |
      +--------------> blocked <------+--------------+-------------+
blocked -> discovering | awaiting-approval
verifying -> implementing
```

For schema 1.1, record the canonical `REQ-READY` Requirement Ready approval before `approved` in checkpointed/co-design work and the canonical `UX-READY` approval before `approved` when `ui_impact` is `material`. Readiness records require a concrete actor, note, and timezone-aware timestamp, may be created only while `awaiting-approval`, and must fall between the applicable awaiting-approval and approved history events. Record a concrete design approval before `approved`; in unambiguous `execute` work, the user's explicit implementation request may be the approval source under the conditions in `collaboration-checkpoints.md`, without a redundant acknowledgement. Do not enter `accepted` with an invalid packet, unapproved dependency, unresolved required test cell, or missing acceptance evidence.

## Complete documentation profile

Use for all non-micro implementation and non-trivial read-only audit work:

- `context.md`: authority, repository roots and facts, instruction ledger, collaboration/readiness, current behavior/reproduction, constraints, protected behavior, assumptions, open questions;
- `requirements.md`: user/product outcome, requirement delta, AC IDs, non-functional needs, compatibility, exclusions, Requirement Ready, confirmation record;
- `design.md`: decision, preferences, alternatives, architecture/failures, conditional product/UX contract, DEP decisions, complete SC scope, compatibility, rollout/rollback/cleanup, VO obligations, approval;
- `execution.md`: task graph, append-only progress, agent ledger, decisions/drift, environment leases, findings/repair rounds, blockers/next task;
- `test-matrix.md`: dimensions, resources, cells, attempts, statuses, flaky triage, teardown, acceptance/release gates;
- `blue-audit.md`: clean review brief, requirement/scope/integration review, verified findings, disposition;
- `red-audit.md`: threat/failure hypotheses, adversarial checks, verified findings, disposition;
- `evidence.md`: AC/SC/VO traceability, instruction/collaboration/UX evidence, exact commands, audit/test summary, changed-file accounting, remaining gates, delivery states;
- `decisions.md`: material choices, user approvals, consulted sources, superseded decisions;
- `briefs/`: one immutable assignment brief per child task;
- `reports/`: child-owned result reports; children do not edit core packet documents;
- `artifacts/`: logs, screenshots, traces, benchmarks, reports, hashes, or links governed by retention policy.

For schema 1.1 full packets, require at least one `INS-n` record in `context.md` and the same instruction-ID set in `design.md`, `execution.md`, `test-matrix.md`, both audit documents, and `evidence.md`. Each downstream occurrence must explain the rule's applicable design, task, test, audit, or final-evidence effect. Micro traces require at least one `INS-n` record in the single trace document.

## Compact micro profile

Use `packet.json`, `trace.md`, and the three subdirectories. `trace.md` must still contain collaboration/UI classification, applicable instructions, authority/repository evidence, requirement/design, AC/SC/VO IDs, scope/protected behavior, progress/decisions, verification, a proportionate blue/red check, delivery, and residual risk.

Escalate to the complete profile when scope crosses files/components, a public contract or compatibility issue appears, a dependency is needed, reproduction is uncertain, risk rises, or delegation becomes useful. Preserve the original trace and record the escalation.

## Identifier and trace rules

- `AC-n`: observable acceptance criterion, present in requirements, execution, and evidence.
- `SC-D/I/C/P/O/Ln`: direct, indirect, conditional, protected, out-of-scope, and delivery scope; present in design, execution, and evidence.
- `VO-n`: verification obligation; present in design, test matrix, and evidence.
- `DEP-n`: dependency decision; approval is also recorded in `packet.json`.
- `INS-n`: material instruction or convention; record source/scope/effect/evidence in context and trace applicable IDs through tasks, audits, and evidence.
- `Tn`, `TM-n`, `BLUE-n`, `RED-n`: task, matrix cell, and audit finding identifiers.

Keep IDs stable. Supersede rather than renumber. Machine-readable ID lists must equal the documented sets.

## Evidence quality

Every command record includes exact command, absolute root, environment/configuration/version, timestamp, exit code, counts, artifact path, and whether it ran after the final relevant edit. Retain the first failure before retries. A child claim, stale run, passing linter, or partial environment is not final product evidence.

Use only `PASSED`, `FAILED`, `FLAKY`, `BLOCKED`, `NOT RUN`, or `WAIVED`. A waiver requires named user approval and never becomes `PASSED`.

## Ownership and update policy

The root alone writes `packet.json` and core documents. A child writes only its assigned report/artifact paths unless its brief grants an exclusive product-code boundary. Append progress at meaningful events; do not rewrite history to make execution look linear.

Validate after requirement/design confirmation, each implementation wave, audit repair, final verification, and before state transitions. Use `dev-flow.py transition` and `record-approval` so history and approval records remain consistent.
