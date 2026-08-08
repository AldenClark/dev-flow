# Specialist Skill routing

This file routes to installed third-party or specialized Skills. It does not duplicate their full standards. Load only the routes relevant to the task.

Specialist guidance is advisory when it presents optional dependencies or architecture. The current user decision, observed contract, approved scope, engineering constitution, and dependency gate remain authoritative.

## Core routes

| Work | Required or preferred Skills |
|---|---|
| Rust writing/refactoring | `rust-best-practices`; add `rust-project-setup` for new projects/workspaces |
| Rust review | `rust-code-review` and mandatory `review-verification-protocol` |
| Broad Rust review | `review-rust`, which fans out to detected specialist reviewers |
| Tokio/async | `rust-async-patterns`; review with `tokio-async-code-review` |
| Axum | `axum-code-review` |
| SQLx/Postgres | `sqlx-code-review`; add `build-web-apps:supabase-postgres-best-practices` only for relevant Postgres work |
| Serde | `serde-code-review` |
| Rust macros | `macros-code-review` |
| Rust tests | `rust-testing-code-review` |
| Rust to Swift/Apple FFI | `rust-swift-ffi`, `ffi-code-review`, plus applicable Apple Skills |
| Rust to Kotlin/Android FFI | `rust-kotlin-ffi` and `ffi-code-review` |
| React/Next.js | `build-web-apps:react-best-practices` |
| Rendered frontend testing/debugging | `build-web-apps:frontend-testing-debugging` |
| Swift concurrency | `swift-concurrency` |
| SwiftUI | `swiftui-expert-skill` or the applicable bundled iOS/macOS Skill |
| Swift tests | `swift-testing-expert` |

## Routing procedure

1. Inspect the repository and detected technology before selecting a route.
2. Read every selected `SKILL.md` completely and load only its references that match the code under review.
3. Apply the project's edition, compiler, framework, and platform version before using version-sensitive advice.
4. Reject findings that are merely stylistic when the repository deliberately uses another valid convention and migration is out of scope.
5. Send every proposed new dependency through `dependency-governance.md`, even if the specialist Skill calls it a default.
6. For reviews, verify each finding with `review-verification-protocol`; never relay a specialist review report uncritically.

## Known coverage gaps

- The installed React Skill focuses on React/Next.js performance, not a complete general TypeScript language standard.
- The installed Kotlin coverage is strong at Rust/Android FFI and Material UI boundaries, not general Kotlin architecture.
- General Swift coverage is strongest in concurrency, SwiftUI, tests, and platform-specific Skills rather than one universal Swift style Skill.

When a task needs a missing standard, report the gap. Search for maintained third-party Skill candidates and compare them, but do not install one without explicit user approval. Until approval, use the repository formatter/linter/compiler and current official language documentation as the correctness baseline.
