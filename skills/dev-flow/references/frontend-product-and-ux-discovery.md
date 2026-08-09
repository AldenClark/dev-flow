# Frontend product and UX discovery

Apply this contract to user-facing web, native desktop, Apple, and Android work. Scale it by visible product impact, not by framework or diff size.

## Classify UI impact

- `none`: no user-visible behavior, layout, content, navigation, or interaction changes. Do not add a UX gate.
- `preserve`: extend or repair an established surface while preserving its product position, features, information architecture, page relationships, interaction flows, design system, and visual language. Infer from current evidence and confirm only material conflicts.
- `material`: create or substantially redesign a screen, workflow, navigation model, information architecture, visual system, brand expression, or high-risk interaction. Require product/UX discovery and a recorded UX Ready approval before production implementation.

Escalate `preserve` to `material` when discovery changes a protected flow, introduces a new user journey, lacks a reliable current design truth, or exposes multiple viable directions with meaningful product tradeoffs.

## Establish the design truth

Use evidence in this order:

1. User-provided Figma files, specifications, screenshots, brand assets, references, and explicit constraints.
2. Current shipped/runtime UI and current source, including narrow and failure states.
3. Repository design systems, tokens, components, content rules, accessibility policy, and tracked design documents.
4. Nearby product surfaces and validated platform patterns.
5. Comparable products or agent-proposed directions, clearly labeled as references or proposals rather than project truth.

When sources disagree, identify which is freshest and authoritative. Do not let an older design document overwrite current product behavior without a deliberate migration decision.

## Capture the product and UX contract

For `preserve` and `material` work, record what is applicable:

- target users, context, primary task, success outcome, and current pain point;
- immutable product positioning, features, information architecture, navigation, page relationships, and flows;
- provided design assets and missing inputs;
- platform, input modes, viewport/window/device range, localization, content density, and data scale;
- visual direction, brand constraints, typography, color, spacing, iconography, and motion;
- primary, alternate, empty, loading, partial, error, permission, offline, destructive, recovery, and completion states;
- keyboard, focus, accessible names, contrast, text zoom, reduced motion, screen reader, and touch-target obligations;
- analytics or success signals when the product decision depends on observed use;
- required fidelity: written brief, state map, sketch, wireframe, interactive prototype, visual specification, or production-ready design.

Do not make the user invent design vocabulary. Present a repository-backed recommended direction and only the alternatives whose tradeoffs matter. Ask whether design assets exist; if not, offer to derive an appropriate artifact.

## Choose design work by uncertainty

- Use a concise written/state contract for established, low-novelty `preserve` work.
- Use sketches or wireframes for layout, hierarchy, navigation, and flow uncertainty.
- Use interactive prototypes for novel, multi-step, high-risk, or hard-to-explain interactions.
- Use high-fidelity design when brand, visual comparison, stakeholder approval, or implementation fidelity requires it.
- Keep prototypes explicitly throwaway unless separately reviewed and approved as production code.

Figma and prototypes are tools, not universal gates. Do not delay a bounded non-visual or clearly established UI fix to create decorative artifacts.

## UX Ready gate

Material UI work is UX Ready only when:

- the user/problem/outcome and protected product constraints are explicit;
- the authoritative design sources and unresolved conflicts are known;
- the selected direction, important alternatives, and rationale are recorded;
- the screen/flow/state/accessibility contract is implementation-ready;
- required design or prototype evidence exists at the agreed fidelity;
- the user has approved the material direction and scope;
- implementation tasks and verification obligations trace back to the UX contract.

During implementation, pause when code would change an approved product constraint or design direction. After implementation, verify the rendered product in representative states and environments; static source inspection alone does not prove visual or interaction fidelity.
