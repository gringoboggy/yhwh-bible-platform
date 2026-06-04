#!/usr/bin/env python3
"""
web_editions.py — customize-data, edition-template, reading-plan,
build-tracker, and per-edition disabled-note JSON API handlers,
extracted from scripts/web.py in the god-module split (2026-05-26).

Pure relocation: every handler here was moved verbatim from
``scripts/web.py``. ``scripts/web.py`` re-exports every name so the
route table + external importers keep resolving them in web.py's
namespace.
"""

from __future__ import annotations

from scripts.core import config
from scripts.web_helpers import REPO


def api_edition_templates_list() -> dict:
    """ψ.7-B — List every edition starter-pack template, sorted by
    template_id. Read-only.

    Returns:
        {"templates": [{template_id, label, description, canon,
                        target_audience}, ...]}

    Surfaced at GET /api/edition-templates. Used by the wizard's
    Step 1 "Start from template…" picker.
    """
    from scripts.core import edition_templates as et

    out = []
    for t in et.load_templates():
        out.append(
            {
                "template_id": t["template_id"],
                "label": t.get("template_label", t["template_id"]),
                "description": t.get("template_description", ""),
                "canon": t.get("canon", ""),
                "target_audience": t.get("target_audience", ""),
            }
        )
    return {"templates": out}


def api_build_tracker(edition_id: str) -> dict:
    """Ω.0 free-public pivot (2026-05-14) — feed for /build-tracker.

    Shows the builder exactly what is enabled in a single edition:
    summary tile counts, per-book × per-chapter enabled-note density,
    per-category and per-kind breakdowns. Composes the existing
    matrix store (per_chapter is canonical post-ψ.35-Final).

    Returns:
        {
            "edition": {id, title, short_title, canon},
            "summary": {total_enabled_notes, books_covered,
                        books_in_canon, chapters_covered,
                        chapters_in_canon, kinds_enabled,
                        categories_enabled, popup_languages},
            "per_book": [
                {book_code, book_label, chapters_in_canon,
                 enabled_notes, enabled_chapters, by_chapter},
                ...
            ],
            "per_category": [{id, label, enabled_notes}, ...],
            "per_kind": [{code, label, category, enabled_notes}, ...],
        }

    Returns ``{"error": "unknown edition", "http": 404}`` when the
    edition isn't in editions.yaml.

    Pinned by ``TestBuildTrackerEndpoint`` in test_scripts.py.
    """
    from scripts.core import matrix as matrix_mod

    eds_by_id = config.editions_by_id()
    if edition_id not in eds_by_id:
        return {"error": f"unknown edition: {edition_id}", "http": 404}

    edition = eds_by_id[edition_id]
    m = matrix_mod.compute_matrix()
    books_idx = {b["code"]: b for b in config.load_books()}
    kinds_idx = {k["code"]: k for k in config.load_kinds()}
    cats_idx = {c["id"]: c for c in config.load_categories()}

    canon_books = m.edition_canon_books.get(edition_id, set())
    enabled_kinds = m.edition_enabled_kinds.get(edition_id, set())
    per_chapter_ed = m.per_chapter.get(edition_id, {})

    # Per-book: walk canon books in canonical order; sum enabled
    # kinds' per_chapter counts.
    book_order = list(books_idx.keys())  # already canonical from books.yaml
    per_book = []
    total_notes = 0
    books_covered = 0
    chapters_in_canon_total = 0
    chapters_covered_total = 0
    for book_code in book_order:
        if book_code not in canon_books:
            continue
        book_def = books_idx[book_code]
        ch_count = int(book_def.get("ch_count") or 0)
        chapters_in_canon_total += ch_count
        # by_chapter is a flat array (1-indexed → array index = ch-1).
        by_chapter = [0] * ch_count
        for kind, by_book in per_chapter_ed.items():
            if kind not in enabled_kinds:
                continue
            for ch_num, count in by_book.get(book_code, {}).items():
                idx = int(ch_num) - 1
                if 0 <= idx < ch_count:
                    by_chapter[idx] += int(count)
        book_total = sum(by_chapter)
        book_chapters_covered = sum(1 for n in by_chapter if n > 0)
        total_notes += book_total
        chapters_covered_total += book_chapters_covered
        if book_total > 0:
            books_covered += 1
        per_book.append(
            {
                "book_code": book_code,
                "book_label": book_def.get("title") or book_def.get("label") or book_code,
                "chapters_in_canon": ch_count,
                "enabled_notes": book_total,
                "enabled_chapters": book_chapters_covered,
                "by_chapter": by_chapter,
            }
        )

    # Per-category + per-kind aggregates (only kinds that are enabled
    # AND have non-zero notes show up).
    cat_totals: dict[str, int] = {}
    kind_rows: list[dict] = []
    for kind, by_book in per_chapter_ed.items():
        if kind not in enabled_kinds:
            continue
        kind_total = 0
        for book_code, by_ch in by_book.items():
            if book_code not in canon_books:
                continue
            kind_total += sum(int(v) for v in by_ch.values())
        if kind_total <= 0:
            continue
        kind_def = kinds_idx.get(kind, {})
        cat_id = kind_def.get("category", "?")
        cat_totals[cat_id] = cat_totals.get(cat_id, 0) + kind_total
        kind_rows.append(
            {
                "code": kind,
                "label": kind_def.get("label", kind),
                "category": cat_id,
                "enabled_notes": kind_total,
            }
        )
    kind_rows.sort(key=lambda r: (-r["enabled_notes"], r["code"]))
    per_category = [
        {
            "id": cid,
            "label": cats_idx.get(cid, {}).get("label", cid),
            "enabled_notes": cat_totals[cid],
        }
        for cid in sorted(cat_totals.keys(), key=lambda c: (-cat_totals[c], c))
    ]

    popup_langs = list(edition.get("popup_languages_default") or [])

    return {
        "edition": {
            "id": edition_id,
            "title": edition.get("title", edition_id),
            "short_title": edition.get("short_title", edition_id),
            "canon": edition.get("canon"),
        },
        "summary": {
            "total_enabled_notes": total_notes,
            "books_covered": books_covered,
            "books_in_canon": len(canon_books),
            "chapters_covered": chapters_covered_total,
            "chapters_in_canon": chapters_in_canon_total,
            "kinds_enabled": len([r for r in kind_rows if r["enabled_notes"] > 0]),
            "categories_enabled": len(per_category),
            "popup_languages": popup_langs,
        },
        "per_book": per_book,
        "per_category": per_category,
        "per_kind": kind_rows,
    }


