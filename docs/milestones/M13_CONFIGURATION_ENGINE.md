# Milestone 13 - Layered Configuration Engine

> Superseded temporary label. This is preparatory work for official M25,
> not completion of official M13 Observability Core.

## Release

- Version: 0.8.0
- Milestone: M13
- Build date: 2026-08-01
- Tag: v0.8.0-configuration-engine

## Objective

Replace hard-coded configuration assembly with a deterministic, typed, and
validated engine while preserving the established `Settings` interface.

## Delivered

- Immutable normalized configuration mapping
- Typed field declarations and conversion
- Required values, defaults, and custom validation
- Secret-value redaction
- Ordered source precedence
- Mapping and environment sources
- Strict unknown-key detection
- Structured configuration errors
- Backward-compatible application settings integration

## Acceptance Criteria

- Later configuration sources override earlier sources
- Invalid and missing values raise specific errors
- Environment keys are filtered and normalized
- Secrets are redacted from dictionary output by default
- Existing application settings remain compatible
- Focused and regression tests pass
- Compilation and repository audit pass

## Next Milestone

M14 - Domain Event System
