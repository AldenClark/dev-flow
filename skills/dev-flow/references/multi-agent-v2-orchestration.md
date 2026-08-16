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
max_concurrent_threads_per_session = 6
```

The limit controls child threads per root session; it does not include the root. Do not use the obsolete `[features.multi_agent_v2]` table or legacy depth/thread keys.

Treat `6` as the governed active-child ceiling, not a target. Use one child for an uncertain, resumed, dirty, or tightly coupled session; start two for isolated implementation; start up to three for breadth-first read-only work. Three is the ordinary soft limit. Admit a fourth through sixth child one slot at a time only when the ready frontier, isolation, root reconciliation capacity, and accepted-result evidence justify it. Resident terminal threads may remain reusable; they do not consume active-execution budget merely by remaining visible.

Separate five values in every scheduling decision:

- configured ceiling: the TOML maximum, which proves only what the client permits;
- governed active-child ceiling: the smaller of the configured ceiling and six;
- task-shaped initial concurrency: one for uncertain or coupled work, two for isolated implementation, and up to three for read-only breadth;
- observed runtime capacity: the highest concurrency admitted without HTTP 429, scheduler saturation, or a rejected spawn in this session and service state;
- observed productive capacity: the highest concurrency that improved accepted critical-path progress without growing root reconciliation backlog, conflicts, rework, or disproportionate token/tool cost.

`preflight` reports configured and governed ceilings, the ordinary soft limit, a conservative task-agnostic legacy start of one, task-shaped starting profiles, and a one-slot admission step, but leaves runtime and productive capacity `not-observed`. Consumers that know the task shape use the profiles; the legacy scalar never substitutes the isolated-write value. When configuration is skipped or unavailable, governed and starting capacities remain `null`; never substitute the policy ceiling for an unobserved client limit. Never infer runtime or productive capacity from configuration or a previous session. Effective concurrency is bounded by the configured and governed ceilings, ready-task width, isolated ownership/resource slots, and root reconciliation capacity. Increase one slot after accepted progress with no growing integration queue; hold or reduce when another child does not shorten the critical path or worsens acceptance, rework, conflicts, or cost.

On HTTP 429, scheduler saturation, or a capacity-rejected spawn, stop new dispatches and preserve the first failure. Reconcile or wait for already active work, then reduce the session allowance by at least one, with a minimum of one; retry only work that never started. When terminal-but-unreconciled results accumulate, pause admission even if runtime slots remain. Do not raise the allowance again until later accepted work proves stable, and do not rewrite the configured ceiling as though transient observations changed configuration. Repeated saturation at one child blocks further delegation for the session and falls back to root execution or a later user-authorized retry.

## Root-only responsibilities

The root owns authority and user communication, repository and requirement synthesis, task classification, approved design and scope, dependency decisions, task graph, file/resource ownership, integration, finding adjudication, fresh verification, and final claims. Children may gather evidence or critique artifacts but never replace these decisions.

## Ceremony and child budgets

| Task | Default child budget | Typical delegation |
|---|---:|---|
| Micro | 0 | none |
| Routine or spike | 0-2 | focused scan, test, or isolated implementation |
| Bug fix or dependency change | 0-3 | independent cause trace, isolated implementation, or verification |
| Large feature/refactor, migration, security, release | 0-6 | disjoint implementation, environment test, clean blue/red review |
| Read-only audit or rollback | 0-6 | independent evidence or adversarial review; three is the ordinary start |

Use fewer agents whenever work is ordered, tightly coupled, shares mutable resources, or depends on continuous user judgment. Risk modifiers raise evidence depth, not automatic agent count.

## Task graph, decomposition, and rolling dispatch

Decompose a large slice by context boundary and independently verifiable outcome, not by arbitrary file counts, equal-sized chunks, or planner/implementer/tester stages. Keep a feature, its focused tests, and the context needed to verify it with one worker unless a frozen black-box boundary makes independent verification useful. Each task records `task_id`, outcome, predecessors, join, downstream unlocks or relative slack, context partition, read/write sets, owner and lease, primary oracle, integration point, cancellation condition, attempt, and disposition.

A task is ready only when every predecessor is root-accepted, the relevant contracts and baseline are frozen, its ownership and resource leases are available, its oracle is complete, and the root has reconciliation capacity. Prioritize low-slack or critical-path work, then tasks that unlock the most downstream work; duration estimates are heuristics, not proof of an optimal schedule. Terminal child status does not make a successor ready.

Schedule the dependency graph as a rolling ready frontier. Dispatch up to the current productive allowance, keep blocked or ordered tasks out of the frontier, and fill a released slot without waiting for unrelated siblings only while integration backpressure remains clear. Reconcile a terminal task before its result unlocks successors or its paths/resources are reused. A disjoint ready task may start while another result is being integrated when root synthesis capacity remains available.

Delegate only when expected critical-path saving exceeds briefing, duplicated-context, reconciliation, merge/test, and expected conflict/repair cost. Use relative `low/medium/high` estimates when timing data is absent. Coalesce adjacent tasks when they share mutable context or cannot be accepted independently, or when coordination cost approaches useful execution work. Fine-grained means independently acceptable, not merely small.

Pipeline different byte generations where contracts are stable: workers may implement the current frontier while reviewers inspect previously frozen bytes and a test-runner owns an isolated environment. Treat `all` as the default implementation join; reserve `first-valid` or `adjudicated-ensemble` for bounded read-only or idempotent work with an explicit oracle. Never review moving bytes, expose an implementer's expected findings to an independent reviewer, or count duplicate derivations as additional implementation progress.

## Role isolation

- `dev-flow-explorer`: read-only repository/current-behavior evidence; no product edits.
- `dev-flow-worker`: one approved implementation slice; exclusive paths; no new dependency or delivery action.
- `dev-flow-test-runner`: controlled test resource lease and artifact report; does not repair product code.
- `dev-flow-blue-reviewer`: clean requirement/scope/maintainability review; read-only.
- `dev-flow-red-reviewer`: clean adversarial/failure review; read-only and defensive.

Install the bundled role configs with `dev-flow.py install-runtime`. Role TOMLs define permissions and responsibility only; they must not pin `model` or `model_reasoning_effort`. Current model names live only in `agent-dispatch-profiles.json` and are selected at spawn time.

## Dispatch profiles and routing

Before every spawn, classify one workload from the table below and run the deterministic router. Use its `requested_model`, `requested_reasoning_effort`, and `fork_turns` in the spawn call. Do not substitute effort for insufficient capability or reinterpret P3 and P4 as a total order.

```bash
python3 skills/dev-flow/scripts/dev-flow.py route-agent \
  --role dev-flow-worker --workload bounded-change \
  --risk concurrency --signal oracle-challenge
