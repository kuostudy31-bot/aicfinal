---
description: Propose, evaluate and (with human approval) adopt one prompt change
argument-hint: <ROLE> <CASE_ID> <short failure description>
---
Run one evolution change for: $ARGUMENTS

You coordinate; the controller (`scripts/eu.py evo-*`) validates and records.

1. `python3 scripts/eu.py evo-prepare --role <ROLE> --case <CASE_ID> --failure "<description>"`
   creates `evolution/changes/<change_id>/failure.json` and marks the evolution request active.
2. Dispatch **gen-lead** asking it to dispatch **evo-proposer** for that change folder
   (evolution mode: the only specialist is evo-proposer). Wait.
3. `python3 scripts/eu.py evo-evaluate --change <change_id>` runs the fixed evaluation
   cases (baseline vs candidate) and the controller regression tests, writing
   `evaluation.json`.
4. Dispatch **crit-lead** asking it to dispatch **evo-reviewer** for the change folder. Wait.
5. `python3 scripts/eu.py evo-submit --change <change_id>` validates the review and sets
   AWAITING_APPROVAL or REJECTED.
6. Report the evidence to the user with the exact adoption command
   (`python3 scripts/eu.py evo-adopt --change <change_id> --approver "<name>"`) and the
   rollback command. Never adopt yourself.
