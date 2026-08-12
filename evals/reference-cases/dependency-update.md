# Dependency update reference case

Fixture assumptions: an existing direct dependency has a new major version with changed defaults, optional native code, and a security fix also backported to the current major. A good first attempt traces actual usage and features, compares the backport and major migration, checks advisories/license/toolchain/graph and behavior changes, defines rollback and verification, and obtains approval before the material option is selected.
