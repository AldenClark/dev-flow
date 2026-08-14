# Verification for confidentiality-controls-v1

[Manifest](./manifest.json)

## Repository acceptance

Repository verification passed on 2026-08-14. The final dedicated DLP run passed 26 tests in 1.275 seconds, and the final repository discovery run passed 368 tests in 74.542 seconds. The 39-contract checker, plugin checker, 13-Skill maintainer validator, Skill validator, compileall, all 97 repository JSON parses, knowledge validator, diff whitespace check, and exact requirements/design authority comparisons passed. Doctor reported `valid_with_manual_gates`, zero required failures, five `not_observed` live gates, and a passing installed-byte Codex synthetic canary.

## Evidence model

Black-box evidence observes the Skill/template contract, three Hook subprocess interfaces, doctor exit/JSON states, and repository public validators. White-box evidence observes rule/exclusion branches, traversal and caps, normalized/encoded input, pseudonym stability, Hook fail-safe branches, semantic drift, and no-raw-value invariants. Adversarial cases supplement rather than replace both views.

The red review exercised encoded and normalized secret forms, nested values and keys, credential paths, malformed and oversized Hook events, raw-value leak oracles, semantic and byte tampering, false-positive decoys, and lifecycle compatibility. The blue review traced AC-1 through AC-12 to the final files and independent oracles. No critical, high, or blocking repository finding remains.

## Residual limits

The detector is a bounded high-confidence V1 and cannot recognize every secret or deliberate evasion. Its baseline is not a signed external trust anchor, so a privileged actor who changes both code and baseline can evade byte-only comparison; semantic checks and installed-byte canaries reduce but do not eliminate that risk. Network egress, endpoint policy, MCP/connector administration, and enterprise immutability remain separate controls. These are accepted V1 boundaries, not failed repository tests.

## External gates

Repository and isolated subprocess evidence cannot prove plugin installation, current Hook trust, fresh-session activation, Work/ordinary Chat instruction alignment, enterprise immutability, or endpoint/network egress enforcement. Those gates remain `NOT RUN` under current authority.

[Current Dev Flow governance](../../project/dev-flow-governance.md)
