# Milestone 17 - Persistence Ports

> Superseded temporary label. This is preparatory work for official M30,
> not completion of official M17 Architecture Decision Records.

## Release

- Version: 0.12.0
- Milestone: M17
- Build date: 2026-08-01
- Tag: v0.12.0-persistence-ports

## Objective

Define domain-facing persistence boundaries without coupling the framework to a
specific database technology.

## Delivered

- Generic repository protocol
- Generic unit-of-work protocol
- Thread-safe in-memory repository
- Identity uniqueness and missing-entity errors
- Insertion-order queries
- Deep transactional snapshots
- Multi-repository unit of work
- Explicit commit and rollback
- Automatic rollback on exceptions

## Acceptance Criteria

- Domain code can depend on repository contracts only
- In-memory storage behaves deterministically
- Failed work restores every registered repository
- Mutable entity state is restored through deep snapshots
- Focused and regression tests pass

## Next Milestone

M18 - Background Job Engine
