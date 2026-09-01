# Dev Flow project governance

[Knowledge catalog](./catalog.json)

- Knowledge ID: `KT-DEV-FLOW-GOVERNANCE`
- Owner: Dev Flow maintainers.
- Review triggers: a change to routing, continuity, risk overlays, Hooks, knowledge ownership, verification, compatibility, or release policy.
- Source anchors: [product state](../../governance/product-state.json), [plugin manifest](../../.codex-plugin/plugin.json), [main Skill](../../skills/dev-flow/SKILL.md), [public CLI](../../skills/dev-flow/scripts/dev-flow.py), [Hook manifest](../../hooks/hooks.json), [release model](../releasing.md), and [RC.6 workstream](../workstreams/dev-flow-2.0-rc.6/).

## Current truth

Dev Flow 2.0 is a thin repository-first workflow. It optimizes for the requested business outcome while preserving three independent planes:

1. repository business continuity through maintained implementation/progress and conditional requirements/design/decision documents for managed work;
2. native engineering evidence from code, Git, tests, CI, runtime checks, review, and immutable artifacts;
3. minimal safety boundaries for confidential data, broad destruction, irreversible actions, and external delivery.

Task entry has four orthogonal dimensions. The primary intent is research/audit, diagnosis, design, change, review, or delivery. `direct` is the default continuity mode; `managed` is selected only for multi-session, multi-slice, cross-module/repository/team work, material design trade-offs, or an explicit durable plan/handoff need. Security/privacy, migration/data, external-system, release/delivery, irreversible, and UI/product risks are overlays. Durable knowledge is rechecked separately: direct work may update maintained current truth or add one concise repository-native change note without creating Dev Flow state.

Managed knowledge lives in the repository that owns the change, following its convention or `docs/workstreams/<slug>/`. Git supplies chronology and review. Workstream prose records business intent, trade-offs, slices, progress, and durable decisions; it does not duplicate commands, logs, hashes, test output, source schemas, or agent activity.

The main Skill applies a zero-artifact quality calibration and loads only specialists that own a real decision or evidence need. Repository discovery, repository knowledge-system establishment, requirements/design, UX, debugging, architecture, dependencies, verification, review, delivery, data security, profile management, and Dev Flow maintenance remain separate capabilities. Repository knowledge establishment owns human-and-agent navigation, stable indexes, document disposition, and replaceable generated maps; it does not absorb ordinary documentation updates or delivery execution. Bounded assurance methods are actively considered at high-leverage risk/failure signals but never persisted as lifecycle gates.

Single-agent execution is the baseline. Every actual child dispatch uses the deterministic P0-P6 selector for task-relative model/reasoning choice, without storing a receipt. Delegation needs only objective/outcome, relevant context, owned paths or read-only scope, allowed verification/resources, stop conditions, and expected return. The root reconciles actual returned changes against current Git state and reruns affected checks. Profile records, fingerprints, leases, lifecycle states, and generated reports are not required.

Dev Flow 2.0 has no process, lifecycle, command-authorization, packet, agent, or completion Hook. Host permissions, explicit user authority, and task instructions own destructive and external actions. The separate data-security capability protects supported prompt/tool surfaces through a narrow detector/redactor contract; it does not make workflow decisions.

Verification is proportional: focused reproducer or check first, affected module/integration/risk evidence next, broad regression only where the change can affect it, then final diff/scope inspection. Black-box, white-box, property, differential, exploratory, and adversarial views are selected by distinct failure sensitivity rather than mandatory prose accounting.

Release evidence is selected by changed surface: R1 standard, R2 runtime, or R3 artifact/security. The full semantic suite runs once for final candidate bytes; focused compatibility cells cover platform/version-sensitive behavior; release-candidate construction owns archive, SBOM, checksums, provenance, and attestation without replaying semantic CI. Stable publication additionally reviews the cumulative semantic delta, applies the consolidated deeper static review, and exercises bounded real functional journeys. Repeated model studies belong to independent Dev Flow Bench and are not release gates. Publication and installation remain separate authorities.

## Legacy compatibility

Explicit packet, method, knowledge, profile, and evaluation CLI surfaces remain readable and validatable for existing 1.x data. Legacy packet state is inert for 2.0 work and cannot block implementation. Historical dossiers under `docs/changes` retain the rationale and evidence for earlier versions; they are not current workflow instructions.

The following records remain useful source history:

- [quality-kernel and knowledge overhaul](../changes/quality-kernel-continuity-knowledge-20260812/manifest.json);
- [assurance-method reasoning layer](../changes/assurance-method-reasoning-layer/manifest.json);
- [1.1.1 method enforcement](../changes/dev-flow-1-1-1-method-enforcement/manifest.json);
- [1.1.2 agent dispatch](../changes/dev-flow-1-1-2-agent-dispatch/manifest.json).

## Limits

Local evidence does not prove hosted CI, a physical device, signing service, remote tag, marketplace install, external account, deployment, production behavior, or business acceptance. Hooks are defense in depth and cannot infer product semantics or grant authority. The data-security Hook is not endpoint/network DLP and cannot cover unsupported hosted paths.
