# Dev Flow 2.0.3 release progress

<!-- dev-flow-workstream-contract: v1 -->

- State: closed
- Current slice: S3
- Published stable: `2.0.3`, immutable `v2.0.3`
- Terminal condition: final candidate qualified, committed/pushed, publicly published as stable 2.0.3 and primary installation verified; report fresh-session loading separately.

## Current truth

- Workspace base and published stable: `v2.0.3`; previous stable and rollback: `v2.0.2`.
- User authority: pre-release checks/docs, commit, push, stable tag/publication and primary installation on 2026-10-10.
- Five functional journeys: WAIVED by explicit user decision on 2026-10-10 for this 2.0.3 release. No journey calls, PASS or quality-equivalence claim are inferred; the prior DLP exception was not reused.

Delivery state: commit=passed; hosted_ci=passed; cross_platform=passed; independent_review=passed; tag=passed; artifact=passed; publication=passed; isolated_install=passed.

## Local evidence

The preceding model-policy implementation passed 806 tests (805 pass, one native Windows Job Object skip), 47 affected checks, final document checks and independent Sol-medium review. These do not qualify subsequent version/projection changes. First failed policy and context-budget observations were preserved; final entrypoint bytes remain unchanged at 13,469/13,500 ordinary static bytes. Final release candidate checks and cumulative review are recorded separately below. Initial workstream checking detected a missing ID condition table; the existing contract table was added, without changing any release gate. A second check rejected the invented `planned` slice status; disposition: simplify to the contract’s existing `pending` vocabulary and keep the plan stable thereafter.

## Cumulative stable-to-candidate review

Independent clean-context Sol-medium review covered the cumulative public v2.0.2-to-candidate delta. One consequential P2 finding was found and closed: active build instructions selected 2.0.3 but comparison/verification/attestation examples still selected 2.0.2. All active example names and expected versions now select 2.0.3; reviewer closure recheck and diff check pass. No unresolved consequential finding remains.

- Traceability/V-model: registry, CLI, guidance and native tests align on ordinary P4, compound P5/P6 and explained explicit promotion. No dropped maintained requirement found.
- Change impact: public entrypoint → parser → public handler → router → host checks/output; both handlers forward selection_reason. Hooks and protected DLP source remain unchanged.
- Specification by example: fixed commands P0; adaptive verification P4; ordinary cross-component/high-risk review P4; complex positive controls retain P5/P6.
- Feature interaction: independent expected-value sweep of 2,048 signal combinations passes, including settled markers paired with unresolved signals.
- Black/white oracle accounting: 29 native routing checks pass, covering explicit override errors, host inventory, root/coupled boundaries and blanket-promotion negative controls. Full final regression separately passes 806 tests (805 pass / one Windows-only skip).
- Assumption mapping/premortem: caller reasons and host inventory remain assertions, not human permission or verified reasoning evidence. Suggestions do not spawn automatically; static routing is not proof of model-quality equivalence or savings. Recovery pins v2.0.2 after a material workflow regression and verifies installed bytes/fresh-session loading.

## Final local qualification

86 affected tests pass; 44 version/stable-method checks and 15 active-guidance checks pass after the runbook repair. The complete suite passes 806 tests in 81.898 seconds with ResourceWarnings treated as errors (805 pass / one native Windows Job Object integration skip). Suite (15 Skills), knowledge, plugin, packaged data-security doctor, 39 contracts, RC.4 static scan, RC.5 coverage, maintained methods, compilation and diff checks pass. Doctor has zero required failures and five live/manual gates not_observed. One additional targeted test command named a nonexistent test module; that invocation error is preserved in dev-flow-203-release-docs.log and corrected to the existing modules without product change. Workstream setup errors and simplification disposition remain recorded above.

Five live-model journeys are explicitly WAIVED for this release; no comparison/model spend or quality-equivalence result is inferred. Native Windows/platform, hosted artifacts and public/installed identity are recorded below as separate completed observations.

## Bounded functional plan

Use the existing five stable journeys: ordinary bugfix; material semantic change with requirement confirmation; diagnose-fix-verify; unrelated local MCP isolation; continuation without inferred delivery authority. Each journey runs once on isolated final-candidate bytes, at most 13 total model calls/turns, at most 600,000 exposed tokens per call and 2,000,000 total. Stop on failure, budget exhaustion or consequential oracle/identity mismatch; no automatic retry, model comparison, production resource, real credential or primary-profile mutation. The user explicitly waived all five journeys for this release; this retained plan was NOT EXECUTED and authorizes no spend.

## Evidence limits

Five actual journeys remain WAIVED. Exact-SHA hosted CI/platform/artifacts, public publication, isolated public installation/uninstall and primary updated bytes have separately observed passes. Packaged security checks do not validate live account policy. Existing chats are not inferred reloaded.

