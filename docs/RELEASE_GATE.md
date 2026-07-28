# PROJECT SARATHI Release Gate

Every stable milestone must satisfy this gate before its commit and tag
are pushed.

## Source and Build

- [ ] No syntax errors
- [ ] Maintained Python locations compile
- [ ] Application and tooling modules import successfully
- [ ] Authoritative version metadata is valid

## Testing

- [ ] Focused milestone tests pass
- [ ] Complete regression suite passes
- [ ] No unexpected skipped tests
- [ ] Process exit codes propagate correctly

## Architecture

- [ ] Dependency graph remains valid
- [ ] No circular dependencies are introduced
- [ ] Public command contracts remain stable
- [ ] New components have focused tests
- [ ] Composition roots remain thin

## Documentation

- [ ] README reflects the current version
- [ ] STATUS reflects current verification results
- [ ] CHANGELOG contains the release
- [ ] Milestone documentation is complete
- [ ] Next milestone is identified

## Repository

- [ ] Required files exist
- [ ] Git diff contains no whitespace errors
- [ ] No temporary or debug files are included
- [ ] Changed files match the milestone scope
- [ ] Commit and annotated tag names are correct

## Standard Verification

Run:

```powershell
python sarathi.py verify
```

The command must finish successfully and print:

```text
VERIFICATION COMPLETE
READY FOR COMMIT
```

Before committing, also run:

```powershell
git diff --check
git status --short
```

A release may be committed and tagged only after every applicable check
passes.
