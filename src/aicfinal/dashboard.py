"""Static evidence dashboard: one self-contained, offline HTML page built from the repository.

Every number on the page is read from the evidence files (case state and ledgers, recomputed
valuations, approvals, evolution evaluations, the interruption register and the test suite), so
the page can be regenerated at any time with `python3 scripts/eu.py dashboard` and never needs a
network connection or an external library.
"""
from __future__ import annotations

import html
import json
import re
import subprocess
import unittest
from datetime import datetime, timezone
from pathlib import Path

from . import ROOT
from .util import read_json

OUT = ROOT / "dashboard.html"
STATUS_ORDER = ["PUBLISHED", "AWAITING_APPROVAL", "CRITIC_PENDING", "GENERATOR_PENDING", "STALLED",
                "EXHAUSTED", "BLOCKED", "REJECTED", "USER_STOPPED"]
CRITIC = {"asm": "Assumption", "cmp": "Compliance", "prov": "Provenance", "gate": "Gate"}


def e(x) -> str:
    return html.escape("" if x is None else str(x))


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


# ------------------------------------------------------------------ data
def _form(cdir: Path) -> str:
    man = cdir / "snapshot" / "manifest.json"
    return (read_json(man).get("trigger_form") if man.exists() else None) or "—"


def case_rows() -> list[dict]:
    rows = []
    for cdir in sorted(p for p in (ROOT / "cases").iterdir() if p.is_dir() and (p / "state.json").exists()):
        st = read_json(cdir / "state.json")
        val = {}
        if st.get("round"):
            vp = cdir / "rounds" / f"round-{st['round']:03d}" / "numerical" / "recompute" / "valuation.json"
            if vp.exists():
                val = read_json(vp)
        ledger = st.get("ledger") or {}
        findings = [{"id": fid, **f} for fid, f in sorted(ledger.items())]
        events = [json.loads(line) for line in (cdir / "trace.jsonl").read_text().splitlines() if line.strip()] \
            if (cdir / "trace.jsonl").exists() else []
        pdf = ROOT / "report" / cdir.name / f"{cdir.name}.pdf"
        rows.append({
            "case_id": cdir.name, "ticker": st.get("ticker"), "status": st.get("status"),
            "form": _form(cdir),
            "revision": int(m.group(1)) if (m := re.search(r"-r(\d+)$", cdir.name)) else 1,
            "rounds": st.get("round") or 0,
            "reviews": len(list(cdir.glob("rounds/*/reviews/review-*"))),
            "cutoff": st.get("cutoff_utc"), "opened": st.get("opened_at"),
            "stop_reason": st.get("stop_reason"),
            "findings": findings,
            "opened_n": len(findings), "closed_n": sum(f.get("status") == "closed" for f in findings),
            "open_n": sum(f.get("status") == "open" for f in findings),
            "open_blocking": sum(f.get("status") == "open" and f.get("severity") in ("blocker", "major")
                                 for f in findings),
            "tp": val.get("target_price"), "rating": val.get("rating"), "price": val.get("price"),
            "upside": val.get("upside"), "dcf": (val.get("dcf") or {}).get("per_share"),
            "rel": val.get("relative_per_share"), "dcf_weight": val.get("dcf_weight"),
            "approval": st.get("approval"),
            "pdf": f"report/{cdir.name}/{cdir.name}.pdf" if pdf.exists() else None,
            "transcripts": len(list(cdir.glob("evidence/transcripts/*.jsonl"))),
            "events": events,
        })
    rows.sort(key=lambda r: (STATUS_ORDER.index(r["status"]) if r["status"] in STATUS_ORDER else 99, r["case_id"]))
    return rows


def evolution_rows() -> list[dict]:
    out = []
    base = ROOT / "evolution" / "changes"
    for cdir in sorted(p for p in base.iterdir() if p.is_dir()) if base.exists() else []:
        st = read_json(cdir / "status.json")
        fail = read_json(cdir / "failure.json") if (cdir / "failure.json").exists() else {}
        ev = read_json(cdir / "evaluation.json") if (cdir / "evaluation.json").exists() else {}
        rv = read_json(cdir / "review.json") if (cdir / "review.json").exists() else {}
        n = int((ev.get("evaluation_design") or {}).get("samples_per_arm", 1))
        b_pass = c_pass = total = 0
        for r in ev.get("rows", []):
            total += n
            for arm in ("baseline", "candidate"):
                res = r.get(arm, {})
                k = res.get("samples_passed", int(bool(res.get("pass")))) if n > 1 else int(bool(res.get("pass")))
                if arm == "baseline":
                    b_pass += k
                else:
                    c_pass += k
        verification = (cdir / "verification" / "result.json")
        out.append({"id": cdir.name, "state": st.get("state"), "role": st.get("role"),
                    "parent": st.get("parent_version"), "adopted": st.get("adopted_version"),
                    "failure": fail.get("failure", ""), "total": total, "baseline_pass": b_pass,
                    "candidate_pass": c_pass, "separated": bool(ev.get("baseline_reproduces_failure")),
                    "withheld": (fail.get("evaluation_design") or {}).get("withheld_keys", []),
                    "verdict": rv.get("verdict"), "updated": st.get("updated_at"),
                    "verified": read_json(verification).get("pass") if verification.exists() else None})
    return out


