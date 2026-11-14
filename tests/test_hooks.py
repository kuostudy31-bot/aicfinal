"""The state-guard hook refuses writes to control files but allows reads."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "guard_state.py"
CTRL = "cases/X/" + "state.json"  # built at runtime so this file itself is not a 'write'


def run(tool, **inp):
    p = subprocess.run([sys.executable, str(HOOK)], input=json.dumps({"tool_name": tool, "tool_input": inp}),
                       capture_output=True, text=True)
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
