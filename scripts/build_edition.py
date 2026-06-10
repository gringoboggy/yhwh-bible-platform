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
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config  # noqa: E402

_NOTE_ID_RE = re.compile(r"^([a-z0-9]+):(\d+):(\d+)([a-z]*):([a-z][a-z0-9-]*)$")

# Moved to scripts/epub_utils.py + scripts/matter_pages.py (module split 2026-05-25).
# Re-exported here (noqa: F401) so existing `from scripts.build_edition import ...`
# call sites keep working unchanged. The 6 inject_* + 3 helpers are also used below.
from scripts.epub_utils import (  # noqa: E402, F401
    _resolve_publishing,
    _xml_escape_text,
    load_canons,
)
from scripts.matter_pages import (  # noqa: E402, F401
    TOPICAL_INDEX_SOURCES,
    _drop_placeholder_introduction,
    _legend_categories_for_edition,
    _sources_sections,
    build_merged_topic_index,
    inject_back_matter,
    inject_copyright_page,
    inject_dedication_page,
    inject_reading_plans_page,
    inject_symbol_legend_page,
    inject_your_edition_page,
    render_closing_colophon_page,
    render_copyright_page,
    render_dedication_page,
    render_merged_topical_index_page,
    render_reading_plans_page,
    render_reference_tables_page,
    render_sources_page,
    render_symbol_legend_page,
    render_your_edition_page,
)

EPUB_DIR = REPO_ROOT / "epub_working"

# mint-9 #18: ANSI colour constants live in scripts.core.ui — import (not
# redefine) the single source of truth. Re-exported here (noqa: F401) so
# existing `from scripts.build_edition import GREEN` callers keep working.
from scripts.core.ui import (  # noqa: E402, F401
    BOLD,
    DIM,
    GREEN,
    RED,
    RESET,
    YELLOW,
)


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
        # Strategy-B books have no id_prefix; inject.py falls back to bxx as the
        # id base (inject.py:674-677), so the live HTML ref-id is ref-<bxx><cc><vv>.
        # Mirror that fallback here or these books' notes never match the disabled
        # set and silently survive tradition/time filters (mint-9 #2).
        prefix = book.get("id_prefix") or book.get("bxx")
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


def _iter_note_ref_symbols():
    """Walk every note tuple on disk and yield
    ``(ref_id, note_id, book_code, chapter, verse, suffix, kind, category)``.

    Sibling of ``_iter_note_ref_traditions`` that surfaces the chapter/verse/
    kind/category baked into each note, for the Phase-ρ.3 per-coordinate symbol
    resolver. ``note_id`` is the canonical ``book:ch:vs[suffix]:kind`` form;
    ``ref_id`` is the compact HTML id ``ref-<prefix><cc><vv><suffix>`` (same
    Strategy-B ``id_prefix``→``bxx`` fallback as the tradition walk).
    """
    from scripts.core.notes_io import load_notes

    books_idx = config.books_by_code()
    cat_by_kind = {k.get("code"): k.get("category") for k in config.load_kinds()}
    notes_dir = REPO_ROOT / "content" / "notes"
    for book_path in sorted(notes_dir.glob("*.py")):
        if book_path.stem == "__init__" or book_path.stem.startswith("_"):
            continue
        book_code = book_path.stem
        book = books_idx.get(book_code) or {}
        prefix = book.get("id_prefix") or book.get("bxx")
        if not prefix:
            continue
        for tup in load_notes(book_path) or []:
            if not isinstance(tup, tuple) or len(tup) < 8:
                continue
            try:
                ch_i = int(tup[0])
                vs_i = int(tup[1])
            except (TypeError, ValueError):
                continue
            suffix = tup[2] or ""
            kind = tup[4]
            ref_id = f"ref-{prefix}{ch_i:02d}{vs_i:02d}{suffix}"
            note_id = f"{book_code}:{ch_i}:{vs_i}{suffix}:{kind}"
            yield ref_id, note_id, book_code, ch_i, vs_i, suffix, kind, cat_by_kind.get(kind)


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


# ──────────────────────────────────────────────────────────────────────────────
# Per-book / per-chapter symbol-token helpers (Phase A — ρ.3)
#
# These mirror decode_per_book_traditions / encode_per_book_traditions above
# but work with the open-ended token space of category ids ∪ kind codes
# (e.g. "xref", "comm", "comm-patristic") rather than the fixed TRADITION_IDS
# set.  Used by the hierarchical-customization symbol engine.
# ──────────────────────────────────────────────────────────────────────────────


def _valid_symbol_tokens() -> set[str]:
    """The set of legal per-scope symbol tokens: category ids ∪ kind codes."""
    from scripts.core import config as _cfg

    cats = {c.get("id") for c in _cfg.load_categories()}
    kinds = {k.get("code") for k in _cfg.load_kinds()}
    return {t for t in (cats | kinds) if t}


def decode_per_book_tokens(raw) -> dict[str, list[str]]:
    """Decode ``note_families_{on,off}_per_book`` on-disk format.

    Flat list of ``"<book>=<tok1>,<tok2>"`` strings (tokens are a category
    id or a kind code). Empty value (``"gen="``) is meaningful: an explicit
    empty override. Accepts None / [] / {} / list[str] / dict. Mirrors
    ``decode_per_book_traditions``.
    """
    if raw is None or raw == [] or raw == {}:
        return {}
    if isinstance(raw, dict):
        return {str(k): list(v or []) for k, v in raw.items()}
    out: dict[str, list[str]] = {}
    for entry in raw:
        if not isinstance(entry, str) or "=" not in entry:
            continue
        code, blob = entry.split("=", 1)
        code = code.strip()
        if not code:
            continue
        out[code] = [s.strip() for s in blob.split(",") if s.strip()] if blob.strip() else []
    return out


def encode_per_book_tokens(per_book: dict[str, list[str]]) -> list[str]:
    """Inverse of decode_per_book_tokens. Sorts by canonical book order
    (§6.1); drops unknown tokens (validate-at-write, like traditions)."""
    if not per_book:
        return []
    from scripts.core import config as _cfg

    valid = _valid_symbol_tokens()
    book_order = list(_cfg.books_by_code().keys())
    rank = {code: i for i, code in enumerate(book_order)}
    out: list[str] = []
    for code, toks in sorted(per_book.items(), key=lambda it: (rank.get(it[0], len(book_order) + 1), it[0])):
        clean = [t for t in (toks or []) if t in valid]
        out.append(f"{code}={','.join(clean)}")
    return out


def decode_per_chapter_tokens(raw) -> dict[str, list[str]]:
    """Decode ``note_families_{on,off}_per_chapter``. Key is ``"<book>:<ch>"``;
    otherwise identical to decode_per_book_tokens."""
    if raw is None or raw == [] or raw == {}:
        return {}
    if isinstance(raw, dict):
        return {str(k): list(v or []) for k, v in raw.items()}
    out: dict[str, list[str]] = {}
    for entry in raw:
        if not isinstance(entry, str) or "=" not in entry:
            continue
        key, blob = entry.split("=", 1)
        key = key.strip()
        if not key:
            continue
        out[key] = [s.strip() for s in blob.split(",") if s.strip()] if blob.strip() else []
    return out


def encode_per_chapter_tokens(per_chapter: dict[str, list[str]]) -> list[str]:
    """Inverse of decode_per_chapter_tokens. Sorts by canonical book order
    then NUMERIC chapter (so gen:2 precedes gen:10); drops unknown tokens."""
    if not per_chapter:
        return []
    from scripts.core import config as _cfg

    valid = _valid_symbol_tokens()
    book_order = list(_cfg.books_by_code().keys())
    rank = {code: i for i, code in enumerate(book_order)}

    def _sort_key(item: tuple[str, list[str]]) -> tuple[int, str, int]:
        key = item[0]
        book, _, ch = key.partition(":")
        try:
            ch_n = int(ch)
        except ValueError:
            ch_n = 1 << 30
        return (rank.get(book, len(book_order) + 1), book, ch_n)

    out: list[str] = []
    for key, toks in sorted(per_chapter.items(), key=_sort_key):
        clean = [t for t in (toks or []) if t in valid]
        out.append(f"{key}={','.join(clean)}")
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


def _symbol_overridden_kinds(edition: dict, all_kinds) -> set[str]:
    """Kind codes touched by ANY per-book/per-chapter symbol token (category
    tokens expanded to their kinds) ∪ kinds named by ``enabled_note_ids``.
    These are resolved at ref-id granularity (so a per-coordinate ON can
    re-include them); all OTHER edition-disabled kinds keep the efficient
    whole-kind strip. Cheap — no corpus walk."""
    cat_to_kinds: dict[str, set[str]] = {}
    valid_kinds: set[str] = set()
    for k in all_kinds:
        code = k.get("code")
        valid_kinds.add(code)
        cat_to_kinds.setdefault(k.get("category"), set()).add(code)

    out: set[str] = set()

    def _absorb(tokens):
        for t in tokens:
            if t in cat_to_kinds:
                # Category token → expand to every kind in that category.
                # Checked BEFORE the kind-code path because ``comm`` is both a
                # category id and a bare kind code; the category meaning wins
                # (mirrors how enabled_kind_codes_for checks cat before code).
                out.update(cat_to_kinds[t])
            elif t in valid_kinds:
                out.add(t)

    for field in ("note_families_on_per_book", "note_families_off_per_book"):
        for toks in decode_per_book_tokens(edition.get(field)).values():
            _absorb(toks)
    for field in ("note_families_on_per_chapter", "note_families_off_per_chapter"):
        for toks in decode_per_chapter_tokens(edition.get(field)).values():
            _absorb(toks)
    for nid in edition.get("enabled_note_ids") or []:
        m = _NOTE_ID_RE.match(nid)
        if m:
            out.add(m.group(5))
    return out


def compute_symbol_disabled_html_ref_ids(edition: dict, all_kinds, overridden_kinds: set[str]) -> set[str]:
    """Phase ρ.3 — ref-ids of notes whose kind resolves OFF at their coordinate
    under the per-book/per-chapter symbol overrides. Mirrors
    ``compute_tradition_disabled_html_ref_ids``. Only processes notes whose kind
    is in ``overridden_kinds`` (non-overridden kinds are handled by the edition-
    wide whole-kind strip). SHORT-CIRCUITS to an empty set when nothing is
    overridden, so standard builds never walk the corpus.

    Individual ``disabled_note_ids`` / ``enabled_note_ids`` are applied in
    ``build_one`` (force-on is subtracted from the final set), not here.
    """
    if not overridden_kinds:
        return set()
    from scripts.core.config import enabled_kind_codes_for

    out: set[str] = set()
    cache: dict[tuple, set[str]] = {}
    for ref_id, _note_id, book, chapter, _verse, _suffix, kind, _cat in _iter_note_ref_symbols():
        if kind not in overridden_kinds:
            continue
        key = (book, chapter)
        enabled = cache.get(key)
        if enabled is None:
            enabled = enabled_kind_codes_for(edition, all_kinds, book, chapter)
            cache[key] = enabled
        if kind not in enabled:
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
        # Strategy-B bxx fallback — see _iter_note_ref_traditions (mint-9 #2).
        prefix = book.get("id_prefix") or book.get("bxx")
        if not prefix:
            continue
        notes = load_notes(book_path) or []
        for tup in notes:
            # mint-10 #high: the minimum valid note is 8-field; the
            # attribution at [8] is OPTIONAL. The old `< 9` skip silently
            # dropped EVERY legacy 8-field note from the time-filter walk,
            # so a positive time_filter_ceiling never disabled them (it
            # silently passed them through). Gate on the real minimum and
            # read attribution defensively — mirrors _iter_note_ref_traditions
            # (len(tup) < 8) and NoteSpec.from_tuple.
            if not isinstance(tup, tuple) or len(tup) < 8:
                continue
            ch = tup[0]
            vs = tup[1]
            suffix = tup[2] or ""
            attribution = (tup[8] if len(tup) > 8 else "") or ""
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


