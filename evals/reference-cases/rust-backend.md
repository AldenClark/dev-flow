# Rust backend reference case

Fixture assumptions: existing Axum/Tokio service, SQL-backed job state, graceful shutdown tests, no external broker. A good first attempt traces enqueue-to-ack lifecycle, derives semantics from repository facts, prefers existing capabilities, documents complete scope, and proves retry/dedup/restart/drain behavior without prescribing Kafka or JetStream.
