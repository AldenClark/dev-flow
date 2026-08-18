# Change execution: <change-id>

> Legacy packet compatibility template. Direct and managed 2.0 work uses repository implementation/progress documents without this ledger.

## Task graph

- Instruction mapping: <INS IDs assigned to tasks and their stop or verification effects>

| Task | Depends on / join | Priority / unlocks | Owner / lease | Context and read/write scope | Acceptance / oracle | Status / readiness evidence |
|---|---|---|---|---|---|---|
| T1 | none / all | critical / <task IDs> | root / epoch 1 | SC-D1; <paths> | AC-1 / VO-1 | ready; <contracts, baseline, leases, and root capacity> |

Ready means every predecessor is root-accepted, relevant contracts and baseline are frozen, ownership and resource leases are available, the oracle is complete, and root reconciliation capacity is available. Terminal child status alone does not unlock successors.

For `shared-disjoint-files`, declare every sibling write set before spawn. Sibling deltas outside a child's write set are expected; overlap or undeclared writes drain the cohort. Freeze one combined cohort candidate only after every writer is quiescent. For `isolated-worktree`, keep one candidate per task/attempt.

## Scheduler snapshot

- Capacity: <configured ceiling; governed ceiling 6; ordinary soft limit 3; observed runtime capacity; observed productive capacity>
- Current admission: <active children; terminal-but-unreconciled count and oldest age; integration queue; root capacity; hold/expand/reduce ruling>
- Task-shaped start: <1 uncertain/coupled, 2 isolated implementation, or up to 3 read-only breadth; reason>
- Productive evidence: <accepted critical-path progress, first-pass acceptance, conflicts, repair rounds, reconciliation time, and token/tool cost when exposed>
- Next ready priority: <lowest slack/longest remaining critical path, downstream unlocks, lease availability, and admission ruling>

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

| Agent/path | Task/attempt/lease epoch / role | Dispatch profile/source | Requested model/effort/fork | Effective model/effort | Spawned | Soft/hard deadline | Last status/time | Native result | Duration/tokens/tools | Fallback | Durable report | Resource lease | Interrupts | Disposition/recovery |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---:|---|
| root | T1/A1/E1 / root | root-only/user | parent-owned | parent-owned | <time> | n/a | working; <time> | inline | <observed or not-observed> | none | not required | <paths and environments> | 0 | active |

Completion requires no approved in-scope task in proposed, blocked, ready, spawned, working, draining, overdue, or interrupt-requested and a reconciled disposition for every task row. Deferral requires explicit scope authority. Resident terminal thread count is not a completion oracle.

## Integration queue

| Candidate | Isolation / task or cohort / attempt / epoch | Base and patch/commit/frozen-worktree digest | Declared / actual writes | Interface and predecessors | Required checks | Status / ruling |
|---|---|---|---|---|---|---|
| IC-1 | isolated-worktree / T1 / A1 / E1 | <base> / <digest> | <paths> / <paths> | <revision> / none | <focused and contract checks> | pending |

The root applies isolated candidates in dependency order to the current integration head. A shared cohort is already materialized, so the root freezes and verifies its combined bytes rather than reapplying child changes. Completion order is not merge order; rebase, conflict repair, shared-output regeneration, or final-byte change creates a new digest and invalidates stale review or test evidence.

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
