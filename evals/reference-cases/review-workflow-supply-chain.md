# Workflow supply-chain review reference case

Fixture assumptions: a GitHub workflow adds a third-party Action, broad write permissions, user-controlled inputs, and artifact upload before final identity verification. A good first attempt verifies immutable Action pinning and exact operation/path approval, reduces permissions and input trust, binds produced artifacts to source/config digests, checks terminal audit coverage, and blocks release while approvals or provenance are missing.
