# Dev Flow 2.0 RC.8 implementation plan

> Status: implemented in the source-candidate worktree for `2.0.0-rc.8`; committed locally, not published. `governance/product-state.json` remains the authority for current product and delivery state. [Progress and audit disposition](progress.md) records what has actually run.

RC.8 deepens the existing technology-neutral Dev Flow lifecycle so an agent reaches the user's observable outcome, retains the target through steering and context changes, and reports the right environment evidence. It also migrates the active GPT-5.6 child-agent routing to GPT-6 without treating model size as a proxy for risk. This is a bounded evolution of the existing owners, not a new workflow, skill catalog, Bench project, or universal project runner.

## Evidence and decision boundary

- **Official guidance.** [OpenAI model selection](https://developers.openai.com/api/docs/guides/model-selection) places clear, constrained, multi-step work within Luna's range; Sol covers everyday coding and judgment; Astra covers ambitious broad-context and especially demanding analysis. It explicitly recommends experimenting with the actual workflow. [GPT-6 guidance](https://developers.openai.com/api/docs/guides/latest-model) says Astra can pause for clarification, is more sensitive to Skills/`AGENTS.md`, and may over-test small changes. [OpenAI's Codex prompt/skill guidance](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) recommends shorter, conditional instructions, progressive disclosure, explicit completion, and a stated exploration boundary when further exploration is wanted. These are starting points, not a measured Dev Flow outcome.
- **Independent signal.** [Artificial Analysis, 2026-09-22](https://artificialanalysis.ai/articles/gpt-6-sol-and-luna-push-the-cost-efficiency-frontier) reports at max effort in its Codex harness Sol's Coding Agent Index at 57 versus 55 for 5.6 Sol, but Luna at 41 versus 43 for 5.6 Luna. Both are cheaper per evaluated task and show mixed gains/regressions across tests; some professional deliverables omit required elements. In a [single controlled hands-on build task](https://www.datacamp.com/blog/gpt-6-sol-and-luna), all compared models handled ordinary cases; a deliberately invalid input separated their failure behavior, with GPT-6 Sol giving the clearest stop and GPT-6 Luna an ambiguous result. That one task is a useful oracle-design example, not a general tier ranking. Luna is more *economically usable for fitting tasks*, not proven universally smarter or safer. Neither source establishes performance in this repository or at other effort levels.
- **User observation and local task audit.** The user's impression that GPT-6 is more purposeful, accurate, and less spontaneously divergent is a useful hypothesis. Recent GPT-6 task samples showed focused implementation but also completion/oracle gaps: a green emulator result could be produced by background rather than the intended app traffic, and build/install evidence did not establish live behavior. These are observed task-level failure modes, not a controlled GPT-5.6/GPT-6 causal comparison. The sampled tasks contained no local GPT-6 Luna work; Luna allocation below is a proposed policy requiring real-work validation.
- **Decision.** Optimize for *bounded, decision-relevant breadth*: when meaning or cause is uncertain, inspect plausible alternatives and a disconfirming case; when the target and oracle are closed, execute directly. Do not demand open-ended brainstorming or add checklists to every small task. Risk sets evidence depth and authority, while unresolved reasoning complexity sets the model tier.

## Model and task allocation

The default for an interactive, non-trivial root task is **GPT-6 Sol at medium effort**. This is a recommendation to the user or host, not a claim that `route-agent` can switch the active root model; an explicit user model choice takes precedence. Start Luna for a clearly bounded task when latency/cost matter; start Astra only when the compound judgment below is already visible. Increase effort within a tier before escalating tiers if the work stays semantically closed. De-escalate after uncertainty is resolved, and do not launch a fresh model merely to match a label. Availability and actual host effort support must be checked before dispatch; no silent GPT-5.6 fallback. Routing advice does not itself authorize model spend.

| Work shape | Preferred route | Boundary and evidence |
|---|---|---|
| Exact lookup, extraction, log filtering, mechanical edit | Luna low/medium | Known target and simple check; do not expand into investigation. |
| Confirmed bug or feature slice, clear brief, deterministic oracle, coordinated files | Luna high; xhigh when context or sequencing is large but constraints remain clear | Reviewer/stronger oracle may be needed for high consequence; risk alone does not force Astra. |
| Everyday coding, research synthesis, moderate ambiguity, ordinary diagnosis or design | Sol medium | Default when the next decision needs judgment, completeness, or exploration that Luna's closed brief cannot supply. |
| Competing causes, uncertain requirements, cross-component contract, careful review or high-consequence bounded work | Sol xhigh | Explicitly compare decision-changing alternatives and independently challenge the oracle. This is the normal escalation ceiling. |
| Deep unresolved causal/architectural reasoning plus interacting unknowns, consequential cross-boundary impact, or a documented failed Sol discrimination | Astra xhigh | Require a genuinely compound reasoning problem, not a single risk word. Define the unresolved question, useful exploration breadth, and stop condition; preserve authority boundaries and finish the authorized outcome. |
| Exceptional, separately acknowledged campaign | Astra max (`PX`) | Keep existing exceptional-budget treatment; never auto-select from a risk keyword. |

The table describes task *suitability*, not an IQ ranking. A closed FFI correction can be Luna or Sol with exact ABI and platform evidence. An open architectural trade-off with incompatible consumers may merit Astra. A security label, large repository, long context, or critical acceptance does not by itself prove Astra is needed; it requires stronger evidence and, where useful, an independent review. Give Luna a short explicit list of required outputs/edge cases so its focused response does not omit a deliverable. If a Luna attempt misses a required criterion or encounters genuine semantic uncertainty, rewrite the remaining question and move to Sol; if Sol's competing explanations remain unresolved after a discriminating check, consider Astra. Repeated retries with the same prompt are not escalation.

### Active routing change

Keep the existing `E/B/F` capability vocabulary and P0–P6/PX public profile IDs unless a focused compatibility test demonstrates that an additional profile is necessary. The intended profile mapping is P0 Luna low, P1 Luna medium, P2 Luna high, P3 Luna xhigh, P4 Sol medium, P5 Sol xhigh, P6 Astra xhigh, PX Astra max. In the current registry, `E/B/F` and upgrade rules conflate model capability with risk: `critical-engineering-risk` raises F for any `ffi`/`security` label, `frontier-judgment` raises F for any ambiguity, and `critical-acceptance` raises F for high-consequence acceptance. RC.8 must replace these unconditional promotions with task-relative, compound reasoning triggers and a separate evidence-depth decision. Inspect `_least_profile`'s capability/effort lattice before changing JSON: every valid signal combination must resolve to an available profile, and profile order must not unexpectedly promote a clear Luna task to Sol or Astra.

| Route counterexample | Expected child policy | Separate evidence decision |
|---|---|---|
| Closed, high-consequence FFI fix with known ABI and oracle | P2 Luna high (or P3 for large clear context) | Exact ABI/platform check and appropriate review; not automatic Astra. |
| Clear multi-file change with a verified brief | P2/P3 Luna | Confirm all specified outputs and a negative control; no mandatory broad ideation. |
| Ordinary ambiguous implementation | P4 Sol medium | Resolve the one semantic choice that changes behavior. |
| Conflicting causal evidence or disputed oracle | P5 Sol xhigh | Discriminating check, competing causes, and final outcome evidence. |
| Critical acceptance after semantics are settled | Existing task-relative P2–P5; not P6 solely from consequence | Stronger independent/environment oracle and explicit unrun boundary. |
| Deep, interacting, unresolved architecture/causality | P6 Astra xhigh | Bounded alternative sweep and exact completion target. |

Implement compound P6 eligibility explicitly (for example an all-of rule or a small classifier with negative controls), not as several independent `any_signal` promotions. Retain current risk tokens in the result for the `verification`/`delivery-readiness` owner; put assurance selection in those existing owners and their fixtures rather than inventing a parallel numeric assurance score. A requested manual higher profile remains possible within model-spend authority; an automatic lower result must never relax the actual oracle. If the current profile lattice forces a higher tier simply because an effort vector is absent, use a tested minimal profile/schema change rather than silently accepting that promotion.

`route-agent` only chooses a child profile; root model recommendation belongs in human-facing guidance, not a fake root-profile result. Preserve child scope/authority attenuation and no extra spawn-authorization gate. Update the active registry, route implementation/help, orchestration reference, plugin prompt/agent metadata, capability contracts, deterministic fixtures, and affected tests together. Historical GPT-5.6 examples may remain historical; active defaults and current-facing help may not. Unsupported/unavailable model or effort returns a visible capability limit and suggested in-family alternative or no dispatch; it must not invent a model alias.

## Implementation slices

### RC8-1 · Remove instruction debt and set focused exploration (P0)

Audit active `AGENTS.md`, main/professional Skills, orchestration and prompt surfaces for duplicate instructions, unconditional reading/testing, premature U1 confirmation or approval pauses, and rules that turn ordinary ambiguity into blocking. Retain true action-authority and high-consequence boundaries. Rewrite the main Skill as a compact intent → slice → native evidence → final reconciliation spine; move case-specific guidance to its existing owner. In requirements work, ask only surviving decision-changing questions and continue authorized work that does not depend on the answer. For uncertain diagnosis/design, require one bounded sweep of competing explanations or counterexamples; for closed tasks, do not force ideation. Explicit completion means final behavior plus the appropriate test/environment evidence, not first implementation or prose-only plan.

**Owners:** `dev-flow`, `requirements-design`, `systematic-debugging`, `repository-knowledge` and the specific over-constraining owner. **Acceptance:** small mechanical task stays short; a material uncertain task considers a disconfirming alternative; a U1 task still stops for a truly material user choice; an authorized task does not pause merely because a Skill or prior instruction sounds cautious; no authority boundary is weakened.

### RC8-2 · Migrate and calibrate the model router (P0)

Apply the allocation above to `agent-dispatch-profiles.json` and the minimal algorithm/schema changes it requires. Separate three inputs: (1) semantic/causal uncertainty, (2) breadth and working-context demand, (3) consequence and required verification. The first two select tier/effort; the third selects oracle, review, environment, and stop/recovery evidence. Ensure a risk signal can still increase review rigor even when the model tier remains Luna or Sol. Do not encode unsupported external model ratings as deterministic truth.

**Acceptance:** table-driven positive and negative route cases include exact lookup, clear multi-file change, closed high-risk FFI fix, open FFI contract, disputed causal diagnosis, routine and high-risk review, critical acceptance with settled semantics, unresolved architectural trade-off, model/effort unavailability, and PX. P0–P6/PX compatibility and no silent 5.6 references in active routes are checked. The availability case is a dispatch-time host check, not fabricated knowledge in the static registry. Record a small set of real-work Luna/Sol/Astra observations separately from deterministic routing validity; any paid live-model comparison is separately authorized and is `NOT RUN` until executed.

The user also authorized migration of the **development** paired-evaluator identity. Preserve its inventory/assembler/grader roles and effective efforts while moving their model to GPT-6, bind the actual local Codex backend version and artifact digest, and update its identity tests. Keep the frozen RC.7 acceptance evaluator configuration as historical truth; define a new RC.8 acceptance identity only in a coherent later candidate transition. Editing a configuration does not authorize or constitute a paid model trial.

### RC8-3 · Target continuity and terminal reconciliation (P0; prior direction 1)

On user steering, scope changes, or compaction, preserve confirmed target, current slice, last trusted oracle, protected paths, active resources, outstanding blockers, and environment gaps. Invalidate or reclassify stale plans, descendant results, and pre-change checks; unchanged continuation needs no re-routing ceremony. Before completion, compare user goal, current source/contract, final diff, final applicable oracle, and unrun environments. Distinguish diagnosis-only, plan-only, local implementation, installed, live, and delivery outcomes.

**Owners:** `dev-flow`, `repo-context`, `verification`, `change-review`; existing managed workstream `progress.md` only when needed. **Acceptance:** mid-task correction changes final claim and stale evidence cannot pass; a repeated goal does not reset work; final report does not promote compile/host/simulator evidence to device or production.

### RC8-4 · Project-native feedback and outcome oracles (P0; prior direction 2)

When a real task is blocked by absent start/health/focused-test/boundary-oracle/log/recovery feedback, repair the smallest project-native entry rather than building a Dev Flow-wide runner. Prefer a test that fails on the actual missing user outcome, including a negative control for wrong actor/source of traffic, zero discovery, stale cache, skipped tests, or weak assertions. Keep first-failure evidence and stop after the causal gap is closed.

**Owners:** `repo-context`, `test-system-engineering`, `verification`; `systematic-debugging` for cause. **Acceptance:** a representative false-green case becomes a real failing oracle before repair; a mature project retains its native runner; a small closed task is not burdened with setup it does not need.

### RC8-5 · Real-environment delivery chain (P0; prior direction 3)

For an outcome requiring an installed, deployed, external, or production environment, connect only applicable links: tested final bytes → artifact identity → correct target/install → effective config/data → user flow/external effect → observation → safe recovery/rollback. Keep action-specific authority: implementation does not authorize commit, install, publish, or production change. `NOT RUN`, `BLOCKED`, and observed failure remain distinct.

**Owners:** `verification`, `delivery-readiness`, `repo-context`, `repository-knowledge` for durable runbook ownership. **Acceptance:** a host-green/device-unknown case cannot claim device success; wrong artifact or stale configuration is caught; rollback/observation is named where consequential; no delivery action is inferred from code-edit authority.

### RC8-6 · Scope-aware agent convergence (P1; prior direction 4)

Bind each useful child/reviewer to the current outcome, slice, path ownership, oracle, resource owner, and stop boundary. On scope changes, cancel/rebase/mark stale; late results may inform reasoning but cannot silently restore old scope. Keep device, port, build cache, generated directory, and other shared resource ownership singular. The root integrates only current-scope evidence and final claims.

**Owners:** `dev-flow` orchestration, route result and affected fixtures. **Acceptance:** stale child output is rejected after a user correction; a shared-resource collision is prevented; single-agent work stays single-agent when delegation has no net value; nested agents inherit narrower authority.

### RC8-7 · Structural convergence and packet-era debt (P1; prior direction 5)

After behavior slices stabilize, remove redundant instructions and obsolete packet-era internals behind the supported `skills/dev-flow/scripts/dev-flow.py` → `public_cli.py` entry. Inventory imports and compatibility users before deletion; preserve supported CLI behavior and historical release truth. Do not bundle large code removal with model-route behavior changes. Stop after two ineffective auxiliary repairs and choose simplify/replace/defer/block rather than a third tweak.

**Owners:** `dev-flow-maintainer`, public CLI/tests, current documentation. **Acceptance:** smaller maintained surface without public-command regression; no new universal state machine; historical docs remain historical; deletion targets and negative controls are explicit before edits.

## Integration and release gates

Sequence RC8-1/2 first so the GPT-6 policy and instruction surface agree; RC8-3 through RC8-5 can then land as coherent owner-level slices, followed by RC8-6/7. Each slice changes active prose, metadata, code and affected tests atomically; independent review challenges the *final* integrated diff and result, not only a preliminary plan. The main lifecycle remains adaptive: no packet IDs, compulsory phase files, or fixed full-suite run for every task.

Before declaring a **source candidate**, run `python3 tools/validate_product_state.py`, affected unit tests, `skills/dev-flow-maintainer/scripts/validate-suite.py`, knowledge/plugin/data-security validators, compilation, `git diff --check`, and the relevant `check-workstream` command. Preserve first failures and rerun repaired checks. Separately qualify deterministic route/oracle fixtures, sampled live-model behavior if authorized, hosted/platform evidence, artifact identity, publication, and installation. No deterministic test or document audit alone proves real-model improvement or release readiness. Update `governance/product-state.json` and maintained projections only during a separately authorized, coherent candidate transition. Commit, push, tag, publish, install and deploy remain separate actions.

## Recheck triggers

Revisit this plan if official model behavior/availability changes, observed Luna/Sol/Astra tasks contradict the route table, the route schema cannot represent the required evidence-depth split, a representative negative control remains green, or an owner boundary changes. Change the smallest affected slice and its progress record; do not quietly rewrite a released baseline.