## Hard conditions

| ID | Condition | Gate | Status | Closure/decision |
|---|---|---|---|---|
| HC1 | Final local regression, affected controls and maintained projections | qualification | passed | 805 local passes / one native Windows skip; validators and focused checks pass |
| HC2 | Cumulative v2.0.2-to-candidate semantic and six-method static review | qualification | passed | Independent review found and closed stale release example versions; six conclusions below |
| HC3 | Five live-model functional journeys | qualification | waived | Explicit user exception for this 2.0.3 release on 2026-10-10 |
| HC4 | Exact-SHA semantic CI and applicable platform matrix | qualification | passed | Exact candidate semantic CI and all five Linux/macOS/Windows compatibility cells pass |
| HC5 | Hosted artifact/SBOM/checksums and bound attestations | qualification | passed | Hosted archive/manifest/checksums/SPDX and provenance/SBOM attestations verify exact source, signer workflow/digest and main ref |
| HC6 | Immutable public stable tag/assets and isolated public lifecycle | qualification | passed | Non-draft/non-prerelease public v2.0.3, four matching assets, isolated installed identity/three synthetic Hooks/uninstall pass |
| HC7 | Primary installed source/cache identity | qualification | passed | Installed/enabled 2.0.3; 466 tracked files and 157 active payload files match source/cache, 15 Skills, doctor zero required failures; old Hook retained |

## External observations

Candidate commit `b5951234d50dc03425e17da2c858e8d7aceb97f8` is pushed on main. [Exact-SHA CI](https://github.com/AldenClark/dev-flow/actions/runs/38015692997) passes full semantic Ubuntu/Python 3.14 and five compatibility cells: Ubuntu/Python 3.11, macOS/Python 3.11 and 3.14, Windows/Python 3.11 and 3.14. No platform failure was waived. The [artifact workflow](https://github.com/AldenClark/dev-flow/actions/runs/38015944179) passed for this exact SHA and does not repeat semantic CI. Current uncommitted truth documentation does not alter candidate/tag/artifact bytes.

Public annotated `v2.0.3` resolves to candidate `b5951234d50dc03425e17da2c858e8d7aceb97f8`; the [stable release](https://github.com/AldenClark/dev-flow/releases/tag/v2.0.3) is observed non-draft/non-prerelease with four assets. All public files match the verified hosted files byte-for-byte. Provenance and SBOM attestation CLI verification enforce source/signer digests, signer workflow, main ref and GitHub-hosted runners. A premature read of the still-running SBOM verifier’s empty output failed locally; no tag/publication action occurred then. Waiting for the existing call to complete produced both successful results; no verifier retry or product repair was needed.

## Installed observations and closure

Public-tag isolated install reports installed/enabled 2.0.3, exact candidate source, 466 matching tracked files (157 active plugin payload files including LICENSE), 15 Skills, packaged doctor zero required failures and all three synthetic installed Hook controls. Uninstall is verified in listing and cache disappearance. Initial setup failed because the isolated Codex home did not yet exist; creating the owned empty home corrected the invocation without product changes.

Primary installation separately reports installed/enabled 2.0.3, exact immutable tag source, all 466 tracked source/cache files and 157 active payload files matching the candidate, 15 Skills, doctor zero required failures and three synthetic installed Hook controls. Installed CLI selects P4 for routine independent review; no live model was called. Adding a different pinned marketplace ref initially failed before mutation; read-only reconciliation confirmed 2.0.2 unchanged. The CLI’s required remove/add flow then succeeded for dev-flow only; other installed plugin identities/enabled states remain unchanged. The 2.0.2 cache was backed up and missing files restored for old-session Hook paths; the old Hook is present after updating. Host cleanup/retention and existing-chat loading remain not_observed.

Detailed evidence lives at `/Users/ethan/.codex/visualizations/2026/10/10/dev-flow-2.0.3-release/`: CI/platform logs, hosted/public files, both bound attestation results, public tag/release readbacks, isolated lifecycle, primary source/cache checks and old-Hook backup/restoration. A separate current-truth commit records these external facts without moving v2.0.3 or replacing its assets. Restart Codex and open a fresh chat to load 2.0.3 guidance. Live account policy and production outcomes remain not_observed; five live-model journeys stay explicitly WAIVED and model-quality equivalence/cost savings remain unproved.

Final current-truth projections passed 59 affected tests, product-state completion validation, closed workstream validation, suite/knowledge/plugin/security/contracts checks, compilation and diff checks. These checks qualify the post-publication truth documentation; release source remains the earlier exact-SHA qualified immutable candidate.
