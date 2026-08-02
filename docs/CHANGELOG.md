# Changelog

All notable PROJECT SARATHI framework changes are documented here.

## [0.8.17] - 2026-08-02 (official M30; Phase 4 complete)

### Added

- Runtime-checkable persistence connection, session, and factory contracts.
- Shared versioned in-memory reference database and connection lifecycle.
- Isolated transactional sessions and named session repositories.
- Atomic multi-repository commits and explicit/context rollback.
- Optimistic conflict detection for stale concurrent snapshots.
- Session-backed unit of work with deterministic state reporting.
- Layered persistence settings and runtime composition root.
- Dependency-injection, managed-resource, and readiness-health integration.
- Runnable transactional repository commit/rollback example.

### Verification

- Focused official M30 persistence layer suite: 20 passed.
- Complete persistence compatibility suite: 32 passed.
- Combined persistence, resources, and health suite: 60 passed.
- Complete automated test inventory: 472.
- Fresh source coverage: 90.86% across 168 files; 85.00% threshold passed.

## [0.8.16] - 2026-08-02 (official M29)

### Added

- Generic cache backend, policy, lookup, and statistics contracts.
- Thread-safe in-memory cache with cached-null support.
- Default and per-entry TTL expiration with proactive reclamation.
- Bounded LRU and FIFO eviction policies.
- Collision-free namespaces and namespace-local clearing.
- Cache-aside loading with per-key stampede protection.
- Independent-key concurrent loading and recursive-load detection.
- Existing metrics integration for outcomes, capacity, loads, and latency.

### Verification

- Focused M29 caching suite: 18 passed.
- Combined caching and metrics suite: 33 passed.
- Complete automated test inventory: 452.

## [0.8.15] - 2026-08-02 (official M28)

### Added

- Dependency-aware managed-resource definitions and lifecycle states.
- Deterministic graph validation, eager/lazy acquisition, and reverse cleanup.
- Context-manager and close-method resource ownership.
- Atomic partial-startup rollback and isolated cleanup reports.
- Thread-safe standalone lazy resource wrapper.
- Bounded pools with warm-up, timeouts, reusable leases, and invalidation.
- Unreleased pool-lease detection and partial warm-up rollback.
- Resource lifecycle and operational-readiness health adapters.

### Verification

- Focused M28 resource management suite: 18 passed.
- Combined resource and health suite: 28 passed.
- Complete automated test inventory: 434.

## [0.8.14] - 2026-08-02 (official M27)

### Added

- Opaque masked secret values with explicit trusted reveal.
- Prioritized mapping, environment, JSON, and TOML secret providers.
- Immutable resolved snapshots with provider provenance and safe summaries.
- Atomic rotation with metadata-only added, rotated, and removed events.
- Stale secret-handle invalidation after rotation or removal.
- Ordered notification subscribers with failure isolation.
- Serializer, copy, logging, and safe-share diagnostic leakage protection.
- Provider reload rollback that preserves the prior live snapshot.

### Verification

- Focused M27 secrets management suite: 16 passed.
- Complete automated test inventory: 416.

## [0.8.13] - 2026-08-02 (official M26)

### Added

- Stable serializer contract and central name/media-type registry.
- Deterministic Unicode JSON serializer with strict non-finite handling.
- Safe optional YAML adapter and nested-table TOML adapter.
- Recursive custom object codec registry.
- Dataclass, tuple, nested sequence, and reserved-mapping-key round trips.
- Schema identity and positive integer version envelopes.
- Deterministic forward migration hooks and chained upgrades.
- Explicit malformed, unsupported, missing-path, failed-hook, and future-version errors.

### Verification

- Focused M26 serialization suite: 15 passed.
- Complete automated test inventory: 400.

## [0.8.12] - 2026-08-02 (official M25)

### Added

- Named configuration provider contract with explicit integer precedence.
- Registration-order-independent priority merging with deterministic tie behavior.
- Nested JSON and TOML file providers with optional-file support.
- Environment and mapping providers integrated into the same precedence model.
- Winning provider and priority provenance for every resolved setting.
- Atomic layered configuration reload manager.
- Added, updated, removed, value, and provider-change comparison data.
- Ordered change subscribers, idempotent unsubscription, and listener-failure isolation.

### Verification

- Focused M25 provider and reload suite: 15 passed.
- Complete configuration suite: 37 passed.
- Complete automated test inventory: 385.

## [0.8.11] - 2026-08-02 (official M24)

### Added

- Plugin-owned registration scopes and contribution records.
- Conditional named, factory, and typed service registration.
- Plugin-provided developer commands, hooks, and typed extensions.
- Frozen-scope protection against unsafe late mutation.
- Reverse-order unload with independent cleanup-failure reporting.
- Automatic rollback after plugin registration or startup failure.
- Automatic cleanup even when plugin shutdown fails.
- Typed framework-service overwrite protection.
- Runnable full plugin integration and unload example.
- Console-only fallback when the configured log file is temporarily unwritable.

