---
description: Run one earnings-update research case (trigger -> orchestrator -> approval gate)
argument-hint: <TICKER> [ACCESSION | latest]
---
Run the earnings-update workflow for: $ARGUMENTS

You are the entry point, not a worker. Do not write mappings, assumptions, notes or reviews
yourself.

1. Parse the ticker (must be in `config/project.yaml` coverage) and optional accession.
2. If no accession is given (or `latest`), run
   `python3 scripts/eu.py watch --tickers <TICKER>` and take the most recent 10-Q/10-K
   accession it reports or that is already in `events/events.jsonl`.
3. Case id is `<TICKER>-<ACCESSION>`. If `cases/<case_id>/state.json` exists, run
   `python3 scripts/eu.py resume --case <case_id>`; if the case is terminal, report its
   `result.json` and stop.
4. Dispatch the **orchestrator** subagent (Agent tool, subagent type `orchestrator`) with
   the ticker, accession and case id. Wait for it to finish.
5. Run `python3 scripts/eu.py status` and report to the user: final status, rounds,
   findings opened and closed, target price and rating if accepted, and — if the status
   is AWAITING_APPROVAL — the exact command for the human approver:
   `python3 scripts/eu.py approve --case <case_id> --approver "<name>" --decision approve|reject --note "<rationale>"`.
   Never run the approval yourself.
