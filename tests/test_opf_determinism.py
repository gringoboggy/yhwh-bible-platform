#!/usr/bin/env python3
"""OPF determinism guards (findings H1 + M18 + M20).

Fast unit tests (NO EPUB build) that pin the publishing metadata to static
values and verify the primary ``<dc:language>`` BCP-47 handling:

* ``_resolve_publishing`` must NOT read the wall clock — copyright_year and
  publication_date are statically pinned to the Ω.0 free-public pivot
  (2026 / 2026-05-14). Monkeypatching the module clock to a far-future date
  must NOT change the output.
* ``patch_opf`` must emit a byte-identical, static ``<dc:date>`` on repeat
  calls, and must suffix ``-US`` ONLY for a bare ``en`` primary language
  (never for ``gez`` and other non-English primaries).
"""

import datetime as _dt_module

import pytest

from scripts import build_edition, epub_utils

PINNED_YEAR = "2026"
PINNED_DATE = "2026-05-14"


# --- (a) _resolve_publishing ignores the wall clock --------------------------


def test_resolve_publishing_static_pins():
    """Defaults are statically pinned, not derived from datetime.now()."""
    pub = epub_utils._resolve_publishing({})
    assert pub["publication_date"] == PINNED_DATE
    assert pub["copyright_year"] == PINNED_YEAR


def test_resolve_publishing_ignores_far_future_clock(monkeypatch):
    """Even with a far-future clock, the pins stay 2026 / 2026-05-14.

    If ``epub_utils`` still references ``datetime`` we poison it; if the
    import was removed (wall clock fully gone) the pins are static anyway,
    so the assertion below still proves wall-clock independence.
    """

    class _FrozenFuture(_dt_module.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(9999, 12, 31, tzinfo=tz)

    # Only patch if the symbol is still present (it may have been removed).
    if hasattr(epub_utils, "datetime"):
        monkeypatch.setattr(epub_utils, "datetime", _FrozenFuture)

    pub = epub_utils._resolve_publishing({})
    assert pub["publication_date"] == PINNED_DATE
    assert pub["copyright_year"] == PINNED_YEAR


# --- patch_opf helpers -------------------------------------------------------

_MINIMAL_OPF = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" '
    'unique-identifier="bookid">\n'
    '  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" '
    'xmlns:opf="http://www.idpf.org/2007/opf">\n'
    '    <dc:identifier id="bookid">urn:yhwh:edition:test</dc:identifier>\n'
    "    <dc:title>Test</dc:title>\n"
    "    <dc:language>en</dc:language>\n"
    "    <dc:date>1900-01-01</dc:date>\n"
    "    <dc:rights>Copyright © 1900 Tester. All rights reserved.</dc:rights>\n"
    '    <meta property="dcterms:modified">1900-01-01T00:00:00Z</meta>\n'
    "  </metadata>\n"
    "  <manifest/>\n"
    "  <spine/>\n"
    "</package>\n"
)


def _primary_language(opf_text: str) -> str:
    """Return the FIRST <dc:language> value in the OPF (the primary)."""
    import re

    m = re.search(r"<dc:language>([^<]*)</dc:language>", opf_text)
    assert m is not None, "no <dc:language> emitted"
    return m.group(1)


def _dc_date(opf_text: str) -> str:
    import re

    m = re.search(r"<dc:date>([^<]*)</dc:date>", opf_text)
    assert m is not None, "no <dc:date> emitted"
    return m.group(1)


# --- (b) patch_opf emits a deterministic, static dc:date ---------------------


def test_patch_opf_dc_date_is_deterministic_and_pinned():
    ed = {"id": "test-edition"}
    out1 = build_edition.patch_opf(_MINIMAL_OPF, ed, "v2.4")
    out2 = build_edition.patch_opf(_MINIMAL_OPF, ed, "v2.4")
    assert out1 == out2, "patch_opf output is not byte-identical across calls"
    assert _dc_date(out1) == PINNED_DATE


# --- (c) primary dc:language: -US only for bare 'en' -------------------------


def test_patch_opf_language_geez_no_us_suffix():
    ed = {"id": "standalone-geez", "language_code": "gez"}
    out = build_edition.patch_opf(_MINIMAL_OPF, ed, "v2.4")
    primary = _primary_language(out)
    assert primary == "gez", f"expected bare 'gez', got {primary!r}"
    assert primary != "gez-US"
    assert primary != "en-US"


def test_patch_opf_language_default_en_us():
    ed = {"id": "flagship"}
    out = build_edition.patch_opf(_MINIMAL_OPF, ed, "v2.4")
    assert _primary_language(out) == "en-US"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
