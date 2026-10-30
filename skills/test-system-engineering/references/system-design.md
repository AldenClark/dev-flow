# Sustainable native test systems

Use this reference when the missing capability is project-level feedback rather than one broken test. Start from the promises and risks the project actually has; do not prebuild every layer or copy a standard lane matrix. For a task already in progress, identify which missing start, health, focused-test, real-boundary, targeted-log, or recovery signal prevents a decision and repair that entry in the project's own commands and conventions. Keep the first failure and stop once that causal gap is closed.

## New project: minimum sustainable skeleton

Start with a project-native command and the smallest check that observes the first meaningful rule or outcome. Add a real-boundary slice when that boundary owns the promise, and CI when shared feedback is needed. Isolate the fixtures and resources actually used; do not require separate unit, black-box and CI setup before a small task can finish.

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

For a traffic or external-effect oracle, observe the initiating actor/source and effect at the promised boundary. A response or log line from background traffic can make a weak check green while the user's flow never ran. Use a wrong-source challenge when attribution is doubtful or easy to fake; reuse applicable negative evidence.

Describe feedback roles only where contributors need that coordination. Do not duplicate the same tests across roles without a feedback or environment reason. A label never proves a lane ran.

## Coverage and technique decisions

Use `verification` to choose checks for the concrete gap. Add only the native capability needed to make those checks repeatable and trustworthy:

- expose line/branch/condition and changed-code coverage only as blind-spot feedback;
- keep constrained pairwise/t-way generators and model/property/fuzz seeds reproducible;
- target changed-code mutation or seeded faults at material rules instead of chasing whole-repository scores;
- retain differential/metamorphic/reference-model oracles where direct expected values are weak;
- provide controlled fault injection, replay, clocks, schedules, and recovery fixtures where failure lifecycle matters.

For AI-authored tests, check assertions against the public promise or another source independent of the code-generation assumption. Use a seeded fault only when sensitivity is doubtful or a credible high-consequence failure warrants a challenge. Do not reward volume, snapshots or mock expectations that cannot observe the public promise.

## Fixtures, data, and resources

Prefer synthetic minimized data with explicit ownership. Give parallel cases separate database/schema, filesystem, port, process, device/simulator, browser profile, cache, clock, and random seed, or serialize the resource when isolation is not proven. Make setup/readiness and teardown observable on success and failure.

Cache keys include relevant source, configuration, toolchain, generated inputs, and environment identity. Retry policy preserves the first failure and surfaces disagreement as flakiness. Skips and quarantines have a reason, owner, and removal condition when they suppress a claimed path.

## Durable strategy and stopping

Record cross-layer responsibilities, environment/resource decisions, feedback roles, fixture contracts, and accepted material gaps in the repository's existing testing owner when future contributors will reuse them. If no owner exists, create the smallest discoverable entry; do not require one file name or repeat a per-change matrix.

Stop once the observed feedback gap is closed and the native result supports the decision. A sensitivity repair must catch the target fault through the native path. Further harness work needs a remaining material gap; severity alone does not make an imagined failure part of the task. A credible high-consequence mechanism connected to the change may still justify a focused check even when rare.
