#!/usr/bin/env python3
"""PreToolUse hook: keep control state and policy out of agents' reach.

* Control files (state.json, ACTIVE.json, result.json, approvals.jsonl, trace.jsonl)
  may be changed only through scripts/eu.py. Direct Write/Edit is refused, and so is a
  shell command that writes to them without going through the controller.
* While a case has a generator or critic request outstanding, policy files
  (config/, references/, prompts/registry.json) are read-only for everyone.

Refusal = exit code 2 with the reason on stderr (Claude Code shows it to the agent).
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[1])
CONTROL = re.compile(r"(cases/[^\s'\"]*/(state\.json|result\.json|approvals\.jsonl|trace\.jsonl)|cases/ACTIVE\.json)")
POLICY = re.compile(r"(^|/)(config/[^\s'\"]+|references/[^\s'\"]+|prompts/registry\.json)")
# Write operations: a redirect into a project path (not 2>/dev/null), file-moving commands,
# in-place edits and Python writes. A read-only command that merely mentions a control file passes.
WRITE_OPS = re.compile(r"((?<![0-9&])>>?\s*[^\s&|;]*(cases/|config/|references/|prompts/registry)"
                       r"|\btee\b|\bsed\s+-i|\bcp\b|\bmv\b|\brm\b|\btruncate\b"
                       r"|open\([^)]*['\"][wa]\+?['\"]|write_text|write_bytes|json\.dump\()")


def run_active() -> bool:
    """True only if the pointer names a case whose own state is still pending (a stale pointer
    left by a finished case must not lock policy files or attract records)."""
    try:
        active = json.loads((ROOT / "cases" / "ACTIVE.json").read_text())
        if active.get("phase") in ("evo-generator", "evo-critic"):
            return True
        if active.get("phase") not in ("generator", "critic") or not active.get("case_id"):
            return False
        st = json.loads((ROOT / "cases" / active["case_id"] / "state.json").read_text())
        return st.get("status") in ("GENERATOR_PENDING", "CRITIC_PENDING")
    except Exception:  # noqa: BLE001
        return False


def refuse(msg: str, data: dict | None = None):
    """Refuse the tool call and keep a record: .logs/guard_refusals.jsonl always, and the active
    case's trace when a case is active, so refusals are evidence rather than lost terminal text."""
    from datetime import datetime, timezone
    data = data or {}
    rec = {"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "actor": "hook",
           "event": "guard_refused", "tool": data.get("tool_name"), "reason": msg,
           "session_id": data.get("session_id")}
    try:
        (ROOT / ".logs").mkdir(exist_ok=True)
        with open(ROOT / ".logs" / "guard_refusals.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
        active = json.loads((ROOT / "cases" / "ACTIVE.json").read_text())
        if not run_active():
            raise LookupError("no run in progress: record in the local log only")
        target = (ROOT / active["trace_path"]) if active.get("trace_path") else (
            ROOT / "cases" / active["case_id"] / "trace.jsonl" if active.get("case_id") else None)
        if target is not None and target.parent.is_dir():
            with open(target, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, sort_keys=True) + "\n")
    except Exception:  # noqa: BLE001 - recording must never turn a refusal into an allow
        pass
    print(f"Refused by hooks/guard_state.py: {msg}", file=sys.stderr)
    sys.exit(2)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        sys.exit(0)
    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}
    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        path = str(ti.get("file_path") or ti.get("notebook_path") or "")
        rel = path.replace(str(ROOT) + "/", "")
        if CONTROL.search(rel):
            refuse(f"{rel} is controller state; use scripts/eu.py", data)
        if run_active() and POLICY.search(rel):
            refuse(f"{rel} is policy and is read-only while a case request is outstanding", data)
    elif tool == "Bash":
        cmd = str(ti.get("command", ""))
        if "scripts/eu.py" in cmd or "scripts/check.py" in cmd:
            sys.exit(0)
        if CONTROL.search(cmd) and WRITE_OPS.search(cmd):
            refuse("shell writes to controller state are not allowed; use scripts/eu.py", data)
        if run_active() and POLICY.search(cmd) and WRITE_OPS.search(cmd):
            refuse("policy files are read-only while a case request is outstanding", data)
    sys.exit(0)


if __name__ == "__main__":
    main()