def api_build_tracker_book(edition_id: str, book_code: str) -> dict:
    """Ω.0 free-public pivot — per-book note-title detail for the
    /build-tracker drilldown. Loaded lazily when the user opens a
    book's details panel.

    Returns ``{"notes": [{chapter, kind, title, id}, ...]}`` for
    notes whose kind is enabled in the edition. The list is bounded
    by canon membership + enabled kind set so it's safe to fetch
    even on the Ethiopian flagship.

    Pinned by ``TestBuildTrackerBookEndpoint``.
    """
    from scripts.core import matrix as matrix_mod
    from scripts.core import notes_io

    eds_by_id = config.editions_by_id()
    if edition_id not in eds_by_id:
        return {"error": f"unknown edition: {edition_id}", "http": 404}
    m = matrix_mod.compute_matrix()
    canon_books = m.edition_canon_books.get(edition_id, set())
    if book_code not in canon_books:
        return {"error": f"book {book_code} not in {edition_id}'s canon", "http": 404}
    enabled_kinds = m.edition_enabled_kinds.get(edition_id, set())

    notes_dir = REPO / "content" / "notes"
    book_file = notes_dir / f"{book_code}.py"
    raw = notes_io.load_notes(book_file) or []
    # NOTES are 9-tuples per content/notes/<book>.py docstring:
    # (chapter, verse, suffix, anchor, kind, title, label, body_html
    #  [, attribution]). Index by position.
    out = []
    for n in raw:
        if not isinstance(n, tuple) or len(n) < 7:
            continue
        chapter = n[0]
        suffix = n[2] or ""
        anchor = n[3] or ""
        kind = n[4] or ""
        title = n[5] or ""
        if kind not in enabled_kinds:
            continue
        # Synthesize a stable id for sort + DOM keying.
        note_id = f"{book_code}-{chapter}-{suffix}" if suffix else f"{book_code}-{chapter}"
        out.append(
            {
                "id": note_id,
                "chapter": int(chapter or 0),
                "kind": kind,
                "title": (title or anchor)[:200],
            }
        )
    out.sort(key=lambda r: (r["chapter"], r["kind"], r["id"]))
    return {"book_code": book_code, "notes": out}


