# Dev Flow 2.0 implementation

## Delivery slices

| Slice | Outcome | Main areas | Completion evidence | Status |
|---|---|---|---|---|
| S1 Research and design | Repository-tracked 2.0 rationale, design, decisions, migration, and progress exist | `docs/workstreams/dev-flow-2.0` | source links, repository baseline, design review | complete |
| S2 Routing and workstreams | New work defaults to direct/managed; managed docs initialize in the repository; risk overlays are orthogonal | `dev_flow.py`, templates, routing tests | direct/managed scenarios and packet-free assertions | complete |
| S3 Thin Skills | Main and specialist instructions no longer mandate packet/ID/fingerprint/method records | Skill entrypoints and 2.0 references | suite validation, routing/contracts, static inspection | complete |
| S4 No process Hook | Legacy packet state and command parsing cannot gate work; confidentiality remains an independent capability | `hooks.json`, deletion of `dev_flow_hook.py`, data-security tests | default manifest, data-security negative/positive cases, doctor | complete |
| S5 Knowledge migration | New docs-as-code model is documented; historical validator residue does not govern 2.0 | knowledge references, README | no mandatory catalog/manifest for new work | complete |
| S6 Verification and release tiers | Full semantic suite runs once; focused compatibility and artifact lanes remain | CI, RC workflow, release docs/tests | workflow contracts and release-artifact tests | complete |
| S7 Integrated verification | Focused then full deterministic validation and final diff audit | repository-wide | tests, contracts, plugin/suite/data-security checks, compile, diff | complete |
| S8 Quality rebalance | Restore zero-artifact calibration, P0-P6 dispatch, bounded methods, hidden-risk rechecks, and conditional design docs without packet ceremony | main Skill, quality reference, router, templates, docs, tests | routing/workstream/Skill contracts plus integrated verification | complete |
| S9 Beta convergence | Freeze the agreed design constitution, complete 2+N requirements support, remove active alpha/version drift, and verify the final beta source | workstream docs, CLI/templates, Skills, version/release surfaces, tests | beta contract tests, residual-ceremony audit, integrated validation | complete |
| S10 Beta.2 correction | Separate task intent, continuity, risk, and knowledge; preserve light direct knowledge; remove the remaining process Hook and dead tests | router, method selector, knowledge template/docs, Hooks, CI, release surfaces | focused intent/knowledge/default-Hook tests plus integrated validation | complete |
| S11 Beta.2 boundary hardening | Separate research from review, make security architecture-explicit, replace packet-era active capability semantics, scope compatibility CI, and run eight isolated task pilots | router, capability contract, CI scope tool, main Skill, tests, workstream progress | deterministic regressions, full suite, eight first attempts, one focused repair rerun | complete |
| S12 Requirement understanding and confirmation | Classify semantic work, publish detailed understanding, and stop in Default mode before design when product meaning is created or changed | requirements Skill/references, main lifecycle, workstream requirements template, contracts/evals | new/change, ambiguous bug, established bug, mechanical, correction, waiver, and no-Plan cases | complete |
| S13 Advanced capability activation spine | Restore proactive specialist, method, review, and child-route activation from request/repository/diff/failure evidence without records | main Skill, quality calibration, repo context, capability contracts, routing output | positive and negative activation contracts plus event-driven rechecks | complete |
| S14 Dynamic technical capability routing | Connect effective host Skills and repository technology/risk signals with bounded fallbacks | repo context, capability registry/adapter, specialist descriptions, tests | Rust/async/FFI/Swift/React/data/security/UI fixtures and missing-capability fallback | complete |
| S15 Methods and engineering guidance | Actively match bounded methods at high-leverage failure mechanisms and consume existing repository/profile guidance without snapshots | methodology references/selector, engineering context, main Skill, tests | requirements/architecture/debug/verification/review method activation and skip cases | complete |
| S16 Codex runtime adaptation | Detect Default-mode interaction, subagent, model, review, Goal, browser/device, MCP, and worktree capabilities from the effective surface | preflight/runtime adapter, native integration references, tests | capability-present and capability-absent paths with no global config mutation | complete |
| S17 Luna-first agent dispatch | Move closed bounded child execution into P0-P2 Luna while retaining Terra/Sol for open and consequential judgment | dispatch registry/resolver, orchestration, docs/tests | workload, closedness, risk, downgrade, fallback, and no-cost-only-delegation cases | complete |
| S18 Flow Activation Coverage | Replace effect metrics with deterministic, semantic, and negative branch-activation coverage | evaluation docs, flow activation fixtures/runner/tests, release tier | explicit and implicit activation, unexpected activation, and no composite score | complete |
| S19 Native Codex engineering bridges | Add light AGENTS health, native review, explicit Goal, worktree isolation, UI/device verification, and external-context adapters | focused references/runtime helpers/evals | each bridge activates only on positive trigger and degrades honestly | complete |
| S20 History and release convergence | Finish the 0.2-1.x disposition, current docs/version identity, isolated fresh-install/idempotence/uninstall smoke, high-fidelity pilots, and integrated verification | history disposition, release docs/tools, plugin/version surfaces, full suite | exact-SHA/source checks, the exercised isolated lifecycle smoke, pilots, contracts, plugin/Skill validation | complete |
| S21 Post-audit truth and activation hardening | Make semantic activation evidence executable, expand deterministic branch coverage, bind native capabilities to the current turn, and remove model-facing/release/version documentation drift | flow-metrics, preflight, catalogs, active prompts, release/workstream truth, version sample, regressions | focused adversarial checks, full suite, contracts, plugin/Skill validation, final reverse audit | complete |
| S22 RC.1 convergence | Freeze features, declare the hard 1.x cut, align version/state documents, run bounded semantic activation, tag, and push | manifest, README, changelog, workstream decisions/progress, semantic fixtures, Git | focused source checks, six matched semantic observations, annotated tag, verified remote refs | complete |

