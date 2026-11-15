#!/usr/bin/env python3
"""SubagentStart / SubagentStop hook: record who was dispatched, for which request.

Appends one line to the active case's trace.jsonl, tagged with the request_id the
controller marked as active in cases/ACTIVE.json. The controller compares these
records with references/roles.yaml before a submission may advance. The hook only
records; it never blocks and never assesses work (exit 0 always).
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[1])


def _case_pending(case: str) -> bool:
    try:
        st = json.loads((ROOT / "cases" / case / "state.json").read_text())
    except Exception:  # noqa: BLE001
        return False
    return st.get("status") in ("GENERATOR_PENDING", "CRITIC_PENDING")


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        payload = {}
    active_path = ROOT / "cases" / "ACTIVE.json"
    active = {}
    if active_path.exists():
        try:
            active = json.loads(active_path.read_text())
        except Exception:  # noqa: BLE001
            active = {}
    rec = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor": "hook",
        "event": payload.get("hook_event_name"),
        "agent_type": payload.get("agent_type") or payload.get("subagent_type"),
        "agent_id": payload.get("agent_id"),
        "session_id": payload.get("session_id"),
        "request_id": active.get("request_id"),
        "phase": active.get("phase"),
        "payload_keys": sorted(payload.keys()),
    }
    logs = ROOT / ".logs"
    logs.mkdir(exist_ok=True)
    with open(logs / "hook_events.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
    # Only workflow roles are case evidence; other subagents (built-in helpers, other
    # sessions' tooling) go to the local log only.
    known = set()
    try:
        import re
        known = set(re.findall(r"^  ([a-z][a-z-]+):", (ROOT / "references" / "roles.yaml").read_text(), re.M))
    except OSError:
        pass
    if rec["agent_type"] not in known:
        return
    case = active.get("case_id")
    target = None
    if active.get("trace_path"):
        target = ROOT / active["trace_path"]           # evolution changes
    elif case and (ROOT / "cases" / case).is_dir() and _case_pending(case):
        # A stale pointer left by a finished case must not attract records (incidents #13).
        target = ROOT / "cases" / case / "trace.jsonl"
    if target is not None and target.parent.is_dir():
        # Evidence of separate contexts: keep each finished subagent's own transcript.
        src = payload.get("agent_transcript_path")
        if payload.get("hook_event_name") == "SubagentStop" and src and Path(src).is_file():
            dest = target.parent / "evidence" / "transcripts"
            dest.mkdir(parents=True, exist_ok=True)
            name = f"{rec['agent_type']}-{rec['agent_id']}.jsonl"
            try:
                (dest / name).write_bytes(Path(src).read_bytes())
                rec["transcript_copy"] = str((dest / name).relative_to(ROOT))
            except OSError as exc:
                rec["transcript_copy_error"] = str(exc)
        with open(target, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
    sys.exit(0)
