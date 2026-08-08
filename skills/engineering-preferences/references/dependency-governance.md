# Dependency governance

## Approval boundary

Require explicit user approval before changing a manifest, lockfile, tool configuration, service definition, generated dependency metadata, or vendored source in order to:

- add a direct runtime, development, test, or build dependency;
- add an external CLI, code generator, runtime, service, plugin, or hosted integration;
- enable a feature that materially expands the transitive graph, runtime capability, native build, or platform surface;
- replace a major dependency or framework;
- vendor or copy third-party code.

Continue safe repository analysis while waiting, but do not cross this boundary. A broad implementation request does not silently waive dependency approval unless the user explicitly pre-authorized the exact dependency or category.

Approved direct dependencies may bring transitive dependencies without one approval per crate/package, but disclose the graph, duplicates, native components, licenses, advisories, and lockfile impact.

## Decision sequence

Evaluate in this order:

1. Can the standard library or platform API satisfy the requirement?
2. Can an already-approved dependency satisfy it without a problematic feature expansion?
3. Is a small local implementation safer and cheaper over its lifetime?
4. Which maintained dependency best fits the actual API surface and constraints?

Do not use a dependency merely because a specialist Skill includes it in an example.

## Build-versus-buy rule

Prefer a local implementation when all are true:

- the behavior is small, stable, isolated, and completely testable;
- edge cases and standards compliance are bounded and understood;
- the implementation does not create a hidden maintenance subsystem;
- security and cross-platform risk are low;
- the dependency would be used only for a trivial API fragment and has disproportionate cost.

Prefer a mature dependency for cryptography, password handling, randomness, Unicode, civil time, complex parsing, compression and archive safety, protocols, serialization formats, concurrency primitives, memory reclamation, FFI ownership machinery, or other deceptively difficult standards work.

## Required decision card

Verify current versions, maintenance, advisories, license, toolchain/platform support, and release status from primary sources immediately before presenting the card. This catalog establishes direction, not current-version facts.

Before approval, report:

1. Requirement and repository evidence.
2. Exact API surface to be used.
3. Standard-library, existing-dependency, and local-implementation options.
4. Two or three viable external candidates when they exist.
5. Comparison of capability, maintenance, security, license, compatibility, dependency graph, native code, build and runtime cost, ergonomics, lock-in, migration, and rollback.
6. Exact manifest, feature, lockfile, generated-file, and CI impact.
7. Recommendation, rejected alternatives, validation, and rollback plan.
8. A direct approval question naming the proposed dependency and version policy.

Do not hide many independently optional dependencies behind one blanket approval. A coordinated baseline may be approved as one bundle only when every direct dependency is named, its exact role and feature policy are visible, optional items are separated, and the user can reject an item without invalidating unrelated choices.

When the sibling `dev-flow` Skill is active, use its `templates/dependency-decision.md`.

## Updates and removals

- A requested routine update of an existing dependency does not count as a new dependency, but major-version, security-sensitive, native-toolchain, license, or behavior changes still require an explicit option comparison.
- Prefer removing unused dependencies and features after reference and build verification.
- Keep one implementation per concern unless a staged migration has an explicit exit condition.
- Never edit a lockfile by hand.
