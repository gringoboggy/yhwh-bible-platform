"""ε.3 — sales import + revenue rollup pins (2026-05-11).

Month 5 #4. Opens with Δ.15 event log + ε.1 metrics collector + ε.2
/exec dashboard as foundation; adds per-channel CSV ingest + rollup
queries + a 6th /exec tile + an import workflow in /exec.

Coverage:
- TestEpsilon3KdpParser:          KDP CSV → normalized records;
  column-name lookup is case-insensitive; currency defaults to USD;
  malformed numbers become 0.
- TestEpsilon3AppleParser:        Apple Books CSV → normalized records;
  date range collapses to (begin, end); cp1252 fallback via api layer.
- TestEpsilon3GoogleParser:       Google Play CSV → normalized records.
- TestEpsilon3ParseDispatcher:    parse_csv dispatch + unknown-channel
  ValueError.
- TestEpsilon3EditionMatch:       longest-substring matching beats
  shorter ones; case-insensitive; None when nothing matches; "" raw
  title returns None.
- TestEpsilon3ImportRecords:      import_records emits one event per
  record with the canonical schema; edition_id set when match exists.
- TestEpsilon3Totals:              totals_by_edition + totals_by_channel
  + totals_mtd composition, currency bag preservation, MTD window
  filter, top-5 cap, _unmatched bucket.
- TestEpsilon3ApiSalesRollup:     api_sales_rollup payload shape +
  composes the three sales aggregators.
- TestEpsilon3ApiSalesImport:     api_sales_import end-to-end —
  multipart parse, channel validation, oversized rejection, decode
  fallback, success summary including matched_editions count.
- TestEpsilon3DashboardTile:      api_exec_dashboard now exposes a
  sales_mtd tile composed from sales.totals_mtd; window filter
  flows through.
- TestEpsilon3ExecTemplate:       EXEC_HTML defines tile #6 + import
  form + per-channel/edition tables + textContent-safe rendering.
- TestEpsilon3RouteRegistration:  /api/sales/rollup wired in
  _SIMPLE_GET_ROUTES; /api/sales/import/<channel> wired in
  _MULTIPART_ROUTES.

Tests isolate the event log via monkeypatch in tmp_path so the
production events.jsonl is never touched. config.load_editions() is
left at its real value (test depends on at least one shipped
edition, which the repo always carries).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest


# --------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------


def _isolate_event_log(monkeypatch, tmp_path):
    """Redirect the event_log module to a tmp file. Mirrors the helper
    in test_exec_epsilon2.py — copy rather than import so a future
    test-file rename doesn't break us silently."""
    from scripts.core import event_log

    log_path = tmp_path / "events.jsonl"
    monkeypatch.setattr(event_log, "_event_log_path", lambda: log_path)
    return log_path


def _build_multipart(filename: str, payload: bytes, *, name: str = "file") -> tuple[bytes, str]:
    """Build a minimal RFC 7578 multipart/form-data body + matching
    Content-Type header. Returns `(body_bytes, content_type_str)`."""
    boundary = "----epsilon3test"
    lines = [
        f"--{boundary}".encode(),
        (f'Content-Disposition: form-data; name="{name}"; filename="{filename}"').encode(),
        b"Content-Type: text/csv",
        b"",
        payload,
        f"--{boundary}--".encode(),
        b"",
    ]
    body = b"\r\n".join(lines)
    return body, f"multipart/form-data; boundary={boundary}"


KDP_SAMPLE = (
    "Royalty Date,Title,Author Name,ASIN/ISBN,Marketplace,Royalty Type,"
    "Transaction Type,Net Units Sold,Royalty,Currency\n"
    "2026-05-03,Catholic Study Bible,YHWH Publishing,9781234567890,"
    "Amazon.com,70%,Sale,5,$12.50,USD\n"
    "2026-05-05,Evangelical Reformed Bible,YHWH Publishing,"
    "9789876543210,Amazon.co.uk,70%,Sale,2,8.40,GBP\n"
)

APPLE_SAMPLE = (
    "Begin Date,End Date,Vendor Identifier,Title,Product Type Identifier,"
    "Quantity,Partner Share,Partner Share Currency\n"
    "05/01/2026,05/31/2026,9781234567890,Catholic Study Bible,1E,3,7.50,USD\n"
)

