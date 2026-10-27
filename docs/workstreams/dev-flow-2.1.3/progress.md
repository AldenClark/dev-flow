# Dev Flow 2.1.3 release progress

<!-- dev-flow-workstream-contract: v1 -->

- State: implementation-complete
- Current slice: S1
- Published source: `2.1.3`
- Terminal condition: accepted patch committed/pushed, public stable assets verified, isolated lifecycle and primary local installation observed; preserve current-host and model limits without claiming complete functional qualification.

## Current truth

- Published stable/workspace base: v2.1.3; rollback target: v2.1.2.
- User authority on 2026-10-27: current cwd patch as 2.1.3, commit, push, formal release and primary local Dev Flow update. No Codex upgrade or alpha installation, real sensitive-data mutation or additional model campaign.
- Delivery observations remain action-specific. Source tests do not establish current-chat loading or runtime execution-directory isolation.

Delivery state: commit=passed; hosted_ci=passed; cross_platform=passed; independent_review=passed; tag=passed; artifact=passed; publication=passed; isolated_install=passed.

## Accepted implementation and sensitivity

Previously a relative `event.cwd` was resolved against the Hook process directory and could consume confirmation issued for an absolute execution directory. The Hook schema and direct canonical_scope boundary now require non-empty native absolute paths without NUL. Missing, relative and URI values fail closed before marker-only confirmation or scope mutation. Absolute-path normalization, complete payload, session binding, TTL, hard policy and locked single consumption are preserved. No remote/workdir/process fallback is added.

Seven new native methods cover same input/different cwd, one correct consume, changed Hook process/turn, invalid metadata without issuing or advancing state, delayed Bash results and opaque remote MCP arguments. The first regression log is preserved, including correction of an initially wrong redaction-label expectation; the corrected pre-fix run exposes 26 cwd assertion failures across 7 methods. Post-fix all 7 pass, and the three related modules pass 84 tests in 7.976 seconds with ResourceWarnings treated as errors. Unchanged runtime bytes retain that evidence; final release/version bytes receive final native and hosted qualification below.

## Real current-host observation

App 26.1021.31345/build 21828, CLI 0.164.0-alpha.11.1, binary SHA-256 `a04752e4d46a4d89e53e6f61c59c5349a638c8ce172ffbf391fd482b4d902a4e`; native code signature validates and predates the public PR merges. Exact embedded source ancestry is not exposed, so behavior is observed directly. The same binary ran isolated app-servers with owned CODEX_HOME roots and a loopback mock Responses provider: no online model inference or primary settings changes. Only the three owned recorder hooks were reviewed/trusted using the native config API.

| Case | Actual command directory | Hook event cwd | Observation |
|---|---|---|---|
| Default | Initial host H | H | Control agrees |
| Relative workdir | Child A | Pre/Post H | Execution-cwd contract not satisfied |
| Absolute workdir | Other B | Pre/Post H | Execution-cwd contract not satisfied |
| Cross-turn empty write_stdin completion | Original A | Later-turn B | Original execution-cwd contract not satisfied |

