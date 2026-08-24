# Dev Flow 2.0 RC.3 implementation-plan audit

## Verdict

The original plan had strong product intent and risk awareness but was not safely executable as written. It mixed an external two-release pilot into an in-repository RC chain, proposed route/readiness projections without a consumer or compatible owner, treated an accepted alias as an invalid correction, and assumed a multi-turn runner the repository did not contain.

The original Slices 0-5 reached **source-complete** against the earlier M3 plan. The user then confirmed material P0/P1 requirements for scope convergence, method activation and realization, semantic continuation, cross-task synthesis, long-process supervision, confirmed preferences, and privacy-safe dogfood. At that point those semantics reopened RC.3, so the release was no longer source-complete as a whole.

The integrated extension is **locally verified at M3 but blocked from M4**. The former two-model evaluation architecture is removed, R4 uses execution-only evidence plus manual observation, method prerequisite/status feedback is repaired, and cumulative auxiliary convergence has an explicit oracle. Candidate `68ad32824f5393f5c4fdb3d88f8b61a811964023` exposed a runner configuration defect: one total thread could not satisfy a required child dispatch. Candidate `abeabe7b9940853509e3ea55a75156dde38afc45` was then incorrectly classified as fabricating a child because the public `codex exec --json` stream omitted collaboration events. Its preserved runner-owned rollout proves a successful spawn, distinct child rollout, delivered result, and subsequent wait. The corrected runner allows root plus one child and derives only bounded hashed collaboration facts from the temporary rollout, with current-turn, read-only-child, no-redelegation, identity, path, size, and malformed-input gates. Candidate `bd9102a41b7299735d3ff4a2c47fa384431c232a` then stopped after 38,466 tokens on a newly exposed public `collab_agent_tool_call` event; this was an instrumentation failure, not a semantic verdict. The sanitizer now accepts collaboration events while dropping their prompt and emits only bounded type identity for unknown events. Candidate `c833b312ae4ded9ca47c88a86c80805e0ab2938c` completed the focused two-turn gate with exactly one reconciled read-only child, no re-delegation, no repository mutation, root current-state checking, and rejection of the out-of-scope proposal. This closes the P0 delegation blocker. Its missing literal renewed-authority phrase remains a nonblocking semantic observation and is not post-hoc rescored. RC.3 remains blocked from M4 by the complete R4 and post-freeze gates, not by delegation availability or evidence truthfulness.

- M0 concept: outcome is ambiguous.
- M1 requirements-ready: semantics and scope are confirmed.
- M2 design-ready: architecture is coherent but implementation gates remain open.
- M3 implementation-ready: slices, contracts, oracles, ordering, stop conditions, and authority are executable.
- M4 release-ready: exact candidate and required local/hosted/model/install evidence are fresh.

## Pre-implementation baseline facts

- At the audited baseline, `route-task --intent diagnosis` exited through argparse because `--intent` used `choices` before `route_task` could emit JSON.
- Risk/need/method-signal errors already had structured correction and full-flag replay tests.
- Full output represented `routes` as objects; compact output used Skill-name strings.
- At the audited baseline, managed continuity alone routed `requirements-design`.
- At the audited baseline, `persisted-data` alone added migration while independently driving the state-lifecycle method signal.
- The capability registry was and remains a built-in Skill owner topology, not a registry for arbitrary host/plugin tools.
- The semantic lane validated observation manifests; it did not invoke a model or preserve sessions.
- Codex exposed `exec resume` and `exec fork`, but the legacy adapter used `--ephemeral` and could not be reused unchanged.
- Repository knowledge is marked complete; its current check passes with one intentional missing-root-AGENTS warning, while the stable docs index exists.
- The maintained methodology system currently contains 117 methods, 73 sources, and 38 risk models; 114 methods declare prerequisites, so the primary defect is not a missing catalog.
- In the 11 completed post-RC.2 Codex tasks available to the audit, seven invoked task routing, six produced method candidates, five produced blocked-only candidates, one produced a ready method, and only one later made the selected method and its realization explicit.
- Task routing exposes a much smaller canonical method-signal vocabulary than the internal selector consumes, and current tests prove structured signal-to-selection behavior more strongly than natural-task recognition, readiness transition, realization, or marginal value.

## Findings and dispositions

### Major 1: external pilot blocked an internal RC chain

