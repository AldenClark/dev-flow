---
name: architecture-decisions
description: Make repository-grounded, language-native architecture decisions when types, boundaries, ownership, concurrency, state, FFI, performance, or other structural tradeoffs are material.
---

# Architecture Decisions

If architecture evidence exposes a user-owned semantic choice, return it to the root in Default mode and follow `../requirements-design/references/user-interaction.md`.

Choose the smallest coherent architecture that satisfies the approved requirement and repository contracts.

## Procedure

1. Consume current context, approved requirements/design constraints, and the effective preference snapshot.
2. Identify language, artifact role, framework/version, boundary, ownership, call path, and brownfield constraints before applying guidance.
3. Read `references/neutral-engineering-policy.md` for portable principles.
4. Read only the applicable language sections in `references/language-native-guidance.md`.
5. Compare at least the viable existing-convention, smaller/local, and more abstract alternatives. State the demonstrated variation axis or ownership seam that justifies an abstraction.
6. Design invalid states out where practical; validate external input once at the boundary and move typed values inward.
7. Make errors, cancellation, resource ownership, shutdown, cleanup, compatibility, observability, and unsafe/FFI contracts explicit.
8. Require measurement before advanced performance mechanisms and preserve a portable fallback when applicable.
9. Record one `architecture.decision.v1` with evidence, applicability, tradeoffs, exceptions, consequences, tests, and recheck triggers.

## Language isolation rule

Do not transplant one ecosystem's ceremony into another. A Rust request/response/database row/event/FFI record is legitimate when it represents a real boundary and is named for that role; a `DTO` suffix alone is neither required nor automatically wrong. Inspect semantics and call path before reporting any architectural finding.

## Boundaries

- Do not add or select an external dependency; route that decision to `dependency-decisions`.
- Do not rewrite unrelated sound conventions.
- Treat specialist Skill advice as scoped evidence, not authority over the approved design or repository facts.
