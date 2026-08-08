# Engineering constitution

Apply these principles to every technical choice. They express preferences among correct options; they do not override observed contracts, safety, or explicit user instructions.

## 1. Repository and evidence first

- Inspect the real repository root, manifests, toolchain, nearby implementations, tests, and runtime contracts before proposing architecture.
- Distinguish code facts, inference, preference, and recommendation.
- Preserve existing conventions when they are sound and changing them is outside the approved scope.

## 2. Native idioms over transplanted architecture

- Write each language in its native style. Do not reproduce patterns merely because they are familiar from another ecosystem.
- Prefer domain names and language-native abstractions over generic enterprise suffixes.
- Use strong types and explicit state transitions so invalid states are difficult to express.
- Keep platform adapters thin and let the portable core own portable business rules.

## 3. Simplicity and abstraction threshold

- Solve the demonstrated requirement, not speculative future variants.
- Prefer a small amount of clear duplication over an unstable abstraction.
- Introduce an abstraction when a stable concept, real variation axis, ownership boundary, test seam, or repeated behavior justifies it.
- Prefer small cohesive modules. Avoid `Helper`, `Utils`, `Base`, `Abstract`, and `Manager` without a precise domain meaning.
- Produce the smallest coherent change, not merely the fewest changed lines.

## 4. Dependency thrift

- Prefer the standard library, then an already-approved dependency, then a small local implementation, and only then a new dependency.
- Prefer lightweight, focused, actively maintained, high-performance dependencies with a narrow enabled feature set.
- Treat compile time, binary/bundle size, transitive graph, platform support, security, licensing, migration, and operational cost as part of the API.
- Follow `dependency-governance.md` before introducing or expanding dependencies.

## 5. Type and API design

- Use newtypes, enums, discriminated unions, explicit capabilities, and constructors that validate invariants.
- Validate external input once at the boundary and move typed values inward.
- Name boundary models by role and protocol, not with generic `DTO` or `VO` suffixes.
- Keep public API surface small. Expose behavior and stable contracts, not incidental storage layout.
- Version persistent and wire formats explicitly when compatibility matters.

## 6. Error and failure design

- Use typed, matchable errors at library and domain boundaries; add operational context at application boundaries.
- Do not branch on error strings.
- Reserve panic for programmer errors or proven invariants; represent external, configuration, storage, and user failures explicitly.
- Map internal errors to stable, non-sensitive external error codes.

## 7. Concurrency and resource ownership

- Prefer structured concurrency, explicit owners, cancellation, join paths, deadlines, bounded queues, and named overload policies.
- Do not detach work without an owner and completion or cancellation policy.
- Do not hold locks across suspension points unless the primitive and design explicitly require it.
- Make resource acquisition, handoff, shutdown, drain, and cleanup observable and testable.

## 8. Performance by measurement

- Establish an idiomatic, clear baseline before advanced optimization.
- Require representative profiling or benchmarks before adding SIMD, unsafe fast paths, lock-free structures, custom allocators, GPU offload, zero-copy formats, or complex caches.
- Preserve a scalar or portable fallback when platform coverage requires it.
- State workload, data distribution, hardware, build profile, and regression threshold for performance claims.

## 9. Testing and verification

- Test observable behavior and risk, not implementation trivia or a global coverage number.
- For bug fixes, reproduce the failure and prove the regression test can fail without the fix when practical.
- Use property, fuzz, model, sanitizer, or concurrency testing where the state space or invariant warrants it.
- Prefer controlled fakes over mock-heavy interaction tests when they better represent the contract.
- Never claim completion from a subagent report, stale run, partial command, or passing linter alone.

## 10. Documentation and observability

- Comments explain why, invariants, safety, compatibility, or non-obvious tradeoffs; they do not narrate syntax.
- Document public contracts, migration and rollback paths, operational limits, and unsafe/FFI invariants.
- Emit structured, actionable telemetry without secrets or unbounded-cardinality labels.

## 11. Security, unsafe, and FFI

- Never invent cryptographic primitives or protocols.
- Isolate unsafe code and document the safety contract adjacent to the unsafe boundary.
- Review both sides of an FFI boundary, including ownership, threading, cancellation, callback quiescence, ABI evolution, packaging, and platform lifecycle.
- Do not log secrets, tokens, personal data, full sensitive payloads, or credentials.

## 12. Change discipline

- Do not perform opportunistic refactoring outside the approved change scope.
- Remove dead code created by the in-scope change; do not add compatibility shims without an identified consumer and removal plan.
- Preserve rollback and migration safety for data, protocols, packaging, deployment, and public API changes.
- Treat commit, push, PR, release, and external writes as separate delivery authorities.
