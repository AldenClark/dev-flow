# Requirements for quality-kernel-continuity-knowledge-20260812

[Manifest](./manifest.json)

## User and product outcome

Improve the Dev Flow Skill suite so development-process quality is the primary outcome. The process must understand requirements thoroughly, persist the resulting truth, ground design in the repository, resist context-loss drift during implementation, preserve detailed and reusable knowledge, strengthen self-challenge across all phases, use installed technical guidance when applicable, enforce serious testing discipline, support team coordination, and encourage useful explanatory code comments and coherent commit-ready slices.

## Requirement source and understanding revisions

| Revision | User-owned clarification retained by this change |
|---|---|
| R0 | Improve both Skill quality and evaluation, with development-process quality taking priority. |
| R1 | Remove quantitative evaluation as a core objective; elevate documentation and knowledge accumulation to the same priority as traceability and recoverability. |
| R2 | Treat periodic rereading only as a candidate tactic. The actual requirement is recovery from context truncation, compaction, interruption, and premise drift without forgetting intent. |
| R3 | Apply adversarial clarification and self-verification during requirements, design, implementation, verification, and delivery rather than reserving review for final acceptance. |
| R4 | Treat a two-layer document model and the existing twelve-Skill topology as proposals, not mandates; choose the architecture that best serves the outcomes. |
| R5 | Require separate black-box and white-box reasoning for nontrivial behavior, review test oracles, discover applicable repository and installed technical guidance, coordinate multi-agent ownership, and favor useful comments without comment quotas or over-defensive code. |
| R6 | Implement the agreed quality-first architecture completely while preserving appropriate compatibility and delivery authority boundaries. |

## Requirement delta

Compared with the prior conditional-routing workflow, persistent mutation now requires a compact non-optional quality kernel, exact requirement/design authority, semantic recovery, separate test views, engineering-context binding, intentional knowledge disposition, and final evidence challenge. Specialist Skills remain additive and evidence-routed rather than universally loaded.

The current requirement truth is R6 plus all non-superseded constraints above. This tracked document is the authoritative sanitized requirement baseline; the manifest binds its exact bytes and a new quality-tagged lifecycle packet must adopt those same bytes rather than reinterpret or summarize them. The earlier change-set-only packet is retained separately as legacy execution history, not as current approval authority. Later user corrections supersede only the affected clauses and must be recorded here and in the active lifecycle projection before further affected mutation.

## Ambiguity ledger

| Item | Competing interpretations | Resolution | Affected criteria |
|---|---|---|---|
| AMB-1 | Make scoring central, or keep measurement subordinate to process quality. | Scoring is not a core objective. Retain thin deterministic validation and evidence reporting without a heavy weighted score layer. | AC-12 |
| AMB-2 | Require two document directories, or model knowledge by semantic authority. | Use three semantic planes: tracked current truth, tracked change dossiers, and ignored runtime recovery evidence. Existing repository conventions may override the default tracked paths. | AC-4, AC-5 |
| AMB-3 | Preserve exactly twelve Skills, or preserve capabilities and compatibility. | Keep the current topology where useful, but derive inventory from the capability registry and allow later evidence-backed merge or split decisions. | AC-6, AC-7, AC-12 |
| AMB-4 | Reread documents on a timer, or recover when meaning can become stale. | Use lifecycle and semantic triggers bound to requirement, design, engineering-context, scope, evidence, and drift state. | AC-3 |
| AMB-5 | Load quality controls only when routing predicts risk, or retain a universal minimum. | Make the small quality kernel unconditional for every persistent mutation; conditional routing adds specialists but cannot subtract the kernel. | AC-6 |

No material product-semantic ambiguity remains open for implementation. Acceptance, promotion, commit, push, release, and deployment remain separate decisions gated by their own evidence and authority.

## Acceptance criteria

