---
name: dependency-decisions
description: Govern adding, enabling, updating, replacing, removing, vendoring, or selecting libraries, tools, generators, plugins, runtimes, services, and material dependency features. Use before manifest, lockfile, plugin, service, generated dependency metadata, or supply-chain changes; verify current candidates from primary sources and obtain explicit approval for each named option and impact.
---

# Dependency Decisions

For named dependency approval, remain in Default mode and follow `../requirements-design/references/user-interaction.md`; an ordinary answer never replaces the host's authorization surface when one is required.

Treat dependency cost and authority as part of the public engineering contract.

## Procedure

1. Read `references/dependency-governance.md` completely.
2. Establish the exact requirement, existing graph/capability, repository/toolchain/platform constraints, and API surface actually needed.
3. Compare in order: standard/platform facility, existing approved dependency, bounded local implementation, then maintained external candidates.
   For a broad greenfield baseline or capability inventory, read `references/rust-frontend-capability-catalog.md`; it is a question/obligation catalog, not a dependency bundle.
4. Prefer a mature dependency for cryptography, password handling, randomness, Unicode, civil time, complex parsing/compression/protocols, concurrency reclamation, and FFI ownership machinery.
5. Verify version, release status, maintenance, advisories, license, platform/toolchain support, features, native/build scripts, transitive graph, duplicates, runtime cost, lock-in, migration, rollback, and removal path from current primary sources.
   Use `references/ecosystem-snapshot-schema.json` for reusable checked observations; copy `references/ecosystem-snapshot.example.json` only as a refresh-required template, never as current evidence.
   Validate reusable or offline evidence with `scripts/snapshot-tool.py`; a stale or refresh-required result cannot support a new default.
6. Write one `dependency.decision.v1` per independently optional choice. Name exact manifest, lockfile, generated, CI, packaging, and operational impact.
7. Ask a direct approval question naming the candidate and version/feature policy. Stop before mutation until approved.
8. After implementation, validate graph diff, lockfile integrity, advisories/licenses, feature minimization, and rollback.

## Boundaries

- A broad implementation request does not authorize unnamed new dependencies.
- Examples or defaults in another Skill are not approval.
- Do not edit lockfiles by hand or use popularity as a substitute for fit and maintenance evidence.

## Snapshot CLI

```bash
python3 scripts/snapshot-tool.py validate <snapshot.json> --as-of <ISO-date>
```

The validator is offline and standard-library-only. It reports observation-specific fallback instructions when evidence is stale.
