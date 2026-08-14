# Dev Flow orchestration

## Classification

Classify independently by task playbook, project archetypes, risk modifiers, and delivery profile. Playbooks are micro, routine, bugfix, large-feature, large-refactor, migration, security, performance, release-hotfix, read-only audit, spike, dependency change, and rollback.

Risks include public API/wire/schema/data; auth/secrets/privacy/untrusted input; unsafe/FFI/ABI/platform lifecycle; concurrency/order/idempotency/backpressure; deletion/migration/rollback; browser/device/OS/toolchain compatibility; performance/resources; deployment/release; and weak evidence or large blast radius.

Escalate when a dependency/public contract appears, scope crosses components/roots, current behavior is unexplained, generated/lock/migration/release files change unexpectedly, three hypotheses/repairs fail, or requirements change materially.

## Lifecycle

1. Establish authority, runtime, instructions, roots, risks, and work mode. Persistent mutation requires traced/governed state; direct is non-mutating micro/spike only.
2. Route repository context/current behavior and bind artifact facts plus instruction/profile/native-control/Skill fingerprints. Rerun routing before mutation when task, risk, UI, capability, path, phase, or delivery changes.
3. Run `select-methods` from explicit phase, task, risk, signals, and evidenced prerequisites; follow `methodology-system.md`. Persist only the bounded observation → failure hypothesis → method → owner artifact → evidence trace, not the full pool. Reselect on phase, risk, premise, architecture, or oracle drift. Missing prerequisites use the recorded fallback and remain unresolved/`NOT RUN`.
4. For persistent work, persist original input and successive AI-understood requirement revisions. Resolve repository facts first, then ask one-to-three material questions per round until no material/high-risk ambiguity remains. Material UI additionally routes product/UX.
5. Compare repository-grounded design alternatives, failure/compatibility/rollback behavior, implementation slices, and verification strategy; bind current requirement and design digests to approval.
6. Confirm complete scope, dependency approvals, operations, and separate black-box/white-box verification obligations.
7. Build a dependency-aware task graph with outcomes, inputs, owned paths/symbols, non-goals, checks, resources, and stop conditions.
8. Freeze the smallest ready slice; rehydrate requirement/design/context/checkpoint; inspect edit sites/analogues; implement a coherent change including tests/docs/comments/generated surfaces; run narrow then relevant module/smoke checks; inspect diff, scope, drift, dependencies, secrets, and user work; update progress/checkpoint and record `change-set.v1`, knowledge disposition, and commit-ready state.
9. Replan when evidence invalidates an assumption. Stop at authority, dependency, destructive/external, or material scope boundaries.
10. Route verification, review test oracles, and run root basic blue/red challenge. Add clean-context independent review for explicit/governed risk; delivery readiness remains explicit.

No slice closes until intent, final bytes/files, decisions/drift, progress, narrow evidence, scope, limits, and recovery next action are durable. Pre-verification additionally requires aligned baseline/checkpoint, both test views, knowledge disposition, module/smoke status, and a diff/comment/documentation audit.

At every user-owned stop, remain in Default mode and apply `../../requirements-design/references/user-interaction.md`. Native structured input is a host adapter for bounded choices, not a collaboration-mode transition or a substitute for approval/secret channels.

## Task routing

- Micro: direct only when non-mutating and single-turn; persistent micro work is traced. Escalate on uncertainty, multiple slices/turns, delegation, or contract risk.
- Routine: traced mode, bounded subsystem and analogue, affected tests/static checks; review only when another trigger applies.
- Bugfix: inspect applicable instructions, causal path, tests, logs, and analogues; separate fact, inference, and unknown; bind direct, protected, and out-of-scope behavior; reproduce the failure and, when practical, prove a focused regression fails before the fix; then rerun the protected and nearby paths.
- Read-only: preserve repository state; evidence/findings are deliverable; remediation needs authority.
- Spike: define learning question, isolation, success evidence, adopt/reject boundary; do not silently ship.
- Large feature/refactor: map full flows/contracts/state/consumers; use coherent vertical slices and integrated review.
- Migration: inventory versions/consumers/data/order, coexistence, resumability, cutover, rollback, observation, cleanup.
- Security/performance: route applicable specialists and require threat/measurement baselines plus independent evidence.
- Release/hotfix/rollback: freeze target, artifacts, exact authorities, observation, and executable recovery.

## Drift

Classify a new fact before mutation as already scoped, conditional activation, implementation defect, design defect, evidence gap, unrelated opportunity, material scope expansion, or requirement ambiguity. Only a material/high-risk ambiguity or scope expansion reopens user approval. Never use implementation momentum as authority.

Rehydrate durable state at start/resume or compaction, user steering, premise/phase changes, slice start/end, delegation/reconciliation, failed-repair reassessment, pre-verification, and final claim. Wall-clock or tool-count reminders may catch long unbounded work but never replace these semantic triggers.

## Failure breaker

After three failed hypotheses or repair rounds, stop layering changes. Re-read first evidence and approved architecture; determine whether reproduction, model, design, environment, oracle, or authority is wrong, then reopen the appropriate owner.

Record each result with `record-iteration --kind <hypothesis|repair> --cause-id <stable-id> --cause-file <file-below-packet-artifacts> --outcome <failed|succeeded>`. The command binds the cause ID to the evidence file path and SHA-256 for the generation; aliases, evidence drift, deleted control state, and a cleared third-failure breaker fail closed. Three consecutive failures for the same generation, kind, and evidence-bound cause atomically block a schema 2.0 packet; a fourth attempt and state resumption are rejected. Resume only after the same evidence binding plus `--outcome reassessed --reopened-owner <owner>` records which upstream owner replaced the causal model, then explicitly transition out of `blocked`. Different evidence-bound causes do not share a counter, and success resets that cause.

## Optional process signals

Quantitative evaluation is supporting diagnostics, never a core workflow objective or substitute for evidence. Record only cheap, decision-useful signals already produced by work; never optimize question, finding, document, test, coverage, Skill, or artifact count as a quality proxy.