def _replace_verse_popup_translation(
    html_text: str,
    translation_id: str,
    translation_short: str = "",
) -> tuple[str, dict]:
    """Swap the English text inside every vnote aside with text from
    ``translation_id`` (Phase ν.2.5-B).

    ⚠ NOT YET WIRED INTO THE BUILD (flagged mint-7 D3, 2026-05-31): a complete,
    tested feature (5 tests in test_scripts.py) with no production caller yet.
    Surfacing it is an edition-feature — editions.yaml schema + a /customize
    control + a build_edition pass (RULES §9 "Add a new edition feature") — and
    is deferred as out-of-scope for the mint-7 debt pass. KEPT, not deleted: it
    is real tested behavior, not dead code.

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


def _resolve_popup_languages(edition: dict, book_code: str, chapter=None, verse=None) -> set[str]:
    """Resolve the active popup-language set for one (edition, book[, chapter, verse]).

    Most-specific-wins (Phase ρ.3 / spec §3.4-popup):
      1. popup_languages_per_verse["book:ch:vs"]   if present
      2. popup_languages_per_chapter["book:ch"]    if present
      3. popup_languages_per_book[book]            if present
      4. popup_languages_default                   if present
      5. DEFAULT_POPUP_WITNESSES                    (back-compat default)

    Calling without chapter/verse (the legacy 2-arg form) skips tiers 1-2 and
    behaves exactly as before — the invariant existing callers rely on. An
    explicit empty list at any tier (``"gen:1:1="``) is a meaningful override
    ("no popups on this verse"); ``is None`` checks preserve that vs absence.

    Returns a set of language ids — only ids in POPUP_LANGUAGES are retained;
    legacy ids (english/hebrew/greek) map to version ids via resolve_version_id.
    """
    raw: list[str] | None = None

    if chapter is not None and verse is not None:
        per_verse = decode_per_verse_languages(edition.get("popup_languages_per_verse"))
        vkey = f"{book_code}:{chapter}:{verse}"
        if vkey in per_verse:
            raw = per_verse[vkey]

    if raw is None and chapter is not None:
        per_chapter = decode_per_chapter_languages(edition.get("popup_languages_per_chapter"))
        ckey = f"{book_code}:{chapter}"
        if ckey in per_chapter:
            raw = per_chapter[ckey]

    if raw is None:
        per_book = decode_per_book_languages(edition.get("popup_languages_per_book"))
        if book_code in per_book:
            raw = per_book[book_code]
        elif edition.get("popup_languages_default") is not None:
            raw = edition.get("popup_languages_default")
        else:
            # §4.3 — no default → the default witness set (Hebrew + Greek LXX/NT
            # + Latin + Arabic), NOT every baked version.
            return {m for m in _pv.DEFAULT_POPUP_WITNESSES if m in POPUP_LANGUAGES}

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


def decode_per_chapter_languages(raw) -> dict[str, list[str]]:
    """Decode ``popup_languages_per_chapter``. Key is ``"<book>:<ch>"``;
    otherwise identical to ``decode_per_book_languages`` (explicit-empty
    ``"gen:1="`` → ``[]`` is a meaningful override)."""
    if raw is None or raw == [] or raw == {}:
        return {}
    if isinstance(raw, dict):
        return {str(k): list(v or []) for k, v in raw.items()}
    out: dict[str, list[str]] = {}
    for entry in raw:
        if not isinstance(entry, str) or "=" not in entry:
            continue
        key, blob = entry.split("=", 1)
        key = key.strip()
        if not key:
            continue
        out[key] = [s.strip() for s in blob.split(",") if s.strip()] if blob.strip() else []
    return out


def decode_per_verse_languages(raw) -> dict[str, list[str]]:
    """Decode ``popup_languages_per_verse``. Key is ``"<book>:<ch>:<vs>"``;
    same parsing as ``decode_per_chapter_languages``."""
    return decode_per_chapter_languages(raw)


def _encode_keyed_languages(per_key: dict[str, list[str]], key_parts: int) -> list[str]:
    """Shared encoder for the per-chapter (key_parts=2 → book:ch) and per-verse
    (key_parts=3 → book:ch:vs) language maps. Sorts by canonical book order then
    numeric chapter (then numeric verse); filters unknown ids against
    POPUP_LANGUAGES (validate-at-write, like encode_per_book_languages)."""
    if not per_key:
        return []
    from scripts.core import config as _cfg

    book_order = list(_cfg.books_by_code().keys())
    rank = {code: i for i, code in enumerate(book_order)}

    def _sort_key(item):
        parts = item[0].split(":")
        book = parts[0]
        nums = []
        for p in parts[1:key_parts]:
            try:
                nums.append(int(p))
            except ValueError:
                nums.append(1 << 30)
        return (rank.get(book, len(book_order) + 1), book, *nums)

    out: list[str] = []
    for key, langs in sorted(per_key.items(), key=_sort_key):
        clean = [L for L in (langs or []) if L in POPUP_LANGUAGES]
        out.append(f"{key}={','.join(clean)}")
    return out


def encode_per_chapter_languages(per_chapter: dict[str, list[str]]) -> list[str]:
    """Inverse of decode_per_chapter_languages (key ``book:ch``)."""
    return _encode_keyed_languages(per_chapter, key_parts=2)


def encode_per_verse_languages(per_verse: dict[str, list[str]]) -> list[str]:
    """Inverse of decode_per_verse_languages (key ``book:ch:vs``)."""
    return _encode_keyed_languages(per_verse, key_parts=3)


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
        "kjv_fallbacks": 0,
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
        active_langs = _resolve_popup_languages(edition, book, chapter=ch, verse=vs)

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
        # §4.3 last-resort English: the popups were built on a KJV floor, so ~6%
        # of verses carry ONLY the English (vnote-text). Dropping kjv there would
        # empty the popup AND break any note cross-ref that targets this vnote
        # (epubcheck RSC-012). So when NO active witness is present in this verse,
        # KEEP the English as a fallback; where a real witness exists the
        # redundant English is dropped as intended. Guarded by `active_classes`
        # so the standalone Bibles (popup_languages_default = []) are untouched.
        if active_classes and not any(f'class="{cc}"' in body for cc in active_classes):
            active_classes = active_classes | {"vnote-text"}
            stats["kjv_fallbacks"] += 1
        for lang_id in ALL_POPUP_LANGUAGES:
            if POPUP_LANGUAGES[lang_id]["content_class"] in active_classes:
                continue
            body, n = _strip_language_paragraph(body, lang_id)
            stats["language_paragraphs_stripped"] += n

        return opening + body + closing

    new_html = _VNOTE_ASIDE_RE.sub(_process, html_text)
    return new_html, stats


def _build_disabled_kind_res(disabled_kinds: set) -> tuple[re.Pattern | None, re.Pattern | None]:
    """Build ONE marker regex + ONE aside regex matching ANY of ``disabled_kinds``
    (a single anchored alternation), or ``(None, None)`` when nothing is disabled.

    The consolidated form of ``filter_html``'s historical per-kind loop: every
    ``note-ref`` / ``note`` element carries exactly one ``note-{kind}`` class
    (mutually exclusive) and markers never nest, so removing all disabled kinds
    in one alternation pass deletes the same element SET — and yields the same
    total ``markers`` / ``asides`` counts — as deleting them kind by kind, at 2
    scans per file instead of ~2N. Kinds are sorted so the compiled pattern is
    deterministic; the trailing ``"`` after the group keeps a kind name that
    prefixes another (e.g. ``xref`` vs ``xref-foo``) from mis-matching.
    """
    if not disabled_kinds:
        return None, None
    alt = "|".join(re.escape(k) for k in sorted(disabled_kinds))
    marker_re = re.compile(rf'<a class="note-ref note-(?:{alt})"[^>]*>.*?</a>', re.DOTALL)
    aside_re = re.compile(rf'<aside class="note note-(?:{alt})"[^>]*>.*?</aside>', re.DOTALL)
    return marker_re, aside_re


def filter_html(
    html_text: str,
    disabled_kinds: set,
    disabled_html_ref_ids: set | None = None,
    verse_popups_enabled: bool = True,
    *,
    kind_marker_re: re.Pattern | None = None,
    kind_aside_re: re.Pattern | None = None,
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

    # ---- Phase λ: filter by KIND (whole categories of notes). ONE alternation
    # over every disabled kind (2 scans/file) instead of recompiling + scanning
    # per kind (~2N scans/file). Byte-identical — see _build_disabled_kind_res:
    # mutually-exclusive per-element kind classes + non-nesting markers make the
    # removed set + the totals independent of batching. build_one pre-builds the
    # pair once per edition and passes it in; other callers get the in-function
    # build from disabled_kinds.
    # Build the pair here unless BOTH were supplied (they're always produced
    # together by _build_disabled_kind_res, so `or` keeps a half-supplied pair
    # from reaching a None.subn()).
    if kind_marker_re is None or kind_aside_re is None:
        kind_marker_re, kind_aside_re = _build_disabled_kind_res(disabled_kinds)
    if kind_marker_re is not None:
        new_text, n = kind_marker_re.subn("", new_text)
        counts["markers"] += n
        new_text, n = kind_aside_re.subn("", new_text)
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
    Dublin-Core metadata. Ω.0 pivot: ISBN fields dropped — see term-ref-ok
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

    # K-R2-8: <dc:description> is reader-visible (the e-reader library synopsis).
    # Use the edition's own description when set; otherwise compose a neutral,
    # always-true line — the base copy is Ethiopian-specific and would misdescribe
    # every other edition's library card.
    desc = (edition.get("description") or "").strip()
    if not desc:
        desc = f"{title}. Compiled from public-domain translations by the YHWH Ya' Way project."
    new_text = re.sub(
        r"<dc:description>[^<]*</dc:description>",
        f"<dc:description>{_xml_escape(desc)}</dc:description>",
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
    bcp47 = "en-US" if primary_lang == "en" else primary_lang
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

    # Ω.0 pivot (2026-05-14): ISBN dropped. EPUB 3 dc:identifier term-ref-ok
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
        # Ω.0 pivot: generator URN replaces the former book identifier.
        # Deterministic per edition id; not a commercial identifier.
        + f'    <dc:identifier id="pub-id">{_xml_escape(edition_urn)}</dc:identifier>\n'
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
    # alone is not sufficient. Apple Books treats this as a soft fail. term-ref-ok
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
# §4.5 — per-book title-page rendering style. framed = the per-book art as a
# contained plate above the title text, inside the border (cross-reader-safe:
# display:inline-block, renders on Kobo + aligns on Apple); full-bleed = the
# art fills the page behind a dark scrim with the title overlaid via
# position:absolute (defeats Kobo's engine → no art; misaligns on Apple over a
# variable-height image). Unset → "framed" (the cross-reader default, 2026-06-05
# reading-experience overhaul). full-bleed stays available as an opt-in.
TITLE_PAGE_STYLES = {"full-bleed", "framed"}
# §4.2 verse_popup_style — original-language popup layout. "cards" (default):
# each witness in a tinted card with a colored spine. "stack": the flat
# source-label-over-text layout. CSS-only — applied by appending the variant's
# rules to the edition stylesheet at build time (no base re-bake).
VERSE_POPUP_STYLES = {"cards", "stack"}
# CSS appended to an edition stylesheet when verse_popup_style == "cards" (the
# default): layers tinted-card chrome + a colored spine onto the existing flat
# .vnote-hebrew/.vnote-greek blocks. "stack" leaves the base flat layout. All
# properties are EPUB-3-allowed (background / border / padding / border-radius).
_VERSE_POPUP_CARDS_CSS = """
/* === §4.2 verse_popup_style=cards — tinted witness cards with colored spines === */
.vnote-hebrew, .vnote-greek { padding: 0.4em 0.6em; border-radius: 0.3em; }
.vnote-hebrew { background: rgba(184, 134, 11, 0.07); border-left: 3px solid #B8860B; }
.vnote-greek  { background: rgba(91, 46, 140, 0.06); border-left: 3px solid #5B2E8C; }
"""


def apply_verse_popup_style(stylesheet_css: str, style: str) -> str:
    """Append the verse_popup_style variant CSS to an edition stylesheet.

    "cards" (default) appends tinted-card-with-spine rules; "stack" is the flat
    base layout (no append). Mirrors the theme-override append — the popup HTML
    is unchanged, so this needs no base re-bake."""
    style = (style or "cards").strip() or "cards"
    if style == "cards":
        return stylesheet_css + _VERSE_POPUP_CARDS_CSS
    return stylesheet_css


# §4.4 note_popup_style — note/aside popup layout. "chip" (default): the
# category label renders as a tinted chip. "pills": in-note cross-references
# render as bordered, tappable pills. CSS-only — appended to the edition
# stylesheet at build time, targeting the EXISTING baked classes (.note-label
# and in-note `a:not(.note-back)`), so no base re-bake. (The §4.4 symbol-into-
# note relocation + stray-‖ removal are base-HTML changes tracked under the
# separate symbols-into-notes Wave-3 task — not this layout setting.)
NOTE_POPUP_STYLES = {"chip", "pills"}

# §4.1 marker_style — how inline note markers render.
#
#   "numbers" — the historical per-note superscript NUMBER, one inline marker
#     per note (the inline category glyph is dropped so nothing renders as
#     tofu). Realized BASE-WIDE by the re-bake (resync_marker_glyphs numbers the
#     shared base); the build's renumber_markers pass closes the gaps a kind/id
#     filter leaves so every edition reads 1,2,3…
#
#   "badge" (DEFAULT, Phase 5) — clean scripture with ONE note-count badge per
#     verse → tap → that verse's notes as a list, via the native EPUB3
#     popup-footnote contract (noteref → footnote, NO JavaScript so it works on
#     e-ink Kobo). The real cure for "too cluttered" (Genesis 1's ~93 markers
#     collapse to ~31 verse badges) WITH every note still ON. Realized at BUILD
#     TIME by apply_badge_markers() as a per-edition post-pass over the temp
#     HTML — epub_working/ stays the canonical "numbers" form (no base re-bake).
MARKER_STYLES = {"numbers", "badge"}

# The code default when an edition pins no marker_style (badge is the §4.1
# intended display; numbers stays selectable). Read by build_one + surfaced as
# the /customize and api_customize_data default.
DEFAULT_MARKER_STYLE = "badge"

# Appended when note_popup_style == "chip" (the default): a rounded tinted
# background on the category label so "Note." / "Topic." / "Cite." reads as a
# chip. All EPUB-3-allowed (display / padding / border-radius / background).
_NOTE_POPUP_CHIP_CSS = """
/* === §4.4 note_popup_style=chip — category label as a tinted chip === */
.note .note-label { display: inline-block; padding: 0.02em 0.5em; border-radius: 0.8em; background: rgba(91, 46, 140, 0.08); }
"""
# Appended when note_popup_style == "pills": in-note cross-reference links
# (every <a> inside a .note that is NOT the .note-back glyph and NOT the
# .note-sym category-symbol link) become bordered, rounded, tappable pills.
# EPUB-3-allowed (display / padding / margin / border / border-radius /
# text-decoration).
_NOTE_POPUP_PILLS_CSS = """
/* === §4.4 note_popup_style=pills — in-note cross-references as tappable pills === */
.note a:not(.note-back):not(.note-sym) { display: inline-block; padding: 0.02em 0.55em; margin: 0.08em 0.12em; border: 1px solid #B8860B; border-radius: 0.9em; text-decoration: none; }
"""


def apply_note_popup_style(stylesheet_css: str, style: str) -> str:
    """Append the note_popup_style variant CSS to an edition stylesheet.

    "chip" (default) appends a tinted label-chip rule; "pills" appends a pill
    rule for in-note cross-references. Both are CSS-only against the existing
    baked classes (the popup HTML is unchanged), so neither needs a base
    re-bake. Mirrors apply_verse_popup_style / the theme-override append."""
    style = (style or "chip").strip() or "chip"
    if style == "pills":
        return stylesheet_css + _NOTE_POPUP_PILLS_CSS
    return stylesheet_css + _NOTE_POPUP_CHIP_CSS


# Per-category group spine for the S2 cascade — reuses the EXACT hues already in
# epub_working/stylesheet.css:751-791 (the `[class*="note-{cat}-"]` left-border
# colours); `topic` has no shipped spine, so it gets the one new hue. The group
# colour is carried by border-left (a survivable property), the header by
# weight + small-caps + a border-bottom — so the cascade stays legible and
# category-identifiable with backgrounds/embedded-fonts off (spec §2 + §5.2).
_CASCADE_CATEGORY_HUES = {
    "lang": "#8B6508",
    "text": "#A0202C",
    "xref": "#5C2E91",
    "hist": "#8B5A2B",
    "lit": "#4A5568",
    "comm": "#0B3D91",
    "compare": "#1F5E5E",
    "dev": "#8C3F5F",
    "liturgy": "#B8860B",
    "apol": "#2E5E3E",
    "modern": "#4A6FA5",
    "ped": "#6B5B4A",
    "vis": "#525E2C",
    "dist": "#4A2E5C",
    "topic": "#5A5F7E",
}

_NOTE_CASCADE_CSS = (
    "\n/* === S2 note cascade — verse→category→source→note (reader-robust) === */\n"
    ".verse-notes .vn-group { margin: 0.55em 0; }\n"
    ".verse-notes .vn-cat-head { font-weight: 700; font-variant-caps: small-caps;\n"
    "  letter-spacing: 0.04em; font-size: 0.86em; margin: 0.15em 0 0.3em;\n"
    "  padding-bottom: 0.12em; border-bottom: 1px solid rgba(110, 88, 64, 0.35); }\n"
    ".verse-notes .vn-cat-sym { margin-right: 0.3em; }\n"
    ".verse-notes .vn-source { margin-left: 0.7em; margin-bottom: 0.25em; }\n"
    ".verse-notes .vn-source-byline { font-style: italic; font-weight: 600;\n"
    "  font-size: 0.82em; color: #6E5840; margin: 0.2em 0 0.1em; }\n"
    ".verse-notes .vn-source .vn-item { margin-left: 0.5em; }\n"
    + "".join(
        f".verse-notes .vn-group.note-cat-{cat} {{ border-left: 3px solid {hue}; padding-left: 0.6em; }}\n"
        for cat, hue in _CASCADE_CATEGORY_HUES.items()
    )
)


def apply_note_cascade_css(stylesheet_css: str) -> str:
    """Append the S2 cascade's robust-layer CSS — the 15 per-category group spines
    plus the header / source / byline / indent rules (spec §2). Pure CSS against
    the cascade classes the build emits (the popup HTML is otherwise unchanged), so
    no base re-bake is needed. Mirrors apply_note_popup_style; appended only when
    ``note_group_by_category`` is on for the edition."""
    return stylesheet_css + _NOTE_CASCADE_CSS


# ----------------------------------------------------------------------
# §4.1 marker_style=badge — build-time per-edition transform
# ----------------------------------------------------------------------
#
# Collapse a verse's N per-note markers into ONE count badge, and merge that
# verse's N per-note asides into ONE listing aside, using the native EPUB3
# popup-footnote contract (noteref → footnote, no JS). Runs over the per-edition
# temp HTML AFTER the kind/canon/tradition filter passes (so the file holds only
# THIS edition's surviving notes); epub_working/ is never touched.
#
# Verse grouping is BY POSITION, not by parsing the marker id's ambiguous prefix:
# we walk each book's verse regions with inject's proven locators
# (find_verse_region / find_chapter_region_b+find_verse_region_b) and collect the
# `id="ref-{full_id}"` markers that physically fall inside each region. That maps
# every surviving marker to its (code, ch, v) — including verse-end-fallback
# markers — exactly as the reader sees them.

# One whole per-note inline marker element: <a class="note-ref note-X" id="ref-…"
# …><sup …>glyph</sup></a>. note-ref content is only the <sup>, so .*? is tight.
# Group 1 = full_id.
_BADGE_MARKER_RE = re.compile(
    r'<a class="note-ref note-[a-z][a-z0-9-]*" id="ref-([^"]+)"[^>]*>.*?</a>',
    re.DOTALL,
)

# The per-note back-link (↩) inside an aside body. Dropped on merge — the merged
# aside carries ONE back-link in its verse header instead.
_NOTE_BACK_RE = re.compile(r'<a href="#ref-[^"]+" class="note-back"[^>]*>.*?</a>\s*', re.DOTALL)

# RX-beta2 ③: fixed most-useful → least-useful category order for the badge
# popup, with the long topical block always LAST. Document order is preserved
# within a category (stable sort). Unknown categories sort just above topical.
_POPUP_CATEGORY_ORDER = (
    "hist",
    "comm",
    "xref",
    "text",
    "lang",
    "lit",
    "compare",
    "apol",
    "dev",
    "liturgy",
    "ped",
    "modern",
    "vis",
    "dist",
    "topic",
)
_POPUP_CATEGORY_RANK = {c: i for i, c in enumerate(_POPUP_CATEGORY_ORDER)}
_POPUP_CATEGORY_FALLBACK_RANK = _POPUP_CATEGORY_ORDER.index("topic") - 1


def _badge_extract_note_kind(marker_html: str) -> str:
    """The kind token (e.g. ``lang-hebrew``) from a per-note marker element."""
    m = re.match(r'<a class="note-ref note-([a-z][a-z0-9-]*)"', marker_html)
    return m.group(1) if m else "comm"


def _badge_aside_inner_to_row(inner: str, kind: str) -> str:
    """Turn one per-note aside's inner content into one merged ``.vn-item`` row.

    Drops the per-note back-link (↩) but KEEPS everything else: the note-sym
    symbol-link, the note-label, the body, and any tradition-label paragraph. The
    inner content is already balanced XHTML — a single ``<p>``/``<div>`` flow
    wrapper, optionally preceded by a ``<p class="note-tradition-label">`` — so we
    wrap it whole in a ``<div class="vn-item note-{kind}">`` block (a <div> may
    legally hold those <p>/<div> children) rather than unwrapping. Unwrapping is
    unsafe: the tradition-label <p> makes two top-level elements, and a greedy
    unwrap would splice their tags and break well-formedness (epubcheck RSC-016).
    """
    body = _NOTE_BACK_RE.sub("", inner, count=1).strip()
    return f'<div class="vn-item note-{kind}">{body}</div>'


# beta-3 (h): categories whose notes legitimately recur verse-to-verse — never
# cross-verse-deduped. Cross-references and topical entries are per-verse by design;
# everything else (manuscript witnesses, commentary, word studies, …) that repeats
# a BYTE-IDENTICAL body across verses is redundant and shown once per book.
_XVERSE_DEDUP_EXCLUDE = {"xref", "topic"}


# ----------------------------------------------------------------------
# Note-presentation rehaul — build-time, lossless, option-gated transforms
# that run INSIDE apply_badge_markers (badge mode only). See
# docs/superpowers/specs/2026-06-08-note-presentation-rehaul-design.md
# (re-verified against the live corpus 2026-06-08; the spec's S3a comma-split
# and source-key boilerplate-strip were corrected before implementation).
#
# S1 — attribution/label de-dup. A leaf note's <span class="note-label"> is
# suppressed when it merely repeats the kind's default label (85,936/91,733
# notes), or when the body self-attributes (comm-ethiopian inner byline). Both
# are lossless: the distinguishing text survives in the kind/category header or
# the body. epub_working/ is never touched — these operate on the per-edition
# temp tree, gated per-edition; an unset flag is a zero-touch no-op.
# ----------------------------------------------------------------------

# A self-attributing comm-ethiopian note carries its OWN inner father->work->(date)
# byline: <strong>Father</strong> <em>Work</em> <small>(date)</small>. In the STORED body
# that byline sits inside an <aside class="note-comm-ethiopian"> wrapper (1579/1589
# comm-ethiopian bodies; the other 10 are plain User-authored and keep their label). But
# apply_badge_markers reads the BAKED HTML, where the sanitizer has STRIPPED that inner
# <aside> (aside is not in html_sanitize.ALLOWED_TAGS) — only the byline triad and the
# kind's `note-comm-ethiopian` wrapper class survive. So detect the SURVIVING baked shape,
# NOT the stored <aside> prefix (matching that prefix against a baked row is ALWAYS False —
# the dead-suppression bug Mac's S2-cascade review caught, 2026-06-09).
_SELF_ATTRIBUTING_BYLINE_RE = re.compile(r"<strong>[^<]*</strong>\s*<em>[^<]*</em>\s*<small>[^<]*</small>")

# The per-note label span inject.build_aside emits. Its text is html.escaped (never
# contains '<'), so a single non-greedy [^<]* is exact (group 1 = the label text); the
# one trailing space from build_aside's "</span> " is consumed with it.
_NOTE_LABEL_SPAN_RE = re.compile(r'<span class="note-label">([^<]*)</span> ?')

_REHAUL_TAG_RE = re.compile(r"<[^>]+>")


def _normalize_label_text(s: str | None) -> str:
    """Normalise a label/default for the S1 equality test: trim, strip ONE trailing
    '.', trim, casefold. Stripping only one dot keeps a future ellipsis label from
    collapsing onto the kind default."""
    t = (s or "").strip()
    if t.endswith("."):
        t = t[:-1]
    return t.strip().casefold()


def _is_self_attributing_comm_ethiopian(row_html: str) -> bool:
    """True iff a BAKED comm-ethiopian row carries its own inner father->work->(date)
    byline, so the outer note-label / group byline is redundant. Keyed on the kind's
    surviving ``note-comm-ethiopian`` wrapper class AND the <strong>/<em>/<small> byline
    triad — both survive the bake; the stored inner <aside> does not. The stored body
    carries both too, so a stored-form caller stays correct (the helper is a superset)."""
    s = row_html or ""
    return "note-comm-ethiopian" in s and _SELF_ATTRIBUTING_BYLINE_RE.search(s) is not None


@lru_cache(maxsize=1)
def _kind_default_labels() -> dict:
    """``kind -> normalised default label`` from kinds.yaml. The S1 predicate fires
    when a note's own label merely repeats this. An empty/missing default is excluded
    so a future label-less kind can never trigger a spurious suppression."""
    out: dict[str, str] = {}
    for code, rec in config.kinds_by_code().items():
        norm = _normalize_label_text(rec.get("label"))
        if norm:
            out[code] = norm
    return out


def _strip_note_label_span(row_html: str) -> tuple[str, bool]:
    """Remove the leaf's first ``<span class="note-label">…</span>`` (+ its trailing
    space). Returns ``(new_html, changed)``."""
    new_html, n = _NOTE_LABEL_SPAN_RE.subn("", row_html, count=1)
    return new_html, n > 0


def _strip_redundant_note_label(row_html: str, kind: str, kind_defaults: dict) -> tuple[str, bool]:
    """S1: drop a leaf row's note-label span when it is redundant — (a) its rendered
    text merely repeats the kind's default label, or (b) the body self-attributes
    (comm-ethiopian inner byline). Operates on the RENDERED row + the marker's kind,
    NOT the live note tuple, so it stays correct even where the baked base has drifted
    from the current notes. Returns ``(new_row, changed)``."""
    m = _NOTE_LABEL_SPAN_RE.search(row_html)
    if not m:
        return row_html, False
    # trigger (b): the body carries its own inner byline -> the label restates it.
    # Detected on the BAKED row (the surviving <strong>/<em>/<small> byline triad), so it
    # stays correct after the sanitizer strips the stored body's inner <aside> wrapper.
    if _is_self_attributing_comm_ethiopian(row_html):
        return _strip_note_label_span(row_html)
    # trigger (a): the label merely repeats the kind default. An empty/missing kind
    # default never suppresses.
    default = kind_defaults.get(kind, "")
    if default and _normalize_label_text(m.group(1)) == default:
        return _strip_note_label_span(row_html)
    return row_html, False


def _body_fingerprint(body_html: str) -> str:
    """SHA-1 of the tag-stripped, whitespace-collapsed, casefolded STORED body (note
    field 7) — the conserved 'distinct point' identity for the §4 completeness guard.
    Computed from the stored body, so it is invariant under S1's label relocation
    (never fingerprint the rendered row)."""
    text = _REHAUL_TAG_RE.sub(" ", body_html or "")
    text = " ".join(text.split()).casefold()
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


# ----------------------------------------------------------------------
# S2 — group by CATEGORY → SOURCE → emit the cascade (spec §2/§3 S2).
# The source is sourced by a BUILD-TIME LIVE attribution lookup keyed by note
# id, NOT a base re-bake (drift is kind=0 / ids 100% stable ⇒ a live lookup is
# base-consistent; the re-bake path is HIGH-risk with no clean entrypoint). See
# docs/superpowers/notes/2026-06-09-v0.1.0-app-ux-replan.md §S2.
# ----------------------------------------------------------------------

# A leading per-instance Strong's locator (Hebrew H / Greek G, with or without a
# trailing comma) — "Strong's H1254, …" / "Strong's H7779 (PD)". Stripping it is
# lossless (the headword lives in the body) and collapses every numbered Strong's
# entry from one dictionary onto a single source byline.
_SOURCE_STRONGS_RE = re.compile(r"^\s*Strong's\s+[HG]\d+\s*,?\s*")

# Trailing licence / public-domain / digital-edition boilerplate, introduced by a
# '.' or '(' delimiter. Cut at the FIRST marker → everything after is licence
# chatter: handles TSK's chained ". PD. Digital edition …, CC-BY 4.0." in one cut
# and the parenthesised "(PD)" form.
_SOURCE_BOILERPLATE_RE = re.compile(
    r"\s*[.(]\s*(?:PD\b|Public\s+domain|Digital\s+edition\b|CC[\s-]?BY\b|Creative\s+Commons)",
    re.IGNORECASE,
)

# A trailing per-locator citation marker on patristic/commentary works (Ephrem
# "Commentary on Genesis I.11" / "… II.2") + a series tail (NPNF…, "vol. 3"), so
# per-locator citations from one author+work collapse to ONE byline.
_SOURCE_SERIES_RE = re.compile(r"\s*[,(]?\s*(?:NPNF[^.]*|vol\.\s*\d+)\)?\.?\s*$", re.IGNORECASE)
# SK-2: also absorb a preceding structural citation word (Bk/Book/Hom./Homily) and the
# comma that introduces it, so "…, Bk I.11" strips WHOLE instead of leaving a dangling "Bk".
_SOURCE_LOCATOR_RE = re.compile(r"(?:,?\s*(?:Bk|Book|Hom\.?|Homily)\s+|\s+)[IVXLC]+\.\d+\s*$")

# Stray separators left dangling after a cut (NOT parens — a year like "(1894)"
# must keep its closing paren).
_SOURCE_TRIM_EDGES_RE = re.compile(r"^[\s,;:.\-]+|[\s,;:.\-]+$")


def _source_display(attribution: str | None) -> str:
    """The source byline (spec §3 S1/S2): the algorithmic trimmed form of a note's
    attribution — leading Strong's locator, trailing licence boilerplate, and a
    trailing per-locator citation removed; whitespace collapsed; original case
    kept. Empty/None → "" (the unattributed bucket). A bare Strong's attribution
    that trims to nothing falls back to "Strong's"."""
    s = (attribution or "").strip()
    if not s:
        return ""
    had_strongs = bool(_SOURCE_STRONGS_RE.match(s))
    s = _SOURCE_STRONGS_RE.sub("", s, count=1)
    cut = _SOURCE_BOILERPLATE_RE.search(s)
    if cut:
        s = s[: cut.start()]
    # POLISH-1: loop the series-strip to a fixpoint — a single pass consumes a trailing
    # "…, vol. N" first and leaves a dangling "NPNF Series N"; iterating clears both.
    prev = None
    while prev != s:
        prev = s
        s = _SOURCE_SERIES_RE.sub("", s)
    s = _SOURCE_LOCATOR_RE.sub("", s)
    s = " ".join(s.split())
    s = _SOURCE_TRIM_EDGES_RE.sub("", s)
    if not s and had_strongs:
        return "Strong's"
    return s


def _source_key(attribution: str | None) -> str:
    """The canonical SOURCE grouping key = casefold of the display byline. Two
    attributions group as one source iff their displays casefold-match (verified
    against the live corpus: only the intended Strong's-dictionary + one casing
    collapse merge >1 distinct attribution)."""
    return _source_display(attribution).casefold()


def _note_attribution_index(book: dict) -> dict[str, str]:
    """Map a book's live notes to their attribution, keyed by inject's full_id
    (``{prefix}{cc}{vv}{suffix}`` — the baked ref-/note- id minus its prefix), so
    apply_badge_markers can resolve a row's source from the marker id it already
    holds. Built once per book (load_notes is (path,mtime)-LRU-cached). Mirrors the
    id construction in _iter_note_ref_traditions exactly (id_prefix→bxx fallback)."""
    from scripts.core.notes_io import load_notes

    prefix = book.get("id_prefix") or book.get("bxx")
    if not prefix:
        return {}
    path = REPO_ROOT / "content" / "notes" / f"{book['code']}.py"
    if not path.is_file():
        return {}
    idx: dict[str, str] = {}
    for tup in load_notes(path) or []:
        if not isinstance(tup, tuple) or len(tup) < 8:
            continue
        try:
            ch_i = int(tup[0])
            vs_i = int(tup[1])
        except (TypeError, ValueError):
            continue
        attr = config.note_attribution(tup)
        if attr:
            idx[f"{prefix}{ch_i:02d}{vs_i:02d}{tup[2] or ''}"] = attr
    return idx


# --- S3a topic-note union --------------------------------------------------
# The rendered term list inside a topic note: "<strong>Topics.</strong> This verse
# appears under: CREATION, EARTH, GOD, HEAVEN." Terms are joined by ", " but 250 of
# the 5,232 Nave/Torrey topic names carry an INTERNAL comma, so the list is segmented
# by longest-match against the authoritative vocab, NOT a comma-split.
_TOPIC_APPEARS_RE = re.compile(r"appears under:\s*(.+?)\s*(</p>|</div>)", re.DOTALL | re.IGNORECASE)


@lru_cache(maxsize=1)
def _topic_vocab() -> frozenset:
    """Casefolded set of every Nave's + Torrey topic name — the authoritative vocab
    for longest-match segmentation of a topic note's ``appears under:`` list."""
    names: set[str] = set()
    for fn in ("naves_topical.json", "torrey_topical.json"):
        p = REPO_ROOT / "content" / "sources" / fn
        if not p.is_file():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        for name in data.get("topics") or {}:
            if name:
                names.add(" ".join(str(name).split()).casefold())
    return frozenset(names)


def _parse_topic_terms(appears_under: str, vocab: frozenset) -> list[str]:
    """Segment a comma-joined topic-term string into terms using ``vocab`` for
    longest-match (terms may contain internal commas). Original case + order kept;
    an unknown token is kept as its own term (defensive — never drops a term)."""
    tokens = [t.strip() for t in appears_under.split(",") if t.strip()]
    terms: list[str] = []
    i = 0
    while i < len(tokens):
        hit_span = 1
        for span in range(min(3, len(tokens) - i), 0, -1):
            cand = ", ".join(tokens[i : i + span])
            if " ".join(cand.split()).casefold() in vocab:
                hit_span = span
                break
        terms.append(", ".join(tokens[i : i + hit_span]))
        i += hit_span
    return terms


def _title_topic(s: str) -> str:
    """Title-case a topic term: capitalise each whitespace word, keep an
    apostrophe-suffix lower (``LORD'S SUPPER`` → ``Lord's Supper``), preserve commas
    (Nave stores UPPERCASE, Torrey Title Case → normalise to a uniform Title Case)."""
    out = []
    for word in s.split(" "):
        if "'" in word:
            head, _, tail = word.partition("'")
            out.append((head[:1].upper() + head[1:].lower()) + "'" + tail.lower())
        elif word:
            out.append(word[:1].upper() + word[1:].lower())
        else:
            out.append(word)
    return " ".join(out)


def _topic_union(term_lists: list) -> list[str]:
    """Case-insensitive union of topic-term lists: first-appearance order,
    Title-cased, deduped on casefold. The S3a lossless invariant — the OUT term set
    equals ``∪`` the IN term sets (keyed on casefold)."""
    seen: set[str] = set()
    out: list[str] = []
    for terms in term_lists:
        for t in terms:
            k = " ".join(t.split()).casefold()
            if k and k not in seen:
                seen.add(k)
                out.append(_title_topic(t))
    return out


def _render_merged_topic_row(row_html: str, merged_terms: list[str]) -> str:
    """Rebuild a topic note's row with the merged term list (`" · "`-joined, the
    spec §2 separator), reusing the first topic row's structure (note-sym / label /
    note-{kind} class) so the leaf spine + tinted card are unchanged."""
    joined = " · ".join(merged_terms)
    new_html, n = _TOPIC_APPEARS_RE.subn(lambda m: f"appears under: {joined}{m.group(2)}", row_html, count=1)
    return new_html if n else row_html


def _merge_topic_rows(cascade_rows: list[dict], vocab: frozenset) -> tuple[list[dict], int]:
    """S3a: fold every topic-category row on a verse into ONE Topics row whose term
    set is the case-insensitive union (Title-cased, first-appearance) of all of them,
    citing every contributing source in the byline. Lossless — the OUT term set ==
    ``∪`` the IN term sets. Returns ``(new_rows, n_topic_rows_folded)``."""
    topic_pos = [i for i, r in enumerate(cascade_rows) if r["cat"] == "topic"]
    if not topic_pos:
        return cascade_rows, 0
    term_lists: list[list[str]] = []
    sources: list[str] = []
    seen_src: set[str] = set()
    for i in topic_pos:
        r = cascade_rows[i]
        m = _TOPIC_APPEARS_RE.search(r["row"])
        raw = (m.group(1) if m else "").rstrip().rstrip(".")
        term_lists.append(_parse_topic_terms(raw, vocab))
        disp = r.get("source_display") or ""
        if disp and disp.casefold() not in seen_src:
            seen_src.add(disp.casefold())
            sources.append(disp)
    merged_terms = _topic_union(term_lists)
    if not merged_terms:
        # nothing parseable (shouldn't happen on real topic notes) — leave untouched
        return cascade_rows, 0
    combined = " · ".join(sources)
    merged_row = {
        "cat": "topic",
        "source_key": combined.casefold(),
        "source_display": combined,
        "suppress_byline": False,
        "row": _render_merged_topic_row(cascade_rows[topic_pos[0]]["row"], merged_terms),
    }
    first = topic_pos[0]
    drop = set(topic_pos[1:])
    out: list[dict] = []
    for i, r in enumerate(cascade_rows):
        if i == first:
            out.append(merged_row)
        elif i not in drop:
            out.append(r)
    return out, len(topic_pos)


# The .vn-item wrapper token every leaf row carries (_render_vn_item emits
# `<div class="vn-item note-{kind}">`, and the merged-topic row reuses that wrapper).
# Counting the WRAPPER — not a bare `class="vn-item` substring — keeps the §4
# conservation guard from a latent false-FAIL on a note body that happens to contain
# that literal text (S2-GUARD-3).
_VN_ITEM_WRAPPER = '<div class="vn-item note-'


def _count_cascade_leaves(html: str) -> int:
    """Number of leaf rows in an emitted cascade — counts the .vn-item wrapper token."""
    return html.count(_VN_ITEM_WRAPPER)


def _emit_cascade_sections(rows: list[dict], cat_meta: dict) -> str:
    """Emit the verse→category→source→note cascade inner HTML (spec §2) from the
    already category-rank-ordered ``rows``. Each row is a dict with keys
    ``cat, source_key, source_display, suppress_byline, row``; ``cat_meta`` maps a
    category id → ``(glyph, label)``. Categories appear in first-appearance order
    (rows arrive pre-sorted by category rank); within a category, sources appear in
    first-appearance order and notes keep document order. Pure re-grouping — every
    input row's ``.vn-item`` leaf survives exactly once (the §4 conservation guard
    asserts this against the caller's surviving-row count). Plain dicts preserve
    insertion order (Python 3.7+), so first-appearance ordering is automatic."""
    cats: dict[str, dict[str, list[dict]]] = {}
    for r in rows:
        by_source = cats.setdefault(r["cat"], {})
        by_source.setdefault(r["source_key"], []).append(r)

    out: list[str] = []
    for cat, by_source in cats.items():
        glyph, label = cat_meta.get(cat, ("", cat))
        out.append(f'  <section class="vn-group note-cat-{cat}">\n')
        # quote=False: label/byline are TEXT content (not attributes), so a literal
        # apostrophe (Strong's / Nave's) stays readable and matches the baked corpus
        # style (which carries literal ', not &#x27;).
        out.append(
            f'    <p class="vn-cat-head"><span class="vn-cat-sym" aria-hidden="true">{glyph}</span>'
            f" {html.escape(label, quote=False)}</p>\n"
        )
        for src_rows in by_source.values():
            out.append('    <div class="vn-source">\n')
            display = src_rows[0].get("source_display") or ""
            # BYLINE-4: suppress the group byline only when EVERY row in the bucket
            # self-attributes — all(), not any(), so one self-attributing row can never
            # hide a co-bucketed non-self-attributing row's source byline.
            suppress = bool(src_rows) and all(rr.get("suppress_byline") for rr in src_rows)
            if display and not suppress:
                out.append(f'      <p class="vn-source-byline">{html.escape(display, quote=False)}</p>\n')
            for rr in src_rows:
                out.append(f"      {rr['row']}\n")
            out.append("    </div>\n")
        out.append("  </section>\n")
    return "".join(out)


def apply_badge_markers(tmp: Path, edition: dict) -> dict:
    """Rewrite the per-edition temp HTML into badge mode (§4.1).

    For every verse that still has ≥1 surviving note:
      * replace its N inline ``note-ref`` markers with ONE
        ``<a class="verse-notes-badge" id="vbadge-{code}-{ch}-{v}"
        href="#vnotes-{code}-{ch}-{v}" epub:type="noteref"
        title="{N} notes"><sup class="marker-badge">{N}</sup></a>`` placed at the
        LAST marker's position (≈ verse end), removing the others;
      * merge its N per-note ``<aside class="note">`` elements into ONE
        ``<aside class="verse-notes" id="vnotes-{code}-{ch}-{v}"
        epub:type="footnote">`` = a verse header (one back-link + ``ch:v``)
        followed by each note as a ``.vn-item`` row, in document order.

    Position-grouped via inject's verse-region locators so it works for both
    strategies and respects the upstream kind/canon/tradition filter. Idempotent
    and deterministic. epub_working/ is NOT modified (the temp tree is). Returns
    ``{badges_inserted, asides_merged, notes_collapsed, files_touched}``.
    """
    from scripts import inject as _inject

    # Note-presentation rehaul flags (effective only here, under marker_style=badge).
    # Each is a zero-touch no-op when absent ⇒ a flag-free edition builds byte-identically.
    s1_dedup = bool(edition.get("note_attribution_dedup", False))
    kind_defaults = _kind_default_labels() if s1_dedup else {}
    # S2 — group surviving rows by category → source into the cascade. The source
    # byline is resolved by a build-time LIVE attribution lookup (per-book index
    # below); cat_meta carries each category's glyph + label once for the headers.
    s2_group = bool(edition.get("note_group_by_category", False))
    cat_meta = (
        {cid: (rec.get("symbol", ""), rec.get("label", cid)) for cid, rec in config.categories_by_id().items()}
        if s2_group
        else {}
    )
    # S3a — union-merge a verse's topic-category notes (topic-nave + topic-torrey)
    # into one Topics row (vocab-aware longest-match). Needs the per-row source too,
    # so the attribution index is built whenever S2 OR S3a is on.
    s3a_topic = bool(edition.get("note_topic_dedup", False))
    topic_vocab = _topic_vocab() if s3a_topic else frozenset()
    resolve_sources = s2_group or s3a_topic

    stats = {
        "badges_inserted": 0,
        "asides_merged": 0,
        "notes_collapsed": 0,
        "files_touched": 0,
        "badges_skipped": 0,
        "notes_deduped": 0,
        "s1_labels_suppressed": 0,
        "s2_groups_emitted": 0,
        "s2_byline_unattributed": 0,
        "s3a_topic_notes_merged": 0,
    }

    # Which split files actually survive in this edition's temp tree (canon
    # filter may have deleted some). Load each once; keyed by file name.
    present = {p.name for p in tmp.glob("*.html")}
    file_texts: dict[str, str] = {}

    def _text(fname: str) -> str | None:
        if fname not in present:
            return None
        if fname not in file_texts:
            file_texts[fname] = (tmp / fname).read_text(encoding="utf-8")
        return file_texts[fname]

    # Plan, per file, the list of (start, end, replacement) splices to apply.
    # Two kinds of splice: (1) collapse a verse's markers → one badge; (2)
    # collapse a verse's asides → one merged aside. Both are computed against the
    # ORIGINAL file offsets, then applied together in one reverse-order pass per
    # file so offsets never shift mid-apply.
    edits: dict[str, list[tuple[int, int, str]]] = {}

    for book in config.load_books():
        code = book["code"]
        # beta-3 (h): cross-verse dedup set — a byte-identical note body that
        # repeats across verses of THIS book (e.g. the generic manuscript-witness
        # blurb on both 1:1 and 45:18) renders only on its first verse. Reset per
        # book; xref/topic are exempt (see _XVERSE_DEDUP_EXCLUDE).
        seen_book_rows: set[str] = set()
        # S2: live attribution index for THIS book (fid → attribution), built once
        # per book (load_notes is LRU-cached). Empty when S2 is off ⇒ zero cost.
        book_attr_index = _note_attribution_index(book) if resolve_sources else {}
        strategy = book.get("strategy", "A")
        bxx = book.get("bxx")
        ch_count = book.get("ch_count", 0)
        files = [f for f in book.get("files", []) if f in present]
        if not files:
            continue

        # Iterate every (ch, v) the book could have; cheap because we only act on
        # verses that actually carry surviving markers in this edition. A verse's
        # markers AND asides are always co-located in one file (inject places
        # them together), but a chapter can spill across a split-file boundary, so
        # we process the chapter in EVERY file that holds its verses (normally
        # exactly one) rather than guessing-and-break.
        for ch in range(1, ch_count + 1):
            for fname in files:
                text = _text(fname)
                if text is None:
                    continue

                # Locate this chapter's verses. The robust, spill-proof path is
                # the per-verse v-{code}-{ch}-{v} anchor walk: it works for
                # Strategy A AND any Strategy-B book that inject anchored (e.g.
                # Kings, Chronicles) regardless of which split file the chapter
                # heading lives in — so a chapter whose anchor spilled to the
                # previous file (1ch 3) is still found by its verse anchors here.
                # Only the anchor-less Strategy-B books (Jubilees, 1 Enoch) need
                # the vn-span chapter-region fallback.
                if f'id="v-{code}-{ch}-' in text:
                    verse_iter = _badge_verses_strategy_a(text, code, ch)
                elif strategy == "B":
                    ch_region = _inject.find_chapter_region_b(text, bxx, ch, ch_count)
                    if ch_region is None:
                        continue
                    verse_iter = _badge_verses_strategy_b(text, ch_region, code, bxx, ch)
                else:
                    continue

                for v, (v_start, v_end) in verse_iter:
                    verse_html = text[v_start:v_end]
                    # Surviving markers in this verse, in document order.
                    markers = list(_BADGE_MARKER_RE.finditer(verse_html))
                    if not markers:
                        continue

                    full_ids = [m.group(1) for m in markers]
                    kinds = [_badge_extract_note_kind(m.group(0)) for m in markers]
                    n = len(full_ids)

                    # --- (2) merged aside ---------------------------------------
                    # Each note's aside may live anywhere in the chapter's
                    # notes-section (same file). Collect them in marker order so
                    # the merged list mirrors the reading order.
                    # Collect each note's row; DEDUP exact repeats (a verse can carry
                    # two byte-identical notes — e.g. duplicate cross-ref tuples — that
                    # otherwise render twice; RX-beta2 ②) and GROUP by category in the
                    # fixed most-useful → least order with the long topical block LAST
                    # (RX-beta2 ③). Document order is preserved within a category.
                    # (cat_rank, doc_order, row, cat, attribution) — cat + attribution
                    # are carried for the S2 cascade; ignored on the flat (S2-off) path.
                    row_items: list[tuple[int, int, str, str, str | None]] = []
                    aside_spans: list[tuple[int, int]] = []
                    seen_rows: set[str] = set()
                    ok = True
                    for doc_i, (fid, kind) in enumerate(zip(full_ids, kinds, strict=True)):
                        am = re.search(
                            r'<aside class="note note-[a-z][a-z0-9-]*" id="note-'
                            + re.escape(fid)
                            + r'"[^>]*>(.*?)</aside>',
                            text,
                            re.DOTALL,
                        )
                        if not am:
                            # An orphan marker with no aside — bail on this verse
                            # rather than emit a badge whose popup is short a row.
                            ok = False
                            break
                        aside_spans.append((am.start(), am.end()))
                        row = _badge_aside_inner_to_row(am.group(1), kind)
                        norm = " ".join(row.split())
                        if norm in seen_rows:
                            stats["notes_deduped"] += 1
                            continue
                        cat = _inject.category_for(kind)
                        dedupable = cat not in _XVERSE_DEDUP_EXCLUDE
                        # beta-3 (h): drop a byte-identical body already shown earlier
                        # in this book (the generic manuscript-witness redundancy).
                        if dedupable and norm in seen_book_rows:
                            stats["notes_deduped"] += 1
                            continue
                        seen_rows.add(norm)
                        if dedupable:
                            seen_book_rows.add(norm)
                        # S1 (note_attribution_dedup): drop the leaf's note-label span
                        # when it merely repeats the kind default OR the body self-
                        # attributes (comm-ethiopian). Lossless — the distinguishing
                        # text survives in the body / category header. Applied AFTER the
                        # dedup decision so the dedup keys stay byte-identical to the
                        # flag-off build. Operates on the rendered row (base-consistent).
                        if s1_dedup:
                            row, _changed = _strip_redundant_note_label(row, kind, kind_defaults)
                            if _changed:
                                stats["s1_labels_suppressed"] += 1
                        rank = _POPUP_CATEGORY_RANK.get(cat, _POPUP_CATEGORY_FALLBACK_RANK)
                        attribution = book_attr_index.get(fid) if resolve_sources else None
                        row_items.append((rank, doc_i, row, cat, attribution))
                    if not ok:
                        # round-5 audit Phase 4 (LOW): record the silent orphan-bail
                        # (a verse with a marker but no matching aside) so a build can
                        # surface "N verses skipped" instead of dropping a badge with
                        # no diagnostic. Stat-only — never written into the EPUB, so
                        # byte-stable.
                        stats["badges_skipped"] += 1
                        continue

                    # Stable category sort (document order preserved within a category).
                    row_items.sort(key=lambda t: (t[0], t[1]))
                    n_show = len(row_items)

                    if n_show == 0:
                        # beta-3 (h): every note here was a cross-verse duplicate →
                        # strip its markers + asides and emit NO badge (no empty ◈0).
                        bucket = edits.setdefault(fname, [])
                        for m in markers:
                            bucket.append((v_start + m.start(), v_start + m.end(), ""))
                        for sp in sorted(aside_spans):
                            bucket.append((sp[0], sp[1], ""))
                        stats["notes_collapsed"] += n
                        continue

                    if resolve_sources:
                        # Resolve each surviving row's source (S2 byline + S3a citation).
                        # The byline comes from the live attribution (base-consistent —
                        # kind never drifts); comm-ethiopian bodies self-attribute, so
                        # their GROUP byline is suppressed.
                        cascade_rows = [
                            {
                                "cat": cat,
                                "source_key": _source_key(attribution),
                                "source_display": _source_display(attribution),
                                "suppress_byline": _is_self_attributing_comm_ethiopian(row),
                                "row": row,
                            }
                            for _rank, _doc, row, cat, attribution in row_items
                        ]
                        # S3a: union-merge the verse's topic-category rows into one.
                        if s3a_topic:
                            cascade_rows, n_merged = _merge_topic_rows(cascade_rows, topic_vocab)
                            stats["s3a_topic_notes_merged"] += n_merged
                        n_show = len(cascade_rows)
                        if s2_group:
                            for r in cascade_rows:
                                if not r["source_display"] and not r["suppress_byline"]:
                                    stats["s2_byline_unattributed"] += 1
                            inner_rows_html = _emit_cascade_sections(cascade_rows, cat_meta)
                            # §4 completeness guard (S2-GUARD-1/2/3): the spec's set-based
                            # DISTINCT_OUT==DISTINCT_IN guard is downgraded to this leaf
                            # count, which is SOUND by construction — _emit_cascade_sections
                            # appends each row once (setdefault().append) and emits it once,
                            # so it provably cannot drop or duplicate a leaf. Count the
                            # .vn-item WRAPPER token (not a bare 'class="vn-item' substring)
                            # so a note body that merely mentions that text never false-FAILs.
                            leaves = _count_cascade_leaves(inner_rows_html)
                            if leaves != n_show:
                                raise AssertionError(
                                    f"S2 cascade conservation failure at {code} {ch}:{v}: "
                                    f"{leaves} leaves vs {n_show} surviving rows"
                                )
                            stats["s2_groups_emitted"] += len({r["cat"] for r in cascade_rows})
                        else:
                            # S3a-only (flat): the merged topic row + the rest, flat.
                            inner_rows_html = "".join(f"  {r['row']}\n" for r in cascade_rows)
                    else:
                        inner_rows_html = "".join(f"  {row}\n" for _rank, _doc, row, _cat, _attr in row_items)

                    merged_aside = (
                        f'<aside class="verse-notes" id="vnotes-{code}-{ch}-{v}" epub:type="footnote">\n'
                        f'  <p class="vn-back"><a href="#vbadge-{code}-{ch}-{v}" class="note-back" '
                        f'title="Back">↩</a> <strong>{ch}:{v}</strong></p>\n' + inner_rows_html + "</aside>\n"
                    )

                    # --- (1) one badge at the LAST marker's position ------------
                    # Glyph = ◈ note-mark + the unique-note count, so it reads as
                    # "notes here" and never blends with the verse number / the
                    # translation (verse-number) marker (RX-beta2 ①).
                    title = f"{n_show} note" if n_show == 1 else f"{n_show} notes"
                    badge = (
                        f'<a class="verse-notes-badge" id="vbadge-{code}-{ch}-{v}" '
                        f'href="#vnotes-{code}-{ch}-{v}" epub:type="noteref" '
                        f'title="{title}"><sup class="marker-badge">◈{n_show}</sup></a>'
                    )

                    bucket = edits.setdefault(fname, [])
                    # Replace the LAST marker with the badge; delete the others.
                    last = markers[-1]
                    bucket.append((v_start + last.start(), v_start + last.end(), badge))
                    for m in markers[:-1]:
                        bucket.append((v_start + m.start(), v_start + m.end(), ""))
                    # Replace the FIRST aside (document order) with the merged
                    # aside; delete the rest.
                    aside_spans_sorted = sorted(aside_spans)
                    first_aside = aside_spans_sorted[0]
                    bucket.append((first_aside[0], first_aside[1], merged_aside))
                    for sp in aside_spans_sorted[1:]:
                        bucket.append((sp[0], sp[1], ""))

                    stats["badges_inserted"] += 1
                    stats["asides_merged"] += 1
                    stats["notes_collapsed"] += n

    # Apply every file's splices in one reverse-order pass (offsets stay valid).
    for fname, splices in edits.items():
        text = file_texts[fname]
        # Deterministic: sort by start descending; ties broken by end so nested
        # spans never interleave (markers/asides are disjoint, so ties are rare).
        for start, end, repl in sorted(splices, key=lambda s: (s[0], s[1]), reverse=True):
            text = text[:start] + repl + text[end:]
        file_texts[fname] = text
        (tmp / fname).write_text(text, encoding="utf-8")
        stats["files_touched"] += 1

    return stats


def _badge_chapter_content_end(text: str, after: int) -> int:
    """The byte offset where chapter content (verse prose + any trailing
    verse-end-fallback markers) ends, starting from ``after``. Bounds the LAST
    verse of a chapter, which can carry stray markers placed AFTER its closing
    ``</p>`` but BEFORE the chapter's notes-section / the next chapter heading /
    the document epilogue. Markers between ``</p>`` and that boundary still
    belong to the last verse, so the region must reach them."""
    end = len(text)
    # The notes-section and </body> are themselves tag-starts, so their match
    # offset IS the safe region end. The next chapter heading is an attribute
    # INSIDE an opening tag (id="ch-…"), so back its offset up to that tag's '<'
    # — only for that one boundary — so we never end mid-tag.
    sec = re.search(r'<aside class="notes-section"', text[after:])
    if sec:
        end = min(end, after + sec.start())
    body = text.find("</body>", after)
    if body != -1:
        end = min(end, body)
    chh = re.search(r'id="ch-b\d+-c\d+"', text[after:])
    if chh:
        abs_chh = after + chh.start()
        tag = text.rfind("<", after, abs_chh)
        end = min(end, tag if tag != -1 else abs_chh)
    return end


def _badge_verses_strategy_a(text: str, code: str, ch: int):
    """Yield ``(v, (start, end))`` for each verse of chapter ``ch`` in a
    Strategy-A file, by walking its ``v-{code}-{ch}-{v}`` anchors in order. The
    region for verse v runs from just after its vn-link close to just before the
    NEXT vn-link's opening ``<a>`` (any verse). The chapter's LAST verse extends
    to the chapter-content boundary so trailing verse-end-fallback markers (which
    inject can place after the verse's ``</p>``) are still grouped with it."""
    anchor_re = re.compile(
        r'<a class="vn-link" id="v-'
        + re.escape(code)
        + r"-"
        + str(ch)
        + r'-(\d+)"[^>]*>\s*<span class="vn">\d+</span>\s*</a>'
    )
    matches = list(anchor_re.finditer(text))
    for m in matches:
        v = int(m.group(1))
        start = m.end()
        nxt = re.search(r'<a class="vn-link" id="v-', text[start:])
        end = start + nxt.start() if nxt else _badge_chapter_content_end(text, start)
        yield v, (start, end)


def _badge_verses_strategy_b(text: str, ch_region: tuple[int, int], code: str, bxx: str, ch: int):
    """Yield ``(v, (start, end))`` for each verse of a Strategy-B chapter region.

    Two shapes coexist: verses wrapped in ``v-{code}-{ch}-{v}`` vn-link anchors
    (post-inject Strategy-B, e.g. Kings) and bare ``<span class="vn">v</span>``
    delimiters (anchor-less Strategy-B, e.g. Jubilees). Anchors are authoritative
    when present; otherwise fall back to the vn-span walk."""
    rs, re_ = ch_region
    region = text[rs:re_]
    anchor_re = re.compile(
        r'<a class="vn-link" id="v-'
        + re.escape(code)
        + r"-"
        + str(ch)
        + r'-(\d+)"[^>]*>\s*<span class="vn">\d+</span>\s*</a>'
    )
    anchors = list(anchor_re.finditer(region))
    if anchors:
        for m in anchors:
            v = int(m.group(1))
            start = m.end()
            nxt = re.search(r'<a class="vn-link" id="v-', region[start:])
            end = (start + nxt.start()) if nxt else len(region)
            yield v, (rs + start, rs + end)
        return
    # Anchor-less: walk <span class="vn">v</span> markers.
    span_re = re.compile(r'<span class="vn">(\d+)</span>')
    spans = list(span_re.finditer(region))
    for i, m in enumerate(spans):
        try:
            v = int(m.group(1))
        except ValueError:
            continue
        start = m.end()
        end = spans[i + 1].start() if i + 1 < len(spans) else len(region)
        yield v, (rs + start, rs + end)


# ----------------------------------------------------------------------
# RX Phase 4b — build-time EPUB file-splitter (apply_file_split)
# ----------------------------------------------------------------------
#
# The calibre-produced base ships 61 ``index_split_*.html`` files, several of them
# 2-5 MB. Colour-e-ink Kobo can't reflow a multi-MB XHTML page (it crawls / crashes /
# never shows the popups). This per-edition BUILD-TIME post-pass splits the big files
# into ~0.4 MB pieces at top-level book/chapter boundaries, rewrites every cross-file
# href to the piece that now holds the target id, distributes each file's single
# trailing ``notes-section`` into per-piece notes-sections (so the bare ``#id``
# footnote/popup contract stays SAME-FILE = native popups on every reader), and
# regenerates the OPF manifest+spine + nav.xhtml + toc.ncx. epub_working/ (the
# canonical 61-file base) is NEVER touched — like apply_badge_markers, this operates
# only on the per-edition temp tree, so all base tooling (inject, nested-anchor base
# check, marker resync) is unaffected.
#
# Runs LAST in build_one (after badge + every matter-page injection) so its
# manifest/spine/nav regeneration is the final word before the zip. Gated on the
# ``reader_file_split`` edition flag; a no-op (byte-identical) when unset.

# Default ON (this RX arc makes the standard editions e-ink/Kobo-safe by default, like the
# badge marker style); an edition may opt out with reader_file_split: false in editions.yaml.
DEFAULT_READER_FILE_SPLIT = True

FILE_SPLIT_TARGET_DEFAULT = 400_000  # soft byte cap per piece; a single chapter that
# already exceeds it becomes its own (over-cap) piece — we never split mid-chapter,
# because a verse's marker and its aside must stay in one file for the popup contract.

# HARD unit boundaries — top-level siblings safe to cut at: a book-title-page (id="bp-NN")
# and EVERY chapter start (id="ch-bNN-cMM"). A chapter's id is carried by EITHER its
# <a class="ch-anchor"> (chapter 2+) OR a <p class="ch-heading"> (chapters that open a
# page/split-file — e.g. Numbers c1/c13/c17). We match the id= attribute (not a "#…" href
# target) and back up to the element's '<', so BOTH forms are caught by one rule — matching
# only ch-anchor silently merges the ch-heading-form chapters into multi-MB units.
_BOUNDARY_HARD_RE = re.compile(r'\bid="(?:bp-\d+|ch-b\d+-c\d+)"')

# Book-title-page boundary — an id that must START a fresh piece. A new spine file is a
# guaranteed fresh page on EVERY renderer; Kobo's kepub engine IGNORES the CSS
# page-break-* rules at the #book-inner nesting depth kepubify wraps everything in, so
# the in-content ToC tail, a book's framed title, and chapter 1 all rendered on ONE Kobo
# page (K-R2-1, 2026-06-09 device QA). Splitting at the boundary is the only bulletproof
# break — the title page gets its OWN piece (forced, even in an under-target file).
_BP_ID_RE = re.compile(r'\bid="bp-\d+"')

# Chapter-heading cut candidate by CLASS. The real base carries page_N ids on its
# <p class="ch-heading"> numerals — the ch-bNN-cMM id form exists only where a
# ch-anchor was emitted — so without this rule a sparsely-noted book provides NO hard
# candidates and packs into one giant over-cap atom (the 700-880 KB pieces found in the
# K-R2 kepub inspection; target is 400 KB).
_CH_HEADING_RE = re.compile(r'<p\b[^>]*\bclass="[^"]*\bch-heading\b[^"]*"')

# Inline verse anchors — extra cut candidates so a heavily-noted chapter can split
# between verses. A vn-link sits inside its <p class="verse-p"> (and a chapter anchor can
# sit inside the PREVIOUS chapter's trailing <p class="verse-p">), so any cut may land
# inside an open element — the stack-aware splitter closes/reopens whatever is open.
_VN_LINK_RE = re.compile(r'<a class="vn-link" id="v-[^"]+"')

# Generic element scanner for the open-tag stack. Groups: leading '/', tag name, trailing
# '/' (self-close). Non-greedy attrs so <br/>'s trailing slash is captured, not swallowed.
_TAG_RE = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9:]*)\b[^>]*?(/?)>", re.DOTALL)
_VOID_ELEMENTS = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
)

