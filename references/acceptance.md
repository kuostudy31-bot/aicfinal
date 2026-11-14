# Acceptance criteria (fixed; owned by the analyst)

These criteria are fixed for a case before it starts. No agent may edit this file,
and an evolution proposal may not weaken it (see `references/policies.md` §5).

## A. Numerical gates (run by the controller, `src/aicfinal/gates.py`)

A candidate reaches the critics only when no gate reports a `blocker` or `major` finding:

| Gate | Requirement |
|---|---|
| mapping_coverage | revenue, operating income, net income, diluted shares, CFO, capex, cash and total assets have a value for the latest quarter |
| stale_mapping | every mapped line has a value for the latest quarter (no silent zeros from discontinued concepts) |
| balance_sheet | total assets equal liabilities and equity within 0.1% |
| eps_consistency | net income / diluted shares within 3% of reported diluted EPS |
| gross_profit_identity | revenue - cost of revenue equals gross profit within 0.5% |
| information_cutoff | every fact and price was observable at the cutoff (SEC acceptance time of the trigger filing) |
| assumption_bounds | WACC in [6%, 16%]; terminal growth in [0%, 4%] and below WACC; margins in (0, 1); q/q growth in [-50%, 100%]; tax in [0, 35%] |
| assumption_rationale | every forecast and valuation input has a written rationale |
| quote_verbatim | every quote appears verbatim in the cited snapshot document |
| guidance_source | every structured guidance value is visible in its cited quote |
| note_placeholder | every `{{key}}` and `[[Q-id]]` in the note resolves |
| untagged_number | the note contains no number that was not supplied by code or by a quote (year and period labels excepted) |
| recompute | any computed file saved by the generator equals the controller's recomputation |

## B. Critic review

* Three critics (provenance, assumptions, compliance) review each candidate in fresh contexts.
* A finding stays open until a critic verifies the repaired output (`resolved` with evidence)
  or, for gate findings, until the recomputed gates no longer report it.
* `blocker` and `major` findings block acceptance; `minor` findings are recorded.

## C. Research acceptance

* All gates pass, every critic returns `pass`, and no blocking finding is open,
  in **two consecutive full reviews of the same candidate**. Any change to the
  candidate starts a new clean-review streak.
* Research acceptance does not authorise publication.

## D. Publication

* A named approver must approve (`eu.py approve`); the record is kept in `approvals.jsonl`.
* If the target price moves more than the threshold in `config/project.yaml` versus the
  last published note, the approval must carry a written rationale.
* The rating follows the policy bands mechanically (upside to target price).

## E. Limits

Per case: 3 generator rounds, 2 invalid submissions per step, 12 dispatches per round,
240 minutes elapsed. Reaching a limit stops the case as EXHAUSTED or BLOCKED; exhaustion
never grants acceptance.
