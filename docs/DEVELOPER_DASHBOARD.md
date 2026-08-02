# Developer Dashboard Workflow

Run the unified daily view from the repository root:

```powershell
python .\sarathi.py dashboard
```

The command refreshes:

- `reports/dashboard/dashboard.html` for interactive reading
- `reports/dashboard/dashboard.json` for automation
- `reports/dashboard/dashboard-summary.json` for CI summaries
- `reports/dashboard/history.jsonl` for historical comparisons

To inspect only selected sections:

```powershell
python .\sarathi.py dashboard --section health --section coverage
```

Recommended daily routine:

1. Run `python .\sarathi.py dashboard` before starting work.
2. Investigate failed sections immediately and refresh stale warning artifacts.
3. Run focused tests while developing.
4. Run `python .\sarathi.py verify` before a release checkpoint.
5. Review the dashboard history for newly changed section states.
