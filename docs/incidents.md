# Incident log

Problems met while building and running the workflow, recorded as they were found.
Times are UTC on 2026-11-14. Status: **resolved** (fixed and verified), **mitigated**
(worked around; the underlying limit remains) or **open**.

| # | Incident | Status |
|---|---|---|
| 1 | Custom subagents created mid-session are not loaded by that session | resolved |
| 2 | Cloud runtime limits subagent nesting to one level | resolved (setting override) |
| 3 | Subagent dispatch allowlists are not enforced inside subagent definitions | mitigated |
| 4 | Agents may not copy subagent transcripts out of `~/.claude` | resolved (hook copies) |
| 5 | Development session's hook wrote a stray line into a case trace | resolved |
| 6 | Catalog-only snapshot hid NVDA's marketable-securities concepts | resolved for new cases |
| 7 | Five controller defects surfaced by the NVDA and AMD runs | resolved |
| 8 | AMD run idle after a deliberate interruption (two stalls) | resolved by handover; watchdog added; Stop hook planned |

## 1. New subagents not visible in the creating session
* **What happened.** `.claude/agents/` was created during the development session; the Agent
  tool there reported the types as not found.
* **Fix.** Live runs start in fresh sessions on the committed branch. (Later in the day the
  development session also listed the agents.)

## 2. Nesting limited to one level (14:47–14:50)
* **What happened.** The first NVDA run's orchestrator had no Agent tool. The cloud runtime sets
  `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1`. The case stopped safely at `GENERATOR_PENDING`
  (`cases/RUN_NOTES.md`).
* **Fix.** `.claude/settings.json` sets the depth to 3. A probe session confirmed that a
  subagent could dispatch a child, and the NVDA case was resumed from its pending request.
* **Remaining risk.** The fix overrides a platform default; a platform change could undo it.

## 3. Dispatch allowlists not enforced by Claude Code
* **What happened.** `Agent(type, …)` lists are honoured only for a main-thread agent.
* **Mitigation.** The controller compares hook-recorded dispatches with
  `references/roles.yaml` and refuses to advance on a disallowed, missing or excessive dispatch
  (`tests/test_controller.py::test_disallowed_dispatch_is_invalid`). This makes a violation
  ineffective; it cannot stop the dispatch itself.

## 4. Transcripts could not be copied by an agent
* **What happened.** An evidence-export step that read `~/.claude/projects/*/subagents/` was
  refused by the permission system.
* **Fix.** The SubagentStop hook copies `agent_transcript_path` into the case's
  `evidence/transcripts/`.

## 5. Stray hook record in the NVDA trace (about 15:0x)
* **What happened.** A built-in helper subagent in the development session (agent type empty)
  triggered the hook, which used the shared `cases/ACTIVE.json` pointer and appended to the
  NVDA trace.
* **Fix.** The line was discarded before any commit, and the hook now records only roles defined
  in `references/roles.yaml` (commit e699198).

## 6. Snapshot coverage (NVDA revision 1)
* **What happened.** gen-mapping correctly rejected the stale `MarketableSecuritiesCurrent`. But
  the catalog-only snapshot lacked `DebtSecuritiesCurrent` and `EquitySecuritiesFvNi`, so net cash
  left out about $77bn. crit-assumption raised asm-001 (major), and the round-2 specialists
  reported it as unresolvable in code rather than inventing a figure.
* **Fix.** Snapshots keep every concept the company reports, and lines may map to summed
  concepts (commit 1d2ba30). The case was re-opened as revision 2 (`--revision 2 --reason …`).
  Revision 2 passed two clean reviews and was published. Revision 1 is kept unchanged as
  evidence of the bounded loop.

## 7. Controller defects found by the live run (15:08)
* **What happened.** The run stopped on a traceback and recorded it instead of patching
  (`cases/RUN_NOTES.md`). The defects were: text guidance crashed `gate_quotes`; weighted-average
  share counts were differenced into negative Q4 values; a range midpoint was flagged as missing
  from its quote; and cover-page share counts were reported stale.
* **Fix.** Commit 9240e7c, with regression tests. The run resumed and kept the completed
  specialist reports.
