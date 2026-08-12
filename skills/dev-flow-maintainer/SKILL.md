---
name: dev-flow-maintainer
description: Explicit-only maintenance of Dev Flow schemas, routing, host adapters, hooks, governance, compatibility, capability contracts, migrations, and evaluations.
---

# Dev Flow Maintainer

For public-contract or breaking-migration decisions, remain in Default mode and follow `../requirements-design/references/user-interaction.md`.

Maintain the suite as a versioned product with measurable trigger, context, safety, and compatibility behavior.

## Responsibility contract

- Consumes: explicit suite scope, a persistent packet, public-surface inventory, and compatibility evidence.
- Owns: Dev Flow Skills, schemas, routing, hooks, migrations, governance, and evaluation policy.
- Stops: without explicit suite scope, before an unapproved breaking contract, or when quality admission has not been proved.
- Hands off: suite semantics/architecture/dependencies to their decision owners, then verification, independent review, and explicit delivery.

## Procedure

1. Require explicit Dev Flow maintenance scope and a persistent packet. Inventory public Skills, commands, schemas, hooks, roles, docs, evals, and installed-runtime compatibility.
2. Apply the promotion test before adding or merging a Skill: direct trigger, bounded artifact, negative trigger, decision ownership, independent evaluation, and material context/authority benefit.
3. Keep Skill entrypoints concise and progressively load focused references. Validate `agents/openai.yaml` against each entrypoint.
4. Maintain neutral policies separately from user/team/project values and current ecosystem snapshots.
5. Read `references/maintenance-contract.md` before changing public names, schemas, routing, or cutover behavior.
6. Read `references/capability-registry.json` before changing EQAC capability IDs or candidate routes. Installation is inventory; local host admission owns activation.
7. First prove exact routing, work mode, owner outputs, stop/handoff behavior, collisions, compatibility, safe counterexamples, and representative repository workflows with deterministic tests.
8. Run paired model evaluation only for a material model-dependent behavior or release comparison after those gates pass; never let the evaluator define ownership or drive case-specific Skill text.
9. Preserve first failures, migration provenance, rollback, and exact content disposition. Publish only the integrated suite.

Use `scripts/validate-suite.py` for the maintainer-specific inventory and dangling-route gate before the repository-wide checks.

## Boundaries

- Never edit or promote personal/team/project profile values as suite maintenance.
- Never auto-install, auto-enable, or silently rewrite third-party Skills/plugins.
- Never treat structural validity as quality admission or publish internal waves as supported partial architecture.