# A child note aside inside a notes-section. The negative lookahead skips the
# notes-section PARENT itself (class="notes-section", which may carry an id like
# notes-b00-c27); children are class="note …" (verse-popup + editorial) or
# class="verse-notes" (the badge-merged aside). Asides never nest asides, so .*? is tight.
_CHILD_ASIDE_RE = re.compile(r'<aside class="(?!notes-section)[^"]*" id="([^"]+)"[^>]*>.*?</aside>', re.DOTALL)

# A notes-section wrapper left empty after its child asides are harvested out.
_EMPTY_NOTES_SECTION_RE = re.compile(r'<aside class="notes-section"[^>]*>\s*</aside>\s*')

_NOTES_SECTION_OPEN = '<aside class="notes-section" epub:type="footnotes" hidden="">\n'


def _split_head_body_tail(text: str) -> tuple[str, str, str] | None:
    """Return ``(head, body, tail)`` where head runs through the ``<body…>`` open tag
    and tail is ``</body>`` to EOF. None when those markers are missing."""
    bm = re.search(r"<body\b[^>]*>", text)
    if not bm:
        return None
    body_start = bm.end()
    body_close = text.rfind("</body>")
    if body_close == -1 or body_close < body_start:
        return None
    return text[:body_start], text[body_start:body_close], text[body_close:]


