#!/usr/bin/env python3
"""
build_edition.py — Build a per-edition EPUB from the master corpus.

Filters notes from ``epub_working/`` per the rules in ``content/editions.yaml``,
patches OPF metadata to identify the edition, and packages a market-tuned
EPUB. The master corpus is never modified — filtering happens in a tempdir.

The same source corpus can therefore produce N market-tuned outputs:

    Ethiopian_Bible_ethiopian-tewahedo_v27_<ts>.epub
    Ethiopian_Bible_catholic-study_v27_<ts>.epub
    Ethiopian_Bible_evangelical-reformed_v27_<ts>.epub
    Ethiopian_Bible_jewish-study_v27_<ts>.epub
    Ethiopian_Bible_scholarly-academic_v27_<ts>.epub

Filter resolution per kind, in priority order:

  1. If ``code in disabled_kinds`` → DISABLED
  2. If ``code in enabled_kinds``  → ENABLED
  3. Else if ``category in enabled_categories`` → ENABLED
  4. Else                                       → DISABLED

Plus a phase gate: if the edition declares ``max_phase: mvp``, kinds at
``phase2``/``phase3`` are dropped regardless. ``legacy`` always passes
(existing notes must keep working).

Examples:
    python3 scripts/build_edition.py ethiopian-tewahedo
    python3 scripts/build_edition.py --all
    python3 scripts/build_edition.py --list
    python3 scripts/build_edition.py catholic-study --output-dir releases/
    python3 scripts/build_edition.py reformed --version v27 --dry-run

Exit codes:
    0  all editions built ok
    1  one or more editions failed
    2  setup error (unknown edition, missing files, bad config)
"""

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config  # noqa: E402

EPUB_DIR = REPO_ROOT / "epub_working"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


# ----------------------------------------------------------------------
# Edition → kind set resolution
# ----------------------------------------------------------------------


def _iter_note_ref_traditions():
    """Walk every note tuple on disk and yield
    ``(ref_id, tradition, book_code)``.

    Used by ``compute_tradition_disabled_html_ref_ids`` (ψ.8.2-A —
    filtering), ``apply_tradition_labels_to_html`` (ψ.8.2-B — label
    injection), and the per-book resolver (ψ.8.4 — overrides).
    Centralising the iteration here keeps every pass reading the same
    canonical mapping; future detectors that add tradition tags only
    need to update ``note_tradition``.

    Yields tuples like ``("ref-g0101a", "catholic", "gen")``. Notes
    whose chapter/verse aren't integers are silently skipped
    (defensive — the note-tuple shape is owned by the corpus).
    """
    from scripts.core.notes_io import load_notes
    from scripts.core.traditions import note_tradition

    books_idx = config.books_by_code()
    notes_dir = REPO_ROOT / "content" / "notes"
    for book_path in sorted(notes_dir.glob("*.py")):
        if book_path.stem == "__init__" or book_path.stem.startswith("_"):
            continue
        book_code = book_path.stem
        book = books_idx.get(book_code) or {}
        prefix = book.get("id_prefix")
        if not prefix:
            continue
        notes = load_notes(book_path) or []
        for tup in notes:
            if not isinstance(tup, tuple) or len(tup) < 8:
                continue
            ch = tup[0]
            vs = tup[1]
            suffix = tup[2] or ""
            try:
                ch_i = int(ch)
                vs_i = int(vs)
            except (TypeError, ValueError):
                continue
            ref_id = f"ref-{prefix}{ch_i:02d}{vs_i:02d}{suffix}"
            yield ref_id, note_tradition(tup), book_code


# ---- Phase ψ.8.4: per-book tradition overrides ----------------------
#
# Mirrors the ν.2.7-A popup_languages_per_book pattern. Editions can
# specify which traditions appear, with two levels of resolution:
#
#   traditions_default      list[str]   per-edition default
#   traditions_per_book     dict[code → list[str]]    overrides
#
# Resolution at filter / label time (per book):
#   if book in per_book:    raw = per_book[book]
#   else:                   raw = traditions_default
#   active = {t for t in raw if t in TRADITION_IDS}
#   active==∅ ⇒ no filter for that book (every tradition survives)
#   active≠∅ ⇒ filter — drop notes whose tradition isn't in active
#
# An explicit empty list at either level (default OR per-book) means
# "no tradition filter" — the §7.2 byte-identical guarantee is preserved
# whenever every book resolves to ∅.


def decode_per_book_traditions(raw) -> dict[str, list[str]]:
    """Decode the on-disk format for ``traditions_per_book``.

    Same indirection as ``decode_per_book_languages`` — flat list of
    ``"<book_code>=<t1>,<t2>"`` strings on disk because the project's
    custom YAML parser supports list fields but not nested mappings.
    Empty value (``"gen="``) is meaningful: "this book gets no
    tradition filter" (an explicit override of the default, distinct
    from absence-of-key which means "fall through to default").

    Accepts:
      - None / [] / {}  → {}
      - list[str]       → decoded
      - dict            → returned as-is (UI/JSON path)

    Returns ``{book_code: [tradition_id, …]}``.
    """
    if raw is None or raw == [] or raw == {}:
        return {}
    if isinstance(raw, dict):
        return {str(k): list(v or []) for k, v in raw.items()}
    out: dict[str, list[str]] = {}
    for entry in raw:
        if not isinstance(entry, str):
            continue
        if "=" not in entry:
            continue
        code, blob = entry.split("=", 1)
        code = code.strip()
        if not code:
            continue
        if not blob.strip():
            out[code] = []
            continue
        out[code] = [s.strip() for s in blob.split(",") if s.strip()]
    return out


def encode_per_book_traditions(per_book: dict[str, list[str]]) -> list[str]:
    """Inverse of decode_per_book_traditions — write the on-disk format.

    Output is sorted by canonical book order (Genesis → … → Revelation
    → Ethiopian tail) per CLAUDE_PROJECT_RULES.md §6.1, so editions.yaml
    diffs stay clean. Unknown tradition ids are filtered out — same
    defensive policy as decode, so the round trip is clean.
    """
    if not per_book:
        return []
    from scripts.core import config as _cfg
    from scripts.core.traditions import TRADITION_IDS

    book_order = list(_cfg.books_by_code().keys())
    rank = {code: i for i, code in enumerate(book_order)}

    def _sort_key(item):
        code = item[0]
        return (rank.get(code, len(book_order) + 1), code)

    out: list[str] = []
    for code, traditions in sorted(per_book.items(), key=_sort_key):
        traditions = list(traditions or [])
        clean = [t for t in traditions if t in TRADITION_IDS]
        out.append(f"{code}={','.join(clean)}")
    return out


def _resolve_traditions_for_book(edition: dict, book_code: str) -> set[str]:
    """Active tradition set for one (edition, book).

    Empty set means "no tradition filter for this book". Per-book
    overrides take precedence over the per-edition default; absence
    of an override falls through to the default.

    Unknown tradition ids are PRESERVED (not filtered out) — they
    simply won't match any note's tradition, which is the safer
    behaviour when editions.yaml contains a typo. The validator at
    the API layer is responsible for rejecting unknowns at write
    time; the build pipeline trusts whatever's on disk and lets a
    config bug yield "no notes survive" rather than silently
    "every note survives".
    """
    per_book = decode_per_book_traditions(edition.get("traditions_per_book"))
    raw = per_book[book_code] if book_code in per_book else (edition.get("traditions_default") or [])
    return {t for t in (raw or []) if isinstance(t, str)}


def compute_tradition_disabled_html_ref_ids(edition: dict) -> set[str]:
    """Phase ψ.8.2-A (+ ψ.8.4 per-book overrides) — return the set of
    HTML ref-ids whose note tradition isn't allowed for that note's
    book in this edition.

    Resolution is per-book: ``traditions_per_book[book]`` if set, else
    ``traditions_default``. Either resolving to an empty list means
    "no filter for that book" (every note survives — pre-ψ.8 behaviour
    per §7.2). When neither default nor any per-book entry is set, this
    short-circuits to an empty set without walking the corpus.

    The output set is unioned into ``disabled_html_ref_ids`` in
    ``build_one()``; ``filter_html()`` then strips the matching
    markers + asides. id format: ``ref-{prefix}{ch:02d}{vs:02d}{suffix}``.
    """
    has_default = bool(edition.get("traditions_default"))
    per_book = decode_per_book_traditions(edition.get("traditions_per_book"))
    if not has_default and not per_book:
        return set()

    out: set[str] = set()
    book_active_cache: dict[str, set[str]] = {}
    for ref_id, tradition, book_code in _iter_note_ref_traditions():
        active = book_active_cache.get(book_code)
        if active is None:
            active = _resolve_traditions_for_book(edition, book_code)
            book_active_cache[book_code] = active
        if not active:
            # No filter for this book — note survives.
            continue
        if tradition not in active:
            out.add(ref_id)
    return out


# ---- Phase ψ.37: time-traveling commentary filter ------------------
#
# Mirrors the ψ.8.2-A tradition filter shape. Editions can specify
# a `time_filter_ceiling: int | null` field. When set, every note whose
# source's circa-year is > ceiling — OR whose attribution has no
# catalogued year at all (User-original / paraphrase — "contemporary")
# — joins the disabled-ref-id set, so the EPUB ships only commentary
# that a reader in `ceiling` would have had.
#
# When `time_filter_ceiling` is None (the default), this short-circuits
# to an empty set — pre-ψ.37 builds stay byte-identical (§7.2).
#
# Source-year resolution: `scripts.core.source_dates.lookup_year` does
# a longest-prefix match against `content/source_dates.yaml`. See
# ψ.37-A for the data-model details.


def _iter_note_ref_attribution_years():
    """Walk every note tuple on disk and yield
    ``(ref_id, attribution_year_or_None, book_code)``.

    Used by ``compute_time_filtered_html_ref_ids``. Same iteration
    shape as ``_iter_note_ref_traditions`` — re-using that helper
    isn't an option because tradition resolution doesn't surface
    attribution, and we don't want to double the walk cost.
    """
    from scripts.core.notes_io import load_notes
    from scripts.core.source_dates import lookup_year

    books_idx = config.books_by_code()
    notes_dir = REPO_ROOT / "content" / "notes"
    for book_path in sorted(notes_dir.glob("*.py")):
        if book_path.stem == "__init__" or book_path.stem.startswith("_"):
            continue
        book_code = book_path.stem
        book = books_idx.get(book_code) or {}
        prefix = book.get("id_prefix")
        if not prefix:
            continue
        notes = load_notes(book_path) or []
        for tup in notes:
            if not isinstance(tup, tuple) or len(tup) < 9:
                continue
            ch = tup[0]
            vs = tup[1]
            suffix = tup[2] or ""
            attribution = tup[8] or ""
            try:
                ch_i = int(ch)
                vs_i = int(vs)
            except (TypeError, ValueError):
                continue
            ref_id = f"ref-{prefix}{ch_i:02d}{vs_i:02d}{suffix}"
            yield ref_id, lookup_year(attribution), book_code


def compute_time_filtered_html_ref_ids(edition: dict) -> set[str]:
    """Phase ψ.37-B — return the set of HTML ref-ids whose source's
    circa-year exceeds the edition's ``time_filter_ceiling``.

    When ``edition["time_filter_ceiling"]`` is None / absent / 0 /
    invalid: returns an empty set (no-op; pre-ψ.37 byte-identical build).

    When it's a positive int (e.g. 1900): walks every note, computes
    its attribution's circa-year via ``source_dates.lookup_year``, and
    adds the ref-id to the output set if EITHER:
      - the year is None (contemporary content like "User original" —
        a 1900 reader wouldn't have had it), OR
      - the year is strictly greater than the ceiling (e.g. an 1897
        Nave's Topical note dropped by a 1890 ceiling).

    Per CLAUDE_PROJECT_RULES §7.2, the "no-op when default" guarantee
    is preserved: an edition with no ``time_filter_ceiling`` produces
    the same EPUB as before this phase shipped.

    The output set is unioned into ``disabled_html_ref_ids`` in
    ``build_one()``; ``filter_html()`` then strips the matching
    markers + asides.
    """
    ceiling = edition.get("time_filter_ceiling")
    if not isinstance(ceiling, int) or ceiling <= 0:
        return set()

    out: set[str] = set()
    for ref_id, year, _book_code in _iter_note_ref_attribution_years():
        if year is None or year > ceiling:
            out.add(ref_id)
    return out


def build_ref_id_to_tradition_map(edition: dict) -> dict[str, str]:
    """Phase ψ.8.2-B (+ ψ.8.4) — ``{ref_id: tradition}`` for every note
    that survived the per-book tradition filter.

    Empty when no edition-level filter is active (no
    ``traditions_default`` and no ``traditions_per_book``). The build
    pipeline only runs the label-injection pass when this dict is
    non-empty, so pre-ψ.8 builds remain byte-identical (§7.2).
    """
    has_default = bool(edition.get("traditions_default"))
    per_book = decode_per_book_traditions(edition.get("traditions_per_book"))
    if not has_default and not per_book:
        return {}

    out: dict[str, str] = {}
    book_active_cache: dict[str, set[str]] = {}
    for ref_id, tradition, book_code in _iter_note_ref_traditions():
        active = book_active_cache.get(book_code)
        if active is None:
            active = _resolve_traditions_for_book(edition, book_code)
            book_active_cache[book_code] = active
        if not active:
            # No filter for this book — labelling would mean "every
            # tradition is allowed", which is essentially pre-ψ.8 build
            # behaviour for that book. Skip the label so default-on-no-
            # filter books don't pick up data-tradition attributes.
            continue
        if tradition in active:
            out[ref_id] = tradition
    return out


# Pattern that matches one ``<aside class="note note-X" id="note-…"``
# editorial-note element (the per-note popup, not the per-verse vnote).
# Captures: (1) full opening tag, (2) ref-id (the note-{full_id}), (3)
# inner body, (4) closing tag.
_NOTE_ASIDE_RE = re.compile(
    r'(<aside\s+class="note\s+note-[a-z][a-z0-9-]*"\s+id="(note-[^"]+)"[^>]*>)'
    r"(.*?)"
    r"(</aside>)",
    re.DOTALL,
)


def apply_tradition_labels_to_html(
    html_text: str,
    ref_id_to_tradition: dict[str, str],
) -> tuple[str, dict]:
    """Phase ψ.8.2-B — label every surviving editorial-note ``<aside>``
    with its tradition.

    For each ``<aside class="note note-X" id="note-…">…</aside>`` whose
    corresponding ref-id is in ``ref_id_to_tradition``, we:

      1. Add ``data-tradition="<tradition_id>"`` to the opening tag
         (after the existing ``id="…"`` attribute, so the canonical
         tradition CSS selector ``aside.note[data-tradition=…]`` works
         in any reader that supports CSS attribute selectors).
      2. Prepend a ``<p class="note-tradition-label">…</p>`` paragraph
         inside the aside body, carrying the canonical display label
         (e.g. ``"Catholic"``, ``"Cross-tradition"``).

    Both rewrites are skipped if the aside already carries a
    ``data-tradition`` attribute (idempotent — re-running this pass
    over already-labelled HTML is a no-op).

    Returns ``(new_html, stats)`` where ``stats = {"labeled": N,
    "skipped_already_labeled": M, "skipped_no_tradition": K}``.
    """
    from scripts.core.traditions import CANONICAL_TRADITIONS

    label_for = {tid: lbl for tid, lbl in CANONICAL_TRADITIONS}
    stats = {"labeled": 0, "skipped_already_labeled": 0, "skipped_no_tradition": 0}

    if not ref_id_to_tradition:
        return html_text, stats

    def _replace(m: re.Match) -> str:
        opening = m.group(1)
        note_id = m.group(2)  # "note-XXXX"
        body = m.group(3)
        closing = m.group(4)

        # ref-id (the marker) is the same suffix as note-id (the aside).
        ref_id = "ref-" + note_id[len("note-") :]

        tradition = ref_id_to_tradition.get(ref_id)
        if tradition is None:
            stats["skipped_no_tradition"] += 1
            return m.group(0)

        if "data-tradition=" in opening:
            stats["skipped_already_labeled"] += 1
            return m.group(0)

        display = label_for.get(tradition, tradition)

        # Inject data-tradition="…" right after the id="…" attribute so
        # the opening tag stays diff-friendly (existing attributes keep
        # their relative order; only one new attribute is added).
        new_opening = re.sub(
            r'(id="note-[^"]+")',
            rf'\1 data-tradition="{tradition}"',
            opening,
            count=1,
        )

        label_para = (
            f'\n  <p class="note-tradition-label" data-tradition-id="{tradition}">{_xml_escape_text(display)}</p>'
        )
        stats["labeled"] += 1
        return new_opening + label_para + body + closing

    new_html = _NOTE_ASIDE_RE.sub(_replace, html_text)
    return new_html, stats


