# Dev Flow release model

This runbook selects evidence from the changed surface. It separates implementation, verification, release readiness, artifact construction, publication, and installation; none implies another.

## 2.0.0-rc.7 personal-assistant hardening candidate

`v2.0.0-rc.6` is the latest public immutable RC tag. `v2.0.0-rc.6` is the rollback target for `2.0.0-rc.7`. The RC.7 source candidate turns the lifecycle into a thin adaptive guide, strengthens every professional Skill and its discovery contract, keeps durable results in canonical repository owners, expands project-native test-system guidance and sensitive black/white-box evidence, and removes the obsolete reviewer-spawn authorization gate without widening any descendant action boundary. Recheck of repaired post-commit findings is pending.

Delivery state: commit=passed; hosted_ci=not-run; cross_platform=not-run; independent_review=failed; tag=not-run; artifact=not-run; publication=not-run; isolated_install=not-run.

## 2.0.0-rc.6 personal-assistant hardening release

`v2.0.0-rc.6` is the latest public immutable RC tag. `v2.0.0-rc.5` is the rollback target for `2.0.0-rc.6`. RC.6 separates published identity from current workspace state, makes doctor distinguish cached plugin bytes from CLI registration, loaded identity, and Hook activation, and moves repeated/comparative model work to independent Dev Flow Bench research. These R2 changes required final local semantic evidence, the applicable hosted compatibility matrix, isolated fresh install/uninstall, exact-SHA artifact evidence, tag, push, and public prerelease verification; all passed for candidate `2d1cb4be8d97433511e6fffb032d2e505deaf0d9`. The final static review is same-context; independent clean-context review is waived because no separate reviewer authority was granted. No live model trial was run or required for this candidate.

## 2.0.0-rc.5 personal-assistant hardening release

The canonical product state identifies the published source as `2.0.0-rc.5` and the current workspace separately as development based on `v2.0.0-rc.5`; later workspace bytes never inherit RC.5 delivery evidence. Source implementation contracts the public CLI and compact route, adds product-state validation, read-only diagnosis, opt-in privacy-safe outcome observation, an always-on untrusted-content boundary, and real user-event DLP confirmation. RC publication uses affected semantic smoke. Stable publication uses the stronger but bounded stable-validation procedure below; Dev Flow Bench is independent research and is never a release tier or gate.

RC.5 completed affected privacy, compatibility, negative-control, product-state, and static-context checks. One full local regression exposed a narrow phrase-contract failure; after that repair only affected checks were rerun, and the exact final commit passed the hosted full semantic job. Publication also preserved one lightweight methodology-backed static review, one bounded attempt for the directly affected semantic case, the applicable hosted matrix, and exact-commit artifact, attestation, isolated-install, tag, and public-prerelease evidence. The semantic smoke matched its first turn; its terminal turn still omitted explicit final-check and final-limit evidence, a recorded RC residual rather than a semantic pass. The former repeated-model stable gate was retired after RC.5; the residual must be reconsidered during cumulative stable review instead of forcing a catalog rerun. `v2.0.0-rc.5` is the latest public immutable RC tag. `v2.0.0-rc.4` is the rollback target for `2.0.0-rc.5`.

## 2.0.0-rc.4 convergence-and-operations release (historical)

RC.4 added stateless route comparison, managed-workstream checking, host-local resource coordination, test-system integrity ownership, privacy-safe dogfood v2, and separate semantic-runtime/qualification-execution identities. Its annotated `v2.0.0-rc.4` tag is the RC.5 rollback point. Qualification waivers and exact release evidence remain recorded in the RC.4 workstream; they are not inherited as RC.5 proof.

## 2.0.0-rc.3 transition-hardening release (historical)

The RC.3 source manifest identified `2.0.0-rc.3` at that historical release point. It changed deterministic routing and model-facing transition/failure/freshness guidance, so publication was R4 even when local source gates passed. The opt-in runner in `evals/run_transition_trials.py` exercised isolated candidate loading plus resume/fork lineage, defaulted to a non-spending plan, and never graded its own responses. Actual execution required separate model-budget authorization; bounded first-attempt evidence was assessed afterward through a manual observation manifest and the public transition lane.

RC.3 source-completeness requires final local deterministic/process/plugin/documentation/security checks. Frozen candidate `99b5831c3d1890a84700aac6baa4a0cb0b33c495` completed the separately authorized three-attempt R4 execution with 144 turns, 9,092,076 tokens, closed usage, unchanged identity, and no mechanical failure. Same-context manual assessment found two bounded semantic gaps: delegation reconciliation omitted an explicit renewed-authority request in all attempts, and reference-repository comparison was absent or weak in two attempts. The version owner explicitly accepted these residual risks and authorized release; the gaps remain `WAIVED`, not passed. Exact-SHA hosted evidence, artifacts, installation, tag, push, and publication remain action-specific delivery gates. `v2.0.0-rc.2` remains the rollback installation.

