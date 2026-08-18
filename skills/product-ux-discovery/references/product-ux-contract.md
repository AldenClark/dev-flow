# Product and UX contract

Use this reference when a user-facing change has complex state, accessibility, responsive behavior, or conflicting design truth.

## Impact

- `none`: no user-facing behavior or presentation.
- `preserve`: implementation or visual refinement should preserve product position, information architecture, navigation, flows, state semantics, terminology, and domain distinctions.
- `material`: product behavior, information architecture, flow, state model, permissions, destructive action, or accessibility contract changes.

Material impact requires a user decision only when current direction and repository evidence do not resolve the product choice. It does not require a named UX Ready artifact or approval revision.

## Discovery

Resolve primary users/jobs, success/failure outcomes, entry points, hierarchy, primary/recovery flows, loading/empty/error/offline/permission/success/undo/partial states, target platforms and inputs, localization/data density, privacy, and protected shipped behavior to the extent they affect this change.

Apply design truth in this order: explicit user direction, accepted design source, shipped behavior, canonical design system/components/tokens, maintained product documentation. Record material conflicts instead of averaging them.

## Fidelity and accessibility

Use the cheapest artifact that resolves uncertainty: prose/table, flow/state diagram, wireframe, or rendered prototype. Do not require a prototype for bounded preserve-mode work.

Cover applicable semantics/landmarks, keyboard order/focus, accessible names and announcements, contrast/non-color cues, text scaling, target sizes, reduced motion, input alternatives, platform conventions, and error/recovery. Automated checks support but do not replace rendered or human evidence.

## Durable output

For managed work, update the repository design with the durable product decision, complete state intent, important responsive/accessibility behavior, conflicts, and open questions. For direct work, code, tests, and the final report are usually sufficient. Keep screenshots, traces, and raw accessibility output as runtime evidence rather than copying them into business documents.
