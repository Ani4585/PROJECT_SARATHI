# PROJECT SARATHI

# Software Architecture Document (SAD)

**Document Version:** 2.0.0

**Project Version:** v0.8.18-http-server-abstraction

**Status:** Active

**Last Updated:** 2026-08-02

---

# 1. Purpose

This document defines the official software architecture for PROJECT SARATHI.

It serves as the single source of truth for system structure, engineering principles, module boundaries, coding practices, dependency rules, and future expansion.

All future development must align with this document.

---

# 2. Vision

PROJECT SARATHI is designed as an enterprise-scale modular platform for planning, designing, operating, monitoring and optimizing integrated circular bioeconomy systems.

The architecture must support long-term scalability while remaining maintainable, testable and extensible.

---

# 3. Core Engineering Principles

The project follows these principles.

- Single Responsibility Principle (SRP)
- Open / Closed Principle (OCP)
- Liskov Substitution Principle (LSP)
- Interface Segregation Principle (ISP)
- Dependency Inversion Principle (DIP)
- DRY (Don't Repeat Yourself)
- KISS (Keep It Simple)
- Separation of Concerns

---

# 4. Architectural Style

PROJECT SARATHI follows Clean Architecture.

```
Presentation Layer
        │
        ▼
Application Layer
        │
        ▼
Domain Layer
        │
        ▼
Infrastructure Layer
```

Dependencies always point inward.

---

# 5. Planned High-Level Structure

```
PROJECT_SARATHI/

config/
docs/
scripts/
tests/

src/
    ai/
    analytics/
    api/
    application/
    container/
    core/
    domain/
    dpr/
    finance/
    gis/
    infrastructure/
    interfaces/
    lifecycle/
    monitoring/
    optimization/
    services/
    utils/
```

Folders may expand as new capabilities are introduced.

---

# 6. Dependency Rules

Allowed

Presentation → Application

Application → Domain

Infrastructure → Domain

Forbidden

Domain → Infrastructure

Domain → API

Domain → Database

Domain → User Interface

Business rules must remain independent of implementation details.

---

# 7. Dependency Injection

All shared services are resolved through the Service Container.

Example services include:

- Configuration
- Logger
- Lifecycle Manager
- Database Connections
- AI Services
- GIS Services
- Background Workers

Application code should request services from the container rather than creating them directly.

---

# 8. Logging

Application logging uses the centralized logging framework.

Logging requirements:

- No print() statements in production code
- Structured log messages
- Appropriate log levels
- Consistent formatting

---

# 9. Exception Handling

The project uses a centralized exception hierarchy.

Requirements:

- Custom exception classes
- Meaningful error codes
- Useful diagnostic information
- Centralized logging of unhandled exceptions

---

# 10. Configuration

Configuration is centralized.

Configuration sources:

- Environment variables
- .env files
- Configuration classes

Hard-coded configuration values should be avoided.

---

# 11. Testing Strategy

Testing is organized into:

- Unit Tests
- Integration Tests
- System Tests
- Performance Tests

Automated tests should accompany new functionality wherever practical.

---

# 12. Coding Standards

All code should include:

- Type hints
- Docstrings for public APIs
- Clear naming
- Modular design
- Consistent formatting

---

# 13. Git Workflow

Primary branch:

main

Future development may introduce:

- develop
- feature/*
- release/*
- hotfix/*

---

# 14. Versioning

Semantic Versioning is used.

Examples:

- v0.1.0
- v0.2.0
- v1.0.0

---

# 15. Definition of Done

A milestone is considered complete when:

- Code builds successfully
- Tests pass
- Documentation is updated where required
- Logging is integrated
- Exceptions are handled appropriately
- Code is committed to Git

---

# 16. Future Evolution

This architecture document is a living document.

As PROJECT SARATHI evolves, this document should be updated whenever architectural decisions materially change the design or direction of the system.

---

# 17. Preparatory Platform Kernel Capabilities

The experimental platform kernel composes the following independently testable
capabilities through the dependency-injection container:

- Layered configuration
- Domain event publication
- Application command and query messaging
- Dependency-aware modules
- Persistence ports and in-memory adapters
- Background job scheduling
- Operational metrics
- Lifecycle and health reporting

This is preparatory infrastructure and does not constitute completion of
official M20. The kernel is a composition boundary. Domain code remains independent of the
kernel, infrastructure adapters, databases, and presentation layers.

---

# 18. Plugin Foundation

Framework plugins implement the `Plugin` lifecycle contract and publish a
validated `PluginManifest`. The registry owns registration, compatibility and
capability validation, explicit enable policy, deterministic startup and
reverse shutdown. Each lifecycle operation is isolated so one faulty plugin
does not prevent unrelated plugins from being processed.

Plugin contexts expose immutable configuration and capability snapshots.
Package discovery, hooks, module loading, and dynamic service registration are
reserved for M21-M24 and must build on this foundation.

---

# 19. Extension Framework

Named extension points declare a runtime-checkable type contract and one of
three resolution policies: single, composition, or replacement. Extension
owners register typed values with integer priorities. Resolution is stable
across runs: higher priority wins first and owner names break ties.

Single points reject competing registrations. Composition points expose every
registration in deterministic order. Replacement points select one active
registration while retaining shadowed registrations in diagnostics. Duplicate
owners, unknown points, mismatched contracts, and conflicting definitions fail
explicitly.

---

# 20. Plugin Package Discovery

Plugin packages are discovered through the `project_sarathi.plugins` installed
entry-point group or explicitly configured local development directories.
Local packages declare `sarathi-plugin.json` with a contained Python file and
target attribute. Loaded metadata must exactly match the declared manifest.

Discovery is deterministic, cached, and explicitly refreshable. Broken,
duplicate, incompatible, and capability-deficient packages are isolated and
reported without preventing valid packages from being discovered. Discovery
does not activate plugins; lifecycle ownership remains with the plugin registry.

---

# 21. Hook System

Hook registrations are owned, filterable, prioritized, and ordered
deterministically by descending priority and owner name. Immutable hook events
can be dispatched through explicit synchronous or asynchronous APIs. Async
dispatch supports both handler kinds; synchronous dispatch reports accidental
async handlers without leaking an unawaited coroutine.

Handlers cancel deliberately by returning `HookDecision.CANCEL`. Filter and
handler failures are isolated, recorded, and do not prevent unrelated handlers
from running. Every attempted handler produces a timed execution event for an
optional observability sink; sink failures never alter hook behavior.

---

# 22. Module Loader

Framework modules publish validated descriptors containing name, semantic
version, description, dependencies, and development reload policy. The module
registry validates descriptor consistency and produces a dependency-respecting
plan with lexical ordering for unrelated modules, independent of registration
sequence.

The module loader coordinates configuration, startup, rollback, reverse
shutdown, and inactive development reloads. Missing dependencies and cycles
fail before lifecycle work begins. Reload requires development mode, an
explicitly reloadable descriptor, and an inactive runtime. Replacement graphs
are revalidated transactionally and the prior module is restored on failure.

---

# 23. Dynamic Registration

Each contributing plugin receives a uniquely owned registration scope before
configuration and startup. The scope conditionally registers named and typed
services, developer commands, hooks, extensions, and arbitrary cleanup work.
Every successful contribution is recorded with its owner and kind.

Scopes freeze before plugin configuration, preventing unsafe late mutation.
Failed registration or startup triggers immediate reverse-order rollback.
Shutdown unloads all owned contributions even when the plugin's stop method
fails. Cleanup failures are isolated and reported without skipping remaining
cleanup. Typed service registrations reject replacement so plugins cannot
overwrite framework-owned services.

---

# 24. Configuration Providers

Configuration providers expose stable names, integer priorities, and detached
normalized values. Larger priorities override smaller priorities independently
of declaration order; declaration order deterministically breaks equal-priority
ties. Built-in providers support mappings, prefixed environments, and nested
JSON or TOML files.

Every resolved value records its winning provider and priority, including
schema defaults. The configuration manager atomically reloads all layers,
compares both values and provenance, publishes deterministic change sets, and
keeps the new configuration active even if one subscriber fails. Listener
failures are isolated and returned to the caller for diagnostics.

---

# 25. Serialization Framework

Serialization is selected through a central registry by stable format name or
media type. JSON is deterministic and built in. Safe YAML and nested-table TOML
adapters share the same contract and convert parser failures into framework
errors. Optional adapters avoid eager third-party imports.

Typed serializers recursively transform registered custom objects, dataclasses,
tuples, nested sequences, and mappings through explicit type envelopes. User
mappings containing reserved envelope keys are escaped without data loss.
Versioned serializers add schema identity and positive integer versions;
deterministic forward-only migration hooks upgrade older payloads and report
missing, failed, future, or invalid migration paths explicitly.

---

# 26. Secrets Management

Secrets are resolved through named, prioritized providers for mappings,
prefixed environment variables, and nested JSON or TOML files. Resolution is
atomic and deterministic, and each active key records its winning provider and
priority without exposing its value.

Applications receive opaque `SecretValue` handles whose string, representation,
formatting, copying, diagnostics, and serialization paths are safe by default.
Plaintext requires an explicit reveal call. Reload emits metadata-only added,
rotated, and removed events; rotated or removed handles are invalidated so stale
application references cannot continue to reveal earlier credentials. Subscriber
and provider failures are isolated, and a failed provider reload leaves the
previous snapshot live.

---

# 27. Resource Management

Managed resources are registered with stable names, factories, optional
releasers, dependency declarations, and eager or lazy acquisition policy. The
registry validates the complete graph before startup, acquires dependencies
first, rolls back partial initialization, and cleans up all acquired resources
in reverse order. Native context managers and closeable objects are owned
automatically, while cleanup failures are isolated in a structured report.

Standalone lazy resources provide thread-safe initialize-on-first-use behavior.
Bounded resource pools support minimum warm-up, maximum capacity, timed leases,
reuse, invalidation, and explicit unreleased-lease detection. A lifecycle
adapter connects registry open/close operations to application startup and
shutdown, and a readiness check reports registry state without acquiring lazy
resources as a side effect.

---

# 28. Caching Framework

The caching layer separates a generic backend contract from policy and
cache-aside orchestration. The reference in-memory backend is thread-safe,
distinguishes cached null values from misses, supports default and per-entry
TTL, reclaims expired entries, and enforces bounded LRU or FIFO eviction.

Namespaces use structural keys rather than string concatenation, preventing
cross-namespace collisions. Cache-aside loading uses a distinct lock per key,
double-checks after waiting, permits unrelated keys to load concurrently, and
detects recursive same-key loads. Loader failures are never cached. Cache
operations publish hit, miss, mutation, eviction, expiration, size, load, and
latency measurements through the existing observability metrics contract.

---

# 29. Persistence Layer

The persistence boundary exposes repository, connection, session factory,
session, and unit-of-work contracts independently of adapters. The reference
in-memory database is a shared versioned store. Each session works on an
isolated deep snapshot, commits all named repository changes atomically, and
uses optimistic version checks to reject stale concurrent commits. Explicit
rollback and exception-driven context rollback discard the complete snapshot.

The persistence runtime owns database and connection lifecycles and produces
transient session-backed units of work. Layered configuration selects the
adapter and database identity. Composition helpers register settings, runtime,
database, and transient units of work with dependency injection; a managed
resource definition connects startup and cleanup; and a readiness check reports
connection availability without opening a session as a side effect.

---

# 30. HTTP Server Abstraction

The HTTP boundary follows the ASGI callable model. A validated request wraps
the server scope and receive channel, preserves ordered duplicate headers, and
collects body chunks under an explicit size limit. Finite and streaming
responses emit standards-shaped start and body messages without requiring a
specific network server.

`HttpApplication` dispatches HTTP and lifespan scopes through one callable.
Startup callbacks run in declaration order and shutdown callbacks run in
reverse order. Exceptions before response start are translated by a configurable
safe boundary; failures after start are surfaced without emitting a conflicting
second response. `UvicornServerAdapter` is an optional concrete integration,
while the framework-facing server contract remains independent of Uvicorn.
