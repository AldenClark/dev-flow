---
name: repo-context
description: Use when repository facts, ownership, or an evidence handoff block the next decision; not for self-contained work.
---

# Repository Context

Establish the smallest fact base for the next decision; resolve repository facts yourself.

Use alone for narrow read-only lookup. For material or cross-boundary work, use `dev-flow` as coordinator when available.

## First action

Name the missing decision evidence; inspect the smallest path that can change it. Do not inventory an unfamiliar repository by default.

## Procedure

1. Resolve Git roots, scope, effective instructions, and protected user changes before mutation.
2. Inspect relevant source, tests, contracts, configuration, generated surfaces, consumers, and normal/error paths. Separate facts from inference.
   A target/reference comparison is atomic even without paths: inspect the bounded repository before asking. With one plausible pair, inspect both before any answer; that response must name each side's facts, differences, and authority. Never omit either side. Otherwise state ambiguity and ask. Analogy is non-authoritative.
3. Trace affected calls, data, errors, artifacts, and compatibility only as far as the next decision requires.
4. Find applicable project-native start, health, focused-test, boundary-oracle, targeted-log, and recovery controls. If a missing control blocks the outcome, hand its smallest repair point to `test-system-engineering`. For external effects, identify the intended actor/source and target effect. Configured is not passed.
5. For target-environment outcomes, trace applicable source → artifact → actual install → effective config/data → user effect → observation/recovery links. Hand evidence gaps to `verification` and action readiness to `delivery-readiness`; host evidence cannot prove a target result.
6. Select specialist Skills from affected evidence and the current-turn catalog only; offer honest native/manual fallbacks. Surface `repository-knowledge` for observed missing ownership, chat-only material handoff, or stale/conflicting durable truth.
7. Return facts, inference, unknowns, boundaries, useful routes, and recheck triggers. Changes to source, artifact, target, config, or data may invalidate the fact base.

## Stop

Stop when the next owner can decide from facts and explicit unknowns. Route product choices to `requirements-design`; refresh only contradicted paths.

Read `references/repository-discovery.md` for complex roots, instructions, or runtime paths. `references/context-readiness.md` diagnoses insufficient context; it is not a gate.

## Boundaries

- Do not decide product semantics, architecture, dependencies, or verification outcomes.
- Do not create routine ledgers, install Skills from discovery, or load every matching Skill.
- Keep volatile observations and secrets out of maintained documentation.
