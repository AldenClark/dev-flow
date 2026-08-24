# Repository knowledge in Dev Flow 2.0

## Knowledge forms

Current project truth describes the maintained system: architecture, contracts, runbooks, module behavior, operations, and conventions.

Direct change records explain a durable behavior or non-obvious rationale that has no adequate home in current-truth docs, code, tests, an issue, changelog, or ADR. They are short change history, not continuity state.

Managed workstream knowledge explains a material change: its outcome, design trade-offs, implementation slices, current progress, and durable decisions.

Runtime evidence is temporary/generated: command output, logs, traces, screenshots, raw model transcripts, local paths, and caches. Keep it out of maintained prose unless a small sanitized excerpt is necessary to explain a durable decision.

## Knowledge-system establishment

Use the `repository-knowledge` Skill when the requested outcome is to audit, design, bootstrap, repair, or validate the repository's documentation and knowledge system itself. Ordinary task documentation continues to use the owning document directly.

System establishment separates four concerns:

- concise path-scoped navigation in AGENTS.md;
- a stable human-readable repository/component index that routes to current truth, decisions, contracts, and operations;
- replaceable generated inventories or task maps for agent retrieval;
- enforceable facts in manifests, schemas, tests, linters, CI, and runtime controls.

A stable index and a generated task map are not substitutes. The index owns purpose, boundary, ownership, and routing; generated maps own revision-bound observations such as candidate files, symbols, and relationships. Load them progressively: effective instructions, stable index, one affected knowledge owner, then task-specific generated evidence.

Do not infer a program-level authority from a directory containing several Git repositories. Confirm the cross-repository ownership boundary first, then either create a versioned meta repository or move each fact to the child repository that owns it.

## Repository ownership

Business documents live in the repository that owns the change and follow its conventions. When none exists, use `docs/change-notes/<slug>.md` for a direct change record and `docs/workstreams/<slug>/` for managed continuity. The separate `docs/changes/<change-id>/` convention remains reserved for legacy 1.x dossiers. Architecture decisions should use the repository ADR convention when available.

For managed work, `implementation.md` and `progress.md` are the minimum shared continuity surface. Add `requirements.md` only when complex or cross-team semantics need a durable source beyond the request or issue, `design.md` only for real trade-offs, and `decisions.md` only when durable decisions have no existing ADR home. Direct work creates no continuity document but still maintains current truth and may add one light change record when it preserves otherwise-missing knowledge.

Use a direct change record when the change materially affects product rules, public contracts, persistent data, authorization/security behavior, operational recovery, cross-boundary invariants, or rationale that future maintainers cannot reconstruct. Do not use one for formatting, mechanical refactors, routine renames, test-only restatement, or information already captured by an issue, changelog, ADR, maintained documentation, code, and tests.

Git provides versioning, authorship, review, timestamps, diffs, and history. New 2.0 documents do not require a catalog, manifest, digest, promotion transition, acceptance identifier set, or packet binding.

Catalogs remain optional for a confirmed monorepo or multi-repository program whose tooling consumes curated component purpose, ownership, or relationship metadata. Derive exact members, versions, and dependencies from native manifests instead of copying them into a second truth source.

Repositories with regulated traceability, generated documentation, or stronger native controls may retain them. Dev Flow consumes those controls rather than duplicating them.

## Writing rules

- Write for the future maintainer and business owner.
- Preserve why, trade-offs, current outcome, next step, and material limits.
- Link to code, schemas, CI, dashboards, or artifacts instead of copying them.
- Keep progress current and short; Git history preserves old snapshots.
- Supersede durable decisions rather than erasing their rationale.
- Exclude secrets, personal payloads, unnecessary production data, machine-local paths, bulk logs, and generated facts owned by code/tooling.
- Delete or archive a workstream only under the repository's normal knowledge-retention rules.

## 1.x boundary

Historical `docs/project`, `docs/changes`, catalogs, manifests, and authority bindings are user-owned repository files, not supported 2.0 workflow inputs. Never let them block implementation or acceptance, and do not migrate or validate them unless the user explicitly requests separate historical maintenance.
