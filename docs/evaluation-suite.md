# Paired evaluation suite

The paired suite measures the first bounded workflow response with and without selected Dev Flow capabilities. Pilots are descriptive diagnostics. A frozen acceptance run also reports two-sided 95% Wilson intervals and requires the lower pass-rate bound to clear the configured floor; neither mode substitutes for deterministic repository, platform, security, packaging, or lifecycle tests.

## Why the suite expanded

The original release set had five task families with one fixed case each. Historical results showed overall gains in pass rate, requirement fidelity, evidence quality, coverage, and actionability, while the cross-language FFI pair regressed. Global averages and integer scores did not explain the local omission: the candidate covered a dense general FFI checklist but repeatedly failed to load the required Swift, Kotlin, and independent FFI guidance first.

The first schema-1.2 FFI smoke exposed a second evaluator defect before broad expansion: the diagnostic grader treated honest `NOT RUN` planning as weaker than equally unexecuted imperative prose, even though the executor is intentionally denied repository and device access. Prompt clarification reduced but did not remove this behavior. A later development run produced the same core scores and obligation coverage for a stronger candidate response but changed the holistic verdict from pass to fail. The runner therefore retains the grader's holistic value as `model_verdict` and derives the reported `verdict` from explicit rubric floors, a rework ceiling, and fail-closed missing/unsafe/forbidden/false-block checks. Honest unavailable physical evidence must remain visible; it is not an opaque automatic failure.

The successor suite therefore makes nine changes:

1. It separates a 39-case development set from a 56-case frozen acceptance set. The combined 95 cases cover 16 categories; every category has at least five independent cases across the two sets.
2. Contract 2.2 and catalog 1.3 group related engineering evidence into owner-bound work units while preserving every independently falsifiable decision, fact, test, and review axis as an atomic facet.
3. Both variants receive the same complete neutral owner vocabulary and the full Cartesian owner/evidence-family vocabulary (`analysis`, `artifact`, `decision`, `interaction`, `limitation`, `test`). These task-agnostic classes contain no FFI, platform, or other gold-derived domain label. Neither variant receives hidden work-unit/facet IDs, actions, criticality, owner mappings, or a repository path to the gold contract/catalog.
4. The blind grader maps every hidden facet only to exact, unique support spans in executor claims whose owner and task-agnostic evidence family both match. `critical` means a high-consequence safety, compatibility, authority, or data-integrity gate; `required` means ordinary task completeness; both are hard gates, while `supporting` must remain non-missing. Distinct non-overlapping spans may reuse one cohesive claim inside one hard-gated work unit, but a claim cannot support two hard-gated work units; normalized whole-claim clones remain blocked. `partial` is a failure for either hard-gated tier, not a green warning.
5. Reports retain raw facet totals only for diagnosis. The quality score first equal-weights facets within a work unit, then work units within a task, tasks within a category, and finally categories. The headline is category-macro strict pass rate, so FFI's denser contract cannot dominate the overall score.
6. Schema 1.6 sends only explicitly selected capability references and binds owner registry, task-neutral evidence-kind registry and digest, contract/catalog version, pair mapping, and selected source bytes into the input identity. Attested-pilot and release modes additionally bind the first-party adapter, runner interpreter, executor/grader roles, model IDs, reasoning efforts, adapter digest, platform-specific Codex CLI version/SHA-256, result schema 1.3, and per-call no-tool usage receipts; only ordinary unbound pilots may use external evaluator programs.
7. Multi-scenario prompts are split into independently scored work units; a dedicated late-reopening case retains the real ambiguity-collision behavior.
8. Every aggregate includes a 95% Wilson interval. Release mode requires both the point pass rate and its lower confidence bound to clear the overall and per-category floor; pilots expose the interval without making it a gate.
9. The report separates model-plan quality from deterministic repository verification, independent review, and release lifecycle evidence. A model score cannot make the product release-ready.

