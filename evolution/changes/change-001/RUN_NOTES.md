# change-001: gen-writer Disclosures cite trigger accession, cutoff and price date

Entry session: `session_01ERG3WYeRNcesmBbiGaHLpu`, 2026-11-15 (UTC). The owner requested this run to
replace the paused Live run 6, which produced nothing. Steps followed `.claude/commands/evo.md`.

## Outcome

**REJECTED** (`status.json` state, set by `evo-submit` at 2026-11-15T02:17:14Z, reason "reviewer
rejected"). The candidate is in scope and caused no regression. It shows **no gain over v2**,
because the parent prompt already passes on every evaluation case. The active gen-writer prompt
stays at **v2**. Nothing was adopted or rolled back.

## Timeline

| UTC | Step | Result |
|---|---|---|
| 02:12:19 | `evo-prepare` (role gen-writer, source case NVDA-0001045810-26-000075-r2, `--require-key trigger_accession cutoff_utc price_date`) | change-001, request `evo-20261115T021219-5d5990`, parent v2, state PREPARED |
| 02:12–02:15 | gen-lead (evolution mode) → evo-proposer, then gen-writer × 6 | `prompts/gen-writer/candidate-change-001.md`, `proposal.json`, six `note.md` files (all present) |
| 02:15:14 | `evo-evaluate` | evaluation_pass true; no regressions; 53 controller tests OK; candidate sha256 `5b863496…c78b` |
| 02:15–02:17 | crit-lead (evolution mode) → evo-reviewer, review request `evoc-20261115T021514-3a62e1` | `review.json` verdict **reject** |
| 02:17:14 | `evo-submit` | state **REJECTED** |

No eu.py command printed an error or a traceback.

## The proposed change

The candidate is v2 plus five lines under step 5 (Disclosures). The writer must state the filing
accession, the information cutoff and the price date as `{{trigger_accession}}`, `{{cutoff_utc}}` and
`{{price_date}}`. It may not leave them out, call them "recorded elsewhere" or spell them in words.

## Evaluation (`evaluation.json`)

Acceptance checks: required placeholders `trigger_accession`, `cutoff_utc` and `price_date`; no
blocker from `gates.gate_note`. No required phrases were set.

| Case | Split | Baseline (v2) | Candidate | Reasons |
|---|---|---|---|---|
| NVDA-0001045810-26-000075-r2 | development | pass | pass | no missing placeholders, no missing phrases, no provenance findings in either arm |
| NVDA-0001045810-26-000075 | development | pass | pass | same as above |
| AMD-0000002488-26-000191 | held_out | pass | pass | same as above |

Regressions: none. Controller regression suite: 53 tests, OK. gen-lead counted the placeholders:
all six notes contain `{{trigger_accession}}` and `{{cutoff_utc}}` once and `{{price_date}}` twice.
Read with care: the controller still reports `candidate_fixes_failure_on_all_cases: true`, but the
baseline also passes, so this evaluation cannot tell the two prompts apart. There was one run per
arm per case.

## Reviewer verdict (`review.json`): reject

The reviewer calls the change unproven rather than harmful.

- **evo-001 (major):** the evaluation does not discriminate. v2 already passes on all three cases,
  including the source case where the proposal expected it to fail. There is only one sample per
  arm.
- **evo-002 (major):** the root cause was already fixed in code. The original failure (missing
  accession and cutoff, dates spelled in words) happened because `values.json` had no such keys.
  Commit 220c535 added them (`src/aicfinal/values.py` lines 37–42). The new prompt lines repeat what
  v2 now does unprompted.
- **evo-003 (minor):** `failure.json` puts a different description under the ID cmp-001. In the
  source case's crit-compliance reviews, cmp-001 is about attribution. The disclosure credits every
  figure to "SEC XBRL data" and omits the price snapshot (price, upside, peer multiples, target
  price). That issue remains open, and the NVDA-r2 candidate note still carries the wording.
- **evo-004 (info):** scope is clean. The edit touches only the gen-writer prompt, the candidate
  hash matches `evaluation.json`, the held-out case passes, and the controller tests pass.

Reviewer's suggestion: a next change should target the real cmp-001 attribution wording ("SEC XBRL
data and the case price snapshot"), with a failure record and evaluation in which the parent
actually fails.

## Observations from the writer runs (outside this change's scope; not acted on)

- **NVDA-0001045810-26-000075: `net_cash` looks wrong.** It is -$10.9bn, while the 10-Q quotes
  (Q-13/Q-14) report $56.6bn of cash, cash equivalents and marketable debt securities. Marketable
  securities may be left out, which would understate the target price. This belongs to the
  mapping or valuation stage. It was flagged by both writer runs and has not been verified here.
- **AMD: `guide_diluted_shares_next_q` renders unformatted** ("1670000000.0"), so both writers
  cited [[Q-5]] instead. Writers also noted there is no DCF/peer blend-weight key and no indication
  whether `eps_q` is basic or diluted.
- No `gate-note-*` checks ran on the evaluation notes, because evaluation mode skips `eu.py compute`.
  The controller's own evaluation checks (placeholders and the provenance gate) did run.

## Commands for the owner

**Adoption.** `evo-adopt` accepts only changes in AWAITING_APPROVAL. change-001 is REJECTED, so this
command will refuse it (`only AWAITING_APPROVAL changes can be adopted (now REJECTED)`):

```
python3 scripts/eu.py evo-adopt --change change-001 --approver "<owner name>"
```

To keep the wording anyway as a defensive clarification, which the reviewer calls low-risk,
prepare a new change carrying the same candidate so it passes review. Do not edit `status.json`.
If a change is later adopted, it becomes `prompts/gen-writer/v3.md`. The person adopting commits
it and tags it `prompt-gen-writer-v3`.

**Rollback** (needed only after an adoption moves gen-writer off v2; it restores the v2 pointer and
keeps both versions):

```
python3 scripts/eu.py evo-rollback --role gen-writer --to v2 --approver "<owner name>" --reason "<reason>"
```

## Evidence in this folder

`failure.json`, `proposal.json`, `runs/<case>/{baseline,candidate}/note.md` and frozen `inputs/`,
`evaluation.json`, `review.json`, `status.json`, `trace.jsonl`, and the subagent transcripts in
`evidence/transcripts/` (gen-lead, evo-proposer, six gen-writer runs, crit-lead, evo-reviewer).