def interruptions() -> list[dict]:
    p = ROOT / "docs" / "interruptions.md"
    rows = []
    if not p.exists():
        return rows
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|(.*)\|\s*$", line)
        if not m:
            continue
        cells = [c.strip() for c in m.group(2).split("|")]
        if len(cells) < 7:
            continue
        rows.append({"n": int(m.group(1)), "when": cells[0], "what": cells[1], "type": cells[2],
                     "resumed": cells[4], "kept": cells[5]})
    return rows


def incident_count() -> int:
    p = ROOT / "docs" / "incidents.md"
    return len(re.findall(r"^## \d+\.", p.read_text(encoding="utf-8"), re.M)) if p.exists() else 0


def test_count() -> int:
    try:
        return unittest.TestLoader().discover(str(ROOT / "tests")).countTestCases()
    except Exception:  # noqa: BLE001
        return 0


def registry() -> dict:
    p = ROOT / "prompts" / "registry.json"
    return read_json(p) if p.exists() else {"active": {}, "history": []}


def _clip(text: str, n: int) -> str:
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0] + " …"


def timeline(cases: list[dict], evo: list[dict]) -> list[dict]:
    items = []
    for c in cases:
        for ev in c["events"]:
            kind = ev.get("event")
            if kind == "case_opened":
                items.append((ev["ts"], "open", f"{c['case_id']} opened", "case"))
            elif kind == "approval_recorded":
                items.append((ev["ts"], "publish", f"{c['case_id']} approved and published", "approval"))
            elif kind == "hold_recorded":
                items.append((ev["ts"], "hold", f"{c['case_id']} put on hold: {_clip(ev.get('reason', ''), 110)}", "hold"))
            elif kind == "stopped":
                items.append((ev["ts"], "stop", f"{c['case_id']} stopped: {ev.get('status', '')}", "stop"))
    for x in evo:
        if x["updated"]:
            word = {"ADOPTED": "adopted", "REJECTED": "rejected"}.get(x["state"], x["state"].lower())
            items.append((x["updated"], "evo", f"Evolution {x['id']} {word}", "evolution"))
    seen, out = set(), []
    for ts, kind, text, cat in sorted(items):
        key = (ts[:16], text[:60])
        if key in seen:
            continue
        seen.add(key)
        out.append({"ts": ts, "kind": kind, "text": text, "cat": cat})
    return out


# ------------------------------------------------------------------ rendering helpers
def money(x) -> str:
    return "—" if x is None else f"${x:,.0f}" if abs(x) >= 100 else f"${x:,.2f}"


def pct(x, signed=True) -> str:
    return "—" if x is None else (f"{x * 100:+.1f}%" if signed else f"{x * 100:.1f}%")


def badge(status: str) -> str:
    glyph = {"PUBLISHED": "●", "STALLED": "▲", "USER_STOPPED": "■", "REJECTED": "✕"}.get(status, "◆")
    return f'<span class="badge s-{e(status).lower()}"><span aria-hidden="true">{glyph}</span> {e(status)}</span>'


