"""scripts.core.po_vision_store — own-versification store writer for the
Patrologia vision-transcription lane (Phase D1b).

Unlike ``extract_patrologia_pdf.write_book_module_patrologia`` (which OCR-
extracted the body then ``renumber_against_canonical``'d the fragments into the
KJV skeleton — losing the source margin numerals + the LXX Additions, and
sweeping the editor's Ge'ez-script apparatus into the verse text), this writes
the vision-transcribed verses VERBATIM at their source margin numbering
(``VERSIFICATION = "own"``). No renumber, no merge, no fabrication.

The verses come from an Opus vision agent that read the PO page images (see the
D1b plan / ``extract_patrologia_pdf.render_body_for_vision``); this module only
serializes them into the store with honest provenance. It writes to a ``slot``
filename (e.g. ``est_patrologia``) while the ``BOOK`` attribute stays canonical
(``est``), so the standalone render path resolves the KJV cross-reference via
``_canonical_book`` and ``est.py`` (the EOTC ocr-tier3 Esther) is left untouched.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path


def write_po_vision_module(
    *,
    slot: str,
    book: str,
    verses: list,
    po_book: str,
    page_range: tuple[int, int],
    phase: str = "D1b",
    extraction_date: str | None = None,
    translations_module=None,
) -> Path:
    """Write ``content/translations/geez-tewahedo/<slot>.py`` from vision-
    transcribed ``(chapter, verse, text)`` tuples, trusting the source
    versification (``VERSIFICATION = "own"``; no renumber).

    Parameters
    ----------
    slot
        Output module stem (e.g. ``"est_patrologia"``) — how the standalone path
        addresses the book; distinct from ``est.py``.
    book
        Canonical ``BOOK`` attribute (e.g. ``"est"``) used for the KJV cross-ref.
    verses
        ``(chapter, verse, text)`` in SOURCE order. ``verse`` may be an int
        (canonical) or a str Addition label (e.g. ``"B1"``) — serialized
        literal_eval-safe by ``write_book_module``.
    po_book
        Key into ``extract_patrologia_pdf.PO_SOURCES`` for the PO provenance.
    page_range
        The (start, end) PDF page range transcribed (recorded in the docstring).
    translations_module
        The module providing ``write_book_module`` (defaults to
        ``scripts.extract_parallel_pdf``; injectable for tests).
    """
    from scripts.extract_patrologia_pdf import PO_SOURCES

    if translations_module is None:
        import scripts.extract_parallel_pdf as translations_module

    src = PO_SOURCES[po_book]
    ext_date = extraction_date or date.today().isoformat()
    doc_extra = "\n".join(
        [
            f"Source: {src.citation}",
            f"Archive: {src.archive_url}",
            f"Editor: {src.editor} ({src.year}); public-domain bilingual critical edition.",
            "",
            "Transcription method: OWN-VERSIFICATION via an Opus VISION agent reading the",
            "Patrologia Orientalis page images (the D1b vision lane) — recovers the source",
            "margin verse-numerals + the interleaved LXX Additions (lettered verse labels)",
            "that the earlier Tesseract OCR lost, and EXCLUDES the editor's apparatus band.",
            "Source numbering is authoritative — NOT renumbered against the KJV floor.",
            f"PDF pages: {page_range[0]}-{page_range[1]}.",
            f"Verse count: {len(verses)}.",
        ]
    )
    return translations_module.write_book_module(
        translation="geez-tewahedo",
        book=book,
        verses=verses,
        source_quality="patrologia-printed-tier1",
        extraction_date=ext_date,
        ingest_phase=phase,
        docstring_extra=doc_extra,
        source_provenance=src.provenance,
        source_yaml_ref=src.archive_url,
        tool="scripts/core/po_vision_store.py (Opus vision)",
        versification="own",
        filename=slot,
    )
