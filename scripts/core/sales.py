"""LOAD-BEARING-NO-LONGER as of Ω.0 free-public pivot (2026-05-14).
This module ingests retailer sales CSVs (KDP, Apple Books, Google
Play) and rolls them up for the /exec dashboard. The project no
longer sells books, so there is nothing to import. Retained per
§7.4 for git-history preservation. /exec dashboard sales panel
should hide rather than call into this module.

ε.3 — sales import + revenue rollups (2026-05-11).

Month 5 #4. Composes Δ.15's append-only event log to record per-channel
sales transactions and ε.1's iter_events_since() to roll them up for
the /exec dashboard.

**Why store as events**: same shape as every other operational signal
(builds, AI spend, perf violations). One stream, one storage path, one
backup story. Per-channel CSV imports just become `emit("sales_record",
...)` calls — the existing tail/iter/count primitives compose for free.

**Channels supported in MVP**: KDP (Amazon), Apple Books, Google Play
Books. Each has a different CSV schema; this module exposes one parser
per channel + a thin `parse_csv(text, channel)` dispatcher. Real-world
CSVs from these vendors evolve — the parsers are defensive about column
order (look up by header name) and tolerate extra columns.

**Edition matching**: each shipped edition has a human title. The CSV
row has a free-text title field. `match_edition(raw_title, editions)`
does case-insensitive substring matching against the edition titles
(longest match wins so "Catholic Study Bible" beats "Catholic"). No
match → edition_id is None and the record is still stored with the
raw title for manual reconciliation.

**Public API**:
    KNOWN_CHANNELS                          tuple of channel ids
    SALES_EVENT_KIND                        canonical event kind str
    parse_kdp_csv(text)                     list[dict]
    parse_apple_csv(text)                   list[dict]
    parse_google_csv(text)                  list[dict]
    parse_csv(text, channel)                dispatcher
    match_edition(raw_title, editions)      edition_id | None
    import_records(records, *, editions)    int — emitted count
    iter_sales_records()                    generator of dicts
    totals_by_edition()                     {edition_id: {units, gross, currency}}
    totals_by_channel()                     {channel: {units, gross, records}}
    totals_mtd(now=None)                    canonical /exec tile payload

Foundation for ε.4 (per-edition cost-vs-revenue rollup), ε.5
(quarterly auto-report), ε.6 (channel checklist consumes per-edition
channel coverage from totals_by_channel), ο.7 (affiliate-code tracking
extends the sales_record schema with a `referral` field).
"""

from __future__ import annotations

import csv
import io
from collections import defaultdict
from datetime import datetime, timezone
from collections.abc import Iterable, Iterator

from . import event_log


KNOWN_CHANNELS: tuple[str, ...] = ("kdp", "apple", "google")
SALES_EVENT_KIND = "sales_record"


def _to_float(value, default: float = 0.0) -> float:
    """Coerce a CSV cell to float. Strips currency symbols, commas, and
    surrounding whitespace. Returns `default` on any failure (the row
    still imports — caller can audit zero-value rows in the rollup)."""
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    for ch in ("$", "€", "£", ",", " "):
        text = text.replace(ch, "")
    try:
        return float(text)
    except ValueError:
        return default


def _to_int(value, default: int = 0) -> int:
    """Coerce a CSV cell to int. Tolerates trailing decimals like
    '5.0' (KDP occasionally exports unit counts as decimals)."""
    if value is None:
        return default
    text = str(value).strip().replace(",", "")
    if not text:
        return default
    try:
        return int(text)
    except ValueError:
        try:
            return int(float(text))
        except ValueError:
            return default


def _normalize_date(raw: str) -> str:
    """Return an ISO-8601 date (YYYY-MM-DD) from common CSV formats.

    Accepts: 'YYYY-MM-DD', 'MM/DD/YYYY', 'M/D/YYYY', 'YYYY/MM/DD'.
    Returns the input untouched if no known format matches — better
    to keep the raw than guess wrong silently.
    """
    raw = (raw or "").strip()
    if not raw:
        return ""
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return raw


