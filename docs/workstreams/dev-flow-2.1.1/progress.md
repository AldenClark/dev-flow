# Dev Flow 2.1.1 release progress

<!-- dev-flow-workstream-contract: v1 -->

- State: implementation-complete
- Current slice: S1
- Published source: `2.1.1`
- Terminal condition: authorized batch committed and formally published as stable 2.1.1 with verified public assets; model journeys and installation remain outside this task.

## Current truth

- Published stable/workspace base: `v2.1.1`; rollback target: `v2.1.0`.
- User authority on 2026-10-24: commit current batch as 2.1.1, then formal release. Prior no-additional-model-evaluation and no-install constraints remain in force. Five real stable model journeys are NOT RUN; this constrained publication does not claim complete functional acceptance, model benefit or installed behavior. Historical release waivers do not transfer.

Delivery state: commit=passed; hosted_ci=passed; cross_platform=passed; independent_review=passed; tag=passed; artifact=passed; publication=passed; isolated_install=not-run.

## Reused implementation evidence

All three accepted goals are implemented. Eight distinct affected native tests, 39 contracts, suite/plugin/shipped-knowledge checks and a fresh independent source review passed before release metadata preparation. These qualify their unchanged guidance inputs, not new version or delivery facts. The three plan-review rounds and bounded implementation review are preserved in the accepted plan; no repeat campaign is needed.

The maintained Markdown knowledge checker previously failed on an unchanged inline-code documentation-link example in the 2.1.0 progress document. The original result remains in `/tmp/dev-flow-proportionate-plan-knowledge.json`; the scanner does not strip inline code. This known observation false positive is not repaired or rerun in this release. Newly added local link targets are checked separately. No failure is relabeled PASS.

## Qualification and delivery

The authorized commit and stable publication are complete. Source identities, first failures, skips, hosted runs, artifact digests and public state are recorded below. HC6 remains not-run; the workstream does not claim the stronger complete functional/installation qualification gate. The immutable candidate contains this pre-publication snapshot; later progress is a separate truth commit.

| ID | Condition | Gate | Status | Closure/decision |
|---|---|---|---|---|
| HC1 | Final native regression and maintained validators | qualification | passed | First full run: 822 tests, two stale assertion failures and one Windows-only skip; nine affected checks pass after focused repair; exact final hosted full suite remains HC3 |
| HC2 | Cumulative public-stable-to-candidate semantic and six-method static review | qualification | passed | Independent clean-context review found no consequential defect in the cumulative guidance delta |
| HC3 | Exact-SHA semantic and applicable compatibility CI | qualification | passed | Final 7c0c950 source passes semantic 822 tests and all five 361-test compatibility cells |
| HC4 | Hosted archive, manifest, SBOM, checksums and bound attestations | qualification | passed | Final candidate hosted bytes and both source/signer-bound attestations verify |
| HC5 | Immutable stable tag and public four-asset identity | qualification | passed | Annotated exact-source tag, non-draft/non-prerelease latest stable and four byte-identical public downloads verified |
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

## Exact-source hosted qualification

Final candidate is `7c0c950f58e848d5452eb5d6242e9d8661d2095a`; the source and focused-oracle correction were pushed without rewriting history. [CI 39987471900](https://github.com/AldenClark/dev-flow/actions/runs/39987471900) is completed/success for that exact SHA. The Python 3.14 semantic lane ran 822 tests in 210.415 seconds (820 passes, two environment-specific skips) and all maintained validators/compilation/clean-tree checks pass. Each of five Ubuntu/macOS/Windows Python 3.11/3.14 compatibility cells ran 361 tests successfully; Ubuntu/macOS skip one Windows-only case, and Windows cells skip four unsupported-environment cases. Individual job logs and the exact-SHA run receipt are preserved with the native evidence. No rerun of successful hosted jobs was needed.

## Hosted artifacts and immutable tag

[Artifact run 39988199437](https://github.com/AldenClark/dev-flow/actions/runs/39988199437) completed successfully for `7c0c950f58e848d5452eb5d6242e9d8661d2095a`. Downloaded archive, release manifest and SHA256SUMS verify expected 2.1.1/source identity. SPDX 2.3 identifies dev-flow 2.1.1 and inventories 579 files. Both provenance and SBOM attestations verify with the exact source digest, `refs/heads/main`, signer workflow `.github/workflows/release-candidate.yml`, exact signer digest and rejection of self-hosted runners.

Archive SHA-256: `6daea4075b5bc83b273adcd0565a661d0fb780dcb73d4692a62faa82bd71ff33`. All four hashes, original downloads and attestation results are preserved in the evidence directory. The annotated remote `v2.1.1` tag resolves to the exact candidate. At the tag checkpoint publication remained pending; tagged pre-publication bytes were retained unchanged.

The [public stable 2.1.1 release](https://github.com/AldenClark/dev-flow/releases/tag/v2.1.1) is observed non-draft/non-prerelease with all four expected assets. At this initial publication observation canonical truth advanced before public-byte download verification. The final verification is recorded below; installation remains not-run.

## Final public observation and limits

Public verification completed: all four downloaded files exactly match the hosted SHA-256 inventory, and the repository latest-release endpoint identifies non-draft/non-prerelease `v2.1.1`. Publication occurred at 2026-10-23 16:39:10 UTC (2026-10-24 Asia/Shanghai). Public verification and latest-release receipts are retained alongside the source, native, hosted and attestation records. The canonical source phase is stable, default installation/workspace base is v2.1.1, and rollback remains v2.1.0.

No isolated/primary installation, live Hook loading, actual model journeys, quality equivalence, measured cost reduction or production outcome was performed or inferred. The existing Markdown scanner false positive remains recorded separately from passing maintained release validators. This follow-up truth commit changes publication projections only; the tag and artifacts continue to identify 7c0c950 and are not rebuilt or rewritten. Complete delivery/functional qualification remains unclaimed because HC6 is not-run; the explicitly requested commit and public release are complete.