GOOGLE_SAMPLE = "Transaction Date,Title,Quantity,Earnings,Currency Code\n2026-05-08,Catholic Study Bible,2,5.00,USD\n"


# --------------------------------------------------------------------
# Parser-level pins
# --------------------------------------------------------------------


class TestEpsilon3KdpParser:
    def test_returns_one_record_per_row(self):
        from scripts.core.sales import parse_kdp_csv

        rows = parse_kdp_csv(KDP_SAMPLE)
        assert len(rows) == 2

    def test_normalizes_currency_symbol(self):
        # First row has "$12.50" — the dollar sign must be stripped
        # before float coercion.
        from scripts.core.sales import parse_kdp_csv

        rows = parse_kdp_csv(KDP_SAMPLE)
        assert rows[0]["gross"] == 12.50

    def test_channel_field_pinned(self):
        from scripts.core.sales import parse_kdp_csv

        for row in parse_kdp_csv(KDP_SAMPLE):
            assert row["channel"] == "kdp"

    def test_extracts_per_row_currency(self):
        # Second row is GBP — currency must come from the row, not a
        # module-level default.
        from scripts.core.sales import parse_kdp_csv

        rows = parse_kdp_csv(KDP_SAMPLE)
        assert rows[1]["currency"] == "GBP"

    def test_units_coerced_to_int(self):
        from scripts.core.sales import parse_kdp_csv

        rows = parse_kdp_csv(KDP_SAMPLE)
        assert rows[0]["units"] == 5
        assert isinstance(rows[0]["units"], int)

    def test_passes_through_marketplace_and_transaction_type(self):
        from scripts.core.sales import parse_kdp_csv

        rows = parse_kdp_csv(KDP_SAMPLE)
        assert rows[0]["marketplace"] == "Amazon.com"
        assert rows[0]["transaction_type"] == "Sale"

    def test_period_dates_normalized_to_iso(self):
        from scripts.core.sales import parse_kdp_csv

        rows = parse_kdp_csv(KDP_SAMPLE)
        assert rows[0]["period_start"] == "2026-05-03"
        assert rows[0]["period_end"] == "2026-05-03"

    def test_empty_rows_dropped(self):
        from scripts.core.sales import parse_kdp_csv

        rows = parse_kdp_csv(KDP_SAMPLE + ",,,,,,,,,\n")
        assert len(rows) == 2  # trailing empty row skipped

    def test_currency_defaults_to_usd_when_missing(self):
        # Drop the currency column entirely; parser should default.
        from scripts.core.sales import parse_kdp_csv

        no_currency = "Royalty Date,Title,Net Units Sold,Royalty\n2026-05-03,X,1,1.00\n"
        rows = parse_kdp_csv(no_currency)
        assert rows[0]["currency"] == "USD"

    def test_garbage_royalty_becomes_zero_not_crash(self):
        from scripts.core.sales import parse_kdp_csv

        garbage = "Royalty Date,Title,Net Units Sold,Royalty,Currency\n2026-05-03,X,1,not-a-number,USD\n"
        rows = parse_kdp_csv(garbage)
        assert rows[0]["gross"] == 0.0


class TestEpsilon3AppleParser:
    def test_returns_normalized_record(self):
        from scripts.core.sales import parse_apple_csv

        rows = parse_apple_csv(APPLE_SAMPLE)
        assert len(rows) == 1
        r = rows[0]
        assert r["channel"] == "apple"
        assert r["raw_title"] == "Catholic Study Bible"
        assert r["units"] == 3
        assert r["gross"] == 7.50
        assert r["currency"] == "USD"
        assert r["identifier"] == "9781234567890"
        assert r["product_type"] == "1E"

    def test_normalizes_us_date_format(self):
        from scripts.core.sales import parse_apple_csv

        rows = parse_apple_csv(APPLE_SAMPLE)
        # 05/01/2026 → 2026-05-01
        assert rows[0]["period_start"] == "2026-05-01"
        assert rows[0]["period_end"] == "2026-05-31"