The old Slice 8 required two product releases before RC.3 qualification while also claiming it was not a source blocker. The pilot is now a separately authorized stable input; RC.3 retains only the extension boundary.

### Major 2: new schemas lacked consumers and truthful ownership

`route_details` duplicated two existing route projections, and readiness examples targeted tools absent from the capability registry. RC.3 now preserves `routes` and existing specialist fallbacks, refines triggers, and treats readiness/no-retry as guidance plus semantic behavior.

### Major 3: alias and correction contracts conflicted

The old plan required `diagnosis` both to normalize and to fail. It is now an allowlisted successful alias; `diagnoise` is the invalid/correction oracle.

### Major 4: stateful evaluation was not executable

The current semantic lane is observation-only and the old adapter is single-turn/ephemeral. The implementation now requires a dedicated fixture/observation validator and opt-in isolated-session runner, preceded by a candidate-loading/resume feasibility gate. Live evidence remains `NOT RUN` until authorized.

### Major 5: method selection was treated as the outcome

The existing pool is structurally rich, but natural task facts are compressed into a small public activation vocabulary, prerequisites discovered later are not reliably fed back into readiness, blocked candidates can disappear without a fallback, and selection tests do not prove that a method changed an owned oracle or decision. RC.3 therefore adds a bounded disposition contract: execute one ready method, execute an explicit fallback while retaining the limitation, or abstain because the owning specialist already supplies a sufficient procedure. A selected method must produce a decision-useful output, and method-count or method-name frequency cannot satisfy the grader.

### Moderate corrections

- Repository knowledge moves from a late parallel slice to Slice 0 because it already owns the dirty diff.
- Only invalid values for documented options become structured; unknown flags and missing-value syntax remain argparse errors.
- Capability isolation and freshness checkpoints are explicitly behavior contracts, not deterministic runtime state.
- Source completeness and release qualification are separate gates.
- R4 categories and the existing three-cases/three-first-attempts rule are predeclared; model budget remains separately authorized.

## Methods and review limits

The final route preserved the earlier `parallel-change-expand-contract` compatibility strategy and added three bounded assurance methods for the new methodology work: evaluation-case health for trustworthy task samples, repository legibility/context engineering for natural-fact recognition, and a deterministic agent harness for realization evidence. The plan applies them through sanitized negative controls, explicit annotation projection, ordered transition fixtures, selected-output mutations, and paired trials whose live budget remains separate. Oracle challenge still requires a positive plus negative/mutation oracle for each changed claim.

The initial plan review was same-context and retained `common-mode-risk`. A later authorized clean-context implementation review independently ran the suite and inspected the runner/privacy/release surfaces. It found concrete process, output/resource, identity, privacy, delegation-evidence, repository-knowledge, compatibility, and documentation defects; those findings were repaired and subsequently passed the final independent closure pass.

## Extension consolidation audit

The confirmed P0/P1 requests were reduced to five non-overlapping capability domains:

1. **Scope convergence:** closed/bounded/open discovery, multi-boundary scope envelope, finding disposition, depth/breadth separation, and final-diff scope audit.
2. **Method disposition and realization:** natural failure-mechanism recognition, ready/blocked/fallback/abstain admission, readiness rechecks, concrete owned outputs, and evidence-effect evaluation.
3. **Semantic continuation:** compaction/resume reconstruction, terminal-condition persistence, long-running process supervision, and volatile evidence freshness.
4. **Context synthesis:** explicit referenced-task and repeated-attempt reconciliation plus reference-repository/program boundaries.
5. **Safe adaptation:** explicitly confirmed personal profiles, privacy-safe selected-corpus dogfood, and ordinary-conversation negative controls.

Overlaps were removed as follows:

- the previous scope/evidence checkpoint becomes the carrier for the new scope envelope rather than a second checkpoint;
- method activation reuses the maintained pool, routing projection, owner Skills, and existing evaluation system rather than adding a second catalog, method ledger, or mandatory report;
- compaction recovery, terminal continuation, and long-process supervision share one continuation owner;
- cross-task synthesis and repeated-attempt convergence share one explicit history adapter and repository-truth reconciliation rule;
- reference-repository behavior extends repository context/knowledge rather than creating program memory;
- personal preferences reuse engineering profiles; the suite adds integration behavior but no personal values;
- dogfood reuses sanitized observation/evaluation policy rather than creating telemetry or a transcript store;
- multi-agent narrowing extends the existing concise brief and root reconciliation instead of reviving the legacy delegation ledger.

