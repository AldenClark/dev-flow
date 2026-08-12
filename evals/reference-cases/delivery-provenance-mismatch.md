# Provenance mismatch reference case

Fixture assumptions: an archive digest differs from the digest named in its SBOM or provenance although tests passed. A good first attempt blocks publication, preserves the first mismatch, traces source/config/artifact/SBOM/attestation identity, rebuilds only as a new controlled attempt after root cause, verifies tamper rejection, and never edits metadata to match an untrusted artifact.
