<!-- dev-flow-workstream-contract: v1 -->
# Dev Flow 2.0 RC.6 progress

## Status

- State: active
- Current slice: S1
- Terminal condition: the immutable RC.6 candidate completes authorized exact-SHA hosted, artifact, isolated-install, tag, and public prerelease actions, then a separate current-truth commit records observed delivery.
- Updated: 2026-09-01

## Current

Candidate identity and maintained projections are ready to freeze. `v2.0.0-rc.5` remains the latest published tag and rollback target. No RC.6 tag, push, public release, artifact attestation, hosted CI result, or isolated installation has yet been recorded.

## Hard conditions

| ID | Condition | Gate | Status | Closure/decision |
|---|---|---|---|---|
| HC1 | Candidate identity and maintained projections agree | implementation | passed | source candidate does not claim RC.6 publication |
| HC2 | Final full deterministic suite and same-context static review pass | qualification | open | independent review is not separately authorized; common-mode risk remains |
| HC3 | Exact-SHA hosted semantic and applicable compatibility jobs pass | qualification | open | hosted result is checked after push |
| HC4 | Artifact, tag, public prerelease, and isolated installation are verified | qualification | open | each external result is action-specific |
| HC7 | Independent clean-context review | qualification | not-run | no separate reviewer authority; same-context review only |

## Evidence limits

- No local evidence is treated as hosted, public, installed, or production evidence.
- Model spend and live model trials remain `NOT RUN` and are not release gates for this candidate.
