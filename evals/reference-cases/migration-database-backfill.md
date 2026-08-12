# Database backfill migration reference case

Fixture assumptions: a large table gains a non-null derived column while two application versions coexist and writes continue. A good first attempt uses expand-migrate-contract, inventories readers/writers/jobs, makes the backfill bounded and resumable, reconciles representative data, defines rollback and cleanup checkpoints, and blocks release while required production-like rehearsal evidence is missing.
