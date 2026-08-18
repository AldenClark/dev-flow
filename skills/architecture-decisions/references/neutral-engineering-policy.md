# Neutral engineering policy

These are portable preferences among correct options. They do not override explicit user authority, safety or law, observed repository/runtime contracts, or valid existing conventions.

## Evidence and change discipline

- Inspect the actual root, manifests, toolchain, nearby implementation, tests, runtime, and call path before deciding.
- Separate observed fact, inference, recommendation, and unavailable evidence.
- Make the smallest coherent change and avoid opportunistic refactors.
- Remove dead code created by the change; add compatibility layers only for an identified consumer and removal condition.

## Coherent slices

- Re-read current product intent, design decisions, affected surface, and worktree before a meaningful implementation slice.
- Keep related production code, focused tests, maintained documentation, and comments aligned when they express one behavior.
- Run the narrow oracle early, then the affected module suite and a representative integration path when relevant.
- Before calling a slice complete, inspect the final diff, user-owned changes, generated/dependency metadata, secrets, tests and oracle validity, comments/docs, and affected native checks.
- Completion evidence never authorizes stage, commit, push, PR, release, or deployment.

## Native idiom and abstraction

- Select by language, framework/version, artifact role, boundary, ownership, and call path.
- Prefer domain and protocol names over generic enterprise suffixes; names alone are never violations.
- Prefer clear local duplication over an unstable abstraction.
- Introduce an abstraction for a stable concept, real variation axis, ownership boundary, public extension, valuable test boundary, or repeated behavior.

## Types, failures, and resources

- Use strong types, explicit capabilities, validated constructors, and exhaustive state handling where they reduce invalid states.
- Validate untrusted input at the boundary and move typed values inward.
- Use typed/matchable errors at library/domain boundaries and add operational context at application boundaries.
- Prefer structured concurrency, explicit resource owners, cancellation and join paths, deadlines, bounded queues, and named overload behavior.
- Make acquisition, handoff, shutdown, drain, callback quiescence, and cleanup observable when the system owns such resources.

## Dependencies and performance

- Prefer platform/standard library, an existing capability, a bounded local implementation, then an external dependency.
- Treat features, graph, build/runtime cost, native code, license, advisories, portability, migration, and removal as dependency cost.
- Establish an idiomatic baseline and representative workload before advanced performance mechanisms.
- Record hardware, build profile, workload, variance, and correctness guard only when making a performance claim.

## Testing, documentation, and observability

- Select black-box, white-box, property, differential, exploratory, or adversarial views only where they add distinct failure sensitivity.
- Test behavior, contracts, risks, states, failures, limits, cancellation, and compatibility rather than implementation trivia or a coverage target.
- Challenge high-risk or easy-to-fake oracles with a practical negative control.
- Add comments where they preserve why, invariants, safety/privacy, compatibility, ownership/lifecycle, non-obvious trade-offs, workaround removal, or public limits.
- Avoid comments that narrate obvious code, preserve dead code, hide a poor abstraction, or leave an unowned `TODO`.
- Document maintained public contracts, operational limits, migration/rollback, and unsafe/FFI safety contracts.
- Emit actionable telemetry without secrets or unbounded-cardinality labels.

## Security, unsafe, and FFI

- Never invent cryptographic primitives or protocols.
- Isolate unsafe code and document its adjacent safety contract.
- For FFI, inspect both sides: layout, ownership, errors, panic containment, threading, cancellation, callback teardown, ABI evolution, symbols, packaging, platform lifecycle, generated bindings, consumers, and supported versions.
- Keep representation, ownership/callback lifetime, and compatibility evolution as separate decisions.
- Do not detach callback producers across teardown; cancel, drain to a defined quiescence point, reject late generations, then release foreign state.
- Keep simulator/emulator evidence separate from physical-device loading, lifecycle, packaging, and architecture evidence.
- Never log secrets, credentials, personal data, or full sensitive payloads.
