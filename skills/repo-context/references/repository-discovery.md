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

## Engineering context and specialist catalog

- Emit one artifact-fact record per affected path or explicit scope. Bind phase, role, boundary, language, framework, version, path, component, and risk instead of applying a repository-wide language label to every artifact.
- Scan only effective repository `.agents/skills`, user Codex/Agents roots, admin/system roots, explicit task roots, and plugin roots proven by the bounded Codex cache layout. Never recursively search the machine for Skills.
- Preserve every observed same-name Skill candidate with provenance, authority, path, digest, and version. Do not collapse the group into a name-keyed dictionary. An admission must bind a unique digest, version, or path before that name can route.
- Treat `not-observed` as an epistemic result, not a claim that a plugin or Skill is uninstalled elsewhere. Discovery never installs, enables, promotes, or turns a personal Skill into team policy.
- Derive the required neutral capability outcomes first; select no more than one admitted specialist per outcome after native controls and owned policies are considered.
- Fingerprint the effective instruction chain, profile resolution, native controls, artifact/version facts, capability registry, Skill catalog, and admissions. Re-resolve at a relevant digest or task-fact change rather than on a timer.

## Output

`context.snapshot.v1` contains roots, Git state, instruction chain, scoped artifact facts, project archetypes, current behavior, commands/controls, architecture and runtime boundaries, bounded Skill catalog/collisions, neutral capability outcomes and selected routes, facts/inferences/unknowns, source-quality findings, authority, recheck triggers, and the aggregate engineering-context fingerprint. It references canonical sources instead of copying them.
