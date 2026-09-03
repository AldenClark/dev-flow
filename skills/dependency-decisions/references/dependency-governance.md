# Dependency governance

Use this reference for a new dependency, material capability expansion, major/high-impact update, or removal with non-obvious consumers. The goal is a sound dependency decision and reversible implementation, not a second approval ledger. Discovery of a package, vendor, plugin, or tool never itself justifies installing it.

## Decision boundary

An explicit implementation request authorizes an exact routine update or removal when repository evidence resolves the identity and no material choice remains. Ask before adding an unnamed dependency or when candidates differ materially in behavior, security, license, native/toolchain impact, service lock-in, data handling, or long-term ownership.

Dependency approval never authorizes commit, push, release, deployment, credentials, or a new external service account.

## Decision order

1. What observable capability is missing, and what caller, data, platform, performance, and failure constraints define it?
2. Can the standard library or platform facility meet the need?
3. Can an existing dependency do so without harmful feature expansion?
4. Is a bounded local implementation simpler and safe over its lifetime?
5. Which maintained external candidate best fits the exact API and constraints?

Prefer mature libraries for cryptography, authentication, randomness, Unicode, civil time, complex parsing/compression/archive/protocol behavior, concurrency primitives, and FFI ownership. Avoid a local implementation that becomes a hidden subsystem.

## Evidence

Check only decision-relevant facts: current version/release status, maintenance, advisories, license, platform/toolchain support, selected features, build scripts/native code, transitive graph, provenance/supply-chain posture, data/service lock-in, runtime cost, migration, rollback, and removal. Use current primary sources for volatile claims and record a durable decision only when future maintainers need the rationale.

Do not hide independently optional packages in a bundle. When several direct dependencies are coordinated, keep each role and removal boundary visible.

## Implementation and verification

- Use native package tooling and do not hand-edit generated lockfiles.
- Enable the narrowest feature set and inspect manifest, lockfile, generated, CI, packaging, and runtime changes.
- Verify affected behavior and consumers, graph integrity, advisories/licenses, and relevant platform/toolchain combinations in proportion to the changed surface.
- For removals, establish current references and consumers, remove through native tooling, then repeat affected builds/tests and confirm dead configuration or generated surfaces before cleanup.
- Keep unavailable platforms, private registries, external services, or hosted checks explicit as `NOT RUN`.
- Preserve a practical rollback path for high-impact changes: identify data/configuration compatibility, version pin or reverse migration needs, and the removal boundary before the rollout is difficult to reverse.

Another Skill's example or default is advice, not dependency authority. No packet approval, exact command receipt, result digest, or DEP identifier is required for 2.0 work.
