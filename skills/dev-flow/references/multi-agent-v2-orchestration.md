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

Separate three values in every scheduling decision:

- configured ceiling: the TOML maximum, which proves only what the client permits;
- recommended initial concurrency: one active child for a new or resumed session;
- observed effective capacity: the highest concurrency completed without HTTP 429, scheduler saturation, or a rejected spawn in this session and service state.

`preflight` reports the configured ceiling and initial recommendation but leaves effective capacity `not-observed`. Never infer service quota from the ceiling or from a previous session. Increase by at most one only after a completed, reconciled wave with no saturation signal and only when the task budget, ownership, and resources permit it.

On HTTP 429, scheduler saturation, or a capacity-rejected spawn, stop new dispatches and preserve the first failure. Reconcile or wait for already active work, then set the session allowance to one fewer active child, with a minimum of one; retry only work that never started. Do not raise the allowance again until a later completed wave is stable, and do not rewrite the configured ceiling as though the transient observation changed configuration. Repeated saturation at one child blocks further delegation for the session and falls back to root execution or a later user-authorized retry.

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

Create a task brief from `templates/task-brief.md` before every spawn. Bind the `route-agent` result, one deliverable and dependency edges to the exact repository root, base commit and worktree, current requirement and design revisions/digests, effective instruction/profile/capability fingerprint, applicable `AMB-n` dispositions, and `AC/SC/VO` IDs. Include user-owned semantics the child must not reinterpret, approved decisions/non-goals, exclusive paths/symbols/environments, resource lease, allowed/forbidden actions, separately derived black-box and white-box obligations, exact verification command/oracle, soft and hard deadlines, native-result route, optional durable-report requirement, and stop conditions.

The child must stop and return drift when the base/worktree, requirement/design baseline, effective engineering context, ownership boundary, resource lease, or `AC/SC/VO` mapping no longer matches. It must not reinterpret semantics, expand scope, add a dependency, or convert a commit-ready checkpoint into staging, commit, push, PR, or delivery authority.

The native final result delivered to the root is the primary coordination result. Request a Markdown report only when a durable independent audit/test artifact materially improves recovery or traceability; name its path in the brief. Failure to write that secondary projection must never block native child stop or by itself justify redispatch.

Default `fork_turns: "none"`; use the smallest positive fork only when exact recent wording cannot be captured safely in the brief. A spawn that overrides model/effort must use `none` or a finite positive fork; full-history forks do not accept those overrides. Full history is exceptional. Children must not delegate unless the root explicitly grants one additional bounded level.

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

Record agent path/id, role/task, dispatch profile/source, requested and effective model/effort, fork, fallback reason, spawn time, deadlines, last status, native result, duration/token/tool observations when exposed, optional report, resource lease, interrupts, final disposition, and recovery evidence in `execution.md`.

- At a soft deadline, inspect `list_agents`, retained native output, repository state, and resource ownership; then wait again or steer. Do not redispatch only because the child is quiet.
- At the declared hard deadline, inspect once more and request at most one interrupt for that task. Interruption stops active work but may intentionally leave a reusable resident thread.
- After the interrupt response, classify the task as terminal or `orphan-suspected`, recover only evidence that can be verified, release or transfer its leases, and record an honest disposition. Never start a duplicate while the original can still mutate the same scope or resource.
- Completion requires no delegated task in `spawned`, `working`, `overdue`, or `interrupt-requested`, and every ledger row reconciled as accepted, revised, rejected, cancelled, or orphan-suspected. The visible thread count does not need to return to one.

Use stable observability definitions from packet/session evidence: `DEV_FLOW_AGENT_MARKER_UNAVAILABLE` per child start, `DEV_FLOW_AGENT_REPORT_MISSING` per active child stop, orphan-suspected tasks per dispatch, duplicate dispatches to a still-owned slice, and delegation efficiency as accepted results divided by dispatched tasks. These are diagnostic signals, not targets to game.

## Result adjudication and repair

For each native result and any optional durable report, the root independently rechecks the bound base/worktree, requirement/design revisions and digests, effective engineering context fingerprint, complete diff and generated artifacts, ownership/scope, black-box and white-box accounting, test-oracle validity, commands, evidence, integration, and resource teardown. Reproduce material claims, resolve conflicts, and record accept/revise/reject. Terminal child status is coordination evidence only; root reconciliation makes the task complete.

Keep the original implementer on a bounded fix when context remains valid. After repair, rerun the affected verification and a scoped clean re-review. After three failed hypotheses or repair rounds, interrupt ongoing work, stop layering patches, classify the failure as reproduction/model/architecture/environment/oracle, and bring the evidence and design question back to the user.