## 2.0.0-rc.2 activation-hardening release

RC.2 completed the authorized R4 model-semantic gate before delivery. A preserved 33-attempt broad matrix covered implicit positive activation, explicit advanced activation, and negative controls; it exposed confirmed-U1 downclassification and missing-kernel trigger failures instead of being waved through. After repair, three distinct confirmed-U1 continuation cases each passed three independent first attempts, and U1 clarification, U1 confirmation, and managed-continuity adjacency cases also matched. This satisfies at least three distinct cases per affected category and at least three independent first attempts per case. Safety/authority stayed a separate hard gate, no aggregate score was produced, and total exposed tokens stayed below the authorized ceiling. Commit, tag, push, installation, publication, and release remain action-specific and require their own result evidence.

## 2.0.0-rc.1 authorized minimal path (historical)

The user froze features and selected a breaking 1.x cut for RC.1. This candidate requires only aligned source/version documentation, focused deterministic checks, one bounded semantic activation pass, an annotated `v2.0.0-rc.1` tag, and push of `main` plus the tag. Push-triggered hosted CI is useful asynchronous feedback but is not a tag gate. The artifact workflow, SBOM/provenance attestations, 1.x upgrade/rollback matrix, active-profile installation, and real-task soak are explicitly deferred and must not be inferred as passed.

The general tiered model below remains available for later stable-release or organizational choices; it does not retroactively add gates to RC.1.

## Principles

- Run the full semantic suite once for an exact commit SHA. Do not repeat it in the release-candidate workflow.
- Run platform/version compatibility only for code whose behavior can vary there.
- Build, SBOM, checksum, provenance, and attestation evidence belongs to the immutable release artifact.
- Flow Activation Coverage is for material model-semantic branch behavior, not productivity or effect measurement.
- Publication, tag creation, push, release creation, and installation always require their own authority.
- A missing hosted, device, signing, account, deployment, or public-network result is `NOT RUN`, never an inferred pass.

## Release tiers

Select the highest applicable tier. Higher tiers add only evidence relevant to the changed surface.

| Tier | Typical changes | Required evidence before publication |
|---|---|---|
| R1 standard | documentation, Skill wording, routing fixtures, ordinary deterministic logic | focused local checks, one full semantic CI job, affected focused compatibility cells |
| R2 runtime | Hook, installer, process, path, shell, host integration, cross-platform behavior | R1 plus full compatibility lane and isolated install/uninstall smoke; upgrade/rollback only when compatibility changed |
| R3 artifact/security | builder, archive format, workflow permissions, SBOM, attestation, confidentiality/security control | R1/R2 as applicable plus deterministic artifact negative tests, candidate SBOM/checksum/provenance/attestation, security-specific checks |

Examples:

- Correcting a typo is R1 and does not rehearse marketplace rollback.
- Changing Hook registration or `data_security_hook.py` is R2/R3 as applicable; it needs focused platform and confidentiality tests plus isolated runtime smoke, not an automatic full model acceptance run.
- Changing `tools/build_release.py` or attestation permissions is R3.
- Changing the model-facing meaning of direct/managed selection uses affected deterministic checks and bounded semantic acceptance even when the code diff is small.
- A mixed change uses the union of applicable evidence, not every gate ever created by the project.

## Evidence lanes

The ordinary CI workflow has two lanes:

1. `semantic`: Ubuntu 24.04/Python 3.14 runs the full unit suite, structural contracts, shipped legacy-data validators, plugin/suite/data-security checks, compilation, and clean-tree check once.
2. `compatibility`: a focused matrix across Ubuntu, macOS, Windows and Python 3.11/3.14 is activated from `governance/compatibility-surfaces.json` and runs platform-sensitive agent dispatch, CLI/preflight, DLP Hook/state, engineering-profile, outcome/doctor, product-state, installer, repository-knowledge, resource, and isolated runtime-lifecycle tests once per cell. It contains no repeated diagnostic loop.

The manual release-candidate workflow is a third lane. It fetches and binds the approved exact SHA, creates the deterministic source archive, verifies it, generates and validates SPDX 2.3 SBOM data, finalizes checksums, creates provenance/SBOM attestations, and uploads immutable candidate evidence. It intentionally does not rerun semantic CI.

## Candidate sequence

