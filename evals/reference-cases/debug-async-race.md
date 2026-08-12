# Async race debugging reference case

Fixture assumptions: after runtime replacement, an old asynchronous callback can publish into the new generation during cancellation. A good first attempt reconstructs the causal timeline and ownership generations, creates a deterministic interleaving reproducer, fixes the ownership/publication boundary, verifies quiescence and shutdown, and reruns nearby ordinary callback behavior.
