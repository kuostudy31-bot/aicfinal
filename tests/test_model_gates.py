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


class SumSeriesTests(unittest.TestCase):
    def test_sum_keeps_only_periods_with_all_components(self):
        from aicfinal.model import sum_series
        a = [{"end": "2026-04-26", "val": 1, "id": "F-a1"}, {"end": "2026-07-26", "val": 2, "id": "F-a2"}]
        b = [{"end": "2026-07-26", "val": 10, "id": "F-b2"}]
        out = sum_series([a, b])
        self.assertEqual([(o["end"], o["val"]) for o in out], [("2026-07-26", 12)])
        self.assertEqual(out[0]["components"], ["F-a2", "F-b2"])
        self.assertTrue(out[0]["id"].startswith("S-"))


class TextGuidanceTests(unittest.TestCase):
    def test_text_guidance_does_not_crash_the_gate(self):
        docs = {"r.txt": "We are not assuming any Data Center compute revenue from China in our outlook."}
        nar = {"quotes": [{"id": "Q-2", "doc": "r.txt",
                           "text": "We are not assuming any Data Center compute revenue from China in our outlook."}],
               "guidance": [{"metric": "china_dc", "value": "none assumed", "unit": "text", "quote_id": "Q-2"}]}
        self.assertEqual(gates.gate_quotes(nar, docs), [])


class RangeGuidanceTests(unittest.TestCase):
    def test_midpoint_visible_through_low_and_high(self):
        docs = {"r.txt": "we expect tax rates to be between 16.0% and 18.0%, excluding discrete items."}
        q = {"id": "Q-5", "doc": "r.txt", "text": "we expect tax rates to be between 16.0% and 18.0%"}
        ok = {"quotes": [q], "guidance": [{"metric": "tax", "value": 0.17, "low": 0.16, "high": 0.18,
                                            "unit": "ratio", "quote_id": "Q-5"}]}
        bad = {"quotes": [q], "guidance": [{"metric": "tax", "value": 0.17, "low": 0.15, "high": 0.19,
                                             "unit": "ratio", "quote_id": "Q-5"}]}
        self.assertEqual(gates.gate_quotes(ok, docs), [])
        self.assertEqual(gates.gate_quotes(bad, docs)[0]["check"], "guidance_source")


class GuidancePrecisionTests(unittest.TestCase):
    def test_two_decimal_guidance_is_visible(self):  # AMD: "Operating Expenses ~$3.75 Billion"
        q = {"id": "Q-3", "doc": "r.txt", "text": "Operating Expenses ~$3.75 Billion"}
        docs = {"r.txt": q["text"]}
        ok = {"quotes": [q], "guidance": [{"metric": "opex", "value": 3.75e9, "unit": "USD", "quote_id": "Q-3"}]}
        rounded = {"quotes": [q], "guidance": [{"metric": "opex", "value": 3.8e9, "unit": "USD", "quote_id": "Q-3"}]}
        self.assertEqual(gates.gate_quotes(ok, docs), [])
        self.assertEqual(gates.gate_quotes(rounded, docs)[0]["check"], "guidance_source")  # rounding is not exact

    def test_no_partial_number_match(self):
        q = {"id": "Q-1", "doc": "r.txt", "text": "Revenue is expected to be $13.75 billion"}
        bad = {"quotes": [q], "guidance": [{"metric": "rev", "value": 3.75e9, "unit": "USD", "quote_id": "Q-1"}]}
        self.assertEqual(gates.gate_quotes(bad, {"r.txt": q["text"]})[0]["check"], "guidance_source")


