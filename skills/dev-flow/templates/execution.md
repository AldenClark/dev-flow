# Change execution: <change-id>

## Task graph

- Instruction mapping: <INS IDs assigned to tasks and their stop or verification effects>

| Task | Depends on | Owner | Scope IDs and paths | Acceptance | Verification | Status |
|---|---|---|---|---|---|---|
| T1 | none | root | SC-D1; <paths> | AC-1 | VO-1 | pending |

## Progress ledger

- E1: <time or order>; <phase>; <action and observed result>; <next state>

## Continuity checkpoint

<record-checkpoint owns exactly these ten labeled fields: Trigger; Requirement baseline; Design baseline; Engineering context; Repository baseline; Repository reconciliation; Active objective and slice; Last completed and evidence; Next action and stop condition; Drift review.>

<OPEN triggers permit the active slice to evolve after a low-cost repository identity/HEAD check. SEALED triggers bind the full declared-root worktree; resume, delegation, pre-verification, and final claims must reconcile any later delta explicitly.>

## Slice and commit readiness

- Status: not commit-ready
- Slice: <bounded behavior and AC/SC IDs>
- Narrow and integration checks: <test-first or same-slice checks, module/smoke status, and remaining broad gates>
- Diff and scope audit: <user changes preserved; scope, generated outputs, dependencies, secrets, formatting, lint, and type checks>
- Test-oracle audit: <black/white accounting and failure sensitivity>
- Comment and documentation audit: <why/invariant comments and knowledge impact updated; stale/obvious comments absent>
- Delivery authority: <stage, commit, push, PR, release, migration, deploy, and external messages are independent>

## Knowledge disposition

- Impact: <none, add, update, or deprecate>
- Runtime evidence: <local packet artifacts retained for recovery and not promoted>
- Change dossier: <tracked manifest path and status, or concrete not-applicable reason>
- Project truth promotion: <implemented, verified, reusable current docs/ADR links; deferred owner/trigger; or none>
- Privacy: <sanitized semantics and secure pointers; no secret, personal raw payload, or machine-local path>

## Agent ledger

| Agent/path | Task/role | Spawned | Soft/hard deadline | Last status/time | Native result | Durable report | Resource lease | Interrupts | Disposition/recovery |
|---|---|---|---|---|---|---|---|---:|---|
| root | T1/root | <time> | n/a | working; <time> | inline | not required | <paths and environments> | 0 | active |

Completion requires no delegated task in spawned, working, overdue, or interrupt-requested and a reconciled disposition for every row. Resident terminal thread count is not a completion oracle.

## Decisions and drift

- D1: <new fact>; <inside scope, conditional activation, design defect, unrelated, or expansion>; <ruling>

## Environment and resource ownership

| Resource | Owner | Isolation | Reset and teardown | Status |
|---|---|---|---|---|
| <browser, simulator, VM, DB, port, build dir, or none> | root | <method> | <method> | available |

## Findings and repair rounds

| Finding | Evidence | Owner | Round | Ruling | Status |
|---|---|---|---:|---|---|
| <F-ID or none> | <path, log, test> | root | 1 | <fix, defer, reject> | <open or closed> |

## Change set

- Artifact: change-set.v1
- Intent and protected behavior: <frozen intent and behavior that must remain stable>
- Final bytes or read-only target: <exact final diff scope or frozen inspection target>
- Changed files: <paths, or none for read-only work>
- Decisions and drift: <owner decisions, reopened premises, and disposition>
- Narrow checks: <fresh check run against these bytes or target>
- Limits: <known limits and invalidated downstream evidence, or none>

## Blockers and next ready task

- Blockers: <none or exact unmet prerequisite>
- Next: <task ID, readiness evidence, and stop condition>
