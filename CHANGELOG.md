# CHANGELOG — PROJECT SARATHI

All notable changes, release tags, and architecture milestones for Project Sarathi.

---

## [v2.0.0] - 2026-08-08 — Master Production Release Candidate & General Availability
### Added
- **SarathiPlatform v2.0.0 Master Orchestration Engine**: Unified entry point synthesizing Vector RAG, Task DAG Workflows, and AI Agent Swarms (`sarathi.v2_platform.platform.SarathiPlatform`).
- **Unified Health Probes**: `SystemHealthProbe` for deep liveness and readiness checking across all platform subsystems.
- **Platform Telemetry & Metrics Reporter**: `PlatformMetricsReporter` calculating $p50, p95, p99$ execution latency, throughput, and error metrics.
- **Concurrency Stress Test Benchmark Suite**: `PlatformBenchmarkSuite` for automated load testing and multi-tenant isolation verification.

---

## [v1.9.0-workflow-graph-dag] - 2026-08-08 — Task DAG Engine, Workflow State Machine & Multi-Agent Swarms
### Added
- **Task Graph DAG Engine**: `TaskNode`, `TaskDAG`, Kahn's topological sorting algorithm, cycle detection (`DAGCycleError`), and concurrent execution branches (`DAGExecutor`).
- **Step-Level Resilience & Rollbacks**: Node retry policies, timeout limits, condition predicates, and automated rollback execution handlers.
- **Distributed Workflow State Machine**: `WorkflowStatus`, `WorkflowState`, transition validations, and checkpoint state serialization.
- **Multi-Agent Swarm Orchestration**: `AgentSwarmOrchestrator` supporting Sequential, Parallel Consensus, Hierarchical (Supervisor/Worker), and Critic Consensus topologies.
- **Swarm Blackboard**: Shared multi-agent memory board (`SwarmBlackboard`) for thread-safe state sharing and consensus tracking.

---

## [v1.8.0-vector-rag-engine] - 2026-08-08 — Vector Database Engine, Semantic Search & RAG Knowledge Pipeline
### Added
- **Vector Database Engine**: In-memory `VectorStore` and `FlatVectorIndex` supporting Cosine, Euclidean, Dot Product, and Manhattan distance metrics.
- **Metadata Filtering Engine**: MongoDB-style query filters (`$eq`, `$ne`, `$gt`, `$gte`, `$lt`, `$lte`, `$in`, `$contains`, `$and`, `$or`, `$not`).
- **BM25 Lexical Retriever**: BM25Okapi sparse term-frequency algorithm.
- **Hybrid Search Engine**: Fuses dense vector similarity with sparse BM25 keyword search using Reciprocal Rank Fusion (RRF).
- **Document Ingestion & Chunking**: `CharacterChunker`, `RecursiveTextChunker`, `SentenceChunker`, and structured `RAGPipeline` context synthesis with citations.
- **AI Agent Tool Binding**: `RAGTool` and `VectorRAGManager` integrating vector knowledge tools into Sarathi AI Agents.

---

## [v1.7.0-ai-agent-engine] - 2026-08-01 — Autonomous AI Agent System & LLM Tool Call Binding
### Added
- Autonomous AI Agent framework, tool binding registries, and agent execution runtimes.

---

## [v1.6.0-edge-sync] - 2026-07-25 — Vector Clocks, State Sync & Edge Workers
### Added
- Edge synchronization, vector clock conflict resolution, and distributed edge worker runtimes.

---

## [v1.5.0-platform-consolidation] - 2026-07-18 — Master Orchestrator Consolidation
### Added
- Core platform orchestration and unified lifecycle hooks.
