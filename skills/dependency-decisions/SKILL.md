---
name: dependency-decisions
description: Decide whether a new external dependency is justified and reversible; exclude ordinary existing-use changes.
---

# Dependency Decisions

Treat dependency cost, compatibility, supply chain, and exit as part of the engineering contract. Use this Skill for a new or materially expanded library, tool, runtime, service, or high-impact update—not merely because a package is discovered or already used. Read [dependency governance](references/dependency-governance.md) when the decision is material.

This Skill may operate alone for a bounded dependency assessment. If the operation becomes a material repository mutation, crosses consumers or repositories, needs managed continuity, or exposes high-risk delivery, load `dev-flow` as the coordinating kernel when it is available and not already active; keep this Skill as the dependency owner.

## Decide the capability, not the package

1. Identify the missing capability and inspect the nearest caller or manifest needed to establish the gap. Stop if a platform facility or existing capability meets the need at reasonable cost.
2. If a gap remains, consider a bounded local implementation or a credible external candidate. Compare more candidates only when a material trade-off remains. Use established implementations in domains where a local substitute would become a hidden subsystem.
3. Investigate facts that can change the candidate decision, using current primary sources for volatile claims. Establish license and relevant security or platform constraints; inspect native/build code, transitive dependencies, service lock-in, or runtime cost when the candidate introduces those concerns. Select the narrowest suitable API and feature set, and stop researching once the decision is supported.
4. Explain the selected option and any consequential trade-off; include migration, removal, and rollback detail for high-impact changes. Ask promptly when an unnamed dependency or materially different candidates require a product, security, license, service, or ownership choice. Routine identified updates/removals can proceed within existing authorization.
5. Use native package tooling and verify affected behavior and consumers. Inspect graph, feature, build, packaging, or platform effects that the dependency change can cause. Keep unavailable necessary checks as `NOT RUN`; unrelated platforms or services do not create a verification obligation.
6. Preserve a durable rationale only when a future maintainer must understand the trade-off; do not create an approval ledger or turn installation into a default outcome.

Use the snapshot schema and tool only for reusable volatile research; a stale snapshot cannot establish a current default.

## Boundaries

- A broad request does not authorize an unnamed new service, library, plugin, or material feature expansion.
- Popularity is not evidence of fit.
- Dependency approval does not authorize delivery or deployment.
