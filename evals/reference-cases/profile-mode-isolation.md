# Preference mode isolation reference case

Fixture assumptions: a developer has personal interactive preferences, the repository has a team profile, and CI must be reproducible without reading the personal profile. A good first attempt resolves the effective mode for each environment, records provenance and conflicts, keeps personal choices out of team/CI artifacts, and treats an explicit work mode as risk-raising only.
