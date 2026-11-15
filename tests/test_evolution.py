"""Evolution controller: submit gating, adoption, versioning and rollback (no LLM, no network)."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aicfinal import evolution  # noqa: E402
from aicfinal.util import read_json, write_json  # noqa: E402


class EvolutionTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "prompts" / "gen-writer").mkdir(parents=True)
        (self.root / "prompts" / "gen-writer" / "v1.md").write_text("v1 text\n")
        (self.root / "prompts" / "gen-writer" / "v2.md").write_text("v2 text\n")
        (self.root / "prompts" / "gen-writer" / "candidate-change-001.md").write_text("v2 text\nplus a fix\n")
        write_json(self.root / "prompts" / "registry.json", {"active": {"gen-writer": "v2"}, "history": []})
        (self.root / "cases").mkdir()
        self.patches = [mock.patch.object(evolution, "ROOT", self.root),
                        mock.patch.object(evolution, "CHANGES", self.root / "evolution" / "changes"),
                        mock.patch.object(evolution, "REGISTRY", self.root / "prompts" / "registry.json")]
        for p in self.patches:
            p.start()
        self.cd = self.root / "evolution" / "changes" / "change-001"
        write_json(self.cd / "failure.json", {"change_id": "change-001", "role": "gen-writer", "parent_version": "v2"})
        write_json(self.cd / "proposal.json", {"candidate_path": "prompts/gen-writer/candidate-change-001.md"})
        write_json(self.cd / "evaluation.json", {"evaluation_pass": True})

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.root)

    def status(self, state, **kw):
        write_json(self.cd / "status.json", {"change_id": "change-001", "state": state, "role": "gen-writer",
                                             "request_id": "evo-1", "review_request_id": "evoc-1", **kw})

    def review(self, verdict, dispatched=True, rid="evoc-1"):
        write_json(self.cd / "review.json", {"request_id": rid, "verdict": verdict})
        if dispatched:
            with open(self.cd / "trace.jsonl", "a") as fh:
                for t in ("crit-lead", "evo-reviewer"):
                    fh.write(json.dumps({"event": "SubagentStart", "agent_type": t, "request_id": "evoc-1"}) + "\n")

    # submit -------------------------------------------------------------
    def test_submit_requires_reviewer_dispatch_record(self):
        self.status("EVALUATED")
        self.review("approve-recommended", dispatched=False)
        with self.assertRaises(ValueError):
            evolution.submit("change-001")

    def test_submit_rejects_stale_review(self):
        self.status("EVALUATED")
        self.review("approve-recommended", rid="evoc-old")
        with self.assertRaises(ValueError):
            evolution.submit("change-001")

    def test_reviewer_reject_keeps_active_version(self):
        self.status("EVALUATED")
        self.review("reject")
        self.assertEqual(evolution.submit("change-001")["state"], "REJECTED")
        self.assertEqual(read_json(self.root / "prompts" / "registry.json")["active"]["gen-writer"], "v2")
        with self.assertRaises(ValueError):
            evolution.adopt("change-001", "Owner")

    # adopt / rollback ---------------------------------------------------
    def test_adopt_versions_then_rollback_restores_pointer(self):
        self.status("EVALUATED")
        self.review("approve-recommended")
        self.assertEqual(evolution.submit("change-001")["state"], "AWAITING_APPROVAL")
        with self.assertRaises(ValueError):
            evolution.adopt("change-001", "  ")  # a named approver is required
        st = evolution.adopt("change-001", "Owner")
        self.assertEqual(st["adopted_version"], "v3")
        reg = read_json(self.root / "prompts" / "registry.json")
        self.assertEqual(reg["active"]["gen-writer"], "v3")
        self.assertEqual((self.root / "prompts/gen-writer/v3.md").read_text(), "v2 text\nplus a fix\n")
        self.assertEqual(reg["history"][-1]["suggested_tag"], "prompt-gen-writer-v3")
        with self.assertRaises(ValueError):
            evolution.adopt("change-001", "Owner")  # already adopted
        evolution.rollback("gen-writer", "v2", "Owner", "regression seen in a later case")
        reg = read_json(self.root / "prompts" / "registry.json")
        self.assertEqual(reg["active"]["gen-writer"], "v2")
        self.assertTrue((self.root / "prompts/gen-writer/v3.md").exists())  # both versions kept
        self.assertEqual(reg["history"][-1]["event"], "rollback")

    def test_adopt_refused_if_active_version_moved(self):
        self.status("AWAITING_APPROVAL")
        reg = read_json(self.root / "prompts" / "registry.json")
        reg["active"]["gen-writer"] = "v1"
        write_json(self.root / "prompts" / "registry.json", reg)
        with self.assertRaises(ValueError):
            evolution.adopt("change-001", "Owner")

    def test_rollback_to_missing_version_refused(self):
        with self.assertRaises(ValueError):
            evolution.rollback("gen-writer", "v9", "Owner", "typo")


if __name__ == "__main__":
    unittest.main()


class SpelledQuantityTests(unittest.TestCase):
    def test_flags_spelled_quantities_but_not_ordinary_words(self):
        bad = "Outperform means fifteen percent upside; data as of August twenty-sixth, 2026; minus ten percent."
        self.assertEqual(len(evolution.spelled_quantities(bad)), 3)
        ok = "One of the two segments grew, and the first quarter set a record. [[Q-1]] Upside is {{upside}}."
        self.assertEqual(evolution.spelled_quantities(ok), [])

    def test_quotes_are_exempt(self):
        self.assertEqual(evolution.spelled_quantities("The company said [[Q-7]]."), [])
