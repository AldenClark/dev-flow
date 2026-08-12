# FFI ownership and error reference case

Fixture assumptions: A Rust library returns allocated buffers and typed failures through a stable C ABI consumed by deployed Swift and Kotlin clients. Some callers disagree about release ownership, nullable values occur on failure paths, and older client versions remain in use during the API evolution.
