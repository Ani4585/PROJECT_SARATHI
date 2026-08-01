# Changelog

All notable PROJECT SARATHI framework changes are documented here.

## [1.0.0] - 2026-08-01

### Added

- Integrated platform kernel and composition builder.
- DI registration for events, messages, modules, jobs, metrics, and the kernel.
- Shared module and application lifecycle coordination.
- Guarded event, message, and background-job operations.
- Automatic operational metrics for integrated kernel activity.
- Immutable kernel health snapshots.
- Expanded Framework Doctor import coverage for every M13-M20 package.

### Verification

- M13-M20 focused suite: 99 passed.
- Complete suite: 207 tests.
- Sandbox-compatible regression run: 205 passed, 2 Python 3.14 checks deferred.

## [0.14.0] - 2026-08-01

### Added

- Thread-safe counters, gauges, and distribution summaries.
- Deterministic metric label normalization and series identity.
- Immutable sorted metric snapshots.
- Timed context blocks with an injectable monotonic clock.
- Duration recording for successful and failed operations.

### Verification

- Focused metrics suite: 12 passed.

## [0.13.0] - 2026-08-01

### Added

- Immutable background job definitions and explicit runtime states.
- Injected scheduler clock for deterministic operation and tests.
- Stable due-job ordering by scheduled time and insertion sequence.
- Cancellation, result capture, and failure isolation.
- Bounded retry attempts with declared retry delays.
- Structured execution records for every attempt.

### Verification

- Focused background job suite: 11 passed.

## [0.12.0] - 2026-08-01

### Added

- Generic repository and unit-of-work ports.
- Thread-safe in-memory repository adapter.
- Duplicate and missing entity protection.
- Deep repository snapshots and restoration.
- Multi-repository in-memory transaction coordination.
- Explicit commit and automatic exception rollback semantics.

### Verification

- Focused persistence suite: 12 passed.

## [0.11.0] - 2026-08-01

### Added

- Explicit platform module contract and no-op base module.
- Unique module registry with dependency validation.
- Stable topological module planning and cycle detection.
- Dependency-ordered configuration and startup.
- Reverse-order shutdown and startup rollback.
- Structured module lifecycle errors and runtime state.

### Verification

- Focused module runtime suite: 10 passed.

## [0.10.0] - 2026-08-01

### Added

- Immutable command and query message contracts.
- One-handler-per-message typed registry.
- Function and object-style message handlers.
- Ordered application middleware pipelines.
- Middleware short-circuiting and result transformation support.
- Structured missing and duplicate handler errors.

### Verification

- Focused application messaging suite: 11 passed.

## [0.9.0] - 2026-08-01

### Added

- Immutable domain event identity and timezone-aware occurrence metadata.
- Ordered event handler registration and unsubscription.
- Function and object-handler delivery.
- Base-event subscriptions for cross-cutting handlers.
- Failure-isolated publication with structured delivery reports.

### Verification

- Focused domain event suite: 11 passed.

## [0.8.0] - 2026-08-01

### Added

- Immutable normalized configuration values.
- Typed configuration fields with defaults, validation, and secret metadata.
- Deterministic layered loading with later-source precedence.
- Mapping and prefixed-environment configuration sources.
- Configuration-specific structured exceptions.
- Backward-compatible application settings loaded through the new engine.
- A defined M13-M20 platform roadmap.

### Verification

- Focused configuration suite: 22 passed.
- Complete regression suite: 130 tests.
- Repository audit: 5 passed, 0 failed.

## [0.7.1] - 2026-07-29

### Added

- Structured framework diagnostic contracts and reports.
- Deterministic Framework Doctor orchestration.
- Runtime, release-metadata, and framework-import checks.
- Plain-text diagnostic rendering.
- Native `doctor` developer CLI command.
- Focused observability and Doctor CLI tests.

### Changed

- Expanded built-in commands from eight to nine.
- Expanded the regression suite from 63 to 97 tests.

### Verification

- Focused Doctor CLI suite: 21 passed.
- Complete regression suite: 97 passed.
- Framework Doctor: 3 passed, 0 warnings, 0 failed.
- Overall framework health: HEALTHY.

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

## 0.7.2 - M12.3 Repository Audit Engine

- Added the reusable repository audit engine.
- Added repository structure and integrity checks.
- Added the native `sarathi.py audit` command.
- Added CLI registration and help integration.
- Added repository-audit and CLI-audit test coverage.
- Added the M12.3 milestone documentation.
