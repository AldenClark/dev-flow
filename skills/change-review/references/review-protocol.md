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

## Simplification and maintainability

Review complexity against the current requirement and repository conventions:

- Is an abstraction, configuration option, compatibility shim, cache, state machine, extension point, dependency, or parallel path justified by a current behavior or demonstrated variation?
- Has one concept been split across layers/files/owners so that errors, state transitions, or cleanup can diverge?
- Is raw input repeatedly parsed or validated instead of crossing one trustworthy typed boundary?
- Are comments and tests preserving reasons and behavior, or compensating for unclear code and locking down incidental representation?

When value is genuinely unclear, compare the current change with a bounded smaller form or remove/bypass one isolated mechanism and run the same behavioral oracle. Report a finding only if the simpler form preserves the requirement while removing a concrete failure surface or material maintenance burden. Line count, language taste, and hypothetical future extensibility are not proof.

## Test and evidence challenge

Inspect changed tests as evidence, especially when the same AI produced implementation and tests. Derive the expected user/contract result independently, then inspect final-code branches, states, boundaries, and errors for missed white-box risk. A test that asserts setup, mock calls, snapshots, or internal details may stay green while the promised behavior is wrong.

Use focused reproduction or route to `verification` when a candidate depends on behavioral proof. Use `test-system-engineering` when the uncertainty is whether the intended tests were discovered/selected, whether caches/retries/skips hid execution, whether fixtures leaked, or whether host/mock/emulator evidence was mislabeled as a real boundary. Do not convert an unrun test idea into a defect.

## Saturation

After each material repair or diff update, revisit the causal path and any newly affected consumer. Stop when applicable boundaries have been traced, candidates have been verified or dismissed, and another relevant lens yields no new consequential evidence. Preference-only differences, duplicate statements of the same cause, unsupported hypotheticals, and recursive reviews do not justify continuation.

A material new diff, newly reachable consumer, contradictory runtime result, or new high-consequence mechanism can reopen review. Finding count and round count never determine completion.

## Recheck

After repair, inspect the affected diff and rerun the checks that can falsify the repaired behavior. Escalate repeated non-causal repairs to design or debugging when they stop producing new evidence. Completion order, report count, and finding count are not quality metrics.
