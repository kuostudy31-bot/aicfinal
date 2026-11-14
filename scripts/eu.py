#!/usr/bin/env python3
"""Command-line entry point for the earnings-update workflow (controller actions).

Agents and people use these commands; only this controller writes state.json.

  watch     detect new 10-Q/10-K filings for the coverage list -> events/events.jsonl
  open      open (or return) the case for a filing and issue the first generator request
  request   show the pending request for a case
  compute   run the deterministic pipeline for the current round (generator use)
  submit    validate the pending submission and advance / repair / stop
  resume    verify saved evidence and name the next action after an interruption
  status    write and print the status board
  approve   record a named approver's publish decision
  stop      stop a case at the user's request
  prompt    print the active prompt file for a role (pinned per case)
  publish   render the approved note to PDF
  evo-*     evolution commands (see src/aicfinal/evolution.py)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aicfinal import ROOT, compute, controller, edgar  # noqa: E402
from aicfinal.util import append_jsonl, iso, load_config, parse_iso, read_json, read_jsonl, utcnow  # noqa: E402

EVENTS = ROOT / "events" / "events.jsonl"


def cmd_watch(a):
    cfg = load_config()
    seen = {e["accession"] for e in read_jsonl(EVENTS)}
    as_of = a.as_of or iso(utcnow())
    since = a.since or iso(parse_iso(as_of).replace(year=parse_iso(as_of).year - 1))
    new = []
    for t in (a.tickers or cfg["coverage"]):
        cik = edgar.cik_for(t)
        for f in edgar.filings(cik):
            if f["form"] in cfg["triggers"]["forms"] and since < f["acceptance_utc"] <= as_of \
                    and f["accessionNumber"] not in seen:
                ev = {"event_id": f["accessionNumber"], "accession": f["accessionNumber"], "ticker": t,
                      "form": f["form"], "period_of_report": f["reportDate"],
                      "acceptance_utc": f["acceptance_utc"], "detected_at": iso(utcnow()), "as_of": as_of,
                      "status": "NEW"}
                append_jsonl(EVENTS, ev)
                seen.add(ev["accession"])
                new.append(ev)
    print(json.dumps({"as_of": as_of, "new_events": new}, indent=2))


def cmd_open(a):
    st = controller.open_case(a.ticker, a.accession, a.peers.split(",") if a.peers else None,
                              revision=a.revision, reason=a.reason)
    print(json.dumps({k: st[k] for k in ("case_id", "status", "round", "pending", "cutoff_utc")}, indent=2))


def cmd_request(a):
    st = controller.load_state(a.case)
    pend = st.get("pending")
    out = {"case_id": a.case, "status": st["status"], "pending": pend}
    if pend and pend.get("path"):
        out["request"] = read_json(ROOT / pend["path"])
    print(json.dumps(out, indent=2))


def cmd_compute(a):
    st = controller.load_state(a.case)
    rdir = controller.case_dir(a.case) / "rounds" / f"round-{st['round']:03d}"
    res = compute.run(controller.case_dir(a.case), rdir)
    print(json.dumps({"hashes": res["hashes"], "gate_findings": res["findings"],
                      "target_price": res["valuation"]["target_price"], "rating": res["valuation"]["rating"]},
                     indent=2))


def cmd_submit(a):
    st = controller.submit(a.case)
    print(json.dumps({k: st.get(k) for k in ("case_id", "status", "round", "review", "clean_streak",
                                              "invalid_submissions", "pending", "stop_reason")}, indent=2))


def cmd_resume(a):
    print(json.dumps(controller.resume(a.case), indent=2))


def board() -> str:
    lines = ["# Status board", "", f"_Generated {iso(utcnow())} by `scripts/eu.py status`._", "",
             "| Case | Status | Round | Review | Clean streak | Open blocking findings | Pending | TP / rating |",
             "|---|---|---|---|---|---|---|---|"]
    for sp in sorted((ROOT / "cases").glob("*/state.json")):
        s = read_json(sp)
        ob = [k for k, v in s["ledger"].items() if v["status"] == "open" and v["severity"] in ("blocker", "major")]
        res = sp.parent / "result.json"
        tp = ""
        if res.exists():
            r = read_json(res)
            if r.get("target_price"):
                tp = f"${r['target_price']} / {r.get('rating')}"
        pend = (s.get("pending") or {}).get("phase", "")
        lines.append(f"| {s['case_id']} | {s['status']} | {s['round']} | {s['review']} | {s['clean_streak']} | "
                     f"{', '.join(ob) or '-'} | {pend or '-'} | {tp or '-'} |")
    ev = read_jsonl(EVENTS)
    lines += ["", f"Events detected: {len(ev)} (see `events/events.jsonl`)."]
    return "\n".join(lines) + "\n"


def cmd_status(a):
    text = board()
    (ROOT / "STATUS.md").write_text(text, encoding="utf-8")
    print(text)


def cmd_approve(a):
    st = controller.approve(a.case, a.approver, a.decision, a.note or "")
    print(json.dumps({"case_id": a.case, "status": st["status"], "approval": st.get("approval")}, indent=2))


def cmd_stop(a):
    st = controller.stop(a.case, a.reason)
    print(json.dumps({"case_id": a.case, "status": st["status"]}, indent=2))


def cmd_prompt(a):
    versions = (controller.load_state(a.case)["prompt_versions"] if a.case
                else read_json(ROOT / load_config()["prompt_registry_file"])["active"])
    ver = versions[a.role]
    path = ROOT / "prompts" / a.role / f"{ver}.md"
    print(path.relative_to(ROOT))


def cmd_concepts(a):
    """Read-only helper for gen-mapping: candidate concepts for a line and their coverage."""
    from aicfinal import snapshot as snap, xbrl
    st = controller.load_state(a.case)
    facts = read_json(controller.case_dir(a.case) / "snapshot" / "facts.json")
    cat = snap.catalog()
    spec = cat[a.line]
    names = spec["candidates"] + [c for c in (a.extra or [])]
    if a.search:
        names += [c for c in facts["available_us_gaap_concepts"] if a.search.lower() in c.lower()]
    out = []
    for c in dict.fromkeys(names):
        unit = spec.get("unit", "USD")
        ser = xbrl.quarterly(facts["facts"], c, unit) if spec["kind"] == "duration" else xbrl.instants(facts["facts"], c, unit)
        out.append({"concept": c, "in_snapshot": bool(ser), "observations": len(ser),
                    "latest_end": ser[-1]["end"] if ser else None, "latest_val": ser[-1]["val"] if ser else None,
                    "in_catalog": c in spec["candidates"]})
    print(json.dumps({"line": a.line, "kind": spec["kind"], "period_of_report": st["period_of_report"],
                      "candidates": out,
                      "note": "facts.json holds every concept the company reported before the cutoff; "
                              "use --search <word> to list them, and map a list to sum parts."}, indent=2))


def cmd_history(a):
    """Read-only helper: quarterly history table from the current round's mapping."""
    from aicfinal import model, snapshot as snap
    st = controller.load_state(a.case)
    cdir = controller.case_dir(a.case)
    mp = cdir / "rounds" / f"round-{st['round']:03d}" / "generator" / "mapping.json"
    hist = model.history(read_json(cdir / "snapshot" / "facts.json"), read_json(mp)["mapping"], snap.catalog())
    rows = {"quarters": [f"{q['fiscal']} ({q['calendar']}, ends {q['end']})" for q in hist["quarters"]]}
    for line, vals in hist["lines"].items():
        rows[line] = [None if v is None else {"val": v["val"], "id": v["id"], "derived": v["derived"]} for v in vals]
    print(json.dumps(rows, indent=1))