### Verification

- Focused M24 dynamic registration suite: 12 passed.
- Complete automated test inventory: 370.
- Runnable integration example: startup, contributions, shutdown, and cleanup passed.
- Current source coverage: 90.67% against an 85.00% threshold.

## [0.8.10] - 2026-08-02 (official M23)

### Added

- Validated module descriptors with semantic versions and dependencies.
- Explicit never/development reload policy.
- Registration-order-independent dependency planning.
- Module loader facade for configuration, startup, and reverse shutdown.
- Production, policy, and active-lifecycle reload guards.
- Transactional graph validation and rollback during replacement.
- Safe stopped-module replacement and lifecycle restart.

### Verification

- Focused M23 descriptor, graph, lifecycle, and loader suite: 18 passed.
- Complete automated test inventory: 356.

## [0.8.9] - 2026-08-02 (official M22)

### Added

- Owned synchronous and asynchronous hook registrations.
- Stable priority and owner ordering.
- Synchronous and asynchronous filters.
- Explicit hook cancellation and remaining-handler short-circuiting.
- Per-filter and per-handler failure isolation.
- Timed hook execution events with isolated observer failures.
- Safe detection of async handlers invoked through synchronous dispatch.
- Explicit unregister behavior for later plugin cleanup.

### Verification

- Focused M22 hook system suite: 11 passed.
- Complete automated test inventory: 348.

## [0.8.8] - 2026-08-02 (official M21)

### Added

- Installed plugin package discovery through `project_sarathi.plugins` entry points.
- Local development discovery through validated `sarathi-plugin.json` manifests.
- Plugin instance, class, and zero-argument factory loading.
- Framework-version and required-capability compatibility reporting.
- Broken and duplicate package isolation.
- Deterministic discovery ordering, caching, invalidation, and explicit refresh.
- Human-readable and machine-readable discovery reports.

### Verification

- Focused M21 package discovery suite: 11 passed.
- Complete automated test inventory: 337.

## [0.8.7] - 2026-08-02 (official M20)

### Added

- Typed, named extension points with runtime-checkable contracts.
- Single, composition, and priority-based replacement policies.
- Deterministic registration ordering by priority and owner.
- Explicit duplicate-owner, single-policy, definition, and type conflicts.
- Typed and untyped extension resolution APIs.
- Human-readable and machine-readable extension diagnostics.
- Active and shadowed registration visibility.

### Verification

- Focused M20 extension framework suite: 11 passed.
- Complete automated test inventory: 326.

## [0.8.6] - 2026-08-02 (official M19)

### Added

- Validated plugin manifests with framework compatibility metadata.
- Immutable plugin context and explicit lifecycle contract.
- Deterministic plugin registry, startup, and reverse shutdown.
- Required and provided capability validation.
- Default and explicit enable/disable policy.
- Lifecycle operation reports and per-plugin failure isolation.

### Verification

- Focused M19 plugin foundation suite: 9 passed.
- Complete automated test inventory: 315.

## [0.8.5] - 2026-08-02 (official M18)

### Added

- Unified dashboard report, section, status, and provider contracts.
- Aggregated version/status, health, coverage, architecture-audit, and benchmark sections.
- Section filtering and provider-failure isolation.
- Terminal dashboard view and standalone HTML report.
- Full JSON artifact and compact CI summary artifact.
- Append-only dashboard history and status-change comparisons.
- Native `sarathi.py dashboard` command.
- Dashboard generation in the release gate and documented daily workflow.

### Verification

- Live dashboard: 5 passed, 0 warnings, 0 failed.
- Focused M18 dashboard suite: 8 passed.
- Complete automated test inventory: 306.

## [0.8.4] - 2026-08-02 (official M17)

### Added

- Typed ADR model, lifecycle statuses, and stable numbering.
- Filesystem ADR repository with deterministic Markdown format.
- Create, list, show, supersede, validate, and index CLI operations.
- Link, relationship, status, date, and required-section validation.
- Generated ADR index documentation.
- Four foundational retrospective ADRs preserved from the legacy decision record.
- ADR validation in the release gate.

### Verification

- Managed ADRs: 4 accepted, 0 validation errors.
- Focused M17 ADR suite: 8 passed.
- Complete automated test inventory: 298.

## [0.8.3] - 2026-08-02 (official M16)

### Added

- Safe-share runtime and environment inspection.
- Registered service, implementation, lifetime, and constructor-cache inspection.
- Dependency resolution graph snapshots.
- Declared-secret and heuristic secret-key redaction.
- Local home-path masking and recursive safe value conversion.
- Failure-isolated five-section diagnostic bundle generation.
- Human-readable and JSON bundle reports.
- Native `sarathi.py diagnostics` command and release-gate integration.

### Verification

- Runtime diagnostic bundle: 5 complete, 0 partial, 0 failed.
- Focused M16 diagnostics suite: 7 passed.
- Complete automated test inventory: 290.

## [0.8.2] - 2026-08-02 (official M15)

