# Dependency governance

## Approval boundary

Require explicit named approval before modifying a manifest, lockfile, tool/plugin configuration, service definition, vendored source, feature set, or generated dependency metadata to add or materially expand a runtime, development, test, build, generator, CLI, plugin, service, or hosted integration.

Already-approved direct dependencies may bring transitive packages, but disclose graph, duplicates, native/build scripts, licenses, advisories, lockfile impact, and removal path. Routine updates remain in scope only when they do not cross a major, security, native-toolchain, license, or behavior boundary.

## Decision order

1. Can the standard library or platform facility meet the requirement?
2. Can an existing approved dependency do so without harmful feature expansion?
3. Is a small local implementation safer and cheaper over its lifetime?
4. Which current maintained external candidate best fits the exact API and constraints?

Use a local implementation only when behavior is small, stable, isolated, fully testable, standards/security risk is low, and it does not create a hidden subsystem. Prefer mature maintained dependencies for cryptography, password handling, randomness, Unicode, civil time, complex parsing/compression/archive/protocol behavior, concurrency primitives/reclamation, FFI ownership, and other deceptive domains.

## Decision record

`dependency.decision.v1` includes:

1. requirement and repository evidence;
2. exact API surface;
3. standard/platform, existing, local, and viable external options;
4. current source links and checked time;
5. capability, maintenance, security, license, toolchain/platform, graph/native/build/runtime, ergonomics, lock-in, migration, rollback, and removal comparison;
6. exact manifest, features, lockfile, generated, CI, packaging, operations, and documentation impact;
7. recommendation, rejected alternatives, validation, and rollback;
8. direct approval request naming candidate and version/feature policy.

Do not hide independently optional packages behind a bundle. A coordinated baseline is one decision only when every direct item and role is named and individually rejectable without invalidating unrelated choices.

## Implementation and verification

Schema 2.0 packet approvals include a `dependency` object with exact `ecosystem`, `name`, human `version`, executable `ref`, canonical full `command` (or null for Actions), normalized `files`, allowed `operations`, and a `result_sha256` map. Package add/update/remove requests must match the full command including flags plus identity before execution; `.exe`/`.cmd` launchers, Cargo toolchain spellings, and ordinary nested shell launchers are recognized, while pre-verb or post-verb path/package/workspace selectors that cannot bind the target file fail closed. Direct manifest/lockfile writes that cannot be bound are denied; final manifest/lockfile bytes must match approved digests. New or updated GitHub Actions and reusable subpaths must match workflow path, action name, operation, and a full commit ref; block/flow mappings, YAML hexadecimal/Unicode escaped quoted keys and values, and every concrete action-like reference in a changed workflow are governed, while dynamic or otherwise unparseable external `uses:` values fail closed. A generic note or unrelated `DEP-n` never authorizes the change.

Task authority and machine binding are separate representations of the same authorized intent, not two user decisions. When the user's implementation request already authorizes an exact existing-dependency removal or routine update and repository evidence deterministically supplies the dependency identity, version, canonical command, affected files, operation, and final digests, record that request as the approval provenance and create the exact machine-readable binding without asking the user to repeat the intent. If any field requires a material choice, the operation/scope differs, final bytes are not yet established, or the request was analysis-only/read-only, do not synthesize authority and stop before mutation. Additions and material feature, security, native-toolchain, license, or behavior expansions always retain their named approval boundary.

- Edit manifests through their native tooling where appropriate; never hand-edit a lockfile.
- Enable the narrowest feature set.
- Inspect direct/transitive graph changes, duplicates, build scripts/native code, licenses, advisories, checksums, and generated changes.
- Verify supported OS/toolchain/architecture and representative downstream builds.
- Document migration, rollback, data/wire consequences, and removal conditions.
- Remove unused dependencies/features only after reference and build verification.

Another Skill's example or default is advisory and never dependency approval.
