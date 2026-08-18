# Red audit: <change-id>

> Legacy packet compatibility template. Direct and managed 2.0 review uses the current diff and native evidence without this artifact.

## Audit brief

<Independent reviewer, clean brief path, attack/failure surface, allowed actions, and evidence date.>

- Applicable instructions: <INS IDs included in the adversarial review>

## Threat and failure hypotheses

- <abuse, malformed input, authorization, concurrency, cancellation, data loss, compatibility, rollback, or resource-exhaustion hypothesis>

## Adversarial checks

| Hypothesis | Experiment or inspection | Oracle | Evidence | Result |
|---|---|---|---|---|
| <RED-H1> | <safe check> | <expected invariant> | <artifact> | <supported or rejected> |

## Finding classification and requirement reopening

<Classify each finding as an implementation defect, design defect, evidence gap, scope change, or requirement ambiguity. A user-owned material/high-risk ambiguity must name its AMB ID, affected IDs, and reopening disposition; the reviewer must not silently turn an assumption into the requirement.>

## Findings

| Finding | Severity | Evidence | Verification | Status |
|---|---|---|---|---|
| <RED-1 or none> | <critical to note> | <path or command> | <how verified> | <open or closed> |

## Disposition

<Accept, repair, defer with approval, or block; include repair round and scoped re-review evidence.>
