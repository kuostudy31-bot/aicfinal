# change-003: gen-writer never writes quantities, dates or percentages in words (re-evaluation, failure condition kept)

Entry session: `session_01ERG3WaWonmmCcWXBnBSRph`, 2026-11-15 (UTC). The owner asked for this
change on 2026-11-15 at 07:30 UTC (`docs/HANDOVER.md`, "Owner decisions on record"). The steps
followed `.claude/commands/evo.md`. Case MU-0000723125-26-000023 ran in another session at the same
time, and this run left its files alone.

## Outcome

**AWAITING_APPROVAL.** `evo-submit` set this state in `status.json` at 2026-11-15T07:41:20Z. The
evaluation passed and the reviewer's verdict was **approve-recommended**. Nothing has been adopted.
The active gen-writer prompt stays at **v2** until the owner runs the adoption command below. The
reviewer raised two minor points (evo-002 and evo-003), and the owner should read them before
adopting.

No eu.py command printed an error or a traceback.

## Timeline

| UTC | Step | Result |
|---|---|---|
| 07:34:38 | `evo-prepare` (role gen-writer, source case NVDA-0001045810-26-000075-r2, `--forbid-spelled-quantities --withhold-key rating_outperform_min rating_underperform_max cutoff_utc price_date --samples 2 --require-baseline-failure`) | change-003, request `evo-20261115T073438-42ad96`, parent v2. Committed as 14d270d |
| 07:35–07:38 | gen-lead (evolution mode) dispatches evo-proposer, then 12 separate gen-writer runs | `prompts/gen-writer/candidate-change-003.md`, `proposal.json`, 12 notes (all present). Committed as ef1763d (mid-run checkpoint) and 047310b |
| 07:38:21 | `evo-evaluate` | evaluation_pass true; baseline_reproduces_failure true; no regressions; 67 controller tests OK; candidate sha256 `c17030f6…9e7200`. Committed as 5a87fdf |
| 07:38–07:41 | crit-lead (evolution mode) dispatches evo-reviewer, review request `evoc-20261115T073821-c7b033` | `review.json`, verdict **approve-recommended**. Committed as 4e2c133 |
| 07:41:20 | `evo-submit` | state **AWAITING_APPROVAL** |

Two `git push` attempts were rejected because the MU session pushed to the same branch at the same
moment. A `pull --rebase` and a retry fixed this, and nothing was lost.

## The proposed change

Only Procedure step 3 differs from v2:
- The instruction "Spell out ordinal words." is removed. Ordinal words are allowed only inside
  period names such as "second quarter".
- New rule: never express a quantity, date or percentage in words. The rule names examples of each
  kind it covers:
  - number words ("fifteen percent", "minus ten percent", "twelve-month");
  - dates ("August twenty-sixth");
  - fractions ("half a percentage point", "a third", "a quarter of revenue");
  - multipliers ("twice", "double", "triple", "threefold").
- The writer uses a `{{key}}` only if the values file lists it, and must not assume that any key
  exists. If no key covers the item, the writer describes it qualitatively or leaves it out.
  Disclosures follow the same rule.

## Evaluation (`evaluation.json`)

Design:
- The frozen inputs withhold `rating_outperform_min`, `rating_underperform_max`, `cutoff_utc` and
  `price_date`. This recreates the condition under which the failure was first recorded.
- Each arm ran 2 samples.
- The evaluation passes only if the baseline reproduces the failure at least once.

Acceptance checks: `forbid_spelled_quantities`, and no blocker from `gates.gate_note`. No required
phrases or placeholders were set.

| Case | Split | Sample | Baseline (v2) | Candidate | Spelled quantities found: baseline | Spelled quantities found: candidate |
|---|---|---|---|---|---|---|
| NVDA-0001045810-26-000075-r2 | development | 1 | fail | pass | "fifteen percent", "ten percent", "minus ten percent" | none |
| NVDA-0001045810-26-000075-r2 | development | 2 | fail | pass | "fifteen percent", "ten percent" | none |
| NVDA-0001045810-26-000075 | development | 1 | fail | pass | "plus fifteen percent", "minus ten percent" | none |
| NVDA-0001045810-26-000075 | development | 2 | fail | pass | "fifteen percent", "ten percent" | none |
| AMD-0000002488-26-000191 | held_out | 1 | fail | pass\* | "fifteen percent", "minus ten percent" | none flagged\* |
| AMD-0000002488-26-000191 | held_out | 2 | fail | pass | "fifteen percent", "ten percent" | none |

