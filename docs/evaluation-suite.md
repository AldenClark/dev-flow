# Quality-first evaluation suite

Dev Flow treats evaluation as supporting evidence for the Skills, not as the product. The primary question is whether the workflow produces a correct, scoped, reviewable repository change. Model scores cannot replace repository tests, platform evidence, security checks, independent review, packaging, or lifecycle proof.

## Evidence pyramid

Use the lowest sufficient layer and keep each claim inside that layer's evidence boundary:

1. **Deterministic admission:** validate Skill structure, direct and negative triggers, exact routing, owner outputs, stop/handoff behavior, authority boundaries, compatibility, and safe counterexamples. Exercise an ordinary bugfix, a structural bugfix, and a public-contract change from task input through final repository evidence.
2. **Affected-category model check:** after layer 1 passes, a material model-dependent Skill change gets a filtered schema-1.8 attested pilot over every affected development category, with at least three independent first attempts. A single pair is useful only to diagnose a specific failure or grader/case defect; it is not admission evidence for a material change.
3. **Frozen release comparison:** run the complete schema-1.6 acceptance plan only for an explicitly authorized and budgeted release comparison. It remains model-behavior evidence, not total release readiness.

Ordinary wording, refactoring, deterministic implementation, and documentation changes stop after proportionate deterministic checks unless they alter model-visible behavior. If no valid case and oracle cover the changed behavior, record model evaluation as `NOT RUN`; do not substitute an unrelated score.

## What a model run may claim

An attested pilot is a controlled comparison of baseline and candidate on selected fixed cases under a bound harness, models, prompts, budget, and scoring policy. It can reveal a repeatable local omission or regression. It does not estimate performance over all software tasks, user productivity, or production correctness.

The development bank is for diagnosis and regression. The frozen acceptance bank is held out from change-level tuning, but repository-visible fixed cases are not guaranteed free of model-training contamination and are not a random population sample. Report that limitation with every durable result.

## Development categories

The current development config is `evals/paired-evaluations.json`. Select categories because the changed behavior can affect them, not to improve a headline result.

| Category | Representative behavior |
|---|---|
| Context and profiles | multi-root precedence; execution-mode isolation; generated ownership |
| Cross-language FFI | callback, ownership/error, lifecycle, and packaging boundaries |
| Migration | persisted protocol, database backfill, and public SDK rollout |
| Verification | retry, shutdown, and compatibility evidence |
| Requirements | ambiguity, contradictions, states, sparse bugs, and material defaults |
| Structured interaction | native input, cancellation, authority, and secret handling |
| Frontend UX and engineering | product intent, protected IA, recovery, state, and accessibility |
| Debugging | timeout, cross-platform path, and async race diagnosis |
| Dependencies | add, update, and removal governance |
| Delivery | signing, rollback lifecycle, and provenance |
| Change review | authorization, concurrency, and workflow supply-chain diffs |

The acceptance config, `evals/paired-evaluations-acceptance.json`, additionally covers architecture, security/privacy, performance/resources, and concurrency/recovery. Do not use acceptance cases to tune a candidate. A revealed acceptance defect invalidates that case as held-out evidence; repair it in development and establish a new freeze before another release claim.

## Running an affected-category pilot

Schema 1.8 defines one first attempt as baseline and candidate executions through owner/kind-blind inventory, routing-manifest assembly, deterministic claim-ledger materialization, and blind grading. The exact requests, source snapshot, evaluator/backend identities, nonces, results, hashes, and no-tool usage receipts are bound by the existing protocol.

Run all affected categories only after deterministic gates pass. Repeat `--category` when more than one category is affected:

```bash
python3 evals/run_paired_evaluations.py \
  --attested-pilot --category CAT-FFI \
  --executor-draft 'python3 evals/codex_model_adapter.py inventory --model gpt-5.6-sol --reasoning-effort medium' \
  --executor-assembler 'python3 evals/codex_model_adapter.py assembler --model gpt-5.6-sol --reasoning-effort high' \
  --grader 'python3 evals/codex_model_adapter.py grader --model gpt-5.6-sol --reasoning-effort medium' \
  --output /absolute/private/eval-output --trials 3 --seed 20260810
```

`--attested-pilot` requires a strict pair/category filter and the configured evaluator identities. There is no runnable unfiltered schema-1.8 development pilot. `--pair` remains available for diagnosis, but a material behavior claim requires every affected category to include at least the configured minimum of three distinct cases, with at least three independent first attempts per case. A smaller slice is explicitly diagnostic and cannot pass the model evidence layer.

