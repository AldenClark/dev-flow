# Dev Flow 2.0 RC.3 design

## Design position

RC.3 is a reliability, scope-convergence, method-realization, and repository-knowledge release. It does not add another orchestration layer or a larger method catalog. The design closes the gap between correct deterministic routing and reliable behavior across real task transitions while making implementation convergent by default.

The architecture remains:

```text
natural task
  -> host Skill discovery
  -> repository facts and instructions
  -> ephemeral route or justified skip
  -> ephemeral scope envelope
  -> required capability owners
  -> bounded method disposition when a concrete failure mechanism warrants it
  -> smallest implementation/analysis slice
  -> native verification
  -> boundary/failure/continuity/final-diff recalibration
  -> honest close or repository handoff
```

The scope envelope is a reasoning and enforcement input, not a new lifecycle object:

```text
confirmed outcome + protected behavior + explicit non-goals
                    |
                    v
 discovery mode + read boundary + write boundary + action authority
                    |
                    v
       root work / narrowed delegation / native evidence
                    |
                    v
       actual-diff and terminal-condition reconciliation
```

Repository knowledge is an owned capability beside repository context, not a replacement for it:

```text
repo-context             repository-knowledge
facts for this task      knowledge-system establishment
       |                           |
       +------------+--------------+
                    v
      AGENTS router -> stable index -> one knowledge owner
                    -> task-specific replaceable map
                    -> manifests/tests/CI enforcement
```

## Architecture decisions

### 1. Model transitions, not persisted task states

RC.2 describes recalibration triggers, but its strongest evaluations are first-attempt or single-route oriented. RC.3 makes transitions explicit in guidance and evaluation:

- entry: classify the current request and decide route/skip;
- expansion: a new risk, repository, platform, external system, or semantic decision appears;
- intent change: research/diagnosis becomes change, change becomes review, or review becomes delivery;
- evidence invalidation: final bytes change or the first failure contradicts the oracle;
- interruption/fork: reconcile repository state before continuing;
- close: bind claims to current bytes and separate remaining gates.

These are decision events, not durable lifecycle statuses. The repository workstream remains the only managed continuity artifact.

### 2. Normalize documented route values before argparse rejection

The route CLI currently validates several values inside the command implementation, where it can return structured suggestions, but argparse `choices` rejects intent and other enumerations before that contract runs.

RC.3 introduces one normalization/validation layer for the documented value-taking `route-task` options:

- accept canonical values unchanged;
- normalize only explicit documented aliases, initially `diagnosis -> diagnose`;
- return `status=invalid`, allowed values, bounded suggestions, and a portable `corrected_command` for correctable input;
- return structured invalid output without a correction when intent is ambiguous or unsafe to infer;
- keep raw argparse failure for unknown flags, missing option values, mutually exclusive syntax errors, and commands outside the public value contract.

This is additive for valid callers. Canonical output remains unchanged unless a new optional field is consumed.

Structured invalid output uses a stable task-facing shape:

```json
{
  "status": "invalid",
  "errors": ["unknown intent: diagnoise"],
  "field": "intent",
  "input": "diagnoise",
  "allowed_values": ["change", "delivery", "design", "diagnose", "research", "research-audit", "review"],
  "suggestions": {"diagnoise": ["diagnose"]},
  "corrected_command": "python3 /absolute/plugin/path/dev-flow.py route-task ..."
}
```

`corrected_command` is present only when one bounded replacement preserves the rest of the request. The exact error text may evolve; the structured fields and semantics are the contract.

The implementation preprocesses only the `route-task` argv value positions before argparse applies `choices`. It preserves original option ordering and repetition for replay, then passes canonical values into the existing parser and route implementation. It does not turn arbitrary fuzzy matches into accepted aliases.

### 3. Keep the route projection single-purpose

The existing output already has three distinct owners:

- `routes`: built-in owners required by the current declared facts;
- `capability_activation.specialist.matches`: effective specialist routes or qualified fallbacks;
- `repo-context`: on-demand candidates discovered from actual repository/framework facts.

RC.3 does not add `route_details`. No current caller consumes it, compact and full output intentionally project `routes` differently, and a second schema would increase compatibility surface without fixing the observed over-routing. Precision is improved in the existing projection instead.

Routing refinements:

