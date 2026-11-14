"""Deterministic tests for valuation arithmetic, gates and note rendering."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aicfinal import gates, valuation, values  # noqa: E402


def v(val, fid="F-x"):
    return {"val": val, "id": fid, "derived": False, "components": [fid], "formula": None}


class DcfTests(unittest.TestCase):
    def test_hand_checkable_dcf(self):
        # one explicit year: FCF 10, wacc 10%, g 0 -> PV 9.0909 + TV 100/1.1 = 100
        d = valuation.dcf(100.0, {"revenue_growth": [], "fcf_margin": [0.1], "wacc": 0.10,
                                  "terminal_growth": 0.0}, net_cash=0.0, shares=1.0)
        self.assertAlmostEqual(d["enterprise_value"], 100.0, places=6)

    def test_terminal_growth_must_be_below_wacc(self):
        with self.assertRaises(ValueError):
            valuation.dcf(100.0, {"revenue_growth": [], "fcf_margin": [0.1], "wacc": 0.05,
                                  "terminal_growth": 0.05}, 0.0, 1.0)


class GateTests(unittest.TestCase):
    def hist(self, assets=100, le=100):
        q = {"start": "2026-04-01", "end": "2026-06-30", "fiscal": "FY2026Q2", "calendar": "CY2026Q2"}
        lines = {k: [v(1)] for k in ("revenue", "operating_income", "net_income", "diluted_shares",
                                      "cfo", "capex", "cash")}
        lines["assets"], lines["liabilities_and_equity"] = [v(assets)], [v(le)]
        return {"quarters": [q], "lines": lines}

    def test_balance_gate(self):
        self.assertEqual(gates.gate_balance(self.hist()), [])
        self.assertEqual(gates.gate_balance(self.hist(le=90))[0]["severity"], "blocker")

    def test_stale_mapping_is_reported(self):
        h = self.hist()
        h["quarters"].insert(0, dict(h["quarters"][0], end="2026-03-31"))
        h["lines"]["short_term_investments"] = [v(5), None]
        ids = [x["id"] for x in gates.gate_mapping(h)]
        self.assertIn("gate-stale-short_term_investments", ids)

    def test_untagged_number_is_flagged_but_labels_are_not(self):
        vals = {"revenue_q": {"display": "$1.0bn", "value": 1e9, "sources": ["F-1"]}}
        ok = "Revenue in FY2027 Q2 (CY2026Q2) was {{revenue_q}} per the 10-Q."
        bad = ok + " Margins were 74% last year."
        self.assertEqual(gates.gate_note(ok, vals, {}), [])
        self.assertEqual(gates.gate_note(bad, vals, {})[0]["check"], "untagged_number")

    def test_unknown_placeholder_is_blocker(self):
        out = gates.gate_note("TP is {{target_price}}.", {}, {})
        self.assertEqual(out[0]["id"], "gate-note-missing-target_price")

    def test_quote_must_be_verbatim(self):
        docs = {"r.txt": "Revenue is expected to be $108.0 billion, plus or minus 2%."}
        good = {"quotes": [{"id": "Q-1", "doc": "r.txt", "text": "Revenue is expected to be $108.0 billion"}],
                "guidance": [{"metric": "rev", "value": 108.0e9, "unit": "USD", "quote_id": "Q-1"}]}
        bad = {"quotes": [{"id": "Q-1", "doc": "r.txt", "text": "Revenue is expected to be $110.0 billion"}]}
        self.assertEqual(gates.gate_quotes(good, docs), [])
        self.assertEqual(gates.gate_quotes(bad, docs)[0]["check"], "quote_verbatim")


class RenderTests(unittest.TestCase):
    def test_render_substitutes_values_and_quotes(self):
        text, missing = values.render("TP {{tp}}; [[Q-1]]", {"tp": {"display": "$5"}},
                                      {"Q-1": {"text": "hello"}})
        self.assertEqual(missing, [])
        self.assertEqual(text, "TP $5; “hello”")


if __name__ == "__main__":
    unittest.main()
