# Dev Flow 2.0 research

## Research question

How can Dev Flow preserve business intent, implementation continuity, engineering quality, and delivery safety without making process maintenance the dominant cost of software work?

This study combines:

- observed Dev Flow 1.x behavior in two long-running GLM tasks;
- the current repository architecture and release process at commit `46ab9e0`;
- primary or original industry sources on developer productivity, developer experience, secure development, software supply-chain provenance, design documents, architecture decisions, change approval, small batches, trunk-based development, and operational toil;
- a cost/value analysis of each existing Dev Flow control.

## Current-state evidence

### Repository control surface

At the research baseline the repository contains:

- 314 tracked files;
- 41,795 lines of tracked Python, 19,168 lines of tracked JSON, and 6,517 lines of tracked Markdown;
- 13 Skill entrypoints and 419 unit-test methods;
- a 6,446-line `dev_flow.py` with 26 subcommands;
- a 1,270-line packet-aware Hook;
- a pool of 117 methods, 73 sources, and 38 deterministic risk models;
- three packet work modes, nine governed primary documents, three packet subdirectories, append-only events, checkpoints, content digests, approval ledgers, method records, context fingerprints, task briefs, reports, and knowledge manifests.

These numbers are not defects by themselves. They show that the control system is large enough to have its own material development, testing, compatibility, and release burden.

### Observed failure pattern in GLM work

The referenced GLM tasks show repeated displacement of business work by control work:

- repository inspection was blocked because an existing packet was at the wrong lifecycle state;
- recovery required packet discovery, checkpoint reconciliation, byte-drift classification, context readiness, method selection, fingerprints, and lifecycle transitions before implementation could continue;
- ordinary searches, Dev Flow's own CLI, approved dependency mutations, interactive shell input, nested roots, and platform-specific quoting were repeatedly misclassified by the Hook;
- delegation required large briefs containing profiles, fingerprints, acceptance/scope/verification IDs, leases, deadlines, resource ownership, exact reports, and checkpoint state;
- the task experienced context-window failures while carrying a large governance history;
- durable GLM design documents in the repository created clear long-term value, while most packet evidence existed only to satisfy or recover the control system.

This is a systemic pattern, not just a collection of isolated Hook bugs: the 1.x design assumes that process state is the primary continuity mechanism and that normal work is unsafe until the process model proves otherwise.

### Release cost

The ordinary CI workflow runs the full behavioral suite, contracts, five validators, compilation, and cleanliness checks in six OS/Python cells. The release-candidate workflow repeats the same full gate set before building, verifying, inventorying, attesting, and uploading the candidate. The runbook additionally requires two local builds, six PR cells, model evaluation, manual RC evidence, install/upgrade/rollback/re-upgrade testing, signing, and publication checks.

The model pilot alone costs six model calls per case and trial. The complete frozen plan uses twelve trials. This may be justified for a model-dependent semantic rewrite, but it is not economical as a standing release expectation for documentation, test, portability, or packaging changes.

## Industry evidence

### Productivity is multidimensional

