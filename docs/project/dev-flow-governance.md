# Dev Flow project governance

[Knowledge catalog](./catalog.json)

- Knowledge ID: `KT-DEV-FLOW-GOVERNANCE`
- Owner: Dev Flow maintainers.
- Review triggers: a lifecycle, capability-owner, packet schema, hook, knowledge-root, or acceptance-policy change.
- Source anchors: the [plugin manifest](../../.codex-plugin/plugin.json), [capability registry](../../governance/capability-contracts.json), [orchestrator Skill](../../skills/dev-flow/SKILL.md), [packet implementation](../../skills/dev-flow/scripts/dev_flow.py), [knowledge contract](../../skills/dev-flow/references/knowledge-system.md), and [contract-check entry point](../../evals/run_contract_checks.py).

## Current truth

Dev Flow is packaged as a Codex plugin by `.codex-plugin/plugin.json`. Its registered capability owners and their inputs, outputs, stops, handoffs, and orchestration conditions are declared in `governance/capability-contracts.json`; repository checks derive the registered inventory from that contract rather than treating a fixed count as the design goal.

The repository's lifecycle CLI is implemented in `skills/dev-flow/scripts/dev_flow.py`, its repository hook entry point is `hooks/dev_flow_hook.py`, and deterministic contract checks enter through `evals/run_contract_checks.py`. Behavioral claims about those surfaces require fresh evidence against the claimed bytes.

Persistent mutation now carries an always-on compact quality kernel. Specialist Skills add depth but cannot remove requirement/design authority, repository context, continuity, test accountability, evidence, or root challenge. `direct` mode is limited to non-mutating micro/spike work; persistent work is at least traced.

New quality-tagged packets bind immutable creation authority, exact requirement and design bytes, event-ordered ambiguity and approval state, engineering-context fingerprints, repository identity/HEAD/worktree evidence, and project-knowledge disposition. Recovery uses semantic checkpoints at lifecycle, slice, handoff, premise, and verification boundaries rather than timers. OPEN slices permit expected edits; SEALED boundaries freeze evidence. Packets are unsigned consistency records, not tamper-proof storage.

Project knowledge has three authority planes:

- tracked current truth under `docs/project/` for what is true now;
- tracked change dossiers under `docs/changes/` for requirement, design, execution, verification, and history;
- ignored `.codex/dev-flow/` state for detailed recovery and raw local evidence.

Only implemented, freshly verified, reusable, and sanitized conclusions are promoted. Governed dossiers bind exact requirement/design bytes and globally unique normative IDs: requirements own AC; design owns SC and VO. New quality packets require that exact authority for material knowledge; standalone legacy dossiers remain readable without retrospective migration.

Engineering context is resolved per affected path, language/framework/version, artifact role, phase, and risk from repository instructions, native controls, profiles, and uniquely admitted specialist Skills. Nontrivial changes separately account black-box behavior and white-box structure, review oracle failure sensitivity, work in coherent slices, and report commit readiness without granting stage/commit/push authority.

The [quality-kernel and knowledge overhaul](../changes/quality-kernel-continuity-knowledge-20260812/manifest.json) is accepted and promoted as the source history for these contracts.

## Limits

This document records stable repository workflow truth. It does not replace language, framework, security, or platform rules discovered for a particular task. Hooks remain defense in depth; lifecycle validation and fresh evidence are the hard gates. Non-Git byte continuity and physical/external environments require task-specific evidence.
