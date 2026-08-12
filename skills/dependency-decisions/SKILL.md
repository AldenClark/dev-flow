---
name: dependency-decisions
description: Research and govern library, tool, plugin, runtime, service, feature, manifest, lockfile, generated metadata, and supply-chain changes before selection or mutation.
---

# Dependency Decisions

For named dependency approval, remain in Default mode and follow `../requirements-design/references/user-interaction.md`; an ordinary answer never replaces the host's authorization surface when one is required.

Treat dependency cost and authority as part of the public engineering contract.

## Responsibility contract

- Consumes: repository context, an approved capability need, the architecture seam, and exact operation authority.
- Owns: candidate comparison, version/features, approval binding, graph, supply chain, migration, rollback, and removal.
- Stops: before an unapproved addition/material expansion, on stale primary evidence, or when approval does not bind the exact mutation.
- Hands off: semantic choices to requirements, structural consequences to architecture, graph evidence to verification, and artifact evidence to delivery readiness.

## Procedure

Complete safe research and an actionable plan before any approval boundary. An explicit implementation request authorizes its exact existing-dependency removal or routine update as task intent; when repository evidence resolves the identity, command, files, and result bytes without a material choice, bind that original request into the exact machine-readable approval record instead of asking for the same intent again. Stop before mutation when exact binding is impossible or mismatched. This never authorizes an addition, material feature or risk expansion, a different dependency/operation/scope, or mutation during analysis-only or read-only work.

1. Read `references/dependency-governance.md` completely.
2. Classify the exact operation as new/material expansion, routine update, or removal; establish the requirement, current graph/capability, manifest and generated surfaces, repository/toolchain/platform constraints, and API actually needed.
3. For a new dependency or material expansion, compare in order: standard/platform facility, existing approved dependency, bounded local implementation, then maintained external candidates.
   For a broad greenfield baseline or capability inventory, read `references/rust-frontend-capability-catalog.md`; it is a question/obligation catalog, not a dependency bundle.
4. Prefer a mature dependency for cryptography, password handling, randomness, Unicode, civil time, complex parsing/compression/protocols, concurrency reclamation, and FFI ownership machinery.
5. For a new dependency, material expansion, or update, verify version, release status, maintenance, advisories, license, platform/toolchain support, features, native/build scripts, transitive graph, duplicates, runtime cost, lock-in, migration, rollback, and removal path from current primary sources.
   Use `references/ecosystem-snapshot-schema.json` for reusable checked observations; copy `references/ecosystem-snapshot.example.json` only as a refresh-required template, never as current evidence.
   Validate reusable or offline evidence with `scripts/snapshot-tool.py`; a stale or refresh-required result cannot support a new default.
6. Follow the matching operation branch below; do not mix an addition approval gate into an already-authorized existing-dependency removal or routine update.
7. Write one `dependency.decision.v1` per independently optional choice and name exact manifest, lockfile, generated, CI, packaging, and operational impact.

### Operation branches

- New dependency or material expansion: finish the option/source comparison, ask one direct approval question naming candidate, version, features, files, and operational impact, then stop before mutation until the exact approval is present.
- Routine update: preserve the current graph and representative behavior, inspect behavior/feature/native/build/license/advisory and compatibility deltas, bind an explicit matching update request or ask only for an unresolved material choice, apply native tooling, repeat the same checks, and retain rollback.
- Removal: establish a pre-change graph; search source, tests, examples, build scripts, generated inputs/outputs, features, platform targets, and downstream consumers; run and preserve applicable default/minimal/all-feature builds and affected tests, generated consistency, platform, and consumer cells; remove through native tooling without hand-editing the lockfile; repeat the same matrix; inspect graph/lockfile integrity, advisories, and licenses; clean only proven-dead features/configuration/generated/build/documentation surfaces; and record rollback plus every `NOT RUN` environment or consumer.

## Boundaries

- A broad implementation request does not authorize unnamed new dependencies.
- Examples or defaults in another Skill are not approval.
- Do not edit lockfiles by hand or use popularity as a substitute for fit and maintenance evidence.

## Snapshot CLI

```bash
python3 scripts/snapshot-tool.py validate <snapshot.json> --as-of <ISO-date>
```

The validator is offline and standard-library-only. It reports observation-specific fallback instructions when evidence is stale.
