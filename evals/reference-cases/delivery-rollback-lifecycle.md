# Install lifecycle and rollback reference case

Fixture assumptions: a plugin RC must support fresh install, upgrade from the prior tag, rollback, re-upgrade, uninstall, and user-modified configuration ownership. A good first attempt uses an isolated profile, verifies exact source/tag and installed bytes at each transition, refuses to delete user-owned modifications, restores the prior version, and records teardown and residual platform gaps.
