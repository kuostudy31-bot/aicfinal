# RUN_NOTES: MU-0000723125-26-000023 (Live run 12)

MU FY2026 10-K, accession 0000723125-26-000023 (accepted 2026-10-09; cutoff_utc 2026-10-09T12:21:00Z).
This is the first case opened on a 10-K. FY2026 ended 2026-09-03 and was a 53-week year, so the derived Q4 is 14 weeks.

## Outcome
**HELD in GENERATOR_PENDING, round 1** (request gen-20261115T073305-99d304). A code defect in 10-K
quarterization blocks the generator round. The entry session did not patch code, as its instructions require.

* Rounds: 1, still in progress. No controller submits were made.
* Findings opened/closed: none (no critic review ran).
* Target price / rating: not produced (valuation never ran).
* eu.py itself: no REFUSED and no traceback.

## Error (exact)
gen-model hit it calling `model.forecast(history, assumptions)`; the text below is as relayed by gen-lead and the orchestrator:
```
File "/home/user/aicfinal_test/src/aicfinal/model.py", line 86, in forecast
    shares = latest(hist, "diluted_shares")["val"]
TypeError: 'NoneType' object is not subscriptable
```
The traceback text appears in `evidence/transcripts/gen-model-a6fc1f869a3b18f53.jsonl`.

* **Cause (as reported by gen-model; the code part was checked read-only by the entry session):** the 10-K's XBRL tags
  diluted shares only for FY2026 (1,143M) and the 9M YTD. Non-additive lines are not differenced, so FY2026Q4
  `diluted_shares` is null. `latest()` (`src/aicfinal/model.py:71-73`) returns the last element even when it is None.
* **Same pattern:** `src/aicfinal/valuation.py:79` would fail next. gen-lead also reports that `gate_eps`
  skips the latest period without a warning.
* **Display-only issue (not a blocker):** the `eu.py concepts` preview differences non-additive lines
  (diluted_shares shown as 1,000,000, eps_diluted as 32.93, per gen-mapping).
* **Fix options (a code-owner decision):** have `latest()` fall back to the last non-null value
  (FY2026Q3 1,145M, F-3d172a9372), or use the FY diluted share count for 10-K cases.

## Work kept for reuse (rounds/round-001/generator/)
mapping.json (21 lines), narrative.json (14 verbatim quotes), assumptions.json, and the reports from
gen-mapping, gen-narrative and gen-model. The latest `eu.py resume` next_action re-dispatches only gen-valuation and gen-writer.

## To resume after a code fix
`python3 scripts/eu.py resume --case MU-0000723125-26-000023`, then dispatch gen-lead for the missing
specialists, compute, submit, dispatch crit-lead, and continue. Never run `eu.py approve` from a run session.

## Session notes
* The entry session's local branch had diverged: the remote history had been rewritten, and the local branch kept only an old tip, 47fec25.
  The auto-mode classifier refused a hard reset, so the work ran on a new local branch `mu-run12` that tracks
  `origin/claude/trusting-thompson-r5m3id`. The old tip is kept locally as `backup/pre-sync-47fec25`.
* The orchestrator handed back once before gen-lead returned and was resumed. It waited for the running
  gen-lead instead of dispatching a second copy.
* Transcripts are present in evidence/transcripts/ (orchestrator, gen-lead, gen-mapping, gen-narrative, gen-model).
  A grep for tokens, keys and credentials found no matches, so no lines were removed.

## Resume after the 10-K fix (Live run 14)

Entry session synced to origin/claude/trusting-thompson-r5m3id at a89f54a (the local branch had the stale tip 47fec25 again; kept as `backup/pre-forcepush-47fec25`).

`eu.py release` output:
```
{
  "case_id": "MU-0000723125-26-000023",
  "status": "GENERATOR_PENDING",
  "hold": null
}
```

