# Quality calibration and escalation

Use this reference after initial repository discovery, after material requirement confirmation, and when a boundary/failure/final diff invalidates the current posture. Calibration is reasoning, not a document, approval, score, or lifecycle state.

## Initial calibration

Establish the smallest useful quality posture from current repository evidence:

1. Define the observable outcome and the authority boundary.
2. Separate confirmed facts, working assumptions, and user-owned business decisions.
3. Scan the changed behavior and its callers/consumers for hidden risk rather than relying only on user-supplied labels.
4. Choose a coherent slice and the native oracle that is most sensitive to its likely failure.
5. Decide independently whether an effective-host specialist, bounded method, independent review, or child model/effort can change the outcome enough to justify its cost.

Scan only relevant dimensions, but do not omit a dimension merely because the request did not name it:

- product semantics and user-visible states;
- trust boundaries, authentication, authorization, secrets, privacy, and untrusted input;
- persisted data, schema, migration, deletion, recovery, and mixed-version operation;
- public APIs, protocols, serialization, ABI/FFI, concurrency, and compatibility;
- dependencies, generated surfaces, external systems, retries, idempotency, and reconciliation;
- performance, resource ownership, observability, rollout, rollback, delivery, and irreversibility.

## Recalibration triggers

Re-run the scan when:

- scope, architecture, or a public contract changes;
- a new dependency, repository, external system, persistent-data path, or production action appears;
- a first failure contradicts the current model or oracle;
- two repairs or hypotheses fail for the same symptom;
- the implementation expands beyond the planned slice;
- release, deployment, migration execution, deletion, or another irreversible action becomes imminent.

Escalation adds only the missing control. It does not change direct work into managed work unless continuity also changed.

An intent change, interruption/resume, fork, new repository or platform, delegated repair, final-diff expansion, or edit that invalidates an affected oracle also requires a bounded recalibration of only the decisions and evidence it changes. An unchanged follow-up within the same objective and boundaries does not justify repeating the route or broadening specialists.

## Scope envelope and convergence

Before substantial discovery or mutation, keep one ephemeral scope envelope in working context:

- observable outcome and terminal condition;
- protected behavior, explicit non-goals, and already rejected expansions;
- discovery mode: `closed`, `bounded`, or `open`;
- separate read, mutation, verification, action, external, dependency, and delegation boundaries;
- facts that permit expansion and facts that require stopping or returning to the user.

Implementation and repair default to `closed`: inspect causal callers, consumers, generated surfaces, and affected tests as needed, but mutate only admitted work. Diagnosis and review default to `bounded`: inspect enough adjacent context to establish cause or impact, while reporting rather than implementing optional findings. `Open` exploration requires an explicit breadth request such as surveying alternatives, discovering opportunities, or designing beyond a fixed deliverable. `Deep`, red/blue analysis, formal rigor, managed mode, model capability, reasoning effort, or method count never changes the discovery mode.

Classify a newly discovered material item before acting:

- `required defect`: directly violates the admitted outcome or protected behavior;
- `necessary enabler`: the outcome cannot be completed or honestly verified without it; recalibrate when it crosses a material boundary;
- `optional opportunity`: useful but not required; report or defer it;
- `unrelated`: leave it untouched.

Treat a child's, reviewer's, or tool's useful out-of-scope proposal as an `optional opportunity`, never as a `necessary enabler` or root mutation authority merely because it was proposed. Root reconciliation may inspect the actual diff and validate the finding, but must reject integration and report or defer the proposal unless the user gives exact renewed authority for the added path or semantic scope. A request to "reconcile" or "decide how to handle" a useful proposal is not that authority.

Reading broadly enough to prove causality and running affected integration checks do not grant broad mutation. Reconcile the final diff, new dependencies, generated files, tools, repositories, and external actions against the envelope. Stop or seek confirmation when a material enabler changes product semantics, platform/repository scope, public contracts, dependencies, destructive/external authority, or another user-owned boundary.

### Auxiliary-mechanism convergence

Evaluation tooling, graders, test harnesses, scanners, documentation generators, release helpers, and other auxiliary mechanisms remain subordinate to the requested outcome. Count cumulative progress against the primary terminal condition, not merely whether each local repair changed a variable. After two consecutive repairs to the same auxiliary mechanism without advancing that primary terminal condition, pause for a mandatory convergence checkpoint: decide whether the mechanism is an indispensable blocker, whether a simpler fallback can support a narrower honest claim, or whether the gate should be deferred.

Unless the user explicitly asks for continued exploration or current evidence proves that no simpler valid fallback exists, simplify or replace the mechanism, use a qualified manual/native assessment, or mark the gate `BLOCKED`/`NOT RUN`; do not make a third tweak. A changed rubric, prompt, wrapper, retry parameter, or implementation detail does not reset this counter when the primary outcome is still unchanged. Preserve the original failure and report the narrower evidence limit instead of turning auxiliary perfection into a new objective.

