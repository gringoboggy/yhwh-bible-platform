#!/usr/bin/env python3
"""
web.py — Local web UI for editing the E-Bible note corpus.

Lightweight HTTP server (stdlib only — no Flask, no install) that exposes
content/notes/<code>.py as a browsable, editable list. Per-note edits go
through atomic_write + ensure_backup, so the UI is just a thin layer over
the same primitives the CLI uses.

Run:
    ebible web                       # default localhost:8765
    ebible web --port 9000
    ebible web --host 0.0.0.0        # bind LAN-wide (use carefully)

Then open http://localhost:8765/ in a browser.

Capabilities:
  * Browse books — counts per kind shown.
  * List + filter notes within a book (by kind, by quality status).
  * Edit one note at a time with live HTML preview + word-count budget
    feedback against the per-kind budget from note_quality.py.
  * Add new notes via the per-kind templates from new_note.py.
  * Delete a note (creates a .backup before mutating).
  * Per-edit feedback: opener detection, presentational-tag warnings,
    word-count vs kind budget.

Architecture:
  - JSON API at /api/* for all data operations.
  - Single-page HTML at / (no build step, vanilla JS, Tailwind via CDN).
  - File mutations always go through scripts.core.notes_io helpers.

Concurrency:
  - ThreadingHTTPServer; each request is independent.
  - File writes are atomic (rename) so partial-write corruption is impossible.
  - Last-write-wins for concurrent edits in different tabs.

This server intentionally binds to localhost by default so the corpus is
not exposed without conscious opt-in via --host.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import secrets
import sys
import threading
import time
import urllib.parse
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts.core import audit_log, config, html_utils, notes_io  # noqa: E402
from scripts.core.covers import UPLOAD_MAX_BYTES as COVERS_UPLOAD_MAX_BYTES  # noqa: E402  # ω.35-A.9

NOTES_DIR = REPO / "content" / "notes"
SCENARIOS_DIR = REPO / "content" / "scenarios"


# ============================================================
# Phase φ.1 — Derived-endpoint caching
# ============================================================
#
# Several read-only API endpoints (audit, edition-diff, publisher-data,
# covers) recompute from scratch on every request even though their
# inputs change only when files on disk change. We cache them keyed on
# (path, mtime_ns) signatures: same signature → same answer → reuse.
#
# This sits on top of the project's existing caching layers
# (notes_io._load_notes_cached, config.load_books/kinds/etc.,
# core.matrix.compute_matrix). Those already short-circuit per-file
# reads; this module short-circuits per-endpoint *aggregation*.
#
# Pattern mirrors notes_io._load_notes_cached: an inner @lru_cache
# function takes the signature as its first arg; the public endpoint
# computes the signature and calls the inner. Cache invalidation is
# automatic on file change — no manual cache_clear() needed.

import functools  # used by the lru_cache decorators below


def _files_signature(*paths) -> tuple:
    """Return a (path, mtime_ns) tuple for a set of paths.

    Missing files contribute (path, 0) so disappearance also
    invalidates derived caches. NOT lru_cached — must read fresh
    mtimes each call, otherwise an in-process write wouldn't be
    picked up by the derived-endpoint caches.

    ω.30 — collapsed a misleading decorator/rebinding pair: the
    function previously had `@lru_cache` plus a later `_files_
    signature = _files_signature_impl` rebinding to override it.
    The decorator was dead code (the rebinding made it unreachable).
    The rename + decorator removal here makes the call shape
    unambiguous: this function reads fresh mtimes every call.
    """
    sig = []
    for p in paths:
        path = Path(p)
        try:
            sig.append((str(path), path.stat().st_mtime_ns))
        except OSError:
            sig.append((str(path), 0))
    return tuple(sig)


def _notes_dir_signature() -> tuple:
    """Signature over every notes file in NOTES_DIR.

    Returns a tuple of (filename, mtime_ns) pairs sorted by name.
    Sorting matters — without it, tuple equality breaks on Linux's
    arbitrary readdir order.
    """
    if not NOTES_DIR.is_dir():
        return ()
    pairs = []
    for f in NOTES_DIR.iterdir():
        if f.suffix == ".py" and not f.name.startswith("_"):
            try:
                pairs.append((f.name, f.stat().st_mtime_ns))
            except OSError:
                pairs.append((f.name, 0))
    pairs.sort()
    return tuple(pairs)


# Cache buckets — keyed on the relevant on-disk signatures. Each
# wrapper is small; the heavy lifting stays in the public endpoint.
@functools.lru_cache(maxsize=4)
def _cached_attribution_audit(notes_sig, kinds_sig, cats_sig, books_sig):
    # Δ.3.1 (2026-05-11) — wire flipped to the indexed path.
    # `corpus_index.audit_attribution()` produces the same counts +
    # needs_attention list (Δ.3 equivalence pin confirms identity);
    # the file-walk reference at `_compute_attribution_audit_uncached`
    # is retained as the equivalence anchor and a fall-back. The
    # outer lru_cache(maxsize=4) keyed on file signatures stays —
    # it adds a second invalidation layer that catches kinds/
    # categories/books YAML mutations the inner corpus_index doesn't
    # track directly. The `by_kind` shape translation
    # (tuple-list → dict-list) preserves the frontend contract:
    # /audit consumers expect `[{"kind": k, "count": n}]`, not
    # `[(k, n)]` (which JSON-serializes to `[[k, n]]`).
    from scripts.core import corpus_index

    raw = corpus_index.audit_attribution()
    return {
        **raw,
        "by_kind": [{"kind": k, "count": n} for k, n in raw["by_kind"]],
    }


@functools.lru_cache(maxsize=16)
def _cached_edition_diff(a_id, b_id, eds_sig, kinds_sig, cats_sig, canons_sig, books_sig, notes_sig):
    return _compute_edition_diff_uncached(a_id, b_id)


@functools.lru_cache(maxsize=4)
def _cached_publisher_data(eds_sig):
    return _compute_publisher_data_uncached()


@functools.lru_cache(maxsize=4)
def _cached_covers(eds_sig, books_sig, notes_sig):
    # Note: cover image mtimes are NOT in the signature — image meta
    # is read at call time and lru_cache only memoizes the structural
    # data (paths, canon membership). Re-reading meta on each call
    # is cheap (header parse only) and reflects fresh disk state.
    return _compute_covers_uncached()


# Lazy import note_quality + new_note (they're scripts, not modules)
def _load_note_quality_helpers():
    import importlib.util

    spec = importlib.util.spec_from_file_location("_note_quality", REPO / "scripts" / "note_quality.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_new_note_helpers():
    import importlib.util

    spec = importlib.util.spec_from_file_location("_new_note", REPO / "scripts" / "new_note.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_note_quality = None
_new_note = None


def _nq():
    global _note_quality
    if _note_quality is None:
        _note_quality = _load_note_quality_helpers()
    return _note_quality


def _nn():
    global _new_note
    if _new_note is None:
        _new_note = _load_new_note_helpers()
    return _new_note


# ============================================================
# Notes serialisation — read + write content/notes/*.py
# ============================================================


def tuple_to_dict(tup) -> dict:
    """Convert an 8/9-field NOTES tuple to a plain dict for the API."""
    pad = list(tup) + [None] * (9 - len(tup))
    ch, v, suffix, anchor, kind, title, label, body, attribution = pad[:9]
    return {
        "ch": ch,
        "v": v,
        "suffix": suffix or "",
        "anchor": anchor or "",
        "kind": kind or "",
        "title": title or "",
        "label": label or "",
        "body": body or "",
        "attribution": attribution or {},
    }


def dict_to_tuple(d: dict) -> tuple:
    """Inverse: API JSON object → NOTES tuple."""
    return (
        int(d["ch"]),
        int(d["v"]),
        d.get("suffix", "") or "",
        d.get("anchor", "") or "",
        d["kind"],
        d.get("title", "") or "",
        d.get("label", "") or "",
        d["body"],
        d.get("attribution") or {},
    )


def write_book(book_code: str, notes: list[tuple]) -> None:
    """Serialise a list of NOTES tuples back to content/notes/<code>.py.
    Uses atomic_write + ensure_backup. Preserves the leading docstring
    of the existing file (if any)."""
    path = NOTES_DIR / f"{book_code}.py"
    notes_io.ensure_backup(path)

    # Try to preserve the original docstring/header
    header = ""
    if path.is_file():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant):
                ds = tree.body[0].value.value
                if isinstance(ds, str):
                    header = f'"""{ds}"""\n\n'
        except (SyntaxError, ValueError):
            pass
    if not header:
        header = f'"""Notes for book {book_code}."""\n\n'

    lines = [header, "NOTES = [\n"]
    for tup in notes:
        ch, v, suffix, anchor, kind, title, label, body, *rest = tup
        attribution = rest[0] if rest else {}
        lines.append(f"    (\n")
        lines.append(f"        {ch}, {v}, {suffix!r},\n")
        lines.append(f"        {anchor!r},\n")
        lines.append(f"        {kind!r},\n")
        lines.append(f"        {title!r},\n")
        lines.append(f"        {label!r},\n")
        lines.append(f"        {body!r},\n")
        lines.append(f"        {attribution!r},\n")
        lines.append(f"    ),\n")
    lines.append("]\n")
    notes_io.atomic_write(path, "".join(lines))
    notes_io.clear_load_notes_cache()  # force re-read on next API call


# ============================================================
# Quality feedback per note
# ============================================================


def quality_for(book_code: str, tup) -> dict:
    """Return per-note quality findings (empty dict if all-clear)."""
    nq = _nq()
    findings = list(nq.run_checks(book_code, [tup], 50, 200, per_kind=True))
    kind = tup[4] if len(tup) >= 5 else ""
    body = tup[7] if len(tup) >= 8 else ""
    wc = html_utils.word_count(body) if isinstance(body, str) else 0
    lo, hi = nq.budget_for(kind, 50, 200)
    return {
        "word_count": wc,
        "budget": [lo, hi],
        "in_budget": lo <= wc <= hi,
        "findings": [{"check": f[5], "detail": f[6]} for f in findings],
    }


# ============================================================
# JSON API handlers
# ============================================================


def api_books() -> dict:
    """List every book with note counts + per-kind histogram."""
    out = []
    for b in config.load_books():
        path = NOTES_DIR / f"{b['code']}.py"
        if not path.is_file():
            continue
        notes = notes_io.load_notes(path) or []
        kinds: dict[str, int] = {}
        for tup in notes:
            if isinstance(tup, tuple) and len(tup) >= 5:
                kinds[tup[4]] = kinds.get(tup[4], 0) + 1
        out.append(
            {
                "code": b["code"],
                "name": b.get("name", b["code"]),
                "bxx": b.get("bxx", ""),
                "strategy": b.get("strategy", ""),
                "ch_count": b.get("ch_count", 0),
                "note_count": len(notes),
                "kinds": kinds,
            }
        )
    return {"books": out}


def api_notes(book_code: str) -> dict:
    """Return all notes in one book as dicts (with index for editing)."""
    path = NOTES_DIR / f"{book_code}.py"
    if not path.is_file():
        return {"error": "book not found", "book": book_code}
    notes = notes_io.load_notes(path) or []
    items = []
    for i, tup in enumerate(notes):
        if not isinstance(tup, tuple) or len(tup) < 8:
            continue
        d = tuple_to_dict(tup)
        d["index"] = i
        d["quality"] = quality_for(book_code, tup)
        items.append(d)
    return {"book": book_code, "notes": items}


def api_kinds() -> dict:
    """Return the kind taxonomy + per-kind budgets."""
    nq = _nq()
    kinds = config.load_kinds()
    out = []
    for k in kinds:
        code = k["code"]
        lo, hi = nq.budget_for(code, 50, 200)
        out.append(
            {
                "code": code,
                "category": k.get("category", ""),
                "label": k.get("label", code),
                "phase": k.get("phase", ""),
                "description": k.get("description", ""),
                "budget": [lo, hi],
            }
        )
    return {"kinds": out}


def api_template(kind: str) -> dict:
    """Return the per-kind scaffold template for a fresh note."""
    label, body, attribution = _nn().template_for(kind)
    return {"label": label, "body": body, "attribution": attribution}


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


# ω.35-B.5 — editions cluster + 2 private helpers moved to
# scripts/api/editions.py. 8 audit-logged mutation handlers
# (api_save_edition, save_edition_meta, save_publisher_meta,
# clone_edition, create_edition_from_template, save_note_toggle,
# preview_edition_changes, apply_kind_to_all_editions) + the
# private helpers _patch_edition_kind_lists, _append_cloned_edition.
# Re-imported here so route-table lambdas + tests keep working.
# Helpers used by handlers (_patch_yaml_entry, _patch_yaml_list_field,
# _load_themes, _validate_cover_path, parse_note_id,
# html_ref_id_from_note_id, PUBLISHING_TEXT_LIMITS,
# PUBLISHING_LIST_FIELDS) STAY in web.py — editions.py lazy-imports
# them at call time (B.3a pattern).
from scripts.api.editions import (  # noqa: E402
    _append_cloned_edition,
    _patch_edition_kind_lists,
    api_apply_kind_to_all_editions,
    api_clone_edition,
    api_create_edition_from_template,
    api_preview_edition_changes,
    api_save_edition,
    api_save_edition_meta,
    api_save_note_toggle,
    api_save_publisher_meta,
)


def api_preview(
    edition_id: str,
    book_code: str,
    chapter,
    *,
    translation_id: str = "kjv",
) -> dict:
    """ψ.1.0 — Live one-chapter preview.

    Returns the §9 standard dict shape:
      {"status": "ok", "html": "<full standalone HTML>",
       "verse_count": int, "notes_shown": int, ...}
      {"status": "error", "code": "...", "http": 4xx, "message": "..."}

    Surfaced at GET /api/preview/<edition_id>/<book>/<chapter>
    (translation_id optional via ?translation=<id>; defaults to KJV).

    Composes scripts.core.preview.render_chapter_preview which
    composes (config + notes_io + translations + build_edition's
    enabled-kinds + tradition resolvers + theme CSS).
    """
    from scripts.core import preview

    return preview.render_chapter_preview(
        edition_id,
        book_code,
        chapter,
        translation_id=translation_id,
    )


def api_matrix() -> dict:
    """Return the symbol-toggle count grid as JSON. Read-only (μ.1)."""
    from scripts.core import matrix as matrix_mod

    m = matrix_mod.compute_matrix()
    cats = config.load_categories()
    kinds = config.load_kinds()
    editions = config.load_editions()
    # ψ.18.1: per-book chapter counts (from books.yaml's ch_count)
    # so the JS sidebar can render full-width chapter sparklines.
    book_ch_counts = {b["code"]: int(b.get("ch_count") or 0) for b in config.load_books()}
    return {
        "categories": [
            {
                "id": c["id"],
                "label": c.get("label", c["id"]),
                "symbol": c.get("symbol", "?"),
                "description": c.get("description", ""),
                "sort_order": c.get("sort_order", 999),
            }
            for c in cats
        ],
        "kinds": [
            {
                "code": k["code"],
                "category": k.get("category", "?"),
                "label": k.get("label", k["code"]),
            }
            for k in kinds
        ],
        "editions": [
            {
                "id": e["id"],
                "title": e.get("title", e["id"]),
                "short_title": e.get("short_title", e["id"]),
                "canon": e.get("canon"),
                "enabled_categories": e.get("enabled_categories") or [],
                "enabled_kinds": e.get("enabled_kinds") or [],
                "disabled_kinds": e.get("disabled_kinds") or [],
            }
            for e in editions
        ],
        "matrix": _api_matrix_per_edition(m, book_ch_counts),
    }


def _api_matrix_per_edition(m, book_ch_counts: dict[str, int]) -> dict:
    """ψ.35-B3 — build the per-edition slice of the api_matrix JSON
    response. Extracted into a helper for clarity now that the bound
    accessor calls per edition have made the comprehension less
    readable inline.

    The per-edition shape is the JSON contract the JS UI depends on
    (matrix sidebar, per-book sparkline, per-chapter drilldown).
    Pinned by ``TestPsi35B3ApiMatrixMigration``."""
    # ψ.35-B3 — was: `for ed_id in m.enabled` reading the raw
    # projection's keyset. Switched to `m.edition_canon_books` which
    # has the same keyset (both are populated from editions.yaml).
    # Per-edition values now derive from the accessor API where
    # possible; `per_book` and `per_chapter` still read raw (the
    # whole-edition nested-dict shape needs a dedicated accessor that
    # ψ.35-B3 deliberately defers — see CHANGELOG).
    out: dict = {}
    for ed_id in m.edition_canon_books:
        # ψ.35-B3 — was: `m.enabled[ed_id]` / `m.potential[ed_id]`.
        enabled_dict = m.enabled_kinds_dict(ed_id)
        potential_dict = m.potential_kinds_dict(ed_id)
        out[ed_id] = {
            "enabled": enabled_dict,
            "potential": potential_dict,
            "total_enabled": sum(enabled_dict.values()),
            "total_potential": sum(potential_dict.values()),
            "canon_books_count": len(m.edition_canon_books[ed_id]),
            "enabled_kinds_count": len(m.edition_enabled_kinds[ed_id]),
            "enabled_kinds_set": sorted(m.edition_enabled_kinds[ed_id]),
            # ψ.18: per-kind, per-book counts (potential scope — all
            # kinds in canon, regardless of enabled state). The JS
            # sidebar sums across LOCAL_ENABLED for a live total, and
            # renders the per-book counts as sparklines.
            # ψ.35-B4 — was: `m.per_book.get(ed_id, {})`. The new
            # `per_book_kinds_dict` accessor derives the same shape
            # from the canonical per_chapter store; once ψ.35-Final
            # ships, the `per_book` field on Matrix is removed and
            # only the accessor remains.
            "per_book": m.per_book_kinds_dict(ed_id),
            # ψ.18.1: per-kind, per-book, per-chapter counts — third
            # drilldown level on the totals sidebar. Same potential
            # scope as per_book; chapter keys ride out as JSON strings
            # (JavaScript object keys). `per_chapter` IS the canonical
            # store — stays as raw read across all of ψ.35.
            "per_chapter": m.per_chapter.get(ed_id, {}),
            # Canon book order (for sparkline column ordering)
            "canon_book_order": [b["code"] for b in config.load_books() if b["code"] in m.edition_canon_books[ed_id]],
            # ψ.18.1: per-book chapter counts so the chapter sparkline
            # knows the book's full width. Flat dict is fine — every
            # edition shares the same book set.
            "book_chapter_counts": {
                code: book_ch_counts[code] for code in m.edition_canon_books[ed_id] if code in book_ch_counts
            },
        }
    return out


def api_matrix_for_edition(edition_id: str) -> dict:
    """Phase ψ.36-A — per-edition matrix slice (the lazy-load endpoint).

    Same per-edition payload as ``api_matrix()['matrix'][edition_id]``
    plus the categories + kinds + this-one-edition metadata so the
    client can render a standalone view without a second
    ``/api/matrix`` round-trip. Targets the 200K-note ceiling lift
    framing of AUDIT_2026-05-11: instead of returning the whole
    matrix on every render, fetch only what the user is viewing.

    Today's corpus (51K notes) doesn't strictly need this — the
    full ``/api/matrix`` response is ~2 MB and renders fine — but
    the endpoint is a foundation the JS UI can adopt incrementally
    as corpus growth justifies it. Existing /api/matrix consumers
    are unaffected.

    Returns:
        {
            "edition": {id, title, short_title, canon, enabled_categories,
                        enabled_kinds, disabled_kinds},
            "categories": [...],     # same shape as /api/matrix
            "kinds": [...],          # same shape as /api/matrix
            "matrix": {...},         # the per-edition slot
        }

    Returns ``{"error": "unknown edition"}`` (HTTP 404 via route
    adapter) when the edition_id isn't in editions.yaml.
    """
    from scripts.core import matrix as matrix_mod

    eds_by_id = config.editions_by_id()
    if edition_id not in eds_by_id:
        return {"error": f"unknown edition: {edition_id}", "http": 404}

    m = matrix_mod.compute_matrix()
    cats = config.load_categories()
    kinds = config.load_kinds()
    edition = eds_by_id[edition_id]
    book_ch_counts = {b["code"]: int(b.get("ch_count") or 0) for b in config.load_books()}
    # Reuse the helper that builds /api/matrix's per-edition slot.
    per_edition_full = _api_matrix_per_edition(m, book_ch_counts)
    slot = per_edition_full.get(edition_id, {})
    return {
        "edition": {
            "id": edition_id,
            "title": edition.get("title", edition_id),
            "short_title": edition.get("short_title", edition_id),
            "canon": edition.get("canon"),
            "enabled_categories": edition.get("enabled_categories") or [],
            "enabled_kinds": edition.get("enabled_kinds") or [],
            "disabled_kinds": edition.get("disabled_kinds") or [],
        },
        "categories": [
            {
                "id": c["id"],
                "label": c.get("label", c["id"]),
                "symbol": c.get("symbol", "?"),
                "description": c.get("description", ""),
                "sort_order": c.get("sort_order", 999),
            }
            for c in cats
        ],
        "kinds": [
            {
                "code": k["code"],
                "category": k.get("category", "?"),
                "label": k.get("label", k["code"]),
            }
            for k in kinds
        ],
        "matrix": slot,
    }


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


# ---------------------------------------------------------------------
# ω.16 / ω.35-B.1 — edition snapshot handlers, now in scripts/api/snapshots.py.
# Re-imported here so route-table lambdas and tests that reference
# `scripts.web.api_snapshot_*` keep working unchanged.
# ---------------------------------------------------------------------
from scripts.api.snapshots import (  # noqa: E402
    api_snapshot_create,
    api_snapshot_delete,
    api_snapshot_diff,
    api_snapshot_get,
    api_snapshot_list,
    api_snapshot_restore,
)


# ---------------------------------------------------------------------
# ψ.26 — bulk apply: enable/disable one kind across every edition
# ---------------------------------------------------------------------


@audit_log.audit_endpoint(action="save_note")
def api_save(book_code: str, payload: dict) -> dict:
    """Replace one note (by index) or insert a new note (index=null)."""
    path = NOTES_DIR / f"{book_code}.py"
    if not path.is_file():
        return {"error": "book not found", "book": book_code}
    notes = list(notes_io.load_notes(path) or [])
    new_tup = dict_to_tuple(payload)
    idx = payload.get("index")
    if idx is None or idx == "":
        notes.append(new_tup)
        new_index = len(notes) - 1
    else:
        idx = int(idx)
        if idx < 0 or idx >= len(notes):
            return {"error": "index out of range", "index": idx}
        notes[idx] = new_tup
        new_index = idx
    write_book(book_code, notes)
    return {"ok": True, "index": new_index, "quality": quality_for(book_code, new_tup)}


@audit_log.audit_endpoint(action="delete_note")
def api_delete(book_code: str, index: int) -> dict:
    """Delete a note. Backup is created automatically."""
    path = NOTES_DIR / f"{book_code}.py"
    if not path.is_file():
        return {"error": "book not found", "book": book_code}
    notes = list(notes_io.load_notes(path) or [])
    if index < 0 or index >= len(notes):
        return {"error": "index out of range", "index": index}
    removed = notes.pop(index)
    write_book(book_code, notes)
    return {"ok": True, "removed": tuple_to_dict(removed)}


# ============================================================
# Scenario API (Phase μ.2½ / ω.35-B.2) — named hypothetical edition
# profiles. Implementation moved to scripts/api/scenarios.py; the
# 5 handler names + internal helpers are re-imported below so the
# existing flat namespace stays the same.
# ============================================================
from scripts.api.scenarios import (  # noqa: E402
    _resolve_scenario_recipe,  # internal helper, used by some tests
    _scenario_path,  # internal helper, used by some tests
    _SCENARIO_NAME_RE,  # constant, used by some tests
    api_delete_scenario,
    api_export_scenario_yaml,
    api_get_scenario,
    api_import_scenario_yaml,
    api_list_scenarios,
    api_save_scenario,
)


# ============================================================
# Sources Navigator API (Phase μ.3) — browse notes by book/chapter
# ============================================================


def api_sources_index() -> dict:
    """Return a lightweight index of every book + its note count.

    Used to populate the left sidebar of the Sources Navigator. Cheap
    to compute (uses notes_io.load_notes which is mtime-cached).
    """
    books = config.load_books()
    out = []
    for b in books:
        path = NOTES_DIR / f"{b['code']}.py"
        notes = notes_io.load_notes(path) if path.is_file() else []
        out.append(
            {
                "code": b["code"],
                "title": b.get("title", b["code"]),
                "abbrev": b.get("abbrev", b["code"]),
                "section": b.get("section", ""),
                "ch_count": b.get("ch_count", 0),
                "note_count": len(notes or []),
                "sort_order": b.get("sort_order", 9999),
            }
        )
    return {"books": out}


def api_sources_for_book(book_code: str) -> dict:
    """Return every note for one book in canonical (chapter, verse) order
    along with its source attribution. The core verification view.

    Note tuple shape (positional):
        (chapter, verse, suffix, anchor, kind, label, title, body, attribution)
    """
    try:
        book = config.get_book(book_code)
    except KeyError:
        return {"error": f"unknown book: {book_code}"}
    if not book:
        return {"error": f"unknown book: {book_code}"}
    path = NOTES_DIR / f"{book_code}.py"
    if not path.is_file():
        return {"book": book_code, "notes": []}

    raw = notes_io.load_notes(path) or []
    kinds_idx = config.kinds_by_code()
    cats_idx = config.categories_by_id()

    out = []
    for i, tup in enumerate(raw):
        if len(tup) < 9:
            continue
        ch, vs, suffix, anchor, kind, title, label, body, attribution = tup[:9]
        kind_def = kinds_idx.get(kind, {})
        cat_id = kind_def.get("category", "?")
        cat_def = cats_idx.get(cat_id, {})
        # ρ.1 stable note ID — used by the per-note disable feature
        note_id = note_id_from_tuple(book_code, tup)
        out.append(
            {
                "index": i,
                "note_id": note_id,
                "chapter": ch,
                "verse": vs,
                "suffix": suffix or "",
                "anchor": anchor or "",
                "kind": kind,
                "kind_label": kind_def.get("label", kind),
                "category": cat_id,
                "category_label": cat_def.get("label", cat_id),
                "category_symbol": cat_def.get("symbol", "?"),
                "label": label,
                "title": title,
                "body": body,
                "attribution": attribution or "",
            }
        )
    # Already in canonical order in NOTES list, but enforce defensively
    out.sort(key=lambda n: (n["chapter"], n["verse"], n["suffix"]))
    return {
        "book": book_code,
        "title": book.get("title", book_code),
        "ch_count": book.get("ch_count", 0),
        "notes": out,
    }


# ---------------------------------------------------------------------
# υ.3 — search across editions (used by the /sources console)
# ---------------------------------------------------------------------


def api_search_notes(
    query: str,
    *,
    edition_id: str | None = None,
    kind: str | None = None,
    book: str | None = None,
    limit: int = 100,
) -> dict:
    """Pure-function wrapper that returns matching notes for the
    given query, optionally filtered by edition / kind / book.

    Δ.2.1 (2026-05-11) — wire flipped from
    `scripts.core.note_search.search_notes` (file-walk) to
    `scripts.core.corpus_index.search` (indexed). The Δ.2
    equivalence pin (`test_search_equivalence_with_file_walk_for_real_corpus`)
    confirms identical hit counts + identical top-5 tuples
    across the real corpus; the indexed path serves the same
    dict shape directly (no `SearchHit.to_dict()` translation
    needed). Empirical: file-walk ~3s cold on 51K notes;
    indexed ≥3× faster (per Δ.2's perf pin) and reads from the
    warm sqlite served by the Δ.6 fingerprint cache.

    Returns:
        ``{"status": "ok", "query": str, "filters": {...},
           "total": int, "hits": [{...}, ...]}`` on success.
        ``{"status": "error", "code": ..., "http": 400, "message": ...}``
        on bad input.
    """
    from scripts.core import corpus_index

    q = (query or "").strip()
    if not q:
        return {
            "status": "ok",
            "query": "",
            "filters": {
                "edition_id": edition_id,
                "kind": kind,
                "book": book,
            },
            "total": 0,
            "hits": [],
        }
    if len(q) > 500:
        return {
            "status": "error",
            "code": "query_too_long",
            "http": 400,
            "message": "query must be ≤ 500 characters",
        }
    try:
        cap = int(limit)
    except (TypeError, ValueError):
        cap = 100
    cap = max(1, min(cap, 500))

    hits = corpus_index.search(
        q,
        edition_id=edition_id or None,
        kind=kind or None,
        book=book or None,
        limit=cap,
    )

    kinds_idx = config.kinds_by_code()
    cats_idx = config.categories_by_id()

    enriched = []
    for d in hits:
        kind_code = d.get("kind", "")
        kind_def = kinds_idx.get(kind_code, {})
        cat_id = kind_def.get("category", "?")
        cat_def = cats_idx.get(cat_id, {})
        d["kind_label"] = kind_def.get("label", kind_code)
        d["category"] = cat_id
        d["category_label"] = cat_def.get("label", cat_id)
        d["category_symbol"] = cat_def.get("symbol", "?")
        enriched.append(d)

    return {
        "status": "ok",
        "query": q,
        "filters": {
            "edition_id": edition_id,
            "kind": kind,
            "book": book,
        },
        "limit": cap,
        "total": len(enriched),
        "hits": enriched,
    }


# ---------------------------------------------------------------------
# υ.8 — verse-of-the-day JSON / RSS feed
# ---------------------------------------------------------------------


def api_verse_of_day(
    date_iso: str | None = None,
    *,
    edition_id: str | None = None,
) -> dict:
    """Pure-function wrapper around `scripts.core.verse_of_day`.
    Returns the JSON-friendly payload for /api/verse-of-day.json.

    Returns:
        ``{"status": "ok", ...verse...}`` on success.
        ``{"status": "error", "code": ..., "http": ..., "message": ...}``
        on bad inputs or empty corpus (defensive — corpus is always
        populated in production).
    """
    from scripts.core.verse_of_day import verse_of_day

    if edition_id and edition_id not in config.editions_by_id():
        return {
            "status": "error",
            "code": "unknown_edition",
            "http": 400,
            "message": f"unknown edition: {edition_id}",
        }
    payload = verse_of_day(date_iso, edition_id=edition_id or None)
    if payload is None:
        return {
            "status": "error",
            "code": "no_notes",
            "http": 503,
            "message": "no notes in corpus",
        }
    return {"status": "ok", **payload}


def api_verse_of_day_rss(
    *,
    days: int = 7,
    base_url: str = "",
    edition_id: str | None = None,
) -> tuple:
    """Return ``(xml_text, content_type)`` for /api/verse-of-day.rss.

    Always returns a string (never raises) — feed consumers should
    never see a 500 on a transient edge case.
    """
    from scripts.core.verse_of_day import rss_feed

    try:
        days_i = int(days)
    except (TypeError, ValueError):
        days_i = 7
    days_i = max(1, min(days_i, 60))
    xml = rss_feed(
        days=days_i,
        base_url=base_url or "",
        edition_id=(edition_id or None) if (edition_id and edition_id in config.editions_by_id()) else None,
    )
    return xml, "application/rss+xml; charset=utf-8"


def _safe_rss_base_url(proto_header: str, host_header: str) -> str:
    """ξ.16 SEC-003 — sanitize the (proto, host) pair into a base URL
    that's safe to interpolate into RSS link tags.

    Trust order:
      1. ``YHWH_PUBLIC_BASE_URL`` env var (operator-set; authoritative).
         Empty / unset means fall through.
      2. ``Host`` header IFF it matches a strict localhost allowlist
         (``localhost``, ``127.0.0.1``, ``[::1]``, optionally with a
         port). Anything else — including domains with embedded
         colons, backslash characters, scheme-like prefixes, or
         non-ASCII — is rejected.
      3. Hardcoded ``http://localhost``.

    The proto header is similarly clamped to ``http`` or ``https``;
    anything else falls back to ``http``.
    """
    import os
    import re

    configured = (os.environ.get("YHWH_PUBLIC_BASE_URL") or "").strip()
    if configured:
        # Operator opted in. Trust it but still strip any trailing slash.
        return configured.rstrip("/")

    # Proto: only "http" or "https" — anything else (`javascript`,
    # `data`, malformed) falls back to http.
    proto = (proto_header or "http").strip().lower()
    if proto not in ("http", "https"):
        proto = "http"

    # Host: strict allowlist. Match `localhost`, `127.0.0.1`, or
    # `[::1]`, optionally suffixed `:<port>` where port is digits.
    # Anything else → fallback.
    host = (host_header or "").strip()
    # Defensive: reject control chars, whitespace, and non-ASCII.
    if not host or any(ord(c) < 0x21 or ord(c) > 0x7E for c in host):
        return "http://localhost"
    # Allow `host[:port]`. Port must be 1-5 digits.
    pattern = re.compile(r"^(localhost|127\.0\.0\.1|\[::1\])(:\d{1,5})?$")
    if not pattern.match(host):
        return "http://localhost"
    return f"{proto}://{host}"


def api_sources_summary() -> dict:
    """Return a high-level summary of the sources/attributions across the
    whole corpus. Used by the Sources Navigator's overview panel."""
    books = config.load_books()
    total_notes = 0
    notes_with_attribution = 0
    by_kind: dict[str, int] = {}
    by_book_section: dict[str, int] = {}
    # Naive source-string frequency map (the attribution is free-form text)
    source_freq: dict[str, int] = {}

    for b in books:
        path = NOTES_DIR / f"{b['code']}.py"
        notes = notes_io.load_notes(path) if path.is_file() else []
        if not notes:
            continue
        section = b.get("section", "?")
        by_book_section[section] = by_book_section.get(section, 0) + len(notes)
        for tup in notes:
            if len(tup) < 9:
                continue
            total_notes += 1
            kind = tup[4]
            by_kind[kind] = by_kind.get(kind, 0) + 1
            attr = (tup[8] or "").strip()
            if attr:
                notes_with_attribution += 1
                # Tokenize on common separators to extract source names
                # (rough — a free-text field, but useful for an overview)
                for chunk in re.split(r"[;,]\s*", attr):
                    chunk = chunk.strip()
                    if chunk:
                        source_freq[chunk] = source_freq.get(chunk, 0) + 1

    # Top sources, sorted by frequency
    top_sources = sorted(source_freq.items(), key=lambda x: -x[1])[:30]
    return {
        "total_notes": total_notes,
        "notes_with_attribution": notes_with_attribution,
        "by_section": by_book_section,
        "by_kind": dict(sorted(by_kind.items(), key=lambda x: -x[1])[:20]),
        "top_attribution_strings": [{"source": s, "count": n} for s, n in top_sources],
    }


# ============================================================
# Sources Cache API (Phase υ.1 / ω.35-B.3b) — manage content/sources/
# files: the PD-source cache that prospect.py + detectors read from.
# Implementation moved to scripts/api/sources.py; the 5 handler names
# + the SOURCES_UPLOAD_MAX_BYTES constant + internal helpers are
# re-imported below so route-table lambdas (the multipart entry
# references SOURCES_UPLOAD_MAX_BYTES directly) and existing tests
# keep working.
# ============================================================
from scripts.api.sources import (  # noqa: E402
    _datetime_iso,
    _sources_cache_dir,
    api_sources_cache_clear,
    api_sources_cache_fetch,
    api_sources_cache_fetch_all,
    api_sources_cache_status,
    api_sources_cache_upload,
    SOURCES_UPLOAD_MAX_BYTES,
)

# ============================================================
# Export API (Phase σ.1 + σ.2 / ω.35-B.6) — buyer-facing build &
# download. Implementation moved to scripts/api/exports.py.
# Re-imports below preserve the flat namespace for route-table
# lambdas + tests that reference scripts.web.api_export_* /
# api_build_all_editions / api_download_export / EXPORTS_DIR.
# ============================================================
from scripts.api.exports import (  # noqa: E402
    EXPORTS_DIR,
    api_build_all_editions,
    api_download_export,
    api_export_build,
    api_export_preview,
)


# ============================================================
# Customization API (Phase ν.1) — edit symbols + labels for cats/kinds
# ============================================================


def _patch_yaml_entry(text: str, key_field: str, key_value: str, updates: dict[str, str]) -> str:
    """Targeted regex update of one entry in a YAML list-of-dicts.

    Generic helper used for BOTH categories.yaml (key_field='id') and
    kinds.yaml (key_field='code'). Finds the entry whose key_field
    matches key_value, then sets each field in `updates` to its new
    value within that entry's block — preserving everything else
    (comments, ordering, other fields).

    Block heuristic: an entry block starts at `  - <key_field>:` and
    ends just before the next `  - <key_field>:` or end of file.
    """
    block_re = re.compile(
        rf"(^  - {re.escape(key_field)}: {re.escape(key_value)}(?:\s|$).*?\n)"
        rf"(.*?)"
        rf"(?=^  - {re.escape(key_field)}:|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = block_re.search(text)
    if not m:
        raise ValueError(f"entry {key_field}={key_value!r} not found in YAML")
    head, body = m.group(1), m.group(2)

    new_body = body
    for field, new_val in updates.items():
        # Find existing `    <field>: ...` and replace its value
        field_re = re.compile(
            rf"^(    {re.escape(field)}:[ \t]*)(.*?)(\n)",
            re.MULTILINE,
        )
        # Decide quoting: leave bools/numbers/already-quoted strings alone,
        # otherwise wrap as a YAML double-quoted scalar for safety.
        # ψ.37-C: also leave "null" unquoted so it round-trips to None
        # via the project's YAML parser (which special-cases unquoted
        # `null` as None at scripts/core/config.py line 158).
        if (
            new_val in ("true", "false", "null")
            or (isinstance(new_val, str) and new_val.startswith('"'))
            or (isinstance(new_val, str) and new_val.isdigit())
        ):
            quoted = new_val
        elif new_val == "":
            quoted = '""'
        else:
            # Escape any embedded double-quotes
            esc = new_val.replace("\\", "\\\\").replace('"', '\\"')
            quoted = f'"{esc}"'
        if field_re.search(new_body):
            new_body = field_re.sub(
                lambda mm: f"{mm.group(1)}{quoted}{mm.group(3)}",
                new_body,
                count=1,
            )
        else:
            # Insert at the head of the body (after the key line)
            new_body = f"    {field}: {quoted}\n" + new_body

    return text[: m.start()] + head + new_body + text[m.end() :]


# ω.35-B.4 — api_save_category + api_save_kind handlers moved to
# scripts/api/customize.py. Re-imported here so route-table
# lambdas (_PUT_ROUTES entries reference these by flat name) and
# tests that import `scripts.web.api_save_*` keep working.
# The `_patch_yaml_entry` helper above stays in web.py because
# api_save_edition_meta + api_save_publisher_meta also use it
# (both still inline below until ω.35-B.5). customize.py
# lazy-imports the helper at call time.
from scripts.api.customize import (  # noqa: E402
    api_save_category,
    api_save_kind,
)


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
    )
    from scripts.core import matrix as _matrix

    books_canonical = [{"code": b["code"], "title": b.get("title", b["code"])} for b in config.load_books()]
    popup_languages_registry = [
        {"id": lid, "label": POPUP_LANGUAGES[lid]["label"], "has_data": lid in {"english", "hebrew", "greek"}}
        for lid in ALL_POPUP_LANGUAGES
    ]
    # Canon membership per edition — lets the UI filter the books
    # list down to "only books in THIS edition" so a Tanakh edition
    # shows 39 rows and an Ethiopian shows 87.
    _mtx = _matrix.compute_matrix()
    edition_canon_books = {ed_id: sorted(books) for ed_id, books in _mtx.edition_canon_books.items()}
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
                "isbn": e.get("isbn", ""),
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
                "notes": e.get("notes", ""),
                # ψ.37-D — year ceiling for time-traveling commentary.
                # None (or absent) = no filter; int = drop notes whose
                # source's circa-year > this.
                "time_filter_ceiling": e.get("time_filter_ceiling"),
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


def _validate_cover_path(path) -> str:
    """Return an error message if ``path`` is unsafe / malformed, else ''.

    Covers live under content/. We forbid:
      - non-string or oversized values
      - absolute paths (escape from content/)
      - parent-traversal segments (``..``)
      - hidden files (``.something``) — keeps the storage area clean
      - extensions outside our supported set

    Empty string is allowed and means "no cover set". Validation
    runs on every save BEFORE any disk write, so a bad payload
    cannot land in editions.yaml.
    """
    if path is None:
        return ""  # treated as empty
    if not isinstance(path, str):
        return "cover path must be a string"
    s = path.strip()
    if not s:
        return ""  # empty == "no cover", allowed
    if len(s) > 500:
        return "cover path too long (max 500 chars)"
    # Normalize separators for the safety checks; we accept either
    # but store as posix-style in editions.yaml.
    norm = s.replace("\\", "/")
    if norm.startswith("/"):
        return f"cover path must be relative to content/, not absolute: {s!r}"
    parts = [p for p in norm.split("/") if p]
    if any(p == ".." for p in parts):
        return f"cover path may not contain '..': {s!r}"
    if any(p.startswith(".") for p in parts):
        return f"cover path may not contain hidden segments: {s!r}"
    # Extension check — keep the door open for file types we accept;
    # we don't validate the FILE here (it may not exist yet), only the
    # path string. π.4-B's upload endpoint validates the actual bytes.
    allowed_ext = {".jpg", ".jpeg", ".png", ".webp"}
    suffix = norm.rsplit(".", 1)
    if len(suffix) != 2 or "." + suffix[1].lower() not in allowed_ext:
        return f"cover path must end in an image extension ({', '.join(sorted(allowed_ext))}): {s!r}"
    return ""


def api_covers() -> dict:
    """Phase π.4-A — per-edition cover status feed. Cached on the
    structural inputs (editions, books, notes); image metadata is
    re-read each call so newly-uploaded covers reflect immediately."""
    return _cached_covers(
        _files_signature(REPO / "content" / "editions.yaml"),
        _files_signature(REPO / "content" / "books.yaml"),
        _notes_dir_signature(),
    )


# ============================================================
# Phase ψ.2 / ω.35-B.7 — Pre-flight checklist
# ============================================================
# Three handlers (api_preflight, _cached_preflight,
# _compute_preflight_uncached) moved to scripts/api/preflight.py.
# Re-imports below preserve scripts.web.api_preflight (route table)
# and scripts.web._cached_preflight / _compute_preflight_uncached
# (test-side cache-clear + monkeypatch sites).
from scripts.api.preflight import (  # noqa: E402
    _cached_preflight,
    _compute_preflight_uncached,
    api_preflight,
)


# ω.35-B.7 — multipart/form-data helpers moved to
# scripts/api/multipart.py. Re-imports preserve
# scripts.web._parse_multipart / _extract_boundary for callers
# that still lazy-import from web (legacy api/covers.py +
# api/sources.py paths will be updated in the same ship).
from scripts.api.multipart import _extract_boundary, _parse_multipart  # noqa: E402


def _save_cover_bytes(data: bytes, edition_id: str, book_code: str | None) -> dict:
    """Internal helper: validate + write + update editions.yaml.

    Returns a dict suitable for direct JSON response. Either
    ``{"ok": True, "path": "...", "meta": {...}}`` on success or
    ``{"error": "..."}`` on any failure. Disk is never mutated on
    failure.
    """
    from scripts.core import covers as _covers

    ok, err, meta = _covers.validate_upload_image(data)
    if not ok:
        return {"error": err}

    eds = config.editions_by_id()
    if edition_id not in eds:
        return {"error": f"unknown edition: {edition_id}"}
    if book_code is not None:
        if book_code not in config.books_by_code():
            return {"error": f"unknown book code: {book_code}"}

    # Compute the storage path. We use the canonical helpers so the
    # naming is consistent with any future migration tool.
    if book_code is None:
        rel_path = _covers.storage_path_for_main(edition_id, meta["format"])
    else:
        rel_path = _covers.storage_path_for_book(edition_id, book_code, meta["format"])
    abs_path = REPO / "content" / rel_path

    # Back up any existing file before overwrite. ensure_backup is a
    # no-op when the file doesn't exist — first-upload case.
    if abs_path.exists():
        notes_io.ensure_backup(abs_path)

    # Write the file atomically. atomic_write_bytes creates parent
    # dirs as needed.
    try:
        notes_io.atomic_write_bytes(abs_path, data)
    except OSError as e:
        return {"error": f"failed to write cover: {e}"}

    # Update editions.yaml — for main, set cover_image; for book,
    # update the book_covers entry. Reuse api_save_edition_meta so
    # validation + caching invalidation flow through one path.
    if book_code is None:
        save_payload = {"cover_image": rel_path}
    else:
        # Read existing per-book covers, modify, write back.
        edition_now = eds[edition_id]
        per_book = _covers.decode_book_covers(edition_now.get("book_covers"))
        per_book[book_code] = rel_path
        save_payload = {"book_covers": per_book}

    save_result = api_save_edition_meta(edition_id, save_payload)
    if not save_result.get("ok"):
        # Roll back the file we just wrote — keeps disk + yaml in sync
        try:
            abs_path.unlink()
        except OSError:
            pass
        return {"error": f"yaml save failed: {save_result.get('error')}"}

    return {
        "ok": True,
        "edition_id": edition_id,
        "book_code": book_code,
        "path": rel_path,
        "meta": meta,
    }


# ω.35-B.3a — cover-mutation handlers moved to scripts/api/covers.py.
# Re-imported here so route-table lambdas (_MULTIPART_ROUTES,
# _DELETE_ROUTES) and tests that reference `scripts.web.api_X` keep
# working unchanged.
from scripts.api.covers import (  # noqa: E402
    api_delete_cover_book,
    api_delete_cover_main,
    api_upload_cover_book,
    api_upload_cover_main,
)


def _compute_covers_uncached() -> dict:
    """Return per-edition cover status for the publisher console
    (Phase π.4-A read API).

    For each edition, the response includes:
      - main_cover  → path + image metadata (or None if missing)
      - book_covers → list of slot records, ONE PER BOOK IN THE
                      EDITION'S CANON, in canonical Book/Chapter
                      order (Rule §6.1). Books outside the canon
                      do NOT appear — Tanakh shows 39 slots,
                      Ethiopian shows 87. Slots without an assigned
                      cover have ``meta: None``.

    The canon ordering comes from books.yaml (the single source of
    truth) intersected with each edition's canon book set from the
    matrix module. The same shape powers the future /covers UI in
    π.4-B.
    """
    from scripts.core import covers as _covers
    from scripts.core import matrix as _matrix

    editions = config.load_editions()
    books_in_order = config.load_books()
    book_rank = {b["code"]: i for i, b in enumerate(books_in_order)}
    books_idx = {b["code"]: b for b in books_in_order}

    mtx = _matrix.compute_matrix()
    edition_canons = mtx.edition_canon_books

    records = []
    for ed in editions:
        canon_set = edition_canons.get(ed["id"], set())
        # Sort by canonical position (NOT alphabetical, NOT insertion).
        canon_books = sorted(canon_set, key=lambda c: book_rank.get(c, 1_000_000))
        records.append(
            _covers.cover_record_for_edition(
                ed,
                canon_books,
                books_idx,
            )
        )
    return {"editions": records}


# ============================================================
# Attribution Audit API (Phase ξ.4) — quality control on sources
# ============================================================


_THIN_ATTR_PATTERNS = (
    re.compile(r"^see\s", re.I),
    re.compile(r"^cf\.?\s", re.I),
    re.compile(r"^ibid", re.I),
    re.compile(r"^author$", re.I),
)


def _classify_attribution(attr: str) -> str:
    """Bucket an attribution string into one of:
    'missing'  — empty/whitespace, no attribution at all
    'thin'     — present but suspiciously short or vague
    'user'     — user-original / user-paraphrase (legitimate but flag)
    'sourced'  — references a real outside source (best case)
    """
    s = (attr or "").strip()
    if not s:
        return "missing"
    if any(p.match(s) for p in _THIN_ATTR_PATTERNS):
        return "thin"
    if len(s) < 12:
        return "thin"
    s_low = s.lower()
    if s_low.startswith("user original") or s_low.startswith("user paraphrase"):
        return "user"
    return "sourced"


# Phase ψ.3 — corpus progress widget. Tunable goal in one place; the
# /api/corpus-progress endpoint returns the structured payload that
# the every-console widget renders. Driven off the existing
# attribution-audit total (which already counts every note across
# every per-book file), so no new computation is introduced.
# Phase ω.0.6 — UI defense prelude. Four tiers of frontend
# robustness, mirroring the backend §15 chain-of-command. Injected
# into every console's <body> close so it runs once after page
# load. Order of definition is intentional: Tier 4 (global error
# backstop) installs first so it can catch any failures from
# Tier 2 / 3 themselves; Tier 2 (safeFetch) and Tier 3 (safe$/$$)
# are available to console-specific code that imports the page.
#
# Why a single shared constant: all 10 consoles need identical
# defensive scaffolding. Inlining the same ~80 lines into each
# template would drift; one constant + bulk-inject = one source
# of truth. Same pattern as the corpus-progress widget (ψ.3).
UI_DEFENSE_PRELUDE = r"""
<!-- ω.0.6 — UI defense prelude — START -->
<!-- Re-injecting / refreshing this block uses
     scripts/bulk_inject.py replace --open-marker "ω.0.6 — UI defense prelude — START"
     ...                          --close-marker "ω.0.6 — UI defense prelude — END"
     The markers are stable contracts; do not change without a coordinated migration. -->
<script>
(function () {
  'use strict';

  // -------------------------------------------------------------------
  // Tier 4 — Global error backstop. Catches anything that escapes
  // the other tiers (null-pointer accesses, unhandled rejections,
  // syntax errors in inline scripts) and shows a soft red banner
  // instead of leaving the page frozen.
  // -------------------------------------------------------------------

  function ensureErrorBanner() {
    var banner = document.getElementById('ebible-error-banner');
    if (banner) return banner;
    banner = document.createElement('div');
    banner.id = 'ebible-error-banner';
    banner.setAttribute('role', 'alert');
    banner.setAttribute('aria-live', 'polite');
    banner.style.cssText =
      'position:fixed;top:0;left:0;right:0;z-index:9999;' +
      'background:#dc2626;color:#fff;padding:8px 16px;font-size:13px;' +
      'font-family:system-ui,sans-serif;display:none;' +
      'box-shadow:0 2px 4px rgba(0,0,0,0.1)';
    banner.innerHTML =
      '<div style="max-width:72rem;margin:0 auto;display:flex;' +
      'align-items:center;justify-content:space-between;gap:12px">' +
      '<span class="ebible-error-text" style="flex:1;min-width:0;' +
      'overflow:hidden;text-overflow:ellipsis;white-space:nowrap"></span>' +
      '<button type="button" class="ebible-error-dismiss" ' +
      'style="background:none;border:1px solid rgba(255,255,255,0.4);' +
      'color:#fff;padding:2px 10px;border-radius:4px;cursor:pointer;' +
      'font-size:12px">Dismiss</button></div>';
    if (document.body) {
      document.body.appendChild(banner);
    } else {
      document.addEventListener('DOMContentLoaded', function () {
        document.body.appendChild(banner);
      });
    }
    banner.querySelector('.ebible-error-dismiss')
      .addEventListener('click', function () { banner.style.display = 'none'; });
    return banner;
  }

  function showErrorBanner(message) {
    try {
      var banner = ensureErrorBanner();
      var text = banner.querySelector('.ebible-error-text');
      if (text) text.textContent = message;
      banner.style.display = 'block';
    } catch (e) {
      // If even the banner fails, log to console as last resort
      try { console.error('[ebible] error banner failed:', e, message); }
      catch (_) {}
    }
  }

  // Install global error handlers
  window.addEventListener('error', function (ev) {
    var msg = (ev && ev.message) ? ev.message : 'Script error';
    // Filter out "Script error." with no info — usually cross-origin
    // loaded resources, nothing actionable for us
    if (msg === 'Script error.') return;
    showErrorBanner('Something went wrong: ' + msg);
    try { console.error('[ebible global error]', ev.error || msg); }
    catch (_) {}
  });
  window.addEventListener('unhandledrejection', function (ev) {
    var reason = ev && ev.reason;
    var msg = (reason && reason.message) ? reason.message : String(reason);
    showErrorBanner('Background task failed: ' + msg);
    try { console.error('[ebible unhandled rejection]', reason); }
    catch (_) {}
  });

  // -------------------------------------------------------------------
  // Tier 2 — safeFetch wrapper. Standard helper for every API call.
  // Throws on non-OK status, parses JSON safely, surfaces failures
  // via the banner. Re-throws so callers can do feature-specific
  // handling on top.
  // -------------------------------------------------------------------

  async function safeFetch(url, opts) {
    opts = opts || {};
    let response;
    try {
      response = await fetch(url, opts);
    } catch (netErr) {
      // Network drop, DNS fail, fetch aborted, etc.
      const msg = (netErr && netErr.message) ? netErr.message : 'network error';
      showErrorBanner('Network error: ' + msg + ' (' + url + ')');
      throw netErr;
    }
    if (!response.ok) {
      let errMsg = response.status + ' ' + response.statusText;
      try {
        const text = await response.text();
        if (text) {
          try {
            const parsed = JSON.parse(text);
            if (parsed && parsed.error) errMsg = parsed.error;
          } catch (_) {
            // Not JSON; use text snippet
            errMsg = text.slice(0, 200);
          }
        }
      } catch (_) {}
      showErrorBanner('API ' + response.status + ': ' + errMsg);
      const err = new Error(errMsg);
      err.status = response.status;
      throw err;
    }
    // Parse response. If empty body, return null (DELETE often is).
    const text = await response.text();
    if (!text) return null;
    try {
      return JSON.parse(text);
    } catch (parseErr) {
      showErrorBanner('Server returned invalid JSON from ' + url);
      throw parseErr;
    }
  }

  // -------------------------------------------------------------------
  // Tier 3 — DOM null-safe helpers. querySelector / querySelectorAll
  // wrappers that don't throw on missing elements. Opt-in: existing
  // code keeps working; new code can adopt these.
  // -------------------------------------------------------------------

  function safe$(selector, parent) {
    try {
      return (parent || document).querySelector(selector);
    } catch (e) {
      // Invalid selector syntax → log and return null instead of crash
      try { console.warn('[safe$] invalid selector:', selector, e); }
      catch (_) {}
      return null;
    }
  }

  function safe$$(selector, parent) {
    try {
      return Array.from((parent || document).querySelectorAll(selector));
    } catch (e) {
      try { console.warn('[safe$$] invalid selector:', selector, e); }
      catch (_) {}
      return [];
    }
  }

  // -------------------------------------------------------------------
  // ω.0.7 — Shared escape helpers. Eleven separate definitions of
  // essentially the same HTML-escaping logic existed across the
  // consoles before this consolidation. New code should use
  // window.ebible.escapeHtml (or the bare alias). Existing call
  // sites can migrate incrementally.
  // -------------------------------------------------------------------

  var ESCAPE_HTML_MAP = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  };

  function escapeHtml(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/[&<>"']/g, function (c) {
      return ESCAPE_HTML_MAP[c] || c;
    });
  }

  // -------------------------------------------------------------------
  // Public surface — attach to window.ebible namespace
  // -------------------------------------------------------------------

  window.ebible = window.ebible || {};
  window.ebible.showErrorBanner = showErrorBanner;
  window.ebible.safeFetch = safeFetch;
  window.ebible.safe$ = safe$;
  window.ebible.safe$$ = safe$$;
  window.ebible.escapeHtml = escapeHtml;
  // Convenience aliases for less typing in inline scripts
  window.safeFetch = safeFetch;
  window.safe$ = safe$;
  window.safe$$ = safe$$;
  window.escapeHtml = escapeHtml;
})();
</script>
<!-- ω.0.6 — UI defense prelude — END -->
"""


# ω.0.8 — web.py split refactor: HTML constants moved to
# scripts/templates/<name>.py during the 2026-05-07 split.
# These imports preserve back-compat with existing
# `from scripts.web import <NAME>_HTML` callers.
from scripts.templates.apihelp import APIHELP_HTML
from scripts.templates.audit import AUDIT_HTML
from scripts.templates.audit_log import AUDIT_LOG_HTML
from scripts.templates.compare import COMPARE_HTML
from scripts.templates.covers import COVERS_HTML
from scripts.templates.customize import CUSTOMIZE_HTML
from scripts.templates.diff import DIFF_HTML
from scripts.templates.exec import EXEC_HTML
from scripts.templates.export import EXPORT_HTML
from scripts.templates.greek import GREEK_HTML
from scripts.templates.hebrew import HEBREW_HTML
from scripts.templates.index import INDEX_HTML
from scripts.templates.matrix import MATRIX_HTML
from scripts.templates.ops import OPS_HTML
from scripts.templates.preflight import PREFLIGHT_HTML
from scripts.templates.publisher import PUBLISHER_HTML
from scripts.templates.sources import SOURCES_HTML
from scripts.templates.wizard import WIZARD_HTML

# γ.1 / γ.2 — interlinear lookup APIs.
from scripts.api.greek import api_greek_lookup
from scripts.api.hebrew import api_hebrew_lookup

# ε.2 — /exec dashboard MVP.
from scripts.api.exec import api_exec_dashboard
from scripts.api.sales import (
    SALES_UPLOAD_MAX_BYTES,
    api_sales_import,
    api_sales_rollup,
)
from scripts.api.distribution import (
    api_distribution_list,
    api_distribution_mark,
    api_distribution_unmark,
)
from scripts.api.press_kit import (
    api_press_kit_get,
    api_press_kit_save,
    build_press_kit_zip,
)
from scripts.api.archive_org import (
    api_archive_org_status,
    api_archive_org_upload,
)
from scripts.api.auth import (
    api_auth_status,
    api_auth_totp_begin,
    api_auth_totp_confirm,
    api_auth_totp_disable,
)

CORPUS_TARGET = 35_000


# Phase ψ.4 — Translation comparison. Read-only API that aligns
# multiple translations of a single book+chapter side by side so
# the /compare console can render a verse-by-verse comparison
# table. Composes scripts.core.translations.get_chapter() for each
# selected translation; missing verses are surfaced as None values
# in the per-verse map so the UI can render an em-dash placeholder.
def api_compare(book: str, chapter: int, translations: list[str]) -> dict:
    """Return aligned verses across the requested translations
    for a single book+chapter.

    Returns:
        {
          "book": str,                      # canonical book code
          "chapter": int,
          "translations": [str, ...],       # echoed back in input order
          "missing_translations": [str, ...],  # requested but unknown
          "verses": [
            {"verse": int, "by_translation": {<id>: str | None, ...}},
            ...
          ],
          "verse_count": int,               # max verse number across
                                             # all selected translations
        }

    The verse list always covers every verse number from 1 through
    the maximum present in any of the selected translations — so
    if KJV has Gen 1 with 31 verses but a hypothetical other
    translation only has 30, the 31st row still renders with the
    other translation's value as None (em-dash in the UI).

    Unknown translation IDs are reported in `missing_translations`
    rather than silently dropped, so the UI can surface them.
    """
    from scripts.core.translations import (
        list_translations,
        has_translation,
        has_book,
        get_chapter,
    )

    book = (book or "").strip().lower()
    if not book:
        return {"error": "book code is required"}
    try:
        chapter_n = int(chapter)
    except (TypeError, ValueError):
        return {"error": f"chapter must be an integer; got {chapter!r}"}
    if chapter_n < 1:
        return {"error": f"chapter must be ≥ 1; got {chapter_n}"}

    # Filter known/unknown translations
    known_set = set(list_translations())
    known: list[str] = []
    missing: list[str] = []
    for t in translations or []:
        t = (t or "").strip().lower()
        if not t:
            continue
        if t in known_set:
            known.append(t)
        else:
            missing.append(t)

    if not known:
        return {
            "book": book,
            "chapter": chapter_n,
            "translations": [],
            "missing_translations": missing,
            "verses": [],
            "verse_count": 0,
        }

    # Fetch each translation's chapter once. get_chapter returns
    # a list of (chapter, verse, text) tuples for that chapter.
    # Build a per-translation map verse_number → text for O(1)
    # alignment.
    by_t: dict[str, dict[int, str]] = {}
    for t in known:
        if not has_book(t, book):
            by_t[t] = {}
            continue
        chapter_rows = get_chapter(t, book, chapter_n) or []
        by_t[t] = {row[0]: row[1] for row in chapter_rows}

    # Determine the verse range. Cover every verse number that
    # appears in ANY of the selected translations so we never
    # silently truncate.
    all_verse_nums = set()
    for t in known:
        all_verse_nums.update(by_t[t].keys())
    if not all_verse_nums:
        # All known translations were missing this book or chapter
        return {
            "book": book,
            "chapter": chapter_n,
            "translations": known,
            "missing_translations": missing,
            "verses": [],
            "verse_count": 0,
        }
    max_verse = max(all_verse_nums)

    verses: list[dict] = []
    for v in range(1, max_verse + 1):
        row = {
            "verse": v,
            "by_translation": {t: by_t[t].get(v) for t in known},
        }
        verses.append(row)

    return {
        "book": book,
        "chapter": chapter_n,
        "translations": known,
        "missing_translations": missing,
        "verses": verses,
        "verse_count": max_verse,
    }


# Phase ψ.5 — Sample-chapter HTML export. Self-contained HTML
# document showing verses + applicable notes for a chapter range,
# filtered by the edition's enabled-kinds. Lets publishers share
# preview material without committing to a full EPUB build.
# Composes existing primitives per Rule §9 ("compose, don't recompute"):
#   - config.editions_by_id() for edition validation
#   - build_edition.load_canons() for in-canon validation
#   - translations.get_chapter() for verses
#   - notes_io.load_notes() for per-book notes
#   - edition.enabled_kinds + disabled_kinds for the kind filter
def api_sample_html(
    edition_id: str,
    book: str,
    from_chapter: int,
    to_chapter: int,
    *,
    translation: str = "kjv",
) -> dict:
    """Return a self-contained sample HTML document.

    Returns a dict shaped:
        {"status": "ok", "html": str, "edition_id": str, "book": str,
         "from": int, "to": int, "verse_count": int, "note_count": int}
    or on error:
        {"status": "error", "code": "...", "message": "...", "http": int}

    The caller (route handler) decides whether to send 200 + HTML
    or the error code + JSON. Keeping the function pure (no Handler
    side effects) makes it directly testable.

    Errors surfaced:
        unknown_edition  -> 404
        out_of_canon     -> 404 (book exists but not in this edition)
        unknown_book     -> 404 (book code not recognized at all)
        invalid_range    -> 400 (from < 1, to < from, etc.)
    """
    from scripts.core import config, translations, notes_io
    from scripts.build_edition import load_canons

    # --- Edition validation ---
    eds = config.editions_by_id()
    edition = eds.get(edition_id)
    if not edition:
        return {
            "status": "error",
            "code": "unknown_edition",
            "http": 404,
            "message": f"No edition with id {edition_id!r}",
        }

    # --- Book validation (recognized?) ---
    book = (book or "").strip().lower()
    if not book:
        return {
            "status": "error",
            "code": "unknown_book",
            "http": 404,
            "message": "book code is required",
        }
    all_books = config.books_by_code()
    if book not in all_books:
        return {
            "status": "error",
            "code": "unknown_book",
            "http": 404,
            "message": f"Unknown book code {book!r}",
        }

    # --- Book-in-edition-canon check ---
    canons = load_canons()
    canon_id = edition.get("canon", "")
    canon_books = set((canons.get(canon_id) or {}).get("books") or [])
    if book not in canon_books:
        return {
            "status": "error",
            "code": "out_of_canon",
            "http": 404,
            "message": (f"Book {book!r} is not in the {canon_id!r} canon used by edition {edition_id!r}"),
        }

    # --- Chapter range validation ---
    try:
        f = int(from_chapter)
        t = int(to_chapter)
    except (TypeError, ValueError):
        return {
            "status": "error",
            "code": "invalid_range",
            "http": 400,
            "message": "from and to must be integers",
        }
    if f < 1 or t < f:
        return {
            "status": "error",
            "code": "invalid_range",
            "http": 400,
            "message": f"invalid range: from={f}, to={t}",
        }
    # Cap range size to keep the document reasonable; pitch decks
    # don't need 50-chapter samples
    MAX_RANGE = 10
    if (t - f + 1) > MAX_RANGE:
        return {
            "status": "error",
            "code": "invalid_range",
            "http": 400,
            "message": (f"range too large: requested {t - f + 1} chapters; max is {MAX_RANGE}"),
        }

    # --- Verses (compose translations.get_chapter) ---
    if not translations.has_translation(translation):
        return {
            "status": "error",
            "code": "invalid_range",
            "http": 400,
            "message": f"translation {translation!r} not available",
        }
    verses_by_chapter: dict[int, list[tuple]] = {}
    total_verses = 0
    for ch in range(f, t + 1):
        rows = translations.get_chapter(translation, book, ch) or []
        verses_by_chapter[ch] = rows
        total_verses += len(rows)

    # --- Notes (compose notes_io + edition kind filter) ---
    notes_path = REPO / "content" / "notes" / f"{book}.py"
    all_notes = notes_io.load_notes(notes_path) if notes_path.is_file() else []
    enabled_kinds = set(edition.get("enabled_kinds") or [])
    disabled_kinds = set(edition.get("disabled_kinds") or [])
    in_range = []
    for n in all_notes:
        if not n or len(n) < 8:
            continue
        ch = n[0]
        if ch < f or ch > t:
            continue
        kind = n[4]
        # Filter rule mirrors build_edition: a kind is included iff
        # (enabled_kinds is empty OR kind in enabled_kinds) AND
        # kind not in disabled_kinds.
        if enabled_kinds and kind not in enabled_kinds:
            continue
        if kind in disabled_kinds:
            continue
        in_range.append(n)

    # --- Render self-contained HTML ---
    html = _render_sample_html(
        edition=edition,
        book=book,
        all_books=all_books,
        from_chapter=f,
        to_chapter=t,
        verses_by_chapter=verses_by_chapter,
        notes=in_range,
        translation=translation,
    )

    return {
        "status": "ok",
        "html": html,
        "edition_id": edition_id,
        "book": book,
        "from": f,
        "to": t,
        "verse_count": total_verses,
        "note_count": len(in_range),
    }


def _render_sample_html(
    *,
    edition: dict,
    book: str,
    all_books: dict,
    from_chapter: int,
    to_chapter: int,
    verses_by_chapter: dict,
    notes: list,
    translation: str,
) -> str:
    """Render the self-contained sample HTML document.

    Pure presentation; no I/O. Inline CSS for portability so the
    document renders correctly when shared via email, Substack
    paste, etc., without needing external resources.
    """
    import html as _html

    book_meta = all_books.get(book) or {}
    book_title = book_meta.get("title") or book.upper()
    edition_title = edition.get("title") or edition.get("short_title") or edition.get("id")

    # Group notes by (chapter, verse) for inline rendering
    notes_by_anchor: dict[tuple[int, int], list] = {}
    for n in notes:
        notes_by_anchor.setdefault((n[0], n[1]), []).append(n)

    chapter_blocks = []
    for ch in range(from_chapter, to_chapter + 1):
        verse_rows = verses_by_chapter.get(ch) or []
        if not verse_rows:
            chapter_blocks.append(
                f'<section class="chapter"><h2>Chapter {ch}</h2>'
                f'<p class="empty">No verses available for this chapter '
                f"in {_html.escape(translation.upper())}.</p></section>"
            )
            continue
        verse_html_parts = []
        for v_num, v_text in verse_rows:
            v_notes = notes_by_anchor.get((ch, v_num)) or []
            note_blocks_html = ""
            if v_notes:
                items = []
                for n in v_notes:
                    # n shape: (chapter, verse, suffix, anchor, kind,
                    #           title, label, body_html, attribution?)
                    title = _html.escape(str(n[5] or "Note"))
                    body = str(n[7] or "")  # body is already HTML
                    kind = _html.escape(str(n[4] or ""))
                    items.append(
                        f'<li class="note"><span class="kind">{kind}</span> <strong>{title}.</strong> {body}</li>'
                    )
                note_blocks_html = f'<ul class="notes">{"".join(items)}</ul>'
            verse_html_parts.append(
                f'<p class="verse"><sup class="vn">{v_num}</sup> {_html.escape(v_text)}{note_blocks_html}</p>'
            )
        chapter_blocks.append(f'<section class="chapter"><h2>Chapter {ch}</h2>{"".join(verse_html_parts)}</section>')

    range_label = f"Chapter {from_chapter}" if from_chapter == to_chapter else f"Chapters {from_chapter}-{to_chapter}"
    style_block = """
  body {
    font-family: Georgia, "Times New Roman", serif;
    max-width: 42rem; margin: 2.5rem auto; padding: 0 1.5rem;
    color: #1f2937; line-height: 1.65;
  }
  header { border-bottom: 2px solid #cbd5e1; margin-bottom: 1.5rem;
           padding-bottom: 1rem; }
  header .edition { color: #475569; font-size: 0.875rem;
                    letter-spacing: 0.05em; text-transform: uppercase; }
  h1 { font-size: 1.75rem; margin: 0.25rem 0 0; }
  h1 .range { font-weight: normal; color: #64748b; }
  .meta { color: #64748b; font-size: 0.875rem; margin-top: 0.5rem; }
  .chapter { margin: 2.5rem 0; }
  .chapter h2 { font-size: 1.25rem; color: #475569;
                border-bottom: 1px solid #e2e8f0; padding-bottom: 0.25rem; }
  .verse { margin: 0.75rem 0; }
  .verse .vn { color: #94a3b8; font-size: 0.7rem; padding-right: 0.25rem;
               font-family: ui-monospace, SFMono-Regular, monospace; }
  .notes { margin: 0.5rem 0 1rem 0; padding-left: 1.25rem; font-size: 0.9rem;
           color: #334155; background: #f8fafc; border-left: 3px solid #cbd5e1;
           padding: 0.5rem 0 0.5rem 1.25rem; }
  .note { margin: 0.4rem 0; list-style: none; }
  .note .kind { display: inline-block; font-size: 0.65rem;
                text-transform: uppercase; padding: 0.1rem 0.4rem;
                background: #e2e8f0; color: #475569; border-radius: 3px;
                letter-spacing: 0.05em; margin-right: 0.4rem; }
  .empty { color: #94a3b8; font-style: italic; }
  footer { margin-top: 3rem; padding-top: 1rem;
           border-top: 1px solid #e2e8f0; color: #94a3b8;
           font-size: 0.75rem; text-align: center; }
"""
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        f"<title>{_html.escape(book_title)} - "
        f"{_html.escape(range_label)} - Sample</title>\n"
        f"<style>{style_block}</style>\n</head>\n<body>\n"
        "<header>\n"
        f'  <div class="edition">{_html.escape(edition_title or "")}</div>\n'
        f"  <h1>{_html.escape(book_title)} "
        f'<span class="range">- {_html.escape(range_label)}</span></h1>\n'
        f'  <p class="meta">Translation: {_html.escape(translation.upper())} '
        f"- Sample preview - {len(notes)} note(s) shown</p>\n"
        "</header>\n"
        f"{''.join(chapter_blocks)}\n"
        "<footer>\n"
        "  Sample generated from the E-Bible publishing platform.\n"
        "  This is a preview excerpt for evaluation.\n"
        "</footer>\n"
        "</body>\n</html>\n"
    )