\* The checker did not flag this note, but it writes "twelve" in period labels three times (lines 7,
13 and 38: "next-twelve-month", "Trailing-twelve-month", "Next twelve months"). The candidate's own
rule lists "twelve-month" as forbidden, so a strict reading fails this sample. See reviewer finding
evo-002.

No sample in either arm had a provenance finding. Nothing regressed, and the 67 controller tests
pass.

**Did the baseline reproduce the failure?** Yes, in all 6 baseline samples (6/6). With the keys
withheld, v2 wrote the rating thresholds in words in every sample, so this time the evaluation can
tell the two prompts apart. Neither arm wrote a spelled-out date or a sensitivity margin of the
NVDA r1 cmp-004 kind. Those two forms are covered by the rule's wording but were not exercised in
this evaluation.

## Reviewer verdict (`review.json`): approve-recommended

The findings, without changes:

- **evo-001 (info): the evaluation now tells the two prompts apart.**
  - Baseline v2 fails 6/6 and the candidate passes 6/6 on the automated checks.
  - The reviewer re-ran the note check on all 12 notes and got the same results as
    `evaluation.json`.
  - The four keys are missing from all three frozen inputs. Nothing regressed, and 67 tests pass.
  - Gap: neither arm triggered a spelled-out date or a cmp-004 sensitivity margin.
- **evo-002 (minor): "twelve" appears in a held-out candidate sample.**
  - The AMD candidate note.md writes "twelve" in period labels, which the candidate's own rule names
    as forbidden. The regex does not catch it.
  - The reviewer treats these as standard period names rather than a return of the failure, and
    not as a regression: all 6 baseline notes contain "twelve", against 1 of 6 candidate notes.
  - Under a strict reading, the candidate result is 5/6, not 6/6.
  - Suggested follow-up: either allow "twelve months" as a period name or require TTM/NTM, and make
    the check match.
- **evo-003 (minor): disclosures are complete in form but not in substance.**
  - With the keys withheld, the candidate notes contain the four disclosures from `policies.md` §6
    in form only. The thresholds, cutoff time and price date are described in words, with no values.
  - The candidate prompt was never run with those keys present.
  - The reviewer asks for one such run, for example the first live case after adoption.
- **evo-004 (info): fractions and multipliers.**
  - A manual scan found no fractions or multipliers in the candidate notes.
  - The automated check still misses "a third", "twice", "threefold" and "twelve-month". This gap
    was already recorded as change-002 evo-003.
- **evo-005 (info): scope follows `policies.md` §5.**
  - Only step 3 changed, and the candidate's sha256 matches.
  - The controller commit ca3c5a1 makes the evaluation stricter. Nothing was weakened.

## Observations from the runs (outside this change's scope; not acted on)

- NVDA `net_cash` (-$10.9bn) again looks inconsistent with the marketable securities in quote Q-13.
  Writers flagged this, as in change-001 and change-002. It has not been verified.
- The AMD key `guide_diluted_shares_next_q` still renders raw ("1670000000.0"), so writers cited Q-5
  instead.
- The spelled-quantity check misses "twelve-month", fractions and multipliers. Whether to widen it,
  and whether to add it to the note gate, are separate decisions for the owner.

## Commands for the owner

**Adoption.** Only the owner runs this. Adoption makes the candidate `prompts/gen-writer/v3.md`
and moves the active gen-writer pointer from v2 to v3. Commit the result and tag it
`prompt-gen-writer-v3`:

```
python3 scripts/eu.py evo-adopt --change change-003 --approver "<owner name>"
```

The reviewer recommends one follow-up before or right after adoption. The first live case on v3
should run with the rating-band, cutoff and price-date keys present, to confirm the §6 disclosures
carry their values (evo-003). The owner should also decide how "twelve months" period labels are
handled (evo-002).

**Rollback.** This is needed only after adoption. It restores the v2 pointer and keeps both
versions:

```
python3 scripts/eu.py evo-rollback --role gen-writer --to v2 --approver "<owner name>" --reason "<reason>"
```

## Evidence in this folder

- `failure.json`, `proposal.json`, `evaluation.json`, `review.json`, `status.json`, `trace.jsonl`
- `runs/<case>/inputs/{values,narrative}.json`: the frozen inputs, with the four keys withheld
- `runs/<case>/{baseline,candidate}/inputs.json`, `inputs-2.json`, `note.md`, `note-2.md`
- subagent transcripts in `evidence/transcripts/`: gen-lead, evo-proposer, 12 gen-writer runs,
  crit-lead and evo-reviewer