The derived strict-pass policy requires fidelity/scope/coverage/restraint/retention/actionability scores of at least 3, fixture-grounded evidence, rework at most 2, structural coverage, every critical and required work unit and all of its facets fully covered, every supporting work unit non-missing, owner-and-kind-aligned support mappings, non-overlapping hard-gated support spans, cross-unit hard-gated claim exclusivity, and zero unsafe, false-blocking, or forbidden actions. Partial-credit semantic coverage remains a diagnostic score and never overrides strict failure. The raw `model_verdict` remains visible beside the policy result; policy overrides are counted rather than hidden.

## Canonical task matrix

| Category | Representative cases | Candidate capabilities |
|---|---|---|
| Context and profiles | multi-root precedence; personal/team/CI isolation; generated ownership boundary | `repo-context`, `manage-engineering-profiles` |
| Cross-language FFI | mobile callback; ownership/error evolution; lifecycle/packaging | `architecture-decisions`, `change-review` |
| Migration | persisted protocol; online database backfill; public SDK rollout | `repo-context`, `delivery-readiness` |
| Verification | retrying worker; concurrent shutdown; compatibility matrix | `verification`, `change-review` |
| Requirements | late ambiguity reopening; design contradiction; missing states; avoidable question; sparse bug; material default | `dev-flow`, `requirements-design`, `repo-context`, task-specific product/debug/verification owners |
| Structured interaction | native input matrix; cancellation/stale response; authority/secret separation | `dev-flow`, `requirements-design` |
| Frontend UX | new product; preserve information architecture; responsive recovery states | `product-ux-discovery`, `requirements-design` |
| Frontend engineering | table/chart extension; server-state ownership; accessibility | `architecture-decisions`, `verification` |
| Systematic debugging | process timeout; cross-platform path; async generation race | `systematic-debugging`, `verification` |
| Dependency governance | new dependency; major update; safe removal | `dependency-decisions`, `architecture-decisions` |
| Delivery readiness | signed RC; install/rollback lifecycle; provenance mismatch | `delivery-readiness`, `verification` |
| Change review | authorization diff; concurrency diff; workflow supply chain | `change-review`, `verification` |
| Architecture | state ownership; plugin isolation; error boundaries; atomic side effects; dependency direction | `architecture-decisions`, `change-review` |
| Security and privacy | tenant authorization; redaction; credential lifecycle; path containment; audit integrity | `architecture-decisions`, `change-review`, `verification` |
| Performance and resources | backpressure; eviction; batching; UI memory; startup budgets | `architecture-decisions`, `verification` |
| Concurrency and recovery | idempotency; cancellation; crash recovery; generations; graceful drain | `architecture-decisions`, `systematic-debugging`, `verification` |

The development config is `evals/paired-evaluations.json`. Schema 1.8 fixes one composite first attempt as owner/kind-blind inventory plus a routing-manifest assembler, followed by deterministic ledger materialization and the grader; `--attested-pilot` requires at least one pair/category filter and exact inventory/assembler/grader identities. Each stage has an opaque root, backend recheck, unique control-plane nonce, request/result hashes, and receipt 1.2. The assembler receives the validated atomic inventory and task-neutral routing vocabularies, never gold or grader feedback. The acceptance config is `evals/paired-evaluations-acceptance.json`; it remains a separately frozen schema-1.6 single-stage release path. Changing pipeline, adapter, model, effort, receipt, or freeze identity requires a new canonical digest. If an acceptance case reveals a defect, that case becomes development evidence and may not be reused as held-out proof.

Each config entry binds a unique prompt, fixture, and structured owner-kind work-unit contract. A work-unit owner must be present in the pair's capability set, and every claim-route kind must exist in the bound registry with that owner. Development inventory sees the task, fixture, and condition-specific capability text with provenance paths removed, but no owner/kind vocabulary. The assembler receives the validated atomic inventory plus the task-neutral routing vocabularies. Neither stage sees hidden work units, facets, criticality, trial/variant labels, real artifact paths, usage, receipts, or grader data. The blind grader sees the task, fixture, oracle, hidden work-unit contract, and materialized content DTO. The combined fixture, contract, entrypoints, and selected references retain the hard 256 KiB per-pair ceiling.

