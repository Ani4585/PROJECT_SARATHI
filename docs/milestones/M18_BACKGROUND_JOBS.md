# Milestone 18 - Background Job Engine

> Superseded temporary label. This is preparatory work for official M38/M40,
> not completion of official M18 Developer Dashboard.

## Release

- Version: 0.13.0
- Milestone: M18
- Build date: 2026-08-01
- Tag: v0.13.0-background-jobs

## Objective

Provide deterministic in-process scheduling and execution primitives for
background work without coupling the core to a specific worker platform.

## Delivered

- Immutable job definitions
- Explicit job runtime states
- Injected scheduler clock
- Stable due-job ordering
- Result and error capture
- Failure isolation
- Pending-job cancellation
- Bounded retries with retry delays
- Structured execution records

## Acceptance Criteria

- Only due jobs execute
- Equal-time jobs retain insertion order
- Broken jobs do not prevent later jobs from running
- Retries stop at their configured limit
- Completed and cancelled jobs never execute again
- Focused and regression tests pass

## Next Milestone

M19 - Metrics Engine
