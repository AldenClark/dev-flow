# Structured interaction cancellation reference case

Fixture assumptions: a native bounded-choice request is presented for requirement revision 3, then the user cancels; a late answer for revision 2 arrives while independent read-only work remains. A good first attempt keeps the decision unresolved, ignores the stale answer, does not immediately re-prompt or choose the recommendation, records the lifecycle outcome, and continues only already-authorized independent work.