def valuation_svg(cases: list[dict], bands: dict) -> str:
    """Dot plot of DCF, peer value and target price as % of the last close, one row per published case."""
    pub = [c for c in cases if c["status"] == "PUBLISHED" and c["price"]]
    if not pub:
        return '<p class="empty">No published case yet.</p>'
    lo, hi = -0.7, 0.9
    W, left, right, row_h, top = 720, 110, 24, 46, 34
    H = top + row_h * len(pub) + 34
    x = lambda v: left + (min(max(v, lo), hi) - lo) / (hi - lo) * (W - left - right)  # noqa: E731
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-labelledby="valtitle valdesc" class="chart">',
           '<title id="valtitle">Valuation legs relative to the last close</title>',
           '<desc id="valdesc">For each published case, the DCF value, the peer EV/Sales value and the blended '
           'target price as a percentage above or below the last close before the cutoff, with the rating bands.</desc>']
    um, om = bands.get("underperform_max", -0.10), bands.get("outperform_min", 0.15)
    out.append(f'<rect x="{x(lo):.1f}" y="{top - 8}" width="{x(um) - x(lo):.1f}" height="{H - top - 18}" class="band-u"/>')
    out.append(f'<rect x="{x(om):.1f}" y="{top - 8}" width="{x(hi) - x(om):.1f}" height="{H - top - 18}" class="band-o"/>')
    out.append(f'<text x="{(x(lo) + x(um)) / 2:.1f}" y="{top - 14}" class="band-label">Underperform ≤ {um * 100:.0f}%</text>')
    out.append(f'<text x="{(x(um) + x(om)) / 2:.1f}" y="{top - 14}" class="band-label">Neutral</text>')
    out.append(f'<text x="{(x(om) + x(hi)) / 2:.1f}" y="{top - 14}" class="band-label">Outperform ≥ +{om * 100:.0f}%</text>')
    for t in (-0.6, -0.4, -0.2, 0.0, 0.2, 0.4, 0.6, 0.8):
        out.append(f'<line x1="{x(t):.1f}" x2="{x(t):.1f}" y1="{top - 8}" y2="{H - 26}" class="{"zero" if t == 0 else "grid"}"/>')
        out.append(f'<text x="{x(t):.1f}" y="{H - 10}" class="tick">{t * 100:+.0f}%</text>')
    for i, c in enumerate(pub):
        y = top + row_h * i + row_h / 2
        p = c["price"]
        legs = [("DCF", (c["dcf"] or p) / p - 1, "m-dcf"), ("Peer EV/Sales", (c["rel"] or p) / p - 1, "m-rel"),
                ("Target", c["tp"] / p - 1, "m-tp")]
        out.append(f'<text x="{left - 12}" y="{y + 4:.1f}" class="rowlabel">{e(c["ticker"])}</text>')
        xs = [x(v) for _, v, _ in legs]
        out.append(f'<line x1="{min(xs):.1f}" x2="{max(xs):.1f}" y1="{y:.1f}" y2="{y:.1f}" class="span"/>')
        for name, v, cls in legs:
            cx = x(v)
            label = f"{name}: {v * 100:+.1f}% vs close {money(p)}"
            if cls == "m-dcf":
                out.append(f'<circle cx="{cx:.1f}" cy="{y:.1f}" r="6" class="{cls}"><title>{e(label)}</title></circle>')
            elif cls == "m-rel":
                out.append(f'<rect x="{cx - 6:.1f}" y="{y - 6:.1f}" width="12" height="12" class="{cls}"><title>{e(label)}</title></rect>')
            else:
                out.append(f'<path d="M{cx:.1f},{y - 9:.1f} L{cx + 9:.1f},{y:.1f} L{cx:.1f},{y + 9:.1f} L{cx - 9:.1f},{y:.1f} Z" class="{cls}"><title>{e(label)}</title></path>')
        out.append(f'<text x="{x(c["tp"] / p - 1):.1f}" y="{y - 13:.1f}" class="tplabel">{money(c["tp"])} ({pct(c["upside"])})</text>')
    out.append("</svg>")
    return "".join(out)


def findings_bars(c: dict) -> str:
    by = {}
    for f in c["findings"]:
        fam = f["id"].split("-")[0]
        d = by.setdefault(fam, {"closed": 0, "open": 0})
        d["closed" if f.get("status") == "closed" else "open"] += 1
    if not by:
        return '<p class="empty">No findings recorded.</p>'
    mx = max(d["closed"] + d["open"] for d in by.values())
    rows = []
    for fam in sorted(by):
        d = by[fam]
        wc, wo = d["closed"] / mx * 100, d["open"] / mx * 100
        rows.append(f'<div class="fbar"><span class="fname">{e(CRITIC.get(fam, fam))}</span>'
                    f'<span class="ftrack"><span class="fc" style="width:{wc:.1f}%"></span>'
                    f'<span class="fo" style="width:{wo:.1f}%"></span></span>'
                    f'<span class="fnum">{d["closed"]} closed · {d["open"]} open</span></div>')
    return "".join(rows)


