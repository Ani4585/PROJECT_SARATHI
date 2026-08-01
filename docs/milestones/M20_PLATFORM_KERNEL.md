# Milestone 20 - Platform Kernel

## Release

- Version: 1.0.0
- Milestone: M20
- Build date: 2026-08-01
- Tag: v1.0.0-platform-kernel

## Objective

Integrate the M13-M19 framework capabilities behind one composition root and
runtime boundary suitable for future production adapters.

## Delivered

- Platform kernel and fluent builder
- Dependency-injection registration for all runtime services
- Shared module and application lifecycle
- Guarded runtime operations
- Integrated application messaging
- Integrated domain event publication
- Integrated background job execution
- Automatic kernel metrics
- Immutable health snapshots
- Expanded Framework Doctor package coverage

## Acceptance Criteria

- The builder produces a fully configured kernel
- All runtime services resolve through the DI container
- Modules start and stop with the kernel lifecycle
- Runtime operations are rejected before startup
- Messages, events, and jobs emit operational metrics
- Kernel health reports version 1.0.0 and milestone M20
- M13-M20 focused and complete regression suites pass
- Compilation, Doctor, audit, and release verification pass

## Next Milestone

M21 - Production Adapters and API Surface
