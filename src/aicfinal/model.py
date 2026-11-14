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
        if concept is None:
            continue
        kind = catalog[line]["kind"]
        unit = catalog[line].get("unit", "USD")
        series = xbrl.quarterly(rows, concept, unit) if kind == "duration" else xbrl.instants(rows, concept, unit)
        lines[line] = series
    anchor = lines.get("revenue") or next(iter(lines.values()), [])
    quarters = []
    for q in anchor[-HISTORY_QUARTERS:]:
        fy, fq = xbrl.fiscal_label(q["end"], fye)
        quarters.append({"start": q["start"], "end": q["end"], "fiscal": f"FY{fy}Q{fq}",
                         "calendar": xbrl.calendar_label(q["start"], q["end"])})
    table: dict[str, list] = {}
    for line, series in lines.items():
        by_end = {s["end"]: s for s in series}
        table[line] = [by_end.get(q["end"]) for q in quarters]
    return {"quarters": quarters, "lines": table, "fiscal_year_end": fye}


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
