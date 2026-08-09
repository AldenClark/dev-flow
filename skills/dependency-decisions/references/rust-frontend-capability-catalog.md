# Rust and frontend capability decision catalog

Load only the affected section. This preserves the useful capability taxonomy from the former preference catalog without preserving stale versions, popularity claims, or universal package winners. Every external choice still requires current primary-source verification, project fit, and named approval.

## Foundation and service boundaries

- Toolchain: edition/language target, supported compiler/runtime range, formatter/linter components, workspace/package-manager behavior, lockfile policy, public-library minimum-version policy.
- Async/runtime: executor ownership, cancellation, task tracking, timers, signals, blocking isolation, runtime embedding, shutdown and overload.
- Errors/config/serialization: typed library errors, application context, secret-safe diagnostics, configuration precedence/reload, boundary validation, wire compatibility and unknown fields.
- HTTP/API: server/client capability, middleware and state ownership, TLS, proxy semantics, timeouts, body limits, retries, idempotency, OpenAPI or other contract generation/validation.
- RPC/GraphQL/webhook: schema/codegen authority, streaming/backpressure, compatibility, authentication, signing/replay, delivery receipts and retry ownership.

## Data and storage

- Relational databases: existing engine, driver/query model, migrations, compile-time checking, pool limits, transactions, isolation, cancellation, failover and rollback.
- Embedded/local storage: process/thread model, locking, durability, encryption, backup/recovery, corruption handling and upgrade compatibility.
- Search/analytics/object storage: indexing/schema evolution, consistency, pagination, bulk limits, credentials, checksums, multipart recovery, retention and cost.
- Cache: in-process versus shared, bounded capacity, eviction/TTL, load coalescing, stampede prevention, invalidation, serialization, durability and observability.
- Data reliability: outbox/inbox, idempotency keys, deduplication window, replay, schema version, backup/restore drills and migration verification.

## Messaging, tasks, realtime and notifications

- In-process work: structured task ownership, bounded channels, cancellation and drain.
- Durable work: database-backed queue versus broker, visibility/lease, retry with jitter, dead-letter, replay, ordering and poison-item policy.
- Scheduling: clock/time-zone semantics, missed-run/catch-up behavior, leader ownership and duplicate prevention.
- Realtime: SSE, WebSocket, MQTT, WebTransport or native QUIC selected by actual client/network needs; define resume cursor, bounds, heartbeat, idle timeout, payload quota and graceful drain.
- Notifications: narrow sender port, per-channel provider adapter, transactional outbox, idempotency, receipts, suppression/preferences and provider-specific retry.

## Security and supply chain

- Cryptography by purpose: password hashing/KDF, MAC, authenticated encryption, signatures, key exchange, randomness/token generation, hashing/checksums and stable identifiers. Never substitute one purpose for another.
- Secret lifecycle: platform keychain/KMS/Vault/HSM, envelope encryption, versioned key IDs, rotation, zeroization limits, redaction and least privilege.
- TLS and compliance: platform constraints, trust roots, certificate lifecycle, FIPS only when required, and interoperability evidence.
- Supply chain: committed lockfile where appropriate, frozen/locked builds, advisory/license/source policy, build scripts/native code, minimum release age when supported, dependency review, pinned CI actions, SBOM and provenance proportional to release risk.
- Web security: untrusted input validation, authorization/tenant isolation, CSRF/XSS/CSP, cookie/session policy, SSRF, redirect/upload/download boundaries, secrets and safe failure/logging.

## Common algorithms and formats

- Unicode/text: normalization, segmentation, case mapping, collation, locale and confusable/security requirements.
- Time: instant versus civil time, time zone database, DST ambiguity, parsing/format, arithmetic and persistence/wire semantics.
- Encoding/serialization: JSON/CBOR/Protobuf or project contract, canonicalization needs, schema evolution and cross-language vectors.
- Compression/archive: format interoperability, streaming, ratios/limits, decompression bombs, path traversal and reproducibility.
- Parsing/numeric/IDs: standards conformance, arbitrary precision/decimal needs, overflow, locale, stable identity and collision/security model.

## Collections, concurrency, memory and I/O