Before authorization, calculate the call budget from the selected plan. Schema 1.8 uses six model calls per pair per trial: baseline and candidate inventory, assembly, and grading. Record selected pairs/categories, trials, expected calls, deadline, and any exposed token fields. Do not infer monetary cost when the provider does not expose it.

Every content result is a first attempt and receives no retry. A pilot may use at most one predeclared retry only for a typed timeout or adapter-declared transport/service failure that produced no usable content result; preserve the failed attempt and its receipt. Release mode permits no infrastructure retry. When an evidence quote occurs exactly once across `fixture` and `task_prompt` but the model declares the other source, the runner preserves the raw result, resolves that mechanical provenance label, and records the normalization in the report. This is deterministic canonicalization, not a content retry; missing, repeated, overlapping, or cross-source-ambiguous quotes still fail closed. Reports containing the normalization audit field require the current report schema; pre-change strict readers may reject the additional field, while the current schema continues to accept older schema-1.7 reports. `progress.json` is operational progress, not completion; only a reconciled terminal `report.json` can close the run.

## Non-composite scorecard

Do not turn the report into one overall quality number. Read and publish these dimensions separately:

| Dimension | Evidence | Interpretation |
|---|---|---|
| Safety and authority hard gates | unsafe actions, forbidden actions, false blocks, tool events, missing critical/required facets, invalid or incomplete records | Zero tolerance. A failure cannot be averaged away. |
| Outcome | strict-pass counts by case and affected category; applicable deterministic workflow results | Shows whether the selected obligations were met under the bound setup. |
| Variability | raw pass pattern across independent first attempts; mixed-outcome cases; paired regressions and recoveries | Distinguishes repeatable behavior from one-off model variation. |
| Fidelity and repair burden | requirement fidelity, scope, coverage, restraint, ordinary-defect retention, actionability, rework, and repair depth | Diagnoses what improved or regressed; inspect exact support and omissions. |
| Cost | calls, elapsed time, prompt/capability/output bytes, context or token fields actually exposed | A resource constraint, never a quality substitute. |

The runner's existing global and category aggregates remain compatibility fields and diagnostics. Neither an aggregate, a grader's opaque `model_verdict`, nor a weighted score can override a hard gate or stand for end-to-end coding quality.

Wilson intervals in existing reports are operational/descriptive summaries of observed binary outcomes. The frozen release configuration continues to use its lower-bound threshold as a conservative configured gate, but fixed curated cases and repeated trials do not justify a population-confidence claim. Report raw numerator/denominator, case/category scope, trial count, instability, and limitations beside any interval.

## Case and grader health

Scores are credible only while cases and graders are credible:

1. Bind each case to a real workflow risk or observed failure, a reviewable fixture, an explicit oracle/reference solution, and both positive and negative behavior where applicable.
2. Audit every new failure transcript and a rotating sample of passes. Classify the cause as candidate behavior, grader error, broken/ambiguous fixture or oracle, harness/infrastructure failure, or possible contamination.
3. Do not count a broken or underspecified case. Quarantine it from development comparisons until repaired and re-baselined; never edit frozen acceptance policy or cases after observing release results.
4. Promote fresh shadow cases from real failures only after manual review establishes that prompt, fixture, and oracle agree. Keep the bank bounded; retire redundant cases with recorded disposition.

Active `contracts/` and frozen acceptance catalogs are no-orphan banks: every active case is consumed exactly once. Retirement removes both the active case and its configuration entry with a recorded disposition. Unpromoted shadow cases stay outside those active and frozen banks.

Add no evaluator protocol, schema, stage, or case family unless a core invariant cannot be observed through the existing deterministic checks and thin harness. Record the invariant, smaller rejected alternative, added maintenance and run cost, rollback, owner, and removal condition.

## Reading and releasing

Inspect results in this order: run validity and hard gates; affected-category and per-case outcomes; cross-trial variability; fidelity/retention/rework evidence; then cost. Read bounded transcripts when aggregates cannot explain a failure. A failed unchanged candidate is not retried; change the source or repair the case, grader, harness, or environment first.

An attested pilot always has `model_gate_ready: false`. `model_gate_ready` can become true only through the exact complete frozen acceptance plan with immutable inputs, clean source/config identity, and every configured gate passing. `release_ready` remains false in the model report because repository verification, independent review, artifact provenance, installation, rollback, signing, and publication authority are separate layers.