class TestEpsilon3GoogleParser:
    def test_returns_normalized_record(self):
        from scripts.core.sales import parse_google_csv

        rows = parse_google_csv(GOOGLE_SAMPLE)
        assert len(rows) == 1
        r = rows[0]
        assert r["channel"] == "google"
        assert r["raw_title"] == "Catholic Study Bible"
        assert r["units"] == 2
        assert r["gross"] == 5.00
        assert r["currency"] == "USD"

    def test_tolerates_bom(self):
        from scripts.core.sales import parse_google_csv

        with_bom = "﻿" + GOOGLE_SAMPLE
        rows = parse_google_csv(with_bom)
        assert len(rows) == 1
        assert rows[0]["raw_title"] == "Catholic Study Bible"


class TestEpsilon3ParseDispatcher:
    def test_dispatches_to_each_known_channel(self):
        from scripts.core.sales import parse_csv

        assert len(parse_csv(KDP_SAMPLE, "kdp")) == 2
        assert len(parse_csv(APPLE_SAMPLE, "apple")) == 1
        assert len(parse_csv(GOOGLE_SAMPLE, "google")) == 1

    def test_unknown_channel_raises(self):
        from scripts.core.sales import parse_csv

        with pytest.raises(ValueError, match="unknown sales channel"):
            parse_csv(KDP_SAMPLE, "kobo")

    def test_known_channels_constant(self):
        from scripts.core import sales

        assert "kdp" in sales.KNOWN_CHANNELS
        assert "apple" in sales.KNOWN_CHANNELS
        assert "google" in sales.KNOWN_CHANNELS


# --------------------------------------------------------------------
# Edition matching
# --------------------------------------------------------------------


class TestEpsilon3EditionMatch:
    def _editions(self):
        return [
            {"id": "catholic-study", "title": "Catholic Study Bible"},
            {"id": "evangelical-reformed", "title": "Evangelical Reformed Bible"},
            {"id": "bible-mini", "title": "Bible"},
        ]

    def test_longest_match_wins(self):
        from scripts.core.sales import match_edition

        result = match_edition("Catholic Study Bible — Annotated", self._editions())
        # 'Catholic Study Bible' (20 chars) beats 'Bible' (5 chars)
        assert result == "catholic-study"

    def test_case_insensitive(self):
        from scripts.core.sales import match_edition

        result = match_edition("CATHOLIC STUDY BIBLE", self._editions())
        assert result == "catholic-study"

    def test_returns_none_when_no_match(self):
        from scripts.core.sales import match_edition

        assert match_edition("Some Random Romance Novel", self._editions()) is None

    def test_empty_title_returns_none(self):
        from scripts.core.sales import match_edition

        assert match_edition("", self._editions()) is None

    def test_needle_in_title(self):
        # CSV has "Reformed" — edition title is the longer
        # "Evangelical Reformed Bible". The needle is inside the title
        # → match.
        from scripts.core.sales import match_edition

        result = match_edition("Reformed", self._editions())
        assert result == "evangelical-reformed"


# --------------------------------------------------------------------
# import_records + rollups
# --------------------------------------------------------------------


class TestEpsilon3ImportRecords:
    def test_emits_one_event_per_record(self, monkeypatch, tmp_path):
        from scripts.core import sales

        _isolate_event_log(monkeypatch, tmp_path)
        records = sales.parse_kdp_csv(KDP_SAMPLE)
        count = sales.import_records(records, editions=[])
        assert count == 2
        all_events = list(sales.iter_sales_records())
        assert len(all_events) == 2

    def test_records_carry_canonical_fields(self, monkeypatch, tmp_path):
        from scripts.core import sales

        _isolate_event_log(monkeypatch, tmp_path)
        sales.import_records(sales.parse_kdp_csv(KDP_SAMPLE), editions=[])
        ev = list(sales.iter_sales_records())[0]
        for field in (
            "channel",
            "period_start",
            "period_end",
            "raw_title",
            "identifier",
            "units",
            "gross",
            "currency",
            "edition_id",
        ):
            assert field in ev, f"event missing canonical field {field!r}"
        assert ev["kind"] == sales.SALES_EVENT_KIND

    def test_edition_id_set_when_match_exists(self, monkeypatch, tmp_path):
        from scripts.core import sales

        _isolate_event_log(monkeypatch, tmp_path)
        editions = [{"id": "catholic-study", "title": "Catholic Study Bible"}]
        sales.import_records(sales.parse_kdp_csv(KDP_SAMPLE), editions=editions)
        events = list(sales.iter_sales_records())
        catholic_event = next(e for e in events if "Catholic" in e["raw_title"])
        assert catholic_event["edition_id"] == "catholic-study"

    def test_edition_id_none_when_no_match(self, monkeypatch, tmp_path):
        from scripts.core import sales

        _isolate_event_log(monkeypatch, tmp_path)
        sales.import_records(
            sales.parse_kdp_csv(KDP_SAMPLE),
            editions=[{"id": "x", "title": "Totally Different Book"}],
        )
        events = list(sales.iter_sales_records())
        assert all(e["edition_id"] is None for e in events)


