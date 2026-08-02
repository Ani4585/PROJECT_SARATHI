# PROJECT SARATHI

> Enterprise-Grade Modular Intelligence and Application Framework

## Current Official Release Line

| Item | Value |
|------|-------|
| Version | v0.8.20 |
| Milestone | M33 - Middleware Pipeline |
| Build Date | 2 August 2026 |
| Status | Phase 5 active; M33 verified locally |

The authoritative 60-milestone programme is available in
[`docs/project_sarathi_master_roadmap.html`](docs/project_sarathi_master_roadmap.html).
PROJECT SARATHI v1.0.0 is reserved for official M60.

## Vision

PROJECT SARATHI is a modular Python framework for building large-scale
intelligent software systems. Its flagship direction is a National Circular
Bioeconomy Infrastructure Intelligence Platform capable of producing technical,
financial, engineering, and policy artefacts from a unified knowledge base.

## Completed Official Capabilities

- Core configuration, logging, exceptions, lifecycle, and dependency injection
- Reflection, dependency graphs, cycle detection, planning, and validation
- Extensible developer CLI and release gate
- Framework Doctor and typed diagnostics
- Source coverage collection with threshold enforcement and JSON/HTML reports
- Repository and architecture audit with text and JSON output
- Benchmark runner with versioned baselines and regression detection
- Dependency, environment, and tooling reports in text, JSON, and HTML
- Installed CLI extension discovery with isolated diagnostics
- Thread-safe metrics, structured events, nested tracing, correlation IDs, and exporters
- Grouped liveness, readiness, and startup monitoring with timeouts and degraded states
- Wall-time, CPU, allocation, budget, event, and comparison performance monitoring
- Safe-share runtime diagnostic bundles with service, dependency, and redacted configuration data
- Managed Architecture Decision Records with lifecycle commands, validation, and index generation
- Unified terminal, JSON, HTML, historical, and CI developer dashboard
- Validated plugin manifests, immutable contexts, lifecycle management, capability checks, enable policies, and failure isolation
- Typed extension points with single, composition, and priority-based replacement policies and deterministic diagnostics
- Cached installed-package and local-development plugin discovery with manifest validation and isolated compatibility reports
- Ordered synchronous and asynchronous hooks with filters, cancellation, failure isolation, and execution instrumentation
- Validated module descriptors, deterministic dependency plans, lifecycle loading, graph protection, and development reload policy
- Plugin-owned conditional services, commands, hooks, and extensions with frozen scopes and reverse unload cleanup
- Prioritized mapping, JSON/TOML file, and environment configuration providers with provenance, reload, and change notifications
- Central JSON, YAML, and TOML serialization with typed codecs, dataclass restoration, schema envelopes, and migration hooks
- Layered secret providers, opaque masked values, atomic rotation, stale-handle invalidation, and leakage prevention
- Dependency-aware managed resources, reverse cleanup, lazy initialization, bounded pools, and health integration
- Thread-safe TTL caching with LRU/FIFO eviction, namespaces, metrics, cache-aside loading, and stampede control
- Transactional persistence sessions with repositories, units of work, rollback, conflict detection, DI, resources, and health
- ASGI HTTP request/response primitives, streaming, error boundaries, lifespan handling, and server adapter integration
- Typed static and parameterized routing with deterministic precedence, groups, reverse URLs, and HTTP 404/405 dispatch
- Ordered sync/async HTTP middleware with safe exceptions, request IDs, timing, response mutation, and execution instrumentation

## Preparatory Capabilities

The repository also contains tested code for metrics, events, messaging,
modules, persistence, jobs, and an integrated kernel. These components are
reusable later in the official roadmap but do not represent completion of
official M13-M20.

## Developer CLI

```powershell
python sarathi.py <command>
```

| Command | Purpose |
|---------|---------|
| `stats` | Display repository statistics |
| `status` | Display framework and Git status |
| `health` | Run automated tests and compilation |
| `test` | Run the complete test suite |
| `coverage` | Collect source coverage and enforce its threshold |
| `compile` | Compile maintained Python locations |
| `version` | Display authoritative release metadata |
| `doctor` | Diagnose runtime and structural health |
| `audit` | Audit repository structure and integrity |
| `benchmark` | Run benchmarks and detect performance regressions |
| `report` | Generate dependency, environment, and tooling reports |
| `plugins` | Inspect installed CLI command extensions |
| `monitor` | Run grouped operational health checks |
| `diagnostics` | Generate a redacted runtime diagnostic bundle |
| `adr` | Create and manage architecture decision records |
| `dashboard` | Generate the unified developer dashboard |
| `release` | Run the release gate |
| `verify` | Run complete repository verification |

Coverage reports are generated with:

```powershell
python sarathi.py coverage
```

The standard release check is:

```powershell
python sarathi.py verify
```

## Current Quality Status

- Automated tests: 576
- Coverage baseline: 91.39% across 185 source files
- Coverage threshold: 85.00%
- Framework Doctor: 3 checks
- Framework import coverage: 27 packages
- Repository and architecture audit: 9 checks
- Performance benchmarks: 3
- Developer report sections: 3
- Built-in CLI commands: 18
- M13 observability focused suite: 25
- M14 health focused suite: 10
- M15 performance focused suite: 10
- M16 runtime diagnostics focused suite: 7
- M17 ADR focused suite: 8
- M18 dashboard focused suite: 8
- M19 plugin foundation focused suite: 9
- M20 extension framework focused suite: 11
- M21 package discovery focused suite: 11
- M22 hook system focused suite: 11
- M23 module loader focused suite: 18
- M24 dynamic registration focused suite: 12
- M25 configuration provider focused suite: 15
- M26 serialization framework focused suite: 15
- M27 secrets management focused suite: 16
- M28 resource management focused suite: 18
- M29 caching framework focused suite: 18
- M30 persistence layer focused suite: 20
- M31 HTTP server abstraction focused suite: 38
- M32 routing engine focused suite: 48
- M33 middleware pipeline focused suite: 18

## Next Work

Begin official M34 Request Lifecycle on the M33 middleware foundation.

## License

Copyright 2026 PROJECT SARATHI TEAM. All Rights Reserved.
