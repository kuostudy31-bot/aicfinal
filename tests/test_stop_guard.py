"""Stop hook: blocks only the run session that owns a silently pending case."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "stop_guard.py"


class StopGuardTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.case = self.root / "cases" / "X-1"
        self.case.mkdir(parents=True)
        (self.root / "cases" / "ACTIVE.json").write_text(json.dumps({"case_id": "X-1"}))
        self.set_state("GENERATOR_PENDING")
        (self.case / "trace.jsonl").write_text(json.dumps({"event": "SubagentStart", "session_id": "S-run"}) + "\n")

    def set_state(self, status, hold=None):
        st = {"status": status, "pending": {"request_id": "gen-1"}}
        if hold:
            st["hold"] = hold
        (self.case / "state.json").write_text(json.dumps(st))

    def run_hook(self, **payload):
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.root))
        p = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), capture_output=True,
                           text=True, env=env)
        return p.returncode, p.stderr

    def test_blocks_the_owning_run_session(self):
        code, err = self.run_hook(session_id="S-run", stop_hook_active=False)
        self.assertEqual(code, 2)
        self.assertIn("eu.py resume --case X-1", err)

    def test_second_stop_is_allowed_to_avoid_a_loop(self):
        self.assertEqual(self.run_hook(session_id="S-run", stop_hook_active=True)[0], 0)

    def test_other_sessions_are_not_blocked(self):
        self.assertEqual(self.run_hook(session_id="S-dev", stop_hook_active=False)[0], 0)

    def test_recorded_hold_or_terminal_case_is_not_blocked(self):
        self.set_state("GENERATOR_PENDING", hold={"reason": "waiting for a fix"})
        self.assertEqual(self.run_hook(session_id="S-run")[0], 0)
        self.set_state("AWAITING_APPROVAL")
        self.assertEqual(self.run_hook(session_id="S-run")[0], 0)


if __name__ == "__main__":
    unittest.main()
