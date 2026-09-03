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

## Dev Flow Bench

Repeated and comparative model studies now belong to the independent `dev-flow-bench` surface. They do not read or update `governance/product-state.json`, select a release tier, publish, install, or emit a release verdict. The default commands are deterministic and non-spending:

```bash
python3 benchmarks/dev_flow_bench.py audit-suite benchmarks/suites/dev-flow-regression.json
python3 benchmarks/dev_flow_bench.py plan benchmarks/suites/dev-flow-capability.json
python3 benchmarks/dev_flow_bench.py plan benchmarks/suites/dev-flow-safety-authority.json
```

The three suites answer different questions:

- regression: did accepted behavior change for a small bank of real historical failures and negative controls;
- capability: what does the candidate do on exploratory scope, method, and context-adaptation cases;
- safety-authority: did it cross a scope, tool, delegation, or delivery boundary.

Every suite case declares provenance, a concrete oracle, limitation, and health. `accepted` cases run by default, `provisional` cases require `--include-provisional`, and `quarantined` cases never run. Audit rejects malformed suites, duplicate or unknown cases, and expected/forbidden overlap. Case health is distinct from candidate behavior and infrastructure health.

An authorized live study additionally requires `run --execute --acknowledge-model-spend`, explicit model and reasoning effort, an empty output directory outside the candidate, and positive total-token, per-call-token, and timeout limits. The output directory is claimed exclusively and JSON records are replaced atomically with owner-only file permissions. Candidate source, Git state, suite/case contracts, benchmark/executor bytes, Codex executable/version, model, limits, and environment policy are bound before execution and rechecked after every trial. The tool preserves a classified first failure and performs no automatic retry. There is no release campaign ledger: each research invocation has one explicit bounded budget, and study owners decide whether later comparison is worth separate spend authority.

Execution, assessment, and comparison remain separate. A live run ends at `awaiting-assessment`; `grade --run-result RESULT --trial N --observations OBSERVATIONS` evaluates separately authored `dev-flow.benchmark.observations.v1` data only after each observation digest is bound to that exact trial. The graded v2 result carries the run, evidence, observation, candidate, execution-context, and case-contract identities. `compare` requires the same suite, case contracts, model/executor/limits, trial number, and complete case set by default. `--allow-partial` makes missing/added cases visible for exploratory work, while `--fail-on-regression` supplies a non-zero automation outcome. No command produces an aggregate score or population claim. Every selected safety-authority result remains visible rather than being inferred from category names.

Bench owns all 26 migrated cases in `benchmarks/cases/dev-flow-cases.json`, the three suite selections under `benchmarks/suites/`, its case/observation contracts in `benchmarks/dev_flow_bench_contracts.py`, its deterministic MCP fixture in `benchmarks/dev_flow_bench_fixture_mcp.py`, and the bounded internal executor in `benchmarks/dev_flow_bench_executor.py`. The catalog has no release tier, minimum repeated-attempt rule, or qualification threshold. The executor has no standalone CLI, campaign ledger, grading authority, or release-state access; the supported entry point remains `benchmarks/dev_flow_bench.py`.

Each observed case binds deterministic repository identity and per-turn repository bytes. The validator rejects missing or out-of-order turns, reused evidence digests, unbound mutations, unmet prerequisites, authority violations, and expected/forbidden mismatches. It does not reconstruct transcripts or infer labels. Model-run output stays outside the candidate tree; the retained bounded response is passed through the repository-local DLP redactor, while raw session IDs, raw MCP arguments, and raw MCP results are not retained. DLP is not proof that all nonsensitive contextual or path information is absent, so the owner-only local evidence must still be reviewed before sharing.

## Historical evaluation lessons

RC.2-RC.4 used an R4 release category and increasingly complex repeated trials. Those runs exposed real semantic defects, but also consumed substantial budget, introduced evaluator false positives and contract defects, and encouraged repeated auxiliary repairs without advancing the release. Preserved results remain historical facts; they are not rescored or treated as current release evidence.

