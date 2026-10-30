# Optional test coordination

> Retained template; ordinary work uses native test results directly and needs no matrix.

Use a table only when several required environments or owners need coordination. Include only checks needed for the changed behavior; there is no required technique inventory or per-view N/A.

| Behavior or risk | Native check and environment | Result or required gap |
|---|---|---|
| <affected behavior> | <command and relevant target> | <result and material limit> |

Keep a first failure when it explains an unresolved issue. Use a pre-fix failure or negative control when oracle sensitivity is doubtful or the consequence warrants it. Retain existing proof while applicable; report unrelated environments only if they affect the requested outcome.
