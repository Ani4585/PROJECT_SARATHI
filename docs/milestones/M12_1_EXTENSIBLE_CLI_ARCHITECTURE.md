# Milestone 12.1 - Extensible Developer CLI Architecture

## Status

Completed on 29 July 2026.

## Version

PROJECT SARATHI 0.7.0

## Release Tag

`v0.7.0-extensible-cli`

## Objective

Milestone 12.1 transformed the initial repository CLI into a reusable,
testable, and extensible command framework while preserving the entire
Milestone 11.5 command contract.

## Architecture

| Component | Responsibility |
|-----------|----------------|
| `Command` | Defines the command interface |
| `CommandContext` | Supplies repository root and Python executable |
| `CommandRegistry` | Registers and resolves commands safely |
| `CliApplication` | Builds the parser and dispatches commands |
| `ScriptCommand` | Executes repository developer scripts |
| `TestCommand` | Executes the complete pytest suite |
| `CompilationCommand` | Compiles maintained Python locations |
| `VersionCommand` | Displays authoritative framework metadata |
| `VerificationCommand` | Runs fail-fast composite verification |
| Built-in registration | Creates the standard command collection |
| `sarathi.py` | Provides the thin executable composition root |

## Built-In Commands

The public developer interface continues to expose:

```text
compile
health
release
stats
status
test
verify
version
```

Existing command names, help descriptions, developer-script mappings,
output behavior, and process exit codes are preserved.

## Verification Behavior

The `verify` command executes its registered verification sequence in
order and stops immediately when a command returns a non-zero exit
code.

Successful execution displays the authoritative framework name and:

```text
MILESTONE 12.1 VERIFICATION COMPLETE
READY FOR COMMIT
```

## Automated Coverage

- Registry ordering and lookup
- Duplicate command rejection
- Missing command rejection
- Parser construction
- Command dispatch
- Script execution and missing-script handling
- Test and compilation process construction
- Version output
- Verification ordering
- Fail-fast verification behavior
- Built-in command registration
- Thin entry-point delegation
- Real subprocess help and version execution
- Unknown-command rejection

## Final Results

| Verification | Result |
|--------------|--------|
| Focused CLI suite | 47 passed |
| Complete regression suite | 63 passed |
| Built-in commands | 8 passed |
| Compilation | Passed |
| Composite verification | Passed |

## Outcome

PROJECT SARATHI now has a professional developer CLI architecture that
can accept future commands without adding conditional dispatch logic
to the executable entry point.

## Next Milestone

M12.2 - Framework Observability