1. Classify the changed behavior and choose the smallest affected tests plus one practical negative control.
2. Run those checks while repairing. See all failures in the affected batch before editing again; rerun only failed or newly affected checks.
3. When the candidate is ready, freeze a clean full commit SHA and run the full local suite once.
4. Review the final diff once through the integrated task route. Apply at most three ready starter methods selected from observed risks; each must yield a concrete finding, counterexample, changed oracle, or explicit no-finding conclusion. Do not count method names or rerun tests as method evidence.
5. If model-facing guidance changed in an RC, preserve one bounded first attempt for each directly affected semantic case. A mismatch returns to affected repair; it does not start a complete catalog.
6. Push only with authority and require the exact SHA's semantic job plus applicable compatibility cells.
7. For installer/runtime changes, exercise fresh install/uninstall in an isolated temporary Codex home. Add prior-version upgrade or rollback checks only when that compatibility changed.
8. Dispatch the RC workflow for the exact merged SHA and matching source version, then download and verify archive, manifest, SBOM, checksums, and attestations.
9. Create/push the tag and publish only when those exact actions are authorized, then verify the public release and isolated installation.

Never rewrite or reuse an RC tag. Any changed byte requires a new commit and candidate identity.

After publication and isolated install verification, record external truth in a separate current-truth commit on the default branch: set the published-source phase to `released`, advance `published.latest_rc` to the immutable RC tag, retain the previous known-good tag as `compatibility.rollback_target`, and record each delivery result without rewriting the release tag. If later implementation begins, set the separate workspace record to `development` from that published tag and bind it to its own workstream; those bytes have no publication claim. The tagged candidate remains the exact pre-publication byte snapshot; the follow-up commit is the canonical current state and does not retroactively alter its artifact identity.

## Local artifact check

For an R3 change, two local builds can establish deterministic behavior before hosted attestation. Use absent output directories:

```bash
git rev-parse HEAD
python3 tools/build_release.py build \
  --root . --output dist-a --version 2.0.0-rc.7 --commit FULL_COMMIT_SHA
python3 tools/build_release.py build \
  --root . --output dist-b --version 2.0.0-rc.7 --commit FULL_COMMIT_SHA
cmp dist-a/dev-flow-2.0.0-rc.7.tar.gz dist-b/dev-flow-2.0.0-rc.7.tar.gz
cmp dist-a/release-manifest.json dist-b/release-manifest.json
cmp dist-a/SHA256SUMS dist-b/SHA256SUMS
python3 tools/build_release.py verify \
  --artifact-dir dist-a --expected-version 2.0.0-rc.7 --expected-commit FULL_COMMIT_SHA
```

Determinism is asserted within the pinned environment. Promotion reuses attested bytes instead of rebuilding on another zlib/toolchain version.

## Hosted candidate

After applicable exact-SHA CI is green:

```bash
gh workflow run release-candidate.yml \
  --ref main -f version=2.0.0-rc.7 -f expected_sha=FULL_COMMIT_SHA
```

The workflow has `contents: read`, `id-token: write`, and `attestations: write`. It has no release-publication permission. After download:

```bash
python3 tools/build_release.py verify \
  --artifact-dir dist --expected-version 2.0.0-rc.7 --expected-commit FULL_COMMIT_SHA
gh attestation verify dist/dev-flow-2.0.0-rc.7.tar.gz \
  --repo AldenClark/dev-flow
gh attestation verify dist/dev-flow-2.0.0-rc.7.tar.gz \
  --repo AldenClark/dev-flow \
  --predicate-type https://spdx.dev/Document/v2.3
```

The SBOM must be SPDX 2.3, name `dev-flow`, contain files, identify the root package and version, and carry a document namespace. Structurally valid but empty inventory is failure.

## Stable validation and semantic acceptance

Use [evaluation-suite.md](evaluation-suite.md). Deterministic Flow Activation Coverage runs first. An RC whose model-facing guidance changed runs one bounded first attempt over only the directly affected semantic cases. This is a regression check, not a population or statistical claim.

Before a stable release, perform four meaningful checks without inventing a new process ledger:

1. Review every maintained requirement and behavior change from the previous public stable to the candidate. Reconcile requirements, decisions, implementation, tests, and current documentation; report dropped, contradicted, or partial behavior in one consolidated findings list.
2. Apply six compact static methods in one pass: traceability/V-model, change-impact graph, specification by example, feature-interaction analysis, black/white oracle accounting, and assumption mapping/premortem. Add at most two risk-specific methods when the actual diff justifies them.
3. Exercise one bounded first attempt for each real functional journey: ordinary bugfix, material semantic change with requirement confirmation, diagnose-fix-verify, unrelated local MCP isolation, and continuation without inferred delivery authority. Rerun only failed or newly affected journeys.
4. Run the complete deterministic suite once after focused repairs pass, plus applicable artifact, compatibility, security, and isolated-install evidence selected by R1-R3.

