"""ε.3 — sales import + rollup API handlers (2026-05-11).

Two endpoints for the publisher's /exec sales workflow:
- `api_sales_rollup()` — GET; renders the totals_mtd + totals_by_channel
  + totals_by_edition payload.
- `api_sales_import(channel, body, content_type)` — POST multipart;
  parses a per-channel CSV (KDP / Apple / Google), matches each row
  to a shipped edition by title, emits one `sales_record` event per
  row, returns a summary.

Storage piggybacks on Δ.15's event log so:
- No new persistence path = no new backup story.
- Every operational signal (builds, AI spend, perf, sales) lives in
  one greppable JSONL.
- ε.5 quarterly-auto-report can compose this exact stream when ready.

`SALES_UPLOAD_MAX_BYTES = 20 MB` matches a year of monthly KDP / Apple
/ Google reports per edition with comfortable headroom (a single
KDP monthly report rarely tops 50 KB).
"""

from __future__ import annotations

from scripts.core import audit_log


SALES_UPLOAD_MAX_BYTES = 20 * 1024 * 1024  # 20 MB


def api_sales_rollup() -> dict:
    """Read-only rollup payload for the /exec sales section.

    Composes `sales.totals_mtd()` + `sales.totals_by_channel()` +
    `sales.totals_by_edition()`. Always a single-pass scan over the
    event log per top-level aggregator (so 3 passes total — acceptable
    for ~200KB/month of events; can be collapsed to 1 pass via a
    helper if it ever matters).
    """
    from scripts.core import sales

    return {
        "status": "ok",
        "mtd": sales.totals_mtd(),
        "by_channel": sales.totals_by_channel(),
        "by_edition": sales.totals_by_edition(),
        "known_channels": list(sales.KNOWN_CHANNELS),
    }


@audit_log.audit_endpoint(action="sales_import")
def api_sales_import(channel: str, body: bytes, content_type: str) -> dict:
    """Import one CSV upload from the publisher.

    Validates: known channel → multipart parse → UTF-8 decode → CSV
    parse (per-channel) → emit N sales_record events. On any error
    before parsing, returns the standard `{status: error, code, http,
    message}` envelope and emits nothing.
    """
    # Lazy imports mirror api/sources.py — keeps initial module load
    # cheap and avoids circulars in the api/* package.
    from scripts.api.multipart import _extract_boundary, _parse_multipart
    from scripts.core import config, sales

    channel = (channel or "").strip().lower()
    if channel not in sales.KNOWN_CHANNELS:
        return {
            "status": "error",
            "code": "unknown_channel",
            "http": 400,
            "message": (f"unknown sales channel: {channel!r} (known: {', '.join(sales.KNOWN_CHANNELS)})"),
        }

    if len(body) > SALES_UPLOAD_MAX_BYTES:
        return {
            "status": "error",
            "code": "too_large",
            "http": 413,
            "message": f"upload exceeds {SALES_UPLOAD_MAX_BYTES} bytes",
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
        return {
            "status": "error",
            "code": "no_file_part",
            "http": 400,
            "message": "no file part in upload",
        }

    payload = file_part["data"]
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        # Try utf-8-sig (BOM-aware) as a fallback — Excel-exported
        # CSVs often have a BOM. Then cp1252 as a last resort because
        # Windows Excel still defaults to it for non-Unicode exports.
        for fallback in ("utf-8-sig", "cp1252"):
            try:
                text = payload.decode(fallback)
                break
            except UnicodeDecodeError:
                continue
        else:
            return {
                "status": "error",
                "code": "not_utf8",
                "http": 400,
                "message": "uploaded CSV is not valid UTF-8/UTF-8-BOM/cp1252",
            }

    try:
        records = sales.parse_csv(text, channel)
    except ValueError as e:
        # Shouldn't happen — we validated channel above — but defensive
        # against future divergence between the validation list and the
        # parser registry.
        return {
            "status": "error",
            "code": "parse_error",
            "http": 400,
            "message": str(e),
        }

    editions = config.load_editions()
    count = sales.import_records(records, editions=editions)

    # Per-row summary so the UI can show "imported N rows; M matched
    # editions" without a follow-up rollup call.
    matched = sum(1 for r in records if sales.match_edition(r.get("raw_title", ""), editions) is not None)
    return {
        "status": "ok",
        "ok": True,
        "channel": channel,
        "imported": count,
        "matched_editions": matched,
        "filename": file_part.get("filename", ""),
        "message": f"imported {count} {channel} sales row(s) ({matched} matched an edition)",
    }
