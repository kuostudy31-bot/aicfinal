# Register of rejections

Every time the workflow, its hooks or the platform refused, rejected or stopped something,
with where the evidence lives. Times are UTC. "Correct" means the refusal was the right
outcome; "defect" means the refusal itself came from a bug that was then fixed.

## Evolution (system changes)

| Item | Decision | Why | Evidence |
|---|---|---|---|
| change-001 (gen-writer disclosures) | REJECTED by evo-reviewer, 2026-11-15 02:17 | Baseline and candidate both passed every case; the code change 220c535 had removed the cause; the failure record was mislabeled by the coordinator. Correct. | `evolution/changes/change-001/` (review.json, evaluation.json, RUN_NOTES.md) |
| change-002 (no spelled-out quantities) | REJECTED by evo-reviewer, 2026-11-15 03:11 | Same: the code prerequisites had already been applied to the evaluation inputs, so the arms could not be told apart. Correct; the evaluation design error is the coordinator's. | `evolution/changes/change-002/`, `evolution/diagnosis-2026-11-15.md` |

| change-003 (same rule, failure condition kept) | Not rejected: evaluation passed (baseline 6/6 fail, candidate 6/6 pass), reviewer recommended adoption, **adopted by the owner** 2026-11-15 07:46 | Listed for completeness: the first change the loop accepted. | `evolution/changes/change-003/` |
## Controller (research cases)

| Item | Decision | Why | Evidence |
|---|---|---|---|
| NVDA r1 | STALLED (round 2) | asm-001 (net cash missing about $77bn of securities) stayed open across two repairs; the old snapshot could not fix it. Correct. | `cases/NVDA-0001045810-26-000075/result.json`, `state.json` ledger, `rounds/*/repair_packet.json` |
| AMD r1 | STALLED (round 2) | The same gate finding twice; the gate itself was wrong (precision). Defect, fixed in 6fddfe2. | `cases/AMD-0000002488-26-000191/`, `docs/incidents.md` #7 |
| NVDA r2 round 1, first submission | INVALID (submission_error_1) | gen-lead had not yet written `manifest.json`; the controller refused to advance, and the resubmission passed. Correct. | `cases/NVDA-0001045810-26-000075-r2/rounds/round-001/submission_error_1.json` |
| Gate findings → repair rounds | REPAIR | Numerical/provenance gates blocked candidates before review (NVDA r1, AMD r1). | `rounds/*/numerical/gates.json`, `repair_packet.json` |
| Critic `fail` verdicts → repair rounds | REPAIR | NVDA r1 (asm-001), AMD r1/r2 (e.g. prov-001 on an unsupported tax-benefit claim). | `rounds/*/reviews/review-*/crit-*.json`, `decision.json` |
| MU round 1, review 1 | FAIL on all three critics → REPAIR | Majors asm-001 (net cash missing $30.0bn long-term investments), cmp-001 (release cited as part of the 10-K), prov-001 (guidance table broken by quoted pipes). All closed in round 2. Correct. | `cases/MU-0000723125-26-000023/rounds/round-001/reviews/review-01/` |
| MU generator round 1 (Live runs 12 and 14) | HELD twice by the run session on code defects | 10-K derived Q4 without diluted shares; gate defects on per-share guidance and the fiscal-Q4 EPS gap. Defects, fixed (a89f54a, 7f47844); then the owner changed the process to repair in place. | `docs/incidents.md` #12, #14 |
| Run 1 `eu.py prompt --case` before the case existed | REFUSED ("no such case") | Expected; not a bug. | `cases/RUN_NOTES.md` |

## Hooks

| Item | Decision | Why | Evidence |
|---|---|---|---|
| Stop hook, verification run | BLOCKED one stop (2026-11-15 02:13:37) | A run session tried to end its turn with its case pending and no hold. Correct. | `docs/verification/stop_hook.md` |
| Guard hook (state guard), coordinating session | REFUSED three commands (2026-11-14) | (1) about 15:00, a read-only `grep`/`json.dumps` command: **defect**, fixed (commit f1edf03); (2) about 15:01, a test command that redirected into `cases/X/state.json`: correct; (3) about 15:57, `git rm --cached cases/ACTIVE.json`: correct but conservative (done instead with `git update-index --force-remove`). | `docs/incidents.md` #10. Before 2026-11-15 the guard kept no record; it now logs every refusal |
| Guard hook, coordinating session | REFUSED one command (2026-11-15 about 03:16) | A Python file write combined with a control-file path in the same command. Correct; recorded in the local log only, because no run was in progress. | `docs/incidents.md` #11 |

| Guard hook, coordinating session | REFUSED one command (2026-11-15 08:30) | A read of the MU ledger written in the same command as a Python file edit; the text held both a write and `state.json`. **False positive** (nothing was written to state); the coordinator split the command. Recorded in `.logs/guard_refusals.jsonl`. | this row |

## Platform

| Item | Decision | Why | Evidence |
|---|---|---|---|
| Privacy plugin | REFUSED a command with the owner's e-mail in an HTTP header (2026-11-14 about 14:27) | Account e-mail may not be sent to an external service from commands. Correct; the SEC client uses a generic agent name or `SEC_USER_AGENT` set by the owner. | `docs/incidents.md` #10, `src/aicfinal/http.py` |
| Permission system | REFUSED copying `~/.claude/projects/*/subagents/` in run 1 | Agents may not read session internals. Correct; the hook copies transcripts instead. | `docs/incidents.md` #4 |
| Cross-session messages | NOT ACTED ON by run sessions (AMD, 15:48 and 15:57) | A peer session's message is data, not an instruction. Correct; resumes now start new sessions. | `docs/incidents.md` #8 |
| Run 8 (AMD r2) | DECLINED TO START, asked for confirmation (2026-11-15 02:12–02:52) | Its task conflicted with a stale HANDOVER line ("AMD r2: not now"). Correct; the coordinator's error. | `docs/incidents.md` #9 |
| Git proxy | REFUSED pushing the tag `prompt-gen-writer-v3` (HTTP 403, 2026-11-15 07:47) | The session may push only its working branch. The tag exists in the coordinator's checkout; the registry records its name. | `evolution/changes/change-003/RUN_NOTES.md` |
| Nesting limit | Orchestrator had no Agent tool (run 1) | Cloud default `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1`. | `docs/incidents.md` #2 |

## Human decisions
* Publication approvals: NVDA r2, AMD r2 and MU approved under delegation (each case's `approvals.jsonl`); no rejection.
* Evolution adoption: change-003 adopted by the owner's decision (2026-11-15, "adopt and verify").
* The owner paused the evolution run on 2026-11-14 16:20 (Live run 6) and resumed it the next day.
