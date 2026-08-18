# Repository knowledge in Dev Flow 2.0

Durable business and engineering knowledge belongs in the repository that owns the change. Dev Flow uses normal docs-as-code and Git history; it does not create a parallel authoritative knowledge database.

## Three useful forms

| Form | Purpose | Typical location | Maintenance |
|---|---|---|---|
| Current truth | Architecture, contracts, runbooks, module behavior, operating limits | Repository-native docs such as `docs/architecture` or `docs/project` | Update when truth changes; Git retains history |
| Direct change record | Durable behavior or rationale without an adequate existing home | Repository convention or `docs/change-notes/<slug>.md` | Create only when it adds knowledge not already preserved elsewhere |
| Workstream knowledge | Outcome, design trade-offs, implementation slices, current progress, durable decisions | Repository convention or `docs/workstreams/<slug>/` | Update at meaningful design/slice/blocker/handoff/closure events |

Existing repository conventions take precedence. When none exists, a managed workstream uses `implementation.md` and `progress.md`, adds `requirements.md` only when complex or cross-team semantics lack another durable source, adds `design.md` only for real trade-offs, and adds `decisions.md` only for durable decisions without an ADR home.

## What to keep

- business outcome, non-goals, current facts, trade-offs, and selected design;
- coherent implementation slices, dependencies/order, current state, blockers, and next step;
- compatibility, failure, rollout/rollback, and operational decisions future maintainers need;
- concise links to authoritative code, schemas, ADRs, runbooks, issues, tests, CI, or artifacts.

Do not copy command transcripts, bulk logs, hashes, source schemas, test output, agent activity, temporary paths, or generated evidence into prose. Code, Git, tests, CI, runtime systems, and release artifacts own technical facts.

## Review and retention

Review knowledge with the code it explains. Replace stale current-state text and rely on Git for chronology. Supersede durable decisions rather than erasing their rationale. Remove or archive a workstream when it no longer helps maintenance, according to the repository's own convention.

Direct work creates no Dev Flow continuity document, but it must update current-truth documentation when the change makes architecture, contracts, runbooks, product behavior, or operational limits stale. Add one light change record only when a material product rule, public contract, persistent-data rule, security/authorization behavior, recovery procedure, cross-boundary invariant, or non-obvious rationale would otherwise be lost. Do not duplicate an issue, changelog, ADR, code, tests, or maintained documentation.

Never persist credentials, private keys, personal data, confidential payloads, or unnecessary user wording. Keep runtime evidence in ignored or temporary storage with appropriate access and retention.

## Legacy compatibility

`docs/project`, `docs/changes`, `catalog.json`, manifests, authority bindings, and the `validate-knowledge` CLI remain supported for repositories that already contain Dev Flow 1.x knowledge dossiers. They are historical compatibility surfaces, not the default for new 2.0 work. Existing dossiers are not automatically migrated or deleted, and their validators cannot block unrelated 2.0 implementation.
