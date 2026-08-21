---
name: dependency-decisions
description: Evaluate and implement dependency additions, updates, removals, tools, services, plugins, runtimes, and supply-chain changes with proportionate evidence.
---

# Dependency Decisions

Treat dependency cost, compatibility, supply chain, and removal as part of the engineering contract. Read `references/dependency-governance.md` for a new dependency, material capability expansion, or high-impact update.

This Skill may operate alone for a bounded dependency assessment. If the operation becomes a material repository mutation, crosses consumers or repositories, needs managed continuity, or exposes high-risk delivery, load `dev-flow` as the coordinating kernel when it is available and not already active; keep this Skill as the dependency owner.

## Procedure

1. Classify the operation: new/material expansion, routine update, or removal. Establish the capability need, current graph, manifests, lockfiles/generated surfaces, toolchain/platform constraints, and API actually used.
2. For a new dependency, compare standard/platform facilities, an existing dependency, a bounded local implementation, and maintained external candidates. Prefer proven libraries for cryptography, Unicode, time, complex protocols/parsing/compression, and FFI ownership.
3. Check decision-relevant current evidence: version/release status, maintenance, advisories, license, platform/toolchain support, selected features, build/native code, transitive graph, runtime cost, migration, rollback, and removal.
4. Ask for a material choice or unnamed new capability. An explicit implementation request normally authorizes an exact routine update or removal when repository evidence resolves the operation and no material choice remains.
5. Use native package tooling; do not hand-edit generated lockfiles. Inspect manifest, lockfile, generated, CI, packaging, and runtime effects.
6. Run affected behavior, graph, advisory/license, feature/platform, and consumer checks in proportion to the changed surface. Report unavailable environments as `NOT RUN`.
7. Record a durable dependency decision only when future maintainers need the rationale.

Use the snapshot schema and tool only for reusable volatile research; a stale snapshot cannot establish a current default.

## Boundaries

- A broad request does not authorize an unnamed new service, library, plugin, or material feature expansion.
- Popularity is not evidence of fit.
- Dependency approval does not authorize delivery or deployment.
