# Milestone 12.3 - Coverage Collection and Enforcement

## Release

- Version: 0.7.3
- Milestone: M12.3
- Build date: 2026-08-02

## Delivered

- Dependency-free source coverage collection using Python tracing
- AST-based executable statement discovery
- Configurable coverage threshold with an 85% default
- Test failure and threshold failure propagation
- Deterministic per-file results
- JSON and HTML reports under `reports/coverage/`
- Native `python sarathi.py coverage` command
- Release-gate enforcement
- Focused success and failure-path tests

## Acceptance Criteria

- The full test suite executes during coverage collection
- Coverage below the configured threshold returns a failing exit code
- Test failures return a failing exit code regardless of coverage
- JSON and HTML reports are generated
- Generated reports do not dirty the repository
- Focused and regression tests pass
