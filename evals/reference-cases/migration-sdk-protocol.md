# SDK protocol migration reference case

Fixture assumptions: a versioned public protocol is used by old and new mobile SDKs against old and new servers, with generated clients and unknown fields. A good first attempt defines all compatibility directions, staged rollout and coexistence, version/unknown-field behavior, rollback and deprecation telemetry, representative golden tests, and cleanup only after the supported-client window closes.