def compute_enabled_kinds(edition: dict, all_kinds: list[dict]) -> tuple[set, set]:
    """Returns (enabled_codes, disabled_codes) for this edition.

    Delegates to the canonical resolver
    :func:`scripts.core.config.enabled_kind_codes` so the build and the matrix
    count grid never drift on "which kinds ship". ``disabled`` is the
    complement of ``enabled`` over ``all_kinds``.
    """
    from scripts.core.config import enabled_kind_codes

    enabled = enabled_kind_codes(edition, all_kinds)
    disabled = {k["code"] for k in all_kinds} - enabled
    return enabled, disabled


# ----------------------------------------------------------------------
# HTML filtering
# ----------------------------------------------------------------------


def _disable_vn_links(html_text: str) -> tuple[str, int]:
    """Convert clickable verse-number anchors to non-clickable spans.

    Each ``<a class="vn-link" id="v-foo-1-1" href="#vnote-foo-1-1"
    epub:type="noteref" title="…">…</a>`` becomes
    ``<span class="vn-link" id="v-foo-1-1" title="…">…</span>``.

    Preserves ``id`` (still useful as a deep-link target) and ``title``
    (accessibility / hover tooltip). Drops ``href`` + ``epub:type`` so
    the element is non-interactive in every EPUB reader (Kindle, Apple
    Books, Calibre, web readers) without requiring CSS or JS support.

    Returns (new_html, count_of_replacements).
    """
    # Match the whole anchor non-greedily — vn-link anchors wrap only
    # the verse number text, so the closing </a> is always the next one.
    tag_re = re.compile(
        r'<a\s+class="vn-link"([^>]*)>(.*?)</a>',
        re.DOTALL,
    )
    # Within the captured attribute string, pull out only the attrs we
    # want to preserve. Order-independent so we don't rely on the
    # current writer's specific attribute ordering.
    keep_attr_re = re.compile(r'\b(id|title)="([^"]*)"')

    count = 0

    def _repl(m):
        nonlocal count
        count += 1
        attrs_blob = m.group(1)
        inner = m.group(2)
        parts = ['<span class="vn-link"']
        for am in keep_attr_re.finditer(attrs_blob):
            parts.append(f' {am.group(1)}="{am.group(2)}"')
        parts.append(f">{inner}</span>")
        return "".join(parts)

    return tag_re.sub(_repl, html_text), count


# ---- Phase ν.2.5-B: verse-popup ENABLE side ------------------------
#
# IMPORTANT — the source HTML in epub_working/ already ships with
# <aside class="vnote" id="vnote-X-Y-Z" epub:type="footnote"> elements
# wired to every vn-link. Each existing vnote currently contains:
#   - a citation header   <p><strong>Genesis 4:1.</strong></p>
#   - the WEB English      <p class="vnote-text">…</p>
#   - the Hebrew (MT)      <p class="vnote-hebrew" dir="rtl" lang="he">…</p>
#   - the Greek (LXX)      <p class="vnote-greek" lang="grc">…</p>
#   - a back link
#
# The body text of every project EPUB is also WEB, so without ν.2.5-B
# the popup just repeats what the reader already sees in the body
# (plus the originals). The publisher's choice of `popup_translation`
# turns the popup into something useful: an alternate English rendering
# beside the originals (e.g. KJV alongside Hebrew & Greek for a
# Reformed edition).
#
# This phase REPLACES the vnote-text paragraph (English) with the
# chosen translation's text — never touches the Hebrew or Greek lines,
# never adds new asides, never deletes anything. Asides whose verse
# isn't present in the chosen translation are left untouched, so the
# reader still gets the WEB fallback.

# Pattern that matches a complete vnote aside element. Captures the
# opening tag (1), book code (2), chapter (3), verse (4), inner body
# (5), and closing tag (6) so we can rewrite just the inner body.
_VNOTE_ASIDE_RE = re.compile(
    r'(<aside\s+class="vnote"\s+id="vnote-([a-z0-9]+)-(\d+)-(\d+)"[^>]*>)'
    r"(.*?)"
    r"(</aside>)",
    re.DOTALL,
)

# The English-text paragraph inside a vnote aside. Replaced (not
# augmented) when popup_translation resolves to a real translation.
_VNOTE_TEXT_PARA_RE = re.compile(
    r'<p\s+class="vnote-text">.*?</p>',
    re.DOTALL,
)


def _xml_escape_text(s: str) -> str:
    """Escape verse text for safe inclusion in EPUB XHTML.

    The only characters we need to neutralize are ``&``, ``<``, ``>``;
    quote characters can pass through because they only appear inside
    plain text in XHTML, never inside attribute values here.
    """
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _replace_verse_popup_translation(
    html_text: str,
    translation_id: str,
    translation_short: str = "",
) -> tuple[str, dict]:
    """Swap the English text inside every vnote aside with text from
    ``translation_id`` (Phase ν.2.5-B).

    Each existing aside's ``<p class="vnote-text">…</p>`` is rewritten
    to be preceded by a source label and contain the chosen
    translation's verse. The Hebrew, Greek, citation header, and back
    link are left untouched.

    Behavior on missing data is **always graceful**:
      · verse not in this translation     → leave the whole aside as-is
        (reader sees the existing WEB text; they don't see a broken
        popup)
      · aside has no vnote-text paragraph  → leave the whole aside as-is
        (probably an unusual entry; never silently lose content)

    Returns (new_html, stats) where stats includes:
      - replaced: asides whose English text was swapped to the new
                  translation
      - missed:   asides skipped because the chosen translation lacks
                  that verse (Ethiopian-only books, gaps, etc.)
      - skipped_no_text_para: asides skipped because their body didn't
                  contain a vnote-text element to swap
    """
    from scripts.core import translations as _tx

    stats = {"replaced": 0, "missed": 0, "skipped_no_text_para": 0}
    short_label = translation_short or translation_id.upper()

    def _replace(m: re.Match) -> str:
        opening = m.group(1)
        book = m.group(2)
        ch = int(m.group(3))
        vs = int(m.group(4))
        body = m.group(5)
        closing = m.group(6)

        verse_text = _tx.get_verse(translation_id, book, ch, vs)
        if verse_text is None:
            stats["missed"] += 1
            return m.group(0)

        # Build the replacement: a source-label paragraph (matching the
        # existing Hebrew/Greek label style) immediately followed by the
        # new vnote-text paragraph carrying the chosen translation.
        new_para = (
            f'<p class="vnote-source-label">English ({_xml_escape_text(short_label)})</p>'
            f'<p class="vnote-text">{_xml_escape_text(verse_text)}</p>'
        )
        new_body, n = _VNOTE_TEXT_PARA_RE.subn(new_para, body, count=1)
        if n == 0:
            stats["skipped_no_text_para"] += 1
            return m.group(0)

        stats["replaced"] += 1
        return opening + new_body + closing

    new_html = _VNOTE_ASIDE_RE.sub(_replace, html_text)
    return new_html, stats


# ---- Phase ν.2.7-A: per-book popup-language toggle -----------------
#
# Each edition can specify which popup languages to show, with two
# levels of resolution:
#
#   popup_languages_default      list[str]   per-edition default
#   popup_languages_per_book     dict[code → list[str]]    overrides
#
# Resolution at build time:
#   languages = per_book.get(book) or default or ALL_LANGUAGES
#
# When a language is NOT in the resolved set, both its source-label
# paragraph and its content paragraph are stripped from the aside.
# Stripping is conservative — only paragraphs whose CSS class matches
# a known language are removed; everything else (citation header,
# back-link, custom annotations) survives.

# Map language id → (label-prefix-regex, content-class).
# Each entry teaches the stripper what to remove for that language.
# - LABEL_PREFIX_RE matches the source-label paragraph that immediately
#   precedes the content paragraph. We use a regex on the visible text
#   inside the label so we tolerate small formatting variations.
# - CONTENT_CLASS is the literal CSS class the content paragraph carries.
#
# Adding a future language is just one new entry here plus source data
# in the HTML; no other code change.
POPUP_LANGUAGES: dict[str, dict] = {
    "english": {
        "label": "English",
        "content_class": "vnote-text",
        "has_label_para": False,  # only after τ.1.5 swap; original has no label
    },
    "hebrew": {
        "label": "Hebrew",
        "content_class": "vnote-hebrew",
        "has_label_para": True,
    },
    "greek": {
        "label": "Greek",
        "content_class": "vnote-greek",
        "has_label_para": True,
    },
    # Future, no source data yet — declared so the schema validator
    # accepts them and the stripper handles them gracefully when the
    # data eventually lands.
    "aramaic": {"label": "Aramaic", "content_class": "vnote-aramaic", "has_label_para": True},
    "geez": {"label": "Ge'ez", "content_class": "vnote-geez", "has_label_para": True},
    "latin": {"label": "Latin", "content_class": "vnote-latin", "has_label_para": True},
    "coptic": {"label": "Coptic", "content_class": "vnote-coptic", "has_label_para": True},
    "syriac": {"label": "Syriac", "content_class": "vnote-syriac", "has_label_para": True},
    # Π.0 (2026-05-14) — parallel-Bible expansion preparation.
    # Amharic is the modern liturgical language of the EOTC alongside
    # Ge'ez (classical). The Tewahedo Bible is printed in modern
    # parallel-Ge'ez-Amharic editions (e.g. the 2,539-page EOTC FULL
    # BIBLE that drives the τ.6.x / τ.7.x ingest in this expansion).
    # Same script family as Ge'ez (Ethiopic Unicode block U+1200-U+137F,
    # LTR, no RTL handling needed). Style class .vnote-amharic mirrors
    # .vnote-geez's CSS in apply_style.py.
    "amharic": {"label": "Amharic", "content_class": "vnote-amharic", "has_label_para": True},
}

# B1: fold in the shared version registry (scripts/core/popup_versions.py) so the
# build side and the bake share ONE source of truth for the multi-translation
# popups. The legacy language ids above (english/hebrew/greek) alias to the
# version ids (kjv/wlc/lxx-greek) in _resolve_popup_languages; the parallel-bible
# / future-language slots above (latin/geez/amharic/aramaic/coptic/syriac) are
# preserved untouched, so anglican-bcp + the standalone bibles don't regress.
from scripts.core import popup_versions as _pv  # noqa: E402

POPUP_LANGUAGES.update(
    {
        vid: {
            "label": s["label"],
            "content_class": s["content_class"],
            "has_label_para": s["has_label_para"],
        }
        for vid, s in _pv.VERSION_REGISTRY.items()
    }
)
# english/hebrew/greek stay as known ids (so save-validation still accepts them
# + _resolve maps them to kjv/wlc/lxx-greek). They SHARE content classes with
# those version ids; the stripper keys on content class (below) so an active
# version is never stripped via its alias.

ALL_POPUP_LANGUAGES: tuple[str, ...] = tuple(POPUP_LANGUAGES.keys())


def _resolve_popup_languages(edition: dict, book_code: str) -> set[str]:
    """Resolve the active popup-language set for one (edition, book).

    Order:
      1. popup_languages_per_book[book_code]   if present
      2. popup_languages_default               if present
      3. all known languages                   (back-compat default)

    Returns a set of language ids — only ids in POPUP_LANGUAGES are
    retained; unknown ids are silently dropped (publisher typo or a
    language we haven't registered yet).
    """
    per_book = decode_per_book_languages(edition.get("popup_languages_per_book"))
    raw: list[str] | None
    if book_code in per_book:
        raw = per_book[book_code]
    elif edition.get("popup_languages_default") is not None:
        raw = edition.get("popup_languages_default")
    else:
        return set(ALL_POPUP_LANGUAGES)
    # Map legacy language ids (english/hebrew/greek) to version ids
    # (kjv/wlc/lxx-greek); registry ids + legacy slots resolve to themselves.
    mapped = ((_pv.resolve_version_id(lang) or lang) for lang in (raw or []))
    return {m for m in mapped if m in POPUP_LANGUAGES}


def decode_per_book_languages(raw) -> dict[str, list[str]]:
    """Decode the on-disk format for ``popup_languages_per_book``.

    On-disk format is a flat list of ``"<book_code>=<lang1>,<lang2>"``
    strings. This indirection exists because the project's custom YAML
    parser (scripts.core.config._parse_yaml_records) supports list
    fields but not nested mappings; a flat list keeps editions.yaml
    legible AND parseable without expanding the parser surface.

    Empty value (``"tob="``) is meaningful — it means "this book gets
    no popup languages at all" (an explicit override of the default,
    distinct from absence-of-key which means "fall through to default").

    Accepts:
      - None            → {}
      - empty list      → {}
      - list[str]       → decoded
      - dict (already decoded, e.g. from a JSON API payload) → returned as-is

    Returns ``{book_code: [lang_id, …]}``.
    """
    if raw is None or raw == [] or raw == {}:
        return {}
    if isinstance(raw, dict):
        # Already decoded — JSON payload from the UI, or PyYAML-loaded data
        return {str(k): list(v or []) for k, v in raw.items()}
    out: dict[str, list[str]] = {}
    for entry in raw:
        if not isinstance(entry, str):
            continue
        if "=" not in entry:
            # Treat a bare book code as "no overrides" — equivalent to
            # absence, so skip it. (Defensive against publisher typos.)
            continue
        code, langs_blob = entry.split("=", 1)
        code = code.strip()
        if not code:
            continue
        if not langs_blob.strip():
            out[code] = []
            continue
        out[code] = [s.strip() for s in langs_blob.split(",") if s.strip()]
    return out


def encode_per_book_languages(per_book: dict[str, list[str]]) -> list[str]:
    """Inverse of decode_per_book_languages.

    Used by the UI/API write path to turn a JSON dict into the on-disk
    list format. Output is sorted by canonical book order — which is
    Book/Chapter order per project rules (see CLAUDE_PROJECT_RULES.md
    §6.1) — so editions.yaml diffs stay clean and predictable.
    """
    if not per_book:
        return []
    # Lazy import here to avoid a circular dep when this module is
    # loaded by core/config-adjacent code at startup.
    from scripts.core import config as _cfg

    book_order = list(_cfg.books_by_code().keys())
    rank = {code: i for i, code in enumerate(book_order)}

    def _sort_key(item):
        code = item[0]
        return (rank.get(code, len(book_order) + 1), code)

    out: list[str] = []
    for code, langs in sorted(per_book.items(), key=_sort_key):
        langs = list(langs or [])
        # Filter unknown ids on write — same defensive policy as read,
        # so the round trip is clean.
        clean = [L for L in langs if L in POPUP_LANGUAGES]
        out.append(f"{code}={','.join(clean)}")
    return out


