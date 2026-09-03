# RC.7 professional-Skill discovery audit

> Status: pre-implementation source/research baseline; its discovery repairs are implemented in the RC.7 source-candidate worktree.

## Question

RC.7 can deepen a professional Skill only if the model can discover it at the moment its owner problem appears. This audit therefore checks the complete path rather than whether the Skill merely exists:

```text
observable task/repository signal
  -> current-turn capability is visible
  -> main flow or repository discovery recognizes an owner problem
  -> an optional diagnostic route can express the owner
  -> the smallest professional Skill is loaded
  -> its result changes a decision, artifact, evidence or limitation
  -> positive and negative behavior tests detect routing drift
```

`repository-knowledge` is the primary probe because RC.7 relies on it to establish documentation continuity without turning every documentation edit into a knowledge-system project.

## Current findings

| Layer | Current evidence | Verdict |
|---|---|---|
| Host/plugin availability | The plugin exposes `repository-knowledge`; its Skill and agent metadata are packaged and visible in the effective catalog. | PASS for availability only |
| Direct semantic discovery | The frontmatter and capability contract clearly match an explicit request to audit, plan, map, bootstrap or check a repository knowledge system. | PASS for explicit knowledge work |
| Implicit lifecycle discovery | The Skill description says “not routine docs”; the main Skill says knowledge-system maintenance is explicit-only. Neither names missing canonical owners, chat-only handoff, conflicting truth or a new project without a documentation entry as positive triggers. | FAIL for the RC.7 lifecycle goal |
| Repository-context handoff | `repo-context` owns bounded specialist discovery and its contract can hand off to `repository-knowledge`, but the procedure gives no concrete knowledge-topology signals or required result for that handoff. | PARTIAL, model-dependent |
| Public deterministic route | `route-task --need repository-knowledge` is invalid because neither `knowledge` nor the Skill name is in the need contract. | FAIL |
| Knowledge-impact route | `--knowledge-impact current-truth` records a disposition but does not add `repository-knowledge`; the same is true for managed cross-module work. | PASS as a non-activation disposition; FAIL as discovery evidence |
| Technical specialist registry | Current effective-Skill matching covers technology capabilities selected from repository facts. `repository-knowledge` has no equivalent selector path. | NOT COVERED |
| Deterministic evaluation | Routing cases cover requirements, architecture, dependencies, debugging, test systems, verification, review and delivery. None requires or forbids `repository-knowledge`. | FAIL |
| Semantic evaluation | Existing natural-language cases cover explicit/implicit Dev Flow, advanced engineering and simple negative boundaries. None tests an implicit knowledge-topology problem. | FAIL |
| Skill-function tests | `test_repository_knowledge.py` exercises the scanner/checker after invocation. It cannot prove that normal development discovers the Skill. | PASS after activation only |
| Negative boundary | Both the Skill and capability contract exclude an ordinary task that only updates one already-owned nearby document. | PASS and must be retained |

The central defect is therefore a **recognition and activation gap**, not a missing documentation capability. RC.6 can use `repository-knowledge` well after an explicit invocation, but RC.7 cannot yet rely on it being found when a material task first reveals that the repository lacks a usable knowledge path.

## Suite-wide discovery posture

The same failure class applies to every conditionally activated owner: a correct route after supplied classification does not prove that the classification will happen. The severity differs by owner.

