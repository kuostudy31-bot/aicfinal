"""Numerical and provenance gates. Each returns a list of findings.

A finding is {"id", "severity", "check", "detail"}. IDs are stable per check
and subject (e.g. "gate-balance-latest"), so the finding ledger can tell a
recurring problem from a new one across rounds.
"""
from __future__ import annotations

import re

from . import values as V
from .model import REQUIRED_LINES, latest, latest_aligned

ALLOWED_TOKEN = re.compile(
    r"(?<![\w$.])(?:FY|CY)?(?:19|20)\d{2}(?:Q[1-4])?(?![\w%]|\.\d)"   # years, FY2027, CY2026Q2 (a full stop may follow)
    r"|\bQ[1-4]\b|\b(?:10-Q|10-K|8-K|EX-99\.\d|S&P\s?500)\b"
    r"|\b(?:H[12])\b"
)
NUMBER = re.compile(r"\d")


def f(fid, sev, check, detail):
    return {"id": fid, "severity": sev, "check": check, "detail": detail}


# Lines a 10-K reports for the fiscal year only: they are never differenced, so the derived
# fourth quarter has no value for them by design (incidents #12, #14).
NON_ADDITIVE_LINES = ("diluted_shares", "eps_diluted")


def _fy_only_gap(hist: dict, line: str, vals: list) -> bool:
    qs = hist.get("quarters") or []
    return (line in NON_ADDITIVE_LINES and bool(qs) and str(qs[-1].get("fiscal", "")).endswith("Q4")
            and len(vals) >= 2 and vals[-2] is not None)


def gate_mapping(hist: dict) -> list[dict]:
    out = []
    for line in REQUIRED_LINES:
        v = latest(hist, line)
        if v is None:
            out.append(f(f"gate-mapping-{line}", "blocker", "mapping_coverage",
                         f"no value for required line '{line}' in the latest quarter"))
    for line, vals in hist["lines"].items():
        if line not in REQUIRED_LINES and vals and vals[-1] is None and not _fy_only_gap(hist, line, vals):
            last = next((v.get("end", "?") for v in reversed(vals) if v), "never")
            out.append(f(f"gate-stale-{line}", "major", "stale_mapping",
                         f"'{line}' has no value in the latest quarter (last {last}); the company may "
                         "have switched XBRL concepts, and treating it as zero would bias the model"))
    return out


def gate_balance(hist: dict) -> list[dict]:
    a, le = latest(hist, "assets"), latest(hist, "liabilities_and_equity")
    if a is None or le is None:
        return [f("gate-balance-latest", "major", "balance_sheet", "assets or liabilities_and_equity unmapped")]
    if abs(a["val"] - le["val"]) > 0.001 * abs(a["val"]):
        return [f("gate-balance-latest", "blocker", "balance_sheet",
                  f"assets {a['val']:.0f} != liabilities+equity {le['val']:.0f}")]
    return []


def gate_eps(hist: dict) -> list[dict]:
    aligned = latest_aligned(hist, "net_income", "diluted_shares", "eps_diluted")
    if not aligned:
        return []
    ni, sh, eps = aligned  # same quarter for all three (a 10-K's Q4 has no diluted shares or EPS)
    implied = ni["val"] / sh["val"]
    if eps["val"] and abs(implied / eps["val"] - 1) > 0.03:
        return [f("gate-eps-latest", "major", "eps_consistency",
                  f"net income / diluted shares = {implied:.3f} vs reported EPS {eps['val']:.3f}")]
    return []


def gate_gross_profit(hist: dict) -> list[dict]:
    r, c, g = latest(hist, "revenue"), latest(hist, "cost_of_revenue"), latest(hist, "gross_profit")
    if not (r and c and g):
        return []
    if abs((r["val"] - c["val"]) - g["val"]) > 0.005 * abs(r["val"]):
        return [f("gate-grossprofit-latest", "major", "gross_profit_identity",
                  f"revenue - cost {r['val'] - c['val']:.0f} != gross profit {g['val']:.0f}")]
    return []