def _strip_language_paragraph(body: str, lang_id: str) -> tuple[str, int]:
    """Remove one language's paragraphs (label + content) from a vnote
    aside body. Returns (new_body, paragraphs_removed).

    Both the source-label paragraph (if any) and the content paragraph
    are removed together. We match them as one chunk so we don't leave
    an orphan label behind if the content is absent.
    """
    spec = POPUP_LANGUAGES.get(lang_id)
    if not spec:
        return body, 0

    content_class = re.escape(spec["content_class"])
    removed = 0

    # First pass: label paragraph followed by content paragraph (when
    # the label is present, e.g. Hebrew/Greek). We require the label
    # to be the immediately preceding paragraph so we don't accidentally
    # strip a label that belongs to a different language.
    if spec["has_label_para"]:
        pat = re.compile(
            r'\s*<p\s+class="vnote-source-label">[^<]*</p>'
            rf'\s*<p\s+class="{content_class}"[^>]*>.*?</p>',
            re.DOTALL,
        )
        body, n1 = pat.subn("", body)
        removed += n1

    # Second pass: any remaining content paragraph for this language
    # without a preceding label (e.g. the original WEB vnote-text
    # before the τ.1.5 swap added a label). This also catches edge
    # cases where label/content got separated by other markup.
    pat2 = re.compile(
        rf'\s*<p\s+class="{content_class}"[^>]*>.*?</p>',
        re.DOTALL,
    )
    body, n2 = pat2.subn("", body)
    removed += n2

    return body, removed


def _apply_popup_languages_and_translation(
    html_text: str,
    edition: dict,
    translation_id: str,
    translation_short: str,
) -> tuple[str, dict]:
    """Single pass over every vnote aside that does BOTH:

      1. (ν.2.5-B) Replace the English vnote-text paragraph with text
         from the chosen translation, when ``translation_id`` is set.
      2. (ν.2.7-A) Strip language paragraphs for any language NOT in
         the resolved popup-language set for this aside's book.

    Doing both in one pass means we walk the HTML once per file even
    when both features are active. Stats from both phases are merged
    into a single dict so build_one needs only one accumulator.
    """
    from scripts.core import translations as _tx

    stats = {
        "replaced": 0,
        "missed": 0,
        "skipped_no_text_para": 0,
        "language_paragraphs_stripped": 0,
        "asides_seen": 0,
    }
    short_label = translation_short or (translation_id.upper() if translation_id else "")

    def _process(m: re.Match) -> str:
        opening = m.group(1)
        book = m.group(2)
        ch = int(m.group(3))
        vs = int(m.group(4))
        body = m.group(5)
        closing = m.group(6)

        stats["asides_seen"] += 1
        active_langs = _resolve_popup_languages(edition, book)

        # Step 1 — translation swap (only if english is active, the
        # translation is set, and the verse exists in it). When
        # english is being stripped we never bother fetching.
        # 'kjv' is the resolved version id for the English slot (legacy
        # 'english' aliases to it); the swap targets that vnote-text paragraph.
        if translation_id and "kjv" in active_langs:
            verse_text = _tx.get_verse(translation_id, book, ch, vs)
            if verse_text is not None:
                new_para = (
                    f'<p class="vnote-source-label">'
                    f"English ({_xml_escape_text(short_label)})</p>"
                    f'<p class="vnote-text">'
                    f"{_xml_escape_text(verse_text)}</p>"
                )
                new_body, n = _VNOTE_TEXT_PARA_RE.subn(
                    new_para,
                    body,
                    count=1,
                )
                if n:
                    body = new_body
                    stats["replaced"] += 1
                else:
                    stats["skipped_no_text_para"] += 1
            else:
                stats["missed"] += 1

        # Step 2 — strip versions whose content class is NOT shown by any active
        # version. Keying on content class (not id) means a legacy alias sharing
        # a class with an active version id (english↔kjv → vnote-text) is never
        # stripped out from under the active version.
        active_classes = {POPUP_LANGUAGES[v]["content_class"] for v in active_langs if v in POPUP_LANGUAGES}
        for lang_id in ALL_POPUP_LANGUAGES:
            if POPUP_LANGUAGES[lang_id]["content_class"] in active_classes:
                continue
            body, n = _strip_language_paragraph(body, lang_id)
            stats["language_paragraphs_stripped"] += n

        return opening + body + closing

    new_html = _VNOTE_ASIDE_RE.sub(_process, html_text)
    return new_html, stats


def filter_html(
    html_text: str, disabled_kinds: set, disabled_html_ref_ids: set | None = None, verse_popups_enabled: bool = True
) -> tuple[str, dict]:
    """Strip note markers + asides whose kind is disabled OR whose ref-id is
    in the per-edition disabled-notes set. Returns (new_html, counts).

    disabled_html_ref_ids: set of HTML IDs like {"ref-g0101a", "ref-m0503b"}
    that correspond to individual notes the edition has turned off.

    verse_popups_enabled: when False, all ``<a class="vn-link" …>`` verse-
    number anchors are converted to non-clickable ``<span>`` elements
    (Phase ν.2.5-A — honors the flag from editions.yaml). Default True
    leaves the EPUB unchanged, preserving every prior build's bytes.
    """
    counts = {"markers": 0, "asides": 0, "id_markers": 0, "id_asides": 0, "vn_links_disabled": 0}
    new_text = html_text

    # ---- Phase λ: filter by KIND (whole categories of notes)
    for kind in disabled_kinds:
        marker_re = re.compile(
            rf'<a class="note-ref note-{re.escape(kind)}"[^>]*>.*?</a>',
            re.DOTALL,
        )
        new_text, n = marker_re.subn("", new_text)
        counts["markers"] += n

        aside_re = re.compile(
            rf'<aside class="note note-{re.escape(kind)}"[^>]*>.*?</aside>',
            re.DOTALL,
        )
        new_text, n = aside_re.subn("", new_text)
        counts["asides"] += n

    # ---- Phase ρ.1: filter by individual note ID
    if disabled_html_ref_ids:
        for ref_id in disabled_html_ref_ids:
            # Inline marker: <a class="note-ref note-<kind>" id="ref-XXXX" ...>...</a>
            m_re = re.compile(
                rf'<a class="note-ref [^"]*" id="{re.escape(ref_id)}"[^>]*>.*?</a>',
                re.DOTALL,
            )
            new_text, n = m_re.subn("", new_text)
            counts["id_markers"] += n
            # Aside: <aside class="note note-<kind>" id="note-XXXX" ...>...</aside>
            #   (note: marker IDs are "ref-..." but aside IDs are "note-...")
            note_id = ref_id.replace("ref-", "note-", 1)
            a_re = re.compile(
                rf'<aside class="note [^"]*" id="{re.escape(note_id)}"[^>]*>.*?</aside>',
                re.DOTALL,
            )
            new_text, n = a_re.subn("", new_text)
            counts["id_asides"] += n

    # ---- Phase ν.2.5-A: honor verse_popups=false by stripping vn-link
    # clickability. Subtractive — when the flag is on (the default),
    # nothing here runs and the EPUB is byte-identical to prior builds.
    if not verse_popups_enabled:
        new_text, n = _disable_vn_links(new_text)
        counts["vn_links_disabled"] = n

    return new_text, counts


# ----------------------------------------------------------------------
# OPF patching
# ----------------------------------------------------------------------


def _resolve_publishing(edition: dict) -> dict:
    """Resolve the publishing metadata for an edition, filling defaults
    for any field the user hasn't set yet (Phase π.2). The defaults match
    the `PUBLISHING_DEFAULTS` dict in web.py so the /publisher UI and the
    build pipeline agree on what an unset edition looks like.
    """
    now_year = datetime.now(timezone.utc).year
    now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    defaults = {
        "publisher_name": "Independent",
        "publisher_url": "",
        "copyright_year": str(now_year),
        "copyright_holder": "",
        "copyright_notice": "All rights reserved.",
        "publication_date": now_date,
        "language_code": "en",
        "cover_credit": "",
        "source_text_credit": "Scripture text based on the World English Bible (public domain).",
    }
    out = {}
    for k, v in defaults.items():
        out[k] = edition.get(k) or v
    out["authors"] = list(edition.get("authors") or [])
    out["bisac_codes"] = list(edition.get("bisac_codes") or [])
    return out