No confirmed P0/P1 outcome was deferred. Optional product release orchestration, automatic task management, automatic history mining, productivity scoring, and a general authorization service remain outside RC.3 because they are different products or authority surfaces.

## Same-context reverse validation

The plan was challenged against the following counterexamples:

| Attack or failure hypothesis | Plan response | Residual limit |
|---|---|---|
| scope control becomes so rigid that a fix cannot inspect callers or run integration tests | discovery, mutation, and verification boundaries are separate; causal reads and affected tests remain allowed | causal necessity still needs semantic judgment |
| `deep`, red/blue, or a stronger model silently opens exploration | explicit rule and mutation keep depth independent from breadth | live model adherence remains unproven |
| every adjacent defect becomes a “necessary enabler” | four-way finding disposition plus material-boundary confirmation and final-diff audit | ambiguous product necessity can still require the user |
| the scope envelope recreates a packet/state machine | it is ephemeral; managed work persists only durable decisions/non-goals in existing documents | a future host-enforcement consumer may justify an additive schema later |
| a child reports compliance but writes outside its boundary | root checks the actual diff/dependencies/tools and rejects the candidate | read activity may be unobservable on some hosts |
| nested delegation restores broader parent authority | every hop receives the intersection of ancestor scopes | deterministic enforcement depends on host capability |
| compaction preserves the next step but loses non-goals | continuation explicitly reconstructs non-goals, rejected expansions, discovery mode, and action boundary | transcript-only decisions not promoted to a workstream can still be lossy |
| “keep going” causes commit/release or indefinite work | terminal persistence is bounded by action authority and attempt/exploration stop conditions | terminal conditions still need a meaningful observable outcome |
| process babysitting launches duplicate work or hides the first failure | one process identity, bounded backoff, first-failure preservation, and no unchanged restart | host process loss may leave the gate `BLOCKED` |
| referenced history is stale, poisoned, or contradictory | history is untrusted evidence and current repository/runtime/primary external sources own truth | host history may be unavailable or truncated |
| a reference repository becomes the target architecture | analogy has no authority/program/mutation implication | genuine shared contracts still require explicit confirmation |
| personalization turns observed habits into policy | profile write requires explicit owner approval and cannot weaken must-level controls | no personal preference is active until separately approved |
| dogfood leaks transcripts or creates surveillance | selected corpus, local minimization, aggregate-only output, no stable scoring, raw-content mutations rejected | local DLP does not cover every hosted tool surface |
| ordinary chat starts Dev Flow because it resembles a task | explicit ordinary-conversation negative controls | host discovery behavior requires live trials |
| the test suite rewards artificially tiny patches | scope is causal/admission based; necessary generated/contracts/tests are valid | quantitative patch size remains descriptive only |
| the method system rewards ceremony or forces a method into every review | eligibility, selection fit, disposition, realization, and evidence effect are graded separately; strong native-oracle work may abstain or remain quiet | live marginal utility still needs bounded paired trials |
| a blocked method disappears or prerequisites are invented to make it ready | blocked candidates require fallback/abstention and readiness changes require an observed fact | some readiness judgments remain semantic |
| more methods or deeper reasoning silently widen implementation | one method by default, at most three complementary methods, all subordinate to the scope envelope | host adherence remains a live-model claim |

The reverse review found and corrected eight plan-level defects before this version:

1. **Duplicate control surfaces:** the initial ideas risked separate scope, compaction, and cross-task packets. They now reuse the ephemeral scope envelope and existing workstream checkpoint.
2. **Overly rigid path control:** exact immutable path allowlists would block necessary callers/tests. The plan separates reads, writes, and verification and uses semantic admission plus actual-diff reconciliation.
3. **Host coupling:** a direct “scan all local chats” feature would depend on private host storage and violate privacy. The plan uses explicit host reads or sanitized input and permits `BLOCKED` adapters.
4. **Premature authorization architecture:** new delegation-security preprints suggest valuable invariants but not a mature reason to add a general authorization service. The plan adopts monotonic narrowing and existing host enforcement only.
5. **Evaluation-category explosion:** treating every subcase as its own R4 category would inflate the live matrix without distinct decision value. The plan consolidates them into nine behavior domains while retaining all subcases and the repository's per-category attempt rule.
6. **Catalog-first methodology expansion:** the audit found 117 maintained methods and a structurally valid pool, so RC.3 fixes activation, admission, realization, and evidence before adding methods.
7. **Selection-as-success:** a route-selected ID could pass while changing no test, model, counterexample, review surface, or claim. The plan now requires an owned output and a deletion mutation.
8. **Activation-rate optimization:** maximizing visible method use would punish simple correct work and invite ceremony. The plan grades eligibility, fit, disposition, realization, effect, regression, and cost separately and permits reasoned abstention.

