# PROJECT SARATHI

> Enterprise-Grade Modular Intelligence and Application Framework

## Current Release

| Item | Value |
|------|-------|
| Version | v1.0.0 |
| Milestone | M20 - Platform Kernel |
| Build Date | 1 August 2026 |
| Status | Passing |

## Vision

PROJECT SARATHI is a modular, enterprise-grade Python framework for
building large-scale intelligent software systems.

It provides a foundation for dependency injection, lifecycle
management, configuration, diagnostics, modular architecture,
developer tooling, and advanced application orchestration.

Its first flagship implementation is the National Circular Bioeconomy
Infrastructure Intelligence Platform, designed to generate technical,
financial, engineering, and policy artefacts from a unified knowledge
repository.

## Framework Capabilities

- Layered, typed, and validated configuration
- Failure-isolated domain events
- Typed command and query messaging with middleware
- Dependency-aware module runtime
- Repository and unit-of-work persistence ports
- Deterministic background job scheduling
- Thread-safe operational metrics
- Integrated platform kernel and health snapshots
- Structured logging
- Exception and error handling
- Application lifecycle management
- Service registration and dependency injection
- Constructor and type-based injection
- Reflection and constructor metadata caching
- Dependency graph recording and traversal
- Cycle detection
- Dependency planning and validation
- Extensible developer command architecture
- Explicit built-in command registration
- Fail-fast repository verification
- Thin executable composition entry point
- Framework Doctor with structured diagnostics
- Deterministic runtime, release-metadata, and import checks

## Developer CLI

PROJECT SARATHI provides one developer entry point:

```powershell
python sarathi.py <command>
```

| Command | Purpose |
|---------|---------|
| `stats` | Display repository statistics |
| `status` | Display framework, repository, and Git status |
| `health` | Run automated tests and compilation checks |
| `test` | Run the complete pytest suite |
| `compile` | Compile maintained Python locations |
| `version` | Display authoritative version information |
| `doctor` | Diagnose framework runtime and structural health |
| `audit` | Audit repository structure and integrity |
| `release` | Run the release gate |
| `verify` | Run complete one-command repository verification |

The standard verification command is:

```powershell
python sarathi.py verify
```

## Project Structure

```text
config/
docs/
scripts/
    tooling/
        cli/
src/
tests/

main.py
sarathi.py
pytest.ini
README.md
```

## Documentation

| Document | Purpose |
|----------|---------|
| `docs/STATUS.md` | Live engineering status |
| `docs/CHANGELOG.md` | Release history |
| `docs/PROJECT_ROADMAP.md` | Long-term roadmap |
| `docs/SOFTWARE_ARCHITECTURE.md` | Architecture documentation |
| `docs/DEVELOPMENT_GUIDE.md` | Development workflow |
| `docs/RELEASE_GATE.md` | Release requirements |
| `docs/milestones/` | Completed milestone records |

## Engineering Workflow

```text
Design
  -> Implementation
  -> Focused Tests
  -> Full Regression Suite
  -> Compilation
  -> Release Gate
  -> Documentation
  -> Commit
  -> Version Tag
```

## Current Quality Status

- Automated tests: 207 passed
- Focused M13-M20 tests: 99 passed
- Compilation: passed
- Built-in CLI commands: 10
- Framework Doctor: 3 passed, 0 warnings, 0 failed
- Architecture health: healthy
- Backward compatibility: preserved

## Next Milestone

M21 - Production Adapters and API Surface

## License

Copyright 2026 PROJECT SARATHI TEAM.

All Rights Reserved.

## Repository Audit

Validate the repository structure and Git integrity:

```powershell
python sarathi.py audit
```
