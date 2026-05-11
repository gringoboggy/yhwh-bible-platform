"""ω.35-B.3b — sources cache API handlers, extracted from scripts/web.py.

Five handlers for the /sources console's PD-cache section
(Phase υ.1 — public-domain source fetching + caching):
- api_sources_cache_status (read-only — status grid)
- api_sources_cache_fetch (mutation; audit-logged)
- api_sources_cache_fetch_all (mutation; audit-logged)
- api_sources_cache_upload (multipart mutation; audit-logged)
- api_sources_cache_clear (mutation; audit-logged)

Plus two internal helpers (`_sources_cache_dir`, `_datetime_iso`)
and one module-level constant (`SOURCES_UPLOAD_MAX_BYTES`). All
three are re-exported from web.py so the route-table multipart
entry (which references `SOURCES_UPLOAD_MAX_BYTES` directly) and
any tests that lookup the helpers via `scripts.web.X` keep working.

Out of scope for B.3b (still in web.py):
- The 3 sources NAVIGATOR functions: api_sources_index,
  api_sources_for_book, api_sources_summary. They're a different
  sub-topic (read-only browsing vs. cache management) and live
  interleaved with unrelated functions. Defer to a B.3c slice if
  the file-split goal warrants further extraction.

Lazy import pattern: the upload handler lazy-imports
`_extract_boundary` and `_parse_multipart` from `scripts.web`
inside its function body. Same rationale as B.3a covers — web.py
top-imports this module, so this module can't top-import web.py
back. Inside a function body, the import doesn't fire until call
time when web.py is fully loaded.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.core import audit_log, notes_io

REPO = Path(__file__).resolve().parent.parent.parent

# Maximum bytes accepted on a single source-cache JSON upload. The
# largest existing cache is TSK at ~5 MB; doubling that gives plenty
# of headroom for richer sources (commentary corpora, lexicons) that
# χ.* phases will add.
SOURCES_UPLOAD_MAX_BYTES = 50 * 1024 * 1024  # 50 MB


def _sources_cache_dir() -> Path:
    """Where the cache files live. Mirrors the constant in
    scripts/fetch_sources.py:SOURCES_DIR; kept as a function so tests
    can monkeypatch via a single attribute."""
    return REPO / "content" / "sources"


def _datetime_iso(ts: float) -> str:
    """Format a unix timestamp as a short ISO string for the UI grid."""
    import datetime

    return datetime.datetime.fromtimestamp(ts).isoformat(timespec="seconds")


def api_sources_cache_status() -> dict:
    """Status grid for the /sources console's PD-cache section.

    Returns one entry per source declared in _fetchers.json with its
    cache filename, current cached/not-cached status, file size and
    last-modified time (when present), and the candidate URL list so
    the UI can show 'tried these mirrors in order'.

    Composes load_fetcher_config (no new file scanning beyond stat
    calls per cache file) per the §9 'compose, don't recompute' rule.
    """
    from scripts.core.fetcher_config import (
        FetcherConfigError,
        load_fetcher_config,
    )

    try:
        cfg = load_fetcher_config()
    except FetcherConfigError as e:
        return {"status": "error", "code": "config_error", "http": 500, "message": str(e), "sources": []}

    cache_dir = _sources_cache_dir()
    out = []
    for s in cfg.sources:
        cache_path = cache_dir / s.cache_path
        if cache_path.is_file():
            stat = cache_path.stat()
            entry = {
                "id": s.id,
                "name": s.name,
                "cache_path": s.cache_path,
                "required": s.required,
                "license": s.license,
                "cached": True,
                "size_bytes": stat.st_size,
                "size_kb": round(stat.st_size / 1024, 1),
                "mtime_iso": _datetime_iso(stat.st_mtime),
            }
        else:
            entry = {
                "id": s.id,
                "name": s.name,
                "cache_path": s.cache_path,
                "required": s.required,
                "license": s.license,
                "cached": False,
                "size_bytes": 0,
                "size_kb": 0.0,
                "mtime_iso": None,
            }
        entry["candidates"] = [{"url": c.url, "parser": c.parser} for c in s.candidates]
        out.append(entry)
    return {
        "status": "ok",
        "sources": out,
    }


@audit_log.audit_endpoint(action="sources_cache_fetch")
def api_sources_cache_fetch(
    source_id: str,
    *,
    force: bool = False,
    url_override: str | None = None,
    parser_override: str | None = None,
    fetch_fn=None,
) -> dict:
    """Fetch one configured source. Returns the post-fetch status entry
    for that source plus an `ok` flag and a `message`.

    Injectable `fetch_fn` (signature ``(source, force) -> bool``) lets
    tests stub network calls. Defaults to the production
    ``scripts.fetch_sources.fetch_source``.

    `url_override` / `parser_override` let the caller try a single
    custom mirror without editing _fetchers.json — the user pastes a
    URL into /sources, picks a parser kind, and clicks Fetch. The
    other declared candidates are skipped for this single call.
    """
    from scripts.core.fetcher_config import (
        Candidate,
        FetcherConfigError,
        KNOWN_PARSERS,
        Source,
        load_fetcher_config,
    )

    try:
        cfg = load_fetcher_config()
    except FetcherConfigError as e:
        return {"status": "error", "code": "config_error", "http": 500, "message": str(e)}

    src = cfg.find(source_id)
    if src is None:
        return {
            "status": "error",
            "code": "unknown_source",
            "http": 404,
            "message": f"unknown source id: {source_id!r}",
        }

    if url_override is not None:
        if not isinstance(url_override, str) or not url_override.startswith(("http://", "https://")):
            return {
                "status": "error",
                "code": "invalid_url",
                "http": 400,
                "message": "url_override must be an http(s) URL",
            }
        parser_kind = parser_override or src.candidates[0].parser
        if parser_kind not in KNOWN_PARSERS:
            return {
                "status": "error",
                "code": "unknown_parser",
                "http": 400,
                "message": f"unknown parser: {parser_kind!r}",
            }
        # Build a one-off Source with only the override candidate.
        src = Source(
            id=src.id,
            name=src.name,
            cache_path=src.cache_path,
            required=src.required,
            license=src.license,
            candidates=(Candidate(url=url_override, parser=parser_kind),),
        )

    if fetch_fn is None:
        from scripts.fetch_sources import fetch_source as fetch_fn  # type: ignore

    ok = bool(fetch_fn(src, force))
    cache_path = _sources_cache_dir() / src.cache_path
    cached = cache_path.is_file()
    return {
        "status": "ok" if ok else "error",
        "ok": ok,
        "id": src.id,
        "cached": cached,
        "size_kb": round(cache_path.stat().st_size / 1024, 1) if cached else 0.0,
        "message": (f"fetched {src.cache_path}" if ok else f"all candidates failed for {src.cache_path}"),
    }


@audit_log.audit_endpoint(action="sources_cache_fetch_all")
def api_sources_cache_fetch_all(*, force: bool = False, fetch_fn=None) -> dict:
    """Fetch every configured source in order. Required-source failure
    is reported but doesn't short-circuit (so the user sees the full
    state after the run, not just the first failure)."""
    from scripts.core.fetcher_config import (
        FetcherConfigError,
        load_fetcher_config,
    )

    try:
        cfg = load_fetcher_config()
    except FetcherConfigError as e:
        return {"status": "error", "code": "config_error", "http": 500, "message": str(e), "results": []}

    results = []
    overall_ok = True
    for s in cfg.sources:
        r = api_sources_cache_fetch(s.id, force=force, fetch_fn=fetch_fn)
        results.append(r)
        if s.required and not r.get("ok"):
            overall_ok = False
    return {
        "status": "ok",
        "ok": overall_ok,
        "results": results,
    }


@audit_log.audit_endpoint(action="sources_cache_upload")
def api_sources_cache_upload(source_id: str, body: bytes, content_type: str) -> dict:
    """Drag-drop upload of a pre-built JSON cache file.

    Validates: multipart parse → JSON parse → top-level shape
    (must be a JSON object, not a list — every cache file we ship
    is dict-shaped). Atomic write with backup of any existing file.
    Disk is never mutated on validation failure (§9 binary-asset
    pattern)."""
    # Lazy import: the multipart helpers still live in scripts.web
    # (shared with cover uploads). See module docstring for the
    # rationale.
    from scripts.web import _extract_boundary, _parse_multipart
    from scripts.core.fetcher_config import (
        FetcherConfigError,
        load_fetcher_config,
    )

    try:
        cfg = load_fetcher_config()
    except FetcherConfigError as e:
        return {"status": "error", "code": "config_error", "http": 500, "message": str(e)}

    src = cfg.find(source_id)
    if src is None:
        return {
            "status": "error",
            "code": "unknown_source",
            "http": 404,
            "message": f"unknown source id: {source_id!r}",
        }

    if len(body) > SOURCES_UPLOAD_MAX_BYTES:
        return {
            "status": "error",
            "code": "too_large",
            "http": 413,
            "message": f"upload exceeds {SOURCES_UPLOAD_MAX_BYTES} bytes",
        }

    boundary = _extract_boundary(content_type)
    if boundary is None:
        return {
            "status": "error",
            "code": "missing_boundary",
            "http": 400,
            "message": "Content-Type header must include boundary=...",
        }

    parts = _parse_multipart(body, boundary)
    file_part = next((p for p in parts if p.get("filename")), None)
    if file_part is None:
        return {"status": "error", "code": "no_file_part", "http": 400, "message": "no file part in upload"}

    payload = file_part["data"]
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return {"status": "error", "code": "not_utf8", "http": 400, "message": "uploaded file is not valid UTF-8"}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        return {"status": "error", "code": "invalid_json", "http": 400, "message": f"not valid JSON: {e}"}
    if not isinstance(parsed, dict):
        return {
            "status": "error",
            "code": "wrong_shape",
            "http": 400,
            "message": "top-level JSON must be an object (dict)",
        }

    cache_dir = _sources_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / src.cache_path

    # ensure_backup before overwrite, atomic write of new content.
    if cache_path.is_file():
        notes_io.ensure_backup(cache_path)
    notes_io.atomic_write_bytes(cache_path, text.encode("utf-8"))

    return {
        "status": "ok",
        "ok": True,
        "id": src.id,
        "cached": True,
        "size_kb": round(cache_path.stat().st_size / 1024, 1),
        "message": f"uploaded {src.cache_path} ({len(payload)} bytes)",
    }


@audit_log.audit_endpoint(action="sources_cache_clear")
def api_sources_cache_clear(source_id: str) -> dict:
    """Delete the cache file for one source. Backs it up first via
    ensure_backup; the .backups/ directory keeps a copy so a
    mistaken click is recoverable."""
    from scripts.core.fetcher_config import (
        FetcherConfigError,
        load_fetcher_config,
    )

    try:
        cfg = load_fetcher_config()
    except FetcherConfigError as e:
        return {"status": "error", "code": "config_error", "http": 500, "message": str(e)}

    src = cfg.find(source_id)
    if src is None:
        return {
            "status": "error",
            "code": "unknown_source",
            "http": 404,
            "message": f"unknown source id: {source_id!r}",
        }

    cache_path = _sources_cache_dir() / src.cache_path
    if not cache_path.is_file():
        return {"status": "ok", "ok": True, "id": src.id, "cached": False, "message": "nothing to clear"}

    notes_io.ensure_backup(cache_path)
    cache_path.unlink()
    return {"status": "ok", "ok": True, "id": src.id, "cached": False, "message": f"cleared {src.cache_path}"}
