# Change verification: dev-flow-1-1-2-agent-dispatch

[Tracked change manifest](./manifest.json)

## Executed local evidence

- VO-1/VO-2: 12 frozen public routing cases and 7 focused tests passed, including byte stability and exact P0-P6/PX mappings.
- VO-3/VO-4: receipt/template tokens, model-neutral roles, malformed/dangling/duplicate registry controls, role mismatch, independent-axis combination, PX acknowledgement, and downgrade acknowledgement passed.
- VO-5: 405 strict repository tests passed repeatedly, including the authority-converged source candidate; 39 public contracts, 117 methods, 73 sources, 38 risk models, 55 covered risks, 23 aliases, 13 Skills, 12 dispatch cases, plugin validation, knowledge validation, compileall, 424 JSON parses, protected-control doctor, and `git diff --check` all passed.
- Windows prevention: CI retains Ubuntu 24.04, macOS 15, and Windows 2025 on Python 3.11/3.14; dispatch runs under each runner's native shell with explicit UTF-8 and no POSIX fake executable, wording, or timing dependency.

## Post-commit delivery evidence

- VO-6: the pushed immutable commit must pass all six GitHub Actions cells.
- VO-7: two isolated 1.1.2 builds from that exact commit must be byte-identical and pass the release verifier.
- VO-8: local/remote main, annotated tag peel, installed plugin version/cache commit, and source/cache tree must agree.

The delivery results are recorded outside the self-referential source commit after its SHA exists. GitHub Release, production deployment, and model-population quality claims are outside this release.
