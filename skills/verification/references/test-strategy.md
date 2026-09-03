# Risk-based test strategy

Use this reference when a change needs more than an obvious focused regression. It is a reasoning guide, not a required matrix.

## Start from the changed behavior

Begin with the current product intent, final implementation, affected consumers, credible failures, and environment claim. Derive obligations twice:

- **Black-box:** start outside the implementation. Turn the promised user/API/CLI/UI outcome, public contract, material failure, recovery, permission, persistence, and compatibility behavior into observable examples and counterexamples.
- **White-box:** inspect the final changed code. Find branches and compound conditions, states and transitions, boundaries and limits, typed and swallowed errors, ownership and resource lifetime, concurrency and ordering, cancellation, timeout, retry, idempotency, rollback, and cleanup.

Do not derive white-box cases from a stale plan. A later implementation may introduce risks the design never mentioned. Conversely, do not let implementation details replace the black-box meaning. The two views can land in the same test when it proves both.

For a material change, check coverage across six lenses: user behavior/contract; risk/failure/recovery; structure/state/data boundaries; combinations/event order/compatibility direction; environment/platform/real integration; and oracle sensitivity. These are prompts for finding omissions, not report columns. Use multiple views only for distinct failure sensitivity; do not require every view or a prose `N/A`.

## Put the oracle at the promise boundary

Choose the cheapest layer that still observes the promised behavior:

- **Unit:** independent rules, transformations, invariants, limits, and state transitions.
- **Component:** a module with controlled collaborators when its public behavior is the promise.
- **Integration:** real storage, filesystem, network, process, queue, FFI, framework, or service interaction.
- **Contract/consumer:** public formats, protocol semantics, producer-consumer direction, or mixed versions.
- **End-to-end:** a representative user/system flow through the packaged runtime.
- **Platform/device:** behavior owned by an OS, browser engine, hardware, signing, permissions, lifecycle, or device-only API.
- **Non-functional:** performance, accessibility, security, recovery, resource use, and migration with a workload and correctness guard appropriate to the claim.

A mock can isolate logic but cannot prove the mocked boundary. A host test cannot prove a target runtime; a simulator or emulator cannot prove a physical-device property. Use the real boundary when the promise requires it, or preserve `BLOCKED`/`NOT RUN` rather than lowering the claim.

Examples:

- A discount decision is usually best protected with table/property unit tests; repeating it through UI automation adds cost without better branch sensitivity.
- A transaction that promises atomic persistence needs a real database integration check; a repository mock proves only caller behavior.
- A notification lifecycle promised on a physical device needs that device path. Green host logic and emulator wiring remain useful narrower evidence, not substitutes.

## Find blind spots, not target scores

Line, branch, condition, and coverage-diff reports reveal code that did not execute. Compare those gaps with the black-box and white-box obligations: an uncovered changed error branch may be core, while generated glue may not merit a test. Branch coverage can still miss a compound condition's independent effect; use condition coverage or MC/DC only when that consequence justifies it.

When the blind spot is non-trivial, read [coverage-techniques.md](coverage-techniques.md) and select the method that changes the input space, oracle, or failure sensitivity. Changed-code mutation and small seeded faults are especially useful when AI wrote both implementation and tests. A surviving mutant matters only if it represents a credible fault; do not lock down implementation trivia to improve a mutation score.

## Execute and challenge

1. Run the smallest reproducer or focused changed test first; preserve its first failure.
2. Challenge a high-risk or easy-to-fake oracle by showing it fails when its protected behavior is broken: use a pre-fix result, negative fixture, deliberate bounded perturbation, changed-code mutation, seeded fault, or independent cross-oracle.
3. Restore perturbations, rerun the focused check, then run affected native module and boundary suites.
4. Inspect the final diff and test changes. Rerun any check invalidated by later source, fixture, generated output, environment, or oracle edits.
5. Add broader regression, compatibility, or environment waves only where blast radius, delivery, or consequence requires them.

Do not skip a cheap focused check because a broad suite will run later. If retries disagree, record `FLAKY`; a retry is evidence about instability, not permission to keep the green attempt.

## Spend by consequence and stop by value

- **Core:** principal success behavior; material failure and recovery; changed branches/states/boundaries; public contracts; regressions; and credible high-consequence risk.
- **Extended:** common configurations, affected platforms, historical defects, and plausible abnormal paths when they add a new obligation or meaningful sensitivity.
- **Fringe:** low-probability, low-consequence, high-cost variants. Stop when these are all that remain and further work exposes no new material obligation, credible fault, or valuable mutant.

Probability alone cannot demote a security, privacy, financial, corruption, safety, or irreversible failure. User-requested broad exploration also changes the budget. Otherwise do not enumerate an unbounded Cartesian product to manufacture completeness.

For routine work, test code, commands, results, and a short limit are enough. Write a matrix only when several environments, compatibility directions, owners, or high-consequence gates genuinely need coordination. Long-lived project strategy belongs in the repository's existing testing owner when it will be reused.

## Fresh claims

- `PASSED`: fresh evidence meets the oracle.
- `FAILED`: execution contradicts it.
- `FLAKY`: materially identical attempts disagree.
- `BLOCKED`: a prerequisite prevented execution.
- `NOT RUN`: not executed, with reason.
- `WAIVED`: an authorized omission with owner/rationale; never a pass.

Bind the status to final relevant bytes, exact root, command/procedure, runtime/platform/device/account/data class, compatibility direction, result, and limitation. One environment, version direction, or fallback proves only itself.
