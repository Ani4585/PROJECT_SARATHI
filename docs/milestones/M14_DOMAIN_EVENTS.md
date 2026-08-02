# Milestone 14 - Domain Event System

> Superseded temporary label. This is preparatory work for official M41,
> not completion of official M14 Health Monitoring.

## Release

- Version: 0.9.0
- Milestone: M14
- Build date: 2026-08-01
- Tag: v0.9.0-domain-events

## Objective

Provide a domain-owned event mechanism that decouples business facts from
application and infrastructure reactions.

## Delivered

- Immutable domain events with unique identity
- Timezone-aware occurrence timestamps
- Ordered handler registry
- Function and object handlers
- Base-type subscriptions
- Handler unsubscription
- Failure isolation
- Structured publication and delivery reports

## Acceptance Criteria

- Matching handlers execute deterministically
- One broken handler does not block later handlers
- Publication reports expose every outcome
- Duplicate handler subscriptions are rejected
- Focused and regression tests pass

## Next Milestone

M15 - Application Messaging