def api_reading_plans_list() -> dict:
    """Return a summary of every reading plan in
    ``content/reading_plans/``.

    Each plan is summarized to ``{id, label, description,
    entry_count, first_day, last_day}`` so the /customize card
    doesn't ship the full per-day verse lists.
    """
    from scripts.core.reading_plans import list_plans, plan_summary

    plans = list_plans()
    return {
        "status": "ok",
        "plans": [plan_summary(p) for p in plans],
    }


def api_reading_plan_get(plan_id: str) -> dict:
    """Return one plan's full record (every entry's verses).

    Used by the build pipeline integration (ψ.19.1, deferred) and
    by future preview / UI surfaces that want to inspect a plan
    in detail.
    """
    from scripts.core.reading_plans import load_plan

    try:
        plan = load_plan(plan_id)
    except ValueError as e:
        return {"status": "error", "code": "invalid_plan", "http": 400, "message": str(e)}
    if plan is None:
        return {"status": "error", "code": "not_found", "http": 404, "message": f"plan {plan_id!r} not found"}
    return {"status": "ok", "plan": plan.to_dict()}


def api_customize_data() -> dict:
    """Return the full categories+kinds+editions+themes dataset for the customize UI."""
    cats = config.load_categories()
    kinds = config.load_kinds()
    editions = config.load_editions()
    themes = _load_themes()
    # Phase τ.1.5 — expose the on-disk translation list so the UI can
    # render a per-edition picker. Includes a small meta blob for each
    # so the dropdown can show a friendly title.
    from scripts.core import translations as _tx

    translations_list = []
    for tid in _tx.list_translations():
        meta = _tx.translation_meta(tid) or {}
        translations_list.append(
            {
                "id": tid,
                "short_title": meta.get("short_title", tid.upper()),
                "title": meta.get("title", tid),
                "license": meta.get("license", ""),
            }
        )
    # Phase ν.2.7-B — popup language registry + canonical book order.
    # Per CLAUDE_PROJECT_RULES.md §6.1, any per-book UI must list books
    # in books.yaml order (Genesis → Revelation → Apocrypha → Ethiopian
    # tail). The UI reads the order from this payload — never sorts on
    # its own — so the canonical-order rule has one source of truth.
    from scripts.build_edition import (
        POPUP_LANGUAGES,
        ALL_POPUP_LANGUAGES,
        decode_per_book_languages,
        decode_per_book_tokens,
        decode_per_chapter_tokens,
        decode_per_chapter_languages,
        decode_per_verse_languages,
    )
    from scripts.core import matrix as _matrix

    books_canonical = [{"code": b["code"], "title": b.get("title", b["code"])} for b in config.load_books()]
    # Every popup version is offered for every edition (one universal pool — full
    # customizability); ``has_data`` marks which actually have ingested text so the
    # UI can gray out the rest. Data-driven via popup_versions.bakes_now (aliases
    # resolve to their version id) so it auto-tracks the spine as each version bakes
    # — never a hardcoded list (which went stale across the WLC/LXX/NT/arabic/jps bakes).
    from scripts.core import popup_versions as _pv

    popup_languages_registry = [
        {
            "id": lid,
            "label": POPUP_LANGUAGES[lid]["label"],
            "has_data": _pv.bakes_now(_pv.resolve_version_id(lid) or lid),
        }
        for lid in ALL_POPUP_LANGUAGES
    ]
    # Canon membership per edition — lets the UI filter the books
    # list down to "only books in THIS edition" so a Tanakh edition
    # shows 39 rows and an Ethiopian shows 87.
    _mtx = _matrix.compute_matrix()
    # Canonical (books.yaml) order, not alphabetical (§6.1). The defensive tail
    # appends — alphabetically — any codes not present in books_canonical so no
    # edition book is ever silently dropped from the payload.
    _book_order = [b["code"] for b in books_canonical]
    edition_canon_books = {
        ed_id: [c for c in _book_order if c in books] + [c for c in sorted(books) if c not in _book_order]
        for ed_id, books in _mtx.edition_canon_books.items()
    }
    # §4.6 — the 25-design cover-template catalog (shared, not per-edition);
    # the /customize cover picker renders one clickable thumbnail per row.
    from scripts.core import covers as _covers

    return {
        "categories": [
            {
                "id": c["id"],
                "label": c.get("label", c["id"]),
                "symbol": c.get("symbol", "?"),
                "description": c.get("description", ""),
                "sort_order": c.get("sort_order", 999),
            }
            for c in sorted(cats, key=lambda x: x.get("sort_order", 999))
        ],
        "kinds": [
            {
                "code": k["code"],
                "category": k.get("category", "?"),
                "label": k.get("label", k["code"]),
                "symbol": k.get("symbol", ""),
                "description": k.get("description", ""),
                "phase": k.get("phase", "mvp"),
            }
            for k in kinds
        ],
        "editions": [
            {
                "id": e["id"],
                "title": e.get("title", e["id"]),
                "short_title": e.get("short_title", ""),
                # Ω.0 pivot: isbn field dropped. Front-end derives term-ref-ok
                # the URN (urn:yhwh:edition:<id>) from the id.
                "canon": e.get("canon", ""),
                "target_audience": e.get("target_audience", ""),
                "verse_popups": e.get("verse_popups", True),
                "verse_marker_glyph": e.get("verse_marker_glyph", ""),
                "popup_translation": e.get("popup_translation", ""),
                "popup_languages_default": list(e.get("popup_languages_default") or []),
                # Decoded to a JSON-friendly dict for the UI; on-disk
                # this is a list of "code=lang1,lang2" strings.
                "popup_languages_per_book": decode_per_book_languages(e.get("popup_languages_per_book")),
                # Phase ψ.8.1 — list of tradition ids enabled for this
                # edition. Empty list (or absent) → include all
                # traditions (no-op, pre-ψ.8 build behavior preserved
                # per §7.2). Filter against TRADITION_IDS defensively
                # via _filter_traditions_default(); see that helper for
                # the YAML round-trip caveat.
                "traditions_default": _filter_traditions_default(e.get("traditions_default")),
                # Phase ψ.8.4 — per-book tradition overrides, decoded
                # to a JSON-friendly dict for the UI; on-disk this is a
                # list of "code=t1,t2" strings.
                "traditions_per_book": _decode_traditions_per_book_for_api(e.get("traditions_per_book")),
                # ψ.19 — list of reading-plan ids enabled for this edition.
                # Empty / absent = no plans (build pipeline ToC integration
                # ships in ψ.19.1; opting in is currently a schema-only
                # flag).
                "enabled_reading_plans": list(e.get("enabled_reading_plans") or []),
                "theme": e.get("theme", "classic"),
                "title_page_style": e.get("title_page_style", "full-bleed"),
                # §4.6 — which of the 25 cover templates the publisher last
                # picked for this edition's main cover ("" = none picked yet).
                "cover_template": e.get("cover_template", ""),
                # §4.2 — original-language verse-popup layout (cards default / stack).
                "verse_popup_style": e.get("verse_popup_style", "cards"),
                # §4.4 — note/aside popup layout (chip default / pills).
                "note_popup_style": e.get("note_popup_style", "chip"),
                # §4.1 — inline marker style (numbers default; badge deferred).
                "marker_style": e.get("marker_style", "numbers"),
                # Torrey merge — which topical authority feeds the back-of-book index.
                "topical_index_source": e.get("topical_index_source", "both"),
                "notes": e.get("notes", ""),
                "description": e.get("description", ""),
                "dedication": e.get("dedication", ""),
                # ψ.37-D — year ceiling for time-traveling commentary.
                # None (or absent) = no filter; int = drop notes whose
                # source's circa-year > this.
                "time_filter_ceiling": e.get("time_filter_ceiling"),
                # ρ.3 Phase C1 — per-book/chapter/verse hierarchical
                # customization fields decoded to JSON-friendly dicts for
                # the UI.  On-disk format is list[str] ("gen=xref,comm");
                # decoders mirror the per-book-languages pattern.
                "note_families_on_per_book": decode_per_book_tokens(e.get("note_families_on_per_book")),
                "note_families_off_per_book": decode_per_book_tokens(e.get("note_families_off_per_book")),
                "note_families_on_per_chapter": decode_per_chapter_tokens(e.get("note_families_on_per_chapter")),
                "note_families_off_per_chapter": decode_per_chapter_tokens(e.get("note_families_off_per_chapter")),
                "popup_languages_per_chapter": decode_per_chapter_languages(e.get("popup_languages_per_chapter")),
                "popup_languages_per_verse": decode_per_verse_languages(e.get("popup_languages_per_verse")),
            }
            for e in editions
        ],
        "themes": themes,
        "translations": translations_list,
        "popup_languages": popup_languages_registry,
        # Phase ψ.8.1 — traditions registry for the customize UI. The
        # ψ.8.3 Traditions card iterates this list (in this exact
        # order — the canonical popup-stack order from
        # scripts/core/traditions.py) to render its checkboxes.
        # Single source of truth; UI never hard-codes the set.
        "traditions": [{"id": tid, "label": label} for tid, label in _traditions_canonical_for_api()],
        "books_canonical": books_canonical,
        "edition_canon_books": edition_canon_books,
        "cover_templates": _covers.cover_template_catalog(),
        # ψ.19 — registry of every reading plan available on disk.
        # The /customize Reading-plans card iterates this to render
        # toggle checkboxes; each edition's `enabled_reading_plans`
        # selects from this list.
        "reading_plans": [
            {
                "id": s["id"],
                "label": s["label"],
                "description": s["description"],
                "entry_count": s["entry_count"],
            }
            for s in _reading_plans_summary_for_api()
        ],
    }


