# Repository discovery contract

## Scope and authority

- Resolve the actual Git root for every path and record nested repositories independently.
- Record mutation, dependency, destructive, external, credential, delivery, and release authority separately.
- Treat workspace folders as navigation containers until Git evidence proves otherwise.
- Preserve unrelated user-owned changes and report overlapping dirty paths before editing.

## Instruction chain

Discover the active host's global and project instructions, then walk from each repository root to every scoped path. At a directory level, treat `AGENTS.override.md` as replacing `AGENTS.md`; do not merge it as an ordinary preference layer. Record source path, scope, precedence, digest, size, applicability, conflicts, broken references, and freshness.

Map consequential instructions to downstream requirement, design, task, verification, review, and evidence IDs. Do not duplicate formatter/linter configuration or large repository facts into agent prose.

## Repository and runtime facts

Inspect only the applicable surfaces:

- manifests, lockfiles, toolchains, feature flags, generated contracts, and package topology;
- CI jobs, scripts, build/test/lint/codegen commands, environment assumptions, and supported targets;
- entry points, callers, data/control flow, ownership, state, persistence, errors, cancellation, shutdown, and telemetry;
- public API, wire/schema/data compatibility, migrations, rollback, packaging, signing, and deployment;
- current behavior through a reproducer, trace, test, benchmark, rendered UI, or explicit source path.

Prefer an existing working analogue over invented architecture. Distinguish:

- `observed`: mechanically or directly evidenced;
- `inferred`: reasonable but not authoritative;
- `owner-input-required`: a product, policy, or authority decision;
- `unknown`: evidence absent or inaccessible.

## Source quality

For each source, check canonical owner, scope, applicability, conflicts, duplicates, version/digest, reviewed time, expiry/recheck trigger, and context/security suitability. Reject placeholder instructions, stale commands, personal preferences committed as team mandates, unscoped language rules in mixed repositories, and prose that claims to enforce security or permissions without a real control.

## Output

`context.snapshot.v1` contains roots, Git state, instruction chain, scoped paths, languages/artifact roles, project archetypes, current behavior, commands/controls, architecture and runtime boundaries, facts/inferences/unknowns, source-quality findings, and authority. It references canonical sources instead of copying them.
