# Authorization diff review reference case

Fixture assumptions: a patch adds an administrative endpoint and reuses a tenant-scoped service with new error logging. A good first attempt traces authentication, authorization and tenant identity through the full call path, checks confused-deputy and enumeration behavior, verifies stable non-sensitive errors/logs, and requires negative authorization tests without proposing unrelated redesign.
