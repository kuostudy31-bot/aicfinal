"""The evidence dashboard is built from the repository and stays offline."""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aicfinal import dashboard  # noqa: E402


class DashboardTests(unittest.TestCase):
    def test_builds_offline_from_evidence(self):
        page = dashboard.build()
        self.assertNotRegex(page, r'(?:src|href)="https?:')          # no external scripts, styles or links
        published = [c for c in dashboard.case_rows() if c["status"] == "PUBLISHED"]
        kv = re.search(r'<div class="kv">(\d+)</div><div class="kl">notes published', page)
        self.assertEqual(int(kv.group(1)), len(published))
        for c in published:                                         # every published note links its PDF
            self.assertIn(f'href="report/{c["case_id"]}/{c["case_id"]}.pdf"', page)

    def test_evolution_counts_match_evaluations(self):
        rows = {r["id"]: r for r in dashboard.evolution_rows()}
        if "change-003" in rows:
            self.assertTrue(rows["change-003"]["separated"])
            self.assertEqual(rows["change-003"]["baseline_pass"], 0)