```

| Profile | Capability / effort | Default use |
|---|---|---|
| P0 | E / low | exact lookup, fixed verification command, filtering, formatting |
| P1 | E / medium | narrow documentation research, summary, deterministic mechanical change |
| P2 | B / medium | ordinary exploration, implementation, or failure triage |
| P3 | B / high | bounded causal depth, oracle challenge, routine independent review |
| P4 | F / medium | broad context or multi-step work with a clear outcome |
| P5 | F / high | cross-component/public contract, migration, concurrency, FFI, security, or complex review |
| P6 | F / xhigh | explicit critical acceptance, irreversibility, or data-loss risk |
| PX | F / max | acknowledged and evaluated exception; never automatic |

E, B, and F are symbolic efficient, balanced, and frontier capability tiers. The current registry maps them to available runtime model slugs. P3 is deeper bounded reasoning; P4 is broader capability. A task requiring both resolves to P5.

| Workload | Compatible role | Default |
|---|---|---:|
| exact lookup / documentation research / broad mapping / causal debugging | explorer | P0 / P1 / P2 / P3 |
| exact verification / failure triage | test-runner | P0 / P2 |
| mechanical / bounded / broad multi-step / cross-component change | worker | P1 / P2 / P4 / P5 |
| routine / high-risk review | blue or red reviewer | P3 / P5 |
| requirement semantics, dependency choice, architecture adjudication, final claim | root | no delegation |

The router raises the capability tier for ambiguity, conflicting evidence, cross-root or large-context work, and multi-step planning. It raises effort for bounded causal uncertainty, nondeterminism, independent review, and oracle challenge. Public contracts, migration, concurrency, FFI, security, privacy, unsafe, data, and release risks require at least P5. `high-risk-acceptance`, `irreversible`, or `data-loss-risk` signals require P6. PX requires `--acknowledge-exception`; an explicit profile below the policy result requires `--acknowledge-downgrade` so the waiver cannot be silent.

An explicit user model/effort request has host-level precedence. Still compute and retain the policy profile, record `selection_source=user`, and expose any difference rather than silently rewriting the user's choice. If the requested pair is unsupported, record `fallback_reason` and the observed `effective_model`/`effective_reasoning_effort`; inherit platform or parent selection only when safe. A non-observable effective pair stays `not-observed`, never assumed equal to the request.

## Dispatch contract

Create a task brief from `templates/task-brief.md` before every spawn. Bind the `route-agent` result, one deliverable and dependency edges to the exact repository root, base commit and worktree, current requirement and design revisions/digests, effective instruction/profile/capability fingerprint, applicable `AMB-n` dispositions, and `AC/SC/VO` IDs. Include user-owned semantics the child must not reinterpret, approved decisions/non-goals, isolation mode, exclusive files/symbols/environments and read/write sets, resource lease, allowed/forbidden actions, separately derived black-box and white-box obligations, exact verification command/oracle, soft and hard deadlines, native-result route, optional durable-report requirement, and stop conditions. In a shared checkout, exclusive symbols never weaken the one-writer-per-file rule.

The child must stop and return drift when the base/worktree, requirement/design baseline, effective engineering context, ownership boundary, resource lease, or `AC/SC/VO` mapping no longer matches. It must not reinterpret semantics, expand scope, add a dependency, or convert a commit-ready checkpoint into staging, commit, push, PR, or delivery authority.

The native final result delivered to the root is the primary coordination result. Request a Markdown report only when a durable independent audit/test artifact materially improves recovery or traceability; name its path in the brief. Failure to write that secondary projection must never block native child stop or by itself justify redispatch.

Default `fork_turns: "none"`; use the smallest positive fork only when exact recent wording cannot be captured safely in the brief. A spawn that overrides model/effort must use `none` or a finite positive fork; full-history forks do not accept those overrides. Full history is exceptional. Children must not delegate unless the root explicitly grants one additional bounded level.

Do not reveal the implementer's expected findings to an independent reviewer. A reviewer receives the approved contracts and changed surface, not the implementer's self-justification.

## Ownership and coordination

Assign one isolation mode to every delegated task:

- `shared-disjoint-files`: tasks share a checkout, so each file has exactly one writer and every sibling write set is declared in the cohort before spawn; symbol-level ownership does not permit concurrent edits to the same file. Declared sibling changes outside a child's write set are expected cohort deltas rather than baseline drift, but any overlap or undeclared path drains the cohort. Individual child bytes are already materialized and are never treated as patches to apply later; after all writers are quiescent, the root freezes and reconciles the combined cohort as one candidate;
- `isolated-worktree`: the checkout and index are isolated, but ports, databases, build directories, caches, external services, and secrets still require separate namespaces or leases;
- `read-only-frozen-bytes`: reviewers or explorers bind an exact immutable target and write no product bytes.

Each writer records `task_id`, `attempt_id`, monotonically increasing `lease_epoch`, base commit/worktree, allowed and forbidden write sets, resource namespaces, and integration order. Its terminal result reports actual touched paths, diff or commit digest, generated artifacts, checks, and unreleased resources. Serialize manifests, lockfiles, schemas, migrations, generated code, snapshots, release metadata, shared simulators, databases, ports, and build directories unless isolation is proven. Prefer workers changing source-of-truth inputs and a single integration owner regenerating or resolving shared outputs after integration.

Use one root-owned integration queue. Completion order never decides integration order. An isolated-worktree result becomes an individual patch/commit candidate; a shared-disjoint-files cohort becomes one combined candidate only after every cohort writer is quiescent and the root freezes the materialized worktree. Bind each candidate to its base, task/cohort attempts and lease epochs, patch/commit or frozen-worktree digest, declared and actual write sets, interface revision, predecessor candidates, required checks, and disposition. Apply isolated candidates in dependency order to the current integration head; for a materialized cohort, verify the frozen combined bytes without pretending to reapply its child changes. Rerun affected focused and contract checks, and bind review/test evidence to the resulting exact bytes. Rebase, conflict repair, or regeneration creates a new candidate digest and invalidates stale downstream evidence.

Use `send_message` to steer running work, `followup_task` for a bounded revision by an idle worker, `interrupt_agent` for drift or unsafe action, `list_agents` to audit tree/capacity, and minute-scale `wait_agent` calls without busy polling. A `wait_agent` timeout means only that no mailbox update arrived within that observation window; it is not evidence of death, loss, or permission to duplicate the task.

## Lifecycle reconciliation

Track each delegated task, not just each visible thread, through the normal state machine:

```text
proposed -> blocked | ready
proposed | blocked | ready -> cancelled -> reconciled
ready -> spawned
spawned -> working -> terminal -> reconciled
                    ^             |
