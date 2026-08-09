---
name: dev-flow-maintainer
description: Explicit-only maintenance of the public Dev Flow Skill suite, including schemas, resolver/readiness logic, capability taxonomy and admission contracts, routing, migrations, hooks, role assets, compatibility, governance, structural contracts, and paired evaluations. Use only when the user asks to change Dev Flow itself; never auto-activate during ordinary repository product work or own personal/team/project profile values.
---

# Dev Flow Maintainer

Maintain the suite as a versioned product with measurable trigger, context, safety, and compatibility behavior.

## Procedure

1. Require explicit Dev Flow maintenance scope and a persistent packet. Inventory public Skills, commands, schemas, hooks, roles, docs, evals, and installed-runtime compatibility.
2. Apply the promotion test before adding or merging a Skill: direct trigger, bounded artifact, negative trigger, decision ownership, independent evaluation, and material context/authority benefit.
3. Keep Skill entrypoints concise and progressively load focused references. Validate `agents/openai.yaml` against each entrypoint.
4. Maintain neutral policies separately from user/team/project values and current ecosystem snapshots.
5. Read `references/maintenance-contract.md` before changing public names, schemas, routing, or cutover behavior.
6. Read `references/capability-registry.json` before changing EQAC capability IDs or candidate routes. Installation is inventory; local host admission owns activation.
7. Add deterministic structure/schema/compatibility tests plus positive, negative, collision, safe-counterexample, unrelated-change, and cross-language cases.
8. Run paired with/without-Skill evaluations on fixed artifacts. Measure coverage, restraint, retention, actionability, rework, context cost, unsafe actions, reminders, and false blocks.
9. Preserve first failures, migration provenance, rollback, and exact content disposition. Publish only the integrated suite.

Use `scripts/validate-suite.py` for the maintainer-specific inventory and dangling-route gate before the repository-wide checks.

## Boundaries

- Never edit or promote personal/team/project profile values as suite maintenance.
- Never auto-install, auto-enable, or silently rewrite third-party Skills/plugins.
- Never treat structural validity as quality admission or publish internal waves as supported partial architecture.