### Added

- Typed profiling sessions, snapshots, statuses, budgets, and comparisons.
- Wall-clock and process-CPU measurement.
- Current and peak Python allocation measurement through `tracemalloc`.
- Duration, CPU, and peak-memory budget enforcement.
- Structured performance-completion events integrated with observability.
- Human-readable and JSON snapshot/comparison reports.
- Failure recording with original exception propagation.
- Low-overhead disabled profiling that avoids instrumentation calls.

### Verification

- Focused M15 performance suite: 10 passed.
- Complete automated test inventory: 283.

## [0.8.1] - 2026-08-02 (official M14)

### Added

- Typed health-check, result, report, status, and group models.
- Deterministic health-check registry and dependency ordering.
- Liveness, readiness, and startup groups.
- Per-check timeout enforcement and exception isolation.
- Dependency blocking, skipped checks, and cycle validation.
- Critical-failure and noncritical degraded-state aggregation rules.
- Built-in configuration, container, and filesystem checks.
- Human-readable and JSON health reports.
- Native `sarathi.py monitor` command with group filtering.
- Operational health enforcement in the release gate.

### Verification

- Built-in operational health: 5 healthy, 0 degraded, 0 unhealthy.
- Focused M14 health suite: 10 passed.
- Complete automated test inventory: 273.

## [0.8.0] - 2026-08-02 (official M13)

### Added

- Stable metric, event, timer, and span contracts.
- Thread-safe counters, gauges, distributions, cumulative histograms, and timers.
- Structured diagnostic events with ordered, failure-isolated publication.
- Nested tracing contexts with correlation, span, and parent identifiers.
- Success and error span records with deterministic attributes.
- In-memory event/span exporters and deterministic JSON metrics export.
- No-op metrics, event, trace, and exporter implementations.

### Verification

- Focused M13 observability suite: 25 passed.
- Complete automated test inventory: 263.

## [0.7.6] - 2026-08-02

### Added

- Installed CLI extension discovery through the `project_sarathi.cli` entry-point group.
- Command instance, command class, and zero-argument command factory contracts.
- Deterministic plugin ordering and duplicate-command protection.
- Failure isolation for discovery, import, contract, and registration errors.
- Human-readable and JSON CLI plugin diagnostics.
- Native `sarathi.py plugins` inspection command.
- CLI extension validation in the release gate.

### Verification

- Installed extension discovery: 0 failures.
- Focused CLI plugin and integration suite: 24 passed with one runtime-specific test deferred.
- Automated test inventory: 250.

## [0.7.5] - 2026-08-02

### Added

- Typed dependency, environment, and tooling report contracts.
- BOM-aware UTF-8 and UTF-16 requirements inspection.
- Installed-versus-pinned dependency comparisons.
- Runtime, platform, virtual-environment, source, test, Git, and pytest facts.
- Human-readable, JSON, and standalone HTML developer reports.
- Native `sarathi.py report` command.
- Developer-report validation in the release gate.

### Verification

- Developer report: 3 sections, 0 failures.
- Focused developer-report suite: 8 passed.
- Automated test inventory: 241.

## [0.7.4] - 2026-08-02

### Added

- Deterministic benchmark case, result, suite, and status contracts.
- Warmup and repeated-operation benchmark execution.
- Versioned JSON benchmark baselines with atomic updates.
- Tolerance-based performance regression detection.
- Human-readable and machine-readable benchmark reports.
- Native `sarathi.py benchmark` command.
- Benchmark enforcement in the release gate.

### Verification

- Standard benchmarks: 3 passed, 0 regressions, 0 errors.
- Focused benchmark and CLI suite: 25 passed with one runtime-specific test deferred.
- Automated test inventory: 233.

## [0.7.3] - 2026-08-02

### Added

- Official 60-milestone HTML roadmap in the repository.
- Roadmap realignment and M12-M20 gap audit.
- Dependency-free source coverage collector.
- Configurable 85% coverage threshold.
- JSON and HTML coverage reports.
- Native `sarathi.py coverage` command.
- Coverage enforcement in the release gate.
- Python syntax, domain-boundary, and composition-root audit checks.
- Machine-readable JSON repository-audit output.
- Authoritative-roadmap validation in the repository audit.

### Corrected

- Restored the active version line to the official M12 programme.
- Reclassified repository auditing from temporary M12.3 to official M12.4.
- Reserved version 1.0.0 for official M60.
- Reclassified the platform-kernel packages as preparatory work rather than
  completion of official M13-M20.

### Verification

- Coverage baseline: 87.52%.
- Coverage threshold: 85.00%.
- Automated tests: 223.
- Repository and architecture audit: 9 passed, 0 failed.

> **Roadmap notice:** The entries below from 0.8.0 through the experimental
> platform-kernel snapshot describe preparatory capability work. They are not
> official completion records for M13-M20 in the master roadmap.

## [1.0.0-platform-kernel] - 2026-08-01 (experimental snapshot)

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
