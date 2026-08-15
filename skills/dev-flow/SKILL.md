---
name: dev-flow
description: Orchestrate repository diagnosis, change, audit and verification with risk-based evidence and Skill routing.
---

# Dev Flow

Preserve meaning, authority, continuity, knowledge, and evidence; see `references/core-lifecycle.md` for multi-owner work.

## Responsibility contract

- Consumes: objective, authority, and owner artifacts.
- Owns: mode, routes, lifecycle, integration, continuity, knowledge, drift, and final claims.
- Stops: affected slices at missing authority, material drift, stale baselines, or unapproved dependency/delivery; independent authorized slices need valid inputs/evidence.
- Hands off: after `repo-context`, each evidence family to one applicable owner; do not route merely to prove a trigger absent.

## Always-on quality kernel

Every persistent mutation must establish facts; persist source, understood requirement, corrections, AC/SC/VO and AMBs; bind design; maintain continuity; separately account black/white-box tests; challenge requirement, implementation, evidence, and diff; and record knowledge impact. Routing cannot remove these duties.

## Classify and start

1. Resolve roots, instructions, worktree, scope, risks, and mutation/delivery authority.
2. Run `route-task`: `direct` is non-mutating micro/spike; persistent is `traced`; high-risk/explicit governance is `governed`.
3. Read `references/artifact-schemas.md`; new capability contracts do not upgrade old packets.
4. Treat routing as provisional. After context, rerun it and record the delta before mutation when task, risk, UI, capability, or delivery classification differs.

## Establish context

Route `repo-context`; load only repository-valid Skills. Follow `references/methodology-system.md`: use `select-methods`, or governed `record-methods`; preliminary selection is not ready, and design/verification/review need fresh records. Reselect on drift.

## Execute

For multi-slice or governed work, read `references/orchestration.md`. Otherwise:

1. Bind current and protected behavior, acceptance, scope, and oracle. For bugs, reproduce the cause and, when practical, a failing focused regression.
2. Persist requirement/design revisions; ask up to three decision-changing questions per round until no material AMB remains.
3. Freeze a coherent slice; keep related code, black/white-box tests, docs, comments, generated surfaces, and cleanup together.
4. At resume, steering, premise/phase change, slice/team/repair boundaries, pre-verification, and final claim, rehydrate requirement, design, context fingerprint, checkpoint, and AMBs. Update at coherent boundaries, not by timer.
5. Run narrow then module/smoke checks. Audit diff/scope, user work, generated/dependency/secret drift, tests, comments, and docs. Record `change-set.v1` and commit-ready status.
6. Reroute/reopen on invalidated premises; rerun affected evidence after final-byte changes.

Deep review is risk/intent-routed; root basic challenge is unconditional. Delivery readiness needs an explicit delivery action; release or rollback planning alone is not authority.

Before delegation, follow `references/multi-agent-v2-orchestration.md`; run `route-agent`, bind baselines/ownership/tests/stops, and reconcile each child.

Use `references/knowledge-system.md`: tracked truth says what is true, dossiers retain why/how, ignored packets recover runs. Promote only implemented, verified, reusable knowledge; exclude secrets, unnecessary raw/personal data, local paths, and logs.

At user checkpoints, remain in Default mode and follow `../requirements-design/references/user-interaction.md`. Requirements owns meaning; dependency/delivery own named decisions; this control plane owns operational approval, secret routing, and waivers. Never infer authority.

## Close

Run fresh `verification` against frozen bytes; review tests/findings before repair. Green needs an oracle sensitive to the target defect. Keep failures, flakes, blocks, waivers, and unrun gates distinct.

Before the successful final, follow the reference's `validate-packet` → terminal transition → `deactivate-packet` sequence; the Stop Hook is advisory.

Never commit, push, create a PR, tag, release, deploy, install, or message externally without separate authority.
