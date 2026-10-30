---
name: product-ux-discovery
description: Use when a user task, UI state, recovery flow, or design truth is unclear; not for a small visual fix with preserved behavior.
---

# Product and UX Discovery

Use this Skill when a user goal, changed workflow, or design choice is unclear enough to affect implementation. An understood change can use the established flow and components directly.

This Skill may operate alone for bounded product discovery. If the result drives material repository mutation, cross-boundary implementation, managed continuity, or high-risk delivery, load `dev-flow` as the coordinating kernel when it is available and not already active; keep this Skill as the product/UX owner.

## First action

Identify the user's goal and the changed part of the current flow from the nearest product evidence. If a material product choice is apparent, ask it through an eligible native surface before investigating every state or technical branch. Walk the affected path only far enough to understand the result and any consequential exception.

## Procedure

1. Classify UI impact as none, preserve, or material.
2. Inspect the current source or rendered behavior needed to resolve the uncertainty; reuse established navigation and component behavior.
3. Explain the user goal, changed interaction, and behavior to preserve.
4. Resolve states or exceptions that the change introduces or affects, including permission or destructive-action consequences. Make the user's next action clear where the changed flow leaves it uncertain; retain established failure and recovery behavior elsewhere.
5. Resolve design truth in this order: explicit direction, accepted design, shipped behavior, canonical components/tokens, maintained product documentation.
6. Use the least fidelity that resolves uncertainty: prose, flow/table, wireframe, or rendered prototype.
7. Preserve accessibility and responsive behavior through native components and existing conventions; resolve specific consequences of the changed interaction, layout, or supported device.
8. When future work needs a durable UX decision and repository mutation is in scope, update the existing design/product owner. Otherwise, report any material owner update in chat. Keep screenshots and raw test output as runtime evidence. Use `repository-knowledge` when a missing or conflicting owner blocks continuation.

Read `references/product-ux-contract.md` for complex state, accessibility, or design-truth conflicts.

## Quality, handoff, and stopping

Return enough understanding to implement the changed interaction while preserving its affected contract, with any unresolved product decision stated. Use the least-fidelity explanation or artifact that resolves the uncertainty.

Stop when the real task and its material exceptions are understandable enough to implement and verify. Return open product meaning to `requirements-design`, technical boundaries to their owner, and contradicting or missing durable truth to `repository-knowledge`. Do not create a UX artifact, introduce new visual preferences, or extend accessibility analysis beyond the affected promise merely to make the work look complete.

## Boundaries

- Do not invent product semantics from a component library or screenshot.
- Do not require a prototype, UX-ready artifact, or fixed schema for every UI change.
- Do not mutate design or product documentation during a read-only or design-only request unless repository mutation is explicitly included.
- Automated accessibility output is not complete accessibility evidence.
