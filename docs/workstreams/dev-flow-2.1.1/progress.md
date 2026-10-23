# Dev Flow 2.1.1 release progress

<!-- dev-flow-workstream-contract: v1 -->

- State: active
- Current slice: S1
- Source candidate: `2.1.1`
- Terminal condition: authorized batch committed and formally published as stable 2.1.1 with verified public assets; model journeys and installation remain outside this task.

## Current truth

- Published stable/workspace base: `v2.1.0`; candidate rollback target: `v2.1.0`.
- User authority on 2026-10-24: commit current batch as 2.1.1, then formal release. Prior no-additional-model-evaluation and no-install constraints remain in force. Five real stable model journeys are NOT RUN; this constrained publication does not claim complete functional acceptance, model benefit or installed behavior. Historical release waivers do not transfer.

Delivery state: commit=passed; hosted_ci=not-run; cross_platform=not-run; independent_review=passed; tag=not-run; artifact=not-run; publication=not-run; isolated_install=not-run.

## Reused implementation evidence

All three accepted goals are implemented. Eight distinct affected native tests, 39 contracts, suite/plugin/shipped-knowledge checks and a fresh independent source review passed before release metadata preparation. These qualify their unchanged guidance inputs, not new version or delivery facts. The three plan-review rounds and bounded implementation review are preserved in the accepted plan; no repeat campaign is needed.

The maintained Markdown knowledge checker previously failed on an unchanged inline-code documentation-link example in the 2.1.0 progress document. The original result remains in `/tmp/dev-flow-proportionate-plan-knowledge.json`; the scanner does not strip inline code. This known observation false positive is not repaired or rerun in this release. Newly added local link targets are checked separately. No failure is relabeled PASS.

## Qualification and delivery

Final-candidate observations are pending. Preserve source identities, first failures, skips, hosted runs, artifact digests and public state here as observed. The immutable candidate contains this pre-publication snapshot; later progress is a separate truth commit.

| ID | Condition | Gate | Status | Closure/decision |
|---|---|---|---|---|
| HC1 | Final native regression and maintained validators | qualification | passed | First full run: 822 tests, two stale assertion failures and one Windows-only skip; nine affected checks pass after focused repair; exact final hosted full suite remains HC3 |
| HC2 | Cumulative public-stable-to-candidate semantic and six-method static review | qualification | passed | Independent clean-context review found no consequential defect in the cumulative guidance delta |
| HC3 | Exact-SHA semantic and applicable compatibility CI | qualification | not-run | Hosted observations pending |
| HC4 | Hosted archive, manifest, SBOM, checksums and bound attestations | qualification | not-run | Hosted observations pending |
| HC5 | Immutable stable tag and public four-asset identity | qualification | not-run | Publication pending |
| HC6 | Five real model journeys and installed behavior | qualification | not-run | Explicit continuing user scope excludes new model evaluation and installation; no PASS or complete-acceptance claim |

## Cumulative static review

A fresh P4 Sol-medium read-only review compared public v2.1.0 with all 11 changed Skill/reference files, accepted plan and affected consumers. No consequential finding remains. Release metadata was prepared concurrently and is checked separately by native projections and root review.

- Traceability/V-model: all three objectives reach their existing requirements/architecture, defense/review and verification/test-system owners; no dropped objective.
- Change impact: kernel, requirement agents, reviewers and test-runner consumers contain no opposing instruction; no executable interface change.
- Specification by example: manual import versus accepted restart recovery, internal invariant versus persisted corruption, normal completion versus timeout and documentation versus runner change keep distinct decisions.
- Feature interaction: simplification preserves accepted guarantees, centralized validation preserves dynamic authorization/resource duties, and reuse preserves first failures, explicit reruns and frozen-candidate acceptance.
- Black/white oracles: expected decisions are grounded in accepted examples and inspected consumers; freshness/context checks observe static properties only, not model understanding or real-task benefit.
- Assumption/premortem: explicit counterrules address weakened guarantees, missing defenses, stale sensitivity evidence and untested failure branches; unknown dependencies require affected checks.

Initial release workstream validation rejected the unsupported gate class `observation`; corrected it to the existing `qualification` vocabulary only. Original receipt: `/tmp/dev-flow-2.1.1-workstream-initial.json`. No product behavior or acceptance threshold changed.

## Native first failure and bounded correction

Candidate `40c7bb578b49d200b21005822af6ac2650f8ab52` ran the complete native suite once with Python 3.13.14 and ResourceWarnings as errors: 822 tests in 73.813 seconds, 819 passes, two failures, one native-Windows-only skip. The first log and receipt are preserved at `/Users/ethan/Documents/Codex/2026-10-23/dev-flow-2.1.1-release-qufne286/native-full.log` and `native-result.json`.

Both failures were stale static wording oracles: `test_quality_practices` required the replaced phrase “practical negative control”; `test_rc7_test_skills` required “preserves the required behavior” while the maintained reference protects “preserves the requirement”. The current accepted guidance still requires a failure-sensitive assertion, invalidation/rechallenge, preserved input/failure/resource responsibilities and confirmation before changing business guarantees. Only these two existing test files were updated to observe those obligations. In-memory omission controls reject loss of each sensitivity obligation and each behavior/authority guard. Nine affected tests pass in `native-focused-repair.log`; no entire native rerun or product-rule weakening was performed. The final exact-source hosted full suite will separately qualify final bytes.

All eleven maintained native validator commands pass: 39 structural contracts, product state, RC.5 coverage, RC.4 static invariants, shipped methods/knowledge, plugin, 15-Skill suite, packaged data-security doctor, compilation and workstream structure. The security doctor has zero required failures and five live/manual gates not_observed. Root checked release metadata, unchanged protected code and 100 local link targets; whitespace checks pass. The previously identified Markdown scanner false positive remains explicitly failed and outside this repair.

The same independent reviewer inspected only the two repaired oracles and current metadata. No consequential finding: explicit sensitivity/invalidation and requirement/input/failure/resource/confirmation safeguards are retained, and omission controls expose their removal. First-failure and affected-pass receipts remain separate.
