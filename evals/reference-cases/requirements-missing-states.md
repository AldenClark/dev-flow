# Missing state and error semantics case

The product requirement defines the happy-path outcome but omits cancellation, retry, partial failure, authorization failure, and empty states. The repository contains an existing state machine, analogous flows, tests, and UI behavior that may establish protected defaults, but material product choices can remain after inspection.

A good first attempt inspects those sources first, enumerates the missing states and transitions, preserves discovered behavior as evidence-backed defaults, and separates repository facts from user-owned semantics. It records only surviving material ambiguities and asks at most three consolidated questions with recommendations, alternatives, impact, safe defaults, and blocked scope.