- managed continuity alone does not imply unresolved product semantics;
- `persisted-data` alone does not imply a migration overlay;
- migration controls require schema, mixed-version, compatibility, deletion, rollback, or explicit migration evidence;
- review intent loads requirements only for ambiguity, public/data semantics, or an explicit requirements need;
- architecture remains risk-triggered rather than a default synonym for complexity.

### 4. Add capability readiness and failure isolation

No universal tool probe is reliable, and the existing capability registry owns built-in Skill topology rather than arbitrary host/plugin tool readiness. RC.3 therefore changes agent guidance and semantic fixtures, not the registry schema or route output.

For a high-leverage optional capability, the active guidance establishes when observable:

- prerequisites visible before invocation;
- whether a cheap readiness probe exists;
- failure classes that cannot change in the unchanged current task environment;
- a qualified fallback and its claim limit;
- the facts that permit a retry.

After an invariant first failure, the agent treats a repeat in the unchanged context as unjustified. This behavior is intentionally not persisted or represented as a deterministic runtime guarantee. A managed handoff records only the blocked gate and retry condition in `progress.md`.

Failure isolation follows:

```text
capability fails
  -> classify transient / invariant / authorization / external
  -> preserve raw first failure
  -> continue independent safe gates
  -> use qualified fallback when allowed
  -> report BLOCKED capability and claim limit
```

### 5. Add a scope and evidence-freshness checkpoint

The checkpoint is triggered by meaning, not a hard file-count score. Observable signals include:

- a new repository, platform, or product boundary;
- a materially different user outcome;
- implementation followed by a complete audit or delivery request;
- repeated compaction/interruption with unresolved changes;
- a final diff whose affected boundaries exceed the previous verification model.

The checkpoint performs:

1. Git-root and user-change reconciliation.
2. Outcome/slice boundary restatement.
3. Evidence-to-byte mapping and stale-evidence invalidation.
4. Workstream progress update when managed.
5. Recommendation to continue, create a new slice/task, or freeze an immutable delivery candidate.

It never creates a task, worktree, commit, or tag without authority.

### 6. Promote repository knowledge as a first-class owner

The current `repository-knowledge` implementation is the RC.3 baseline. Its contract remains explicit: ordinary code tasks update their nearby owning document and do not invoke a knowledge-system audit.

RC.3 completes:

- plugin and governance registration;
- audit/plan/map/bootstrap/check documentation;
- single-repository, monorepo, nested-root, multi-repository workspace, generated-root, symlink, link, and budget cases;
- one canonical-owner rule for durable facts;
- human-and-agent writing guidance;
- optional stable catalogs only where a confirmed program and consuming tool justify them;
- task maps as local/generated evidence rather than committed policy.

No root AGENTS.md is generated merely because a repository lacks one. The plan must show which non-discoverable facts justify it.

Knowledge lineage is explicit so generated observations cannot silently become policy:

| Source | Transformation | Destination/owner | Freshness and removal |
|---|---|---|---|
| Git roots, tracked paths, manifests | deterministic scan | temporary inventory | replace on every scan; do not commit by default |
| manifests, CI, scripts | command/control extraction | stable index links or AGENTS golden commands | recheck when native owner changes; native file remains authoritative |
| maintained docs and owner input | disposition plan | one canonical current-truth, ADR, runbook, or index owner | normal Git review; retire duplicates after approved migration |
| source symbols and lexical task terms | bounded ranking | replaceable task map | revision/task-bound; discard after use or regenerate |
| inferred structure or frequency | labeled proposal | review queue only | never promote without owner confirmation |
| policy/test/schema facts | link and enforcement mapping | manifests, tests, linters, CI, schemas | update at the enforcing owner; prose links rather than copies |

The scanner must not retain file contents, raw production data, secrets, full transcripts, or a permanent per-user knowledge ledger.

### 7. Keep release orchestration incubation outside RC.3 qualification

RC.3 adds an integration contract, not a generic release Skill.

A product-owned release capability should separate:

- Skill: intent, component selection, evidence interpretation, user checkpoints, authority, and recovery decisions;
- resumable CLI: deterministic discovery, plan/state, document/version consistency, per-repository actions, monitoring, reconciliation, and structured evidence;
- child repositories: native build, test, signing, packaging, publication, deployment, and rollback commands;
- Dev Flow delivery readiness: exact targets, provenance, remaining gates, rollback assets, authority, and post-action confirmation.