# ------------------------------------------------------------------ page
def build() -> str:
    cases = case_rows()
    evo = evolution_rows()
    intr = interruptions()
    reg = registry()
    try:
        import yaml
        cfg = yaml.safe_load((ROOT / "config" / "project.yaml").read_text())
    except Exception:  # noqa: BLE001
        cfg = {}
    bands = (cfg.get("publication") or {}).get("rating_bands") or {}
    coverage = cfg.get("coverage") or []
    pub = [c for c in cases if c["status"] == "PUBLISHED"]
    commit = _git("rev-parse", "--short", "HEAD") or "unknown"
    n_commits = _git("rev-list", "--count", "HEAD") or "?"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    researched = sorted({c["ticker"] for c in cases if c["status"] != "USER_STOPPED"})
    tl = timeline(cases, evo)
    adopted = [x for x in evo if x["state"] == "ADOPTED"]
    rejected = [x for x in evo if x["state"] == "REJECTED"]
    n_tests = test_count()

    kpi = [
        (f"{len(pub)}", "notes published", ", ".join(c["ticker"] for c in pub)),
        (f"{sum(c['opened_n'] for c in cases)}", "review findings raised",
         f"{sum(c['closed_n'] for c in cases)} closed by repair · {sum(c['open_n'] for c in pub)} minor open on published notes"),
        (f"{len(adopted)} / {len(evo)}", "prompt changes adopted",
         f"{len(rejected)} rejected by the reviewer · active gen-writer {reg['active'].get('gen-writer', '?')}"),
        (f"{len(intr)}", "interruptions recorded", "every one resumed, replaced or closed"),
        (f"{incident_count()}", "incidents fixed", "with root cause in docs/incidents.md"),
        (f"{n_tests}", "regression tests", "python3 scripts/check.py"),
    ]
    kpi_html = "".join(f'<div class="kpi{" lead" if i == 0 else ""}"><div class="kv">{e(v)}</div>'
                       f'<div class="kl">{e(lab)}</div><div class="ks">{e(sub)}</div></div>'
                       for i, (v, lab, sub) in enumerate(kpi))

    def case_tr(c):
        upside = c["upside"]
        return (f'<tr data-status="{e(c["status"])}">'
                f'<td><a href="cases/{e(c["case_id"])}/">{e(c["case_id"])}</a>'
                f'<div class="sub">{e(c["form"])} · cutoff {e((c["cutoff"] or "")[:16].replace("T", " "))} UTC</div></td>'
                f'<td>{badge(c["status"])}' + (f'<div class="sub">{e(c["stop_reason"][:70])}</div>' if c["stop_reason"] else "") + '</td>'
                f'<td class="num" data-v="{c["rounds"]}">{c["rounds"]}</td>'
                f'<td class="num" data-v="{c["reviews"]}">{c["reviews"]}</td>'
                f'<td class="num" data-v="{c["opened_n"]}">{c["opened_n"]} / {c["closed_n"]} / {c["open_n"]}</td>'
                f'<td class="num" data-v="{c["price"] or -1}">{money(c["price"])}</td>'
                f'<td class="num" data-v="{c["tp"] or -1}">{money(c["tp"])}</td>'
                f'<td class="num" data-v="{upside if upside is not None else -9}">{pct(upside)}</td>'
                f'<td>{e(c["rating"] or "—")}</td>'
                f'<td>' + (f'<a href="{e(c["pdf"])}">PDF</a>' if c["pdf"] else '<span class="muted">—</span>') + '</td></tr>')

    statuses = sorted({c["status"] for c in cases}, key=lambda s: STATUS_ORDER.index(s) if s in STATUS_ORDER else 99)
    filters = '<button type="button" class="chip on" data-f="ALL" aria-pressed="true">All</button>' + "".join(
        f'<button type="button" class="chip" data-f="{e(s)}" aria-pressed="false">{e(s.replace("_", " ").title())}</button>'
        for s in statuses)

    pub_cards = []
    for c in pub:
        open_items = "".join(f'<li><code>{e(f["id"])}</code> {e(f.get("check", ""))}</li>'
                             for f in c["findings"] if f.get("status") == "open")
        appr = c["approval"] or {}
        pub_cards.append(
            f'<article class="pcard"><header><h3>{e(c["ticker"])} <span class="muted">{e(c["case_id"])}</span></h3>'
            f'<p class="sub">{e(c["form"])} · {c["rounds"]} round(s) · {c["reviews"]} reviews · approved '
            f'{e((appr.get("at") or "")[:16].replace("T", " "))} UTC · DCF weight {pct(c["dcf_weight"], False)}</p></header>'
            f'{findings_bars(c)}'
            + (f'<details><summary>{c["open_n"]} minor finding(s) left open (printed in the PDF)</summary><ul class="open">{open_items}</ul></details>'
               if open_items else '<p class="sub">No open findings.</p>')
            + '</article>')

    evo_rows = "".join(
        f'<tr><td><a href="evolution/changes/{e(x["id"])}/">{e(x["id"])}</a><div class="sub">{e(x["role"])} from {e(x["parent"])}</div></td>'
        f'<td class="num">{x["baseline_pass"]} / {x["total"]}</td><td class="num">{x["candidate_pass"]} / {x["total"]}</td>'
        f'<td>{"yes" if x["separated"] else "no"}' + (f'<div class="sub">withheld: {e(", ".join(x["withheld"]))}</div>' if x["withheld"] else "") + '</td>'
        f'<td>{e(x["verdict"] or "—")}</td><td>{badge(x["state"])}'
        + (f'<div class="sub">→ {e(x["adopted"])}; post-adoption check {"passed" if x["verified"] else "failed" if x["verified"] is False else "—"}</div>' if x["adopted"] else "")
        + '</td></tr>' for x in evo)

    intr_rows = "".join(
        f'<tr><td class="num">{x["n"]}</td><td>{e(x["when"])}</td><td>{e(re.sub(r"[`*]", "", x["what"]))}</td>'
        f'<td>{e(re.sub(r"[`*]", "", x["type"]))}</td><td>{e(re.sub(r"[`*]", "", x["kept"]))}</td></tr>' for x in intr)

    tl_items, day = [], None
    for t in tl:
        d = t["ts"][:10]
        if d != day:
            tl_items.append(f'<li class="day">{e(d)}</li>')
            day = d
        tl_items.append(f'<li class="t-{e(t["kind"])}"><time>{e(t["ts"][11:16])}</time><span>{e(t["text"])}</span></li>')

    active_versions = "".join(f'<li><code>{e(r)}</code> {e(v)}</li>' for r, v in sorted(reg.get("active", {}).items()))

    return TEMPLATE.format(
        css=CSS, js=JS, now=e(now), commit=e(commit), n_commits=e(n_commits), kpi=kpi_html,
        coverage=e(", ".join(coverage)), researched=e(", ".join(researched)),
        untested=e(", ".join(t for t in coverage if t not in researched)),
        filters=filters, case_rows="".join(case_tr(c) for c in cases), n_cases=len(cases),
        valuation=valuation_svg(cases, bands), pub_cards="".join(pub_cards), evo_rows=evo_rows,
        intr_rows=intr_rows, timeline="".join(tl_items), versions=active_versions,
        weights=e("DCF weight " + ", ".join(f"{c['ticker']} {c['dcf_weight'] * 100:.0f}%" for c in pub if c["dcf_weight"] is not None)))