* **Fifth defect (AMD, 16:10).** `gate_quotes` compared guidance at one decimal, so AMD's
  "Operating Expenses ~$3.75 Billion", correctly recorded as 3.75e9, was flagged as "3.8 not
  visible" and sent to repair. A repair could have "fixed" a correct value into a wrong one.
  The gate now accepts the value only in forms that equal it exactly (3.75, not 3.8) and as a
  whole number (not inside 13.75). The round-001 inputs of NVDA r2 and AMD recompute with no
  findings.
* **Consequence: a false stop (16:15).** The fix reached the branch while AMD round 2 was
  already running, and the run pulls only after a submit. gen-narrative correctly kept 3.75e9.
  The old gate flagged it again, and the controller stopped the case as STALLED ("same open
  findings across 2 repairs"). The stop rule worked as designed; its input was a defective
  gate. AMD's round-2 inputs pass the fixed gate. The stall stays on record. Opening a revision
  (`--revision 2 --reason "gate defect fixed in 6fddfe2"`) is the documented way to continue
  the case. Lesson: a controller fix that changes a verdict should reach running cases before
  their next submit. A run should pull at the start of each round, not only after a submit.

## 8. AMD run idle after the recovery test (14:58–15:48)
* **Timeline (from `cases/AMD-0000002488-26-000191/trace.jsonl` and commits).**
  14:55:04 case opened · 14:55:43 gen-mapping and gen-narrative started · 14:56:08/14:56:16 both
  finished · 14:56:24 gen-model started · about 14:57 the coordinating session interrupted the
  run on purpose (recovery test) and sent a resume instruction · 14:58:01 gen-model's stop event,
  with no report · 15:12 the run committed a late hook line and went idle, asking for
  confirmation · 15:48 the owner asked about AMD, the coordinating session found the stall and
  sent an explicit go-ahead.
* **Impact.** About 50 minutes without progress. **No loss of state:** the case stayed at
  `GENERATOR_PENDING` with request `gen-20261114T145504-830038`. The two completed reports were
  intact, and `eu.py resume` names only the three missing specialists.
* **Root cause (corrected after a second stall).** The first diagnosis was that two instructions
  sent close together had left the session waiting for confirmation. The run's transcript shows
  otherwise. The platform treats a message from another session (`send_message`) as **data, not
  as an instruction**, so a session does not push or resume solely because a peer asks. The AMD
  session therefore correctly waited for a human after each of the coordinator's messages
  (15:48 and 15:57). The second time it also reported a pull conflict on `cases/ACTIVE.json`,
  a per-session runtime pointer that was wrongly tracked by git. The deeper gap is the same:
  saved state guarantees that work **can** resume, but nothing guaranteed that someone **would**.
  The stall was found by a person asking, not by the system.
* **Second stall (15:48–15:58).** Two more coordinator messages were received and, correctly,
  not acted on. `cases/ACTIVE.json` is now git-ignored (commit 6ad1ad1). The case was handed to
  a **new session whose initial task is the resume** (Live run 5, 15:59), the same way NVDA moved
  from run 1 to run 2. A session's assigned task is an instruction. A peer's message is not.
* **Fix.** `eu.py watchdog --minutes N` lists cases with an outstanding request and no trace
  activity for N minutes, and exits with code 1 so a scheduler can alert or start a resume
  session (test `WatchdogTests`). Its first run on the real repository at 15:51 reported:

  ```json
  {"case_id": "AMD-0000002488-26-000191", "status": "GENERATOR_PENDING", "round": 1,
   "idle_minutes": 53.1, "last_event_at": "2026-11-14T14:58:01Z",
   "pending_request": "gen-20261114T145504-830038"}
  ```
  The NVDA revision-1 case, which was active at the time, was correctly not reported.
* **Lesson for operation.** To resume a stalled run, start a session whose initial task is the
  resume, or have the human answer the stalled session. Do not rely on cross-session messages.
  Give one complete instruction. Detect stalls with the watchdog: run on a schedule, it finds a
  stall within one interval instead of when someone happens to ask. Without a schedule, the
  coordinating session's own monitor now wakes on "pending and idle for 12 minutes" as well as
  on state changes (the earlier monitor watched only state changes, which a stalled case never
  produces). Planned next: a Stop hook in run sessions that will not let a session end its turn
  while its case has an unrecorded pending request, and `eu.py hold --reason` to make an
  intentional pause explicit.
