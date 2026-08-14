# Verification, review, and assurance methods

Verification begins with the claim and likely defect, not a preferred tool.

## Oracle-first selector

| Oracle condition | Candidate methods |
|---|---|
| Exact expected output is available | example, boundary, decision/state, contract tests |
| General law/invariant is clearer | property-based testing |
| Exact output is hard but relations are known | metamorphic testing |
| Independent implementation/version/model exists | differential testing |
| Existing behavior must be preserved | characterization/golden master plus intentional-delta review |
| Stateful sequences dominate | state/model-based testing |
| Configuration interactions dominate | t-way combinatorial testing |
| Test sensitivity is uncertain | manual mutation, mutation testing, semantic mutation |
| Low-level path constraints dominate | fuzzing, sanitizers, symbolic execution |
| Concurrent histories dominate | schedule/linearizability testing plus temporal model |

Always account black-box and white-box derivations separately. Experience-based/adversarial work is a third view and cannot replace either.

## Failure-sensitivity challenge

For each critical test ask:

- What exact defect should this test detect?
- At what observation point is intended behavior distinguished?
- Did the test fail before the fix, under a local perturbation, mutation, invalid input, or independent cross-oracle?
- Could setup/mocking bypass the changed path?
- Could the assertion pass on an empty/default/stale result?
- Which false positive/negative remains?

Never optimize a mutation score, coverage percentage, test count, or green status as the outcome.

## Combinatorial and feature-interaction protocol

Define factors, values, constraints, and expected relation. Choose t from consequence/history, generate or verify the covering array, and add known higher-order hotspots. Pairwise coverage cannot prove absence of 3+-way feature interactions.

## Semantic mutation protocol

Use semantic mutation only when an executable/formal specification is itself part of the oracle. Mutate invariants, transition enabling, ordering, fairness, or relational constraints; run independent properties/tests; classify survivors as model, oracle, implementation-mapping, or equivalent-mutant gaps. Ordinary code mutation is the cheaper default.

## Performance and resilience evidence

Bind workload, dataset, environment, versions, warmup, thresholds, repetitions/variance, tails, resources, and telemetry. Separate load (expected), stress (beyond capacity), and soak (duration/leak/decay). Lab results are not production proof.

Chaos/fault experiments require a steady-state hypothesis, isolated/authorized target, blast-radius limit, abort threshold, recovery/reset, and post-state reconciliation. Simulation remains `NOT RUN` production resilience.

## Accessibility and usability evidence

Map applicable standard/platform criteria, run automated checks, then manually test semantics, focus, keyboard, zoom/text, contrast, motion, errors, and representative assistive technology. Conformance does not establish usability. Observe representative users for material comprehension/workflow claims; absence of users/devices stays explicit.

## Independent review

Blue review checks requirement fidelity, scope, integration, idioms, compatibility, maintainability, tests, and knowledge. Red review attacks misuse, malformed input, resources, concurrency, cancellation, recovery, compatibility, rollback, false assurance, and oracle weakness.

Freeze intent and bytes. Classify findings as implementation defect, design defect, evidence gap, scope change, or requirement ambiguity. Reviewers do not choose user-owned meaning. Repairs require finding-specific verification and scoped re-review.

Use independent N-version derivation or a GSN assurance case only when consequence and weak/common-mode oracles justify the cost.
