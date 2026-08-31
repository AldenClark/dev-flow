---
name: manage-engineering-profiles
description: Manage engineering profiles and AGENTS.md projections: create, validate, explain, diff, or audit.
---

# Manage Engineering Profiles

For profile ownership, write, promotion, suppression, or waiver decisions, remain in Default mode and follow `../requirements-design/references/user-interaction.md`.

Manage preference assets without turning current code frequency, installed Skills, or personal taste into unreviewed team policy.

## Responsibility contract

- Consumes: repository context plus the target layer, owner, scope, and authority.
- Owns: profile lifecycle, resolution, conflicts, promotion/retirement/waiver, and concise projection.
- Stops: before a write that the request does not authorize or at an unresolved applicable must-level conflict.
- Hands off: an effective snapshot to task and repository consumers when they need one; it never makes their decisions.

## Procedure

1. Read `references/profile-contract.md` completely before changing a manifest, profile, decision, or projection.
2. Establish the target layer, owner, scope, authority, and canonical facts. Keep personal values out of shared project files.
3. Extract candidates from manifests, CI, scripts, ADRs, source, and existing instructions. Label each `observed`, `inferred`, or `owner-input-required`.
4. Propose minimal, separate changes for `AGENTS.md`, `.dev-flow/preferences.toml`, profiles, or decision records. Never infer a team-wide rule or public compatibility promise from frequency alone.
5. Treat an explicit create/change/promote/retire/waive request from the authorized owner as write authority. Otherwise use `scripts/profile-tool.py` without `--write` for a review-first proposal; do not ask twice for the same authorized action.
6. Validate and resolve the full affected layer stack and requested personal/team/CI modes; run the clean-profile invariance checks in `Resolution modes`. Applicable `must` conflicts require an authorized decision; missing optional layers degrade safely.
7. Explain winners, shadowed entries, conflicts, exceptions, source hashes, mismatches, and recheck triggers.
8. Promote only from trial evidence and owner approval; retire without erasing history.

Dev Flow may propose a personal workflow preference only from an explicit owner request or an authorized selected-history/dogfood review. Persist it only after the owner confirms the exact layer, scope, strength, observable effect, conflict behavior, and review trigger. Observed repetition, method frequency, repository statistics, or ordinary conversation never writes or activates a profile automatically.

Durable personal profiles must carry explicit-user provenance, path scope, future expiry, and fixed correction/deletion policies. Expiry or missing governance makes the profile invalid; do not silently renew or infer replacement values.

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

Add `--write` when the current request already authorizes that exact profile action or after the owner approves the shown artifact. Promotion, retirement, suppression, and waiver remain review-first when the request did not already authorize them.

## Boundaries

- Do not choose product architecture or a dependency implicitly; route to the corresponding decision Skill.
- Do not store exact installed versions, advisories, popularity, or “latest” claims as durable preferences.
- Do not let personal route preferences weaken team/project native checks.
- Do not name one vendor Skill as the only acceptable quality outcome.
- Do not infer or persist personal values from task history, dogfood aggregates, or ordinary conversations, and never let a personal layer weaken team/project `must` controls.
