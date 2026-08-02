# Roadmap Realignment Audit

## Authoritative Source

- Source: `project_sarathi_master_roadmap.html`
- Baseline: v0.6.2
- Previously completed milestone: M11.5
- Programme: 10 phases, 60 milestones, 378 micro-milestones
- Stable v1.0.0 target: M60

## Official M12-M20 Gap Analysis

| Milestone | Assessment | Evidence and remaining work |
|-----------|------------|-----------------------------|
| M12 | Partial | M12.1 and M12.2 complete; M12.3 coverage now complete; repository portion of M12.4 exists; architecture audit, M12.5-M12.7 remain |
| M13 | Partial | Metrics and event primitives exist; spans, tracing context, correlation, exporters, and no-op implementations remain |
| M14 | Partial | Basic Doctor checks exist; health registry, grouped liveness/readiness/startup, timeouts, dependencies, degraded states, and machine output remain |
| M15 | Missing | Profiling, CPU/memory measurement, budgets, comparisons, and disabled-mode guarantees remain |
| M16 | Partial | Runtime/version/import diagnostics exist; service inspection, dependency traces, sanitized bundles, and sharing policy remain |
| M17 | Missing | ADR model, repository, CLI lifecycle, validation, generated index, and tests remain |
| M18 | Missing | Aggregated terminal/HTML dashboard, filters, history, CI artifacts, and workflow documentation remain |
| M19 | Missing | Plugin manifest, lifecycle, context, registry, compatibility, enable/disable, and failure tests remain |
| M20 | Missing | Typed extension points, ordering, priorities, replacement/composition, diagnostics, and conflict tests remain |

## Reclassification of Preparatory Code

| Existing package | Correct official destination |
|------------------|------------------------------|
| `src/metrics` | Partial M13 |
| `src/modules` | Partial M23 |
| `src/configuration` | Partial M25 |
| `src/persistence` | Partial M30 |
| `src/jobs` | Partial M38/M40 |
| `src/domain/events` | Partial M41 |
| `src/application/messaging` | Preparatory M33/M42 concepts |
| `src/kernel` | Cross-cutting preparatory integration |

No preparatory package is considered completion of its destination milestone
until every official micro-milestone and definition-of-done item is verified.