The useful hardening survives inside the independent benchmark: exact mutation paths and baselines, bounded fixtures, deterministic Git identity, explicit absent/unrelated/authorized MCP states, unmet-state consistency, fork reconciliation, first-failure preservation, and the two-repair convergence boundary. After two auxiliary repairs without primary progress, simplify, defer, or block instead of tuning the evaluator again.

## Privacy-safe dogfood aggregates

An explicitly authorized local dogfood audit may convert already selected observations into the strict backward-compatible `dev-flow.dogfood.observations.v1`, `.v2`, or `.v3` schema and run:

```bash
python3 skills/dev-flow-maintainer/scripts/analyze_dogfood.py \
  /absolute/path/to/sanitized-observations.json
```

The analyzer accepts only enumerated task shapes, transitions, correction categories, scope outcomes, and method-funnel states. Unknown fields are rejected, so raw transcript text, task/session IDs, absolute paths, credentials, personal values, free-form notes, and productivity scores cannot enter its output. V3 is additive: it retains the V2 route, convergence, resource, workstream, test-system, and evidence aggregates and adds one bounded behavior slice with an observed black-box oracle, affected owner, structural signals, outcome, and terminal disposition. Structural success cannot impersonate a repair or productivity gain. Every version reports counts and limitations only, and `aggregate_score` remains null. Unsupported direct host-history access remains `BLOCKED`, and aggregates never authorize a profile write.

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
3. High-fidelity isolated pilots use fresh repositories and a temporary plugin home when confidence depends on actual Codex interpretation. An RC or stable functional check runs one bounded first attempt for each directly affected journey. Repeated studies belong to Dev Flow Bench and require their own sampling, stopping rule, budget, and claim limits. The nested model shell must not inherit the maintainer environment.

Semantic and high-fidelity cases are not effect experiments. They do not compare developer speed, defect rates, token economics, or one model's general quality. A pilot can show that a branch did or did not activate under its exact setup; it cannot establish a population performance claim.

## Release use

An RC always runs deterministic activation coverage and, when model-facing guidance changed, one bounded first attempt for every directly affected semantic case. Stable validation expands this to the five real functional journeys defined in the release runbook, but does not repeat an entire catalog. Repeated or comparative studies are optional Dev Flow Bench work and never become release evidence by default.

A result may block publication only when a required branch is missing, a forbidden branch activates, authority is exceeded, or the fixture/prerequisite is invalid. Repository tests, platform checks, security controls, artifact provenance, installation, and publication authority remain separate evidence.

## RC.2 model-semantic evidence

The authorized RC.2 R4 run used 24,521,511 of a 25,000,000-token maximum with `gpt-5.6-terra` at medium reasoning in isolated synthetic repositories. The preserved broad matrix ran 33 attempts over 15 cases and found two real candidate failures during convergence: confirmed U1 could be downclassified to U2, and a read-only webhook contract design could load specialist owners without the Dev Flow kernel. Both failures and their raw attempts were retained rather than relabeled.

The repaired impact family then matched 12/12 attempts across six cases. Public-schema compatibility, signed webhook compatibility, and privacy-sensitive retention/deletion each had three independent first attempts; U1 clarification, U1 confirmation, and managed continuity provided adjacency coverage. All safety/authority gates passed. The semantic observation lane matched all six case contracts and emitted no aggregate score. Evidence remains limited to one model/effort and synthetic repositories; same-context review retained common-mode risk, and no production or business-effect claim follows.

## Unsupported 1.x evaluation residue

The repository still contains the 1.x paired-evaluation runner, schemas, development bank, and frozen acceptance bank as internal historical residue. They are not a supported 2.0 compatibility or research interface, not `flow-metrics`, and not a release gate. They may be removed without a migration promise.

Dev Flow 2.0 never uses their historical metric or threshold fields to rank people, optimize process activation counts, or decide releases. Flow Activation Coverage is the only active routing-evaluation contract.
