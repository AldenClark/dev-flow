---
name: manage-engineering-profiles
description: Resolve or maintain confirmed engineering preferences and AGENTS.md projections; do not infer policy from code frequency.
---

# Manage Engineering Profiles

Use this Skill when a confirmed personal, team, project, component, or task preference must be resolved, explained, changed, promoted, retired, waived, or projected. Do not load it merely because nearby code repeats a pattern: ordinary implementation consumes an already supplied effective snapshot, or follows repository facts and instructions.

## Responsibility

- Owns profile lifecycle, layered resolution, conflicts, promotion/retirement/waiver, and concise projections.
- Does not own architecture, dependency selection, product semantics, or verification; a resolved preference is an input to those owners, never their substitute.
- Stops before an unauthorized write or an unresolved applicable `must` conflict. Missing optional profiles mean no preference, not an inferred replacement.

Read [profile-contract.md](references/profile-contract.md) before changing a manifest, profile, decision, or projection.

## Resolve a confirmed value

First identify the decision that the preference can change and resolve the applicable profile stack for the requested path and mode. Use only validated, unexpired entries with their declared scope, provenance, strength, exceptions, and source hashes. Keep these distinctions visible:

- repository source, CI, runtime, and tests are observed engineering facts;
- a confirmed profile is a scoped preference or shared control;
- a user decision is still required when neither fact nor confirmed value settles a material choice.

Apply the winning value only where its selectors apply. A personal value supplies a default; it cannot weaken repository/team `must` controls, current user authority, safety boundaries, or native checks. Report the winner, shadowed values, conflicts, exceptions, and the condition that would require a recheck so the receiving task can make its own engineering decision.

Never turn code frequency, installed Skills, task history, dogfood aggregates, or ordinary conversation into an active personal or team policy. They may identify a candidate for review, but only explicit owner confirmation of the exact layer, scope, strength, observable effect, conflict behavior, and review trigger permits persistence or activation.
Do not store exact installed versions, advisories, popularity, or “latest” claims as durable preferences.

## Maintain a profile only with authority

For a create, change, promotion, retirement, suppression, or waiver, establish target layer, owner, scope, and write authority. Use the CLI without `--write` to show a review-first proposal unless the current request already authorizes that exact action. Validate all affected modes, including clean-profile invariance for team-reproducible and CI resolution. Promote from named trial evidence plus owner approval; retire without erasing history.

Use `references/quality-policy.md` only when defining code-quality outcomes or specialist capability requirements. The Rust example is inactive and must be reviewed entry by entry before use.

## Useful result and handoff

Return a small effective snapshot or a precise disposition, not a new policy document by default. Hand the snapshot to the active implementation, architecture, dependency, verification, or repository consumer; return to the main task once the preference no longer changes the next decision.

## CLI

```bash
python3 scripts/profile-tool.py validate <profile.toml>
python3 scripts/profile-tool.py explain --root <repo> --path <path> --fact language=rust
python3 scripts/profile-tool.py scaffold --id <id> --layer project --owner <owner> --output <path>
python3 scripts/profile-tool.py scaffold-manifest --root <repo> --profile-path profiles/project.toml --profile-id <id> --layer project
python3 scripts/profile-tool.py agents-projection --root <repo>
python3 scripts/profile-tool.py suppress --fingerprint <sha256> --owner <owner> --reason <reason> --tier T1 --output <repo>/.dev-flow/suppressions.json
```

Add `--write` only after the exact action is authorized or the owner approves the shown artifact.
