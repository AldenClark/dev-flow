# Repository knowledge capability progress

## Status

Complete.

## Completed

- Confirmed the capability boundary: repository knowledge establishment is separate from release orchestration and delivery authority.
- Inspected Dev Flow's current knowledge, profile, maintenance, security, and verification contracts.
- Observed that naive `.git` discovery includes generated evaluation repositories and Swift dependency checkouts, so discovery requires bounded traversal and explicit exclusions.
- Added the `repository-knowledge` Skill with audit, plan, map, bootstrap, and check modes plus progressive-disclosure topology and human/agent writing guidance.
- Added a standard-library read-only scanner/planner/task-map/checker and focused synthetic coverage for single repositories, monorepos, multi-repository workspaces, unversioned container knowledge, release/product document separation, generated-root exclusion, link drift, AGENTS.md budgets, subtree resolution, and lexical task retrieval.
- Scanned 39 development directories and 42 owned Git roots: 11 manifest-supported monorepos and 31 single repositories. Only four roots currently have AGENTS.md and one has a detected stable docs index.
- Found 304 documentation files outside an owning Git root, concentrated in the PushGo and glm multi-repository containers, plus 310 repository-knowledge documents inside Git roots.
- Exercised plans for PushGo, Aegir, gui_ju, and airport and task maps for PushGo release orchestration and Gateway channel-password compatibility.
- Deterministic machine-wide checking reports 15 errors and 57 warnings: 14 broken relative links, one non-portable machine-local link, 38 missing root AGENTS.md files, 18 missing stable indexes for qualifying repositories, and one oversized AGENTS.md warning. These are audit findings only; target repositories were not changed.
- Decided that PushGo release work should use a separate PushGo-owned Skill plus resumable CLI, with generic delivery readiness retained in Dev Flow.
- Passed Skill structural validation, Dev Flow maintenance and capability-contract validation, 50 focused integration/security checks, and all 476 repository evaluations for the final implementation bytes.

## Current

- No active implementation slice.

## Next

- If authorized separately, bootstrap selected repositories from generated plans in small reviewable batches.
- Design the PushGo-owned release Skill and resumable CLI in a confirmed versioned program repository.

## Evidence limits

- No repository outside `/Users/ethan/Repo/dev-flow` has been modified.
- No commit, push, tag, release, or external GitHub action is authorized or performed.
