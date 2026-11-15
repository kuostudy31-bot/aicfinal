---
description: Propose, evaluate and (with human approval) adopt one prompt change
argument-hint: <ROLE> <CASE_ID> <short failure description>
---
Run one evolution change for: $ARGUMENTS

You coordinate; the controller (`scripts/eu.py evo-*`) validates and records. Dispatch only
`gen-lead` and `crit-lead`; they dispatch the specialists.

1. Prepare (the human chooses the evaluation cases and the acceptance checks):
   `python3 scripts/eu.py evo-prepare --role <ROLE> --case <CASE_ID> --failure "<description>" --dev <case...> --heldout <case...> --require-phrase "<phrase>"... --require-key <key>...`
   Optional evaluation design: `--withhold-key <key>...` removes code-supplied values from the
   frozen inputs, so the failure condition still exists after a code fix; `--samples N` runs each
   arm N times (`inputs.json`, `inputs-2.json`, ... write `note.md`, `note-2.md`, ...);
   `--require-baseline-failure` passes the evaluation only if the baseline reproduces the failure.
   This writes `evolution/changes/<change_id>/failure.json`, one `runs/<case>/<arm>/inputs*.json`
   per evaluation case, arm and sample (baseline = parent version, candidate = proposed file), and
   marks the evolution request active for the dispatch log.
2. Dispatch **gen-lead** in evolution mode with the change id. It must:
   a. dispatch **evo-proposer** for the change folder (writes `prompts/<ROLE>/candidate-<change_id>.md`
      and `proposal.json`);
   b. then, for every `runs/<case>/<arm>/inputs*.json`, dispatch the target role (**<ROLE>**) with
      that inputs file: in evaluation mode it follows `prompt_file`, reads `values` and
      `narrative`, and writes only `output`. Baseline and candidate runs are separate dispatches.
3. `python3 scripts/eu.py evo-evaluate --change <change_id>` checks the dispatch records, compares
   baseline vs candidate on every case and runs the controller regression tests
   (`evaluation.json`).
4. Dispatch **crit-lead** asking it to dispatch **evo-reviewer** for the change folder
   (`review.json`, with the review request_id from `status.json`).
5. `python3 scripts/eu.py evo-submit --change <change_id>` → AWAITING_APPROVAL or REJECTED.
6. Report the evidence and the exact commands for the human:
   `python3 scripts/eu.py evo-adopt --change <change_id> --approver "<name>"` and
   `python3 scripts/eu.py evo-rollback --role <ROLE> --to <version> --approver "<name>" --reason "<why>"`.
   Never adopt yourself.
