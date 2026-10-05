<!-- dev-flow-workstream-contract: v1 -->
# DLP comprehensive audit progress

## Status

- State: closed
- Current slice: S6
- Terminal condition: verified consequential findings repaired, local tests/validators and independent review complete, remaining observation limits explicit.
- Updated: 2026-10-05

## Completed outcomes

- Baseline: clean worktree, repository and installed 2.0.1 engine bytes identical; existing 44 data-security tests passed before repair.
- First new engine regression run: 12 test methods, 30 failing subcases; raw synthetic-only failure log retained locally at `/tmp/dev-flow-dlp-engine-first.log`.
- Independently reproduced path punctuation/escape bypass, broad safe-name exclusions, structured authorization gaps, base64 candidate-size mismatch and malformed PEM timeout. The malformed 384 KiB PEM input exceeded 6 seconds before repair against a 5-second packaged Hook budget; independent repaired replay completed in 0.0253 seconds.
- The documented `apply_patch.command` source shape still reproduced the old Swift member-access denial through shell tokenization. Shell tokenization now applies only to canonical shell tool names; actual patch-command Swift and Rust decoys pass in both policy modes, while Bash relative-keyfile controls still deny.
- New approval tests independently reproduced malformed expiry/settings, unbounded record reads, concurrent capacity overflow and untyped I/O failures. Repairs preserve one-shot session/exact-scope binding and bound lock acquisition to 0.75 seconds.
- Hook/doctor input tests cover missing payloads, all valid JSON tool-value types, malformed/non-finite/duplicate/deep inputs and bounded diagnostic failures. Official Hook protocol readback on 2026-10-05 established the PostToolUse `decision: block` boundary; no live host activation is claimed.
- First strict workstream check rejected the combined current-slice label `S1/S2`; progress now names the actual integration slice `S3`. This was documentation structure, not a product-test failure.

## Current slice

S5-S6 are complete. Following the user's request for deeper rounds, ten further failure families were reproduced, repaired and independently rechecked; six credible mutations were caught at their intended behavior oracles. The complete final local suite and validators passed. No consequential candidate remains unresolved in the reviewed scope. Earlier source snapshots remain historical rather than final-source proof.

## Findings and repairs

| Area | Confirmed failure and consequence | Repair and regression oracle |
|---|---|---|
| Source assignments | Rust constructors and variable/member references were classified as literal secrets, including numeric suffixes, reference operators and optional/pointer access | Distinguish unquoted expressions from literals; source decoys pass while quoted values, wrapper literals and provider-token controls remain detected/redacted |
| Patch tool shape | The documented `apply_patch.command` field was shell-tokenized, reproducing the previous Swift member-access denial | Shell tokenization is enabled only for shell tool names; actual patch-command decoys pass in strict and personal modes, and real shell path controls still deny |
| Literal context | JSON object keys, quoted authorization headers and conventional environment/header names lost credential context | Context-aware scanning and redaction cover strings and nested JSON without serializing away field ownership |
| Placeholder scope | A placeholder word embedded inside a credential suppressed the whole match | Exempt only complete explicit placeholders; embedded-word credential controls remain blocked/redacted |
| Path scope | `dummy`/`fixture` names and template-name prefixes exempted private files; shell punctuation/escaping hid relative file arguments | Exact template/public-key exemptions and POSIX/Windows lexical token handling; safe files pass and private-file controls deny |
| Finding cap | Stopping at 64 findings could miss a later secret or return a partly raw result | Exactly 64 findings redact completely; overflow fails closed across strings, keys and nested values |
| Overlap | Dropping a wider overlapping match left a credential suffix visible | Merge the full overlap span and retain the strongest classification |
| Unicode normalization | Whole-text changes could reclassify an unrelated ASCII test token; matching duplicate values by content could hide a fullwidth token | Track direct matches by normalized position; both duplicate orders and expanding/composing prefixes are covered through engine and Hook output |
| Encodings and token formats | The base64 candidate bound was smaller than the supported decoded limit; additional documented GitHub formats were absent | Inspect one encoded layer up to the declared 16 KiB decoded bound, normalize decoded text and recognize fine-grained/stateless installation tokens |
| PEM matching | Repeated unclosed markers caused quadratic work; paired marker constants caused source false positives | Linear marker processing with plausible body recognition, including truncated and legacy-encrypted bodies; source constants pass and the malformed bundle completes within budget |
| Phone identifiers | Numeric epochs, dates, versions, IPv4 addresses and multiline counters were treated as phones | Require an international prefix, plausible groups or explicit phone context; retained labelled/international positive controls |
| JSON boundaries | Unsupported types, invalid Unicode, non-finite numbers, duplicate keys and recursion failures could escape structured error handling | Validate bounded JSON and emit fixed event-specific failures without raw input or tracebacks |
| Post-tool protocol | `continue: false` alone did not reject the original nested code-mode Promise result; the doctor did not require the blocking decision | Emit `decision: block` and verify that semantic field; a mutated Hook missing it must fail the doctor self-test |
| Approval storage | Oversized/malformed records, expiry types, concurrent capacity checks and untyped cleanup failures weakened bounded state handling | Bounded descriptor reads, authenticated typed schemas, exact expiry and serialized mutations with a 0.75-second lock budget; corruption/concurrency/failure controls pass |
| Approval exact scope | Prompt-marker whitespace stripping changed the scope of an otherwise exact retry | Remove only the framing newline; preserve original leading whitespace and verify successful one-shot confirmation followed by replay denial |
| Diagnostic robustness | Missing/invalid templates, malformed registry containers and oversized files could crash or consume unbounded input | Bounded readers and explicit failed checks; malformed packaging fixtures do not raise uncontrolled exceptions |

