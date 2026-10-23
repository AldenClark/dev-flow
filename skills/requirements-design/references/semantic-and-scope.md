# Semantic requirements and scope

Use this reference when several plausible product meanings, compatibility directions, or scope boundaries survive repository investigation. The purpose is shared understanding, not a requirements database.

## Collaboration

- Execute established local work directly when product meaning is clear; important new features still need the first implementation understanding below.
- Pause choice-dependent work for a material business/authority decision. Separately confirm the whole business and technical understanding before an important new feature's first implementation.
- Co-design when several valid product directions remain. Material UI does not require a named approval artifact when intent is already explicit.

## Understanding depth

Classify from the semantic decision Codex must make, not the user's noun:

- `U1 semantic creation/change`: new or changed product behavior, public contract, authorization, data lifecycle, user flow, external integration, migration semantics, or an unresolved defect expectation. Publish business understanding sufficient for design; pause choice-dependent work for a material user-owned choice or explicit review-first request. Important new features also require whole-understanding confirmation before first implementation.
- `U2 structural adjustment`: behavior-preserving refactor, dependency/configuration/performance work, internal interface change, or another engineering adjustment. Stop only when a user-owned behavior, compatibility, or operational meaning can change.
- `U3 defect correction`: current behavior is wrong and expected/protected behavior is established by repository evidence or a clear request. Diagnose and repair without a confirmation stop; upgrade to U1 when plausible product meanings survive.
- `U4 mechanical`: exact spelling, formatting, replacement, generated synchronization, or another deterministic edit. Proceed directly.
- `U5 read-only`: research, review, and delivery assessment, including an explicit review of a proposed design or architecture. Clarify only a material target/scope ambiguity; do not reclassify the task as U1 merely because the reviewed subject would change semantics if later implemented.

A prior explicit acceptance of the same business and technical scope remains valid. An explicit direction to proceed without confirmation can waive the first implementation checkpoint; merely naming a requirements source, asking to build a new feature, urgency, or silence cannot. No approval receipt or ledger is required.

## Requirement model

Distinguish goals, hard constraints, preferences, candidate mechanisms, and delegated exploration before deciding what is settled. Investigate technical feasibility and compare credible alternatives autonomously; return only user-owned business trade-offs. Describe the actor, trigger, preconditions, inputs and trust boundary, observable outcome/state, important failures, cancellation/retry/timeout, recovery, authorization/privacy, compatibility, performance/resource limits, observability/support, non-goals, and bounded assumptions that actually matter.

Cover the whole requested outcome before choosing implementation slices. These dimensions reveal relevant choices; they do not require promising every imaginable recovery, compatibility or lifecycle guarantee. A one-device manual import need not acquire cross-device resumability without a request, contract, consumer or consequential risk supporting it. An accepted promise to resume after restart without duplicate effects does need an adequate mechanism. Present material guarantee trade-offs in the existing business discussion or whole-understanding confirmation, not an additional approval round. Rare security, data-integrity or irreversible consequences remain relevant; use a reachable counterexample or platform contract rather than demanding a past incident or a precise probability.

Use repository-native issue or requirement IDs when the project already relies on them. Dev Flow does not create AC/SC/VO/AMB identifiers, revisions, or digests for 2.0 work.

For a U1 understanding result, present the relevant subset: goal/problem; current behavior and evidence; users/triggers/scenarios; intended observable behavior and important state/failure/recovery; in/out scope; protected behavior and constraints; acceptance behavior/examples; confirmed facts, user decisions, bounded assumptions, and remaining unknowns; durable knowledge impact. Use headings only when they aid understanding. State which dependent work is paused for a material choice; do not imply all technical learning has stopped.

Use example mapping or a decision table for interacting business rules, state-transition scenarios for lifecycle behavior, a user journey/service blueprint for cross-participant flows, a trust-boundary/threat view for permissions and untrusted input, and a compatibility matrix for multi-version/public-contract work when the method changes the requirement meaning. Keep the method bounded and omit its process trace from the result.

## Ambiguity ownership

An ambiguity is material only when at least two plausible interpretations survive evidence gathering and lead to meaningfully different outcomes. Resolve repository facts yourself. Make low-risk reversible assumptions visible and continue. Ask the user for final product or authority semantics.

While a choice remains open, use already-authorized read-only investigation, technical feasibility comparison, or reversible isolated probes when they can eliminate an interpretation. Such learning does not select a product branch, add a dependency, change production data, or authorize external actions. An explicit review-first request still pauses the work it names.

When a durable decision changes, update the managed design or repository-native record before dependent implementation continues. A correction also requires reconciling affected code/data, tests, children, and evidence; an updated record does not make old results current. Conversation is enough for decisions that will not matter after the current task.

## Design and scope

A useful design record contains current facts, intended outcome and non-goals, credible alternatives, selected behavior, constraints, important failures, compatibility, rollout/rollback, verification intent, and open material decisions.

Scope should cover the intended implementation plus affected callers, consumers, generated outputs, tests, docs, configuration, packaging, telemetry, and migration surfaces. Name protected behavior and tempting exclusions when they reduce drift. Treat commit, push, PR, tag, release, migration execution, deploy, and external communication as separate delivery authority.

Classify late discovery as covered impact, implementation defect, design defect, evidence gap, unrelated opportunity, material scope expansion, or renewed product ambiguity. Reopen only the affected decision; do not invalidate unrelated completed work or create a new workflow state.

## Decision boundary

An explicit user answer or implementation request is sufficient authority for the product decision it names. It does not authorize a different dependency, destructive action, or external delivery. Record rationale in the repository only when future maintainers need it; do not create approval receipts or hash-bind prose.

For U1, settled business meaning permits technical design within existing authority. An important new feature means a material new capability, user flow, public contract, authorization or data lifecycle, rather than an established defect or mechanical edit. Before its first implementation, present one concise whole understanding: business scenarios/UI/rules and material states/recovery, together with the technical effects that explain the same change. Cover consequential field/default/threshold semantics, conditions, algorithms, dependencies, data paths, compatibility and risk; disclose undecided technical details. Obtain explicit whole acceptance or an explicit waiver, then reuse it across the accepted scope. A local option answer closes only its question; partial acceptance authorizes only the accepted subset. CLI confirmation flags report caller claims and never establish user authority. Reopen only a new material choice or changed scope; do not create fixed two-round sign-off or ask again for already accepted work.
