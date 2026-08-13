# Project knowledge system

Use three semantic planes. Their authority differs; directory count is not the architecture.

## 1. Tracked current truth

Current truth answers “what is true now?” for future work. Prefer an existing repository convention. Otherwise use `docs/project/` with `catalog.json` as the mechanical index.

- Give each current document one stable `KT-*` identifier and one current path.
- Update current truth in place; Git retains its prior states.
- Do not restate facts that source, schemas, generated API references, or configuration already express more reliably. Link to those sources.
- Accepted ADRs remain immutable and are superseded by a new ADR. The catalog points to the current decision.
- Keep ownership, review triggers, limitations, and source anchors close to the claim.

Current truth is authoritative for current project knowledge, not for the detailed history of one change.

## 2. Tracked change dossier

A change dossier answers “what did this task mean, decide, change, verify, and leave behind?” Use `docs/changes/<change-id>/` by default.

- Create `manifest.json` when durable planning begins, not after implementation.
- Use exactly `change.md` for a small traced change. Use the exact split `requirements.md`, `design.md`, `execution.md`, and `verification.md` for governed work. Declare every retained dossier file; undeclared files fail validation.
- Preserve the original request or a sanitized source reference, the AI-understood requirement revisions, user corrections, decision rationale, progress, drift rulings, evidence, and residual gates at proportionate detail.
- Keep AC, SC, and VO identifiers stable. Record black-box and white-box test accounting separately.
- For a new dossier, declare `authority_binding` only when its requirement/design baseline is ready to freeze. Bind the exact document bytes and exact AC/SC/VO sets; do not refresh a digest to conceal a semantic change.
- Freeze an accepted dossier. Correct it through a clearly identified erratum or a new follow-up dossier; do not silently rewrite accepted history.
- Cross-link every dossier document to its manifest. Related change links must resolve to another `manifest.json` below the configured changes root.

The dossier is authoritative for that change's history, not for the project's current state.

## 3. Ignored runtime evidence

`.codex/dev-flow/` is local recovery state and raw evidence. It may contain packet projections, append-only events, transient checkpoints, logs, screenshots, and tool output.

- Keep the active objective, requirement/design digests, current slice, last proven result, next safe action, and stop conditions recoverable there.
- Treat raw evidence as supporting material, not as project knowledge.
- Keep the tracked dossier self-contained through sanitized conclusions and stable relative pointers where appropriate.
- Do not copy secrets, personal data, credentials, or sensitive raw payloads into tracked knowledge. Record only the minimum sanitized semantic conclusion and an authorized secure-system reference.

Runtime evidence is never made a publication artifact merely because validation passed.

## Root selection

The defaults are `docs/project` and `docs/changes`. A repository may adopt different relative roots through its own convention or `.dev-flow/knowledge.json`:

```json
{
  "schema_version": "1.0",
  "project_root": "engineering/knowledge",
  "changes_root": "engineering/changes"
}
```

Explicit relative roots supplied by the caller take precedence. All roots must remain inside the repository, be disjoint from each other and `.codex/dev-flow`, and contain no symlink traversal. Never infer a new convention when the repository already has one.

## Knowledge impact and promotion

Every change records one impact and one disposition:

| Impact | Meaning |
|---|---|
| `none` | No reusable current truth changes. |
| `add` | Introduces reusable current truth. |
| `update` | Changes existing current truth. |
| `deprecate` | Retires or supersedes current truth. |

| Disposition | Meaning |
|---|---|
| `not-applicable` | Required only with impact `none`. |
| `pending` | Promotion decision is still open; it cannot remain on accepted material-impact work. |
| `promoted` | Implemented, verified, reusable conclusions were intentionally applied to current truth. |
| `deferred` | An owner intentionally left current truth unchanged, with a concrete rationale or follow-up. |

Promotion is a human/agent decision, not automatic synchronization. Promote only conclusions that are implemented, freshly verified, reusable beyond the current task, and safe to retain. Plans, temporary observations, command transcripts, and one-off debugging details remain in the dossier or runtime evidence.

## Change-authority binding

New templates use this opt-in manifest shape:

```json
{
  "authority_binding": {
    "schema_version": "1.0",
    "change_id": "safe-change-id",
    "requirements": {
      "path": "requirements.md",
      "sha256": "sha256:<64 lowercase hex>"
    },
    "design": {
      "path": "design.md",
      "sha256": "sha256:<64 lowercase hex>"
    },
    "identifier_sets": {
      "acceptance_criteria": ["AC-1"],
      "scope": ["SC-D1", "SC-P1", "SC-L1"],
      "verification_obligations": ["VO-1"]
    }
  }
}
```

For governed dossiers, the paths must equal `documents.requirements` and `documents.design`. Requirements may normatively define only AC IDs; design may normatively define only SC and VO IDs. The validator requires each stable ID to occur exactly once across that two-document authority set, so a second or wrong-role definition is invalid even when the editor refreshes the changed file's digest. A single-document dossier uses `change.md` for both roles and may define all three families in that one file. Define normative IDs on explicit Markdown list or table definition lines such as `- AC-1: ...`, `- SC-D1: ...`, and `- VO-1: ...`; prose mentions do not create authority. The validator recomputes both file digests, rejects duplicate definitions, compares the extracted AC set from requirements and SC/VO sets from design, and requires `identifier_sets` to equal `traceability` exactly.

The field is intentionally optional for existing history: absence means legacy-readable, not authority-bound. Once present it is all-or-nothing and fails closed. A quality-tagged runtime packet additionally compares this binding with the packet's approved requirement/design bytes and ID sets; updating both a document and its manifest digest is therefore not a substitute for reopening the authoritative packet when meaning changes. No legacy dossier is automatically migrated.

## Mechanical validation

Run `knowledge_system.py` against the repository after material dossier updates, before acceptance, and after promotion:

```bash
python3 skills/dev-flow/scripts/knowledge_system.py --repo-root .
```

The validator is deliberately thin and fail-closed. It checks containment, symlinks, a repository-local ignore rule for `.codex/dev-flow` (including the actual Git-owned exclude path in linked worktrees), declared-file accounting, manifest fields, unique current IDs/paths, local links/backlinks, AC/SC/VO shape and opted-in authority binding, knowledge disposition, black-box/white-box accounting, placeholders, obvious local absolute paths, and common secret-like strings. `promoted` is structurally available only to accepted or superseded dossiers with completed test-family accounting. It does not judge semantic correctness, completeness, writing quality, or test adequacy; those remain review obligations. It never generates, migrates, promotes, archives, or edits files.
