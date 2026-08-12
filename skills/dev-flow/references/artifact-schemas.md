# Dev Flow state contract

`<repo>/.codex/dev-flow/<change-id>/` is local state; exclude it with `.git/info/exclude` unless publication is authorized. New writes use schema 2.0; the validator still reads schemas 1.0, 1.1, and 1.2 under their original `micro`/`full` contracts.

## Work modes

- `direct`: no packet; retain the decision, scope, and fresh evidence inline for clear micro/spike work.
- `traced`: `packet.json`, append-only `events.jsonl`, `trace.md`, and optional `artifacts/`.
- `governed`: traced state plus context, requirements, design, execution, matrix, two audits, evidence, decisions, and child brief/report/artifact directories.

Auto-select governed for security, unsafe/FFI/ABI, migration, dependency, release/deployment, public protocol/API, persisted-data, regulated, rollback, or material UI semantics. Explicit user/team policy may escalate; rising risk may never silently downgrade.

## Schema 2.0 machine state

`packet.json` projects identity/version, work/documentation mode, state/time, roots/base, authority, collaboration/UI/compatibility/risk, AC/SC/VO IDs, requirement revision/digest, ambiguity/dependency ledgers, iteration control, approvals, and transition history.

`events.jsonl` is append-only schema 1.0 with contiguous sequence, event, time, projected state/mode, and payload. It starts with `packet-created`; state events exactly project `packet.json.history` and final state. Mutators append then atomically replace the projection; mismatch is invalid.

Schema 2.0 iteration state enforces the breaker in `orchestration.md`.

States and ordinary transitions are:

```text
discovering -> awaiting-approval -> approved -> implementing -> verifying -> accepted -> archived
      |                |              |              |             |
      +--------------> blocked <------+--------------+-------------+
blocked -> discovering | awaiting-approval
verifying -> implementing
implementing | verifying -> awaiting-approval (open material/high-risk AMB-n required)
```

Checkpointed/co-design work records `REQ-READY` between awaiting and approved. Material UI also records `UX-READY`. A concrete design approval is required for approved and later states. Content-bound approvals carry the current positive requirement revision and SHA-256 digest: governed hashes exact `requirements.md` bytes; traced hashes the `Requirement and design` body. Reopening archives the prior design approval, increments revision, clears the digest/current design, and requires a fresh approval cycle.

Every `AMB-n` records source, at least two interpretations, evidence, materiality, owner, affected AC/SC/VO IDs, recommendation, creation revision, status, and evidence-bearing resolution. Open material or high-risk ambiguity prevents approval.

## Documentation

`trace.md` keeps concrete authority/repository facts, INS IDs, acceptance/design, AC/SC/VO scope, protected behavior, ordered progress/decisions, fresh verification, proportionate blue/red checks, delivery status, and residual gates. No placeholder may remain.

Governed documents split those concerns so independent work is recoverable:

- context and requirements: authority, facts, instructions, semantics, ambiguity, outcomes, compatibility, exclusions;
- design and execution: decision, alternatives, failure behavior, complete scope, dependencies, task graph, ownership, drift, findings;
- test matrix and audits: environments/resources, required cells/attempts/status, clean blue/red review and adjudication;
- evidence and decisions: AC/SC/VO traceability, exact commands, changed files, remaining gates, approvals, sources, superseded choices.

Only root writes core packet state and owns final claims. Children return native finals; brief-assigned durable reports never gate stop. Root logs each task's reconciliation, deadlines, result/report, lease, interrupt, disposition, and recovery.

`current` activates hooks, not history; child lifecycle hooks ignore accepted, archived, and blocked packets. `deactivate-packet <packet>` preserves data and removes only its matching terminal regular-file pointer. Absence is idempotent; unsafe or mismatched pointers are refused.

## Identifiers and evidence

- `AC-n`: observable acceptance.
- `SC-D/I/C/P/O/Ln`: direct, indirect, conditional, protected, excluded, and delivery scope.
- `VO-n`: verification obligation.
- `DEP-n`, `INS-n`, `AMB-n`: dependency, instruction, and ambiguity records.
- `Tn`, `TM-n`, `BLUE-n`, `RED-n`: tasks, matrix cells, and review findings.

Keep IDs stable and make declared ID sets equal documented sets. Each command record includes command, absolute root, relevant environment/version, time, exit, oracle/counts, artifact, and freshness after the last relevant edit. Preserve the first failure. Status is exactly `PASSED`, `FAILED`, `FLAKY`, `BLOCKED`, `NOT RUN`, or `WAIVED`; waiver is never pass.

Schema 2.0 binds each `DEP-n` to identity, exact command/ref, files, operations and result digests. Matrix suffixes are uppercase; `Required` is `yes`/`no`. Unknowns or duplicates block acceptance.

Optional `effective-preferences.json` and `context-readiness.json` retain their v1 contracts. Accepted state cannot retain blocked preferences or readiness checkpoint/block. Absence alone is advisory.

Validate after approval, compaction, each material implementation/repair wave, final verification, and before transition. Use the CLI mutators so the event ledger and projection remain consistent.
