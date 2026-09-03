---
name: repository-knowledge
description: "Use when durable truth lacks a discoverable owner, is stale or conflicting, or a material handoff is chat-only; not routine docs."
---

# Repository Knowledge

Establish the smallest maintainable knowledge topology that lets people and later agents find current truth without relying on chat history. This Skill owns placement and reader paths, not every ordinary documentation update.

## Responsibility contract

- Consumes: repository facts, existing documentation conventions, ownership boundaries, current instructions, and the user's requested scope.
- Owns: repository/workspace classification, knowledge inventory, document disposition, progressive-disclosure topology, bootstrap proposals, and deterministic knowledge checks.
- Stops: before overwriting maintained documents, promoting inferred behavior into policy, creating a program-level authority without owner confirmation, or performing commit/push/tag/release/external actions.
- Hands off: engineering preferences and concise AGENTS.md projections to `manage-engineering-profiles`; material architecture rationale to `architecture-decisions`; task implementation and verification to their normal owners; delivery execution to `delivery-readiness` or a dedicated release workflow.

## Activate for topology, not documentation

Use this Skill when a new project has no discoverable native entry; a material result would otherwise be handed off only in chat; a durable fact has no clear canonical owner; active owners duplicate, contradict, or retain stale truth; or the long-term location of a project-level testing strategy, architecture boundary, or runbook is unresolved. An explicit audit, map, bootstrap, repair, plan, or check request also qualifies.

Stay quiet for one nearby update to a clear owner, a typo or formatting change, generated-document refresh, or a fact already owned exactly by source, schema, manifest, test, CI, or runtime configuration. Release execution belongs to its delivery owner.

## Modes

Select one mode from the request; start with `audit` when write scope is unclear.

- `audit`: inventory repositories, documents, instructions, CI/release surfaces, and gaps without mutation.
- `plan`: produce a reviewable, per-artifact create/keep/merge/move/generate/retire proposal without mutation.
- `map`: build a bounded, task-specific file and symbol map for progressive retrieval without mutation.
- `bootstrap`: apply an authorized plan with minimal files and preserve existing repository conventions and user changes.
- `check`: validate deterministic knowledge invariants and report drift without rewriting content.

The script is read-only in every mode:

```bash
python3 scripts/repository_knowledge.py scan --root <path> --format markdown
python3 scripts/repository_knowledge.py plan --root <path> --format markdown
python3 scripts/repository_knowledge.py map --root <path> --task "<task>" --format markdown
python3 scripts/repository_knowledge.py check --root <path> --format markdown
```

## First action

Identify the next reader and the durable fact they need, then locate its existing owner and entry path before proposing files. For a new small library, test whether its README can be the native entry. For conflicting API guidance, identify each active claimant and its readers before choosing one canonical owner. Do not start by creating a `docs/` tree or a phase template.

## Procedure

1. Resolve the requested path, actual Git roots, effective AGENTS.md chain, user changes, and whether the path is a repository or only a workspace container. Use the scanner before broad manual traversal.
2. Keep file contents local and inspect only maintained engineering surfaces. Do not open credential stores, `.env` values, raw production data, or generated dependency/build trees.
3. Classify facts as `observed`, `inferred`, `owner-input-required`, or `unknown`. A folder containing several Git roots is a multi-repository workspace until an owner confirms program-level authority.
4. Read [knowledge-topology.md](references/knowledge-topology.md) when selecting artifacts or deciding what belongs in AGENTS.md, an index, current-truth docs, ADRs, runbooks, automation, or generated maps.
5. Read [repository-shapes.md](references/repository-shapes.md) for monorepo, nested-root, workspace-container, or multi-repository planning.
6. Preserve a useful existing convention. Prefer linking and focused repair over creating a parallel `docs/` hierarchy. Never copy facts already owned by manifests, source, schemas, tests, CI, or runtime configuration.
7. For `plan`, assign one canonical owner to each durable fact and identify readers, next-read path, enforcement, freshness/recheck trigger, and disposition of overlapping existing documents. Distinguish current truth from historical rationale and generated evidence; merge, link, supersede, or report conflicting owners rather than silently duplicating them.
8. For `bootstrap`, show the plan before material replacement unless the user already authorized the exact rewrite. Create only files justified by current knowledge; do not create empty ADR, runbook, architecture, catalog, or workstream shells. A README can be the native entry for a small project; establish `docs/` plus an index (or a project equivalent) only once multiple long-lived knowledge domains need navigation.
9. Write maintained prose for both people and agents. Read [writing-for-people-and-agents.md](references/writing-for-people-and-agents.md) before generating or materially restructuring documents.
10. For a code task, use `map --task` after the stable index identifies the affected repository or component. Treat its ranked paths and symbols as candidate retrieval evidence; verify the actual source before deciding or editing.
11. Keep generated inventories and task maps replaceable. Do not treat inferred descriptions, dependency graphs, or generated summaries as project policy.
12. For a material lifecycle handoff, return the chosen canonical owner, next-reader path, freshness trigger, updates due to current truth, and any unresolved owner decision. Write durable product/contract, UX, architecture/ADR, testing-strategy, and operational facts back to their respective owners instead of copying them into a central record.
13. Create a minimal change record only when work must continue across sessions, owners, or independent slices and existing owners cannot provide reliable progress navigation. It links those owners and current blockers; it is not a packet, approval record, or duplicate long-term truth.
14. Run `check`, repository-native documentation checks, and affected suite checks. Report fresh evidence and unresolved owner decisions separately.

## Core invariants

- AGENTS.md is a concise router: scope, starting points, golden commands, protected boundaries, and knowledge-update routing. It is not a repository encyclopedia, release transcript, dependency catalog, or file tree.
- A stable index explains components, purposes, ownership, boundaries, and where deeper truth lives. A generated task map helps retrieval but never replaces the stable index.
- Prose owns why and operational judgment; deterministic commands own repeatable execution; manifests/tests/CI own enforceable facts.
- One durable fact has one canonical owner. Other documents link to it instead of copying it.
- Exact versions, current dependency graphs, generated APIs, build outputs, logs, and scan reports stay with their native/generated owners.
- Local implementation authority does not include commit, push, tag, release, deployment, or GitHub workflow monitoring.

## Quality and stopping

A useful result lets the next reader find the needed current truth, know why it is authoritative, and know when to recheck it. A later task should not need this chat to continue. Stop after the smallest owner/path change that solves that problem. If ownership remains genuinely ambiguous, report the competing owners and needed owner decision; do not promote an inference into policy or keep expanding documentation.

Do not use this Skill to execute or monitor a release, manage personal preferences, generate generic language documentation, or replace a repository's working documentation system without a demonstrated navigation, ownership, or drift problem.
