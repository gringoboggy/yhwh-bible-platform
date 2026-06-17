"""scripts.core.preview — live one-chapter preview composer (Phase ψ.1.0).

Produces a self-contained HTML page suitable for iframe srcdoc=
rendering on /customize and /wizard. Composes existing surfaces
(translations, notes, editions, themes, traditions, kinds) into
a single chapter view so a publisher can see the apparatus their
edition would ship without going through the full EPUB build
pipeline.

Public API:
    render_chapter_preview(edition_id, book_code, chapter,
                            *, translation_id="kjv") -> dict

        Returns the §9 standard dict shape:
          {"status": "ok", "html": "<full standalone HTML>",
           "notes_shown": int, "verse_count": int}
          {"status": "error", "code": "...", "http": 4xx,
           "message": "..."}

The composer is deliberately a SEPARATE rendering path from
scripts/build_edition.py's full build. The full build reads
pre-built HTML from epub_working/ and runs filter passes on it;
the preview reads notes + translation directly and renders fresh.
This means:

  - The preview can run when epub_working/ doesn't exist (e.g. on
    a fresh checkout, or in the bundled binary's first launch).
  - The preview's output won't be byte-identical to the EPUB —
    minor formatting nuances may differ. Per the spec ("rendering
    one chapter as the reader sees it"), close-enough is fine for
    a live preview.
  - Future polish (apparatus pop-up positioning, verse-popup
    translation overlay, per-book popup-language CSS classes)
    rides on this module without touching the build pipeline.

Sub-phasing:
  - **ψ.1.0** (this module + api_preview wrapper) — infra
  - **ψ.1.1** (future) /customize iframe slot + debounced refresh
  - **ψ.1.2** (future) /wizard iframe slot on relevant steps
"""

from __future__ import annotations

import html
from pathlib import Path

from scripts.core import config, notes_io, translations


REPO = Path(__file__).resolve().parent.parent.parent
THEMES_DIR = REPO / "content" / "themes"
NOTES_DIR = REPO / "content" / "notes"


# Note tuple shape per CLAUDE_PROJECT_RULES §7.1 + scripts.core.matrix:
#     (chapter, verse, suffix, anchor, kind, title, label, body, attribution)
_NOTE_CH = 0
_NOTE_VERSE = 1
_NOTE_KIND = 4
_NOTE_TITLE = 5
_NOTE_LABEL = 6
_NOTE_BODY = 7
_NOTE_ATTR = 8


def _read_theme_css(theme_id: str) -> str:
    """Return the theme override CSS, or empty string if absent."""
    if not theme_id:
        return ""
    f = THEMES_DIR / f"{theme_id}.css"
    if not f.is_file():
        return ""
    return f.read_text(encoding="utf-8")


def _load_book_notes(book_code: str) -> list[tuple] | dict:
    """Read notes for one book; empty list if absent; error dict if unparseable."""
    p = NOTES_DIR / f"{book_code}.py"
    if not p.is_file():
        return []
    loaded = notes_io.load_notes_checked(p, book=book_code)
    if isinstance(loaded, dict):
        return loaded
    return loaded


def _filter_chapter_notes(
    notes: list[tuple],
    chapter: int,
    enabled_kinds: set[str],
) -> list[tuple]:
    """Return notes for ``chapter`` whose kind is enabled. Sorted by
    verse, then by their original tuple order (stable)."""
    out = []
    for tup in notes:
        if len(tup) < 5:
            continue
        if tup[_NOTE_CH] != chapter:
            continue
        if tup[_NOTE_KIND] not in enabled_kinds:
            continue
        out.append(tup)
    out.sort(key=lambda t: t[_NOTE_VERSE])
    return out


def _kind_symbol(kind_code: str, kinds_idx: dict, cats_idx: dict) -> str:
    """Resolve the inline-marker glyph for a kind. Falls back to ``◆``."""
    k = kinds_idx.get(kind_code)
    if not k:
        return "◆"
    cat_id = k.get("category", "")
    cat = cats_idx.get(cat_id, {})
    return cat.get("symbol", "◆")