`eu.py resume` output:
```
{
  "case_id": "MU-0000723125-26-000023",
  "status": "GENERATOR_PENDING",
  "checks": [
    {
      "snapshot_hashes": "ok"
    }
  ],
  "next_action": "re-dispatch only ['gen-valuation', 'gen-writer'] for request gen-20261115T073305-99d304 (completed reports ['gen-mapping', 'gen-narrative', 'gen-model'] are kept)",
  "pending": {
    "issued_at": "2026-11-15T07:33:05Z",
    "path": "cases/MU-0000723125-26-000023/rounds/round-001/request.json",
    "phase": "generator",
    "request_id": "gen-20261115T073305-99d304"
  },
  "reports_present": [
    "gen-mapping",
    "gen-narrative",
    "gen-model"
  ],
  "reports_missing": [
    "gen-valuation",
    "gen-writer"
  ]
}
```

### Outcome of Live run 14: HELD again in GENERATOR_PENDING, round 1
Request gen-20261115T073305-99d304. The diluted-shares fix in a89f54a worked: gen-valuation finished, and `eu.py compute` exited 0 with **target price 1084, rating Neutral** (from computed/values.json; no note was written and nothing was submitted or accepted). gen-lead then stopped on three major gate findings caused by code defects in `src/aicfinal/gates.py`. The entry session checked those read-only and did not patch code.

* Rounds: 1, still in progress. Controller submits: none. Critic findings: none opened or closed (no critic round ran).
* eu.py: no REFUSED and no traceback. The blocker is the gate defects below, as reported by the orchestrator and gen-lead.

#### Error (exact gate findings, all major)
```
gate-stale-eps_diluted (stale_mapping): 'eps_diluted' has no value in the latest quarter (last 2026-05-28); the company may have switched XBRL concepts, and treating it as zero would bias the model
gate-guidance-eps_next_q_gaap (guidance_source): eps_next_q_gaap value 0.0 not visible in Q-4
gate-guidance-eps_next_q_nongaap (guidance_source): eps_next_q_nongaap value 0.0 not visible in Q-4
```
* **gate_quotes (`gates.py` ~146-160):** `v = x / 1e9 if g["unit"] == "USD" else x * 100`. Per-share EPS guidance (37.84, range 36.84-38.84; 38.15, range 37.15-39.15) is scaled to 0.0 and cannot match Q-4 ("$37.84 ± $1.00 | | $38.15 ± $1.00"). The contract allows only the units USD, ratio and text, so no unit fits per-share guidance.
* **gate_mapping (`gates.py` 32-37):** any optional line whose last value is None is flagged. A 10-K's derived Q4 (2026-09-03) has no diluted EPS by design. a89f54a fixed `model.latest()` and `gate_eps` but not this gate. The EarningsPerShareDiluted mapping is correct.
* **Workarounds not applied** (they would hide the defects): tagging the EPS guidance `unit: "text"`, or unmapping eps_diluted. That decision belongs to the code owner.
* **Open question for gen-mapping/critics:** net cash leaves out $30.019B of long-term marketable investments (AvailableForSaleSecuritiesDebtSecuritiesNoncurrent, F-5368223b24). Including them would add about $26 per share; gen-valuation says the rating would stay Neutral.

#### Work kept
mapping.json, narrative.json, assumptions.json, valuation_inputs.json, computed/values.json, and the reports from gen-mapping, gen-narrative, gen-model and gen-valuation. Still missing: gen-writer, note.md, manifest.json.

#### To resume after the fix
`eu.py release`, then `eu.py resume`. Dispatch gen-lead for gen-writer, compute and the manifest, then `eu.py submit` and crit-lead. Never run `eu.py approve` from a run session.

#### Session notes
* The local branch had the stale tip 47fec25 again; the entry session reset to origin at a89f54a and kept `backup/pre-forcepush-47fec25`.
* The orchestrator handed back early once, before gen-lead returned. It was resumed with the same agent and told not to start a second gen-lead. gen-valuation's hand-back reached the entry session directly, and the entry session forwarded it to the orchestrator without acting on it.
* Transcripts are present in evidence/transcripts/ (orchestrator x2, gen-lead x3, gen-mapping, gen-narrative, gen-model, gen-valuation). A grep for tokens, keys and credentials found no matches, so no lines were removed.

Hold recorded 2026-11-15T07:50:02Z by run session (`eu.py hold` succeeded; status GENERATOR_PENDING with hold set).
