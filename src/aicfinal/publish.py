"""Render a published case as an A4 PDF memo (latex skill template, English).

Generated content stays separate from authored wrappers, per the latex skill:
  output/tables/<case>/key_data.tex      generated booktabs tabular only
  output/figures/<case>/revenue.pdf      generated chart (plot skill defaults)
  report/<case>/sections/*.tex           wrappers: captions, units, source notes
  report/<case>/main.tex                 template with header macros + note body
Only PUBLISHED cases are rendered; every figure comes from the recomputed files.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from . import ROOT
from .util import read_json

TEMPLATE = ROOT / ".claude" / "skills" / "latex" / "finance" / "assets" / "report_template.tex"


def tex_escape(s: str) -> str:
    rep = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
           "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(rep.get(c, c) for c in s)


def md_to_tex(md: str) -> str:
    """Small Markdown subset: ##/### headings, '-' bullets, **bold**, paragraphs."""
    out, in_list = [], False
    for raw in md.splitlines():
        line = raw.rstrip()
        if line.startswith("# "):
            continue  # title is in the header block
        if re.match(r"^\s*[-*] ", line):
            if not in_list:
                out.append(r"\begin{itemize}\setlength{\itemsep}{1pt}")
                in_list = True
            out.append(r"\item " + _inline(re.sub(r"^\s*[-*] ", "", line)))
            continue
        if in_list:
            out.append(r"\end{itemize}")
            in_list = False
        if line.startswith("#"):
            out.append(r"\par\smallskip\textbf{\color{MemoBlue}" + _inline(line.lstrip("#").strip()) + r"}\par")
        elif not line.strip():
            out.append("")
        else:
            out.append(_inline(line))
    if in_list:
        out.append(r"\end{itemize}")
    return "\n".join(out)


def _inline(s: str) -> str:
    parts = re.split(r"(\*\*[^*]+\*\*)", s)
    return "".join(r"\textbf{" + tex_escape(p[2:-2]) + "}" if p.startswith("**") else tex_escape(p) for p in parts)


