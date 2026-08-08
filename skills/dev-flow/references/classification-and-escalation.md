# Classification and escalation

Classify along four independent axes: task playbook, project profile, risk modifiers, and delivery profile. Never infer process solely from diff size.

## Task playbooks

- `micro`: local, obvious, one coherent edit, no public contract, dependency, compatibility, or risky behavior.
- `routine`: normal feature or maintenance work with understood architecture and bounded impact.
- `bugfix`: incorrect behavior requiring reproduction and root-cause evidence.
- `large-feature`: new capability spanning components, contracts, state, or UX.
- `large-refactor`: behavior-preserving structural change across ownership boundaries.
- `migration`: toolchain, dependency, API, protocol, schema, storage, platform, or architecture transition.
- `security`: authentication, authorization, secrets, cryptography, untrusted input, sandbox, permissions, or vulnerability remediation.
- `performance`: latency, throughput, memory, CPU, size, startup, energy, or scalability work requiring measurement.
- `release-hotfix`: publication, production recovery, release hardening, or time-critical risk containment.

## Risk modifiers

Add every applicable modifier:

- public API, wire protocol, persisted data, schema, or generated contract;
- authentication, authorization, secret, privacy, or untrusted input;
- unsafe, FFI, ABI, native packaging, signing, entitlement, or platform lifecycle;
- concurrency, cancellation, ordering, idempotency, backpressure, or distributed state;
- data deletion, migration, rollback, one-way conversion, or recovery;
- browser, simulator, device, OS, architecture, toolchain, or version compatibility;
- performance/SLO, memory, battery, startup, binary/bundle size, or resource limits;
- deployment, production configuration, CI/CD, release, or external writes;
- unfamiliar subsystem, weak tests, flaky baseline, incomplete reproduction, or large blast radius.

## Escalation rules

Escalate at least one playbook level when:

- a micro/routine task acquires a new dependency or public contract;
- implementation crosses a second component or repository boundary;
- current behavior cannot be reproduced or explained;
- a test exposes an undocumented compatibility or data contract;
- one agent's task requires overlapping writes with another;
- generated files, lockfiles, migrations, release metadata, or signing change unexpectedly;
- three hypotheses or repair attempts fail;
- the user changes the requirement or approved scope materially.

Security, migration, release, protocol, persisted-data, and FFI modifiers cannot be downgraded to micro merely because the diff is small.

## Failure breaker

After three failed hypotheses, fixes, or review-repair rounds:

1. Stop layering changes.
2. Revert only the current experimental slice if safe and recoverable.
3. Re-read original evidence, recent changes, and architectural assumptions.
4. Decide whether the fault is reproduction, model, architecture, environment, or test oracle.
5. Present the new evidence and architectural question to the user before continuing.
