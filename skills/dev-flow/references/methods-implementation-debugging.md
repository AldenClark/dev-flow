# Implementation and debugging methods

Implementation methods should reduce a named failure class. They are not team-identity labels.

## Implementation selector

| Need | Method | Critical stop |
|---|---|---|
| Fast behavior/design feedback | TDD | no failure-sensitive oracle |
| Shared actor-language acceptance | ATDD/BDD | brittle UI steps or ambiguous scenarios |
| Invalid value/state should be impossible | typestate/smart types | type complexity exceeds protected invariant |
| Independent versions must coexist | parallel change / expand-contract | no compatibility/rollback contract |
| Incremental replacement behind a seam | branch by abstraction/flag or strangler | unowned flag or ambiguous data ownership |
| Correctness-first high assurance | Cleanroom | unstable specification or missing proof/usage-profile capability |
| Design-fault tolerance | N-version programming | correlated specification/tool/conceptual faults dominate |
| Consequential dense code/spec | formal inspection/structured pairing | unfrozen scope or unprepared walkthrough |

## Coherent slice protocol

Freeze one acceptance outcome, its protected behavior, edit sites, affected consumers, black-box obligations, white-box obligations, docs/comments/generated surfaces, resources, and stop conditions. Run the narrow oracle early; then module/smoke checks; then audit final diff, scope, dependencies, secrets, user work, comments, and knowledge impact.

Do not use slice size, test count, or commit count as a quality metric.

## Compatibility change protocol

For parallel change/expand-contract:

1. Add a backward-compatible producer/consumer/schema path.
2. Migrate callers/data with both shapes working.
3. Observe old-path use and reconcile mixed versions.
4. Remove only with evidence, cleanup owner, and separate authority.

For feature flags, record owner, default, audience, telemetry, rollback behavior, combinations, expiry, removal gate, and tests for both states and transitions. A flag without cleanup is a permanent interaction dimension.

## Cleanroom and N-version cautions

Cleanroom combines precise box-structured specification, correctness verification/inspection, increments, and usage-distribution testing. Do not reduce it to “developers may not execute code.” Use it only when stable formalizable requirements and consequence justify the discipline.

N-version programming requires genuine diversity and explicit adjudication. Analyze common specification, data, toolchain, library, hardware, and conceptual failures. A majority vote is not trustworthy when errors are correlated.

Independent N-version *derivation* is cheaper: isolate reviewers/agents against a neutral frozen specification, compare results, and investigate disagreements. It strengthens an oracle but still shares the specification.

## Debugging protocol

1. Preserve the first failure exactly.
2. Minimize environment/input/sequence without changing the causal signature.
3. State at least two plausible hypotheses when evidence permits.
4. Choose the cheapest experiment whose outcomes distinguish them.
5. Repair the supported cause only; prove the focused regression and protected paths.
6. After three failed hypotheses/repairs, reopen reproduction, causal model, design, environment, oracle, or authority.

Use delta debugging only with a stable pass/fail predicate and meaningful partition. Use bisection only across comparable history. Use fault injection only in an isolated/authorized environment with explicit invariant, blast radius, reset, and teardown.

Five-whys can prompt questions; it is not causal proof. Logs can establish observed sequence; they do not automatically establish causation.