| Professional owner | Deterministic expression | Current semantic-catalog posture | Primary discovery risk | RC.7 disposition |
|---|---|---|---|---|
| `repo-context` | Default owner on public routes; direct narrow-read trigger | Negative non-repository coverage; no owner-specific positive assertion | Low under-activation risk inside Dev Flow, but its specialist recommendations remain model-dependent | Keep the fact spine; test observed specialist handoffs rather than generic recommendations |
| `requirements-design` | Intent/class/need/ambiguity/UI/public-contract signals | Strong positive and negative coverage | Hidden semantic change can still be mislabeled structural or established | Retain compact semantic check plus U1/U3/U4 boundaries |
| `product-ux-discovery` | UI impact and UI unknowns | No direct semantic activation case | Workflow, state or accessibility impact can be treated as ordinary UI implementation | Add rendered/repository-evidence positives and small-visual-fix negatives |
| `architecture-decisions` | Need, task type and architecture/concurrency/compatibility/resource risks | Multiple implicit cross-boundary cases | A material boundary can emerge after the initial route | Add a mid-task rebind oracle |
| `dependency-decisions` | Need, dependency risk and dependency-change type | No direct semantic activation case | A library, service or tool can enter as an unnoticed implementation detail | Add implicit-new-dependency and exact-routine-update boundaries |
| `systematic-debugging` | Diagnose intent, diagnosis need, bug type and diagnosis risks | Strong positive coverage | “Fix” phrasing can invite a symptom patch instead of diagnosis | Preserve causal-effect semantic cases |
| `verification` | Persistent mutation, review intent or explicit need | Broad positive coverage | Frequent activation can still degrade into shallow “run tests” behavior | Evaluate changed oracle, fresh evidence and negative controls |
| `test-system-engineering` | Explicit need; weak-test risk also requires the effective Skill | No natural false-green/harness case | Zero discovery, inert assertions, fixture pollution or misleading runner success can be mistaken for product evidence | High-priority implicit positives plus ordinary-feature-test negative |
| `change-review` | Review intent/need/material exposure/independent-review conditions | Outcome/downgrade concepts appear, but no direct owner case | Final review can be skipped, while generic review can over-activate on routine work | Test consequential finding, stopping and final-diff rebind |
| `delivery-readiness` | Delivery intent/need and release/rollback paths | No direct semantic activation case | Commit, push or release can be conflated with implementation completion | Add exact-action positives and no-authority negatives |
| `repository-knowledge` | No public need; knowledge impact is disposition only | No activation case | Missing entry, owner or handoff is not recognized | First-class discovery repair described below |
| `company-data-security` | No public owner route; separate Hooks and native tests exist | No Skill-level semantic activation case | Hook blocking can occur without least-data planning; broad matching can also over-activate on public work | High-priority C2-C4 positives and public-only negatives; separate Hook from Skill evidence |
| `manage-engineering-profiles` | Explicit profile-operation flag | No semantic activation case | Contract is explicit-only, but metadata does not disable implicit invocation | Align metadata; test explicit management versus consume-only work |
| `dev-flow-maintainer` | Explicit suite-maintenance flag | No semantic case; implicit invocation is explicitly disabled | Low; explicit-only behavior is coherent | Retain; add smoke only when metadata changes |
| External language/framework specialists | Effective current-turn Skill plus repository-fact selectors and qualified fallback | Plugin-prefix/fallback deterministic cases only | Facts or current-turn capability identity can be missed | Test fact discovery, visibility, collision and fallback; never scan/install for recall |

The current relative posture is:

- **stronger but not universally proven:** `requirements-design`, `systematic-debugging`, `architecture-decisions`, `verification`, and the `repo-context` spine;
- **deterministically expressible but semantically under-tested:** `product-ux-discovery`, `dependency-decisions`, `test-system-engineering`, `change-review`, and `delivery-readiness`;
- **material discovery/contract gap:** `repository-knowledge` and `company-data-security`;
- **explicit-only metadata consistency issue:** `manage-engineering-profiles`;
- **coherently explicit-only:** `dev-flow-maintainer`.

Catalog entries are test designs, not fresh live-model PASS evidence. RC.6 did not run a new all-owner semantic campaign for this audit, so even the stronger group is described as lower risk rather than proven reliable.

RC.7 must evaluate two distinct questions for every professional owner: **can the owner decision be expressed after classification**, and **can the model recognize the owner problem from natural task and repository evidence before a flag exists**. Current tests are much stronger on the first question than the second.

## Industry practice and emerging evidence

Current platform practice converges on progressive disclosure, but it does not make discovery automatic:

- [OpenAI Docs: Build skills](https://developers.openai.com/codex/build-skills) says Codex initially sees Skill names and descriptions, then loads the full `SKILL.md` only when selected. Implicit selection is driven by the description; descriptions should front-load the use case and trigger words, state boundaries, and be tested against realistic prompts. The initial Skill list also has a context cap, so descriptions can be shortened and, at sufficient scale, entries can be omitted.
- [OpenAI Docs: tool search](https://developers.openai.com/api/docs/guides/tools-tool-search) applies the same principle to large tool catalogs: expose clear high-level namespaces, dynamically retrieve the relevant subset, and avoid loading every definition up front. This supports a small discovery surface, not a permanently expanded main prompt.
- [Anthropic's Agent Skills engineering note](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) likewise preloads metadata, loads Skill instructions when relevant and retrieves supporting references on demand. Its [context-engineering guidance](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) emphasizes small, high-signal context and minimally overlapping tools with clear contracts.
- The [Agent Skills description guide](https://agentskills.io/skill-creation/optimizing-descriptions) treats the description as the primary trigger surface. It recommends intent-oriented `Use when...` language, implicit positive prompts, adjacent near-miss negatives, varied phrasing, repeated trials and held-out cases so description tuning does not become keyword memorization.

Recent research sharpens the limits of those practices. These papers are useful design evidence, not settled platform guarantees:

| Evidence | Finding | RC.7 implication |
|---|---|---|
| [SkillRet, 2026 preprint](https://arxiv.org/abs/2605.05726) | In a 17,810-Skill corpus, generic retrieval underperformed a task-trained retriever; long noisy requests often contained only a small Skill-relevant signal. | Do not assume ordinary semantic similarity is enough. Preserve implicit, embedded positives and owner-specific signals in evaluation. |
| [SkillRouter, 2026 preprint](https://arxiv.org/abs/2603.22455) | In its roughly 80K-Skill experiment, metadata-only routing lost substantial accuracy versus body-aware retrieval; most measured attention fell on Skill bodies. The expert-query set was small. | Keep richer body-derived discovery evidence available for offline indexing/reranking if scale demands it, but do not preload every body into normal context. |
| [Skill Retrieval Augmentation, 2026](https://sr-agents.github.io/) | Retrieval, incorporation and application are separate failure stages; stronger retrieval did not reliably imply stronger task answers. | Measure candidate recall, admission/application and realized outcome separately. A transcript containing the Skill name is not success. |
| [Skills in the Wild, 2026 preprint](https://arxiv.org/abs/2604.04323) | Reported gains became fragile under realistic retrieval and noisy candidate pools; query-specific refinement recovered some task/model-specific performance. | Evaluate the effective catalog and realistic long tasks, not only a clean one-Skill prompt. Allow bounded re-evaluation when new evidence changes the problem. |
| [ToolRet, 2025](https://arxiv.org/abs/2503.01763) and [RAG-MCP, 2025](https://arxiv.org/abs/2505.03275) | Large capability catalogs expose a specialized retrieval problem; retrieve-before-load can cut prompt cost and improve selection, but benchmark selection remains imperfect. | Add a retriever only when measured catalog scale/omission warrants it; it would remain a candidate generator, never the decision authority. |
| [Skills security analysis, 2026 preprint](https://arxiv.org/abs/2605.11418) | Skill metadata and instructions can manipulate retrieval and selection; metadata is operational input, not harmless documentation. | Candidate discovery never grants trust, installation, authority or external-action permission. Provenance and current-turn exposure are admission conditions. |

The combined lesson is not “write longer descriptions” or “install a vector database.” It is: keep the always-visible surface small and discriminative, load specialist knowledge progressively, and test the entire path from noisy evidence to a changed engineering result.

## RC.7 solution: evidence-triggered owner discovery

RC.7 adopts an **evidence-triggered owner discovery** design. It is a behavior contract across the existing main Skill, `repo-context`, professional metadata/contracts and evaluations; it is not a new orchestration service or another lifecycle stage.

```text
small always-visible discovery spine
             |
 user intent + repository facts + new evidence
             v
      candidate owner (or none)
             |
    scope / value / trust admission
             v
      load one professional Skill
             |
 changed decision, artifact, oracle or limitation
             v
         return to main task
```

### Two disclosure planes

1. **Always-visible discovery spine.** The thin main `dev-flow` entry and `repo-context` retain only compact observable owner problems: semantic uncertainty, user-flow impact, material boundary choice, new capability/dependency, causal uncertainty, untrusted test evidence, consequential final-diff risk, unresolved knowledge ownership, sensitive-data exposure and a requested delivery action. This is a semantic safety net, not a list to execute.
2. **On-demand professional plane.** The host catalog exposes concise Skill metadata. Once an owner is admitted, its full Skill and only the necessary references supply the craft. The main entry does not copy their procedures.

With the current 15 built-in Skills, RC.7 should not add embedding infrastructure or a second central router. Host metadata plus the discovery spine is the least complex credible design. A richer retrieve-and-rerank layer becomes a separate future decision only if effective-catalog truncation/omission is observed or held-out owner recall degrades as the catalog grows. If introduced, it indexes trusted body-derived trigger summaries offline and returns candidates; it never injects all bodies or makes the admission decision.

### Descriptions and contracts

Every implicitly discoverable professional Skill must make the standard host surface work well:

- front-load `Use when...` with the user goal or observable problem, including cases where the user never names the domain;
- include one adjacent exclusion that protects ordinary work from a plausible false positive;
- describe what decision/evidence the Skill changes, not its internal method inventory;
- keep `SKILL.md`, agent metadata and capability contracts semantically aligned;
- set explicit-only owners consistently to the host-supported `allow_implicit_invocation: false` rather than relying on prose alone;
- retain richer examples, repository signals and collision cases in the suite-owned discovery contract and eval catalog, not in the normal static path.

The description is the host trigger capsule. The contract/eval corpus is the maintainable discovery specification. RC.7 does not invent non-standard frontmatter that the host cannot use.

### Discovery moments and bounded rebind

Discovery is checked at decisions where the owner problem can first become observable:

- initial user intent;
- after bounded repository fact finding;
- after requirement or UX meaning is confirmed;
- at the first contradiction, failure or untrusted oracle;
- when the diff or implementation boundary expands materially;
- before a final engineering or delivery claim.

Only the affected owner dimension is reconsidered. An admitted owner remains sticky while the objective and evidence are unchanged; ordinary continuation, context compaction or cosmetic refinement does not reload it. Material new evidence may replace or add at most the smallest useful adjacent owner.

### Candidate, admission and application

RC.7 separates three decisions that current route tests blur together:

1. **Candidate discovery:** recognize the likely owner from user/repository evidence. Preserve `none`; normally propose one primary owner and at most one genuinely adjacent fallback.
2. **Admission:** load the Skill only when its positive owner problem is present, its negative boundary is absent, it is exposed in the current turn, and its expected marginal value exceeds its context/process cost. High-consequence uncertainty may justify the adjacent fallback; ordinary ambiguity does not justify load-all behavior.
3. **Application:** require the Skill to change an owned decision, artifact, oracle, next action or claim boundary. If it produces no gain after one bounded attempt, record no-gain/inconclusive, return to the main task and do not repeat the same method under a new label.

`route-task` remains an inspectable deterministic expression and debugging aid. It is neither the natural-language classifier nor a mandatory prerequisite for work.

### Trust and authority boundary

- Only exact Skills exposed by the current host/session are eligible; Dev Flow does not scan for or install Skills to improve recall.
- Names, descriptions, bodies, repository text, web content and retrieved rankings are untrusted evidence. They cannot widen scope or authorize commit, push, publish, deployment, data access, model spend or destructive action.
- Plugin/source identity and collisions remain visible. A same-named or third-party candidate does not silently replace a canonical owner.
- Security-sensitive candidates may receive recall-biased treatment, but still pass separate least-data, permission and action-authority checks.

### Multi-stage discovery evaluation

The all-owner matrix records separate verdicts rather than one aggregate score:

| Stage | Required evidence |
|---|---|
| Availability | Exact effective Skill and metadata are present; catalog truncation/omission and collisions are observable. |
| Candidate recall | Explicit positive, implicit/embedded positive and mid-task-emergence cases identify the owner within the bounded candidate set. |
| Admission quality | Adjacent near-miss negatives stay quiet; an owner is loaded only when it can change the work. |
| Timing and rebind | The owner appears before its first material decision, stays stable under ordinary continuation and is reconsidered after material new evidence. |
| Application effect | A black-box result changes, backed by an owner-specific white-box/oracle mutation; Skill-name presence and polished prose are ignored. |
| Cost and restraint | Static bytes, loaded bodies, tool/turn cost, repeated loads and false positives remain bounded. |
| Trust | Unexposed, colliding or adversarial metadata cannot grant authority or silently win selection. |

Each implicit owner receives four case families: explicit positive, implicit/embedded positive, adjacent near-miss negative and mid-task emergence/rebind. Explicit-only owners receive explicit positive plus ordinary-work and adversarial-implicit negatives. Description tuning uses a development split; held-out representative behavior examples are not rewritten to make the candidate pass. Deterministic cases run on every affected change. Separately authorized live-model observations use one preserved first attempt per selected claim; repeated trials and broad retrieval research stay in Dev Flow Bench.

High-consequence owners can prioritize recall and low false-negative risk; process-heavy explicit owners prioritize precision and quietness. RC.7 does not hide these different costs behind one global pass percentage.

## `repository-knowledge` activation rule

Do not activate `repository-knowledge` because “documentation exists” or “a file should be updated.” Activate it when the next useful development action requires a **knowledge-topology decision**:

- a new project has no discoverable documentation or equivalent project-native entry;
- a material or managed change would leave requirements, design, test strategy or acceptance available only in chat;
- a durable fact has no clear canonical owner, or multiple maintained documents claim ownership;
- current truth is stale, contradictory, superseded but still active, or unreachable from the normal repository entrypoint;
- a project-level test system, architecture boundary or runbook is being established and its long-term location/read path is unresolved;
- the user explicitly requests knowledge audit, planning, mapping, bootstrap, repair or validation.

Keep the full Skill quiet when:

- one nearby canonical document needs an ordinary affected update;
- a typo, formatting fix or generated document refresh changes no knowledge topology;
- manifests, schemas, source, tests or CI already own the exact fact and only a link/reference needs maintenance;
- the task is release execution rather than knowledge-system work.

## `repository-knowledge` repair surfaces

RC.7 should make the activation rule redundant across the minimum necessary surfaces, not depend on one CLI:

1. **Skill metadata:** describe observable knowledge-topology problems in `SKILL.md` and `agents/openai.yaml`, while retaining the ordinary-document negative trigger.
2. **Thin main flow:** at initial repository discovery and before close, ask only whether durable results have a discoverable canonical owner and whether the next position can proceed without chat-only state. A “no” routes to `repository-knowledge`; a clear existing owner is updated directly.
3. **`repo-context`:** return `repository-knowledge` as a useful owner when it observes a missing entry, owner ambiguity, duplicate/stale truth or an unresolved cross-stage handoff. It must report the observed signal, not a generic recommendation.
4. **Diagnostic route:** add canonical `--need knowledge` and alias `--need repository-knowledge`. This is an inspectable/testable expression of a decision, not a mandatory call for ordinary work. `--knowledge-impact` remains a disposition and must not by itself force the Skill.
5. **Capability contract:** replace `explicit-repository-knowledge-operation` as the only orchestrated condition with explicit operation plus observed topology/handoff failure.
6. **Return contract:** the professional Skill returns the chosen canonical owner, readers/next-read path, update/freshness trigger and any unresolved owner decision, then yields to the main task. It does not take over implementation.

## Acceptance and sensitivity

Discovery is not proven by seeing the Skill name in a transcript. The positive oracle must show that the Skill changed the repository knowledge path and that a seeded successor can find and use the result.

Required cases:

- explicit knowledge-system audit selects `repository-knowledge`;
- new material project without a documentation entry selects it and establishes the smallest useful entry/owner path;
- existing project with contradictory owners selects it and resolves or reports the owner conflict;
- a material task with an established documentation owner updates that owner directly without loading the full Skill;
- one-line README/doc correction stays direct and quiet;
- removing the main-flow trigger, the `repo-context` handoff, or the route alias makes the corresponding case fail;
- a later seeded task fails when the produced index/owner link is removed or stale truth is reactivated.

The same audit pattern is mandatory for every professional Skill: availability, observable positive trigger, negative trigger, main/repository recognition, optional deterministic expression, realized outcome, and a mutation-sensitive behavior case. `repository-knowledge` remains the first required repair because documentation continuity depends on it, but it is not the scope boundary.

Maintain a table-driven discovery matrix for all professional owners. Every row needs at least one positive and one adjacent negative deterministic case. Owners inferred from natural language or repository evidence also need a bounded semantic case; explicit-only owners instead need a semantic negative proving ordinary work stays quiet. The cross-cutting `RC7-DISCOVER-015` release smoke does not replace this full matrix.

## Evidence boundary

This audit inspected all RC.6 built-in Skill descriptions and bodies, agent metadata, capability contracts, public route implementation, deterministic cases, semantic catalog and affected unit-test ownership. It also executed the public route against explicit knowledge need and knowledge-impact inputs and compared the design with the cited platform guidance and recent research. External benchmark results are not Dev Flow runtime evidence. The audit did not run a live-model semantic campaign, modify runtime files or prove population-level activation reliability.