class TestEpsilon3Totals:
    def _seed(self, monkeypatch, tmp_path):
        from scripts.core import sales

        _isolate_event_log(monkeypatch, tmp_path)
        editions = [
            {"id": "catholic-study", "title": "Catholic Study Bible"},
            {"id": "evangelical-reformed", "title": "Evangelical Reformed Bible"},
        ]
        sales.import_records(sales.parse_kdp_csv(KDP_SAMPLE), editions=editions)
        sales.import_records(sales.parse_apple_csv(APPLE_SAMPLE), editions=editions)
        sales.import_records(sales.parse_google_csv(GOOGLE_SAMPLE), editions=editions)

    def test_totals_by_channel_buckets_correctly(self, monkeypatch, tmp_path):
        from scripts.core import sales

        self._seed(monkeypatch, tmp_path)
        by_channel = sales.totals_by_channel()
        assert set(by_channel.keys()) == {"kdp", "apple", "google"}
        assert by_channel["kdp"]["records"] == 2
        assert by_channel["apple"]["records"] == 1
        assert by_channel["google"]["records"] == 1
        # KDP totals: 5 + 2 = 7 units
        assert by_channel["kdp"]["units"] == 7

    def test_totals_by_channel_preserves_currency_bag(self, monkeypatch, tmp_path):
        from scripts.core import sales

        self._seed(monkeypatch, tmp_path)
        kdp = sales.totals_by_channel()["kdp"]
        # KDP has both USD ($12.50) and GBP ($8.40) — both bucketed.
        assert kdp["gross_by_currency"]["USD"] == 12.50
        assert kdp["gross_by_currency"]["GBP"] == 8.40

    def test_totals_by_edition_buckets_correctly(self, monkeypatch, tmp_path):
        from scripts.core import sales

        self._seed(monkeypatch, tmp_path)
        by_ed = sales.totals_by_edition()
        # Catholic Study has KDP row#1, Apple, Google → 3 records, 10 units (5+3+2)
        catholic = by_ed["catholic-study"]
        assert catholic["records"] == 3
        assert catholic["units"] == 10
        assert set(catholic["channels"]) == {"kdp", "apple", "google"}
        assert catholic["gross_by_currency"]["USD"] == 25.00  # 12.50+7.50+5.00

    def test_totals_mtd_window_filter(self, monkeypatch, tmp_path):
        from scripts.core import event_log, sales

        _isolate_event_log(monkeypatch, tmp_path)
        # One April event (outside window), one May (inside).
        monkeypatch.setattr(event_log, "_now_iso", lambda: "2026-04-15T10:00:00+00:00")
        event_log.emit("sales_record", channel="kdp", units=99, gross=999.0, currency="USD")
        monkeypatch.undo()
        _isolate_event_log(monkeypatch, tmp_path)
        event_log.emit("sales_record", channel="kdp", units=1, gross=1.00, currency="USD")

        now = datetime(2026, 5, 15, 12, 0, 0, tzinfo=timezone.utc)
        mtd = sales.totals_mtd(now=now)
        # Only the May record is counted.
        assert mtd["records"] == 1
        assert mtd["units"] == 1
        assert mtd["gross_by_currency"]["USD"] == 1.00

    def test_totals_mtd_top_editions_capped_at_5(self, monkeypatch, tmp_path):
        from scripts.core import sales

        _isolate_event_log(monkeypatch, tmp_path)
        editions = [{"id": f"ed-{i}", "title": f"Ed {i}"} for i in range(10)]
        for i in range(10):
            sales.import_records(
                [
                    {
                        "channel": "kdp",
                        "period_start": "2026-05-01",
                        "period_end": "2026-05-01",
                        "raw_title": f"Ed {i}",
                        "identifier": "",
                        "units": 1,
                        "gross": float(i),
                        "currency": "USD",
                    }
                ],
                editions=editions,
            )
        mtd = sales.totals_mtd()
        assert len(mtd["top_editions"]) == 5
        # Sorted descending by USD; top entry should be ed-9 (gross 9.00)
        assert mtd["top_editions"][0]["edition_id"] == "ed-9"

    def test_totals_unmatched_bucket(self, monkeypatch, tmp_path):
        from scripts.core import sales

        _isolate_event_log(monkeypatch, tmp_path)
        sales.import_records(sales.parse_kdp_csv(KDP_SAMPLE), editions=[])
        by_ed = sales.totals_by_edition()
        assert "_unmatched" in by_ed
        assert by_ed["_unmatched"]["records"] == 2


