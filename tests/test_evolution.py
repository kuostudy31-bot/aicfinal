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


class SpelledFractionTests(unittest.TestCase):
    def test_fractions_flagged_period_names_not(self):
        self.assertEqual(len(evolution.spelled_quantities("margin moves roughly half a percentage point")), 1)
        self.assertEqual(evolution.spelled_quantities("in the first half of fiscal 2027 and the fourth quarter"), [])


class DiscriminationTests(unittest.TestCase):
    """evaluate() with several samples per arm and require_baseline_failure (change-003 design)."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "prompts" / "gen-writer").mkdir(parents=True)
        (self.root / "prompts" / "gen-writer" / "candidate-change-001.md").write_text("candidate\n")
        (self.root / "cases").mkdir()
        self.patches = [mock.patch.object(evolution, "ROOT", self.root),
                        mock.patch.object(evolution, "CHANGES", self.root / "evolution" / "changes"),
                        mock.patch.object(evolution.subprocess, "run",
                                          return_value=mock.Mock(returncode=0, stderr="OK"))]
        for p in self.patches:
            p.start()
        self.cd = self.root / "evolution" / "changes" / "change-001"
        write_json(self.cd / "failure.json", {
            "change_id": "change-001", "role": "gen-writer", "parent_version": "v2",
            "acceptance_checks": {"required_phrases": [], "required_placeholders": [],
                                  "forbid_spelled_quantities": True},
            "evaluation_cases": {"development": ["C1"], "held_out": []},
            "evaluation_design": {"withheld_keys": ["rating_outperform_min"], "samples_per_arm": 2,
                                  "require_baseline_failure": True}})
        write_json(self.cd / "proposal.json", {"candidate_path": "prompts/gen-writer/candidate-change-001.md"})
        write_json(self.cd / "status.json", {"change_id": "change-001", "state": "PREPARED", "request_id": "evo-1",
                                             "role": "gen-writer", "parent_version": "v2"})
        with open(self.cd / "trace.jsonl", "w") as fh:
            for t in ("gen-lead", "evo-proposer", "gen-writer"):
                fh.write(json.dumps({"event": "SubagentStart", "agent_type": t, "request_id": "evo-1"}) + "\n")
        inp = self.cd / "runs" / "C1" / "inputs"
        write_json(inp / "values.json", {"upside": {"value": 0.2, "display": "20%"}})
        write_json(inp / "narrative.json", {"quotes": []})

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.root)

    def notes(self, baseline, candidate):
        for arm, texts in (("baseline", baseline), ("candidate", candidate)):
            for k, t in enumerate(texts, 1):
                p = self.cd / "runs" / "C1" / arm / evolution._sample_name("note", k, "md")
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(t)

    def test_passes_only_when_baseline_reproduces_failure(self):
        good, bad = "Upside is {{upside}}.", "Outperform means fifteen percent upside."
        self.notes([good, good], [good, good])
        self.assertFalse(evolution.evaluate("change-001")["evaluation_pass"])  # arms not separated
        self.notes([good, bad], [good, good])
        ev = evolution.evaluate("change-001")
        self.assertTrue(ev["baseline_reproduces_failure"])
        self.assertTrue(ev["evaluation_pass"])
        self.assertEqual(ev["rows"][0]["baseline"]["samples_passed"], 1)

    def test_one_failing_candidate_sample_fails(self):
        self.notes(["Outperform means fifteen percent upside."] * 2, ["Upside is {{upside}}.", "fifteen percent"])
        self.assertFalse(evolution.evaluate("change-001")["evaluation_pass"])
