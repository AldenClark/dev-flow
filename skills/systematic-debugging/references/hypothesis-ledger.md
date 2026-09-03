# Hypothesis-led debugging

Use a scratch table for a complex or long-running incident when several causes remain plausible. Ordinary bugs do not need a persisted diagnosis artifact.

## Reproduction

Capture the exact symptom, expected and actual result, relevant environment/configuration, input, reliability, first known good/bad state, and useful logs or traces. Classify where it was observed: product code, command/configuration, harness/fixture/runner, local environment/resource, or target platform/integration. If reproduction is unavailable, state the limitation and add the smallest useful observation point instead of guessing.

## Competing hypotheses

For each live hypothesis, note:

- causal claim and earliest predicted bad state;
- supporting and contradicting facts;
- smallest experiment that distinguishes it;
- expected observation if true and false;
- observed result and current disposition.

Keep this in local scratch space unless the causal analysis itself will help future maintainers. Prefer one changed variable per experiment and trace backward across boundaries.

## Flakes and concurrency

Repeat an identical check only enough to distinguish a deterministic failure, product race, test race, environment contamination, resource collision, timeout, platform variance, or infrastructure outage. Preserve the first failure; a later pass does not erase it. A host pass cannot prove a device, deployed, or external integration path.

For concurrent or distributed paths, inspect ownership, cancellation, ordering, idempotency, deadlines, retry/backoff, duplicates, queue bounds, locks across suspension, slow consumers, shutdown/drain, and crash recovery as applicable.

## Root cause and correction

A root-cause claim identifies the violated invariant, earliest wrong state, causal path, and why credible alternatives no longer fit. Correct the invariant rather than masking the terminal symptom.

When practical, show a focused oracle fail before the correction and pass after it, then run nearby regressions. If this is unsafe or impossible, use another discriminating oracle and state the limitation.

After repeated failed hypotheses or repairs, stop layering changes and reassess the reproducer, causal model, architecture, environment, and oracle. There is no fixed attempt count; the stop signal is lack of new information or growing collateral risk.