## Sampling and cost control

- A focused schema-1.8 development case uses three trials: six inventory, six assembler, and six grader calls (18 total).
- The 39-case development broad pilot uses three trials: 702 calls.
- The 56-case acceptance pilot uses three trials: 336 executor and 336 grader calls.
- The frozen acceptance release plan uses twelve trials: 672 executor and 672 grader calls. With the minimum three cases per category, a perfect 36/36 category has a 95% Wilson lower bound above 0.9; 35/36 does not.

Development uses a 0.8 candidate pass-rate floor for diagnosis; frozen acceptance raises it to 0.9 for the overall and every category gate, while unsafe-action and false-block tolerances remain zero. Frozen acceptance must clear both the observed rate and the 95% Wilson lower bound. With the current minimum category size this is intentionally stricter than the point estimate and prevents a small sample from being described as high-confidence evidence.

Order is counterbalanced within trials and case order is seeded. Every run is a first attempt. Raw results remain local/private; durable or public evidence should retain only hashes, receipts, aggregates, bounded work-unit/facet summaries, and limitations. Monetary cost remains unknown when the authenticated Codex session does not expose it, and must not be inferred from tokens.

The runner atomically updates `progress.json` after every baseline or candidate record with the config digest, expected/completed/failed counts, and the last bounded case position. Usage receipts separate prompt, selected-capability, and output bytes and retain only token fields actually exposed by the adapter; unavailable monetary cost or token splits remain `null`. Progress is operational evidence only; `report.json` remains the sole aggregate result, and an interrupted `running` state is never completion.

Run the broad pilot only after deterministic config, contract, schema, adapter, isolation, category-gate, and focused-category model checks pass; evidence used to expand scope must come from `--attested-pilot`, not an unbound command. A pilot may predeclare a 600-second child deadline and at most one infrastructure retry. The retry applies only to a typed runner timeout or an adapter-declared transport/service failure, uses a separate attempt directory, and preserves the original request, output, error, duration, and path in the report. Any terminal evaluator failure opens a circuit so later model calls are not scheduled against a broken program or service. Ordinary exits, no-diagnostic environment failures, invalid output, tool events, unsafe behavior, missing/partial facets, grader verdicts, and every content or quality failure receive zero retries. Adapter failure receipts retain only bounded byte counts and SHA-256 fingerprints plus the typed class, never raw service diagnostics. A recovered failure remains visible even though its terminal valid sample can complete the descriptive pilot. Release mode requires zero infrastructure retries. On catchable SIGTERM/SIGINT, the runner records an incomplete terminal report after cleaning its trusted evaluator process group and live descendants observed to have changed groups/sessions. Arbitrary evaluator commands retain ambient user authority and are not a sandbox; SIGKILL, forced OS termination, and an untrusted instant double-fork remain outside the guarantee. A failed unchanged candidate is not retried; create a source-changing successor or investigate the model, architecture, environment, or oracle.

## Reading a result

The overall aggregate is useful for direction, but it is not the release decision. Inspect in order:

1. structural completeness, tool events, process exits, and invalid records;
2. each category's pass rate, fidelity, defect retention, safety, false blocks, and context ratio;
3. per-case scores, work-unit summaries, and facet assessments;
4. repeated omissions across distinct fixtures versus one-off model variation;
5. raw private evidence only when the bounded diagnostic summary cannot establish cause.

`model_gate_ready` requires the exact frozen acceptance config, all cases and trials, immutable input snapshot, clean source/config identity before and after the run, and every global and category gate passing. A pilot can pass descriptive thresholds but never becomes model-gate-ready. `release_ready` remains false in this report because deterministic repository outcomes, independent change review, and attestation/install/rollback/signing evidence are separate mandatory layers.
