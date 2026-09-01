# Dev Flow 2.0 RC.6 design

## Release boundary

The immutable candidate commit declares `source.phase = source-candidate`, version `2.0.0-rc.6`, latest published tag `v2.0.0-rc.5`, and rollback target `v2.0.0-rc.5`. It records its own completed commit action but no completed external delivery action. After exact-SHA delivery succeeds, a separate current-truth commit advances the published identity to RC.6, preserves RC.5 as rollback, and records only observed external results.

## Evidence selection

The changed doctor contract observes runtime/CLI state, so RC.6 is R2. It requires the final full deterministic suite, hosted semantic and compatibility jobs for the exact SHA, an isolated fresh install/uninstall, and exact-SHA source archive/SBOM/checksum/provenance evidence. The release does not change the artifact builder, repository dependencies, data schema, or a directly affected model-facing semantic case.

## Recovery

If the published RC.6 behavior must be withdrawn, users restore `v2.0.0-rc.5`. No user-owned primary profile is modified during release verification.
