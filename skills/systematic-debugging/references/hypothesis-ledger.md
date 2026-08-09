# Hypothesis-led debugging

## Reproduction record

Capture exact symptom, expected/actual result, environment, versions/configuration, input/fixture, frequency, first known good/bad state, logs/trace/stack, and destructive/privacy constraints. If reproduction is unavailable, state the missing evidence and add observability rather than guessing.

## Ledger

For each hypothesis record:

- causal claim and earliest predicted bad state;
- supporting and contradicting facts;
- smallest experiment that distinguishes it;
- expected observation if true and false;
- exact command/environment/result;
- status: open, supported, rejected, environmental, or superseded.

Prefer one variable per experiment. Trace data and ownership across boundaries; the last visible failure is often not the first incorrect transition.

## Flakes and concurrency

Repeat the identical cell only enough to classify deterministic failure, product race, test race, environment contamination, resource collision, timeout, or infrastructure outage. Preserve the first failure. Do not count a later retry as passing evidence for the original cell.

For concurrent or distributed paths, inspect ownership, cancellation, ordering, idempotency, deadlines, retry/backoff, duplicate delivery, queue bounds, locks across suspension, slow consumers, shutdown/drain, leases, and crash recovery.

## Root cause and correction

A root-cause claim names the violated invariant, earliest wrong state, causal path, and why competing hypotheses no longer fit. A correction must restore the invariant rather than mask its terminal symptom.

When practical, demonstrate red-green:

1. add or identify an oracle that fails on the defect;
2. run it against the broken state or a safe reversed change;
3. apply the root-cause correction;
4. rerun the oracle and nearby regression scope.

If red-green is unsafe or impossible, record the alternative evidence.

## Breaker

After three failed hypotheses or repair attempts, stop patching. Reassess reproduction, causal model, architecture, environment, and oracle. Reopen the design or ask for the missing authority/fact when the evidence requires it.
