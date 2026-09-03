---
name: product-ux-discovery
description: Use when a user task, UI state, recovery flow, or design truth is unclear; not for a small visual fix with preserved behavior.
---

# Product and UX Discovery

Use this Skill when a user-facing change alters a workflow, information architecture, or product behavior. Small visual fixes normally stay on the direct path.

This Skill may operate alone for bounded product discovery. If the result drives material repository mutation, cross-boundary implementation, managed continuity, or high-risk delivery, load `dev-flow` as the coordinating kernel when it is available and not already active; keep this Skill as the product/UX owner.

## First action

Walk one real user goal from its entry point to success or recovery using current behavior and plausible data. For example, a new upload flow is not understood until a user can find it, see progress, recover from a rejected file, and return without losing context. Do not begin with a component list, a visual style, or an ideal-state screenshot.

## Procedure

1. Classify UI impact as none, preserve, or material.
2. Inspect current source and rendered behavior when available, including navigation, state ownership, design system, assets, and freshest product truth.
3. Identify users, jobs, domain distinctions, primary flows, IA/navigation, and protected behavior.
4. Cover applicable loading, empty, error, offline, permission, destructive confirmation, success, undo, cancellation, retry, and recovery states. Make state transitions and the user's next available action explicit when they are not already obvious.
5. Resolve design truth in this order: explicit direction, accepted design, shipped behavior, canonical components/tokens, maintained product documentation.
6. Use the least fidelity that resolves uncertainty: prose, flow/table, wireframe, or rendered prototype.
7. Define accessibility and responsive intent across semantics, keyboard/focus, names/status, contrast, scaling, motion, input modes, and relevant viewports/devices.
8. When repository mutation is explicitly in scope, write durable user-flow, information, state, accessibility, and design-truth decisions back to the existing design/product owner. If mutation is not authorized, return the proposed owner and exact update in chat without editing the repository. Keep screenshots and raw test output as runtime evidence. If that owner or the next-reader path is missing, conflicting, or chat-only, hand the topology decision to `repository-knowledge` rather than creating a parallel design file.

Read `references/product-ux-contract.md` for complex state, accessibility, or design-truth conflicts.

## Quality, handoff, and stopping

Return a flow a later implementer can follow: user goal and entry, meaningful states and transitions, protected behavior, recovery, accessibility intent, canonical design truth, and unresolved product decisions. Use the least-fidelity artifact that resolves the uncertainty; a state table or real rendering can be stronger than a polished prototype.

Stop when the real task and its material exceptions are understandable enough to implement and verify. Return open product meaning to `requirements-design`, technical boundaries to their owner, and contradicting or missing durable truth to `repository-knowledge`. Do not create a UX artifact, introduce new visual preferences, or extend accessibility analysis beyond the affected promise merely to make the work look complete.

## Boundaries

- Do not invent product semantics from a component library or screenshot.
- Do not require a prototype, UX-ready artifact, or fixed schema for every UI change.
- Do not mutate design or product documentation during a read-only or design-only request unless repository mutation is explicitly included.
- Automated accessibility output is not complete accessibility evidence.
