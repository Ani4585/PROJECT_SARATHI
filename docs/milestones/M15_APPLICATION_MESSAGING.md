# Milestone 15 - Application Messaging

## Release

- Version: 0.10.0
- Milestone: M15
- Build date: 2026-08-01
- Tag: v0.10.0-application-messaging

## Objective

Create a typed application boundary for state-changing commands and read-only
queries, with middleware for cross-cutting concerns.

## Delivered

- Immutable command and query metadata
- Typed handler registry
- Exactly one handler per message type
- Function and object handlers
- Ordered middleware pipeline
- Middleware short-circuiting
- Query result propagation
- Structured registration and resolution errors

## Acceptance Criteria

- Commands and queries dispatch only to their exact registered handler
- Duplicate handlers are rejected
- Middleware wraps handlers in declared order
- Query results propagate through the entire pipeline
- Focused and regression tests pass

## Next Milestone

M16 - Module Runtime