## Capability failure isolation

Preserve the first capability failure and classify its blocking mechanism before retrying:

- `transient`: the same operation may succeed after bounded time or service recovery;
- `invariant`: the current tool, platform, configuration, or repository shape cannot satisfy the gate;
- `authority`: permission, approval, credentials, budget, or external-write authority is absent;
- `external`: a required remote service, device, account, or controlled environment is unavailable.

Do not retry an invariant, authority, or external failure while its observable readiness facts are unchanged. Retry once when a relevant fact changes, such as a newly callable tool, changed permission profile, available device/service, repaired configuration, or explicit budget/authority. A time-bounded transient retry must preserve the first failure and must not relabel a repeated or flaky outcome as `PASSED`.

Isolate the blocked gate and continue unrelated safe repository-native checks. A fallback may support a narrower claim only: same-context inspection is not independent review, a native lint is not an unavailable deep scanner, and synthetic evidence is not real-system evidence. Report the original gate as `BLOCKED` or `NOT RUN`, the qualified fallback separately, and the exact claim limit. This classification is turn-local reasoning; do not add a readiness registry, circuit-breaker record, route field, or persisted task state.

An unspecified optional capability is not authority to search for, install, or invoke a substitute. Inspect the current callable surface and repository-native commands only, and require an exact exposed tool or command identity before invocation; a capability label is not an MCP server/tool name. Never synthesize a tool identity or use an unrelated local MCP merely because it is present. If the named capability is absent, do not call Web, browser, MCP, app, computer-use, image-generation, or dynamic tools to discover or emulate it; record the first unavailable result and continue safe native checks under the narrower claim. If the user or controlled runner explicitly names and authorizes one exact local tool, keep use confined to that identity and purpose.

## Evidence freshness

Bind an evidence conclusion to the relevant bytes, scope, environment, platform, and compatibility direction it actually observed. An affected source/config/generated-file edit after a PASS invalidates that PASS until the smallest affected-scope freshness check runs again. The same rule applies after delegated edits, review repairs, new platform/repository scope, final-diff expansion, and delivery preparation.

Do not rerun an irrelevant oracle merely because any file changed: an unrelated documentation edit leaves unaffected runtime evidence current. At resume or fork, compare current Git roots and changed paths with the prior semantic checkpoint; mark only affected claims stale, carry forward clearly unaffected evidence, and choose the smallest ready next slice.

## Semantic continuation checkpoint

Before interruption/handoff and after a material objective, repository, platform, or delivery-boundary change, record only completed/current/next outcomes, the terminal condition, discovery mode, mutation/action boundary, non-goals and rejected expansions, affected Git roots, user-owned changes, active process identity when one exists, stale evidence, blockers or unrun gates, the recommended next slice, and worktree/parallel-change state. This is repository-owned continuity, not a transcript, task database, or authority to create a host task/worktree.

At resume, compaction, fork, or handoff, reconcile that checkpoint against current workstream, Git, runtime, and process facts. Conversation summaries and referenced task prose are recovery hints, not repository authority. Terminal language such as “implement fully” or “keep going” means persist through safe ready slices inside the existing envelope; it does not authorize dependencies, broader discovery, delivery, deployment, destructive/external action, or indefinite retry. Stop at the terminal outcome, a genuine blocker, a material expansion, missing authority, or a predeclared attempt/exploration limit.

Supervise only a process or session that was actually launched and whose identity is known. Preserve its first failure, use bounded backoff, distinguish running/failure/completion, and never start duplicate unchanged work merely because an observation timed out. If the host loses the process identity, mark the gate `BLOCKED` instead of guessing or relaunching.

## Capability activation

Use the effective Skills and tools exposed in the current turn as the capability surface. Match them against affected technology, framework, behavior, and risk discovered from relevant manifests, paths, call/data/state/artifact flow, confirmed requirements, current diff, and failures. An installed file, registry entry, remembered session, version, or feature flag is not proof that a capability is callable now.

Activate the smallest owner whose procedure can change a decision or evidence surface. Examples include language correctness, async/concurrency, FFI/ABI, UI/framework, database/migration, security/privacy, accessibility, packaging/signing, and browser/device/runtime verification. Check the candidate's negative trigger. If unavailable, use repository-native controls or the capability's qualified fallback; do not block ordinary work or claim specialist coverage.

Existing engineering guidance is an input, not a management task. Read effective `AGENTS.md`, repository rules, native configuration, and an applicable existing profile. Invoke `manage-engineering-profiles` or persist a resolved snapshot only for an explicit profile operation or a real unresolved policy conflict.

## Agent and reasoning route

When a child agent will actually be dispatched, run:

```text
python3 skills/dev-flow/scripts/dev-flow.py route-agent \
  --role <role> \
  --workload <workload> \
  [--risk <observed-risk>] \
  [--signal <reasoning-signal>]
```

Use the returned child role, model, reasoning effort, and fork request. P0-P1 use Luna for exact, narrow, or mechanical work. P2 may use Luna only when semantics and scope are closed and a deterministic oracle bounds the work. P3-P4 use Terra for ordinary multi-step work, causal depth, trade-offs, and routine independent review. P5 uses Sol for open cross-component or critical engineering boundaries; P6 covers critical acceptance, irreversibility, or data-loss exposure. PX is an explicit evaluated exception.

Routing is task-relative. Do not store the profile, generate a dispatch receipt, or turn a higher profile into a quality claim. If the selected route makes delegation more expensive than doing the work in the root context, do not delegate.

## Method activation

Use the owning specialist Skill directly when its established procedure is sufficient. At one of the following concrete failure mechanisms, either use that procedure or perform one bounded method match through the public task route:

- migration, mixed-version data, rollback, or reconciliation;
- FFI/ABI/unsafe ownership and lifecycle;
- concurrency, nondeterminism, ordering, or distributed state;
- security/privacy, authorization, public protocol/API, or regulated behavior;
- irreversible/data-loss consequence;
- repeated failed hypotheses, conflicting evidence, or an oracle challenge;
- interacting business rules, state lifecycle, cross-participant flow, or a requirement model that examples can disambiguate.

This is active method matching, not a requirement to call the CLI. When a deterministic lookup would help, use the integrated route and supply only observed facts and prerequisites, for example:

```text
python3 skills/dev-flow/scripts/dev-flow.py route-task \
  --intent design \
  --risk ffi \
  --method-signal multi-version-coexistence \
  --method-prerequisite repository-facts \
  --method-prerequisite requirement-baseline \
  --compact
```

The command path is resolved from the loaded Dev Flow Skill/plugin, not from the target repository. Do not use the lower-level `select-methods` maintenance interface from ordinary task execution, and do not pass the target repository as its methodology source root.

Separate five questions: whether the observed failure mechanism makes a method eligible; which candidate fits; whether its prerequisites make it ready; which disposition is taken; and whether realization changed an owned decision or evidence surface. A valid disposition is exactly one of: execute a ready method, execute the explicit fallback for a blocked method while retaining its limitation, or abstain because the owning specialist already supplies a sufficient discriminating procedure. Selection without a disposition is incomplete; absence of a method name is not itself a defect.

Perform at most one selection for the current decision and prefer one directly relevant, ready, lower-cost method. Apply at most three only when each addresses a distinct failure mechanism and has a concrete evidence obligation. Recheck readiness after repository discovery, material requirement confirmation, an oracle-breaking first failure, repeated non-progress, and before material verification/review; do not repeat when the decision, facts, and prerequisites are unchanged. Never invent a repository fact, stable contract, independent implementation, user example, live environment, or authority merely to make a method ready.

If a candidate is blocked, use its bounded fallback or retain the evidence limit; do not browse, load the full method pool, or broaden discovery merely to obtain a ready method name.

A ready method or fallback is realized only when it changes an owned surface: a test/property/mutation, counterexample, state/decision/compatibility model, review attack surface, evidence matrix, or explicit claim limitation. A selected ID, method mention, generated method artifact, or invocation count is not realization or quality evidence. Method depth remains subordinate to the active scope envelope. The selection is advisory and non-persisted; code, design, tests, review findings, and runtime evidence remain authoritative.

## Independent review

Use an independent context when at least one is true:

- material security, privacy, migration, compatibility, rollback, or data-loss exposure;
- the implementer selected a consequential trade-off with credible alternatives;
- evidence conflicts or the primary oracle may share the implementation's blind spot;
- repository or regulatory policy requires separation of duties.

Do not recursively review a review. When the primary task is already an independent read-only review, the current context owns that review; add a second context only for an explicit second-opinion/separation requirement or a concrete conflicting-evidence blind spot.

If a child is actually justified, use registered runtime vocabulary rather than guessed labels. For a high-risk adversarial review:

```text
python3 skills/dev-flow/scripts/dev-flow.py route-agent \
  --role dev-flow-red-reviewer \
  --workload high-risk-review \
  --signal independent-review
```

Freeze the relevant objective, contracts, diff/scope, and raw evidence for the review. Recheck findings in current source. Do not require a review packet, profile record, or generated report.

When the route requires independent review, either execute that clean-context route or explicitly downgrade to same-context review and report `common-mode-risk`. A blue/red sequence performed by the implementer is a pair of useful lenses, not independent evidence. Do not silently treat unavailable or unauthorized delegation as satisfied review.