The first product pilot should produce evidence from at least two releases. A generic Dev Flow capability may be proposed only after a second product demonstrates matching states, actions, and recovery semantics. Product-specific fields must not be copied into the core contract.

RC.3 retains this boundary as a design decision and documentation link only. Building or exercising the product-owned workflow belongs to a separate repository/workstream with separate mutation and external-action authority; its result is a stable-release input, not an RC.3 source gate.

### 8. Add a layered evaluation model

RC.3 qualification uses four distinct evidence layers:

1. Deterministic route/parser tests: exact inputs, outputs, corrections, method candidate/readiness projection, negative controls, and mutations.
2. Stateful semantic transition fixtures plus an observation validator: multi-turn prompts with expected activation/recalibration/method-disposition/stop behavior, without invoking a model.
3. A separately authorized bounded model runner: isolated temporary Codex homes, persisted sessions only inside that temporary home for `exec resume`/`exec fork`, first-attempt preservation, method-realization and outcome/trajectory observations, and sanitized export before cleanup.
4. Privacy-safe dogfood audit: sanitized shapes from real tasks, reporting activation latency, invalid route attempts, blocked capabilities, method disposition/realization, stale evidence, and scope transitions without an aggregate productivity score.

Each layer has a negative control. A green route test cannot substitute for host Skill discovery, and a model trial cannot prove production effectiveness.

### 9. Make scope an ephemeral execution envelope

RC.3 derives one compact scope envelope from the confirmed request, current repository facts, and managed workstream when present. It contains only the decisions needed to keep the active slice convergent:

- observable outcome and terminal condition;
- protected behavior and explicit non-goals;
- discovery mode: `closed`, `bounded`, or `open`;
- admitted Git roots and relevant read boundary;
- admitted mutation paths, components, and contracts;
- verification boundary and stale-evidence triggers;
- dependency, external-action, delivery, and delegation authority;
- expansion and stop triggers.

The envelope is not added to `route-task`, a packet, the capability registry, or a task database in RC.3. Direct work keeps it in active reasoning. Managed work persists only durable semantic changes, non-goals, boundary decisions, or handoff facts in the existing workstream. A later consumer may justify an additive machine-readable projection, but no current behavior depends on one.

The boundaries are intentionally asymmetric. A read-only review can inspect callers or consumers without obtaining write authority. A bounded implementation can run affected repository-wide tests without obtaining repository-wide mutation authority. Verification breadth and implementation breadth are separate decisions.

### 10. Separate exploration breadth from reasoning depth

The discovery modes are semantic behaviors, not public route values:

| Mode | Default use | Permitted expansion | Forbidden implication |
|---|---|---|---|
| `closed` | implementation and defect repair | causal code, callers/consumers, configuration, tests, and native evidence necessary for the admitted outcome | repository redesign, optional cleanup, new platform/dependency |
| `bounded` | diagnosis and review | one evidence-backed causal, contract, or risk boundary at a time | promoting a finding into implementation without admission |
| `open` | explicit requirements/architecture/research exploration | broader read-only alternatives and scenarios inside the named product/program question | automatic source mutation or indefinite exploration |

`deep`, `complete`, `careful`, red/blue analysis, formal methods, higher reasoning effort, or a stronger model changes the rigor inside the selected mode. It never changes the mode itself.

Every new finding receives one disposition:

| Finding | Admission rule | Current-task behavior |
|---|---|---|
| required defect | current acceptance cannot pass without it and semantics are already confirmed | repair inside current boundary |
| necessary enabler | required outcome needs it but a material premise may change | recalibrate; confirm material semantic/repository/dependency/platform expansion |
| optional opportunity | useful but not necessary for current acceptance | report or defer; do not implement |
| unrelated | no causal or contract relevance to current outcome | exclude |

This classification replaces ad hoc “while we are here” expansion. It does not force a new issue or backlog system.

### 11. Close the method activation-to-evidence loop

The methodology registry remains an advisory knowledge source. RC.3 adds no method lifecycle or persisted selection record; it makes the existing bounded selection usable in ordinary verification, review, audit, and high-leverage engineering decisions.

