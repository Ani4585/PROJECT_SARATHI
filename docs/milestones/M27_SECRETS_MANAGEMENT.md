# Milestone 27 - Secrets Management

## Status

Complete.

## Delivered

- Opaque secret-value contract with explicit trusted reveal
- Masked string, representation, formatting, and logging behavior
- Copy and serialization refusal for sensitive values
- Prioritized mapping, environment, JSON, and TOML secret providers
- Normalized layered resolution with winning-provider provenance
- Immutable active secret snapshots and safe metadata summaries
- Atomic reload and deterministic added, rotated, and removed change events
- Stale-handle invalidation after rotation or removal
- Ordered rotation subscribers with failure isolation and idempotent unsubscribe
- Safe-share diagnostic redaction and secret inventory integration
- Typed serialization guard that rejects secret values before custom codecs
- Provider failure rollback that preserves the previous live snapshot

## Security Boundary

Secret plaintext is available only through the explicit `SecretValue.reveal()`
operation while its handle remains active. Python strings cannot be reliably
zeroed by application code, so the framework minimizes exposure, clears its
own stale reference, prevents implicit serialization, and never includes
plaintext in change events or diagnostic output.

## Verification

- Focused M27 secrets management suite: 16 passed
- Complete regression inventory: 416 tests

## Next Milestone

M28 - Resource Management.