The stable process does not require a complete repeated model catalog or a universal independent-review ceremony. Independent review is risk-triggered; if one is attempted and fails or blocks, it cannot be ignored.

For an affected RC smoke, use the supported Bench surface with only the relevant case selected:

```bash
python3 benchmarks/dev_flow_bench.py plan benchmarks/suites/dev-flow-regression.json --case CASE_ID
```

Live execution still requires separately approved model spend, `run --execute --acknowledge-model-spend`, and explicit bounds. The internal executor has no standalone CLI or release authority. Bench writes bounded evidence and ends at `awaiting-assessment`; grading remains separate and same-context assessment reports `common-mode-risk`.

Dev Flow Bench is the supported research surface for repeated or comparative model studies. It is independent of product state and release commands, defaults to a non-spending plan, separates regression/capability/safety-authority suites, carries explicit case health, and never emits an aggregate release score:

```bash
python3 benchmarks/dev_flow_bench.py audit-suite benchmarks/suites/dev-flow-regression.json
python3 benchmarks/dev_flow_bench.py plan benchmarks/suites/dev-flow-capability.json
```

Earlier RC.3 candidates preserved three first-attempt failures: scanner shell-wrapper recognition, an undefined platform mutation target, and an undefined fork mutation target. Their diagnostics led to exact command normalization, concrete mutation baselines/paths, bounded fixture validation, expected-unmet consistency, and current-state fork reconciliation. The former two-model evaluation mechanism was removed completely because it added cost, classification defects, and an auxiliary tuning loop. None of its results qualifies the corrected bytes, and no historical failure is rescored.

The historical R4 catalog contained 22 cases across nine categories and added an explicit auxiliary-convergence boundary. After two auxiliary repairs without primary-outcome progress, the current rule is still to simplify, defer, or block rather than tune the evaluator again. Candidate `99b5831c3d1890a84700aac6baa4a0cb0b33c495` supplied RC.3's then-required complete three-attempt execution; its manual semantic exceptions remain historical owner waivers and do not define current release policy.

Corrected candidate `68ad32824f5393f5c4fdb3d88f8b61a811964023` stopped its first qualification attempt after 2,434,991 tokens because the runner allowed only one total session thread while a catalog case required child dispatch. A later focused run against candidate `abeabe7b9940853509e3ea55a75156dde38afc45` was initially misclassified because `codex exec --json` omitted collaboration events. The preserved isolated rollout proves a real spawn, distinct child execution, delivered result, and wait-after-result. The runner now allows exactly one child and, only for delegation-required turns, extracts bounded hashed spawn/result/nested-spawn/file-change facts from its temporary isolated rollout before deletion. Candidate `bd9102a41b7299735d3ff4a2c47fa384431c232a` then stopped without retry after 38,466 tokens because the public stream emitted `collab_agent_tool_call`, which the sanitizer still treated as an unknown generic tool. The red-first correction accepts public collaboration event identities but never copies their prompt; unknown tools expose only bounded type metadata. Candidate `c833b312ae4ded9ca47c88a86c80805e0ab2938c` subsequently completed the focused gate with one matching hashed spawn/result, a read-only non-delegating child, zero repository mutation, and root rejection of an out-of-scope proposal. The P0 delegation blocker is closed; the later complete R4 result and waivers are recorded above.

Residual paired-evaluation code is unsupported 1.x research debt, not a 2.0 release or compatibility surface. Flow Activation Coverage is the only active semantic-routing check.

## Install and rollback

Use an isolated temporary Codex home. Never mutate the maintainer's primary profile as a release test.

```bash
DEV_FLOW_TEST_CODEX_HOME=/absolute/private/temporary-codex-home
CODEX_HOME="$DEV_FLOW_TEST_CODEX_HOME" \
  codex plugin marketplace add AldenClark/dev-flow --ref vX.Y.Z-rc.N --json
CODEX_HOME="$DEV_FLOW_TEST_CODEX_HOME" \
  codex plugin add dev-flow@dev-flow --json
CODEX_HOME="$DEV_FLOW_TEST_CODEX_HOME" \
  codex plugin list --json
```

A local snapshot proves local CLI/manifest behavior only. The 2.0 RC line makes no prior-version upgrade, rollback, or re-upgrade promise; those cells are not applicable to the hard cut. Target-platform loading remains `NOT RUN` until exercised. Modified user-owned runtime files must never be deleted merely to complete a test.

## Failure handling

- Preserve and classify the first failure before retrying.
- Do not weaken a threshold, delete a platform, or relabel `NOT RUN` to make a release green.
- Fix on a new commit and rerun only invalidated evidence lanes.
- Do not rebuild or replace bytes behind an existing digest or attestation.
- If rollback is needed after publication, restore the last known-good plugin version and behavior; retain repository research/design history and legacy packet data.
