# RUN_NOTES — AMD-0000002488-26-000191 (AMD 10-Q, quarter ended 2026-09-26)

## Interruption and resume

Context: the case was interrupted on purpose during round 1 of the generator phase as a
recovery test (see docs/incidents.md #8). gen-mapping and gen-narrative had finished;
gen-model was stopped mid-run. A fresh entry session resumed it.

Before resuming, the entry session pulled `origin/claude/trusting-thompson-r5m3id` (the local
checkout predated the case; a first `resume` attempt on the stale checkout printed
`REFUSED: no such case AMD-0000002488-26-000191` because the case directory was not yet present
locally). After the pull:

Time (UTC): 2026-11-14T15:59:25Z

Command: `python3 scripts/eu.py resume --case AMD-0000002488-26-000191` (exit 0)

```json
{
  "case_id": "AMD-0000002488-26-000191",
  "status": "GENERATOR_PENDING",
  "checks": [
    {
      "snapshot_hashes": "ok"
    }
  ],
  "next_action": "re-dispatch only ['gen-model', 'gen-valuation', 'gen-writer'] for request gen-20261114T145504-830038 (completed reports ['gen-mapping', 'gen-narrative'] are kept)",
  "pending": {
    "issued_at": "2026-11-14T14:55:04Z",
    "path": "cases/AMD-0000002488-26-000191/rounds/round-001/request.json",
    "phase": "generator",
    "request_id": "gen-20261114T145504-830038"
  },
  "reports_present": [
    "gen-mapping",
    "gen-narrative"
  ],
  "reports_missing": [
    "gen-model",
    "gen-valuation",
    "gen-writer"
  ]
}
```

Generator reports present at resume (`rounds/round-001/generator/reports/`):

- `gen-mapping.json` (280 bytes)
- `gen-narrative.json` (339 bytes)

Missing (to be re-dispatched): gen-model, gen-valuation, gen-writer. Completed reports kept.
