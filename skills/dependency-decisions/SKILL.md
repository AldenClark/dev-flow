---
name: dependency-decisions
description: Decide whether a new external dependency is justified and reversible; exclude ordinary existing-use changes.
---

# Dependency Decisions

Treat dependency cost, compatibility, supply chain, and exit as part of the engineering contract. Use this Skill for a new or materially expanded library, tool, runtime, service, or high-impact update—not merely because a package is discovered or already used. Read [dependency governance](references/dependency-governance.md) when the decision is material.

This Skill may operate alone for a bounded dependency assessment. If the operation becomes a material repository mutation, crosses consumers or repositories, needs managed continuity, or exposes high-risk delivery, load `dev-flow` as the coordinating kernel when it is available and not already active; keep this Skill as the dependency owner.

## Decide the capability, not the package

1. Name the capability gap, its callers, constraints, and success/failure behavior. Inspect the actual manifests, lockfiles, selected features, current graph, platform/toolchain, generated surfaces, and existing capabilities before looking for a package.
2. Compare platform/standard facilities, an existing dependency without harmful expansion, a bounded local implementation, and credible external candidates. A package's existence, popularity, or a Skill example is not a reason to install it; use established implementations for domains where a local substitute is a hidden subsystem.
3. For candidates that remain, use current primary sources for decision-relevant facts: maintenance and releases, advisories, license, provenance/supply-chain posture, native/build code, transitive graph, data/service lock-in, and runtime/platform cost. Select the narrowest API and feature set that meets the need.
4. Explain the minimum selected option, rejected alternatives, migration impact, removal boundary, and a practical rollback. Ask when an unnamed capability or materially different candidates require a product, security, license, service, or ownership choice; routine identified updates/removals can proceed only within existing authorization.
5. Use native package tooling, then verify affected behavior and consumers plus relevant graph, advisory/license, feature, build, packaging, and platform evidence. Keep unavailable registries, platforms, services, or hosted checks as `NOT RUN`.
6. Preserve a durable rationale only when a future maintainer must understand the trade-off; do not create an approval ledger or turn installation into a default outcome.

Use the snapshot schema and tool only for reusable volatile research; a stale snapshot cannot establish a current default.

## Boundaries

- A broad request does not authorize an unnamed new service, library, plugin, or material feature expansion.
- Popularity is not evidence of fit.
- Dependency approval does not authorize delivery or deployment.
