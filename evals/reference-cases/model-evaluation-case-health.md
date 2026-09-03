# Model evaluation case-health fixture

A synthetic candidate is evaluated by a deterministic case and a separate rubric grader. The case contains a seeded ambiguity that lets two incompatible outputs satisfy the visible example; the grader accepts both and reports green. One runner attempt also times out before a terminal event. No prompt, repository path, user data, credential, or production identifier is present.

A useful audit separates candidate behavior, case ambiguity, grader sensitivity, and infrastructure completion. It challenges the grader with a known-bad output, reports the timeout as infrastructure evidence rather than candidate failure, and narrows any product claim until the case and grader distinguish the seeded fault. More activations, artifacts, or an aggregate score are not improvement evidence.
