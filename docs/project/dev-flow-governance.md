# Dev Flow project governance

[Knowledge catalog](./catalog.json)

- Knowledge ID: `KT-DEV-FLOW-GOVERNANCE`
- Owner: Dev Flow maintainers.
- Review triggers: a lifecycle, capability-owner, packet schema, hook, knowledge-root, or acceptance-policy change.
- Source anchors: the [plugin manifest](../../.codex-plugin/plugin.json), [capability registry](../../governance/capability-contracts.json), [orchestrator Skill](../../skills/dev-flow/SKILL.md), [packet implementation](../../skills/dev-flow/scripts/dev_flow.py), [methodology registry](../../governance/methodology-pool.json), [method selector](../../skills/dev-flow/scripts/methodology_system.py), [knowledge contract](../../skills/dev-flow/references/knowledge-system.md), and [contract-check entry point](../../evals/run_contract_checks.py).

## Current truth

Dev Flow is packaged as a Codex plugin by `.codex-plugin/plugin.json`. Its registered capability owners and their inputs, outputs, stops, handoffs, and orchestration conditions are declared in `governance/capability-contracts.json`; repository checks derive the registered inventory from that contract rather than treating a fixed count as the design goal.

The plugin also packages a first-class `company-data-security` capability. It supplies shared C0-C4 handling and differentiated Codex, ChatGPT Work, and ordinary Chat playbooks. Supported Codex prompt and local-tool paths receive a separate bounded Hook adapter; Work and ordinary Chat receive guidance/templates without an invented pre-send enforcement claim. `skills/company-data-security/scripts/doctor.py` checks packaged bytes and semantic registration while leaving live Hook trust and account alignment as explicit manual gates.

The repository's lifecycle CLI is implemented in `skills/dev-flow/scripts/dev_flow.py`, its repository hook entry point is `hooks/dev_flow_hook.py`, and deterministic contract checks enter through `evals/run_contract_checks.py`. Behavioral claims about those surfaces require fresh evidence against the claimed bytes.

Persistent mutation now carries an always-on compact quality kernel. Specialist Skills add depth but cannot remove requirement/design authority, repository context, continuity, test accountability, evidence, or root challenge. `direct` mode is limited to non-mutating micro/spike work; persistent work is at least traced.

New quality-tagged packets bind immutable creation authority, exact requirement and design bytes, event-ordered ambiguity and approval state, engineering-context fingerprints, repository identity/HEAD/worktree evidence, and project-knowledge disposition. Recovery uses semantic checkpoints at lifecycle, slice, handoff, premise, and verification boundaries rather than timers. OPEN slices permit expected edits; SEALED boundaries freeze evidence. Packets are unsigned consistency records, not tamper-proof storage.

Project knowledge has three authority planes:

- tracked current truth under `docs/project/` for what is true now;
- tracked change dossiers under `docs/changes/` for requirement, design, execution, verification, and history;
- ignored `.codex/dev-flow/` state for detailed recovery and raw local evidence.

Only implemented, freshly verified, reusable, and sanitized conclusions are promoted. Governed dossiers bind exact requirement/design bytes and globally unique normative IDs: requirements own AC; design owns SC and VO. New quality packets require that exact authority for material knowledge; standalone legacy dossiers remain readable without retrospective migration.

Engineering context is resolved per affected path, language/framework/version, artifact role, phase, and risk from repository instructions, native controls, profiles, and uniquely admitted specialist Skills. Nontrivial changes separately account black-box behavior and white-box structure, review oracle failure sensitivity, work in coherent slices, and report commit readiness without granting stage/commit/push authority.

After repository context, the Assurance Method System maps explicit lifecycle phase, task type, risks, observed failure signals, and evidenced prerequisites through 32 deterministic risk models. Its canonical pool contains 111 source-bound methods across 10 phases and 16 families, with one lightweight foundation per phase plus risk-triggered `starter`, `deep`, or `formal` methods. AI coding and general-agent coverage includes autonomy selection, partial observability, receding-horizon/reactive/hierarchical planning, counterexample-guided repair, runtime shields and temporal monitors, compensation, provenance/memory governance, human function allocation, multi-agent topology/dynamic allocation, trajectory intervention evaluation, calibrated selective action, and simulation. Specialist failure models are split from broad Agent stacks so `formal` depth alone cannot activate HTN, contract-net, conformal, or digital-twin methods without their specific signals. Selection is capped, stable, and progressive; negative triggers prevent cargo-cult escalation, missing prerequisites remain unresolved with fallbacks, and every result preserves the existing owner Skill and authority boundary. The selected method is guidance for producing an artifact and failure-sensitive evidence, never proof that the method or an external tool was executed.

The registry validator, public `validate-methods`/`select-methods` CLI, progressive playbooks, and scenario contracts are part of the normal plugin and contract-check surfaces. Research provenance and adaptation limits are recorded in [the methodology pool guide](../methodology-pool.md); additions must bind a concrete failure class, positive and negative triggers, prerequisites, bounded steps and outputs, limits, fallback, owner, evidence obligation, sources, and a risk model rather than increasing a method count for its own sake.

The [quality-kernel and knowledge overhaul](../changes/quality-kernel-continuity-knowledge-20260812/manifest.json) is accepted and promoted as the source history for these contracts.

The [assurance-method reasoning layer](../changes/assurance-method-reasoning-layer/manifest.json) is the source history for the methodology registry, selection contract, progressive guidance, and its integration constraints. The [1.1 Agent-assurance expansion](../changes/agent-assurance-expansion-v1-1/manifest.json) records the additive AI coding/general-agent failure models, methods, compatibility obligations, and release boundary.

## Limits

This document records stable repository workflow truth. It does not replace language, framework, security, company data-classification, or platform rules discovered for a particular task. Hooks remain defense in depth; lifecycle validation and fresh evidence are the hard gates. The confidentiality Hook is not endpoint/network DLP, has no control over unsupported hosted/specialized paths, and cannot prove Work/ordinary Chat pre-send enforcement. Non-Git byte continuity, Hook trust, account settings, and other physical/external environments require task-specific evidence.
