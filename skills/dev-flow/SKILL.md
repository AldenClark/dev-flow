---
name: dev-flow
description: Orchestrate non-trivial repository diagnosis, design, implementation, fixes, refactors, migrations, audits, and verification with risk-scaled evidence and focused Skill routing.
---

# Dev Flow

Use this as a thin control plane. Preserve user authority, repository conventions, compatibility, and evidence; load only the focused Skills required by the task.

## Classify and start

1. Resolve the real Git root, effective Codex instruction chain, worktree state, task scope, risks, and mutation/delivery authority.
2. Run `route-task` and use its smallest work mode:
   - `direct`: clear micro/spike work; no packet; keep the decision and fresh check inline.
   - `traced`: ordinary non-trivial work; `packet.json`, append-only `events.jsonl`, and `trace.md` only.
   - `governed`: security/migration/release/dependency/public-contract/persisted-data risks, material UI semantics, or an explicit governance request; use the full packet.
3. Create state only when the selected mode requires it:

```bash
python3 scripts/dev-flow.py route-task --task-type <type> --risk <risk>
python3 scripts/dev-flow.py init-packet --root <repo> --change-id <id> \
  --task-type <type> --objective <objective> --risk <risk>
```

Read `references/artifact-schemas.md` before creating, migrating, repairing, or validating a packet. New writes use schema 2.0; old schemas remain readable.

## Establish context

Route `repo-context` for facts and run compact readiness by default. Use `--detail full` only to diagnose a readiness decision. Select `personal-interactive` for personal work and `team-reproducible` or `ci` when the result must reproduce without personal profiles.

```bash
python3 scripts/dev-flow.py assess-context --root <repo> --task-type <type> \
  --profile-mode team-reproducible --path <scope> --risk <risk>
```

Missing optional profiles, AGENTS files, or specialist Skills never expand authority or block by name. Native repository controls cover the repository; the task mapping separately identifies which oracle must be run for the change.

## Execute

For multi-slice or governed work, read `references/orchestration.md`. Otherwise:

1. Confirm current behavior, acceptance, protected behavior, scope, and the narrow verification oracle.
2. Activate focused owners only as needed: requirements/UX, architecture/dependency decisions, debugging, verification, review, or delivery readiness.
3. Implement the smallest coherent slice, run its narrow check, inspect drift and user-owned changes, and update persistent state when present.
4. Reopen only the affected requirement or scope when evidence changes it. Never treat momentum as authority.

Independent review is conditional on explicit review, governed risk, material UI impact, or security/migration/release/rollback work. Delivery readiness is conditional on explicit delivery intent or release/rollback work; it is not an ordinary mutation tax.

Single-agent execution is the baseline. Before delegation, run `preflight --require-delegation --tool-surface-confirmed` and read `references/multi-agent-v2-orchestration.md`; otherwise stay single-agent unless parallel review is required. Native child final is primary: reconcile every task, and never duplicate it only for wait timeout or missing optional report.

At any user-owned checkpoint, remain in Default mode and follow `../requirements-design/references/user-interaction.md`. Never infer approval for dependencies, destructive/external actions, delivery, or materially expanded scope.

## Close

Run repository-native fresh checks through `verification`. Use `change-review` only when routed; verify findings before repair. Use `delivery-readiness` only when routed. Claim implemented, verified, accepted, release-ready, or delivered only when evidence proves that exact state; keep failures, flakes, blocks, waivers, and unrun gates distinct.

Never commit, push, create a PR, tag, release, deploy, install, or message externally without separate authority.
