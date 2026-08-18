# Engineering profile contract

## Authority surfaces

- Skills own procedures.
- `AGENTS.md` owns concise always-visible commands, boundaries, and the pointer to `.dev-flow/preferences.toml`.
- TOML profiles own personal/team/project/component/task preferences and quality policies.
- Repository manifests, source, CI, and runtime own observed facts and installed versions.
- ADRs and `.dev-flow/decisions/PREF-*.json` own accepted durable exceptions or choices.
- JSON effective snapshots own normalized task resolution; they are replaceable evidence, not policy.

## Six layers

Resolve low to high: public neutral baseline, personal, team, project, component/subtree, task decision. This precedence applies to preferences, not safety, law, current user authority, repository instructions, observed contracts, or native manifests.

Personal values are defaults only. Team/project/component layers own shared requirements. A task exception requires an authorized decision and scope.

## Resolution modes

Resolve three modes explicitly: `personal-interactive` may read the known personal directory plus declared repository/task sources; `team-reproducible` and `ci` must exclude personal directories, environment-derived personal values, and credentials, and use only the public baseline plus declared repository/task sources.

For `team-reproducible` and `ci`, run the resolver from clean isolated profile homes with deliberately different personal profiles; require identical effective bytes and fingerprints, and prove shared artifacts contain no personal paths, hashes, values, or credentials.

Record source hashes, winners, shadowed entries, conflicts, unresolved material choices, fingerprints, exact commands/environments/outcomes, and every `NOT RUN` cell; an explicit work mode may raise but never lower evidence-derived risk or shared controls.

## Locations

```text
${CODEX_HOME}/dev-flow/profiles/*.toml
<repo>/.dev-flow/preferences.toml
<repo>/.dev-flow/profiles/*.toml
<repo>/.dev-flow/decisions/PREF-*.json
<repo>/.dev-flow/suppressions.json
<caller-selected-output>/effective-preferences.json  # optional replaceable audit output
```

Ordinary resolution uses local pinned sources and does not fetch remote policy. Repository sources may not escape `.dev-flow/`, and declared digests must match.

## Profile fields

Every profile declares `schema_version`, stable `id`, `layer`, `owner`, `version`, `status`, and `[[preferences]]` records. Every record declares:

- stable `key`, `kind`, and `strength` (`must`, `should`, `may`);
- typed `value` or quality `outcome`;
- `applies_when` and `avoid_when` selectors;
- rationale and viable alternatives;
- exception policy and optional required approver;
- review trigger and optional enforcement class.

Selectors use `key=value` or `key!=value` and may describe language, framework/version, artifact role, boundary, component/path, platform, phase, risk, or brownfield state.

## Resolution

1. Record the effective instruction chain separately.
2. Load the public baseline, known personal directory, declared repository sources, and approved task profiles.
3. Validate schema, owner, source, digest, layer, scope, and references.
4. Observe project facts and classify task/artifact selectors.
5. Filter inapplicable entries before precedence.
6. Resolve by layer. A more specific `should`/`may` may replace a lower preference; an applicable `must` requires an authorized exception.
7. Mark each entry applied, shadowed, inapplicable, conflicting, stale, or unknown with source and reason.
8. Treat same-layer different values and unexcepted `must` disagreement as conflicts.
9. Record mismatches with current repository facts as decision signals, not migration permission.
10. Write source paths/hashes, facts, winners, shadowed entries, conflicts, exceptions, mismatches, errors, and a stable fingerprint.

Block only unresolved applicable `must` conflicts, invalid required sources, or an authority boundary. Missing optional profiles degrade safely.

## Lifecycle

- Capture candidate with provenance and scope.
- Trial it in named tasks/projects and collect rework/effect evidence.
- Promote only through explicit owner review.
- Override through a scoped decision with approver, rationale, residual risk, and expiry/removal trigger.
- Validate preference exceptions against `preference-decision-schema.json`; expired, malformed, out-of-scope, or wrong-key records never authorize a `must` override.
- Recheck on recorded ecosystem, project, exception, or contract triggers.
- Retire without rewriting history.

Reminder suppression is not policy and never resolves an applicable `must` conflict. When suppression output is explicitly requested, bind it to the resolved profile fingerprint, owner, reason, scope, and optional expiry; re-evaluate when the resolved inputs change.

## AGENTS projection

Keep authoritative commands, destructive/dependency/release/security/migration boundaries, a few non-obvious protected contracts, and the manifest pointer. Exclude catalogs, “latest” versions, personal values in shared scope, copied formatter/linter rules, full installed-Skill inventories, generic language manuals, resolver internals, and secrets.
