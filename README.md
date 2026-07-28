# PROJECT SARATHI

> Enterprise-Grade Modular Intelligence and Application Framework

## Current Release

| Item | Value |
|------|-------|
| Version | v0.7.0 |
| Milestone | M12.1 - Extensible Developer CLI Architecture |
| Build Date | 29 July 2026 |
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

- Centralized configuration
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

- Automated tests: 63 passed
- Focused CLI tests: 47 passed
- Compilation: passed
- Built-in CLI commands: 8
- Architecture health: stable
- Backward compatibility: preserved

## Next Milestone

M12.2 - Framework Observability

## License

Copyright 2026 PROJECT SARATHI TEAM.

All Rights Reserved.
