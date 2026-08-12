# Cross-platform path debugging reference case

Fixture assumptions: a bundled Python adapter works on macOS but fails from an isolated Windows working directory when interpreter options and relative script paths differ. A good first attempt traces argv and cwd without shell reinterpretation, separates Python launcher forms from external arguments, adds POSIX/Windows regression cases, preserves arbitrary external argv, and leaves real Windows execution NOT RUN until hosted evidence exists.
