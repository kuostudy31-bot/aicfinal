"""Controller regression tests: transitions, invalid submissions, ledger, limits,
dispatch allowlist, approval and resume. Uses a frozen NVDA snapshot; no network.
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aicfinal import controller, snapshot  # noqa: E402
from aicfinal.util import append_jsonl, read_json, write_json  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures" / "nvda"
GEN_ROLES = ["gen-mapping", "gen-narrative", "gen-model", "gen-valuation", "gen-writer"]
CRIT_ROLES = ["crit-provenance", "crit-assumption", "crit-compliance"]


class Harness(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.patches = [mock.patch.object(controller, "CASES", self.tmp / "cases"),
                        mock.patch.object(controller, "ACTIVE", self.tmp / "cases" / "ACTIVE.json"),
                        mock.patch.object(controller, "ROOT", self.tmp)]
        for p in self.patches:
            p.start()
        # roles.yaml / registry are read relative to controller.ROOT
        (self.tmp / "references").mkdir()
        shutil.copy(Path(controller.__file__).resolve().parents[2] / "references" / "roles.yaml",
                    self.tmp / "references" / "roles.yaml")
        (self.tmp / "prompts").mkdir()
        shutil.copy(Path(controller.__file__).resolve().parents[2] / "prompts" / "registry.json",
                    self.tmp / "prompts" / "registry.json")

        def fake_build(case_dir, ticker, accession, peers):
            dst = Path(case_dir) / "snapshot"
            if not dst.exists():
                shutil.copytree(FIX / "snapshot", dst)
            return read_json(dst / "manifest.json")

        self.patches.append(mock.patch.object(snapshot, "build", fake_build))
        self.patches[-1].start()
        self.st = controller.open_case("NVDA", "0001045810-26-000075", peers=["AMD", "MU"])
        self.cid = self.st["case_id"]

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.tmp)

    # helpers -------------------------------------------------------------
    @property
    def state(self):
        return controller.load_state(self.cid)

    def cdir(self):
        return controller.case_dir(self.cid)

    def dispatch(self, roles, rid=None):
        rid = rid or self.state["pending"]["request_id"]
        for r in roles:
            append_jsonl(self.cdir() / "trace.jsonl", {"event": "SubagentStart", "agent_type": r, "request_id": rid})

    def gen_submit(self, note=None, roles=None, skip=(), stale=False, dispatch=True):
        s = self.state
        rid = s["pending"]["request_id"]
        gdir = self.cdir() / "rounds" / f"round-{s['round']:03d}" / "generator"
        gdir.mkdir(parents=True, exist_ok=True)
        for f in FIX.joinpath("generator").iterdir():
            shutil.copy(f, gdir / f.name)
        if note is not None:
            (gdir / "note.md").write_text(note)
        for r in GEN_ROLES:
            if r in skip:
                continue
            write_json(gdir / "reports" / f"{r}.json",
                       {"request_id": "gen-old" if stale else rid, "role": r, "status": "complete"})
        write_json(gdir / "manifest.json", {"request_id": rid, "files": []})
        if dispatch:
            self.dispatch(roles or ["gen-lead", *GEN_ROLES])
        return controller.submit(self.cid)

    def crit_submit(self, findings=None, resolved=None, verdict="pass", dispatch=True):
        s = self.state
        rid = s["pending"]["request_id"]
        rv = self.cdir() / "rounds" / f"round-{s['round']:03d}" / "reviews" / f"review-{s['review']:02d}"
        for r in CRIT_ROLES:
            rep = {"request_id": rid, "role": r, "candidate_id": s["candidate_id"], "verdict": verdict,
                   "findings": (findings or {}).get(r, []), "resolved": (resolved or {}).get(r, [])}
            write_json(rv / f"{r}.json", rep)
        write_json(rv / "merged.json", {"request_id": rid})
        if dispatch:
            self.dispatch(["crit-lead", *CRIT_ROLES])
        return controller.submit(self.cid)


class OpenAndInvalidTests(Harness):
    def test_open_issues_generator_request_and_is_idempotent(self):
        self.assertEqual(self.st["status"], "GENERATOR_PENDING")
        again = controller.open_case("NVDA", "0001045810-26-000075")
        self.assertEqual(again["pending"]["request_id"], self.st["pending"]["request_id"])

    def test_missing_report_then_blocked(self):
        s1 = self.gen_submit(skip=("gen-writer",))
        self.assertEqual(s1["status"], "GENERATOR_PENDING")
        self.assertEqual(s1["invalid_submissions"], 1)
        s2 = self.gen_submit(skip=("gen-writer",))
        self.assertEqual(s2["status"], "BLOCKED")

    def test_stale_request_id_is_invalid(self):
        s = self.gen_submit(stale=True)
        self.assertEqual(s["invalid_submissions"], 1)

    def test_no_dispatch_record_is_invalid(self):
        self.assertEqual(self.gen_submit(dispatch=False)["invalid_submissions"], 1)

    def test_disallowed_dispatch_is_invalid(self):
        s = self.gen_submit(roles=["gen-lead", *GEN_ROLES, "crit-provenance"])
        self.assertEqual(s["invalid_submissions"], 1)
        err = read_json(next((self.cdir() / "rounds" / "round-001").glob("submission_error_*.json")))
        self.assertTrue(any("crit-provenance" in p for p in err["problems"]))


class LoopTests(Harness):
    def test_gate_failure_triggers_repair_with_packet(self):
        s = self.gen_submit(note="Revenue {{revenue_q}} and a stray 42.\n")
        self.assertEqual((s["status"], s["round"]), ("GENERATOR_PENDING", 2))
        req = read_json(self.cdir() / "rounds" / "round-002" / "request.json")
        self.assertIn("gate-note-untagged-L1", [f["id"] for f in req["repair_packet"]["open_findings"]])
        s = self.gen_submit()  # clean note: the gate finding closes on recompute
        self.assertEqual(s["status"], "CRITIC_PENDING")
        self.assertEqual(self.state["ledger"]["gate-note-untagged-L1"]["status"], "closed")

    def test_two_clean_reviews_then_approval(self):
        self.gen_submit()
        s = self.crit_submit()
        self.assertEqual((s["status"], s["clean_streak"]), ("CRITIC_PENDING", 1))
        s = self.crit_submit()
        self.assertEqual(s["status"], "AWAITING_APPROVAL")
        with self.assertRaises(controller.ControllerError):
            controller.approve(self.cid, " ", "approve", "")
        s = controller.approve(self.cid, "Analyst A", "approve", "Initial publication of the note.")
        self.assertEqual(s["status"], "PUBLISHED")
        self.assertTrue((self.cdir() / "approvals.jsonl").exists())
        with self.assertRaises(controller.ControllerError):
            controller.submit(self.cid)

    def test_critic_finding_stays_open_until_verified(self):
        self.gen_submit()
        f = {"id": "prov-001", "severity": "major", "title": "net cash", "detail": "excludes securities"}
        s = self.crit_submit(findings={"crit-assumption": [f]}, verdict="fail")
        self.assertEqual((s["status"], s["round"]), ("GENERATOR_PENDING", 2))
        self.gen_submit()
        s = self.crit_submit()  # omits prov-001 without verifying: still open -> repair again
        self.assertEqual(self.state["ledger"]["prov-001"]["status"], "open")
        self.assertEqual(s["status"], "STALLED")  # same open set across two repairs

    def test_resolved_finding_closes(self):
        self.gen_submit()
        f = {"id": "prov-001", "severity": "major", "title": "net cash", "detail": "x"}
        self.crit_submit(findings={"crit-assumption": [f]}, verdict="fail")
        self.gen_submit()
        self.crit_submit(resolved={"crit-assumption": [{"id": "prov-001", "evidence": "valuation.json net_cash"}]})
        self.assertEqual(self.state["ledger"]["prov-001"]["status"], "closed")
        self.assertEqual(self.state["clean_streak"], 1)

    def test_round_limit_exhausts(self):
        for i in range(3):  # a different problem each round, so this is not a stall
            note = "Revenue {{revenue_q}}.\n" + "\n" * i + "A stray 7 number.\n"
            s = self.gen_submit(note=note)
        self.assertEqual(s["status"], "EXHAUSTED")
        self.assertIn("round limit", s["stop_reason"])

    def test_tampered_computed_output_is_caught(self):
        s = self.state
        rdir = self.cdir() / "rounds" / "round-001"
        write_json(rdir / "computed" / "valuation.json", {"target_price": 9999})
        s = self.gen_submit()
        self.assertEqual(s["round"], 2)
        self.assertIn("gate-recompute-valuation.json", s["ledger"])


class ResumeTests(Harness):
    def test_resume_names_only_missing_reports(self):
        s = self.state
        gdir = self.cdir() / "rounds" / "round-001" / "generator"
        for r in GEN_ROLES[:2]:
            write_json(gdir / "reports" / f"{r}.json", {"request_id": s["pending"]["request_id"], "role": r})
        rep = controller.resume(self.cid)
        self.assertEqual(rep["reports_present"], GEN_ROLES[:2])
        self.assertEqual(rep["reports_missing"], GEN_ROLES[2:])

    def test_resume_stops_when_verified_evidence_changed(self):
        self.gen_submit()
        p = self.cdir() / "rounds" / "round-001" / "generator" / "assumptions.json"
        d = json.loads(p.read_text()); d["tax_rate"] = 0.01; p.write_text(json.dumps(d))
        self.assertTrue(controller.resume(self.cid)["next_action"].startswith("STOP"))

    def test_user_stop_is_terminal(self):
        s = controller.stop(self.cid, "analyst paused coverage")
        self.assertEqual(s["status"], "USER_STOPPED")
        self.assertIn("none", controller.resume(self.cid)["next_action"])


if __name__ == "__main__":
    unittest.main()


class RevisionTests(Harness):
    def test_revision_needs_reason_and_keeps_earlier_case(self):
        with self.assertRaises(controller.ControllerError):
            controller.open_case("NVDA", "0001045810-26-000075", peers=["AMD"], revision=2)
        st = controller.open_case("NVDA", "0001045810-26-000075", peers=["AMD"], revision=2,
                                  reason="snapshot now keeps all company concepts")
        self.assertEqual(st["case_id"], "NVDA-0001045810-26-000075-r2")
        case = read_json(controller.case_dir(st["case_id"]) / "case.json")
        self.assertEqual(case["supersedes"], "NVDA-0001045810-26-000075")
        self.assertEqual(self.state["status"], "GENERATOR_PENDING")  # original untouched


class WatchdogTests(Harness):
    def test_idle_pending_case_is_reported_and_active_case_is_not(self):
        self.assertEqual(controller.watchdog(minutes=20), [])  # just opened: activity now
        from datetime import timedelta
        later = controller.utcnow() + timedelta(minutes=45)
        with mock.patch.object(controller, "utcnow", return_value=later):
            stale = controller.watchdog(minutes=20)
        self.assertEqual([s["case_id"] for s in stale], [self.cid])
        self.assertGreaterEqual(stale[0]["idle_minutes"], 45)
