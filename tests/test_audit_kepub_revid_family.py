"""Tests for dev/audit_kepub_revid_family.py — gate D9 (kepub -sN rev-id family).

Synthetic in-memory kepubs exercise the bucketing: an inline ``verse-notes`` aside MUST
carry a ``-sN`` tail (bare → live regression), a navigate ``study-glossary-cat`` aside is
bare by design, and the liveness self-check fails when the class-first popup regex matches
0 (kepubify attribute reorder → vacuous gate). The real-kepub census is validated on the
on-disk flagship during round-15 D9.
"""

import importlib.util
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("audit_kepub_revid_family", REPO / "dev" / "audit_kepub_revid_family.py")
akr = importlib.util.module_from_spec(_spec)
sys.modules["audit_kepub_revid_family"] = akr
_spec.loader.exec_module(akr)


def _kepub(tmp_path: Path, body: str) -> str:
    out = tmp_path / "t.kepub.epub"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr(
            "index.xhtml",
            '<?xml version="1.0" encoding="utf-8"?><html xmlns="http://www.w3.org/1999/xhtml" '
            'xmlns:epub="http://www.idpf.org/2007/ops"><body>' + body + "</body></html>",
        )
    return str(out)


_INLINE_SN = '<aside class="verse-notes" id="vnotes-gen-1-1-s1" epub:type="footnote">n</aside>'
_NAV_BARE = '<aside class="study-glossary-cat verse-notes" id="vnotes-gen-1-1-comm" epub:type="footnote">n</aside>'
_INLINE_BARE = '<aside class="verse-notes" id="vnotes-gen-1-2" epub:type="footnote">n</aside>'


def test_clean_kepub_passes(tmp_path):
    """An inline aside with -sN + a by-design bare navigate aside → PASS; liveness > 0."""
    epub = _kepub(tmp_path, _INLINE_SN + _NAV_BARE)
    res = akr.audit_kepub(epub)
    assert res.green, res.fails
    assert res.stats["inline_sN"] == 1 and res.stats["navigate_bare_by_design"] == 1
    assert res.stats["liveness_class_first_matches"] >= 1
    assert akr.main([epub]) == 0


def test_bare_inline_id_fails(tmp_path):
    """An inline verse-notes aside WITHOUT a -sN tail is the live guard-#19 regression
    (Kobo navigates away mid-read) → FAIL."""
    epub = _kepub(tmp_path, _INLINE_SN + _INLINE_BARE)
    res = akr.audit_kepub(epub)
    assert not res.green
    assert res.stats["inline_bare"] == 1
    assert any("bare INLINE popup id" in f and "vnotes-gen-1-2" in f for f in res.fails), res.fails
    assert akr.main([epub]) == 1


def test_navigate_bare_is_allowed(tmp_path):
    """A bare study-glossary-cat (navigate) id is by design — it must NOT count as a bare
    inline regression."""
    epub = _kepub(tmp_path, _NAV_BARE + _NAV_BARE)
    res = akr.audit_kepub(epub)
    assert res.green, res.fails
    assert res.stats["inline_bare"] == 0 and res.stats["navigate_bare_by_design"] == 2


def test_attribute_reorder_trips_liveness(tmp_path):
    """If kepubify puts id BEFORE class, the class-first popup regex matches 0 → the gate
    would pass vacuously; the liveness self-check FAILs instead."""
    reordered = '<aside id="vnotes-gen-1-1-s1" class="verse-notes" epub:type="footnote">n</aside>'
    epub = _kepub(tmp_path, reordered)
    res = akr.audit_kepub(epub)
    # The attribute-agnostic bucketer still sees a valid inline -sN id (no inline-bare) ...
    assert res.stats["inline_bare"] == 0 and res.stats["inline_sN"] == 1
    # ... but the class-first liveness probe matched 0 → FAIL (vacuous-pass guard).
    assert res.stats["liveness_class_first_matches"] == 0
    assert not res.green
    assert any("LIVENESS" in f for f in res.fails), res.fails
