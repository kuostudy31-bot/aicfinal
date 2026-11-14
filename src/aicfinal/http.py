"""HTTP access restricted to the permitted sources in config/project.yaml.

* Hosts outside the allowlist raise ``SourceNotPermitted`` (enforced in code,
  not in a prompt).
* SEC requests carry the User-Agent from the ``SEC_USER_AGENT`` environment
  variable (set by the analyst; never committed) and respect a minimum interval.
* Temporary errors are retried a fixed number of times with backoff; other
  errors propagate so the controller can stop or escalate.
* Responses are cached under data/cache/ (git-ignored) with retrieval metadata.
"""
from __future__ import annotations

import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from . import ROOT
from .util import iso, load_config, read_json, sha256_bytes, utcnow, write_json

GENERIC_UA = "aicfinal-course-project research-bot"
CACHE = ROOT / "data" / "cache" / "http"
RETRY_STATUS = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 4

_last_call: dict[str, float] = {}


class SourceNotPermitted(RuntimeError):
    pass


class FetchError(RuntimeError):
    pass


def _allowed_hosts() -> dict[str, str]:
    cfg = load_config()["sources"]
    hosts = {}
    for name, spec in cfg.items():
        for h in spec["hosts"]:
            hosts[h] = name
    return hosts


def _headers(source: str) -> dict[str, str]:
    if source == "sec":
        env = load_config()["sources"]["sec"]["user_agent_env"]
        ua = os.environ.get(env, "").strip() or GENERIC_UA
        return {"User-Agent": ua, "Accept-Encoding": "identity"}
    return {"User-Agent": "Mozilla/5.0 (compatible; aicfinal-course-project)"}


def _cache_paths(url: str) -> tuple[Path, Path]:
    key = sha256_bytes(url.encode())[:24]
    return CACHE / f"{key}.bin", CACHE / f"{key}.meta.json"


def fetch(url: str, *, use_cache: bool = True, max_age_seconds: float | None = None) -> tuple[bytes, dict]:
    """Return (body, meta). meta has url, retrieved_at, sha256, source."""
    host = urllib.parse.urlparse(url).hostname or ""
    hosts = _allowed_hosts()
    if host not in hosts:
        raise SourceNotPermitted(f"{host} is not a permitted source")
    source = hosts[host]
    body_path, meta_path = _cache_paths(url)
    if use_cache and body_path.exists() and meta_path.exists():
        meta = read_json(meta_path)
        age = time.time() - meta.get("retrieved_epoch", 0)
        if max_age_seconds is None or age <= max_age_seconds:
            return body_path.read_bytes(), meta

    min_gap = load_config()["sources"].get(source, {}).get("min_interval_seconds", 0.0)
    last_error: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        wait = min_gap - (time.time() - _last_call.get(source, 0.0))
        if wait > 0:
            time.sleep(wait)
        _last_call[source] = time.time()
        req = urllib.request.Request(url, headers=_headers(source))
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read()
            break
        except urllib.error.HTTPError as exc:  # pragma: no cover - network
            last_error = exc
            if exc.code not in RETRY_STATUS:
                raise FetchError(f"HTTP {exc.code} for {url}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:  # pragma: no cover
            last_error = exc
        time.sleep(2 ** attempt)
    else:  # pragma: no cover - network
        raise FetchError(f"giving up on {url} after {MAX_ATTEMPTS} attempts: {last_error}")

    now = utcnow()
    meta = {
        "url": url,
        "source": source,
        "retrieved_at": iso(now),
        "retrieved_epoch": now.timestamp(),
        "sha256": sha256_bytes(body),
        "bytes": len(body),
    }
    CACHE.mkdir(parents=True, exist_ok=True)
    body_path.write_bytes(body)
    write_json(meta_path, meta)
    return body, meta
