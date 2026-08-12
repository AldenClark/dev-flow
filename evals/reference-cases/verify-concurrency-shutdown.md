# Concurrency shutdown verification reference case

Fixture assumptions: a background worker intermittently hangs during shutdown when retries and cancellation overlap. A good first attempt preserves the first failure, names task/resource owners and join paths, builds a deterministic interleaving or bounded stress reproducer, checks timeout/drain/leak behavior, and separates a product race from test or environment instability.