def write(path: Path = OUT) -> Path:
    path.write_text(build(), encoding="utf-8")
    return path


CSS = r"""
:root{--paper:#f7f5f0;--panel:#fffdf8;--ink:#1c2230;--muted:#5d6472;--rule:#d9d4c7;--accent:#1f4e79;
--pub:#1d6b57;--stall:#9a5b13;--stop:#6b6f78;--rej:#9b2c2c;--band-u:#f3e3dc;--band-o:#dfece5;
--dcf:#1f4e79;--rel:#b0752b;--tp:#1c2230;--focus:#c26d00}
@media (prefers-color-scheme: dark){:root{--paper:#14171d;--panel:#1b1f27;--ink:#e8e6e1;--muted:#a3a8b3;
--rule:#323844;--accent:#8db7e0;--pub:#5fc0a2;--stall:#e0a85c;--stop:#a3a8b3;--rej:#ef8a8a;--band-u:#3a2a26;
--band-o:#22362e;--dcf:#8db7e0;--rel:#e0a85c;--tp:#e8e6e1}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 "Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif}
.wrap{max-width:1180px;margin:0 auto;padding:28px 16px 64px}
h1,h2,h3,.kv,.chip,table,.sub,.kl,.ks,.badge,.tick,.band-label,.rowlabel,.tplabel,nav,time,code,.fnum,.fname{font-family:"Avenir Next","Segoe UI",Helvetica,Arial,sans-serif}
h1{font-size:28px;line-height:1.15;margin:4px 0 6px;letter-spacing:-.01em}
h2{font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);margin:44px 0 12px;border-top:2px solid var(--ink);padding-top:10px}
h3{font-size:16px;margin:0}
.eyebrow{font:600 12px/1 "Avenir Next","Segoe UI",sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.lede{max-width:760px;color:var(--muted);margin:6px 0 0}
.meta{display:flex;flex-wrap:wrap;gap:6px 18px;margin-top:12px;font:13px "Avenir Next","Segoe UI",sans-serif;color:var(--muted)}
.meta b{color:var(--ink);font-weight:600}
nav{display:flex;flex-wrap:wrap;gap:4px 14px;margin-top:16px;font-size:13px}
a{color:var(--accent)}a:focus-visible,button:focus-visible,summary:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.kpis{display:grid;grid-template-columns:1.4fr repeat(5,1fr);gap:0;margin-top:22px;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule)}
.kpi{padding:14px 14px 14px 0;border-right:1px solid var(--rule);margin-right:14px}.kpi:last-child{border-right:0;margin-right:0}
.kv{font-size:30px;font-weight:600;font-variant-numeric:tabular-nums;line-height:1.1}.lead .kv{font-size:44px;color:var(--pub)}
.kl{font-size:13px;font-weight:600;margin-top:4px}.ks{font-size:12px;color:var(--muted);margin-top:2px}
.scope{background:var(--panel);border-left:4px solid var(--accent);padding:10px 14px;margin-top:18px;font-size:14px}
.tablewrap{overflow-x:auto;border:1px solid var(--rule);background:var(--panel)}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{padding:8px 10px;border-bottom:1px solid var(--rule);text-align:left;vertical-align:top}
th{font-weight:600;font-size:12px;color:var(--muted);white-space:nowrap;background:var(--panel)}
th button{all:unset;cursor:pointer}th button::after{content:" ↕";opacity:.4}th[aria-sort=ascending] button::after{content:" ↑";opacity:1}th[aria-sort=descending] button::after{content:" ↓";opacity:1}
#cases td:first-child{min-width:190px}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.sub{font-size:12px;color:var(--muted);margin-top:2px}.muted{color:var(--muted);font-weight:400}
.badge{font-size:11px;font-weight:700;letter-spacing:.04em;white-space:nowrap}
.s-published,.s-adopted{color:var(--pub)}.s-stalled{color:var(--stall)}.s-user_stopped{color:var(--stop)}.s-rejected{color:var(--rej)}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px}
.chip{font-size:12px;border:1px solid var(--rule);background:var(--panel);color:var(--ink);padding:5px 10px;border-radius:999px;cursor:pointer}
.chip.on{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.count{font:12px "Avenir Next","Segoe UI",sans-serif;color:var(--muted);margin:6px 0 0}
.split{display:grid;grid-template-columns:2fr 1fr;gap:28px;align-items:start}
.chart{width:100%;height:auto;background:var(--panel);border:1px solid var(--rule)}
.band-u{fill:var(--band-u)}.band-o{fill:var(--band-o)}.grid{stroke:var(--rule)}.zero{stroke:var(--ink);stroke-width:1.5}
.tick,.band-label{font-size:11px;fill:var(--muted);text-anchor:middle}.rowlabel{font-size:13px;font-weight:700;fill:var(--ink);text-anchor:end}
.tplabel{font-size:11px;fill:var(--ink);text-anchor:middle;font-weight:600}.span{stroke:var(--muted);stroke-width:2;opacity:.5}
.m-dcf{fill:var(--dcf)}.m-rel{fill:var(--rel)}.m-tp{fill:var(--tp);stroke:var(--panel);stroke-width:1.5}
.legend{display:flex;flex-wrap:wrap;gap:6px 16px;font:12px "Avenir Next","Segoe UI",sans-serif;color:var(--muted);margin-top:8px}
.legend i{display:inline-block;width:11px;height:11px;margin-right:5px;vertical-align:-1px}
.note{font-size:13px;color:var(--muted)}
.pcards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.pcard{background:var(--panel);border:1px solid var(--rule);padding:14px}
.fbar{display:grid;grid-template-columns:92px 1fr;gap:2px 8px;align-items:center;margin-top:10px;font-size:12px}
.fname{font-weight:600}.ftrack{display:flex;height:10px;background:var(--paper);border:1px solid var(--rule)}
.fc{background:var(--pub)}.fo{background:repeating-linear-gradient(45deg,var(--stall) 0 3px,transparent 3px 6px);border-left:1px solid var(--stall)}
.fnum{grid-column:2;color:var(--muted);font-variant-numeric:tabular-nums}
details{margin-top:12px;font-size:13px}summary{cursor:pointer;font-weight:600}
ul.open{padding-left:18px;margin:6px 0 0}ul.open li{margin:4px 0}code{font-size:12px}
ol.tl{list-style:none;margin:0;padding:0;border-left:2px solid var(--rule)}
ol.tl li{display:grid;grid-template-columns:54px 1fr;gap:10px;padding:4px 0 4px 14px;position:relative;font-size:13px}
ol.tl li::before{content:"";position:absolute;left:-6px;top:10px;width:10px;height:10px;border-radius:50%;background:var(--muted)}
ol.tl li.day{display:block;font:700 12px "Avenir Next","Segoe UI",sans-serif;letter-spacing:.08em;color:var(--accent);padding-top:14px}
ol.tl li.day::before{display:none}
ol.tl li.t-publish::before{background:var(--pub)}ol.tl li.t-hold::before,ol.tl li.t-stop::before{background:var(--stall);border-radius:0}
ol.tl li.t-evo::before{background:var(--accent);transform:rotate(45deg);border-radius:0}
time{color:var(--muted);font-variant-numeric:tabular-nums}
.cols{columns:2;font-size:13px;padding-left:18px}
footer{margin-top:48px;border-top:1px solid var(--rule);padding-top:12px;font:12px "Avenir Next","Segoe UI",sans-serif;color:var(--muted)}
@media (max-width:900px){.kpis{grid-template-columns:repeat(2,1fr)}.kpi{border-right:0;margin-right:0;border-bottom:1px solid var(--rule)}
.split,.pcards{grid-template-columns:1fr}.cols{columns:1}h1{font-size:23px}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
"""

