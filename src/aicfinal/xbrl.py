"""Point-in-time XBRL facts -> discrete fiscal quarters with provenance.

Key rules (each is unit-tested in tests/test_xbrl.py):

* Only facts from filings accepted at or before the case cutoff are used
  (the snapshot already enforces this; ``facts_table`` re-checks it).
* When several allowed filings report the same period, the most recently
  accepted value wins (restatements supersede), and the fact ID records which.
* Quarterly flows are taken directly when a ~3-month fact exists; otherwise
  they are derived by differencing a longer and a shorter period with the same
  start (YTD-9M minus YTD-6M, FY minus 9M, ...). Derived values carry a "D-"
  ID and the IDs of their components.
* Fiscal labels are computed from the period end and the company's fiscal
  year end. The ``fy``/``fp`` fields in companyfacts describe the *filing*, so
  they are wrong for comparative-period facts and are not used.
* Calendar labels use the period midpoint, so NVDA's quarter ending in late
  January maps to the prior calendar Q4 and peers can be aligned.
"""
from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta

QUARTER_DAYS = (80, 100)


def _d(text: str) -> date:
    return datetime.strptime(text, "%Y-%m-%d").date()


def fact_id(concept: str, unit: str, start: str | None, end: str, accn: str, val) -> str:
    raw = f"{concept}|{unit}|{start or ''}|{end}|{accn}|{val}"
    return "F-" + hashlib.sha1(raw.encode()).hexdigest()[:10]


def facts_table(companyfacts: dict, acceptance_by_accn: dict[str, str], cutoff_utc: str,
                min_end: str | None = None, concepts: set[str] | None = None) -> list[dict]:
    """Flatten companyfacts into rows, keeping only facts observable at cutoff."""
    rows = []
    for taxonomy in ("us-gaap", "dei"):
        for concept, body in companyfacts.get("facts", {}).get(taxonomy, {}).items():
            if concepts is not None and concept not in concepts:
                continue
            for unit, items in body.get("units", {}).items():
                for it in items:
                    acc = acceptance_by_accn.get(it["accn"])
                    if acc is None or acc > cutoff_utc:
                        continue
                    if min_end and it["end"] < min_end:
                        continue
                    rows.append({
                        "fact_id": fact_id(concept, unit, it.get("start"), it["end"], it["accn"], it["val"]),
                        "taxonomy": taxonomy, "concept": concept, "unit": unit,
                        "start": it.get("start"), "end": it["end"], "val": it["val"],
                        "accn": it["accn"], "form": it.get("form"), "filed": it.get("filed"),
                        "acceptance_utc": acc,
                    })
    rows.sort(key=lambda r: (r["concept"], r["unit"], r["end"], r["start"] or "", r["acceptance_utc"]))
    return rows


def _latest(rows: list[dict]) -> dict[tuple, dict]:
    """(start, end) -> latest-accepted fact."""
    best: dict[tuple, dict] = {}
    for r in rows:
        key = (r["start"], r["end"])
        if key not in best or r["acceptance_utc"] >= best[key]["acceptance_utc"]:
            best[key] = r
    return best


def _days(start: str, end: str) -> int:
    return (_d(end) - _d(start)).days + 1


def quarterly(rows: list[dict], concept: str, unit: str = "USD", additive: bool = True) -> list[dict]:
    """Discrete quarters for a duration concept, oldest first.

    ``additive=False`` (weighted-average share counts, per-share amounts) uses only
    directly reported ~3-month facts: averages and ratios cannot be differenced.
    """
    sel = [r for r in rows if r["concept"] == concept and r["unit"] == unit and r["start"]]
    periods = _latest(sel)
    quarters: dict[tuple, dict] = {}
    for (s, e), r in periods.items():
        if QUARTER_DAYS[0] <= _days(s, e) <= QUARTER_DAYS[1]:
            quarters[(s, e)] = {"start": s, "end": e, "val": r["val"], "id": r["fact_id"],
                                "derived": False, "components": [r["fact_id"]], "formula": None}
    changed = additive
    while changed:  # derive by differencing nested periods with a common start
        changed = False
        known = {**{k: {"val": v["val"], "id": v["id"]} for k, v in quarters.items()},
                 **{k: {"val": r["val"], "id": r["fact_id"]} for k, r in periods.items()}}
        for (s1, e1), long_ in known.items():
            for (s2, e2), short in known.items():
                if s1 != s2 or e2 >= e1:
                    continue
                qs = (_d(e2) + timedelta(days=1)).isoformat()
                if not (QUARTER_DAYS[0] <= _days(qs, e1) <= QUARTER_DAYS[1]):
                    continue
                if (qs, e1) in quarters:
                    continue
                val = long_["val"] - short["val"]
                did = "D-" + hashlib.sha1(f"{long_['id']}-{short['id']}".encode()).hexdigest()[:10]
                quarters[(qs, e1)] = {"start": qs, "end": e1, "val": val, "id": did, "derived": True,
                                      "components": [long_["id"], short["id"]],
                                      "formula": f"{long_['id']} - {short['id']}"}
                changed = True
    return sorted(quarters.values(), key=lambda q: q["end"])


def instants(rows: list[dict], concept: str, unit: str = "USD") -> list[dict]:
    sel = [r for r in rows if r["concept"] == concept and r["unit"] == unit and not r["start"]]
    best = _latest(sel)
    out = [{"end": e, "val": r["val"], "id": r["fact_id"], "derived": False,
            "components": [r["fact_id"]], "formula": None} for (_, e), r in best.items()]
    return sorted(out, key=lambda q: q["end"])


def fiscal_label(end: str, fiscal_year_end: str) -> tuple[int, int]:
    """(fiscal_year, fiscal_quarter) for a quarter ending on ``end``.

    ``fiscal_year_end`` is EDGAR's MMDD string. 52/53-week years end within a
    week of that date, so a 10-day tolerance is used.
    """
    e = _d(end)
    m, d = int(fiscal_year_end[:2]), int(fiscal_year_end[2:])

    def fye(year: int) -> date:
        day = min(d, 28) if m == 2 else d
        return date(year, m, day)

    fy = e.year if e <= fye(e.year) + timedelta(days=10) else e.year + 1
    prev_end = fye(fy - 1)
    q = round((e - prev_end).days / 91.3)
    return fy, max(1, min(4, q))


def calendar_label(start: str, end: str) -> str:
    mid = _d(start) + (_d(end) - _d(start)) / 2
    return f"CY{mid.year}Q{(mid.month - 1) // 3 + 1}"


def ttm(quarters: list[dict], as_of_end: str | None = None) -> dict | None:
    qs = [q for q in quarters if as_of_end is None or q["end"] <= as_of_end]
    if len(qs) < 4:
        return None
    last4 = qs[-4:]
    # the four quarters must be contiguous (no gap > 10 days)
    for a, b in zip(last4, last4[1:]):
        if (_d(b["start"]) - _d(a["end"])).days > 10:
            return None
    return {"val": sum(q["val"] for q in last4), "end": last4[-1]["end"],
            "components": [q["id"] for q in last4]}
