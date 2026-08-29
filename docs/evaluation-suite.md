# Flow Activation Coverage

Dev Flow tests whether representative work enters the intended branches and avoids unnecessary ones. It does not measure developer productivity, business effect, overall model quality, or the value of a Skill by counting its use.

`flow-metrics` is retained as a compatibility name for this activation test only.

## Active coverage contract

The shipped catalog is `evals/flow-activation-cases.json`. Run it through the public command:

```bash
python3 skills/dev-flow/scripts/dev-flow.py flow-metrics
```

Material multi-boundary regressions also run through the same evaluator using `evals/large-task-routing-cases.json`. The catalog contains 80 cases: 20 common task families with four distinct variants each. Its coverage test rejects a missing or imbalanced family and separately protects intent, requirement class, direct/managed mode, risk, method-signal, owner, overlay, negative-trigger, and recent-regression diversity:

```bash
python3 skills/dev-flow/scripts/flow_metrics.py \
  evals/large-task-routing-cases.json
```

The 20 families are issue diagnosis, bounded defect repair, structural defect repair, feature implementation, cross-module feature work, behavior-preserving refactor, performance/resource work, concurrency/distributed state, data lifecycle/migration, API/protocol/ABI contracts, dependency/toolchain change, security/privacy, UI/accessibility/platform lifecycle, tests/evaluation/CI, code/proposal review, architecture/product design, repository/options research, build/operations/scientific workflows, release/delivery readiness, and long-horizon coordinated evolution.