def _strip_notes_sections(body: str) -> tuple[str, list[tuple[str, str]]]:
    """Harvest + remove EVERY note aside, leaving pure chapter prose.

    The base mixes aside placement: most asides sit inside a
    ``<aside class="notes-section">`` block (trailing, sometimes a leading spill-over),
    but a large share are INLINE right after their verse. Stripping only the
    notes-section blocks would leave the inline asides lumped in the prose — inflating a
    chapter to multiple MB AND grouping a chapter's notes by physical position instead of
    by the verse that references them. So we strip every leaf note aside wherever it sits
    (a single non-greedy pass — leaf asides never nest), then drop the emptied
    notes-section wrappers. Returns ``(prose, [(aside_id, aside_html), …])`` with the
    pooled asides in document order for per-piece redistribution BY REFERENCE."""
    asides: list[tuple[str, str]] = []

    def _take(m: re.Match) -> str:
        asides.append((m.group(1), m.group(0)))
        return ""

    content = _CHILD_ASIDE_RE.sub(_take, body)
    content = _EMPTY_NOTES_SECTION_RE.sub("", content)
    return content, asides


def _open_tag_name(open_tag: str) -> str:
    """The element name from an open tag (``<p class="verse-p">`` → ``p``)."""
    m = re.match(r"<([a-zA-Z][a-zA-Z0-9:]*)", open_tag)
    return m.group(1) if m else ""