# Phase ω.1 — Backup restore API. Surface the .backups/ snapshots
# that already exist (every atomic_write triggers ensure_backup);
# lets publishers undo destructive changes from the UI. Operational
# confidence is buyer-demo gold: "you can play with this without
# breaking anything." Path traversal is the main security concern —
# only files inside content/ are addressable.

# Backup filename pattern: <stem>.<TIMESTAMP>.<suffix>.bak
# where TIMESTAMP is the YYYYMMDDTHHMMSSZ string from ensure_backup.
_BACKUP_FILENAME_RE = re.compile(r"^(?P<stem>.+?)\.(?P<ts>\d{8}T\d{6}Z)(?P<suffix>\..+)?\.bak$")


def _resolve_content_path(rel_path: str) -> tuple[Path | None, str | None]:
    """Resolve a user-supplied relative path to an absolute path
    inside content/. Returns (path, error_message). On error, path
    is None and error_message describes why (path-traversal guard).
    """
    if not rel_path or not isinstance(rel_path, str):
        return None, "file path is required"
    rel_path = rel_path.strip()
    # Reject absolute paths — the API only addresses files relative
    # to content/, so an absolute path is either a misuse or an
    # attack. Don't auto-relativize.
    if rel_path.startswith("/") or rel_path.startswith("\\"):
        return None, "absolute paths are not allowed"
    # ξ.17 SEC-008 — explicit Windows drive-letter reject. On Windows,
    # `Path("C:\\foo")` is absolute, and `(REPO / "content" / "C:\\foo")`
    # returns `C:\\foo` (rightmost-absolute wins). The downstream
    # `relative_to(content_root)` does catch and reject — fail-closed
    # today — but adding the explicit reject here mirrors
    # `safe_path._check_string_safety` and removes the drift risk if
    # the relative_to check is ever refactored. Reject any string
    # whose first 2 chars look like `<letter>:` (drive prefix) and
    # also reject the form `C:foo` (drive-relative path, no slash).
    if len(rel_path) >= 2 and rel_path[1] == ":" and rel_path[0].isalpha():
        return None, "drive-letter prefix not allowed"
    # Reject obvious traversal patterns before resolving
    if ".." in Path(rel_path).parts:
        return None, "path traversal not allowed"
    content_root = (REPO / "content").resolve()
    try:
        candidate = (REPO / "content" / rel_path).resolve()
    except (OSError, RuntimeError):
        return None, "could not resolve path"
    # Ensure the resolved path is still under content/. The
    # is_relative_to method (3.9+) is the explicit way to ask.
    try:
        candidate.relative_to(content_root)
    except ValueError:
        return None, "path resolves outside content/"
    return candidate, None


