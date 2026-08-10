# Product and UX contract

## Impact classification

- `none`: no user-facing behavior or presentation.
- `preserve`: implementation or visual refinement must preserve product position, IA, navigation, flows, states, terminology, and domain distinctions.
- `material`: product behavior, IA, flow, state model, permissions, destructive action, or accessibility contract changes and requires explicit UX Ready.

## Discovery questions

Resolve from evidence before asking:

- primary users, jobs, success and failure outcomes;
- product position and domain-specific distinctions;
- entry points, navigation, hierarchy, primary and recovery flows;
- loading, empty, error, offline, permission, destructive confirmation, success, undo, and partial states;
- target platforms, viewports, input modes, native conventions, localization, and data density;
- telemetry/consent and privacy boundaries;
- protected shipped behavior and explicitly approved changes.

## Design truth

Apply explicit user direction first, then approved design source, shipped product behavior, canonical design system/components/tokens, and maintained product documentation. Record conflicts instead of averaging them.

Screenshots and generic component-library examples are evidence, not automatic product authority. When product domains differ, share primitives and table/layout infrastructure while preserving typed workflows and information architecture.

## Fidelity

Use the cheapest artifact that resolves the uncertainty:

- prose or acceptance table for simple state/behavior;
- flow or state diagram for branching/sequence;
- wireframe for layout/hierarchy;
- rendered prototype for high-risk interaction, visual system, responsive behavior, or accessibility uncertainty.

Do not require interaction design for no-UI work or a prototype for a bounded preserve-mode change.

## Accessibility

Define semantic structure and landmarks, keyboard order and visible focus, accessible names/descriptions, screen-reader announcements, contrast and non-color cues, zoom/text scaling, target sizes, reduced motion, input alternatives, platform conventions, and error/recovery behavior.

Automated checks support but never replace human judgment. Name manual keyboard, screen-reader/assistive-technology, motion, scaling, and target-platform cells when they are material.

## Output

The versioned contract contains impact, users/outcomes, IA/navigation/flows, complete state model, design truth and conflicts, platform/input/responsive behavior, accessibility obligations, telemetry/privacy, protected behavior, open material questions, evidence, and UX Ready approval revision.