def _render_note_aside(note: tuple, idx: int, kind_symbol: str) -> str:
    """Render one note as an inline aside (popup)."""
    title = note[_NOTE_TITLE] if len(note) > _NOTE_TITLE else ""
    body = note[_NOTE_BODY] if len(note) > _NOTE_BODY else ""
    attr = note[_NOTE_ATTR] if len(note) > _NOTE_ATTR else ""
    kind = note[_NOTE_KIND]

    pieces = []
    if title:
        pieces.append(f'<strong class="note-title">{html.escape(title)}</strong>')
    if body:
        # Sanitize at the preview boundary, mirroring the build path
        # (inject.build_aside → sanitize_html). Bodies legitimately carry
        # inline markup (em / a / strong / sup …) which is whitelisted;
        # <script>, on* handlers, javascript: URLs etc. are stripped.
        # The /api/preview GET route is UNAUTHENTICATED and AI-authored
        # bodies share the note store, so "publisher-trusted" does not
        # hold here (G2 / B2a.7).
        from scripts.core.html_sanitize import sanitize_html

        pieces.append(f'<div class="note-body">{sanitize_html(body)}</div>')
    if attr:
        pieces.append(f'<div class="note-attr">— {html.escape(attr)}</div>')
    inner = "".join(pieces)
    return (
        f'<aside class="note note-{html.escape(kind)}" '
        f'id="preview-note-{idx}" data-kind="{html.escape(kind)}">'
        f'<span class="note-symbol">{html.escape(kind_symbol)}</span> '
        f"{inner}"
        f"</aside>"
    )


# Base CSS for the preview iframe — minimal but readable. Theme
# overrides append after this. Inline so the iframe's srcdoc is
# fully self-contained (no relative URLs to resolve).
_BASE_CSS = """
* { box-sizing: border-box; }
body {
  font-family: Georgia, "Times New Roman", serif;
  font-size: 17px;
  line-height: 1.6;
  color: #1f2937;
  max-width: 38em;
  margin: 2em auto;
  padding: 0 1.5em;
  background: #fafaf7;
}
header {
  border-bottom: 1px solid #d1d5db;
  margin-bottom: 1.5em;
  padding-bottom: 0.75em;
}
h1 {
  font-size: 1.6rem;
  margin: 0 0 0.25em;
  font-weight: 600;
  letter-spacing: -0.01em;
}
.preview-meta {
  font-size: 0.75rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.verse {
  margin: 0 0 0.65em;
  text-align: justify;
}
.verse-num {
  font-size: 0.65em;
  color: #94a3b8;
  vertical-align: super;
  font-family: ui-monospace, SFMono-Regular, monospace;
  margin-right: 0.25em;
  user-select: none;
}
.verse-text { display: inline; }
.note-ref {
  color: #2563eb;
  text-decoration: none;
  font-size: 0.85em;
  cursor: pointer;
  margin: 0 0.1em;
  user-select: none;
}
.note-ref:hover { text-decoration: underline; }
.notes-block {
  margin-top: 2em;
  padding-top: 1em;
  border-top: 1px solid #d1d5db;
  font-size: 0.9rem;
}
.note {
  margin: 0.5em 0;
  padding: 0.6em 0.85em;
  background: white;
  border-left: 3px solid #cbd5e1;
  border-radius: 0.25rem;
  font-size: 0.92em;
  line-height: 1.5;
}
.note-symbol {
  font-size: 1.2em;
  margin-right: 0.4em;
  color: #475569;
}
.note-title { display: block; margin-bottom: 0.25em; color: #1e293b; }
.note-body { color: #334155; }
.note-attr {
  font-size: 0.8em;
  color: #6b7280;
  margin-top: 0.4em;
  font-style: italic;
}
.preview-empty {
  text-align: center;
  padding: 3em 0;
  color: #94a3b8;
  font-style: italic;
}
.preview-fineprint {
  margin-top: 3em;
  font-size: 0.7rem;
  color: #9ca3af;
  text-align: center;
}
"""