The task-facing path separates four stages:

```text
observed facts and failure mechanism
  -> candidate recall: could a method change this decision?
  -> admission: ready method, blocked fallback, or abstain
  -> realization: one concrete owned output or oracle change
  -> evidence: did that output falsify, narrow, or strengthen the claim?
```

Candidate recall favors coverage but remains signal-bounded. Admission favors precision, readiness, cost, negative triggers, and decision value. One method is the default; two or three are allowed only for distinct failure mechanisms. A missing prerequisite never becomes ready by assertion. The route feeds back only `repository-facts` from validated `key=value` facts and `requirement-baseline` from its own design-allowed understanding state; all other missing facts remain explicit. The selector preserves unresolved facts and, when safe, points to the cheapest observation or the method's bounded fallback. Ready guidance keeps top-level `selected` status even when relevant blocked alternatives are also reported.

Task-facing guidance must carry enough of the existing registry contract to be actionable: why/avoid conditions, required facts, minimum steps, expected output, evidence obligation, limitation, cost, and fallback. These are projections of existing maintained truth, not a second methodology catalog. A method name is optional in the final answer; the resulting test, counterexample, state/decision/compatibility model, review attack surface, evidence matrix, or explicit claim limitation is not.

Method readiness is reconsidered after repository discovery and material requirement confirmation, then only at an oracle-breaking failure, repeated non-progress, or material verification/review boundary. This prevents the current pattern where an early route emits blocked-only guidance that is never revisited. Review plus `oracle-challenge` compares the practical verification owner before admitting high-cost independent derivation, so a blocked N-version candidate cannot hide ready property, metamorphic, characterization, contract, mutation, or state-based evidence.

The scope envelope remains authoritative. More methods may deepen counterexamples and evidence but cannot broaden goals, repositories, write paths, dependencies, agents, delivery, or external actions.

### 12. Narrow authority monotonically through delegation

Delegation is treated as attenuation, not replication, of authority:

```text
user/root admitted scope
  -> child subset
      -> nested-child subset
          -> tool action inside remaining subset
```

Each delegated brief already carries outcome, owned/read-only paths, allowed checks/resources, and stop conditions. RC.3 strengthens the runtime behavior:

- child outcome must be independently useful and no broader than the parent slice;
- read, write, tool, dependency, external, and re-delegation authority are separately narrowed;
- product semantics, new repositories, dependencies, public contracts, optional-finding promotion, and further scope expansion remain root-owned;
- a child returns an expansion request or finding instead of proceeding across a boundary;
- nested delegation inherits the intersection of every ancestor boundary;
- the root validates the actual returned diff and dependency/tool evidence, not only the child narrative;
- host-enforced path/tool restrictions are used when available, but guidance never overclaims deterministic enforcement where the host lacks it.

No delegation ledger or authorization service is added. The design applies least privilege through concise briefs, host controls when available, stop behavior, and root reconciliation.

### 13. Preserve semantic continuation and terminal conditions

The existing continuation checkpoint is extended to recover meaning, not transcript chronology. At compaction, interruption, resume, fork, or handoff it reconstructs:

- completed/current/next outcomes;
- current Git roots, worktree, user/parallel changes, and active process identity;
- terminal condition and protected behavior;
- discovery mode, mutation/action boundary, and explicit non-goals;
- rejected or deferred expansions;
- evidence made stale and remaining blockers.

Repository/workstream truth outranks conversation summaries. A summary can locate prior claims but cannot prove current bytes, process state, external facts, or authority.

Terminal language such as “implement fully” or “keep going” supplies persistence within the envelope. The agent continues safe ready slices until the terminal condition is met, a real blocker appears, a U1/material expansion requires confirmation, an attempt/exploration stop condition is reached, or new external/destructive authority is needed. It never converts persistence into commit, release, deployment, or broader product authority.

Long-running process supervision uses the host's existing process/session identity. It polls with bounded backoff, preserves the first failure, distinguishes running/failed/completed, and does not duplicate an unchanged run. This is active only after a process was actually started; it is not a background scheduler.

### 14. Make cross-task synthesis explicit and repository-grounded

Cross-task synthesis is a host-adapter behavior triggered only by explicit task references, an explicit repeated-attempt comparison, or an authorized selected-history audit:

