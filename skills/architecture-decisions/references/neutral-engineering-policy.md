# Neutral engineering policy

These are portable preferences among correct options. They do not override explicit user authority, safety/law, approved requirements/design, observed repository/runtime contracts, or valid existing conventions.

## Evidence and change discipline

- Inspect the actual root, manifests, toolchain, nearby implementation, tests, runtime, and call path before deciding.
- Separate fact, inference, resolved preference, volatile ecosystem evidence, and recommendation.
- Make the smallest coherent change and avoid opportunistic refactors.
- Remove dead code created by the in-scope change; add compatibility layers only for an identified consumer and removal condition.

## Native idiom and abstraction

- Select by language, framework/version, artifact role, boundary, ownership, and call path.
- Prefer domain and protocol names over generic enterprise suffixes.
- A suffix or type name alone is never a violation; verify semantics and impact.
- Prefer a little clear duplication over an unstable abstraction.
- Introduce an abstraction for a stable concept, real variation axis, ownership boundary, public extension, valuable test seam, or repeated behavior.
- Avoid vague `Helper`, `Utils`, `Base`, `Abstract`, or `Manager` unless the name represents a precise domain responsibility.

## Types and APIs

- Use strong types, enums/discriminated unions, explicit capabilities, validated constructors, and exhaustive state handling.
- Validate untrusted input once at the boundary and move typed values inward.
- Name boundary records by role: request, response, event, row, wire message, or FFI record.
- Keep public surfaces small and version persistent/wire formats when compatibility matters.

## Failure and resources

- Use typed/matchable errors at library/domain boundaries and add operational context at application boundaries.
- Never branch on error strings or expose sensitive internals.
- Reserve panic/fatal failure for programmer error or proven invariant.
- Prefer structured concurrency, explicit task/resource owners, cancellation, join paths, deadlines, bounded queues, and named overload policy.
- Make acquisition, handoff, shutdown, drain, callback quiescence, and cleanup observable and testable.

## Dependencies and performance

- Prefer platform/standard library, existing approved capability, bounded local implementation, then approved external dependency.
- Treat graph, features, build/runtime cost, native code, license, advisories, portability, migration, and removal as API cost.
- Establish an idiomatic baseline and representative workload before SIMD, unsafe fast paths, lock-free structures, custom allocators, GPU, zero-copy formats, or complex caching.
- State hardware, build profile, data distribution, variance, and regression threshold; preserve portable fallback when applicable.

## Testing, documentation, and observability

- Test behavior, contracts, risks, state transitions, failures, limits, cancellation, and compatibility rather than implementation trivia or one coverage percentage.
- Use property/model/fuzz/sanitizer/concurrency methods when the invariant/state space warrants them.
- Comments explain why, invariants, safety, compatibility, or non-obvious tradeoffs.
- Document public contracts, operational limits, migration/rollback, and unsafe/FFI safety contracts.
- Emit structured actionable telemetry without secrets or unbounded-cardinality labels.

## Security, unsafe, and FFI

- Never invent cryptographic primitives or protocols.
- Isolate unsafe code and document its adjacent safety contract.
- Review both sides of FFI: layout, ownership, errors, panic containment, threading, cancellation, callback teardown, ABI evolution, symbols, packaging, and platform lifecycle.
- Before cross-language design, require and consume a repo-context-owned discovery record for exports, generated bindings, handwritten consumers, package artifacts, support ranges, deployed versions, and native loading paths; if absent, record a context gap. Reference that upstream claim without relabeling discovery as architecture evidence. Preserve mixed-version migration and rollback, allocator symmetry, leak evidence, and boundary-isolation tests.
- Never detach callback producers across teardown. Bind cancellation to an owner, join/drain in-flight work to a documented quiescence point, reject late generations, and only then release foreign state.
- For Apple/Android mobile FFI, keep Xcode Test Plan and xcresult evidence separate from Android API/ABI matrices and CheckJNI; keep simulator/emulator evidence separate from physical-device loading, lifecycle, packaging, and architecture gates.
- Never log secrets, credentials, personal data, or full sensitive payloads.
