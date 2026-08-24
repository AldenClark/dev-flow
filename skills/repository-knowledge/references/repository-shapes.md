# Repository shapes

Use this reference when a path contains nested Git roots, manifest workspaces, several products/platforms, or ambiguous program ownership.

## Single repository

One Git root without a maintained multi-component boundary. Reuse README as the stable index when it already routes readers effectively. Add `docs/index.md` only when several maintained document families or components need navigation. Root AGENTS.md is normally enough.

## Monorepo

One Git root with component boundaries supported by workspace manifests, build configuration, ownership, deployment, or maintained source structure.

- Put shared scope and golden commands at the root.
- Add nested AGENTS.md only where toolchain, authority, verification, security, release, or ownership rules materially differ.
- Derive workspace membership and exact versions from manifests; maintain only component purpose, ownership, public boundaries, and routing as prose or curated metadata.
- Prefer one root documentation index with component entrypoints over a copied document tree in every component.

Directory count alone does not prove a monorepo. A collection of examples, fixtures, vendored sources, or generated packages is not automatically a component model.

## Multi-repository workspace

A non-Git navigation path containing multiple independent Git roots is an observed workspace, not automatically a product/program authority.

Before creating a program hub, require owner confirmation that the grouping owns durable cross-repository knowledge such as product architecture, compatibility contracts, coordinated releases, or shared operations.

When confirmed, prefer a dedicated versioned meta repository containing:

```text
AGENTS.md
README.md or docs/index.md
catalog.toml                 # only for curated facts tooling consumes
docs/architecture/
docs/contracts/
docs/adr/
docs/runbooks/
tools/<program-command>
```

Child repositories continue to own their implementation truth, manifests, tests, release scripts, and local instructions. Cross-repository facts have one owner in the hub and are linked from children rather than copied.

## Nested and generated repositories

Treat these as excluded from workspace ownership discovery unless the user names them:

- dependency checkouts and submodule internals;
- build, packaging, derived-data, target, cache, vendor, and generated artifact trees;
- temporary test/evaluation fixtures;
- archived copies and export directories.

If an excluded location is itself the explicit target, inspect it normally. Exclusion prevents accidental discovery; it does not declare that the content is unimportant.

## Planning matrix

| Observed shape | Default plan | Owner decision |
|---|---|---|
| Small single repository with effective README | Keep README as index; add/repair concise AGENTS.md if useful | Which non-obvious boundaries belong in shared instructions |
| Repository with several document families | Add or repair a stable docs index; link from README/AGENTS.md | Canonical owner for overlaps |
| Manifest-defined monorepo | Root routing plus component map; selective nested instructions | Which components have independent ownership/tooling |
| Multi-repository workspace | Audit each Git root; propose but do not create a hub | Whether the directory is a durable program boundary |
| Existing comprehensive docs system | Map and repair it; do not impose the default layout | What can be retired or merged |
