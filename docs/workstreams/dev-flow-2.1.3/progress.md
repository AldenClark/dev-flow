# Dev Flow 2.1.3 release progress

<!-- dev-flow-workstream-contract: v1 -->

- State: active
- Current slice: S1
- Source candidate: `2.1.3`
- Terminal condition: accepted patch committed/pushed, public stable assets verified, isolated lifecycle and primary local installation observed; preserve current-host and model limits without claiming complete functional qualification.

## Current truth

- Published stable/workspace base: v2.1.2; rollback target: v2.1.2.
- User authority on 2026-10-27: current cwd patch as 2.1.3, commit, push, formal release and primary local Dev Flow update. No Codex upgrade or alpha installation, real sensitive-data mutation or additional model campaign.
- Delivery observations remain action-specific. Source tests do not establish current-chat loading or runtime execution-directory isolation.

Delivery state: commit=not-run; hosted_ci=not-run; cross_platform=not-run; independent_review=passed; tag=not-run; artifact=not-run; publication=not-run; isolated_install=not-run.

## Accepted implementation and sensitivity

Previously a relative `event.cwd` was resolved against the Hook process directory and could consume confirmation issued for an absolute execution directory. The Hook schema and direct canonical_scope boundary now require non-empty native absolute paths without NUL. Missing, relative and URI values fail closed before marker-only confirmation or scope mutation. Absolute-path normalization, complete payload, session binding, TTL, hard policy and locked single consumption are preserved. No remote/workdir/process fallback is added.

Seven new native methods cover same input/different cwd, one correct consume, changed Hook process/turn, invalid metadata without issuing or advancing state, delayed Bash results and opaque remote MCP arguments. The first regression log is preserved, including correction of an initially wrong redaction-label expectation; the corrected pre-fix run exposes26 cwd assertion failures across7 methods. Post-fix all7 pass, and the three related modules pass84 tests in7.976 seconds with ResourceWarnings treated as errors. Unchanged runtime bytes retain that evidence; final release/version bytes receive final native and hosted qualification below.

## Real current-host observation

App26.1021.31345/build21828, CLI0.164.0-alpha.11.1, binary SHA-256 `a04752e4d46a4d89e53e6f61c59c5349a638c8ce172ffbf391fd482b4d902a4e`; native code signature validates and predates the public PR merges. Exact embedded source ancestry is not exposed, so behavior is observed directly. The same binary ran isolated app-servers with owned CODEX_HOME roots and a loopback mock Responses provider: no online model inference or primary settings changes. Only the three owned recorder hooks were reviewed/trusted using the native config API.

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
| HC3 | Exact-source semantic and five compatibility cells | qualification | not-run | Hosted checks pending |
| HC4 | Hosted archive, SPDX and bound attestations | qualification | not-run | Artifact workflow pending |
| HC5 | Immutable public stable tag/four exact assets | qualification | not-run | Publication pending |
| HC6 | Isolated public install/discovery/controls/uninstall | qualification | not-run | Public-source lifecycle pending |
| HC7 | Primary identity, controls and unrelated-plugin preservation | qualification | not-run | Authorized update pending |
| HC8 | Complete execution-cwd isolation on current real host | qualification | blocked | Host emits old metadata; retained external limitation, no guessed fallback or completeness claim |
| HC9 | Five live-model journeys and existing-chat loading | qualification | not-run | No additional model campaign or loading inference |

Evidence is retained under `/Users/ethan/Documents/Codex/2026-10-27/dev-flow-2.1.3-release-v9yf3ema`, including copied implementation failures/results and real-host raw Hook/RPC/mock receipts. Full regression, source identities and external action results will be recorded as they occur. Earlier valid tests are not rerun without an affected claim.

## Cumulative review

A clean-context P4 reviewer inspected the public v2.1.2-to-candidate runtime/test/policy delta and traced schema, marker confirmation, canonical scope, keyed matching and locked consume. No consequential finding remained. Six conclusions: traceability matches both guards to7 methods; impact stays within metadata and existing consumers/state; paired examples distinguish changed cwd/input and once-only reuse; interactions retain host prompt vs tool directory separation, hard policy and PostToolUse non-consumption; black/white evidence preserves pre-fix26 failures and final84 passes; assumptions explicitly retain native-platform normalization and unobservable older-host/remote directory truth. No extra dependency, registration, migration or inferred approval action is introduced. Parent-owned version/delivery projections are outside that review and receive maintained validators.

## First final-native and projection check

One full local regression ran848 methods in92.952 seconds:845 passed,one native-Windows-only case skipped and two product-state/doctor assertions failed because the new release heading/rollback wording and governance navigation omitted required maintained projections. The first full log and validator result remain preserved. Only those documentation projections were restored; the two affected native tests and product-state/workstream/diff checks are rechecked. No runtime, test oracle or safety rule was weakened and the successful full-suite cases are not replayed locally. Exact-source CI will qualify all final candidate bytes.
