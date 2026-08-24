# Repository knowledge capability design

## Current facts

- Dev Flow already separates current truth, direct change records, managed workstreams, and temporary runtime evidence.
- `manage-engineering-profiles` owns concise AGENTS.md projections and forbids promoting observed frequency into shared policy.
- `/Users/ethan/Repo` contains independent repositories, manifest-defined monorepos, and non-Git directories that group several repositories.
- A broad filesystem walk reaches build caches, dependency checkouts, vendored sources, and evaluation fixtures that must not be treated as owned repositories.

## Decision

Create `repository-knowledge` as a first-class Skill with one bounded outcome: establish or restore a repository-owned knowledge and documentation system that is useful to both people and agents.

The Skill uses five modes:

- `audit`: inspect and report facts, gaps, ambiguity, and drift without writing.
- `plan`: propose a minimal topology and per-artifact disposition without writing.
- `map`: derive a bounded task-specific file and symbol map for progressive retrieval without writing.
- `bootstrap`: apply only an explicitly approved plan, preserving existing documents and repository conventions.
- `check`: validate links, ownership, AGENTS.md budgets, catalog paths, and other deterministic invariants.

Repository topology is classified separately from documentation maturity:

- `single-repo`: one Git root without a manifest-defined multi-component workspace.
- `monorepo`: one Git root with manifest- or source-supported component boundaries.
- `polyrepo`: a non-Git program directory containing multiple independently owned Git roots.
- `workspace`: a navigation directory whose ownership or grouping is not strong enough to infer a program-level contract.

## Knowledge planes

- Navigation: concise AGENTS.md plus a stable documentation index.
- Current truth: architecture, contracts, component boundaries, product/operational facts.
- Rationale and history: ADRs, fork rationale, and change records.
- Operations: human-readable runbooks and deterministic repository commands.
- Retrieval: replaceable generated inventory and later task-specific code maps.
- Enforcement: manifests, tests, linters, CI, and policy checks remain authoritative.

## Human and agent readability

Maintained documents use meaningful titles, short summaries, stable links, explicit ownership, current status, and "when to read" routing. Machine-readable metadata is added only where deterministic tooling consumes it; it does not replace readable prose or duplicate manifest facts.

## Alternatives rejected

- A large generated AGENTS.md: permanently consumes context, duplicates facts, and becomes stale.
- A generated full file tree committed to Git: high churn with weak semantic value.
- One universal document template: ignores repository conventions and creates empty documentation shells.
- Combining release delivery with knowledge bootstrap: mixes safe local analysis with external writes and recovery-sensitive operations.

## External evidence

- OpenAI's 2026 harness-engineering report describes the failure of a large AGENTS.md, uses a short AGENTS.md as a table of contents into a structured repository knowledge base, and mechanically checks links and freshness: <https://openai.com/index/harness-engineering/>.
- Codex discovers an instruction chain from the repository root toward the working directory, gives nearer instructions precedence, and applies a combined byte limit; this supports concise root routing plus selective nested instructions: <https://developers.openai.com/codex/guides/agents-md>.
- GitHub Copilot distinguishes repository-wide, path-specific, and agent instructions and recommends a Skill or custom agent when instructions become too large or task-specific: <https://docs.github.com/en/copilot/reference/custom-instructions-support> and <https://docs.github.com/en/copilot/concepts/agents/copilot-cli/comparing-cli-features>.
- Aider's repository map selects important symbols and dependency-connected files under a token budget instead of loading a full tree: <https://github.com/Aider-AI/aider/blob/main/aider/website/docs/repomap.md>.
- Repository-level retrieval research supports iterative and selective context instead of undifferentiated whole-repository context: RepoCoder (<https://arxiv.org/abs/2303.12570>) and the 2026 MRCoder preprint (<https://arxiv.org/abs/2607.26805>).
- Backstage keeps curated ownership and component metadata near source and turns it into a catalog; this justifies an optional program catalog only when tooling consumes it: <https://backstage.io/docs/features/software-catalog/>.
- Google's release-engineering guidance separates well-defined policies from repeatable automation, while GitHub's workflow-run API separates read/observation from rerun/cancel write authority: <https://sre.google/sre-book/release-engineering/> and <https://docs.github.com/en/rest/actions/workflow-runs>.

## PushGo release orchestration disposition

PushGo's release workflow justifies a separate Skill, but the first implementation should be PushGo-owned rather than a generic Dev Flow core capability. The workflow combines deep release audit, coordinated changelog/release-note/update-payload edits, version and artifact checks, commit/push/tag boundaries, tag-triggered GitHub Actions, workflow monitoring, reconciliation, and failure recovery. Those decisions and permissions differ materially from repository knowledge bootstrap.

The recommended unit is a thin `$pushgo-release` Skill plus deterministic `pushgo-release` or `pushgoctl release` commands in a confirmed versioned PushGo program repository:

- the Skill owns release intent, component selection, evidence interpretation, human checkpoints, external-action authority, and recovery decisions;
- the command owns repeatable discovery, plan generation, deep preflight invocation, document/version consistency checks, per-repository status, action execution, resumable state, and structured evidence;
- existing child-repository scripts and workflows remain the implementation owners for platform-specific build, signing, packaging, publishing, and artifact verification;
- `delivery-readiness` remains the generic Dev Flow owner for exact target/artifact, evidence, rollback, residual gates, and action-specific authority.

Use a persisted release plan/state machine because repositories and workflows can fail independently. At minimum distinguish planned, audited, documentation-prepared, locally-verified, commit-ready, pushed, tagged, workflow-running, released, failed, and recovery-required outcomes per component. Commit, push, tag, release, retry, cancellation, and rollback remain separate explicitly authorized actions. Extract a generic `release-orchestration` Skill into Dev Flow only after another product demonstrates the same stable workflow and ownership model.

## Recheck triggers

- Real scans cannot distinguish owned repositories from generated or vendored repositories.
- Existing document conventions cannot be preserved without manual mapping.
- A future symbol/dependency index requires a persistent schema or new dependency.
- Release orchestration needs shared catalog fields not justified by knowledge navigation alone.
