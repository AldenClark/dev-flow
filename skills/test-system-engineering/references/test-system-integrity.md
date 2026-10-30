# Test-system integrity obligations

Investigate only the failure mode under suspicion. Native results normally suffice; this reference is not a six-part audit or completion record.

## Discovery

When discovery is unclear or suspect, inspect the intended test's identity in native collection or execution output. Enumerate tests only if that resolves the uncertainty. Zero discovery, silent import failure, disabled suites, conditional registration, naming mismatch, missing generated tests and skipped modules are distinct from a passing test.

## Selection

When selection is suspect, check the relevant filter, path, scheme, tag, flag, variant, shard, exclusion or retry rule against the intended target. Check full-set shard coverage only when that is the claim. Use an excluded negative only when it can reveal a credible selection fault that ordinary output would miss.

## Sensitivity

When sensitivity is doubtful or a credible high-consequence failure warrants a challenge, use a pre-fix result, negative fixture, safe mutation, seeded fault, property violation or independent oracle. Confirm failure at the target assertion rather than setup or unrelated infrastructure, then restore perturbations and rerun the affected check. Reuse applicable sensitivity evidence; do not repeat a challenge on every run.

For an external effect needing an attribution challenge, reuse applicable wrong-source evidence or seed an event from the wrong actor/source or request. The intended user-flow oracle must fail even if a generic health check, network packet, log line, or mock invocation exists. Show the intended actor produces the promised effect at the real boundary; a reused negative control does not replace affected product checks.

## Isolation

Trace the fixture, clock, randomness, cache, resource or ordering that could explain the suspected leak between cases or runs. Use order reversal or a fresh cache when it distinguishes pollution. A shared resource needs isolation or serialization, and production/user data must not become a fixture.

## Interpretation

Read native outcomes accurately: runner launch or exit zero is not an assertion pass; skips, expected failures, quarantine, retries, timeout, crash, cancellation and infrastructure errors retain their meanings. Investigate retries or caches when they may have hidden a failure or reused an inapplicable result.

Apply [evidence freshness](../../verification/references/evidence-contract.md#freshness-binding) when a subsequent change can affect the result, and repeat the smallest affected native check. Ordinary work needs no full input or artifact inventory. Preserve the first failure and distinguish a repaired observation from a repaired product.

## Representativeness

Limit the result to what ran, adding environment or compatibility detail when it distinguishes the claim. A mock proves the caller around the mock; host tests, simulators and emulators prove their own environments. A required unobserved target remains `BLOCKED` or `NOT RUN`; unrelated environments create no obligation.

## AI self-confirmation audit

When AI produced both implementation and tests, check that assertions follow the user-visible/public contract or another independent source rather than repeating the implementation's assumption. A retained real example, property, reference model or differential relation may suffice. AI authorship does not itself require a seeded fault or separate audit record.

Inspect tests for assertions on setup, mocks, call counts, snapshots, or internal representation that can stay green while the promised outcome is wrong. A useful seeded fault changes a material branch, state write, error, boundary call, cleanup, or environment attribution and must make the intended native gate fail.

Return the affected native result and material limits to `verification`. Include a negative-control result if one was needed; do not create six dispositions or imply that harness repair proves product correctness.