def cmd_publish(a):
    from aicfinal import publish
    print(publish.render(a.case))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("watch"); s.add_argument("--as-of"); s.add_argument("--since"); s.add_argument("--tickers", nargs="*")
    s.set_defaults(fn=cmd_watch)
    s = sub.add_parser("open"); s.add_argument("--ticker", required=True); s.add_argument("--accession", required=True)
    s.add_argument("--peers"); s.add_argument("--revision", type=int, default=1)
    s.add_argument("--reason", help="required for --revision > 1: which input version changed")
    s.set_defaults(fn=cmd_open)
    for name, fn in (("request", cmd_request), ("compute", cmd_compute), ("submit", cmd_submit),
                     ("resume", cmd_resume), ("publish", cmd_publish)):
        s = sub.add_parser(name); s.add_argument("--case", required=True); s.set_defaults(fn=fn)
    s = sub.add_parser("status"); s.set_defaults(fn=cmd_status)
    s = sub.add_parser("concepts"); s.add_argument("--case", required=True); s.add_argument("--line", required=True)
    s.add_argument("--search"); s.add_argument("--extra", nargs="*"); s.set_defaults(fn=cmd_concepts)
    s = sub.add_parser("history"); s.add_argument("--case", required=True); s.set_defaults(fn=cmd_history)
    s = sub.add_parser("approve"); s.add_argument("--case", required=True); s.add_argument("--approver", required=True)
    s.add_argument("--decision", choices=["approve", "reject"], required=True); s.add_argument("--note")
    s.set_defaults(fn=cmd_approve)
    s = sub.add_parser("stop"); s.add_argument("--case", required=True); s.add_argument("--reason", required=True)
    s.set_defaults(fn=cmd_stop)
    s = sub.add_parser("prompt"); s.add_argument("--role", required=True); s.add_argument("--case")
    s.set_defaults(fn=cmd_prompt)
    try:
        from aicfinal import evolution
        evolution.add_commands(sub)
    except ImportError:
        pass
    a = p.parse_args(argv)
    try:
        a.fn(a)
    except controller.ControllerError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
