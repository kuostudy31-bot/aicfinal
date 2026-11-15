"""Run the deterministic pipeline for one round from saved generator inputs.

Generator specialists call this through ``eu.py compute``; the controller calls
it again independently at the numerical gate and compares output hashes, so a
hand-edited computed file cannot pass.
"""
from __future__ import annotations

from pathlib import Path

from . import ROOT, gates, model, valuation, values
from .snapshot import catalog
from .util import load_config, read_json, write_json

INPUTS = ["mapping.json", "narrative.json", "assumptions.json", "valuation_inputs.json"]


def _docs(snap: Path) -> dict[str, str]:
    return {p.name: p.read_text(encoding="utf-8") for p in sorted((snap / "docs").glob("*.txt"))}


def prior_target(case_dir: Path, ticker: str, cutoff: str) -> float | None:
    best = None
    for res in (ROOT / "cases").glob("*/result.json"):
        if res.parent == case_dir:
            continue
        r = read_json(res)
        if r.get("ticker") == ticker and r.get("status") == "PUBLISHED" and r.get("cutoff_utc", "") < cutoff:
            if best is None or r["cutoff_utc"] > best["cutoff_utc"]:
                best = r
    return best["target_price"] if best else None


def run(case_dir: Path, round_dir: Path, out_subdir: str = "computed") -> dict:
    case_dir, round_dir = Path(case_dir), Path(round_dir)
    snap = case_dir / "snapshot"
    gen = round_dir / "generator"
    cat = catalog()
    cfg = load_config()
    facts = read_json(snap / "facts.json")
    prices = read_json(snap / "prices.json")
    peers_snap = read_json(snap / "peers.json")
    mapping = read_json(gen / "mapping.json")["mapping"]
    narrative = read_json(gen / "narrative.json")
    assumptions = read_json(gen / "assumptions.json")
    vinputs = read_json(gen / "valuation_inputs.json")

    hist = model.history(facts, mapping, cat)
    fc = model.forecast(hist, assumptions)
    peers_table = valuation.peer_multiples(peers_snap, cat, vinputs["peers"])
    price = prices["closes"][-1]["close"]
    val = valuation.value(hist, fc, vinputs, price, peers_table, cfg["publication"],
                          prior_target(case_dir, facts["ticker"], facts["cutoff_utc"]))
    man = read_json(snap / "manifest.json")
    vals = values.build(facts["ticker"], hist, fc, val, narrative,
                        {"accession": man.get("trigger_accession"), "cutoff_utc": facts["cutoff_utc"],
                         "release_accession": next((f.get("accession") for k, f in sorted(man.get("files", {}).items())
                                                    if k.startswith("docs/release_") and f.get("accession")), None),
                         "price_date": prices["closes"][-1]["date"],
                         "rating_bands": cfg["publication"]["rating_bands"]})

    note_path = gen / "note.md"
    note_md = note_path.read_text(encoding="utf-8") if note_path.exists() else None
    quotes = {q["id"]: q for q in narrative.get("quotes", [])}
    out = round_dir / out_subdir
    hashes = {
        "history.json": write_json(out / "history.json", hist),
        "forecast.json": write_json(out / "forecast.json", fc),
        "peers.json": write_json(out / "peers.json", peers_table),
        "valuation.json": write_json(out / "valuation.json", val),
        "values.json": write_json(out / "values.json", vals),
    }
    if note_md is not None:
        rendered, _ = values.render(note_md, vals, quotes)
        (out / "note_rendered.md").write_text(rendered, encoding="utf-8")
    findings = gates.run_all({"history": hist, "facts": facts, "prices": prices, "assumptions": assumptions,
                              "valuation_inputs": vinputs, "peers_table": peers_table, "narrative": narrative,
                              "docs": _docs(snap), "note_md": note_md, "values": vals})
    return {"hashes": hashes, "findings": findings, "valuation": val}
