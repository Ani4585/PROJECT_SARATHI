# ADR-0002: Use Dependency Injection

- Status: Accepted
- Date: 2026-07-26
- Supersedes: None
- Superseded by: None

## Context

Direct construction of shared services makes testing, composition, and lifecycle control difficult.

## Decision

Resolve shared services through the framework service container and explicit composition roots.

## Consequences

Dependencies become replaceable and observable, at the cost of container infrastructure and registration discipline.

## Links

- ../SOFTWARE_ARCHITECTURE.md