def _figure(hist: dict, fc: dict, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 7, "axes.spines.top": False, "axes.spines.right": False,
                         "pdf.fonttype": 42, "savefig.bbox": "tight"})
    rev = [v["val"] / 1e9 if v else None for v in hist["lines"]["revenue"]]
    def short(label: str) -> str:  # "FY2027Q2" -> "2Q27"
        m = re.match(r"FY\d\d(\d\d)Q(\d)", label)
        return f"{m.group(2)}Q{m.group(1)}" if m else label

    labels = [short(q["fiscal"]) for q in hist["quarters"]]
    f_rev = [q["revenue"] / 1e9 for q in fc["quarters"]]
    f_lab = [short(q["label"]) + "E" for q in fc["quarters"]]
    fig, ax = plt.subplots(figsize=(2.6, 1.9))
    x1 = range(len(rev))
    ax.bar(list(x1), [r or 0 for r in rev], color="#203E70", label="Reported")
    x2 = range(len(rev), len(rev) + len(f_rev))
    ax.bar(list(x2), f_rev, color="#B9C8DF", hatch="///", edgecolor="#203E70", linewidth=0.4,
           label="Forecast (model)")
    ax.set_xticks(list(x1) + list(x2), labels + f_lab, fontsize=5, rotation=90)
    ax.set_xlabel("Fiscal quarter (E = model estimate)", fontsize=5.5)
    ax.set_ylabel("Revenue (US$ bn)")
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=5.5, frameon=False, loc="upper left")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def _table(values: dict, val: dict, path: Path) -> None:
    rows = [("Revenue (quarter)", "revenue_q"), ("Revenue q/q", "revenue_qoq"), ("Revenue y/y", "revenue_yoy"),
            ("Gross margin", "gross_margin_q"), ("Operating margin", "operating_margin_q"),
            ("Diluted EPS", "eps_q"), ("Free cash flow", "fcf_q"), ("NTM revenue (model)", "ntm_revenue"),
            ("NTM EPS (model)", "ntm_eps"), ("DCF value / share", "dcf_per_share"),
            ("Peer EV/Sales (median)", "peer_ev_sales"), ("Last close", "price"),
            ("Target price", "target_price"), ("Upside", "upside"), ("Rating", "rating")]
    lines = [r"\begin{tabular}{@{}lr@{}}", r"\toprule", r"Item & Value \\", r"\midrule"]
    for label, key in rows:
        if key in values:
            lines.append(f"{tex_escape(label)} & {tex_escape(values[key]['display'])} \\\\")
        if key == "fcf_q":
            lines.append(r"\midrule")
    lines += [r"\bottomrule", r"\end{tabular}"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render(case_id: str, author: str = "Coursework analyst (AI-assisted workflow)") -> str:
    cdir = ROOT / "cases" / case_id
    st = read_json(cdir / "state.json")
    if st["status"] != "PUBLISHED":
        raise ValueError(f"only PUBLISHED cases are rendered (status {st['status']})")
    rdir = cdir / "rounds" / f"round-{st['round']:03d}"
    rec = rdir / "numerical" / "recompute"
    hist, fc, val, values = (read_json(rec / n) for n in ("history.json", "forecast.json", "valuation.json",
                                                          "values.json"))
    note = (rec / "note_rendered.md").read_text(encoding="utf-8")
    approval = st["approval"]

    tab = ROOT / "output" / "tables" / case_id / "key_data.tex"
    fig = ROOT / "output" / "figures" / case_id / "revenue.pdf"
    _table(values, val, tab)
    _figure(hist, fc, fig)

    rep = ROOT / "report" / case_id
    (rep / "sections").mkdir(parents=True, exist_ok=True)
    fq, cq, pe = values["fiscal_quarter"]["display"], values["calendar_quarter"]["display"], values["period_end"]["display"]
    (rep / "sections" / "tables.tex").write_text(
        "\\captionof{table}{Key data, " + tex_escape(fq) + "}\\label{tab:key-data}\n"
        "{\\footnotesize Reported figures for the quarter ended " + tex_escape(pe) + " (" + tex_escape(cq) +
        ") from SEC XBRL facts; NTM, DCF and target price are model outputs. US\\$.\\par}\n"
        "\\input{../../output/tables/" + case_id + "/key_data.tex}\n", encoding="utf-8")
    (rep / "sections" / "figures.tex").write_text(
        "\\captionof{figure}{Quarterly revenue, reported and forecast}\\label{fig:revenue}\n"
        "{\\footnotesize Solid: reported (SEC XBRL, fiscal quarters). Hatched: model forecast from "
        "this case's assumptions. US\\$ bn.\\par}\n"
        "\\includegraphics[width=\\linewidth]{../../output/figures/" + case_id + "/revenue.pdf}\n",
        encoding="utf-8")

    tex = TEMPLATE.read_text(encoding="utf-8")
    macros = {
        "ReportTitle": f"{st['ticker']} {fq}: {values['rating']['display']}, target price {values['target_price']['display']}",
        "ReportType": "EARNINGS UPDATE",
        "ReportDate": approval["at"][:10],
        "DataDate": st["cutoff_utc"].replace("T", " ").replace("Z", " UTC"),
        "ReportScope": f"Quarter ended {pe} ({cq}); trigger filing {st['accession']}",
        "TeamName": "Semis Coverage (coursework)",
        "DeskName": "AI semiconductor supply chain",
        "ReportAuthor": author,
        "Coverage": "NVDA, AMD, INTC, AVGO, MRVL, MU, AMAT",
        "KeyFinding": (f"Revenue {values['revenue_q']['display']} ({values['revenue_qoq']['display']} q/q); "
                       f"target price {values['target_price']['display']} vs last close "
                       f"{values['price']['display']} ({values['upside']['display']})."),
    }
    for k, v in macros.items():
        tex = re.sub(r"\\newcommand\{\\" + k + r"\}\{[^\n]*\}",
                     lambda m, k=k, v=v: "\\newcommand{\\" + k + "}{" + tex_escape(v) + "}", tex)
    body = md_to_tex(note)
    left_block = re.search(r"\\textbf\{Scope\}.*?\\textbf\{Risks and limitations\}\\par\n\[[^\]]*\]\n", tex, re.S)
    tex = tex.replace(left_block.group(0), "\\textbf{Summary}\\par\nSee key points and full note below. "
                      "Figures are generated by code from SEC filings; prose is AI-drafted and human-approved.\n")
    tex = tex.replace("\\par\\vfill\n", "\\par\\bigskip\n" + body + "\n\\par\\vfill\n", 1)
    tex = tex.replace("[Identify the provider, retrieval date, original files, and source locators.]",
                      tex_escape(f"SEC EDGAR filings accepted at or before {st['cutoff_utc']} (trigger "
                                 f"{st['accession']}); last close {values['price']['display']} on the cutoff "
                                 "date from the Yahoo chart endpoint. Case files: cases/" + case_id + "."))
    tex = tex.replace("[Record completed verification and any outstanding checks.]",
                      tex_escape(f"Numerical and provenance gates passed; two consecutive clean reviews by three "
                                 f"independent critics (round {st['round']}); approved by {approval['approver']} "
                                 f"on {approval['at'][:10]}."))
    tex = tex.replace("[Describe actual methods and relevant AI assistance.]",
                      tex_escape("Claude Code agent team (orchestrator, generator and critic leads, eight "
                                 "specialists) under a Python controller; for coursework demonstration only, "
                                 "not investment advice."))
    (rep / "main.tex").write_text(tex, encoding="utf-8")
    subprocess.run(["latexmk", "-C"], cwd=rep, capture_output=True)
    res = subprocess.run(["latexmk", "-pdf", "-halt-on-error", "-interaction=nonstopmode", "main.tex"],
                         cwd=rep, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError("LaTeX failed; see report/" + case_id + "/main.log")
    shutil.copy(rep / "main.pdf", rep / f"{case_id}.pdf")
    return str((rep / f"{case_id}.pdf").relative_to(ROOT))