def _stack_at_positions(content: str, positions: list[int]) -> dict[int, list[str]]:
    """For each position, the open-tag strings of the elements still OPEN just before it
    (outermost→innermost), computed in one scan. The splitter uses this to make any cut
    well-formed: reopen the elements a piece STARTS inside, close those still open where
    it ENDS — so a cut landing inside a ``<p class="verse-p">`` (a verse anchor always; a
    chapter anchor when it nests in the previous chapter's trailing paragraph) never
    orphans an unterminated tag."""
    want = sorted(set(positions))
    out: dict[int, list[str]] = {}
    pi = 0
    stack: list[tuple[str, str]] = []  # (name, full-open-tag)
    for m in _TAG_RE.finditer(content):
        while pi < len(want) and want[pi] <= m.start():
            out[want[pi]] = [t for _, t in stack]
            pi += 1
        closing, name, selfclose = m.group(1), m.group(2).lower(), m.group(3)
        if closing:
            for k in range(len(stack) - 1, -1, -1):
                if stack[k][0] == name:
                    del stack[k:]  # close this element (and any improperly-still-open descendants)
                    break
        elif not selfclose and name not in _VOID_ELEMENTS:
            stack.append((name, m.group(0)))
    while pi < len(want):
        out[want[pi]] = [t for _, t in stack]
        pi += 1
    return out


