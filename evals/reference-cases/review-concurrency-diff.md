# Concurrency diff review reference case

Fixture assumptions: a patch parallelizes retrying delivery and changes shutdown order. A good first attempt identifies owners, bounds, ordering and duplicate-delivery semantics, checks cancellation/join/drain/leak paths and durable state, verifies causal failures with focused tests, and preserves a rollback path rather than reporting style-only concerns.