class RatingBandValueTests(unittest.TestCase):
    def test_rating_bands_are_code_supplied(self):
        meta = {"rating_bands": {"outperform_min": 0.15, "underperform_max": -0.10}}
        q = {"start": "2026-04-01", "end": "2026-06-30", "fiscal": "FY2026Q2", "calendar": "CY2026Q2"}
        h = {"quarters": [q] * 5, "lines": {k: [{"val": 2.0, "id": f"F-{k}"}] * 5 for k in
                                             ("revenue", "net_income", "eps_diluted", "cfo", "capex", "gross_profit",
                                              "operating_income")}}
        fc = {"quarters": [{"label": "FY2026Q3", "revenue": 1.0, "eps": 1.0}], "ntm": {"revenue": 4.0, "eps": 4.0}}
        val = {"target_price": 10, "price": 8.0, "upside": 0.25, "rating": "Outperform", "net_cash": 0.0,
               "dcf": {"per_share": 9.0, "terminal_share_of_ev": 0.6}, "peer_median_ev_sales": None,
               "prior_target_price": None}
        out = values.build("X", h, fc, val, {}, meta)
        self.assertEqual(out["rating_outperform_min"]["display"], "+15%")
        self.assertEqual(out["rating_underperform_max"]["display"], "-10%")


class TenKFourthQuarterTests(unittest.TestCase):
    """A 10-K tags diluted shares and EPS for the fiscal year only: the derived Q4 has none."""

    def hist(self):
        v = lambda x, i: {"val": x, "id": i, "derived": False}  # noqa: E731
        return {"quarters": [{}, {}], "lines": {
            "net_income": [v(1000.0, "n3"), v(2000.0, "n4")],
            "diluted_shares": [v(100.0, "s3"), None],
            "eps_diluted": [v(10.0, "e3"), None]}}

    def test_latest_skips_missing_fourth_quarter(self):
        from aicfinal.model import latest
        self.assertEqual(latest(self.hist(), "diluted_shares")["id"], "s3")

    def test_eps_gate_compares_one_quarter(self):
        from aicfinal.gates import gate_eps
        self.assertEqual(gate_eps(self.hist()), [])  # Q3 vs Q3, not Q4 income over Q3 shares


class PerShareGuidanceTests(unittest.TestCase):
    """MU guides EPS in dollars per share; the gate must not scale it to billions (incidents #14)."""

    def gate(self, g, text):
        narrative = {"quotes": [{"id": "Q-4", "doc": "d.txt", "text": text}], "guidance": [g]}
        return [x["id"] for x in gates.gate_quotes(narrative, {"d.txt": text})]

    def test_eps_guidance_tagged_usd_is_visible(self):
        g = {"metric": "eps_next_q", "value": 37.84, "unit": "USD", "quote_id": "Q-4", "low": 36.84, "high": 38.84}
        self.assertEqual(self.gate(g, "Diluted EPS $37.84 ± $1.00"), [])

    def test_explicit_units(self):
        self.assertEqual(self.gate({"metric": "e", "value": 38.15, "unit": "USD/share", "quote_id": "Q-4"},
                                   "EPS of $38.15"), [])
        self.assertEqual(self.gate({"metric": "s", "value": 1.67e9, "unit": "shares", "quote_id": "Q-4"},
                                   "approximately 1.67 billion shares"), [])
        self.assertEqual(self.gate({"metric": "s", "value": 1.67e9, "unit": "shares", "quote_id": "Q-4"},
                                   "approximately 1,670 million shares"), ["gate-guidance-s"])  # comma form not matched

    def test_display_of_per_share_guidance(self):
        from aicfinal.gates import guidance_unit
        self.assertEqual(guidance_unit({"value": 37.84, "unit": "USD"}), "USD/share")
        self.assertEqual(guidance_unit({"value": 108e9, "unit": "USD"}), "USD")


class TenKStaleGateTests(unittest.TestCase):
    def test_fiscal_q4_without_eps_is_not_stale(self):
        h = {"quarters": [{"fiscal": "FY2026Q3"}, {"fiscal": "FY2026Q4"}],
             "lines": {"eps_diluted": [v(24.67), None], "other_line": [v(1.0), None]}}
        ids = [x["id"] for x in gates.gate_mapping(h)]
        self.assertNotIn("gate-stale-eps_diluted", ids)
        self.assertIn("gate-stale-other_line", ids)

    def test_mid_year_gap_is_still_stale(self):
        h = {"quarters": [{"fiscal": "FY2026Q2"}, {"fiscal": "FY2026Q3"}], "lines": {"eps_diluted": [v(12.07), None]}}
        self.assertIn("gate-stale-eps_diluted", [x["id"] for x in gates.gate_mapping(h)])
