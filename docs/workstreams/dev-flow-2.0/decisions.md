# Dev Flow 2.0 decisions

## D1: Repository knowledge replaces packet continuity

- Status: accepted
- Context: packet checkpoints and digests repeatedly displaced implementation and were ignored by Git, while repository business documents retained long-term GLM value.
- Decision: managed work stores implementation and progress in the affected repository; it adds design and decision records only when real trade-offs or durable decisions justify them.
- Alternatives: simplify packets; generate packets from docs; keep both authoritative.
- Consequences: continuity becomes human-readable and reviewable with code; documents require normal maintenance judgment; Git supplies history instead of an event ledger.

## D2: Direct is the default for persistent work

- Status: accepted
- Context: 1.x classified every persistent mutation as traced or governed, making small batches pay fixed setup and closure cost.
- Decision: ordinary persistent work is direct and creates no Dev Flow artifact.
- Alternatives: retain a micro trace; auto-create a single trace file.
- Consequences: lower startup and closure cost; correctness depends on native engineering practices and the final diff rather than packet completeness.

## D3: Continuity mode and risk controls are orthogonal

- Status: accepted
- Context: high-risk work may be bounded, while low-risk product rewrites may span months. A single ordered mode mixed two different concerns.
- Decision: choose direct/managed from continuity needs and add security, migration, external-system, release, irreversible, and UI overlays independently.
- Alternatives: numeric risk tiers; direct/traced/governed ranking.
- Consequences: risk controls become more precise; routing tests must cover composition rather than a single escalation ladder.

## D4: Hooks enforce only deterministic safety boundaries

- Status: superseded by D11 after Beta.1 review
- Context: Hooks cannot reliably infer business semantics, dependency approval, lifecycle state, or nested-repository ownership from command strings and local packet pointers.
- Decision: remove packet workflow enforcement. Keep secret protection, broad-destruction blocking, and external-delivery confirmation.
- Alternatives: keep patching the packet parser; expand the approval ledger.
- Consequences: this was a useful alpha simplification, but even the reduced process Hook duplicated host authority, covered only some tools, and retained command-parsing cost and a misleading partial safety boundary.

## D5: Legacy packets remain readable but inert

- Status: superseded by D20 before RC.1
- Context: existing repositories contain valuable packet history and may need archive/validation, but compatibility must not force continued use.
- Decision: retain explicit legacy packet CLI and validators for the first 2.0 release; new routing, Skills, and Hooks never activate them.
- Alternatives: delete packet code now; migrate every packet automatically.
- Consequences: lower migration risk and larger temporary code surface; later removal needs usage evidence and a separate decision.

## D6: Release evidence is selected by changed surface

- Status: superseded on 2026-09-01 by `../dev-flow-2.0-benchmark-separation/decisions.md` D1-D3
- Context: six identical full CI suites, repeated RC suites, model evaluation, artifact evidence, and install rollback make every release pay the maximum cost.
- Decision: the original 2.0 design used R1-R4 release tiers, one semantic lane, a focused compatibility lane, and a release-only artifact lane. Current policy retains R1-R3 and moves repeated model research to independent Dev Flow Bench.
- Alternatives: retain maximum gates; reduce every release to one CI job.
- Consequences: materially lower routine release cost while retaining platform, runtime, security, and provenance evidence where each can change the outcome; stable functional validation is stronger without a repeated-model release tier.

## D7: Source version becomes a prerelease, publication remains separate

- Status: superseded by D10 after the local alpha convergence
- Context: 2.0 changes default modes and Hook behavior and are semantically breaking even though packet readers remain.
- Decision: after integrated verification, update source manifests and examples to `2.0.0-alpha.1`; do not create or publish a tag/release/install in this task.
- Alternatives: call the change 1.2; publish 2.0.0 immediately.
- Consequences: communicates migration status honestly and leaves room for real-project validation before stable 2.0.

## D8: Quality calibration and advanced capabilities stay visible but non-persisted

- Status: accepted
- Context: the first 2.0 alpha removed packet ceremony but made hidden-risk discovery, P0-P6 routing, and method selection too easy to skip.
- Decision: keep a zero-artifact quality calibration on every task; require task-relative routing for actual child dispatch; actively consider bounded methods at high-leverage risk/failure signals; recheck risks at boundary and failure changes.
- Alternatives: restore governed packets; leave all advanced capabilities optional and implicit.
- Consequences: engineering quality intervenes at decision points without creating receipts, hashes, checkpoints, or a second workflow state.

## D9: Managed duration does not automatically require a design document

- Status: accepted
- Context: implementation/progress state is valuable for every long task, while design docs are overhead when the solution has no meaningful alternatives or trade-offs.
- Decision: the managed initializer creates `implementation.md` and `progress.md` by default; `--with-requirements`, `--with-design`, and `--with-decisions` are explicit conditional additions.
- Alternatives: always create three files; put all content in one large workstream file.
- Consequences: users retain a simple shared progress surface and avoid empty or implementation-manual design documents.

## D10: Promote the locally converged design to beta source

