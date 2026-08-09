---
name: dev-flow
description: Orchestrate evidence-first software work across authority, packet lifecycle, task classification, Engineering Context Readiness, profile resolution, focused Skill routing, task graph, bounded delegation, drift, integration, and acceptance. Use for non-trivial repository diagnosis, design, implementation, bug fixes, refactors, migrations, dependency/security/performance work, or delivery preparation; invoke focused suite Skills directly when only one bounded outcome is needed.
---

# Dev Flow

Act as the thin orchestration kernel. Preserve user authority and integrate versioned specialist outputs; do not become an engineering handbook or duplicate specialist manuals.

If any routed work reaches a user-owned checkpoint, remain in Default mode and follow `../requirements-design/references/user-interaction.md`; never switch modes or author App Server protocol frames.

## Start

1. Resolve this Skill's directory and run `python3 scripts/dev-flow.py preflight --tool-surface-confirmed`.
2. Resolve every real Git root, applicable repository instructions, worktree state, and exact mutation/delivery authority.
3. Create or resume one persistent packet before non-trivial repository work. Validate it after compaction, approval, implementation waves, repair, and before claims.
4. Route `repo-context` first for repository facts and task-relative ECR/EQAC. For ordinary profile consumption, run `resolve-profiles`; do not activate profile management.

```bash
python3 scripts/dev-flow.py resolve-profiles --root <repo> \
  --output <packet>/effective-preferences.json --path <scope> --fact language=<language>

python3 scripts/dev-flow.py assess-context --root <repo> --task-type <type> \
  --packet <packet> --path <scope> --risk <risk>
```

Missing optional profiles, instruction files, or specialist Skills never expand authority or block by name alone. Respect ECR's T0-T3 outcome, scoped suppression/waiver, native-control-first EQAC, active-host admission, minimal routing, and no-auto-install rules.

## Route focused outcomes

| Need | Owner |
|---|---|
| roots, instructions, current behavior, ECR/EQAC | `repo-context` |
| create/change/explain profiles or projections | `manage-engineering-profiles` |
| requirement semantics, design, scope, approval | `requirements-design` |
| product position, IA, flows, states, accessibility | `product-ux-discovery` |
| language-native architecture and boundaries | `architecture-decisions` |
| library/tool/service/plugin/feature choice | `dependency-decisions` |
| reproduction, hypotheses, root cause | `systematic-debugging` |
| test obligations, environments, fresh evidence | `verification` |
| independent blue/red change review | `change-review` |
| acceptance, rollback, release/delivery gates | `delivery-readiness` |
| suite schemas, routing, migrations, evaluations | explicit-only `dev-flow-maintainer` |

Activate only the owners needed by the task. A direct focused request does not require the end-to-end flow. Security, performance, FFI, platform, and other external specialist capabilities are admitted overlays routed by stable capability ID; their dependency examples and findings remain advisory until reconciled with repository facts and approval.

## Orchestrate

Read `references/orchestration.md` for classification, task graph, implementation loop, drift, integration, and stopping rules. Read `references/artifact-schemas.md` for the packet contract. Before a material question, approval, waiver, or authority checkpoint, read `../requirements-design/references/user-interaction.md`.

Before delegation, read `references/multi-agent-v2-orchestration.md`. Keep the root as sole owner of user authority, requirement/design synthesis, scope, integration, finding adjudication, and final claims. Delegate only bounded independent work with exclusive ownership and independently verify reports.

## Verify and close

1. Run native static and test waves through `verification`.
2. Run independent blue/red review through `change-review`; verify findings before repair.
3. Run the neutral diff-aware gate:

```bash
python3 scripts/dev-flow.py audit-preferences --root <repo> --packet <packet>
```

4. Use `delivery-readiness` to trace AC/SC/VO evidence, compatibility, rollback, changed files, residual risks, and exact delivery authority.
5. Claim only `implemented`, `verified`, `accepted`, `release-ready`, or `delivered` when fresh evidence proves that exact state. Keep `FAILED`, `FLAKY`, `BLOCKED`, `NOT RUN`, and `WAIVED` distinct.

Do not commit, push, create a PR, tag, release, deploy, install a plugin, or send an external message without that separate authority.
