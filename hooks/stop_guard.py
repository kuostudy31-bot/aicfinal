#!/usr/bin/env python3
"""Stop hook: a run session may not end its turn while its case silently waits.

Blocks (exit 2, reason on stderr) only when all of these hold:
  * this checkout's cases/ACTIVE.json names a case,
  * that case is GENERATOR_PENDING or CRITIC_PENDING and has no recorded hold,
  * this very session dispatched workflow agents for that case (its session_id appears in
    the case trace), so coordinating or development sessions are never blocked,
  * the hook has not already blocked this stop (stop_hook_active is false), so a session
    that still needs to stop after being told is let through and the fact is logged.
The message tells the session to resume, or to record why it must stop
(eu.py hold --reason ...), which the watchdog then reports as accounted for.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[1])


def log(rec):
    logs = ROOT / ".logs"
    logs.mkdir(exist_ok=True)
    rec["ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(logs / "stop_guard.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        return 0
    try:
        active = json.loads((ROOT / "cases" / "ACTIVE.json").read_text())
    except Exception:  # noqa: BLE001
        return 0
    case = active.get("case_id")
    if not case:
        return 0
    cdir = ROOT / "cases" / case
    try:
        state = json.loads((cdir / "state.json").read_text())
    except Exception:  # noqa: BLE001
        return 0
    if state.get("status") not in ("GENERATOR_PENDING", "CRITIC_PENDING") or state.get("hold"):
        return 0
    sid = payload.get("session_id")
    mine = False
    if sid and (cdir / "trace.jsonl").exists():
        for line in (cdir / "trace.jsonl").read_text(encoding="utf-8").splitlines():
            if f'"session_id": "{sid}"' in line:
                mine = True
                break
    if not mine:
        return 0
    if payload.get("stop_hook_active"):
        log({"case": case, "session_id": sid, "decision": "allowed after one block"})
        return 0
    log({"case": case, "session_id": sid, "decision": "blocked", "status": state["status"]})
    print(
        f"Case {case} has an outstanding {state['status']} request "
        f"{(state.get('pending') or {}).get('request_id')} and no recorded hold. Do not end your turn "
        f"while it silently waits. Run `python3 scripts/eu.py resume --case {case}` and continue from "
        f"its next_action. If you genuinely must stop (an error to fix, a decision only the owner can "
        f"make), first record it: `python3 scripts/eu.py hold --case {case} --reason \"<why>\"`, then "
        "commit and push the case directory.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
