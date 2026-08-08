# Project Sarathi — Release Notes v0.9.0-rc1

## Master Release Candidate 1 Highlights

Project Sarathi `v0.9.0-rc1` delivers a complete, production-hardened enterprise framework with 100% test coverage across all subsystems:

### Core Framework Subsystems
- **Async Runtime & Task Engine**: Coroutine isolation, cancellation, timeout enforcement (`v0.8.24`, `v0.8.25`).
- **Distributed Scheduler**: Cron expression evaluator, ScheduledJob lifecycle, and lease-based cluster synchronization (`v0.8.26`).
- **Resilience & Rate Limiting**: Circuit breakers, exponential jitter retries, bulkhead capacity limiters, token buckets, and Two-Level distributed caching (`v0.8.27`).
- **Observability & Tracing**: OpenTelemetry metrics, Prometheus exposition renderer, and W3C Trace Context propagation (`v0.8.28`).
- **Security & RBAC**: JWT token management, PBKDF2 password hashing, API Key authentication, and `@require_role` / `@require_permission` decorators (`v0.8.29`).
- **API Gateway & OpenAPI**: Dynamic path parameter routing, CORS/Logging/Auth interceptor pipeline, and OpenAPI 3.1.0 specification generator (`v0.8.30`).
- **Production Hardening**: System readiness auditor, graceful signal shutdown task draining, and latency percentile benchmarking (`v0.8.31`).

### Test Coverage Baseline
- **660+ Passed Tests** (100% pass rate, 0 failures, 0 warnings across all test suites).
