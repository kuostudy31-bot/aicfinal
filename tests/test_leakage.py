"""No-leakage perturbation test (lecture slide 44).

Freeze the inputs through the cutoff, alter everything after it -- a later
quarter, a later restatement of an already-reported quarter, and later prices --
and check that every number the case uses is unchanged.
"""
import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aicfinal import compute, prices, xbrl  # noqa: E402
from aicfinal.util import read_json  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures" / "nvda"


def to_companyfacts(rows):
    """Rebuild a companyfacts-shaped dict from snapshot rows."""
    cf = {"facts": {}}
    for r in rows:
        units = cf["facts"].setdefault(r["taxonomy"], {}).setdefault(r["concept"], {"units": {}})["units"]
        units.setdefault(r["unit"], []).append(
            {k: r[k] for k in ("start", "end", "val", "accn", "form", "filed") if r.get(k) is not None or k == "start"})
    return cf


class LeakageTests(unittest.TestCase):
    def setUp(self):
        self.snap = read_json(FIX / "snapshot" / "facts.json")
        self.cutoff = self.snap["cutoff_utc"]
        self.acc = {r["accn"]: r["acceptance_utc"] for r in self.snap["facts"]}
        self.cf = to_companyfacts(self.snap["facts"])

    def perturbed(self):
        cf = copy.deepcopy(self.cf)
        acc = dict(self.acc)
        late = "LATE-0001"
        acc[late] = "2026-11-19T21:00:00Z"  # accepted after the cutoff
        rev = cf["facts"]["us-gaap"]["Revenues"]["units"]["USD"]
        rev.append({"start": "2026-07-27", "end": "2026-10-25", "val": 1e15, "accn": late,
                    "form": "10-Q", "filed": "2026-11-19"})                      # a future quarter
        last = max(rev[:-1], key=lambda x: x["end"])
        rev.append(dict(last, val=last["val"] * 0.5, accn=late, filed="2026-11-19"))  # later restatement
        return cf, acc

    def test_facts_after_cutoff_do_not_change_any_series(self):
        base = xbrl.facts_table(self.cf, self.acc, self.cutoff)
        cf, acc = self.perturbed()
        pert = xbrl.facts_table(cf, acc, self.cutoff)
        self.assertEqual(base, pert)
        self.assertEqual(xbrl.quarterly(base, "Revenues"), xbrl.quarterly(pert, "Revenues"))

    def test_same_perturbation_is_visible_after_the_cutoff(self):
        # control: the perturbation is real -- with a later cutoff it does change the data
        cf, acc = self.perturbed()
        later = xbrl.quarterly(xbrl.facts_table(cf, acc, "2026-12-31T00:00:00Z"), "Revenues")
        self.assertEqual(later[-1]["val"], 1e15)

    def test_prices_after_cutoff_are_invisible(self):
        px = read_json(FIX / "snapshot" / "prices.json")["closes"]
        future = px + [{"date": "2026-08-27", "close": 1.0}, {"date": "2026-09-30", "close": 9999.0}]
        self.assertEqual(prices.observable(future, self.cutoff), prices.observable(px, self.cutoff))

    def test_full_pipeline_values_unchanged_under_perturbation(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            outs = []
            for perturb in (False, True):
                case = tmp / ("p" if perturb else "b")
                shutil.copytree(FIX / "snapshot", case / "snapshot")
                shutil.copytree(FIX / "generator", case / "rounds" / "round-001" / "generator")
                if perturb:  # rebuild facts.json from perturbed raw data under the same cutoff
                    cf, acc = self.perturbed()
                    snap = dict(self.snap, facts=xbrl.facts_table(cf, acc, self.cutoff))
                    (case / "snapshot" / "facts.json").write_text(json.dumps(snap))
                    pj = read_json(case / "snapshot" / "prices.json")
                    pj["closes"] = prices.observable(pj["closes"] + [{"date": "2026-09-30", "close": 1.0}],
                                                     self.cutoff)
                    (case / "snapshot" / "prices.json").write_text(json.dumps(pj))
                res = compute.run(case, case / "rounds" / "round-001")
                outs.append(read_json(case / "rounds" / "round-001" / "computed" / "values.json"))
                outs[-1]["_tp"] = res["valuation"]["target_price"]
            self.assertEqual(outs[0], outs[1])
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
