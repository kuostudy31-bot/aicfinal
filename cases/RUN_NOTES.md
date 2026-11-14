# Run notes

## NVDA-0001045810-26-000075 (NVIDIA 10-Q, FY2027 Q2) — live agent-team run, 2026-11-14

**Outcome:** stopped at `GENERATOR_PENDING`, round 1. No generator or critic work was done.

### What happened
1. The entry session confirmed that the custom agents were available (orchestrator, gen-lead,
   crit-lead, gen-*, crit-*) and dispatched `orchestrator` (agent_id a3c0f00ebd3b2d81f).
2. The orchestrator ran `python3 scripts/eu.py open --ticker NVDA --accession 0001045810-26-000075`.
   - status GENERATOR_PENDING, round 1, cutoff_utc 2026-08-26T20:36:00Z
   - request_id `gen-20261114T144812-0d99ea`, request at `rounds/round-001/request.json`
   - (Before the case was opened, `eu.py prompt --role orchestrator --case ...` returned
     `REFUSED: no such case NVDA-0001045810-26-000075`, exit code 2. That is expected for a case
     that does not exist yet; it is not a code bug.)
3. **Blocker:** the orchestrator subagent had no Agent tool, so it could not dispatch `gen-lead`.
   Its report, verbatim: "I have no Agent tool, so I could not dispatch gen-lead. The case is stuck
   at GENERATOR_PENDING in round 1."
   In this Claude Code runtime, subagents cannot spawn further subagents, even when their
   frontmatter lists `Agent` in `tools:`. That means the orchestrator → gen-lead/crit-lead →
   specialists hierarchy cannot run as designed. gen-lead and crit-lead would hit the same limit
   when they try to dispatch the specialists.
4. Following the run rules, nothing was patched and the entry session did not do the
   orchestrator's or the leads' dispatch work itself. `eu.py approve` was never run.

### Controller state after the stop (`eu.py resume`)
next_action: "re-dispatch only ['gen-mapping', 'gen-narrative', 'gen-model', 'gen-valuation',
'gen-writer'] for request gen-20261114T144812-0d99ea (completed reports [] are kept)"

### Evidence
- `NVDA-0001045810-26-000075/evidence/hook_events.jsonl`: SubagentStart and SubagentStop for
  the orchestrator. Both events carry `agent_type`.
- Subagent transcripts were **not** exported. Copying `~/.claude/projects/*/*/subagents/agent-*.jsonl`
  into the repo was denied by the session's permission classifier, and that was not worked around.

### Options to unblock (need a human decision)
- Flatten dispatch: the top-level session acts as the orchestrator and leads, and dispatches each
  gen-*/crit-* specialist directly. This departs from the current run rules.
- Or run under a runtime or harness that allows nested subagent dispatch.

## NVDA-0001045810-26-000075 — resumed run, 2026-11-14 (after spawn depth raised to 3)

**Outcome:** stopped at `GENERATOR_PENDING`, round 1. The cause is a traceback in controller code
during `eu.py compute`. Nothing was submitted, no critic review ran, and `eu.py approve` was never run.
Nothing was patched.

### What happened
1. `python3 scripts/eu.py resume --case NVDA-0001045810-26-000075` returned GENERATOR_PENDING, with
   all five generator reports missing. The snapshot hashes checked out.
2. **Nested dispatch now works.** Orchestrator #1 (aae02dc395ce88075) dispatched gen-lead
   (a45d6a86c1b849060), which dispatched gen-mapping (ac8b26515bfd5e63a), gen-narrative
   (a65715c8ec4e66ed6), gen-model (ae1848f4399e2a87a) and gen-valuation (ad186b28666a679cc).
3. **A new runtime problem: early hand-back.** Child agents launched in the background even when
   `run_in_background: false` was requested. Orchestrator #1 handed back while gen-lead was still
   running, and gen-lead then handed back while gen-valuation was still running. So gen-writer was
   never dispatched and no manifest was written.
4. After a fresh `resume` (next_action: re-dispatch only gen-valuation and gen-writer), the entry
   session dispatched orchestrator #2 (a7992913088ae9632). It was told not to hand back while any
   children were still running. It dispatched gen-lead (a0102cfa197f0e6a2), which re-dispatched
   gen-valuation (a260af786d7b7dce7). The two gen-valuation runs overlapped by about 10 s. The
   earlier one stopped at 14:56:54, and the files on disk (valuation_inputs.json and
   reports/gen-valuation.json, both written at 14:58:01) are from the second run.
5. The integration compute failed. gen-lead hit it first, and orchestrator #2 reproduced it.

