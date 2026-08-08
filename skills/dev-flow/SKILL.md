---
name: dev-flow
description: Run the project's lightweight, evidence-first Codex development workflow for non-trivial repository diagnosis, design, implementation, bug fixes, refactors, migrations, dependency changes, security or performance work, releases, CLI/TUI, background jobs, Rust backends, React frontends, native apps, and Rust FFI. Use when work needs repository-first requirements, explicit design and change scope, persistent trace documents, controlled Multi-Agent V2 delegation, risk-based testing, independent blue/red audit, acceptance evidence, or authorized delivery. Pair with engineering-preferences for technical choices.
---

# Dev Flow

Prioritize implementation quality, preserve user authority, and scale ceremony to risk. Use normal conversation for confirmation; do not use Plan Mode as the workflow engine.

## Establish the runtime and authority

1. Resolve `<skill-root>` as the directory containing this `SKILL.md`.
2. Run `python3 <skill-root>/scripts/dev-flow.py preflight`. Require Codex 0.147.0+, `multi_agent`, `multi_agent_v2`, and `hooks`; require `[agents].max_concurrent_threads_per_session = 3`.
3. Confirm that the active turn exposes the V2 collaboration tools before delegation. Do not use a V1 fallback.
4. Read repository instructions and establish every real Git root before deriving status or scope.
5. Distinguish read-only, design, local implementation/testing, commit, push, PR, release, deployment, and external-message authority. Never widen authority by inference.
6. Load `$engineering-preferences` before any technical choice.

## Create the trace before implementation

For every code or project mutation, create a persistent packet before the first edit:

```bash
python3 <skill-root>/scripts/dev-flow.py init-packet \
  --root <repo> --change-id <id> --task-type <type> \
  --objective <request> --authority <authorized-actions>
```

Use the compact `trace.md` profile only for a genuine micro change. Use the complete packet for all other changes and all non-trivial read-only audits. The complete packet contains `packet.json`, context, requirements, design, execution, test matrix, blue audit, red audit, evidence, decisions, task briefs, agent reports, and artifacts.

Treat documentation as execution state, not an after-action summary:

- record repository facts and current behavior before final design;
- record every acceptance criterion, material choice, alternative, approval, dependency decision, and change-scope boundary;
- append progress, agent dispatches, drift rulings, failed hypotheses, repair rounds, test attempts, and blockers while they happen;
- keep blue and red audit evidence separate;
- record exact commands, roots, environments, timestamps, exits, artifacts, `NOT RUN` cells, residual risk, and every delivery action;
- never erase superseded decisions or first-failure evidence.

No undocumented implementation is complete. After compaction or resume, reconstruct state from the packet, repository, and artifacts before continuing.

Read `references/artifact-schemas.md` for the contract. Validate at phase boundaries and before any acceptance claim:

```bash
python3 <skill-root>/scripts/dev-flow.py validate-packet <packet-dir>
```

## Run the lifecycle

Follow `references/core-lifecycle.md`:

1. Scan repository structure, instructions, manifests, tests, CI, runtime paths, and nearby analogues.
2. Reproduce current behavior or establish a measured baseline.
3. Convert the request into an explicit requirement delta, acceptance criteria, constraints, and protected behavior.
4. Classify task, project profiles, risk modifiers, compatibility, documentation depth, and delivery authority.
5. Compare designs against repository evidence and engineering preferences; write the full direct, indirect, conditional, protected, out-of-scope, and delivery scope.
6. Confirm material design choices and every new dependency with the user before crossing their approval boundaries.
7. Build a dependency-aware task graph and resource ledger.
8. Implement coherent slices; update progress and drift records at each meaningful boundary.
9. Run static checks and controlled test waves from narrow/cheap to broad/environment-heavy.
10. Perform independent, risk-scaled blue and red audits; verify findings before remediation and re-review only the affected scope.
11. Trace every acceptance, scope, and verification ID to fresh evidence.
12. Perform only separately authorized delivery actions, then archive the accepted packet when appropriate.

## Route by task and project

- Read `references/classification-and-escalation.md` and the matching section of `references/task-playbooks.md`.
- Compose the applicable profiles from `references/project-profiles.md`; never average away the strictest gate.
- Read `references/requirements-design-and-scope.md` before requirement confirmation or final design.
- Read `references/multi-agent-v2-orchestration.md` before any delegation.
- Read `references/test-strategy-and-coverage.md` for every change.
- Also read `references/test-environment-orchestration.md` when browsers, simulators, devices, VMs, containers, services, concurrency, or compatibility apply.
- Read `references/evidence-privacy-and-retention.md` before retaining logs, screenshots, traces, dumps, or user data.
- Read `references/audit-acceptance-and-delivery.md` before review, completion, commit, push, PR, release, or deployment.
- Read `references/flow-metrics.md` when evaluating or improving the workflow itself.

## Enforce dependency and preference gates

Before changing a manifest, lockfile, feature, plugin, tool, service, vendored source, or generated dependency metadata, follow the sibling Skill's dependency governance and write a dependency card from `templates/dependency-decision.md`. Obtain explicit approval for the named option and impact.

Run the diff-aware audit before final verification:

```bash
python3 <skill-root>/scripts/dev-flow.py audit-preferences \
  --root <repo> --packet <packet-dir>
```

Hooks provide additional warnings and narrow denials while a packet is active, but they never replace root inspection or evidence.

## Control Multi-Agent V2

Keep the root as the sole owner of user authority, requirement/design synthesis, scope, approvals, integration, finding adjudication, and final claims. Delegate only bounded independent work with a written brief and exclusive ownership. Default to no inherited conversation, require a report file, and independently verify child claims.

Use at most the task budget defined in `references/multi-agent-v2-orchestration.md`; never fill capacity merely because it exists. Stop drift, ownership overlap, unapproved dependencies, external/destructive action, or repeated failure. After three failed hypotheses or repair rounds, stop layering patches and return to evidence and architecture.

## Completion rule

Do not say complete, fixed, passing, compatible, secure, release-ready, committed, pushed, or deployed unless fresh evidence proves that exact claim. Report `PASSED`, `FAILED`, `FLAKY`, `BLOCKED`, `NOT RUN`, and `WAIVED` separately. Account for every changed file and state residual risks, environment gaps, hook trust/restart needs, and unexecuted live evaluations explicitly.
