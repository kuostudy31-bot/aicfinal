"""DCF and peer-multiple valuation, target price and rating (deterministic)."""
from __future__ import annotations

import statistics

from . import xbrl
from .model import latest, ttm


def dcf(ntm_revenue: float, inputs: dict, net_cash: float, shares: float) -> dict:
    growth = inputs["revenue_growth"]          # years 2..N growth rates
    margins = inputs["fcf_margin"]             # years 1..N FCF margins
    wacc, g = inputs["wacc"], inputs["terminal_growth"]
    if len(margins) != len(growth) + 1:
        raise ValueError("fcf_margin needs one more entry than revenue_growth")
    if g >= wacc:
        raise ValueError("terminal growth must be below WACC")
    revs = [ntm_revenue]
    for gr in growth:
        revs.append(revs[-1] * (1 + gr))
    fcfs = [r * m for r, m in zip(revs, margins)]
    pv = [f / (1 + wacc) ** (t + 1) for t, f in enumerate(fcfs)]
    tv = fcfs[-1] * (1 + g) / (wacc - g)
    pv_tv = tv / (1 + wacc) ** len(fcfs)
    ev = sum(pv) + pv_tv
    equity = ev + net_cash
    return {"revenues": revs, "fcf": fcfs, "pv_fcf": pv, "terminal_value": tv, "pv_terminal": pv_tv,
            "enterprise_value": ev, "equity_value": equity, "per_share": equity / shares,
            "terminal_share_of_ev": pv_tv / ev}


def peer_multiples(peers_snapshot: dict, catalog: dict, peer_list: list[str]) -> list[dict]:
    """TTM EV/Sales and P/E for peers using default concept preference."""
    out = []
    for t in peer_list:
        p = peers_snapshot["peers"].get(t)
        if not p or not p.get("last_close"):
            out.append({"ticker": t, "excluded": "no price or facts at cutoff"})
            continue
        rows = p["facts"]

        def first_q(line):
            spec = catalog[line]
            for c in spec["candidates"]:
                unit = spec.get("unit", "USD")
                s = xbrl.quarterly(rows, c, unit) if spec["kind"] == "duration" else xbrl.instants(rows, c, unit)
                if s:
                    return c, s
            return None, []

        rc, rq = first_q("revenue")
        nc, nq = first_q("net_income")
        _, sh = first_q("shares_outstanding")
        _, cash = first_q("cash")
        _, debt = first_q("total_debt")
        rev_ttm, ni_ttm = xbrl.ttm(rq), xbrl.ttm(nq)
        if not rev_ttm or not sh:
            out.append({"ticker": t, "excluded": "incomplete TTM revenue or share count"})
            continue
        price = p["last_close"]["close"]
        mcap = price * sh[-1]["val"]
        ev = mcap - (cash[-1]["val"] if cash else 0) + (debt[-1]["val"] if debt else 0)
        out.append({
            "ticker": t, "price": price, "price_date": p["last_close"]["date"],
            "ttm_end": rev_ttm["end"], "calendar": ("TTM to " + xbrl.calendar_label(rq[-1]["start"], rq[-1]["end"])) if rq else None,
            "revenue_ttm": rev_ttm["val"], "net_income_ttm": ni_ttm["val"] if ni_ttm else None,
            "market_cap": mcap, "ev": ev, "ev_sales": ev / rev_ttm["val"],
            "pe": (mcap / ni_ttm["val"]) if ni_ttm and ni_ttm["val"] > 0 else None,
            "concepts": {"revenue": rc, "net_income": nc},
        })
    return out


def value(hist: dict, fc: dict, inputs: dict, price: float, peers: list[dict], policy: dict,
          prior_tp: float | None) -> dict:
    cash = (latest(hist, "cash") or {}).get("val", 0.0)
    sti = (latest(hist, "short_term_investments") or {}).get("val", 0.0) if hist["lines"].get("short_term_investments") else 0.0
    debt = (latest(hist, "total_debt") or {}).get("val", 0.0) if hist["lines"].get("total_debt") else 0.0
    shares = latest(hist, "diluted_shares")["val"]
    net_cash = cash + sti - debt
    d = dcf(fc["ntm"]["revenue"], inputs["dcf"], net_cash, shares)

    usable = [p for p in peers if "ev_sales" in p and p["ticker"] in inputs["peers"]]
    med = statistics.median(p["ev_sales"] for p in usable) if usable else None
    rev_ttm = ttm(hist, "revenue")
    rel = None
    if med and rev_ttm:
        rel = (med * rev_ttm + net_cash) / shares
    w = inputs.get("dcf_weight", 1.0) if rel is not None else 1.0
    blended = w * d["per_share"] + (1 - w) * (rel or 0.0)
    tp = round(blended)
    upside = tp / price - 1
    bands = policy["rating_bands"]
    rating = ("Outperform" if upside >= bands["outperform_min"]
              else "Underperform" if upside <= bands["underperform_max"] else "Neutral")
    tp_change = (tp / prior_tp - 1) if prior_tp else None
    return {
        "net_cash": net_cash, "cash": cash, "short_term_investments": sti, "debt": debt,
        "diluted_shares": shares, "dcf": d, "peer_median_ev_sales": med, "relative_per_share": rel,
        "dcf_weight": w, "blended_per_share": blended, "target_price": tp, "price": price,
        "upside": upside, "rating": rating, "prior_target_price": prior_tp, "tp_change_pct": tp_change,
        "tp_change_needs_rationale": tp_change is not None and abs(tp_change) * 100 > policy["tp_change_threshold_pct"],
    }
