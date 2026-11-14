"""SEC EDGAR access: tickers, filings (with acceptance times), XBRL facts, documents."""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser

from .http import fetch
from .util import parse_iso

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
SUBMISSIONS_PAGE_URL = "https://data.sec.gov/submissions/{name}"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc_nodash}/{name}"
INDEX_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc_nodash}/index.json"

PERIODIC = {"10-Q", "10-K", "10-Q/A", "10-K/A"}


def cik_for(ticker: str) -> int:
    body, _ = fetch(TICKERS_URL, max_age_seconds=7 * 86400)
    for row in json.loads(body).values():
        if row["ticker"].upper() == ticker.upper():
            return int(row["cik_str"])
    raise KeyError(f"unknown ticker {ticker}")


def _rows(block: dict) -> list[dict]:
    keys = list(block.keys())
    n = len(block["accessionNumber"])
    return [{k: block[k][i] for k in keys} for i in range(n)]


def filings(cik: int, *, include_older: bool = False, max_age_seconds: float | None = 3600) -> list[dict]:
    """All filings with acceptance timestamps, newest first."""
    body, meta = fetch(SUBMISSIONS_URL.format(cik=cik), max_age_seconds=max_age_seconds)
    sub = json.loads(body)
    rows = _rows(sub["filings"]["recent"])
    if include_older:
        for page in sub["filings"].get("files", []):
            pbody, _ = fetch(SUBMISSIONS_PAGE_URL.format(name=page["name"]), max_age_seconds=None)
            rows.extend(_rows(json.loads(pbody)))
    for r in rows:
        r["cik"] = cik
        r["acceptance_utc"] = parse_iso(r["acceptanceDateTime"]).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows.sort(key=lambda r: r["acceptance_utc"], reverse=True)
    return rows


def company_meta(cik: int) -> dict:
    body, _ = fetch(SUBMISSIONS_URL.format(cik=cik), max_age_seconds=3600)
    sub = json.loads(body)
    return {"cik": cik, "name": sub["name"], "fiscalYearEnd": sub.get("fiscalYearEnd"),
            "sic": sub.get("sic"), "sicDescription": sub.get("sicDescription")}


def company_facts(cik: int, max_age_seconds: float | None = 3600) -> tuple[dict, dict]:
    body, meta = fetch(FACTS_URL.format(cik=cik), max_age_seconds=max_age_seconds)
    return json.loads(body), meta


def filing_index(cik: int, accession: str) -> list[dict]:
    acc = accession.replace("-", "")
    body, _ = fetch(INDEX_URL.format(cik=cik, acc_nodash=acc), max_age_seconds=None)
    return json.loads(body)["directory"]["item"]


def exhibits(cik: int, accession: str, prefix: str = "EX-99") -> list[tuple[str, str]]:
    """[(exhibit_type, file_name)] parsed from the filing's index page."""
    acc = accession.replace("-", "")
    url = ARCHIVE_URL.format(cik=cik, acc_nodash=acc, name=f"{accession}-index.html")
    body, _ = fetch(url, max_age_seconds=None)
    out = []
    for tr in re.findall(r"<tr.*?</tr>", body.decode("utf-8", errors="replace"), re.S):
        cells = re.findall(r"<td[^>]*>([^<]*)</td>", tr)
        href = re.search(r'href="([^"]+)"', tr)
        typ = next((c.strip() for c in cells if c.strip().startswith(prefix)), None)
        if typ and href and href.group(1).lower().endswith((".htm", ".html")):
            out.append((typ, href.group(1).rsplit("/", 1)[-1]))
    return out


def document(cik: int, accession: str, name: str) -> tuple[bytes, dict]:
    acc = accession.replace("-", "")
    return fetch(ARCHIVE_URL.format(cik=cik, acc_nodash=acc, name=name), max_age_seconds=None)


class _TextExtractor(HTMLParser):
    SKIP = {"script", "style", "ix:header", "head"}
    BLOCK = {"p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6", "table"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        if tag in self.BLOCK:
            self.parts.append("\n")
        if tag in ("td", "th"):
            self.parts.append(" | ")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        if tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def html_to_text(raw: bytes) -> str:
    parser = _TextExtractor()
    parser.feed(raw.decode("utf-8", errors="replace"))
    text = "".join(parser.parts).replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    lines = [ln.strip(" |") .strip() for ln in text.splitlines()]
    out, blank = [], 0
    for ln in lines:
        if not ln:
            blank += 1
            if blank <= 1:
                out.append("")
        else:
            blank = 0
            out.append(ln)
    return "\n".join(out).strip() + "\n"
