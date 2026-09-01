# Dev Flow 2.0 release validation and benchmark separation decisions

## D1: Remove R4 from releases

- Status: accepted by the version owner on 2026-09-01.
- Decision: R4 and repeated model qualification are not active release gates.
- Consequence: canonical delivery state no longer records `model_qualification`.

## D2: Make stable validation stronger through meaningful breadth

- Status: accepted.
- Decision: stable validation uses cumulative semantics, six consolidated static methods, five bounded functional journeys, and one complete deterministic regression.
- Consequence: stable is stronger than an RC without recreating a statistical model campaign.

## D3: Make Dev Flow Bench independent

- Status: accepted.
- Decision: the former R4 machinery becomes a research tool with separate suites, case health, execution, grading, comparison, and explicit spend limits.
- Consequence: benchmark results cannot update release truth or produce a release score.

## D4: Simulate but do not release

- Status: accepted.
- Decision: inventory and exercise the new stable process without model calls or delivery actions.
- Consequence: simulation evidence proves process shape only; stable `2.0.0` remains deferred.
