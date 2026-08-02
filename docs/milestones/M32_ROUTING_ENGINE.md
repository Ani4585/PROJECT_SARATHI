# Milestone 32 - Routing Engine

## Status

Complete.

## Delivered

- Validated route, match, parameter, and group models
- Static, string, integer, UUID, and catch-all path matching
- Extensible named converter registry with typed values
- Deterministic static, typed, generic, and catch-all precedence
- Registration decorators and immutable route inventory
- Ambiguous path-shape, overlapping-method, and duplicate-name protection
- Explicit route-not-found and method-not-allowed outcomes
- Sorted allowed-method reporting
- Reusable route groups with path and name prefixes
- Reverse URL generation with type validation and percent encoding
- Synchronous and asynchronous handler dispatch
- M31 ASGI application integration with plain 404 and 405 responses
- Standards-shaped Allow header for method failures

## Verification

- Route models and converters: 18 passed
- Router registry, precedence, conflicts, and errors: 15 passed
- Groups, reverse URLs, and HTTP integration: 15 passed
- Focused official M32 routing suite: 48 passed
- Complete regression inventory: 558 tests
- Fresh source coverage: 91.30% across 183 files
- Coverage threshold: 85.00%, PASS

## Phase Result

Phase 5 remains active. M32 adds deterministic request routing on top of the
M31 ASGI application and server boundary.

## Next Milestone

M33 - Middleware Pipeline.
