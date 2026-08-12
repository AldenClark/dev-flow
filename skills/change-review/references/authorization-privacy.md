# Authorization and privacy review

Load this reference only when the approved task or diff contains an authorization or privacy boundary. Do not mention or apply it to unrelated reviews.

## Authorization completion gate

Before returning an authorization-boundary review, explicitly account for all five groups: (1) the full actor-to-log path; (2) positive and missing, stale, confused, and cross-tenant identities; (3) stable non-enumerating errors, audit events, and credential or personal-data redaction; (4) relevant limits, malformed input, retry, cancellation, and rollback effects; and (5) for each verified finding, severity, affected contract, causal proof, and focused remediation.

When source or execution evidence is absent, preserve each group as an action or `NOT RUN` gate; never invent a finding and never omit the group.

## Privacy-only completion gate

For a privacy-only change, trace the affected data from collection through error, log, metric, audit, retention, access, export, and deletion sinks. Verify minimization, tenant and actor scope, redaction, sampling, access control, failure behavior, and representative secret or personal-data negatives. Do not add an identity matrix unless the changed path actually makes an authorization decision.