def render_chapter_preview(
    edition_id: str,
    book_code: str,
    chapter: int,
    *,
    translation_id: str = "kjv",
) -> dict:
    """Render one chapter as a self-contained HTML page.

    Returns the §9 standard dict shape; HTML is in the ``html``
    key on success.

    Composes existing modules:
      - config.editions_by_id    → edition record
      - config.load_books        → book metadata (title, ch_count)
      - config.load_kinds        → kind → category resolver
      - config.load_categories   → category → symbol resolver
      - config.themes_by_id      → theme record (for label)
      - notes_io.load_notes      → notes for the book (lru-cached on mtime)
      - translations.get_chapter → verses for the chapter
      - build_edition.compute_enabled_kinds → kind filter
      - build_edition._resolve_traditions_for_book → tradition filter
      - read content/themes/<id>.css → theme override CSS

    No EPUB packaging, no file write, no subprocess. Purely a
    function over the corpus + edition spec.
    """
    book_code = config.resolve_book_code(book_code)

    eds = config.editions_by_id()
    if edition_id not in eds:
        return {
            "status": "error",
            "code": "unknown_edition",
            "http": 404,
            "message": f"unknown edition: {edition_id}",
        }
    edition = eds[edition_id]

    books = {b["code"]: b for b in config.load_books()}
    if book_code not in books:
        return {
            "status": "error",
            "code": "unknown_book",
            "http": 404,
            "message": f"unknown book: {book_code}",
        }
    book = books[book_code]
    ch_count = int(book.get("ch_count") or 0)

    try:
        chapter_int = int(chapter)
    except (TypeError, ValueError):
        return {
            "status": "error",
            "code": "invalid_chapter",
            "http": 400,
            "message": f"chapter must be an integer; got {chapter!r}",
        }
    if chapter_int < 1 or (ch_count and chapter_int > ch_count):
        return {
            "status": "error",
            "code": "chapter_out_of_range",
            "http": 400,
            "message": (f"{book_code} chapter {chapter_int} out of range (book has {ch_count} chapters)"),
        }

    # Filter notes by enabled_kinds (per the matrix's ship rules)
    # + tradition (per ψ.8.4 per-book resolver).
    from scripts.build_edition import (
        compute_enabled_kinds,
        _resolve_traditions_for_book,
    )

    enabled_kinds, _disabled_kinds = compute_enabled_kinds(edition, config.load_kinds())
    active_traditions = _resolve_traditions_for_book(edition, book_code)
    # Empty active_traditions = no tradition filter for this book.

    notes = _load_book_notes(book_code)
    if isinstance(notes, dict):
        return {
            "status": "error",
            "code": notes.get("code", "notes_unparseable"),
            "http": notes.get("http", 500),
            "message": notes.get("error", "notes file unparseable"),
            "book": book_code,
        }
    chapter_notes = _filter_chapter_notes(notes, chapter_int, enabled_kinds)

    # If a tradition filter is active, drop notes whose
    # tradition isn't in the active set. Notes carry tradition in
    # their ``attribution`` string (per ψ.8.0 backfill convention)
    # OR in a structured field; this preview uses a permissive
    # check that respects what's encoded in the body's data
    # attributes if present. For ψ.1.0 we trust the kind filter
    # to be the primary surface; tradition filtering adds visible
    # value once χ.2-5 commentaries land tradition-tagged content.
    if active_traditions:
        # Conservative: only filter when notes resolve to an explicit
        # tradition tag. Untagged (cross-tradition) notes always pass.
        # ω.31 — fixed a latent ImportError: prior code imported
        # `canonical_tradition_id` (doesn't exist; never executed
        # because no edition has populated `active_traditions` yet
        # in the production corpus). Replaced with `note_tradition`,
        # which is the project's standard tuple-shaped resolver.
        from scripts.core.traditions import note_tradition

        filtered = []
        for note in chapter_notes:
            tag = note_tradition(note) or "cross"
            if tag == "cross" or tag in active_traditions:
                filtered.append(note)
        chapter_notes = filtered

    # Verses for the chapter via translations.get_chapter.
    verses = translations.get_chapter(translation_id, book_code, chapter_int)

    # Build the kind → symbol map once.
    kinds_idx = {k["code"]: k for k in config.load_kinds()}
    cats_idx = {c["id"]: c for c in config.load_categories()}

    # Group notes by verse so each verse's markers land inline.
    notes_by_verse: dict[int, list[tuple]] = {}
    for note in chapter_notes:
        notes_by_verse.setdefault(note[_NOTE_VERSE], []).append(note)

    # Render the verse stream.
    verse_html_parts = []
    note_aside_parts = []
    note_idx = 0
    for vnum, vtext in verses:
        verse_pieces = [
            f'<span class="verse-num">{vnum}</span>',
            f'<span class="verse-text">{html.escape(vtext)}</span>',
        ]
        verse_notes = notes_by_verse.get(vnum, [])
        for note in verse_notes:
            note_idx += 1
            sym = _kind_symbol(note[_NOTE_KIND], kinds_idx, cats_idx)
            verse_pieces.append(
                f'<a class="note-ref" href="#preview-note-{note_idx}" '
                f'data-kind="{html.escape(note[_NOTE_KIND])}">'
                f"{html.escape(sym)}</a>"
            )
            note_aside_parts.append(_render_note_aside(note, note_idx, sym))
        verse_html_parts.append(f'<p class="verse" id="preview-v-{vnum}">{"".join(verse_pieces)}</p>')

    # Theme metadata for the header chip.
    theme_id = edition.get("theme") or "classic"
    theme_css = _read_theme_css(theme_id)

    # Edition + book + theme labels for the header strip.
    edition_title = edition.get("title", edition_id)
    book_title = book.get("title") or book_code.upper()

    if not verses:
        body_html = (
            '<div class="preview-empty">'
            f"No verses available for {html.escape(book_code.upper())} "
            f"chapter {chapter_int} in translation "
            f"<code>{html.escape(translation_id)}</code>. "
            "Check that the translation has this book extracted."
            "</div>"
        )
        notes_block = ""
    else:
        body_html = "\n".join(verse_html_parts)
        if note_aside_parts:
            notes_block = (
                '<section class="notes-block" aria-label="Editorial apparatus">'
                + "\n".join(note_aside_parts)
                + "</section>"
            )
        else:
            notes_block = ""

    # Compose the final standalone document.
    full_html = (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        f'<meta charset="utf-8">\n'
        f"<title>Preview · {html.escape(edition_title)} · "
        f"{html.escape(book_title)} {chapter_int}</title>\n"
        f"<style>{_BASE_CSS}{theme_css}</style>\n"
        "</head>\n"
        "<body>\n"
        "<header>\n"
        f"<h1>{html.escape(book_title)} {chapter_int}</h1>\n"
        '<div class="preview-meta">'
        f"{html.escape(edition_title)} · "
        f"theme <strong>{html.escape(theme_id)}</strong> · "
        f"translation <strong>{html.escape(translation_id)}</strong> · "
        f"{len(verses)} verse{'s' if len(verses) != 1 else ''} · "
        f"{note_idx} note{'s' if note_idx != 1 else ''}"
        "</div>\n"
        "</header>\n"
        f"{body_html}\n"
        f"{notes_block}\n"
        '<div class="preview-fineprint">'
        "Live preview · ψ.1.0 · render_chapter_preview() composes "
        "corpus + edition spec; not byte-identical to a full EPUB build."
        "</div>\n"
        "</body>\n"
        "</html>\n"
    )

    return {
        "status": "ok",
        "html": full_html,
        "verse_count": len(verses),
        "notes_shown": note_idx,
        "edition_id": edition_id,
        "book_code": book_code,
        "chapter": chapter_int,
        "theme_id": theme_id,
        "translation_id": translation_id,
    }
