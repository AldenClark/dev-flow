---
name: product-ux-discovery
description: Define product intent, IA, flows, states, accessibility, design truth, and UX readiness for material user-facing work.
---

# Product and UX Discovery

For product questions or UX Ready, remain in Default mode and follow `../requirements-design/references/user-interaction.md`; use native structured input only for faithful bounded choices.

Establish what the interface must preserve or change before implementation.

## Responsibility contract

- Consumes: repository/UI context and explicit product direction.
- Owns: IA, flows, states, accessibility intent, design truth, protected interface behavior, and UX Ready.
- Stops: at a material product choice, conflicting design truth, or insufficient current UI evidence.
- Hands off: material semantics to requirements, rendered/manual proof to verification, and UX Ready to the control plane.

## Procedure

1. Classify UI impact as `none`, `preserve`, or `material`.
2. Before returning a user-facing plan, explicitly inspect current source/rendered states, semantic/event/data/state ownership, routes/navigation, design system/assets, browser projects, and freshest product truth; if unavailable, make this the first `NOT RUN` action.
3. Identify users, jobs, domain distinctions, flows, IA/navigation, and protected behavior.
4. Inventory loading, empty, error, offline, permission, destructive confirmation, success, undo, and recovery states.
5. Resolve design truth: explicit direction > approved design > shipped behavior > canonical components/tokens > maintained product docs.
6. Use the least fidelity that resolves uncertainty: prose, flow/table, wireframe, or rendered prototype.
7. Define accessibility across semantic structure, keyboard/focus, accessible names, contrast, scaling, motion, input mode, and assistive-technology/manual evidence.
8. Verification names representative viewport, input, browser/platform, accessibility, and every recovery transition; missing rendered or physical cells remain `NOT RUN`.
9. Preserve product IA and typed domain workspaces during refreshes; share infrastructure without collapsing distinct domains into generic CRUD.
10. Before returning a material UI plan, confirm it covers relevant states plus semantics, keyboard/focus, names/status, confirmation, motion/scaling, responsive behavior, and rendered/manual evidence; mark inapplicable items with a reason.
11. Record UX Ready only for a concrete, current product/UX contract.

Read `references/product-ux-contract.md` for state, design-truth, fidelity, accessibility, and approval details.

## Output contract

Produce `product_ux.contract.v1` with impact class, users/outcomes, IA/flow/state contract, protected behavior, design truth, accessibility requirements, open material questions, evidence, and UX Ready status.

## Boundaries

- Do not invent product semantics from a component library or screenshot.
- Do not require a prototype for every UI task.
- Do not report automated accessibility output as complete accessibility evidence.