The review covered all production DLP modules, their new regression modules and real callers in the Hook, CLI and benchmark evidence redactor. No dependency was added. `dlp_policy.py` required no behavior change; its strict-mode and personal one-shot boundaries were exercised through existing and new tests.

## Verification history

- The first complete local suite after the initial repairs ran 768 tests: 767 passed and one native-Windows integration test was skipped. That result predates the six later review findings and is not the final-source result.
- Independent review added positional-normalization, additional source-reference, post-tool doctor-oracle, leading-whitespace confirmation, PEM-constant and IPv4/version regressions. The resulting four new audit modules contain 51 test methods and passed together after repair.
- Final source: `python3 -W error::ResourceWarning -m unittest discover -s evals -v` ran 772 tests in 83.470 seconds: **771 passed, 1 skipped**. The skip is `test_real_windows_job_closes_a_successful_parents_descendant`, explicitly requiring hosted Windows Job Object integration. Full output is retained locally at `/tmp/dev-flow-dlp-full-suite-final.log`; a SHA-256 manifest of the 12 tested production, contract, baseline and DLP test files is retained at `/tmp/dev-flow-dlp-verified-source-final.json`.
- Final product-state, Skill suite (15 Skills), knowledge index, packaged-plugin, data-security doctor, contract checks, Python compilation and diff-whitespace checks passed. Strict workstream validation is repeated after this evidence record closes.
- The first closure check reported `incomplete-terminal-slice` because the stable plan still had `ready` status cells. Only those three cells were advanced to `complete`; the plan's scope, outcomes and ownership stayed unchanged. The corrected closed workstream passes strict validation.
- The final doctor reports `valid_with_manual_gates`, with zero required failures. Unobserved Codex Hook trust and ChatGPT Work/ordinary-chat instruction and live self-test gates remain `not_observed`; local packaged checks do not promote them to PASS.
- Final clean-context independent review passed 51 new audit tests and 38 existing engine/policy/approval/Hook tests, then replayed original failures and additional encrypted/truncated PEM, normalization-coordinate, CRLF framing, replay and phone controls. The post-tool semantic negative control fails when `decision: block` is removed. Near-limit Unicode normalization with 64 findings completed in 0.882 seconds. The reviewer independently confirmed all 12 final-manifest hashes and found no remaining consequential issue in the reviewed frozen scope.

## Next

Complete S5's deeper counterexamples and S6's fault-sensitive verification. Installation, live-session qualification and release remain separate actions.

## Second audit: methods and outcomes

The user requested another bug-discovery pass and explicitly asked to use Dev Flow's risk methods. The three applied methods changed executable evidence rather than adding method-count gates:

