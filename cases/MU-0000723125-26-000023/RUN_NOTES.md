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
