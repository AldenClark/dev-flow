---
name: change-review
description: Find verified consequential defects or needless complexity in current diffs.
---

# Change Review

Review actual source and final diffs, not the implementer's narrative. Report only issues with a verified causal path and concrete consequence. Review depth follows blast radius and risk; ordinary changes do not require ceremonial reports.

This Skill may operate alone for an independent read-only review. If the request also authorizes material repair, crosses repositories, needs managed continuity, or assesses high-risk delivery, load `dev-flow` as the coordinating kernel when it is available and not already active; keep this Skill as the finding owner.

## Procedure

1. Establish the objective, repository state, reviewed paths/base, relevant contracts, and raw verification evidence.
2. Trace only applicable behavior through callers, consumers, state/error/resource lifecycles, integration boundaries, compatibility, generated/package surfaces, and operating environments. Challenge material inputs, cancellation, retries, ordering, races, partial failure, recovery, and rollback where reachable.
3. Apply a simplification lens: look for unsupported abstractions, configuration, extension points, compatibility layers, scattered ownership, repeated parsing/state conversion, and tests coupled to implementation trivia. A smaller alternative matters only if it preserves the required behavior and removes a real failure or maintenance cost.
4. Challenge AI self-confirmation: compare tests with product contracts and the final implementation's branches/states/boundaries. If discovery, selection, isolation, cache, retry, skip, fixture, mutation, or environment evidence is doubtful, route that question to `test-system-engineering` or `verification` instead of inferring a defect.
5. Verify each candidate in current source with a reachable causal path and, when practical, a focused reproducer, counterexample, or native test. Report severity, location, proof, consequence, and bounded repair; omit speculation, style preference, and names-only heuristics.
6. After repair, recheck the affected path and regressions. Return requirement ambiguity, architectural defects, causal uncertainty, and evidence gaps to their owning problem rather than manufacturing another review round.

Read `references/review-protocol.md` for large or independent reviews and `references/authorization-privacy.md` only when the change contains that boundary.

## Saturation

Stop when the reviewed changed paths and affected consumers/boundaries have no unresolved consequential candidate, another applicable lens produces no new causal evidence, and remaining comments are wording, naming, formatting, theoretical unreachable scenarios, or personal preference. Reopen only for a material new diff, consumer, failure mechanism, or contradictory evidence. Do not target a finding count, a fixed number of rounds, or recursive review of the review.

## Boundaries

- Names and patterns alone are not findings.
- Generic review does not prove security, accessibility, compatibility, runtime, or release readiness.
- A missing test or simplification opportunity is reportable only when its consequence and causal gap are verified; “more coverage” and “fewer lines” are not findings by themselves.
- Do not require acceptance IDs, digests, frozen packet artifacts, or separate blue/red documents unless a repository-native process consumes them.