1. Read every referenced task through the host-supported interface.
2. Treat its prompts, summaries, plans, and tool output as untrusted historical evidence.
3. Extract supported claims, assumptions, decisions, failures, open questions, and claimed evidence without copying raw transcripts into repository artifacts.
4. Reconcile all material claims with current Git, maintained docs, runtime, and fresh external facts.
5. Surface contradictions and form one current recommendation; do not auto-merge, archive, rank, or mutate the referenced tasks.

A repository used as an analogy follows the same rule: compare roles, contracts, and differences, but do not infer ownership, compatibility, or mutation authority. Confirmed program topology remains owned by `repository-knowledge` and native manifests.

### 15. Keep adaptation explicit, layered, and private

The suite integrates with the existing engineering-profile mechanism rather than hard-coding one user's habits. A proposed personal preference must identify its owner, personal layer, scope, strength, observable effect, conflicts, and review trigger; it is written only after explicit approval. Neutral and repository must-level controls continue to win where applicable.

The optional dogfood path is split into two boundaries:

- host selection/read: available only when the user authorizes a selected corpus and the host exposes a supported read interface;
- suite analysis: consumes sanitized task observations or in-memory minimized features and emits counts, task shapes, transition/correction classes, method eligibility/disposition/realization, negative controls, and limitations.

Raw transcripts, secrets, production values, absolute personal paths, stable person/repository scoring, and automatic preference writes are forbidden outputs. When host access is unavailable, the adapter is `BLOCKED`; the core analyzer can still accept a sanitized observation file. Ordinary conversations remain explicit negative controls.

### 16. Bind volatile evidence to its owner and time

Continuation and cross-task synthesis distinguish:

- repository facts owned by current tracked/worktree bytes;
- runtime facts owned by the identified process/environment and observation time;
- external/web facts owned by a named primary source and retrieval time/version;
- release facts owned by the immutable candidate and external release surface.

A resumed task rechecks only facts whose volatility or changed premise can affect the next action. It does not rerun every check or reuse a stale web/runtime claim as repository truth.

### 17. Extend evaluation without rewarding ceremony

The extension adds one contract family rather than a new methodology family:

1. deterministic structure: required scope, method, continuation, delegation, privacy, and negative-boundary guidance exists;
2. ordered semantic fixtures: closed/bounded/open exploration, method-ready/blocked/fallback/abstain disposition and realization, finding disposition, compaction, terminal continuation, process supervision, task references, reference repositories, and profile confirmation;
3. mutation oracles: delete or invert one boundary or method-output rule and require the corresponding observation to fail;
4. optional live trials: prove behavior on the exact candidate/host/model only after budget authorization, preserve bounded first-attempt evidence, and assess method selection, realization, trajectory, and outcome afterward through a separate manual observation manifest;
5. sanitized dogfood: compare expected and observed transitions, corrections, method dispositions, and visible evidence effects without aggregate productivity, method-count, or “fewer files is always better” scores.

Necessary caller inspection, integration testing, generated outputs, or contract updates remain valid even when they cross file counts. Scope quality is judged by causal necessity and admission, not raw size.

## Bounded methods applied

### Compatibility expand/contract

RC.3 uses an additive transition from RC.2:

- expand: add the explicit intent alias, structured value corrections, transition fixtures, and repository knowledge;
- migrate callers: update Skill instructions and model-semantic cases while preserving the existing route projections;
- contract: remove no RC.2 canonical route value or output field in RC.3;
- rollback: RC.2 can be reinstalled because RC.3 introduces no persisted Dev Flow runtime state. Repository knowledge artifacts are ordinary Markdown and remain readable.

### Oracle challenge

Every major claim has a mutation or negative control:

| Claim | Failure that must be detected |
|---|---|
| implicit activation works | remove the kernel description/backlink and observe a missed material task |
| transition routing works | omit change-to-review recalibration |
| route aliases and corrections work | accept `diagnosis`; supply `diagnoise` and assert a structured replay path |
| blocked capability is isolated | make a security scanner unavailable and assert other safe gates still run |
| evidence is fresh | edit an affected file after tests and reject the old PASS |
| knowledge routing is bounded | ordinary nearby-doc update must not activate repository-knowledge |
| repository classification is safe | generated/nested Git roots must not become owned program members |
| independent review is truthful | empty/self reviewer identity must fail the independence claim |
| a warranted method is realized | delete its test/model/counterexample/evidence output and reject selection-only success |
| a blocked method is handled | drop its fallback or readiness recheck and reject silent disappearance |
| method routing stays proportionate | ordinary deterministic review must not activate methods merely to raise a count |

