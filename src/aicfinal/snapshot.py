"""Frozen, dated input snapshot for one case.

A case is opened by a periodic filing (10-Q/10-K). Its cutoff is that filing's
SEC acceptance time. The snapshot stores only what was observable then:

  snapshot/filings.json   periodic filings + 8-K item 2.02 accepted <= cutoff
  snapshot/facts.json     XBRL facts from those filings (catalog concepts + all
                          us-gaap concept names for mapping)
  snapshot/prices.json    daily closes whose session ended <= cutoff
  snapshot/peers.json     peer facts and prices under the same cutoff
  snapshot/docs/*.txt     text of the 10-Q/10-K and the earnings release (EX-99.1)
  snapshot/manifest.json  every file's sha256, source URL and retrieval time

Building a snapshot is idempotent: an existing manifest whose hashes verify is
returned unchanged, so a resumed run never re-downloads or silently changes
its inputs.
"""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import yaml

from . import ROOT, edgar, prices
from .util import iso, parse_iso, read_json, sha256_file, utcnow, write_json
from .xbrl import facts_table

FACT_HISTORY_YEARS = 4


def catalog() -> dict:
    with open(ROOT / "references" / "xbrl_catalog.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)["line_items"]


def catalog_concepts() -> set[str]:
    return {c for spec in catalog().values() for c in spec["candidates"]}


def verify_manifest(snap_dir: Path) -> tuple[bool, list[str]]:
    man_path = snap_dir / "manifest.json"
    if not man_path.exists():
        return False, ["manifest.json missing"]
    man = read_json(man_path)
    problems = []
    for rel, info in man["files"].items():
        p = snap_dir / rel
        if not p.exists():
            problems.append(f"missing {rel}")
        elif sha256_file(p) != info["sha256"]:
            problems.append(f"hash mismatch {rel}")
    return not problems, problems


def _periodic_and_releases(rows: list[dict], cutoff: str) -> list[dict]:
    keep = []
    for r in rows:
        if r["acceptance_utc"] > cutoff:
            continue
        if r["form"] in edgar.PERIODIC or (r["form"] == "8-K" and "2.02" in (r.get("items") or "")):
            keep.append({k: r[k] for k in ("accessionNumber", "form", "filingDate", "reportDate",
                                           "acceptance_utc", "primaryDocument", "items")})
    return keep


def _doc_text(cik: int, accession: str, name: str) -> str:
    raw, _ = edgar.document(cik, accession, name)
    return edgar.html_to_text(raw)


def build(case_dir: Path, ticker: str, accession: str, peers: list[str]) -> dict:
    snap = Path(case_dir) / "snapshot"
    ok, _ = verify_manifest(snap)
    if ok:
        return read_json(snap / "manifest.json")

    cik = edgar.cik_for(ticker)
    all_filings = edgar.filings(cik)
    trig = next((f for f in all_filings if f["accessionNumber"] == accession), None)
    if trig is None:
        raise KeyError(f"{accession} not found for {ticker}")
    if trig["form"] not in edgar.PERIODIC:
        raise ValueError(f"{accession} is a {trig['form']}, not a periodic filing")
    cutoff = trig["acceptance_utc"]
    min_end = (parse_iso(cutoff) - timedelta(days=365 * FACT_HISTORY_YEARS)).date().isoformat()

    files: dict[str, dict] = {}

    def save(rel: str, obj, sources: list[str]):
        path = snap / rel
        write_json(path, obj)
        files[rel] = {"sha256": sha256_file(path), "sources": sources, "retrieved_at": iso(utcnow())}

    flist = _periodic_and_releases(all_filings, cutoff)
    save("filings.json", {"ticker": ticker, "cik": cik, "cutoff_utc": cutoff, "filings": flist},
         [edgar.SUBMISSIONS_URL.format(cik=cik)])

    acc_map = {f["accessionNumber"]: f["acceptance_utc"] for f in all_filings
               if f["form"] in edgar.PERIODIC}
    cf, cf_meta = edgar.company_facts(cik)
    concepts_cat = catalog_concepts()
    # The covered company's snapshot keeps every concept it reports (companies rename and split
    # XBRL lines; a catalog-only snapshot hid NVDA's DebtSecuritiesCurrent / EquitySecuritiesFvNi
    # in the first live run). Peers keep catalog concepts only.
    rows = facts_table(cf, acc_map, cutoff, min_end=min_end, concepts=None)
    available = sorted({c for c, body in cf["facts"].get("us-gaap", {}).items()
                        if any(it["accn"] in acc_map and acc_map[it["accn"]] <= cutoff
                               for u in body["units"].values() for it in u)})
    save("facts.json", {"ticker": ticker, "cik": cik, "cutoff_utc": cutoff,
                        "fiscal_year_end": edgar.company_meta(cik)["fiscalYearEnd"],
                        "entity": cf.get("entityName"), "facts": rows,
                        "available_us_gaap_concepts": available},
         [cf_meta["url"]])

    px_rows, px_meta = prices.daily_closes(ticker)
    save("prices.json", {"ticker": ticker, "cutoff_utc": cutoff, "currency": px_meta.get("currency"),
                         "note": px_meta["note"], "closes": prices.observable(px_rows, cutoff)},
         [px_meta["url"]])

    peer_block = {}
    for p in peers:
        if p.upper() == ticker.upper():
            continue
        pcik = edgar.cik_for(p)
        pf = edgar.filings(pcik)
        pacc = {f["accessionNumber"]: f["acceptance_utc"] for f in pf if f["form"] in edgar.PERIODIC}
        pcf, _ = edgar.company_facts(pcik)
        prow = facts_table(pcf, pacc, cutoff, min_end=min_end, concepts=concepts_cat)
        ppx, _ = prices.daily_closes(p)
        obs = prices.observable(ppx, cutoff)
        peer_block[p] = {"cik": pcik, "fiscal_year_end": edgar.company_meta(pcik)["fiscalYearEnd"],
                         "facts": prow, "last_close": obs[-1] if obs else None}
    save("peers.json", {"cutoff_utc": cutoff, "peers": peer_block},
         ["submissions/companyfacts/chart for each peer (see http cache metadata)"])

    docs = {}
    docs["periodic.txt"] = (_doc_text(cik, accession, trig["primaryDocument"]),
                            trig["primaryDocument"], accession)
    release = next((f for f in flist if f["form"] == "8-K"), None)
    if release:  # latest earnings release accepted <= cutoff: EX-99.x exhibits
        for typ, name in edgar.exhibits(cik, release["accessionNumber"]):
            rel = "release_" + typ.lower().replace("-", "").replace(".", "_") + ".txt"
            docs[rel] = (_doc_text(cik, release["accessionNumber"], name), name, release["accessionNumber"])
    for rel, (text, name, acc) in docs.items():
        path = snap / "docs" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        files[f"docs/{rel}"] = {"sha256": sha256_file(path), "retrieved_at": iso(utcnow()),
                                "sources": [edgar.ARCHIVE_URL.format(cik=cik, acc_nodash=acc.replace('-', ''),
                                                                     name=name)],
                                "accession": acc, "document": name}

    manifest = {"ticker": ticker, "cik": cik, "trigger_accession": accession,
                "trigger_form": trig["form"], "period_of_report": trig["reportDate"],
                "cutoff_utc": cutoff, "created_at": iso(utcnow()), "peers": peers, "files": files}
    write_json(snap / "manifest.json", manifest)
    return manifest
