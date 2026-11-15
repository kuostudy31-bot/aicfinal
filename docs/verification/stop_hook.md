# Live Stop-hook verification — result: PASS

Plan: `docs/HANDOVER.md`, "Proposed (not started): live Stop-hook verification".
Run on 2026-11-15 (UTC) in session `a7b1f44d-3f20-55fd-878c-11c879100055`, branch
`claude/trusting-thompson-r5m3id` at `e6f1a2f`. Throwaway case: `AMD-0000002488-26-000123`.

## Steps
1. `python3 scripts/eu.py open --ticker AMD --accession 0000002488-26-000123` → GENERATOR_PENDING,
   request `gen-20261115T021251-f0fa02` (issued 2026-11-15T02:12:51Z).
2. Dispatched only `gen-mapping` for that request (agent `ae28ba58d181b9d18`). It wrote
   `generator/mapping.json` and `generator/reports/gen-mapping.json`. No other agent was dispatched,
   and the round was not finished.
3. Ended the turn straight away with a one-line status. **The Stop hook blocked that stop** (02:13:37Z).
4. Recorded a hold (02:13:43Z), gathered the evidence, then released and stopped the case.

## The hook's message (verbatim)
```
Stop hook feedback:
[command hook 1]: Case AMD-0000002488-26-000123 has an outstanding GENERATOR_PENDING request gen-20261115T021251-f0fa02 and no recorded hold. Do not end your turn while it silently waits. Run `python3 scripts/eu.py resume --case AMD-0000002488-26-000123` and continue from its next_action. If you genuinely must stop (an error to fix, a decision only the owner can make), first record it: `python3 scripts/eu.py hold --case AMD-0000002488-26-000123 --reason "<why>"`, then commit and push the case directory.

Stop hook feedback:
[command hook 2]: There are untracked files in the repository. Please commit and push these changes to the remote branch.
```
Hook 1 is `hooks/stop_guard.py`. Hook 2 does not come from this repository's `.claude/settings.json`;
it is the cloud environment's own untracked-files check. It is recorded here as received.

## `.logs/stop_guard.jsonl` (copied to `stop_hook.jsonl`)
```
{"case": "AMD-0000002488-26-000123", "session_id": "a7b1f44d-3f20-55fd-878c-11c879100055", "decision": "blocked", "status": "GENERATOR_PENDING", "ts": "2026-11-15T02:13:37Z"}
```
This is the only record. No "allowed after one block" record was written, because the hold was in
place before the next stop. Once a hold exists, the hook returns before it logs anything.

## Case trace lines (`cases/AMD-0000002488-26-000123/trace.jsonl`)
```
{"actor": "hook", "agent_id": "ae28ba58d181b9d18", "agent_type": "gen-mapping", "event": "SubagentStart", "payload_keys": ["agent_id", "agent_type", "cwd", "hook_event_name", "prompt_id", "scratchpad_dir", "session_id", "transcript_path"], "phase": "generator", "request_id": "gen-20261115T021251-f0fa02", "session_id": "a7b1f44d-3f20-55fd-878c-11c879100055", "ts": "2026-11-15T02:12:56Z"}
{"actor": "hook", "agent_id": "ae28ba58d181b9d18", "agent_type": "gen-mapping", "event": "SubagentStop", "payload_keys": ["agent_id", "agent_transcript_path", "agent_type", "background_tasks", "cwd", "effort", "hook_event_name", "permission_mode", "prompt_id", "scratchpad_dir", "session_crons", "session_id", "stop_hook_active", "transcript_path"], "phase": "generator", "request_id": "gen-20261115T021251-f0fa02", "session_id": "a7b1f44d-3f20-55fd-878c-11c879100055", "transcript_copy": "cases/AMD-0000002488-26-000123/evidence/transcripts/gen-mapping-ae28ba58d181b9d18.jsonl", "ts": "2026-11-15T02:13:30Z"}
{"actor": "controller", "by": "run session", "event": "hold_recorded", "reason": "Stop-hook verification test: deliberate pause", "round": 1, "status": "GENERATOR_PENDING", "ts": "2026-11-15T02:13:43Z"}
```

## `python3 scripts/eu.py watchdog --minutes 0` (after the hold)
```
{
  "checked_at": "2026-11-15T02:13:43Z",
  "threshold_minutes": 0,
  "stale": []
}
```
The held case is not listed.

## Pass criteria (from HANDOVER)
- One `blocked` record: **yes**
- Then `hold_recorded`: **yes**
- The session then ends: yes. After the hold, the case was released and stopped
  (`eu.py release`, then `eu.py stop` → USER_STOPPED), so the next stop does not meet the hook's conditions.
- A watchdog run afterwards does not list the case: **yes**

## Housekeeping note
When this session started, the local branch was not an ancestor of the force-updated
`origin/claude/trusting-thompson-r5m3id`. The old local HEAD (`47fec25`) was kept as the local branch
`backup/pre-verification-47fec25` before resetting to `e6f1a2f`. That backup branch has not been pushed.