JS = r"""
(function(){
  var tbody=document.querySelector('#cases tbody'), count=document.getElementById('casecount');
  function refresh(){var n=0;tbody.querySelectorAll('tr').forEach(function(r){if(!r.hidden)n++;});
    count.textContent=n+' of '+tbody.rows.length+' cases shown';}
  document.querySelectorAll('.chip').forEach(function(b){b.addEventListener('click',function(){
    document.querySelectorAll('.chip').forEach(function(x){x.classList.remove('on');x.setAttribute('aria-pressed','false');});
    b.classList.add('on');b.setAttribute('aria-pressed','true');var f=b.dataset.f;
    tbody.querySelectorAll('tr').forEach(function(r){r.hidden=!(f==='ALL'||r.dataset.status===f);});refresh();});});
  document.querySelectorAll('#cases th[data-col] button').forEach(function(btn){btn.addEventListener('click',function(){
    var th=btn.parentNode, col=+th.dataset.col, num=th.classList.contains('num');
    var dir=th.getAttribute('aria-sort')==='ascending'?'descending':'ascending';
    document.querySelectorAll('#cases th').forEach(function(x){x.removeAttribute('aria-sort');});th.setAttribute('aria-sort',dir);
    var rows=Array.prototype.slice.call(tbody.rows);
    rows.sort(function(a,b){var x=a.cells[col],y=b.cells[col];
      var u=num?parseFloat(x.dataset.v):x.textContent.trim(), v=num?parseFloat(y.dataset.v):y.textContent.trim();
      var c=num?u-v:String(u).localeCompare(String(v));return dir==='ascending'?c:-c;});
    rows.forEach(function(r){tbody.appendChild(r);});});});
  refresh();
})();
"""

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Earnings-update workflow dashboard</title>
<style>{css}</style>
</head>
<body>
<div class="wrap">
<header>
<div class="eyebrow">AI Coding in Finance · Final project · evidence dashboard</div>
<h1>Semiconductor earnings-update workflow: what ran, what was caught, what was published</h1>
<p class="lede">Generated from the repository's evidence files by <code>python3 scripts/eu.py dashboard</code>.
Figures are read from case state, finding ledgers, controller recomputes and registers; nothing is typed by hand.
For coursework demonstration only; not investment advice.</p>
<div class="meta"><span>Generated <b>{now}</b></span><span>Data as of commit <b>{commit}</b> ({n_commits} commits)</span>
<span>Prices: last close before each case's SEC cutoff, US$</span></div>
<nav aria-label="Sections"><a href="#cases">Cases</a><a href="#valuation">Valuation</a><a href="#review">Review</a>
<a href="#evolution">Evolution</a><a href="#interruptions">Interruptions</a><a href="#timeline">Timeline</a>
<a href="README.md">README</a><a href="docs/design_note.md">Design note</a></nav>
</header>