# --------------------------------------------------------------------
# API endpoints
# --------------------------------------------------------------------


class TestEpsilon3ApiSalesRollup:
    def test_payload_shape(self, monkeypatch, tmp_path):
        from scripts.api.sales import api_sales_rollup

        _isolate_event_log(monkeypatch, tmp_path)
        result = api_sales_rollup()
        assert result["status"] == "ok"
        for key in ("mtd", "by_channel", "by_edition", "known_channels"):
            assert key in result, f"sales rollup missing {key!r}"
        assert result["known_channels"] == ["kdp", "apple", "google"]

    def test_empty_log_returns_empty_buckets(self, monkeypatch, tmp_path):
        from scripts.api.sales import api_sales_rollup

        _isolate_event_log(monkeypatch, tmp_path)
        result = api_sales_rollup()
        assert result["by_channel"] == {}
        assert result["by_edition"] == {}
        assert result["mtd"]["records"] == 0

    def test_reflects_imports(self, monkeypatch, tmp_path):
        from scripts.api.sales import api_sales_rollup
        from scripts.core import sales

        _isolate_event_log(monkeypatch, tmp_path)
        sales.import_records(sales.parse_kdp_csv(KDP_SAMPLE), editions=[])
        result = api_sales_rollup()
        assert result["by_channel"]["kdp"]["records"] == 2


