<!-- dev-flow-workstream-contract: v1 -->
# Dev Flow 2.0 RC.6 implementation

## Outcome

Freeze the current release-process, product-state, and doctor-truth changes as an RC.6 candidate and complete separately authorized delivery actions.

## Slice plan

| Slice | Outcome | Write prefixes | Protected paths | Evidence | Status | Decision |
|---|---|---|---|---|---|---|
| S0 | Create candidate identity and maintained projections | `.codex-plugin/`, `.github/`, `CHANGELOG.md`, `README.md`, `docs/`, `evals/`, `governance/`, `skills/company-data-security/`, `tools/` | `docs/workstreams/dev-flow-2.0-rc.4/`, `docs/workstreams/dev-flow-2.0-rc.5/` | focused state/release tests | complete | D1 |
| S1 | Freeze and locally qualify exact candidate | - | - | full deterministic suite, static review, clean diff | in-progress | D2 |
| S2 | Complete exact-SHA external delivery and current truth | `CHANGELOG.md`, `README.md`, `docs/`, `governance/` | - | CI, artifacts, install, public release checks | pending | D1, D2 |

## Acceptance

- Candidate and published identities are distinct until delivery is observed.
- The exact candidate passes local R2 gates and the final review is explicitly same-context.
- Immutable tag, public prerelease, artifact attestations, and isolated install are verified before published truth is recorded.