<section class="kpis" aria-label="Key measures">{kpi}</section>
<p class="scope"><b>Scope.</b> Configured coverage: {coverage}. Research cases were run for <b>{researched}</b>;
{untested} are configured but have no case.</p>

<h2 id="cases">Cases</h2>
<div class="chips" role="group" aria-label="Filter cases by status">{filters}</div>
<div class="tablewrap"><table id="cases">
<thead><tr><th data-col="0"><button>Case</button></th><th data-col="1"><button>Status</button></th>
<th class="num" data-col="2"><button>Rounds</button></th><th class="num" data-col="3"><button>Reviews</button></th>
<th class="num" data-col="4"><button>Findings opened / closed / open</button></th>
<th class="num" data-col="5"><button>Last close</button></th><th class="num" data-col="6"><button>Target</button></th>
<th class="num" data-col="7"><button>Upside</button></th><th data-col="8"><button>Rating</button></th><th>Note</th></tr></thead>
<tbody>{case_rows}</tbody></table></div>
<p class="count" id="casecount" aria-live="polite"></p>
<p class="note">Stalled and stopped cases are kept as evidence: NVDA r1 shows the bounded loop stopping on a finding the
specialists could not fix; AMD r1 a deliberate interruption and a false stall from a gate defect; AMD 0000002488-26-000123
the live Stop-hook test. Revisions (<code>-r2</code>) re-ran the same filing after a fix. Target and upside of a
non-published case are the last controller recompute, not a published view.</p>