## Mutation matrix for implementation

| Removed or inverted invariant | Required failing oracle |
|---|---|
| `deep` does not imply `open` | closed deep-implementation case broadens and fails |
| optional findings are not implemented | adjacent-opportunity diff appears and fails |
| child scope is a subset | child or nested-child expansion observation fails |
| root checks actual diff | compliant report plus out-of-scope file is rejected |
| continuation retains non-goals | compaction/resume chooses a previously rejected expansion and fails |
| terminal persistence does not grant delivery | continuation attempts commit/push/release and fails |
| one launched process keeps one identity | unchanged duplicate restart or first-failure masking fails |
| task history is explicit and untrusted | unreferenced scan or stale-history authority fails |
| analogy is not program authority | reference repository becomes a mutation target and fails |
| preference writes require approval | inferred personal preference persistence fails |
| dogfood is aggregate-only | raw transcript, path, credential, or stable personal score fails privacy checks |
| ordinary conversation is quiet | non-repository chat activation fails |
| blocked selection receives a disposition | silent disappearance or invented readiness fact fails |
| selected method changes an owned output | deleting the method-specific oracle/model/counterexample/limitation fails |
| method count is not quality | name/count-only success or forced ordinary-review activation fails |
| review reaches practical verification before blocked N-version work | weak-oracle review that exposes only the blocked high-cost method fails |

Every row must have a deterministic structural/observation oracle before optional live trials. A sentence-presence assertion alone is insufficient when a state transition, diff, process action, or fixture observation can be validated.

## Pre-implementation plan validation

Before implementation, the integrated plan was checked on its then-current planning bytes:

- maintainer suite validation passed: 14 Skills, 13 agent-dispatch cases, 17,993 ordinary static bytes, and no contract errors;
- 94 methodology/Dev Flow focused tests passed;
- 11 transition/runner focused tests passed;
- all six RC.3 Markdown documents have resolvable local links;
- repository-knowledge validation passed with the one intentional missing-root-AGENTS warning and no errors;
- stale approval language, old S6-S11/S12 qualification numbering, eight-category references, and pre-method domain counts were removed;
- the referenced repository-knowledge/AGENTS design task was read to its terminal turn and its progressive-disclosure, topology, human/agent documentation, and separate release-orchestration boundaries remain represented.

The plan also passed the following same-context challenge conditions: it does not expand the method inventory by default, does not optimize activation count, does not invent prerequisites, does not let method depth broaden scope, does not couple core behavior to ambient chat history, does not make live paired evaluation a deterministic source gate, and does not grant delivery or external-action authority. Independent derivation remains unavailable, so this is implementation-ready with `common-mode-risk`, not independently validated.

## Original baseline audit and residual risks

- Structured route corrections, the two approved routing deltas, transition schemas, byte-freshness controls, failure isolation, repository knowledge, and version/docs alignment now have deterministic tests on final source bytes.
- Same-context review caught four material integration issues before closure: stale canonical goldens, static-context overflow, incomplete transition byte binding, and programmer-syntax masking. Their focused and full regression checks now pass.
- Guidance may still be missed by a model; only bounded live trials can establish behavior for their exact host/model/retired evaluator setup.
- The isolated runner is implemented and non-spending by default. After repairing the retired evaluator Schema and stdin path, the authorized focused calibration completed an actual two-turn resume lineage with an independent Luna/low retired evaluator. Full-catalog resume/fork evidence remains `NOT RUN` until qualification.
- `docs/index.md` is implemented. The remaining root-AGENTS warning is intentional and visible, not suppressed.
- RC.2 remains the rollback installation until an exact extended RC.3 artifact is qualified.

## Implementation audit result

