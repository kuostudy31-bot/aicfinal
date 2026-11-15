# change-002: gen-writer never writes quantities, dates or percentages in words

Entry session: `session_01ERG3WYYTwk8ST1L8Q1LKdg`, 2026-11-15 (UTC). The owner approved this change
on 2026-11-15 (`docs/HANDOVER.md`, "Evolution change-002"). Steps followed `.claude/commands/evo.md`.
A separate session ran case AMD-0000002488-26-000191-r2 at the same time; this run did not touch
its files.

## Outcome

**REJECTED.** `evo-submit` set this state in `status.json` at 2026-11-15T03:10:34Z, with reason
"reviewer rejected". The candidate stays in scope and causes no regression. It shows **no gain over
v2**, because v2 already passes every evaluation case, the source case included. The active
gen-writer prompt stays at **v2**. Nothing was adopted or rolled back.

## Timeline

| UTC | Step | Result |
|---|---|---|
| 03:05:08 | `evo-prepare` (role gen-writer, source case NVDA-0001045810-26-000075-r2, `--require-key rating_outperform_min rating_underperform_max --forbid-spelled-quantities`) | change-002, request `evo-20261115T030508-144a17`, parent v2 |
| 03:05–03:08 | gen-lead (evolution mode) dispatches evo-proposer, then six gen-writer runs | writes `prompts/gen-writer/candidate-change-002.md`, `proposal.json` and six `note.md` files (all present) |
| 03:08:02 | `evo-evaluate` | evaluation_pass true; no regressions; 62 controller tests OK; candidate sha256 `ce72ddae…53bae4` |
| 03:08–03:10 | crit-lead (evolution mode) dispatches evo-reviewer, review request `evoc-20261115T030802-d7957d` | `review.json`, verdict **reject** |
| 03:10:34 | `evo-submit` | state **REJECTED** |

No eu.py command printed an error or a traceback.

## The proposed change

The candidate is v2 with one change, in Procedure step 3. It removes the instruction "Spell out
ordinal words." In its place, a new rule allows ordinal words only in period names such as "second
quarter". The rule forbids writing any quantity, date or percentage in words. Where a `{{key}}` exists
(`rating_outperform_min`, `rating_underperform_max`, `cutoff_utc`, `price_date`, `trigger_accession`),
the writer uses it. Otherwise the writer describes the item qualitatively or leaves it out.

## Evaluation (`evaluation.json`)

Acceptance checks:
- the required placeholders `rating_outperform_min` and `rating_underperform_max`;
- `forbid_spelled_quantities`;
- no blocker from `gates.gate_note`.

No required phrases were set.

| Case | Split | Baseline (v2) | Candidate | Spelled quantities found (base / cand) | Missing keys (base / cand) |
|---|---|---|---|---|---|
| NVDA-0001045810-26-000075-r2 | development | pass | pass | none / none | none / none |
| NVDA-0001045810-26-000075 | development | pass | pass | none / none | none / none |
| AMD-0000002488-26-000191 | held_out | pass | pass | none / none | none / none |

Neither arm had a provenance finding or a missing phrase. There were no regressions, and the 62
controller regression tests pass. gen-lead confirmed that all six notes contain both rating-band
placeholders. Its search for number words found only the period labels "next/trailing twelve
months" (in both arms), and the check did not flag them.

Read with care. The controller reports `candidate_fixes_failure_on_all_cases: true`, but the
baseline also passes, so this evaluation cannot tell the two prompts apart. Each prompt was run once
per case.

## Reviewer verdict (`review.json`): reject

The reviewer judged the change unproven rather than harmful. Its findings, unaltered:

- **evo-001 (major): the evaluation does not tell the two prompts apart.**
  - v2 and the candidate both pass all three cases, with no spelled quantities, missing placeholders
    or provenance findings.
  - The reviewer re-ran `evolution.check_note` on all six notes and got the same results as
    `evaluation.json`.
  - The recorded failure did not recur under v2, and there is one sample per prompt per case.