def api_list_backups(file_path: str) -> dict:
    """List backup snapshots for a given content file.

    Returns:
        {"status": "ok", "file": str, "snapshots": [
            {"id": str, "timestamp": "20260508T050639Z",
             "iso_time": "2026-05-08T05:06:39+00:00",
             "size_bytes": int}, ...
          ]}
    Errors:
        invalid_path / not_under_content -> 400
        file_not_found                   -> 404
    """
    abs_path, err = _resolve_content_path(file_path)
    if err:
        return {"status": "error", "code": "invalid_path", "http": 400, "message": err}
    # The file itself need not currently exist (it could have been
    # deleted) — what we care about is whether backups exist.
    backup_dir = abs_path.parent / ".backups"
    snapshots = []
    if backup_dir.is_dir():
        # Match files whose stem matches abs_path.stem
        wanted_stem = abs_path.stem
        for bp in sorted(backup_dir.iterdir()):
            m = _BACKUP_FILENAME_RE.match(bp.name)
            if not m:
                continue
            if m.group("stem") != wanted_stem:
                continue
            ts = m.group("ts")
            # Format ISO-8601 from the timestamp
            try:
                iso_time = f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]}T{ts[9:11]}:{ts[11:13]}:{ts[13:15]}+00:00"
            except IndexError:
                iso_time = ts
            try:
                size_bytes = bp.stat().st_size
            except OSError:
                size_bytes = 0
            snapshots.append(
                {
                    "id": bp.name,
                    "timestamp": ts,
                    "iso_time": iso_time,
                    "size_bytes": size_bytes,
                }
            )
    # Newest first — easier for UI
    snapshots.reverse()
    return {
        "status": "ok",
        "file": str(abs_path.relative_to((REPO / "content").resolve())),
        "snapshots": snapshots,
        "count": len(snapshots),
    }


