# ADR-0004: Centralize Exceptions

- Status: Accepted
- Date: 2026-07-26
- Supersedes: None
- Superseded by: None

## Context

Generic exceptions provide insufficient structure for framework recovery and diagnostics.

## Decision

Use a centralized hierarchy of domain-specific exceptions with actionable context.

## Consequences

Callers receive predictable failures and diagnostics, with more exception types to maintain.

## Links

- ../SOFTWARE_ARCHITECTURE.md
