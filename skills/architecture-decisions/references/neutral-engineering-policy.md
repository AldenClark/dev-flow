# Neutral engineering policy

These are portable preferences among correct options. They do not override explicit user authority, safety or law, observed repository/runtime contracts, or valid existing conventions.

## Evidence and change discipline

- Inspect the nearby implementation or contract needed to decide the current task; follow manifests, runtime, or callers only when they can change that decision.
- Separate observed fact, inference, recommendation, and unavailable evidence.
- Make the smallest coherent change and avoid opportunistic refactors.
- Remove dead code created by the change; add compatibility layers only for an identified consumer and removal condition.

## Coherent slices

- Refresh product intent, affected behavior, or worktree context when it has changed or is missing for the next action.
- Keep related production code, focused tests, maintained documentation, and comments aligned when they express one behavior.
- Run the focused check for changed behavior; broaden to a module suite or integration path when it resolves a distinct affected risk.
- Before calling the work complete, inspect the final diff and relevant checks. Protect user-owned changes and sensitive data; include generated metadata or maintained documentation when the change affects them.
- Completion evidence never authorizes stage, commit, push, PR, release, or deployment.

## Native idiom and abstraction

- Select by language, framework/version, artifact role, boundary, ownership, and call path.
- Prefer domain and protocol names over generic enterprise suffixes; names alone are never violations.
- Prefer clear local duplication over an unstable abstraction.
- Introduce an abstraction for a stable concept, real variation axis, ownership boundary, public extension, valuable test boundary, or repeated behavior.

## Types, failures, and resources

- Use strong types, explicit capabilities, validated constructors, and exhaustive state handling where they reduce invalid states.
- Validate external input, reloaded persisted data and cross-process representations at their trust boundary. Rely on validated internal types for invariants they actually guarantee; avoid repeating the same validation at every layer. Dynamic authorization and state checks remain necessary.
- Use typed/matchable errors at library/domain boundaries and add operational context at application boundaries. Handle contractual recoverable failures; do not replace them with assertions, empty results or default success. Internal invariant violations follow language and repository conventions, including assertions where appropriate, without an automatic recovery promise.
- Add retries, compensation, durable recovery, fallback stores or generic result wrappers only for a current responsibility with a credible failure model. Before removing an existing defense, trace its consumers and the responsibility that remains. A reachable counterexample or platform contract can justify protection without a past incident; low frequency alone cannot dismiss serious consequences.
- Give resources and concurrent tasks an owner and a completion or cleanup path. Add deadlines, queues, overload handling, or durable recovery when the current responsibility needs them.
- Verify resource release and lifecycle transitions affected by the change. Require timeout/cancellation/recovery-specific proof when that path executes; normal completion owes its own result and resource guarantees, not evidence of an untriggered failure response.

## Falsifiable design choices

- Use an existing suitable convention directly. Compare alternatives when a material difference in benefit, cost, compatibility, or reversibility needs a decision; record only facts a future change needs.
- State why a material choice is worthwhile. Use a spike, contract check, measurement, or failure/recovery scenario only when it can resolve uncertainty that changes the choice.
- AHA and design ablation apply only when a proposed abstraction, layer, dependency, cache, state machine, or extension point has unclear value. Keep local duplication or remove/bypass the isolated component, compare required behavior and failure surface, then simplify or retain the demonstrated responsibility.
- For disputed or costly defenses, explain the owned boundary, credible failure, existing protection and marginal benefit; ordinary guards need no separate justification record. Do not add a general recovery framework merely to make a lifecycle look complete.

## Dependencies and performance

- Start with a suitable platform or existing capability and stop when it meets the need at reasonable cost. Consider local or external alternatives when a material gap remains; use mature implementations where a local substitute would create a hidden subsystem.
- Treat features, graph, build/runtime cost, native code, license, advisories, portability, migration, and removal as dependency cost.
- Establish an idiomatic baseline and representative workload before advanced performance mechanisms.
- Record hardware, build profile, workload, variance, and correctness guard only when making a performance claim.

## Testing, documentation, and observability

- Select black-box, white-box, property, differential, exploratory, or adversarial views only where they add distinct failure sensitivity.
- Test behavior, contracts, risks, states, failures, limits, cancellation, and compatibility rather than implementation trivia or a coverage target.
- Challenge high-risk or easy-to-fake oracles with a practical negative control.
- Add comments where they preserve why, invariants, safety/privacy, compatibility, ownership/lifecycle, non-obvious trade-offs, workaround removal, or public limits.
- Avoid comments that narrate obvious code, preserve dead code, hide a poor abstraction, or leave an unowned deferred marker.
- Document maintained public contracts, operational limits, migration/rollback, and unsafe/FFI safety contracts.
- Emit actionable telemetry without secrets or unbounded-cardinality labels.

## Security, unsafe, and FFI

- Never invent cryptographic primitives or protocols.
- Isolate unsafe code and document its adjacent safety contract.
- For a changed FFI contract, inspect both sides and the affected representation, ownership, error, threading, or ABI responsibilities. Follow generated bindings, packaging, and platform consumers when that contract change can affect them.
- Keep representation, ownership/callback lifetime, and compatibility evolution as separate decisions.
- Ensure callback producers have stopped and in-flight callbacks are quiescent before releasing foreign state; prevent callbacks from using released or replaced state.
- Keep simulator/emulator evidence separate from physical-device loading, lifecycle, packaging, and architecture evidence.
- Never log secrets, credentials, personal data, or full sensitive payloads.
