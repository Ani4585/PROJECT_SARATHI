# Changelog

All notable PROJECT SARATHI framework changes are documented here.

## [0.7.0] - 2026-07-29

### Added

- Extensible developer command abstraction.
- Immutable shared command execution context.
- Command registry with deterministic iteration.
- Duplicate-command and missing-command protection.
- Reusable script-backed command implementation.
- Native test, compilation, and version commands.
- Composite fail-fast verification command.
- Explicit built-in command registration.
- Standard CLI application factory.
- Focused command, registry, application, built-in, and entry-point tests.
- End-to-end validation for all eight developer commands.

### Changed

- Replaced the conditional `sarathi.py` implementation with a thin
  executable composition root.
- Routed established developer commands through reusable command
  objects.
- Preserved the existing command names, help descriptions, script
  mappings, output behavior, and exit-code propagation.
- Expanded the complete regression suite to 63 tests.

### Verification

- Focused CLI suite: 47 passed.
- Complete regression suite: 63 passed.
- All eight real CLI commands passed.
- Compilation passed.
- Composite repository verification passed.

## [0.6.2] - 2026-07-28

### Added

- Reusable repository tooling utilities.
- Repository statistics reporting.
- Project and Git status reporting.
- Automated health checks.
- Release-gate automation.
- Authoritative framework-version tooling.
- Initial unified `sarathi.py` developer interface.
- One-command repository verification.

### Changed

- Standardized milestone verification through:

  ```powershell
  python sarathi.py verify
  ```

## [0.6.1] - 2026-07-28

### Added

- Dependency Validator.
- Dependency Planner.
- Dependency Graph integration.
- Graph Recorder enhancements.
- Release Gate documentation.
- Live Status Dashboard.

### Changed

- Improved dependency graph construction.
- ServiceContainer now manages dependency planning.

### Fixed

- Validator integration with CycleDetector.
- Dependency graph recording consistency.