- **AC-1:** Before consequential implementation, every persistent mutation records a user-correctable requirement source chain: sanitized original intent, successive AI understanding and user corrections, repository facts, observable acceptance, protected behavior, exclusions, bounded assumptions, and every remaining ambiguity. Codex investigates repository-owned facts itself and asks decision-changing user questions until no open material or high-risk ambiguity remains.
- **AC-2:** Every persistent mutation records a repository-grounded design and dependency-aware task plan before implementation. Material alternatives, current-state evidence, tradeoffs, failure behavior, compatibility, rollback, operations, documentation, black-box obligations, white-box invariants, and verification methods are visible; new governed approval binds exact requirement and design bytes.
- **AC-3:** Start or resume, context compaction, user steering, approval, coherent slice boundaries, delegation and reconciliation, premise-changing failure or repair, phase transition, pre-verification, and final claim trigger semantic rehydration from the authoritative requirement, design, and short continuity checkpoint. The checkpoint records active objective and IDs, last evidence, drift ruling, next action, stop condition, and effective engineering-context fingerprint; wall-clock timers and per-tool diaries are not the contract.
- **AC-4:** Project knowledge has three distinct authorities: Git-tracked current truth under the repository's established knowledge location or `docs/project/`; Git-tracked per-change history under `docs/changes/`; and ignored `.codex/dev-flow/` recovery state and raw evidence. Small changes may use one compact change document; larger changes split by semantic concern without creating a parallel workflow.
- **AC-5:** Before acceptance, every change records knowledge impact and disposes reusable conclusions as promoted current truth, history-only, or not applicable with reason. Only implemented, verified, reusable conclusions may be promoted; current truth is updated in place with Git history, accepted ADRs are superseded rather than rewritten, accepted change history is stable, and raw logs, secrets, personal data, speculative plans, and one-run pass claims never become current truth.
- **AC-6:** Every persistent mutation receives an always-on compact Dev Flow quality kernel, repository context, fresh verification, final-diff inspection, and root-level constructive/adversarial challenge. The kernel always reassesses requirement, architecture, dependency, UI, security/privacy, data/schema, compatibility, testing, documentation, collaboration, and delivery applicability. A full owner or specialist runs when the trigger is present or materially unknown; direct mode is limited to non-mutating exploration or an explicit compatible exception.
- **AC-7:** At requirements, design, implementation, verification, and review boundaries, Codex resolves effective `AGENTS.md` instructions, repository conventions, profiles, native controls, and host-provided specialist Skills by affected artifact language, framework/version, role, boundary, phase, and risk. It derives a neutral capability outcome first, activates the smallest applicable set, reports collisions and limits, rebinds on material change, and never turns a personal Skill into silent team policy.
- **AC-8:** Implementation proceeds in bounded coherent slices that keep behavior, tests, necessary documentation, and appropriate comments together. Each slice freezes intent, runs the cheapest narrow checks early, adds smoke/module evidence at integration points, inspects diff/scope/secrets/dependency/generated changes, and ends in an honest commit-ready or blocked state. Commit-ready prompts for separate authority; it never authorizes stage, commit, push, or PR.
- **AC-9:** Every non-trivial behavior change separately accounts for specification-derived black-box tests and structure/risk-derived white-box tests. Applicable obligations must be designed, implemented, and run; `N/A` requires a concrete reason. Test code and oracle strength are reviewed, experience-based/red/exploratory checks supplement rather than replace the two views, and no universal coverage or test-count target is introduced.
- **AC-10:** Code comments are intentionally adequate rather than count-driven: they explain why, invariants, safety/privacy/compatibility/protocol constraints, concurrency/lifecycle/resource ownership, non-obvious tradeoffs, workarounds/removal conditions, and public API limits or errors. They do not narrate obvious code, preserve commented-out code, add unsupported defensive complexity, mask unclear design, or leave ownerless triggerless TODOs; behavioral claims in comments are test-protected and stale nearby comments are updated.
- **AC-11:** Delegated and team work binds repository/worktree/base, requirement and design revisions/digests, effective instruction/profile/capability fingerprint, AC/SC/VO slice, exclusive paths, shared-resource lease, allowed and forbidden actions, black-box and white-box obligations, and stop conditions. Drift stops the child for resynchronization; root integration re-reads the final diff and evidence, and a child terminal status is never completion by itself.
- **AC-12:** The solution adds no composite quality score, external dependency, automatic semantic documentation generator, vector/graph system, or automatic archive migration. It does not treat the current count of Skills as an architectural target, preserves legacy packets and accepted history, keeps user-owned dirty work and privacy boundaries intact, and separates local implementation, verification, acceptance, commit, push, release, installation, and external actions.

## Non-functional requirements

- Quality gates fail closed for a stale or missing strict-packet authority, baseline, context projection, continuity boundary, test disposition, review result, or knowledge disposition.
- The mandatory kernel stays concise; full specialist bodies load only for present or materially unknown applicability.
- New tagged semantics do not retroactively tighten legacy packets, and all local packet state remains consistency evidence rather than a signed tamper-proof record.
- The implementation uses repository-native Python, Markdown, and JSON with no new external dependency or automatic semantic publication.

## Compatibility and exclusions

- Preserve legacy packet handling unless it falsely claims the new quality-kernel guarantees.
- Do not require every task to load every specialist Skill; discover and admit the minimum applicable set while recording unresolved coverage gaps.
- Do not turn runtime logs, private data, credentials, or machine-local paths into tracked knowledge.
- Do not make a fixed cadence, document count, Skill count, comment density, test count, or numerical score the goal.
- Do not perform commit, push, pull-request, release, migration, deployment, destructive rollback, or external communication without explicit authority.

## Requirement Ready gate

Status: ready. The user authorized the integrated local implementation with `我同意，请实施到位`; AMB-1 through AMB-5 are disposed by the recorded conversation, and no open material or high-risk ambiguity remains. Delivery actions are outside this approval.

## Requirement baseline

Revision 1 uses this complete file as the exact requirement content. The external change manifest records its SHA-256, and the active quality-tagged packet must bind the same bytes before design approval or implementation.

## Confirmation record

The retained user corrections make process quality primary, remove quantitative evaluation as a core objective, elevate documentation/knowledge, target context-loss recovery rather than periodic ritual, require cross-phase self-challenge, treat two-layer docs and twelve Skills as proposals, require applicable technical guidance and complementary tests, and request adequate explanatory comments plus team-safe coherent slices.

[Current Dev Flow governance](../../project/dev-flow-governance.md)