def split_html_document(text: str, stem: str, target: int) -> list[tuple[str, str]]:
    """Split ONE ``index_split`` file's text into ~``target``-byte pieces.

    Cuts at book/chapter boundaries and (for a heavily-noted chapter that alone exceeds
    target) between verses. A cut may land INSIDE a ``<p class="verse-p">`` — a verse
    anchor always is, and a chapter anchor can be nested in the previous chapter's
    trailing paragraph — so a stack-aware wrapper reopens the elements each piece STARTS
    inside and closes those still open where it ENDS, keeping every piece well-formed.
    The file's asides (harvested from its notes-section(s) AND inline placements) are
    redistributed into a per-piece ``notes-section`` holding exactly the asides that piece
    references (first referencer wins; the link-rewrite pass later promotes any cross-piece
    reference to a cross-file link), so the bare ``#id`` footnote/popup contract stays
    same-file. A book-title-page (id="bp-NN") ALWAYS gets its own piece — forced even in
    an under-target file — because a fresh spine file is the only page break Kobo's
    kepub renderer honors (K-R2-1); and no piece ever ENDS with a bare chapter
    opener (anchor/heading) — trailing openers move to the next piece so a chapter
    numeral never strands at the bottom of a page (K-R2-4 seam). Returns
    ``[(piece_filename, text), …]``; a file at/under ``target`` without a
    book-title-page (or without a usable structure) is returned unchanged (zero churn)."""
    if len(text) <= target and not _BP_ID_RE.search(text):
        return [(f"{stem}.html", text)]
    parts = _split_head_body_tail(text)
    if parts is None:
        return [(f"{stem}.html", text)]
    head, body, tail = parts

    # Strip every note aside (notes-section blocks + inline) to pure prose, pooling them
    # for per-piece redistribution by reference.
    content, harvested = _strip_notes_sections(body)
    aside_by_id: dict[str, str] = {}
    ordered_aside_ids: list[str] = []
    for aid, aside_html in harvested:
        if aid not in aside_by_id:
            aside_by_id[aid] = aside_html
            ordered_aside_ids.append(aid)

    # Cut candidates: every book/chapter start (id="bp-"/"ch-…", backed up to its '<'),
    # every ch-heading by CLASS (the real base's page_N-id form), and every verse
    # anchor. The packer cuts ONLY at a candidate; the stack-aware wrapper below makes
    # any such cut well-formed even when it lands inside a <p>/<div>. cand_kind tracks
    # WHAT each cut position opens ('bp' = book title, 'ch' = chapter opener) for the
    # forced-isolation and no-trailing-opener rules.
    cands: set[int] = set()
    cand_kind: dict[int, str] = {}
    for m in _BOUNDARY_HARD_RE.finditer(content):
        lt = content.rfind("<", 0, m.start())
        if lt > 0:
            cands.add(lt)
            cand_kind[lt] = "bp" if 'id="bp-' in m.group(0) else "ch"
    for m in _CH_HEADING_RE.finditer(content):
        if m.start() > 0:
            cands.add(m.start())
            cand_kind.setdefault(m.start(), "ch")
    for m in _VN_LINK_RE.finditer(content):
        if m.start() > 0:
            cands.add(m.start())
    # Title positions for forced isolation. A title's '<' may sit at position 0 (a file
    # that BEGINS with a book title): 0 is never a cut, but atom 0 must still be
    # recognized as a title atom so the piece after it starts fresh.
    title_cuts: set[int] = set()
    for m in _BP_ID_RE.finditer(content):
        lt = content.rfind("<", 0, m.start())
        if lt >= 0:
            title_cuts.add(lt)
    if not cands:
        return [(f"{stem}.html", text)]
    cuts = [0, *sorted(cands), len(content)]
    atoms = [content[cuts[i] : cuts[i + 1]] for i in range(len(cuts) - 1)]

    # Attribute each aside to the FIRST atom that references it (orphans → last); an atom's
    # NOTES dominate its weight, so packing reflects real per-piece size.
    aside_atom: dict[str, int] = {}
    for ai, atom in enumerate(atoms):
        for frag in re.findall(r'href="#([^"]+)"', atom):
            if frag in aside_by_id and frag not in aside_atom:
                aside_atom[frag] = ai
    last_ai = len(atoms) - 1
    atom_weight = [len(a) for a in atoms]
    for aid in ordered_aside_ids:
        ai = aside_atom.setdefault(aid, last_ai)
        atom_weight[ai] += len(aside_by_id[aid])

    # Greedy-pack atoms into pieces ≤ target (a lone over-weight atom stands alone).
    # A title atom is a FORCED singleton: it closes the running group (unless that group
    # is whitespace-only filler, which merges into the title piece) and closes itself
    # immediately, so the book-title page owns a whole spine file.
    title_atoms = {i for i in range(len(atoms)) if cuts[i] in title_cuts}
    groups: list[list[int]] = []
    cur: list[int] = []
    cur_w = 0
    for i, w in enumerate(atom_weight):
        is_title = i in title_atoms
        force_break = is_title and any(atoms[j].strip() for j in cur)
        if cur and (force_break or cur_w + w > target):
            groups.append(cur)
            cur, cur_w = [], 0
        cur.append(i)
        cur_w += w
        if is_title:
            groups.append(cur)
            cur, cur_w = [], 0
    if cur:
        groups.append(cur)

    # No piece may END with a bare chapter opener (a ch-anchor and/or ch-heading with no
    # verse prose after it) — pop trailing opener atoms onto the next group so a chapter
    # numeral never strands at the bottom of a page (the K-R2-4 orphan seam). Skip when
    # the next group is a forced title piece (nothing precedes a book title).
    for gi in range(len(groups) - 1):
        g, nxt = groups[gi], groups[gi + 1]
        if nxt and nxt[0] in title_atoms:
            continue
        while (
            g
            and g[-1] not in title_atoms
            and cand_kind.get(cuts[g[-1]]) == "ch"
            and len(atoms[g[-1]]) < 600
            and 'class="vn-link' not in atoms[g[-1]]
        ):
            # A small ch-kind atom with no verse anchor is a bare opener (an anchor,
            # a heading, or heading + the next paragraph's open tag — the verse cut
            # lands inside the <p>, and the stack-aware wrapper keeps both sides
            # well-formed). An atom carrying real verse prose is large or holds a
            # vn-link and never pops.
            nxt.insert(0, g.pop())
    groups = [g for g in groups if g]
    if len(groups) <= 1:
        return [(f"{stem}.html", text)]

    # Open-element stack at each piece boundary → reopen what a piece starts inside, close
    # what is still open where it ends. Guarantees every piece is well-formed XHTML.
    stack_at = _stack_at_positions(content, cuts)
    atom_to_group = {ai: gi for gi, g in enumerate(groups) for ai in g}
    group_asides: list[list[str]] = [[] for _ in groups]
    for aid in ordered_aside_ids:  # document order within each piece
        group_asides[atom_to_group[aside_atom[aid]]].append(aid)

    pieces: list[tuple[str, str]] = []
    for k, g in enumerate(groups):
        prefix = "".join(stack_at[cuts[g[0]]])  # reopen the elements this piece starts inside
        suffix = "".join(f"</{_open_tag_name(t)}>" for t in reversed(stack_at[cuts[g[-1] + 1]]))
        gt = "".join(atoms[i] for i in g)
        ids = group_asides[k]
        notes_html = (
            (_NOTES_SECTION_OPEN + "".join(aside_by_id[aid] + "\n" for aid in ids) + "</aside>\n") if ids else ""
        )
        pieces.append((f"{stem}_{k:02d}.html", head + prefix + gt + suffix + notes_html + tail))
    return pieces


def apply_file_split(tmp: Path, edition: dict) -> dict:
    """Split the per-edition temp tree's big ``index_split_*.html`` files into ~0.4 MB
    pieces, remap every cross-file href, and regenerate the OPF manifest+spine +
    nav.xhtml + toc.ncx. No-op (byte-identical) unless ``edition['reader_file_split']``.
    Returns ``{files_split, pieces_created, hrefs_rewritten, largest_piece_kb}``."""
    stats = {"files_split": 0, "pieces_created": 0, "hrefs_rewritten": 0, "largest_piece_kb": 0}
    if not edition.get("reader_file_split", DEFAULT_READER_FILE_SPLIT):
        return stats
    target = int(edition.get("reader_file_split_target") or FILE_SPLIT_TARGET_DEFAULT)

    src_files = sorted(tmp.glob("index_split_*.html"))
    if not src_files:
        return stats

    # 1. Plan pieces per source file (in sorted, deterministic order).
    plan: dict[str, list[tuple[str, str]]] = {}
    for p in src_files:
        plan[p.name] = split_html_document(p.read_text(encoding="utf-8"), p.stem, target)

    # 2. Global maps: id → final piece file; original file → its first piece.
    idmap: dict[str, str] = {}
    filemap: dict[str, str] = {}
    split_origs: set[str] = set()
    for orig, pieces in plan.items():
        filemap[orig] = pieces[0][0]
        if not (len(pieces) == 1 and pieces[0][0] == orig):
            split_origs.add(orig)
        for pname, ptext in pieces:
            for m in re.finditer(r'\bid="([^"]+)"', ptext):
                idmap[m.group(1)] = pname

    if not split_origs:
        return stats  # nothing exceeded the target

    full_re = re.compile(r'(href|src)="(index_split_\d+\.html)(?:#([^"]+))?"')
    bare_re = re.compile(r'href="#([^"]+)"')

    def rewrite_links(text: str, self_name: str) -> tuple[str, int]:
        n = [0]

        def _full(m: re.Match) -> str:
            attr, orig, frag = m.group(1), m.group(2), m.group(3)
            if frag:
                newfile = idmap.get(frag, filemap.get(orig, orig))
                out = f'{attr}="{newfile}#{frag}"'
            else:
                out = f'{attr}="{filemap.get(orig, orig)}"'
            if out != m.group(0):
                n[0] += 1
            return out

        def _bare(m: re.Match) -> str:
            frag = m.group(1)
            tgt = idmap.get(frag)
            if tgt is None or tgt == self_name:
                return m.group(0)
            n[0] += 1
            return f'href="{tgt}#{frag}"'

        text = full_re.sub(_full, text)
        text = bare_re.sub(_bare, text)
        return text, n[0]

    # 3. Materialise pieces: delete split originals, write each piece's RAW text.
    for orig, pieces in plan.items():
        if orig in split_origs:
            (tmp / orig).unlink()
        for pname, ptext in pieces:
            (tmp / pname).write_text(ptext, encoding="utf-8")

    # 4. Rewrite links in every content file (pieces + nav.xhtml + toc.ncx + matter
    #    pages). content.opf is handled by the manifest/spine regen below.
    for fp in sorted(tmp.iterdir()):
        if fp.suffix not in (".html", ".xhtml", ".ncx"):
            continue
        txt = fp.read_text(encoding="utf-8")
        new_txt, n = rewrite_links(txt, fp.name)
        if new_txt != txt:
            fp.write_text(new_txt, encoding="utf-8")
        stats["hrefs_rewritten"] += n

    # 5. Regenerate the OPF manifest + spine: expand each split file's single item /
    #    itemref into its pieces' items / itemrefs, in order; preserve everything else.
    opf_path = tmp / "content.opf"
    if opf_path.is_file():
        opf_text = opf_path.read_text(encoding="utf-8")
        for orig in sorted(split_origs):
            item_m = re.search(rf'<item\b[^>]*\bhref="{re.escape(orig)}"[^>]*/>', opf_text)
            if not item_m:
                continue
            old_item = item_m.group(0)
            idm = re.search(r'\bid="([^"]+)"', old_item)
            if not idm:
                continue
            old_id = idm.group(1)
            new_items, new_refs = [], []
            for j, (pname, _t) in enumerate(plan[orig]):
                pid = f"{old_id}_{j:02d}"
                new_items.append(f'<item id="{pid}" href="{pname}" media-type="application/xhtml+xml"/>')
                new_refs.append(f'<itemref idref="{pid}"/>')
            opf_text = opf_text.replace(old_item, "\n    ".join(new_items), 1)
            opf_text = opf_text.replace(f'<itemref idref="{old_id}"/>', "\n    ".join(new_refs), 1)
        opf_path.write_text(opf_text, encoding="utf-8")

    # 6. Stats.
    stats["files_split"] = len(split_origs)
    stats["pieces_created"] = sum(len(plan[o]) for o in split_origs)
    largest = 0
    for fp in tmp.glob("index_split_*.html"):
        largest = max(largest, fp.stat().st_size)
    stats["largest_piece_kb"] = round(largest / 1024)
    return stats


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
    # beta-3 (b) made FLAT + always-visible chapter pills the DEFAULT (no reader can
    # strand the pills behind a disclosure widget it can't operate); the expandable
    # Contents is a STRICT OPT-IN — reader_toc_collapsible must be exactly true (the
    # wizard offers it only for capable targets, e.g. Apple Books; e-ink term-ref-ok
    # ignore <details> still render the pills, so the opt-in degrades safely). The
    # legacy reader_toc_books_only flag is vestigial — flat is the default anyway —
    # and stays schema-accepted for back-compat. (K-R2 / user-directed 2026-06-09;
    # this also makes the /customize checkbox actually effective — the old
    # books_only coupling silently overrode it on every edition.)
    collapsible = edition.get("reader_toc_collapsible") is True
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
            # beta-3 (b): ALWAYS keep the chapter pills in the in-content ToC.
            # The user dropped the books-only / expand idea — every book label is
            # now followed by its always-visible chapter pills. `books_only` now
            # only means "flat, non-collapsible" (the <details> wrapper is removed
            # but the chapter <ol> is kept). Chapter nav is always visible inline.
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


# ── beta-3 (f)/(g): superscriptions, appendix demotion, eyebrow renumbering ──

# Books that are textual ADDITIONS, not standalone books: shown as modest inline
# appendix headings (no grand "BOOK N" title page), not numbered. The empty
# "Additions to Esther" (aes) is dropped from every canon entirely (canons.yaml);
# these three carry real text and become appendices to Daniel.
APPENDIX_BOOKS = ("paz", "sus", "bel")

_ROMAN_NUMERALS = (
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
)


def _to_roman(n: int) -> str:
    out: list[str] = []
    for val, sym in _ROMAN_NUMERALS:
        while n >= val:
            out.append(sym)
            n -= val
    return "".join(out)


_PSALM_SUPERSCRIPTION_RE = re.compile(
    r'(<p\b[^>]*class="ch-heading"[^>]*>.*?</p>\s*)<p class="verse-p[^"]*">(.*?)</p>',
    re.DOTALL,
)


def apply_superscriptions(tmp: Path) -> dict:
    """beta-3 (g): wrap chapter-start superscriptions (Psalm titles such as
    'A Prayer by David.') in ``<p class="superscription">`` so they read as a
    heading, not as scripture body. Scoped to the Psalms: the first verse
    paragraph after a chapter heading that carries NO verse anchor/marker is a
    superscription. Idempotent (a wrapped one is no longer a verse-p, so it is not
    re-matched). epub_working/ is untouched (operates on the temp tree)."""
    stats = {"superscriptions_wrapped": 0, "files_touched": 0}
    psa = config.books_by_code().get("psa")
    if not psa:
        return stats

    def repl(m: re.Match) -> str:
        head, body = m.group(1), m.group(2)
        # A real verse carries a verse anchor/marker; a superscription does not.
        if 'id="v-psa-' in body or 'class="vn"' in body or "vn-link" in body:
            return m.group(0)
        if len(body) > 240 or not body.strip():  # superscriptions are short, non-empty
            return m.group(0)
        stats["superscriptions_wrapped"] += 1
        return f'{head}<p class="superscription">{body}</p>'

    for fname in psa.get("files", []):
        fp = tmp / fname
        if not fp.is_file():
            continue
        text = fp.read_text(encoding="utf-8")
        new = _PSALM_SUPERSCRIPTION_RE.sub(repl, text)
        if new != text:
            fp.write_text(new, encoding="utf-8")
            stats["files_touched"] += 1
    return stats


_EYEBROW_RENUMBER_RE = re.compile(
    r'(<div class="book-title-page"[^>]*>'
    r'(?:(?!<div class="book-title-page").)*?'
    r'<p class="bookpage-eyebrow">)[^<]*(</p>)',
    re.DOTALL,
)


def apply_appendix_demotion_and_renumber(tmp: Path, canon_books: set[str] | None) -> dict:
    """beta-3 (f): (1) demote APPENDIX_BOOKS from grand 'BOOK N' title pages to
    modest inline appendix headings (so additions like Susanna read as part of
    their parent book, not separate books); (2) re-sequence every surviving
    'BOOK <roman>' eyebrow in spine order so the numbers are correct PER EDITION
    (a canon-filtered edition was showing the superset's numbers) and have no gaps
    where the empty 'Additions to Esther' or these appendices were removed. Runs
    AFTER the canon filter. epub_working/ is untouched (operates on the temp tree)."""
    stats = {"appendices_demoted": 0, "eyebrows_renumbered": 0, "files_touched": 0}
    books = config.books_by_code()
    touched: set[Path] = set()

    # (1) demote appendix book title pages — flip ONLY the opening div class so we
    # never have to balance the nested frame </div>. CSS .appendix-section drops the
    # page break, frame, BOOK eyebrow and plate art. Keep the bp-NN id so the ToC /
    # nav / ncx anchors still resolve.
    for code in APPENDIX_BOOKS:
        b = books.get(code)
        if not b:
            continue
        if canon_books is not None and code not in canon_books:
            continue  # already filtered out of this edition
        bp = b.get("bp", "")
        if not bp:
            continue
        needle = f'<div class="book-title-page" id="{bp}"'
        replacement = f'<div class="appendix-section" id="{bp}"'
        for fname in b.get("files", []):
            fp = tmp / fname
            if not fp.is_file():
                continue
            text = fp.read_text(encoding="utf-8")
            if needle in text:
                fp.write_text(text.replace(needle, replacement), encoding="utf-8")
                stats["appendices_demoted"] += 1
                touched.add(fp)

    # (2) renumber eyebrows in spine order (sorted index_split filenames). The
    # demoted appendices are now .appendix-section, so they are skipped → no number
    # is consumed and the sequence has no gaps.
    counter = 0

    def renum(m: re.Match) -> str:
        nonlocal counter
        counter += 1
        return f"{m.group(1)}BOOK {_to_roman(counter)}{m.group(2)}"

    for fp in sorted(tmp.glob("index_split_*.html")):
        text = fp.read_text(encoding="utf-8")
        new, n = _EYEBROW_RENUMBER_RE.subn(renum, text)
        if n and new != text:
            fp.write_text(new, encoding="utf-8")
            stats["eyebrows_renumbered"] += n
            touched.add(fp)

    stats["files_touched"] = len(touched)
    return stats


