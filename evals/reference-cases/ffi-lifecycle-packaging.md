# FFI lifecycle and packaging reference case

Fixture assumptions: Callbacks may arrive during app backgrounding, shutdown, and runtime replacement. Apple and Android packages cover multiple architectures, use generated bindings, and load native code through platform-specific paths. Simulator and emulator environments are available, while physical-device access may vary.
