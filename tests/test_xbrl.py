"""Deterministic tests for point-in-time XBRL handling (no network)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aicfinal import xbrl  # noqa: E402
from aicfinal.prices import close_time_utc, observable  # noqa: E402


def cf(*items, concept="Revenues", unit="USD"):
    return {"facts": {"us-gaap": {concept: {"units": {unit: list(items)}}}}}


def it(start, end, val, accn):
    return {"start": start, "end": end, "val": val, "accn": accn, "form": "10-Q", "filed": "x"}


ACC = {"A1": "2025-05-01T20:00:00Z", "A2": "2025-08-01T20:00:00Z",
       "A3": "2025-11-01T20:00:00Z", "K1": "2026-02-20T20:00:00Z", "R1": "2026-05-01T20:00:00Z"}


class FactsTableTests(unittest.TestCase):
    def test_cutoff_excludes_later_filings(self):
        data = cf(it("2025-01-01", "2025-03-31", 10, "A1"), it("2025-04-01", "2025-06-30", 12, "A2"))
        rows = xbrl.facts_table(data, ACC, cutoff_utc="2025-06-01T00:00:00Z")
        self.assertEqual([r["accn"] for r in rows], ["A1"])

    def test_unknown_accession_is_dropped(self):
        rows = xbrl.facts_table(cf(it("2025-01-01", "2025-03-31", 10, "ZZ")), ACC, "2030-01-01T00:00:00Z")
        self.assertEqual(rows, [])

    def test_restatement_latest_accepted_wins(self):
        data = cf(it("2025-01-01", "2025-03-31", 10, "A1"), it("2025-01-01", "2025-03-31", 11, "R1"))
        early = xbrl.quarterly(xbrl.facts_table(data, ACC, "2025-12-31T00:00:00Z"), "Revenues")
        late = xbrl.quarterly(xbrl.facts_table(data, ACC, "2026-12-31T00:00:00Z"), "Revenues")
        self.assertEqual(early[0]["val"], 10)  # an old case keeps the number it saw
        self.assertEqual(late[0]["val"], 11)


class QuarterizeTests(unittest.TestCase):
    def setUp(self):
        data = cf(
            it("2025-01-01", "2025-03-31", 10, "A1"),
            it("2025-01-01", "2025-06-30", 22, "A2"),   # YTD 6M
            it("2025-01-01", "2025-09-30", 36, "A3"),   # YTD 9M
            it("2025-01-01", "2025-12-31", 50, "K1"),   # FY
        )
        self.q = xbrl.quarterly(xbrl.facts_table(data, ACC, "2026-12-31T00:00:00Z"), "Revenues")

    def test_derives_all_four_quarters(self):
        self.assertEqual([q["val"] for q in self.q], [10, 12, 14, 14])
        self.assertEqual([q["derived"] for q in self.q], [False, True, True, True])

    def test_derived_values_keep_components(self):
        q4 = self.q[-1]
        self.assertTrue(q4["id"].startswith("D-"))
        self.assertEqual(len(q4["components"]), 2)

    def test_ttm_requires_contiguous_quarters(self):
        self.assertEqual(xbrl.ttm(self.q)["val"], 50)
        self.assertIsNone(xbrl.ttm(self.q[:3]))


class LabelTests(unittest.TestCase):
    def test_nvda_style_january_year_end(self):
        self.assertEqual(xbrl.fiscal_label("2026-07-26", "0131"), (2027, 2))
        self.assertEqual(xbrl.fiscal_label("2026-01-25", "0131"), (2026, 4))
        self.assertEqual(xbrl.calendar_label("2025-10-27", "2026-01-25"), "CY2025Q4")

    def test_calendar_year_end(self):
        self.assertEqual(xbrl.fiscal_label("2026-06-27", "1226"), (2026, 2))
        self.assertEqual(xbrl.calendar_label("2026-03-29", "2026-06-27"), "CY2026Q2")

    def test_august_year_end(self):  # MU-style
        self.assertEqual(xbrl.fiscal_label("2026-05-28", "0902"), (2026, 3))


class PriceCutoffTests(unittest.TestCase):
    def test_close_must_precede_cutoff(self):
        rows = [{"date": "2026-08-25", "close": 1}, {"date": "2026-08-26", "close": 2}]
        # 16:00 New York on 2026-08-26 is 20:00 UTC; a 20:36 UTC cutoff sees it
        self.assertEqual(len(observable(rows, "2026-08-26T20:36:00Z")), 2)
        self.assertEqual(len(observable(rows, "2026-08-26T19:59:00Z")), 1)
        self.assertEqual(close_time_utc("2026-01-15").hour, 21)  # EST


if __name__ == "__main__":
    unittest.main()


class NonAdditiveTests(unittest.TestCase):
    def test_share_counts_are_never_differenced(self):
        data = cf(it("2025-01-01", "2025-03-31", 100, "A1"), it("2025-01-01", "2025-12-31", 101, "K1"),
                  it("2025-01-01", "2025-09-30", 100.5, "A3"), concept="WeightedAverageNumberOfDilutedSharesOutstanding",
                  unit="shares")
        rows = xbrl.facts_table(data, ACC, "2026-12-31T00:00:00Z")
        q = xbrl.quarterly(rows, "WeightedAverageNumberOfDilutedSharesOutstanding", "shares", additive=False)
        self.assertEqual([x["val"] for x in q], [100])  # no derived (and negative) Q4
        self.assertTrue(all(not x["derived"] for x in q))
