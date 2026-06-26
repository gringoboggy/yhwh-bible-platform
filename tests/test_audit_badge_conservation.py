"""Tests for dev/audit_badge_conservation.py — gate G4 (badge-conservation / P2).

Synthetic, in-memory tmp epubs + tmp sidecars (no real build) exercise the two
checks the gate enforces:
  * SIDECAR — the build's ``badge_verses_skipped`` counter == 0 (and the
    sidecar-absent require/warn behavior),
  * ORPHAN MARKERS — a badge edition (a ``verse-notes-badge`` /
    ``study-glossary-jump`` present) holds zero raw ``note-ref`` inline markers;
    a non-badge (numbers) edition keeps its markers without false-FAILing.
The real-epub scan is covered by a ``slow`` test gated on the round-14 build.
"""

import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("audit_badge_conservation", REPO / "dev" / "audit_badge_conservation.py")
abc = importlib.util.module_from_spec(_spec)
# Register before exec so the module's @dataclass can resolve its own module.
sys.modules["audit_badge_conservation"] = abc
_spec.loader.exec_module(abc)

_CONTAINER = (
    '<?xml version="1.0"?><container version="1.0" '
    'xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
    '<rootfiles><rootfile full-path="content.opf" '
    'media-type="application/oebps-package+xml"/></rootfiles></container>'
)

# A collapsed badge anchor (popup layout) + its merged aside — the clean shape.
_BADGE = (
    '<a class="verse-notes-badge" id="vbadge-gen-1-1-s1" href="#vnotes-gen-1-1-s1" '
    'epub:type="noteref" title="2 notes"><sup class="marker-badge">2</sup></a>'
)
_ASIDE = (
    '<aside class="verse-notes" id="vnotes-gen-1-1-s1" epub:type="footnote">'
    '<div class="vn-item note-comm">a note body</div>'
    '<div class="vn-item note-xref">another</div></aside>'
)
# A raw, un-collapsed inline marker (the orphan symptom).
_ORPHAN = '<a class="note-ref note-comm" id="ref-gen0102comm" href="#note-gen0102comm" epub:type="noteref"><sup class="marker-comm">*</sup></a>'  # noqa: E501


def _doc(body: str) -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<html xmlns="http://www.w3.org/1999/xhtml" '
        'xmlns:epub="http://www.idpf.org/2007/ops"><body>' + body + "</body></html>"
    )


def _make_epub(tmp_path: Path, body: str, *, name: str = "t.epub") -> str:
    """Minimal one-document epub whose single spine piece holds ``body``."""
    opf = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bid">'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="bid">urn:x:1</dc:identifier>'
        "<dc:title>t</dc:title><dc:language>en</dc:language></metadata>"
        '<manifest><item id="c" href="c.xhtml" media-type="application/xhtml+xml"/></manifest>'
        '<spine><itemref idref="c"/></spine></package>'
    )
    out = tmp_path / name
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", _CONTAINER)
        zf.writestr("content.opf", opf)
        zf.writestr("c.xhtml", _doc(body))
    return str(out)


def _write_sidecar(epub_path: str, payload: dict) -> None:
    Path(epub_path + ".stats.json").write_text(json.dumps(payload), encoding="utf-8")


def _ok_sidecar(**over) -> dict:
    base = {
        "edition_id": "catholic-study",
        "version": "v",
        "cache_hit": False,
        "skipped": False,
        "size_mb": 1.0,
        "build_seconds": 1.0,
        "filename": "t.epub",
        "target_reader": "everywhere",
        "badge_verses_skipped": 0,
    }
    base.update(over)
    return base


def test_pass_clean_badge_edition(tmp_path):
    """(a) PASS — sidecar badge_verses_skipped=0 + a collapsed badge with NO raw
    note-ref marker → green / exit 0."""
    epub = _make_epub(tmp_path, "<p>In the beginning" + _BADGE + "</p>" + _ASIDE)
    _write_sidecar(epub, _ok_sidecar())
    res = abc.audit_epub(epub)
    assert res.green, res.fails
    assert res.stats["badge_verses_skipped"] == 0
    assert res.stats["orphan_markers"] == 0
    assert res.stats["is_badge_edition"] == 1
    assert abc.main([epub]) == 0


