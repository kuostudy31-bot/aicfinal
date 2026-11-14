"""Historical quarterly table and forecast. Pure functions of their inputs.

Agents choose the XBRL mapping and the forecast assumptions; this module does
all arithmetic, so a reviewer can recompute every figure from the saved files.
"""
from __future__ import annotations

from . import xbrl

HISTORY_QUARTERS = 8
REQUIRED_LINES = ["revenue", "operating_income", "net_income", "diluted_shares", "cfo", "capex",
                  "cash", "assets"]


def history(facts_snapshot: dict, mapping: dict, catalog: dict) -> dict:
    """Last N discrete quarters for each mapped line, with fact IDs."""
    rows = facts_snapshot["facts"]
    fye = facts_snapshot["fiscal_year_end"]
    lines: dict[str, list[dict]] = {}
    for line, spec in mapping.items():
        concept = spec["concept"]
        if not concept:
            continue
        kind = catalog[line]["kind"]
        unit = catalog[line].get("unit", "USD")
        concepts = concept if isinstance(concept, list) else [concept]
        additive = catalog[line].get("additive", True)
        parts = [xbrl.quarterly(rows, c, unit, additive) if kind == "duration" else xbrl.instants(rows, c, unit)
                 for c in concepts]
        lines[line] = parts[0] if len(parts) == 1 else sum_series(parts)
    anchor = lines.get("revenue") or next(iter(lines.values()), [])
    quarters = []
    for q in anchor[-HISTORY_QUARTERS:]:
        fy, fq = xbrl.fiscal_label(q["end"], fye)
        quarters.append({"start": q["start"], "end": q["end"], "fiscal": f"FY{fy}Q{fq}",
                         "calendar": xbrl.calendar_label(q["start"], q["end"])})
    table: dict[str, list] = {}
    for line, series in lines.items():
        by_end = {s["end"]: s for s in series}
        col = [by_end.get(q["end"]) for q in quarters]
        if catalog[line]["kind"] == "instant" and quarters and col and col[-1] is None:
            # Cover-page counts (dei) are dated after the quarter end, at the filing date.
            from datetime import date, timedelta
            qe = date.fromisoformat(quarters[-1]["end"])
            later = [s for s in series if qe < date.fromisoformat(s["end"]) <= qe + timedelta(days=75)]
            if later:
                col[-1] = later[-1]
        table[line] = col
    return {"quarters": quarters, "lines": table, "fiscal_year_end": fye}


def sum_series(parts: list[list[dict]]) -> list[dict]:
    """Sum several concepts period by period (e.g. debt + equity securities).

    A period is kept only when every component reports it, so a missing
    component never turns into a silent zero.
    """
    import hashlib
    by_end = [{p["end"]: p for p in part} for part in parts]
    common = sorted(set.intersection(*(set(b) for b in by_end)))
    out = []
    for end in common:
        comps = [b[end] for b in by_end]
        ids = [c["id"] for c in comps]
        out.append({"start": comps[0].get("start"), "end": end, "val": sum(c["val"] for c in comps),
                    "id": "S-" + hashlib.sha1("+".join(ids).encode()).hexdigest()[:10], "derived": True,
                    "components": ids, "formula": " + ".join(ids)})
    return out


def latest(hist: dict, line: str):
    vals = hist["lines"].get(line) or []
    return vals[-1] if vals else None


def ttm(hist: dict, line: str) -> float | None:
    vals = (hist["lines"].get(line) or [])[-4:]
    if len(vals) < 4 or any(v is None for v in vals):
        return None
    return sum(v["val"] for v in vals)


def forecast(hist: dict, assumptions: dict) -> dict:
    """Next four quarters from q/q revenue growth and margin assumptions."""
    rev = latest(hist, "revenue")["val"]
    shares = latest(hist, "diluted_shares")["val"]
    tax = assumptions["tax_rate"]
    out = []
    for i, q in enumerate(assumptions["next_quarters"], start=1):
        rev = rev * (1 + q["revenue_qoq"])
        gp = rev * q["gross_margin"]
        opex = rev * q["opex_pct_revenue"]
        op = gp - opex
        ni = op * (1 - tax) + q.get("other_income", 0.0)
        shares = shares * (1 + assumptions.get("share_change_qoq", 0.0))
        out.append({"step": i, "label": q["label"], "revenue": rev, "gross_profit": gp, "opex": opex,
                    "operating_income": op, "net_income": ni, "diluted_shares": shares,
                    "eps": ni / shares})
    ntm = {k: sum(r[k] for r in out) for k in ("revenue", "gross_profit", "operating_income", "net_income")}
    ntm["eps"] = sum(r["eps"] for r in out)
    return {"quarters": out, "ntm": ntm}
