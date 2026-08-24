# Repository knowledge capability

## Objective

Add a Dev Flow Skill that can inspect a single repository, monorepo, or polyrepo workspace and propose or establish a maintainable human-and-agent knowledge system without turning generated observations into unreviewed policy.

## Scope

- Add a first-class `repository-knowledge` Skill with explicit audit, plan, map, bootstrap, and check boundaries.
- Add deterministic, read-only discovery and planning for repository roots, manifests, documentation, CI, release surfaces, and AGENTS.md coverage.
- Support progressive disclosure: a concise AGENTS.md route, a stable human-readable index, focused current-truth/decision/runbook documents, and replaceable task maps.
- Exercise the scanner against `/Users/ethan/Repo` and representative single-repository, monorepo, and polyrepo layouts without modifying those repositories.
- Integrate the capability with Dev Flow documentation and deterministic suite checks.

## Out of scope

- Commit, push, tag, GitHub Actions monitoring, release execution, or other external delivery actions.
- Automatically promoting inferred conventions, architecture, ownership, or dependency choices into project policy.
- Replacing repository-native manifests, CI, changelogs, API documentation, or release scripts.
- Creating a full dynamic symbol/dependency indexer in the initial slice.

## Outcome slices

1. Define knowledge ownership, document topology, repository classifications, and mutation authority.
2. Implement the Skill and deterministic scanner/planner/checker with fixtures.
3. Run a read-only machine-wide workspace rehearsal and refine heuristics from observed layouts.
4. Integrate repository truth, user-facing documentation, and suite validation.

## Completion evidence

- Skill structural validation passes.
- Focused scanner tests cover single repository, monorepo, polyrepo, generated nested repositories, and knowledge-placement boundaries.
- Read-only scan of `/Users/ethan/Repo` completes without entering excluded build/cache/vendor trees.
- Dev Flow contract checks and maintainer validation pass for the final bytes.