def test_fail_sidecar_skipped_nonzero(tmp_path):
    """(b) FAIL — sidecar badge_verses_skipped=3 (the build bailed on 3 verses)."""
    epub = _make_epub(tmp_path, "<p>x" + _BADGE + "</p>" + _ASIDE)
    _write_sidecar(epub, _ok_sidecar(badge_verses_skipped=3))
    res = abc.audit_epub(epub)
    assert not res.green
    assert any("badge_verses_skipped=3" in f for f in res.fails), res.fails
    assert res.stats["badge_verses_skipped"] == 3
    assert abc.main([epub]) == 1


def test_fail_orphan_marker_present(tmp_path):
    """(c) FAIL — a raw note-ref marker survives alongside a badge (desync), even
    though the sidecar counter reads 0."""
    epub = _make_epub(tmp_path, "<p>x" + _BADGE + " and " + _ORPHAN + "</p>" + _ASIDE)
    _write_sidecar(epub, _ok_sidecar())
    res = abc.audit_epub(epub)
    assert not res.green
    assert res.stats["orphan_markers"] == 1
    assert any("orphan inline marker ref-gen0102comm" in f for f in res.fails), res.fails
    assert abc.main([epub]) == 1


def test_sidecar_absent_warns_then_requires(tmp_path):
    """(d) Sidecar absent → WARN + skip by default (still green if no orphan);
    ``--require-sidecar`` turns the same absence into a FAIL."""
    epub = _make_epub(tmp_path, "<p>x" + _BADGE + "</p>" + _ASIDE)  # no sidecar written
    res = abc.audit_epub(epub)
    assert res.green, res.fails
    assert any("not found" in w for w in res.warns), res.warns
    assert res.stats["sidecar_present"] == 0
    # require_sidecar promotes the absence to a FAIL
    res2 = abc.audit_epub(epub, require_sidecar=True)
    assert not res2.green
    assert any("not found" in f for f in res2.fails), res2.fails
    assert abc.main(["--require-sidecar", epub]) == 1


def test_numbers_edition_markers_not_orphans(tmp_path):
    """A non-badge (numbers) edition has NO badge anchors → its inline note-ref
    markers are by-design and must NOT FAIL (a WARN notes the skip)."""
    epub = _make_epub(tmp_path, "<p>x" + _ORPHAN + " more " + _ORPHAN + "</p>")
    _write_sidecar(epub, _ok_sidecar(marker_style="numbers"))
    res = abc.audit_epub(epub)
    assert res.green, res.fails
    assert res.stats["is_badge_edition"] == 0
    assert res.stats["orphan_markers"] == 2
    assert any("non-badge" in w for w in res.warns), res.warns


def test_sidecar_present_without_key_warns(tmp_path):
    """A pre-instrument sidecar (no badge_verses_skipped key) → WARN, treated as 0,
    not a FAIL."""
    epub = _make_epub(tmp_path, "<p>x" + _BADGE + "</p>" + _ASIDE)
    payload = _ok_sidecar()
    del payload["badge_verses_skipped"]
    _write_sidecar(epub, payload)
    res = abc.audit_epub(epub)
    assert res.green, res.fails
    assert any("predates the G4 instrument" in w for w in res.warns), res.warns


def test_glossary_jump_counts_as_badge_edition(tmp_path):
    """The eink backmatter layout uses ``study-glossary-jump`` anchors; they too
    mark a badge edition, so a surviving note-ref there is an orphan."""
    jump = (
        '<a class="study-glossary-jump badge-cat-comm" id="vbadge-gen-1-1-comm" '
        'href="#vnotes-gen-1-1-comm" epub:type="noteref"><span class="marker-badge">1</span></a>'
    )
    epub = _make_epub(tmp_path, "<p>x" + jump + " " + _ORPHAN + "</p>")
    _write_sidecar(epub, _ok_sidecar(target_reader="eink"))
    res = abc.audit_epub(epub)
    assert not res.green
    assert res.stats["is_badge_edition"] == 1
    assert res.stats["orphan_markers"] == 1


# ── real-data fixture (round-14 catholic-study epub) — gated slow ──────────────
_REAL_GLOBS = [
    Path(r"C:\Users\bogda\YHWH-builds\round14-g4"),
    Path(r"C:\Users\bogda\YHWH-builds"),
]


def _find_real_epub() -> str | None:
    for root in _REAL_GLOBS:
        if root.is_dir():
            hits = sorted(root.glob("**/*catholic-study*.epub"))
            if hits:
                return str(hits[0])
    return None


@pytest.mark.slow
def test_real_catholic_study_epub_is_badge_conserved():
    epub = _find_real_epub()
    if not epub:
        pytest.skip("no round-14 catholic-study epub on disk")
    res = abc.audit_epub(epub)
    assert res.green, "\n".join(res.fails[:50])