@audit_log.audit_endpoint(action="restore_backup")
def api_restore_backup(file_path: str, snapshot_id: str) -> dict:
    """Restore a backup snapshot to its source file.

    Crucially, this creates a NEW backup of the current state
    BEFORE restoring — so the restore itself is reversible.
    Same defense-in-depth pattern as ensure_backup itself.

    Returns:
        {"status": "ok", "file": str, "restored_from": str,
         "new_backup": str}  (new_backup = the pre-restore snapshot)
    Errors:
        invalid_path     -> 400
        invalid_snapshot -> 400 (id has bad format / not for this file)
        snapshot_not_found -> 404
    """
    abs_path, err = _resolve_content_path(file_path)
    if err:
        return {"status": "error", "code": "invalid_path", "http": 400, "message": err}
    if not snapshot_id or not isinstance(snapshot_id, str):
        return {"status": "error", "code": "invalid_snapshot", "http": 400, "message": "snapshot_id is required"}

    m = _BACKUP_FILENAME_RE.match(snapshot_id)
    if not m:
        return {
            "status": "error",
            "code": "invalid_snapshot",
            "http": 400,
            "message": f"snapshot id {snapshot_id!r} has bad format",
        }
    # Belt-and-braces: the snapshot's stem must match the file's stem,
    # else the caller is trying to restore a snapshot of a DIFFERENT
    # file into this path, which is a bug or attack.
    if m.group("stem") != abs_path.stem:
        return {
            "status": "error",
            "code": "invalid_snapshot",
            "http": 400,
            "message": (f"snapshot {snapshot_id!r} does not belong to file {abs_path.name!r}"),
        }

    backup_dir = abs_path.parent / ".backups"
    snapshot_path = backup_dir / snapshot_id
    if not snapshot_path.is_file():
        return {
            "status": "error",
            "code": "snapshot_not_found",
            "http": 404,
            "message": f"no such snapshot: {snapshot_id}",
        }

    # Defense-in-depth: snapshot_path must also be under content/,
    # in case backup_dir was a symlink or something equally weird.
    content_root = (REPO / "content").resolve()
    try:
        snapshot_path.resolve().relative_to(content_root)
    except ValueError:
        return {
            "status": "error",
            "code": "invalid_snapshot",
            "http": 400,
            "message": "snapshot resolves outside content/",
        }

    # Step 0: read the snapshot content INTO MEMORY before doing
    # anything else. ensure_backup uses second-resolution timestamps;
    # if the pre-restore backup runs in the same second as the
    # snapshot we're restoring, the backup paths can collide and
    # ensure_backup would silently overwrite our snapshot file with
    # the current (about-to-be-replaced) content. Reading first
    # captures the bytes we actually care about, regardless of any
    # backup-path collision later.
    try:
        snapshot_bytes = snapshot_path.read_bytes()
    except OSError as e:
        return {
            "status": "error",
            "code": "snapshot_not_found",
            "http": 404,
            "message": f"could not read snapshot: {e}",
        }

    # Step 1: snapshot the current state (if file exists) so this
    # restore is itself reversible. May collide with an existing
    # backup path — that's fine; the data we need is already in
    # snapshot_bytes.
    from scripts.core import notes_io

    pre_restore_backup = None
    if abs_path.is_file():
        pre_restore_backup = notes_io.ensure_backup(abs_path)
    # Step 2: write the captured snapshot bytes to the source file.
    # ω.9 — atomic write: a crash here leaves either the previous
    # file (just backed up by ensure_backup above) or the new
    # snapshot bytes, never a half-restored corrupt state.
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    notes_io.atomic_write_bytes(abs_path, snapshot_bytes)
    # Step 3: invalidate any cached parse of this file.
    notes_io.clear_load_notes_cache()

    return {
        "status": "ok",
        "file": str(abs_path.relative_to(content_root)),
        "restored_from": snapshot_id,
        "new_backup": pre_restore_backup.name if pre_restore_backup else None,
    }


# Phase ψ.6 — Operator dashboard. Single "are we OK?" page for the
# project owner. Composes existing primitives per Rule §9 — no new
# computation engine, just orchestration of already-cached data:
#   - api_corpus_progress()       → note count + target + percent
#   - api_attribution_audit()     → attribution health metrics
#   - api_preflight()             → ship-readiness aggregator
#   - shutil.disk_usage()         → free space on content/
#   - process start time          → server uptime
# Pattern: pure-function-API + thin route adapter (the 5th instance
# of this; see CHANGELOG ω.1 retro and queued §9 codification).

# Module-load time = process start time (good enough for "uptime")
_PROCESS_START_TIME = time.time()


def api_ops_dashboard() -> dict:
    """Aggregate "are we OK?" metrics from existing endpoints.

    Returns a dict with the following sections; every section has
    its own status field so partial failures don't break the whole
    response (the dashboard UI still renders):
        {
          "corpus":      {status, current, target, percent},
          "attribution": {status, total, attributed, percent},
          "preflight":   {status, items_ok, items_failed, items_warn},
          "uptime":      {status, seconds, human},
          "disk":        {status, free_bytes, free_human, used_pct},
          "save_tag":    {status, name},  # most recent save (best-effort)
        }
    """
    import shutil

    out: dict = {}

    # 1. Corpus progress — already cached, near-free
    try:
        cp = api_corpus_progress()
        out["corpus"] = {
            "status": "ok",
            "current": cp.get("current", 0),
            "target": cp.get("target", 0),
            "percent": cp.get("percent", 0.0),
        }
    except Exception as e:
        out["corpus"] = {"status": "error", "message": str(e)}

    # 2. Attribution audit — composed for the percent-attributed metric
    try:
        au = api_attribution_audit()
        counts = au.get("counts", {}) or {}
        total = counts.get("total", 0) or 0
        attributed = counts.get("attributed", 0) or 0
        pct = (attributed / total * 100.0) if total else 0.0
        out["attribution"] = {
            "status": "ok",
            "total": total,
            "attributed": attributed,
            "percent": round(pct, 1),
        }
    except Exception as e:
        out["attribution"] = {"status": "error", "message": str(e)}

    # 3. Preflight — count items by severity
    try:
        pf = api_preflight()
        items = pf.get("items", []) or []
        items_ok = sum(1 for i in items if i.get("status") == "pass")
        items_failed = sum(1 for i in items if i.get("status") == "fail")
        items_warn = sum(1 for i in items if i.get("status") == "warn")
        out["preflight"] = {
            "status": "ok",
            "items_ok": items_ok,
            "items_failed": items_failed,
            "items_warn": items_warn,
            "items_total": len(items),
        }
    except Exception as e:
        out["preflight"] = {"status": "error", "message": str(e)}

    # 4. Uptime — module-load time is a reasonable proxy for
    # process start (the process loads this module on import)
    try:
        seconds = int(time.time() - _PROCESS_START_TIME)
        if seconds < 60:
            human = f"{seconds}s"
        elif seconds < 3600:
            human = f"{seconds // 60}m {seconds % 60}s"
        elif seconds < 86400:
            human = f"{seconds // 3600}h {(seconds % 3600) // 60}m"
        else:
            human = f"{seconds // 86400}d {(seconds % 86400) // 3600}h"
        out["uptime"] = {"status": "ok", "seconds": seconds, "human": human}
    except Exception as e:
        out["uptime"] = {"status": "error", "message": str(e)}

    # 5. Disk free on content/
    try:
        usage = shutil.disk_usage(str(REPO / "content"))
        free_gb = usage.free / (1024**3)
        used_pct = round(usage.used / usage.total * 100.0, 1)
        out["disk"] = {
            "status": "ok",
            "free_bytes": usage.free,
            "free_human": f"{free_gb:.1f} GB",
            "used_pct": used_pct,
        }
    except Exception as e:
        out["disk"] = {"status": "error", "message": str(e)}

    # 6. Save tag — best-effort, scan dev/CHANGELOG.md for the
    # most recent line containing "save tag" or use the lineage marker
    try:
        changelog = REPO / "dev" / "CHANGELOG.md"
        save_tag = "(unknown)"
        if changelog.is_file():
            text = changelog.read_text(encoding="utf-8", errors="ignore")
            # Look for the most recent "Save tag:" line in the most
            # recent entry (top of file, append-only). Match up to
            # end of line or sentence-ending; allow dots since save
            # tags include them (e.g. "YHWH v1.2-slim").
            m = re.search(r"\*\*Save tag:\*\*\s*([^\n]+)", text)
            if m:
                save_tag = m.group(1).strip().rstrip(".").strip()
        out["save_tag"] = {"status": "ok", "name": save_tag}
    except Exception as e:
        out["save_tag"] = {"status": "error", "message": str(e)}

    return out


# Phase ω.3 / ω.35-B.7 — /apihelp data endpoint.
# api_help_data + the _ROUTE_PATTERNS / _CONSOLE_PATTERNS
# constants moved to scripts/api/help.py. Re-imports preserve
# scripts.web.api_help_data (route table + tests).
from scripts.api.help import api_help_data  # noqa: E402


def api_dev_templates_mtime() -> dict:
    """ω.39 — return the maximum mtime_ns across the project's
    template files. Used by `THEME_HOTRELOAD_JS` to drive
    auto-reload-on-edit in localhost dev sessions.

    Scope: `scripts/templates/*.py` only. A future ω.39.x can
    extend to content/notes/ + content/translations/ as needed.

    Returns:
        {"status": "ok", "mtime_ns": int} — max of every
        template module's stat mtime. If no templates are
        found (defensive), returns 0.

    No auth gate — this is read-only metadata. The endpoint
    is harmless even on production deployments; the JS-side
    guard (`hostname in ('localhost', '127.0.0.1', '::1')`)
    keeps the polling client out of production.
    """
    templates_dir = REPO / "scripts" / "templates"
    if not templates_dir.is_dir():
        return {"status": "ok", "mtime_ns": 0}
    max_mtime = 0
    for path in templates_dir.glob("*.py"):
        try:
            m = path.stat().st_mtime_ns
        except OSError:
            continue
        if m > max_mtime:
            max_mtime = m
    return {"status": "ok", "mtime_ns": max_mtime}


def api_corpus_progress() -> dict:
    """Return current corpus size + the project's note-count target,
    plus derived progress. Surfaced as a small widget in every
    console header so the publisher sees the trajectory toward the
    35-40K Ethiopian Tewahedo flagship goal on every page hit.

    Composes api_attribution_audit() (which is already cached); no
    new file scanning."""
    audit = api_attribution_audit()
    current = int(audit.get("counts", {}).get("total", 0))
    target = CORPUS_TARGET
    deficit = max(0, target - current)
    # Avoid divide-by-zero in the off chance someone sets
    # CORPUS_TARGET = 0 mid-experiment
    percent = (current / target * 100.0) if target > 0 else 0.0
    return {
        "current": current,
        "target": target,
        "deficit": deficit,
        "percent": round(percent, 2),
    }


