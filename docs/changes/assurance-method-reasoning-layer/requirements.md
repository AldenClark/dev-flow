# Change requirements: assurance-method-reasoning-layer

[Tracked change manifest](../../../docs/changes/assurance-method-reasoning-layer/manifest.json)

## Requirement source and understanding revisions

- Original input: The user asked for a broad and deeply implemented full-lifecycle method guidance layer, beginning at requirement clarification and ending at testing/acceptance, grounded in web research and designed to help AI deliver quality even when the human user has little methodology knowledge.
- AI understanding revision 1: Build a research-grounded, extensible method pool; model risk-to-failure-to-method reasoning; deterministically select bounded, progressive method stacks from lifecycle/risk/signals; provide novice-readable guidance, artifacts, templates, fallbacks, and evidence duties; integrate without displacing existing owners or weakening authority/evidence gates.
- AI understanding revision 2: No product or implementation semantic changed; add the shared tracked-manifest backlink required for exact governed knowledge binding.
- Corrections and decisions: The user clarified that named methods were examples, not a closed list, and explicitly requested research, design, filtering, integration, and a large step in implementation depth.
- Current requirement truth: Revision 2 above; it preserves revision 1 semantics and adds only the governed knowledge backlink.

## User and product outcome

Primary actors are less-experienced developers using Dev Flow and the AI executing their work. Today the user must know which specialist reasoning method to ask for, while the AI has no canonical mechanism for choosing between lightweight clarification, relational/formal modeling, adversarial analysis, specialized testing, or operational assurance. Success means the AI can identify the likely failure mechanism from explicit facts, select a proportionate stack, explain it in plain language, produce bounded artifacts, and expose remaining evidence gaps without the user naming a methodology.

## Requirement delta

Add an assurance-method system above the existing owner Skills: a source-grounded method pool, risk models, a deterministic `select-methods` CLI, progressive method-card guidance, reusable templates, lifecycle integration, tracked current truth, and regression contracts. Existing routing still chooses owners; the new layer chooses how those owners should reason and what evidence/artifacts they should produce.

## Acceptance criteria

- AC-1: Given a supported lifecycle phase plus explicit task/risk/signal facts, `select-methods` returns deterministic `method.selection.v1` JSON that traces each selected stack from observation to failure hypothesis, method, owner, output, and evidence obligation.
- AC-2: The pool spans discovery, requirements/semantics, scope/interaction, architecture, formal reasoning, security/privacy/safety, implementation, debugging, verification, review/assurance, delivery/operations, UX/accessibility, and AI-agent engineering with primary or authoritative source bindings.
- AC-3: Every selectable method declares positive and negative triggers, prerequisites, bounded steps/outputs, limitations, effort/depth, owner, sources, and fallback behavior; missing prerequisites never become a silent pass.
- AC-4: A novice can omit method names: foundation methods are always selected for persistent work, explicit risks/signals activate proportionate starter/deep/formal stacks, and the output explains why, how, and when to stop/escalate in plain language.
- AC-5: Low-risk routine input stays bounded and excludes heavyweight formal, safety, and adversarial methods with reasons; no request loads the whole pool into working context.
- AC-6: Representative identity/migration, feature-interaction, concurrency/liveness, public-contract/refinement, oracle-gap, security/privacy, safety, performance/resources, UX/accessibility, data migration, and AI-evaluation cases select the expected owners and methods.
- AC-7: Dev Flow lifecycle guidance requires method re-selection after repository context and on phase/risk/premise drift while preserving requirements, architecture, verification, review, dependency, and delivery ownership.
- AC-8: The implementation is covered by deterministic schema, coverage, selection, negative-control, compatibility, documentation, and full-suite checks; optional model evaluation remains subordinate and is not required for normal validation.

## Non-functional requirements

- Selection is deterministic, standard-library-only, offline after installation, and emits stable sorted output.
- Progressive disclosure limits selected methods by depth and makes detailed cards opt-in by reference rather than loading the complete catalog.
- Registry validation fails closed on unknown IDs, dangling sources/references, invalid owners/phases/depths, missing triggers/limitations/artifacts, duplicate IDs, uncovered lifecycle phases, or risk models with no method.
- Sources and adaptations are reviewable and dated; research provenance is separate from claims of executed verification.
- Output is usable by a novice but retains precise method names and limitations for expert inspection.

## Compatibility and exclusions

- Compatibility: additive CLI and references; current `route-task`, packet schema, owner Skills, hook behavior, manifests, and Python/platform support remain unchanged. Registry extension must be backward-compatible within schema 1.0.
- Excluded behavior: claiming exhaustive coverage of all human/project-management methods; automatically installing/invoking external tools; replacing professional certification or regulated approval; inferring unobserved facts from prose; adding a top-level owner Skill; dependency, commit, push, release, install, deployment, or external publication.

## Requirement Ready gate

- Status: ready.
- Evidence: explicit user direction; clean repository discovery; T3 ECR ready; existing owner topology, quality kernel, CLI, test, and knowledge contracts inspected; primary-source research completed across all target families.
- Remaining decisions: none. A new dependency, owner, mandatory packet schema, incompatible CLI behavior, or external action would require reopening.

## Requirement baseline

- Revision: 2; product semantics are unchanged from revision 1.
- Digest: content-bound by the revision-2 `REQ-READY` record after these exact bytes are complete.
- Baseline content: this complete `requirements.md`.
- Reopen conditions: user correction, new public incompatibility, owner-boundary change, dependency requirement, or verified finding that changes AC/SC/VO semantics.

## Ambiguity ledger

| ID | Source and interpretations | Evidence | Materiality and owner | Affected IDs | Recommendation | Status and resolution |
|---|---|---|---|---|---|---|
| AMB-1 | Exact approved bytes could omit the dossier backlink or be reopened for an administrative-only revision. | The knowledge contract requires both exact authority hashes and a manifest backlink; avoiding the binding would misstate current-truth promotion. | Material; Codex | AC-8, SC-I1, VO-6 | Add the same repository-relative backlink to packet and dossier copies, preserving all product semantics. | Resolved by repository contract evidence; revision 2 records the administrative link. |

## Confirmation record

- 2026-08-14: The user confirmed the named theories were examples and requested broad research, a foundational pool, a risk-to-method layer, filtered integration, and deep implementation for novice users.
