# Project Sarathi — Official Changelog

All notable changes to Project Sarathi are documented in this file.

---

## [1.0.0] - 2026-08-08

### General Availability (GA) Master Production Release
- **Tag**: `v1.0.0`
- **Test Baseline**: 665 / 665 passed (100% pass rate, 0 failures, 0 warnings).
- Promoted Project Sarathi to General Availability (GA) v1.0.0 production status.
- Finalized enterprise features across Async Runtime, Background Processing, Scheduler, Resilience, Caching, Telemetry, Security, API Gateway, and Hardening.
- Added `tests/test_release_v1_0_0.py` master GA test suite.

---

## [0.9.0-rc1] - 2026-08-08

### Master Release Candidate 1
- **Tag**: `v0.9.0-rc1`
- Synthesized framework features across Milestones 37 through 45 into Master Release Candidate 1.
- Added `tests/test_release_v0_9_0.py` master integration verification suite.

---

## [0.8.31] - 2026-08-08

### Production Hardening, Graceful Shutdown & Benchmarking
- **Tag**: `v0.8.31-production-hardening`
- Added `HardeningAuditor` & `HardeningReport` for system readiness verification.
- Implemented `ShutdownManager` with coroutine draining and signal handling.
- Introduced `ProductionBenchmarkSuite` for latency percentile calculations (`p50`, `p95`, `avg` ms).

---

## [0.8.30] - 2026-08-08

### API Gateway, OpenAPI Contract Engine & Interceptors
- **Tag**: `v0.8.30-api-gateway`
- Added `GatewayRouter` with dynamic path parameter extraction (`/path/{id}`).
- Implemented interceptor pipeline (`GatewayInterceptor`, `CORSInterceptor`, `LoggingInterceptor`, `AuthInterceptor`).
- Integrated `OpenAPIGenerator` producing valid OpenAPI 3.1.0 specifications.

---

## [0.8.29] - 2026-08-08

### Security, Authentication, RBAC & Identity Management
- **Tag**: `v0.8.29-security-auth`
- Implemented HMAC SHA-256 `JWTManager` for token encoding, decoding, signature verification, and expiration enforcement.
- Added PBKDF2 `PasswordHasher` and `constant_time_compare` timing-attack protection.
- Created `UserIdentity` containers and `@require_auth`, `@require_role`, `@require_permission` decorators.

---

## [0.8.28] - 2026-08-08

### Telemetry, Observability & Distributed Tracing
- **Tag**: `v0.8.28-telemetry-metrics`
- Added `Counter`, `Gauge`, and `Histogram` metrics.
- Built `PrometheusExporter` rendering metrics in standard Prometheus exposition format.
- Added distributed tracing with W3C Trace Context propagation (`traceparent`).

---

## [0.8.27] - 2026-08-08

### Resilience, Rate Limiting & Distributed Caching
- **Tag**: `v0.8.27-resilience-caching`
- Implemented `CircuitBreaker`, `@retry` with exponential jitter backoff, and `@bulkhead` concurrency limiters.
- Added `TokenBucket`, `SlidingWindowCounter`, and `LeakyBucket` rate limiters.
- Built `TwoLevelCache` (L1 Local Memory + L2 Distributed Store) with SingleFlight stampede protection.

---

## [0.8.26] - 2026-08-08

### Cron Engine & Scheduled Jobs
- **Tag**: `v0.8.26-scheduled-jobs`
- Added `CronExpression` parser (5 and 6 field support).
- Built `ScheduledJob` lifecycle engine and `DistributedLeaseLock`.

---

## [0.8.25] - 2026-08-08

### Background Task Engine
- **Tag**: `v0.8.25-background-tasks`
- Added asynchronous task queueing, worker pools, and execution tracking.

---

## [0.8.24] - 2026-08-08

### Async Runtime Integration
- **Tag**: `v0.8.24-async-runtime`
- Built core `AsyncService` protocols, cancellation tokens, thread boundaries, and timeout safeguards.
