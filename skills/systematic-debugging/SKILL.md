---
name: systematic-debugging
description: Diagnose uncertain failures from competing causes; exclude routine fixes with a clear oracle.
---

# Systematic Debugging

Trace the earliest incorrect state rather than patching the final symptom. Use it when cause is uncertain, reproduction is flaky, or a prior repair did not explain the failure—not for a known, bounded fix with a clear oracle.

This Skill may operate alone for narrow diagnosis. If the repair becomes a material repository mutation, crosses boundaries, needs managed continuity, or exposes high-risk delivery, load `dev-flow` as the coordinating kernel when it is available and not already active; keep this Skill as the causal-diagnosis owner.

## Find the causal boundary

1. Capture the expected and actual result, exact input/configuration, version, environment/platform, reliability, and first failure. Preserve the first failure even if a retry passes.
2. Reduce to the smallest faithful reproducer, then classify the observed boundary: product code, invocation command/configuration, test harness/fixture/runner, local environment/resource, or target platform/integration. Do not let a passing host or harness check erase a target-platform observation.
3. State a small set of competing causal hypotheses. For each, predict the earliest wrong state and one observation that would distinguish it from the others; prefer one changed variable and the cheapest discriminating experiment.
4. Trace backward across inputs, state transitions, process/network/FFI boundaries, ownership, ordering, retries, cancellation, resource limits, and recovery until the earliest actionable invariant violation is supported and credible alternatives no longer fit.
5. Only when repair is authorized, add or identify an oracle that exposes the broken behavior where practical, make one causal correction, and rerun the reproducer plus nearby regressions. A diagnostic request remains diagnosis unless the user also asked for a fix.
6. Stop adding retries or patches when experiments no longer add information, collateral risk rises, or the observation boundary is unresolved. Reassess the reproducer, causal model, harness, environment, platform, and oracle instead of turning a terminal symptom into a root cause.

Use [hypothesis-ledger guidance](references/hypothesis-ledger.md) for complex or long-running incidents. A local scratch table may help; no persisted diagnosis ledger is required for ordinary bugs.

## Boundaries

- Diagnosis does not by itself authorize remediation.
- Retries do not erase flakes and a passing linter does not prove root cause.
- Do not refactor outside the causal boundary without separately justified scope.
