# Semantic requirements and scope

Use this reference when product meaning, compatibility direction, or scope is unclear. Inspect the few relevant facts needed to frame the choice, then ask the user when the choice is theirs.

## Collaboration

- Execute established local work directly when product meaning is clear; important new features still need the first implementation understanding below.
- Pause choice-dependent work for a material business/authority decision. Before an important new feature's first implementation, confirm the overall result, scope, and major technical trade-offs in one concise readback.
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

Distinguish goals and hard constraints from preferences, candidate mechanisms, and delegated exploration. Describe the observable result, its scope, and what must stay true. Investigate technical facts needed for the current decision yourself; ask promptly about unresolved product meaning rather than first designing all its technical branches.

Preserve the whole requested outcome when choosing implementation slices. Expand state, failure, recovery, or compatibility detail only where the change needs it. A one-device manual import does not need cross-device resumability without a supporting request, contract, consumer or consequential risk. An accepted promise to resume after restart without duplicate effects does need an adequate mechanism, but acceptance of a proposed mechanism does not establish its engineering value. Recommend a simpler mechanism when it delivers the same promise; bring a proposed reduction of the promise back to the user in the existing discussion. Security, data-integrity and irreversible consequences remain relevant when a reachable counterexample or platform contract establishes the need.

Use repository-native issue or requirement IDs when the project already relies on them. Dev Flow does not create AC/SC/VO/AMB identifiers, revisions, or digests for 2.0 work.

For a U1 understanding result, explain the intended behavior, scope, preserved contract, and material choices or assumptions. Include an example when it makes the result clearer. State which dependent work is paused for a choice; independent authorized learning may continue.

Use a small example, state model, or other discovery method only when ordinary prose leaves a consequential ambiguity unresolved. Stop when the result is clear enough to implement correctly.

## Ambiguity ownership

An ambiguity is material when plausible interpretations lead to meaningfully different outcomes. Read enough evidence to avoid asking for repository facts, then ask the user for product or authority semantics without exhausting technical investigation. Make low-risk reversible assumptions visible and continue.

While a choice remains open, use already-authorized read-only investigation, technical feasibility comparison, or reversible isolated probes when they can eliminate an interpretation. Such learning does not select a product branch, add a dependency, change production data, or authorize external actions. An explicit review-first request still pauses the work it names.

When a durable decision changes, update the managed design or repository-native record before dependent implementation continues. A correction also requires reconciling affected code/data, tests, children, and evidence; an updated record does not make old results current. Conversation is enough for decisions that will not matter after the current task.

## Design and scope

A useful design record explains the chosen behavior and the consequential trade-off a future maintainer needs to understand. Use the existing owner; settled local work can remain in code, tests, and the final report.

Follow the changed behavior to its affected consumers and maintained outputs. Include compatibility, migration, or rollout work only when the change affects those responsibilities. Name exclusions when they prevent scope drift. Commit, push, PR, tag, release, migration execution, deploy, and external communication require their own authority.

For late discovery, repair an in-scope defect, surface a material scope or product change, and leave unrelated opportunities aside. Reopen only the affected decision and preserve unrelated completed work.

## Decision boundary

An explicit user answer or implementation request is sufficient authority for the product decision it names. It does not authorize a different dependency, destructive action, or external delivery. Record rationale in the repository only when future maintainers need it; do not create approval receipts or hash-bind prose.

For U1, settled business meaning permits technical design within existing authority. An important new feature means a material new capability, user flow, public contract, authorization or data lifecycle, rather than an established defect or mechanical edit. Before its first implementation, confirm the overall result, scope, and major technical trade-offs with user-visible consequences. Include a field, algorithm, dependency, or data-path detail only when it changes that decision. Obtain explicit whole acceptance or an explicit waiver, then reuse it across the accepted scope. A local option answer closes only its question; partial acceptance authorizes only the accepted subset. CLI confirmation flags report caller claims and never establish user authority. Reopen only a new material choice or changed scope; do not create fixed two-round sign-off or ask again for already accepted work.