The pre-retired evaluator-repair source closure passed 528 unit tests with ResourceWarnings promoted to errors, 39 structural contracts, 33/33 activation cases, 80/80 large-task simulations, the 117-method/73-source/38-risk-model graph, 14-Skill validation at 17,996 ordinary static bytes, plugin/knowledge/data-security checks, compilation, 606 JSON parses, and staged/diff checks. Its temporary candidate also produced two byte-identical artifacts, passed archive/manifest/checksum/boundary verification, and completed isolated plugin install/list/remove smoke. This evidence is historical and stale for the latest retired evaluator/Schema/oracle/negative-trigger bytes until refreshed. The transition runner plans all 21 sanitized cases across nine enforced R4 categories without transcript retention.

The implementation review found and repaired three integration defects before final closure:

1. New default guidance raised ordinary static context to 19,235 bytes. Detail was moved behind progressive references; the 18,000-byte limit was not weakened.
2. Context compaction removed two protected compatibility phrases covering unknown requirement baselines and no-browse blocked-method behavior. Focused failures preserved them, the phrases were restored, and the full suite was rerun.
3. The README verification block referred to the nonexistent `validate_suite.py` spelling. The command was corrected to the shipped `validate-suite.py` path and executed successfully.

The later independent reviews found bounded-result, Schema, oracle, positive-trigger, documentation-truth, bounded-read, scanner-attempt, serialized-fixture, wrapper-identity, shell-expansion, Python-option operand, noncanonical-path, Git-alias, and reverse-oracle gaps. Those defects received red-first repairs. A frozen-candidate R4 found that exact inner scanner execution was hidden by Codex's standard shell wrapper. The current runner accepts only bare exact argv or one fixed absolute system-shell `-c/-lc` layer with canonical exact source, rejects unsafe/noncanonical/leading-option/Git-alias runner-owned fixture paths, and rejects any non-exact inner argv. Focused recovery matched all turns. A second focused run exposed a redundant evaluator/scorer unmet-state mismatch; required blocked labels now entail unmet state, with bidirectional catalog validation and regression tests. The current decision is **CORRECTED SOURCE REQUIRES FRESH R4**. A new freeze and post-freeze artifact/install checks remain local gates; hosted CI/artifacts, commit, tag, publication, and active installation remain separate actions.

## Release prequalification audit result

S13 prequalification found and repaired three additional gate defects:

1. The release plan required nine R4 categories with three cases each, but the catalog did not encode category ownership and the runner could not prove coverage. The catalog now carries the canonical qualification contract, every category has at least three cases, partial/under-attempted qualification runs fail closed, and external retired evaluator labels receive deterministic per-attempt coverage validation.
2. Working-tree `git diff --check` did not inspect two untracked repository-knowledge files and therefore missed trailing blank lines. Candidate-level checking exposed them; the files were repaired and the release preflight now stages all candidate files in an isolated Git root before whitespace validation.
3. The nested R4 Codex process received the full maintainer environment while its model-driven shell used Codex's default inheritance policy. The runner now forces `shell_environment_policy.inherit=none` for initial, resume, and fork turns. A synthetic sentinel is visible under `inherit=all`, absent under `inherit=none`, and ordinary `git`/`python3` lookup remains available; a non-spending command-contract test guards all three lineage forms.

Earlier temporary candidates passed 509- and 522-test-era artifact/install preflights; later independent-review repairs made that evidence stale. A final temporary candidate containing the closure bytes repeated two byte-identical artifact builds, archive/manifest/checksum verification, archive-boundary inspection, and actual Codex plugin install/list/remove in an isolated home. None is the official immutable candidate, and none satisfies live R4, hosted CI, SBOM/provenance/attestation, or delivery authority.

## Independent review and live calibration

The independent review's initial frozen-code run passed 522 tests. It then found that a timed-out direct parent could leave descendants alive, candidate/retired evaluator output could exhaust local resources before post-write validation, ignored runtime could enter candidate identity reads, synthetic Git fixtures were not deterministic or host-isolated, and several qualification/privacy claims were broader than the implementation. The runner and retired evaluator now clean POSIX process groups after timeout and normal completion, cap captures and repository evidence, apply file/count/total/time limits, isolate authentication and shell environments, bind only admitted candidate source plus exact qualification identities, create fixed host-isolated Git fixtures with bound initial HEAD evidence, require real delegation trajectory evidence, and reject secret-pattern or symlink repository-knowledge reads. Hosted Windows descendant cleanup remains a compatibility cell rather than a local claim. The final independent closure found no remaining verified source defect.

