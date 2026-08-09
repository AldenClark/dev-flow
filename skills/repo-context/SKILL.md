---
name: repo-context
description: Establish repository-grounded context and task-relative Engineering Context Readiness before diagnosis, design, implementation, audit, or migration. Use to resolve Git roots, scoped instructions, manifests, architecture and call paths, current behavior, native commands and quality controls, profile sources, active-host capability candidates, and T0-T3 ECR/EQAC gaps without authorizing product changes.
---

# Repository Context

If a context gap truly requires user input, remain in Default mode and follow `../requirements-design/references/user-interaction.md`; inspect repository-resolvable facts instead of asking.

Establish facts before recommendations. Keep observed facts, inference, owner decisions, preferences, and volatile ecosystem claims separate.

## Procedure

1. Resolve every real Git root and the exact paths in scope. Do not infer a root from the workspace directory.
2. Discover global, root, and nested instruction files for those paths. Apply host-native precedence and report hidden overrides.
3. Inspect manifests, CI, scripts, toolchains, tests, code generation, ADRs, ownership, runtime configuration, and nearby working analogues.
4. Trace the relevant entry point, call/data flow, state, boundaries, errors, and current behavior. Reproduce or measure when the claim depends on runtime behavior.
5. Detect languages by affected artifacts, not repository labels. Record each artifact role and boundary separately.
6. Resolve the known Dev Flow manifest and profiles without treating their values as repository facts. Do not inventory arbitrary machine paths.
7. Select the lowest sufficient ECR tier and assess only applicable dimensions. Read `references/context-readiness.md` for tier, outcome, reminder, waiver, and EQAC rules.
8. Write `context.snapshot.v1`; when ECR applies, write `context-readiness.json`. Never write project instructions or profiles as an automatic remedy.

Use the shared deterministic assessor when a packet exists:

```bash
python3 ../dev-flow/scripts/dev-flow.py assess-context \
  --root <repo> --task-type <type> --packet <packet> \
  --path <scoped-path> --risk <risk>
```

Read `references/repository-discovery.md` for instruction, repository, runtime, and source-quality discovery details.

## Output contract

Report roots, scoped instruction chain, current behavior, facts and unknowns, selected tier and reasons, readiness outcome, native controls, applicable profile sources, quality obligations/routes/gaps, minimal remedy, recheck triggers, and authority limits. Missing `AGENTS.md`, a personal profile, or a named Skill is never by itself a blocker.

## Boundaries

- Do not decide product semantics, architecture, or dependencies; route those jobs to their owning Skills.
- Do not create, install, enable, or promote a Skill from discovery alone.
- Do not copy full instructions, native configs, Skill bodies, or secrets into snapshots.
- Do not claim that a configuration file proves the associated command passed.