- **evo-002 (major): the evaluation inputs no longer contain the condition that caused the failure.**
  - The original failing notes were written against `values.json` files without
    `trigger_accession`, `cutoff_utc`, `price_date`, `rating_outperform_min` or
    `rating_underperform_max`. Lines 59–60 of the NVDA r2 round-001 note say the date was spelled out
    because no digit-free key existed.
  - Commit dde8e89 now supplies these keys, and v2 uses them. The evaluation therefore measured the
    code fix, not the prompt.
  - No evaluation run tests the case the prompt rule actually targets: a quantity that has no key,
    such as the sensitivity margins behind NVDA r1 cmp-004.
- **evo-003 (minor): the spelled-quantity check misses some recorded wording.** It does not flag
  "roughly half a percentage point", one of the cmp-004 phrases. It also misses words such as half,
  quarter, double and twice. The check is incomplete but has not been weakened; dde8e89 only made it
  stricter.
- **evo-004 (info): the change stays in scope and nothing regressed.**
  - Only step 3 of the prompt changed, and the candidate's sha256 matches `evaluation.json`.
  - No acceptance check, gate, threshold or policy was weakened.
  - Nothing regressed on the held-out case, and the controller tests pass.
  - The required disclosures are still present.
  - Both arms repeat the "outlook excludes China Data Center compute" framing behind the earlier
    finding prov-002, so this is not a regression.
  - The reviewer called the edit plausible, low-risk hygiene.

**What would change the verdict:** re-evaluate on inputs that tempt the writer to state a quantity
with no `values.json` key, with several samples per prompt. The results should show v2 spelling
quantities in words and the candidate leaving them out.

## Observations from the runs (outside this change's scope; not acted on)

- **NVDA `net_cash` (-$10.9bn) looks low** next to the cash and marketable securities in the
  filing. Writers in both NVDA arms flagged it again, as in change-001. This is a mapping or
  valuation issue and has not been verified.
- **AMD `guide_diluted_shares_next_q` still renders raw** ("1670000000.0"), so the writers cited
  [[Q-5]] instead.
- **The proposer noted that the NVDA r1 cmp-004 sensitivity magnitudes have no `values.json` key.**
  Under the rule, the writer would have to state them qualitatively. Supplying such keys in code
  might be the better fix.
- **The header of `prompts/gen-writer/v2.md` still reads "(v1)".**
- **Whether the spelled-quantity check should join the note gate is a separate decision for the
  owner.** The diagnosis records it that way, and the reviewer's evo-003 shows that the check's
  coverage would need widening first.
- **Local repository state at the start of the session.** The local clone was stale and shared no
  history with the remote branch. It held no local work. It was kept as the local branch
  `backup/stale-local-47fec25` and reset to `origin/claude/trusting-thompson-r5m3id` (dde8e89) before
  step 1.

## Commands for the owner

**Adoption.** `evo-adopt` accepts only changes in AWAITING_APPROVAL. change-002 is REJECTED, so this
command will refuse it (`only AWAITING_APPROVAL changes can be adopted (now REJECTED)`):

```
python3 scripts/eu.py evo-adopt --change change-002 --approver "<owner name>"
```

To pursue the rule anyway, prepare a new change with discriminating inputs, as described under
evo-002. Do not edit `status.json`. If a change is adopted later, it becomes
`prompts/gen-writer/v3.md`. Whoever adopts it commits the file and tags it `prompt-gen-writer-v3`.

**Rollback.** This is needed only after an adoption moves gen-writer off v2. It restores the v2
pointer and keeps both versions:

```
python3 scripts/eu.py evo-rollback --role gen-writer --to v2 --approver "<owner name>" --reason "<reason>"
```

## Evidence in this folder

- `failure.json`, `proposal.json`, `evaluation.json`, `review.json`, `status.json`, `trace.jsonl`
- `runs/<case>/{baseline,candidate}/note.md` and the frozen inputs
- subagent transcripts in `evidence/transcripts/`: gen-lead, evo-proposer, six gen-writer runs,
  crit-lead, evo-reviewer
