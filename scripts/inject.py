#!/usr/bin/env python3
"""
inject.py — Strategy-A note injector.

When a note is promoted via prospect→promote (or authored via add_note),
its tuple is written to ``content/notes/<book>.py`` but NOTHING inserts
the corresponding `<a class="note-ref">…<sup>…</sup></a>` marker into
the rendered HTML or the matching `<aside class="note">…</aside>` into
the chapter's notes section. So the note exists in source but stays
invisible in EPUBs.

This tool closes that gap. For each source note whose HTML id is NOT
already present in the rendered HTML, it:

  1. Locates the verse region (between two `<a class="vn-link" id="v-…">`
     anchors) in the appropriate `index_split_NNN.html` file
  2. Locates the anchor text within that verse
  3. Inserts the marker `<a class="note-ref note-{kind}" id="ref-…">…
     <sup class="marker-{kind}">{glyph}</sup></a>` immediately after
     the anchor text (or at end of verse if anchor is empty)
  4. Inserts the corresponding `<aside class="note note-{kind}" id="note-…">`
     into the chapter's `<aside class="notes-section">` block in correct
     verse order

Strategy-A only (early canon — books with `id_prefix` and
`v-{prefix}-{ch}-{v}` deep-link verse anchors). Strategy-B handling for
late-canon books is a future addition (see sync_html_kinds.py for the
same split).

Crash-safe: ensure_backup() + atomic_write() per modified file.

Usage:
    python3 scripts/inject.py --book gen --dry-run
    python3 scripts/inject.py --book gen
    python3 scripts/inject.py --all-books

Modes:
    --dry-run       show what would change, don't write
    --book CODE     single book (e.g. 'gen')
    --all-books     every Strategy-A book in canon
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config  # noqa: E402
from scripts.core.notes_io import (  # noqa: E402
    atomic_write, ensure_backup, load_notes,
)

EPUB_DIR = REPO_ROOT / "epub_working"
NOTES_DIR = REPO_ROOT / "content" / "notes"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


# ----------------------------------------------------------------------
# Kind → glyph / HTML title mappings (derived from rendered HTML samples)
# ----------------------------------------------------------------------

KIND_TO_GLYPH = {
    # Word / language family
    "word": "⌘",
    "source": "✧",
    "parallel": "‖",
    "comm": "◇",
}

# Sub-kind families inherit glyph from their family prefix
def glyph_for(kind: str) -> str:
    if kind in KIND_TO_GLYPH:
        return KIND_TO_GLYPH[kind]
    if kind.startswith("lang-"):
        return "⌘"
    if kind.startswith("comm-"):
        return "◇"
    if kind.startswith("xref-") or kind.startswith("parallel-"):
        return "‖"
    if kind.startswith("text-") or kind.startswith("source-"):
        return "✧"
    # Sensible default for unknown kinds
    return "◇"


# Short HTML title attribute (category label, not the popover title)
def html_title_for(kind: str) -> str:
    if kind == "word":
        return "Word"
    if kind == "parallel" or kind.startswith("xref-") or kind.startswith("parallel-"):
        return "Parallel"
    if kind == "source" or kind.startswith("source-") or kind.startswith("text-"):
        return "Source"
    if kind in ("lang-hebrew", "lang-aramaic"):
        return "Hebrew"  # convention: hebrew + aramaic share the title
    if kind == "lang-greek":
        return "Greek"
    if kind == "lang-amharic":
        return "Amharic"
    if kind == "lang-geez":
        return "Ge'ez"
    if kind == "lang-latin":
        return "Latin"
    if kind == "lang-syriac":
        return "Syriac"
    if kind == "lang-arabic":
        return "Arabic"
    if kind.startswith("lang-"):
        return "Word"
    return "Note"


# ----------------------------------------------------------------------
# HTML builders
# ----------------------------------------------------------------------


def build_marker(kind: str, full_id: str) -> str:
    """The inline `<a class="note-ref">…<sup>…</sup></a>` element."""
    glyph = glyph_for(kind)
    title = html_title_for(kind)
    return (
        f'<a class="note-ref note-{kind}" id="ref-{full_id}" '
        f'href="#note-{full_id}" epub:type="noteref" title="{title}">'
        f'<sup class="marker-{kind}">{glyph}</sup></a>'
    )


def build_aside(kind: str, full_id: str, label: str, body_html: str) -> str:
    """The `<aside class="note">…</aside>` element for the notes-section.

    Phase ξ.4: body_html is sanitized at the build boundary. Notes
    legitimately contain inline markup (em / strong / a / sup /
    span etc.) so we whitelist; <script>, on* handlers, javascript:
    URLs, etc. are stripped. See scripts/core/html_sanitize.py for
    the threat model and whitelist."""
    from scripts.core.html_sanitize import sanitize_html
    glyph = glyph_for(kind)
    safe_body = sanitize_html(body_html)
    return (
        f'<aside class="note note-{kind}" id="note-{full_id}" '
        f'epub:type="footnote">\n'
        f'  <p><a href="#ref-{full_id}" class="note-back" title="Back">'
        f'{glyph}</a> <span class="note-label">{label}</span> '
        f'{safe_body}</p>\n'
        f'</aside>\n'
    )


# ----------------------------------------------------------------------
# Verse-region locator
# ----------------------------------------------------------------------


def find_verse_region(html: str, book_code: str, ch: int, v: int) -> tuple[int, int] | None:
    """Strategy-A verse region locator. See find_verse_region_b for late-canon."""
    # Match this verse's vn-link element fully
    this_anchor_re = re.compile(
        r'<a\s+class="vn-link"\s+id="v-' + re.escape(f"{book_code}-{ch}-{v}")
        + r'"[^>]*>\s*<span\s+class="vn">\d+</span>\s*</a>',
        re.DOTALL,
    )
    m = this_anchor_re.search(html)
    if not m:
        return None
    start = m.end()  # content begins right after closing </a>

    # End is the start of the NEXT vn-link (any verse), or end of containing <p>
    next_anchor_re = re.compile(r'<a\s+class="vn-link"\s+id="v-')
    nxt = next_anchor_re.search(html, start)
    if nxt:
        end = nxt.start()
    else:
        # No more verses; cap at end of containing paragraph
        close_p = html.find("</p>", start)
        end = close_p if close_p > 0 else len(html)
    return (start, end)


def find_chapter_region_b(text: str, bxx: str, ch: int, ch_count: int) -> tuple[int, int] | None:
    """Locate the byte-range for chapter ``ch`` of a Strategy-B book using
    ``id="ch-{bxx}-c{ch}"`` boundaries. Returns (start, end) or None."""
    start_marker = f'id="ch-{bxx}-c{ch}"'
    pos = text.find(start_marker)
    if pos == -1:
        return None
    end_pos = len(text)
    if ch + 1 <= ch_count:
        ep = text.find(f'id="ch-{bxx}-c{ch + 1}"', pos + 1)
        if ep != -1:
            end_pos = ep
    # Also cap by next book's first chapter (b{xx+1}-c1) if present
    try:
        bxx_n = int(bxx[1:])
        next_marker = f'id="ch-b{bxx_n + 1:02d}-c1"'
        ep = text.find(next_marker, pos + 1)
        if ep != -1 and ep < end_pos:
            end_pos = ep
    except (ValueError, IndexError):
        pass
    return (pos, end_pos)


def find_verse_region_b(text: str, region_start: int, region_end: int, v: int) -> tuple[int, int] | None:
    """Within a Strategy-B chapter region, locate verse ``v`` and return
    (verse_content_start, verse_content_end). Verse content is what
    follows ``<span class="vn">v</span>`` up to the next vn span or
    region end."""
    needle = f'<span class="vn">{v}</span>'
    p = text.find(needle, region_start, region_end)
    if p == -1:
        return None
    start = p + len(needle)
    # End: next vn span or region end
    next_p = re.search(r'<span\s+class="vn">\d+</span>', text[start:region_end])
    end = (start + next_p.start()) if next_p else region_end
    return (start, end)


def ensure_notes_section_b(text: str) -> tuple[str, tuple[int, int]] | None:
    """Strategy-B files often lack a ``<aside class="notes-section">`` block.
    Find existing or create one before ``</body>`` (or before a
    verse-refs-section if present). Returns (possibly-modified-text,
    (inside_start, inside_end)) ready for aside insertion."""
    section_open = '<aside class="notes-section" epub:type="footnotes" hidden="">'
    existing = text.find(section_open)
    if existing != -1:
        inside_start = existing + len(section_open)
        # Find matching </aside> using depth counting (same as Strategy-A logic)
        depth = 1
        pos = inside_start
        while depth > 0 and pos < len(text):
            no = text.find("<aside", pos)
            nc = text.find("</aside>", pos)
            if nc == -1:
                return None
            if no != -1 and no < nc:
                depth += 1
                pos = no + len("<aside")
            else:
                depth -= 1
                if depth == 0:
                    return text, (inside_start, nc)
                pos = nc + len("</aside>")
        return None
    # No section — create one before </body>
    body_close = text.rfind("</body>")
    if body_close == -1:
        return None
    block_open = (
        "\n" + section_open + "\n"
        '<hr class="notes-rule"/>\n'
        '<h3 class="notes-heading">Notes</h3>\n'
    )
    block_close = "</aside>\n"
    new_text = text[:body_close] + block_open + block_close + text[body_close:]
    inside_start = body_close + len(block_open)
    inside_end = inside_start  # empty section
    return new_text, (inside_start, inside_end)


def find_marker_insertion_point(verse_html: str, anchor: str) -> int | None:
    """Within a verse's HTML region, return the byte offset where a new
    marker should be inserted. Strategy:

      - If anchor text is provided, find its first occurrence in the
        VISIBLE text (skipping HTML tags); insert immediately after it.
      - If anchor is empty, insert at the end of the verse text (before
        any final whitespace).
      - If anchor isn't found, return None.

    Already-existing markers (`<a class="note-ref">`) right after the
    same anchor will sit BEFORE the new one (we insert at the spot
    immediately past the anchor text, which means after any prior markers
    that are already there). That's fine — order doesn't matter for
    function and is acceptable visually.
    """
    if not anchor or not anchor.strip():
        # Trim trailing whitespace; insert at end
        end = len(verse_html)
        while end > 0 and verse_html[end - 1] in " \t\n":
            end -= 1
        return end

    # Search for anchor in plain text (case-sensitive). The anchor field
    # in source notes is plain text, so a simple substring search works
    # most of the time. Skip occurrences inside tag attributes by tracking
    # depth.
    target = anchor.strip()
    depth = 0
    i = 0
    while i < len(verse_html):
        c = verse_html[i]
        if c == "<":
            depth += 1
        elif c == ">":
            depth -= 1
        elif depth == 0:
            # We're in text content. Try matching anchor here.
            if verse_html[i:i + len(target)] == target:
                return i + len(target)
        i += 1
    return None


def find_notes_section_for_chapter(html: str, ch: int) -> tuple[int, int] | None:
    """Return (start, end) of the `<aside class="notes-section">` block
    that holds asides for the given chapter. Strategy: each chapter's
    verses appear before its notes-section in document order; find the
    chapter heading marker `id="ch-bNN-cM"` (or any `id="ch-…-c{ch}"`)
    and then scan forward for the next `<aside class="notes-section">`.

    Returns the byte range INSIDE the notes-section (between its opening
    `>` and closing `</aside>`), where a new aside child should be
    inserted in verse order.
    """
    # Find the chapter heading anchor
    ch_marker_re = re.compile(r'<a\s+id="ch-b\d+-c' + str(ch) + r'"')
    m = ch_marker_re.search(html)
    if not m:
        return None
    # Find the first notes-section after the chapter heading
    section_open = re.search(
        r'<aside\s+class="notes-section"[^>]*>',
        html[m.end():],
    )
    if not section_open:
        return None
    open_start = m.end() + section_open.start()
    inside_start = m.end() + section_open.end()
    # Find matching </aside> — outer level. Naive but works because
    # nested <aside> children are siblings, and the outer </aside>
    # comes after all children. We scan with depth counting on `<aside`
    # / `</aside>` tokens.
    depth = 1
    pos = inside_start
    while depth > 0 and pos < len(html):
        next_open = html.find("<aside", pos)
        next_close = html.find("</aside>", pos)
        if next_close == -1:
            return None
        if next_open != -1 and next_open < next_close:
            depth += 1
            pos = next_open + len("<aside")
        else:
            depth -= 1
            if depth == 0:
                return (inside_start, next_close)
            pos = next_close + len("</aside>")
    return None


def find_aside_insertion_point(html: str, section: tuple[int, int],
                                ch: int, v: int, suffix: str, prefix: str) -> int:
    """Inside the chapter's notes-section, find the byte offset to insert
    a new aside such that asides remain in (verse, suffix) order. Returns
    the offset just before the first existing aside whose (v, s) is
    greater than ours, or the end of the section if all are smaller.
    """
    inside_start, inside_end = section
    region = html[inside_start:inside_end]
    # All existing aside ids: id="note-{prefix}{cc}{vv}{s}"
    existing_re = re.compile(
        r'<aside\s+class="note\s+[^"]+"\s+id="note-' + re.escape(prefix)
        + r'(\d{2})(\d{2})([a-z]?)"',
    )
    target = (v, suffix or "")
    insertion = inside_start  # default: just inside opening tag
    for m in existing_re.finditer(region):
        existing_ch = int(m.group(1))
        existing_v = int(m.group(2))
        existing_s = m.group(3) or ""
        if existing_ch != ch:
            # Different chapter — should not happen if section is ours;
            # treat as preceding ours so we land after them.
            insertion = inside_start + m.end()
            continue
        existing_target = (existing_v, existing_s)
        if existing_target < target:
            # find end of THIS aside (its </aside>) to land just after
            after_close = region.find("</aside>", m.end())
            if after_close < 0:
                continue
            # land just after the </aside> + any whitespace/newline
            after_close += len("</aside>")
            while after_close < len(region) and region[after_close] in " \t\n":
                after_close += 1
            insertion = inside_start + after_close
        else:
            # existing_target >= target → insert before this one
            return inside_start + m.start()
    return insertion


# ----------------------------------------------------------------------
# Per-book inject
# ----------------------------------------------------------------------


def inject_book(book: dict, dry_run: bool) -> dict:
    code = book["code"]
    prefix = book.get("id_prefix")
    bxx = book.get("bxx")
    ch_count = book.get("ch_count", 0)
    files = book.get("files", [])
    strategy = book.get("strategy", "A")

    notes = load_notes(NOTES_DIR / f"{code}.py") or []

    # Strategy gating — A needs id_prefix; B needs bxx + ch_count
    if strategy == "A":
        if not prefix:
            if not notes:
                return {"scanned": 0, "injected": 0, "already_in": 0,
                        "skipped_reason": "Strategy A but no id_prefix"}
            return {"error": f"book {code}: Strategy A but no id_prefix in metadata"}
    elif strategy == "B":
        if not bxx:
            if not notes:
                return {"scanned": 0, "injected": 0, "already_in": 0,
                        "skipped_reason": "Strategy B but no bxx"}
            return {"error": f"book {code}: Strategy B but no bxx in metadata"}
        if not prefix:
            # For Strategy-B id construction, fall back to bxx-as-prefix
            # (some projects use bxx + chvv as the note id base)
            prefix = bxx
    else:
        return {"error": f"book {code}: unknown strategy {strategy!r}"}

    if not files:
        return {"error": f"book {code} missing files in metadata"}

    stats = {"scanned": 0, "injected": 0, "already_in": 0, "missing_anchor": [],
             "missing_section": 0, "files_changed": []}

    # Load all book HTML files into memory once
    file_texts = {}
    for fname in files:
        fpath = EPUB_DIR / fname
        if fpath.is_file():
            file_texts[fname] = fpath.read_text(encoding="utf-8")

    if not file_texts:
        return {"error": f"no readable HTML files for {code}"}

    # For each note, decide where it lives + whether already there
    for tup in notes:
        if not isinstance(tup, tuple) or len(tup) < 8:
            continue
        ch, v, suffix, anchor, kind, _title, label, body = tup[:8]
        if not isinstance(ch, int) or not isinstance(v, int):
            continue
        full_id = f"{prefix}{ch:02d}{v:02d}{suffix or ''}"
        stats["scanned"] += 1

        # Find the file + verse region (strategy-dispatched)
        target_fname = None
        target_text = None
        verse_region = None

        # First check across ALL files — if marker exists ANYWHERE in this
        # book, the note is already in HTML. Handles file-split-boundary
        # cases where the marker may have been originally injected in one
        # file but the verse anchor ended up in another after re-splitting.
        if any(f'id="ref-{full_id}"' in t for t in file_texts.values()):
            stats["already_in"] += 1
            continue

        if strategy == "A":
            for fname, text in file_texts.items():
                if f'id="v-{code}-{ch}-{v}"' in text:
                    target_fname = fname
                    target_text = text
                    break
            if target_text is None:
                stats["missing_anchor"].append(f"{ch}:{v}{suffix} (no verse anchor)")
                continue
            verse_region = find_verse_region(target_text, code, ch, v)
        else:  # strategy == "B"
            # Locate the file containing this chapter
            for fname, text in file_texts.items():
                if f'id="ch-{bxx}-c{ch}"' in text:
                    target_fname = fname
                    target_text = text
                    break
            if target_text is None:
                stats["missing_anchor"].append(f"{ch}:{v}{suffix} (chapter heading not in any file)")
                continue
            ch_region = find_chapter_region_b(target_text, bxx, ch, ch_count)
            if ch_region is None:
                stats["missing_anchor"].append(f"{ch}:{v}{suffix} (chapter region not found)")
                continue
            verse_region = find_verse_region_b(target_text, ch_region[0], ch_region[1], v)

        if verse_region is None:
            stats["missing_anchor"].append(f"{ch}:{v}{suffix} (verse region not parseable)")
            continue
        v_start, v_end = verse_region
        verse_html = target_text[v_start:v_end]

        # Locate marker insertion point
        ins = find_marker_insertion_point(verse_html, anchor or "")
        if ins is None:
            stats["missing_anchor"].append(
                f"{ch}:{v}{suffix} anchor={anchor!r} not found in verse text")
            continue

        # Build marker
        marker_html = build_marker(kind, full_id)

        # Locate / create notes-section (strategy-dispatched)
        if strategy == "A":
            section = find_notes_section_for_chapter(target_text, ch)
            if section is None:
                stats["missing_section"] += 1
                continue
        else:  # strategy == "B" — single per-file section, create if absent
            ensured = ensure_notes_section_b(target_text)
            if ensured is None:
                stats["missing_section"] += 1
                continue
            target_text, section = ensured

        # Locate aside insertion point in document order
        aside_insertion = find_aside_insertion_point(
            target_text, section, ch, v, suffix or "", prefix
        )

        # Build aside
        aside_html = "  " + build_aside(kind, full_id, label, body)

        # Apply insertions in REVERSE byte-order so positions stay valid
        marker_pos_abs = v_start + ins
        # First insert aside (later in file usually), then marker
        if aside_insertion > marker_pos_abs:
            new_text = (
                target_text[:aside_insertion]
                + aside_html
                + target_text[aside_insertion:marker_pos_abs - 0 if False else aside_insertion]
            )
            # ^ that line was wrong; simpler approach below
        # Simpler: rebuild manually
        if aside_insertion >= marker_pos_abs:
            # aside comes later → insert aside first (no offset shift for marker)
            new_text = (
                target_text[:aside_insertion]
                + aside_html
                + target_text[aside_insertion:]
            )
            # then insert marker (its offset still valid)
            new_text = (
                new_text[:marker_pos_abs]
                + marker_html
                + new_text[marker_pos_abs:]
            )
        else:
            # marker comes later → insert marker first
            new_text = (
                target_text[:marker_pos_abs]
                + marker_html
                + target_text[marker_pos_abs:]
            )
            shifted_aside = aside_insertion  # earlier than marker, unchanged
            new_text = (
                new_text[:shifted_aside]
                + aside_html
                + new_text[shifted_aside:]
            )

        # Write back
        file_texts[target_fname] = new_text
        target_text = new_text  # keep refs current for next note in same file
        stats["injected"] += 1
        if target_fname not in stats["files_changed"]:
            stats["files_changed"].append(target_fname)

    if dry_run:
        return stats

    # Persist all modified files atomically with backup
    for fname in stats["files_changed"]:
        fpath = EPUB_DIR / fname
        ensure_backup(fpath)
        atomic_write(fpath, file_texts[fname])

    return stats


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(
        description="Strategy-A note injector — bridges source notes "
                    "to rendered HTML.",
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--book", help="single book code (e.g. 'gen')")
    g.add_argument("--all-books", action="store_true", help="every book")
    p.add_argument("--dry-run", action="store_true",
                   help="show what would change, don't write")
    args = p.parse_args()

    books = (
        [config.get_book(args.book)] if args.book else config.load_books()
    )

    print(f"\n{BOLD}inject{RESET} {DIM}{len(books)} book(s)"
          f"{'  (dry-run)' if args.dry_run else ''}{RESET}\n")

    grand = {"scanned": 0, "injected": 0, "already_in": 0,
             "missing_anchor": 0, "missing_section": 0}
    files_changed: set = set()
    failed = []

    for book in books:
        code = book["code"]
        if not (NOTES_DIR / f"{code}.py").is_file():
            continue
        stats = inject_book(book, dry_run=args.dry_run)
        if "error" in stats:
            print(f"  {RED}✗ {code:6}{RESET}  {stats['error']}")
            failed.append(code)
            continue
        if stats.get("skipped_reason"):
            print(f"  {DIM}○ {code:6}  skipped — {stats['skipped_reason']}{RESET}")
            continue

        s = stats["scanned"]
        inj = stats["injected"]
        ai = stats["already_in"]
        ma = len(stats.get("missing_anchor", []))
        ms = stats.get("missing_section", 0)
        flag = GREEN + "✓" if inj or ai else DIM + "○"
        verb = "would inject" if args.dry_run else "injected"
        msg = (f"  {flag}{RESET} {code:6}  {s:>4} src · {inj:>3} {verb} · "
               f"{ai:>4} already in HTML")
        if ma:
            msg += f" · {YELLOW}{ma} anchor-not-found{RESET}"
        if ms:
            msg += f" · {RED}{ms} no-notes-section{RESET}"
        print(msg)

        for k_ in ("scanned", "injected", "already_in", "missing_section"):
            grand[k_] += stats.get(k_, 0)
        grand["missing_anchor"] += len(stats.get("missing_anchor", []))
        files_changed.update(stats["files_changed"])

    print(f"\n  {BOLD}TOTAL{RESET}: "
          f"{grand['scanned']} scanned · "
          f"{grand['injected']} {'would-inject' if args.dry_run else 'injected'} · "
          f"{grand['already_in']} already in HTML")
    if grand["missing_anchor"]:
        print(f"  {YELLOW}{grand['missing_anchor']} note(s) had anchor text "
              f"not found in verse text — left untouched{RESET}")
    if grand["missing_section"]:
        print(f"  {RED}{grand['missing_section']} note(s) couldn't locate "
              f"their chapter's notes-section{RESET}")
    if files_changed:
        print(f"  {len(files_changed)} HTML file(s) "
              f"{'would be' if args.dry_run else ''} modified")
    print()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
