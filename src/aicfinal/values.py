"""Code-generated values for the note, and placeholder rendering.

The writer references values only as ``{{key}}`` and quotes only as
``[[Q-id]]``. Every key here carries its provenance (fact IDs, a formula over
other keys, or a quote ID), so each figure in the published note can be traced.
"""
from __future__ import annotations

import re

from .model import latest, ttm

PLACEHOLDER = re.compile(r"\{\{([a-z0-9_]+)\}\}")
QUOTE = re.compile(r"\[\[(Q-[A-Za-z0-9_-]+)\]\]")


def usd_b(x: float) -> str:
    return f"${x / 1e9:,.1f}bn"


def pct(x: float, nd: int = 1) -> str:
    return f"{x * 100:.{nd}f}%"


def money(x: float) -> str:
    return f"${x:,.2f}"


def build(ticker: str, hist: dict, fc: dict, val: dict, narrative: dict) -> dict:
    v: dict[str, dict] = {}

    def put(key, value, display, sources):
        v[key] = {"value": value, "display": display, "sources": sources}

    q = hist["quarters"]
    cur, prev, yago = q[-1], q[-2], q[-5] if len(q) >= 5 else None
    put("ticker", ticker, ticker, ["config"])
    put("fiscal_quarter", cur["fiscal"], cur["fiscal"].replace("Q", " Q"), ["history.quarters"])
    put("calendar_quarter", cur["calendar"], cur["calendar"], ["history.quarters"])
    put("period_end", cur["end"], cur["end"], ["history.quarters"])

    def line_vals(line):
        return hist["lines"].get(line) or []

    rev = line_vals("revenue")
    put("revenue_q", rev[-1]["val"], usd_b(rev[-1]["val"]), [rev[-1]["id"]])
    put("revenue_qoq", rev[-1]["val"] / rev[-2]["val"] - 1, pct(rev[-1]["val"] / rev[-2]["val"] - 1),
        [rev[-1]["id"], rev[-2]["id"]])
    if yago and rev[-5]:
        put("revenue_yoy", rev[-1]["val"] / rev[-5]["val"] - 1, pct(rev[-1]["val"] / rev[-5]["val"] - 1),
            [rev[-1]["id"], rev[-5]["id"]])
    for line, key in (("gross_profit", "gross_margin_q"), ("operating_income", "operating_margin_q")):
        s = line_vals(line)
        if s and s[-1]:
            put(key, s[-1]["val"] / rev[-1]["val"], pct(s[-1]["val"] / rev[-1]["val"]), [s[-1]["id"], rev[-1]["id"]])
    ni = line_vals("net_income")
    put("net_income_q", ni[-1]["val"], usd_b(ni[-1]["val"]), [ni[-1]["id"]])
    eps = line_vals("eps_diluted")
    if eps and eps[-1]:
        put("eps_q", eps[-1]["val"], money(eps[-1]["val"]), [eps[-1]["id"]])
    cfo, capex = line_vals("cfo"), line_vals("capex")
    if cfo and capex and cfo[-1] and capex[-1]:
        fcf = cfo[-1]["val"] - capex[-1]["val"]
        put("fcf_q", fcf, usd_b(fcf), [cfo[-1]["id"], capex[-1]["id"]])
    rt = ttm(hist, "revenue")
    if rt:
        put("revenue_ttm", rt, usd_b(rt), [x["id"] for x in rev[-4:]])

    f1 = fc["quarters"][0]
    put("next_q_label", f1["label"], f1["label"], ["assumptions.next_quarters[0].label"])
    put("next_q_revenue", f1["revenue"], usd_b(f1["revenue"]), ["forecast.quarters[0].revenue"])
    put("next_q_eps", f1["eps"], money(f1["eps"]), ["forecast.quarters[0].eps"])
    put("ntm_revenue", fc["ntm"]["revenue"], usd_b(fc["ntm"]["revenue"]), ["forecast.ntm.revenue"])
    put("ntm_eps", fc["ntm"]["eps"], money(fc["ntm"]["eps"]), ["forecast.ntm.eps"])

    put("target_price", val["target_price"], f"${val['target_price']:,.0f}", ["valuation.target_price"])
    put("price", val["price"], money(val["price"]), ["snapshot/prices.json last close"])
    put("upside", val["upside"], pct(val["upside"]), ["valuation.upside"])
    put("rating", val["rating"], val["rating"], ["valuation.rating (policy bands)"])
    put("dcf_per_share", val["dcf"]["per_share"], money(val["dcf"]["per_share"]), ["valuation.dcf.per_share"])
    put("terminal_share", val["dcf"]["terminal_share_of_ev"], pct(val["dcf"]["terminal_share_of_ev"], 0),
        ["valuation.dcf.terminal_share_of_ev"])
    if val.get("peer_median_ev_sales"):
        put("peer_ev_sales", val["peer_median_ev_sales"], f"{val['peer_median_ev_sales']:.1f}x",
            ["valuation.peer_median_ev_sales"])
    if val.get("prior_target_price"):
        put("prior_target_price", val["prior_target_price"], f"${val['prior_target_price']:,.0f}",
            ["prior published case"])
    put("net_cash", val["net_cash"], usd_b(val["net_cash"]), ["valuation.net_cash"])

    for g in narrative.get("guidance", []):
        key = "guide_" + re.sub(r"[^a-z0-9_]", "_", g["metric"].lower())
        disp = usd_b(g["value"]) if g.get("unit") == "USD" else (pct(g["value"]) if g.get("unit") == "ratio" else str(g["value"]))
        put(key, g["value"], disp, [g["quote_id"]])
    return v


def render(text: str, values: dict, quotes: dict) -> tuple[str, list[str]]:
    missing = []

    def sub_v(m):
        k = m.group(1)
        if k not in values:
            missing.append(k)
            return "[MISSING " + k + "]"
        return values[k]["display"]

    def sub_q(m):
        k = m.group(1)
        if k not in quotes:
            missing.append(k)
            return "[MISSING " + k + "]"
        return "“" + quotes[k]["text"] + "”"

    return QUOTE.sub(sub_q, PLACEHOLDER.sub(sub_v, text)), missing
