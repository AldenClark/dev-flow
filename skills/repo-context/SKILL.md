---
name: repo-context
description: Resolve repository facts, boundaries, instructions, and readiness without changing product code.
---

# Repository Context

Resolve repository facts before asking. For a user-owned gap, stay in Default mode and follow `../requirements-design/references/user-interaction.md`. Separate observed facts, inference, owner decisions, preferences, and volatile claims.

## Responsibility contract

- Consumes: task scope, paths, and risks.
- Owns: roots, instructions, current behavior, repository controls, observed facts, and context gaps.
- Stops: when a required fact cannot be resolved safely or user-owned changes conflict with scope.
- Hands off: semantics to requirements, causes to debugging, structure to architecture, graphs to dependency, and proof to verification.

## Procedure

1. Resolve every real Git root and the exact paths in scope. Do not infer a root from the workspace directory.
2. Resolve the effective global-to-directory instruction chain. Changed paths select evidence, not instruction precedence.
3. Record consequential rules as stable `INS-n` with source, scope, authority, conflict/freshness, downstream effect, and evidence.
4. Inspect guidance, manifests, CI/native controls, tests/codegen, ADRs, ownership, runtime, analogues, and bounded host Skill roots. Report same-name collisions; an unseen candidate is `not-observed`, not proven uninstalled.
5. Inventory the applicable call, data, error, consumer, artifact, version, loading, and runtime paths. Never hide independent unknowns behind a collective label.
6. Before routing, bind each affected path's phase, role, boundary, language/framework/version, component, and risk.
7. Resolve profiles and bind instruction, profile, native-control, artifact, capability-registry, and Skill-catalog digests. Personal assets are local evidence, not team policy.
8. Derive neutral outcomes first, then select at most one minimal admitted specialist. A named Skill's absence is not a gap when native evidence, an owned fallback, or a waiver covers the outcome.
9. Select the lowest sufficient ECR tier. Read `references/context-readiness.md` for governed/checkpointed work or a readiness diagnosis.
10. Return compact context and recheck triggers. Persist `context-readiness.json` only when required; never auto-write instructions or profiles.

Use the shared assessor when a packet exists. Read `references/repository-discovery.md` when discovery, binding, precedence, runtime truth, or source quality needs detail.

## Output contract

Report roots, instructions, behavior, artifact facts/unknowns, engineering-context fingerprint, tier/reasons, controls, profiles, Skill catalog/collisions, outcomes/routes, gaps, remedies, recheck triggers, and authority limits.

## Boundaries

- Do not decide product semantics, architecture, or dependencies; route those jobs to their owning Skills.
- Do not create, install, enable, or promote a Skill from discovery alone.
- Do not use a personal admission as shared policy without team/project binding or a shared fallback.
- Do not copy full instructions, native configs, Skill bodies, or secrets into snapshots.
- Do not claim that a configuration file proves the associated command passed.
