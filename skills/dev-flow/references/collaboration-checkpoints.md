# Collaboration checkpoints

Use interaction to expose consequential decisions early, not to maximize messages or approvals.

## Select a collaboration profile

- `execute`: use for clear, reversible, low-risk work. Proceed with recorded assumptions and ask only at approval, safety, dependency, delivery, or material drift boundaries.
- `checkpointed`: default for non-micro work. Share discovery, reach Requirement Ready, confirm material design/scope, then implement with drift checkpoints.
- `co-design`: use for ambiguous product work, material UI/UX, architecture redesign, unfamiliar high-risk domains, or when the user wants to shape the solution iteratively.

Default micro work to `execute`, ordinary non-micro work to `checkpointed`, and material UI work to `co-design` unless the user explicitly selects another safe profile. A profile changes collaboration cadence, not verification rigor or authority.

In `execute`, an explicit implementation request may serve as the requirement/design approval record only when scoped discovery leaves no material behavior, architecture, compatibility, dependency, UI-direction, scope, or delivery choice unresolved. Record the repository-derived requirement and design before coding and cite the request as their authorization; do not ask for a ceremonial acknowledgement. If any material choice remains, switch to a checkpoint and obtain a fresh decision. Silence never supplies this approval.

## Run purposeful checkpoints

1. **Kickoff:** restate objective, authority, delivery boundary, known constraints, and collaboration profile. Do not block on facts that local discovery can answer.
2. **Discovery readout:** present observed facts, conflicts, unknowns, and the recommended requirement/design implications in a small batch.
3. **Requirement Ready:** confirm actors, flows, observable outcomes, failures, non-functional needs, acceptance criteria, non-goals, and protected behavior.
4. **UX Ready:** for material UI work, confirm the product/UX contract and design evidence before production implementation.
5. **Design and Scope Ready:** confirm material architecture, dependencies, compatibility, rollout/rollback, complete change scope, and verification obligations.
6. **Drift checkpoint:** pause only when evidence activates conditional scope, invalidates the design, crosses an authority boundary, or creates a material expansion.
7. **Acceptance and delivery:** present fresh evidence, limitations, residual risks, and `NOT RUN` gates. Obtain separate authority for commit, push, PR, release, deploy, or external communication.

Progress updates at meaningful boundaries are informational and do not require acknowledgement. User corrections supersede prior assumptions; record the correction and re-evaluate affected requirements, scope, tasks, and evidence before continuing.

## Ask high-value questions

Before asking, inspect repository instructions, current behavior, configuration, tests, nearby analogues, and runtime evidence. Ask only when the answer changes product behavior, architecture, public/data compatibility, dependency choice, security/privacy, material UI direction, scope, acceptance, or delivery.

Batch one to three related decisions when possible. For each question provide:

- the evidence and unresolved conflict;
- why the decision matters now;
- a recommended option;
- viable alternatives and concrete impact;
- the safe default, if one exists;
- what work is blocked by the answer.

Do not ask the user to choose between options that are not genuinely distinct. Do not hide major decisions inside a status update or implementation plan.

## Manage assumptions and silence

- Proceed with explicit, reversible, low-impact assumptions when they fit repository evidence and the selected profile; record the assumption and how it will be verified.
- Require a user decision for irreversible changes, public contracts, persisted data, security/privacy boundaries, new dependencies, material UI direction, destructive/external actions, and delivery.
- Lack of a response is never approval. Continue only independent work that does not cross the unresolved boundary.
- If questions multiply, return to repository evidence and consolidate the actual decision boundary instead of continuing a questionnaire.

## Define readiness

- **Instruction Ready:** applicable scoped rules are known, conflicts are resolved or blocking, and material rules map to downstream work.
- **Requirement Ready:** no unresolved question changes behavior, architecture, public/data compatibility, scope, acceptance, or delivery.
- **UX Ready:** the conditional gate in `frontend-product-and-ux-discovery.md` is satisfied.
- **Design and Scope Ready:** material choices, dependency state, full scope, migration/rollback, and verification obligations are approved.

Measure late requirement corrections, preventable rework, user overrides after implementation, unresolved assumptions, missed instructions, and first-attempt acceptance. Never use question count or message count as a success metric.
