# Dev Flow 2.0 release validation and benchmark separation design

## Release path

RC repair stays small: affected checks, one consolidated lightweight static review, one complete deterministic suite on final bytes, and affected semantic smoke only when guidance changed. Stable adds breadth over time rather than repeated trials: cumulative semantic reconciliation, six static methods in one pass, five functional journeys, and applicable R1-R3 evidence.

The six default stable methods are traceability/V-model, change-impact graph, specification by example, feature-interaction analysis, black/white oracle accounting, and assumption mapping/premortem. They produce one findings list. At most two extra methods may be added for concrete diff risks.

## Bench path

`benchmarks/dev_flow_bench.py` owns the supported research CLI:

- `audit-suite` validates case contracts and health without a model;
- `plan` exposes the exact non-spending selection and stopping rules;
- `run` defaults to planning and requires explicit spend acknowledgement plus per-run limits for live execution;
- `grade` binds separately authored observations to one exact run and trial before assessment;
- `compare` requires compatible execution identities, unchanged case contracts, and complete case sets by default, and reports per-case changes without an aggregate score.

Regression, capability, and safety-authority are separate suites. Accepted cases run by default, provisional cases require explicit inclusion, and quarantined cases do not run. Bench owns a native case catalog, observation schema, bounded executor, suite selection, grading, and comparison. The catalog keeps descriptive case categories but has no fixed release-category inventory, population threshold, or repeated-attempt qualification rule.

Live records use exclusive output ownership, atomic owner-only JSON writes, bounded local DLP redaction, pre/post candidate and executor identity checks, and enumerated first-failure classification. Comparison can opt into an explicitly partial descriptive view and an automation-oriented regression exit, but neither changes release truth.

## Failure behavior

- Preserve the first case, infrastructure, safety, authority, or candidate failure.
- Do not retry automatically or tune a case after seeing candidate output.
- After two unchanged auxiliary repairs, simplify, replace, defer, or block.
- Release repair reruns only failed or newly affected checks; the complete deterministic suite runs once on the final candidate.
