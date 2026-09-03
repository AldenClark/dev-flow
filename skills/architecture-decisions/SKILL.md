---
name: architecture-decisions
description: Choose minimal, falsifiable boundary and lifecycle designs; exclude routine local implementation.
---

# Architecture Decisions

Choose the smallest coherent design that satisfies the product outcome and existing repository contracts. Use it when a technical choice affects a boundary, ownership, state/lifecycle, compatibility, recovery, or a lasting abstraction—not for an already-owned local implementation.

This Skill may operate alone for a bounded design decision. If the decision drives material repository mutation, cross-boundary implementation, managed continuity, or high-risk delivery, load `dev-flow` as the coordinating kernel when it is available and not already active; keep this Skill as the architecture owner.

Public-contract or data-lifecycle design spanning compatibility, rollout, recovery, privacy, or deletion is cross-boundary even when it is read-only. Load `dev-flow` before technical design in that case.

## Decide from the boundary outward

1. Start with the observable outcome, consumers, current call/data path, and the smallest boundary that owns the decision. Establish relevant language/platform constraints before importing a pattern.
2. Model only the states and transitions that matter: valid values and invalid inputs, ownership and handoff, failure classification, cancellation/shutdown, recovery, and compatibility direction. Make an internal trusted type at an untrusted boundary when it eliminates repeated ambiguous validation.
3. Compare the existing convention, a smaller/local option, and any credible alternative. State what each cannot satisfy, the chosen minimum, and evidence that could disprove the choice (a spike, contract test, measurement, consumer check, or failure scenario).
4. Add an abstraction only for a demonstrated stable concept, variation, ownership boundary, public extension, or useful test seam. When a proposed abstraction's value is unclear, use AHA or a design ablation: keep clear local code or remove/bypass one component and compare required behavior, complexity, and failure surface. They are diagnostic simplification tools, never mandatory coding steps.
5. Make independently failing concerns explicit where they apply: error propagation and user/operational context; resource acquisition, bounds, cancellation, drain, cleanup, and recovery; concurrency ordering and overload; compatibility, migration, and rollback. Keep FFI representation, ownership/callback lifetime, and evolution separate.
6. Leave the decision in code/tests or update the existing design owner when future readers need the rationale. A durable ADR is for consequential, cross-owner, public, persistent, or costly-to-reverse choices—not routine local design.

Read [neutral engineering policy](references/neutral-engineering-policy.md) for implementation-quality defaults, and the relevant section of [language-native guidance](references/language-native-guidance.md) for language or platform constraints. Revisit a decision when its stated assumption, consumer set, workload, failure mode, or rollback cost changes; do not retain an abstraction merely because it already exists.

## Boundaries

- Return user-visible semantic choices to requirements/design.
- Route selection of an external dependency to `dependency-decisions`.
- Specialist guidance is scoped evidence, not authority over repository facts.
- Do not require a versioned architecture artifact for routine local design choices.
