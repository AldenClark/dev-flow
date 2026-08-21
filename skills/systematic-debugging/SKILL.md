---
name: systematic-debugging
description: Reproduce and diagnose bugs, flakes, crashes, hangs, integration failures, and performance anomalies through competing hypotheses and discriminating evidence.
---

# Systematic Debugging

Trace the earliest incorrect state rather than patching the final symptom.

This Skill may operate alone for narrow diagnosis. If the repair becomes a material repository mutation, crosses boundaries, needs managed continuity, or exposes high-risk delivery, load `dev-flow` as the coordinating kernel when it is available and not already active; keep this Skill as the causal-diagnosis owner.

## Procedure

1. Capture the symptom, expected and actual behavior, environment, input, version, and reproduction reliability.
2. Reduce to the smallest faithful reproducer and preserve the first failure.
3. Form a small set of competing hypotheses with observations that would distinguish them.
4. Run the cheapest discriminating experiment and trace backward across boundaries.
5. Identify the earliest actionable cause and the invariant it violates before changing code.
6. When implementation is authorized, add or identify a regression oracle that fails on the broken behavior when practical, apply one causal correction, then rerun the reproducer and nearby regressions.
7. After repeated failed hypotheses or repairs, stop layering changes and reassess the reproducer, model, architecture, environment, and oracle.

Use `references/hypothesis-ledger.md` for complex or long-running incidents. A local scratch table may help; no persisted diagnosis ledger is required for ordinary bugs.

## Boundaries

- Diagnosis does not by itself authorize remediation.
- Retries do not erase flakes and a passing linter does not prove root cause.
- Do not refactor outside the causal boundary without separately justified scope.
