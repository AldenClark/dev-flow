# Process timeout debugging reference case

Fixture assumptions: a test runner times out and occasionally leaves a child process; increasing the timeout hides the symptom. A good first attempt preserves the first failure, traces parent/child ownership and blocked I/O, forms one causal hypothesis, runs the smallest discriminating experiment, proves descendant teardown and bounded output, and avoids stacking retries or timeout increases as a fix.
