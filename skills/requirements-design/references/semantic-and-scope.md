# Semantic requirements and scope

Use this reference when several plausible product meanings, compatibility directions, or scope boundaries survive repository investigation. The purpose is shared understanding, not a requirements database.

## Collaboration

- Execute directly when product meaning is clear and repository facts resolve implementation.
- Pause for the user only when a surviving choice changes business behavior, public contract, scope, irreversible consequences, dependency choice, or external authority.
- Co-design when several valid product directions remain. Material UI does not require a named approval artifact when intent is already explicit.

## Understanding depth

Classify from the semantic decision Codex must make, not the user's noun:

- `U1 semantic creation/change`: new or changed product behavior, public contract, authorization, data lifecycle, user flow, external integration, migration semantics, or an unresolved defect expectation. Publish a detailed understanding and stop for confirmation before technical design.
- `U2 structural adjustment`: behavior-preserving refactor, dependency/configuration/performance work, internal interface change, or another engineering adjustment. Stop only when a user-owned behavior, compatibility, or operational meaning can change.
- `U3 defect correction`: current behavior is wrong and expected/protected behavior is established by repository evidence or a clear request. Diagnose and repair without a confirmation stop; upgrade to U1 when plausible product meanings survive.
- `U4 mechanical`: exact spelling, formatting, replacement, generated synchronization, or another deterministic edit. Proceed directly.
- `U5 read-only`: research, review, and delivery assessment, including an explicit review of a proposed design or architecture. Clarify only a material target/scope ambiguity; do not reclassify the task as U1 merely because the reviewed subject would change semantics if later implemented.

An original request may explicitly waive U1 reconfirmation when it names an already accepted requirement source or directs Codex to proceed without another stop. Do not infer a waiver from urgency or silence.

## Requirement model

Describe the actor, trigger, preconditions, inputs and trust boundary, observable outcome/state, important failures, cancellation/retry/timeout, recovery, authorization/privacy, compatibility, performance/resource limits, observability/support, non-goals, and bounded assumptions that actually matter.

Use repository-native issue or requirement IDs when the project already relies on them. Dev Flow does not create AC/SC/VO/AMB identifiers, revisions, or digests for 2.0 work.

For a U1 confirmation result, present the relevant subset under clear human-readable headings: goal/problem; current behavior and evidence; users/triggers/scenarios; intended observable behavior and important state/failure/recovery; in/out scope; protected behavior and constraints; acceptance behavior/examples; confirmed facts, user decisions, bounded assumptions, and remaining unknowns; durable knowledge impact. State explicitly that this is requirements understanding rather than technical design.

Use example mapping or a decision table for interacting business rules, state-transition scenarios for lifecycle behavior, a user journey/service blueprint for cross-participant flows, a trust-boundary/threat view for permissions and untrusted input, and a compatibility matrix for multi-version/public-contract work when the method changes the requirement meaning. Keep the method bounded and omit its process trace from the result.

## Ambiguity ownership

An ambiguity is material only when at least two plausible interpretations survive evidence gathering and lead to meaningfully different outcomes. Resolve repository facts yourself. Make low-risk reversible assumptions visible and continue. Ask the user for final product or authority semantics.

When a durable decision changes, update the managed design or repository-native record before dependent implementation continues. Conversation is enough for decisions that will not matter after the current task.

## Design and scope

A useful design record contains current facts, intended outcome and non-goals, credible alternatives, selected behavior, constraints, important failures, compatibility, rollout/rollback, verification intent, and open material decisions.

Scope should cover the intended implementation plus affected callers, consumers, generated outputs, tests, docs, configuration, packaging, telemetry, and migration surfaces. Name protected behavior and tempting exclusions when they reduce drift. Treat commit, push, PR, tag, release, migration execution, deploy, and external communication as separate delivery authority.

Classify late discovery as covered impact, implementation defect, design defect, evidence gap, unrelated opportunity, material scope expansion, or renewed product ambiguity. Reopen only the affected decision; do not invalidate unrelated completed work or create a new workflow state.

## Decision boundary

An explicit user answer or implementation request is sufficient authority for the product decision it names. It does not authorize a different dependency, destructive action, or external delivery. Record rationale in the repository only when future maintainers need it; do not create approval receipts or hash-bind prose.

For U1, the initial implementation request authorizes investigation and requirement drafting but not entry into technical design until the detailed understanding is confirmed, unless the request explicitly waives reconfirmation. After confirmation, continue through design and already-authorized local implementation without a second mandatory approval; stop again only for a new material user-owned decision or another authority boundary.
