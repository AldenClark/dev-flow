# Requirements, design, and scope

## Scan before questions

Before asking the user to choose a requirement or design:

1. Locate every real repository root and reach Instruction Ready through `repository-instructions-and-conventions.md`.
2. Identify entry points, call/data flow, ownership boundaries, state, contracts, and tests.
3. Inspect manifests and existing dependencies before suggesting new ones.
4. Find one or more working analogues and recent relevant changes.
5. Establish current behavior through tests, runtime evidence, or code trace.
6. List facts, hypotheses, unknowns, and conflicts with engineering preferences.

Ask only questions that cannot be answered from the repository and whose answer would materially change behavior, architecture, scope, compatibility, dependency selection, risk, or delivery.

Follow `semantic-requirement-clarification.md` before Requirement Ready. A structured `AMB-n` record is required whenever two plausible interpretations survive repository investigation. User-owned material semantics require an explicit user disposition; Codex-owned repository facts require evidence, not a questionnaire.

Select and follow the collaboration profile in `collaboration-checkpoints.md`. For user-facing work, classify UI impact and follow `frontend-product-and-ux-discovery.md` before treating requirements or design as ready.

## Requirement model

Capture:

- target user or system actor, context, problem, and successful outcome;
- actor or caller;
- trigger and preconditions;
- inputs, validation, and trust boundary;
- desired output and state transition;
- errors, cancellation, retry, timeout, and recovery;
- authorization and privacy;
- compatibility and migration;
- performance and resource constraints;
- observability and supportability;
- acceptance criteria and non-goals.

For `preserve` or `material` UI impact, also capture immutable product/IA/flow constraints and the applicable product/UX contract. Do not prescribe visual or technical implementation before its direction is approved.

Give acceptance criteria stable IDs such as `AC-1`. Use observable language and avoid prescribing implementation unless it is an approved constraint.

## Design record

The approved design must include:

- repository evidence and current behavior;
- requirement delta and assumptions;
- engineering preferences that affect the choice;
- viable alternatives and tradeoffs;
- selected architecture, data/control flow, ownership, and failure handling;
- dependency decisions and approval state;
- compatibility, migration, rollout, rollback, and cleanup;
- security, performance, operational, documentation, and testing consequences;
- unresolved risks and explicit user decisions.

It must also identify the collaboration profile, Instruction Ready evidence, Requirement Ready decision, conditional UX Ready decision, and the drift conditions that return work to discovery.

For schema 1.2, bind the design to the current requirement revision and SHA-256 digest, trace disposed `AMB-n` records into the selected behavior, and specify how a late material ambiguity reopens approval.

Confirm high-impact sections with the user before calling the design final. Do not hide major decisions inside an implementation plan.

## Mandatory change scope

Every non-micro design contains:

- **Direct scope:** files, modules, APIs, data, UI, jobs, or artifacts intentionally changed.
- **Indirect scope:** callers, consumers, generated output, tests, docs, configuration, packaging, metrics, or deployment affected by the direct change.
- **Conditional scope:** changes activated only if discovery or tests prove they are necessary.
- **Protected scope:** behavior, interfaces, data, files, or platforms that must remain unchanged.
- **Explicitly out of scope:** tempting adjacent refactors or product changes excluded from this task.
- **Delivery scope:** whether commit, push, PR, tag, release, migration, deployment, or external communication is authorized.

Assign scope IDs such as `SC-D1`, `SC-I1`, and `SC-P1`. Trace tasks and evidence back to them.

## Drift control

During implementation, classify every newly discovered change as:

- already covered by scope;
- necessary conditional scope activation;
- defect in the approved design;
- unrelated opportunity;
- material scope expansion requiring user approval.

Also distinguish a clear implementation defect from missing evidence and an ambiguous intended requirement. Only the last category enters the ambiguity/reopening protocol; do not ask the user to diagnose an implementation defect or rediscover repository facts.

Record the classification before changing code. Do not use implementation momentum as authorization.
