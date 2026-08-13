# Core lifecycle

This is the canonical human-readable projection of `governance/capability-contracts.json`. Registered owner count is a compatibility fact, not a quality target. Use only applicable focused owners, while the quality kernel below always runs.

## Always-on quality kernel

Every persistent mutation, independent of routed specialists, must retain these invariants:

1. Repository facts and effective rules are fresh for the affected paths.
2. Original/sanitized input, AI-understood requirement revisions, user corrections, material ambiguity dispositions, AC/SC/VO, and approved repository-grounded design are durable.
3. A schema-1.1 recovery checkpoint binds requirement, design, engineering context, repository baseline/reconciliation, current objective, last evidence, next action, stop condition, and drift ruling so the task is recoverable after compaction/interruption.
4. Black-box and white-box obligations are derived separately; applicable views run, N/A has a concrete reason, and the oracle is challenged for failure sensitivity.
5. Root performs basic specification and adversarial challenge during requirements, design, implementation, verification, and final diff. Clean-context deep review remains risk-routed.
6. Project-knowledge impact is explicit; only implemented, verified, reusable truth is promoted.

If classification is uncertain, route the plausible owner until evidence resolves it. A missed specialist may reduce depth, but never removes the kernel.

## Forward path

1. `dev-flow` binds authority, work mode, route order, integration, and the exact claim being pursued.
2. `repo-context` establishes roots, instructions, current behavior, call paths, native controls, artifact facts, effective fingerprints, and minimum admitted technical Skills.
3. Persistent work always uses `requirements-design` to persist semantic understanding. For material UI, `product-ux-discovery` first establishes interface intent and UX Ready. Repeated high-value interaction continues until no material ambiguity remains.
4. For a bug or unexplained failure, `systematic-debugging` proves the earliest cause and affected invariant before a corrective design.
5. `architecture-decisions` owns structural choices; `dependency-decisions` separately owns external capability selection and graph mutation.
6. The root freezes the smallest ready coherent slice, updates continuity/progress at event boundaries, keeps code/tests/docs/comments together, runs narrow then integration/smoke checks, audits the diff, and records `change-set.v1` plus commit/knowledge readiness. OPEN checkpoints allow slice work after a low-cost repository identity/HEAD check; checkpoint, resume, delegation, pre-verification, and final-claim boundaries compare the full declared-root worktree. No specialist may enlarge its authority.
7. `verification` executes separately derived black-box/white-box risk oracles against final bytes and reviews test validity.
8. `change-review` independently reviews frozen source/change scope only when explicitly requested or routed by governed risk.
9. `delivery-readiness` evaluates an explicit delivery action only; ordinary mutation, verification, or rollback planning does not imply delivery authority.

`manage-engineering-profiles` is explicit profile lifecycle work. `dev-flow-maintainer` is explicit maintenance of Dev Flow itself. Neither is part of an ordinary repository task.

## Root change set

`change-set.v1` is inline for direct work and uses the existing ledger otherwise. Bind intent/protected behavior, final bytes/scope, files, decisions/drift, narrow checks, and limits. Creation-tagged packets bind it at each `verifying`; one-sided or post-binding drift blocks. Unsigned state is not tamper evidence. Untagged packets keep their old contract; upgrades require explicit migration. Later relevant byte changes invalidate affected evidence.

Quality-tagged packets also content-bind design approval, a pre-verification continuity checkpoint, engineering-context fingerprint, separate test-technique accounting, and project-knowledge disposition. Untagged legacy packets remain readable and are not retroactively tightened.

## Knowledge and engineering context

The three knowledge planes have different authority: tracked project truth describes current verified behavior; tracked change dossiers preserve requirement/design/execution/verification history; ignored packet state stores detailed recovery evidence. Current truth changes in place under Git, accepted ADRs are superseded rather than rewritten, and accepted dossiers use errata/follow-ups. Do not promote raw logs, secrets, unnecessary personal payloads, or generated facts better owned by code/schema.

At each phase/path/risk change, resolve applicable repository instructions, profiles, native controls, artifact facts, and installed Skills. First state the neutral capability outcome, then admit the minimum technical specialist by identity/fingerprint. User-local Skills do not silently become shared policy.

## Owner boundaries

| Owner | Owns | Must not substitute for |
|---|---|---|
| `dev-flow` | authority, mode, routing, lifecycle, root implementation integration, final change set, final claim state | repository discovery or specialist decisions |
| `repo-context` | observed repository/runtime facts and context gaps | user semantics, architecture, or dependency selection |
| `requirements-design` | user-owned semantics, acceptance, scope, compatibility intent, approval | technical implementation evidence |
| `product-ux-discovery` | IA, flows, states, accessibility intent, design truth, UX Ready | final product approval or rendered verification |
| `systematic-debugging` | reproduction, hypotheses, earliest cause, invariant | broad redesign or proof that a fix works |
| `architecture-decisions` | boundaries, ownership, state, concurrency, lifecycle, compatibility mechanics | dependency approval or test execution |
| `dependency-decisions` | external capability, version/features, graph, supply chain, rollback/removal | product semantics or delivery authority |
| `verification` | oracles, commands, environments, evidence, evidence status | design, repair, review, or acceptance |
| `change-review` | verified findings, severity, classification, disposition | upstream design or missing execution evidence |
| `delivery-readiness` | exact readiness level, residual gates, rollback, action-specific authority | implementation or inferred permission |
| `manage-engineering-profiles` | profile ownership, resolution, promotion, retirement, waiver | product or repository decisions |
| `dev-flow-maintainer` | Dev Flow public surfaces, compatibility, governance, and evaluation policy | ordinary product work |

## Reopen and stop rules

- Verification or review may expose an upstream defect, but may not repair the missing requirement, diagnosis, architecture, or dependency decision inside its own artifact. Return the issue to its owner, then rerun only affected downstream evidence.
- Initial routing is provisional. When repository evidence changes task type, risk, UI impact, requested capability, or delivery need, rerun routing and record the delta before mutation; never preserve a smaller route merely because work already started. Escalate on newly discovered risk. Remove a route only when exact evidence disproves an inferred trigger; never downgrade a user-declared risk, need, or authority boundary.
- A user-owned semantic or scope change invalidates affected approvals. A final-byte change invalidates affected verification and review evidence.
- Context compaction, resume, user correction, premise/phase change, slice/team boundary, repeated failure, pre-verification, and final claim trigger rehydration from durable requirement/design/context/checkpoint state. Time/tool-count reminders are advisory, not correctness gates.
- `implementation-start`, `resume`, `user-steering`, `slice-start`, `reconciliation`, and `premise-change` are OPEN-slice triggers. `slice-end`, `delegation`, `phase-transition`, `pre-verification`, and `final-claim` are SEALED-slice triggers. Ordinary mutation checks repository identity and Git `HEAD` without repeatedly hashing worktree bytes; sealed boundaries bind and compare the full worktree.
- Repository observation conservatively covers each entire declared root. A non-Git root is recorded with `observable=false`, so byte stability needs external/manual evidence. A Git `HEAD` change requires explicit reconciliation with the exact accepted object ID; ordinary resume may not silently adopt it. Repository-identity changes reopen the premise or require a new packet.
- Three failed hypotheses or repair rounds on the same cause stop local iteration. Reassess the reproducer, requirement, architecture, environment, and oracle before another repair.
- `PASSED`, `FAILED`, `FLAKY`, `BLOCKED`, `NOT RUN`, and `WAIVED` remain distinct. A downstream green result never upgrades an unresolved upstream state.
- Commit, push, PR, tag, release, deploy, install, migration execution, and external messages each require their own authority.