- Status: accepted
- Context: the alpha removed packet-first governance, and the subsequent quality rebalance restored proactive risk calibration, P0-P6 routing, bounded methods, independent review triggers, and a complete 2+N business-document model without restoring receipts or lifecycle gates.
- Decision: identify the locally verified source as `2.0.0-beta.1`. Keep commit, tag, push, hosted CI, Marketplace publication, installation, and deployment as separately authorized and separately evidenced actions.
- Alternatives: retain the alpha label; publish stable 2.0 immediately; restore part of the 1.x governance machinery.
- Consequences: beta communicates a complete intended operating model ready for real-project and hosted validation while preserving room for compatibility and usability corrections before stable 2.0.

## D11: Remove the Dev Flow process Hook

- Status: accepted
- Context: the reduced Beta.1 Hook still parsed every Bash command, rediscovered roots, duplicated host confirmation/authority behavior, did not cover equivalent non-Bash tools, and could not reliably infer destructive intent from syntax. The same mechanism had already produced repeated false blocks and self-maintenance work in the referenced GLM tasks.
- Decision: ship no Dev Flow process, lifecycle, command-authorization, packet, agent, or completion Hook. Keep the independent data-security Hook because it owns a narrow confidentiality boundary with deterministic detectors, negative cases, and a dedicated doctor.
- Alternatives: expand the reduced Hook to more tools; keep only broad-destruction parsing; move all process checks into the data-security Hook.
- Consequences: default command overhead and partial-enforcement ambiguity disappear. Destructive and external actions remain governed by host permissions, user authority, task instructions, and delivery guidance rather than plugin command parsing.

## D12: Task entry and durable knowledge are orthogonal

- Status: accepted
- Context: `developer`/`manager` or the 1.x task taxonomy mixed the requested business action, continuity needs, risk, and documentation. Direct work then risked being interpreted as knowledge-free even when a small change altered durable product behavior.
- Decision: use six primary intents (`research`, `diagnose`, `design`, `change`, `review`, `delivery`), choose `direct`/`managed` only from continuity needs, compose independent risk overlays, and recheck a separate knowledge disposition (`none`, maintained current truth, or one concise change note). Research is non-judgmental fact finding; audits map to read-only review; review-and-fix is change plus a review need. Managed workstream documents supersede a separate change note.
- Alternatives: add more ordered task tiers; make every change managed; require a final implementation record for all direct mutations.
- Consequences: entry classification is precise without proliferating workflows. Small consequential changes can remain direct and still preserve durable knowledge, while routine self-evident edits create no document.

## D13: Advance the corrected source to Beta.2

- Status: accepted
- Context: Beta.1 established the intended quality architecture, while task-entry ambiguity, direct-work knowledge loss, and the remaining process Hook still carried avoidable cost.
- Decision: identify the corrected local source as `2.0.0-beta.2`. Preserve Beta.1 as history and keep commit, push, hosted CI, tag, release, publication, installation, and deployment as separate authorities and evidence states.
- Alternatives: amend Beta.1 in place; wait for stable 2.0; remove all 1.x compatibility code during the same correction.
- Consequences: Beta.2 is a coherent pilot candidate without combining the low-risk workflow correction with a high-risk legacy-runtime deletion.

## D14: Measure only the actual default context path

- Status: accepted
- Context: the ordinary static-context budget still counted the full legacy packet schema reference even though 2.0 does not load or route that reference for ordinary work. This made compatibility documentation consume the default-path budget and caused unrelated changes to fail a hard gate.
- Decision: keep the byte budget, but calculate it from the Skill entrypoints actually loaded on the ordinary mutation path: Dev Flow, repository context, and verification. Validate legacy packet documentation separately as a compatibility surface.
- Alternatives: raise the 18,000-byte threshold; delete compatibility documentation; keep shrinking active guidance to subsidize an unloaded legacy reference.
- Consequences: the budget once again measures real default context cost instead of total retained compatibility bytes, without weakening packet validation or documentation integrity.

## D15: Confirm material requirement understanding before design

- Status: accepted
- Context: repository investigation and ambiguity questions can still leave Codex with a complete but incorrect interpretation. New or materially changed behavior has a higher semantic error cost than an established bug or mechanical edit.
- Decision: classify requirement-understanding depth by task semantics. For material new or changed product behavior, publish a detailed technology-neutral understanding result in Default mode and stop for explicit user confirmation before technical design. Established bugs, internal behavior-preserving changes, and mechanical edits skip the stop unless evidence leaves material expected behavior unresolved.
- Alternatives: proceed whenever no ambiguity is detected; require confirmation for every mutation; require a persisted approval record.
- Consequences: one deliberate user checkpoint protects product meaning without adding a universal questionnaire, Plan mode, digest, receipt, or repeated design approval.

## D16: Restore advanced-capability initiative without restoring process enforcement

