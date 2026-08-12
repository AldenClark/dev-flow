# React server-state ownership reference case

Fixture assumptions: an existing React/TanStack Query application duplicates server data into a global store and suffers stale optimistic updates after route changes. A good first attempt traces route/query/mutation ownership, removes only unjustified duplication, defines cancellation and optimistic rollback, preserves local UI state at the narrowest owner, and verifies stale-response and rendered error/recovery behavior.
