# Core lifecycle

This is the canonical human-readable projection of `governance/capability-contracts.json`. Use only the owners applicable to the task; the route list is an execution order, not a checklist.

## Forward path

1. `dev-flow` binds authority, work mode, route order, integration, and the exact claim being pursued.
2. `repo-context` establishes roots, instructions, current behavior, call paths, native controls, facts, and unknowns.
3. For material UI work, `product-ux-discovery` first establishes interface intent and UX Ready. `requirements-design` then binds material user-visible semantics, scope, compatibility intent, and approval.
4. For a bug or unexplained failure, `systematic-debugging` proves the earliest cause and affected invariant before a corrective design.
5. `architecture-decisions` owns structural choices; `dependency-decisions` separately owns external capability selection and graph mutation.
6. The root implements the smallest approved coherent change. No specialist may silently enlarge its authority while handing work back.
7. `verification` executes the risk-based oracles against the final relevant bytes.
8. `change-review` independently reviews frozen source/change scope only when explicitly requested or routed by governed risk.
9. `delivery-readiness` evaluates an explicit delivery action only; ordinary mutation, verification, or rollback planning does not imply delivery authority.

`manage-engineering-profiles` is explicit profile lifecycle work. `dev-flow-maintainer` is explicit maintenance of Dev Flow itself. Neither is part of an ordinary repository task.

## Owner boundaries

| Owner | Owns | Must not substitute for |
|---|---|---|
| `dev-flow` | authority, mode, routing, lifecycle, integration, final claim state | repository discovery or specialist decisions |
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
- A user-owned semantic or scope change invalidates affected approvals. A final-byte change invalidates affected verification and review evidence.
- Three failed hypotheses or repair rounds on the same cause stop local iteration. Reassess the reproducer, requirement, architecture, environment, and oracle before another repair.
- `PASSED`, `FAILED`, `FLAKY`, `BLOCKED`, `NOT RUN`, and `WAIVED` remain distinct. A downstream green result never upgrades an unresolved upstream state.
- Commit, push, PR, tag, release, deploy, install, migration execution, and external messages each require their own authority.