The delayed result preserves original Bash input/tool-use identity; Hook process cwd remains the current host directory. [PR57198](https://github.com/openai/codex/pull/57198) and [PR57203](https://github.com/openai/codex/pull/57203) specify different event metadata. The first collector omitted a space while parsing an otherwise valid session id; its failure remains preserved and the already-valid local cases were reused. Nonempty stdin was actually rejected by the isolated read-only/never policy; this is not a passed stdin-approval test. A separate empty-poll case completed without relaxing that policy.

Consequently identical normalized Bash input and host cwd may coincide across actual workdirs on this host. The plugin cannot recover omitted metadata, and this patch does not claim complete native directory isolation. Remote host behavior, native Windows host paths, PermissionRequest/network approvals, nonempty stdin approval, existing desktop-chat effective loading and five live-model journeys remain unverified.

## Qualification and delivery

| ID | Condition | Gate | Status | Closure/decision |
|---|---|---|---|---|
| HC1 | Final native regression and maintained validators | qualification | passed | One848-test run preserved; two projection failures repaired and focused recheck passed; all maintained validators pass |
| HC2 | Cumulative six-method security/protocol review | qualification | passed | Independent cumulative review found no consequential defect; metadata validated separately |
| HC3 | Exact-source semantic and five compatibility cells | qualification | passed | CI 40435410692 exact 2dc35ef:848 semantic tests and all five 387-test compatibility cells pass |
| HC4 | Hosted archive, SPDX and bound attestations | qualification | passed | Run40435973989 exact-source archive/manifest/checksums,587-file SPDX and exact-source/ref/signer-bound attestations pass |
| HC5 | Immutable public stable tag/four exact assets | qualification | passed | Public stable/latest v2.1.3 and all four downloads match verified hosted bytes/source 2dc35ef |
| HC6 | Isolated public install/discovery/controls/uninstall | qualification | passed | First Git clone reset preserved; ref probe passed; one recovery home installs exact public tag,478 files/eight controls/doctor and complete uninstall pass |
| HC7 | Primary identity, controls and unrelated-plugin preservation | qualification | passed | Installed/enabled2.1.3;478 files/eight methods pass;23 unrelated plugins/bindings unchanged;519 old-cache file hashes match |
| HC8 | Complete execution-cwd isolation on current real host | qualification | blocked | Host emits old metadata; retained external limitation, no guessed fallback or completeness claim |
| HC9 | Five live-model journeys and existing-chat loading | qualification | not-run | No additional model campaign or loading inference |

Evidence is retained under `/Users/ethan/Documents/Codex/2026-10-27/dev-flow-2.1.3-release-v9yf3ema`, including copied implementation failures/results and real-host raw Hook/RPC/mock receipts. Full regression, source identities and external action results will be recorded as they occur. Earlier valid tests are not rerun without an affected claim.

## Cumulative review

A clean-context P4 reviewer inspected the public v2.1.2-to-candidate runtime/test/policy delta and traced schema, marker confirmation, canonical scope, keyed matching and locked consume. No consequential finding remained. Six conclusions: traceability matches both guards to 7 methods; impact stays within metadata and existing consumers/state; paired examples distinguish changed cwd/input and once-only reuse; interactions retain host prompt vs tool directory separation, hard policy and PostToolUse non-consumption; black/white evidence preserves pre-fix 26 failures and final 84 passes; assumptions explicitly retain native-platform normalization and unobservable older-host/remote directory truth. No extra dependency, registration, migration or inferred approval action is introduced. Parent-owned version/delivery projections are outside that review and receive maintained validators.

## First final-native and projection check

One full local regression ran 848 methods in 92.952 seconds: 845 passed, one native-Windows-only case skipped and two product-state/doctor assertions failed because the new release heading/rollback wording and governance navigation omitted required maintained projections. The first full log and validator result remain preserved. Only those documentation projections were restored; the two affected native tests and product-state/workstream/diff checks are rechecked. No runtime, test oracle or safety rule was weakened and the successful full-suite cases are not replayed locally. Exact-source CI will qualify all final candidate bytes.

## Source commit and hosted checkpoint

Candidate `2dc35efe8e76fe3e80c8a5469ee73027e4dfc93d` is committed and pushed on main. [Exact-source CI 40435410692](https://github.com/AldenClark/dev-flow/actions/runs/40435410692) is running. No published tag or installation completion is inferred. The primary 2.1.2 cache was backed up with 519 regular file hashes before update; unrelated plugin/marketplace snapshots are retained.

## Exact-source CI

[CI 40435410692](https://github.com/AldenClark/dev-flow/actions/runs/40435410692) succeeds on `2dc35efe8e76fe3e80c8a5469ee73027e4dfc93d`. Semantic Python 3.14 runs 848 tests in 205.541 seconds:846 pass/two environment skips. All five platform/Python cells pass 387 tests each; POSIX cells skip one Windows-only case, Windows cells skip four POSIX-only cases. All maintained validators, compilation and clean-tree checks pass. No native/hosted suite was repeated. The initial log-download CLI refused terminal escapes; raw output was subsequently captured only to local files with explicit output permission, never rendered as terminal control sequences. This was collection tooling, not a test failure. [Artifact run 40435973989](https://github.com/AldenClark/dev-flow/actions/runs/40435973989) is dispatched against the same immutable source.

## Hosted artifact and immutable tag

[Run40435973989](https://github.com/AldenClark/dev-flow/actions/runs/40435973989) succeeds on exact 2dc35ef. All four hosted files verify 2.1.3/full source SHA, with 587 SPDX 2.3 file entries and the correct root package. Provenance and SBOM attestations enforce exact source digest, signer digest/workflow and main ref, rejecting self-hosted runners. Archive SHA-256 is `3f5f2bf6b4b4d0adfcd3fcac5522c3a3a558dca344c76c724594e45c099ad7ca`. Annotated remote v2.1.3 resolves to `2dc35efe8e76fe3e80c8a5469ee73027e4dfc93d`; prior tags remain unchanged. Public GitHub Release and primary installation are pending.

## Isolated public-tag lifecycle

The first native marketplace add failed before installation with GitHub connection reset. Original logs/home are preserved. A same-environment read-only tag-resolution probe passed, followed by one bounded recovery in a fresh owned home. Native discovery reports enabled/installed 2.1.3 from 2dc35ef; all 478 source-archive files match, eight synthetic installed methods pass and doctor has zero required failures/five manual not_observed gates. Native uninstall confirms no installed plugin and removes its cache, then removes only the isolated marketplace. This recovery does not rewrite the first network failure. Canonical isolated-install state advances with observed publication, retaining the source-candidate invariant.

## Public stable checkpoint

[Public v2.1.3](https://github.com/AldenClark/dev-flow/releases/tag/v2.1.3) is observed non-draft/non-prerelease, published 2026-10-27T02:12:27Z with all four expected assets. Canonical source/published/workspace truth advances now; public-download byte verification and primary installation remain independent pending steps. The isolated public-tag observation remains bound to immutable 2dc35ef. A later read-only Git transport check also reset; publication preflight used exact annotated-tag REST dereference, preserving the original failure without changing global network settings.

## Completed public delivery and primary installation

All four public downloads are byte-identical to hosted assets and latest-release discovery confirms non-draft/non-prerelease v2.1.3. Archive SHA-256 remains `3f5f2bf6b4b4d0adfcd3fcac5522c3a3a558dca344c76c724594e45c099ad7ca`. Native targeted marketplace upgrade plus plugin add preserves the existing default-branch Git binding and discovers enabled/installed 2.1.3 from 2dc35ef. All 478 public-archive files match the installed cache. Eight synthetic installed methods pass, with doctor required failures 0 and five manual/live gates not_observed. All 23 unrelated plugin records and all marketplace bindings match immediate pre-update snapshots. Missing old-cache entries removed by native upgrade were restored before completion; all 519 prior 2.1.2 file hashes match, keeping current-chat Hook paths available.

Receipts include `public-verification.json`, `isolated-lifecycle.json`, `isolated-first-failure-disposition.json`, `primary-discovery-verification.json`, `primary-installed-verification.json` and `primary-old-cache-preservation.json` in the release evidence directory above. A separate documentation/state-only truth commit records actual delivery without changing tagged source or artifacts; no full native suite is repeated for these projections. HC8 remains blocked by the observed host contract and HC9 remains NOT RUN. Completion means the authorized release/install actions, not complete execution-directory isolation, live-model qualification or existing-chat activation. Codex itself was not upgraded or replaced.
