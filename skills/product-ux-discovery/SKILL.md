---
name: product-ux-discovery
description: Establish product intent, IA, flows, states, accessibility, design truth, and UX readiness for new or materially changed user-facing experiences.
---

# Product and UX Discovery

For product questions or UX Ready, remain in Default mode and follow `../requirements-design/references/user-interaction.md`; use native structured input only for faithful bounded choices.

Establish what the interface must preserve or change before implementation details anchor the result.

## Procedure

1. Classify UI impact as `none`, `preserve`, or `material`.
2. Identify users, jobs, product position, domain distinctions, primary flows, information architecture, navigation, and protected behavior.
3. Inventory loading, empty, error, offline, permission, destructive confirmation, success, undo, and recovery states.
4. Resolve design truth in this order: explicit user direction, approved design source, shipped behavior, canonical components/tokens, then maintained product documentation.
5. Select the smallest useful fidelity: prose for simple behavior, flow/table for relationships, wireframe for layout, rendered prototype only when interaction or visual uncertainty warrants it.
6. Define accessibility across semantic structure, keyboard/focus, accessible names, contrast, scaling, motion, input mode, and assistive-technology/manual evidence.
7. Preserve product IA and typed domain workspaces during refreshes; share infrastructure without collapsing distinct domains into generic CRUD.
8. Record UX Ready only for a concrete, current product/UX contract.

Read `references/product-ux-contract.md` for state, design-truth, fidelity, accessibility, and approval details.

## Output contract

Produce `product_ux.contract.v1` with impact class, users/outcomes, IA/flow/state contract, protected behavior, design truth, accessibility requirements, open material questions, evidence, and UX Ready status.

## Boundaries

- Do not invent product semantics from a component library or screenshot.
- Do not require a prototype for every UI task.
- Do not report automated accessibility output as complete accessibility evidence.