class TestEpsilon3ApiSalesImport:
    def test_happy_path_imports_csv(self, monkeypatch, tmp_path):
        from scripts.api.sales import api_sales_import
        from scripts.core import sales

        _isolate_event_log(monkeypatch, tmp_path)
        body, ctype = _build_multipart("kdp-may.csv", KDP_SAMPLE.encode("utf-8"))
        result = api_sales_import("kdp", body, ctype)
        assert result["status"] == "ok"
        assert result["ok"] is True
        assert result["imported"] == 2
        # Events landed in the log.
        assert sum(1 for _ in sales.iter_sales_records()) == 2

    def test_unknown_channel_rejected(self, monkeypatch, tmp_path):
        from scripts.api.sales import api_sales_import

        _isolate_event_log(monkeypatch, tmp_path)
        body, ctype = _build_multipart("x.csv", b"a,b\n1,2\n")
        result = api_sales_import("kobo", body, ctype)
        assert result["status"] == "error"
        assert result["code"] == "unknown_channel"
        assert result["http"] == 400

    def test_oversized_rejected(self, monkeypatch, tmp_path):
        from scripts.api.sales import SALES_UPLOAD_MAX_BYTES, api_sales_import

        _isolate_event_log(monkeypatch, tmp_path)
        oversized = b"x" * (SALES_UPLOAD_MAX_BYTES + 1)
        result = api_sales_import("kdp", oversized, "multipart/form-data; boundary=x")
        assert result["status"] == "error"
        assert result["code"] == "too_large"
        assert result["http"] == 413

    def test_missing_boundary_rejected(self, monkeypatch, tmp_path):
        from scripts.api.sales import api_sales_import

        _isolate_event_log(monkeypatch, tmp_path)
        result = api_sales_import("kdp", b"hello", "text/plain")
        assert result["status"] == "error"
        assert result["code"] == "missing_boundary"

    def test_no_file_part_rejected(self, monkeypatch, tmp_path):
        from scripts.api.sales import api_sales_import

        _isolate_event_log(monkeypatch, tmp_path)
        # Build a multipart with no filename — just a form field.
        boundary = "----epsilon3test"
        lines = [
            f"--{boundary}".encode(),
            b'Content-Disposition: form-data; name="not-a-file"',
            b"",
            b"some text",
            f"--{boundary}--".encode(),
            b"",
        ]
        body = b"\r\n".join(lines)
        ctype = f"multipart/form-data; boundary={boundary}"
        result = api_sales_import("kdp", body, ctype)
        assert result["status"] == "error"
        assert result["code"] == "no_file_part"

    def test_cp1252_fallback_decodes(self, monkeypatch, tmp_path):
        # Windows-Excel CSV with cp1252-only smart-quote in the title.
        # Build the body as raw bytes: header (ascii) + a row containing
        # \x93 (cp1252 left double quote) and \x94 (right double quote)
        # — these decode as invalid UTF-8 but valid cp1252.
        from scripts.api.sales import api_sales_import
        from scripts.core import sales

        _isolate_event_log(monkeypatch, tmp_path)
        ascii_header = b"Royalty Date,Title,Net Units Sold,Royalty,Currency\n"
        cp1252_row = b"2026-05-03,Catholic Study \x93Bible\x94,1,1.00,USD\n"
        bytes_with_smart_quote = ascii_header + cp1252_row
        # Sanity: this byte sequence is NOT valid UTF-8 (so utf-8 decode
        # path will fail and the cp1252 fallback must engage).
        with pytest.raises(UnicodeDecodeError):
            bytes_with_smart_quote.decode("utf-8")

        body, ctype = _build_multipart("kdp.csv", bytes_with_smart_quote)
        result = api_sales_import("kdp", body, ctype)
        assert result["status"] == "ok"
        assert result["imported"] == 1
        events = list(sales.iter_sales_records())
        # Smart quotes survived through the cp1252 fallback path.
        assert "“" in events[0]["raw_title"] or "”" in events[0]["raw_title"]

    def test_matched_editions_count_reported(self, monkeypatch, tmp_path):
        # End-to-end: api_sales_import uses config.load_editions(); we
        # don't monkeypatch that — just confirm the field is present
        # and a non-negative int.
        from scripts.api.sales import api_sales_import

        _isolate_event_log(monkeypatch, tmp_path)
        body, ctype = _build_multipart("kdp.csv", KDP_SAMPLE.encode("utf-8"))
        result = api_sales_import("kdp", body, ctype)
        assert "matched_editions" in result
        assert isinstance(result["matched_editions"], int)
        assert result["matched_editions"] >= 0


# --------------------------------------------------------------------
# /exec dashboard tile composition
# --------------------------------------------------------------------


class TestEpsilon3DashboardTile:
    def test_sales_mtd_tile_present(self, monkeypatch, tmp_path):
        from scripts.api.exec import api_exec_dashboard

        _isolate_event_log(monkeypatch, tmp_path)
        result = api_exec_dashboard()
        assert "sales_mtd" in result["tiles"]
        # Stable shape even when log is empty.
        tile = result["tiles"]["sales_mtd"]
        for k in (
            "window_start_iso",
            "records",
            "units",
            "gross_by_currency",
            "by_channel",
            "top_editions",
        ):
            assert k in tile, f"sales_mtd tile missing {k!r}"

    def test_sales_mtd_tile_reflects_imports(self, monkeypatch, tmp_path):
        from scripts.api.exec import api_exec_dashboard
        from scripts.core import sales

        _isolate_event_log(monkeypatch, tmp_path)
        sales.import_records(sales.parse_kdp_csv(KDP_SAMPLE), editions=[])
        tile = api_exec_dashboard()["tiles"]["sales_mtd"]
        assert tile["records"] == 2
        assert tile["units"] == 7

    def test_sales_mtd_tile_respects_now_injection(self, monkeypatch, tmp_path):
        from datetime import datetime, timezone

        from scripts.api.exec import api_exec_dashboard
        from scripts.core import event_log, sales

        _isolate_event_log(monkeypatch, tmp_path)
        # Emit an April record then ask for May rollup.
        monkeypatch.setattr(event_log, "_now_iso", lambda: "2026-04-15T10:00:00+00:00")
        event_log.emit("sales_record", channel="kdp", units=99, gross=999.0, currency="USD")
        monkeypatch.undo()
        _isolate_event_log(monkeypatch, tmp_path)
        sales.import_records(sales.parse_kdp_csv(KDP_SAMPLE), editions=[])

        now = datetime(2026, 5, 15, 12, 0, 0, tzinfo=timezone.utc)
        tile = api_exec_dashboard(now=now)["tiles"]["sales_mtd"]
        # April record excluded; only the 2 KDP-sample records counted.
        assert tile["records"] == 2


