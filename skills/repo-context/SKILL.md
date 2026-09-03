---
name: repo-context
description: Use when repository facts, ownership, or an evidence handoff block the next decision; not for self-contained work.
---

# Repository Context

Establish the smallest safe fact base for the next decision. Resolve repository facts yourself; do not ask the user to rediscover code, configuration, branches, or tool output.

This Skill may operate alone for narrow read-only lookup. For material mutation, cross-boundary work, managed continuity, or high-risk delivery, load `dev-flow` as the coordinating kernel when available and not already active; keep this Skill as fact owner.

## First action

Name the decision that lacks evidence, then inspect the smallest path that can change it. A bug report might begin at the failing call and its regression test; a proposed compatibility change starts with consumers and the current contract. Do not begin with a repository-wide inventory merely because the repository is unfamiliar.

## Procedure

1. Resolve Git roots and scoped paths; a workspace may not be a repository root.
2. Read effective instructions and preserve user changes. Report conflicts or overlapping edits before mutation.
3. Inspect only the relevant manifests, source, tests, CI, generated surfaces, architecture records, runtime configuration, and nearby analogues. Follow the normal and error paths, affected consumers, and an existing test far enough to distinguish a fact from a plausible inference.
   A target/reference comparison is atomic even without paths: inspect the bounded repository before asking. With one plausible pair, inspect both before any answer; that response must name each side's facts, differences, and authority. Never omit either side. Otherwise state ambiguity and ask. Analogy is non-authoritative.
4. Trace affected call, data, errors, consumers, artifacts, and compatibility enough to separate fact from inference.
5. Find native controls and missing environment evidence; configured is not passed.
6. Compare affected technology/framework/risk evidence with the effective Skills exposed in the current turn. Return only useful specialist routes and honest native/manual fallbacks; do not infer availability from installed files or a registry. Surface `repository-knowledge` only for an observed missing project entry, chat-only material handoff, ambiguous canonical owner, duplicate/stale truth, or unresolved durable strategy location; report that signal, not a generic documentation recommendation.
7. Return compact roots, instructions, behavior, boundaries, facts versus inference, unknowns, specialist routes, and recheck triggers. State what later evidence would invalidate the fact base.

## Examples and stopping

- A clear owner and one affected design page: return that page and its readers; the ordinary update stays direct and quiet.
- Two active documents disagree about an API rule, or no successor can find a material decision outside chat: hand off the topology decision to `repository-knowledge`.
- A mechanical README correction or self-contained question: do not expand discovery or create a handoff.

Stop when the next owner can make its decision from observed facts and explicit unknowns. If an ambiguity is a product choice, return it to `requirements-design`; if evidence contradicts the working model, refresh only the affected path rather than accumulating a ledger.

Use `references/repository-discovery.md` for complicated root, instruction, runtime, source-quality, or cross-repository discovery. Use `references/context-readiness.md` only to diagnose why context is insufficient, not as a mandatory persisted gate.

## Boundaries

- Do not decide product semantics, architecture, dependencies, or verification outcomes.
- Do not create fingerprints, packet records, context ledgers, or profile snapshots for ordinary work.
- Do not install or activate a Skill from discovery alone.
- Do not load every matching Skill. A candidate needs an affected owner surface, positive decision/evidence value, and no applicable negative trigger.
- Keep volatile observations and secrets out of maintained documentation.