def _reading_plans_summary_for_api() -> list[dict]:
    """Indirection for tests — same shape as api_reading_plans_list's
    `plans` field. Tests can monkeypatch this if they need to."""
    from scripts.core.reading_plans import list_plans, plan_summary

    return [plan_summary(p) for p in list_plans()]


def _traditions_canonical_for_api() -> tuple[tuple[str, str], ...]:
    """Indirection for tests — exposes CANONICAL_TRADITIONS as a tuple
    of (id, label) pairs in canonical order. Tests can monkeypatch
    this without touching the underlying constant."""
    from scripts.core.traditions import CANONICAL_TRADITIONS

    return CANONICAL_TRADITIONS


def _decode_traditions_per_book_for_api(raw) -> dict[str, list[str]]:
    """Phase ψ.8.4 — decode the on-disk ``traditions_per_book`` list-of-
    strings into a JSON-friendly ``{book_code: [tradition_ids]}`` dict.

    Same defensive policy as ``_filter_traditions_default``: unknown
    tradition ids are silently dropped from the per-book lists so the
    UI never sees junk; the validator catches the typo on next save."""
    from scripts.build_edition import decode_per_book_traditions
    from scripts.core.traditions import TRADITION_IDS

    decoded = decode_per_book_traditions(raw)
    return {
        code: [t for t in traditions if isinstance(t, str) and t in TRADITION_IDS]
        for code, traditions in decoded.items()
    }