- **Specification by example:** preserve confidentiality when the same value acquires insignificant wrapper whitespace, a reflowed/indented private-key body, a normalized field name or a supported structured phone representation; retain source-reference, marker-only and ordinary-counter controls.
- **Black/white oracle accounting:** derive detection/redaction and fail-closed rules from the handling contract, then challenge the actual wrapper, placeholder, context, state-parser and cleanup branches. Every new repair has a pre-fix failure. Test-discovery and execution are checked separately: an eight-subcase failing control showed that all four audit modules were absent both from the compatibility trigger inventory and from its executed module list.
- **Data lineage and provenance:** trace input through normalization/context projection/redaction to the model-visible result, and trace in-memory scope/session hashes through pending, confirmation, used markers, expiry and deletion. A real macOS permission failure checked the retained state and replay behavior after pending deletion failed, then verified recovery after permissions were restored.

| Confirmed failure family | Bounded repair and decisive evidence |
|---|---|
| Wrapper whitespace drops literal detection | Consume whitespace before the first quoted argument; unchanged literal remains detected while variable-reference controls remain allowed |
| A detected PEM prefix leaves an indented raw tail | Recognize the complete contiguous body across reflow/indentation; the already-C4 body continuation cannot survive redaction |
| Fullwidth sensitive JSON keys lose credential context | Normalize supported context keys and retain `obfuscated_secret` classification, including the no-one-shot policy boundary |
| Redaction labels re-trigger secret assignment | Exempt exact generated labels; repeated redaction stays stable, while a label with an appended raw synthetic token still triggers |
| Supported phone context differs across representations | Preserve Chinese field context and integer values in explicit phone fields; unrelated numeric counters and booleans retain their original values/types |
| Confirmation tombstones permanently exhaust cleanup | Reserve bounded issuance/consumption capacity; expired old pending/used overflow makes progress before denial and recovers on retry; replay remains denied |
| Unresolvable local state path escapes fail-closed handling | Translate path-resolution failures to typed state errors; Hook returns JSON deny, default mode becomes strict and no traceback escapes |
| Ambiguous persisted JSON relaxes policy | Reject duplicate keys and non-finite numbers; malformed settings become strict and malformed pending approvals are blocked |
| Platform CI never runs the new regressions | Register audit modules in both change-scope inventory and compatibility execution; the discovery/execution regression fails before and passes after repair |

First-failure logs remain under `/tmp/dev-flow-dlp-round2-*-first.log`, `/tmp/dev-flow-dlp-round2-*-first-failure.json` and `/tmp/dlp-engine-round2-first-failures.jsonl`. No real credentials or primary-profile state were used. The initial S4 workstream check rejected `active` as a slice status; only that cell was corrected to the supported `in-progress` spelling, and strict validation passed.

The second-round complete local suite ran **784 tests in 100.801 seconds: 783 passed, 1 Windows-only integration skip**, with ResourceWarnings treated as errors. The DLP audit modules now contain 62 methods, and the CI discovery module contains 5. Independent engine replay passed 82 confirmed-failure/control assertions, 2139 seeded composition/escaping assertions and 139 boundary assertions against freshly loaded source. These counts describe exercised relations, not a completeness proof. Independent approval/Hook replay passed 26 tests plus the original three failure probes, oversized pending/used recovery and native macOS permission-failure recovery. Validators, compilation and diff checks pass; installed/live and native Windows/Linux evidence remains unobserved.

A remaining cwd stress hypothesis was qualified once against the actual Hook: a 100000-segment synthetic cwd completed in 0.798 seconds with exit 0, JSON deny and no stderr, inside the packaged 5-second budget. The nonexistent generated path cannot be a native working directory, and host cwd is trusted metadata rather than tool-controlled input. This is a **NONFINDING**, recorded in `/tmp/dev-flow-dlp-round2-cwd-qualification.json` rather than promoted to a security claim.

Final source identity is retained in `/tmp/dev-flow-dlp-round2-final-source.json` (15 files); the full test log is `/tmp/dev-flow-dlp-round2-full-suite.log`. After the full suite, only the handling contract's capacity wording and its protected baseline changed; 10 doctor tests passed again, and all production/test/CI configuration bytes still match the full-suite snapshot. The closed workstream and maintained knowledge are checked again at closeout. No unresolved consequential candidate remains in the reviewed scope.

## Deeper sequence and representation audit (S5-S6)