def api_attribution_audit() -> dict:
    """Phase ξ.4 — quality-control read endpoint.

    Cached on the signature of all notes files + kinds/categories/books
    (Phase φ.1). Stays in sync with edits automatically because every
    note write updates the file's mtime.
    """
    return _cached_attribution_audit(
        _notes_dir_signature(),
        _files_signature(REPO / "content" / "kinds.yaml"),
        _files_signature(REPO / "content" / "categories.yaml"),
        _files_signature(REPO / "content" / "books.yaml"),
    )


def _compute_attribution_audit_uncached() -> dict:
    """Scan every note in the corpus and classify its attribution.

    Returns counts + a flat list of notes that need attention
    (missing or thin), each with an anchor that can be cross-linked
    to /sources for editing.
    """
    books = config.load_books()
    kinds_idx = config.kinds_by_code()
    cats_idx = config.categories_by_id()

    counts = {"total": 0, "missing": 0, "thin": 0, "user": 0, "sourced": 0}
    needs_attention = []  # missing + thin notes, in canonical order

    for book in books:
        code = book["code"]
        path = NOTES_DIR / f"{code}.py"
        if not path.is_file():
            continue
        notes = notes_io.load_notes(path) or []
        for i, tup in enumerate(notes):
            if len(tup) < 9:
                continue
            ch, vs, suffix, anchor, kind, title, label, body, attribution = tup[:9]
            counts["total"] += 1
            cls = _classify_attribution(attribution or "")
            counts[cls] = counts.get(cls, 0) + 1
            if cls in ("missing", "thin"):
                kind_def = kinds_idx.get(kind, {})
                cat_id = kind_def.get("category", "?")
                cat_def = cats_idx.get(cat_id, {})
                needs_attention.append(
                    {
                        "book": code,
                        "book_title": book.get("title", code),
                        "section": book.get("section", ""),
                        "chapter": ch,
                        "verse": vs,
                        "suffix": suffix or "",
                        "kind": kind,
                        "kind_label": kind_def.get("label", kind),
                        "category": cat_id,
                        "category_symbol": cat_def.get("symbol", "?"),
                        "title": title,
                        "body_preview": (body or "")[:120],
                        "attribution": (attribution or "").strip(),
                        "classification": cls,
                    }
                )

    # Per-book counts of notes needing attention (for the left rail)
    by_book: dict[str, dict] = {}
    for item in needs_attention:
        b = item["book"]
        if b not in by_book:
            by_book[b] = {
                "code": b,
                "title": item["book_title"],
                "section": item["section"],
                "missing": 0,
                "thin": 0,
            }
        by_book[b][item["classification"]] += 1
    by_book_list = sorted(by_book.values(), key=lambda x: -(x["missing"] + x["thin"]))

    # Per-kind counts of notes needing attention
    by_kind: dict[str, int] = {}
    for item in needs_attention:
        by_kind[item["kind"]] = by_kind.get(item["kind"], 0) + 1
    by_kind_list = sorted(by_kind.items(), key=lambda x: -x[1])

    return {
        "counts": counts,
        "needs_attention": needs_attention,
        "by_book": by_book_list,
        "by_kind": [{"kind": k, "count": n} for k, n in by_kind_list],
    }


# ============================================================
# Audit-log read endpoint (Phase ξ.13 / ω.35-B.7)
# ============================================================
# api_audit_log moved to scripts/api/audit.py. Re-import preserves
# scripts.web.api_audit_log (route table lambda + tests).
from scripts.api.audit import api_audit_log  # noqa: E402


# ============================================================
# Per-Note Disable API (Phase ρ.1) — disable individual notes per edition
# ============================================================


_NOTE_ID_RE = re.compile(r"^([a-z0-9]+):(\d+):(\d+)([a-z]*):([a-z][a-z0-9-]*)$")


def note_id_from_tuple(book_code: str, tup: tuple) -> str:
    """Compute a stable, human-readable note ID for an editions.yaml entry.

    Format: <book>:<ch>:<vs>[<suffix>]:<kind>
    e.g. gen:1:1a:word

    The format is intentionally stable across reorders, additions, and
    deletions: it identifies a note by its content, not its position.
    """
    if len(tup) < 5:
        raise ValueError("malformed note tuple")
    ch, vs, suffix, _anchor, kind = tup[0], tup[1], tup[2], tup[3], tup[4]
    return f"{book_code}:{ch}:{vs}{suffix or ''}:{kind}"


def parse_note_id(nid: str) -> dict | None:
    """Parse a note ID back into its components. Returns None on invalid."""
    m = _NOTE_ID_RE.match(nid)
    if not m:
        return None
    return {
        "book": m.group(1),
        "chapter": int(m.group(2)),
        "verse": int(m.group(3)),
        "suffix": m.group(4),
        "kind": m.group(5),
    }


def html_ref_id_from_note_id(nid: str, books_idx: dict | None = None) -> str | None:
    """Translate our note ID format to the HTML's compact `ref-<prefix><cc><vv><suffix>`.

    The build's HTML uses the per-book id_prefix and zero-padded chapter/verse:
        ref-g0101a   →   gen:1:1a:word
    """
    parsed = parse_note_id(nid)
    if not parsed:
        return None
    if books_idx is None:
        books_idx = config.books_by_code()
    book = books_idx.get(parsed["book"])
    if not book:
        return None
    prefix = book.get("id_prefix")
    if not prefix:
        return None
    return f"ref-{prefix}{parsed['chapter']:02d}{parsed['verse']:02d}{parsed['suffix']}"


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


# ============================================================
# Publisher Console API (Phase π.1) — full publishing metadata per edition
# ============================================================
#
# Stored as flat fields in editions.yaml (backward-compat: missing fields
# fall back to sensible defaults from build_onix). The π.2 phase will
# wire these into the EPUB build pipeline.

# Sensible defaults applied when an edition has no publishing data yet.
# These match what build_onix.py currently hardcodes, so behavior on the
# next build is identical until the user explicitly edits.
PUBLISHING_DEFAULTS = {
    "publisher_name": "Independent",
    "publisher_url": "",
    "copyright_year": str(datetime.now(timezone.utc).year),
    "copyright_holder": "",
    "copyright_notice": "All rights reserved.",
    "publication_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    "language_code": "en",
    "isbn_epub": "",
    "isbn_print": "",
    "cover_credit": "",
    "source_text_credit": ("Scripture text based on the World English Bible (public domain)."),
}

# These are list-typed fields — stored as YAML sub-lists.
PUBLISHING_LIST_FIELDS = ("authors", "bisac_codes")

# Single-line text fields (length max varies).
PUBLISHING_TEXT_LIMITS = {
    "publisher_name": 200,
    "publisher_url": 500,
    "copyright_year": 10,
    "copyright_holder": 200,
    "copyright_notice": 500,
    "publication_date": 30,
    "language_code": 12,
    "isbn_epub": 40,
    "isbn_print": 40,
    "cover_credit": 200,
    "source_text_credit": 500,
}


def api_publisher_data() -> dict:
    """Phase π.1 — publisher console feed. Cached on editions.yaml mtime."""
    return _cached_publisher_data(
        _files_signature(REPO / "content" / "editions.yaml"),
    )


def _compute_publisher_data_uncached() -> dict:
    """Return all editions' publishing metadata for the /publisher UI.

    Each edition row includes both its existing meta (id, title) and
    its publishing fields (with defaults filled in for missing values
    so the UI can show the user what would actually be used at build).
    """
    editions = config.load_editions()
    out = []
    for e in editions:
        row = {
            "id": e["id"],
            "title": e.get("title", e["id"]),
            "short_title": e.get("short_title", ""),
            # Legacy generic isbn — keep displaying for reference, but the
            # publisher console writes to isbn_epub / isbn_print instead.
            "isbn_legacy": e.get("isbn", ""),
        }
        for field, default in PUBLISHING_DEFAULTS.items():
            row[field] = e.get(field, default)
        for lf in PUBLISHING_LIST_FIELDS:
            row[lf] = list(e.get(lf) or [])
        out.append(row)
    return {"editions": out}


