# Project Sarathi — Official Framework Changelog

All notable changes to Project Sarathi are documented in this file.

---

## [1.7.0] - 2026-08-08

### Autonomous AI Agent System & LLM Tool Call Binding Engine
- **Tag**: `v1.7.0-ai-agent-engine`
- **Test Baseline**: 683 / 683 passed (100% pass rate, 0 failures, 0 warnings).
- Added `@tool` decorator generating JSON Schema parameter specifications (`properties`, `type`, `required`).
- Implemented `AIAgent` for binding framework tools and executing structured LLM tool calls (`ToolCall`).
- Added `tests/test_ai_agent_m53.py`.

---

## [1.6.0] - 2026-08-08

### Enterprise Edge Computing & Distributed State Synchronization Engine
- **Tag**: `v1.6.0-edge-sync`
- Added `VectorClock` for logical causality tracking and conflict detection.
- Implemented `DistributedStateSync` with `LAST_WRITE_WINS` and `MERGE_MAPS` conflict resolution policies.
- Introduced `EdgeWorker` and `EdgeNode` for offline request queueing and sync replay.
- Added `tests/test_edge_sync_m52.py`.

---

## [1.5.0] - 2026-08-08

### Full Platform Consolidation & Orchestrator
- **Tag**: `v1.5.0-platform-consolidation`
- Added `SarathiPlatform` master orchestrator initializing and binding all 13 core framework subsystems.
- Implemented `PlatformHealthReport` aggregating subsystem status (`UP`, `DEGRADED`, `DOWN`).
- Added `tests/test_platform_m51.py`.

---

## [1.4.0] - 2026-08-08

### Enterprise Messaging, Event Sourcing & CQRS Engine
- **Tag**: `v1.4.0-cqrs-event-sourcing`
- Added `AggregateRoot` and append-only `EventStore` for stream recording and replay.
- Implemented `CommandBus` and `QueryBus` for async and sync message dispatching.
- Added `ProjectionManager` for materialised read-model views.
- Added `tests/test_cqrs_m50.py`.

---

## [1.3.0] - 2026-08-08

### Enterprise Multi-Tenant Architecture & Data Isolation
- **Tag**: `v1.3.0-multi-tenancy`
- Added `TenantContext` using thread/coroutine-isolated `contextvars`.
- Implemented `TenantResolver` resolving tenant identity from HTTP headers (`X-Tenant-ID`), subdomains (`acme.sarathi.io`), or JWT claims.
- Added `@require_tenant` decorator enforcing active tenant presence.
- Added `tests/test_multitenancy_m49.py`.

---

## [1.2.0] - 2026-08-08

### Cloud-Native Containerization, K8s Operator & Service Mesh Integration
- **Tag**: `v1.2.0-cloud-native`
- Added `K8sProbeHandler` (`LivenessProbe`, `ReadinessProbe`, `StartupProbe`).
- Implemented `SarathiCRDGenerator` producing `SarathiApp` K8s CRD specifications.
- Added `ServiceMeshContext` for Envoy/Istio sidecar tracing header extraction (`x-request-id`, `x-b3-traceid`, `x-b3-spanid`).
- Added `tests/test_cloud_native_m48.py`.

---

## [1.1.0] - 2026-08-08

### Enterprise Plugin SDK, LTS Maintenance Engine & Deprecation Lifecycle
- **Tag**: `v1.1.0-sdk-lts`
- Added `PluginSDK` and `BasePlugin` for third-party framework extensions with async `on_load`/`on_unload` hooks.
- Implemented `@deprecated` decorator tracking replacement recommendations and target retirement versions.
- Added `LTSHealthChecker` and `LTSMaintenancePolicy`.
- Added `tests/test_sdk_lts_m47.py`.

---

## [1.0.0] - 2026-08-08

### General Availability (GA) Master Production Release
- **Tag**: `v1.0.0`
- Promoted Project Sarathi to General Availability (GA) v1.0.0 production status.
- Finalized enterprise features across Async Runtime, Background Processing, Scheduler, Resilience, Caching, Telemetry, Security, API Gateway, and Hardening.
- Added `tests/test_release_v1_0_0.py`.