The third pass used different failure mechanisms: actual Hook event sequences and state-model transitions, native permission faults and recovery, real historical-version issuance followed by current-policy consumption, equivalent JSON/shell representations, path ownership, and a bounded resource oracle. Expected behavior came from the supported contract and actual consumers, including the RFC 6750 Bearer alphabet, rather than from the matcher implementation.

| Confirmed failure family | Repair and evidence |
|---|---|
| A consumed pending record shadows a fresh identical tool request after unlink fails | Ignore pending records already represented in used; native permission recovery permits a fresh request and still rejects replay |
| Failed atomic replacement leaves an orphan that permanently poisons confirmation | Under the lock, discard only the exact private generated staging names; partial writes recover and unknown temporary files still fail closed |
| Historical prompt confirmations bypass newly hardened classification | Recheck strict/current-hard/test-declaration policy before consuming; a prompt actually issued by HEAD's older Hook is now blocked under current private-key detection, while an ordinary historical test-token marker still works once |
| A Bearer token containing `~` is only partly redacted | Cover the supported alphabet and assert both prefix and tail disappear through text, nested objects and serialized JSON |
| JSON separator LF/CRLF loses literal/header context | Recognize separator whitespace with unchanged literal values; json.loads supplies an independent equivalent-value oracle and source references/placeholders remain allowed |
| Static `--option=value` and environment-assignment file arguments evade path checks | Inspect their literal RHS in shell token context; equivalent bare paths deny and exact safe templates/public counterparts pass |
| Windows drive-relative sensitive paths evade lexical detection | Recognize drive-relative prefixes while keeping safe-template basename matching correct; this is lexical host evidence, not native Windows execution |
| A quoted credential filename in patch source is mistaken for actual file access | Select canonical framed patch targets, inspect all Add/Update/Delete/Move targets, and keep full-payload C4 scanning; source references pass while real targets, source secrets and unknown/ambiguous shapes remain denied |
| A single long public shell token exceeds the packaged five-second Hook budget | Bound each shlex read span to 65,536 characters and propagate InspectionLimit; aggregate short-token commands retain the existing larger text budget |
| A different filename inherits an exact safe-template/public-key exemption through a space-truncated match | Carry the whole-filename boundary from shell lexing or patch targets and evaluate exemptions against it; safe quoted RHS paths, directories with spaces and unsafe filename suffixes are covered together |

First-failure artifacts include `/tmp/dev-flow-dlp-round3-engine-regression-first.log`, `/tmp/dev-flow-dlp-round3-engine-first-failures.jsonl`, `/tmp/dev-flow-dlp-round3-engine-resource-results.json`, `/tmp/dev-flow-dlp-round3-state-stale-consumed-lookup-first-failure.json`, `/tmp/dev-flow-dlp-round3-state-temp-orphan-native-proof.json`, and `/tmp/dev-flow-dlp-round3-state-mixed-version-policy-first-failure.json`. The full-size public command exceeded six seconds before repair and was terminated; no inference is made about a live host's timeout disposition. A URI query/fragment hypothesis was not established against an actual supported file reader and is a **NONFINDING / contract limit**, not a reason to broaden arbitrary URI decoding.

The independent state model exercised **46 actual Hook subprocess events and 85 assertions**, covering session/scope mismatch, prompt/tool interleaving, exact expiry, mode switching and simultaneous confirmation/consumption. All three state repairs passed independent native/historical rechecks. Wall-clock expiry, cancellation text and mode switching do not promise monotonic elapsed-time or pending-revocation semantics.

S6's isolated mutation challenge has **six passing original-source controls and six mutants killed at their intended behavior oracles**, with no mutation-harness setup failures. Removed hard-policy checking, omitted replay tombstones, widened temporary-file cleanup, incomplete Bearer redaction, swallowed shell inspection limits and bypassed patch-body secret scanning are all detected. Sources and mutants are hashed; evidence is in `/tmp/dev-flow-dlp-S6-mutation-evidence.json` and `/tmp/dev-flow-dlp-round3-engine-mutation-results.json`. Neither repository nor installed source was replaced by a mutant.

