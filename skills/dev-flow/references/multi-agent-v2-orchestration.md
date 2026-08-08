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

Create a task brief from `templates/task-brief.md` before every spawn. Include one deliverable, dependency edges, exact repository root, instructions/Skills, owned paths/symbols/environments, AC/SC IDs, approved decisions/non-goals, allowed/forbidden actions, verification command/oracle, report path, and stop conditions.

Default `fork_turns: "none"`; use the smallest positive fork only when exact recent wording cannot be captured safely in the brief. Full history is exceptional. Children must not delegate unless the root explicitly grants one additional bounded level.

Do not reveal the implementer's expected findings to an independent reviewer. A reviewer receives the approved contracts and changed surface, not the implementer's self-justification.

## Ownership and coordination

Assign exclusive write ownership. Serialize manifests, lockfiles, schemas, migrations, generated code, snapshots, release metadata, shared simulators, databases, ports, and build directories unless isolation is proven.

Use `send_message` to steer running work, `followup_task` for a bounded revision by an idle worker, `interrupt_agent` for drift or unsafe action, `list_agents` to audit tree/capacity, and minute-scale `wait_agent` calls without busy polling. Record every dispatch and disposition in `execution.md`.

## Result adjudication and repair

For each report, read its referenced source/diff/artifact, verify ownership and scope, reproduce material claims, resolve conflicts, and record accept/revise/reject. Agent completion is coordination evidence only.

Keep the original implementer on a bounded fix when context remains valid. After repair, rerun the affected verification and a scoped clean re-review. After three failed hypotheses or repair rounds, interrupt ongoing work, stop layering patches, classify the failure as reproduction/model/architecture/environment/oracle, and bring the evidence and design question back to the user.
