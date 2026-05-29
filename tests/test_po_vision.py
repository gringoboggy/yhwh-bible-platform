"""Phase D1b — Patrologia vision-transcription scaffolding tests.

Covers the three connection-tolerant code components (plan Tasks 1-3):
- render_body_for_vision (extract_patrologia_pdf) — render a PO page's
  banner+Ge'ez-body strip to a PNG for an Opus vision agent (apparatus excluded).
- write_book_module(versification=, filename=) + string-verse serialization
  (extract_parallel_pdf) — emit VERSIFICATION="own", write an arbitrary slot
  filename, and serialize string verse labels (the LXX Additions A-F) faithfully.
- po_vision_store.write_po_vision_module — own-versification store writer that
  trusts the source numbering (no renumber, no merge).
"""

import ast
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
EST_PDF = REPO / "GAPS" / "5_Esther" / "Esther__PO-9-fasc-1_Pereira_1913.pdf"


def _const(text: str, name: str):
    """Parse a top-level ``NAME = <literal>`` from generated module text,
    quote-style-agnostic: write_book_module emits repr() (single quotes); ruff
    converts to double quotes at commit. literal_eval reads both identically."""
    m = re.search(rf"^{name} = (.+)$", text, re.MULTILINE)
    return ast.literal_eval(m.group(1)) if m else None


def _verses(text: str):
    return ast.literal_eval(text.split("VERSES = ", 1)[1].strip())


# ── Task 1 ────────────────────────────────────────────────────────────
def test_render_body_for_vision_writes_png(tmp_path):
    if not EST_PDF.is_file():
        pytest.skip("Esther PO PDF not on disk (gitignored GAPS tree)")
    import fitz

    from scripts.extract_patrologia_pdf import render_body_for_vision

    doc = fitz.open(str(EST_PDF))
    try:
        out = render_body_for_vision(doc[24], tmp_path / "p24.png", dpi=230, geez_top_fraction=0.45)
    finally:
        doc.close()
    assert out.is_file()
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic
    pix = fitz.Pixmap(str(out))
    assert pix.width <= 1568 and pix.height <= 1568  # under the vision downsample cap
    assert pix.width > 800  # full page width preserved (not a thin sliver)


# ── Task 2 ────────────────────────────────────────────────────────────
def test_write_book_module_int_verses_byte_identical_format(tmp_path, monkeypatch):
    """Default call (no versification/filename, int verses) is byte-identical to before."""
    import scripts.extract_parallel_pdf as ep

    monkeypatch.setattr(ep, "TRANSLATIONS_DIR", tmp_path)
    out = ep.write_book_module(translation="t", book="b", verses=[(1, 2, "x")], source_quality="q", extraction_date="d")
    text = out.read_text(encoding="utf-8")
    assert "    (1, 2, 'x')," in text  # int ch/v stay unquoted exactly as before
    assert "VERSIFICATION" not in text  # default unset → no line
    assert out.name == "b.py"  # default filename = book


def test_write_book_module_versification_and_filename(tmp_path, monkeypatch):
    import scripts.extract_parallel_pdf as ep

    monkeypatch.setattr(ep, "TRANSLATIONS_DIR", tmp_path)
    out = ep.write_book_module(
        translation="geez-tewahedo",
        book="est",
        verses=[(1, 1, "ሰላም።")],
        source_quality="patrologia-printed-tier1",
        extraction_date="2026-05-28",
        versification="own",
        filename="est_patrologia",
    )
    assert out.name == "est_patrologia.py"  # filename overrides the book-derived name
    text = out.read_text(encoding="utf-8")
    assert _const(text, "VERSIFICATION") == "own"
    assert _const(text, "BOOK") == "est"  # BOOK stays canonical


def test_write_book_module_string_verse_label_roundtrips(tmp_path, monkeypatch):
    """A string Addition label (e.g. B1) serializes to a literal_eval-safe tuple,
    in source order, with the canonical verses around it intact."""
    import scripts.extract_parallel_pdf as ep

    monkeypatch.setattr(ep, "TRANSLATIONS_DIR", tmp_path)
    verses = [(3, 13, "canonical።"), (3, "B1", "addition።"), (3, 14, "back።")]
    out = ep.write_book_module(
        translation="geez-tewahedo",
        book="zzz",
        verses=verses,
        source_quality="patrologia-printed-tier1",
        extraction_date="2026-05-28",
        versification="own",
    )
    assert _verses(out.read_text(encoding="utf-8")) == verses  # label + source order preserved


# ── Task 3 ────────────────────────────────────────────────────────────
def test_write_po_vision_module_own_no_renumber(tmp_path, monkeypatch):
    import scripts.extract_parallel_pdf as ep

    monkeypatch.setattr(ep, "TRANSLATIONS_DIR", tmp_path)
    from scripts.core import po_vision_store as pv

    verses = [(1, "A1", "dream።"), (1, 1, "canonical።"), (3, "B1", "edict።")]
    out = pv.write_po_vision_module(
        slot="est_patrologia",
        book="est",
        verses=verses,
        po_book="est",
        page_range=(24, 65),
        phase="D1b",
        translations_module=ep,
    )
    assert out.name == "est_patrologia.py"
    text = out.read_text(encoding="utf-8")
    assert _const(text, "VERSIFICATION") == "own"
    assert _const(text, "SOURCE_QUALITY") == "patrologia-printed-tier1"
    assert _const(text, "BOOK") == "est"  # canonical BOOK, slot filename
    assert "vision" in text.lower()  # provenance records the vision method
    assert "patrologia-orientalis-vol9" in text  # provenance pulled from PO_SOURCES["est"]
    assert _verses(text) == verses  # source order + string labels preserved, NOT renumbered
