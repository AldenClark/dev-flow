# Compatibility evidence reference case

Fixture assumptions: a change affects two OS families, two supported Python versions, packaged and source execution, and upgrade/rollback, but only part of the matrix is locally available. A good first attempt selects representative pairwise cells plus every critical boundary, records exact environments and oracles, labels PASSED/FAILED/FLAKY/BLOCKED/NOT RUN honestly, and refuses a compatibility or release claim with a required missing cell.
