# Language-native guidance

Load only the sections matching affected artifacts and their real boundary roles. These are corrections and routing hints, not complete language manuals or dependency approval.

## Rust

- Prefer ownership/borrowing, enums, newtypes, traits for real capabilities, inherent `impl`, generics, exhaustive matching, and typed errors.
- Prefer static dispatch; use `dyn Trait` for genuine runtime heterogeneity, plugin boundaries, or object-safe extension.
- Keep portable domain logic independent of Tokio, Axum, database, FFI, and UI unless the actual product boundary requires coupling.
- A repository trait is justified by a real persistence port, multiple implementations, or valuable test seam—not a Java convention.
- Do not manufacture DTO/VO/Service/Manager/Base/Abstract layers. Request/response/row/event/FFI records are valid real boundaries and should be named for that role.
- Avoid `async-trait` when native async traits and static dispatch suffice. Do not hold unsuitable locks across suspension.
- Personal choices such as Jiff, hashbrown, cache libraries, GPUI, or framework versions belong in an applicable profile and still require dependency approval.
- Unsafe, FFI, SIMD, lock-free, zero-copy, and allocator work requires measured need and specialist/qualified review.

## TypeScript and React

- Prefer functional composition, discriminated unions, narrow interfaces, explicit external schemas, and semantic HTML.
- Derive state rather than duplicating it. Keep local state at the narrowest owner and server state in the selected repository-native data layer.
- Avoid Java-style class/service/repository ceremony; use focused functions, modules, hooks, components, and adapters.
- Validate untrusted external input at boundaries without wrapping every internal object in runtime schema ceremony.
- Model loading, empty, error, permission, offline, and recovery explicitly. Preserve keyboard, focus, accessible names, and reduced-motion behavior.
- Do not speculate with memoization, global state, or abstraction; profile renders and bundle cost first.
- Package manager, React/Vite/Next versions, router/query/table/chart libraries, and schema libraries are project/profile/dependency decisions, not neutral defaults.

## Swift and Apple

- Use value types, protocols, structured concurrency, actor isolation, and platform lifecycle.
- Keep SwiftUI/AppKit/UIKit, permissions, entitlements, extensions, packaging, and background execution in the Apple layer.
- Do not use blanket `@MainActor`, `@unchecked Sendable`, or `Task.detached` to silence compiler warnings.
- Move portable state/protocol/data processing to a shared core only when ownership and FFI cost remain clear.

## Kotlin and Android

- Use null safety, sealed types, coroutines, structured concurrency, and Android lifecycle primitives.
- Keep Activity, Service, WorkManager, Binder, permissions, UI lifecycle, and packaging in the Android layer.
- Do not let JNI references, platform objects, or process-local handles escape their valid boundary.

## Shell, configuration, SQL, and generated code

- Follow repository-native formatter, linter, schema, and migration conventions.
- Keep shell strict, quoted, bounded, portable where required, and non-destructive; move complex control flow to a testable language.
- Use explicit reviewable migrations and parameterized SQL.
- Prefer ordinary code over macros/generation until schema authority, compile-time validation, cross-language contracts, or stable repetition justify it.
- Separate generated from handwritten code and verify deterministic regeneration.
