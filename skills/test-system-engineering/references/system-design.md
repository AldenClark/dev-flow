# Sustainable native test systems

Use this reference when the missing capability is project-level feedback rather than one broken test. Start from the promises and risks the project actually has; do not prebuild every layer or copy a standard lane matrix.

## New project: minimum sustainable skeleton

Establish the smallest loop that can grow with real slices:

1. Keep one project-native command that developers and automation can run identically.
2. Add a fast failing test at the unit/component layer for independent logic or the first meaningful rule.
3. Add one black-box slice through the first real critical boundary—not a mock of that boundary—with a product-facing outcome oracle.
4. Put both into the smallest CI feedback path—a minimal lane that detects discovery failure and returns actionable output.
5. Isolate fixtures and make teardown, seeds, prerequisites, and unsupported environments explicit.

If the first promise is platform-owned, the boundary slice belongs on that platform or device. A host substitute may help develop lower layers but leaves the platform path `NOT RUN`. Do not add empty suites, speculative compatibility matrices, or a universal wrapper merely to look complete.

## Mature project: strengthen what exists

Inventory only what affects the current gap:

- native commands, collected tests, filters/tags/shards, CI jobs, and feedback time;
- which layers protect which behaviors and real boundaries;
- fixtures, data, clocks, randomness, networks, processes, caches, retries, skips, quarantine, and teardown;
- repeated or slow coverage, weak assertions, mock substitutions, missing platforms, and accepted gaps.

Extend the existing runner and CI convention whenever it can carry the new oracle. Consolidate duplicate fixtures or lanes only when the current change proves the duplication harmful. Build a parallel harness only after evidence shows the native system cannot express a required test and the replacement cost is justified.

## Feedback roles, not prescribed lane names

Partition checks by feedback need and resource cost. A project may call these Focused, PR, Nightly, Release, pre-submit/post-submit, or something else:

- the fastest role protects edited logic and immediate regressions;
- the integration role protects affected real boundaries and consumers;
- slower roles may cover broad compatibility, randomized/fuzz exploration, performance, soak, devices, or packaged behavior;
- a delivery-oriented role, when the project has one, protects exact candidate identity and required target environments.

Every role states what it protects, how selection is proven, what resources it owns, how failures are interpreted, and which evidence remains outside it. Do not duplicate the same tests across roles without a feedback or environment reason. A label never proves a lane ran.

## Coverage and technique decisions

Use `verification` to derive black-box and white-box obligations and choose the actual layers. The test system makes those choices repeatable and trustworthy:

- expose line/branch/condition and changed-code coverage only as blind-spot feedback;
- keep constrained pairwise/t-way generators and model/property/fuzz seeds reproducible;
- target changed-code mutation or seeded faults at material rules instead of chasing whole-repository scores;
- retain differential/metamorphic/reference-model oracles where direct expected values are weak;
- provide controlled fault injection, replay, clocks, schedules, and recovery fixtures where failure lifecycle matters.

For AI-authored tests, require an oracle source independent of the code-generation assumption and run at least one material seeded fault through normal discovery and selection. Do not reward volume, snapshots, or mock expectations that cannot observe the public promise.

## Fixtures, data, and resources

Prefer synthetic minimized data with explicit ownership. Give parallel cases separate database/schema, filesystem, port, process, device/simulator, browser profile, cache, clock, and random seed, or serialize the resource when isolation is not proven. Make setup/readiness and teardown observable on success and failure.

Cache keys include relevant source, configuration, toolchain, generated inputs, and environment identity. Retry policy preserves the first failure and surfaces disagreement as flakiness. Skips and quarantines have a reason, owner, and removal condition when they suppress a claimed path.

## Durable strategy and stopping

Record cross-layer responsibilities, environment/resource decisions, feedback roles, fixture contracts, and accepted material gaps in the repository's existing testing owner when future contributors will reuse them. If no owner exists, create the smallest discoverable entry; do not require one file name or repeat a per-change matrix.

Stop once the observed feedback gap is closed, the target fault is caught through the native path, and maintenance cost is proportionate. Low-probability, low-consequence, high-cost fringe expansion stops; rare high-consequence security, privacy, financial, corruption, safety, or irreversible risks stay in core scope.