def _read_dict_rows(text: str) -> list[dict]:
    """Parse CSV text into list[dict] with header-keyed rows. Tolerates
    BOM, leading whitespace lines, and quoted fields. Empty rows are
    dropped."""
    # Strip a UTF-8 BOM if present — common when Excel exports CSV.
    if text.startswith("﻿"):
        text = text[1:]
    reader = csv.DictReader(io.StringIO(text))
    return [r for r in reader if any((v or "").strip() for v in r.values())]


def _row_lookup(row: dict, *candidates: str) -> str:
    """Find the first present non-empty value for any of the candidate
    header names. Case-insensitive — vendors are inconsistent about
    capitalization between report variants."""
    lowered = {(k or "").strip().lower(): v for k, v in row.items()}
    for c in candidates:
        v = lowered.get(c.strip().lower())
        if v is not None and str(v).strip():
            return str(v).strip()
    return ""


def parse_kdp_csv(text: str) -> list[dict]:
    """Parse an Amazon KDP royalty report CSV.

    Expected columns (real KDP export, monthly royalty report):
        Royalty Date, Title, Author Name, ASIN/ISBN, Marketplace,
        Royalty Type, Transaction Type, Net Units Sold, Royalty,
        Currency

    Returns one dict per row with normalized fields:
        {channel: "kdp", period_start, period_end, raw_title,
         identifier, units, gross, currency, marketplace,
         transaction_type}
    """
    out: list[dict] = []
    for row in _read_dict_rows(text):
        date = _normalize_date(_row_lookup(row, "Royalty Date", "Date"))
        out.append(
            {
                "channel": "kdp",
                "period_start": date,
                "period_end": date,
                "raw_title": _row_lookup(row, "Title"),
                "identifier": _row_lookup(row, "ASIN/ISBN", "ASIN", "ISBN"),
                "units": _to_int(_row_lookup(row, "Net Units Sold", "Units")),
                "gross": _to_float(_row_lookup(row, "Royalty", "Earnings")),
                "currency": _row_lookup(row, "Currency").upper() or "USD",
                "marketplace": _row_lookup(row, "Marketplace"),
                "transaction_type": _row_lookup(row, "Transaction Type"),
            }
        )
    return out


def parse_apple_csv(text: str) -> list[dict]:
    """Parse an Apple Books partner-share report CSV.

    Expected columns (real Apple export, monthly partner report):
        Begin Date, End Date, Vendor Identifier, Title,
        Product Type Identifier, Quantity, Partner Share,
        Partner Share Currency

    Returns normalized dicts mirroring `parse_kdp_csv`.
    """
    out: list[dict] = []
    for row in _read_dict_rows(text):
        period_start = _normalize_date(_row_lookup(row, "Begin Date", "Start Date"))
        period_end = _normalize_date(_row_lookup(row, "End Date")) or period_start
        out.append(
            {
                "channel": "apple",
                "period_start": period_start,
                "period_end": period_end,
                "raw_title": _row_lookup(row, "Title"),
                "identifier": _row_lookup(row, "Vendor Identifier", "ISBN"),
                "units": _to_int(_row_lookup(row, "Quantity", "Units")),
                "gross": _to_float(_row_lookup(row, "Partner Share", "Earnings")),
                "currency": _row_lookup(row, "Partner Share Currency", "Currency").upper() or "USD",
                "product_type": _row_lookup(row, "Product Type Identifier"),
            }
        )
    return out


def parse_google_csv(text: str) -> list[dict]:
    """Parse a Google Play Books earnings report CSV.

    Expected columns (real Google export, transaction report):
        Transaction Date, Title, Quantity, Earnings, Currency Code

    Returns normalized dicts.
    """
    out: list[dict] = []
    for row in _read_dict_rows(text):
        date = _normalize_date(_row_lookup(row, "Transaction Date", "Date"))
        out.append(
            {
                "channel": "google",
                "period_start": date,
                "period_end": date,
                "raw_title": _row_lookup(row, "Title"),
                "identifier": _row_lookup(row, "ISBN", "Book ID"),
                "units": _to_int(_row_lookup(row, "Quantity", "Units")),
                "gross": _to_float(_row_lookup(row, "Earnings", "Royalty")),
                "currency": _row_lookup(row, "Currency Code", "Currency").upper() or "USD",
            }
        )
    return out


_PARSERS = {
    "kdp": parse_kdp_csv,
    "apple": parse_apple_csv,
    "google": parse_google_csv,
}