# A flat book navPoint in toc.ncx (no children yet): label + a #bp-NN content target.
_NCX_BOOK_NAVPOINT_RE = re.compile(
    r"<navPoint\b[^>]*>\s*<navLabel>\s*<text>[^<]*</text>\s*</navLabel>\s*"
    r'<content\s+src="index_split_\d+\.html#bp-(\d+)"\s*/>\s*</navPoint>'
)
# A book <li> in nav.xhtml: <li><a href="…#bp-NN">Book name</a></li>.
_NAV_BOOK_LI_RE = re.compile(r'(<li[^>]*>)\s*(<a\s+href="index_split_\d+\.html#bp-(\d+)"[^>]*>[^<]*</a>)\s*</li>')


def enrich_nav_chapters(tmp: Path) -> dict:
    """Add per-chapter entries under each book in nav.xhtml + toc.ncx so the reader's
    NATIVE table of contents keeps one-tap chapter navigation even when the in-content
    ToC is book-list-only (``reader_toc_books_only``). Chapter links point at the
    original ``index_split`` file holding each ``ch-bNN-cMM`` anchor; the later
    ``apply_file_split`` pass remaps them to the final pieces. No-op (epubcheck-safe)
    when nav files or chapter anchors are absent. Runs AFTER the canon filter (only
    surviving books' chapters are present) and BEFORE the splitter."""
    stats = {"nav_chapters_added": 0, "ncx_chapters_added": 0}

    # ch-bNN-cMM → the index_split file currently holding it; grouped per book, sorted.
    by_book: dict[int, list[tuple[int, str, str]]] = {}
    seen: set[str] = set()
    for p in sorted(tmp.glob("index_split_*.html")):
        for m in re.finditer(r'\bid="ch-b(\d+)-c(\d+)"', p.read_text(encoding="utf-8")):
            chid = f"ch-b{m.group(1)}-c{m.group(2)}"
            if chid in seen:
                continue
            seen.add(chid)
            by_book.setdefault(int(m.group(1)), []).append((int(m.group(2)), chid, p.name))
    if not by_book:
        return stats
    for chs in by_book.values():
        chs.sort()

    nav = tmp / "nav.xhtml"
    if nav.is_file():

        def _nav(mm: re.Match) -> str:
            chs = by_book.get(int(mm.group(3)))
            if not chs:
                return mm.group(0)
            items = "".join(f'<li><a href="{f}#{cid}">{n}</a></li>' for n, cid, f in chs)
            stats["nav_chapters_added"] += len(chs)
            return f'{mm.group(1)}{mm.group(2)}\n<ol class="toc-nav-chapters">{items}</ol>\n</li>'

        nav.write_text(_NAV_BOOK_LI_RE.sub(_nav, nav.read_text(encoding="utf-8")), encoding="utf-8")

    ncx = tmp / "toc.ncx"
    if ncx.is_file():
        ncx_text = ncx.read_text(encoding="utf-8")

        def _ncx(mm: re.Match) -> str:
            block = mm.group(0)
            chs = by_book.get(int(mm.group(1)))
            if not chs:
                return block
            kids = "".join(
                f'<navPoint id="num-{cid}" playOrder="0"><navLabel><text>{n}</text></navLabel>'
                f'<content src="{f}#{cid}"/></navPoint>'
                for n, cid, f in chs
            )
            stats["ncx_chapters_added"] += len(chs)
            return block[: -len("</navPoint>")] + kids + "</navPoint>"

        ncx_text = _NCX_BOOK_NAVPOINT_RE.sub(_ncx, ncx_text)
        # EPUB-2 NCX requires gapless playOrder — renumber every navPoint depth-first.
        counter = [0]

        def _renum(_m: re.Match) -> str:
            counter[0] += 1
            return f'playOrder="{counter[0]}"'

        ncx_text = re.sub(r'playOrder="\d+"', _renum, ncx_text)
        ncx.write_text(ncx_text, encoding="utf-8")

    return stats


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
#     every e-reader's built-in ToC sheet (Apple Books, Kindle, term-ref-ok
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


# ----------------------------------------------------------------------
# "About this Edition" front-matter page (2026-05-24)
#
# The LAST front-matter page (Title → Colophon → Guide → About). All
# data is composed from the edition's resolved choices — canon, matrix
# breakdown, popup witnesses, theme — so whatever the builder picked
# shows up automatically. No hardcoded counts.
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
# Back-matter pages (2026-05-24)
#
# Three end-of-book pages appended after the last biblical book:
#   1. Sources & Acknowledgments  (sources.xhtml,     id=backsources)
#   2. Reference Tables           (reftables.xhtml,   id=backreftables)
#   3. Closing Colophon           (colophonend.xhtml, id=backcolophon)
#
# Spine order: backsources → backreftables → backcolophon (genuinely last).
# A Topical Index will later be inserted before backcolophon — the seam
# is clean because all three items are appended to </spine> in order.
# ----------------------------------------------------------------------


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
    sources.append(REPO_ROOT / "content" / "editions.yaml")
    sources.append(REPO_ROOT / "scripts" / "build_edition.py")
    # mint-10: reach toward parity with build_cache._PIPELINE_SCRIPTS + the
    # content configs the build reads, so editing any of them invalidates this
    # cruder mtime-based "is the cached EPUB current?" check too (only bites on
    # a cold content-addressable cache). Additive + conservative — can only ever
    # force a (correct) rebuild, never skip one.
    sources.append(REPO_ROOT / "scripts" / "matter_pages.py")
    sources.append(REPO_ROOT / "scripts" / "epub_utils.py")
    sources.append(REPO_ROOT / "content" / "kinds.yaml")
    sources.append(REPO_ROOT / "content" / "categories.yaml")
    sources.append(REPO_ROOT / "content" / "books.yaml")
    sources.extend((REPO_ROOT / "content" / "themes").glob("*.css"))
    # mint-9 (opt): the notes corpus also feeds the build (filter/attribution),
    # so a notes edit must invalidate a cached build. Watch every notes/*.py too
    # or a direct `build_edition.py` run after editing notes serves a stale EPUB.
    # Additive + conservative — it can only ever force a (correct) rebuild.
    sources.extend((REPO_ROOT / "content" / "notes").glob("*.py"))
    # mint-11 #25: compose the FULL build_cache pipeline-script set + the topical /
    # source-date DATA the build reads, so this mtime check can't drift from
    # build_cache._PIPELINE_SCRIPTS again (local import avoids any circular load).
    # Additive + conservative — can only ever force a (correct) rebuild.
    from scripts.core.build_cache import _PIPELINE_SCRIPTS as _PS

    sources.extend(REPO_ROOT / "scripts" / s for s in _PS)
    sources.append(REPO_ROOT / "content" / "source_dates.yaml")
    sources.append(REPO_ROOT / "content" / "sources" / "naves_topical.json")
    sources.append(REPO_ROOT / "content" / "sources" / "torrey_topical.json")
    for s in sources:
        if s.is_file() and s.stat().st_mtime > out_mtime:
            return None
    return latest


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
    code_by_prefix: dict[str, str] = {}
    for i, book in enumerate(all_books):
        # bp_idx parses from book["bp"] like "bp-15" → 15
        bp = book.get("bp", "")
        m = re.match(r"bp-(\d+)", bp)
        idx = int(m.group(1)) if m else i
        code_by_idx[idx] = book["code"]
        # Strategy-B `bxx` fallback — same id_prefix→bxx ladder used by
        # _iter_note_ref_symbols. The chapter anchors in the base HTML carry
        # this prefix (``<a id="ch-<prefix>-cN">``); we use it to identify a
        # dropped book's *spilled* segment when it has no book-title-page
        # anchor in the file (a multi-file book whose continuation shares a
        # file with a later kept book).
        _prefix = book.get("id_prefix") or book.get("bxx")
        if _prefix:
            code_by_prefix[_prefix] = book["code"]

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

        # Leading-spillover guard: a multi-file book's continuation can share a
        # file with a *later* kept book and have NO book-title-page anchor of
        # its own in that file (its title page lived in the prior, now-deleted
        # file). _BOOK_SEGMENT_RE only matches segments that *begin* with a
        # book-title-page div, so that leading orphan region (verse text +
        # note-ref markers) would survive — shipping a dropped book's content
        # (and orphan markers → epubcheck RSC-012). When the region before the
        # first book-title-page belongs entirely to dropped books, splice it
        # out. Identified via its chapter-anchor prefixes
        # (``<a id="ch-<prefix>-c…">``) mapped back to book codes. The now-
        # orphaned asides for these notes are removed by Pass 3 below (it drops
        # any aside whose ``id="ref-…"`` marker is gone).
        lead_spliced = False
        _first_bp = text.find('<div class="book-title-page"')
        if _first_bp > 0:
            _body_m = re.search(r"<body[^>]*>", text[:_first_bp])
            _lead_start = _body_m.end() if _body_m else 0
            _lead = text[_lead_start:_first_bp]
            # Anchors are bxx-form (ch-b21-c7…) for all books. Strategy-A books
            # (gen-deu) appear in every canon, so their leading spillover never
            # needs stripping; any unrecognized prefix maps to None and trips
            # the guard below (no strip). So the conservative default is safe.
            _lead_prefixes = set(re.findall(r'id="ch-(b\d+)-c', _lead))
            _lead_codes = {code_by_prefix.get(p) for p in _lead_prefixes}
            # Strip only when the leading region carries book content, every
            # prefix resolves to a known book, and every such book is dropped
            # (never strip a kept book's spillover or an unrecognized prefix).
            if _lead_prefixes and None not in _lead_codes and _lead_codes <= dropped:
                text = text[:_lead_start] + text[_first_bp:]
                lead_spliced = True

        def _maybe_drop(m: re.Match) -> str:
            idx = int(m.group(1))
            code = code_by_idx.get(idx)
            if code in dropped:
                return ""  # splice out the segment
            return m.group(0)  # keep

        new_text, n_subs = _BOOK_SEGMENT_RE.subn(_maybe_drop, text)
        if new_text != text or lead_spliced:
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

            # mint-9 #21/#22: count only links we actually STRIP, not every match.
            # subn's return value is the total match count, but _check_anchor /
            # _check_file_only leave kept links unchanged (return m.group(0)), so
            # `+= n1` overcounted cross_refs_stripped by every surviving link.
            # nonlocal counters incremented only on the strip branches fix the
            # stat without touching the output bytes.
            stripped_here = 0

            def _check_anchor(m: re.Match, fname: str = f.name) -> str:
                nonlocal stripped_here
                target_file, anchor, visible = m.group(1), m.group(2), m.group(3)
                # Resolve target file: empty = same file
                target = target_file if target_file else fname
                if target not in id_inventory:
                    # File was dropped — strip wrapper
                    stripped_here += 1
                    return visible
                if anchor not in id_inventory[target]:
                    # Anchor was spliced out — strip wrapper
                    stripped_here += 1
                    return visible
                return m.group(0)

            new_text, _n1 = link_re.subn(_check_anchor, text)

            def _check_file_only(m: re.Match, fname: str = f.name) -> str:
                nonlocal stripped_here
                target_file, visible = m.group(1), m.group(2)
                # Skip non-html refs (mailto, http, etc.)
                if not target_file.endswith(".html") and not target_file.endswith(".xhtml"):
                    return m.group(0)
                if target_file not in id_inventory and target_file != fname:
                    stripped_here += 1
                    return visible  # strip
                return m.group(0)

            new_text2, _n2 = file_only_re.subn(_check_file_only, new_text)
            stats["cross_refs_stripped"] += stripped_here

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


# ----------------------------------------------------------------------
# §4.5 — per-book title-page art (full-bleed / framed)
# ----------------------------------------------------------------------

_BOOK_TITLE_PAGE_RE = re.compile(r'<div class="book-title-page"([^>]*)>\s*<div class="book-title-frame">')
_BOOK_IMG_MEDIA = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}


def _resolve_book_art(code: str, per_book: dict[str, str]) -> Path | None:
    """Resolve a book's title-page art. Three-tier: uploaded override
    (``book_covers``, relative to ``content/``) → ``content/covers/
    _book_defaults/<code>.jpg`` → ``None`` (text-only title page)."""
    content = REPO_ROOT / "content"
    override = per_book.get(code, "")
    if override:
        p = Path(override)
        if not p.is_absolute():
            p = content / override
        if p.is_file():
            return p
    default = content / "covers" / "_book_defaults" / f"{code}.jpg"
    return default if default.is_file() else None


def apply_title_pages(tmp: Path, edition: dict, canon_books: set[str] | None) -> list[str]:
    """Inject each KEPT book's title-page art into its ``book-title-frame`` in
    the per-build ``tmp`` tree, per ``title_page_style`` (framed default /
    full-bleed opt-in). Returns the OPF-relative image paths copied in (for
    ``patch_opf_book_images``). Books with no resolvable art keep the text-only
    title page. MUST run after canon filtering so dropped books leave no orphan
    image manifest items. Every injected ``<img>`` carries descriptive ``alt``
    (check_a11y requires it)."""
    from scripts.core import covers

    style = edition.get("title_page_style") or "framed"
    if style not in TITLE_PAGE_STYLES:
        style = "framed"
    per_book = covers.decode_book_covers(edition.get("book_covers"))

    idx_to_art: dict[int, tuple[str, str]] = {}
    image_paths: list[str] = []
    images_dir = tmp / "images"
    for i, book in enumerate(config.load_books()):
        code = book["code"]
        if canon_books is not None and code not in canon_books:
            continue
        bp = book.get("bp", "")
        idx = int(bp.split("-", 1)[1]) if bp.startswith("bp-") else i
        art = _resolve_book_art(code, per_book)
        if art is None:
            continue
        ext = art.suffix.lstrip(".").lower() or "jpg"
        ext = "jpg" if ext == "jpeg" else ext
        rel = f"images/book-{code}.{ext}"
        images_dir.mkdir(exist_ok=True)
        shutil.copy2(art, tmp / rel)
        idx_to_art[idx] = (rel, f"Illustration — {book.get('title', code)}")
        image_paths.append(rel)

    if not idx_to_art:
        return []

    def _inject(m: re.Match) -> str:
        attrs = m.group(1)
        im = re.search(r'data-book-idx="(\d+)"', attrs)
        if not im:
            return m.group(0)
        art = idx_to_art.get(int(im.group(1)))
        if not art:
            return m.group(0)  # text-only fallback (no art for this book)
        src, alt = art
        alt_x = html.escape(alt, quote=True)
        if style == "framed":
            return (
                f'<div class="book-title-page"{attrs}>\n  <div class="book-title-frame">\n'
                f'    <img class="bookpage-art" src="{src}" alt="{alt_x}"/>'
            )
        return (
            f'<div class="book-title-page style-full-bleed"{attrs}>\n'
            f'  <img class="bookpage-art-bleed" src="{src}" alt="{alt_x}"/>\n'
            '  <div class="book-title-frame">'
        )

    for html_path in tmp.glob("*.html"):
        text = html_path.read_text(encoding="utf-8")
        new = _BOOK_TITLE_PAGE_RE.sub(_inject, text)
        if new != text:
            html_path.write_text(new, encoding="utf-8")

    return sorted(set(image_paths))


def patch_opf_book_images(opf_text: str, image_paths: list[str]) -> str:
    """Register per-book title-page images in the OPF manifest (model:
    ``patch_opf_fonts``). No-op when empty (byte-identical for art-less
    editions); skips already-registered paths (idempotent)."""
    if not image_paths:
        return opf_text
    new_items: list[str] = []
    for rel in image_paths:
        if f'href="{rel}"' in opf_text:
            continue
        ext = rel.rsplit(".", 1)[-1].lower()
        media_type = _BOOK_IMG_MEDIA.get(ext, "image/jpeg")
        stem = rel.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        img_id = re.sub(r"[^A-Za-z0-9]+", "-", stem).strip("-").lower() or "bookimg"
        new_items.append(f'<item id="{img_id}" href="{rel}" media-type="{media_type}"/>')
    if not new_items:
        return opf_text
    insertion = "\n    " + "\n    ".join(new_items) + "\n  "
    return opf_text.replace("</manifest>", f"{insertion}</manifest>", 1)