- Map/set: order, adversarial keys, concurrency, memory, stable iteration and serialization.
- Stable handles/arenas: deletion/reuse, generation checks, compaction, ownership and memory ceiling.
- Shared state/channels/streams: contention, fairness, backpressure, cancellation, close semantics and async/sync boundary.
- Bytes/strings/I/O: ownership, zero-copy value, buffering, partial reads/writes, limits, cancellation and encoding.
- Files/system: atomic replace, permissions, symlinks, temporary resources, locking, watching, sandboxing and platform differences.

## Performance and hardware

- Begin with a representative benchmark/profile and portable idiomatic baseline.
- SIMD/intrinsics: target features, runtime dispatch, alignment/tails, numerical equivalence and scalar fallback.
- Parallelism/NUMA: workload partition, scheduling, affinity, topology, contention and oversubscription.
- Lock-free/high-performance I/O: memory reclamation, ABA, ordering proof, cancellation, kernel/platform support and measurable advantage.
- GPU/accelerators: transfer/compile cost, device availability, determinism, fallback and packaging.
- Build optimization: release profile, LTO/PGO/codegen units, reproducible artifacts, symbol/debug strategy and regression thresholds.

## Extensibility, code generation, IPC and verification

- Macros/build scripts/codegen: schema authority, deterministic output, reviewability, sandbox/network behavior and handwritten/generated separation.
- Plugins/Wasm/WASI: ABI/capability model, sandbox, version negotiation, resource limits, signatures/trust, upgrades and teardown.
- Local IPC/shared memory: peer authentication, framing/versioning, handles, lifetime, synchronization, crash recovery and platform support.
- FFI: stable ABI strategy, layout, strings/buffers, ownership, errors/panics, callbacks, concurrency, cancellation, unload/teardown, symbols and consumer packaging.
- Advanced verification: property/model/fuzz/sanitizer/concurrency/formal techniques selected by invariant/state-space risk, not prestige.

## Frontend product stack

- Runtime/framework/build: preserve existing project choices; for greenfield compare rendering model, server/client boundaries, browser targets, plugin ecosystem, build/test compatibility and deployment.
- Routing/data/state/forms: URL and loader ownership, remote cache versus local UI state, validation boundary, optimistic updates, offline/recovery and accessibility errors.
- Design system/UI: product IA and interaction states, semantic HTML, keyboard/focus, accessible names, contrast/zoom/motion, theming/tokens and component ownership.
- Tables/visualization: data scale, virtualization, sorting/filtering authority, export, responsive behavior, accessible alternatives and rendering cost.
- Testing: unit/component, contract, rendered browser, accessibility and representative end-to-end coverage with isolated projects and first-failure artifacts.
- Performance: bundle budgets, code splitting, image/font/network policy, rendering/profile evidence, cache behavior and field telemetry where authorized.
- Package management: one authoritative manager/lockfile, workspace policy, scripts/build permissions, supply-chain controls and migration cost.

## Native UI, platform integration and domain packs

- Desktop/mobile UI: platform coverage, accessibility, lifecycle, background work, permissions, packaging/signing/notarization and update distribution.
- CLI/TUI: stream contracts, exit codes, terminals, non-interactive use, config, cancellation and scripting compatibility.
- Domain packs are opt-in only: media, geospatial, ML, scientific, finance, healthcare, embedded, games, blockchain or other specialized domains require their own standards, data, safety, licensing and verification evidence.

## Delivery and maintenance

- CI: required platforms/toolchains, cache correctness, generated-diff checks, security/supply-chain checks, artifact retention and least permissions.
- Build/container: multi-stage/reproducible builds, base provenance, non-root runtime, minimal context, health/shutdown and multi-architecture evidence.
- Release/update: semantic compatibility, changelog/migration, signing/checksum/SBOM/provenance, staged rollout, rollback, observation and support policy.
- Deployment: begin with the simplest fitting target; define configuration/secrets, database migration ordering, health/readiness, telemetry, capacity, backup/restore and disaster recovery.
- Documentation: architecture/decision records, public contracts, operations/runbooks, security/unsafe/FFI invariants, generation/update ownership and stale-content triggers.

## Decision output

For every activated capability, record why it applies, why simpler/existing choices do not suffice, current candidates and sources, maturity/freshness, exact API/features, costs and risks, migration/rollback/removal, validation, and explicit approval. Unactivated sections add no dependency and no prompt context.
