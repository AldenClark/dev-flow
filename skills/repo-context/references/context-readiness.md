# Engineering Context Readiness

ECR is task-relative sufficiency, not a profile-completeness score. It asks whether enough applicable evidence exists to proceed safely and whether material gaps have an owner, minimal remedy, suppression, fallback, or waiver.

## Tiers

| Tier | Typical work | Missing-context behavior |
|---|---|---|
| `T0 incidental` | explanation, disposable spike, tiny obvious edit | no gate or setup recommendation |
| `T1 lean` | bounded bug fix or routine edit | require root/scope, instructions, native operations, language/toolchain, and authority; warn once when safely derivable |
| `T2 standard` | multi-file feature/refactor, architecture/dependency choice, durable shared project | add architecture/boundary, targets, decisions, tests, profile/language scope, and quality coverage; material gaps create a skippable checkpoint |
| `T3 governed` | public contracts/data, security, unsafe/FFI, migration, release/deploy, regulated or cross-repository work | require ownership, compatibility/migration/rollback, security/authority, verification/release and governed quality coverage; unsafe unknowns block or require authorized waiver |

Select by risk and reversibility, not repository size. Greenfield is not automatically T3; a one-line authentication or schema change can be.

## Dimensions

Assess only what applies:

1. authority and delivery boundaries;
2. Git roots, worktree state, scope, generated or nested repositories;
3. active host, tools, bounded repository/user/admin/system/plugin Skill roots, and environment limits;
4. effective instruction chain, source digests, and conflicts;
5. personal/team/project/component/task profile evidence and ownership;
6. product outcome and protected behavior;
7. per-artifact phase, role, boundary, language/framework/version, path, component, and risk facts;
8. repository-native commands, CI, test and codegen paths with source digests;
9. architecture, boundaries, state, errors, concurrency, resources, and current behavior;
10. dependencies, tool/service approvals, snapshots, and rollback;
11. public API, protocol, schema, persisted data, migration, and compatibility;
12. security, privacy, permissions, unsafe, FFI, and secrets;
13. product/UX/accessibility states and design truth;
14. verification oracles, environments, freshness, privacy, and status;
15. operations, rollout, rollback, observability, packaging, and release;
16. collaboration, review ownership, branch/delivery policy, and changed-file accounting;
17. source applicability, freshness, conflicts, broken references, and context cost;
18. safe minimal remediation;
19. Engineering Quality Assurance Coverage.

## EQAC

Derive neutral outcome obligations from phase, role, boundary, language/framework/version, path, component, and risk before choosing any implementation-specific route. Resolve coverage in this order:

1. repository-native compiler/typecheck, formatter, selected lint/static analysis, tests, codegen validation, security/supply-chain checks, CI and protected-branch controls;
2. concise scoped owned invariants in instructions, profile `quality-policy`, ADR, or accepted decision;
3. the minimal active-host-compatible, admitted and evaluated specialist capability that covers the remaining outcome;
4. qualified independent/manual review, explicit fallback, or authorized waiver.

Observed Skills are candidates, not approval or policy. Discover only the active host's bounded repository, user, admin, system, and verified Codex plugin roots. Record provenance, authority, digest/version, host compatibility, scope, tools/permissions/side effects, context cost, source freshness, collision set, validation, paired utility, fallback, and state. A same-name collision remains explicit until an admission binds a unique digest/version/path. A bounded scan may say `not-observed`; it must not claim a plugin is globally uninstalled. Only `approved` routes are normally recommended; `trial` requires an explicit note. Never auto-install, enable, rewrite, or promote a candidate.

A personal admission may support an interactive local task, but it cannot by itself satisfy a baseline/team/project/component/task quality policy. Shared policy coverage needs repository-native evidence, a non-personal admission, an owned shared fallback, or a scoped authorized waiver.

Absence of a style guide or named Skill is not a gap. An applicable quality outcome without acceptable coverage or fallback is.

A config file proves only that a native control is available, not that it ran or that it covers semantic judgment. Capabilities marked `contextual_review_required` (for example security, FFI, or accessibility) need qualified contextual coverage in addition to any scanner/test evidence; final verification separately records actual execution and results.

## Outcomes

- `not_applicable`: no useful gate for this task;
- `ready`: all required dimensions covered;
- `partial_advisory`: safe to continue with one useful reminder;
- `checkpoint`: owner context or an explicit skip/waiver is required;
- `blocked`: a required T3 safety/authority/compatibility fact cannot be guessed;
- `waived`: the authorized owner accepted recorded residual risk for a scope and duration.

Missing personal profiles never block. Missing team/project profiles remain advisory when equivalent native evidence or accepted decisions exist. Missing `AGENTS.md` never blocks by itself. Missing optional specialist Skills never block by themselves.

## Context binding and re-resolution

Bind separate digests for the effective instruction chain, resolved profile stack, repository-native controls, artifact facts/version sources, capability registry, and bounded Skill catalog. Their aggregate is the engineering-context fingerprint. Re-resolve before relying on an old snapshot when the task path/component/role/boundary, phase, language/framework/version, risk, instruction/profile/native-control/Skill digest, admission, or waiver state changes. This is an event boundary, not a timer.

## Reminder, suppression, and waiver

Fingerprint repository identity, tier, gap set, and source hashes. Do not repeat a dismissed reminder until the tier or fingerprint changes. A waiver records owner, reason, affected paths/operations, residual risk, expiry/recheck trigger, and applicable policy. A block names the missing fact, affected operation, evidence checked, minimal remedy, and waiver policy.

Record a packet waiver with `dev-flow.py record-approval <packet> waivers` plus `--scope`, every covered `--blocker`, `--residual-risk`, a future timezone-aware `--expires-at`, and `--recheck-trigger`. A generic approval note, expired record, out-of-scope record, or partially covered blocker set never changes ECR to `waived`.

## Remediation

Prefer deriving facts from canonical sources, asking one focused owner question, repairing native enforcement, recording an ADR/decision, or proposing a minimal scoped profile/instruction change. Generation is review-first and labels observed facts, inference, and owner input. Never write merely because ECR found a gap.
