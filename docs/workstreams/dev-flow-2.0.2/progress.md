# Dev Flow 2.0.2 release progress

<!-- dev-flow-workstream-contract: v1 -->

- State: closed
- Current slice: S3
- Terminal condition: final candidate qualified, pushed, published as stable 2.0.2 and primary installation verified, with unobserved loading limits explicit.

## Current truth

- Published stable: `2.0.2`, immutable `v2.0.2`. Workspace base is `v2.0.2`; rollback target remains `v2.0.0`.
- User authority: pre-release checks/documentation, commit, push, stable tag/release and primary local update.
- Five actual model functional journeys: WAIVED by explicit user instruction on 2026-10-05. No live-model spend or PASS is inferred.

Delivery state: commit=passed; hosted_ci=passed; cross_platform=passed; independent_review=passed; tag=passed; artifact=passed; publication=passed; isolated_install=passed.

## Evidence

- The three-pass DLP audit closed verified findings, exercised 73 audit tests and six credible isolated mutations, and passed 795 full-suite tests (794 pass, one native-Windows-only skip). Final audit source identity remains available; release version/projection changes require fresh candidate checks.
- Primary pre-update listing was installed/enabled 2.0.1. Final primary listing is installed/enabled 2.0.2, pinned to immutable public `v2.0.2`; marketplace source resolves to the candidate, and both source and versioned cache match all 156 shipped files. Fifteen Skills are discoverable and packaged doctor has zero required failures. The immutable 2.0.1 cache was backed up for running old-session Hook paths. Subsequent host cleanup removed its Hook and blocked the final record commit; after resuming, that original Hook is present again and tools work. Host cache retention is not guaranteed, and other chats are not inferred reloaded.
- Final repaired candidate `e5abd4bbb2dc6758400ea74a299e12d5e0770c39` passed 796 local tests in 83.398 seconds: 795 passes and one native-Windows-only skip, with ResourceWarnings treated as errors. The complete log is `/tmp/dev-flow-202-repaired-full-suite.log`; the preceding candidate result remains historical.
- Product-state, 15-Skill suite, knowledge, plugin, packaged security doctor, contracts, legacy-method data, RC.4/RC.5 static invariants, compilation and diff checks pass. Doctor has zero required failures and five manual/live gates. The subsequent Windows binary-read repair has focused regression and independent review evidence; required validators were rerun on the repaired candidate.
- Cumulative clean-context stable review and the final Windows repair review pass. Exact-SHA hosted CI `run_37256307278` passes semantic Ubuntu/Python 3.14 and all five compatibility cells: Ubuntu/Python 3.11, macOS/Python 3.11 and 3.14, Windows/Python 3.11 and 3.14. Hosted artifact, public stable tag/release, four-asset byte readback, public-tag isolated lifecycle and primary installation all pass. The first extra flow-metrics command incorrectly supplied unsupported `--root`; this was a test invocation error, corrected using the public command help rather than a product change.

## Preserved candidate failure and repair

- Candidate `79c90025935fbe32095eeff4852f023a15746c2d` was committed and pushed. Its local two-build artifacts match, and isolated local install/discovery/156-file identity, three Hook controls and uninstall pass. Deterministic activation matches all 38 catalog and 80 large-task cases; these are routing observations, not model-journey outcomes.
- Exact-SHA CI run `37255846323` failed both Windows compatibility cells: three invalid-key errors on Python 3.11 and one missing-confirmation assertion on Python 3.14. Linux/macOS cells pass. The original native logs remain under the first delivery directory as `windows-first-real-3.11.log` and `windows-first-real-3.14.log`; no failed cell was removed or waived.
- Causal repair: raw `_read_limited` descriptors now select `O_BINARY` on Windows, preventing CRT CRLF/Ctrl-Z translation of a valid random 32-byte HMAC key. A fixed control-byte key must round-trip, issue and consume once; native Windows additionally proves that explicit text-mode reading changes the bytes. A test-setup mock initially affected all random IDs and failed schema validation; narrowing the mock to key creation repaired the harness. That setup failure is not the native product failure.
- The six-method cumulative independent review found no unresolved high-consequence issue and passed 78 focused tests before this platform repair. Its 35-file fingerprint and concrete controls are retained in `/tmp/dev-flow-2.0.2-cumulative-review-manifest.json`; the new minimal repair is independently rechecked separately. No public tag was created for the failed candidate.

- Hosted artifact workflow `run_37256753263` succeeds for the exact repaired source. Annotated immutable public `v2.0.2` resolves to `e5abd4bbb2dc6758400ea74a299e12d5e0770c39`; the stable release is observed non-draft and non-prerelease with all four required assets.

- Public-tag isolated install reports installed/enabled 2.0.2, exact candidate source, 156 matching shipped files, 15 Skills, zero required doctor failures, three synthetic Hook controls and verified uninstall. Public downloads match archive, manifest, SBOM and SHA256SUMS byte-for-byte with hosted evidence.
- Final primary installation evidence is `primary-install-evidence.json` under the repaired delivery directory. Existing chats must restart Codex and open a fresh chat/context to load the new version; current-session loading remains `not_observed`. No real credential or approval store was read or migrated.
- Candidate source CI: [exact-SHA platform and semantic checks](https://github.com/AldenClark/dev-flow/actions/runs/37256307278). Artifact evidence: [build and attest workflow](https://github.com/AldenClark/dev-flow/actions/runs/37256753263). Public observation: [stable 2.0.2 release](https://github.com/AldenClark/dev-flow/releases/tag/v2.0.2). Detailed local artifacts reside at the path in `/tmp/dev-flow-202-delivery-root.json`; native Windows first-failure logs stay in its `first_delivery`.
- Closure records observed external facts in a separate documentation/product-state commit. This commit does not move the immutable public tag or replace published assets; model journeys remain explicitly WAIVED.

## Hard conditions

| ID | Condition | Gate | Status | Closure/decision |
|---|---|---|---|---|
| HC1 | Final native suite and maintained projections validate | qualification | passed | 795 local passes / one native-Windows skip; required validators pass |
| HC2 | Stable-to-candidate requirements and consolidated static review close | qualification | passed | Six-method cumulative review and final Windows repair review close |
| HC3 | Exact candidate CI and applicable platform matrix pass | qualification | passed | Final candidate semantic and five compatibility cells pass; no historical waiver inherited |
| HC4 | Hosted artifact, SBOM/checksum and attestations bind exact source | qualification | passed | Archive/checksums/SPDX identity verified; provenance and SBOM attestations enforce repository, workflow and exact source |
| HC5 | Public immutable stable tag/assets and isolated lifecycle observed | qualification | passed | Public non-prerelease tag/release; all four assets match hosted bytes; isolated public-tag install, three Hook controls and uninstall pass |
| HC6 | Primary installed version/source/content verified | qualification | passed | Installed/enabled 2.0.2; source and cache match 156 files, 15 Skills, doctor zero required failures; old-chat loading not_observed |
| HC7 | Five live-model functional journeys | qualification | waived | Explicit user exception for this scoped DLP patch |

## Evidence limits

Live account policy, other running chats and production outcomes remain not_observed. Current approval/credential stores are outside this release test. A public/install command response must be reconciled against actual remote/installed identity before being reported complete.
