# Dev Flow 2.0 RC.6 decisions

## D1: Freeze a distinct candidate before delivery

- Decision: RC.6 uses a new candidate version and workstream while `published.latest_rc` remains RC.5 until tag, publication, and isolated installation have been observed.
- Consequence: source candidate bytes cannot inherit RC.5 delivery evidence.

## D2: Select the runtime release tier proportionately

- Decision: classify RC.6 as R2 because doctor now runs an explicit CLI registry observation and its public diagnostic contract changed.
- Consequence: require final local suite, hosted compatibility, exact-SHA artifact evidence, and isolated fresh install/uninstall, without inventing a model-spend or artifact-builder gate.