def gate_cutoff(facts_snapshot: dict, prices_snapshot: dict, hist: dict) -> list[dict]:
    out, cutoff = [], facts_snapshot["cutoff_utc"]
    late = [r["fact_id"] for r in facts_snapshot["facts"] if r["acceptance_utc"] > cutoff]
    if late:
        out.append(f("gate-cutoff-facts", "blocker", "information_cutoff", f"{len(late)} facts after cutoff"))
    used = {v["id"] for vals in hist["lines"].values() for v in vals if v}
    known = {r["fact_id"] for r in facts_snapshot["facts"]}
    for vals in hist["lines"].values():
        for v in vals:
            if v and not v["derived"] and v["id"] not in known:
                out.append(f("gate-cutoff-unknown-fact", "blocker", "information_cutoff",
                             f"history uses fact {v['id']} not in snapshot"))
                break
    del used
    if prices_snapshot["closes"] and prices_snapshot["closes"][-1]["date"] > cutoff[:10]:
        out.append(f("gate-cutoff-prices", "blocker", "information_cutoff", "price after cutoff date"))
    return out


def gate_assumptions(assumptions: dict, vinputs: dict) -> list[dict]:
    out = []
    d = vinputs["dcf"]
    if not 0.06 <= d["wacc"] <= 0.16:
        out.append(f("gate-bounds-wacc", "major", "assumption_bounds", f"WACC {d['wacc']} outside [6%, 16%]"))
    if not 0.0 <= d["terminal_growth"] <= 0.04:
        out.append(f("gate-bounds-tg", "major", "assumption_bounds", f"terminal growth {d['terminal_growth']} outside [0, 4%]"))
    for q in assumptions["next_quarters"]:
        if not 0 < q["gross_margin"] < 1 or not 0 <= q["opex_pct_revenue"] < 1:
            out.append(f("gate-bounds-margin", "major", "assumption_bounds", f"margin out of range in {q['label']}"))
        if not -0.5 <= q["revenue_qoq"] <= 1.0:
            out.append(f("gate-bounds-growth", "major", "assumption_bounds", f"q/q growth out of range in {q['label']}"))
    if not 0 <= assumptions["tax_rate"] <= 0.35:
        out.append(f("gate-bounds-tax", "major", "assumption_bounds", "tax rate outside [0, 35%]"))
    missing = [k for k in ("revenue_qoq", "gross_margin", "opex_pct_revenue", "tax_rate", "wacc", "terminal_growth")
               if k not in assumptions.get("rationales", {}) and k not in vinputs.get("rationales", {})]
    if missing:
        out.append(f("gate-rationale-missing", "major", "assumption_rationale", f"no rationale for {missing}"))
    return out


def gate_peers(peers_table: list[dict], latest_end: str) -> list[dict]:
    out = []
    from datetime import date
    le = date.fromisoformat(latest_end)
    for p in peers_table:
        if "ttm_end" in p and abs((date.fromisoformat(p["ttm_end"]) - le).days) > 120:
            out.append(f(f"gate-peer-period-{p['ticker']}", "minor", "period_alignment",
                         f"{p['ticker']} TTM ends {p['ttm_end']}, >120 days from {latest_end}"))
    return out


def _norm(s: str) -> str:
    s = s.replace("’", "'").replace("“", '"').replace("”", '"').replace("—", "-")
    return re.sub(r"\s+", " ", s).strip()


# How a guidance value may appear in the company's text: USD in billions, a ratio in percent,
# per-share dollars as written, share counts in millions or billions.
GUIDANCE_SCALES = {"USD": (1e-9,), "ratio": (100.0,), "USD/share": (1.0,), "shares": (1e-6, 1e-9)}


def guidance_unit(g: dict) -> str | None:
    """The contract unit; a 'USD' value below 1,000 can only be a per-share amount (MU's EPS
    guidance was tagged 'USD' before 'USD/share' existed, incidents #14)."""
    u = g.get("unit")
    if u == "USD" and isinstance(g.get("value"), (int, float)) and abs(g["value"]) < 1000:
        return "USD/share"
    return u


