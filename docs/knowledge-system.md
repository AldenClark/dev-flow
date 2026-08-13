# Durable project knowledge

Dev Flow separates durable knowledge by meaning instead of treating one packet directory as a universal document store.

| Plane | Default | Answers | Retention |
|---|---|---|---|
| Current project truth | `docs/project/` | What is true now? | Updated in place; Git retains history |
| Change dossier | `docs/changes/<change-id>/` | Why and how did this change happen? | Accepted records are stable history |
| Runtime evidence | `.codex/dev-flow/` | How can this interrupted run recover and prove its work? | Local and ignored; never implicitly published |

Existing repository conventions take precedence. If none exists, the defaults above provide a small interoperable structure. `.dev-flow/knowledge.json` can declare alternate repository-relative `project_root` and `changes_root` paths; callers may also supply explicit relative roots.

## Tracked current truth

`catalog.json` maps each stable `KT-*` identifier to exactly one current document. Current documents link back to the catalog and prefer source anchors over duplicated generated facts. Accepted architecture decisions are superseded rather than rewritten.

## Tracked change dossiers

Small changes use one `change.md`; governed work uses the exact split `requirements.md`, `design.md`, `execution.md`, and `verification.md`. Every retained file in either tracked plane is declared; an undeclared file fails validation instead of becoming an unreviewed evidence side channel. Both formats use `manifest.json` to record:

- change ID, lifecycle status, and document paths;
- AC, SC, and VO identity sets;
- for new dossiers, an `authority_binding` over the exact requirement/design bytes and the exact AC/SC/VO sets;
- separate black-box and white-box test status, rationale, and evidence;
- project-knowledge impact and final disposition;
- promotion links to cataloged current documents and links to related change manifests.

Create the dossier early enough to preserve the original request, clarified requirement, user decisions, design, progress, drift rulings, and evidence. Once accepted, change history should not be silently rewritten; use an explicit erratum or follow-up dossier.

New templates opt in to `authority_binding`. It names the same change ID, binds `requirements` and `design` to their declared document paths and `sha256:<64 lowercase hex>` digests, and repeats the exact identifier sets for comparison with `traceability`. In a governed dossier, requirements may define only authoritative `AC-*`; design may define only authoritative `SC-*` and `VO-*`. Every stable ID has one normative definition across those two files, so a wrong-role or cross-file duplicate definition fails even after its file digest is refreshed. A single dossier intentionally uses the same `change.md` for both roles and may define all three families there, once each. Freeze the authority document set before calculating its digests. A later byte edit, missing or duplicate declaration, renamed ID, path substitution, or set divergence fails validation. Existing dossiers without this field remain readable and are not automatically migrated; once the field is declared, an incomplete binding fails closed.

## Promotion and privacy

Promotion is intentional, not automatic. Only implemented, freshly verified, reusable conclusions belong in current truth. Temporary plans, raw command output, logs, and local recovery checkpoints stay in the dossier or ignored runtime state as appropriate.

Never persist credentials, private keys, personal data, or sensitive raw payloads in tracked knowledge. Retain a sanitized conclusion and, when authorized, a reference to the secure system that owns the evidence.

## Structural check

The standard-library-only validator reports `valid` or `invalid` and concrete structural errors:

```bash
python3 skills/dev-flow/scripts/knowledge_system.py --repo-root /path/to/repository
```

It rejects root escape, symlink escape, a missing repository-local ignore rule for `.codex/dev-flow`, stale declared authority bytes or ID sets, unresolved placeholders, obvious machine-local absolute paths, common secret-like values, broken links/backlinks, missing knowledge disposition, and missing black-box/white-box accounting. In a linked Git worktree it asks Git for the repository-owned `info/exclude` path rather than assuming `.git` is a directory. It deliberately does not score document prose or infer semantic quality. Templates live under `skills/dev-flow/templates/knowledge/`.
