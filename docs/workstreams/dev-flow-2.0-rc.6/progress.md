<!-- dev-flow-workstream-contract: v1 -->
# Dev Flow 2.0 RC.6 progress

## Status

- State: release-qualified
- Current slice: none
- Terminal condition: satisfied by the immutable RC.6 candidate and this separate current-truth record.
- Updated: 2026-09-01

## Current

Candidate `2d1cb4be8d97433511e6fffb032d2e505deaf0d9` is immutably published as `v2.0.0-rc.6`. Hosted semantic CI and all applicable compatibility cells passed; archive, SPDX SBOM, checksums, provenance/SBOM attestations, public prerelease, and isolated fresh marketplace installation/uninstall passed. `v2.0.0-rc.5` is retained as rollback target.

## Hard conditions

| ID | Condition | Gate | Status | Closure/decision |
|---|---|---|---|---|
| HC1 | Candidate identity and maintained projections agree | implementation | passed | source candidate does not claim RC.6 publication |
| HC2 | Final full deterministic suite and same-context static review pass | qualification | passed | final local suite passed; review found and repaired RC.5 traceability drift before candidate freeze |
| HC3 | Exact-SHA hosted semantic and applicable compatibility jobs pass | qualification | passed | GitHub Actions run 33482276265 passed semantic and all six compatibility jobs |
| HC4 | Artifact, tag, public prerelease, and isolated installation are verified | qualification | passed | artifact run 33482784927, annotated tag, public prerelease, and temporary-profile install/uninstall passed |
| HC7 | Independent clean-context review | qualification | waived | no separate reviewer authority; same-context review retained common-mode risk |

## Evidence limits

- No local evidence is treated as hosted, public, installed, or production evidence.
- Model spend and live model trials remain `NOT RUN` and are not release gates for this candidate.
