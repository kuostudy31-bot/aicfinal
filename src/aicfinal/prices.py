"""Daily closing prices, filtered to what was observable at a cutoff time."""
from __future__ import annotations

import json
from datetime import datetime, time as dtime, timezone
from zoneinfo import ZoneInfo

from .http import fetch
from .util import parse_iso

CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range={rng}&interval=1d&events=split"
NY = ZoneInfo("America/New_York")


def close_time_utc(day: str) -> datetime:
    """US equity regular-session close (16:00 New York) for a trading date."""
    d = datetime.strptime(day, "%Y-%m-%d").date()
    return datetime.combine(d, dtime(16, 0), tzinfo=NY).astimezone(timezone.utc)


def daily_closes(ticker: str, rng: str = "5y") -> tuple[list[dict], dict]:
    body, meta = fetch(CHART_URL.format(ticker=ticker, rng=rng), max_age_seconds=6 * 3600)
    res = json.loads(body)["chart"]["result"][0]
    tz = ZoneInfo(res["meta"].get("exchangeTimezoneName", "America/New_York"))
    quotes = res["indicators"]["quote"][0]
    rows = []
    for ts, close in zip(res.get("timestamp", []), quotes.get("close", [])):
        if close is None:
            continue
        day = datetime.fromtimestamp(ts, tz).strftime("%Y-%m-%d")
        rows.append({"date": day, "close": round(float(close), 4)})
    meta = dict(meta, currency=res["meta"].get("currency"), adjusted=False,
                note="Unadjusted daily close from the Yahoo chart endpoint (split-adjusted by provider).")
    return rows, meta


def observable(rows: list[dict], cutoff_utc: str) -> list[dict]:
    """Keep only closes whose session ended at or before the cutoff."""
    cutoff = parse_iso(cutoff_utc)
    return [r for r in rows if close_time_utc(r["date"]) <= cutoff]
