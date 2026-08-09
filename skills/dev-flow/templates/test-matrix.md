# Test matrix: <change-id>

## Dimensions and selection rationale

- Instruction mapping: <INS IDs and the cells that prove them>
- ECR/EQAC mapping: <tier, applicable obligations, selected controls/routes/fallbacks, and cells that verify them>
- <OS, browser, device, architecture, version, feature, data, or configuration dimension and why selected>

## Resource ownership

| Resource | Cell and owner | Isolation | Reset | Teardown |
|---|---|---|---|---|
| <resource or none> | TM-1; root | <exclusive or shareable> | <method> | <method> |

## Cells

| Cell | Obligation | Environment | Level and oracle | Required | Attempts | Status | Evidence or blocker |
|---|---|---|---|---|---:|---|---|
| TM-1 | VO-1 | <exact versions and configuration> | <test and pass condition> | yes | 0 | NOT RUN | <artifact path or reason> |

## Flaky triage

- <first failure retained, identical retry behavior, classification, owner, and removal condition; or no flaky cells>

## Teardown and leaked resources

- <processes stopped, state reset, leases released, artifact retention, and leaked-resource check>

## Acceptance and release gates

- <required cells, current statuses, waiver owner if any, and claim they gate>
