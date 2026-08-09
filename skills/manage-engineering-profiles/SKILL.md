---
name: manage-engineering-profiles
description: Assess, scaffold, create, validate, explain, diff, promote, retire, waive, and audit layered Dev Flow engineering profiles and concise AGENTS.md projections. Use when a user or team wants to establish or change personal, team, project, component, task, language, dependency, or quality-policy guidance; do not activate merely to consume an existing profile during ordinary product work.
---

# Manage Engineering Profiles

Manage preference assets without turning current code frequency, installed Skills, or personal taste into unreviewed team policy.

## Procedure

1. Read `references/profile-contract.md` completely before changing a manifest, profile, decision, or projection.
2. Establish the target layer, owner, scope, authority, and canonical facts. Keep personal values out of shared project files.
3. Extract candidates from manifests, CI, scripts, ADRs, source, and existing instructions. Label each `observed`, `inferred`, or `owner-input-required`.
4. Propose minimal, separate changes for `AGENTS.md`, `.dev-flow/preferences.toml`, profiles, or decision records. Never infer a team-wide rule or public compatibility promise from frequency alone.
5. Require approval before writing or replacing any instruction/profile asset. Use `scripts/profile-tool.py` without `--write` for review-first proposals.
6. Validate and resolve the full affected layer stack. Applicable `must` conflicts require an authorized decision; missing optional layers degrade safely.
7. Explain winners, shadowed entries, conflicts, exceptions, source hashes, mismatches, and recheck triggers.
8. Promote only from trial evidence and owner approval; retire without erasing history.

Read `references/quality-policy.md` when defining code-quality outcomes or specialist capability requirements.
Use `references/rust-frontend-profile.example.toml` only as an inactive personal-profile example; review and update every entry before activation.

## CLI

```bash
python3 scripts/profile-tool.py validate <profile.toml>
python3 scripts/profile-tool.py explain --root <repo> --path <path> --fact language=rust
python3 scripts/profile-tool.py scaffold --id <id> --layer project --owner <owner> --output <path>
python3 scripts/profile-tool.py scaffold-manifest --root <repo> --profile-path profiles/project.toml --profile-id <id> --layer project
python3 scripts/profile-tool.py agents-projection --root <repo>
python3 scripts/profile-tool.py suppress --fingerprint <sha256> --owner <owner> --reason <reason> --tier T1 --output <repo>/.dev-flow/suppressions.json
```

Add `--write` only after the user approves the shown artifact. Promotion, retirement, suppression, and waiver commands are also review-first by default.

## Boundaries

- Do not choose product architecture or a dependency implicitly; route to the corresponding decision Skill.
- Do not store exact installed versions, advisories, popularity, or “latest” claims as durable preferences.
- Do not let personal route preferences weaken team/project native checks.
- Do not name one vendor Skill as the only acceptable quality outcome.