# --------------------------------------------------------------------
# Template + route registration
# --------------------------------------------------------------------


class TestEpsilon3ExecTemplate:
    @classmethod
    def setup_class(cls):
        from scripts.templates.exec import EXEC_HTML

        cls.html = EXEC_HTML

    def test_sales_tile_present(self):
        assert 'data-tile="sales_mtd"' in self.html

    def test_sales_import_form_present(self):
        for piece in (
            'id="sales-import-form"',
            'id="sales-channel"',
            'id="sales-file"',
            'value="kdp"',
            'value="apple"',
            'value="google"',
        ):
            assert piece in self.html, f"missing piece: {piece!r}"

    def test_sales_rollup_tables_present(self):
        assert 'id="sales-by-channel-tbody"' in self.html
        assert 'id="sales-by-edition-tbody"' in self.html

    def test_form_posts_to_correct_endpoint(self):
        # The fetch call is built dynamically; pin the URL prefix.
        assert "/api/sales/import/" in self.html
        assert "/api/sales/rollup" in self.html

    def test_renders_currency_bags_xss_safe(self):
        # Table cells use textContent — no innerHTML on sales data.
        # This is a coarse pin: confirm there's no `innerHTML = ` on
        # any sales-tbody. We don't grep over the entire file because
        # the events table legitimately uses tbody.innerHTML = '' to
        # clear; that's only on initial reset, not for user input.
        for marker in (
            "sales-by-channel-tbody",
            "sales-by-edition-tbody",
        ):
            # The tbody element id is referenced, but no
            # `tbody.innerHTML = '...html with row...'` pattern.
            assert ".innerHTML = '<tr>" not in self.html

    def test_load_sales_rollup_function_present(self):
        assert "loadSalesRollup" in self.html


class TestEpsilon3RouteRegistration:
    def test_get_rollup_in_simple_table(self):
        from scripts import web

        routes = {p: h for (p, h) in web._SIMPLE_GET_ROUTES}
        assert "/api/sales/rollup" in routes
        assert routes["/api/sales/rollup"] is web.api_sales_rollup

    def test_multipart_import_route_present(self):
        # /api/sales/import/<channel> in _MULTIPART_ROUTES.
        import re

        from scripts import web

        pattern_strs = [r.pattern for (r, _max, _h) in web._MULTIPART_ROUTES]
        assert any(re.match(p, "/api/sales/import/kdp") for p in pattern_strs), (
            f"no multipart route matches /api/sales/import/kdp; patterns: {pattern_strs}"
        )

    def test_multipart_import_route_uses_sales_handler(self):
        # Dispatch one match to confirm the lambda calls api_sales_import.
        from scripts import web

        for regex, max_bytes, handler in web._MULTIPART_ROUTES:
            m = regex.match("/api/sales/import/kdp")
            if m:
                # Make a tiny invalid body — handler should run and
                # return an error envelope (no boundary), confirming
                # the wiring rather than the parser logic itself
                # (parser is exhaustively tested elsewhere).
                result = handler(m, b"", "")
                assert result.get("status") == "error"
                assert result.get("code") == "missing_boundary"
                return
        pytest.fail("no multipart route handler ran for /api/sales/import/kdp")
