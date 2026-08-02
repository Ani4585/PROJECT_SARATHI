# ADR-0003: Centralize Logging

- Status: Accepted
- Date: 2026-07-26
- Supersedes: None
- Superseded by: None

## Context

Operational diagnosis requires consistent log levels, formatting, destinations, and exception capture.

## Decision

Production framework code uses the centralized logging facilities rather than direct console printing.

## Consequences

Logs are consistent and configurable, while developers must use the framework logging contract.

## Links

- ../SOFTWARE_ARCHITECTURE.md
