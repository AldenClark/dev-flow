# Risk-based test strategy

Use this reference when a change needs more than an obvious focused regression. It is a reasoning guide, not a required matrix.

## Start from the changed behavior

Begin with the current product intent, final implementation, affected callers and usage paths, and credible failures. An obvious focused regression needs no further classification. Use these views when they resolve a concrete uncertainty:

- **Black-box:** start outside the implementation. Turn the promised user/API/CLI/UI outcome, public contract, material failure, recovery, permission, persistence, and compatibility behavior into observable examples and counterexamples.
- **White-box:** inspect the final changed code. Find branches and compound conditions, states and transitions, boundaries and limits, typed and swallowed errors, ownership and resource lifetime, concurrency and ordering, cancellation, timeout, retry, idempotency, rollback, and cleanup.

Use the final code rather than a stale plan to find implementation risks, while keeping the user-visible meaning of the outcome. The two views may share a test; neither requires a separate test or report.

For a remaining blind spot, consider the relevant behavior, failure/recovery, state/data boundary, event order/compatibility, platform/integration, or oracle sensitivity. Use only the perspective that can expose a credible fault; do not scan every category or record unused ones.

## Put the oracle at the promise boundary

Choose the cheapest layer that still observes the promised behavior. For traffic or an external effect, identify the initiating actor and request/event at the real boundary; a successful response caused by background activity is a false green. Use a wrong-source negative control when this attribution is easy to fake:

- **Unit:** independent rules, transformations, invariants, limits, and state transitions.
- **Component:** a module with controlled collaborators when its public behavior is the promise.
- **Integration:** real storage, filesystem, network, process, queue, FFI, framework, or service interaction.
- **Contract/consumer:** public formats, protocol semantics, producer-consumer direction, or mixed versions.
- **End-to-end:** a representative user/system flow through the packaged runtime.
- **Platform/device:** behavior owned by an OS, browser engine, hardware, signing, permissions, lifecycle, or device-only API.
- **Non-functional:** performance, accessibility, security, recovery, resource use, and migration with a workload and correctness guard appropriate to the claim.

A mock can isolate logic but cannot prove the mocked boundary. A host test cannot prove a target runtime; a simulator or emulator cannot prove a physical-device property. Use the real boundary when the promise requires it, or preserve `BLOCKED`/`NOT RUN` rather than lowering the claim. Other environments do not become obligations merely because they exist.

Examples:

- A discount decision is usually best protected with table/property unit tests; repeating it through UI automation adds cost without better branch sensitivity.
- A transaction that promises atomic persistence needs a real database integration check; a repository mock proves only caller behavior.
- A notification lifecycle promised on a physical device needs that device path. Green host logic and emulator wiring remain useful narrower evidence, not substitutes.

## Find blind spots, not target scores

Use available line, branch, condition, or coverage-diff reports to investigate a concrete gap, rather than collecting them for every change. An uncovered changed error branch may matter, while generated glue may not merit a test. Branch coverage can still miss a compound condition's independent effect; use condition coverage or MC/DC only when that consequence justifies it.

For a non-trivial blind spot, read [coverage-techniques.md](coverage-techniques.md) and select a method that changes the input space, oracle, or failure sensitivity. Use mutation or seeded faults when the oracle is doubtful or a credible high-consequence failure warrants a challenge. AI authorship alone does not require fault injection. A surviving mutant matters only if it represents a credible fault; do not lock down implementation trivia to improve a mutation score.

## Execute and challenge

1. Run the smallest reproducer or focused changed test first; preserve its first failure.
2. For a doubtful or easy-to-fake oracle, or one protecting a credible high-consequence failure, reuse applicable sensitivity evidence or show that breaking its protected behavior fails the intended assertion: use a pre-fix result, negative fixture, bounded mutation, seeded fault or independent relation. Rechallenge when that boundary changes or sensitivity is doubtful, not merely because another run started.
3. If a perturbation was made, restore it and rerun the focused check. Run module and boundary checks affected by the repair, reusing valid results under [evidence freshness](evidence-contract.md#freshness-binding).
4. Inspect the final diff for changed outcomes, callers and usage paths that earlier checks no longer cover. Rerun the affected checks; cumulative PR breadth alone does not set an intermediate repair's rerun scope. Investigate uncertain impact when it could change the decision, without enumerating every input or artifact.
5. Add broader regression, compatibility, or environment waves only where blast radius, delivery, or consequence requires them.

For a target-environment promise, check the applicable artifact, installed/deployed target, effective configuration/data and intended user flow or effect, including recovery when the promise depends on it. Read relevant effective state rather than trusting a source file or build command. An artifact or configuration change requires rechecking the affected downstream behavior. Distinguish host, simulator/emulator, device, hosted and production results when reporting them.

Normal completion owes its result and resource guarantees; timeout/cancellation/recovery-specific proof is required when that path executes, not as a condition of an untriggered path's success. Material failure paths still need their own coverage. Do not skip a cheap focused check because a broad suite will run later. If retries disagree, record `FLAKY`; a retry is evidence about instability, not permission to keep the green attempt.

## Spend by consequence and stop by value

- **Core:** principal success behavior, material failure/recovery, affected contracts and consumers, regressions, and credible high-consequence failures connected to the change.
- **Extended:** configurations, affected platforms, historical defects and abnormal paths when they add meaningful fault sensitivity.
- **Stop:** omit further checks when they cannot change a material correctness or delivery decision.

A serious failure needs a credible mechanism connected to this change before it becomes a verification obligation; severity alone is insufficient. A credible rare failure with serious consequences may still need a focused check. User-requested broad exploration, full reruns or repeated stability observations remain part of the outcome.

For routine work, consume the native result and report the command and material limit. No per-check risk rationale, full input record or proof bundle is needed. Write a matrix only when several required environments, compatibility directions or owners need coordination. Long-lived project strategy belongs in the repository's existing testing owner when it will be reused.

## Fresh claims

- `PASSED`: fresh evidence meets the oracle.
- `FAILED`: execution contradicts it.
- `FLAKY`: materially identical attempts disagree.
- `BLOCKED`: a prerequisite prevented execution.
- `NOT RUN`: not executed, with reason.
- `WAIVED`: an authorized omission with owner/rationale; never a pass.

Include environment, artifact or compatibility detail only when it distinguishes what the result proves. One environment, version direction or fallback proves only itself. A required unobserved path stays `BLOCKED` or `NOT RUN`; unrelated environments do not create pending work.