Test-system failures remain separate: the initial mocked unlink fault missed because `/var` and `/private/var` were compared without canonicalization; the corrected setup and independent native permission reproduction establish the defect. One focused command named the nonexistent `EngineTests` class; it is **FAILED_TEST_SYSTEM**, not a product failure. The corrected selection ran 67 tests successfully. The first whole-filename repair's safe quoted-option control failed; the causal adjustment inspects an assignment's RHS and keeps non-POSIX incomplete quote fragments in raw-text mode. The corrected 64-test boundary selection passed; its first/fixed logs remain `/tmp/dev-flow-dlp-round3-path-suffix-*.log`.

The first S6 complete local suite ran **795 tests in 86.980 seconds: 794 passed and one native-Windows integration test skipped**, with ResourceWarnings treated as errors. A final drive-relative public-key control then exposed a new false positive in the path repair: drive removal applied to the template basename but not the SSH public-key check. Normalizing the same complete candidate before both checks repairs it; `/tmp/dev-flow-dlp-round3-drive-public-first.log` and the corrected nine-test path selection retain the evidence. The first full-suite log and source identity are `/tmp/dev-flow-dlp-round3-full-suite.log` and `/tmp/dev-flow-dlp-round3-first-suite-source.json`; a complete final-source run follows this last repair.

The complete **final-source** suite ran **795 tests in 89.881 seconds: 794 passed and one native-Windows integration test skipped**, with ResourceWarnings treated as errors. The audit modules contain **73 tests**. Product-state, 15-Skill suite, knowledge, plugin and contract validators passed, as did compilation and diff checking. Data-security doctor reports `valid_with_manual_gates`, zero required failures and five manual/live gates. Final test evidence is `/tmp/dev-flow-dlp-round3-final-full-suite.log`; the refreshed 15-file source/test/CI/contract identity manifest is `/tmp/dev-flow-dlp-round3-final-source.json`. All recorded source bytes remain unchanged after the final run.

The independent final engine recheck passed **371 relation assertions**, including **50 actual source-Hook subprocess events** with isolated synthetic state. It covered redaction equivalence, full filenames and safe counterparts, POSIX/Windows spellings, patch-body/target ownership and malformed fallback. The maximum one-MiB word now fails closed in 0.087 seconds; actual shell-tool Hook denials took 0.1089–0.1144 seconds. A 160-KiB aggregate of short tokens remains allowed. These are local timing observations, not a universal performance guarantee. All 15 manifest files matched and source was unchanged during the probe; `/tmp/dev-flow-dlp-round3-engine-recheck-results.json` and its reproducible script retain the checks. The parent also used the actual apply_patch tool on one disposable public-text filename to verify that target trailing whitespace is trimmed; this is a **NONFINDING**, recorded in `/tmp/dev-flow-dlp-round3-patch-parser-whitespace-proof.json`, and the created file was removed.

## Hard conditions

| ID | Condition | Gate | Status | Closure/decision |
|---|---|---|---|---|
| HC1 | Engine allows source decoys and detects/redacts protected synthetic content | implementation | passed | S1; 26 new engine audit methods plus existing controls |
| HC2 | Hook, approval and diagnostic failures remain bounded and fail closed | implementation | passed | S2; 25 new approval/Hook/doctor audit methods plus existing controls |
| HC3 | Independent review and complete local verification close | implementation | passed | S3; 771 local tests passed / 1 Windows-only skip; six review findings independently closed; validators pass |
| HC4 | Additional adversarial findings are dispositioned and repaired where confirmed | implementation | passed | S4; nine failure families fixed/rechecked; path pressure NONFINDING; 783 local passes / 1 Windows-only skip |
| HC5 | Deeper sequence/representation findings and regression-sensitivity challenges close | implementation | passed | Ten failure families repaired; six mutants caught; 371 independent engine assertions plus 85 state assertions; 794 local passes / one native-Windows skip |

## Active convergence checkpoint

None.

## Evidence limits

- Hosted CI, native Windows/Linux, installation and current-session loading: NOT RUN. The installed 2.0.1 cache has not been modified.
- The bounded lexical detector is not a complete language/dataflow interpreter, personal-data classifier or egress firewall. General runtime construction, arbitrary encodings/encryption and fragmented credentials remain outside its maintained contract. These are explicit scope limits, not inferred detection successes.
- Commit, push, tag, publication and deployment: NOT RUN. Product-state/version projections retain their existing delivery truth; this audit adds unreleased source changes only.