- Status: accepted
- Context: Beta.2 retained specialist Skills, P0-P6 dispatch, 117 methods, review lenses, and risk-based verification, but several active routes depended on explicit flags or optional references. Capability inventory and selector correctness did not prove that natural requests and repository evidence would activate them.
- Decision: add an ephemeral capability-activation spine after repository discovery and after requirement confirmation, with event-driven rechecks on boundary, failure, and final-diff changes. It considers specialist Skills, bounded methods, independent review, and child model/effort from current evidence and the effective Codex surface. Nothing is persisted solely to prove activation.
- Alternatives: restore mandatory 1.x gates and records; leave advanced activation entirely implicit; load all specialists on every task.
- Consequences: advanced engineering quality becomes proactive and testable while simple tasks retain negative triggers and zero process artifacts.

## D17: Route closed child execution toward Luna

- Status: accepted
- Context: the current P0-P1 profiles use Luna while ordinary bounded implementation starts at Terra. Current GPT-5.6 capabilities allow Luna to perform tool-using, high-volume directed work, but requirements, architecture, open diagnosis, high-risk review, authority, and final claims still need stronger judgment.
- Decision: use Luna for P0 low, P1 medium, and P2 high when the child task has confirmed semantics, bounded ownership, and a deterministic oracle; use Terra for ordinary exploratory and causal work, and Sol for broad ambiguity, consequential contracts, high-risk review, and critical acceptance. Never delegate solely to obtain a cheaper model.
- Alternatives: retain Luna only for lookup; route routine work to Luna regardless of closedness; select a model from task size alone.
- Consequences: directed work can use the low-cost model without making cheapness a substitute for capability or creating coordination overhead.

## D18: Define flow metrics as activation coverage only

- Status: accepted
- Context: effect, productivity, latency, defect, and composite-quality metrics can turn Dev Flow into a surveillance or optimization system and do not prove routing correctness. The release need is to know whether realistic tasks reach the intended branches and avoid unintended ones.
- Decision: retain `flow-metrics` only as a compatibility name for Flow Activation Coverage. Test deterministic routing, natural-language/repository semantic activation, and negative cost boundaries; report expected versus observed activation and unmet prerequisites without an aggregate score.
- Alternatives: keep outcome/friction KPIs; remove all model-semantic testing; optimize for Skill or method call counts.
- Consequences: releases can detect missing or excessive activation without measuring people or encouraging gratuitous process.

## D19: Converge the accepted S12-S20 baseline as Beta.3 source

- Context: the user approved implementing the previously proposed RC/2.1 capabilities in the current 2.0 baseline, including stronger requirement confirmation, advanced activation, Luna routing, native Codex adapters, and activation-only flow metrics.
- Decision: identify the completed local source as `2.0.0-beta.3`, correct the published baseline to the remotely verifiable `v1.1.2`, and keep 1.1.3 as untagged source history. Commit, push, hosted CI, tag, release, publication, active installation, and deployment remain separate authority boundaries.
- Alternatives: keep the expanded source under Beta.2; claim untagged 1.1.3 as published; defer approved capabilities to RC or 2.1.
- Consequences: source identity matches the material model-facing change while published and local states remain exact.

## D20: Freeze scope and publish RC.1 as a hard 1.x cut

- Status: accepted; supersedes D5's compatibility promise and D19's Beta.3 source state
- Context: the 2.0 outcome is complete, further feature work is frozen, and preserving 1.x upgrade/state compatibility would reintroduce the release and validation burden that 2.0 removes.
- Decision: identify the next source as `2.0.0-rc.1`; provide no public 1.x packet, command, state, upgrade, migration, or rollback compatibility contract. Run one bounded semantic activation pass, then create an annotated RC tag and push `main` plus the tag. Hosted CI is asynchronous feedback, while artifact construction, upgrade/rollback matrices, active-profile installation, and real-task soak are not RC.1 gates.
- Alternatives: preserve read compatibility through 2.x; remove every legacy implementation byte before RC; require hosted CI and attested artifacts before a tag.
- Consequences: RC.1 stays small and matches the intentional breaking cut. Residual legacy code is unsupported internal debt, not a compatibility promise, and can be removed separately without blocking this release.

## D21: Harden activation through additive task-facing contracts

- Status: accepted for RC.2 implementation
- Context: real RC.1 tasks showed that specialist Skills often activated while the main kernel did not, explicit Dev Flow use did not reliably invoke the deterministic route, guessed risk labels were rejected as method signals, blocked broad-domain methods displaced actionable guidance, same-context red/blue work was described too strongly, and managed work did not reliably survive interruptions.
- Decision: improve the main description and implicit policy, add bounded specialist-to-kernel reconnects, require one compact route only for explicit/material cases, normalize aliases and derive foundational signals at the task-facing route, project ready and blocked methods through separate caps and domain gates, expose an executable independent-review-or-downgrade contract, and make managed resume/handoff invariants explicit. Preserve canonical signals, method IDs, existing output fields, and `method.selection.v1`.
- Alternatives: add a new orchestration Skill; expand the methodology pool; require routing for every task; change the lower-level selection schema; restore packet/checkpoint state.
- Consequences: natural engineering work has a stronger path into the quality kernel and advanced methods without imposing ceremony on negative controls. The change is model-semantic and therefore cannot support an RC.2 release claim until separately budgeted first-attempt trials run after deterministic gates.
