"""The state-guard hook refuses writes to control files but allows reads."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "guard_state.py"
CTRL = "cases/X/" + "state.json"  # built at runtime so this file itself is not a 'write'


def run(tool, **inp):
    """Run the hook against an empty temporary project, never the real repository."""
    import os
    import tempfile
    env = dict(os.environ, CLAUDE_PROJECT_DIR=tempfile.mkdtemp())
    p = subprocess.run([sys.executable, str(HOOK)], input=json.dumps({"tool_name": tool, "tool_input": inp}),
                       capture_output=True, text=True, env=env)
    return p.returncode


class GuardTests(unittest.TestCase):
    def test_refuses_writes(self):
        self.assertEqual(run("Write", file_path="/repo/" + CTRL), 2)
        self.assertEqual(run("Bash", command="echo {} > " + CTRL), 2)
        self.assertEqual(run("Bash", command=f"python3 -c \"open('{CTRL}','w')\""), 2)
        self.assertEqual(run("Bash", command="cp a cases/X/result.json"), 2)

    def test_allows_reads_and_controller(self):
        self.assertEqual(run("Bash", command="grep -c x cases/X/trace.jsonl 2>/dev/null"), 0)
        self.assertEqual(run("Bash", command="python3 -c 'import json; print(json.dumps(1))' " + CTRL), 0)
        self.assertEqual(run("Bash", command="python3 scripts/eu.py submit --case X"), 0)
        self.assertEqual(run("Write", file_path="/repo/cases/X/rounds/round-001/generator/note.md"), 0)


if __name__ == "__main__":
    unittest.main()


class GuardRecordTests(unittest.TestCase):
    def test_refusal_is_recorded_in_log_and_active_trace(self):
        import os
        import tempfile
        root = Path(tempfile.mkdtemp())
        (root / "cases" / "X").mkdir(parents=True)
        (root / "cases" / "ACTIVE.json").write_text(json.dumps({"case_id": "X", "phase": "generator"}))
        (root / "cases" / "X" / "state.json").write_text(json.dumps({"status": "GENERATOR_PENDING"}))
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(root))
        p = subprocess.run([sys.executable, str(HOOK)], env=env, capture_output=True, text=True,
                           input=json.dumps({"tool_name": "Write", "session_id": "S1",
                                             "tool_input": {"file_path": str(root / CTRL)}}))
        self.assertEqual(p.returncode, 2)
        self.assertIn("guard_refused", (root / ".logs" / "guard_refusals.jsonl").read_text())
        self.assertIn("guard_refused", (root / "cases" / "X" / "trace.jsonl").read_text())


class AuditPointerTests(unittest.TestCase):
    """The dispatch-audit hook records into a case trace only while that case is pending."""

    def dispatch(self, status):
        import os
        import tempfile
        root = Path(tempfile.mkdtemp())
        (root / "cases" / "X").mkdir(parents=True)
        (root / "references").mkdir()
        (root / "references" / "roles.yaml").write_text("roles:\n  gen-writer:\n    phase: generator\n")
        (root / "cases" / "ACTIVE.json").write_text(json.dumps({"case_id": "X", "phase": "critic"}))
        (root / "cases" / "X" / "state.json").write_text(json.dumps({"status": status}))
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(root))
        subprocess.run([sys.executable, str(HOOK.parent / "audit_event.py")], env=env, capture_output=True,
                       text=True, input=json.dumps({"hook_event_name": "SubagentStart", "agent_type": "gen-writer"}))
        return (root / "cases" / "X" / "trace.jsonl").exists()

    def test_pending_case_gets_the_record(self):
        self.assertTrue(self.dispatch("CRITIC_PENDING"))

    def test_stale_pointer_to_finished_case_is_ignored(self):
        self.assertFalse(self.dispatch("STALLED"))
