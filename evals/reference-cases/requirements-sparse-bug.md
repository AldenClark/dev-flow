# Sparse bug requirement reference case

Fixture assumptions: “fix duplicate notifications” is the entire request, while repository tests, idempotency keys, retry code, and logs identify a clear regression. A good first attempt investigates those facts, records the existing contract and bounded acceptance/scope/verification IDs, fixes only the causal path, and does not ask the user to restate repository-discoverable behavior.
