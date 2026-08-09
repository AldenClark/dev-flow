---
name: systematic-debugging
description: Reproduce and diagnose incorrect behavior through competing causal hypotheses, discriminating experiments, call-path evidence, and regression proof. Use for bugs, flaky tests, crashes, hangs, integration failures, performance anomalies, and read-only root-cause investigations; do not use to bundle unrelated cleanup or silently implement a fix when authority is diagnosis-only.
---

# Systematic Debugging

If diagnosis reaches a missing user-owned fact or semantic boundary, remain in Default mode and follow `../requirements-design/references/user-interaction.md`.

Trace the earliest incorrect state rather than patching the final symptom.

## Procedure

1. Capture symptom, environment, version, input, expected/actual result, logs/trace, and reproduction reliability.
2. Reduce to the smallest faithful reproducer and trace backward across boundaries.
3. Maintain a `diagnosis.ledger.v1` with facts, unknowns, hypotheses, predicted observations, experiments, results, and dispositions.
4. Run the cheapest discriminating experiment; preserve first failures and rejected hypotheses.
5. Identify the root cause and affected invariant before proposing a correction.
6. For implementation authority, add or identify a regression oracle that fails on the broken behavior when practical, apply one root-cause correction, then rerun the reproducer and nearby regressions.
7. After three failed hypotheses or repair attempts, stop layering changes and reassess reproduction, model, architecture, environment, and oracle.

Read `references/hypothesis-ledger.md` for evidence, flake, breaker, and regression rules.

## Boundaries

- Keep diagnosis and remediation authority separate.
- Do not use retries to erase flakiness or a passing linter as root-cause proof.
- Do not opportunistically refactor outside the causal boundary.