## Implementation rules

- Do not create a Dev Flow packet for this work.
- Treat 1.x packet data and commands as unsupported internals; never make them part of a 2.0 task or release promise.
- Keep manual edits scoped and use existing standard-library tooling.
- Prefer deleting mandatory coupling over adding adapters that reproduce it.
- Change tests with the behavior; preserve decision-useful cross-platform and security coverage.
- Do not commit, push, tag, publish, install, or release without separate authority.

## S2 details: routing and workstreams

- Use six primary task intents: research, diagnosis, design, change, review, and delivery; normalize audit compatibility inputs to review.
- Add `direct` and `managed` as the only new default continuity modes.
- Choose managed from multi-session/multi-slice/cross-module/coordination need, plus large feature/refactor/substantial migration defaults.
- Emit risk overlays independently.
- Emit knowledge disposition independently; direct work may update maintained truth or add one concise change note without becoming managed.
- Remove universal requirements, review, and method-selection routes from ordinary mutation; add independent review only for an explicit calibrated review need, not from an overlay label alone.
- Add `init-workstream`:
  - respect `--path` when a repository has its own convention;
  - default to `docs/workstreams/<slug>`;
  - create `implementation.md` and `progress.md` atomically;
  - create `requirements.md` only with `--with-requirements`;
  - create `design.md` only with `--with-design`;
  - create `decisions.md` only with `--with-decisions`;
  - refuse symlink/path escape and non-empty overwrite;
  - never create `.codex/dev-flow/current` or a packet.
- Do not advertise residual `init-packet` internals as a 2.0 interface.

## S3 details: Skills

- Rewrite `skills/dev-flow/SKILL.md` around the three-plane model.
- Replace core lifecycle and orchestration references with short 2.0 guidance.
- Simplify specialist entrypoints where they require packet artifacts or IDs.
- Keep deep technical checklists in specialist references and load them only when applicable.
- Add an always-on calibration and explicit recheck triggers without an artifact or lifecycle state.
- Require `route-agent` for actual child dispatch while keeping P0-P6 output ephemeral.
- Trigger bounded method consideration at high-leverage risk and failure signals; remove method records from 2.0 lifecycle closure.
- Replace exhaustive multi-agent brief requirements with the six-field brief.

## S4 details: Hooks

- Delete the Dev Flow process Hook instead of maintaining a partial command parser.
- Remove packet discovery, lifecycle enforcement, dependency approval, checkpoint, delegation, Stop validation, destructive-command parsing, and delivery confirmation from plugin Hook execution.
- Let host permissions, explicit user authority, and task guidance own destructive and external actions.
- Keep the independent data-security Hook, its bounded detector/redactor contract, negative cases, and doctor.
- Do not retain skipped process-Hook tests as a permanent compatibility burden.

## S5 details: knowledge

- Treat repository documents as normal tracked knowledge reviewed through Git.
- Remove new-work instructions for catalog, manifest, digest, promotion, and packet binding.
- Keep historical files user-owned but outside the 2.0 support contract.
- Update top-level documentation so teams may choose their own docs/ADR convention.

## S6 details: verification and release

- Create one full semantic CI job on Ubuntu/Python 3.14.
- Classify changed paths in one cheap Ubuntu job and start the focused compatibility matrix only for runtime, host, installer, bundled-agent, or compatibility-test paths.
- Keep the compatibility matrix across supported OS and minimum/latest Python boundaries when that path gate is active.
- Keep plugin, suite, methodology legacy data, knowledge legacy data, data-security, compile, and clean-tree validators in the semantic lane while they remain shipped surfaces.
- Remove duplicate full behavioral/contract/validator execution from the RC artifact workflow.
- Update runbook to select R1-R4 from changed surfaces.
- Keep immutable SHA binding, deterministic archive verification, SPDX SBOM, checksums, provenance, attestation, and least privilege for release artifacts.

## Verification strategy

### Focused

- new routing/workstream tests;
- zero-artifact calibration, conditional design, and dispatch-routing assertions;
- default-manifest no-process-Hook and data-security tests;
- updated routing fixture and lifecycle assertions;
- release workflow contract tests.

### Integrated

- `python3 -m unittest discover -s evals -v`;
- `python3 evals/run_contract_checks.py`;
- `python3 skills/dev-flow/scripts/dev-flow.py validate-methods --root .` for shipped legacy pool integrity;
- `python3 skills/dev-flow/scripts/dev-flow.py validate-knowledge --root .` for shipped legacy knowledge compatibility;
- `python3 skills/dev-flow/scripts/dev-flow.py check --plugin-root .`;
- `python3 skills/dev-flow-maintainer/scripts/validate-suite.py`;
- `python3 skills/company-data-security/scripts/doctor.py --plugin-root .`;
- `python3 -m compileall -q hooks skills evals tools`;
- `git diff --check` and final scope review.

### Evidence boundaries

- No live Codex install/upgrade/rollback unless separately authorized and justified by the final changed surfaces.
- No GitHub-hosted CI result until changes are pushed.
- No model evaluation unless final changes materially depend on model interpretation and a budget is authorized.
- No tag, release, publication, or user-profile installation in this task.