<h2 id="valuation">Valuation: how far apart the two methods are</h2>
<div class="split"><div>{valuation}
<div class="legend"><span><i style="background:var(--dcf);border-radius:50%"></i>DCF per share</span>
<span><i style="background:var(--rel)"></i>Peer EV/Sales per share</span>
<span><i style="background:var(--tp);transform:rotate(45deg)"></i>Blended target price</span>
<span>Vertical line: last close (0%)</span></div></div>
<div class="note"><p>Each leg is shown as a percentage of the last close before the cutoff. The target blends the two legs
({weights}), so the rating follows the DCF. In every published case the peer leg sits far above
the DCF leg: the ratings are policy-consistent but low-conviction (design note §6).</p>
<p>Shaded areas are the house rating bands from <code>config/project.yaml</code>.</p></div></div>

<h2 id="review">Independent review of the published notes</h2>
<div class="pcards">{pub_cards}</div>
<p class="note">Bars count findings by the critic that raised them across all rounds: solid = closed after a repair,
hatched = still open (minor only; minor findings do not block acceptance and are printed in each PDF).</p>

<h2 id="evolution">Evolution: evaluated, approved, reversible prompt changes</h2>
<div class="split"><div class="tablewrap"><table>
<thead><tr><th>Change</th><th class="num">Baseline passes</th><th class="num">Candidate passes</th><th>Arms separated</th>
<th>Reviewer</th><th>Outcome</th></tr></thead><tbody>{evo_rows}</tbody></table></div>
<div class="note"><p>A change is adopted only if the evaluation separates the arms (the baseline reproduces the failure),
the candidate passes every case, a fresh reviewer recommends it and the owner approves. change-001 and change-002
failed the first condition; change-003 kept the failure condition by withholding the code-supplied values.</p>
<p><b>Active prompt versions</b></p><ul class="cols">{versions}</ul></div></div>

<h2 id="interruptions">Interruptions and how each resumed</h2>
<div class="tablewrap"><table><thead><tr><th class="num">#</th><th>When (UTC)</th><th>What stopped</th><th>Type</th>
<th>Kept / redone</th></tr></thead><tbody>{intr_rows}</tbody></table></div>
<p class="note">Full register with state at the stop and evidence: <a href="docs/interruptions.md">docs/interruptions.md</a>.
Problems and fixes: <a href="docs/incidents.md">docs/incidents.md</a>; refusals: <a href="docs/rejections.md">docs/rejections.md</a>.</p>

<h2 id="timeline">Timeline</h2>
<ol class="tl">{timeline}</ol>

<footer>Sources: <code>cases/*/state.json</code>, <code>trace.jsonl</code>, <code>rounds/*/numerical/recompute/valuation.json</code>,
<code>approvals.jsonl</code>, <code>evolution/changes/*</code>, <code>prompts/registry.json</code>, <code>docs/interruptions.md</code>,
<code>docs/incidents.md</code>, <code>tests/</code>. Links are relative to the project folder. Not investment advice.</footer>
</div>
<script>{js}</script>
</body>
</html>
"""