def apply_edition_cover(edition: dict, build_dir: Path) -> str | None:
    """Swap the base master cover (``build_dir/cover.jpeg``) for the edition's
    declared ``cover_image`` when it resolves to a real file under ``content/``.

    Returns the applied ``cover_image`` path, or ``None`` when the edition
    declares no cover / the file is missing / there's no master cover to
    replace — in which case the master cover is kept. This is the §7.2
    back-compat case (σ.5 gave the 2 standalone bibles composed covers; any
    edition that declares no cover stays byte-identical). Resolution + the content/
    sandbox are reused from ``covers.resolve_cover_path`` (compose, don't
    recompute). Mirrors the theme-override step in ``build_one``."""
    from scripts.core.covers import resolve_cover_path

    src = resolve_cover_path(edition)
    dst = build_dir / "cover.jpeg"
    if src is None or not dst.is_file():
        return None
    shutil.copyfile(src, dst)
    return str(edition.get("cover_image") or "")


def compute_edition_filter_sets(edition: dict) -> tuple[set[str], set[str]]:
    """Return (disabled_kinds_for_filter, disabled_html_ref_ids) — exactly the
    two sets ``build_one`` uses to strip notes (via ``filter_html``). Single
    source of truth for "what ships" so ``edition_stats.resolved_note_counts``
    matches the built EPUB by construction.

    Folds in: edition-wide disabled kinds (minus symbol-overridden kinds),
    explicit per-note ``disabled_note_ids``, the tradition + time filters, the
    per-book/per-chapter symbol OFF overrides, minus the ``enabled_note_ids``
    force-on (applied last).

    ``all_kinds`` is recomputed from ``config.load_kinds()`` — the same cached
    list every ``build_one`` caller passes — so the result is identical to the
    block this was extracted from.
    """
    all_kinds = config.load_kinds()
    enabled, disabled = compute_enabled_kinds(edition, all_kinds)

    # Phase ρ.1: per-edition disabled note IDs. Translate our note IDs
    # (book:ch:vs[suffix]:kind) into the HTML ref-id format the build sees
    # (ref-<prefix><cc><vv><suffix>).
    disabled_note_ids = list(edition.get("disabled_note_ids") or [])
    disabled_html_ref_ids: set[str] = set()
    if disabled_note_ids:
        books_idx = config.books_by_code()
        note_id_re = _NOTE_ID_RE
        for nid in disabled_note_ids:
            m = note_id_re.match(nid)
            if not m:
                continue
            book_code = m.group(1)
            book = books_idx.get(book_code) or {}
            # Strategy-B bxx fallback — see _iter_note_ref_traditions (mint-9 #2).
            # Without it, an explicit disabled_note_ids entry for a Strategy-B
            # book (e.g. 2ch) is silently ignored and the note ships anyway.
            prefix = book.get("id_prefix") or book.get("bxx")
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

    # Phase ρ.3: per-book / per-chapter symbol overrides → ref-ids, and the
    # enabled_note_ids force-on (absolute finest — subtracted last).
    overridden_kinds = _symbol_overridden_kinds(edition, all_kinds)
    disabled_html_ref_ids |= compute_symbol_disabled_html_ref_ids(edition, all_kinds, overridden_kinds)

    force_on_ref_ids: set[str] = set()
    _enabled_nids = list(edition.get("enabled_note_ids") or [])
    if _enabled_nids:
        # books_idx may already be set from the disabled_note_ids block above;
        # config.books_by_code() delegates to lru_cache(load_books) so the
        # second call is free.
        _fon_books_idx = config.books_by_code()
        for nid in _enabled_nids:
            m = _NOTE_ID_RE.match(nid)
            if not m:
                continue
            _book = _fon_books_idx.get(m.group(1)) or {}
            _prefix = _book.get("id_prefix") or _book.get("bxx")
            if not _prefix:
                continue
            force_on_ref_ids.add(f"ref-{_prefix}{int(m.group(2)):02d}{int(m.group(3)):02d}{m.group(4)}")
    disabled_html_ref_ids -= force_on_ref_ids

    # Overridden kinds are resolved at ref-id granularity above, so they must
    # NOT be whole-kind-stripped (else a per-coordinate ON could never re-include
    # them). All other edition-disabled kinds keep the efficient whole-kind strip.
    disabled_kinds_for_filter = disabled - overridden_kinds

    return disabled_kinds_for_filter, disabled_html_ref_ids


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

    # Phase C3d: standalone Bibles render from the own-versification store via a
    # dedicated path; the 9 KJV editions never enter this branch, so their output
    # is byte-identical to before. Single chokepoint — every build_one caller is routed.
    if edition.get("standalone"):
        from scripts import build_standalone

        return build_standalone.build_standalone(edition_id, output_dir, version)

    enabled, disabled = compute_enabled_kinds(edition, all_kinds)

    # Phases ρ.1 / ψ.8.2-A / ψ.37-B / ρ.3: the two filter sets that decide
    # which notes ship are assembled by ``compute_edition_filter_sets`` (the
    # single source of truth shared with ``edition_stats.resolved_note_counts``
    # so the printed counts match the built EPUB by construction). ``enabled`` /
    # ``disabled`` are kept above because the stats sidecar below still consumes
    # them (the σ.6.2 matter-page counts now come from resolved_note_counts).
    disabled_kinds_for_filter, disabled_html_ref_ids = compute_edition_filter_sets(edition)
    # Pre-compile the kind-filter regexes ONCE per edition — they're identical for
    # every split file, so build them here instead of (re)compiling per kind per
    # file inside filter_html. One marker alternation + one aside alternation over
    # all disabled kinds; filter_html falls back to building them itself for
    # callers that don't pass them.
    _kind_marker_re, _kind_aside_re = _build_disabled_kind_res(disabled_kinds_for_filter)

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
    # edition has explicit popup_languages config in ANY of the five
    # resolution tiers that _resolve_popup_languages consults
    # (per-verse > per-chapter > per-book > default > DEFAULT). If none,
    # the pass would be a no-op so we skip it to keep build times tight.
    # mint-11 audit MED: per-chapter / per-verse were missing here, so an
    # edition setting ONLY one of them silently skipped all language pruning.
    needs_vnote_pass = verse_popups_enabled and (
        bool(popup_translation_id)
        or edition.get("popup_languages_default") is not None
        or bool(edition.get("popup_languages_per_book"))
        or bool(edition.get("popup_languages_per_chapter"))
        or bool(edition.get("popup_languages_per_verse"))
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
                disabled_kinds_for_filter,
                disabled_html_ref_ids,
                verse_popups_enabled=verse_popups_enabled,
                kind_marker_re=_kind_marker_re,
                kind_aside_re=_kind_aside_re,
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

        # §4.2 verse_popup_style — append the cards/stack variant CSS (cards =
        # default tinted-card chrome; stack = flat base). Same append-to-stylesheet
        # mechanism as the theme override above; the popup HTML is unchanged.
        if css_path.is_file():
            vps = (edition.get("verse_popup_style") or "cards").strip() or "cards"
            css_path.write_text(
                apply_verse_popup_style(css_path.read_text(encoding="utf-8"), vps),
                encoding="utf-8",
            )
            stats["verse_popup_style"] = vps

        # §4.4 note_popup_style — append the chip/pills variant CSS (chip =
        # default tinted label-chip; pills = bordered cross-reference pills).
        # Same append-to-stylesheet mechanism; the note HTML is unchanged.
        if css_path.is_file():
            nps = (edition.get("note_popup_style") or "chip").strip() or "chip"
            css_path.write_text(
                apply_note_popup_style(css_path.read_text(encoding="utf-8"), nps),
                encoding="utf-8",
            )
            stats["note_popup_style"] = nps

        # S2 note cascade — append the robust-layer CSS (15 per-category group
        # spines + header/source/byline/indent rules) when note_group_by_category
        # is on. Same append-to-stylesheet mechanism; absent ⇒ byte-identical.
        if css_path.is_file() and bool(edition.get("note_group_by_category", False)):
            css_path.write_text(
                apply_note_cascade_css(css_path.read_text(encoding="utf-8")),
                encoding="utf-8",
            )
            stats["note_cascade_css"] = True

        # Per-edition cover (fixes visual-QA finding b): the base
        # epub_working/cover.jpeg is the master cover; swap in the edition's
        # declared cover_image when it resolves to a real file. All 11 editions
        # now declare a cover (9 curated + the 2 standalone Bibles' Ethiopic-
        # script covers, σ.5); any edition that declares none keeps the master
        # (§7.2 back-compat). The OPF already marks cover.jpeg
        # as the cover-image; this replaces the BYTES it points at.
        cover_applied = apply_edition_cover(edition, tmp)
        if cover_applied:
            stats["cover_applied"] = cover_applied

        # Wave-3 marker_style=numbers: the base is numbered base-wide, so a
        # filtered edition (which drops some kinds' markers) would read 1,3,4,7…
        # Renumbering the survivors per chapter after filter_html keeps every
        # edition at 1,2,3…. The same renumber pass that numbered the base; it is
        # idempotent on an unfiltered file, so the superset flagship's build is
        # byte-identical to a pre-renumber build.
        from scripts.resync_marker_glyphs import renumber_markers

        for html_path in tmp.glob("*.html"):
            text = html_path.read_text(encoding="utf-8")
            new_text, counts = filter_html(
                text,
                disabled_kinds_for_filter,
                disabled_html_ref_ids,
                verse_popups_enabled=verse_popups_enabled,
                kind_marker_re=_kind_marker_re,
                kind_aside_re=_kind_aside_re,
            )
            stats["markers_removed"] += counts["markers"]
            stats["asides_removed"] += counts["asides"]
            stats["id_markers_removed"] += counts.get("id_markers", 0)
            stats["id_asides_removed"] += counts.get("id_asides", 0)
            stats["vn_links_disabled"] += counts.get("vn_links_disabled", 0)

            # Close the numbering gaps left by the kind/id filter above.
            new_text, _ = renumber_markers(new_text)

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
                stats["vnote_kjv_fallbacks"] = stats.get("vnote_kjv_fallbacks", 0) + vp_counts.get("kjv_fallbacks", 0)

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
        canon_books: set[str] | None = None
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

        # §4.5 — inject per-book title-page art (full-bleed/framed). After the
        # canon filter so dropped books leave no orphan image manifest items.
        book_image_paths = apply_title_pages(tmp, edition, canon_books)
        stats["book_title_images"] = len(book_image_paths)

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
            opf_text = patch_opf_book_images(opf_text, book_image_paths)
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

        # beta-3 (f) — demote appendix books (Daniel additions) to inline appendix
        # headings and renumber the BOOK <roman> eyebrows per edition: no gaps from
        # the dropped empty "Additions to Esther" or the demoted appendices, and
        # canon-filtered editions no longer show the superset's numbers.
        appendix_stats = apply_appendix_demotion_and_renumber(tmp, canon_books)
        stats["appendices_demoted"] = appendix_stats["appendices_demoted"]
        stats["eyebrows_renumbered"] = appendix_stats["eyebrows_renumbered"]

        # beta-3 (g) — wrap Psalm/incipit superscriptions in .superscription so they
        # read as headings, not scripture body.
        supersc_stats = apply_superscriptions(tmp)
        stats["superscriptions_wrapped"] = supersc_stats["superscriptions_wrapped"]

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

        # §4.1 marker_style=badge (Phase 5) — collapse each verse's per-note
        # markers into ONE count badge + merge its asides into ONE per-verse
        # listing aside. Runs AFTER every kind/canon/tradition filter + the
        # renumber pass (so the temp HTML holds only THIS edition's surviving
        # notes) and BEFORE the front/back-matter injection (which adds no
        # bodymatter markers). Gated on marker_style; "numbers" leaves the temp
        # HTML in its per-note form (byte-identical to the historical build).
        marker_style = (edition.get("marker_style") or DEFAULT_MARKER_STYLE).strip() or DEFAULT_MARKER_STYLE
        stats["marker_style"] = marker_style
        if marker_style == "badge":
            badge_stats = apply_badge_markers(tmp, edition)
            stats["badges_inserted"] = badge_stats["badges_inserted"]
            stats["badge_notes_collapsed"] = badge_stats["notes_collapsed"]
            stats["badge_verses_skipped"] = badge_stats["badges_skipped"]

        # Inject per-edition copyright/credits page. σ.6.2 — its printed
        # annotation/category counts come from edition_stats.resolved_note_counts
        # (the build-accurate counter), so they equal the symbol legend, the
        # "Your Edition" page, and the real EPUB. This retired the mint-9 #8
        # annotation_count_override (which corrected only the tradition/time
        # ref-id filters): resolved_note_counts subsumes it AND adds the rest of
        # the ρ.3 hierarchy + the base-coverage gate — strictly more accurate.
        inject_copyright_page(tmp, edition)
        inject_dedication_page(tmp, edition)
        # σ.3.2 — the "Your Edition" page is the FIRST content page after the
        # cover. It anchors its spine/nav insert at the titlepage and runs AFTER
        # copyright + dedication (each of which also inserts after titlepage), so
        # the last-runs-first ordering lands it immediately after titlepage:
        # titlepage → your-edition → dedication → copyright → legend. Its
        # build-accurate counts (resolved_note_counts) replace the retired About
        # page, which carried the matrix-based summary.
        inject_your_edition_page(tmp, edition, version)
        inject_symbol_legend_page(tmp, edition)
        inject_back_matter(tmp, edition, canon_books)

        # ψ.19.1 — inject the per-edition reading-plans page (no-op
        # when `enabled_reading_plans` is empty, preserving pre-ψ.19.1
        # build-byte behavior per §6.5).
        rp_stats = inject_reading_plans_page(tmp, edition)
        stats["reading_plans_written"] = rp_stats.get("plans_written", 0)
        stats["reading_plans_total_days"] = rp_stats.get("total_days", 0)

        # RX P4a-2 — when the in-content ToC is book-list-only, enrich the NATIVE ToC
        # (nav.xhtml + toc.ncx) to chapter level so one-tap chapter navigation survives
        # in the reader's own ToC menu. MUST run LAST among the nav passes — after every
        # front/back-matter + reading-plan insertion (each assumes a flat single-<ol>
        # book list and inserts at the first </ol>; running before them would land their
        # entries inside the first book's nested chapter <ol> → an out-of-spine-order
        # nav, epubcheck NAV-011). Runs BEFORE the splitter, which remaps the chapter
        # hrefs from the index_split files to the final pieces.
        # RX-beta2 ⑧: per-chapter native-ToC enrichment is now OPT-IN via
        # ``reader_native_toc_chapters`` (default off). On long-chapter books it made
        # the Kobo native ToC an endless scroll; book-level is now the default (the
        # nav.xhtml/toc.ncx already carry the book-level entries from the canon patch).
        if edition.get("reader_native_toc_chapters"):
            nav_ch = enrich_nav_chapters(tmp)
            stats["nav_chapters_added"] = nav_ch["nav_chapters_added"]
            stats["ncx_chapters_added"] = nav_ch["ncx_chapters_added"]

        # RX Phase 4b — file-split for e-ink (Kobo) speed. Runs LAST (after badge +
        # every matter-page injection) so its OPF/nav/ncx regeneration is the final
        # word before the zip: splits the 2-5 MB index_split_* into ~0.4 MB pieces,
        # remaps every cross-file href, and rebuilds the manifest/spine/nav/ncx.
        # No-op (byte-identical) unless the edition sets reader_file_split.
        split_stats = apply_file_split(tmp, edition)
        stats["files_split"] = split_stats["files_split"]
        stats["pieces_created"] = split_stats["pieces_created"]
        stats["largest_piece_kb"] = split_stats["largest_piece_kb"]

        # Build EPUB. In a PyInstaller-frozen binary ``sys.executable`` is the
        # launcher (YHWH.exe), NOT a Python interpreter — so re-invoking
        # ``build_epub.py`` as a subprocess breaks (the launcher's argparse
        # rejects the script path). Call build_epub IN-PROCESS when frozen;
        # keep the subprocess in dev so ``--all`` builds still parallelize
        # across processes (build_epub's zip step releases the GIL — see main()).
        if getattr(sys, "frozen", False):
            from scripts import build_epub as _build_epub

            try:
                _build_epub.build(tmp, output_path, bump=False)
            except SystemExit as e:  # build_epub.err() may sys.exit; surface as a build error
                raise RuntimeError(f"build_epub failed (exit {e.code})") from e
        else:
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
                stdin=subprocess.DEVNULL,
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