working -> overdue -> interrupt-requested
                         |
                         +-> terminal | orphan-suspected -> reconciled
spawned | working -> draining -> terminal | orphan-suspected -> reconciled
```

Record agent path/id, role/task, dispatch profile/source, requested and effective model/effort, fork, fallback reason, spawn time, deadlines, last status, native result, duration/token/tool observations when exposed, optional report, resource lease, interrupts, final disposition, and recovery evidence in `execution.md`.

- At a soft deadline, inspect `list_agents`, retained native output, repository state, and resource ownership; then wait again or steer. Do not redispatch only because the child is quiet.
- At the declared hard deadline, inspect once more and request at most one interrupt for that task. Interruption stops active work but may intentionally leave a reusable resident thread.
- An interrupt request is not proof that a writer is quiescent. Revoke or transfer a lease only after terminal acknowledgement, observed quiescence, or quarantine that makes further writes unable to affect the integration target. A retry keeps `task_id`, increments `attempt_id` and `lease_epoch`, and rejects late stale-epoch results from automatic integration.
- After the interrupt response, classify the task as terminal or `orphan-suspected`, recover only evidence that can be verified, release or transfer its leases, and record an honest disposition. Cancel or drain descendants when an accepted predecessor or frozen premise becomes invalid. Never start a duplicate while the original can still mutate the same scope or resource.
- Completion requires no approved in-scope task in `proposed`, `blocked`, `ready`, `spawned`, `working`, `draining`, `overdue`, or `interrupt-requested`, and every task row reconciled as accepted, revised, rejected, cancelled, deferred by explicit scope authority, or orphan-suspected. The visible thread count does not need to return to one.

Use stable observability definitions from packet/session evidence: `DEV_FLOW_AGENT_MARKER_UNAVAILABLE` per child start, `DEV_FLOW_AGENT_REPORT_MISSING` per active child stop, orphan-suspected tasks per dispatch, duplicate dispatches to a still-owned slice, and delegation efficiency as accepted results divided by dispatched tasks. Also observe end-to-end makespan, critical-path completion, accepted results per wall-clock, first-pass acceptance, terminal-but-unreconciled queue age, root reconciliation/integration time, conflicts, repair rounds, cancellations, and token/tool cost when exposed. These are diagnostic signals, not targets to game; raw agent utilization or task count is not productivity.

For a critical-path straggler, first steer, narrow, or split the remaining work. Speculative duplication is exceptional and only allowed for read-only or idempotent work with a deterministic oracle, isolated resources, and an explicit cap; first accepted result wins and the other attempt is cancelled. Never duplicate a writer that still owns a mutable scope.

Before making four through six children ordinary for a task class, forward-test the same frozen representative DAG at `1`, `2`, `4`, and `6` with the same model/effort and resource policy. Compare makespan, critical-path time, accepted results, root reconciliation time, first-pass acceptance, conflicts, rework, cancellations, and token/tool cost. Promote a higher default only for task classes where the evidence shows net benefit.

## Result adjudication and repair

For each native result and any optional durable report, the root independently rechecks the bound base/worktree, requirement/design revisions and digests, effective engineering context fingerprint, complete diff and generated artifacts, ownership/scope, black-box and white-box accounting, test-oracle validity, commands, evidence, integration, and resource teardown. Reproduce material claims, resolve conflicts, and record accept/revise/reject. Terminal child status is coordination evidence only; root reconciliation makes the task complete.

Keep the original implementer on a bounded fix when context remains valid. After repair, rerun the affected verification and a scoped clean re-review. After three failed hypotheses or repair rounds, interrupt ongoing work, stop layering patches, classify the failure as reproduction/model/architecture/environment/oracle, and bring the evidence and design question back to the user.
