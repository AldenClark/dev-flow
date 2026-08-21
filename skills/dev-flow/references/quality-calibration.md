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

Perform at most one selection for the current decision. Apply at most one-to-three selected methods whose steps can change that decision. If a method is blocked, use the returned bounded fallback or state the evidence limit; do not browse, load the full method pool, or invent prerequisites merely to obtain a named method. Re-run only after a material requirement, boundary, or evidence change. The selection is advisory and non-persisted; code, design, tests, review findings, and runtime evidence remain authoritative.

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
