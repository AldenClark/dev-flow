# Forward-test case: existing project bug fix

Use `$dev-flow` on an existing Rust plus React repository and route only the applicable focused capabilities.

The user reports that reconnecting a WebSocket can duplicate notifications. The likely area spans a Tokio connection task, an in-memory cache, and a React query invalidation hook. A child agent suggests adding Moka and another suggests adding an npm deduplication package.

Diagnose and plan the fix. Do not receive an expected answer or hidden finding list.
