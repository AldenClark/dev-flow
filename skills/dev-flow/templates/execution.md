# Change execution: <change-id>

## Task graph

- Instruction mapping: <INS IDs assigned to tasks and their stop or verification effects>

| Task | Depends on | Owner | Scope IDs and paths | Acceptance | Verification | Status |
|---|---|---|---|---|---|---|
| T1 | none | root | SC-D1; <paths> | AC-1 | VO-1 | pending |

## Progress ledger

- E1: <time or order>; <phase>; <action and observed result>; <next state>

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

## Blockers and next ready task

- Blockers: <none or exact unmet prerequisite>
- Next: <task ID, readiness evidence, and stop condition>
