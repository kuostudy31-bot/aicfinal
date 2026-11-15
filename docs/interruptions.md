# Register of interruptions

Every interruption of the workflow: what stopped, the saved state at that moment, how work
resumed, and what was kept or redone. Times are UTC. Type: **planned** (a deliberate recovery
test), **unplanned** (platform, quota or defect), **owner** (paused by the owner).

The resume guarantee in every row comes from the same mechanism. State is saved at each
transition. `eu.py resume` verifies the snapshot and artifact hashes and names the single next
action, and only missing reports are re-dispatched under the same request ID. The traces hold
the inspections: AMD r1 has 14 `resume_inspected` events, NVDA r1 has 9, NVDA r2 has 8 and
AMD r2 has 5.

| # | When | What stopped | Type | State at the stop | How it resumed | Kept / redone | Evidence |
|---|---|---|---|---|---|---|---|
| 1 | 2026-11-14 14:48 | Live run 1 (NVDA r1): orchestrator had no Agent tool | unplanned (platform nesting limit) | GENERATOR_PENDING, round 1, request `gen-20261114T144812-0d99ea`, no reports | 14:51, Live run 2 in a new session, after the spawn depth was raised to 3 | Nothing to keep; same request ID reused | `cases/RUN_NOTES.md`, incidents #2 |
| 2 | 2026-11-14 15:08 | Live run 2 (NVDA r1): `eu.py compute` traceback | unplanned (controller defect) | GENERATOR_PENDING, round 1; mapping, narrative, model and valuation reports done | about 15:13, same session, after fix 9240e7c (`resume` named only gen-writer) | **Kept 4 reports; re-dispatched gen-writer only** | `cases/RUN_NOTES.md` ("Resume after controller fix"), incidents #7 |
| 3 | 2026-11-14 about 14:57 | Live run 3 (AMD r1), interrupted by the coordinator during gen-model | **planned** (recovery test) | GENERATOR_PENDING, round 1; mapping and narrative done; gen-model stopping | 15:59, Live run 5 in a new session (after the idle period, #4) | **Kept 3 reports (gen-model had finished writing); re-dispatched gen-valuation and gen-writer** | `cases/AMD-0000002488-26-000191/RUN_NOTES.md` ("Interruption and resume", verbatim `resume` output), trace |
| 4 | 2026-11-14 14:58–15:59 | AMD r1 sat idle after #3 (two stalls) | unplanned (peer messages are not instructions; tracked runtime pointer) | unchanged from #3 | handed over to Live run 5 | none lost | incidents #8 |
| 5 | 2026-11-14 16:20 | Live run 6 (evolution change-001), interrupted at the owner's request | **owner** | prepare not yet committed; nothing pushed | 2026-11-15 02:11, Live run 7 in a new session, from the start | nothing to keep | `docs/HANDOVER.md` ("Paused by the owner"), `docs/rejections.md` |
| 6 | 2026-11-14 about 16:20 → 20:10 | The whole workflow: the five-hour usage quota was exhausted (a run session reported `rejected`, overage) | unplanned (quota) | No run mid-flight (run 6 already paused). All case state committed and pushed. HANDOVER written at 16:08 | A one-shot scheduled wake-up (trigger `trig_0193Ab9zLhWFXzHZLCGhXXXa`) fired at 20:16 and the coordinator resumed from HANDOVER. The owner gave new instructions on 2026-11-15 about 02:10 | none lost | `docs/HANDOVER.md` ("Scheduled wake-up"), commit timestamps |
| 7 | 2026-11-15 02:12–02:52 | Live run 8 (AMD r2) stopped before opening the case | unplanned (task conflicted with a stale HANDOVER line) | case not yet opened | Live run 10, 02:52, in a new session | nothing to keep | incidents #9 |
| 8 | 2026-11-15 02:13 | Live run 9 tried to end its turn with the verification case pending | **planned** (Stop-hook test) | GENERATOR_PENDING, gen-mapping done | Stop hook blocked; the session recorded a hold, then released and stopped the throwaway case | n/a | `docs/verification/stop_hook.md` |

Not interruptions: NVDA r1 and AMD r1 ended **STALLED**. Those are terminal decisions by the
controller (`docs/rejections.md`); the cases were continued as new revisions, not resumed.

Lessons recorded elsewhere: one complete instruction per resume, and a new session for a stalled
run (#4, #7). A watchdog and a Stop hook catch silent idling (#4). Update HANDOVER before a run
that depends on a changed decision (#7). Commit and push after every submit, so that a quota stop
(#6) loses nothing.