def _patch_yaml_list_field(text: str, edition_id: str, field: str, items: list[str]) -> str:
    """Replace or insert a YAML sub-list block (e.g. authors:) inside one
    edition record. Items are written QUOTED, like the disabled_note_ids
    pattern, so they survive the project's custom YAML parser even if
    they happen to contain colons or other punctuation.
    """
    block_re = re.compile(
        rf"(^  - id: {re.escape(edition_id)}\n)(.*?)(?=^  - id:|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = block_re.search(text)
    if not m:
        raise ValueError(f"edition {edition_id} not found")
    head, body = m.group(1), m.group(2)

    # Build the new block
    if items:
        new_block = f"    {field}:\n" + "\n".join(f'      - "{_yaml_escape(s)}"' for s in items) + "\n"
    else:
        new_block = f"    {field}: []\n"

    # Try to replace existing block first
    list_re = re.compile(
        rf"^(    {re.escape(field)}:.*?\n)"
        rf"((?:      - [^\n]+\n)*|    {re.escape(field)}: \[\]\n)",
        re.MULTILINE,
    )
    if list_re.search(body):
        new_body = list_re.sub(new_block, body, count=1)
    else:
        # Insert at end of the record block (before the trailing blank
        # line if any). This places it stably regardless of which other
        # optional fields the edition has.
        new_body = body.rstrip("\n") + "\n" + new_block + "\n" if body.rstrip("\n") else new_block

    return text[: m.start()] + head + new_body + text[m.end() :]


def _yaml_escape(s: str) -> str:
    """Escape a string for safe inclusion inside a YAML double-quoted scalar."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


# ============================================================
# Phase ξ.5 — Edition Diff View (read-only sales / demo tool)
# ============================================================


def _canons_index() -> dict:
    """Cached load of canons.yaml — returns {canon_id: {label, description, books}}."""
    canons_path = REPO / "content" / "canons.yaml"
    if not canons_path.is_file():
        return {}
    import yaml

    data = yaml.safe_load(canons_path.read_text(encoding="utf-8")) or {}
    return data.get("canons", {}) or {}


def _diff_edition_summary(ed: dict, mtx, kinds_idx: dict, books_idx: dict, canons_idx: dict) -> dict:
    """One edition's side of the diff — headline metadata plus
    pre-computed totals so the UI doesn't have to re-derive them.
    """
    ed_id = ed["id"]
    # ψ.35-B2 — was: `mtx.enabled.get(ed_id, {})`. Accessor returns
    # the same shape from the canonical per_chapter store.
    enabled = mtx.enabled_kinds_dict(ed_id)
    canon_books = mtx.edition_canon_books.get(ed_id, set())
    enabled_kinds = mtx.edition_enabled_kinds.get(ed_id, set())
    canon_id = ed.get("canon", "")
    canon_def = canons_idx.get(canon_id, {}) or {}
    return {
        "id": ed_id,
        "title": ed.get("title", ed_id),
        "short_title": ed.get("short_title", ed_id),
        "audience": ed.get("target_audience", ""),
        "isbn": ed.get("isbn", ""),
        "imprint": ed.get("imprint", ""),
        "canon_id": canon_id,
        "canon_label": canon_def.get("label", canon_id),
        "totals": {
            "books": len(canon_books),
            "kinds": len(enabled_kinds),
            "notes": sum(enabled.values()),
        },
    }


def _diff_books_section(a_books: set, b_books: set, books_idx: dict) -> dict:
    """Per-book diff: which books ship in A but not B and vice-versa.
    Sorted by canonical book ordering (the order in books.yaml)."""
    book_order = list(books_idx.keys())  # books.yaml order is canonical
    order_rank = {code: i for i, code in enumerate(book_order)}

    def _format(code_set):
        rows = []
        for code in sorted(code_set, key=lambda c: order_rank.get(c, 9999)):
            b = books_idx.get(code, {})
            rows.append(
                {
                    "code": code,
                    "title": b.get("title", code),
                }
            )
        return rows

    return {
        "only_a": _format(a_books - b_books),
        "only_b": _format(b_books - a_books),
        "both_count": len(a_books & b_books),
    }


def _diff_kinds_section(a_id: str, b_id: str, mtx, kinds_idx: dict, cats_idx: dict) -> dict:
    """Per-kind diff with shipping counts. Three buckets:
       only_a   — kinds enabled in A but not B (with A's count)
       only_b   — kinds enabled in B but not A (with B's count)
       shared   — kinds enabled in both, with both counts and the delta
    Within each bucket, sort by category sort_order, then by descending
    count so the most prominent differences appear first.
    """
    a_kinds = mtx.edition_enabled_kinds.get(a_id, set())
    b_kinds = mtx.edition_enabled_kinds.get(b_id, set())
    # ψ.35-B2 — was: `mtx.enabled.get(a_id, {})` / `mtx.enabled.get(b_id, {})`.
    a_counts = mtx.enabled_kinds_dict(a_id)
    b_counts = mtx.enabled_kinds_dict(b_id)

    def _row(code, a_n=None, b_n=None):
        k = kinds_idx.get(code, {}) or {}
        cat_id = k.get("category", "?")
        cat = cats_idx.get(cat_id, {}) or {}
        row = {
            "code": code,
            "label": k.get("label", code),
            "category": cat_id,
            "category_label": cat.get("label", cat_id),
            "category_sort": cat.get("sort_order", 999),
            "symbol": k.get("symbol") or cat.get("symbol", "?"),
        }
        if a_n is not None:
            row["a_count"] = a_n
        if b_n is not None:
            row["b_count"] = b_n
        return row

    only_a = [_row(c, a_n=a_counts.get(c, 0)) for c in a_kinds - b_kinds]
    only_b = [_row(c, b_n=b_counts.get(c, 0)) for c in b_kinds - a_kinds]
    shared = []
    for c in a_kinds & b_kinds:
        a_n = a_counts.get(c, 0)
        b_n = b_counts.get(c, 0)
        r = _row(c, a_n=a_n, b_n=b_n)
        r["delta"] = a_n - b_n
        shared.append(r)

    only_a.sort(key=lambda r: (r["category_sort"], -r.get("a_count", 0)))
    only_b.sort(key=lambda r: (r["category_sort"], -r.get("b_count", 0)))
    # shared: largest absolute count-difference first (most newsworthy)
    shared.sort(key=lambda r: (-abs(r["delta"]), r["category_sort"]))

    return {"only_a": only_a, "only_b": only_b, "shared": shared}


def _diff_categories_section(a_id: str, b_id: str, kinds_idx: dict, cats_idx: dict, mtx) -> list:
    """Category-level rollup: total notes per category, A vs B.
    Includes every category that is non-zero in at least one side, plus
    every category that is enabled (zero-count) in either edition — so
    the UI can show "0 vs 142" stark gaps that are part of the story.
    """
    from scripts.core import matrix as matrix_mod

    a_by_cat = matrix_mod.breakdown_by_category(a_id)
    b_by_cat = matrix_mod.breakdown_by_category(b_id)

    cat_ids = set(a_by_cat) | set(b_by_cat)
    rows = []
    for cid in cat_ids:
        c = cats_idx.get(cid, {}) or {}
        rows.append(
            {
                "id": cid,
                "label": c.get("label", cid),
                "symbol": c.get("symbol", "?"),
                "sort_order": c.get("sort_order", 999),
                "a_count": a_by_cat.get(cid, 0),
                "b_count": b_by_cat.get(cid, 0),
            }
        )
    rows.sort(key=lambda r: r["sort_order"])
    return rows


def _diff_headline(a_summary: dict, b_summary: dict, books_section: dict, kinds_section: dict) -> str:
    """Plain-English one-line summary suitable for a buyer-demo opening
    slide. Picks the most recognisable difference — books-only-in-one
    side first, then kinds-only-in-one side, then total-note delta.
    """
    a_short = a_summary["short_title"]
    b_short = b_summary["short_title"]
    a_only_books = books_section["only_a"]
    b_only_books = books_section["only_b"]
    a_only_kinds = len(kinds_section["only_a"])
    b_only_kinds = len(kinds_section["only_b"])

    bits = []
    if a_only_books and not b_only_books:
        bits.append(
            f"{a_short} includes {len(a_only_books)} book{'s' if len(a_only_books) != 1 else ''} that {b_short} omits"
        )
    elif b_only_books and not a_only_books:
        bits.append(
            f"{b_short} includes {len(b_only_books)} book{'s' if len(b_only_books) != 1 else ''} that {a_short} omits"
        )
    elif a_only_books and b_only_books:
        bits.append(
            f"{a_short} adds {len(a_only_books)} book"
            f"{'s' if len(a_only_books) != 1 else ''} the other lacks; "
            f"{b_short} adds {len(b_only_books)}"
        )

    if a_only_kinds or b_only_kinds:
        bits.append(f"{a_only_kinds} note kinds are exclusive to {a_short}, {b_only_kinds} to {b_short}")

    a_tot = a_summary["totals"]["notes"]
    b_tot = b_summary["totals"]["notes"]
    if a_tot != b_tot:
        diff = abs(a_tot - b_tot)
        bigger = a_short if a_tot > b_tot else b_short
        bits.append(f"{bigger} ships {diff} more notes overall")

    if not bits:
        return f"{a_short} and {b_short} are identical at the edition level."
    return " · ".join(bits) + "."


def api_edition_diff(a_id: str, b_id: str) -> dict:
    """Phase ξ.5 — sales-tool edition diff. Cached on the signature
    of every file involved in the diff computation."""
    return _cached_edition_diff(
        a_id,
        b_id,
        _files_signature(REPO / "content" / "editions.yaml"),
        _files_signature(REPO / "content" / "kinds.yaml"),
        _files_signature(REPO / "content" / "categories.yaml"),
        _files_signature(REPO / "content" / "canons.yaml"),
        _files_signature(REPO / "content" / "books.yaml"),
        _notes_dir_signature(),
    )


def _compute_edition_diff_uncached(a_id: str, b_id: str) -> dict:
    """Side-by-side diff between two editions (Phase ξ.5).

    Pure read-only view — no writes anywhere. Powers the "Catholic vs
    Evangelical: what's different" demo slide a sales rep can pull up
    in front of a publisher buyer in two clicks.

    Errors:
        unknown edition id → 404-style {"error": ...}
        a_id == b_id       → returns a valid diff (all bins empty); the
                              UI is responsible for nudging the user.
    """
    from scripts.core import matrix as matrix_mod

    eds = config.editions_by_id()
    if a_id not in eds:
        return {"error": f"unknown edition: {a_id}"}
    if b_id not in eds:
        return {"error": f"unknown edition: {b_id}"}

    mtx = matrix_mod.compute_matrix()
    kinds_idx = config.kinds_by_code()
    cats_idx = config.categories_by_id()
    books_idx = config.books_by_code()
    canons_idx = _canons_index()

    a = _diff_edition_summary(eds[a_id], mtx, kinds_idx, books_idx, canons_idx)
    b = _diff_edition_summary(eds[b_id], mtx, kinds_idx, books_idx, canons_idx)

    a_books = mtx.edition_canon_books.get(a_id, set())
    b_books = mtx.edition_canon_books.get(b_id, set())

    books_section = _diff_books_section(a_books, b_books, books_idx)
    kinds_section = _diff_kinds_section(a_id, b_id, mtx, kinds_idx, cats_idx)
    cats_section = _diff_categories_section(a_id, b_id, kinds_idx, cats_idx, mtx)
    headline = _diff_headline(a, b, books_section, kinds_section)

    # Light index for the picker dropdown (id + display name only).
    editions_index = [
        {"id": e["id"], "short_title": e.get("short_title", e["id"]), "title": e.get("title", e["id"])}
        for e in config.load_editions()
    ]

    return {
        "a": a,
        "b": b,
        "books": books_section,
        "kinds": kinds_section,
        "categories": cats_section,
        "headline": headline,
        "editions_index": editions_index,
    }


# ============================================================
# HTTP handler
# ============================================================


def _safe_request(method):
    """Phase ω.8 — top-level error boundary for do_* request methods.
    Any uncaught Exception becomes a 500 JSON response instead of a
    stack trace dumped to the response stream. Per-endpoint handlers
    still catch their own expected errors with appropriate 4xx codes;
    this wrapper is the safety net for genuinely unexpected
    conditions (Python bugs, OS errors, etc.).

    Used as a decorator on Handler.do_GET / do_POST / do_PUT /
    do_DELETE."""

    def wrapper(self):
        try:
            return method(self)
        except Exception as e:
            return self._send_unhandled_error(e, method.__name__)

    wrapper.__name__ = method.__name__
    wrapper.__wrapped__ = method
    return wrapper


# ω.35-A.1 (2026-05-11) — table-driven dispatch for the simplest GET
# routes (the `if path == "/api/X": return self._send_json(api_X())`
# shape that dominated the do_GET cascade). The Handler.do_GET method
# checks this table FIRST; falls through to the legacy if/elif
# cascade for routes that don't fit the simple shape (auth-gated,
# payload-reading, multipart parsing, custom error translation).
#
# **Migration strategy:** the migrated branches REMAIN in the legacy
# if/elif as dead code. The table dispatch returns first, so those
# branches are unreachable but still picked up by the ω.35-A
# `check_routes.py` drift linter (which discovers routes by regex-
# scanning do_GET). Future ω.35-A.2 cleanup will delete the dead
# branches once the table dispatch is proven across a full release
# cycle. For now, dead-code preservation = safety net + zero linter
# delta.
#
# **What qualifies for the table:** routes that are (a) GET, (b) no
# admin auth, (c) no payload reading, (d) no querystring parsing
# beyond what the handler does internally, (e) the response is a
# bare `_send_json(api_X())` with no error-translation logic. Any
# route that needs more inline logic stays in the legacy cascade.
#
# Routes are migrated as `(path, handler_callable)` tuples. The
# handlers are the existing pure-function `api_*` helpers — no
# changes to handler signatures or call patterns.
_SIMPLE_GET_ROUTES: list[tuple[str, "object"]] = [
    ("/api/books", api_books),
    ("/api/kinds", api_kinds),
    ("/api/matrix", api_matrix),
    ("/api/reading-plans", api_reading_plans_list),
    ("/api/scenarios", api_list_scenarios),
    ("/api/sources", api_sources_index),
    ("/api/customize", api_customize_data),
    ("/api/publisher", api_publisher_data),
    ("/api/covers", api_covers),
    ("/api/preflight", api_preflight),
    ("/api/ops", api_ops_dashboard),
    ("/api/apihelp", api_help_data),
    ("/api/corpus-progress", api_corpus_progress),
    ("/api/edition-templates", api_edition_templates_list),
    # ω.39 — dev-side template mtime probe for THEME_HOTRELOAD_JS.
    ("/api/dev/templates-mtime", api_dev_templates_mtime),
    # ε.2 — executive dashboard payload (6 KPI tiles + recent events).
    ("/api/exec", api_exec_dashboard),
    # ε.3 — sales rollup: per-channel + per-edition + MTD totals.
    ("/api/sales/rollup", api_sales_rollup),
    # ε.6 — distribution checklist: per-edition × per-channel grid.
    ("/api/distribution", api_distribution_list),
    # ο.4 — archive.org configuration status (does the publisher have
    # credentials set yet?). Never touches the network.
    ("/api/archive-org/status", api_archive_org_status),
    # ξ.21 — admin-auth + 2FA enrollment status (read-only; never
    # reveals the secret).
    ("/api/auth/status", api_auth_status),
]


# ω.35-A.2 (2026-05-11) — second slice of the route-table migration.
# `_REGEX_GET_ROUTES` covers the next-simplest GET shape: parameterized
# paths with the boilerplate "regex.match → handler(*groups) →
# if result.get('status') == 'error': error-translate → else
# send_json(result)" pattern that appears 10+ times in the legacy
# cascade. Order matters here — table iteration is sequential and
# more-specific patterns MUST precede less-specific ones (e.g.
# `/api/snapshots/<ed>/<ver>` before `/api/snapshots/<ed>`). Same
# migration contract as ω.35-A.1: dispatch loop in do_GET checks
# this table after `_SIMPLE_GET_ROUTES` and before the legacy
# if/elif; migrated branches stay in legacy as dead code; the drift
# linter dedups so the route count is preserved.
#
# Qualifying criteria for this table:
#   - GET method
#   - No admin auth gate
#   - No querystring parsing (paths that need querystring stay in
#     legacy until ω.35-A.4 adds a query-aware table)
#   - Handler takes the regex capture groups as positional args
#   - Response is `_send_json(result)` with the standard
#     "if status == 'error', translate to HTTP error" dance
_REGEX_GET_ROUTES: list[tuple[re.Pattern, "object"]] = [
    (re.compile(r"^/api/reading-plans/([a-z0-9_-]+)$"), api_reading_plan_get),
    # Snapshots: order matters — /<ed>/<ver> must precede /<ed>
    (re.compile(r"^/api/snapshots/([a-z0-9._-]+)/([a-z0-9._-]+)$"), api_snapshot_get),
    (re.compile(r"^/api/snapshots/([a-z0-9._-]+)$"), api_snapshot_list),
    # ψ.36-A: per-edition matrix slice (lazy-load endpoint).
    (re.compile(r"^/api/matrix/edition/([a-z0-9_-]+)$"), api_matrix_for_edition),
    # γ.1: Strong's Hebrew lookup. Accepts 'H1' / 'h1' / '1' /
    # 'H0001' — the handler normalizes.
    (re.compile(r"^/api/hebrew/([Hh]?\d+)$"), api_hebrew_lookup),
    # γ.2: Strong's Greek lookup. Parallel to γ.1; G-prefix.
    (re.compile(r"^/api/greek/([Gg]?\d+)$"), api_greek_lookup),
    # ε.7 — /api/press-kit/<edition> — per-edition blurbs + cover-
    # present flag + field limits. The /download companion lives in
    # the legacy cascade because it returns binary (ZIP) bytes.
    (re.compile(r"^/api/press-kit/([a-z0-9-]+)$"), api_press_kit_get),
]


# ω.35-A.4 (2026-05-11) — third slice of the route-table migration.
# `_QS_REGEX_GET_ROUTES` covers GET routes that need to parse the
# URL's querystring before calling their handler. The legacy
# cascade had this shape inlined 6+ times:
#
#   qs = urllib.parse.parse_qs(url.query or "")
#   arg = (qs.get("name") or ["default"])[0]
#   ...
#   result = api_X(group1, group2, kwarg=arg)
#   return self._send_json(result)   # or with error-translate
#
# The table represents each route as `(regex, handler_with_qs)`
# where `handler_with_qs` is `Callable[[Match, dict[str, list[str]]], dict]`
# — takes the regex match and the parsed qs dict, returns the
# response dict. Most entries use a small `lambda m, qs: api_X(...)`
# to keep the per-route boilerplate visible.
#
# Same dispatch contract as `_REGEX_GET_ROUTES`: order = precedence
# (more-specific patterns first), runs through
# `_dispatch_table_result` for the standard error-translation
# envelope, migrated branches deleted from legacy via ω.35-A.3-style
# cleanup once the table is proven.
_QS_REGEX_GET_ROUTES: list[tuple[re.Pattern, "object"]] = [
    # /api/snapshots/<ed>/<ver>/diff?against=<ver>
    (
        re.compile(r"^/api/snapshots/([a-z0-9._-]+)/([a-z0-9._-]+)/diff$"),
        lambda m, qs: api_snapshot_diff(
            m.group(1),
            m.group(2),
            against_version=(qs.get("against") or [""])[0] or None,
        ),
    ),
    # /api/audit-log?n=<int>
    (
        re.compile(r"^/api/audit-log$"),
        lambda m, qs: api_audit_log(n=(qs.get("n") or ["100"])[0]),
    ),
    # /api/diff?a=<ed>&b=<ed> — sensible defaults baked in
    (
        re.compile(r"^/api/diff$"),
        lambda m, qs: api_edition_diff(
            (qs.get("a") or ["catholic-study"])[0] or "catholic-study",
            (qs.get("b") or ["evangelical-reformed"])[0] or "evangelical-reformed",
        ),
    ),
]


# ω.35-A.5 (2026-05-11) — fourth slice of the route-table migration.
# `_PUT_ROUTES` covers PUT mutation routes that share the
# uniform shape: regex match → `payload = self._read_body()` →
# `result = api_X(group(1), payload)` → translate `ok: False`
# to HTTP 400 → send_json. Dispatch is wrapped in try/except so
# any handler exception becomes a 400 with the exception message
# (mirrors the legacy 9-line boilerplate inlined 6+ times).
#
# Admin auth happens at do_PUT function entry (one
# `_check_admin_auth()` call); table dispatch runs AFTER that
# check, so every table-registered route is auto-protected.
#
# Entries are `(regex, handler)` where handler is
# `Callable[[Match, dict], dict]` — takes the regex match and
# the parsed JSON payload, returns the response dict.
# `_dispatch_table_result` was extended in ω.35-A.5 to handle
# the `{ok: False}` legacy mutation-result shape (→ HTTP 400).
_PUT_ROUTES: list[tuple[re.Pattern, "object"]] = [
    (re.compile(r"^/api/notes/([a-z0-9]+)$"), lambda m, payload: api_save(m.group(1), payload)),
    # ω.35-A.10 — /api/edition/<id>/note-toggle MUST precede the
    # broader /api/edition/<id> below; both regex match on the same
    # prefix but the more-specific suffix-bearing pattern needs to
    # iterate first.
    (
        re.compile(r"^/api/edition/([a-z0-9-]+)/note-toggle$"),
        lambda m, payload: api_save_note_toggle(m.group(1), payload),
    ),
    (re.compile(r"^/api/edition/([a-z0-9-]+)$"), lambda m, payload: api_save_edition(m.group(1), payload)),
    (re.compile(r"^/api/scenarios/([a-z0-9_-]+)$"), lambda m, payload: api_save_scenario(m.group(1), payload)),
    (re.compile(r"^/api/category/([a-z0-9-]+)$"), lambda m, payload: api_save_category(m.group(1), payload)),
    (re.compile(r"^/api/kind/([a-z0-9-]+)$"), lambda m, payload: api_save_kind(m.group(1), payload)),
    (re.compile(r"^/api/publisher/([a-z0-9-]+)$"), lambda m, payload: api_save_publisher_meta(m.group(1), payload)),
    # ω.35-A.10 — /api/edition-meta/<id> — uses standard ok:True|False
    # shape (200 / 400). Standard helper covers it.
    (
        re.compile(r"^/api/edition-meta/([a-z0-9-]+)$"),
        lambda m, payload: api_save_edition_meta(m.group(1), payload),
    ),
    # ε.6 — /api/distribution/<edition> — mark a channel shipped.
    # Payload: {channel: <id>, url?, isbn?, notes?, shipped_at?}.
    (
        re.compile(r"^/api/distribution/([a-z0-9-]+)$"),
        lambda m, payload: api_distribution_mark(m.group(1), payload),
    ),
    # ε.7 — /api/press-kit/<edition> — save per-edition blurbs.
    # Payload: {blurb_150?, blurb_500?, sample_chapter_html?}.
    (
        re.compile(r"^/api/press-kit/([a-z0-9-]+)$"),
        lambda m, payload: api_press_kit_save(m.group(1), payload),
    ),
    # ω.35-A.10 — /api/editions/from-template — uses status==ok|error
    # shape. Standard helper covers it via status==error → http
    # envelope and fall-through 200.
    (
        re.compile(r"^/api/editions/from-template$"),
        lambda m, payload: api_create_edition_from_template(
            (payload or {}).get("template_id", ""),
            (payload or {}).get("new_id", ""),
            (payload or {}).get("new_title", ""),
        ),
    ),
]


# ω.35-A.6 (2026-05-11) — fifth slice of the route-table migration.
# `_DELETE_ROUTES` covers DELETE routes (no payload) that go through
# the standard `_dispatch_table_result` helper. Same shape as
# `_PUT_ROUTES` but the handler signature is `lambda m: api_X(...)`
# — no payload, no read_body() call. Admin auth runs at do_DELETE
# function entry (one `_check_admin_auth()` call).
#
# Order matters: more-specific patterns precede less-specific ones
# (e.g. `/api/covers/<ed>/book/<book>` before `/api/covers/<ed>/main`
# isn't needed because the suffixes differ, but the principle holds).
_DELETE_ROUTES: list[tuple[re.Pattern, "object"]] = [
    # /api/notes/<book>/<idx> — note delete by 0-based index
    (re.compile(r"^/api/notes/([a-z0-9]+)/(\d+)$"), lambda m: api_delete(m.group(1), int(m.group(2)))),
    # /api/snapshots/<ed>/<ver> — uses status==error envelope (Δ-shape)
    (
        re.compile(r"^/api/snapshots/([a-z0-9._-]+)/([a-z0-9._-]+)$"),
        lambda m: api_snapshot_delete(m.group(1), m.group(2)),
    ),
    # /api/scenarios/<name> — uses ok:False envelope
    (re.compile(r"^/api/scenarios/([a-z0-9_-]+)$"), lambda m: api_delete_scenario(m.group(1))),
    # /api/covers/<ed>/book/<book> — more specific; MUST precede /<ed>/main
    (
        re.compile(r"^/api/covers/([a-z0-9-]+)/book/([a-z0-9]+)$"),
        lambda m: api_delete_cover_book(m.group(1), m.group(2)),
    ),
    # /api/covers/<ed>/main
    (re.compile(r"^/api/covers/([a-z0-9-]+)/main$"), lambda m: api_delete_cover_main(m.group(1))),
    # ω.35-A.8 — /api/sources/cache/<id> — clear a source cache.
    # Previously used `_send_dict_result` (which preserved extras in
    # error envelopes); now table-compatible because A.8 extended
    # `_dispatch_table_result` to preserve extras too.
    # api_sources_cache_clear's error envelopes don't include extras
    # but the discipline is uniform now.
    (
        re.compile(r"^/api/sources/cache/([a-z0-9_-]+)$"),
        lambda m: api_sources_cache_clear(m.group(1)),
    ),
    # ε.6 — /api/distribution/<edition>/<channel> — unmark shipped.
    # Idempotent (already-absent returns ok:True, removed:False).
    (
        re.compile(r"^/api/distribution/([a-z0-9-]+)/([a-z_]+)$"),
        lambda m: api_distribution_unmark(m.group(1), m.group(2)),
    ),
]


# ω.35-A.7 (2026-05-11) — sixth slice of the route-table migration.
# `_POST_ROUTES` covers POST routes whose result-shape goes through
# the standard `_dispatch_table_result` helper. Same lambda signature
# as `_PUT_ROUTES`: `lambda m, payload`. Admin auth runs at do_POST
# function entry. Body read happens once in the dispatch loop (matches
# the PUT loop), and `_read_body() or {}` makes empty-body POSTs
# (e.g. snapshot restore) work transparently.
#
# Out of scope for A.7 (deferred to A.8 — bespoke cleanup):
# - /api/sources/cache/_all/fetch and /api/sources/cache/<id>/fetch
#   (use `_send_dict_result` which preserves extras in error envelopes
#   — they need either an extension to `_dispatch_table_result` or a
#   dedicated `_POST_DICT_RESULT_ROUTES` table, both judgment calls
#   best deferred).
# - 3 multipart routes (cover main, cover book, sources cache upload)
#   — these read the raw body, not JSON; they need a `_MULTIPART_ROUTES`
#   table with a distinct lambda signature `lambda m, body, ctype` and
#   their own dispatch loop. Separate slice.
_POST_ROUTES: list[tuple[re.Pattern, "object"]] = [
    # /api/snapshots/<ed>/<ver>/restore — no payload; status==error
    # envelope. MUST precede /api/snapshots/<ed> (more specific).
    (
        re.compile(r"^/api/snapshots/([a-z0-9._-]+)/([a-z0-9._-]+)/restore$"),
        lambda m, payload: api_snapshot_restore(m.group(1), m.group(2)),
    ),
    # /api/snapshots/<ed> — create; payload pass-through; status==error
    (
        re.compile(r"^/api/snapshots/([a-z0-9._-]+)$"),
        lambda m, payload: api_snapshot_create(m.group(1), payload),
    ),
    # /api/matrix/apply-kind-to-all — payload destructure; status==error
    (
        re.compile(r"^/api/matrix/apply-kind-to-all$"),
        lambda m, payload: api_apply_kind_to_all_editions(
            payload.get("kind") or "",
            enable=bool(payload.get("enable")),
        ),
    ),
    # /api/scenarios/_import — payload destructure; status==error
    (
        re.compile(r"^/api/scenarios/_import$"),
        lambda m, payload: api_import_scenario_yaml(
            payload.get("yaml") or "",
            name=payload.get("name") or None,
            overwrite=bool(payload.get("overwrite")),
        ),
    ),
    # /api/editions/clone — payload pass-through; uses ok:False envelope
    (
        re.compile(r"^/api/editions/clone$"),
        lambda m, payload: api_clone_edition(payload),
    ),
    # /api/backups/restore — payload destructure; status==ok|error
    (
        re.compile(r"^/api/backups/restore$"),
        lambda m, payload: api_restore_backup(
            payload.get("file") or "",
            payload.get("snapshot_id") or "",
        ),
    ),
    # ο.4 — /api/archive-org/upload/<edition> — compose press-kit
    # ZIP + S3-style PUT to archive.org + auto-mark distribution
    # cell. Payload reserved for future options (currently {}).
    # Returns ok:True on success (200/2xx from archive.org) or
    # standard {status:error, code, http, message} envelope on
    # missing credentials / unknown edition / upload failure.
    (
        re.compile(r"^/api/archive-org/upload/([a-z0-9-]+)$"),
        lambda m, payload: api_archive_org_upload(m.group(1), payload),
    ),
    # ξ.21 — 2FA enrollment flow (begin → confirm → disable).
    (
        re.compile(r"^/api/auth/totp/begin$"),
        lambda m, payload: api_auth_totp_begin(payload),
    ),
    (
        re.compile(r"^/api/auth/totp/confirm$"),
        lambda m, payload: api_auth_totp_confirm(payload),
    ),
    (
        re.compile(r"^/api/auth/totp/disable$"),
        lambda m, payload: api_auth_totp_disable(payload),
    ),
    # ω.35-A.8 — sources/cache fetch routes. Previously used
    # `_send_dict_result` (which preserved extras in error
    # envelopes). Now table-compatible because A.8 extended
    # `_dispatch_table_result` to preserve extras too. MORE-
    # SPECIFIC /<id>/fetch must precede the broader _all/fetch
    # match isn't a concern here (paths are distinct), but
    # convention pinned.
    # /api/sources/cache/_all/fetch — payload "force"; status==ok|error
    (
        re.compile(r"^/api/sources/cache/_all/fetch$"),
        lambda m, payload: api_sources_cache_fetch_all(
            force=bool(payload.get("force")),
        ),
    ),
    # /api/sources/cache/<id>/fetch — payload force/url_override/parser_override
    (
        re.compile(r"^/api/sources/cache/([a-z0-9_-]+)/fetch$"),
        lambda m, payload: api_sources_cache_fetch(
            m.group(1),
            force=bool(payload.get("force")),
            url_override=payload.get("url_override") or None,
            parser_override=payload.get("parser_override") or None,
        ),
    ),
]


# ω.35-A.9 (2026-05-11) — eighth slice of the route-table migration.
# `_MULTIPART_ROUTES` covers POST routes that take a multipart body
# instead of JSON. Distinct entry shape: 3-tuple
# `(regex, max_bytes, lambda m, body, content_type)` because the
# body is bytes (not parsed dict) and the per-route size cap differs
# (cover uploads = 10 MB; source cache uploads = 50 MB).
#
# The hard cap stored here is the per-file limit; the dispatch loop
# multiplies by 2 before rejecting (matches the legacy pattern's
# "twice the per-file limit so a hostile client can't tie up the
# server with an unbounded read" comment).
#
# Handlers return the standard `{ok, ...}` or `{status, ...}` dict
# shape and route through `_dispatch_table_result` like the other
# tables — uniform on the response side.
_MULTIPART_ROUTES: list[tuple[re.Pattern, int, "object"]] = [
    # /api/covers/<ed>/main — cover upload (main hero cover)
    (
        re.compile(r"^/api/covers/([a-z0-9-]+)/main$"),
        COVERS_UPLOAD_MAX_BYTES,
        lambda m, body, ctype: api_upload_cover_main(m.group(1), body, ctype),
    ),
    # /api/covers/<ed>/book/<book> — cover upload (per-book cover).
    # MUST precede /api/covers/<ed>/main if both could match — they
    # don't here (different suffixes) but the discipline is pinned.
    (
        re.compile(r"^/api/covers/([a-z0-9-]+)/book/([a-z0-9]+)$"),
        COVERS_UPLOAD_MAX_BYTES,
        lambda m, body, ctype: api_upload_cover_book(m.group(1), m.group(2), body, ctype),
    ),
    # /api/sources/cache/<id>/upload — drag-drop JSON cache upload
    (
        re.compile(r"^/api/sources/cache/([a-z0-9_-]+)/upload$"),
        SOURCES_UPLOAD_MAX_BYTES,
        lambda m, body, ctype: api_sources_cache_upload(m.group(1), body, ctype),
    ),
    # ε.3 — /api/sales/import/<channel> — CSV upload of per-channel
    # sales (KDP / Apple / Google). Channel is validated server-side
    # against sales.KNOWN_CHANNELS; rows emit sales_record events.
    (
        re.compile(r"^/api/sales/import/([a-z]+)$"),
        SALES_UPLOAD_MAX_BYTES,
        lambda m, body, ctype: api_sales_import(m.group(1), body, ctype),
    ),
]


def _dispatch_multipart_route(
    handler_self,
    match: "re.Match",
    max_bytes: int,
    handler: "object",
) -> None:
    """ω.35-A.9 helper — read a multipart body within a per-route
    size cap and route the result through the standard dispatch
    helper. Consolidates the boilerplate that was duplicated in
    `_handle_cover_upload` and `_handle_sources_cache_upload`:
    parse Content-Length → validate int → reject > 2 * max_bytes
    → read body → call handler(match, body, content_type) →
    `_dispatch_table_result`. Any error path returns 400 with
    `{error: str}` (matches legacy)."""
    try:
        length_header = handler_self.headers.get("Content-Length", "")
        try:
            length = int(length_header)
        except ValueError:
            return handler_self._send_json(
                {"error": "missing or invalid Content-Length"},
                status=400,
            )
        # Hard cap at twice the per-file limit (defensive against a
        # hostile client streaming an unbounded body).
        cap = max_bytes * 2
        if length > cap:
            return handler_self._send_json(
                {"error": f"request too large: {length} bytes (max {cap})"},
                status=413,
            )
        body = handler_self.rfile.read(length) if length > 0 else b""
        content_type = handler_self.headers.get("Content-Type", "")
        result = handler(match, body, content_type)
        return _dispatch_table_result(handler_self, result)
    except Exception as e:
        return handler_self._send_json({"error": str(e)}, status=400)


def _dispatch_table_result(handler_self, result: dict) -> None:
    """ω.35-A.2 helper — translate a handler dict result to an HTTP
    response, mirroring the boilerplate that appeared 10+ times in
    the legacy cascade.

    Three response shapes handled:
    1. `{"status": "error", "code": ..., "http": ..., "message": ...,
       <extras>}` — translated to JSON error envelope with appropriate
       HTTP status. (ω.35-A.2 introduced this for the GET tables.
       ω.35-A.8 added extras-preservation so handlers that include
       additional fields in their error envelope — e.g.
       `api_sources_cache_fetch_all` returning `"results": []` on
       config error — match the legacy `_send_dict_result` behavior.)
    2. `{"ok": False, ...}` — legacy mutation-result shape used by
       api_save_edition / api_save_scenario / api_save_kind etc.
       Sends the raw result with HTTP 400. (ω.35-A.5 added this for
       the PUT/DELETE tables; preserves the legacy
       `status = 200 if result.get("ok") else 400` pattern.)
    3. Any other dict — sent as 200. Covers the `{"ok": True, ...}`
       success shape AND handlers that return bare result dicts
       without the ok-or-status discriminator (e.g. api_save's
       happy path returns `{"ok": True, ...}`; its error path
       returns `{"error": ..., "book": ...}` with no `ok` key —
       both go through as 200, matching legacy behavior).
    """
    if result.get("status") == "error":
        envelope = {
            "error": result.get("code") or "internal_error",
            "message": result.get("message") or "",
        }
        # ω.35-A.8 — preserve any extras (fields beyond the standard
        # status/code/http/message) so behavior matches the legacy
        # `_send_dict_result` helper. None of the routes migrated
        # before A.8 return extras in error envelopes (verified via
        # grep across all `"status": "error"` returns), so this
        # extension is behavior-neutral for them.
        for k, v in result.items():
            if k not in ("status", "code", "http", "message", "error"):
                envelope[k] = v
        handler_self._send_json(envelope, status=result.get("http") or 500)
        return
    if result.get("ok") is False:
        handler_self._send_json(result, status=400)
        return
    handler_self._send_json(result)


class Handler(BaseHTTPRequestHandler):
    # ξ.3 — security response headers. Applied to every HTML + JSON
    # response via _send_security_headers below.
    #
    # CSP rationale:
    #   default-src 'self'         — only same-origin loads
    #   script-src ... 'unsafe-inline' https://cdn.tailwindcss.com
    #                              — inline <script> blocks + the
    #                                Tailwind Play CDN are intentional
    #                                (CLAUDE_PROJECT_RULES §6.3 — no
    #                                build step). Tighten in a future
    #                                ξ phase if we move to bundled JS.
    #   style-src ... 'unsafe-inline' https://cdn.tailwindcss.com
    #                              — Tailwind injects styles at runtime
    #                                from the CDN; inline <style> blocks
    #                                are also intentional.
    #   img-src 'self' data:       — uploaded covers + data: URLs for
    #                                small icons.
    #   frame-ancestors 'none'     — forbid embedding /matrix etc. in
    #                                iframes (prevents clickjacking).
    #   base-uri 'self'            — block <base> tag injection.
    #   form-action 'self'         — submissions stay same-origin.
    _CSP_POLICY = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
        "img-src 'self' data:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )

    # ξ.18 (2026-05-12) — per-request nonce regex. Inserts
    # `nonce="<value>"` into every `<script` tag that doesn't already
    # carry one. Anchored on `<script` followed by a tag-attribute
    # boundary character (space, slash, or `>`); `<scripts>` and
    # `<scripting>` deliberately don't match.
    _SCRIPT_TAG_RE = re.compile(r"<script(?![a-zA-Z0-9-_])")

    @staticmethod
    def _generate_nonce() -> str:
        """Fresh CSP nonce per request. 16 bytes of os.urandom → base64
        url-safe encoding → 22-char string. RFC 8941 recommends ≥128
        bits of entropy for CSP nonces; 16 bytes (128 bits) satisfies."""
        return secrets.token_urlsafe(16)

    @classmethod
    def _csp_with_nonce(cls, nonce: str) -> str:
        """Return the strict CSP for an HTML response with this nonce.
        Drops `'unsafe-inline'` from `script-src` and adds the per-
        request `'nonce-<value>'` so every inline `<script>` block in
        the rendered HTML must carry the matching nonce attribute.

        `style-src` keeps `'unsafe-inline'` for now — Tailwind's Play
        CDN injects styles at runtime; tightening style-src is a
        separate ξ phase (style-src nonces require a Tailwind-build
        migration, which conflicts with §6.3 'no build step').
        """
        return (
            "default-src 'self'; "
            f"script-src 'self' 'nonce-{nonce}' https://cdn.tailwindcss.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
            "img-src 'self' data:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

    @classmethod
    def _inject_script_nonces(cls, html: str, nonce: str) -> str:
        """Add `nonce="<value>"` to every `<script` tag in `html` that
        doesn't already carry one. Pure function — html and nonce
        passed in, transformed html returned.

        Variant coverage:
            <script>            → <script nonce="X">
            <script src="...">  → <script nonce="X" src="...">
            <script async>      → <script nonce="X" async>
            <script\\nsrc="...">  → <script nonce="X"\\nsrc="..."> (preserves
                                                            internal whitespace)

        Tags that already have a `nonce=` attribute are skipped — the
        regex's lookahead requires a non-name boundary character right
        after `<script`, and the replacement adds the attribute
        prefix, so re-running the helper on already-noncified HTML is
        a no-op for any tag with an existing nonce."""

        def add_nonce(match: re.Match) -> str:
            return f'<script nonce="{nonce}"'

        # Skip tags that already have nonce="" (idempotent).
        # We accomplish this by limiting the regex to <script tags
        # without `nonce=` in the next 200 chars — but that requires
        # lookahead. Simpler: post-process to dedupe nonce attrs.
        result = cls._SCRIPT_TAG_RE.sub(add_nonce, html)
        # Collapse duplicate nonce attrs (defensive against caller
        # re-noncifying already-noncified HTML).
        if "nonce=" in html:
            result = re.sub(
                rf'<script nonce="{re.escape(nonce)}" nonce="[^"]+"',
                f'<script nonce="{nonce}"',
                result,
            )
        return result

    def _send_security_headers(self, *, nonce: str | None = None):
        """ξ.3 + ξ.18 — add CSP + nosniff + Referrer-Policy headers.

        Called by every response helper (_send_html, _send_json,
        _send_file, plus inline routes that build their own header
        block). Tailwind CDN is allow-listed; everything else is
        same-origin. Frame-ancestors blocks clickjacking.

        ξ.18 (2026-05-12): when `nonce` is provided, emit the strict
        CSP that requires `nonce-<value>` on every inline script
        instead of `'unsafe-inline'`. JSON / file / zip responses
        pass nonce=None (no inline scripts in those responses) and
        keep the legacy policy as defense-in-depth.
        """
        policy = self._csp_with_nonce(nonce) if nonce else self._CSP_POLICY
        self.send_header("Content-Security-Policy", policy)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._send_security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_unhandled_error(self, exc: Exception, method_name: str = "?"):
        """ω.8 — last-resort error path. Logs the traceback to stderr
        for the operator (the existing log_message convention) and
        returns a structured 500 JSON to the client. Critically, the
        client never sees a Python stack trace — that's both an
        information-disclosure concern and an unfriendly UX."""
        import traceback

        # Log full detail to stderr — useful for operators tailing
        # the dev server; the existing log_message format is short
        # so we drop straight to stderr for tracebacks.
        sys.stderr.write(f"  [unhandled {method_name}] {type(exc).__name__}: {exc}\n")
        traceback.print_exc(file=sys.stderr)
        try:
            return self._send_json(
                {
                    "error": "internal_error",
                    "message": (f"unhandled {type(exc).__name__} in {method_name}; see server log for details"),
                },
                status=500,
            )
        except Exception:
            # If even the JSON send fails (broken pipe, etc.), there's
            # nothing else to do — the request is gone.
            pass

    def _send_dict_result(self, result: dict):
        """§9 'pure function + thin route adapter' — translate a
        result dict ({status, code?, http?, message?, ...}) into an
        HTTP response. Reused by any endpoint following that shape."""
        if result.get("status") == "ok":
            return self._send_json(result)
        http_code = result.get("http") or 500
        return self._send_json(
            {
                "error": result.get("code") or "internal_error",
                "message": result.get("message") or "",
                **{k: v for k, v in result.items() if k not in ("status", "code", "http", "message")},
            },
            status=http_code,
        )

    def _send_html(self, html: str):
        # ξ.18 — fresh per-request nonce + noncified body + strict CSP.
        nonce = self._generate_nonce()
        noncified = self._inject_script_nonces(html, nonce)
        body = noncified.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_security_headers(nonce=nonce)  # ξ.3 + ξ.18
        self.end_headers()
        self.wfile.write(body)

    def _send_zip(self, filename: str, data: bytes):
        """ε.7 — serve a ZIP as an attachment download. Filename is
        sanitized to ASCII-safe characters via the standard simple
        filter (alphanumerics + dash + underscore + dot); anything
        else collapses to underscore so the Content-Disposition header
        stays well-formed across browsers."""
        safe_name = "".join(c if (c.isalnum() or c in "._-") else "_" for c in filename) or "download.zip"
        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Content-Disposition", f'attachment; filename="{safe_name}"')
        self.send_header("Cache-Control", "no-store")
        self._send_security_headers()
        self.end_headers()
        self.wfile.write(data)

    def _send_file(self, path: Path, content_type: str | None = None):
        """Serve a binary file (cover images etc.). Path must already
        be confirmed safe by the caller — this helper does NOT
        re-validate path traversal, since the route is responsible
        for sandboxing to a known-safe directory."""
        try:
            data = path.read_bytes()
        except OSError:
            return self._send_json({"error": "file not found"}, status=404)
        if content_type is None:
            # ξ.16 SEC-001 — restrict served images to the same
            # allowlist the upload validator accepts (png/jpeg/webp).
            # Critically, drop SVG and GIF: SVG is XML and renders
            # inline `<script>` / `on*` handlers when navigated to
            # directly, which would XSS the localhost origin from the
            # /content/covers/ same-origin route. Verify magic bytes
            # match the extension — a hostile file dropped under
            # content/covers/ (via backup restore, scenario import,
            # or hand placement) cannot be served as an image.
            from scripts.core.covers import UPLOAD_ALLOWED_FORMATS, _detect_format

            ext = path.suffix.lower().lstrip(".")
            ext_norm = "jpeg" if ext == "jpg" else ext
            fmt = _detect_format(data[:32], ext)
            if fmt not in UPLOAD_ALLOWED_FORMATS or ext_norm not in UPLOAD_ALLOWED_FORMATS:
                return self._send_json({"error": "unsupported media type"}, status=415)
            if fmt != ext_norm:
                # Magic bytes disagree with extension — refuse to
                # serve. The route is read-only so we can't fix the
                # disk state from here; the upload pipeline is
                # responsible for never letting this combination land.
                return self._send_json({"error": "format/extension mismatch"}, status=415)
            content_type = {
                "jpeg": "image/jpeg",
                "png": "image/png",
                "webp": "image/webp",
            }[fmt]
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        # ξ.16 SEC-010 — `private` not `public`: the localhost app has
        # no shared cache, but if a user binds --host 0.0.0.0 with a
        # corporate proxy on path, public would let the proxy cache
        # private editorial content.
        self.send_header("Cache-Control", "private, max-age=60")
        self._send_security_headers()  # ξ.3
        # ξ.16 SEC-001 — extra defense: even with the magic-byte
        # check above, sandbox the response. `default-src 'none'`
        # blocks every subresource fetch the image-as-document
        # would attempt; `sandbox` blocks scripts/forms/popups in
        # browsers that respect it.
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; sandbox; img-src 'self'",
        )
        self.end_headers()
        self.wfile.write(data)

    # ξ.16 SEC-002 — generous cap on JSON body size. Every legitimate
    # JSON payload on this server is well under 1 MB (kind toggles,
    # edition meta, scenarios, audit reads). 32 MB gives 30× headroom
    # for the largest plausible legit payload while still rejecting a
    # 2 GB Content-Length attack BEFORE allocation. The size check
    # comes BEFORE self.rfile.read() — no allocation happens for an
    # over-cap request.
    JSON_BODY_MAX_BYTES = 32 * 1024 * 1024

    def _read_body(self) -> dict:
        length_header = self.headers.get("Content-Length") or "0"
        try:
            length = int(length_header)
        except ValueError:
            raise ValueError("invalid Content-Length")
        if length < 0:
            raise ValueError("negative Content-Length")
        if not length:
            return {}
        if length > self.JSON_BODY_MAX_BYTES:
            # ξ.16 SEC-002 — reject the request BEFORE allocating
            # `length` bytes. Existing per-route `except Exception
            # as e: return self._send_json({"error": str(e)},
            # status=400)` translates this to a 400 with the
            # message; importantly, no buffer allocation, no DoS.
            raise ValueError(f"request body too large: {length} bytes (max {self.JSON_BODY_MAX_BYTES})")
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def _check_admin_auth(self) -> bool:
        """Phase ω.4 + ξ.21 — auth gate for mutation endpoints.

        Two factors compose:

          - **Factor 1 — admin token** (``EBIBLE_ADMIN_TOKEN`` env
            var). Unset → factor 1 not required. Set → caller must
            present a matching token.
          - **Factor 2 — TOTP** (enrolled via ξ.21's `/api/auth/totp/*`
            endpoints). Disabled → factor 2 not required. Enabled →
            caller must present a current 6-digit code.

        ``Authorization`` header formats accepted (per active factors):

            Both factors enabled →  ``Authorization: Bearer <token>:<code>``
            Token only            →  ``Authorization: Bearer <token>``
            TOTP only             →  ``Authorization: Bearer :<code>``
                                     (token slot is empty)
            Neither               →  no header required (back-compat)

        GET / HEAD bypass this gate (read-only stays open even when
        the rest is locked down).

        Returns True when allowed; on False the 401 response has
        already been sent and the caller should return immediately.
        """
        token = os.environ.get("EBIBLE_ADMIN_TOKEN", "").strip()
        from scripts.core import auth as auth_core

        totp_enabled = auth_core.is_totp_enabled()
        if not token and not totp_enabled:
            return True  # auth disabled, back-compat default
        header = self.headers.get("Authorization", "")
        prefix = "Bearer "
        if not header.startswith(prefix):
            self._send_json(
                {"error": "missing Authorization: Bearer <token>[:<totp-code>] header"},
                status=401,
            )
            return False
        supplied = header[len(prefix) :].strip()
        # Parse "<token>:<code>" — split on the FIRST colon only so
        # tokens that themselves contain colons (e.g. base64-encoded
        # secrets) round-trip correctly.
        supplied_token, _, supplied_code = supplied.partition(":")
        import hmac

        if token:
            if not hmac.compare_digest(supplied_token, token):
                self._send_json({"error": "invalid admin token"}, status=401)
                return False
        # ξ.21 — if TOTP is enabled, require a matching code in addition
        # to (or instead of) the token.
        if totp_enabled:
            secret = auth_core.get_totp_secret()
            from scripts.core import totp as totp_mod

            if not secret or not totp_mod.verify_code(secret, supplied_code):
                self._send_json(
                    {"error": "invalid or missing TOTP code"},
                    status=401,
                )
                return False
        return True

    def log_message(self, fmt, *args):
        # Quieter than the default
        sys.stderr.write(f"  {self.address_string()} - {fmt % args}\n")

    # -------- routes --------

    @_safe_request
    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        # ω.35-A.1 — table-driven dispatch for the simplest JSON GET
        # routes. Falls through to the legacy if/elif cascade for
        # routes that don't fit (auth-gated, payload-reading, etc.).
        # See `_SIMPLE_GET_ROUTES` near the top of the file for
        # the migration contract and the drift-tolerance strategy.
        for route_path, handler in _SIMPLE_GET_ROUTES:
            if path == route_path:
                return self._send_json(handler())

        # ω.35-A.2 — regex routes with the standard
        # "handler(*groups) + error-translate" boilerplate.
        # Table order = precedence (more-specific before less).
        for regex, handler in _REGEX_GET_ROUTES:
            m = regex.match(path)
            if m:
                result = handler(*m.groups())
                return _dispatch_table_result(self, result)

        # ω.35-A.4 — regex routes with querystring parsing. Each
        # handler is `lambda m, qs: api_X(...)` — takes the match
        # and the parsed querystring dict, returns the response.
        # Routes through the same `_dispatch_table_result` helper
        # so the standard error-translate envelope still applies
        # uniformly.
        for regex, handler in _QS_REGEX_GET_ROUTES:
            m = regex.match(path)
            if m:
                qs = urllib.parse.parse_qs(url.query or "")
                result = handler(m, qs)
                return _dispatch_table_result(self, result)

        if path == "/" or path == "/index.html":
            return self._send_html(INDEX_HTML)
        if path == "/matrix" or path == "/matrix.html":
            return self._send_html(MATRIX_HTML)
        # ω.35-A.3 (2026-05-11) — deleted dead-code legacy branches
        # for the 14 simple + 3 regex routes migrated to
        # `_SIMPLE_GET_ROUTES` / `_REGEX_GET_ROUTES`. The table
        # dispatch loops at the top of this method handle them now.
        # The /api/snapshots/<ed>/<ver>/diff route stays here — it
        # needs querystring parsing (`?against=<ver>`) which the
        # current tables don't support; ω.35-A.4 will widen the
        # regex table to cover query-bearing routes.

        # ω.35-A.4 — /api/snapshots/<ed>/<ver>/diff migrated to
        # _QS_REGEX_GET_ROUTES.

        # ψ.27 — YAML export route. Place BEFORE the generic
        # /api/scenarios/<name> matcher so the .yaml suffix is matched
        # specifically (the suffix puts it outside the generic regex).
        m = re.match(r"^/api/scenarios/([a-z0-9_-]+)/export\.yaml$", path)
        if m:
            result = api_export_scenario_yaml(m.group(1))
            if result.get("status") == "error":
                return self._send_json(
                    {"error": result.get("code") or "internal_error", "message": result.get("message") or ""},
                    status=result.get("http") or 500,
                )
            yaml_text = result["yaml"]
            body = yaml_text.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/x-yaml; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header(
                "Content-Disposition",
                f'attachment; filename="{m.group(1)}.yaml"',
            )
            self._send_security_headers()  # ξ.3
            self.end_headers()
            self.wfile.write(body)
            return

        m = re.match(r"^/api/scenarios/([a-z0-9_-]+)$", path)
        if m:
            return self._send_json(api_get_scenario(m.group(1)))

        # Sources Navigator (Phase μ.3)
        if path == "/sources" or path == "/sources.html":
            return self._send_html(SOURCES_HTML)
        # PD source-cache management (Phase υ.1) — distinct from
        # /api/sources below, which navigates note attribution
        if path == "/api/sources/cache":
            return self._send_json(api_sources_cache_status())
        # ω.35-A.3 — /api/sources migrated to _SIMPLE_GET_ROUTES.
        if path == "/api/sources/summary":
            return self._send_json(api_sources_summary())
        # υ.3 — cross-edition note search. Read query + filters from
        # the URL query string; thin route adapter over api_search_notes.
        if path == "/api/search-notes":
            qs = urllib.parse.parse_qs(url.query or "")
            q = (qs.get("q") or [""])[0]
            ed = (qs.get("edition_id") or [""])[0] or None
            kf = (qs.get("kind") or [""])[0] or None
            bk = (qs.get("book") or [""])[0] or None
            try:
                lim = int((qs.get("limit") or ["100"])[0])
            except ValueError:
                lim = 100
            result = api_search_notes(
                q,
                edition_id=ed,
                kind=kf,
                book=bk,
                limit=lim,
            )
            if result.get("status") == "error":
                return self._send_json(
                    {"error": result.get("code") or "internal_error", "message": result.get("message") or ""},
                    status=result.get("http") or 500,
                )
            return self._send_json(result)
        m = re.match(r"^/api/sources/([a-z0-9]+)$", path)
        if m:
            return self._send_json(api_sources_for_book(m.group(1)))
        # υ.8 — verse-of-the-day feeds. JSON + RSS share the same
        # underlying picker. ?date=YYYY-MM-DD pins a specific day;
        # ?edition_id=<id> restricts to that edition's enabled kinds.
        if path == "/api/verse-of-day.json":
            qs = urllib.parse.parse_qs(url.query or "")
            d = (qs.get("date") or [""])[0] or None
            ed = (qs.get("edition_id") or [""])[0] or None
            result = api_verse_of_day(d, edition_id=ed)
            if result.get("status") == "error":
                return self._send_json(
                    {"error": result.get("code") or "internal_error", "message": result.get("message") or ""},
                    status=result.get("http") or 500,
                )
            return self._send_json(result)
        if path == "/api/verse-of-day.rss":
            qs = urllib.parse.parse_qs(url.query or "")
            ed = (qs.get("edition_id") or [""])[0] or None
            try:
                days = int((qs.get("days") or ["7"])[0])
            except ValueError:
                days = 7
            # ξ.16 SEC-003 — never reflect Host / X-Forwarded-Proto
            # verbatim into RSS link URLs. An attacker (LAN peer in
            # --host 0.0.0.0 mode, or a tab that gets the RSS reader
            # to fetch with crafted headers) can otherwise pin
            # `javascript://attacker.tld/...` or `https://evil.tld/...`
            # into syndicated feeds. Trust order:
            #   1. YHWH_PUBLIC_BASE_URL (operator-set, authoritative)
            #   2. Host header IFF it matches the localhost allowlist
            #   3. hardcoded fallback http://localhost
            base = _safe_rss_base_url(
                self.headers.get("X-Forwarded-Proto", "http"),
                self.headers.get("Host") or "",
            )
            xml, mime = api_verse_of_day_rss(
                days=days,
                base_url=base,
                edition_id=ed,
            )
            body = xml.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            # 1-hour cache (dates roll over once a day; 1h is conservative)
            self.send_header("Cache-Control", "public, max-age=3600")
            self._send_security_headers()  # ξ.3
            self.end_headers()
            self.wfile.write(body)
            return

        # Export (Phase σ.1 + σ.2)
        if path == "/export" or path == "/export.html":
            return self._send_html(EXPORT_HTML)
        m = re.match(r"^/api/export/preview/([a-z0-9-]+)$", path)
        if m:
            return self._send_json(api_export_preview(m.group(1)))
        m = re.match(r"^/api/export/download/([\w.-]+)$", path)
        if m:
            result = api_download_export(m.group(1))
            if isinstance(result, dict):
                return self._send_json(result, status=404)
            data, mime = result
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.send_header(
                "Content-Disposition",
                f'attachment; filename="{m.group(1)}"',
            )
            self._send_security_headers()  # ξ.3
            self.end_headers()
            self.wfile.write(data)
            return

        # Customize (Phase ν.1)
        if path == "/customize" or path == "/customize.html":
            return self._send_html(CUSTOMIZE_HTML)
        # ω.35-A.3 — /api/customize migrated to _SIMPLE_GET_ROUTES.

        # Attribution Audit (Phase ξ.4)
        if path == "/audit" or path == "/audit.html":
            return self._send_html(AUDIT_HTML)
        if path == "/api/audit/attribution":
            return self._send_json(api_attribution_audit())

        # Mutation Audit Log (Phase ξ.13)
        if path == "/audit-log" or path == "/audit-log.html":
            return self._send_html(AUDIT_LOG_HTML)
        # ω.35-A.4 — /api/audit-log migrated to _QS_REGEX_GET_ROUTES.

        # Per-note disable list for one edition (Phase ρ.1)
        m = re.match(r"^/api/edition/([a-z0-9-]+)/disabled-notes$", path)
        if m:
            return self._send_json(api_disabled_notes_for_edition(m.group(1)))

        # Publisher console (Phase π.1)
        if path == "/publisher" or path == "/publisher.html":
            return self._send_html(PUBLISHER_HTML)
        # ω.35-A.3 — /api/publisher migrated to _SIMPLE_GET_ROUTES.

        # Bible Builder Wizard (Phase π.5)
        if path == "/wizard" or path == "/wizard.html":
            return self._send_html(WIZARD_HTML)

        # Edition Diff View (Phase ξ.5) — read-only sales/demo tool
        if path == "/diff" or path == "/diff.html":
            return self._send_html(DIFF_HTML)
        # ω.35-A.4 — /api/diff migrated to _QS_REGEX_GET_ROUTES.

        # Translation comparison view (Phase ψ.4) — read-only side-
        # by-side renderer. Buyer demo without needing a full EPUB.
        if path == "/compare" or path == "/compare.html":
            return self._send_html(COMPARE_HTML)
        if path == "/api/compare":
            qs = urllib.parse.parse_qs(url.query or "")
            book = (qs.get("book") or ["gen"])[0]
            chapter_str = (qs.get("chapter") or ["1"])[0]
            try:
                chapter = int(chapter_str)
            except ValueError:
                chapter = 1
            # translations may come as repeated ?translations=kjv params
            # OR as a single comma-separated value
            translations: list = []
            for raw in qs.get("translations") or []:
                for piece in raw.split(","):
                    piece = piece.strip()
                    if piece:
                        translations.append(piece)
            # Sensible default: just KJV (the only translation we ship today)
            if not translations:
                translations = ["kjv"]
            return self._send_json(api_compare(book, chapter, translations))

        # Sample-chapter HTML export (Phase ψ.5) — buyer demo
        # without committing to a full EPUB build. URL pattern:
        #   /api/sample/<edition_id>?book=gen&from=1&to=3
        # Returns either text/html (200) or JSON error (404/400).
        # Spec discusses POST but GET is more idiomatic for a
        # read operation driven entirely by query params.
        if path.startswith("/api/sample/"):
            edition_id = path[len("/api/sample/") :].split("/", 1)[0]
            qs = urllib.parse.parse_qs(url.query or "")
            book = (qs.get("book") or [""])[0]
            from_str = (qs.get("from") or ["1"])[0]
            to_str = (qs.get("to") or [from_str])[0]
            try:
                from_n = int(from_str)
                to_n = int(to_str)
            except ValueError:
                # api_sample_html will surface its own error; pass
                # the originals through (it does its own int coercion)
                from_n, to_n = from_str, to_str
            translation = (qs.get("translation") or ["kjv"])[0]
            result = api_sample_html(
                edition_id,
                book,
                from_n,
                to_n,
                translation=translation,
            )
            if result.get("status") == "ok":
                return self._send_html(result["html"])
            # Error path — return JSON with the spec'd HTTP status
            http_code = result.get("http") or 500
            self.send_response(http_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            payload = json.dumps(
                {
                    "error": result.get("code") or "internal_error",
                    "message": result.get("message") or "",
                }
            ).encode("utf-8")
            self.wfile.write(payload)
            return

        # Backup listing (Phase ω.1) — surface the .backups/
        # snapshots that already exist. Path-traversal-safe; only
        # files inside content/ are addressable. Restore is POST
        # (see do_POST), this is GET-only.
        if path == "/api/backups":
            qs = urllib.parse.parse_qs(url.query or "")
            file_arg = (qs.get("file") or [""])[0]
            result = api_list_backups(file_arg)
            if result.get("status") == "ok":
                return self._send_json(result)
            http_code = result.get("http") or 500
            self.send_response(http_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    {
                        "error": result.get("code") or "internal_error",
                        "message": result.get("message") or "",
                    }
                ).encode("utf-8")
            )
            return

        # Per-book cover status (Phase π.4-A) — read-only feed for
        # the upcoming /covers UI. Returns each edition's main + per-book
        # cover slots, filtered by canon and sorted in canonical order.
        # ω.35-A.3 — /api/covers migrated to _SIMPLE_GET_ROUTES.

        # Pre-flight checklist (Phase ψ.2) — aggregator dashboard
        if path == "/preflight" or path == "/preflight.html":
            return self._send_html(PREFLIGHT_HTML)
        # ω.35-A.3 — /api/preflight migrated to _SIMPLE_GET_ROUTES.

        # Corpus progress widget (Phase ψ.3) — read-only feed for
        # the every-console progress bar. Cheap; composes the
        # already-cached api_attribution_audit.

        # Phase ω.0.2 — scaffolded route for /ops
        if path == "/ops" or path == "/ops.html":
            return self._send_html(OPS_HTML)
        # Phase ψ.6 — operator dashboard data feed
        # ω.35-A.3 — /api/ops migrated to _SIMPLE_GET_ROUTES.

        # Phase ω.0.2 — scaffolded route for /apihelp
        if path == "/apihelp" or path == "/apihelp.html":
            return self._send_html(APIHELP_HTML)

        # γ.1 — Hebrew interlinear console (Strong's Hebrew lookup).
        # The JSON endpoint /api/hebrew/<num> is in _REGEX_GET_ROUTES.
        if path == "/hebrew" or path == "/hebrew.html":
            return self._send_html(HEBREW_HTML)

        # ε.2 — /exec executive dashboard.
        # JSON endpoint /api/exec is in _SIMPLE_GET_ROUTES.
        if path == "/exec" or path == "/exec.html":
            return self._send_html(EXEC_HTML)

        # γ.2 — Greek interlinear console (Strong's Greek lookup).
        # The JSON endpoint /api/greek/<num> is in _REGEX_GET_ROUTES.
        if path == "/greek" or path == "/greek.html":
            return self._send_html(GREEK_HTML)
        # Phase ω.3 — API reference data feed (auto-generated)
        # ω.35-A.3 — /api/apihelp + /api/corpus-progress migrated to _SIMPLE_GET_ROUTES.

        # Cover console (Phase π.4-B UI). The image-upload flow lives
        # in do_POST; this route just serves the page shell.
        if path == "/covers" or path == "/covers.html":
            return self._send_html(COVERS_HTML)

        # Web favicon — serves the multi-resolution program icon
        # (.ico embedding 16/32/48/64/128/256 sizes) for browser
        # tabs + bookmarks. Sourced from assets/icons/ (publisher's
        # icon pack, ingested 2026-05-11). 24-hour public cache so
        # the browser doesn't re-fetch on every console nav.
        # See assets/icons/README.md for the full icon catalog.
        if path == "/favicon.ico":
            ico_path = REPO / "assets" / "icons" / "program_icon.ico"
            if not ico_path.is_file():
                return self._send_json({"error": "favicon missing"}, status=404)
            try:
                data = ico_path.read_bytes()
            except OSError:
                return self._send_json({"error": "favicon unreadable"}, status=404)
            self.send_response(200)
            self.send_header("Content-Type", "image/x-icon")
            self.send_header("Content-Length", str(len(data)))
            # Public cache OK — favicon is static + non-sensitive.
            self.send_header("Cache-Control", "public, max-age=86400")
            self._send_security_headers()
            self.end_headers()
            self.wfile.write(data)
            return

        # ψ.34 — static-asset route for the matrix console JS bundle.
        # Lives at scripts/templates/matrix_app.js after extraction
        # from the inline <script> block of MATRIX_HTML. Read-only;
        # served with `application/javascript`, the project security
        # headers, and a 5-minute private cache so navigations
        # between consoles don't re-fetch.
        if path == "/static/matrix.js":
            js_path = REPO / "scripts" / "templates" / "matrix_app.js"
            if not js_path.is_file():
                return self._send_json({"error": "not found"}, status=404)
            try:
                data = js_path.read_bytes()
            except OSError:
                return self._send_json({"error": "not found"}, status=404)
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "private, max-age=300")
            self._send_security_headers()
            self.end_headers()
            self.wfile.write(data)
            return

        # Static cover-image serving so the /covers UI can render
        # thumbnails. Sandboxed to content/covers/ ; any path that
        # tries to escape (.., absolute, hidden) is rejected with 404.
        # Read-only — uploads go through POST /api/covers/...
        if path.startswith("/content/covers/"):
            # ξ.2 — sandbox via shared safe_path helper. The string
            # after the route prefix is treated as a path RELATIVE
            # TO content/covers/.
            rel = path[len("/content/covers/") :]
            from scripts.core.safe_path import (
                SafePathError,
                resolve_under,
            )

            covers_root = REPO / "content" / "covers"
            try:
                file_path = resolve_under(covers_root, rel)
            except SafePathError:
                # 403/404-equivalent — don't disclose which check
                # failed. The §9 route-recipe convention.
                return self._send_json({"error": "forbidden"}, status=403)
            if not file_path.is_file():
                return self._send_json({"error": "not found"}, status=404)
            return self._send_file(file_path)

        # ε.7 — press-kit ZIP download. Returns binary (zipfile bytes)
        # so it can't go through the JSON-shaped route tables. Lives in
        # the legacy cascade by design.
        m = re.match(r"^/api/press-kit/([a-z0-9-]+)/download$", path)
        if m:
            result = build_press_kit_zip(m.group(1))
            if isinstance(result, tuple):
                filename, body = result
                return self._send_zip(filename, body)
            # Error envelope dict — JSON-translate via the standard helper.
            return _dispatch_table_result(self, result)

        m = re.match(r"^/api/notes/([a-z0-9]+)$", path)
        if m:
            return self._send_json(api_notes(m.group(1)))

        m = re.match(r"^/api/template/([\w-]+)$", path)
        if m:
            return self._send_json(api_template(m.group(1)))

        # ψ.7-B — list edition starter-pack templates
        # ω.35-A.3 — /api/edition-templates migrated to _SIMPLE_GET_ROUTES.

        # ψ.1.0 — live one-chapter preview
        # /api/preview/<edition>/<book>/<chapter>?translation=<id>
        m = re.match(
            r"^/api/preview/([a-z0-9-]+)/([a-z0-9]+)/(\d+)$",
            path,
        )
        if m:
            from urllib.parse import parse_qs, urlparse

            edition_id = m.group(1)
            book_code = m.group(2)
            try:
                chapter_int = int(m.group(3))
            except ValueError:
                return self._send_json(
                    {"error": "invalid_chapter"},
                    status=400,
                )
            qs = parse_qs(urlparse(self.path).query)
            translation_id = (qs.get("translation") or ["kjv"])[0]
            result = api_preview(
                edition_id,
                book_code,
                chapter_int,
                translation_id=translation_id,
            )
            if result.get("status") == "ok":
                return self._send_json(result)
            http_code = result.get("http") or 500
            return self._send_json(
                {
                    "error": result.get("code") or "internal_error",
                    "message": result.get("message") or "",
                },
                status=http_code,
            )

        self._send_json({"error": "not found", "path": path}, status=404)

    @_safe_request
    def do_PUT(self):
        if not self._check_admin_auth():
            return
        # ω.35-A.5/A.10 — table-driven dispatch for uniform-shape
        # PUT routes (regex → read body → call handler →
        # _dispatch_table_result → send_json). After A.10 the table
        # covers 9 of 10 PUT routes; the 3 remaining bespoke routes
        # below have semantically-distinct response shapes that
        # don't fit the standard helper:
        #   - /api/export/build/<id> uses HTTP 500 on build failure
        #     (server-side build error, not bad input)
        #   - /api/build-all uses HTTP 500 only when ALL editions
        #     fail (custom `success_count > 0` check; partial-ok
        #     is a real 200 outcome)
        #   - /api/edition-meta/<id>/preview uses a bare `"error"`
        #     key (no status/ok discriminator) — the helper can't
        #     distinguish error from success without additional
        #     introspection
        # Adapting them would require either modifying the API
        # functions' return shape (risky — UI may depend on the
        # current shape) or a wrapper helper per route (adds a
        # layer without saving meaningful code). Pinned bespoke.
        for regex, handler in _PUT_ROUTES:
            m = regex.match(self.path)
            if m:
                try:
                    payload = self._read_body()
                    result = handler(m, payload)
                    return _dispatch_table_result(self, result)
                except Exception as e:
                    return self._send_json({"error": str(e)}, status=400)
        # Bespoke #1 — Build edition (Phase σ.2). 500 on build
        # failure (not 400 — build is a server-side operation).
        m = re.match(r"^/api/export/build/([a-z0-9-]+)$", self.path)
        if m:
            try:
                payload = self._read_body()
                version = (payload or {}).get("version", "v28a")
                result = api_export_build(m.group(1), version=version)
                status = 200 if result.get("ok") else 500
                return self._send_json(result, status=status)
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)
        # Bespoke #2 — Build all editions (Phase ω.2). 500 only
        # when ALL editions fail; partial success is a real 200.
        if self.path == "/api/build-all":
            try:
                payload = self._read_body() or {}
                version = payload.get("version", "v28a")
                result = api_build_all_editions(version=version)
                status = 200 if result.get("success_count", 0) > 0 else 500
                return self._send_json(result, status=status)
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)
        # Bespoke #3 — Edition metadata change-impact preview
        # (Phase ν.5). Returns either a bare diff dict (success)
        # or `{"error": "..."}` (failure) — no status/ok marker.
        m = re.match(r"^/api/edition-meta/([a-z0-9-]+)/preview$", self.path)
        if m:
            try:
                payload = self._read_body()
                result = api_preview_edition_changes(m.group(1), payload)
                status = 200 if "error" not in result else 400
                return self._send_json(result, status=status)
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)
        # ω.35-A.10 — /api/edition-meta/<id>, /api/edition/<id>/
        # note-toggle, /api/editions/from-template migrated to
        # _PUT_ROUTES (above). /api/publisher/<id> was migrated
        # in A.5; the dead-code block previously kept for diff-
        # cleanliness has been deleted in A.10.
        return self._send_json({"error": "not found"}, status=404)

    @_safe_request
    def do_DELETE(self):
        if not self._check_admin_auth():
            return
        # ω.35-A.6/A.8 — table-driven dispatch for ALL 6 DELETE routes
        # (regex → handler(m) → _dispatch_table_result → send_json).
        # /api/sources/cache/<id> joined the table in A.8 once
        # _dispatch_table_result was extended to preserve extras in
        # error envelopes.
        for regex, handler in _DELETE_ROUTES:
            m = regex.match(self.path)
            if m:
                try:
                    result = handler(m)
                    return _dispatch_table_result(self, result)
                except Exception as e:
                    return self._send_json({"error": str(e)}, status=400)
        return self._send_json({"error": "not found"}, status=404)

    @_safe_request
    def do_POST(self):
        if not self._check_admin_auth():
            return
        # ω.35-A.7 — POST route-table dispatch. Covers:
        #   /api/snapshots/<ed>/<ver>/restore (no payload)
        #   /api/snapshots/<ed>               (create)
        #   /api/matrix/apply-kind-to-all
        #   /api/scenarios/_import
        #   /api/editions/clone
        #   /api/backups/restore
        # Body is read once here; routes that don't need a payload
        # (snapshot restore) accept the {} default. Any read failure
        # before pattern-match is a 400.
        payload: dict | None = None
        for pattern, handler in _POST_ROUTES:
            m = pattern.match(self.path)
            if not m:
                continue
            if payload is None:
                try:
                    payload = self._read_body() or {}
                except Exception as e:
                    return self._send_json({"error": str(e)}, status=400)
            return _dispatch_table_result(self, handler(m, payload))
        # ω.16 routes migrated to _POST_ROUTES (ω.35-A.7).
        # ψ.26 + ψ.27 routes migrated to _POST_ROUTES (ω.35-A.7).
        # ν.4 + ω.1 routes migrated to _POST_ROUTES (ω.35-A.7).
        # Source cache fetch routes (Phase υ.1) migrated to
        # _POST_ROUTES (ω.35-A.8) — `_dispatch_table_result` now
        # preserves extras in error envelopes, so the legacy
        # `_send_dict_result` behavior is preserved.
        # ω.35-A.9 — multipart POST routes (covers main, covers
        # book, sources cache upload) dispatched via
        # `_MULTIPART_ROUTES` with a per-route size cap.
        for pattern, max_bytes, handler in _MULTIPART_ROUTES:
            m = pattern.match(self.path)
            if m:
                return _dispatch_multipart_route(self, m, max_bytes, handler)
        # Everything else: same as PUT — front-end uses POST for create
        return self.do_PUT()


# ============================================================
# Single-page HTML  (Tailwind via CDN, vanilla JS, no build step)
# ============================================================


# ============================================================
# Matrix view (Phase μ.1) — read-only count grid in the browser
# ============================================================


# ============================================================
# Sources Navigator (Phase μ.3) — browse notes by book/chapter
# ============================================================


# ============================================================
# Export UI (Phase σ.1 + σ.2) — buyer-facing /export page
# ============================================================


# ============================================================
# Customize UI (Phase ν.1) — edit symbols + labels for cats/kinds
# ============================================================


# ============================================================
# Attribution Audit UI (Phase ξ.4) — quality control dashboard
# ============================================================


# ============================================================
# Publisher Console UI (Phase π.1)
# ============================================================


# ============================================================
# Bible Builder Wizard (Phase π.5) — the buyer-demo flow
# ============================================================


# ============================================================
# PREFLIGHT_HTML — Phase ψ.2 UI
# ============================================================
#
# /preflight console — single dashboard that aggregates every
# readiness check into a "ship-ready / not ready" view, with
# click-through links to the right console for each finding.
#
# Composes existing tools (api_attribution_audit, api_covers) plus
# a few in-process checks; new checks added in api_preflight()
# automatically render here without UI changes.


#
# /covers console — drag-drop cover upload per edition + per book.
#
# Layout per edition:
#   - hero "main cover" slot (large thumbnail or placeholder)
#   - canon-filtered grid of book slots in canonical order
#     (Rule §6.1 — from DATA.books_canonical, NEVER sorted client-side)
#
# Behavior:
#   - click a slot or drop a file → POST multipart to the upload
#     endpoint that already exists from π.4-B backend
#   - delete (×) on a populated slot → DELETE endpoint
#   - validation feedback inline; 400s render as red error banner
#   - thumbnails served via /content/covers/... (sandboxed file route)
#   - each upload is its own transactional API call — the backend
#     handles atomicity per-file (Rule from §9 mental model)


# Phase ψ.4 — Translation comparison view (/compare).
# Buyer-demo gold: side-by-side rendering of multiple translations
# for a given book + chapter, no full EPUB build required.
# Cross-linked into all 10 other consoles per Rule §6.2.


# Phase ω.0.2 — generated by scripts/scaffold_console.py.
# Console: /ops (Operator Dashboard)


# Phase ω.0.2 — generated by scripts/scaffold_console.py.
# Console: /apihelp (API Reference)


def _warm_corpus_index() -> dict:
    """Δ.9 — pre-build the derived corpus_index before the server
    starts handling requests so the first call doesn't pay the
    ~5s rebuild cost (51K notes × per-file parse). When the
    fingerprint already matches an existing on-disk index this is
    a fast no-op (sub-50ms — just a stat-walk + cached fingerprint
    compare).

    Best-effort: any failure logs a warning and returns a sentinel
    dict but does NOT propagate. The server should still start
    even if the index can't be built — first-request callers will
    fall back to file-walk paths and the next operator run can
    diagnose.

    Returns the rebuild() result dict (or `{"rebuilt": False,
    "error": str}` on failure) for callers that want to log the
    outcome themselves.
    """
    try:
        from scripts.core import corpus_index

        t0 = time.perf_counter()
        result = corpus_index.rebuild()
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        note_count = result.get("note_count", 0)
        if result.get("rebuilt"):
            print(f"  corpus_index: warmed ({note_count} notes, {elapsed_ms}ms)")
        else:
            print(f"  corpus_index: already fresh ({note_count} notes, {elapsed_ms}ms)")
        return result
    except Exception as exc:  # noqa: BLE001 — best-effort hook; never block server start
        print(f"  corpus_index: warm-up failed, will rebuild on first request: {exc}")
        return {"rebuilt": False, "error": str(exc)}


def main() -> int:
    p = argparse.ArgumentParser(description="Local web UI for the E-Bible note corpus.")
    p.add_argument("--host", default="127.0.0.1", help="bind address (default: 127.0.0.1, localhost-only)")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--no-browser", action="store_true", help="don't auto-open the browser")
    args = p.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.port}/"
    print("\n  E-Bible web — note editor")
    print(f"  serving at: {url}")
    print("  Ctrl-C to stop\n")

    # Δ.9 — pre-build the corpus_index BEFORE the first request
    # so cold-cache cost is paid here, not in a user-visible
    # 5s pause on the first /matrix or /api/search call.
    _warm_corpus_index()

    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  stopping…")
        server.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