[The SPACE of Developer Productivity](https://queue.acm.org/detail.cfm?id=3454124) rejects activity counts and any single universal productivity metric. It recommends examining satisfaction and well-being, performance, activity, communication and collaboration, and efficiency and flow together and in context.

Implication: Dev Flow must not optimize packet completeness, artifact count, method count, questions, reviews, or test count as proxies for business delivery. It should monitor a small balanced set of outcomes and friction signals.

### Feedback, cognitive load, and flow are direct productivity drivers

[DevEx: What Actually Drives Productivity](https://queue.acm.org/detail.cfm?id=3595878) identifies feedback loops, cognitive load, and flow state as the three central dimensions of developer experience. Clear tasks and organized code/documentation help; slow feedback, unnecessary hurdles, handoffs, and context switching hurt.

Implication: every Dev Flow control has a cost in delay, context, and task switching. A control belongs on the default path only when its expected risk reduction is greater than those costs.

### Secure practices should be integrated into the SDLC

[NIST SSDF 1.1](https://csrc.nist.gov/pubs/sp/800/218/final) defines a high-level set of secure-development practices intended to be integrated into each organization's SDLC, not a replacement SDLC imposed identically on every change.

Implication: security is an overlay selected by exposure and consequence. Common controls should be automated in repositories and CI; expert judgment should be reserved for material threat and trust-boundary decisions.

### Provenance is about verifiable artifact facts

[SLSA provenance](https://slsa.dev/spec/v1.2/provenance) defines provenance as verifiable information about where, when, and how an artifact was produced.

Implication: build, SBOM, checksum, signature, and attestation facts should remain machine-generated and artifact-bound. They should not be copied into planning prose or generalized into requirements for pre-release development.

### Design documents are useful only when design uncertainty is real

[Design Docs at Google](https://www.industrialempathy.com/posts/design-docs-at-google/) describes relatively informal documents focused on context, goals and non-goals, trade-offs, alternatives, cross-cutting concerns, and organizational memory. It explicitly calls design documents overhead and recommends skipping them when the solution is unambiguous or the document would only be an implementation manual. It also recognizes short 1-3 page mini design docs for bounded work.

Implication: design documentation is conditional on decision value even for managed work. Long duration requires an implementation/progress memory, but it does not prove that a separate design document has value.

### Architecture decisions should be short and live with the code

Michael Nygard's original [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) recommends small, modular decision records in the project repository, retaining superseded decisions and their rationale. It argues that agile rejects valueless documentation, not documentation itself.

Implication: durable decisions belong in Git beside the implementation. A short decision history is more useful than a complete execution transcript.

### Uniform external approval harms delivery without proving lower failure rates

[DORA: Streamlining change approval](https://dora.dev/capabilities/streamlining-change-approval/) reports that heavyweight external approval reduces delivery performance and found no evidence that it lowers change-failure rates. DORA recommends peer review, automated testing, monitoring, early risk detection, and extra scrutiny for high-risk changes. It explicitly identifies treating all changes equally and responding to incidents by adding more process as pitfalls.

Implication: approval must be action- and risk-specific. Normal implementation authority must not be re-approved through packet transitions. External delivery, destructive actions, material product semantics, and irreversible migration decisions remain separate boundaries.

### Small batches and fast integration reduce risk

[DORA: Working in small batches](https://dora.dev/capabilities/working-in-small-batches/) and [DORA: Trunk-based development](https://dora.dev/capabilities/trunk-based-development/) connect small, frequent integration with faster feedback and lower merge/stabilization burden. Heavy reviews encourage larger batches and make review harder.

Implication: Dev Flow should help form small coherent implementation slices and run the narrowest useful checks early. It should not add a fixed packet setup cost that makes small changes uneconomical.

### Repetitive control work is toil

[Google SRE: Eliminating Toil](https://sre.google/sre-book/eliminating-toil/) defines toil as manual, repetitive, automatable, tactical work with little enduring value that scales linearly. Durable design/documentation and automation can be engineering; repeatedly maintaining process state is toil when it does not improve the product or future system.

Implication: repeated packet synchronization, hash bookkeeping, method selection, and prose evidence duplication should be removed or automated away.

### Long context is not reliable project memory

[Lost in the Middle](https://arxiv.org/abs/2307.03172) found that long-context models can degrade significantly based on where relevant information appears, with information in the middle often used less reliably. Anthropic's [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) similarly treats context as a finite attention budget and recommends compaction, structured note-taking, just-in-time retrieval, and focused subagents for long-horizon work.

Implication: Dev Flow should not preserve continuity by carrying every prompt, event, command, or evidence result forward. A small repository progress snapshot plus links to current design/code/native evidence is a more useful external memory than an exhaustive packet or transcript.

### Agent complexity should earn its cost

[Building effective agents](https://www.anthropic.com/research/building-effective-agents) recommends starting with the simplest capable solution and adding routing, parallelization, orchestrator-worker, or evaluator patterns only when they demonstrably improve outcomes. It also describes routing easy work to efficient models and hard work to more capable models.

Implication: single-agent work remains the baseline, but when Dev Flow actually delegates, its existing P0-P6 model and reasoning profiles should be used consistently. The route should guide the dispatch without becoming a persisted governance artifact.

### Skills should use progressive disclosure

[Official OpenAI documentation: Customization](https://developers.openai.com/codex/customization/overview) states that `AGENTS.md` should stay small, Skills should package repeatable workflows, and references/scripts should load through progressive disclosure. [Codex best practices](https://developers.openai.com/codex/learn/best-practices) recommends concise durable guidance, planning for difficult tasks, reasoning depth based on task difficulty, relevant tests/review, bounded subagents, and one chat per coherent outcome.

Implication: Dev Flow's main Skill should contain a short, always-on quality spine and discovery rules. Detailed security, migration, release, UI, dependency, methodology, and agent-routing content should load only when their signals apply.

## Control value analysis

| Existing control | Risk reduction | Marginal cost | 2.0 decision |
|---|---|---|---|
| Fresh repository facts and effective instructions | High | Low | Keep on every task |
| User-owned material semantic decisions | High | Low when selective | Keep only at real decision boundaries |
| Repository implementation/progress knowledge | High for long work | Low to moderate | Keep as the managed minimum |
| Design/decision documents | High when real trade-offs exist | Moderate | Create conditionally, not from duration alone |
| Native tests, type checks, lint, build, CI, runtime evidence | High | Proportional | Keep and select by affected risk |
| Final diff/scope inspection | High | Low | Keep on mutation work |
| Separate delivery/destructive authority | High | Low | Keep as a safety boundary |
| Packet lifecycle for normal work | Low incremental | High | Remove from 2.0 default path |
| Mandatory AC/SC/VO identifiers and digests | Low outside regulated traceability | High | Remove; allow repository-specific use |
| Mandatory black-box/white-box prose accounting | Low beyond test strategy | Medium | Remove from default; retain specialist guidance |
| Bounded method selection | Low on normal work; high at uncertain critical boundaries | Low when non-persisted | Trigger selectively; never a gate |
| Persisted method records | Low outside regulated/native traceability | High | Legacy only |
| Context fingerprints and repeated checkpoints | Low beyond Git/docs | High | Remove from 2.0 work; Git plus progress is continuity |
| Task-relative model/reasoning routing for actual delegation | High when workloads differ | Low | Keep, but do not persist a receipt |
| Exhaustive delegation briefs and profile evidence | Low for bounded collaboration | High | Replace with a short ownership brief |
| Knowledge catalog/manifest/digest binding | Low for ordinary docs-as-code | High | Legacy only; new work uses normal Git review |
| Hook-enforced packet correctness | Negative when misclassified | Very high | Remove |
| Secret guardrails | High | Low when detector scope is explicit | Keep as the independent data-security Hook |
| Broad destruction and external-delivery command parsing | Mixed and partially covered | Persistent per-command and false-positive cost | Remove from the plugin; use host permissions, explicit authority, and delivery guidance |
| Full suite in every OS/Python cell | Duplicated | High | Split semantic and compatibility lanes |
| Full release gates for every change type | Duplicated | Very high | Replace with change-class release tiers |

## Root cause

The central design error is not simply "too much rigor." It is a mismatch between control type and evidence owner:

1. Runtime process artifacts became authoritative over repository truth.
2. The same controls were applied to changes with very different risk and continuity needs.
3. Human-readable prose duplicated facts already owned by Git, code, tests, CI, and artifacts.
4. Hooks attempted semantic authorization and lifecycle enforcement from syntactic command text.
5. Evaluation and release optimized completeness of the assurance system instead of marginal decision value.
6. Compatibility promises preserved every new control, so the control surface only grew.

The first 2.0 alpha exposed the opposite risk: after correctly removing packet ceremony, it made method and agent-routing capabilities too optional and created `design.md` for every managed workstream despite its own decision-value rule. That would reduce process cost at the price of inconsistent quality and unnecessary documentation.

## Research conclusion

Dev Flow 2.0 should be a thin policy for choosing the smallest useful combination of:

1. an always-on, zero-artifact quality calibration;
2. repository-tracked business continuity for long-running work;
3. signal-triggered specialist, method, model-routing, and review capabilities;
4. native engineering evidence for technical correctness;
5. deterministic safety boundaries for secrets, broad destruction, and external delivery.

It should not be a parallel workflow engine. Git, repository documents, code review, tests, CI, and delivery systems already own most of the relevant state.
