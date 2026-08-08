# Language idiom overrides

These are project-specific corrections and routing rules, not complete language style guides. Load the specialist Skills in `skill-routing.md` for full guidance.

## Rust

- Prefer newtypes, enums, traits, inherent `impl`, generics, ownership, borrowing, and exhaustive matching.
- Put type-owned behavior in inherent `impl`; introduce a trait for a real capability, interchangeable implementation, public extension point, or justified test seam.
- Prefer static dispatch. Use `dyn Trait` when runtime heterogeneity, plugin boundaries, or object-safe abstraction genuinely requires it.
- Do not reproduce Java-style DTO/VO/Manager/Service/Repository/Base/Abstract layers. A request, response, database row, event envelope, or FFI record is valid when it represents a real boundary and is named for that boundary.
- A repository trait is justified by a real persistence port, multiple implementations, or a valuable test boundary, not by convention alone.
- Keep the domain independent of Tokio, Axum, database drivers, FFI, and UI unless the product's actual boundary makes that impossible.
- Prefer `hashbrown::HashMap` for ordinary maps. Use a HashDoS-resistant map only at an identified adversarial-key boundary.
- Use Jiff for civil time, timestamps, time zones, and calendar arithmetic. Do not introduce Chrono; isolate third-party Chrono values in an adapter and convert immediately.
- Prefer `scc::HashCache` for the default lightweight in-memory cache. Use Moka only for richer eviction, async loading, or policy requirements.
- Do not add `async-trait` when native async trait support and static dispatch are sufficient.
- Unsafe, SIMD, lock-free, zero-copy, and allocator choices require measured need and specialist review.

## TypeScript and React

- For a new project, use the baseline Node.js 24 LTS, React 19.2, TypeScript 6.0, Vite 8.1, and pnpm 11 unless current primary-source verification or a project constraint requires a newly approved adjustment. Do not silently substitute an older compatibility baseline.
- Prefer functional components, composition, discriminated unions, narrow interfaces, and explicit external schemas.
- Derive state rather than duplicating it. Keep state at the narrowest owner; do not introduce a global store for local or server-owned state.
- Use TanStack Query for server state and TanStack Router/Table according to the engineering preferences. Specialist examples suggesting SWR or other packages do not override this decision.
- Validate untrusted external input at the boundary; do not wrap every internal object in runtime schemas.
- Avoid Java-style class/service/repository layers. Use small modules, functions, hooks, components, and domain-focused adapters.
- Prefer semantic HTML, keyboard operation, visible focus, accessible names, reduced-motion support, and testable loading/error/empty states.
- Avoid speculative memoization and abstraction; profile renders and bundle weight before optimization.
- All new frontend projects use pnpm with one authoritative lockfile.

## Swift and Apple adapters

- Use Swift's value types, protocols, structured concurrency, actor isolation, and platform lifecycle rather than simulating Rust or Java ownership patterns.
- Keep SwiftUI/AppKit/UIKit, entitlements, app extensions, background execution, and platform permissions in the Apple layer.
- Route portable protocol, state machine, and data processing logic to Rust when it improves sharing or performance without making the FFI boundary chatty.
- Do not use blanket `@MainActor`, `@unchecked Sendable`, or `Task.detached` as compiler-warning suppression.
- Apply `rust-swift-ffi`, `swift-concurrency`, and the relevant Apple UI/build Skills.

## Kotlin and Android adapters

- Use Kotlin null safety, sealed types, coroutines, structured concurrency, and Android lifecycle primitives.
- Keep Activity, Service, WorkManager, permissions, Binder, packaging, and UI lifecycle in Kotlin/Android.
- Prefer registered JNI for high-frequency Android paths and UniFFI or a versioned C ABI for suitable typed control surfaces, according to `rust-kotlin-ffi`.
- Do not let JNI references, platform objects, or process-local handles escape their valid boundary.

## Shell, configuration, SQL, and generated code

- Follow repository-native formatter, linter, schema, and migration conventions.
- Keep shell scripts strict, quoted, bounded, and non-destructive; use a higher-level implementation when shell control flow becomes complex.
- Prefer explicit, reviewable migrations and parameterized SQL. Route SQLx/Postgres work to the installed database Skills.
- Prefer normal code over macros or generation until repetition, schema authority, compile-time validation, or cross-language contracts justify generation.
- Separate generated code from handwritten code and verify regeneration is deterministic.
