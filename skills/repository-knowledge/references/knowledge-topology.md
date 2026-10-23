# Repository knowledge topology

Use this reference to decide which artifact owns a fact and how agents discover it without loading the whole repository knowledge base.

## Planes and owners

| Plane | Canonical owner | Purpose | Load timing |
|---|---|---|---|
| Navigation | `AGENTS.md`, existing instruction equivalent | Scope, pointers, golden commands, protected boundaries | Always for the affected path |
| Stable map | `README.md`, `docs/index.md`, or repository-native portal | Components, purpose, ownership, boundaries, deeper links | At task entry, then follow relevant links |
| Current contract and implementation | Architecture, product, contract, operations, module documents | Required behavior, observed implementation, and any gap between them | Only for an affected boundary |
| Rationale | ADRs, fork records, focused change records | Why a durable choice exists, alternatives, consequences, recheck trigger | When changing or challenging the choice |
| Operations | Runbooks plus repository commands | Human judgment, prerequisites, failure/recovery, deterministic execution | For the named operation |
| Managed change | Repository-native workstream/plan documents | Scope, slices, design, progress, handoff | While the workstream is active |
| Retrieval | Generated inventory or task-specific code map | Candidate files, symbols, relationships, freshness | Generated for the current task |
| Enforcement | Manifests, schemas, tests, linters, CI | Machine-enforced facts and constraints | During implementation and verification |

## Placement rules

Use AGENTS.md only when the instruction must be available before an agent knows which deeper document to load. Keep:

- applicability and precedence;
- the stable knowledge entrypoint;
- repository-native environment/check commands;
- destructive, dependency, migration, security, and release authority boundaries;
- a few non-obvious protected contracts;
- where durable knowledge from a change belongs.

Exclude:

- full directory trees or component catalogs;
- copied formatter, linter, manifest, or CI facts;
- exact installed versions or "latest" claims;
- complete release procedures;
- long design rationale or history;
- generated symbol/dependency maps;
- secrets, machine-local paths, logs, and personal preferences in shared scope.

Use a stable index when readers need to choose among three or more components or knowledge areas. A small library may use its README as the index. A larger repository should normally link from README to a focused `docs/index.md`; do not create a second index that duplicates a complete working README.

Use an ADR for a material choice whose rationale and alternatives will remain useful after implementation. Accepted ADRs are historical records: supersede rather than silently rewrite them. Put the maintained current requirement and implementation status in their existing owners and link to the ADR for rationale.

## Intent, accepted decisions, and implementation gaps

Keep the original intent traceable through an existing issue, user statement, or decision source, including the reason for the accepted choice. A proposed mechanism or an assistant summary is not a user decision. When only part of a proposal was accepted, identify that subset and leave the rest proposed or unresolved; do not promote the whole proposal into the contract.

Distinguish what is currently required from what source or runtime evidence shows is implemented. Name a material gap, including platform differences, rather than rewriting the requirement to match today's code. Link implementation status to its native evidence; do not copy logs or maintain a second inventory.

A later decision may replace only one clause: identify that clause and its replacement source while preserving the unaffected contract and historical rationale. If the requirement body cannot be updated in the same authorized change, put a short temporary pointer in the affected paragraph to the accepted decision, then remove it when the body is synchronized. A note hidden only in progress is insufficient for a reader who starts from the requirement.

Implementation rollback changes observed delivery status; it does not revoke an accepted product decision. Only an actual superseding product decision changes the requirement. Record the resulting implementation gap in the existing owner. These are content distinctions, not mandatory fields, a new ledger, or an approval workflow. For a worked handoff into design and verification, see [the integrated example](../../dev-flow/references/methodology-system.md#integrated-example-status-presentation-and-recovery).

Use a runbook when success depends on human judgment, credentials/roles, environment state, sequencing, observation, or recovery. Move repeated deterministic steps into a repository command; keep the runbook as the explanation and exception/recovery guide.

Use a fork record when a fork has a continuing synchronization burden. Preserve upstream identity/baseline, local divergence, rationale, sync procedure, compatibility constraints, and exit condition.

## Progressive disclosure contract

Design every maintained entrypoint to answer:

1. What scope does this cover?
2. What should I read next for this task?
3. Which source is authoritative?
4. Which command or check proves the relevant fact?
5. When does this information need rechecking?

The normal loading sequence is:

```text
effective AGENTS.md chain
  -> stable repository/component index
    -> one affected current-truth, ADR, contract, or runbook
      -> task-specific generated map or source evidence
```

Do not require readers to load sibling documents preemptively. Cross-link at decision boundaries and include a short "when to read" phrase where a title alone is ambiguous.

## Generated knowledge boundary

Generated material must include or expose:

- generator and schema version;
- source revision or freshness time when retained;
- bounded scope and exclusions;
- replacement command;
- a label that it is derived evidence, not policy.

Prefer ignored local caches for task maps. Commit generated documentation only when the repository already treats it as a built public artifact and CI verifies regeneration.
