---
name: repo-context
description: Resolve repository facts, boundaries, instructions, and readiness without changing product code.
---

# Repository Context

Resolve repository facts before asking. For a user-owned gap, remain in Default mode and follow `../requirements-design/references/user-interaction.md`.

Establish facts before recommendations. Keep observed facts, inference, owner decisions, preferences, and volatile ecosystem claims separate.

## Responsibility contract

- Consumes: task scope, paths, and risks.
- Owns: roots, instructions, current behavior, repository controls, observed facts, and context gaps.
- Stops: when a required fact cannot be resolved safely or user-owned changes conflict with scope.
- Hands off: semantics to requirements, causal uncertainty to debugging, structural choices to architecture, graph choices to dependency, and proof to verification.

## Procedure

1. Resolve every real Git root and the exact paths in scope. Do not infer a root from the workspace directory.
2. Discover the host-native instruction chain from global scope and repository root to the effective working directory. Keep changed paths as evidence selectors, not instruction-precedence inputs.
3. Record consequential rules as stable `INS-n` with source, scope, authority, conflict/freshness, downstream effect, and final evidence.
4. Inspect task guidance and local Skills, manifests, CI, scripts, formatter/linter/toolchains, tests, code generation, ADRs, ownership, runtime configuration, and nearby analogues.
5. Inventory the applicable call, data, error, consumer, artifact, version, loading, and runtime paths. Preserve independently variable facts separately; collective labels never replace a material unknown.
6. Detect languages by affected artifacts, not repository labels. Record each artifact role and boundary separately.
7. Resolve the known Dev Flow manifest and profiles without treating their values as repository facts. Do not inventory arbitrary machine paths.
8. Select the lowest sufficient ECR tier and assess only applicable dimensions. Read `references/context-readiness.md` only for governed/checkpointed work or when diagnosing a readiness decision.
9. Return a compact context result. Persist `context-readiness.json` only when a packet or explicit output requires it. Never write project instructions or profiles as an automatic remedy.

Use the shared deterministic assessor when a packet exists. Read `references/repository-discovery.md` only when roots, instruction precedence, runtime truth, or source quality remain unclear.

## Output contract

Report roots, instructions, current behavior, facts/unknowns, tier/readiness reasons, native controls, applicable profiles, quality gaps, remedies, recheck triggers, and authority limits. Missing optional assets are not blockers by name.

## Boundaries

- Do not decide product semantics, architecture, or dependencies; route those jobs to their owning Skills.
- Do not create, install, enable, or promote a Skill from discovery alone.
- Do not copy full instructions, native configs, Skill bodies, or secrets into snapshots.
- Do not claim that a configuration file proves the associated command passed.
