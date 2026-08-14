## Confidential data handling

When a task may involve credentials, personal data, production/customer information, internal documents, or external disclosure:

1. Avoid reading raw sensitive values when a variable, secret reference, path, schema, or record ID is sufficient.
2. Prefer local computation; expose only the smallest redacted or pseudonymized result needed for reasoning.
3. Use `$company-data-security` for the detailed surface-aware workflow.
4. Never echo, copy, log, patch, or explain a discovered credential value.
5. Keep external send/post/update actions as drafts until the exact destination and minimized payload are confirmed.
6. Do not bypass a data-security Hook. Report unsupported tool paths and live trust/configuration as limitations rather than claiming protection.
