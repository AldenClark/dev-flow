---
name: dev-flow-maintainer
description: Explicit-only maintenance of Dev Flow schemas, routing, host adapters, hooks, governance, compatibility, capability contracts, migrations, and evaluations.
---

# Dev Flow Maintainer

For public-contract or breaking-migration decisions, remain in Default mode and follow `../requirements-design/references/user-interaction.md`.

Maintain the suite as a versioned product whose core workflow quality comes first and whose evaluation stays proportionate, diagnostic, and claim-bounded.

## Responsibility contract

- Consumes: explicit suite scope, repository workstream knowledge when continuity requires it, public-surface inventory, and compatibility evidence.
- Owns: Dev Flow Skills, schemas, routing, hooks, migrations, governance, and evaluation policy.
- Stops: without explicit suite scope, before an unapproved breaking contract, or before making a release/admission claim whose applicable evidence is missing.
- Hands off: suite semantics/architecture/dependencies to their decision owners, then verification, risk-triggered independent review, and explicit delivery.

## Procedure

1. Require explicit Dev Flow maintenance scope. Use managed repository documents only when continuity warrants it; never require a packet. Inventory public Skills, commands, schemas, hooks, roles, docs, evals, and installed-runtime compatibility.
2. Apply the promotion test before adding or merging a Skill: direct trigger, bounded primary outcome or artifact, negative trigger, decision ownership, independent evaluation, and material context/authority benefit.
3. Keep Skill entrypoints concise and progressively load focused references. Validate `agents/openai.yaml` against each entrypoint.
4. Maintain neutral policies separately from user/team/project values and current ecosystem snapshots.
5. Read `references/maintenance-contract.md` before changing public names, schemas, routing, or cutover behavior.
6. Read `references/capability-registry.json` before changing EQAC capability IDs or candidate routes. Installation is inventory; local host admission owns activation.
7. First prove direct/managed routing, overlay composition, owner boundaries, stop/handoff behavior, compatibility, safe counterexamples, and representative repository workflows with deterministic tests.
8. When an explicitly authorized release or capability-admission decision depends materially on model interpretation, predeclare the affected categories and budget, then run the configured minimum of three distinct cases per category with at least three independent first attempts after deterministic gates pass. For local iteration, use one focused diagnostic only when it can resolve a concrete uncertainty. Reserve the frozen full comparison for a separately authorized and budgeted release decision.
9. When model evaluation runs, keep safety/authority hard gates separate from outcome, variability, fidelity/retention/rework, and cost. Do not derive one overall quality number. Audit every new failure transcript and a rotating sample of passes for candidate, grader, case, contamination, or infrastructure defects.
10. Freeze evaluator/schema growth unless a core invariant is otherwise unobservable; record the smaller rejected alternative, owner, cost, rollback, and removal condition. Preserve first failures, migration provenance, and exact content disposition. Publish only the integrated suite.

Use `scripts/validate-suite.py` for the maintainer-specific inventory and dangling-route gate before the repository-wide checks.

For an explicitly authorized local dogfood audit, pass only the aggregate-safe observation schema to `scripts/analyze_dogfood.py`. The analyzer accepts no transcript text, task/session IDs, absolute paths, credentials, personal values, or free-form notes; it reports task shapes, transitions, correction categories, scope conformance, and the method eligibility/activation/selection/readiness/disposition/realization funnel without a person, repository, productivity, or composite quality score. Unsupported direct host-history access is `BLOCKED`; do not read private host storage or persist a profile from aggregates.

## Boundaries

- Never edit or promote personal/team/project profile values as suite maintenance.
- Never auto-install, auto-enable, or silently rewrite third-party Skills/plugins.
- Never use a model score or confidence interval as population truth or repository/release proof.
- Never treat structural validity as quality admission or publish internal waves as supported partial architecture.
