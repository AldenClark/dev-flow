# Dev Flow orchestration

## Classification

Classify independently by task playbook, project archetypes, risk modifiers, and delivery profile. Playbooks are micro, routine, bugfix, large-feature, large-refactor, migration, security, performance, release-hotfix, read-only audit, spike, dependency change, and rollback.

Risks include public API/wire/schema/data; auth/secrets/privacy/untrusted input; unsafe/FFI/ABI/platform lifecycle; concurrency/order/idempotency/backpressure; deletion/migration/rollback; browser/device/OS/toolchain compatibility; performance/resources; deployment/release; and weak evidence or large blast radius.

Escalate when a dependency/public contract appears, scope crosses components/roots, current behavior is unexplained, generated/lock/migration/release files change unexpectedly, three hypotheses/repairs fail, or requirements change materially.

## Lifecycle

1. Establish authority, runtime, instructions, roots, risks, and direct/traced/governed work mode; create persistent state only for traced/governed work.
2. Route repository context and current behavior.
3. Route requirement/design and product/UX only when their triggers apply.
4. Resolve effective profiles and material decisions without loading unrelated catalogs.
5. Confirm complete scope, compatibility, dependency approvals, rollback, and verification obligations.
6. Build a dependency-aware task graph with outcomes, inputs, owned paths/symbols, non-goals, checks, resources, and stop conditions.
7. Implement the smallest coherent ready slice; run its narrow check; inspect drift, generated/dependency changes, secrets, and user-owned work; update the packet.
8. Replan when evidence invalidates an assumption. Stop at authority, dependency, destructive/external, or material scope boundaries.
9. Route verification. Add independent review for explicit/governed risk and delivery readiness only for explicit delivery or release/rollback work.

No slice closes until progress, decision/drift, scope mapping, verification, and changed-file evidence are durable.

At every user-owned stop, remain in Default mode and apply `../../requirements-design/references/user-interaction.md`. Native structured input is a host adapter for bounded choices, not a collaboration-mode transition or a substitute for approval/secret channels.

## Task routing

- Micro: direct inline record, exact file/caller/test, no packet or delegation; escalate on uncertainty or contract risk.
- Routine: traced mode, bounded subsystem and analogue, affected tests/static checks; review only when another trigger applies.
- Bugfix: route to systematic debugging and require causal/regression evidence.
- Read-only: preserve repository state; evidence/findings are deliverable; remediation needs authority.
- Spike: define learning question, isolation, success evidence, adopt/reject boundary; do not silently ship.
- Large feature/refactor: map full flows/contracts/state/consumers; use coherent vertical slices and integrated review.
- Migration: inventory versions/consumers/data/order, coexistence, resumability, cutover, rollback, observation, cleanup.
- Security/performance: route applicable specialists and require threat/measurement baselines plus independent evidence.
- Release/hotfix/rollback: freeze target, artifacts, exact authorities, observation, and executable recovery.

## Drift

Classify a new fact before mutation as already scoped, conditional activation, implementation defect, design defect, evidence gap, unrelated opportunity, material scope expansion, or requirement ambiguity. Only a material/high-risk ambiguity or scope expansion reopens user approval. Never use implementation momentum as authority.

## Failure breaker

After three failed hypotheses or repair rounds, stop layering changes. Re-read first evidence and approved architecture; determine whether reproduction, model, design, environment, oracle, or authority is wrong, then reopen the appropriate owner.

## Metrics

Record only available values: first-attempt acceptance, requirement churn, scope drift, repair depth, evidence health, test stability, delegation efficiency, and real delivery/recovery measures. Grade first output separately from repairs. Never optimize question, finding, instruction-file, or artifact count as a quality proxy.
