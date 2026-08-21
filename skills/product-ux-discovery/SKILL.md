---
name: product-ux-discovery
description: Define product intent, information architecture, flows, states, accessibility, and design truth for material user-facing work.
---

# Product and UX Discovery

Use this Skill when a user-facing change alters a workflow, information architecture, or product behavior. Small visual fixes normally stay on the direct path.

This Skill may operate alone for bounded product discovery. If the result drives material repository mutation, cross-boundary implementation, managed continuity, or high-risk delivery, load `dev-flow` as the coordinating kernel when it is available and not already active; keep this Skill as the product/UX owner.

## Procedure

1. Classify UI impact as none, preserve, or material.
2. Inspect current source and rendered behavior when available, including navigation, state ownership, design system, assets, and freshest product truth.
3. Identify users, jobs, domain distinctions, primary flows, IA/navigation, and protected behavior.
4. Cover applicable loading, empty, error, offline, permission, destructive confirmation, success, undo, and recovery states.
5. Resolve design truth in this order: explicit direction, accepted design, shipped behavior, canonical components/tokens, maintained product documentation.
6. Use the least fidelity that resolves uncertainty: prose, flow/table, wireframe, or rendered prototype.
7. Define accessibility and responsive intent across semantics, keyboard/focus, names/status, contrast, scaling, motion, input modes, and relevant viewports/devices.
8. For managed work, keep durable product decisions in the repository design document; keep screenshots and raw test output as runtime evidence.

Read `references/product-ux-contract.md` for complex state, accessibility, or design-truth conflicts.

## Boundaries

- Do not invent product semantics from a component library or screenshot.
- Do not require a prototype, UX-ready artifact, or fixed schema for every UI change.
- Automated accessibility output is not complete accessibility evidence.
