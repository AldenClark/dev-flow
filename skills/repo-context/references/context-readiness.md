# Context sufficiency diagnosis

Use this reference only when progress is blocked or likely to be unsafe because context is missing. It is a diagnostic checklist, not a tier, score, persisted checkpoint, or packet gate.

## Ask what is missing

Assess only dimensions that can change the current decision:

- authority and delivery boundaries;
- real Git roots, worktree, generated or nested repositories;
- effective instructions and repository conventions;
- product outcome, protected behavior, and material open decisions;
- relevant language/framework/version and native build/test/codegen controls;
- architecture, state, errors, concurrency, resources, and current behavior;
- dependency, public contract, schema/data, migration, compatibility, security, privacy, FFI, UI/accessibility, operations, packaging, and rollback where exposed;
- required environment, account, device, service, credential, or external-system evidence.

Absence of a profile, AGENTS.md, named Skill, dossier, catalog, or optional tool is not itself a gap. A configured control is available evidence, not proof that it ran.

## Outcomes

- `ready`: enough applicable evidence exists to proceed.
- `advisory`: a limitation is useful to note but reversible work can continue.
- `blocked`: a safety, product, compatibility, or authority fact cannot be inferred and the affected action must wait.

Name the exact missing fact, evidence already checked, affected action, and smallest safe way to resolve it. Do not generate setup or ask the user for repository facts Codex can inspect.

## Recheck

Recheck only when a fact relied upon by the current work changes: task path, repository root, instructions, relevant version/configuration, design decision, risk boundary, final bytes, or execution environment. Do not compute fingerprints or repeat the whole diagnosis at every phase.