def parse_csv(text: str, channel: str) -> list[dict]:
    """Dispatch to the per-channel parser. Raises ValueError for an
    unknown channel — `api_sales_import` translates this to HTTP 400."""
    parser = _PARSERS.get(channel)
    if parser is None:
        raise ValueError(f"unknown sales channel: {channel!r} (known: {', '.join(KNOWN_CHANNELS)})")
    return parser(text)


def match_edition(raw_title: str, editions: Iterable[dict]) -> str | None:
    """Best-effort substring match of a CSV title against shipped
    editions. Case-insensitive; the edition whose title appears as a
    substring of the raw title (or vice-versa) AND is longest wins, so
    'Catholic Study Bible' beats 'Bible' when both could match.

    Returns the edition's `id` or None if nothing matches.
    """
    if not raw_title:
        return None
    needle = raw_title.lower()
    best_id: str | None = None
    best_len = 0
    for ed in editions:
        title = str(ed.get("title", "")).strip()
        ed_id = str(ed.get("id", "")).strip()
        if not title or not ed_id:
            continue
        title_lc = title.lower()
        if title_lc in needle or needle in title_lc:
            score = len(title_lc)
            if score > best_len:
                best_len = score
                best_id = ed_id
    return best_id


def import_records(records: Iterable[dict], *, editions: Iterable[dict] | None = None) -> int:
    """Emit one `sales_record` event per record. Returns the count of
    events written.

    `editions` is the canonical edition list (typically
    `config.load_editions()`); if supplied each record is enriched with
    `edition_id` via `match_edition`. Pass None to skip matching (the
    raw_title is still stored).
    """
    ed_list = list(editions) if editions is not None else []
    count = 0
    for r in records:
        edition_id = match_edition(r.get("raw_title", ""), ed_list) if ed_list else None
        # Filter to JSON-serializable fields; never echo the raw row.
        fields = {
            "channel": str(r.get("channel", "")),
            "period_start": str(r.get("period_start", "")),
            "period_end": str(r.get("period_end", "")),
            "raw_title": str(r.get("raw_title", "")),
            "identifier": str(r.get("identifier", "")),
            "units": int(r.get("units", 0)),
            "gross": float(r.get("gross", 0.0)),
            "currency": str(r.get("currency", "USD")).upper(),
            "edition_id": edition_id,
        }
        # Optional per-channel fields (marketplace / transaction_type
        # / product_type) — pass through when present so future
        # filters can use them without re-import.
        for opt in ("marketplace", "transaction_type", "product_type"):
            if r.get(opt):
                fields[opt] = str(r[opt])
        event_log.emit(SALES_EVENT_KIND, **fields)
        count += 1
    return count


def iter_sales_records() -> Iterator[dict]:
    """Yield every recorded sales event, in write order."""
    for ev in event_log.iter_events():
        if ev.get("kind") == SALES_EVENT_KIND:
            yield ev


def totals_by_edition() -> dict[str, dict]:
    """Aggregate {edition_id_or_unmatched: {units, gross_by_currency,
    records, channels}}. The `_unmatched` bucket groups records where
    edition matching returned None so the publisher can audit them."""
    out: dict[str, dict] = defaultdict(
        lambda: {
            "units": 0,
            "gross_by_currency": defaultdict(float),
            "records": 0,
            "channels": set(),
        }
    )
    for ev in iter_sales_records():
        key = ev.get("edition_id") or "_unmatched"
        bucket = out[key]
        bucket["units"] += int(ev.get("units", 0))
        currency = str(ev.get("currency", "USD")).upper() or "USD"
        bucket["gross_by_currency"][currency] += float(ev.get("gross", 0.0))
        bucket["records"] += 1
        channel = str(ev.get("channel", ""))
        if channel:
            bucket["channels"].add(channel)
    # Convert defaultdicts + sets to JSON-safe shapes before return.
    return {
        k: {
            "units": v["units"],
            "gross_by_currency": {cur: round(amt, 2) for cur, amt in v["gross_by_currency"].items()},
            "records": v["records"],
            "channels": sorted(v["channels"]),
        }
        for k, v in out.items()
    }