def _filter_traditions_default(raw) -> list[str]:
    """Return ``raw`` as a list of valid tradition ids, dropping anything
    that isn't a known id.

    Defensive: the project's tiny YAML parser writes ``traditions_default:
    []`` for an explicit-empty list and re-reads that as the literal
    two-char list ``['[', ']']``. We filter that junk out here so the
    API surface stays clean. Also covers the case where editions.yaml
    is hand-edited with a typo'd tradition value — the bad entry just
    doesn't surface in the customize data; the validator catches it
    on the next save."""
    from scripts.core.traditions import TRADITION_IDS

    if not raw:
        return []
    return [t for t in raw if isinstance(t, str) and t in TRADITION_IDS]


def _load_themes() -> list[dict]:
    """Read content/themes.yaml — registry of available CSS themes."""
    path = REPO / "content" / "themes.yaml"
    if not path.is_file():
        return [{"id": "classic", "name": "Classic", "description": ""}]
    import yaml

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("themes", []) or []


def api_disabled_notes_for_edition(edition_id: str) -> dict:
    """Return the disabled-note-ID set for one edition. Used by /sources UI
    to show which notes are currently turned off for an edition."""
    eds = config.editions_by_id()
    if edition_id not in eds:
        return {"error": f"unknown edition: {edition_id}"}
    return {
        "edition": edition_id,
        "disabled_note_ids": sorted(eds[edition_id].get("disabled_note_ids") or []),
    }