### Exact error (`python3 scripts/eu.py compute --case NVDA-0001045810-26-000075`)
```
  File "/home/user/aicfinal_test/src/aicfinal/gates.py", line 178, in run_all
    out += gate_quotes(ctx["narrative"], ctx["docs"])
  File "/home/user/aicfinal_test/src/aicfinal/gates.py", line 144, in gate_quotes
    token = f"{val:.1f}"
ValueError: Unknown format code 'f' for object of type 'str'
```
Call chain: eu.py:209 main → eu.py:202 → eu.py:72 cmd_compute → compute.py:70 run → gates.py:178 →
gates.py:144.

Cause (checked by the entry session, read-only): `references/contracts.md` line 31 allows guidance
`unit` to be `USD`, `ratio` or `text`. `generator/narrative.json` line 104 has
`{"metric": "china_data_center_compute_in_outlook", "value": "none assumed", "unit": "text", "quote_id": "Q-2"}`.
`gate_quotes` (gates.py:143–144) formats every guidance value as a float. This is a controller code
bug, not a specialist error. **Human decision needed:** either fix `gate_quotes` to skip or
string-match text-unit guidance (a code change), or re-dispatch gen-narrative to drop that entry,
which goes against the "keep completed reports" resume rule.

### Controller state after the stop
- `eu.py resume` next_action: "re-dispatch only ['gen-writer'] for request
  gen-20261114T144812-0d99ea (completed reports ['gen-mapping', 'gen-narrative', 'gen-model',
  'gen-valuation'] are kept)". gen-writer needs `computed/values.json`, and compute will crash again
  until the bug above is resolved.
- `rounds/round-001/computed/` holds files written at 15:08:15 by a compute attempt that crashed.
  The values in them were produced before the gate step crashed. They are **ungated and not
  accepted**: target $184, Underperform, -12.2% against the $209.66 close on 2026-08-26.
- Rounds: 1 (generator phase only). Findings opened: 0, closed: 0. No controller target price or
  rating has been accepted.
- `eu.py status` now also lists AMD-0000002488-26-000191 (GENERATOR_PENDING). That case was not
  started by this session.

### Issues the specialists raised (not yet reviewed by a critic)
1. `short_term_investments` is unmapped (MarketableSecuritiesCurrent last reported 2025-10-26).
   Net cash of -$10.923B therefore leaves out the 2026-07-26 marketable debt securities ($34.143B)
   and marketable equity securities ($42.783B). By gen-valuation's estimate this is worth +$1.41 to
   +$3.17 per share.
2. Derived diluted share counts for FY2025Q4 (D-30c5a1282c) and FY2026Q4 (D-475c151c60) are
   negative, because quarters are subtracted from an annual weighted average. This may be a
   derivation bug, and derived Q4 EPS may be wrong too.
3. The snapshot has no XBRL fact for tax expense or pre-tax income, so the tax cross-check relies
   on the 10-Q text.
4. H1 FY2027 net income includes $23.707B of net gains on equity securities, so trailing EPS and
   P/E overstate operating earnings.

### Evidence
Transcripts in `evidence/transcripts/`: two orchestrator, two gen-lead, gen-mapping, gen-narrative,
gen-model, and both gen-valuation runs. A grep for tokens, keys and credentials (GitHub, Anthropic
or OpenAI, AWS, Slack, Bearer and Authorization headers, private keys) found nothing, so no lines
were removed.

## NVDA-0001045810-26-000075 — Resume after controller fix, 2026-11-14

Another session (session_01ERG3WZcbWkidht1tadsh6H) reported that commit 9240e7c fixed the controller defects recorded above: text guidance in gate_quotes, non-additive share counts, range midpoints, and cover-page share dates. It relayed that the owner decided to keep the completed reports. The entry session pulled the branch and confirmed that gates.py now skips text-unit guidance. It made no code edits.

`python3 scripts/eu.py resume --case NVDA-0001045810-26-000075` (exit 0):
```json
{
  "case_id": "NVDA-0001045810-26-000075",
  "status": "GENERATOR_PENDING",
  "checks": [
    {
      "snapshot_hashes": "ok"
    }
  ],
  "next_action": "re-dispatch only ['gen-writer'] for request gen-20261114T144812-0d99ea (completed reports ['gen-mapping', 'gen-narrative', 'gen-model', 'gen-valuation'] are kept)",
  "pending": {
    "issued_at": "2026-11-14T14:48:12Z",
    "path": "cases/NVDA-0001045810-26-000075/rounds/round-001/request.json",
    "phase": "generator",
    "request_id": "gen-20261114T144812-0d99ea"
  },
  "reports_present": [
    "gen-mapping",
    "gen-narrative",
    "gen-model",
    "gen-valuation"
  ],
  "reports_missing": [
    "gen-writer"
  ]
}
```

A fresh orchestrator was dispatched to continue from this next_action only.
