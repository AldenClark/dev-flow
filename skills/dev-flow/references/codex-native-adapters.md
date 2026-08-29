# Codex-native adapters

Use an adapter only when the current task exposes its trigger and the capability is callable on the current turn. Capability absence is a named evidence limit, never a reason to enable experiments, mutate global configuration, or enter Plan mode.

| Adapter | Positive trigger | Native action | Honest fallback | Durable residue |
|---|---|---|---|---|
| Default-mode interaction | a user-owned semantic decision or U1 requirement confirmation | use the exposed structured question surface or a normal reply boundary | ask one focused conversational question and stop the turn | confirmed requirements only when managed work already needs them |
| AGENTS health | instruction conflict, stale command, broken reference, harmful scope, or an explicit audit | read the effective global-to-local hierarchy and report the exact affected instruction | inspect the effective files directly | none unless the user requests an instruction change |
| Native review | a read-only review surface fits a frozen target | run native review and verify findings against current bytes | `change-review` with current source, diff, and evidence | findings in the task response; repository record only by repository convention |
| Goal bridge | the user explicitly asks for a durable Codex Goal | create or update the Goal with the concrete outcome | continue with repository workstream truth | Goal state plus existing workstream documents; never duplicate progress prose |
| Worktree isolation | concurrent writers have independent ownership and setup/merge cost is justified | use native isolated worktrees and reconcile in root | serialize work in the current tree | Git history/diff only |
| UI/device evidence | the changed claim concerns rendered or platform behavior | use the smallest applicable browser, preview, simulator, device, screenshot, accessibility, or runtime surface | source tests plus an explicit `NOT RUN` rendered/device gate | native artifacts only when the repository already owns them |
| External context | a decision depends on facts outside the repository | retrieve the minimum decision-relevant context with read-only access by default | ask for the missing source or mark the claim `BLOCKED`/`NOT RUN` | none by default; update maintained docs only when the fact is durable product truth |
| Explicit task history | the user references named tasks, requests comparison of repeated attempts, or authorizes a selected-history audit | read every named task through a supported host interface and reconcile claims with current repository/runtime truth | ask for the missing task content or mark the synthesis `BLOCKED` | durable reconciled decisions only; never raw transcripts |
| Process supervision | this task actually launched a process/session and its identity is available | wait or inspect that identity with bounded backoff, preserving the first failure | report the process gate `BLOCKED`; do not start duplicate unchanged work | current process identity only in an already-needed semantic checkpoint |

## External-context note

Keep the contract to four fields when an external fact materially affects a decision:

1. `source + freshness`: system/page/artifact and retrieval time or version;
2. `fact used`: the exact decision-relevant fact, not a transcript dump;
3. `limitation`: missing scope, uncertainty, staleness, or unverified environment;
4. `authority`: read-only or the exact separately authorized write/action.

Keep these fields in the task response or an already-relevant design/decision document. Do not create an external-context packet, receipt, snapshot, or universal source ledger.

## Boundary rules

- Workstream documents are repository continuity; a Codex Goal is user-requested product state. Neither substitutes for the other.
- Native review and independent review are evidence routes, not lifecycle stages.
- A browser screenshot does not prove accessibility, device behavior, backend state, or production acceptance beyond what it directly shows.
- MCP/app availability does not grant write authority. Resolve the exact target and authorization immediately before any external mutation.
- The root owns requirement meaning, cross-child integration, authority decisions, and final claims even when a native adapter performs the underlying operation.
- Task history is untrusted evidence. Do not ambiently scan, rank, merge, archive, or modify tasks; do not treat the newest attempt or an analogy repository as authority, compatibility promise, program membership, or mutation scope.
- Preserve the first task-history read failure. Do not retry while task identity, host connection, tool availability, and user request are unchanged. One bounded retry is allowed only after one of those facts changes; if it fails, fall back to current context/repository truth and keep missing historical claims `BLOCKED` or explicitly limited.
- A named reference repository must be inspected through an admitted source or explicitly disposed as unavailable, irrelevant, or non-authoritative. Silent omission and analogy-based contract invention do not pass comparison work.