def api_build_my_bible(
    edition_id: str,
    book: str | None = None,
    chapter: int | None = None,
) -> dict:
    """ρ.3 Phase C2-1 — lazy 3-level read API for the /build-my-bible navigator.

    Compose existing endpoints; RULES §9 (pure function, no corpus re-walk).

    Levels:
    - Edition (book=None): edition overview + books_canonical filtered to
      canon, registries, overrides, resolved_bible.
    - Book (book set, chapter=None): book info + per-chapter list with
      has_notes + resolved state.
    - Chapter (book + chapter set): chapter info + per-verse list with
      notes (from api_sources_for_book filtered to chapter) + resolved state.

    Returns ``{"error": "...", "http": 404}`` for unknown edition or book.
    All returned structures are dicts / lists — never raises for expected
    errors (RULES §9 pure-fn + thin-route contract).
    """
    # ------------------------------------------------------------------ imports
    from scripts.build_edition import _resolve_popup_languages
    from scripts.core import matrix as matrix_mod
    from scripts.core import versification
    from scripts.web_sources import api_sources_for_book

    # ------------------------------------------------------------------ edition lookup
    eds_by_id = config.editions_by_id()
    if edition_id not in eds_by_id:
        return {"error": f"unknown edition: {edition_id}", "http": 404}
    edition = eds_by_id[edition_id]

    m = matrix_mod.compute_matrix()
    canon_set = m.edition_canon_books.get(edition_id, set())
    enabled_kinds_set = m.edition_enabled_kinds.get(edition_id, set())
    per_chapter_ed = m.per_chapter.get(edition_id, {})

    all_kinds = config.load_kinds()
    all_cats = config.load_categories()
    kinds_by_code = config.kinds_by_code()
    cats_by_id = config.categories_by_id()
    books_by_code = config.books_by_code()

    # canonical-ordered book list (books.yaml order)
    all_books_ordered = config.load_books()
    canon_books_ordered = [b for b in all_books_ordered if b["code"] in canon_set]

    # ------------------------------------------------------------------ LEVEL helpers

    def _symbols_for(bk: str, ch: int | None = None) -> dict[str, str]:
        """Return {cat_id: "on"|"off"} for the given (book[, chapter]) coordinate."""
        enabled = config.enabled_kind_codes_for(edition, all_kinds, bk, ch)
        result: dict[str, str] = {}
        for cat in all_cats:
            cat_id = cat["id"]
            any_on = any(k.get("code") in enabled and k.get("category") == cat_id for k in all_kinds)
            result[cat_id] = "on" if any_on else "off"
        return result

    def _popups_for(bk: str, ch: int | None = None, vs: int | None = None) -> list[str]:
        """Return sorted list of popup language ids for the given coordinate."""
        langs = _resolve_popup_languages(edition, bk, ch, vs)
        return sorted(langs)

    def _has_notes_for_chapter(bk: str, ch: int) -> bool:
        """Return True if the chapter has at least one enabled-kind note."""
        for kind, by_book in per_chapter_ed.items():
            if kind not in enabled_kinds_set:
                continue
            if by_book.get(bk, {}).get(ch, 0):
                return True
        return False

    # ------------------------------------------------------------------ EDITION level
    if book is None:
        # Use first canon book as the anchor for resolved_bible
        first_book = canon_books_ordered[0]["code"] if canon_books_ordered else ""

        # Registries (from api_customize_data shape but targeted slices)
        categories = [
            {
                "id": c["id"],
                "label": c.get("label", c["id"]),
                "symbol": c.get("symbol", "?"),
                "description": c.get("description", ""),
                "sort_order": c.get("sort_order", 999),
            }
            for c in sorted(all_cats, key=lambda x: x.get("sort_order", 999))
        ]
        kinds = [
            {
                "code": k["code"],
                "category": k.get("category", "?"),
                "label": k.get("label", k["code"]),
                "symbol": k.get("symbol", ""),
                "description": k.get("description", ""),
                "phase": k.get("phase", "mvp"),
            }
            for k in all_kinds
        ]
        from scripts.build_edition import POPUP_LANGUAGES, ALL_POPUP_LANGUAGES
        from scripts.core import popup_versions as _pv

        popup_languages = [
            {
                "id": lid,
                "label": POPUP_LANGUAGES[lid]["label"],
                "has_data": _pv.bakes_now(_pv.resolve_version_id(lid) or lid),
            }
            for lid in ALL_POPUP_LANGUAGES
        ]

        # Overrides — the 6 decoded per-coordinate fields + disabled/enabled note ids
        from scripts.build_edition import (
            decode_per_book_tokens,
            decode_per_chapter_tokens,
            decode_per_chapter_languages,
            decode_per_verse_languages,
            decode_per_book_languages,
        )

        overrides = {
            "note_families_on_per_book": decode_per_book_tokens(edition.get("note_families_on_per_book")),
            "note_families_off_per_book": decode_per_book_tokens(edition.get("note_families_off_per_book")),
            "note_families_on_per_chapter": decode_per_chapter_tokens(edition.get("note_families_on_per_chapter")),
            "note_families_off_per_chapter": decode_per_chapter_tokens(edition.get("note_families_off_per_chapter")),
            # C2-4 — book-level popup writes use absolute-replace on the full
            # per-book map, so the navigator needs the current decoded map
            # here (the per-chapter / per-verse maps were already exposed;
            # this fills the one gap). decode_per_book_languages is imported
            # in the block above. Read-API addition only — byte-neutral.
            "popup_languages_per_book": decode_per_book_languages(edition.get("popup_languages_per_book")),
            "popup_languages_per_chapter": decode_per_chapter_languages(edition.get("popup_languages_per_chapter")),
            "popup_languages_per_verse": decode_per_verse_languages(edition.get("popup_languages_per_verse")),
            "disabled_note_ids": sorted(edition.get("disabled_note_ids") or []),
            "enabled_note_ids": sorted(edition.get("enabled_note_ids") or []),
        }

        # resolved_bible — the EDITION DEFAULT (Bible level), NOT any book's
        # resolved state. The read-only Bible panel shows this, and the book
        # level uses it as the "inherits …" baseline, so it must reflect the
        # edition-wide default even when the first canon book carries per-book
        # overrides. Reuses the SSOT resolvers: enabled_kind_codes (symbols,
        # no book), and _resolve_popup_languages with a sentinel book code
        # (never a valid per-book key — the write validator requires the key's
        # book ∈ books_by_code) so it falls through to the default popup tier.
        edition_default_kinds = config.enabled_kind_codes(edition, all_kinds)
        default_symbols = {
            cat["id"]: (
                "on"
                if any(k.get("code") in edition_default_kinds and k.get("category") == cat["id"] for k in all_kinds)
                else "off"
            )
            for cat in all_cats
        }
        resolved_bible: dict[str, object] = {
            "symbols": default_symbols,
            "popups": sorted(_resolve_popup_languages(edition, "\x00edition-default")),
        }

        # books_canonical — ordered, filtered, with ch_count
        books_canonical_out = [
            {
                "code": b["code"],
                "title": b.get("title", b["code"]),
                "ch_count": int(books_by_code.get(b["code"], {}).get("ch_count") or 0),
            }
            for b in canon_books_ordered
        ]

        return {
            "edition": {
                "id": edition_id,
                "title": edition.get("title", edition_id),
                "short_title": edition.get("short_title", edition_id),
            },
            "books_canonical": books_canonical_out,
            "categories": categories,
            "kinds": kinds,
            "popup_languages": popup_languages,
            "overrides": overrides,
            "resolved_bible": resolved_bible,
        }

    # ------------------------------------------------------------------ BOOK level
    if chapter is None:
        # Validate book
        if book not in canon_set:
            # Could also be unknown book entirely
            if book not in books_by_code:
                return {"error": f"unknown book: {book}", "http": 404}
            return {"error": f"book {book!r} not in edition {edition_id!r} canon", "http": 404}

        book_def = books_by_code[book]
        ch_count = int(book_def.get("ch_count") or 0)

        chapters_out = []
        for ch_num in range(1, ch_count + 1):
            has_notes = _has_notes_for_chapter(book, ch_num)
            chapters_out.append(
                {
                    "num": ch_num,
                    "has_notes": has_notes,
                    "resolved": {
                        "symbols": _symbols_for(book, ch_num),
                        "popups": _popups_for(book, ch_num),
                    },
                }
            )

        return {
            "book": {
                "code": book,
                "title": book_def.get("title", book),
                "ch_count": ch_count,
            },
            "chapters": chapters_out,
        }

    # ------------------------------------------------------------------ CHAPTER level
    # Validate book
    if book not in books_by_code:
        return {"error": f"unknown book: {book}", "http": 404}
    if book not in canon_set:
        return {"error": f"book {book!r} not in edition {edition_id!r} canon", "http": 404}

    book_def = books_by_code[book]
    ch_count = int(book_def.get("ch_count") or 0)

    # Validate chapter
    if chapter < 1 or chapter > ch_count:
        return {"error": f"chapter {chapter} out of range for {book} (1–{ch_count})", "http": 404}

    try:
        verse_count = versification.canonical_count(book, chapter)
    except KeyError:
        return {"error": f"chapter {chapter} not in canonical skeleton for {book}", "http": 404}

    # Load notes for this book (lazy — api_sources_for_book loads from disk)
    book_notes_data = api_sources_for_book(book)
    all_notes = book_notes_data.get("notes", [])

    # Index notes by (chapter, verse)
    notes_by_verse: dict[int, list[dict]] = {}
    disabled_ids = set(edition.get("disabled_note_ids") or [])
    enabled_ids = set(edition.get("enabled_note_ids") or [])

    # ρ.3 Phase C2-5 — the FAMILY-resolved enabled-kind set for this (book,
    # chapter) coordinate, computed ONCE (the per-note checkbox needs each
    # note's RESOLVED ships state, not just the individual overrides). Read-API
    # addition only — byte-neutral (no build/resolver/epub change).
    chapter_enabled_kinds = config.enabled_kind_codes_for(edition, all_kinds, book, chapter)

    for n in all_notes:
        if n.get("chapter") != chapter:
            continue
        vs_num = n.get("verse", 0)
        kind_def = kinds_by_code.get(n.get("kind", ""), {})
        cat_def = cats_by_id.get(n.get("category", ""), {})
        note_id = n["note_id"]
        note_kind = n.get("kind", "")
        is_disabled = note_id in disabled_ids
        is_forced_on = note_id in enabled_ids
        kind_enabled = note_kind in chapter_enabled_kinds
        note_out = {
            "note_id": note_id,
            "kind": note_kind,
            "category": n.get("category", ""),
            "symbol": cat_def.get("symbol", kind_def.get("symbol", "?")),
            "title": (n.get("title") or n.get("anchor") or "")[:200],
            "disabled": is_disabled,
            "forced_on": is_forced_on,
            # FAMILY resolution at this coordinate (kind on/off ignoring the
            # per-note individual overrides).
            "kind_enabled": kind_enabled,
            # Effective build outcome (§3.4 precedence: enabled_note_ids →
            # disabled_note_ids → family). force-on wins absolutely.
            "ships": is_forced_on or (kind_enabled and not is_disabled),
        }
        if vs_num not in notes_by_verse:
            notes_by_verse[vs_num] = []
        notes_by_verse[vs_num].append(note_out)

    # Build verse list in canonical order
    verses_out = []
    for vs_num in range(1, verse_count + 1):
        verse_notes = notes_by_verse.get(vs_num, [])
        verses_out.append(
            {
                "vs": vs_num,
                "resolved": {
                    "symbols": _symbols_for(book, chapter),
                    "popups": _popups_for(book, chapter, vs_num),
                },
                "notes": verse_notes,
            }
        )

    return {
        "chapter": chapter,
        "verses": verses_out,
    }
