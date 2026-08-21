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

## Required branch families

Keep pairwise and boundary cases for:

1. intent: research, diagnosis, design, change, review, and delivery;
2. continuity: direct work and managed work with only the two core documents;
3. requirement understanding: U1 confirmation stop, confirmed continuation, ambiguous-defect upgrade, and established-bug/mechanical/read-only skips;
4. overlays: security/privacy, migration/data, external systems, release, irreversible action, and UI/product without automatic mode escalation;
5. specialist routing: applicable effective Skills, plugin-prefixed Skill names, and qualified fallback when a route is absent;
6. methods: high-leverage activation and ordinary-work quietness;
7. review: material/explicit activation and generic-label restraint;
8. child routing: P0-P2 Luna only for closed directed work, Terra for ordinary judgment, Sol for open/consequential work, and root-only decisions;
9. verification, knowledge, delivery authority, and native-adapter boundaries.

Add a case when a real activation omission or over-activation is observed. Prefer the smallest case that distinguishes the boundary; do not create a Cartesian matrix.

## Three evidence layers

1. Deterministic routing executes the public commands, large-task simulations, oracle mutations, and negative controls in normal CI.
2. Semantic fixtures combine a natural-language request with a small repository shape and assert expected/forbidden activation against a preserved first-attempt observation manifest. Run these when model-facing instructions or triggers change.
3. High-fidelity isolated pilots use fresh repositories and a temporary plugin home when release/admission confidence depends on actual Codex interpretation. For a material R4 decision, predeclare at least three distinct cases per affected category and preserve at least three independent first attempts per case; report safety/authority, outcome, variability, repair burden, cost, prerequisites, and evidence limits separately.

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
