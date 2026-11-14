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

## Run after resume

- 15:59:25Z — `eu.py resume` (above). Entry session dispatched the `orchestrator` subagent with
  the case id and the next_action.
- The orchestrator's first gen-lead finished gen-model and gen-valuation and then stopped
  without running gen-writer. The orchestrator also handed back once too early, and the entry
  session sent it back to continue. Later `resume` calls showed the reports filling in
  (`re-dispatch only ['gen-valuation', 'gen-writer']`, then `['gen-writer']`). This confirms
  that completed reports were kept, including gen-mapping and gen-narrative from before the
  interruption.
- The gen-valuation report was delivered to the entry session instead of gen-lead. The entry
  session passed it on to the orchestrator without acting on it. The files on disk match the
  report.
- A second gen-lead ran gen-writer, then integration compute, and wrote manifest.json.
- Submit 1 (round 1, request gen-20261114T145504-830038): numerical gates failed. The
  controller issued repair round 2, request gen-20261114T160700-654fe5.
- Round 2: all five specialists re-dispatched (6 dispatches in total).
- Submit 2 (round 2) at 16:11:02Z: the controller stopped the case with **STALLED**:
  "same open findings across 2 repairs: ['gate-guidance-opex_next_q']".

## Outcome

| Item | Value |
|---|---|
| Final status | **STALLED** (terminal); no critic review ran (review 0) |
| Rounds | 2 generator rounds (max 3) |
| Findings opened | `gate-guidance-opex_next_q` (major, gate, guidance_source): "opex_next_q value 3.8 not visible in Q-3" |
| Findings closed | none |
| Computed target price / rating | $265 / Underperform vs $483.90 close (cutoff 2026-11-03T23:00:17Z). Code output, **not accepted**: the case stalled before review and has no approval |
| Errors | No REFUSED or traceback after the resume. Before the pull, one `resume` on the stale checkout printed `REFUSED: no such case` (see above) |

### Why the case stalled (analyst note, not a controller output)

Quote Q-3 (release_ex99_2.txt) reads "Operating Expenses ~$3.75 Billion". This is the only opex
guidance in the snapshot. `src/aicfinal/gates.py` (`check guidance_source`, the `visible()`
helper) shows a USD value in billions to one decimal (`f"{v:.1f}"`), so 3.75e9 becomes "3.8".
That string can never appear in the quote. The generators kept the value the filing supports
rather than change it to pass the gate. The finding therefore looks like a gate false positive
from rounding, not a data error. Clearing it needs a human decision: either accept it as a
rounding false positive, or change the gate to compare at the quote's own precision. The entry
session did not edit any code.

### Open points from specialists (not filed as findings)

- Customer warrants for up to 320M shares at $0.01 are not in the 1,661M diluted share base.
  gen-valuation estimates up to about 16% lower value per share if they all vest.
- The pending Taalas (about $2.9B, cash and stock) and World Labs (about $8.2B, stock) deals are
  in neither net cash nor the share count.
- About $3.2B of long-term equity investments are left out of net cash (conservative).
- In round 1, gen-narrative's report used status "ok" and had no "outputs" field.

### Evidence

- `evidence/transcripts/`: 14 transcripts (orchestrator, gen-lead x3, and each specialist for
  rounds 1–2). Scanned for secrets (token, key, private-key and credential patterns); no matches,
  so nothing was removed.
- Decision notes: `rounds/round-001/decision_note.md`, `rounds/round-002/decision_note.md`.
  Result: `result.json`.
- `eu.py approve` was not run. There is nothing to approve: the status is STALLED, not
  AWAITING_APPROVAL.
