# Semantic requirements, approval, and scope

## Collaboration profiles

- `execute`: requirements are explicit and repository facts resolve the implementation safely; do not add ceremonial approval gates.
- `checkpointed`: Codex leads discovery and design, pausing only for material user-owned decisions.
- `co-design`: product/architecture direction has several valid outcomes and is shaped with the user before implementation.

UI impact and collaboration mode are independent. Use `none`, `preserve`, or `material` for UI; material UI requires UX Ready.

Interaction surface and collaboration profile are also independent. Keep every profile in Default mode and use `user-interaction.md` to route bounded choices, open discussion, approvals, secrets, unavailable tools, and cancellations.

## Requirement model

Maintain an ordered truth chain: sanitized original source; each AI-understood revision; repository evidence; user corrections/decisions; and the current requirement truth that supersedes earlier interpretations. Capture actor/caller, trigger/preconditions, input/trust boundary, validation, output/state, errors, cancellation, retry, timeout, recovery, authorization/privacy, compatibility/migration, performance/resources, observability/support, acceptance, non-goals, and bounded assumptions.

Use stable IDs:

- `AC-n`: observable acceptance;
- `AMB-n`: surviving semantic ambiguity;
- `SC-D/I/C/P/O/Ln`: direct, indirect, conditional, protected, out-of-scope, delivery scope;
- `VO-n`: verification obligation;
- `DEP-n`: separately approved dependency choice.

## Ambiguity ownership

Create an ambiguity only when at least two plausible interpretations survive repository investigation and the choice changes behavior, data, public contract, security, compatibility, architecture, scope, dependency, risk, or acceptance.

Record summary, source, interpretations, evidence, materiality, owner, affected IDs, recommendation, status, and eventual resolution/evidence. Owners are:

- Codex for repository-resolvable facts;
- user for final material requirement/product/authority semantics.

Low-risk assumptions must be evidence-backed, visible, reversible, and outside protected boundaries. A worker or reviewer cannot resolve user-owned semantics. Requirement Ready means semantic closure: no unhandled material/high-risk ambiguity and every remaining assumption explicitly disposed. It does not mean unknowable future facts have disappeared.

After each material answer or correction, update the durable baseline before downstream work continues. Questions are batched only for cognitive clarity (normally one-to-three); repeat rounds when needed and never optimize interaction count.

## Design record

Include current evidence, requirement delta, applicable preferences, product/scope alternatives and tradeoffs, selected observable behavior, acceptance, constraints, compatibility intent, migration/rollout/rollback outcomes, operations/docs/testing obligations, unresolved risks, approval, and links to separately owned architecture or dependency artifacts when routed.

The record may constrain architecture through approved behavior, compatibility, safety, performance, or operational requirements, but it does not select technical control/data flow, state ownership, concurrency/lifecycle mechanics, or an external capability. Those remain owned by `architecture-decisions` and `dependency-decisions`.

Do not hide high-impact choices in tasks. A dependency approval names the exact option and impact; design approval does not imply delivery.

## Complete scope

- Direct: intentionally changed files/modules/APIs/data/UI/jobs/artifacts.
- Indirect: callers, consumers, generated outputs, tests, docs, config, packaging, metrics, deployment.
- Conditional: activated only when named discovery/test evidence proves necessary.
- Protected: behavior/contracts/data/platforms/files that must remain unchanged.
- Out of scope: tempting adjacent refactors or product changes.
- Delivery: edit, commit, push, PR, tag, release, migration, deploy, or message authority.

Classify late discovery before mutation as covered scope, conditional activation, implementation defect, design defect, evidence gap, unrelated opportunity, material scope expansion, or requirement ambiguity.

## Content-bound approval

For readiness-capable packet schemas, compute the requirement digest from the current requirements artifact. Requirement Ready and design approval record revision, digest, approver, time, and note. A later material/high-risk ambiguity invalidates affected approval and returns work to `awaiting-approval`; preserve old approval as history.

Do not reopen for implementation defects, evidence gaps, or unrelated opportunities. Reopen only the affected semantic baseline and downstream tasks.
