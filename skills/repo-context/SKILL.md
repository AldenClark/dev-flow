---
name: repo-context
description: Resolve Git roots, effective instructions, manifests, call paths, current behavior, native commands, profiles, and task-relative context readiness without mutating product code.
---

# Repository Context

If a context gap truly requires user input, remain in Default mode and follow `../requirements-design/references/user-interaction.md`; inspect repository-resolvable facts instead of asking.

Establish facts before recommendations. Keep observed facts, inference, owner decisions, preferences, and volatile ecosystem claims separate.

## Procedure

1. Resolve every real Git root and the exact paths in scope. Do not infer a root from the workspace directory.
2. Discover the host-native instruction chain from global scope and repository root to the effective working directory. Keep changed paths as evidence selectors, not instruction-precedence inputs.
3. Inspect manifests, CI, scripts, toolchains, tests, code generation, ADRs, ownership, runtime configuration, and nearby working analogues.
4. Trace the relevant entry point, call/data flow, state, boundaries, errors, and current behavior. Reproduce or measure when the claim depends on runtime behavior.
5. Detect languages by affected artifacts, not repository labels. Record each artifact role and boundary separately.
6. Resolve the known Dev Flow manifest and profiles without treating their values as repository facts. Do not inventory arbitrary machine paths.
7. Select the lowest sufficient ECR tier and assess only applicable dimensions. Read `references/context-readiness.md` only for governed/checkpointed work or when diagnosing a readiness decision.
8. Return a compact context result. Persist `context-readiness.json` only when a packet or explicit output requires it. Never write project instructions or profiles as an automatic remedy.

Use the shared deterministic assessor when a packet exists:

```bash
python3 ../dev-flow/scripts/dev-flow.py assess-context \
  --root <repo> --task-type <type> --packet <packet> \
  --path <scoped-path> --risk <risk>
```

Read `references/repository-discovery.md` only when roots, instruction precedence, runtime truth, or source quality remain unclear after the direct inspection.

## Output contract

Report roots, scoped instruction chain, current behavior, facts and unknowns, selected tier and reasons, readiness outcome, native controls, applicable profile sources, quality obligations/routes/gaps, minimal remedy, recheck triggers, and authority limits. Missing `AGENTS.md`, a personal profile, or a named Skill is never by itself a blocker.

## Boundaries

- Do not decide product semantics, architecture, or dependencies; route those jobs to their owning Skills.
- Do not create, install, enable, or promote a Skill from discovery alone.
- Do not copy full instructions, native configs, Skill bodies, or secrets into snapshots.
- Do not claim that a configuration file proves the associated command passed.
