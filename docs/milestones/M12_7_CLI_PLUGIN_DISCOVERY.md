# Milestone 12.7 - CLI Plugin Discovery

## Status

Complete.

## Extension Contract

Installed packages may publish an entry point in the `project_sarathi.cli`
group. Its target must be one of:

- A `Command` instance
- A concrete `Command` class with a zero-argument constructor
- A zero-argument factory returning a `Command`

Every resulting command remains subject to the existing command-name and
duplicate-registration protections.

## Delivered

- Installed entry-point discovery
- Deterministic discovery and registration ordering
- Strict command extension resolution
- Duplicate built-in and third-party command protection
- Isolation of metadata, loading, contract, and registration failures
- Typed plugin diagnostics and aggregate reports
- Human-readable and JSON renderers
- Native `sarathi.py plugins` command
- Release-gate CLI extension validation

This developer-CLI extension point does not claim completion of the full
framework plugin lifecycle planned for official M19.

## Verification

- Installed extension failures: 0
- Focused CLI plugin and integration suite: 24 passed
- Complete regression inventory: 250 tests
