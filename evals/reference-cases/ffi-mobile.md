# FFI mobile reference case

Fixture assumptions: A Rust core exposes a callback API through generated bindings to deployed Swift and Kotlin consumers. Old consumer versions remain supported while the callback API evolves. Both mobile packages ship native artifacts, and callback delivery can overlap cancellation, shutdown, and runtime replacement.