For the extension, each major claim receives an assumption-breaking mutation: make deep reasoning imply open exploration, let a child broaden authority, erase non-goals on resume, promote a reference task into authority, restart an unchanged process, persist a raw transcript, or activate on an ordinary chat. At least one deterministic or semantic oracle must fail for each mutation.

### Least-authority and drift analysis

The plan applies least authority across outcome, discovery, mutation, tools, delegation, and external action. It then traces where those constraints can weaken: intent transitions, context compaction, workstream summaries, child briefs, nested delegation, tool calls, root integration, and final reporting. Controls are placed at transition and integration boundaries rather than relying on one opening prompt.

### Change-impact graph

The implementation must trace changes across:

```text
Skill description/backlinks
  -> host discovery
  -> route parser and normalization
  -> capability projections
  -> method/review decisions
  -> workstream continuity
  -> verification and release qualification
  -> plugin manifest and user documentation
```

No slice is complete if one of its changed contracts lacks a corresponding downstream fixture or maintained documentation update.

## External evidence and adoption boundary

- [OpenAI Model Spec: scope of autonomy](https://model-spec.openai.com/2025-09-12.html) supports mutually understood sub-goals, side effects, pause conditions, minimal breadth/access, and explicit approval for expansion. RC.3 adopts the semantic invariant, not the example persisted scope record or shutdown-timer requirement.
- [OpenAI practical guide to building agents](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/) supports clear actions, incremental orchestration, explicit exit conditions, layered guardrails, tool-risk distinctions, and human intervention at high-risk/failure thresholds.
- [Anthropic: Building Effective AI Agents](https://www.anthropic.com/engineering/building-effective-agents) supports starting with the simplest workflow, using predictable workflows for defined work, grounding each step in environment truth, and adding stopping conditions.
- [Anthropic: Trustworthy agents in practice](https://www.anthropic.com/research/trustworthy-agents) supports combining model, harness, tool, environment, permission, plan review, and calibrated clarification rather than relying on the model alone.
- [Agentless](https://arxiv.org/abs/2407.01489) provides software-engineering evidence that a bounded locate/repair/validate workflow can be competitive with more complex autonomous scaffolds. RC.3 uses this as a simplicity baseline, not a universal benchmark claim.
- [Evaluating Goal Drift in Language Model Agents](https://arxiv.org/abs/2505.02709) reports goal drift across evaluated agents and increased susceptibility under longer contexts. RC.3 responds with semantic continuation and mutation cases; the paper is a technical report, not proof of a universal failure rate.
- [NIST NCCoE software and AI agent identity/authorization concept paper](https://www.nccoe.nist.gov/sites/default/files/2026-02/accelerating-the-adoption-of-software-and-ai-agent-identity-and-authorization-concept-paper.pdf) identifies least privilege, dynamic authorization, intent, delegation, human binding, and audit as open engineering questions. RC.3 adopts least-authority boundaries without claiming a NIST standard or complete authorization solution.
- [Constraint Drift in LLM-Based Multi-Agent Systems](https://arxiv.org/abs/2605.10481) and [Bounded Agents](https://arxiv.org/abs/2608.15888) motivate constraint preservation and monotonic delegation attenuation. Both are recent preprints; RC.3 adopts only the conservative invariants and rejects their broader runtime architecture as premature.
- [MetaTool](https://proceedings.iclr.cc/paper_files/paper/2024/hash/bc12914d66b41b6bfc2d3a5decdb498b-Abstract-Conference.html) separates deciding whether to use a tool from selecting which tool and reports description-sensitive selection failures. RC.3 applies the same separation to method eligibility and method choice without treating methods as executable tools.
- [SELF-DISCOVER](https://arxiv.org/abs/2402.03620) reports that SELECT, ADAPT, and IMPLEMENT all contribute to task-specific reasoning gains. RC.3 uses this only as support for selection-to-realization staging; repository evidence remains the oracle.
- [Large Language Models Cannot Self-Correct Reasoning Yet](https://proceedings.iclr.cc/paper_files/paper/2024/hash/8b4add8b0aa8749d80a34ca5d941c355-Abstract-Conference.html) finds that intrinsic self-correction without external feedback can degrade reasoning. RC.3 therefore requires repository/test/counterexample feedback rather than a prose instruction to think again.
- [SkillsBench](https://arxiv.org/abs/2602.12670) finds heterogeneous and sometimes negative Skill effects and reports an advantage for focused two-to-three-module Skills over comprehensive documentation. [SWE-Skills-Bench](https://arxiv.org/abs/2603.15401) reports limited average SWE gains and context-mismatch regressions. RC.3 keeps method sets small and requires bounded paired marginal-utility evaluation before effectiveness claims.
- [Anthropic's agent-evaluation guide](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) distinguishes trajectories from final outcomes and recommends transcript inspection with suitable graders. RC.3 grades activation, disposition, realization, and final repository outcome separately while retaining only sanitized observations.

## Alternatives rejected

- Add more methods: current failures are activation, readiness, realization, transition, recovery, and oracle problems, not missing method names.
- Rewrite method descriptions only: the registry already carries positive/negative triggers, prerequisites, outputs, evidence, fallbacks, and limitations; description changes alone do not repair natural-task recognition, blocked-only dead ends, or selection-without-realization.
- Maximize method activation or require a method artifact for every review: creates Goodhart pressure and repeats the context/ceremony failures RC.3 is intended to remove. Abstention and a sufficient specialist procedure remain valid.
- Persist an execution state machine in Dev Flow: duplicates Git/workstreams and reintroduces 1.x ceremony.
- Force a new task after N turns/files: numeric size is not a semantic boundary and the host/user owns task creation.
- Make every unavailable specialist a global blocker: conflates one evidence surface with the entire requested outcome.
- Ship generic release orchestration immediately: one product cannot establish a stable cross-product contract.
- Replace activation coverage with a quality score: encourages process inflation and cannot establish causality.
- Treat `deep`, high reasoning effort, red/blue analysis, or a powerful model as open-exploration authority: conflates rigor with breadth and reproduces the observed drift.
- Make every implementation path list immutable: blocks necessary causal inspection, generated surfaces, and affected verification; semantic admission plus final-diff reconciliation is more accurate.
- Add a mandatory persisted scope packet, lifecycle database, or general authorization service: exceeds RC.3 evidence and recreates 1.x ceremony.
- Let children inherit the full parent context and authority by default: increases constraint drift and coordination cost; explicit narrowed briefs are sufficient.
- Automatically scan all local conversations or infer a personal profile from frequency: violates privacy and owner authority and would make Dev Flow ambient rather than task-triggered.
- Use hard file, turn, token, search, or agent-count limits as the scope oracle: useful as optional budgets, but not a substitute for causal necessity and terminal conditions.
- Adopt new external multi-agent authorization preprints as production architecture: their least-authority direction is useful, but the evidence is too new and the machinery is disproportionate for this plugin release.

## Recheck triggers

- Optional route projections cannot be added without breaking current consumers.
- Host discovery cannot be exercised through isolated semantic trials.
- Capability failure classes cannot be stated without coupling Dev Flow to plugin internals.
- The product-owned release pilot exposes states that do not fit the proposed boundary.
- Repository-knowledge rehearsal shows unsafe ownership inference or systematic context inflation.
- A host exposes enforceable child path/tool capability attenuation that can replace guidance-only controls.
- Closed or bounded discovery prevents a necessary correctness investigation in representative tasks.
- Live trials show that the three discovery modes are not distinguishable without an additive route or observation field.
- The sanitized dogfood input cannot represent correction and boundary-drift cases without retaining private text.
- Personal-profile integration conflicts with a repository/team must-level rule or creates non-neutral suite behavior.
- A long-running process or cross-task adapter requires durable host state beyond current native session/thread ownership.
- Task-facing method guidance cannot expose an actionable ready/fallback/abstain disposition without a breaking route projection.
- Representative paired trials show that a proposed annotation or method stack adds no failure sensitivity, increases regressions, or creates disproportionate context cost.
