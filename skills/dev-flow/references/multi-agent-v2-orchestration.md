# Multi-Agent V2 orchestration

Require Codex 0.147.0+ and the stable `multi_agent_v2` feature. Do not maintain a V1 path.

## Runtime contract

Use this shape:

```toml
[features]
multi_agent = true
multi_agent_v2 = true
hooks = true

[agents]
max_concurrent_threads_per_session = 3
```

The limit controls child threads per root session; it does not include the root. Do not use the obsolete `[features.multi_agent_v2]` table or legacy depth/thread keys.

Treat `3` as a capacity ceiling, not a target. Operationally start one child and keep no more than two children active for ordinary independent slices. Use three only when all slices are independent, briefs and ownership are complete, resource isolation is proven, and root synthesis capacity is reserved. Resident terminal threads may remain reusable; they do not consume active-execution budget merely by remaining visible.

## Root-only responsibilities

The root owns authority and user communication, repository and requirement synthesis, task classification, approved design and scope, dependency decisions, task graph, file/resource ownership, integration, finding adjudication, fresh verification, and final claims. Children may gather evidence or critique artifacts but never replace these decisions.

## Ceremony and child budgets

| Task | Default child budget | Typical delegation |
|---|---:|---|
| Micro | 0 | none |
| Routine or spike | 0-1 | focused scan, test, or isolated implementation |
| Bug fix or dependency change | 0-2 | independent cause trace, implementation, or verification |
| Large feature/refactor, migration, security, release | 0-3 | disjoint implementation, environment test, clean blue/red review |
| Read-only audit or rollback | 0-2 | independent evidence or adversarial review |

Use fewer agents whenever work is ordered, tightly coupled, shares mutable resources, or depends on continuous user judgment. Risk modifiers raise evidence depth, not automatic agent count.

## Role isolation

- `dev-flow-explorer`: read-only repository/current-behavior evidence; no product edits.
- `dev-flow-worker`: one approved implementation slice; exclusive paths; no new dependency or delivery action.
- `dev-flow-test-runner`: controlled test resource lease and artifact report; does not repair product code.
- `dev-flow-blue-reviewer`: clean requirement/scope/maintainability review; read-only.
- `dev-flow-red-reviewer`: clean adversarial/failure review; read-only and defensive.

Install the bundled role configs with `dev-flow.py install-runtime`. Resolve current models by capability at runtime; do not hardcode a model name in the policy. Use strongest capability for root synthesis, ambiguity, security, migration, concurrency, FFI, audits, and acceptance; balanced capability fits deterministic bounded work.

## Dispatch contract

Create a task brief from `templates/task-brief.md` before every spawn. Include one deliverable, dependency edges, exact repository root, instructions/Skills, owned paths/symbols/environments, AC/SC IDs, current requirement revision/digest, applicable `AMB-n` dispositions, user-owned semantics the child must not reinterpret, approved decisions/non-goals, allowed/forbidden actions, verification command/oracle, soft and hard deadlines, resource lease, native-result route, optional durable-report requirement, and stop conditions.

The native final result delivered to the root is the primary coordination result. Request a Markdown report only when a durable independent audit/test artifact materially improves recovery or traceability; name its path in the brief. Failure to write that secondary projection must never block native child stop or by itself justify redispatch.

Default `fork_turns: "none"`; use the smallest positive fork only when exact recent wording cannot be captured safely in the brief. Full history is exceptional. Children must not delegate unless the root explicitly grants one additional bounded level.

Do not reveal the implementer's expected findings to an independent reviewer. A reviewer receives the approved contracts and changed surface, not the implementer's self-justification.

## Ownership and coordination

Assign exclusive write ownership. Serialize manifests, lockfiles, schemas, migrations, generated code, snapshots, release metadata, shared simulators, databases, ports, and build directories unless isolation is proven.

Use `send_message` to steer running work, `followup_task` for a bounded revision by an idle worker, `interrupt_agent` for drift or unsafe action, `list_agents` to audit tree/capacity, and minute-scale `wait_agent` calls without busy polling. A `wait_agent` timeout means only that no mailbox update arrived within that observation window; it is not evidence of death, loss, or permission to duplicate the task.

## Lifecycle reconciliation

Track each delegated task, not just each visible thread, through the normal state machine:

```text
spawned -> working -> terminal -> reconciled
                    ^             |
working -> overdue -> interrupt-requested
                         |
                         +-> terminal | orphan-suspected -> reconciled
```

Record agent path/id, role/task, spawn time, soft and hard deadline, last observed status/time, native-result status, optional-report status, resource lease, interrupt count, final disposition, and recovery evidence in `execution.md`.

- At a soft deadline, inspect `list_agents`, retained native output, repository state, and resource ownership; then wait again or steer. Do not redispatch only because the child is quiet.
- At the declared hard deadline, inspect once more and request at most one interrupt for that task. Interruption stops active work but may intentionally leave a reusable resident thread.
- After the interrupt response, classify the task as terminal or `orphan-suspected`, recover only evidence that can be verified, release or transfer its leases, and record an honest disposition. Never start a duplicate while the original can still mutate the same scope or resource.
- Completion requires no delegated task in `spawned`, `working`, `overdue`, or `interrupt-requested`, and every ledger row reconciled as accepted, revised, rejected, cancelled, or orphan-suspected. The visible thread count does not need to return to one.

Use stable observability definitions from packet/session evidence: `DEV_FLOW_AGENT_MARKER_UNAVAILABLE` per child start, `DEV_FLOW_AGENT_REPORT_MISSING` per active child stop, orphan-suspected tasks per dispatch, duplicate dispatches to a still-owned slice, and delegation efficiency as accepted results divided by dispatched tasks. These are diagnostic signals, not targets to game.

## Result adjudication and repair

For each native result and any optional durable report, read referenced source/diff/artifacts, verify ownership and scope, reproduce material claims, resolve conflicts, and record accept/revise/reject. Terminal child status is coordination evidence only; root reconciliation makes the task complete.

Keep the original implementer on a bounded fix when context remains valid. After repair, rerun the affected verification and a scoped clean re-review. After three failed hypotheses or repair rounds, interrupt ongoing work, stop layering patches, classify the failure as reproduction/model/architecture/environment/oracle, and bring the evidence and design question back to the user.