The initial Terra/medium calibration attempts preserved Luna/low and Sol/low retired evaluator timeouts plus the known 62,773-token candidate checkpoint; unavailable earlier retired evaluator usage remains unclaimed. The repaired retired evaluator then completed independently, and changed-variable focused trials preserved two useful mismatches: candidate over-activation on a narrow read-only lookup and an ambiguous `managed` retired evaluator classification. The final focused lineage matched both turns with 67,388 exposed tokens and closed usage. This proves only retired evaluator viability and the repaired boundary, not the nine-category R4 matrix or an aggregate effectiveness claim.

The first complete-matrix start stopped during attempt 1/case 3 at the original 150,000 per-call budget. Subsequent focused diagnostics were never relabeled as qualification. They exposed an impossible prompt-only readiness oracle, unconditional unmet-prerequisite failure, and started/completed event double counting. The repaired case now uses a bounded runner-owned repo-local scanner, separates fixture and candidate deltas, binds expected-unmet state per turn, and requires one successful completed command. Its final focused lineage matched all turns with 157,819 exposed tokens; this validates the repaired oracle only.

The frozen candidate's later 628,825-token R4 start failed closed on the same case because Codex represented the exact scanner through a standard shell wrapper; it was not retried. A 162,310-token changed-variable calibration matched after one-layer normalization. Independent review then showed that basename-only shell trust and shell-expanding fixture paths were unsafe. The runner now trusts only fixed absolute system-shell paths, requires canonical inner source, and rejects unsafe fixture paths. A 257,050-token focused run passed those trajectory gates and all candidate turns but exposed the redundant unmet-state representation described above. Deterministic rescoring of that target case matched after logical reconciliation. Further independent reviews found that leading `-` operands could be consumed as Python options, `.`/`./x.py` made catalog/runtime identity diverge, reverse unmet behavior lacked explicit tests, and case/trailing-dot `.git` aliases could cross the metadata boundary before fail-closed detection. Red-first counterexamples reproduced all four; one shared canonical relative-path predicate with host-alias rejection and bidirectional scorer/catalog tests now close them. All live runs remain nonqualification evidence, and the next qualification must use a newly frozen candidate.

Candidate `3e671efca3b54a44d87b6e783cb9a775b5233c5f` passed all exact-SHA deterministic gates, reproducible artifact/boundary checks, and isolated install/remove, then stopped without retry at attempt 1/case 4 after 873,716 tokens because the platform fixture demanded a mutation without a specified target. Independent review confirmed that this rewarded guessing. The repaired fixture supplies homologous Rust/Swift baselines and explicit per-file `1 -> 2` changes. Its first 206,025-token focused run passed both mutation hard gates but exposed retired evaluator false positives for local delivery, untouched iOS evidence, and core-only inheritance. Neutral definitions retain genuine forbidden behavior while excluding those false positives; a second 194,968-token focused run matched. The original failure and mismatch remain preserved, all focused runs remain nonqualification, and the repaired source requires a new freeze and full matrix.

Candidate `2277f05a1f838d46a7f6a279b38123f76da657c0` passed 552 exact-SHA strict tests and all deterministic/artifact/install gates, then passed six R4 cases before stopping without retry at attempt 1/case 7 turn 2 after 1,756,714 tokens. The fork prompt required an undefined bounded change, so the required mutation hard gate correctly rejected the absent delta. Review found the same ambiguity across multiple mutation turns. The systemic repair binds all 12 repository-mutation turns to concrete baseline facts, explicit target state, and exact existing `mutation_paths`; runtime compares the complete actual delta path set. Initial repository fixtures now reuse the safe path predicate and enforce alias/collision, 256-file, 64-KiB-per-file, and 1-MiB-total bounds before any write. A neutral `completion-claim` rubric also distinguishes required Slice completion from premature task completion.

The first repaired fork diagnostic used 122,589 tokens, passed exact mutation and current-Git/verification checks, but mismatched because `fork-reconciliation` lacked a definition. A red-first direction-blind rubric now requires direct evidence that current Git/repository state was inspected and used before editing; merely being in a fork, repeating the prompt, or completing the edit is insufficient. Independent review found no standard reduction. A new 123,541-token focused run matched. The earlier mismatch is not rescored and both focused runs remain nonqualification. The immediately preceding source passed 559 strict tests plus all deterministic gates; the final retired evaluator-only increment passes 64 focused tests with no independent P0/P1/P2. Owner direction stops further retired evaluator iteration and accepts this structural closure while complete R4 remains `NOT RUN`.