def _xml_escape(s: str) -> str:
    """Escape a string for safe inclusion in XML text or attribute."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _parse_author(author_str: str) -> tuple[str, str]:
    """Parse an author entry stored as 'Name (role)'.

    Returns (name, marc_relator_code). Defaults to 'aut' (author) when no
    role given. Common MARC relator codes:
      aut = author       edt = editor       trl = translator
      ill = illustrator  fwd = author of foreword
      pbl = publisher    com = compiler
    """
    s = author_str.strip()
    role_map = {
        "author": "aut",
        "aut": "aut",
        "editor": "edt",
        "edt": "edt",
        "translator": "trl",
        "trl": "trl",
        "illustrator": "ill",
        "ill": "ill",
        "foreword": "fwd",
        "fwd": "fwd",
        "compiler": "com",
        "com": "com",
        "introduction": "win",
        "win": "win",
        "preface": "win",
        "afterword": "aft",
        "aft": "aft",
    }
    m = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", s)
    if m:
        name = m.group(1).strip()
        role_word = m.group(2).strip().lower()
        return name, role_map.get(role_word, "aut")
    return s, "aut"


def patch_opf(opf_text: str, edition: dict, version: str) -> str:
    """Update OPF title + add edition-identifying metadata, accessibility
    declarations (WCAG 2.1 AA), BCP-47 language tags for cross-script content,
    and optional DOI/LCSH identifiers for distribution-channel coverage.

    Phase π.2: also reads the per-edition publishing block (publisher_name,
    copyright_*, authors, bisac_codes) and injects those into the EPUB's
    Dublin-Core metadata. Ω.0 pivot: ISBN fields dropped — see
    SCOPE_2026-05-14-omega0-free-public-pivot.md.
    """
    title = edition.get("title", "Ethiopian Bible")
    pub = _resolve_publishing(edition)

    new_text = re.sub(
        r"<dc:title>[^<]*</dc:title>",
        f"<dc:title>{_xml_escape(title)}</dc:title>",
        opf_text,
        count=1,
    )

    # Replace <dc:publisher> with the configured imprint
    new_text = re.sub(
        r"<dc:publisher>[^<]*</dc:publisher>",
        f"<dc:publisher>{_xml_escape(pub['publisher_name'])}</dc:publisher>",
        new_text,
        count=1,
    )

    # Replace <dc:date> with publication_date
    new_text = re.sub(
        r"<dc:date>[^<]*</dc:date>",
        f"<dc:date>{_xml_escape(pub['publication_date'])}</dc:date>",
        new_text,
        count=1,
    )

    # Replace <dc:creator> + role with the FIRST author from authors list,
    # or fall back to publisher_name. Additional authors become contributors.
    primary_author = "Public Domain"
    primary_role = "aut"
    additional = []
    for a in pub["authors"]:
        name, role = _parse_author(a)
        if not primary_author or primary_author == "Public Domain":
            primary_author = name
            primary_role = role
        else:
            additional.append((name, role))
    if not pub["authors"] and pub["publisher_name"] != "Independent":
        # No explicit authors — use the publisher itself as creator
        primary_author = pub["publisher_name"]
        primary_role = "pbl"

    new_text = re.sub(
        r'<dc:creator id="creator">[^<]*</dc:creator>',
        f'<dc:creator id="creator">{_xml_escape(primary_author)}</dc:creator>',
        new_text,
        count=1,
    )
    new_text = re.sub(
        r'(<meta refines="#creator" property="role" scheme="marc:relators">)[^<]*(</meta>)',
        rf"\g<1>{primary_role}\g<2>",
        new_text,
        count=1,
    )
    new_text = re.sub(
        r'(<meta refines="#creator" property="file-as">)[^<]*(</meta>)',
        rf"\g<1>{_xml_escape(primary_author)}\g<2>",
        new_text,
        count=1,
    )

    # Refine the primary dc:language to BCP-47 'en-US' when it's bare 'en'.
    # Multiple dc:language entries declare languages PRESENT in the work
    # for cross-script content (Hebrew, Greek, Aramaic, Ge'ez transliterations
    # in editorial notes). EPUB 3 permits multiple dc:language elements.
    primary_lang = pub["language_code"] or "en"
    bcp47 = primary_lang if "-" in primary_lang else f"{primary_lang}-US"
    new_text = re.sub(
        r"<dc:language>en</dc:language>",
        (
            f"<dc:language>{_xml_escape(bcp47)}</dc:language>\n"
            "    <dc:language>hbo</dc:language>"
            "<!-- Biblical Hebrew (transliterations + script in lang-* notes) -->\n"
            "    <dc:language>grc</dc:language>"
            "<!-- Koine Greek -->\n"
            "    <dc:language>arc</dc:language>"
            "<!-- Aramaic -->\n"
            "    <dc:language>gez</dc:language>"
            "<!-- Ge'ez (Ethiopian liturgical) -->"
        ),
        new_text,
        count=1,
    )

    # Ω.0 pivot (2026-05-14): ISBN dropped. EPUB 3 dc:identifier
    # requirement is met via a generator URN tied to the edition id
    # (urn:yhwh:edition:<id>) — no commercial registration.
    edition_urn = f"urn:yhwh:edition:{edition['id']}"

    # Build the additional contributor block (authors beyond the primary)
    contributor_meta = ""
    for i, (name, role) in enumerate(additional):
        cid = f"contributor-{i + 2}"  # the existing one is "contributor"
        contributor_meta += (
            f'    <dc:contributor id="{cid}">{_xml_escape(name)}</dc:contributor>\n'
            f'    <meta refines="#{cid}" property="role" scheme="marc:relators">{role}</meta>\n'
            f'    <meta refines="#{cid}" property="file-as">{_xml_escape(name)}</meta>\n'
        )

    # Build the rights block from copyright fields
    rights_text = pub["copyright_notice"]
    if pub["copyright_year"] or pub["copyright_holder"]:
        rights_text = (
            f"Copyright © {pub['copyright_year']} {pub['copyright_holder']}. {pub['copyright_notice']}"
        ).strip()
    rights_meta = f"    <dc:rights>{_xml_escape(rights_text)}</dc:rights>\n"

    # Build BISAC subjects (in addition to the LCSH subjects below)
    bisac_meta = ""
    for code in pub["bisac_codes"]:
        # EPUB3: a subject with property="authority" MUST be paired with a
        # property="term" refining the same dc:subject id, else epubcheck
        # RSC-005 ("A term property must be associated with a dc:subject when
        # an authority is specified"). Emit both, refining the bisac- id.
        esc = _xml_escape(code)
        bisac_meta += (
            f'    <dc:subject id="bisac-{esc}">{esc}</dc:subject>\n'
            f'    <meta refines="#bisac-{esc}" property="authority">BISAC</meta>\n'
            f'    <meta refines="#bisac-{esc}" property="term">{esc}</meta>\n'
        )

    # WCAG 2.1 AA accessibility declarations + BCP-47 + DOI placeholder + LCSH
    edition_meta = (
        f'    <meta property="dcterms:isVersionOf">'
        f"ethiopian-bible-master/{version}</meta>\n"
        f'    <meta property="dcterms:variant">{edition["id"]}</meta>\n'
        # Rights (Phase π.2)
        + rights_meta
        # Additional contributors (Phase π.2)
        + contributor_meta
        # Ω.0 pivot: generator URN replaces the former ISBN identifier.
        # Deterministic per edition id; not a commercial identifier.
        + f'    <dc:identifier id="pub-id">{_xml_escape(edition_urn)}</dc:identifier>\n'
        # DOI hook (TODO_DOI when academic distribution registered)
        f'    <dc:identifier id="doi">urn:doi:TODO_DOI_HERE</dc:identifier>\n'
        f'    <meta refines="#doi" property="identifier-type" scheme="onix:codelist5">06</meta>\n'
        # LCCN hook (Library of Congress Control Number — assigned via PCN
        # program when registered with LoC; standardises academic catalog
        # discovery)
        f'    <dc:identifier id="lccn">urn:lccn:TODO_LCCN_HERE</dc:identifier>\n'
        f'    <meta refines="#lccn" property="identifier-type" scheme="onix:codelist5">13</meta>\n'
        # BISAC subjects from publishing block (Phase π.2)
        + bisac_meta
        # LCSH subject classifications
        + "    <dc:subject>Bible -- Commentaries</dc:subject>\n"
        "    <dc:subject>Bible. Old Testament -- Commentaries</dc:subject>\n"
        "    <dc:subject>Bible. New Testament -- Commentaries</dc:subject>\n"
        "    <dc:subject>Ethiopian Orthodox Tewahedo Church -- Doctrines</dc:subject>\n"
        # WCAG 2.1 Level AA conformance declarations
        '    <link rel="dcterms:conformsTo" '
        'href="http://www.idpf.org/epub/a11y/accessibility-20170105.html#wcag-aa"/>\n'
        '    <meta property="a11y:certifiedBy">TODO_CERTIFIER_NAME</meta>\n'
        '    <meta property="schema:accessMode">textual</meta>\n'
        '    <meta property="schema:accessMode">visual</meta>\n'
        '    <meta property="schema:accessModeSufficient">textual</meta>\n'
        '    <meta property="schema:accessibilityFeature">tableOfContents</meta>\n'
        '    <meta property="schema:accessibilityFeature">readingOrder</meta>\n'
        '    <meta property="schema:accessibilityFeature">structuralNavigation</meta>\n'
        '    <meta property="schema:accessibilityFeature">alternativeText</meta>\n'
        '    <meta property="schema:accessibilityFeature">unlocked</meta>\n'
        '    <meta property="schema:accessibilityHazard">none</meta>\n'
        '    <meta property="schema:accessibilityAPI">ARIA</meta>\n'
        '    <meta property="schema:accessibilitySummary">'
        "This publication conforms to WCAG 2.1 Level AA. It includes a structured "
        "table of contents, semantic reading order, structural navigation by book and "
        "chapter, alt text on the cover image, and BCP-47 language tags for the "
        "cross-script content (Hebrew, Greek, Aramaic, Ge\u2019ez transliterations). "
        "There are no known accessibility hazards. The text is unlocked (no DRM)."
        "</meta>\n"
        '    <meta property="schema:typicalAgeRange">18-</meta>\n'
    )
    new_text = re.sub(
        r"</metadata>",
        edition_meta + "  </metadata>",
        new_text,
        count=1,
    )

    # EPUB 3 spec: cover image must declare properties="cover-image" so
    # readers can extract it for thumbnails. The legacy <meta name="cover"/>
    # alone is not sufficient. Apple Books treats this as a soft fail.
    new_text = re.sub(
        r'<item id="cover" href="cover\.jpeg" media-type="image/jpeg"/>',
        '<item id="cover" href="cover.jpeg" media-type="image/jpeg" properties="cover-image"/>',
        new_text,
        count=1,
    )

    return new_text


# ----------------------------------------------------------------------
# Build orchestrator
# ----------------------------------------------------------------------


def render_copyright_page(edition: dict, defaults: dict, version: str) -> str:
    """Render an XHTML copyright/credits page for a given edition.

    Pulls per-edition data (title, BISAC) from the edition record and
    project-wide data (publisher, contributor, copyright year) from the
    project defaults. TODO_* placeholders are left visible — they're
    flagged by ship-check until filled in. Ω.0 pivot (2026-05-14):
    ISBN removed; the copyright page now identifies the edition by its
    URN (urn:yhwh:edition:<id>) instead.
    """
    pub = defaults.get("publisher", "TODO_PUBLISHER_NAME")
    contributor = defaults.get("contributor", {}).get("name", "TODO_CONTRIBUTOR_FULL_NAME")
    cyear = defaults.get("copyright_year", "TODO_YYYY")
    pdate = defaults.get("publication_date", "TODO_YYYYMMDD")
    edition_title = edition.get("title_full", edition.get("title", "Untitled"))
    edition_subtitle = edition.get("title_subtitle", "")
    edition_urn = f"urn:yhwh:edition:{edition['id']}"
    description = (edition.get("description", "") or "").strip()
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head>
  <title>Copyright &amp; Credits</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
  <link rel="stylesheet" type="text/css" href="stylesheet.css"/>
</head>
<body epub:type="copyright-page">
  <section class="copyright-page" epub:type="copyright-page">
    <h1 class="copyright-title">{edition_title}</h1>
    {f'<p class="copyright-subtitle">{edition_subtitle}</p>' if edition_subtitle else ""}

    <hr class="copyright-rule"/>

    <p class="copyright-compiler">Compiled and annotated by <strong>{contributor}</strong>.</p>

    <h2 class="copyright-heading">Sources</h2>
    <p>Biblical text: <strong>World English Bible</strong> (Public Domain), released by Rainbow Missions, Inc.</p>
    <p>Hebrew lexicon: <strong>Strong's Exhaustive Concordance</strong>, James Strong, 1890 (Public Domain).</p>
    <p>Cross-references: <strong>Treasury of Scripture Knowledge</strong>, R. A. Torrey, 1834 (Public Domain).</p>
    <p>Patristic, rabbinic, and reformation-era commentary cited in editorial notes is drawn from public-domain sources whose authors died more than 95 years prior. Per-note attribution is preserved in the apparatus.</p>

    <h2 class="copyright-heading">Editorial Apparatus</h2>
    <p>Editorial notes, selection, arrangement, and presentation: &#169; {cyear} {pub}. All rights reserved.</p>
    <p>The 1,371 annotations across 14 categories — including the Andemta-tradition references, cross-canon parallels, Hebrew/Greek/Ge'ez linguistic notes, and theological synthesis — represent original editorial work. Quotation of more than fifty consecutive words from any single annotation for commercial purposes requires written permission of the copyright holder.</p>

    <h2 class="copyright-heading">This Edition</h2>
    <p><strong>Edition ID:</strong> {edition_urn}</p>
    <p><strong>Publisher:</strong> {pub}</p>
    <p><strong>Build:</strong> {version}</p>
    <p><strong>Publication date:</strong> {pdate}</p>

    {f'<h2 class="copyright-heading">About</h2><p>{description}</p>' if description else ""}

    <hr class="copyright-rule"/>

    <p class="copyright-disclaimer">This work is provided without warranty of any kind. The compiler makes no representation regarding the doctrinal positions of any tradition referenced in the editorial apparatus; cross-tradition synthesis is descriptive, not prescriptive.</p>

    <p class="copyright-trademark"><em>"Ethiopian Tewahedo" is descriptive of the Ethiopian Orthodox Tewahedo Church and its canonical tradition; this edition is not affiliated with or endorsed by the Ethiopian Orthodox Tewahedo Church unless explicitly stated.</em></p>
  </section>
</body>
</html>
"""


# ----------------------------------------------------------------------
# Phase ν.6 — Reader experience customization
# ----------------------------------------------------------------------
#
# Surface previously-developer-only knobs (chapter number format, TOC
# collapse, etc.) as per-edition options. Body chapter headings are
# rewritten during the per-edition build; TOC dropdown preference is
# stored on the edition for future per-edition apply_style work.
#
# The body chapter heading markup is:
#     <span class="bold-num">42</span>
# inside a `<p class="ch-heading">`. We rewrite the inner text to
# match `chapter_number_format` and wrap it per
# `chapter_number_decoration`.

# Names follow the pattern <FAMILY>_<VARIANT>; values match the
# "format" / "decoration" string values stored in editions.yaml.
CHAPTER_NUMBER_FORMATS = {
    "digit",  # 42
    "word",  # Forty-Two
    "word_chapter",  # Chapter Forty-Two
}
CHAPTER_NUMBER_DECORATIONS = {
    "plain": ("", ""),
    "dashes": ("— ", " —"),
    "em_dashes": ("———— ", " ————"),
    "stars": ("✦ ", " ✦"),
    "asterisks": ("**** ", " ****"),
    "bullets": ("• • • ", " • • •"),
    "ornament": ("❦ ", " ❦"),
    "fleurons": ("❧ ", " ❧"),
    "wave": ("～ ", " ～"),
    "double_lines": ("══ ", " ══"),
}

# Phase ν.6.1 — book ToC ornaments. Small visual marker that
# precedes each book name in the in-book Table of Contents. Picked
# per edition by the publisher; build-pipeline rendering is queued
# for a follow-up phase (matches the deferral pattern of
# reader_toc_collapsible / reader_toc_default_open).
#
# Each entry is (preview_glyph, description). `preview_glyph` is what
# the /customize select shows in its option label so the publisher
# sees what they'll get without leaving the page; `description` is
# the long-form name used in tooltips and the api_customize_data
# response.
#
# Design choices documented:
#   - "none" is the default (back-compat — existing ToCs render
#     byte-identically with this setting)
#   - "cross_latin" / "cross_lalibela" / "star_david" each map to a
#     specific tradition; the publisher picks the appropriate one
#     for their SKU. Putting a cross in a Jewish edition's ToC is a
#     trivial, costly mistake; the registry lets the publisher self-
#     select rather than the platform guessing
#   - The Lalibela cross uses U+2719 (OUTLINED GREEK CROSS) as a
#     unicode placeholder; the build-pipeline phase will replace
#     this with a proper SVG so Ethiopian editions look right
BOOK_TOC_ORNAMENTS = {
    "none": ("", "no ornament (classic)"),
    "square": ("▪", "small filled square"),
    "cross_latin": ("✝", "Latin cross (Catholic / Reformed / Evangelical)"),
    "cross_lalibela": ("✛", "Lalibela cross (Ethiopian Tewahedo)"),
    "star_david": ("✡", "Star of David (Jewish / Hebrew Bible)"),
    "fleur": ("⚜", "fleur-de-lis (decorative / scholarly)"),
}

# Cardinal English number names for chapters 1..150. Bible chapters
# don't go higher (Psalm 150 is the longest book at 150 chapters).
_NUMBER_WORDS_ONES = {
    0: "Zero",
    1: "One",
    2: "Two",
    3: "Three",
    4: "Four",
    5: "Five",
    6: "Six",
    7: "Seven",
    8: "Eight",
    9: "Nine",
    10: "Ten",
    11: "Eleven",
    12: "Twelve",
    13: "Thirteen",
    14: "Fourteen",
    15: "Fifteen",
    16: "Sixteen",
    17: "Seventeen",
    18: "Eighteen",
    19: "Nineteen",
}
_NUMBER_WORDS_TENS = {
    20: "Twenty",
    30: "Thirty",
    40: "Forty",
    50: "Fifty",
    60: "Sixty",
    70: "Seventy",
    80: "Eighty",
    90: "Ninety",
}


