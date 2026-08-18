# Test matrix: <change-id>

> Legacy packet compatibility template. Direct and managed 2.0 verification selects native evidence without requiring this artifact.

## Dimensions and selection rationale

- Instruction mapping: <INS IDs and the cells that prove them>
- ECR/EQAC mapping: <tier, applicable obligations, selected controls/routes/fallbacks, and cells that verify them>
- <OS, browser, device, architecture, version, feature, data, or configuration dimension and why selected>

## Technique accountability

For every non-trivial behavior change, derive black-box and white-box obligations separately. Map every applicable perspective to implemented and executed cells. Use `N/A` only with a concrete change-specific reason; experience-based or red-team work cannot substitute for either perspective.

| Perspective | Derivation and obligations | Applicability or concrete N/A reason | Mapped cells |
|---|---|---|---|
| Black-box | <approved requirements, AC/protected behavior, API/CLI/UI/component outcomes, errors, authorization, recovery, boundaries, states> | <applicable or N/A because...> | <TM IDs or none with reason> |
| White-box | <changed branches/states/errors, cancellation/retry/timeout, lifecycle/resources, concurrency, idempotency, rollback, property/model/fuzz/fault cases> | <applicable or N/A because...> | <TM IDs or none with reason> |
| Experience-based / exploratory / adversarial | <history, misuse/threat model, red-team or surprising sequences> | <applicable or N/A because...> | <TM IDs or none with reason> |

## Resource ownership

| Resource | Cell and owner | Isolation | Reset | Teardown |
|---|---|---|---|---|
| <resource or none> | TM-1; root | <exclusive or shareable> | <method> | <method> |

## Cells

| Cell | Obligation | Environment | Level and oracle | Required | Attempts | Status | Evidence or blocker |
|---|---|---|---|---|---:|---|---|
| TM-1 | VO-1 | <exact versions and configuration> | <test and pass condition> | yes | 0 | NOT RUN | <artifact path or reason> |

## Oracle validity review

| Oracle cell | Protected behavior and observation point | Failure-sensitivity challenge | Result or evidence gap |
|---|---|---|---|
| Oracle TM-1 | <what must be distinguished and where it is observed> | <pre-fix failure, negative control, local perturbation/mutation, assertion-path inspection, or independent cross-oracle> | <why this test fails when behavior breaks, or OPEN evidence gap> |

## Flaky triage

- <first failure retained, identical retry behavior, classification, owner, and removal condition; or no flaky cells>

## Teardown and leaked resources

- <processes stopped, state reset, leases released, artifact retention, and leaked-resource check>

## Acceptance and release gates

- <required cells, current statuses, waiver owner if any, and claim they gate>
