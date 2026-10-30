---
name: architecture-decisions
description: Choose minimal, falsifiable boundary and lifecycle designs; exclude routine local implementation.
---

# Architecture Decisions

Choose the smallest coherent design that satisfies the product outcome and existing repository contracts. Use it when a technical choice affects a boundary, ownership, state/lifecycle, compatibility, recovery, or a lasting abstraction—not for an already-owned local implementation.

This Skill may operate alone for a bounded design decision. If the decision drives material repository mutation, cross-boundary implementation, managed continuity, or high-risk delivery, load `dev-flow` as the coordinating kernel when it is available and not already active; keep this Skill as the architecture owner.

Public-contract or data-lifecycle design spanning compatibility, rollout, recovery, privacy, or deletion is cross-boundary even when it is read-only. Load `dev-flow` before technical design in that case.

## Decide from the boundary outward

1. Start with the observable outcome and the current boundary or call/data path that owns it. Separate user goals and hard constraints from candidate mechanisms. Use an existing suitable solution directly; investigate only facts that could change the choice, including relevant language or platform limits. Return a clear product choice promptly rather than first designing all technical branches.
2. Describe states, ownership, and transitions only where the change depends on them. Validate untrusted input at its boundary; introduce an internal trusted type when it removes repeated ambiguous validation.
3. Compare alternatives only when there is a material trade-off in behavior, cost, compatibility, or reversibility. Judge necessary guarantees and candidate mechanisms by benefit versus state, coordination, recovery, and maintenance cost, even when a user has accepted a proposal. Recommend the sufficient simpler option where stronger guarantees add little value; ask before changing accepted business guarantees. Within authorized work, merge or remove redundant mechanisms after checking their consumers and preserved responsibilities; an unsuccessful search alone does not prove absence. Bring incidental defects forward only when they block the primary objective.
4. Add an abstraction only for a demonstrated stable concept, variation, ownership boundary, public extension, or useful test seam. When a proposed abstraction's value is unclear, use AHA or a design ablation: keep clear local code or remove/bypass one component and compare required behavior, complexity, and failure surface. They are diagnostic simplification tools, never mandatory coding steps.
5. Design resource cleanup, cancellation, concurrency, or recovery mechanisms for responsibilities the changed path actually owns. Account for affected public compatibility or persistent-data migration when the change reaches those boundaries. Keep FFI representation, ownership/callback lifetime, and evolution separate where they change independently.
6. Before an important new feature's first implementation, give `requirements-design` and the kernel the major technical trade-offs needed to confirm the overall result and scope. Explain implementation details only when they change a user-visible decision; reuse confirmation for unchanged scope.
7. Leave the decision in code/tests or update the existing design owner when future readers need the rationale. Record the consequential choice and why it is sufficient. A durable ADR is for consequential, cross-owner, public, persistent, or costly-to-reverse choices—not routine local design.

Read [neutral engineering policy](references/neutral-engineering-policy.md) for implementation-quality defaults, and the relevant section of [language-native guidance](references/language-native-guidance.md) for language or platform constraints. Revisit a decision when its stated assumption, consumer set, workload, failure mode, or rollback cost changes; do not retain an abstraction merely because it already exists.

After a semantic correction, replace the affected design premise and identify dependent code/data, tests, and delegated work under `dev-flow/references/core-lifecycle.md`. Independent authorized feasibility learning may continue while a user choice is pending; it cannot commit the product to that branch.

## Boundaries

- Return user-visible semantic choices to requirements/design.
- Route selection of an external dependency to `dependency-decisions`.
- Specialist guidance is scoped evidence, not authority over repository facts.
- Do not require a versioned architecture artifact for routine local design choices.
