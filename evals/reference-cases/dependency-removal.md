# Dependency removal reference case

Fixture assumptions: a direct dependency appears unused but may be activated by a feature, build script, generated file, or downstream example. A good first attempt proves references and feature paths, removes manifest usage through the package manager rather than editing a lockfile, checks default/minimal/all features and representative consumers, and records cleanup and rollback.
