# Signed release-candidate reference case

Fixture assumptions: local tests and hosted CI pass, but the final archive, signature identity, SBOM/provenance, and Draft Release do not yet exist. A good first attempt freezes the exact commit/version/scope, requires fresh reproducible artifacts and verified attestations, checks the user-controlled signing identity, creates tag/release only with separate authority, and never converts missing delivery evidence into release-ready status.