def gate_quotes(narrative: dict, docs: dict[str, str]) -> list[dict]:
    out = []
    normdocs = {k: _norm(v) for k, v in docs.items()}
    quotes = {q["id"]: q for q in narrative.get("quotes", [])}
    for q in quotes.values():
        doc = normdocs.get(q["doc"])
        if doc is None or _norm(q["text"]) not in doc:
            out.append(f(f"gate-quote-{q['id']}", "blocker", "quote_verbatim",
                         f"{q['id']} not found verbatim in {q['doc']}"))
    for g in narrative.get("guidance", []):
        q = quotes.get(g["quote_id"])
        if q is None:
            out.append(f(f"gate-guidance-{g['metric']}", "blocker", "guidance_source", f"{g['metric']} cites unknown quote"))
            continue
        unit = guidance_unit(g)
        if unit not in GUIDANCE_SCALES or not isinstance(g.get("value"), (int, float)):
            continue  # text guidance (e.g. "none assumed") is checked by the verbatim quote alone

        def visible(x):
            for scale in GUIDANCE_SCALES[unit]:
                v = x * scale
                # the value as the company may have written it: 3.75, 3.8, 108.0, 108, 74, 37.84
                forms = {f"{v:.{d}f}" for d in (0, 1, 2, 3)}
                forms |= {t.rstrip("0").rstrip(".") for t in forms if "." in t}
                forms = {t for t in forms if t and abs(float(t) - v) <= 1e-9 * max(1.0, abs(v)) + 1e-12}
                if any(re.search(r"(?<![\d.])" + re.escape(t) + r"(?![\d])", q["text"]) for t in forms):
                    return True
            return False

        token = f"{g['value'] * GUIDANCE_SCALES[unit][0]:.2f}"
        # A midpoint of a stated range is visible through its stated low and high.
        rng = isinstance(g.get("low"), (int, float)) and isinstance(g.get("high"), (int, float))
        ok = visible(g["value"]) or (rng and visible(g["low"]) and visible(g["high"])
                                     and g["low"] <= g["value"] <= g["high"])
        if not ok:
            out.append(f(f"gate-guidance-{g['metric']}", "major", "guidance_source",
                         f"{g['metric']} value {token} not visible in {g['quote_id']}"))
    return out


def gate_note(note_md: str, values: dict, quotes: dict) -> list[dict]:
    """Provenance gate: placeholders resolve and no untagged numbers remain."""
    out = []
    _, missing = V.render(note_md, values, quotes)
    for k in sorted(set(missing)):
        out.append(f(f"gate-note-missing-{k}", "blocker", "note_placeholder", f"unknown placeholder or quote {k}"))
    stripped = V.QUOTE.sub("", V.PLACEHOLDER.sub("", note_md))
    stripped = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), stripped, flags=re.S)
    stripped = ALLOWED_TOKEN.sub("", stripped)
    for i, line in enumerate(stripped.splitlines(), start=1):
        if NUMBER.search(line):
            snippet = line.strip()[:80]
            out.append(f(f"gate-note-untagged-L{i}", "blocker", "untagged_number",
                         f"line {i} contains a number not supplied by code or quote: '{snippet}'"))
    return out


def run_all(ctx: dict) -> list[dict]:
    hist = ctx["history"]
    out = []
    out += gate_mapping(hist)
    out += gate_balance(hist)
    out += gate_eps(hist)
    out += gate_gross_profit(hist)
    out += gate_cutoff(ctx["facts"], ctx["prices"], hist)
    out += gate_assumptions(ctx["assumptions"], ctx["valuation_inputs"])
    out += gate_peers(ctx["peers_table"], hist["quarters"][-1]["end"])
    out += gate_quotes(ctx["narrative"], ctx["docs"])
    if ctx.get("note_md") is not None:
        out += gate_note(ctx["note_md"], ctx["values"], {q["id"]: q for q in ctx["narrative"].get("quotes", [])})
    return out
