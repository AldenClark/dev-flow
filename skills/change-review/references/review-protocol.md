# Independent change review

Use this deeper protocol for a large change, high-risk boundary, or review intentionally separated from implementation.

## Review input

Establish the objective, current source or base/final diff, reviewed paths, important contracts, explicit exclusions, and raw verification results. Use an exact revision when the review must remain stable; otherwise state that findings are against the current worktree. Do not preload the implementer's conclusions.

## Lenses

Inspect only applicable areas:

- requirement and scope fidelity, integration, public/data/protocol compatibility;
- errors, cancellation, ownership, lifecycle, cleanup, migration, rollback;
- security/privacy, unsafe/FFI, performance, operations, observability;
- generated artifacts, dependencies, packaging/loading, platform and mixed-version behavior;
- malformed/adversarial input, authorization, retries, duplicates, ordering, races, overload, shutdown, data loss, partial failure, and recovery.

Load a specialist only when its language, platform, or boundary is present and its additional failure model is worth the context cost.

## Finding discipline

A reportable finding needs a current source location, causal path, concrete impact, and bounded correction. Verify it in the current source and omit speculation, style preference, or names-only heuristics.

Classify the issue as implementation defect, design defect, evidence gap, scope change, requirement ambiguity, or non-issue. Report severity, proof, consequence, and remediation. Use repository-native IDs only when the project already has them; Dev Flow does not require finding ledgers, repair-round counters, or fixed blue/red documents.

For cross-language changes, trace affected consumers, generated artifacts, ABI/ownership/lifecycle, packaging/loading, version coexistence, and rollback where relevant. Missing device, platform, signing, or runtime evidence remains `NOT RUN`.

## Recheck

After repair, inspect the affected diff and rerun the checks that can falsify the repaired behavior. Escalate repeated non-causal repairs to design or debugging when they stop producing new evidence. Completion order, report count, and finding count are not quality metrics.
