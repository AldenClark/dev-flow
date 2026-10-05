# Dev Flow 2.0.2 release progress

<!-- dev-flow-workstream-contract: v1 -->

- State: active
- Current slice: S1
- Terminal condition: final candidate qualified, pushed, published as stable 2.0.2 and primary installation verified, with unobserved loading limits explicit.

## Current truth

- Source candidate: `2.0.2`. Published stable remains `v2.0.0`; rollback target is `v2.0.0`.
- User authority: pre-release checks/documentation, commit, push, stable tag/release and primary local update.
- Five actual model functional journeys: WAIVED by explicit user instruction on 2026-10-05. No live-model spend or PASS is inferred.

Delivery state: commit=not-run; hosted_ci=not-run; cross_platform=not-run; independent_review=not-run; tag=not-run; artifact=not-run; publication=not-run; isolated_install=not-run.

## Evidence

- The three-pass DLP audit closed verified findings, exercised 73 audit tests and six credible isolated mutations, and passed 795 full-suite tests (794 pass, one native-Windows-only skip). Final audit source identity remains available; release version/projection changes require fresh candidate checks.
- Primary pre-update listing: installed/enabled 2.0.1. This is an installation observation, not current-session hot reload.
- Final 2.0.2 local regression passed: 795 tests in 82.993 seconds, 794 passes and one native-Windows integration skip, ResourceWarnings treated as errors. The complete log is `/tmp/dev-flow-202-full-suite.log`.
- Product-state, 15-Skill suite, knowledge, plugin, packaged security doctor, contracts, legacy-method data, RC.4/RC.5 static invariants, compilation and diff checks pass. Doctor has zero required failures and five manual/live gates. No protected DLP production/test/CI bytes changed since the final audit source manifest.
- Cumulative stable review, exact-SHA hosted platform checks and artifact/public/install observations are pending. The first extra flow-metrics command incorrectly supplied unsupported `--root`; this was a test invocation error, corrected using the public command help rather than a product change.

## Preserved candidate failure and repair

- Candidate `79c90025935fbe32095eeff4852f023a15746c2d` was committed and pushed. Its local two-build artifacts match, and isolated local install/discovery/156-file identity, three Hook controls and uninstall pass. Deterministic activation matches all 38 catalog and 80 large-task cases; these are routing observations, not model-journey outcomes.
- Exact-SHA CI run `37255846323` failed both Windows compatibility cells: three invalid-key errors on Python 3.11 and one missing-confirmation assertion on Python 3.14. Linux/macOS cells pass. The original native logs remain under the first delivery directory as `windows-first-real-3.11.log` and `windows-first-real-3.14.log`; no failed cell was removed or waived.
- Causal repair: raw `_read_limited` descriptors now select `O_BINARY` on Windows, preventing CRT CRLF/Ctrl-Z translation of a valid random 32-byte HMAC key. A fixed control-byte key must round-trip, issue and consume once; native Windows additionally proves that explicit text-mode reading changes the bytes. A test-setup mock initially affected all random IDs and failed schema validation; narrowing the mock to key creation repaired the harness. That setup failure is not the native product failure.
- The six-method cumulative independent review found no unresolved high-consequence issue and passed 78 focused tests before this platform repair. Its 35-file fingerprint and concrete controls are retained in `/tmp/dev-flow-2.0.2-cumulative-review-manifest.json`; the new minimal repair is independently rechecked separately. No public tag was created for the failed candidate.

## Hard conditions

| ID | Condition | Gate | Status | Closure/decision |
|---|---|---|---|---|
| HC1 | Final native suite and maintained projections validate | qualification | passed | 794 local passes / one native-Windows skip; required validators pass |
| HC2 | Stable-to-candidate requirements and consolidated static review close | qualification | open | Six selected methods; independent consequential review |
| HC3 | Exact candidate CI and applicable platform matrix pass | qualification | open | No 2.0.1 waiver inherited |
| HC4 | Hosted artifact, SBOM/checksum and attestations bind exact source | qualification | open | Reuse verified hosted bytes |
| HC5 | Public immutable stable tag/assets and isolated lifecycle observed | qualification | open | Public readback required |
| HC6 | Primary installed version/source/content verified | qualification | open | Installation and existing-session loading separate |
| HC7 | Five live-model functional journeys | qualification | waived | Explicit user exception for this scoped DLP patch |

## Evidence limits

Live account policy, other running chats and production outcomes remain not_observed. Current approval/credential stores are outside this release test. A public/install command response must be reconciled against actual remote/installed identity before being reported complete.