def chapter_number_to_word(n: int) -> str:
    """Convert 1-150 to its English word form. Returns the digit
    if outside that range — chapters above 150 don't exist in any
    canonical text we publish."""
    if n < 1 or n > 150:
        return str(n)
    if n < 20:
        return _NUMBER_WORDS_ONES[n]
    if n < 100:
        tens = (n // 10) * 10
        ones = n % 10
        if ones == 0:
            return _NUMBER_WORDS_TENS[tens]
        return f"{_NUMBER_WORDS_TENS[tens]}-{_NUMBER_WORDS_ONES[ones].lower()}"
    # 100-150
    rest = n - 100
    if rest == 0:
        return "One Hundred"
    if rest < 20:
        return f"One Hundred {_NUMBER_WORDS_ONES[rest]}"
    tens = (rest // 10) * 10
    ones = rest % 10
    if ones == 0:
        return f"One Hundred {_NUMBER_WORDS_TENS[tens]}"
    return f"One Hundred {_NUMBER_WORDS_TENS[tens]}-{_NUMBER_WORDS_ONES[ones].lower()}"


def format_chapter_label(num: int, format_style: str) -> str:
    """Render the inner chapter label text per the chosen format."""
    if format_style not in CHAPTER_NUMBER_FORMATS:
        format_style = "digit"
    if format_style == "digit":
        return str(num)
    word = chapter_number_to_word(num)
    if format_style == "word_chapter":
        return f"Chapter {word}"
    return word


def decorate_chapter_label(label: str, decoration_style: str) -> str:
    """Wrap a chapter label with the chosen decorative affixes."""
    prefix, suffix = CHAPTER_NUMBER_DECORATIONS.get(decoration_style, ("", ""))
    return f"{prefix}{label}{suffix}"


# Match the existing chapter heading marker so we can rewrite the
# inner text. The marker is intentionally narrow (matches only the
# specific span class used by the body chapter heading); incidental
# `bold-num` uses elsewhere are not affected.
_CHAPTER_NUM_RE = re.compile(r'(<span class="bold-num">)(\d+)(</span>)')


def apply_chapter_decoration(tmp: Path, edition: dict) -> dict:
    """Apply per-edition chapter number format + decoration to every
    body chapter heading in the temporary build directory.

    Returns ``{files_touched: int, chapters_rewritten: int}`` for the
    overall build stats summary. Idempotent: running twice on the same
    files produces the same output (the regex matches digits only,
    not already-decorated labels).
    """
    fmt = (edition.get("chapter_number_format") or "digit").strip()
    deco = (edition.get("chapter_number_decoration") or "plain").strip()

    if fmt == "digit" and deco == "plain":
        # No-op for the default; saves a full file scan per edition build
        return {"files_touched": 0, "chapters_rewritten": 0}

    files_touched = 0
    chapters_rewritten = 0

    def rewrite(m: re.Match) -> str:
        nonlocal chapters_rewritten
        n = int(m.group(2))
        label = format_chapter_label(n, fmt)
        decorated = decorate_chapter_label(label, deco)
        chapters_rewritten += 1
        return f"{m.group(1)}{decorated}{m.group(3)}"

    for fpath in sorted(tmp.glob("*.html")):
        text = fpath.read_text(encoding="utf-8")
        new_text, n_subs = _CHAPTER_NUM_RE.subn(rewrite, text)
        if n_subs > 0 and new_text != text:
            fpath.write_text(new_text, encoding="utf-8")
            files_touched += 1

    return {
        "files_touched": files_touched,
        "chapters_rewritten": chapters_rewritten,
    }


# Phase ν.6.x — render pass for reader's TOC transforms. Closes the
# loop on the schema-only fields shipped in ν.6 (reader_toc_*) and
# ν.6.1 (book_toc_ornament). Three separate transforms, all driven
# off the same in-book ToC structure (each book entry already uses
# <details><summary>...</summary><ol>...</ol></details>):
#
#   reader_toc_collapsible       false → unwrap <details> into a
#                                        flat <li>...<ol>...</ol> so
#                                        chapters are always visible
#                                 true  → keep collapsible (default)
#
#   reader_toc_default_open      true  → add open="" to each <details>
#                                 false → no attribute (collapsed by
#                                        default; clearer ToC for
#                                        long-canon editions)
#
#   book_toc_ornament            non-empty, non-"none" → inject the
#                                ornament glyph inside <summary>
#                                immediately before the book's <a>,
#                                wrapped in a <span class="toc-ornament">
#                                so theme CSS can style it
#
# No-op for the default settings (reader_toc_collapsible=true +
# reader_toc_default_open=false + book_toc_ornament="" or "none").
# Existing builds rebuild byte-identically — Rule §6.5 (defaults
# preserve back-compat).

# The visible ToC's per-book block. Captures (in order):
#   1. opening <li class="toc-book"> + any whitespace
#   2. opening <details> + any attributes (we'll rewrite this)
#   3. opening <summary> + any whitespace
#   4. the book's <a href=...>...</a> tag
#   5. closing </summary> through to </details></li>
#
# Designed to match the exact HTML the existing pipeline emits;
# format documented in ν.6.1 scope addendum.
_TOC_BOOK_BLOCK_RE = re.compile(
    r'(<li class="toc-book">\s*)'
    r"(<details(?:\s[^>]*)?>)"
    r"(\s*<summary>\s*)"
    r"(<a\s[^>]*>[^<]*</a>)"
    r"(\s*</summary>.*?</details>\s*</li>)",
    re.DOTALL,
)


def apply_reader_toc_transforms(tmp: Path, edition: dict) -> dict:
    """Apply reader_toc_collapsible, reader_toc_default_open, and
    book_toc_ornament to the in-book Table of Contents.

    Returns ``{files_touched, books_transformed, ornaments_inserted,
    details_unwrapped, defaults_opened}`` for the build stats summary.
    Idempotent on default settings.
    """
    collapsible = edition.get("reader_toc_collapsible")
    if collapsible is None:
        collapsible = True  # default: keep collapsible
    default_open = bool(edition.get("reader_toc_default_open", False))
    ornament_code = (edition.get("book_toc_ornament") or "").strip()
    ornament_glyph = ""
    if ornament_code and ornament_code != "none" and ornament_code in BOOK_TOC_ORNAMENTS:
        ornament_glyph = BOOK_TOC_ORNAMENTS[ornament_code][0]
        # Unknown codes are silently ignored — the API validator
        # already rejects them upstream, and a build-time crash
        # over a stale value in editions.yaml would be worse than
        # a no-op.

    # Default-settings short-circuit. Saves the file scan for the
    # 4 of 5 editions that ship with default reader experience.
    if collapsible and not default_open and not ornament_glyph:
        return {
            "files_touched": 0,
            "books_transformed": 0,
            "ornaments_inserted": 0,
            "details_unwrapped": 0,
            "defaults_opened": 0,
        }

    files_touched = 0
    books_transformed = 0
    ornaments_inserted = 0
    details_unwrapped = 0
    defaults_opened = 0

    # Open-tag for <details> when keeping it collapsible. The
    # `open` attribute is HTML-spec-correct and renders identically
    # across e-readers; we use the bare attribute form (open="" not
    # open="open") since EPUB readers tolerate both but the bare
    # form is one byte shorter.
    if collapsible:
        new_details_open = '<details open="">' if default_open else "<details>"
    # If non-collapsible, we replace the entire <details>...</details>
    # with the inner content — see the rewrite function below.

    def rewrite(m: re.Match) -> str:
        nonlocal books_transformed, ornaments_inserted
        nonlocal details_unwrapped, defaults_opened
        li_open, _details_open, summary_open, anchor, tail = m.groups()
        books_transformed += 1

        # Compose the ornament fragment — no leading <span>...</span>
        # if no ornament selected, so default-builds look identical.
        ornament_html = ""
        if ornament_glyph:
            # Single space after the closing </span> matches the
            # spacing convention the existing toc-chapters block uses.
            ornament_html = f'<span class="toc-ornament">{ornament_glyph}</span> '
            ornaments_inserted += 1

        if collapsible:
            # Keep <details>; conditionally add open attribute;
            # inject ornament inside <summary> before the <a>.
            if default_open:
                defaults_opened += 1
            return f"{li_open}{new_details_open}{summary_open}{ornament_html}{anchor}{tail}"
        else:
            # Strip <details>/</details> wrappers; the <summary>
            # becomes a flat label, chapter list follows directly.
            # We pull the <ol class="toc-chapters">...</ol> out of
            # the original tail and emit a clean structure.
            details_unwrapped += 1
            # tail starts with whitespace + </summary>, then has the
            # chapter list, then closes </details></li>. We need to
            # extract everything between </summary> and </details>.
            inner = re.sub(
                r"^\s*</summary>(.*?)</details>\s*</li>\s*$",
                r"\1",
                tail,
                flags=re.DOTALL,
            )
            return f'{li_open}<p class="toc-book-label">{ornament_html}{anchor}</p>{inner}</li>'

    for fpath in sorted(tmp.glob("*.html")):
        text = fpath.read_text(encoding="utf-8")
        new_text, n_subs = _TOC_BOOK_BLOCK_RE.subn(rewrite, text)
        if n_subs > 0 and new_text != text:
            fpath.write_text(new_text, encoding="utf-8")
            files_touched += 1

    return {
        "files_touched": files_touched,
        "books_transformed": books_transformed,
        "ornaments_inserted": ornaments_inserted,
        "details_unwrapped": details_unwrapped,
        "defaults_opened": defaults_opened,
    }


# ----------------------------------------------------------------------
# Phase ν.8 — Bilingual ToC
# ----------------------------------------------------------------------
#
# Re-label each ToC entry (book + chapter) with native-script names
# alongside English when the edition opts in via the
# ``toc_bilingual`` field. Affects BOTH:
#
#   - the in-book visible ToC (the <li class="toc-book"> nested
#     structure inside the chapter HTML files), AND
#   - the EPUB navigation document (nav.xhtml), whose entries drive
#     every e-reader's built-in ToC sheet (Apple Books, Kindle,
#     Calibre, Thorium, …).
#
# Enum (from scripts.core.book_native_names.TOC_BILINGUAL_OPTIONS):
#   "none"             — English only (default; back-compat byte-
#                        identical builds when this field is unset)
#   "geez-english"     — ኦሪት ዘፍጥረት / Genesis, ምዕራፍ ፩ / Chapter 1
#   "amharic-english"  — same script as Ge'ez but allows publishers
#                        to label intent (and gives a hook for any
#                        future name-divergence)
#   "both"             — Ge'ez + Amharic + English where they
#                        differ; de-duplicates when identical
#
# Idempotency: each pass identifies entries by the canonical anchor
# href (``#bp-NN`` for books, ``#ch-bXX-cN`` for chapters) and
# rewrites the label text. The bp-NN → book-code mapping is read
# fresh from ``books_canonical_order`` each call; calling the pass
# twice with the same toc_style produces the same output bytes.

# Book ToC entry — the in-book visible ToC. Match the <a> tag for a
# book entry; the href points to ``…#bp-NN`` so we can identify
# which book this is.
_BILINGUAL_BOOK_ANCHOR_RE = re.compile(
    r'(<a\s+[^>]*?href="[^"]*#bp-(\d+)"[^>]*>)'
    r"([^<]*)"
    r"(</a>)"
)

# Chapter ToC entry — match the <a> in a toc-chapters list. The href
# points to ``…#ch-bXX-cN``; we capture the chapter number from N.
_BILINGUAL_CHAPTER_ANCHOR_RE = re.compile(
    r'(<li>\s*<a\s+[^>]*?href="[^"]*#ch-b(\d+)-c(\d+)"[^>]*>)'
    r"([^<]*)"
    r"(</a>\s*</li>)"
)


def _bp_idx_to_code_map() -> dict[int, str]:
    """Build ``{bp_index: book_code}`` once per call.

    ``bp_index`` is the numeric suffix of the ``bp-NN`` anchor that
    identifies a book in the rendered HTML / nav.xhtml. The mapping
    is derived from the canonical book list rather than from string
    parsing of the anchor itself.
    """
    out: dict[int, str] = {}
    for i, book in enumerate(config.load_books()):
        bp = book.get("bp", "")
        m = re.match(r"bp-(\d+)", bp)
        idx = int(m.group(1)) if m else i
        out[idx] = book["code"]
    return out


def _xml_escape_label(s: str) -> str:
    """Escape a ToC label for safe inclusion in XHTML <a> body text.

    Mirrors _xml_escape_text but is named distinctly so the call
    sites are easy to grep.
    """
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def apply_bilingual_toc(tmp: Path, edition: dict) -> dict:
    """Phase ν.8 — rewrite ToC entries with bilingual labels.

    Reads ``edition["toc_bilingual"]`` (one of TOC_BILINGUAL_OPTIONS).
    When the value is "none" (the default), this is a complete no-op:
    no file scan, no rewrite, no byte change — preserving Rule §6.5's
    back-compat guarantee.

    For other values, walks every .html and the nav.xhtml in ``tmp``
    and rewrites book / chapter anchor labels via
    ``book_native_names.format_toc_book_label`` and
    ``format_toc_chapter_label``.

    Returns ``{files_touched, book_labels_rewritten,
    chapter_labels_rewritten}`` for the build stats summary.
    Idempotent: re-running on already-bilingual output produces the
    same output (the formatter takes book CODES not labels, so a
    second pass starts from the same input).
    """
    from scripts.core.book_native_names import (
        TOC_BILINGUAL_OPTIONS,
        format_toc_book_label,
        format_toc_chapter_label,
    )

    toc_style = (edition.get("toc_bilingual") or "none").strip()
    if toc_style not in TOC_BILINGUAL_OPTIONS:
        # Unknown value (stale data / typo) — treat as no-op rather
        # than crash. The API validator rejects unknowns on save;
        # the build pipeline is defensive.
        toc_style = "none"

    if toc_style == "none":
        return {
            "files_touched": 0,
            "book_labels_rewritten": 0,
            "chapter_labels_rewritten": 0,
            "toc_style": toc_style,
        }

    bp_to_code = _bp_idx_to_code_map()

    files_touched = 0
    book_labels_rewritten = 0
    chapter_labels_rewritten = 0

    def _rewrite_book(m: re.Match) -> str:
        nonlocal book_labels_rewritten
        opening = m.group(1)
        bp_idx = int(m.group(2))
        closing = m.group(4)
        code = bp_to_code.get(bp_idx)
        if not code:
            return m.group(0)
        label = format_toc_book_label(code, toc_style)
        if not label:
            return m.group(0)
        book_labels_rewritten += 1
        return f"{opening}{_xml_escape_label(label)}{closing}"

    def _rewrite_chapter(m: re.Match) -> str:
        nonlocal chapter_labels_rewritten
        opening = m.group(1)
        # group(2) = book bxx index, group(3) = chapter number
        try:
            ch_num = int(m.group(3))
        except ValueError:
            return m.group(0)
        closing = m.group(5)
        label = format_toc_chapter_label(ch_num, toc_style)
        chapter_labels_rewritten += 1
        return f"{opening}{_xml_escape_label(label)}{closing}"

    # Scan every .html file (the in-book ToC lives in
    # index_split_000.html in current builds but is generally not
    # pinned to a single file).
    scan_paths = list(tmp.glob("*.html"))
    # Plus nav.xhtml (e-reader ToC).
    nav_path = tmp / "nav.xhtml"
    if nav_path.is_file():
        scan_paths.append(nav_path)

    for fpath in sorted(scan_paths):
        text = fpath.read_text(encoding="utf-8")
        new_text = _BILINGUAL_BOOK_ANCHOR_RE.sub(_rewrite_book, text)
        new_text = _BILINGUAL_CHAPTER_ANCHOR_RE.sub(_rewrite_chapter, new_text)
        if new_text != text:
            fpath.write_text(new_text, encoding="utf-8")
            files_touched += 1

    return {
        "files_touched": files_touched,
        "book_labels_rewritten": book_labels_rewritten,
        "chapter_labels_rewritten": chapter_labels_rewritten,
        "toc_style": toc_style,
    }


def inject_copyright_page(tmp: Path, edition: dict, version: str) -> None:
    """Write copyright.xhtml into tmp_dir, register it in content.opf
    (manifest + spine), and add a TOC entry to nav.xhtml. Edition-specific:
    different title and BISAC per build (Ω.0 pivot: ISBN dropped)."""
    # Load ONIX defaults so the page can render real publisher / contributor
    # info when the user has filled it in.
    onix_py = REPO_ROOT / "content" / "onix.py"
    defaults: dict = {}
    if onix_py.is_file():
        import importlib.util

        spec = importlib.util.spec_from_file_location("_onix_cfg_b", onix_py)
        # spec_from_file_location returns Optional[ModuleSpec]; treat
        # None as "no defaults to load" rather than crashing the build.
        if spec is not None and spec.loader is not None:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            defaults = getattr(mod, "DEFAULTS", {})
            # If editions are also defined there, prefer the matching one's data
            for ed in getattr(mod, "EDITIONS", []):
                if ed.get("id") == edition.get("id"):
                    edition = {**edition, **ed}
                    break

    # 1) Write the page
    html = render_copyright_page(edition, defaults, version)
    (tmp / "copyright.xhtml").write_text(html, encoding="utf-8")

    # 2) Patch OPF — add manifest item + insert into spine after titlepage
    opf_path = tmp / "content.opf"
    if opf_path.is_file():
        opf = opf_path.read_text(encoding="utf-8")
        if "copyright.xhtml" not in opf:
            opf = opf.replace(
                '<item id="titlepage" href="titlepage.xhtml"',
                '<item id="copyright" href="copyright.xhtml" media-type="application/xhtml+xml"/>\n    '
                '<item id="titlepage" href="titlepage.xhtml"',
            )
            # Spine: after titlepage
            opf = opf.replace(
                '<itemref idref="titlepage"/>', '<itemref idref="titlepage"/>\n    <itemref idref="copyright"/>'
            )
            opf_path.write_text(opf, encoding="utf-8")

    # 3) Patch nav.xhtml TOC
    nav_path = tmp / "nav.xhtml"
    if nav_path.is_file():
        nav = nav_path.read_text(encoding="utf-8")
        if 'href="copyright.xhtml"' not in nav:
            nav = nav.replace(
                "<ol>\n      <li>",
                '<ol>\n      <li><a href="copyright.xhtml">Copyright &amp; Credits</a></li>\n      <li>',
                1,
            )
            nav_path.write_text(nav, encoding="utf-8")


# ----------------------------------------------------------------------
# ψ.19.1 — reading-plan EPUB ToC integration
#
# Companion to ψ.19's loader infrastructure. When an edition opts into
# one or more reading plans via `enabled_reading_plans`, we render a
# `reading_plans.xhtml` page (one section per enabled plan, one
# `<li>` per day with the verse refs as plain-text), register it in
# the OPF manifest + spine, and add a ToC entry to nav.xhtml. No-op
# when the edition has no plans enabled — back-compat per §6.5.
# ----------------------------------------------------------------------


def render_reading_plans_page(edition: dict, plans: list) -> str:
    """Render the XHTML page bundling every enabled plan's day-by-day
    schedule.

    `plans` is a list of `ReadingPlan` records (from
    scripts.core.reading_plans.load_plan); the caller is responsible
    for filtering to the edition's `enabled_reading_plans` list. The
    output is the full XHTML document including doctype + head, ready
    to write to ``tmp/reading_plans.xhtml``.

    Verse refs render as plain text (no in-EPUB deep links for v1);
    a future ψ.19.2 could resolve refs to chapter HTML anchors.
    """
    edition_title = edition.get("title", "Untitled")
    sections = []
    for plan in plans:
        entry_lines = []
        for entry in plan.entries:
            verses_text = " · ".join(_xml_escape_text(v) for v in entry.verses)
            entry_lines.append(
                f'      <li class="reading-plan-day">'
                f'<span class="reading-plan-day-number">Day {entry.day}</span>'
                f' — <span class="reading-plan-refs">{verses_text}</span>'
                f"</li>"
            )
        entries_html = "\n".join(entry_lines)
        description_html = ""
        if plan.description:
            # Trim to first paragraph for the section header; full
            # description may be long-form Markdown-style.
            first_para = plan.description.strip().split("\n\n")[0]
            description_html = f'<p class="reading-plan-description">{_xml_escape_text(first_para)}</p>'
        sections.append(
            f'<section class="reading-plan" id="reading-plan-{_xml_escape_text(plan.id)}">\n'
            f'  <h2 class="reading-plan-title">{_xml_escape_text(plan.label)}</h2>\n'
            f"  {description_html}\n"
            f'  <ol class="reading-plan-days">\n'
            f"{entries_html}\n"
            f"  </ol>\n"
            f"</section>"
        )
    body_sections = (
        "\n\n".join(sections)
        if sections
        else ('<p class="reading-plans-empty">No reading plans enabled for this edition.</p>')
    )
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head>
  <title>Reading Plans</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
  <link rel="stylesheet" type="text/css" href="stylesheet.css"/>
</head>
<body epub:type="frontmatter">
  <section class="reading-plans-page" epub:type="frontmatter">
    <h1 class="reading-plans-page-title">Reading Plans</h1>
    <p class="reading-plans-page-intro">Daily reading schedules for <em>{_xml_escape_text(edition_title)}</em>. Verse references follow the canonical book / chapter / verse format used throughout the apparatus.</p>
    <hr class="reading-plans-rule"/>
{body_sections}
  </section>
</body>
</html>
"""


def inject_reading_plans_page(tmp: Path, edition: dict) -> dict:
    """Render + write the reading-plans page; patch OPF + nav.xhtml.

    Returns ``{"plans_written": int, "skipped_reason": str | None}``
    so the build_one stats accumulator can record what happened.
    No-op when:
      - the edition's `enabled_reading_plans` is empty / absent
      - none of the listed plan ids resolve to a real file (the
        validator usually catches this on save, but the build is
        defensive)
    """
    enabled_ids = list(edition.get("enabled_reading_plans") or [])
    if not enabled_ids:
        return {"plans_written": 0, "skipped_reason": "no plans enabled"}

    # Lazy import — keeps the module's import surface clean for
    # consumers that don't trigger the build pipeline.
    from scripts.core.reading_plans import load_plan

    plans = []
    for pid in enabled_ids:
        try:
            plan = load_plan(pid)
        except ValueError:
            continue
        if plan is None:
            continue
        plans.append(plan)
    if not plans:
        return {"plans_written": 0, "skipped_reason": "no plans loaded"}

    html = render_reading_plans_page(edition, plans)
    out_path = tmp / "reading_plans.xhtml"
    out_path.write_text(html, encoding="utf-8")

    # Patch OPF — add manifest item + insert into spine after the
    # copyright page (so the order is title → copyright → reading
    # plans → main matter).
    opf_path = tmp / "content.opf"
    if opf_path.is_file():
        opf = opf_path.read_text(encoding="utf-8")
        if "reading_plans.xhtml" not in opf:
            opf = opf.replace(
                '<item id="copyright" href="copyright.xhtml"',
                '<item id="readingplans" href="reading_plans.xhtml" media-type="application/xhtml+xml"/>\n    '
                '<item id="copyright" href="copyright.xhtml"',
            )
            opf = opf.replace(
                '<itemref idref="copyright"/>',
                '<itemref idref="copyright"/>\n    <itemref idref="readingplans"/>',
            )
            opf_path.write_text(opf, encoding="utf-8")

    # Patch nav.xhtml — append a ToC entry after the Copyright link.
    nav_path = tmp / "nav.xhtml"
    if nav_path.is_file():
        nav = nav_path.read_text(encoding="utf-8")
        if 'href="reading_plans.xhtml"' not in nav:
            anchor = '<li><a href="copyright.xhtml">Copyright &amp; Credits</a></li>'
            if anchor in nav:
                nav = nav.replace(
                    anchor,
                    anchor + '\n      <li><a href="reading_plans.xhtml">Reading Plans</a></li>',
                    1,
                )
                nav_path.write_text(nav, encoding="utf-8")

    return {
        "plans_written": len(plans),
        "skipped_reason": None,
        "plan_ids": [p.id for p in plans],
        "total_days": sum(len(p.entries) for p in plans),
    }


def is_output_current(output_dir: Path, edition_id: str, version: str) -> Path | None:
    """Find a pre-existing edition file matching ``edition_id`` + ``version``
    and return its path if newer than every input source. Returns None if
    no current build exists; caller should rebuild."""
    pattern = f"Ethiopian_Bible_{edition_id}_{version}_*.epub"
    candidates = sorted(output_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        return None
    latest = candidates[0]
    try:
        out_mtime = latest.stat().st_mtime
    except OSError:
        return None
    sources = list(EPUB_DIR.glob("*.html"))
    sources.append(EPUB_DIR / "content.opf")
    sources.append(EPUB_DIR / "nav.xhtml")
    sources.append(EPUB_DIR / "stylesheet.css")
    sources.append(REPO_ROOT / "content" / "onix.py")
    sources.append(REPO_ROOT / "content" / "editions.yaml")
    sources.append(REPO_ROOT / "scripts" / "build_edition.py")
    for s in sources:
        if s.is_file() and s.stat().st_mtime > out_mtime:
            return None
    return latest


def load_canons() -> dict:
    """Read content/canons.yaml and return {canon_id: {label, description, books}}."""
    canons_path = REPO_ROOT / "content" / "canons.yaml"
    if not canons_path.is_file():
        return {}
    import yaml

    data = yaml.safe_load(canons_path.read_text(encoding="utf-8")) or {}
    return data.get("canons", {}) or {}


# Match a single book-title-page div + everything that follows until the
# next book-title-page div or end of body. The `id="bp-NN"` capture tells
# us which book this segment is.
# A book's segment runs from its title page to the NEXT title page — OR to the
# per-file shared footnote containers (the single `<aside class="notes-section">`
# and `<section class="verse-refs-section">` at the file's end, which hold asides
# / verse-popups for EVERY book in the file). Stopping at those keeps the LAST
# book's segment from swallowing them when that book is dropped by a smaller
# canon — otherwise kept books' asides vanish while their markers survive
# (orphaned note-ref markers → epubcheck RSC-012).
_BOOK_SEGMENT_RE = re.compile(
    r'<div class="book-title-page"[^>]*id="bp-(\d+)"[^>]*>'
    r".*?"
    r'(?=<div class="book-title-page"|<aside class="notes-section"|<section class="verse-refs-section"|</body>|\Z)',
    re.DOTALL,
)


def filter_books_for_canon(tmp: Path, canon_books: set[str], all_books: list[dict]) -> dict:
    """Splice out books that aren't in ``canon_books``.

    Strategy:
      1. Compute the set of dropped book codes.
      2. Map bp-NN index → book code via the canonical book list.
      3. For each HTML file:
         - If all books in the file are dropped → delete the file entirely.
         - Otherwise → splice out the dropped book segments via
           ``_BOOK_SEGMENT_RE``.
      4. Strip cross-reference link wrappers that point to dropped books'
         vnote IDs (preserves visible text — Q2 option a).
      5. Caller is responsible for updating OPF manifest + spine + nav.xhtml.

    Returns: dict with ``dropped_books``, ``files_removed``, ``segments_spliced``,
    ``cross_refs_stripped`` for stats reporting.
    """
    code_by_idx: dict[int, str] = {}
    for i, book in enumerate(all_books):
        # bp_idx parses from book["bp"] like "bp-15" → 15
        bp = book.get("bp", "")
        m = re.match(r"bp-(\d+)", bp)
        idx = int(m.group(1)) if m else i
        code_by_idx[idx] = book["code"]

    book_codes = {b["code"] for b in all_books}
    dropped = book_codes - canon_books
    # Mixed-type stats dict: ints + a list. `dict[str, Any]` lets
    # mypy accept both `+= 1` on counter keys and `.append(...)` on
    # the `files_touched` list. A TypedDict would be more precise
    # but adds boilerplate the call sites don't need (ω.31).
    from typing import Any as _Any

    stats: dict[str, _Any] = {
        "dropped_books": len(dropped),
        "files_removed": 0,
        "segments_spliced": 0,
        "cross_refs_stripped": 0,
        "files_touched": [],
    }

    if not dropped:
        return stats

    # Map: file path → list of book codes that appear in that file (in order)
    files_to_books: dict[str, list[str]] = {}
    for book in all_books:
        for fname in book.get("files", []):
            files_to_books.setdefault(fname, []).append(book["code"])

    # Process each HTML file
    for fname, books_in_file in files_to_books.items():
        fpath = tmp / fname
        if not fpath.is_file():
            continue
        kept = [c for c in books_in_file if c not in dropped]

        if not kept:
            # Every book in this file is dropped → remove file entirely
            fpath.unlink()
            stats["files_removed"] += 1
            stats["files_touched"].append(fname)
            continue

        if len(kept) == len(books_in_file):
            # All books kept — no edit needed
            continue

        # Mixed — splice out dropped book segments
        text = fpath.read_text(encoding="utf-8")
        original_len = len(text)

        def _maybe_drop(m: re.Match) -> str:
            idx = int(m.group(1))
            code = code_by_idx.get(idx)
            if code in dropped:
                return ""  # splice out the segment
            return m.group(0)  # keep

        new_text, n_subs = _BOOK_SEGMENT_RE.subn(_maybe_drop, text)
        if n_subs > 0 and new_text != text:
            fpath.write_text(new_text, encoding="utf-8")
            stats["segments_spliced"] += (original_len - len(new_text)) // 100  # rough chars
            stats["files_touched"].append(fname)

    # Pass 1.5: remove in-book reading-ToC blocks for dropped books.
    # The master HTML has a visible Table of Contents at the front of
    # index_split_000.html that uses this structure per book:
    #
    #   <li class="toc-book">
    #     <details>
    #       <summary><a href="index_split_NNN.html#bp-NN">Book Title</a></summary>
    #       <ol class="toc-chapters">
    #         <li><a href="...#ch-bXX-cN">1</a></li>
    #         …
    #       </ol>
    #     </details>
    #   </li>
    #
    # We must remove the entire <li class="toc-book"> block whose summary
    # link points to a dropped bp-anchor or dropped file. Otherwise the
    # universal dangling-anchor strip (Pass 2) would reduce the block to
    # an empty husk listing chapter numbers as plain text — visually
    # nonsensical to the reader.
    #
    # IMPORTANT: This runs BEFORE Pass 2 strips the <a> wrappers, so the
    # href attributes are still intact and we can identify the target.
    if dropped:
        # Compute dropped bp-anchors + files for this pass
        dropped_bp_anchors_for_toc: set[str] = set()
        for book in all_books:
            if book["code"] in dropped:
                bp = book.get("bp", "")
                if bp:
                    dropped_bp_anchors_for_toc.add(bp)
        dropped_files_for_toc: set[str] = set()
        for fname, books_in_file in files_to_books.items():
            kept = [c for c in books_in_file if c not in dropped]
            if not kept:
                dropped_files_for_toc.add(fname)

        toc_book_re = re.compile(
            r'<li class="toc-book">\s*<details>.*?</details>\s*</li>\s*',
            re.DOTALL,
        )
        # Match summary's link to extract the target file + anchor
        summary_link_re = re.compile(
            r'<summary>\s*<a\s+href="([^"#]*)(?:#([^"]+))?"',
        )

        def _maybe_drop_toc_block(m: re.Match) -> str:
            block = m.group(0)
            link_m = summary_link_re.search(block)
            if not link_m:
                return block
            target_file = link_m.group(1) or ""
            anchor = link_m.group(2) or ""
            if target_file in dropped_files_for_toc:
                return ""
            if anchor in dropped_bp_anchors_for_toc:
                return ""
            return block

        for f in tmp.glob("*.html"):
            text = f.read_text(encoding="utf-8")
            new_text, n = toc_book_re.subn(_maybe_drop_toc_block, text)
            if n > 0 and new_text != text:
                f.write_text(new_text, encoding="utf-8")
                stats.setdefault("toc_blocks_removed", 0)
                stats["toc_blocks_removed"] += text.count('<li class="toc-book">') - new_text.count(
                    '<li class="toc-book">'
                )

    # Pass 2: strip <a href="..."> wrappers pointing to anchors / files
    # that no longer exist after the canon splice. Keeps the visible text
    # but removes the link (Q2 option a — preserve authorial intent).
    if dropped:
        # 2a) whole-file references to entirely-dropped HTML files
        dropped_files_in_pass2: set[str] = set()
        for fname, books_in_file in files_to_books.items():
            kept = [c for c in books_in_file if c not in dropped]
            if not kept:
                dropped_files_in_pass2.add(fname)

        # 2b) Build ID inventory of all surviving HTML files. Any
        # `<a href="X.html#Y">` whose target Y is not in the inventory
        # (either because Y was spliced out, or X.html itself is gone)
        # gets stripped. This is bulletproof: covers vnote-*, bp-NN,
        # ch-bXX-cN, page_NNN, ref-*, and any other anchor scheme.
        id_inventory: dict[str, set[str]] = {}
        for f in tmp.glob("*.html"):
            text = f.read_text(encoding="utf-8")
            id_inventory[f.name] = set(re.findall(r'\bid="([^"]+)"', text))

        # Generic dangling-anchor link pattern. Captures: file (optional) + anchor.
        link_re = re.compile(r'<a\s+href="([^"#]*)#([^"]+)"[^>]*>([^<]+)</a>')
        # Also handle file-only refs (no #fragment) to dropped files.
        file_only_re = re.compile(r'<a\s+href="([^"#]+)"[^>]*>([^<]+)</a>')

        for f in tmp.glob("*.html"):
            text = f.read_text(encoding="utf-8")

            def _check_anchor(m: re.Match, fname: str = f.name) -> str:
                target_file, anchor, visible = m.group(1), m.group(2), m.group(3)
                # Resolve target file: empty = same file
                target = target_file if target_file else fname
                if target not in id_inventory:
                    # File was dropped — strip wrapper
                    return visible
                if anchor not in id_inventory[target]:
                    # Anchor was spliced out — strip wrapper
                    return visible
                return m.group(0)

            new_text, n1 = link_re.subn(_check_anchor, text)
            stats["cross_refs_stripped"] += n1

            def _check_file_only(m: re.Match, fname: str = f.name) -> str:
                target_file, visible = m.group(1), m.group(2)
                # Skip non-html refs (mailto, http, etc.)
                if not target_file.endswith(".html") and not target_file.endswith(".xhtml"):
                    return m.group(0)
                if target_file not in id_inventory and target_file != fname:
                    return visible  # strip
                return m.group(0)

            new_text2, n2 = file_only_re.subn(_check_file_only, new_text)
            stats["cross_refs_stripped"] += n2

            if new_text2 != text:
                f.write_text(new_text2, encoding="utf-8")

    # Pass 3: drop footnote asides orphaned by the splice. A dropped book's
    # scripture (with its inline `id="ref-X"` markers) was spliced out, but its
    # asides remain in the shared per-file notes-section (now preserved by
    # _BOOK_SEGMENT_RE). Remove asides whose marker is gone so no dangling
    # footnote is left; kept books' asides (marker present) are untouched.
    # vnote popups are intentionally left intact — kept books' cross-references
    # may legitimately target a dropped book's verse popup.
    if dropped:
        orphan_aside_re = re.compile(
            r'<aside class="note [^"]*" id="note-([^"]+)"[^>]*>.*?</aside>\s*',
            re.DOTALL,
        )
        for f in tmp.glob("*.html"):
            text = f.read_text(encoding="utf-8")
            ref_ids = set(re.findall(r'\bid="ref-([^"]+)"', text))

            def _drop_orphan_aside(m: re.Match, _refs: set = ref_ids) -> str:
                return m.group(0) if m.group(1) in _refs else ""

            new_text, _ = orphan_aside_re.subn(_drop_orphan_aside, text)
            if new_text != text:
                removed = text.count('<aside class="note ') - new_text.count('<aside class="note ')
                f.write_text(new_text, encoding="utf-8")
                stats.setdefault("orphan_asides_removed", 0)
                stats["orphan_asides_removed"] += removed

    return stats


# φ.1 (2026-05-14) — OPF font-manifest emission.
#
# The EPUB 3 spec requires every resource referenced by stylesheet.css
# (including @font-face url() targets) to be registered in the OPF
# manifest with a correct media-type. apply_style.py emits the
# @font-face CSS rules; this helper backfills the manifest entries.
# Pairs with style_config.EMBED_FONT_PATHS (the Π.0 multi-font knob)
# and the legacy EMBED_FONT_PATH (single-font knob).
#
# Idempotent: a font already registered in the manifest is not
# re-added. No-op when both knobs are empty (preserves v1.0
# byte-identical builds — important for v1.0 reproducibility).

_FONT_MEDIA_TYPES = {
    ".ttf": "font/ttf",
    ".otf": "application/vnd.ms-opentype",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
}


def patch_opf_fonts(opf_text: str) -> str:
    """Register style_config.EMBED_FONT_PATH + EMBED_FONT_PATHS entries
    in the OPF manifest with proper font media-types.

    Each entry is added as an `<item id="font-N" href="<path>"
    media-type="<mime>"/>` line just before `</manifest>`. The id is
    derived from a slug of the basename so it's stable across runs.

    No-op when neither knob is set (v1.0 reproducibility per §6.5).
    """
    # Avoid an import cycle — style_config is local module loaded at runtime.
    from scripts import style_config

    entries: list[dict] = []
    legacy_path = getattr(style_config, "EMBED_FONT_PATH", None)
    legacy_family = getattr(style_config, "EMBED_FONT_FAMILY", "")
    if legacy_path:
        entries.append({"path": legacy_path, "family": legacy_family})
    entries.extend(getattr(style_config, "EMBED_FONT_PATHS", []) or [])

    if not entries:
        # v1.0 reproducibility — byte-identical build when no embeds.
        return opf_text

    new_items: list[str] = []
    for entry in entries:
        path = entry.get("path", "")
        if not path:
            continue
        # Skip if already registered.
        if f'href="{path}"' in opf_text:
            continue
        ext = path.lower().rsplit(".", 1)
        suffix = "." + ext[-1] if len(ext) == 2 else ""
        media_type = _FONT_MEDIA_TYPES.get(suffix, "application/octet-stream")
        # Slug the basename into a stable id.
        basename = path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        slug = re.sub(r"[^A-Za-z0-9]+", "-", basename).strip("-").lower() or "font"
        font_id = f"font-{slug}"
        # Ensure id uniqueness even across multiple weights/styles of
        # the same family by appending a counter if collision.
        candidate = font_id
        i = 2
        while f'id="{candidate}"' in opf_text or any(f'id="{candidate}"' in line for line in new_items):
            candidate = f"{font_id}-{i}"
            i += 1
        new_items.append(f'<item id="{candidate}" href="{path}" media-type="{media_type}"/>')

    if not new_items:
        return opf_text

    insertion = "\n    " + "\n    ".join(new_items) + "\n  "
    return opf_text.replace("</manifest>", f"{insertion}</manifest>", 1)


def patch_opf_canon(opf_text: str, dropped_files: set[str]) -> str:
    """Remove dropped HTML files from <manifest> + <spine>.

    Order matters: we need the manifest item's `id` attribute to remove
    the corresponding `<itemref>` from the spine — so we extract the id
    BEFORE deleting the manifest item.
    """
    if not dropped_files:
        return opf_text
    for fname in dropped_files:
        # 1) Find the manifest item's id (BEFORE removing it).
        m = re.search(rf'id="([^"]+)"\s+href="{re.escape(fname)}"', opf_text)
        idref = m.group(1) if m else None
        # 2) Remove the manifest item.
        opf_text = re.sub(
            rf'\s*<item\s+[^>]*href="{re.escape(fname)}"[^>]*/>',
            "",
            opf_text,
        )
        # 3) Remove the spine reference using the captured id.
        if idref:
            opf_text = re.sub(
                rf'\s*<itemref\s+[^>]*idref="{re.escape(idref)}"[^>]*/>',
                "",
                opf_text,
            )
    return opf_text


def patch_nav_canon(nav_text: str, dropped_files: set[str], dropped_book_bp_indices: set[int]) -> str:
    """Remove TOC entries pointing to dropped files OR dropped book bp-anchors.

    `dropped_book_bp_indices` is a set of integers — the bp-NN values
    of books that were spliced out. Even when a book's HTML file was
    not deleted (because the file held kept books too), its TOC entry
    must be removed to avoid orphan-anchor RSC-012 errors.
    """
    if not dropped_files and not dropped_book_bp_indices:
        return nav_text
    # Remove <li> entries whose <a href="..."> points to a dropped file
    for fname in dropped_files:
        nav_text = re.sub(
            rf'\s*<li[^>]*>\s*<a\s+[^>]*href="{re.escape(fname)}(?:#[^"]*)?"[^>]*>[^<]*</a>\s*(?:<ol[^>]*>.*?</ol>\s*)?</li>',
            "",
            nav_text,
            flags=re.DOTALL,
        )
    # Remove <li> entries whose <a href="..."> points to a dropped book's bp-anchor
    for bp_idx in dropped_book_bp_indices:
        bp_anchor = f"bp-{bp_idx:02d}"
        nav_text = re.sub(
            rf'\s*<li[^>]*>\s*<a\s+[^>]*href="[^"]*#{re.escape(bp_anchor)}"[^>]*>[^<]*</a>\s*(?:<ol[^>]*>.*?</ol>\s*)?</li>',
            "",
            nav_text,
            flags=re.DOTALL,
        )
    return nav_text


def patch_ncx_canon(ncx_text: str, id_inventory: dict[str, set[str]]) -> str:
    """Strip navPoint elements from toc.ncx whose <content src="..."> points
    to a dropped file or a missing anchor.

    Uses the same id_inventory built by filter_books_for_canon — any
    `src="X.html#Y"` where X is gone or Y is not in X's IDs gets the
    whole navPoint removed. After pruning, playOrder is renumbered
    contiguously to satisfy EPUB 2 spec (no gaps allowed).
    """
    navpoint_re = re.compile(r"<navPoint\b[^>]*>.*?</navPoint>\s*", re.DOTALL)
    src_re = re.compile(r'<content\s+src="([^"#]*)(?:#([^"]+))?"\s*/>')

    def _check_navpoint(m: re.Match) -> str:
        block = m.group(0)
        src_m = src_re.search(block)
        if not src_m:
            return block
        target_file = src_m.group(1) or ""
        anchor = src_m.group(2) or ""
        if target_file and target_file not in id_inventory:
            return ""
        if anchor and target_file in id_inventory and anchor not in id_inventory[target_file]:
            return ""
        return block

    pruned = navpoint_re.sub(_check_navpoint, ncx_text)

    # Renumber playOrder sequentially — each surviving navPoint becomes 1, 2, 3, …
    counter = [0]

    def _renumber(_m: re.Match) -> str:
        counter[0] += 1
        return f'playOrder="{counter[0]}"'

    pruned = re.sub(r'playOrder="\d+"', _renumber, pruned)
    return pruned


# Phase ω.20-C — companion stats sidecar so api_export_build (and any
# operator tooling) can tell whether the EPUB was served from cache or
# freshly built. The sidecar lives at `<output_path>.stats.json` —
# adjacent to its EPUB, easy to find by string-replace, easy to clean
# up via `glob("*.stats.json")` alongside the existing `glob("*.epub")`.
def _write_stats_sidecar(
    output_path: Path,
    stats: dict,
    build_seconds: float,
) -> Path | None:
    """Write a small JSON sidecar capturing build outcome metadata.

    The sidecar is a buyer-facing surface (api_export_build folds it
    into the response payload) so it stays minimal: edition_id,
    version, cache_hit, skipped, size_mb, build_seconds. Operator-
    facing stats (enabled_kinds, markers_removed, etc.) stay in the
    in-memory dict and are NOT serialized — different audience.

    Sidecar writes are best-effort; failures (read-only disk, etc.)
    return None and don't propagate. The EPUB itself is always the
    primary artifact.
    """
    try:
        from scripts.core import notes_io
    except Exception:
        return None
    payload = {
        "edition_id": stats.get("edition_id"),
        "version": stats.get("version"),
        "cache_hit": bool(stats.get("cache_hit", False)),
        "skipped": bool(stats.get("skipped", False)),
        "size_mb": float(stats.get("size_mb", 0.0)),
        "build_seconds": round(float(build_seconds), 3),
        "filename": output_path.name,
    }
    sidecar = output_path.with_suffix(output_path.suffix + ".stats.json")
    try:
        notes_io.atomic_write(
            sidecar,
            json.dumps(payload, indent=2, ensure_ascii=False),
        )
    except Exception:
        return None
    return sidecar


def _retitle_html_pages(text: str, edition_title: str) -> tuple[str, int]:
    """Replace the calibre-default ``<title>Converted Ebook</title>`` baked into
    the base scripture chunks with the edition's own title (matching the OPF
    dc:title). Only the exact calibre default is touched, so generated pages
    (copyright, reading plans) keep their proper titles and the pass is
    idempotent. The title is XML-escaped so a title containing ``&`` or ``<``
    stays well-formed XHTML. Returns ``(new_text, n_replaced)``."""
    needle = "<title>Converted Ebook</title>"
    if not edition_title or needle not in text:
        return text, 0
    safe = html.escape(edition_title, quote=False)
    return text.replace(needle, f"<title>{safe}</title>"), text.count(needle)


def build_one(
    edition_id: str,
    output_dir: Path,
    version: str,
    all_kinds: list[dict],
    dry_run: bool = False,
    force: bool = False,
) -> dict:
    # ω.20-C — wall-clock timing for the build_seconds field of the
    # stats sidecar. Captured at function entry so the value covers
    # cache-lookup time on hits and full-pipeline time on misses.
    _t0 = time.perf_counter()

    eds = config.editions_by_id()
    if edition_id not in eds:
        raise ValueError(f"unknown edition {edition_id!r}; known: {sorted(eds)}")
    edition = eds[edition_id]

    enabled, disabled = compute_enabled_kinds(edition, all_kinds)

    # Phase ρ.1: per-edition disabled note IDs. Translate our note IDs
    # (book:ch:vs[suffix]:kind) into the HTML ref-id format the build sees
    # (ref-<prefix><cc><vv><suffix>).
    disabled_note_ids = list(edition.get("disabled_note_ids") or [])
    disabled_html_ref_ids: set[str] = set()
    if disabled_note_ids:
        books_idx = config.books_by_code()
        note_id_re = re.compile(r"^([a-z0-9]+):(\d+):(\d+)([a-z]*):([a-z][a-z0-9-]*)$")
        for nid in disabled_note_ids:
            m = note_id_re.match(nid)
            if not m:
                continue
            book_code = m.group(1)
            book = books_idx.get(book_code) or {}
            prefix = book.get("id_prefix")
            if not prefix:
                continue
            ch = int(m.group(2))
            vs = int(m.group(3))
            suffix = m.group(4)
            disabled_html_ref_ids.add(f"ref-{prefix}{ch:02d}{vs:02d}{suffix}")

    # Phase ψ.8.2-A: tradition-based filtering. When the edition declares
    # `traditions_default`, every note whose tradition isn't in that
    # list joins the disabled set. Empty/unset → no-op (set is empty).
    disabled_html_ref_ids |= compute_tradition_disabled_html_ref_ids(edition)

    # Phase ψ.37-B: time-traveling commentary filter. When the edition
    # sets `time_filter_ceiling: <year>`, every note whose source's
    # circa-year exceeds the ceiling (OR whose attribution has no
    # catalogued year — User-original / contemporary) joins the
    # disabled set. None/0/absent → no-op (set is empty); §7.2
    # byte-identical guarantee preserved.
    disabled_html_ref_ids |= compute_time_filtered_html_ref_ids(edition)

    # Phase ψ.8.2-B: tradition labelling. We build a {ref_id → tradition}
    # map for the notes that SURVIVED the ψ.8.2-A filter. Empty when
    # `traditions_default` is unset/empty — the label-injection pass is
    # then skipped entirely so pre-ψ.8 builds stay byte-identical (§7.2).
    ref_id_to_tradition = build_ref_id_to_tradition_map(edition)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    output_path = output_dir / f"Ethiopian_Bible_{edition_id}_{version}_{timestamp}.epub"

    stats = {
        "edition_id": edition_id,
        "version": version,
        "title": edition.get("title", ""),
        "enabled_kinds": len(enabled),
        "disabled_kinds": len(disabled),
        "disabled_notes": len(disabled_html_ref_ids),
        "markers_removed": 0,
        "asides_removed": 0,
        "id_markers_removed": 0,
        "id_asides_removed": 0,
        "vn_links_disabled": 0,
        "verse_popups": bool(edition.get("verse_popups", True)),
        "popup_translation": edition.get("popup_translation", ""),
        "vnote_translations_replaced": 0,
        "vnote_translations_missed": 0,
        "vnote_language_paragraphs_stripped": 0,
        "tradition_labels_applied": 0,
        "page_titles_retitled": 0,
        "output_path": output_path,
        "size_mb": 0.0,
        "skipped": False,
    }

    # Phase ν.2.5-A: read the per-edition verse_popups flag (default True
    # to keep prior builds byte-identical). When False, filter_html will
    # strip clickability from <a class="vn-link"> anchors.
    verse_popups_enabled = bool(edition.get("verse_popups", True))

    # Phase ν.2.5-B + ν.2.7-A: read the per-edition popup_translation
    # and resolve its short label once. The unified runner consumes
    # `edition` for the per-book popup_languages config.
    popup_translation_id = (edition.get("popup_translation") or "").strip()
    popup_translation_short = ""
    if popup_translation_id and verse_popups_enabled:
        from scripts.core import translations as _tx

        meta = _tx.translation_meta(popup_translation_id) or {}
        popup_translation_short = meta.get("short_title", popup_translation_id.upper())

    # Decide whether the unified vnote pass is needed. It runs when
    # popups are on AND either (a) a translation is set OR (b) the
    # edition has explicit popup_languages config that prunes some
    # languages. If neither, the pass would be a no-op so we skip it
    # to keep build times tight.
    needs_vnote_pass = verse_popups_enabled and (
        bool(popup_translation_id)
        or edition.get("popup_languages_default") is not None
        or bool(edition.get("popup_languages_per_book"))
    )

    # Phase ω.20-B — content-addressable cache key. Computed once per
    # build_one call; reused for the lookup-on-entry below and the
    # store-after-success at the bottom of the function. None when the
    # cache module can't compute a key (e.g. the edition record has a
    # non-JSON-serializable field) — in that case the cache is bypassed
    # silently and the existing mtime cache remains the only fast path.
    cache_key: str | None = None
    if not dry_run:
        try:
            from scripts.core import build_cache as _bc

            cache_key = _bc.compute_cache_key(
                edition_id,
                version=version,
            )
        except Exception:
            cache_key = None

    # Phase ω.20-B — content cache hit short-circuit. Runs BEFORE the
    # legacy mtime-based check because content-addressable hits even
    # when the output file in `output_dir` is missing (deleted, moved,
    # cleaned). On a cache hit, copy the cached EPUB into `output_dir`
    # so callers get a real artifact to download/inspect at the
    # expected path — same surface as the mtime branch.
    if cache_key and not dry_run and not force:
        from scripts.core import build_cache as _bc
        from scripts.core import notes_io as _io

        cached = _bc.cache_lookup(cache_key)
        if cached is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            _io.atomic_write_bytes(output_path, cached.read_bytes())
            stats["output_path"] = output_path
            stats["size_mb"] = output_path.stat().st_size / (1024 * 1024)
            stats["skipped"] = True
            stats["cache_hit"] = True
            _write_stats_sidecar(output_path, stats, time.perf_counter() - _t0)
            return stats

    # Incremental: skip if a current build already exists for this version
    if not dry_run and not force:
        existing = is_output_current(output_dir, edition_id, version)
        if existing is not None:
            stats["output_path"] = existing
            stats["size_mb"] = existing.stat().st_size / (1024 * 1024)
            stats["skipped"] = True
            _write_stats_sidecar(existing, stats, time.perf_counter() - _t0)
            return stats

    if dry_run:
        # Simulate filter to count, but don't build
        for f in EPUB_DIR.glob("*.html"):
            text = f.read_text(encoding="utf-8")
            _, counts = filter_html(
                text,
                disabled,
                disabled_html_ref_ids,
                verse_popups_enabled=verse_popups_enabled,
            )
            stats["markers_removed"] += counts["markers"]
            stats["asides_removed"] += counts["asides"]
            stats["id_markers_removed"] += counts.get("id_markers", 0)
            stats["id_asides_removed"] += counts.get("id_asides", 0)
            stats["vn_links_disabled"] += counts.get("vn_links_disabled", 0)
        return stats

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir) / "build"

        # Ignore dotfile directories (e.g. .backups/) and editor cruft.
        # Without this, ensure_backup() snapshots in epub_working/.backups/
        # would be packaged into every per-edition EPUB, doubling its size.
        def _ignore(_d, names):
            return [n for n in names if n.startswith(".") or n.endswith(".bak")]

        shutil.copytree(EPUB_DIR, tmp, ignore=_ignore)

        # Apply theme override (Phase ν.3) — append the chosen theme's CSS
        # to the base stylesheet. CSS last-rule-wins, so theme overrides
        # the defaults without modifying the base file.
        theme_id = edition.get("theme", "classic")
        theme_css = REPO_ROOT / "content" / "themes" / f"{theme_id}.css"
        css_path = tmp / "stylesheet.css"
        if theme_css.is_file() and css_path.is_file():
            with css_path.open("a", encoding="utf-8") as theme_handle:
                theme_handle.write(f"\n\n/* === theme: {theme_id} === */\n")
                theme_handle.write(theme_css.read_text(encoding="utf-8"))
            stats["theme_applied"] = theme_id

        for html_path in tmp.glob("*.html"):
            text = html_path.read_text(encoding="utf-8")
            new_text, counts = filter_html(
                text,
                disabled,
                disabled_html_ref_ids,
                verse_popups_enabled=verse_popups_enabled,
            )
            stats["markers_removed"] += counts["markers"]
            stats["asides_removed"] += counts["asides"]
            stats["id_markers_removed"] += counts.get("id_markers", 0)
            stats["id_asides_removed"] += counts.get("id_asides", 0)
            stats["vn_links_disabled"] += counts.get("vn_links_disabled", 0)

            # Phases ν.2.5-B + ν.2.7-A run as a single pass over the
            # vnote asides — translation swap and language stripping
            # share the same regex anchor so we walk the file once.
            if needs_vnote_pass:
                new_text, vp_counts = _apply_popup_languages_and_translation(
                    new_text,
                    edition,
                    popup_translation_id,
                    popup_translation_short,
                )
                stats["vnote_translations_replaced"] += vp_counts["replaced"]
                stats["vnote_translations_missed"] += vp_counts["missed"]
                stats["vnote_language_paragraphs_stripped"] += vp_counts["language_paragraphs_stripped"]

            # Phase ψ.8.2-B — label surviving editorial-note asides with
            # their tradition. Skipped entirely when the edition has no
            # `traditions_default` (the map is empty), preserving §7.2.
            if ref_id_to_tradition:
                new_text, t_counts = apply_tradition_labels_to_html(
                    new_text,
                    ref_id_to_tradition,
                )
                stats["tradition_labels_applied"] += t_counts["labeled"]

            # Per-file page title: the base scripture chunks carry calibre's
            # default <title>Converted Ebook</title>. Rewrite it to this
            # edition's title (the OPF dc:title is already correct; the chapter
            # XHTML <title>s were not). Generated pages keep their own titles.
            new_text, retitled = _retitle_html_pages(new_text, edition.get("title", ""))
            stats["page_titles_retitled"] += retitled

            if new_text != text:
                html_path.write_text(new_text, encoding="utf-8")

        # Canon filter — drop books not in this edition's canon
        canon_id = edition.get("canon")
        canon_stats: dict = {"dropped_books": 0, "files_removed": 0, "cross_refs_stripped": 0, "files_touched": []}
        dropped_files: set[str] = set()
        dropped_bp_indices: set[int] = set()
        if canon_id:
            all_canons = load_canons()
            canon_def = all_canons.get(canon_id)
            if canon_def:
                canon_books = set(canon_def.get("books", []))
                all_books = config.load_books()
                # Note which files exist before filtering to detect deletions
                files_before = {f.name for f in tmp.glob("*.html")}
                canon_stats = filter_books_for_canon(tmp, canon_books, all_books)
                files_after = {f.name for f in tmp.glob("*.html")}
                dropped_files = files_before - files_after
                # Compute bp-NN indices for spliced-but-not-file-removed books
                for i, book in enumerate(all_books):
                    if book["code"] not in canon_books:
                        bp = book.get("bp", "")
                        m = re.match(r"bp-(\d+)", bp)
                        if m:
                            dropped_bp_indices.add(int(m.group(1)))
                        else:
                            dropped_bp_indices.add(i)
        stats["canon_dropped_books"] = canon_stats["dropped_books"]
        stats["canon_files_removed"] = canon_stats["files_removed"]
        stats["canon_xrefs_stripped"] = canon_stats["cross_refs_stripped"]

        # Patch OPF (kind-based + canon-based + φ.1 font-manifest)
        opf = tmp / "content.opf"
        if opf.is_file():
            opf_text = patch_opf(opf.read_text(encoding="utf-8"), edition, version)
            if dropped_files:
                opf_text = patch_opf_canon(opf_text, dropped_files)
            # φ.1 — register EMBED_FONT_PATHS + legacy EMBED_FONT_PATH
            # entries in the manifest. No-op when both knobs are empty
            # (preserves v1.0 byte-identical reproducibility).
            opf_text = patch_opf_fonts(opf_text)
            opf.write_text(opf_text, encoding="utf-8")

        # Patch nav.xhtml TOC (canon-based — drop dead links to files AND books)
        nav = tmp / "nav.xhtml"
        if nav.is_file() and (dropped_files or dropped_bp_indices):
            nav.write_text(
                patch_nav_canon(nav.read_text(encoding="utf-8"), dropped_files, dropped_bp_indices),
                encoding="utf-8",
            )

        # Patch toc.ncx (legacy EPUB 2 nav — same canon scope)
        ncx = tmp / "toc.ncx"
        if ncx.is_file() and (dropped_files or dropped_bp_indices):
            # Rebuild id_inventory from the post-splice state
            ncx_id_inventory: dict[str, set[str]] = {}
            for f in tmp.glob("*.html"):
                ftext = f.read_text(encoding="utf-8")
                ncx_id_inventory[f.name] = set(re.findall(r'\bid="([^"]+)"', ftext))
            ncx.write_text(
                patch_ncx_canon(ncx.read_text(encoding="utf-8"), ncx_id_inventory),
                encoding="utf-8",
            )

        # Phase ν.6 — Apply per-edition chapter number format +
        # decoration to body chapter headings. Default
        # (format=digit, decoration=plain) is a no-op for back-compat.
        chapter_stats = apply_chapter_decoration(tmp, edition)
        stats["chapters_decorated"] = chapter_stats["chapters_rewritten"]
        stats["chapter_files_touched"] = chapter_stats["files_touched"]

        # Phase ν.6.x — Apply reader's TOC transforms (collapsibility,
        # default-open, and book ornament). Default settings are a
        # no-op for back-compat (Rule §6.5).
        toc_stats = apply_reader_toc_transforms(tmp, edition)
        stats["toc_books_transformed"] = toc_stats["books_transformed"]
        stats["toc_ornaments_inserted"] = toc_stats["ornaments_inserted"]
        stats["toc_details_unwrapped"] = toc_stats["details_unwrapped"]
        stats["toc_defaults_opened"] = toc_stats["defaults_opened"]

        # Phase ν.8 — Apply bilingual ToC labels (Ge'ez/Amharic +
        # English) when the edition opts in via toc_bilingual. Default
        # ("none") is a complete no-op preserving §6.5 byte-identical
        # builds. Runs AFTER apply_reader_toc_transforms so the book
        # anchor is still in its canonical <a href="...#bp-NN"> form
        # for matching.
        bilingual_stats = apply_bilingual_toc(tmp, edition)
        stats["toc_bilingual_style"] = bilingual_stats["toc_style"]
        stats["toc_book_labels_rewritten"] = bilingual_stats["book_labels_rewritten"]
        stats["toc_chapter_labels_rewritten"] = bilingual_stats["chapter_labels_rewritten"]

        # Inject per-edition copyright/credits page
        inject_copyright_page(tmp, edition, version)

        # ψ.19.1 — inject the per-edition reading-plans page (no-op
        # when `enabled_reading_plans` is empty, preserving pre-ψ.19.1
        # build-byte behavior per §6.5).
        rp_stats = inject_reading_plans_page(tmp, edition)
        stats["reading_plans_written"] = rp_stats.get("plans_written", 0)
        stats["reading_plans_total_days"] = rp_stats.get("total_days", 0)

        # Build EPUB
        result = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts" / "build_epub.py"),
                str(output_path),
                "--epub-dir",
                str(tmp),
                "--no-bump",  # don't update dc:date for filtered builds
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"build_epub failed:\n{result.stderr or result.stdout}")

        stats["size_mb"] = output_path.stat().st_size / (1024 * 1024)

    # Phase ω.20-B — warm the content cache after a successful build.
    # Opportunistic: failures here (read-only disk, full disk) MUST NOT
    # fail the build itself — the artifact at output_path is still
    # valid; the next run will just rebuild from scratch.
    if cache_key:
        try:
            from scripts.core import build_cache as _bc

            _bc.cache_store(cache_key, output_path)
        except Exception:
            pass

    # ω.20-C — write the stats sidecar for the freshly-built EPUB.
    _write_stats_sidecar(output_path, stats, time.perf_counter() - _t0)

    return stats


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def cmd_list(eds: list[dict], all_kinds: list[dict]) -> None:
    print()
    for ed in eds:
        try:
            enabled, disabled = compute_enabled_kinds(ed, all_kinds)
        except ValueError as e:
            print(f"  {RED}✗ {ed['id']}: {e}{RESET}")
            continue
        print(f"  {BOLD}{ed['id']:30s}{RESET}  {ed.get('title', '-')}")
        print(
            f"    {DIM}{len(enabled)}/{len(all_kinds)} kinds · "
            f"max_phase={ed.get('max_phase', 'phase3')} · "
            f"audience: {ed.get('target_audience', '-')[:60]}{RESET}"
        )
    print()


def main() -> None:
    p = argparse.ArgumentParser(
        description="Build a per-edition EPUB from the master corpus.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("edition_id", nargs="?", help="edition id (omit with --all or --list)")
    p.add_argument("--all", action="store_true", help="build every edition")
    p.add_argument("--list", action="store_true", help="list editions and what they include")
    p.add_argument("--output-dir", type=Path, default=REPO_ROOT, help="output directory")
    p.add_argument("--version", default="v27", help="version label (default: v27)")
    p.add_argument("--dry-run", action="store_true", help="report filter stats, don't build")
    p.add_argument(
        "--no-parallel", action="store_true", help="build editions sequentially (default is parallel for --all)"
    )
    p.add_argument("--force", action="store_true", help="rebuild editions even when an existing build is current")
    args = p.parse_args()

    eds = config.load_editions()
    if not eds:
        print(f"{RED}ERROR: no editions defined in content/editions.yaml{RESET}", file=sys.stderr)
        sys.exit(2)

    all_kinds = config.load_kinds()

    if args.list:
        cmd_list(eds, all_kinds)
        sys.exit(0)

    if args.all:
        targets = [e["id"] for e in eds]
    elif args.edition_id:
        targets = [args.edition_id]
    else:
        p.error("specify an edition id, --all, or --list")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Sequential when --dry-run (so output is readable) or single edition.
    # Parallel when --all + actual build (each build_one is mostly disk I/O
    # + a subprocess call to build_epub.py, both of which release the GIL).
    if not args.dry_run and len(targets) > 1 and not args.no_parallel:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        failures = 0
        results: dict[str, dict] = {}
        with ThreadPoolExecutor(max_workers=min(len(targets), 5)) as pool:
            future_to_id = {
                pool.submit(build_one, ed_id, args.output_dir, args.version, all_kinds, args.dry_run, args.force): ed_id
                for ed_id in targets
            }
            for fut in as_completed(future_to_id):
                ed_id = future_to_id[fut]
                try:
                    results[ed_id] = fut.result()
                except Exception as e:
                    print(f"  {RED}✗ {ed_id}: {e}{RESET}", file=sys.stderr)
                    failures += 1
        # Render stats in canonical (target) order
        for ed_id in targets:
            if ed_id not in results:
                continue
            stats = results[ed_id]
            print(f"\n{BOLD}{ed_id}{RESET}")
            print(f"  {DIM}{stats['enabled_kinds']} kinds enabled, {stats['disabled_kinds']} disabled{RESET}")
            print(f"  {DIM}filtered: {stats['markers_removed']} markers + {stats['asides_removed']} asides{RESET}")
            tag = f" {DIM}(cached){RESET}" if stats.get("skipped") else ""
            print(f"  {GREEN}✓{RESET} {stats['output_path'].name}  {DIM}({stats['size_mb']:.2f} MB){RESET}{tag}")
        print()
        sys.exit(1 if failures else 0)

    # Sequential path
    failures = 0
    for ed_id in targets:
        print(f"\n{BOLD}{ed_id}{RESET}{DIM}{'  (dry-run)' if args.dry_run else ''}{RESET}")
        try:
            stats = build_one(ed_id, args.output_dir, args.version, all_kinds, args.dry_run, args.force)
        except Exception as e:
            print(f"  {RED}✗ {e}{RESET}", file=sys.stderr)
            failures += 1
            continue

        print(f"  {DIM}{stats['enabled_kinds']} kinds enabled, {stats['disabled_kinds']} disabled{RESET}")
        print(f"  {DIM}filtered: {stats['markers_removed']} markers + {stats['asides_removed']} asides{RESET}")
        if not args.dry_run:
            tag = f" {DIM}(cached){RESET}" if stats.get("skipped") else ""
            print(f"  {GREEN}✓{RESET} {stats['output_path'].name}  {DIM}({stats['size_mb']:.2f} MB){RESET}{tag}")

    sys.exit(0 if failures == 0 else 1)


if __name__ == "__main__":
    main()
