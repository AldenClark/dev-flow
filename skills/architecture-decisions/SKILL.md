---
name: architecture-decisions
description: Make repository-grounded architecture decisions for material types, boundaries, ownership, concurrency, state, FFI, or performance tradeoffs.
---

# Architecture Decisions

If architecture evidence exposes a user-owned semantic choice, return it to the root in Default mode and follow `../requirements-design/references/user-interaction.md`.

Choose the smallest coherent architecture that satisfies the approved requirement and repository contracts.

## Responsibility contract

- Consumes: repository context, approved requirement constraints, applicable diagnosis, resolved preferences, and already-admitted specialist evidence.
- Owns: structural alternatives and decisions for types, boundaries, ownership, state, concurrency, lifecycle, compatibility mechanics, and performance.
- Stops: at a context gap, unresolved user semantics, named dependency selection, or an unmeasured performance premise.
- Hands off: external capability choices to dependency decisions, proof obligations to verification, and the chosen design to the control plane.

## Procedure

1. Consume current context, approved requirements/design constraints, and the effective preference snapshot.
2. Identify language, artifact role, framework/version, boundary, ownership, call path, and brownfield constraints before applying guidance.
3. Read `references/neutral-engineering-policy.md` for portable principles.
4. Read only the applicable language sections in `references/language-native-guidance.md`.
5. For cross-ecosystem work, consume the smallest repo-context-admitted specialist evidence per affected consumer plus an independent boundary-review route. Missing or inapplicable evidence is a named context gap, never a waiver; route selection is not review execution.
6. Compare at least the viable existing-convention, smaller/local, and more abstract alternatives. State the demonstrated variation axis or ownership seam that justifies an abstraction.
7. Design invalid states out where practical; validate external input once at the boundary and move typed values inward.
8. Make errors, cancellation, resource ownership, shutdown, cleanup, compatibility, observability, and unsafe/FFI contracts explicit.
9. Preserve every independently falsifiable boundary and lifecycle invariant as a separate decision or named limitation; umbrella safety labels never replace independently failing axes. Detailed FFI policy remains in `references/neutral-engineering-policy.md` and applicable language guidance.
10. Separate ABI versioning from compatibility migration/rollback/removal.
For FFI, keep representation, callback lifecycle, and compatibility evolution separate.
11. Require measurement before advanced performance mechanisms and preserve a portable fallback when applicable.
12. Record separate `architecture.decision.v1` items when choices, protected behaviors, or recheck triggers can change independently; each item includes evidence, applicability, tradeoffs, exceptions, consequences, tests, and recheck triggers.

## Language isolation rule

Do not transplant one ecosystem's ceremony into another. A Rust request/response/database row/event/FFI record is legitimate when it represents a real boundary and is named for that role; a `DTO` suffix alone is neither required nor automatically wrong. Inspect semantics and call path before reporting any architectural finding.

## Boundaries

- Do not add or select an external dependency; route that decision to `dependency-decisions`.
- Do not rewrite unrelated sound conventions.
- Treat specialist Skill advice as scoped evidence, not authority over the approved design or repository facts.
