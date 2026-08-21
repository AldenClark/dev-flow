---
name: architecture-decisions
description: Make repository-grounded architecture decisions for material boundaries, ownership, state, concurrency, FFI, compatibility, or performance trade-offs.
---

# Architecture Decisions

Choose the smallest coherent architecture that satisfies the product outcome and existing repository contracts.

This Skill may operate alone for a bounded design decision. If the decision drives material repository mutation, cross-boundary implementation, managed continuity, or high-risk delivery, load `dev-flow` as the coordinating kernel when it is available and not already active; keep this Skill as the architecture owner.

Public-contract or data-lifecycle design spanning compatibility, rollout, recovery, privacy, or deletion is cross-boundary even when it is read-only. Load `dev-flow` before technical design in that case.

## Procedure

1. Establish the active language/framework/version, artifact role, call path, boundary, ownership, and brownfield constraints.
2. Read `references/neutral-engineering-policy.md` and only the applicable sections of `references/language-native-guidance.md` when deeper guidance is needed.
3. Compare credible alternatives, normally including the existing convention and a smaller/local option. Add abstraction only for a demonstrated variation or ownership need.
4. Make external validation, errors, cancellation, resource ownership, shutdown, cleanup, compatibility, observability, and unsafe/FFI contracts explicit where applicable.
5. Keep independently failing boundaries separate. For FFI, representation, ownership/callback lifetime, and compatibility evolution are distinct decisions.
6. Require measurement before advanced performance mechanisms and preserve a simpler fallback when practical.
7. Record a concise ADR or managed-work decision only when the rationale will remain useful after implementation. Include context, choice, alternatives, consequences, and recheck trigger.

## Boundaries

- Return user-visible semantic choices to requirements/design.
- Route selection of an external dependency to `dependency-decisions`.
- Specialist guidance is scoped evidence, not authority over repository facts.
- Do not require a versioned architecture artifact for routine local design choices.
