# Milestone 21 - Package Discovery

## Status

Complete.

## Delivered

- Installed package discovery through `project_sarathi.plugins` entry points
- Local development plugin paths
- JSON plugin manifest parsing and strict validation
- Plugin instance, class, and factory resolution
- Framework-version compatibility checks
- Required-capability checks
- Deterministic source ordering
- Cached results, explicit refresh, and invalidation
- Broken, incompatible, and duplicate package isolation
- Human-readable and machine-readable reports

## Verification

- Focused M21 package discovery suite: 11 passed
- Complete regression inventory: 337 tests

## Boundary

Discovery never starts a plugin. M19 remains responsible for lifecycle and
M22-M24 add hooks, dependency-aware module loading, and owned dynamic services.
