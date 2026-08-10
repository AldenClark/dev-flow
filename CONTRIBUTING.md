# Contributing to Dev Flow

Thank you for improving Dev Flow. Keep changes focused, evidence-backed, and safe for a public plugin repository.

## Engineering expectations

- Preserve idiomatic language conventions and the existing plugin, Skill, Hook, packet, and evaluator contracts.
- Inspect the affected code and tests before proposing architectural changes.
- Discuss new dependencies before adding them, including alternatives, maintenance cost, compatibility, and security impact.
- Keep generated artifacts, local runtime state, credentials, personal data, machine-specific paths, and sensitive logs out of commits.
- Update documentation and tests when behavior, public commands, configuration, or compatibility changes.

## Validate changes

Run the repository gates before opening a pull request:

```bash
python3 -m unittest discover -s evals -v
python3 evals/run_contract_checks.py
python3 skills/dev-flow/scripts/dev-flow.py check --plugin-root "$PWD"
python3 skills/dev-flow-maintainer/scripts/validate-suite.py
python3 -m compileall -q hooks skills evals
git diff --check
```

The CI matrix repeats the deterministic checks on Linux, macOS, and Windows with the supported Python versions.

## Pull requests

Describe the problem, approved scope, implementation, validation evidence, compatibility impact, and remaining risks. Keep unrelated cleanup separate. Do not claim a check passed unless it was actually executed against the submitted revision.

Use semantic versioning for public contract changes and update `CHANGELOG.md` when the change is user-visible.