The taxonomy was refreshed on 2026-08-21 from primary public benchmark descriptions. [SWE-bench](https://www.swebench.com/SWE-bench/faq/) contributes real issue repair plus multilingual and screenshot/UI variation; [SWE-Lancer](https://openai.com/index/swe-lancer/) contributes bug fixes, feature implementations, end-to-end checks, and engineering proposal selection; [Terminal-Bench](https://www.tbench.ai/news/announcement) contributes terminal, network, data, API, scientific, and security workflows; [FeatureBench](https://github.com/LiberCoders/FeatureBench) contributes feature-level work spanning multiple commits; [LongCLI-Bench](https://github.com/finyorko/longcli-bench) contributes from-scratch, feature, bug-fix, and refactor shapes with requirement and regression oracles; [CRAVE](https://research.turing.com/crave) contributes code-review work; [MLE-bench](https://openai.com/index/mle-bench/) contributes data preparation, model training, and experiment workflows; and [RoadmapBench](https://arxiv.org/abs/2605.15846) contributes multi-target version evolution. Dev Flow adapts only these task shapes; it does not import their datasets, graders, scores, environments, or model claims.

These are deterministic public-route simulations. They prove that declared facts enter the expected owners, methods, review, continuity, specialist, and evidence boundaries; they do not prove that a model inferred those facts or invoked Dev Flow from natural language.

For a semantic or isolated pilot, execute the task outside the evaluator in a fresh repository, preserve its first attempt, and describe only the observed activation in a small manifest:

```json
{
  "schema_version": "flow.activation.observations.v1",
  "cases": [{
    "id": "SEMANTIC-U1-CLARIFICATION",
    "observed": ["requirements-design", "focused-material-clarification", "default-mode-stop", "no-repository-mutation"],
    "evidence": ["isolated first response and repository diff inspected"],
    "unmet_prerequisites": [],
    "authority_violations": []
  }]
}
```

Then evaluate every catalog case through the same public command:

```bash
python3 skills/dev-flow/scripts/dev-flow.py flow-metrics \
  --lane semantic --observations /absolute/path/to/first-attempt-observations.json
```

The default semantic catalog requires an observation for every shipped case. For a predeclared affected subset, pass a smaller catalog with `--catalog`; missing observations within that selected catalog still fail instead of being inferred. The runner does not invoke or rank a model, copy credentials, or spend a model budget. Model execution remains an explicitly authorized release/research action; `flow-metrics` only checks the resulting branch evidence.

The result reports:

- each case as `matched` or `mismatched`;
- the expected and observed branch when they differ;
- missing activation, unexpected activation, or an unmet prerequisite;
- `effect_measurement: false` and `aggregate_score: null`.

The matched count is test accounting, not a quality percentage or release score. Never aggregate Skill, method, model, review, agent, question, or document counts into an effectiveness claim.

Method-aware evaluation separates eligibility, activation, candidate selection, readiness, disposition, realization, and evidence effect. A valid method disposition is execute-ready, blocked-fallback with its limitation retained, or reasoned abstention because the owning specialist already supplies a sufficient procedure. Transition fixtures fail when a selected method silently disappears or when its concrete test, mutation, counterexample, model, review surface, evidence matrix, or claim limitation is removed. Method names, generated method artifacts, and selection counts cannot satisfy the oracle.

## Multi-turn transition observations

The shipped transition catalog is `evals/flow-transition-semantic-cases.json`. It declares the nine canonical R4 categories, at least three cases assigned to each category, at least three independent first attempts per case, ordered turns, resume/fork lineage, candidate repository-mutation expectations, optional bounded runner-owned pre-turn fixtures, per-turn expected-unmet state, and expected/forbidden branch observations. Validate externally observed attempts with:

```bash
python3 skills/dev-flow/scripts/dev-flow.py flow-metrics \
  --lane transition \
  --observations /absolute/path/to/attempt-001.json
```

Each observed case binds an `initial_repository_sha256`, a deterministic `initial_git_head_sha256`, and one `repository_sha256` per turn. Fixture Git initialization ignores system/global config and hooks and fixes the branch, identity, and timestamp. The validator rejects missing or out-of-order turns, reused evidence digests, a declared repository mutation not bound to changed bytes, byte changes during a `mutation=none` turn, unmet prerequisites, authority violations, and expected/forbidden mismatches. It does not invoke a model, reconstruct a transcript, infer labels, or emit an effect/aggregate score.

The companion runner is non-spending by default. A release-qualification plan must explicitly select the full catalog and minimum attempt count:

```bash
python3 evals/run_transition_trials.py
python3 evals/run_transition_trials.py --qualification --attempts 3
```

An authorized live run additionally requires `--qualification --attempts 3`, `--execute`, `--acknowledge-model-spend`, explicit `--model` and `--reasoning-effort`, an empty `--output-dir`, per-run ceilings, and one external cumulative campaign ledger. A complete invocation is:

```bash
python3 evals/run_transition_trials.py \
  --qualification --attempts 3 --execute --acknowledge-model-spend \
  --model MODEL --reasoning-effort EFFORT \
  --output-dir /absolute/empty/output \
  --campaign-budget-file /absolute/private/campaign.json \
  --campaign-id CAMPAIGN --campaign-max-total-tokens CAMPAIGN_MAXIMUM \
  --max-total-tokens MAXIMUM --per-call-token-limit PER_CALL \
  --per-call-timeout-seconds SECONDS
```

Before the first model call, the runner reserves the complete per-run allowance from the campaign ledger. Allocations accumulate across output directories and candidate revisions and are never released. A second run with unchanged semantic-runtime and qualification-execution identities is rejected in favor of prior-evidence reuse. A changed identity invalidates only the affected claim; it does not renew budget authority. Each invocation binds a fresh reservation nonce into its run ID, so admission recovery cannot claim another concurrent invocation's reservation. A stale guard, malformed ledger, or indeterminate ledger-update failure fails closed with an explicit recovery record rather than guessing that no writer is active.

The runner has one responsibility: execute the candidate in isolated synthetic repositories and preserve bounded first-attempt evidence. Each attempt contains the synthetic response text, sanitized tool trajectory, runner-owned fixture delta, candidate repository delta, Git/repository digests, lineage digest, and evidence digest. It checkpoints that evidence before semantic hard gates, so a prohibited mutation or lineage/trajectory failure remains inspectable after the temporary repository is removed. Mutation identity excludes only Python bytecode under `__pycache__` and `.pytest_cache` test-runner state; those paths still count toward resource limits, and source-like neighbors remain visible. It checks resume/fork identity, Git HEAD, candidate-versus-fixture mutations, per-call, per-run, and campaign token usage, timeouts, process groups, output size, repository size, and exact candidate/catalog/runner/Codex identity. Delegation-required turns allow exactly one child slot and supplement the incomplete public JSON stream with bounded facts from the runner-owned temporary rollout: hashed child identity/path and result content plus fixed nested-spawn/file-change markers. Current-turn identity, exact spawn/result reconciliation, read-only-child, no-redelegation, safe real paths, JSONL shape, and resource bounds fail closed; raw child text and raw session identities are never copied into attempt evidence. The runner preserves the first execution failure without automatic retry, terminates the process tree on interruption, records bounded partial usage/evidence, and deletes temporary plugin homes, raw session events, raw session identifiers, and fixture repositories.

Execution ends with `status: awaiting-manual-assessment`; it does not emit observations or a qualification verdict. Inspect each bounded synthetic evidence file, write a separate `flow.transition.observations.v1` manifest, and evaluate it through `flow-metrics --lane transition`. Keep the assessment manifest and coverage result outside the candidate tree. Do not include credentials, personal paths, production values, or raw session IDs. This restores the RC.2 separation between model execution and same-context/manual adjudication; report `common-mode-risk` rather than claiming independent evaluation. `--qualification` rejects a partial `--case` selection or fewer than three attempts. A non-qualification diagnostic run proves only its exact lineage mechanics and cannot satisfy R4.

The runner uses a POSIX process group plus TERM/KILL cleanup and per-file resource limits. Hosted Windows compatibility must still prove descendant cleanup under its native process model; local source evidence does not upgrade that cell to passed. A host-level filesystem quota remains recommended because no portable per-directory disk quota is supplied by Python.

The transition catalog also covers closed versus explicitly open discovery, finding disposition, blocked-to-ready method rechecks, fallback and abstention, review-to-verification adjacency, method realization, nested delegation narrowing, terminal persistence, process supervision, auxiliary-mechanism convergence, explicit task synthesis, reference-repository boundaries, confirmed profile writes, and ordinary-conversation quietness. These are observation contracts; they do not claim deterministic host enforcement.

## RC.3 evaluation correction

Earlier RC.3 candidates used a two-model evaluation mechanism. It consumed substantial budget, introduced its own false positives and contract defects, and encouraged repeated local evaluator repairs without advancing the primary release condition. That mechanism, its Schema, tests, CLI surface, identity fields, and release requirement were removed on 2026-08-24. Its preserved failed and diagnostic results remain historical nonqualification evidence only and must not be rescored or represented as current R4 evidence.

The corrected catalog contains 22 cases across nine enforced categories. It retains the useful hard-gate repairs learned from earlier trials: exact mutation paths and baselines, bounded repository fixtures, deterministic Git identity, changed-fact capability recovery, exact scanner execution including one trusted shell-wrapper layer, unmet-state consistency, and fork current-state reconciliation. It also adds a cumulative auxiliary-mechanism convergence case: after two repairs without primary-outcome progress, the default is a simpler/manual fallback or an honest blocked/deferred gate, not a third evaluator tweak.

Qualification output belongs outside the candidate tree so recording a result cannot change the source identity being qualified. The default qualification condition remains a complete three-first-attempt matrix on corrected bytes; earlier partial or focused results do not satisfy it. After two auxiliary repairs without primary progress, further live execution requires an explicit version-owner disposition. A bounded release-specific exception remains `WAIVED`, not `PASSED`, and cannot establish stable-release or population-effectiveness claims.

## Privacy-safe dogfood aggregates

An explicitly authorized local dogfood audit may convert already selected observations into the strict `dev-flow.dogfood.observations.v1` schema and run:

```bash
python3 skills/dev-flow-maintainer/scripts/analyze_dogfood.py \
  /absolute/path/to/sanitized-observations.json
```

The analyzer accepts only enumerated task shapes, transitions, correction categories, scope outcomes, and method-funnel states. Unknown fields are rejected, so raw transcript text, task/session IDs, absolute paths, credentials, personal values, free-form notes, and productivity scores cannot enter its output. It reports counts and limitations only; `aggregate_score` is always null. Unsupported direct host-history access remains `BLOCKED`, and aggregates never authorize a profile write.

`evals/method-marginal-utility-cases.json` predeclares three bounded with-method/without-method comparisons for weak-oracle review, blocked-to-ready privacy reasoning, and model-evaluation case health. Requirement, repository fixture, model/tool/Skill identity, acceptance oracle, conditions, first-attempt minimum, negative regression, trajectory, scope, authority, and exposed cost are fixed separately. The catalog is non-executing and non-scoring; running it requires a separately authorized model budget and a frozen candidate.

## Required branch families

Keep pairwise and boundary cases for:

1. intent: research, diagnosis, design, change, review, and delivery;
2. continuity: direct work and managed work with only the two core documents;
3. requirement understanding: U1 confirmation stop, confirmed continuation, ambiguous-defect upgrade, and established-bug/mechanical/read-only skips;
4. overlays: security/privacy, migration/data, external systems, release, irreversible action, and UI/product without automatic mode escalation;
5. specialist routing: applicable effective Skills, plugin-prefixed Skill names, and qualified fallback when a route is absent;
6. methods: high-leverage eligibility, ready/blocked/fallback/abstain disposition, realization, evidence effect, and ordinary-work quietness;
7. review: material/explicit activation and generic-label restraint;
8. child routing: P0-P2 Luna only for closed directed work, Terra for ordinary judgment, Sol for open/consequential work, and root-only decisions;
9. verification, knowledge, delivery authority, and native-adapter boundaries.

Add a case when a real activation omission or over-activation is observed. Prefer the smallest case that distinguishes the boundary; do not create a Cartesian matrix.

## Three evidence layers

1. Deterministic routing executes the public commands, large-task simulations, oracle mutations, and negative controls in normal CI.
2. Semantic fixtures combine a natural-language request with a small repository shape and assert expected/forbidden activation against a preserved first-attempt observation manifest. Run these when model-facing instructions or triggers change.
3. High-fidelity isolated pilots use fresh repositories and a temporary plugin home when release/admission confidence depends on actual Codex interpretation. The nested model shell must not inherit the maintainer environment; client authentication remains outside that shell boundary. For a material R4 decision, predeclare at least three distinct cases per affected category and preserve at least three independent first attempts per case; report safety/authority, outcome, variability, repair burden, cost, prerequisites, and evidence limits separately.

Semantic and high-fidelity cases are not effect experiments. They do not compare developer speed, defect rates, token economics, or one model's general quality. A pilot can show that a branch did or did not activate under its exact setup; it cannot establish a population performance claim.

## Release use

R1 always runs deterministic activation coverage. Before publishing or admitting a material R4 model-semantic change, run a separately authorized and budgeted evaluation across every affected category after deterministic gates pass: at least three distinct cases per category and three independent first attempts per case. Predeclare expected/forbidden activation, keep safety/authority as hard gates, and do not collapse results into one score. One focused diagnostic attempt may resolve a local uncertainty, but it is not release/admission evidence.

A result may block publication only when a required branch is missing, a forbidden branch activates, authority is exceeded, or the fixture/prerequisite is invalid. Repository tests, platform checks, security controls, artifact provenance, installation, and publication authority remain separate evidence.

## RC.2 model-semantic evidence

The authorized RC.2 R4 run used 24,521,511 of a 25,000,000-token maximum with `gpt-5.6-terra` at medium reasoning in isolated synthetic repositories. The preserved broad matrix ran 33 attempts over 15 cases and found two real candidate failures during convergence: confirmed U1 could be downclassified to U2, and a read-only webhook contract design could load specialist owners without the Dev Flow kernel. Both failures and their raw attempts were retained rather than relabeled.

The repaired impact family then matched 12/12 attempts across six cases. Public-schema compatibility, signed webhook compatibility, and privacy-sensitive retention/deletion each had three independent first attempts; U1 clarification, U1 confirmation, and managed continuity provided adjacency coverage. All safety/authority gates passed. The semantic observation lane matched all six case contracts and emitted no aggregate score. Evidence remains limited to one model/effort and synthetic repositories; same-context review retained common-mode risk, and no production or business-effect claim follows.

## Unsupported 1.x evaluation residue

The repository still contains the 1.x paired-evaluation runner, schemas, development bank, and frozen acceptance bank as internal historical residue. They are not a supported 2.0 compatibility or research interface, not `flow-metrics`, and not a release gate. They may be removed without a migration promise.

Dev Flow 2.0 never uses their historical metric or threshold fields to rank people, optimize process activation counts, or decide releases. Flow Activation Coverage is the only active routing-evaluation contract.