def totals_by_channel() -> dict[str, dict]:
    """Aggregate {channel: {units, gross_by_currency, records}}."""
    out: dict[str, dict] = defaultdict(
        lambda: {
            "units": 0,
            "gross_by_currency": defaultdict(float),
            "records": 0,
        }
    )
    for ev in iter_sales_records():
        channel = str(ev.get("channel", "")) or "_unknown"
        bucket = out[channel]
        bucket["units"] += int(ev.get("units", 0))
        currency = str(ev.get("currency", "USD")).upper() or "USD"
        bucket["gross_by_currency"][currency] += float(ev.get("gross", 0.0))
        bucket["records"] += 1
    return {
        k: {
            "units": v["units"],
            "gross_by_currency": {cur: round(amt, 2) for cur, amt in v["gross_by_currency"].items()},
            "records": v["records"],
        }
        for k, v in out.items()
    }


def _month_start_iso(now: datetime | None = None) -> str:
    """Mirror of api.exec._month_start_iso so this module stays
    self-contained for the ε.3 unit tests. The duplication is two
    lines; an "import from .api.exec" would invert the layering."""
    n = now or datetime.now(timezone.utc)
    return n.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()


def totals_mtd(now: datetime | None = None) -> dict:
    """Month-to-date sales rollup for the /exec dashboard's 6th tile.

    Composes event_log.iter_events() once and filters in-memory to the
    current-month window. Returns a stable shape consumers can render
    even when the log is empty.

    Shape:
        {
          "window_start_iso": str,
          "records": int,
          "units": int,
          "gross_by_currency": {"USD": float, ...},
          "by_channel": {channel: {units, gross_by_currency, records}},
          "top_editions": list[{edition_id, units, gross_by_currency,
                                channels, records}] — top 5 by primary
                          currency (USD first; else first encountered)
        }
    """
    window_start = _month_start_iso(now)
    records = 0
    units = 0
    gross_by_currency: dict[str, float] = defaultdict(float)
    by_channel: dict[str, dict] = defaultdict(
        lambda: {
            "units": 0,
            "gross_by_currency": defaultdict(float),
            "records": 0,
        }
    )
    by_edition: dict[str, dict] = defaultdict(
        lambda: {
            "units": 0,
            "gross_by_currency": defaultdict(float),
            "records": 0,
            "channels": set(),
        }
    )

    for ev in iter_sales_records():
        ts = ev.get("ts", "")
        if not isinstance(ts, str) or ts < window_start:
            continue
        records += 1
        u = int(ev.get("units", 0))
        units += u
        currency = str(ev.get("currency", "USD")).upper() or "USD"
        g = float(ev.get("gross", 0.0))
        gross_by_currency[currency] += g
        ch = str(ev.get("channel", "")) or "_unknown"
        by_channel[ch]["units"] += u
        by_channel[ch]["gross_by_currency"][currency] += g
        by_channel[ch]["records"] += 1
        ed = ev.get("edition_id") or "_unmatched"
        by_edition[ed]["units"] += u
        by_edition[ed]["gross_by_currency"][currency] += g
        by_edition[ed]["records"] += 1
        if ch:
            by_edition[ed]["channels"].add(ch)

    def _primary_value(currency_dict: dict[str, float]) -> float:
        if "USD" in currency_dict:
            return currency_dict["USD"]
        if not currency_dict:
            return 0.0
        # First-encountered currency wins when USD is absent — stable
        # within one Python dict (3.7+ preserves insertion order).
        return next(iter(currency_dict.values()))

    top_editions = sorted(
        (
            {
                "edition_id": ed_id,
                "units": v["units"],
                "gross_by_currency": {cur: round(amt, 2) for cur, amt in v["gross_by_currency"].items()},
                "records": v["records"],
                "channels": sorted(v["channels"]),
            }
            for ed_id, v in by_edition.items()
        ),
        key=lambda e: _primary_value({k: float(v) for k, v in e["gross_by_currency"].items()}),
        reverse=True,
    )[:5]

    return {
        "window_start_iso": window_start,
        "records": records,
        "units": units,
        "gross_by_currency": {cur: round(amt, 2) for cur, amt in gross_by_currency.items()},
        "by_channel": {
            ch: {
                "units": v["units"],
                "gross_by_currency": {cur: round(amt, 2) for cur, amt in v["gross_by_currency"].items()},
                "records": v["records"],
            }
            for ch, v in by_channel.items()
        },
        "top_editions": top_editions,
    }
