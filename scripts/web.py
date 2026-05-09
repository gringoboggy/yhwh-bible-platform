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

from scripts.core import config, html_utils, notes_io  # noqa: E402

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

@functools.lru_cache(maxsize=1024)
def _files_signature(*paths) -> tuple:
    """Return a stable (path, mtime_ns) tuple for a set of paths.

    Missing files contribute (path, 0) so disappearance also invalidates
    the cache. NOT lru_cached — must read fresh mtimes each call,
    otherwise an in-process write wouldn't be picked up by the
    derived-endpoint caches.
    """
    return _files_signature_impl(*paths)


def _files_signature_impl(*paths) -> tuple:
    sig = []
    for p in paths:
        path = Path(p)
        try:
            sig.append((str(path), path.stat().st_mtime_ns))
        except OSError:
            sig.append((str(path), 0))
    return tuple(sig)


# Override: the public name should NOT be lru_cached; rebind to the
# impl so callers pick up fresh mtimes each call.
_files_signature = _files_signature_impl


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
    return _compute_attribution_audit_uncached()

@functools.lru_cache(maxsize=16)
def _cached_edition_diff(a_id, b_id, eds_sig, kinds_sig, cats_sig,
                          canons_sig, books_sig, notes_sig):
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
    spec = importlib.util.spec_from_file_location(
        "_note_quality", REPO / "scripts" / "note_quality.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_new_note_helpers():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_new_note", REPO / "scripts" / "new_note.py")
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
        "ch": ch, "v": v, "suffix": suffix or "",
        "anchor": anchor or "", "kind": kind or "",
        "title": title or "", "label": label or "",
        "body": body or "",
        "attribution": attribution or {},
    }


def dict_to_tuple(d: dict) -> tuple:
    """Inverse: API JSON object → NOTES tuple."""
    return (
        int(d["ch"]), int(d["v"]),
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
            if tree.body and isinstance(tree.body[0], ast.Expr) \
               and isinstance(tree.body[0].value, ast.Constant):
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
        "findings": [
            {"check": f[5], "detail": f[6]} for f in findings
        ],
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
        out.append({
            "code": b["code"],
            "name": b.get("name", b["code"]),
            "bxx": b.get("bxx", ""),
            "strategy": b.get("strategy", ""),
            "ch_count": b.get("ch_count", 0),
            "note_count": len(notes),
            "kinds": kinds,
        })
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
        out.append({
            "code": code,
            "category": k.get("category", ""),
            "label": k.get("label", code),
            "phase": k.get("phase", ""),
            "description": k.get("description", ""),
            "budget": [lo, hi],
        })
    return {"kinds": out}


def api_template(kind: str) -> dict:
    """Return the per-kind scaffold template for a fresh note."""
    label, body, attribution = _nn().template_for(kind)
    return {"label": label, "body": body, "attribution": attribution}


def api_matrix() -> dict:
    """Return the symbol-toggle count grid as JSON. Read-only (μ.1)."""
    from scripts.core import matrix as matrix_mod
    m = matrix_mod.compute_matrix()
    cats = config.load_categories()
    kinds = config.load_kinds()
    editions = config.load_editions()
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
        "matrix": {
            ed_id: {
                "enabled": m.enabled[ed_id],
                "potential": m.potential[ed_id],
                "total_enabled": sum(m.enabled[ed_id].values()),
                "total_potential": sum(m.potential[ed_id].values()),
                "canon_books_count": len(m.edition_canon_books[ed_id]),
                "enabled_kinds_count": len(m.edition_enabled_kinds[ed_id]),
                "enabled_kinds_set": sorted(m.edition_enabled_kinds[ed_id]),
            }
            for ed_id in m.enabled
        },
    }


def _patch_edition_kind_lists(text: str, edition_id: str,
                                enabled_kinds: list[str],
                                disabled_kinds: list[str]) -> str:
    """Targeted regex update of one edition's enabled_kinds + disabled_kinds
    blocks in editions.yaml — preserves all comments, ordering, and other
    fields outside those blocks.

    Strategy: find the `  - id: <edition_id>` line, then modify the
    nearest following enabled_kinds: / disabled_kinds: blocks (or insert
    them after enabled_categories: if absent).
    """
    # Locate the edition block: from `  - id: <id>` to the next `  - id:`
    # or end of file. Body is "everything that follows" until the next
    # sibling `- id:` line at 2-space indent (or EOF). We use DOTALL so
    # the body matches across newlines including 4-space scalars and
    # 6-space list items both.
    block_re = re.compile(
        rf'(^  - id: {re.escape(edition_id)}\n)'
        rf'(.*?)'
        rf'(?=^  - id:|\Z)',
        re.MULTILINE | re.DOTALL,
    )
    m = block_re.search(text)
    if not m:
        raise ValueError(f"edition {edition_id!r} not found in editions.yaml")

    block_start, block_body, block_end = m.start(), m.group(2), m.end()

    def _format_list(name: str, items: list[str]) -> str:
        if not items:
            return f"    {name}: []\n"
        lines = "\n".join(f"      - {x}" for x in items)
        return f"    {name}:\n{lines}\n"

    # Replace or insert enabled_kinds:
    new_enabled = _format_list("enabled_kinds", enabled_kinds)
    enabled_re = re.compile(
        r"^(    enabled_kinds:.*?\n)((?:      - [^\n]+\n)*)",
        re.MULTILINE,
    )
    if enabled_re.search(block_body):
        new_body = enabled_re.sub(new_enabled, block_body, count=1)
    else:
        # insert after enabled_categories: block (or at end if absent)
        cats_re = re.compile(
            r"^(    enabled_categories:.*?\n(?:      - [^\n]+\n)*)",
            re.MULTILINE,
        )
        cm = cats_re.search(block_body)
        if cm:
            new_body = block_body[:cm.end()] + new_enabled + block_body[cm.end():]
        else:
            new_body = new_enabled + block_body

    # Replace or insert disabled_kinds:
    new_disabled = _format_list("disabled_kinds", disabled_kinds)
    disabled_re = re.compile(
        r"^(    disabled_kinds:.*?\n)((?:      - [^\n]+\n)*)",
        re.MULTILINE,
    )
    if disabled_re.search(new_body):
        new_body = disabled_re.sub(new_disabled, new_body, count=1)
    else:
        # insert after enabled_kinds: block we just placed
        ek_re = re.compile(
            r"^(    enabled_kinds:.*?\n(?:      - [^\n]+\n)*|    enabled_kinds: \[\]\n)",
            re.MULTILINE,
        )
        em = ek_re.search(new_body)
        if em:
            new_body = new_body[:em.end()] + new_disabled + new_body[em.end():]
        else:
            new_body = new_body + new_disabled

    return text[:block_start] + m.group(1) + new_body + text[block_end:]


def api_save_edition(edition_id: str, payload: dict) -> dict:
    """Persist a new enabled-kind state for one edition (μ.2).

    The frontend sends the full set of kinds it wants enabled. We diff
    against the edition's `enabled_categories` to compute minimal
    `enabled_kinds` (additions over the category baseline) and
    `disabled_kinds` (subtractions from the category baseline) — this
    preserves the YAML's authorial intent.
    """
    new_enabled_set = set(payload.get("enabled_kinds") or [])
    if not isinstance(new_enabled_set, set) or not all(
            isinstance(x, str) for x in new_enabled_set):
        return {"error": "enabled_kinds must be a list of strings"}

    editions_path = REPO / "content" / "editions.yaml"
    if not editions_path.is_file():
        return {"error": "editions.yaml missing"}

    # Look up the edition + validate
    editions = config.editions_by_id()
    if edition_id not in editions:
        return {"error": f"unknown edition: {edition_id}"}
    edition = editions[edition_id]

    # Validate that every requested kind exists in the registry
    known_kinds = {k["code"] for k in config.load_kinds()}
    unknown = new_enabled_set - known_kinds
    if unknown:
        return {"error": f"unknown kind(s): {sorted(unknown)}"}

    # Compute the category baseline (kinds enabled by category membership)
    enabled_cats = set(edition.get("enabled_categories") or [])
    baseline = {
        k["code"] for k in config.load_kinds()
        if k.get("category") in enabled_cats
    }
    # Minimal explicit lists
    new_enabled_kinds = sorted(new_enabled_set - baseline)
    new_disabled_kinds = sorted(baseline - new_enabled_set)

    # Patch the file
    text = editions_path.read_text(encoding="utf-8")
    try:
        new_text = _patch_edition_kind_lists(
            text, edition_id, new_enabled_kinds, new_disabled_kinds
        )
    except ValueError as e:
        return {"error": str(e)}

    # Atomic write + backup
    notes_io.ensure_backup(editions_path)
    notes_io.atomic_write(editions_path, new_text)

    # Invalidate caches so the next /api/matrix shows the change
    config.load_editions.cache_clear()
    from scripts.core import matrix as matrix_mod
    matrix_mod.compute_matrix.cache_clear()

    return {
        "ok": True,
        "edition": edition_id,
        "enabled_kinds": new_enabled_kinds,
        "disabled_kinds": new_disabled_kinds,
        "enabled_total": len(new_enabled_set),
    }


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
    return {"ok": True, "index": new_index,
            "quality": quality_for(book_code, new_tup)}


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
# Scenario API (Phase μ.2½) — named hypothetical edition profiles
# ============================================================


_SCENARIO_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,40}$")


def _scenario_path(name: str) -> Path:
    """Resolve a scenario name to its file path, validating safety."""
    if not _SCENARIO_NAME_RE.match(name):
        raise ValueError(
            f"invalid scenario name {name!r} — "
            f"use lowercase a-z, 0-9, -, _ (max 41 chars)"
        )
    return SCENARIOS_DIR / f"{name}.yaml"


def api_list_scenarios() -> dict:
    """List saved scenarios with their metadata."""
    if not SCENARIOS_DIR.is_dir():
        return {"scenarios": []}
    import yaml
    out = []
    for f in sorted(SCENARIOS_DIR.glob("*.yaml")):
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        out.append({
            "name": f.stem,
            "based_on": data.get("based_on"),
            "label": data.get("label", f.stem),
            "notes": data.get("notes", ""),
            "enabled_kinds": data.get("enabled_kinds") or [],
            "created": data.get("created"),
        })
    return {"scenarios": out}


def api_get_scenario(name: str) -> dict:
    """Return one scenario's full record."""
    try:
        path = _scenario_path(name)
    except ValueError as e:
        return {"error": str(e)}
    if not path.is_file():
        return {"error": f"scenario {name!r} not found"}
    import yaml
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        return {"error": f"corrupt scenario file: {e}"}
    return {"ok": True, "scenario": {"name": name, **data}}


def api_save_scenario(name: str, payload: dict) -> dict:
    """Create or overwrite a named scenario from the current toggle state.

    Scenarios live in content/scenarios/<name>.yaml — separate from
    editions.yaml. They store:
      - based_on: the edition id this scenario was forked from
      - label: human-readable name
      - notes: optional description
      - enabled_kinds: the explicit final set of enabled kind codes
      - created: ISO 8601 timestamp

    Saving DOES NOT modify editions.yaml or affect the build pipeline.
    Scenarios are exploration-only until promoted (future μ.2½ task).
    """
    try:
        path = _scenario_path(name)
    except ValueError as e:
        return {"error": str(e)}

    enabled_kinds = payload.get("enabled_kinds") or []
    if not isinstance(enabled_kinds, list) or not all(
            isinstance(x, str) for x in enabled_kinds):
        return {"error": "enabled_kinds must be a list of strings"}

    based_on = payload.get("based_on")
    if based_on is not None and based_on not in config.editions_by_id():
        return {"error": f"unknown based_on edition: {based_on}"}

    known_kinds = {k["code"] for k in config.load_kinds()}
    unknown = set(enabled_kinds) - known_kinds
    if unknown:
        return {"error": f"unknown kind(s): {sorted(unknown)}"}

    from datetime import datetime, timezone
    record = {
        "based_on": based_on,
        "label": payload.get("label") or name,
        "notes": payload.get("notes", ""),
        "enabled_kinds": sorted(set(enabled_kinds)),
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)

    # Use plain text rendering so we don't need ruamel; PyYAML's default
    # output is fine for these simple records (no comments to preserve).
    import yaml
    text = yaml.safe_dump(record, sort_keys=False, allow_unicode=True,
                          default_flow_style=False)
    if path.is_file():
        notes_io.ensure_backup(path)
    notes_io.atomic_write(path, text)

    return {"ok": True, "name": name, "path": str(path.relative_to(REPO))}


def api_delete_scenario(name: str) -> dict:
    """Remove a saved scenario file."""
    try:
        path = _scenario_path(name)
    except ValueError as e:
        return {"error": str(e)}
    if not path.is_file():
        return {"error": f"scenario {name!r} not found"}
    notes_io.ensure_backup(path)
    path.unlink()
    return {"ok": True, "removed": name}


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
        out.append({
            "code": b["code"],
            "title": b.get("title", b["code"]),
            "abbrev": b.get("abbrev", b["code"]),
            "section": b.get("section", ""),
            "ch_count": b.get("ch_count", 0),
            "note_count": len(notes or []),
            "sort_order": b.get("sort_order", 9999),
        })
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
        out.append({
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
        })
    # Already in canonical order in NOTES list, but enforce defensively
    out.sort(key=lambda n: (n["chapter"], n["verse"], n["suffix"]))
    return {
        "book": book_code,
        "title": book.get("title", book_code),
        "ch_count": book.get("ch_count", 0),
        "notes": out,
    }


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
        "top_attribution_strings": [
            {"source": s, "count": n} for s, n in top_sources
        ],
    }


# ============================================================
# Sources Cache API (Phase υ.1) — manage content/sources/ files:
# the PD-source cache that prospect.py + detectors read from.
# Distinct from the note-attribution navigator above (which lives
# under /api/sources/* and inspects per-note source strings).
# Reads the declarative config from υ.7's content/sources/_fetchers.json
# via scripts/core/fetcher_config.load_fetcher_config.
# ============================================================


# Maximum bytes accepted on a single source-cache JSON upload. The
# largest existing cache is TSK at ~5 MB; doubling that gives plenty
# of headroom for richer sources (commentary corpora, lexicons) that
# χ.* phases will add.
SOURCES_UPLOAD_MAX_BYTES = 50 * 1024 * 1024  # 50 MB


def _sources_cache_dir() -> Path:
    """Where the cache files live. Mirrors the constant in
    scripts/fetch_sources.py:SOURCES_DIR; kept as a function so tests
    can monkeypatch via a single attribute."""
    return REPO / "content" / "sources"


def _datetime_iso(ts: float) -> str:
    """Format a unix timestamp as a short ISO string for the UI grid."""
    import datetime
    return datetime.datetime.fromtimestamp(ts).isoformat(timespec="seconds")


def api_sources_cache_status() -> dict:
    """Status grid for the /sources console's PD-cache section.

    Returns one entry per source declared in _fetchers.json with its
    cache filename, current cached/not-cached status, file size and
    last-modified time (when present), and the candidate URL list so
    the UI can show 'tried these mirrors in order'.

    Composes load_fetcher_config (no new file scanning beyond stat
    calls per cache file) per the §9 'compose, don't recompute' rule.
    """
    from scripts.core.fetcher_config import (
        FetcherConfigError,
        load_fetcher_config,
    )
    try:
        cfg = load_fetcher_config()
    except FetcherConfigError as e:
        return {"status": "error", "code": "config_error",
                "http": 500, "message": str(e), "sources": []}

    cache_dir = _sources_cache_dir()
    out = []
    for s in cfg.sources:
        cache_path = cache_dir / s.cache_path
        if cache_path.is_file():
            stat = cache_path.stat()
            entry = {
                "id": s.id,
                "name": s.name,
                "cache_path": s.cache_path,
                "required": s.required,
                "license": s.license,
                "cached": True,
                "size_bytes": stat.st_size,
                "size_kb": round(stat.st_size / 1024, 1),
                "mtime_iso": _datetime_iso(stat.st_mtime),
            }
        else:
            entry = {
                "id": s.id,
                "name": s.name,
                "cache_path": s.cache_path,
                "required": s.required,
                "license": s.license,
                "cached": False,
                "size_bytes": 0,
                "size_kb": 0.0,
                "mtime_iso": None,
            }
        entry["candidates"] = [
            {"url": c.url, "parser": c.parser} for c in s.candidates
        ]
        out.append(entry)
    return {
        "status": "ok",
        "sources": out,
    }


def api_sources_cache_fetch(source_id: str, *,
                             force: bool = False,
                             url_override: str | None = None,
                             parser_override: str | None = None,
                             fetch_fn=None) -> dict:
    """Fetch one configured source. Returns the post-fetch status entry
    for that source plus an `ok` flag and a `message`.

    Injectable `fetch_fn` (signature ``(source, force) -> bool``) lets
    tests stub network calls. Defaults to the production
    ``scripts.fetch_sources.fetch_source``.

    `url_override` / `parser_override` let the caller try a single
    custom mirror without editing _fetchers.json — the user pastes a
    URL into /sources, picks a parser kind, and clicks Fetch. The
    other declared candidates are skipped for this single call.
    """
    from scripts.core.fetcher_config import (
        Candidate,
        FetcherConfigError,
        KNOWN_PARSERS,
        Source,
        load_fetcher_config,
    )

    try:
        cfg = load_fetcher_config()
    except FetcherConfigError as e:
        return {"status": "error", "code": "config_error",
                "http": 500, "message": str(e)}

    src = cfg.find(source_id)
    if src is None:
        return {"status": "error", "code": "unknown_source",
                "http": 404,
                "message": f"unknown source id: {source_id!r}"}

    if url_override is not None:
        if not isinstance(url_override, str) or not url_override.startswith(("http://", "https://")):
            return {"status": "error", "code": "invalid_url",
                    "http": 400,
                    "message": "url_override must be an http(s) URL"}
        parser_kind = parser_override or src.candidates[0].parser
        if parser_kind not in KNOWN_PARSERS:
            return {"status": "error", "code": "unknown_parser",
                    "http": 400,
                    "message": f"unknown parser: {parser_kind!r}"}
        # Build a one-off Source with only the override candidate.
        src = Source(
            id=src.id, name=src.name, cache_path=src.cache_path,
            required=src.required, license=src.license,
            candidates=(Candidate(url=url_override, parser=parser_kind),),
        )

    if fetch_fn is None:
        from scripts.fetch_sources import fetch_source as fetch_fn  # type: ignore

    ok = bool(fetch_fn(src, force))
    cache_path = _sources_cache_dir() / src.cache_path
    cached = cache_path.is_file()
    return {
        "status": "ok" if ok else "error",
        "ok": ok,
        "id": src.id,
        "cached": cached,
        "size_kb": round(cache_path.stat().st_size / 1024, 1) if cached else 0.0,
        "message": (
            f"fetched {src.cache_path}" if ok
            else f"all candidates failed for {src.cache_path}"
        ),
    }


def api_sources_cache_fetch_all(*, force: bool = False, fetch_fn=None) -> dict:
    """Fetch every configured source in order. Required-source failure
    is reported but doesn't short-circuit (so the user sees the full
    state after the run, not just the first failure)."""
    from scripts.core.fetcher_config import (
        FetcherConfigError,
        load_fetcher_config,
    )
    try:
        cfg = load_fetcher_config()
    except FetcherConfigError as e:
        return {"status": "error", "code": "config_error",
                "http": 500, "message": str(e), "results": []}

    results = []
    overall_ok = True
    for s in cfg.sources:
        r = api_sources_cache_fetch(s.id, force=force, fetch_fn=fetch_fn)
        results.append(r)
        if s.required and not r.get("ok"):
            overall_ok = False
    return {
        "status": "ok",
        "ok": overall_ok,
        "results": results,
    }


def api_sources_cache_upload(source_id: str, body: bytes,
                              content_type: str) -> dict:
    """Drag-drop upload of a pre-built JSON cache file.

    Validates: multipart parse → JSON parse → top-level shape
    (must be a JSON object, not a list — every cache file we ship
    is dict-shaped). Atomic write with backup of any existing file.
    Disk is never mutated on validation failure (§9 binary-asset
    pattern)."""
    from scripts.core.fetcher_config import (
        FetcherConfigError,
        load_fetcher_config,
    )
    try:
        cfg = load_fetcher_config()
    except FetcherConfigError as e:
        return {"status": "error", "code": "config_error",
                "http": 500, "message": str(e)}

    src = cfg.find(source_id)
    if src is None:
        return {"status": "error", "code": "unknown_source",
                "http": 404,
                "message": f"unknown source id: {source_id!r}"}

    if len(body) > SOURCES_UPLOAD_MAX_BYTES:
        return {"status": "error", "code": "too_large",
                "http": 413,
                "message": f"upload exceeds {SOURCES_UPLOAD_MAX_BYTES} bytes"}

    boundary = _extract_boundary(content_type)
    if boundary is None:
        return {"status": "error", "code": "missing_boundary",
                "http": 400,
                "message": "Content-Type header must include boundary=..."}

    parts = _parse_multipart(body, boundary)
    file_part = next((p for p in parts if p.get("filename")), None)
    if file_part is None:
        return {"status": "error", "code": "no_file_part",
                "http": 400,
                "message": "no file part in upload"}

    payload = file_part["data"]
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return {"status": "error", "code": "not_utf8",
                "http": 400,
                "message": "uploaded file is not valid UTF-8"}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        return {"status": "error", "code": "invalid_json",
                "http": 400,
                "message": f"not valid JSON: {e}"}
    if not isinstance(parsed, dict):
        return {"status": "error", "code": "wrong_shape",
                "http": 400,
                "message": "top-level JSON must be an object (dict)"}

    cache_dir = _sources_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / src.cache_path

    # ensure_backup before overwrite, atomic write of new content.
    if cache_path.is_file():
        notes_io.ensure_backup(cache_path)
    notes_io.atomic_write_bytes(cache_path, text.encode("utf-8"))

    return {
        "status": "ok",
        "ok": True,
        "id": src.id,
        "cached": True,
        "size_kb": round(cache_path.stat().st_size / 1024, 1),
        "message": f"uploaded {src.cache_path} ({len(payload)} bytes)",
    }


def api_sources_cache_clear(source_id: str) -> dict:
    """Delete the cache file for one source. Backs it up first via
    ensure_backup; the .backups/ directory keeps a copy so a
    mistaken click is recoverable."""
    from scripts.core.fetcher_config import (
        FetcherConfigError,
        load_fetcher_config,
    )
    try:
        cfg = load_fetcher_config()
    except FetcherConfigError as e:
        return {"status": "error", "code": "config_error",
                "http": 500, "message": str(e)}

    src = cfg.find(source_id)
    if src is None:
        return {"status": "error", "code": "unknown_source",
                "http": 404,
                "message": f"unknown source id: {source_id!r}"}

    cache_path = _sources_cache_dir() / src.cache_path
    if not cache_path.is_file():
        return {"status": "ok", "ok": True, "id": src.id,
                "cached": False, "message": "nothing to clear"}

    notes_io.ensure_backup(cache_path)
    cache_path.unlink()
    return {"status": "ok", "ok": True, "id": src.id,
            "cached": False, "message": f"cleared {src.cache_path}"}


# ============================================================
# Export API (Phase σ.1 + σ.2) — buyer-facing build & download
# ============================================================

EXPORTS_DIR = REPO / "exports"


def api_export_preview(edition_id: str) -> dict:
    """Pre-flight summary of what shipping `edition_id` will produce.

    The user-facing pitch: 'before you click Export, here's exactly
    what you're about to get — books, notes, kinds, file overview.'
    Powered by the matrix layer (μ.0) so counts are guaranteed
    consistent with what the build will actually emit.
    """
    from scripts.core import matrix as matrix_mod
    eds = config.editions_by_id()
    if edition_id not in eds:
        return {"error": f"unknown edition: {edition_id}"}
    edition = eds[edition_id]

    m = matrix_mod.compute_matrix()
    enabled = m.enabled.get(edition_id, {})
    potential = m.potential.get(edition_id, {})
    canon_books = m.edition_canon_books.get(edition_id, set())
    enabled_kinds = m.edition_enabled_kinds.get(edition_id, set())

    breakdown = matrix_mod.breakdown_by_category(edition_id)
    cats_idx = config.categories_by_id()
    cat_breakdown = []
    for cid in sorted(breakdown, key=lambda x: -breakdown[x]):
        c = cats_idx.get(cid, {})
        cat_breakdown.append({
            "id": cid,
            "label": c.get("label", cid),
            "symbol": c.get("symbol", "?"),
            "count": breakdown[cid],
        })

    filtered_out_kinds = []
    for kind_code, n in potential.items():
        if n > 0 and enabled.get(kind_code, 0) == 0:
            filtered_out_kinds.append({"kind": kind_code, "count": n})
    filtered_out_kinds.sort(key=lambda x: -x["count"])

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    pattern = f"Ethiopian_Bible_{edition_id}_*.epub"
    existing = sorted(EXPORTS_DIR.glob(pattern),
                      key=lambda p: p.stat().st_mtime, reverse=True)
    last_build = None
    if existing:
        f = existing[0]
        st = f.stat()
        last_build = {
            "filename": f.name,
            "size_kb": round(st.st_size / 1024),
            "mtime": st.st_mtime,
        }

    return {
        "edition": {
            "id": edition_id,
            "title": edition.get("title", edition_id),
            "short_title": edition.get("short_title", edition_id),
            "canon": edition.get("canon"),
            "isbn": edition.get("isbn", "—"),
            "target_audience": edition.get("target_audience", ""),
            "notes_field": edition.get("notes", ""),
        },
        "summary": {
            "books": len(canon_books),
            "kinds_enabled": len(enabled_kinds),
            "kinds_total": len(config.load_kinds()),
            "notes_shipping": sum(enabled.values()),
            "notes_potential": sum(potential.values()),
        },
        "category_breakdown": cat_breakdown,
        "filtered_out_kinds": filtered_out_kinds[:10],
        "last_build": last_build,
    }


def api_export_build(edition_id: str, version: str = "v28a") -> dict:
    """Run the build pipeline for `edition_id` and return a downloadable
    file reference. Wraps scripts/build_edition.py as a subprocess —
    same CLI tool that produces the actual retail EPUBs, so the buyer
    gets exactly what would ship in the existing pipeline.

    Build is synchronous (typically 10-30 seconds); the HTTP request
    blocks until the EPUB is ready or fails.
    """
    if edition_id not in config.editions_by_id():
        return {"error": f"unknown edition: {edition_id}"}

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    import subprocess
    cmd = [
        sys.executable,
        str(REPO / "scripts" / "build_edition.py"),
        edition_id,
        "--output-dir", str(EXPORTS_DIR),
        "--version", version,
        "--force",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO))
    if proc.returncode != 0:
        return {
            "error": "build failed",
            "returncode": proc.returncode,
            "stderr": proc.stderr[-2000:] if proc.stderr else "",
            "stdout_tail": proc.stdout[-500:] if proc.stdout else "",
        }

    pattern = f"Ethiopian_Bible_{edition_id}_{version}_*.epub"
    candidates = sorted(EXPORTS_DIR.glob(pattern),
                        key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        return {"error": "build reported success but no EPUB found"}

    out = candidates[0]
    st = out.stat()
    return {
        "ok": True,
        "filename": out.name,
        "size_kb": round(st.st_size / 1024),
        "size_mb": round(st.st_size / 1024 / 1024, 2),
        "download_url": f"/api/export/download/{out.name}",
        "build_log_tail": proc.stdout[-300:] if proc.stdout else "",
    }


# Phase ω.2 — Build-all-editions one-click. The buyer-demo arc:
# "click two buttons, get all your customized Bibles." Composes
# api_export_build per edition, collects results, packages successful
# EPUBs into a single zip. Per-edition errors don't abort the batch
# (spec requirement) — partial success is a real outcome and the
# UI surfaces which editions made it.
#
# Pattern: pure-function-API + thin route adapter (6th instance —
# §9 codification well overdue at this point).

def api_build_all_editions(
    *,
    version: str = "v28a",
    build_one=None,
) -> dict:
    """Build every configured edition, package successful outputs
    into a single combined zip, return per-edition status.

    Args:
        version: build version tag (passed through to build_one)
        build_one: callable(edition_id, version=...) → dict
                    Defaults to api_export_build. Tests inject a
                    mock to avoid real subprocess builds.

    Returns:
        {
          "ok": bool,                          # all editions succeeded?
          "zip_filename": str | None,          # combined zip name (None if 0 succeeded)
          "zip_size_mb": float | None,
          "download_url": str | None,
          "success_count": int,
          "fail_count": int,
          "total_count": int,
          "per_edition": [
            {"edition_id": str, "ok": bool, "filename": str | None,
             "size_mb": float | None, "error": str | None},
            ...
          ],
        }
    """
    if build_one is None:
        build_one = api_export_build

    eds = config.load_editions()
    edition_ids = [e["id"] for e in eds]

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    per_edition: list[dict] = []
    successful_files: list[Path] = []

    for ed_id in edition_ids:
        try:
            result = build_one(ed_id, version=version)
        except Exception as e:
            # Defensive: if build_one itself raises (e.g. internal
            # bug), log and continue. Don't abort the batch.
            per_edition.append({
                "edition_id": ed_id, "ok": False,
                "filename": None, "size_mb": None,
                "error": f"exception: {type(e).__name__}: {e}",
            })
            continue
        if result.get("ok"):
            per_edition.append({
                "edition_id": ed_id, "ok": True,
                "filename": result.get("filename"),
                "size_mb": result.get("size_mb"),
                "error": None,
            })
            fp = EXPORTS_DIR / result.get("filename", "")
            if fp.is_file():
                successful_files.append(fp)
        else:
            per_edition.append({
                "edition_id": ed_id, "ok": False,
                "filename": None, "size_mb": None,
                "error": result.get("error", "build failed"),
            })

    success_count = sum(1 for p in per_edition if p["ok"])
    fail_count = len(per_edition) - success_count

    # Package successful EPUBs into one zip. If zero succeeded,
    # skip — the UI shows the per-edition error list.
    zip_filename = None
    zip_size_mb = None
    download_url = None
    if successful_files:
        import zipfile
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        zip_name = f"All_Editions_{version}_{ts}.zip"
        zip_path = EXPORTS_DIR / zip_name
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for fp in successful_files:
                zf.write(fp, arcname=fp.name)
        st = zip_path.stat()
        zip_filename = zip_name
        zip_size_mb = round(st.st_size / 1024 / 1024, 2)
        download_url = f"/api/export/download/{zip_name}"

    return {
        "ok": fail_count == 0 and success_count > 0,
        "zip_filename": zip_filename,
        "zip_size_mb": zip_size_mb,
        "download_url": download_url,
        "success_count": success_count,
        "fail_count": fail_count,
        "total_count": len(edition_ids),
        "per_edition": per_edition,
    }


def api_download_export(filename: str) -> tuple[bytes, str] | dict:
    """Read a built export file from disk for streaming to the browser.

    Returns (bytes, mime) on success, or {"error": ...} on failure.
    Validates that the filename matches the expected build pattern so
    we never serve files outside the exports dir.
    """
    if not re.match(r"^Ethiopian_Bible_[a-z0-9-]+_[a-z0-9]+_[\dT\-:Z]+\.epub$",
                     filename):
        return {"error": "invalid export filename"}
    path = EXPORTS_DIR / filename
    if not path.is_file():
        return {"error": "file not found"}
    return (path.read_bytes(), "application/epub+zip")


# ============================================================
# Customization API (Phase ν.1) — edit symbols + labels for cats/kinds
# ============================================================


def _patch_yaml_entry(text: str, key_field: str, key_value: str,
                       updates: dict[str, str]) -> str:
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
        rf'(^  - {re.escape(key_field)}: {re.escape(key_value)}(?:\s|$).*?\n)'
        rf'(.*?)'
        rf'(?=^  - {re.escape(key_field)}:|\Z)',
        re.MULTILINE | re.DOTALL,
    )
    m = block_re.search(text)
    if not m:
        raise ValueError(
            f"entry {key_field}={key_value!r} not found in YAML"
        )
    head, body = m.group(1), m.group(2)

    new_body = body
    for field, new_val in updates.items():
        # Find existing `    <field>: ...` and replace its value
        field_re = re.compile(
            rf'^(    {re.escape(field)}:[ \t]*)(.*?)(\n)',
            re.MULTILINE,
        )
        # Decide quoting: leave bools/numbers/already-quoted strings alone,
        # otherwise wrap as a YAML double-quoted scalar for safety.
        if new_val in ("true", "false") or (
                isinstance(new_val, str) and new_val.startswith('"')) or (
                isinstance(new_val, str) and new_val.isdigit()):
            quoted = new_val
        elif new_val == "":
            quoted = '""'
        else:
            # Escape any embedded double-quotes
            esc = new_val.replace('\\', '\\\\').replace('"', '\\"')
            quoted = f'"{esc}"'
        if field_re.search(new_body):
            new_body = field_re.sub(
                lambda mm: f"{mm.group(1)}{quoted}{mm.group(3)}",
                new_body, count=1,
            )
        else:
            # Insert at the head of the body (after the key line)
            new_body = f"    {field}: {quoted}\n" + new_body

    return text[:m.start()] + head + new_body + text[m.end():]


def api_save_category(cat_id: str, payload: dict) -> dict:
    """Update symbol / label / description for one category."""
    cats = config.categories_by_id()
    if cat_id not in cats:
        return {"error": f"unknown category: {cat_id}"}

    updates = {}
    if "symbol" in payload:
        s = (payload["symbol"] or "").strip()
        if not s or len(s) > 4:
            return {"error": "symbol must be 1-4 visible chars"}
        updates["symbol"] = s
    if "label" in payload:
        lab = (payload["label"] or "").strip()
        if not lab:
            return {"error": "label cannot be empty"}
        if len(lab) > 60:
            return {"error": "label too long (max 60 chars)"}
        updates["label"] = lab
    if "description" in payload:
        updates["description"] = (payload["description"] or "").strip()
    if not updates:
        return {"error": "no updates supplied"}

    path = REPO / "content" / "categories.yaml"
    text = path.read_text(encoding="utf-8")
    try:
        new_text = _patch_yaml_entry(text, "id", cat_id, updates)
    except ValueError as e:
        return {"error": str(e)}

    notes_io.ensure_backup(path)
    notes_io.atomic_write(path, new_text)
    config.load_categories.cache_clear()
    from scripts.core import matrix as matrix_mod
    matrix_mod.compute_matrix.cache_clear()
    return {"ok": True, "id": cat_id, "updated": list(updates.keys())}


def api_save_kind(kind_code: str, payload: dict) -> dict:
    """Update symbol / label / description for one kind."""
    kinds = config.kinds_by_code()
    if kind_code not in kinds:
        return {"error": f"unknown kind: {kind_code}"}

    updates = {}
    if "symbol" in payload:
        s = (payload["symbol"] or "").strip()
        if not s or len(s) > 4:
            return {"error": "symbol must be 1-4 visible chars"}
        updates["symbol"] = s
    if "label" in payload:
        lab = (payload["label"] or "").strip()
        if not lab:
            return {"error": "label cannot be empty"}
        if len(lab) > 60:
            return {"error": "label too long (max 60 chars)"}
        updates["label"] = lab
    if "description" in payload:
        updates["description"] = (payload["description"] or "").strip()
    if not updates:
        return {"error": "no updates supplied"}

    path = REPO / "content" / "kinds.yaml"
    text = path.read_text(encoding="utf-8")
    try:
        new_text = _patch_yaml_entry(text, "code", kind_code, updates)
    except ValueError as e:
        return {"error": str(e)}

    notes_io.ensure_backup(path)
    notes_io.atomic_write(path, new_text)
    config.load_kinds.cache_clear()
    from scripts.core import matrix as matrix_mod
    matrix_mod.compute_matrix.cache_clear()
    return {"ok": True, "code": kind_code, "updated": list(updates.keys())}


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
        translations_list.append({
            "id": tid,
            "short_title": meta.get("short_title", tid.upper()),
            "title": meta.get("title", tid),
            "license": meta.get("license", ""),
        })
    # Phase ν.2.7-B — popup language registry + canonical book order.
    # Per CLAUDE_PROJECT_RULES.md §6.1, any per-book UI must list books
    # in books.yaml order (Genesis → Revelation → Apocrypha → Ethiopian
    # tail). The UI reads the order from this payload — never sorts on
    # its own — so the canonical-order rule has one source of truth.
    from scripts.build_edition import (
        POPUP_LANGUAGES, ALL_POPUP_LANGUAGES, decode_per_book_languages,
    )
    from scripts.core import matrix as _matrix
    books_canonical = [
        {"code": b["code"], "title": b.get("title", b["code"])}
        for b in config.load_books()
    ]
    popup_languages_registry = [
        {"id": lid, "label": POPUP_LANGUAGES[lid]["label"],
         "has_data": lid in {"english", "hebrew", "greek"}}
        for lid in ALL_POPUP_LANGUAGES
    ]
    # Canon membership per edition — lets the UI filter the books
    # list down to "only books in THIS edition" so a Tanakh edition
    # shows 39 rows and an Ethiopian shows 87.
    _mtx = _matrix.compute_matrix()
    edition_canon_books = {
        ed_id: sorted(books)
        for ed_id, books in _mtx.edition_canon_books.items()
    }
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
                "popup_languages_default": list(
                    e.get("popup_languages_default") or []
                ),
                # Decoded to a JSON-friendly dict for the UI; on-disk
                # this is a list of "code=lang1,lang2" strings.
                "popup_languages_per_book": decode_per_book_languages(
                    e.get("popup_languages_per_book")
                ),
                # Phase ψ.8.1 — list of tradition ids enabled for this
                # edition. Empty list (or absent) → include all
                # traditions (no-op, pre-ψ.8 build behavior preserved
                # per §7.2). Filter against TRADITION_IDS defensively
                # via _filter_traditions_default(); see that helper for
                # the YAML round-trip caveat.
                "traditions_default":
                    _filter_traditions_default(e.get("traditions_default")),
                "theme": e.get("theme", "classic"),
                "notes": e.get("notes", ""),
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
        "traditions": [
            {"id": tid, "label": label}
            for tid, label in _traditions_canonical_for_api()
        ],
        "books_canonical": books_canonical,
        "edition_canon_books": edition_canon_books,
    }


def _traditions_canonical_for_api() -> tuple[tuple[str, str], ...]:
    """Indirection for tests — exposes CANONICAL_TRADITIONS as a tuple
    of (id, label) pairs in canonical order. Tests can monkeypatch
    this without touching the underlying constant."""
    from scripts.core.traditions import CANONICAL_TRADITIONS
    return CANONICAL_TRADITIONS


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
        return (
            f"cover path must end in an image extension "
            f"({', '.join(sorted(allowed_ext))}): {s!r}"
        )
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
# Phase ψ.2 — Pre-flight checklist (composes existing checks)
# ============================================================
#
# Single API + single console that aggregates every quality / readiness
# check into one ship-ready dashboard. Composes existing tools
# (api_attribution_audit, api_covers) plus a few in-process checks
# that are too small to warrant their own endpoint.
#
# Each check returns the same shape so the UI can render uniformly:
#
#   {
#       "id":      machine-readable slug,
#       "name":    human-readable label,
#       "status":  "pass" | "warn" | "fail",
#       "message": one-line summary for the dashboard,
#       "details": list of dict (cap at ~10 for payload size),
#       "jump_to": URL of the console where this gets fixed,
#   }
#
# Adding a new check = appending to the list in api_preflight().
# Status order: any "fail" → not-ready; otherwise it ships.

def api_preflight() -> dict:
    """Run every preflight check and return a structured dashboard
    payload (Phase ψ.2). Cached cheaply via the same mtime-keyed
    cache pattern as the other derived endpoints."""
    return _cached_preflight(
        _files_signature(REPO / "content" / "editions.yaml"),
        _files_signature(REPO / "content" / "books.yaml"),
        _files_signature(REPO / "content" / "kinds.yaml"),
        _files_signature(REPO / "content" / "categories.yaml"),
        _notes_dir_signature(),
    )


@functools.lru_cache(maxsize=4)
def _cached_preflight(eds_sig, books_sig, kinds_sig, cats_sig, notes_sig):
    return _compute_preflight_uncached()


def _compute_preflight_uncached() -> dict:
    from scripts.core import translations as _tx
    from scripts.core import matrix as _matrix

    checks: list[dict] = []
    editions = config.load_editions()
    mtx = _matrix.compute_matrix()

    # 1. Note attribution — direct reuse of the audit endpoint
    audit = api_attribution_audit()
    counts = audit.get("counts", {})
    miss = counts.get("missing", 0)
    thin = counts.get("thin", 0)
    total = counts.get("total", 0)
    if miss:
        status, msg = "fail", (
            f"{miss} note(s) have no attribution at all "
            f"(of {total} total)"
        )
    elif thin:
        status, msg = "warn", (
            f"{thin} note(s) have thin attribution "
            f"(of {total} total)"
        )
    else:
        status, msg = "pass", f"all {total} notes have attribution"
    checks.append({
        "id": "attribution",
        "name": "Note attribution",
        "status": status,
        "message": msg,
        "details": (audit.get("needs_attention") or [])[:10],
        "jump_to": "/audit",
    })

    # 2. Main covers — every edition has its main cover image set
    #    AND that file exists on disk
    covers = api_covers()
    no_main, broken_main = [], []
    for ed_rec in covers["editions"]:
        path = ed_rec["main_cover"]["path"]
        meta = ed_rec["main_cover"]["meta"]
        if not path:
            no_main.append({"edition_id": ed_rec["edition_id"]})
        elif not meta:
            # Path is set but the file is missing from disk
            broken_main.append({
                "edition_id": ed_rec["edition_id"],
                "path": path,
            })
    if broken_main:
        status, msg = "fail", (
            f"{len(broken_main)} edition(s) have a cover_image path "
            f"pointing at a missing file"
        )
    elif no_main:
        status, msg = "warn", (
            f"{len(no_main)} edition(s) have no main cover set yet"
        )
    else:
        status, msg = "pass", "every edition has a main cover image"
    checks.append({
        "id": "covers_main",
        "name": "Main covers per edition",
        "status": status,
        "message": msg,
        "details": (broken_main + no_main)[:10],
        "jump_to": "/covers",
    })

    # 3. Popup translation set per edition (warn-only — popup uses WEB
    #    when not set, which is acceptable but not ideal for a buyer)
    no_translation = [
        {"edition_id": e["id"]}
        for e in editions
        if not (e.get("popup_translation") or "").strip()
    ]
    if not no_translation:
        status, msg = "pass", "every edition has a popup translation"
    else:
        status, msg = "warn", (
            f"{len(no_translation)} edition(s) using default WEB for "
            f"verse popups (no explicit translation chosen)"
        )
    checks.append({
        "id": "popup_translation",
        "name": "Popup translation per edition",
        "status": status,
        "message": msg,
        "details": no_translation[:10],
        "jump_to": "/customize",
    })

    # 4. Popup translation coverage of the edition's canon
    #    For each edition with a popup_translation set, count how many
    #    of its canon books the translation actually covers
    coverage_issues = []
    for ed in editions:
        tx_id = (ed.get("popup_translation") or "").strip()
        if not tx_id:
            continue
        canon = mtx.edition_canon_books.get(ed["id"], set())
        missing = sorted(b for b in canon if not _tx.has_book(tx_id, b))
        if missing:
            coverage_issues.append({
                "edition_id": ed["id"],
                "translation": tx_id,
                "missing_count": len(missing),
                "missing_books": missing[:20],
            })
    total_missing = sum(c["missing_count"] for c in coverage_issues)
    if not coverage_issues:
        status, msg = "pass", (
            "every popup translation covers its edition's canon"
        )
    else:
        status, msg = "warn", (
            f"{total_missing} book(s) across {len(coverage_issues)} "
            f"edition(s) have no popup translation data"
        )
    checks.append({
        "id": "popup_coverage",
        "name": "Popup translation coverage",
        "status": status,
        "message": msg,
        "details": coverage_issues[:10],
        "jump_to": "/customize",
    })

    # 5. Per-book covers — informational. Not blocking; many editions
    #    legitimately ship with only a main cover.
    per_book_stats = []
    for ed_rec in covers["editions"]:
        total_slots = len(ed_rec["book_covers"])
        with_cover = sum(
            1 for s in ed_rec["book_covers"] if s.get("meta")
        )
        per_book_stats.append({
            "edition_id": ed_rec["edition_id"],
            "set": with_cover,
            "total": total_slots,
        })
    total_set = sum(s["set"] for s in per_book_stats)
    total_slots = sum(s["total"] for s in per_book_stats)
    msg = f"{total_set} of {total_slots} per-book cover slots filled"
    checks.append({
        "id": "covers_per_book",
        "name": "Per-book covers (informational)",
        "status": "pass",   # never blocks ship
        "message": msg,
        "details": per_book_stats,
        "jump_to": "/covers",
    })

    # 6. Publisher metadata — title + ISBN at minimum for OPF
    incomplete = []
    for ed in editions:
        missing_fields = [
            f for f in ("title", "isbn")
            if not (ed.get(f) or "").strip()
        ]
        if missing_fields:
            incomplete.append({
                "edition_id": ed["id"],
                "missing": missing_fields,
            })
    if not incomplete:
        status, msg = "pass", (
            "every edition has title + ISBN set"
        )
    else:
        status, msg = "warn", (
            f"{len(incomplete)} edition(s) missing publisher fields"
        )
    checks.append({
        "id": "publisher_meta",
        "name": "Publisher metadata",
        "status": status,
        "message": msg,
        "details": incomplete,
        "jump_to": "/publisher",
    })

    # 7. Empty kinds — kinds in kinds.yaml that no note uses.
    #    Soft warn: hints at over-engineered taxonomy or missing apparatus.
    kinds = config.load_kinds()
    used_kinds: set[str] = set()
    for ed_id, by_kind in mtx.enabled.items():
        for kind_code, count in (by_kind or {}).items():
            if count > 0:
                used_kinds.add(kind_code)
    unused = sorted(
        k["code"] for k in kinds
        if k["code"] not in used_kinds
    )
    if not unused:
        status, msg = "pass", "every registered kind has at least one note"
    else:
        status, msg = "warn", (
            f"{len(unused)} kind(s) have zero notes across all editions"
        )
    checks.append({
        "id": "empty_kinds",
        "name": "Kind utilization",
        "status": status,
        "message": msg,
        "details": [{"kind_code": k} for k in unused[:20]],
        "jump_to": "/matrix",
    })

    # 8. Rules compliance (Phase ω.0.1) — composes lint_rules.run_all()
    # so the readiness dashboard surfaces drift from §6.1 / §6.2 / etc.
    # the moment it appears, not at the next code review.
    try:
        from scripts.lint_rules import run_all as _lint_run_all
        lint = _lint_run_all()
        sub_fail = lint["summary"]["fail"]
        sub_warn = lint["summary"]["warn"]
        if sub_fail:
            status, msg = "fail", (
                f"{sub_fail} rule(s) violated, {sub_warn} warning(s)"
            )
        elif sub_warn:
            status, msg = "warn", f"{sub_warn} rule warning(s)"
        else:
            status, msg = "pass", (
                f"all {lint['summary']['total']} project rules pass"
            )
        # Surface the failing/warning sub-checks as the details list
        # so a publisher sees "what's wrong" without leaving the page.
        details = [
            {"rule_id": c["id"], "name": c["name"],
             "status": c["status"], "message": c["message"]}
            for c in lint["checks"]
            if c["status"] != "pass"
        ]
    except Exception as e:
        status = "warn"
        msg = f"rules linter failed to run: {e}"
        details = []
    checks.append({
        "id": "rules_compliance",
        "name": "Rules compliance (§6.1, §6.2, encode/decode, docs)",
        "status": status,
        "message": msg,
        "details": details,
        "jump_to": "/preflight",   # nowhere better to jump — fix in code
    })

    # 9. epubcheck — W3C/IDPF EPUB validator (Phase ω.14)
    #    Runs against built EPUBs in exports/. The check stays
    #    informational when no EPUBs exist yet (info, not warn) so a
    #    fresh checkout doesn't show a red flag for "not validated".
    #    When Java is unavailable, surfaces as 'warn' with a clear
    #    install hint — the platform stays usable without it.
    try:
        from scripts.core import epubcheck as _ec
        ec_result = _ec.run_epubcheck_on_dir(REPO / "exports")
        ec_status = ec_result["status"]
        if ec_status == "pass":
            msg = (
                f"all {ec_result['n_epubs']} EPUB(s) validate cleanly"
            )
            details = []
        elif ec_status == "warn":
            t = ec_result["totals"]
            msg = (
                f"epubcheck: {t['warnings']} warning(s) across "
                f"{ec_result['n_epubs']} EPUB(s) (no errors)"
            )
            details = [
                {
                    "epub": r["epub"],
                    "errors": r["errors"],
                    "warnings": r["warnings"],
                    "first_message":
                        (r["messages"][0]["message"]
                         if r["messages"] else ""),
                }
                for r in ec_result["results"]
                if r["status"] != "pass"
            ][:10]
        elif ec_status == "fail":
            t = ec_result["totals"]
            msg = (
                f"epubcheck: {t['errors']} error(s), {t['warnings']} "
                f"warning(s) across {ec_result['n_epubs']} EPUB(s)"
            )
            details = [
                {
                    "epub": r["epub"],
                    "errors": r["errors"],
                    "warnings": r["warnings"],
                    "first_message":
                        (r["messages"][0]["message"]
                         if r["messages"] else ""),
                }
                for r in ec_result["results"]
                if r["status"] == "fail"
            ][:10]
        elif ec_status == "unavailable":
            # Java missing or JAR absent. Surface as warn with the
            # install hint; the rest of the platform stays usable.
            ec_status = "warn"
            msg = ec_result.get(
                "explanation", "epubcheck unavailable"
            )
            details = []
        else:  # 'empty'
            ec_status = "info"
            msg = ec_result.get(
                "explanation",
                "no built EPUBs to validate yet — run "
                "`python scripts/build_edition.py <id>`",
            )
            details = []
    except Exception as e:
        ec_status = "warn"
        msg = f"epubcheck check failed to run: {e}"
        details = []
    # The dashboard's status set is {pass, warn, fail}; map 'info'
    # to 'pass' for the summary tally but keep the message
    # informational so the UI can render it differently if it wants.
    summary_status = "pass" if ec_status == "info" else ec_status
    checks.append({
        "id": "epubcheck",
        "name": "EPUB validation (W3C epubcheck)",
        "status": summary_status,
        "message": msg,
        "details": details,
        "jump_to": "/export",
    })

    # Summary
    summary = {
        "total": len(checks),
        "pass": sum(1 for c in checks if c["status"] == "pass"),
        "warn": sum(1 for c in checks if c["status"] == "warn"),
        "fail": sum(1 for c in checks if c["status"] == "fail"),
    }
    summary["ready_to_ship"] = summary["fail"] == 0
    return {"checks": checks, "summary": summary}


def _parse_multipart(body: bytes, boundary: bytes) -> list[dict]:
    """Minimal multipart/form-data parser — focused on the cover-upload
    use case (one file part per request, no nested multipart).

    Returns a list of part dicts:
        {name, filename, content_type, data}

    We use this instead of cgi.FieldStorage because cgi is deprecated
    in 3.13 and a focused 30-line parser is easier to reason about than
    a stdlib module that's on its way out. The format itself is RFC
    7578: ``--boundary\\r\\n`` separates parts; each part has headers,
    an empty line, then bytes. ``--boundary--\\r\\n`` ends the body.
    """
    delim = b"--" + boundary
    chunks = body.split(delim)
    # First chunk is the prelude (often empty); last is the closing
    # "--\r\n" marker plus optional trailer.
    parts = []
    for chunk in chunks[1:-1]:
        # Strip the CRLF that follows the boundary line
        if chunk.startswith(b"\r\n"):
            chunk = chunk[2:]
        # Strip the CRLF that precedes the next boundary
        if chunk.endswith(b"\r\n"):
            chunk = chunk[:-2]
        sep = chunk.find(b"\r\n\r\n")
        if sep < 0:
            continue
        header_blob = chunk[:sep].decode("utf-8", errors="replace")
        data = chunk[sep + 4:]
        headers = {}
        for line in header_blob.split("\r\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        cd = headers.get("content-disposition", "")
        name = ""
        filename = ""
        for piece in cd.split(";"):
            piece = piece.strip()
            if piece.startswith("name="):
                name = piece[5:].strip().strip('"')
            elif piece.startswith("filename="):
                filename = piece[9:].strip().strip('"')
        parts.append({
            "name": name,
            "filename": filename,
            "content_type": headers.get("content-type", ""),
            "data": data,
        })
    return parts


def _extract_boundary(content_type_header: str) -> bytes | None:
    """Pull the ``boundary=...`` token out of a Content-Type header."""
    if not content_type_header:
        return None
    for piece in content_type_header.split(";"):
        piece = piece.strip()
        if piece.lower().startswith("boundary="):
            v = piece[9:].strip()
            # Strip surrounding quotes if present
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            return v.encode("ascii", errors="replace")
    return None


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
        rel_path = _covers.storage_path_for_book(
            edition_id, book_code, meta["format"]
        )
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


def api_upload_cover_main(edition_id: str, body: bytes,
                           content_type: str) -> dict:
    """Phase π.4-B — upload a main cover for one edition."""
    boundary = _extract_boundary(content_type)
    if boundary is None:
        return {"error": "request must be multipart/form-data with a boundary"}
    parts = _parse_multipart(body, boundary)
    file_parts = [p for p in parts if p.get("filename")]
    if not file_parts:
        return {"error": "no file part in upload"}
    return _save_cover_bytes(file_parts[0]["data"], edition_id, None)


def api_upload_cover_book(edition_id: str, book_code: str, body: bytes,
                           content_type: str) -> dict:
    """Phase π.4-B — upload a per-book cover."""
    boundary = _extract_boundary(content_type)
    if boundary is None:
        return {"error": "request must be multipart/form-data with a boundary"}
    parts = _parse_multipart(body, boundary)
    file_parts = [p for p in parts if p.get("filename")]
    if not file_parts:
        return {"error": "no file part in upload"}
    return _save_cover_bytes(file_parts[0]["data"], edition_id, book_code)


def api_delete_cover_main(edition_id: str) -> dict:
    """Phase π.4-B — clear an edition's main cover assignment + file."""
    eds = config.editions_by_id()
    if edition_id not in eds:
        return {"error": f"unknown edition: {edition_id}"}
    edition = eds[edition_id]
    cur_path = (edition.get("cover_image") or "").strip()
    # Update YAML first (set cover_image to empty)
    save_result = api_save_edition_meta(edition_id, {"cover_image": ""})
    if not save_result.get("ok"):
        return {"error": save_result.get("error", "yaml save failed")}
    # Then back up + remove the on-disk file
    if cur_path:
        abs_path = REPO / "content" / cur_path
        if abs_path.exists():
            notes_io.ensure_backup(abs_path)
            try:
                abs_path.unlink()
            except OSError:
                pass
    return {"ok": True, "edition_id": edition_id, "cleared": cur_path}


def api_delete_cover_book(edition_id: str, book_code: str) -> dict:
    """Phase π.4-B — clear a per-book cover assignment + file."""
    from scripts.core import covers as _covers
    eds = config.editions_by_id()
    if edition_id not in eds:
        return {"error": f"unknown edition: {edition_id}"}
    if book_code not in config.books_by_code():
        return {"error": f"unknown book code: {book_code}"}
    edition = eds[edition_id]
    per_book = _covers.decode_book_covers(edition.get("book_covers"))
    cur_path = per_book.pop(book_code, "")
    save_result = api_save_edition_meta(
        edition_id, {"book_covers": per_book}
    )
    if not save_result.get("ok"):
        return {"error": save_result.get("error", "yaml save failed")}
    if cur_path:
        abs_path = REPO / "content" / cur_path
        if abs_path.exists():
            notes_io.ensure_backup(abs_path)
            try:
                abs_path.unlink()
            except OSError:
                pass
    return {"ok": True, "edition_id": edition_id,
            "book_code": book_code, "cleared": cur_path}


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
        records.append(_covers.cover_record_for_edition(
            ed, canon_books, books_idx,
        ))
    return {"editions": records}


def api_clone_edition(payload: dict) -> dict:
    """Phase ν.4 — clone an existing edition into a new one.

    Body shape:
        {
            "source_id":   "<existing edition id>",   required
            "new_id":      "<unused edition id>",     required
            "new_title":   "<display title>",         optional
            "clone_files": bool,                      optional, default False
        }

    On success:
        - editions.yaml gets a fresh entry with source's full record
          copied verbatim, except `id` and (if provided) `title`
        - if clone_files=True, the source's main cover and per-book
          cover files are duplicated under the new edition's storage
          path; book_covers paths in the cloned record are rewritten
          to point at the new files
        - all caches that key on editions.yaml mtime invalidate
          automatically (φ.1 pattern)

    Returns the standard `{ok: true, ...}` envelope or `{error: "..."}`.
    Disk and editions.yaml are kept transactional: if the YAML write
    fails after files were copied, the copied files are removed.
    """
    if not isinstance(payload, dict):
        return {"error": "payload must be an object"}

    source_id = (payload.get("source_id") or "").strip()
    new_id = (payload.get("new_id") or "").strip()
    new_title = payload.get("new_title")
    clone_files = bool(payload.get("clone_files", False))

    if not source_id:
        return {"error": "source_id is required"}
    if not new_id:
        return {"error": "new_id is required"}
    # Same id-format constraints as elsewhere in the project — kebab-case,
    # alphanumeric + dashes only, no leading/trailing dash, no whitespace
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", new_id):
        return {"error": (
            f"new_id must be lowercase kebab-case "
            f"(letters/digits/dashes only): got {new_id!r}"
        )}

    eds = config.editions_by_id()
    if source_id not in eds:
        return {"error": f"unknown source edition: {source_id!r}"}
    if new_id in eds:
        return {"error": f"edition already exists: {new_id!r}"}

    source = eds[source_id]

    # If cloning files, do it BEFORE touching editions.yaml so a file
    # error doesn't leave an orphaned record. Track copied paths for
    # rollback.
    from scripts.core import covers as _covers
    copied: list[Path] = []
    new_book_covers_encoded: list[str] | None = None
    new_main_path: str = source.get("cover_image", "")

    if clone_files:
        try:
            # Main cover
            src_main = (source.get("cover_image") or "").strip()
            if src_main:
                src_path = REPO / "content" / src_main
                if src_path.is_file():
                    suffix = src_path.suffix.lstrip(".") or "jpg"
                    fmt = {"jpg": "jpeg"}.get(suffix.lower(), suffix.lower())
                    rel_new = _covers.storage_path_for_main(new_id, fmt)
                    abs_new = REPO / "content" / rel_new
                    abs_new.parent.mkdir(parents=True, exist_ok=True)
                    # ω.9 — atomic copy: never leave a half-written
                    # cloned cover image on a crash.
                    notes_io.atomic_write_bytes(
                        abs_new, src_path.read_bytes()
                    )
                    copied.append(abs_new)
                    new_main_path = rel_new
            # Per-book covers
            src_per_book = _covers.decode_book_covers(
                source.get("book_covers")
            )
            new_per_book: dict[str, str] = {}
            for code, src_rel in src_per_book.items():
                if not src_rel:
                    new_per_book[code] = ""
                    continue
                src_path = REPO / "content" / src_rel
                if not src_path.is_file():
                    # Source path missing — preserve the entry as empty
                    # so the cloned edition reflects the broken state
                    # honestly rather than copying garbage.
                    new_per_book[code] = ""
                    continue
                suffix = src_path.suffix.lstrip(".") or "jpg"
                fmt = {"jpg": "jpeg"}.get(suffix.lower(), suffix.lower())
                rel_new = _covers.storage_path_for_book(new_id, code, fmt)
                abs_new = REPO / "content" / rel_new
                abs_new.parent.mkdir(parents=True, exist_ok=True)
                # ω.9 — atomic copy (same rationale as main cover).
                notes_io.atomic_write_bytes(abs_new, src_path.read_bytes())
                copied.append(abs_new)
                new_per_book[code] = rel_new
            new_book_covers_encoded = _covers.encode_book_covers(
                new_per_book
            )
        except OSError as e:
            # Clean up any files we copied before the failure
            for p in copied:
                try:
                    p.unlink()
                except OSError:
                    pass
            return {"error": f"failed to clone files: {e}"}

    # Build the new YAML record. We serialize via the same primitives
    # as the existing patch helpers so list/dict fields encode
    # canonically.
    yaml_path = REPO / "content" / "editions.yaml"
    try:
        text = yaml_path.read_text(encoding="utf-8")
        new_text = _append_cloned_edition(
            text, source_id, new_id, new_title or source.get("title", new_id),
            override_cover_image=new_main_path,
            override_book_covers=new_book_covers_encoded,
        )
        notes_io.ensure_backup(yaml_path)
        notes_io.atomic_write(yaml_path, new_text)
    except Exception as e:
        # Roll back any files we copied — keep disk + yaml in sync
        for p in copied:
            try:
                p.unlink()
            except OSError:
                pass
        return {"error": f"failed to write editions.yaml: {e}"}

    # Invalidate caches that key on editions.yaml mtime (φ.1 picks up
    # automatically via the mtime signature; config.load_editions has
    # its own lru_cache that needs explicit clearing).
    config.load_editions.cache_clear()
    from scripts.core import matrix as matrix_mod
    matrix_mod.compute_matrix.cache_clear()

    return {
        "ok": True,
        "source_id": source_id,
        "new_id": new_id,
        "files_cloned": len(copied),
    }


def _append_cloned_edition(
    text: str,
    source_id: str,
    new_id: str,
    new_title: str,
    override_cover_image: str = "",
    override_book_covers: list[str] | None = None,
) -> str:
    """Append a deep-copy of one edition record to editions.yaml.

    We re-serialize the source record from its parsed form rather than
    cut-and-pasting from the source text, because the parsed form has
    already normalized the encoded list fields (popup_languages_per_book,
    book_covers) and the YAML output uses the same indentation/format
    as the project's writer helpers.
    """
    src = config.editions_by_id().get(source_id)
    if not src:
        raise ValueError(f"unknown source: {source_id!r}")

    # Build the new record's field list. Order mirrors what the
    # existing editions.yaml uses; absent fields are skipped.
    fields_text: list[str] = [f"  - id: {new_id}"]

    # Scalar passthrough fields (text/bool); apply overrides where
    # the clone semantics call for them.
    scalar_fields = [
        ("title", new_title),
        ("short_title", src.get("short_title", "")),
        ("isbn", ""),                                    # blank for the clone
        ("canon", src.get("canon", "")),
        ("target_audience", src.get("target_audience", "")),
        ("verse_popups", src.get("verse_popups", True)),
        ("verse_marker_glyph", src.get("verse_marker_glyph", "")),
        ("popup_translation", src.get("popup_translation", "")),
        ("theme", src.get("theme", "classic")),
        ("notes", src.get("notes", "")),
        ("cover_image", override_cover_image
             if override_cover_image is not None
             else src.get("cover_image", "")),
    ]
    for fname, fval in scalar_fields:
        if fval is None:
            continue
        if fval is True:
            fields_text.append(f"    {fname}: true")
        elif fval is False:
            fields_text.append(f"    {fname}: false")
        elif fval == "" or fval == 0:
            # Match existing style: empty strings serialize as ""
            fields_text.append(f'    {fname}: ""')
        else:
            # Quote strings to be safe against YAML special chars
            sval = str(fval).replace('"', '\\"')
            fields_text.append(f'    {fname}: "{sval}"')

    # List-typed fields — passthrough copy
    list_fields: list[tuple[str, list]] = []
    pld = src.get("popup_languages_default")
    if pld:
        list_fields.append(("popup_languages_default", list(pld)))
    plpb = src.get("popup_languages_per_book")
    if plpb:
        # Already in encoded list form
        list_fields.append(("popup_languages_per_book", list(plpb)))

    # book_covers: prefer override (when clone_files=True), else copy
    if override_book_covers is not None:
        if override_book_covers:
            list_fields.append(("book_covers", override_book_covers))
    else:
        bc = src.get("book_covers")
        if bc:
            list_fields.append(("book_covers", list(bc)))

    for fname, items in list_fields:
        fields_text.append(f"    {fname}:")
        for item in items:
            sitem = str(item).replace('"', '\\"')
            fields_text.append(f'      - "{sitem}"')

    new_block = "\n".join(fields_text) + "\n"
    if not text.endswith("\n"):
        text += "\n"
    return text + new_block


# Phase ν.5 — change-impact preview. Show the publisher exactly
# what the next save will alter — field-by-field — BEFORE touching
# disk. Prevents save regret on busy edits and gives buyers
# confidence that the platform isn't doing anything sneaky.
#
# Read-only: this function never writes. It compares the current
# on-disk edition record against the proposed payload and returns
# a structured diff. Validation errors are NOT surfaced here (they
# fire on actual save) — the preview shows what the publisher
# *intended* even if some values would be rejected, so they can
# spot-check the diff without first being yelled at by validators.
def api_preview_edition_changes(edition_id: str, payload: dict) -> dict:
    """Compute the field-by-field diff between the current edition
    record and the proposed payload, without persisting anything.

    Returns:
        {
            "edition_id": str,
            "changes":      [{"field": str, "before": Any, "after": Any}, ...],
            "unchanged":    [str, ...],   # field names that match current
            "no_changes":   bool,
            "field_count":  int,          # total fields in payload
        }

    Or {"error": "..."} for an unknown edition.
    """
    eds = config.editions_by_id()
    if edition_id not in eds:
        return {"error": f"unknown edition: {edition_id}"}
    current = eds[edition_id]

    # Mirror api_save_edition_meta's editable surfaces so the preview
    # accepts exactly the same field set. Anything outside this set
    # would be silently ignored by save anyway, so the preview marks
    # those as "unknown" to give the publisher early feedback.
    EDITABLE = {
        "title", "short_title", "isbn", "target_audience", "notes",
        "verse_marker_glyph", "theme", "popup_translation",
        "cover_image", "verse_popups",
        # Phase ν.2.7 popup languages
        "popup_languages_default", "popup_languages_per_book",
        # Phase π.4-A covers
        "book_covers",
        # Phase ν.6 reader experience
        "chapter_number_format", "chapter_number_decoration",
        # Phase ν.6.1 book ToC ornament
        "book_toc_ornament",
        # Phase ν.6 reader's TOC behavior
        "reader_toc_collapsible", "reader_toc_default_open",
    }

    changes: list[dict] = []
    unchanged: list[str] = []
    unknown: list[str] = []

    for field, proposed in payload.items():
        if field not in EDITABLE:
            unknown.append(field)
            continue
        before = current.get(field)
        # Normalize string fields the way save does (strip whitespace)
        # so "  hello " vs "hello" doesn't show as a spurious change.
        # Bool/list/dict fields: compare directly.
        if isinstance(proposed, str) and isinstance(before, str):
            if proposed.strip() == before.strip():
                unchanged.append(field)
                continue
        elif proposed == before:
            unchanged.append(field)
            continue
        changes.append({
            "field": field,
            "before": before,
            "after": proposed,
        })

    result = {
        "edition_id": edition_id,
        "changes": changes,
        "unchanged": unchanged,
        "no_changes": len(changes) == 0,
        "field_count": len(payload),
    }
    if unknown:
        # Surface unknown fields so the publisher sees they wouldn't
        # take effect. Save would silently drop them; preview shows
        # them explicitly.
        result["unknown_fields"] = unknown
    return result


def api_save_edition_meta(edition_id: str, payload: dict) -> dict:
    """Update editable metadata for one edition (Phase ν.2).

    Editable fields:
      - title, short_title, isbn, target_audience, notes
      - verse_popups (bool) — master toggle for verse-number popups
      - verse_marker_glyph (str) — custom character to show as verse marker;
        empty = default digit numbering
      - popup_translation (str, Phase τ.1.5) — id of a translation in
        content/translations/. Empty string means "use the system
        default" at build time. Any non-empty value is validated
        against the on-disk translation list.

    NOT editable here: id, canon, enabled/disabled kinds (use /matrix
    for the kind toggles, which is its own dedicated UI).
    """
    eds = config.editions_by_id()
    if edition_id not in eds:
        return {"error": f"unknown edition: {edition_id}"}

    EDITABLE_TEXT = {"title", "short_title", "isbn", "target_audience", "notes",
                      "verse_marker_glyph", "theme", "popup_translation",
                      "cover_image",
                      # Phase ν.6 — reader experience customization
                      "chapter_number_format",
                      "chapter_number_decoration",
                      # Phase ν.6.1 — book ToC ornament picker
                      "book_toc_ornament"}
    EDITABLE_BOOL = {"verse_popups",
                      # Phase ν.6 — reader's TOC display preferences
                      "reader_toc_collapsible",
                      "reader_toc_default_open"}

    # Validate theme if changed
    if "theme" in payload:
        valid_theme_ids = {t["id"] for t in _load_themes()}
        if payload["theme"] not in valid_theme_ids:
            return {"error": f"unknown theme: {payload['theme']!r}"}

    # Phase ν.6 — chapter number format + decoration validation.
    # These accept enumerated values defined in build_edition.py;
    # an unknown value is a hard error so the publisher gets clear
    # feedback rather than a silent fallback to 'digit'/'plain'.
    if "chapter_number_format" in payload:
        from scripts.build_edition import CHAPTER_NUMBER_FORMATS
        v = (payload["chapter_number_format"] or "").strip()
        if v and v not in CHAPTER_NUMBER_FORMATS:
            return {"error": (
                f"unknown chapter_number_format: {v!r}; "
                f"valid: {sorted(CHAPTER_NUMBER_FORMATS)}"
            )}
        payload["chapter_number_format"] = v
    if "chapter_number_decoration" in payload:
        from scripts.build_edition import CHAPTER_NUMBER_DECORATIONS
        v = (payload["chapter_number_decoration"] or "").strip()
        if v and v not in CHAPTER_NUMBER_DECORATIONS:
            return {"error": (
                f"unknown chapter_number_decoration: {v!r}; "
                f"valid: {sorted(CHAPTER_NUMBER_DECORATIONS)}"
            )}
        payload["chapter_number_decoration"] = v

    # Phase ν.6.1 — book ToC ornament validation. Same pattern as
    # the chapter decoration above. Schema-only for now; build-
    # pipeline rendering of the ornament into the in-book ToC is
    # queued for the same follow-up phase as reader_toc_*.
    if "book_toc_ornament" in payload:
        from scripts.build_edition import BOOK_TOC_ORNAMENTS
        v = (payload["book_toc_ornament"] or "").strip()
        if v and v not in BOOK_TOC_ORNAMENTS:
            return {"error": (
                f"unknown book_toc_ornament: {v!r}; "
                f"valid: {sorted(BOOK_TOC_ORNAMENTS)}"
            )}
        payload["book_toc_ornament"] = v

    # Validate cover_image path safety (Phase π.4-A)
    # Cover paths are stored relative to content/, so we forbid absolute
    # paths and parent-traversal. Empty string is allowed (means "no
    # cover set"). Validation happens here, BEFORE any disk write —
    # so a malformed payload never reaches editions.yaml.
    if "cover_image" in payload:
        err = _validate_cover_path(payload["cover_image"])
        if err:
            return {"error": err}

    # Validate popup_translation if changed (Phase τ.1.5)
    if "popup_translation" in payload:
        v = payload["popup_translation"]
        if v is None:
            v = ""
        if not isinstance(v, str):
            return {"error": "popup_translation must be a string"}
        if v:
            from scripts.core import translations as _tx
            available = set(_tx.list_translations())
            if v not in available:
                return {
                    "error": (
                        f"unknown translation: {v!r}; "
                        f"available: {sorted(available) or 'none'}"
                    )
                }
        payload["popup_translation"] = v

    # Validate popup_languages_default + popup_languages_per_book (Phase ν.2.7-B)
    list_field_updates: dict[str, list[str]] = {}
    from scripts.build_edition import (
        ALL_POPUP_LANGUAGES, encode_per_book_languages, decode_per_book_languages,
    )
    valid_langs = set(ALL_POPUP_LANGUAGES)

    if "popup_languages_default" in payload:
        v = payload["popup_languages_default"]
        if v is None:
            v = []
        if not isinstance(v, list):
            return {"error": "popup_languages_default must be a list of language ids"}
        cleaned: list[str] = []
        for item in v:
            if not isinstance(item, str):
                return {"error": "popup_languages_default items must be strings"}
            s = item.strip()
            if not s:
                continue
            if s not in valid_langs:
                return {
                    "error": (
                        f"unknown popup language: {s!r}; "
                        f"available: {sorted(valid_langs)}"
                    )
                }
            if s not in cleaned:
                cleaned.append(s)
        list_field_updates["popup_languages_default"] = cleaned

    # Phase ψ.8.1 — traditions_default validator. Mirror of
    # popup_languages_default: list of tradition ids, each in
    # CANONICAL_TRADITIONS. Empty list (or absent) means "include all
    # traditions" — byte-identical pre-ψ.8.2 build behavior.
    if "traditions_default" in payload:
        from scripts.core.traditions import TRADITION_IDS
        v = payload["traditions_default"]
        if v is None:
            v = []
        if not isinstance(v, list):
            return {"error":
                    "traditions_default must be a list of tradition ids"}
        cleaned: list[str] = []
        for item in v:
            if not isinstance(item, str):
                return {"error": "traditions_default items must be strings"}
            s = item.strip()
            if not s:
                continue
            if s not in TRADITION_IDS:
                return {
                    "error": (
                        f"unknown tradition: {s!r}; "
                        f"available: {sorted(TRADITION_IDS)}"
                    )
                }
            if s not in cleaned:
                cleaned.append(s)
        list_field_updates["traditions_default"] = cleaned

    if "popup_languages_per_book" in payload:
        v = payload["popup_languages_per_book"]
        if v is None:
            v = {}
        if not isinstance(v, dict):
            return {
                "error": (
                    "popup_languages_per_book must be a mapping "
                    "of book_code → list-of-language-ids"
                )
            }
        valid_books = set(config.books_by_code().keys())
        cleaned_dict: dict[str, list[str]] = {}
        for code, langs in v.items():
            if not isinstance(code, str) or not code.strip():
                return {"error": "popup_languages_per_book book codes must be non-empty strings"}
            code = code.strip()
            if code not in valid_books:
                return {"error": f"unknown book code: {code!r}"}
            if langs is None:
                langs = []
            if not isinstance(langs, list):
                return {
                    "error": (
                        f"popup_languages_per_book[{code!r}] must be a list "
                        f"of language ids"
                    )
                }
            book_langs: list[str] = []
            for L in langs:
                if not isinstance(L, str):
                    return {"error": f"language id in {code!r} must be a string"}
                s = L.strip()
                if not s:
                    continue
                if s not in valid_langs:
                    return {
                        "error": (
                            f"unknown popup language in {code!r}: {s!r}; "
                            f"available: {sorted(valid_langs)}"
                        )
                    }
                if s not in book_langs:
                    book_langs.append(s)
            cleaned_dict[code] = book_langs
        # Encode to the on-disk list-of-strings format
        list_field_updates["popup_languages_per_book"] = encode_per_book_languages(
            cleaned_dict
        )

    # Validate book_covers (Phase π.4-A)
    # Same indirection as popup_languages_per_book — UI sends a dict
    # {code: path}; we encode to a list of "code=path" strings on disk.
    # Each path is validated for safety; we do NOT require the file
    # to exist (publishers may save the assignment before uploading).
    if "book_covers" in payload:
        from scripts.core.covers import encode_book_covers
        v = payload["book_covers"]
        if v is None:
            v = {}
        if not isinstance(v, dict):
            return {
                "error": (
                    "book_covers must be a mapping of book_code → "
                    "cover path string"
                )
            }
        valid_books = set(config.books_by_code().keys())
        cleaned_covers: dict[str, str] = {}
        for code, path in v.items():
            if not isinstance(code, str) or not code.strip():
                return {"error": "book_covers book codes must be non-empty strings"}
            code = code.strip()
            if code not in valid_books:
                return {"error": f"unknown book code in book_covers: {code!r}"}
            if path is None:
                path = ""
            if not isinstance(path, str):
                return {"error": f"book_covers[{code!r}] must be a string path"}
            err = _validate_cover_path(path)
            if err:
                return {"error": f"book_covers[{code!r}]: {err}"}
            cleaned_covers[code] = path.strip()
        list_field_updates["book_covers"] = encode_book_covers(cleaned_covers)

    updates: dict[str, str] = {}
    for field in EDITABLE_TEXT:
        if field in payload:
            val = (payload[field] or "")
            if isinstance(val, str):
                if field == "verse_marker_glyph" and len(val) > 4:
                    return {"error": "verse_marker_glyph max 4 chars"}
                if field in {"title", "short_title"} and len(val) > 200:
                    return {"error": f"{field} too long (max 200)"}
                if field in {"target_audience", "notes"} and len(val) > 500:
                    return {"error": f"{field} too long (max 500)"}
                if field == "popup_translation" and len(val) > 32:
                    return {"error": "popup_translation too long (max 32)"}
                updates[field] = val
            else:
                return {"error": f"{field} must be a string"}
    for field in EDITABLE_BOOL:
        if field in payload:
            v = payload[field]
            if v not in (True, False):
                return {"error": f"{field} must be true or false"}
            updates[field] = "true" if v else "false"
    if not updates and not list_field_updates:
        return {"error": "no updates supplied"}

    path = REPO / "content" / "editions.yaml"
    text = path.read_text(encoding="utf-8")
    try:
        if updates:
            text = _patch_yaml_entry(text, "id", edition_id, updates)
        # List-field updates use the existing publisher-console helper.
        # Each list field is rewritten as a quoted YAML sub-list, which
        # the project's custom parser reads cleanly (same mechanism as
        # disabled_note_ids).
        for lf, items in list_field_updates.items():
            text = _patch_yaml_list_field(text, edition_id, lf, items)
    except ValueError as e:
        return {"error": str(e)}

    notes_io.ensure_backup(path)
    notes_io.atomic_write(path, text)
    config.load_editions.cache_clear()
    from scripts.core import matrix as matrix_mod
    matrix_mod.compute_matrix.cache_clear()
    return {
        "ok": True,
        "id": edition_id,
        "updated": list(updates.keys()) + list(list_field_updates.keys()),
    }


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
from scripts.templates.compare import COMPARE_HTML
from scripts.templates.covers import COVERS_HTML
from scripts.templates.customize import CUSTOMIZE_HTML
from scripts.templates.diff import DIFF_HTML
from scripts.templates.export import EXPORT_HTML
from scripts.templates.index import INDEX_HTML
from scripts.templates.matrix import MATRIX_HTML
from scripts.templates.ops import OPS_HTML
from scripts.templates.preflight import PREFLIGHT_HTML
from scripts.templates.publisher import PUBLISHER_HTML
from scripts.templates.sources import SOURCES_HTML
from scripts.templates.wizard import WIZARD_HTML

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
        list_translations, has_translation, has_book, get_chapter,
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
            "status": "error", "code": "unknown_edition", "http": 404,
            "message": f"No edition with id {edition_id!r}",
        }

    # --- Book validation (recognized?) ---
    book = (book or "").strip().lower()
    if not book:
        return {
            "status": "error", "code": "unknown_book", "http": 404,
            "message": "book code is required",
        }
    all_books = config.books_by_code()
    if book not in all_books:
        return {
            "status": "error", "code": "unknown_book", "http": 404,
            "message": f"Unknown book code {book!r}",
        }

    # --- Book-in-edition-canon check ---
    canons = load_canons()
    canon_id = edition.get("canon", "")
    canon_books = set((canons.get(canon_id) or {}).get("books") or [])
    if book not in canon_books:
        return {
            "status": "error", "code": "out_of_canon", "http": 404,
            "message": (
                f"Book {book!r} is not in the {canon_id!r} canon "
                f"used by edition {edition_id!r}"
            ),
        }

    # --- Chapter range validation ---
    try:
        f = int(from_chapter)
        t = int(to_chapter)
    except (TypeError, ValueError):
        return {
            "status": "error", "code": "invalid_range", "http": 400,
            "message": "from and to must be integers",
        }
    if f < 1 or t < f:
        return {
            "status": "error", "code": "invalid_range", "http": 400,
            "message": f"invalid range: from={f}, to={t}",
        }
    # Cap range size to keep the document reasonable; pitch decks
    # don't need 50-chapter samples
    MAX_RANGE = 10
    if (t - f + 1) > MAX_RANGE:
        return {
            "status": "error", "code": "invalid_range", "http": 400,
            "message": (
                f"range too large: requested {t - f + 1} chapters; "
                f"max is {MAX_RANGE}"
            ),
        }

    # --- Verses (compose translations.get_chapter) ---
    if not translations.has_translation(translation):
        return {
            "status": "error", "code": "invalid_range", "http": 400,
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
        edition=edition, book=book, all_books=all_books,
        from_chapter=f, to_chapter=t,
        verses_by_chapter=verses_by_chapter, notes=in_range,
        translation=translation,
    )

    return {
        "status": "ok", "html": html,
        "edition_id": edition_id, "book": book,
        "from": f, "to": t,
        "verse_count": total_verses, "note_count": len(in_range),
    }


def _render_sample_html(
    *, edition: dict, book: str, all_books: dict,
    from_chapter: int, to_chapter: int,
    verses_by_chapter: dict, notes: list, translation: str,
) -> str:
    """Render the self-contained sample HTML document.

    Pure presentation; no I/O. Inline CSS for portability so the
    document renders correctly when shared via email, Substack
    paste, etc., without needing external resources.
    """
    import html as _html
    book_meta = all_books.get(book) or {}
    book_title = book_meta.get("title") or book.upper()
    edition_title = (
        edition.get("title") or edition.get("short_title") or edition.get("id")
    )

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
                f'in {_html.escape(translation.upper())}.</p></section>'
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
                        f'<li class="note"><span class="kind">{kind}</span> '
                        f'<strong>{title}.</strong> {body}</li>'
                    )
                note_blocks_html = (
                    f'<ul class="notes">{"".join(items)}</ul>'
                )
            verse_html_parts.append(
                f'<p class="verse">'
                f'<sup class="vn">{v_num}</sup> {_html.escape(v_text)}'
                f'{note_blocks_html}'
                f'</p>'
            )
        chapter_blocks.append(
            f'<section class="chapter">'
            f'<h2>Chapter {ch}</h2>'
            f'{"".join(verse_html_parts)}'
            f'</section>'
        )

    range_label = (
        f"Chapter {from_chapter}"
        if from_chapter == to_chapter
        else f"Chapters {from_chapter}-{to_chapter}"
    )
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
        f'<title>{_html.escape(book_title)} - '
        f'{_html.escape(range_label)} - Sample</title>\n'
        f'<style>{style_block}</style>\n</head>\n<body>\n'
        '<header>\n'
        f'  <div class="edition">{_html.escape(edition_title or "")}</div>\n'
        f'  <h1>{_html.escape(book_title)} '
        f'<span class="range">- {_html.escape(range_label)}</span></h1>\n'
        f'  <p class="meta">Translation: {_html.escape(translation.upper())} '
        f'- Sample preview - {len(notes)} note(s) shown</p>\n'
        '</header>\n'
        f'{"".join(chapter_blocks)}\n'
        '<footer>\n'
        '  Sample generated from the E-Bible publishing platform.\n'
        '  This is a preview excerpt for evaluation.\n'
        '</footer>\n'
        '</body>\n</html>\n'
    )


# Phase ω.1 — Backup restore API. Surface the .backups/ snapshots
# that already exist (every atomic_write triggers ensure_backup);
# lets publishers undo destructive changes from the UI. Operational
# confidence is buyer-demo gold: "you can play with this without
# breaking anything." Path traversal is the main security concern —
# only files inside content/ are addressable.

# Backup filename pattern: <stem>.<TIMESTAMP>.<suffix>.bak
# where TIMESTAMP is the YYYYMMDDTHHMMSSZ string from ensure_backup.
_BACKUP_FILENAME_RE = re.compile(
    r"^(?P<stem>.+?)\.(?P<ts>\d{8}T\d{6}Z)(?P<suffix>\..+)?\.bak$"
)


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
        return {"status": "error", "code": "invalid_path",
                "http": 400, "message": err}
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
                iso_time = (
                    f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]}T"
                    f"{ts[9:11]}:{ts[11:13]}:{ts[13:15]}+00:00"
                )
            except IndexError:
                iso_time = ts
            try:
                size_bytes = bp.stat().st_size
            except OSError:
                size_bytes = 0
            snapshots.append({
                "id": bp.name,
                "timestamp": ts,
                "iso_time": iso_time,
                "size_bytes": size_bytes,
            })
    # Newest first — easier for UI
    snapshots.reverse()
    return {
        "status": "ok",
        "file": str(abs_path.relative_to((REPO / "content").resolve())),
        "snapshots": snapshots,
        "count": len(snapshots),
    }


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
        return {"status": "error", "code": "invalid_path",
                "http": 400, "message": err}
    if not snapshot_id or not isinstance(snapshot_id, str):
        return {"status": "error", "code": "invalid_snapshot",
                "http": 400, "message": "snapshot_id is required"}

    m = _BACKUP_FILENAME_RE.match(snapshot_id)
    if not m:
        return {"status": "error", "code": "invalid_snapshot",
                "http": 400, "message": f"snapshot id {snapshot_id!r} has bad format"}
    # Belt-and-braces: the snapshot's stem must match the file's stem,
    # else the caller is trying to restore a snapshot of a DIFFERENT
    # file into this path, which is a bug or attack.
    if m.group("stem") != abs_path.stem:
        return {"status": "error", "code": "invalid_snapshot",
                "http": 400, "message": (
                    f"snapshot {snapshot_id!r} does not belong to "
                    f"file {abs_path.name!r}"
                )}

    backup_dir = abs_path.parent / ".backups"
    snapshot_path = backup_dir / snapshot_id
    if not snapshot_path.is_file():
        return {"status": "error", "code": "snapshot_not_found",
                "http": 404, "message": f"no such snapshot: {snapshot_id}"}

    # Defense-in-depth: snapshot_path must also be under content/,
    # in case backup_dir was a symlink or something equally weird.
    content_root = (REPO / "content").resolve()
    try:
        snapshot_path.resolve().relative_to(content_root)
    except ValueError:
        return {"status": "error", "code": "invalid_snapshot",
                "http": 400, "message": "snapshot resolves outside content/"}

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
        return {"status": "error", "code": "snapshot_not_found",
                "http": 404, "message": f"could not read snapshot: {e}"}

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
        free_gb = usage.free / (1024 ** 3)
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


# Phase ω.3 — API reference page. Auto-enumerates every /api/*
# route by regex-scanning this file's source. Helps future Claude
# / future dev orient — the /api/* surface has grown to ~30 routes
# across 12+ phases. Single page with method + path + description
# + phase tag + permission level beats hunting through web.py.
#
# Pattern: pure-function-API + thin route adapter (7th instance —
# now properly codified in §9 since ω.0.7).

# Route patterns to recognize, in source-scan order. Each entry's
# regex captures the path. The regex matches the WHOLE source line
# (including leading whitespace) so context comments can be located
# from the same line index.
_ROUTE_PATTERNS = [
    # GET: if path == "/api/X":   or   if path == "/X" or path == "/X.html":
    (re.compile(r'^\s*if\s+path\s*==\s*"(/api/[^"]+)"'), "GET"),
    (re.compile(r'^\s*if\s+path\.startswith\("(/api/[^"]+)"'), "GET"),
    # POST: if self.path == "/api/X":
    (re.compile(r'^\s*if\s+self\.path\s*==\s*"(/api/[^"]+)"'), "POST"),
    # Pattern: m = re.match(r"^/api/X/...$", self.path)
    (re.compile(
        r'^\s*m\s*=\s*re\.match\(r"\^(/api/[^"$]+)\$"'), "PATTERN"),
]

# Console-page routes (HTML, not API). These get listed separately
# in the help page since they're a different kind of surface.
_CONSOLE_PATTERNS = [
    re.compile(r'^\s*if\s+path\s*==\s*"(/[a-z][^"/]*)"\s*or\s*'
               r'path\s*==\s*"\1\.html"'),
]


def api_help_data() -> dict:
    """Enumerate every /api/* route + every /<console> route by
    scanning scripts/web.py source. The result powers the /apihelp
    console; nothing here mutates state or hits the network.

    Returns:
        {
          "status": "ok",
          "api_routes": [
            {"method": str, "path": str, "description": str,
             "phase": str | None, "line": int}, ...
          ],
          "consoles": [
            {"path": str, "description": str, "phase": str | None,
             "line": int}, ...
          ],
          "totals": {"api": int, "consoles": int},
        }
    """
    src_path = REPO / "scripts" / "web.py"
    try:
        lines = src_path.read_text(encoding="utf-8").splitlines()
    except OSError as e:
        return {"status": "error", "code": "source_read_failed",
                "http": 500, "message": str(e)}

    api_routes: list[dict] = []
    consoles: list[dict] = []
    seen_api: set[tuple[str, str]] = set()
    seen_console: set[str] = set()

    # Phase regex — matches "Phase X.Y" or "Phase Xx.Y" in
    # comments above a route. ω, ψ, etc. are real characters
    # in the codebase.
    phase_re = re.compile(r"Phase\s+([α-ωΑ-Ω][a-z]?\.[\w.\-]+)")

    def gather_context(line_idx: int, max_lookback: int = 8) -> str:
        """Walk backward from a route line collecting comment lines.
        Stop at the first non-comment, non-empty line OR after
        max_lookback lines."""
        comment_lines: list[str] = []
        for j in range(line_idx - 1, max(-1, line_idx - max_lookback), -1):
            line = lines[j].strip()
            if not line:
                if comment_lines:
                    break
                continue
            if line.startswith("#"):
                comment_lines.append(line.lstrip("#").strip())
            else:
                break
        comment_lines.reverse()
        return " ".join(comment_lines)

    for i, line in enumerate(lines):
        # API routes
        for pattern, method in _ROUTE_PATTERNS:
            m = pattern.match(line)
            if m:
                path = m.group(1)
                # The PATTERN method gets its placeholders
                # explicit (e.g. /api/translation/<id>/<book>)
                if method == "PATTERN":
                    # Convert regex segments like ([a-z0-9-]+) → <param>
                    path = re.sub(r"\(\[[^\]]+\]\+\)", "<param>", path)
                key = (method, path)
                if key in seen_api:
                    break
                seen_api.add(key)
                ctx = gather_context(i)
                phase_match = phase_re.search(ctx)
                api_routes.append({
                    "method": method if method != "PATTERN" else "GET/POST",
                    "path": path,
                    "description": ctx,
                    "phase": phase_match.group(1) if phase_match else None,
                    "line": i + 1,
                })
                break

        # Console pages
        for pattern in _CONSOLE_PATTERNS:
            m = pattern.match(line)
            if m:
                path = m.group(1)
                if path in seen_console:
                    break
                seen_console.add(path)
                ctx = gather_context(i)
                phase_match = phase_re.search(ctx)
                consoles.append({
                    "path": path,
                    "description": ctx,
                    "phase": phase_match.group(1) if phase_match else None,
                    "line": i + 1,
                })
                break

    # Sort: API routes by path; consoles by path
    api_routes.sort(key=lambda r: r["path"])
    consoles.sort(key=lambda r: r["path"])

    return {
        "status": "ok",
        "api_routes": api_routes,
        "consoles": consoles,
        "totals": {
            "api": len(api_routes),
            "consoles": len(consoles),
        },
    }


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
                needs_attention.append({
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
                })

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
    by_book_list = sorted(by_book.values(),
                           key=lambda x: -(x["missing"] + x["thin"]))

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
# Per-Note Disable API (Phase ρ.1) — disable individual notes per edition
# ============================================================


_NOTE_ID_RE = re.compile(
    r"^([a-z0-9]+):(\d+):(\d+)([a-z]*):([a-z][a-z0-9-]*)$"
)


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


def api_save_note_toggle(edition_id: str, payload: dict) -> dict:
    """Add or remove a note ID from an edition's disabled_note_ids list (ρ.1).

    Payload: {"note_id": "<id>", "enabled": true|false}
      enabled: false → add to disabled_note_ids
      enabled: true  → remove from disabled_note_ids
    """
    eds = config.editions_by_id()
    if edition_id not in eds:
        return {"error": f"unknown edition: {edition_id}"}

    nid = payload.get("note_id", "")
    enabled = payload.get("enabled")
    if enabled not in (True, False):
        return {"error": "enabled must be true or false"}
    parsed = parse_note_id(nid)
    if not parsed:
        return {"error": f"invalid note_id format: {nid!r}"}

    # Validate the note actually exists in the corpus
    books = config.books_by_code()
    if parsed["book"] not in books:
        return {"error": f"unknown book: {parsed['book']}"}

    # Sanity check: the note ID must resolve to a valid HTML ref-id
    # (which the build pipeline will use). Cheap belt-and-braces validation.
    html_ref = html_ref_id_from_note_id(nid, books)
    if not html_ref:
        return {"error": f"could not resolve note_id to HTML ref: {nid}"}

    edition = eds[edition_id]
    current_disabled = list(edition.get("disabled_note_ids") or [])
    new_set = set(current_disabled)
    if enabled:
        new_set.discard(nid)
    else:
        new_set.add(nid)
    new_list = sorted(new_set)

    # If unchanged, no-op
    if new_list == sorted(current_disabled):
        return {"ok": True, "edition": edition_id, "unchanged": True,
                "disabled_count": len(new_list)}

    # Patch editions.yaml using a list-block-aware regex similar to μ.2
    path = REPO / "content" / "editions.yaml"
    text = path.read_text(encoding="utf-8")

    block_re = re.compile(
        rf'(^  - id: {re.escape(edition_id)}\n)(.*?)(?=^  - id:|\Z)',
        re.MULTILINE | re.DOTALL,
    )
    m = block_re.search(text)
    if not m:
        return {"error": f"edition {edition_id} not found in YAML"}
    head, body = m.group(1), m.group(2)

    # Build the new list block. We quote each value because note IDs contain
    # colons (e.g. "gen:1:1a:word"), and an unquoted list item like
    # `      - gen:1:1a:word` would be misparsed as a new record-start by
    # the project's custom YAML parser (which uses `field:` after a dash to
    # detect record boundaries). Quoting makes the items pure scalars.
    if new_list:
        new_block = "    disabled_note_ids:\n" + "\n".join(
            f'      - "{nid}"' for nid in new_list
        ) + "\n"
    else:
        new_block = "    disabled_note_ids: []\n"

    # Replace existing block, or insert near other related fields
    list_re = re.compile(
        r"^(    disabled_note_ids:.*?\n)((?:      - [^\n]+\n)*|    disabled_note_ids: \[\]\n)",
        re.MULTILINE,
    )
    if list_re.search(body):
        new_body = list_re.sub(new_block, body, count=1)
    else:
        # Insert before disabled_kinds: if present, else at end of block
        anchor_re = re.compile(r"^(    disabled_kinds:)", re.MULTILINE)
        am = anchor_re.search(body)
        if am:
            new_body = body[:am.start()] + new_block + body[am.start():]
        else:
            new_body = body + new_block

    new_text = text[:m.start()] + head + new_body + text[m.end():]
    notes_io.ensure_backup(path)
    notes_io.atomic_write(path, new_text)
    config.load_editions.cache_clear()
    from scripts.core import matrix as matrix_mod
    matrix_mod.compute_matrix.cache_clear()

    return {
        "ok": True,
        "edition": edition_id,
        "note_id": nid,
        "now_enabled": enabled,
        "disabled_count": len(new_list),
    }


def api_disabled_notes_for_edition(edition_id: str) -> dict:
    """Return the disabled-note-ID set for one edition. Used by /sources UI
    to show which notes are currently turned off for an edition."""
    eds = config.editions_by_id()
    if edition_id not in eds:
        return {"error": f"unknown edition: {edition_id}"}
    return {
        "edition": edition_id,
        "disabled_note_ids": sorted(
            eds[edition_id].get("disabled_note_ids") or []
        ),
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
    "source_text_credit": (
        "Scripture text based on the World English Bible (public domain)."
    ),
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


def api_save_publisher_meta(edition_id: str, payload: dict) -> dict:
    """Update one edition's publishing metadata. Accepts a partial payload —
    only the fields supplied are modified; anything else is left alone.

    Validation:
      · text fields enforced to their PUBLISHING_TEXT_LIMITS
      · authors / bisac_codes accepted as lists of short strings
      · empty list submitted as [] resets the list
    """
    eds = config.editions_by_id()
    if edition_id not in eds:
        return {"error": f"unknown edition: {edition_id}"}

    text_updates: dict[str, str] = {}
    list_updates: dict[str, list[str]] = {}

    for field, max_len in PUBLISHING_TEXT_LIMITS.items():
        if field not in payload:
            continue
        v = payload[field]
        if v is None:
            v = ""
        if not isinstance(v, str):
            return {"error": f"{field} must be a string"}
        if len(v) > max_len:
            return {"error": f"{field} too long (max {max_len})"}
        text_updates[field] = v

    for lf in PUBLISHING_LIST_FIELDS:
        if lf not in payload:
            continue
        v = payload[lf]
        if not isinstance(v, list):
            return {"error": f"{lf} must be a list"}
        items: list[str] = []
        for item in v:
            if not isinstance(item, str):
                return {"error": f"{lf} items must be strings"}
            s = item.strip()
            if not s:
                continue
            if len(s) > 300:
                return {"error": f"{lf} item too long (max 300)"}
            items.append(s)
        list_updates[lf] = items

    if not text_updates and not list_updates:
        return {"error": "no updates supplied"}

    path = REPO / "content" / "editions.yaml"
    text = path.read_text(encoding="utf-8")

    # Apply text-field updates via the existing _patch_yaml_entry helper.
    if text_updates:
        try:
            text = _patch_yaml_entry(text, "id", edition_id, text_updates)
        except ValueError as e:
            return {"error": str(e)}

    # Apply list-field updates by replacing or inserting the list block.
    for lf, items in list_updates.items():
        text = _patch_yaml_list_field(text, edition_id, lf, items)

    notes_io.ensure_backup(path)
    notes_io.atomic_write(path, text)
    config.load_editions.cache_clear()
    from scripts.core import matrix as matrix_mod
    matrix_mod.compute_matrix.cache_clear()

    return {
        "ok": True,
        "id": edition_id,
        "updated_text": list(text_updates.keys()),
        "updated_lists": list(list_updates.keys()),
    }


def _patch_yaml_list_field(text: str, edition_id: str,
                            field: str, items: list[str]) -> str:
    """Replace or insert a YAML sub-list block (e.g. authors:) inside one
    edition record. Items are written QUOTED, like the disabled_note_ids
    pattern, so they survive the project's custom YAML parser even if
    they happen to contain colons or other punctuation.
    """
    block_re = re.compile(
        rf'(^  - id: {re.escape(edition_id)}\n)(.*?)(?=^  - id:|\Z)',
        re.MULTILINE | re.DOTALL,
    )
    m = block_re.search(text)
    if not m:
        raise ValueError(f"edition {edition_id} not found")
    head, body = m.group(1), m.group(2)

    # Build the new block
    if items:
        new_block = f"    {field}:\n" + "\n".join(
            f'      - "{_yaml_escape(s)}"' for s in items
        ) + "\n"
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

    return text[:m.start()] + head + new_body + text[m.end():]


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


def _diff_edition_summary(ed: dict, mtx, kinds_idx: dict, books_idx: dict,
                           canons_idx: dict) -> dict:
    """One edition's side of the diff — headline metadata plus
    pre-computed totals so the UI doesn't have to re-derive them.
    """
    ed_id = ed["id"]
    enabled = mtx.enabled.get(ed_id, {})
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
            rows.append({
                "code": code,
                "title": b.get("title", code),
            })
        return rows

    return {
        "only_a": _format(a_books - b_books),
        "only_b": _format(b_books - a_books),
        "both_count": len(a_books & b_books),
    }


def _diff_kinds_section(a_id: str, b_id: str, mtx, kinds_idx: dict,
                         cats_idx: dict) -> dict:
    """Per-kind diff with shipping counts. Three buckets:
       only_a   — kinds enabled in A but not B (with A's count)
       only_b   — kinds enabled in B but not A (with B's count)
       shared   — kinds enabled in both, with both counts and the delta
    Within each bucket, sort by category sort_order, then by descending
    count so the most prominent differences appear first.
    """
    a_kinds = mtx.edition_enabled_kinds.get(a_id, set())
    b_kinds = mtx.edition_enabled_kinds.get(b_id, set())
    a_counts = mtx.enabled.get(a_id, {})
    b_counts = mtx.enabled.get(b_id, {})

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

    only_a = [_row(c, a_n=a_counts.get(c, 0))
              for c in a_kinds - b_kinds]
    only_b = [_row(c, b_n=b_counts.get(c, 0))
              for c in b_kinds - a_kinds]
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


def _diff_categories_section(a_id: str, b_id: str,
                              kinds_idx: dict, cats_idx: dict, mtx) -> list:
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
        rows.append({
            "id": cid,
            "label": c.get("label", cid),
            "symbol": c.get("symbol", "?"),
            "sort_order": c.get("sort_order", 999),
            "a_count": a_by_cat.get(cid, 0),
            "b_count": b_by_cat.get(cid, 0),
        })
    rows.sort(key=lambda r: r["sort_order"])
    return rows


def _diff_headline(a_summary: dict, b_summary: dict,
                    books_section: dict, kinds_section: dict) -> str:
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
            f"{a_short} includes {len(a_only_books)} book"
            f"{'s' if len(a_only_books)!=1 else ''} that {b_short} omits"
        )
    elif b_only_books and not a_only_books:
        bits.append(
            f"{b_short} includes {len(b_only_books)} book"
            f"{'s' if len(b_only_books)!=1 else ''} that {a_short} omits"
        )
    elif a_only_books and b_only_books:
        bits.append(
            f"{a_short} adds {len(a_only_books)} book"
            f"{'s' if len(a_only_books)!=1 else ''} the other lacks; "
            f"{b_short} adds {len(b_only_books)}"
        )

    if a_only_kinds or b_only_kinds:
        bits.append(
            f"{a_only_kinds} note kinds are exclusive to {a_short}, "
            f"{b_only_kinds} to {b_short}"
        )

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
        a_id, b_id,
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
        {"id": e["id"],
         "short_title": e.get("short_title", e["id"]),
         "title": e.get("title", e["id"])}
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


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
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
        sys.stderr.write(
            f"  [unhandled {method_name}] "
            f"{type(exc).__name__}: {exc}\n"
        )
        traceback.print_exc(file=sys.stderr)
        try:
            return self._send_json({
                "error": "internal_error",
                "message": (
                    f"unhandled {type(exc).__name__} in {method_name}; "
                    "see server log for details"
                ),
            }, status=500)
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
        return self._send_json({
            "error": result.get("code") or "internal_error",
            "message": result.get("message") or "",
            **{k: v for k, v in result.items()
               if k not in ("status", "code", "http", "message")},
        }, status=http_code)

    def _send_html(self, html: str):
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

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
            ext = path.suffix.lower().lstrip(".")
            content_type = {
                "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "png": "image/png", "webp": "image/webp",
                "gif": "image/gif", "svg": "image/svg+xml",
            }.get(ext, "application/octet-stream")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        # Browser cache covers for a minute — saves bandwidth across
        # navigations between consoles. Short enough that re-uploads
        # show within reasonable time without manual refresh.
        self.send_header("Cache-Control", "public, max-age=60")
        self.end_headers()
        self.wfile.write(data)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def _check_admin_auth(self) -> bool:
        """Phase ω.4 — auth gate for mutation endpoints.

        Behavior is governed by the ``EBIBLE_ADMIN_TOKEN`` env var:

          - **unset (default)**: every endpoint behaves as before.
            Local-only / single-user assumption holds; the project
            stays trivially launchable for development.
          - **set**: every POST / PUT / DELETE on /api/* requires
            an ``Authorization: Bearer <token>`` header that matches
            exactly. Mismatch → 401.

        GET / HEAD are unaffected (read-only is fine to leave open
        even when the rest is locked down).

        Returns True when the request is allowed to proceed; when
        False, this method has already sent a 401 response and the
        caller should return immediately.
        """
        token = os.environ.get("EBIBLE_ADMIN_TOKEN", "").strip()
        if not token:
            return True   # auth disabled, back-compat default
        header = self.headers.get("Authorization", "")
        prefix = "Bearer "
        if not header.startswith(prefix):
            self._send_json(
                {"error": "missing Authorization: Bearer <token> header"},
                status=401,
            )
            return False
        supplied = header[len(prefix):].strip()
        # constant-time compare to avoid timing leaks
        import hmac
        if not hmac.compare_digest(supplied, token):
            self._send_json({"error": "invalid admin token"}, status=401)
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

        if path == "/" or path == "/index.html":
            return self._send_html(INDEX_HTML)
        if path == "/matrix" or path == "/matrix.html":
            return self._send_html(MATRIX_HTML)
        if path == "/api/books":
            return self._send_json(api_books())
        if path == "/api/kinds":
            return self._send_json(api_kinds())
        if path == "/api/matrix":
            return self._send_json(api_matrix())
        if path == "/api/scenarios":
            return self._send_json(api_list_scenarios())

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
        if path == "/api/sources":
            return self._send_json(api_sources_index())
        if path == "/api/sources/summary":
            return self._send_json(api_sources_summary())
        m = re.match(r"^/api/sources/([a-z0-9]+)$", path)
        if m:
            return self._send_json(api_sources_for_book(m.group(1)))

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
            self.end_headers()
            self.wfile.write(data)
            return

        # Customize (Phase ν.1)
        if path == "/customize" or path == "/customize.html":
            return self._send_html(CUSTOMIZE_HTML)
        if path == "/api/customize":
            return self._send_json(api_customize_data())

        # Attribution Audit (Phase ξ.4)
        if path == "/audit" or path == "/audit.html":
            return self._send_html(AUDIT_HTML)
        if path == "/api/audit/attribution":
            return self._send_json(api_attribution_audit())

        # Per-note disable list for one edition (Phase ρ.1)
        m = re.match(r"^/api/edition/([a-z0-9-]+)/disabled-notes$", path)
        if m:
            return self._send_json(api_disabled_notes_for_edition(m.group(1)))

        # Publisher console (Phase π.1)
        if path == "/publisher" or path == "/publisher.html":
            return self._send_html(PUBLISHER_HTML)
        if path == "/api/publisher":
            return self._send_json(api_publisher_data())

        # Bible Builder Wizard (Phase π.5)
        if path == "/wizard" or path == "/wizard.html":
            return self._send_html(WIZARD_HTML)

        # Edition Diff View (Phase ξ.5) — read-only sales/demo tool
        if path == "/diff" or path == "/diff.html":
            return self._send_html(DIFF_HTML)
        if path == "/api/diff":
            qs = urllib.parse.parse_qs(url.query or "")
            a = (qs.get("a") or [""])[0]
            b = (qs.get("b") or [""])[0]
            # Sensible defaults for the buyer-demo headline
            if not a:
                a = "catholic-study"
            if not b:
                b = "evangelical-reformed"
            return self._send_json(api_edition_diff(a, b))

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
            edition_id = path[len("/api/sample/"):].split("/", 1)[0]
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
                edition_id, book, from_n, to_n, translation=translation,
            )
            if result.get("status") == "ok":
                return self._send_html(result["html"])
            # Error path — return JSON with the spec'd HTTP status
            http_code = result.get("http") or 500
            self.send_response(http_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            payload = json.dumps({
                "error": result.get("code") or "internal_error",
                "message": result.get("message") or "",
            }).encode("utf-8")
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
            self.wfile.write(json.dumps({
                "error": result.get("code") or "internal_error",
                "message": result.get("message") or "",
            }).encode("utf-8"))
            return

        # Per-book cover status (Phase π.4-A) — read-only feed for
        # the upcoming /covers UI. Returns each edition's main + per-book
        # cover slots, filtered by canon and sorted in canonical order.
        if path == "/api/covers":
            return self._send_json(api_covers())

        # Pre-flight checklist (Phase ψ.2) — aggregator dashboard
        if path == "/preflight" or path == "/preflight.html":
            return self._send_html(PREFLIGHT_HTML)
        if path == "/api/preflight":
            return self._send_json(api_preflight())

        # Corpus progress widget (Phase ψ.3) — read-only feed for
        # the every-console progress bar. Cheap; composes the
        # already-cached api_attribution_audit.

        # Phase ω.0.2 — scaffolded route for /ops
        if path == "/ops" or path == "/ops.html":
            return self._send_html(OPS_HTML)
        # Phase ψ.6 — operator dashboard data feed
        if path == "/api/ops":
            return self._send_json(api_ops_dashboard())

        # Phase ω.0.2 — scaffolded route for /apihelp
        if path == "/apihelp" or path == "/apihelp.html":
            return self._send_html(APIHELP_HTML)
        # Phase ω.3 — API reference data feed (auto-generated)
        if path == "/api/apihelp":
            return self._send_json(api_help_data())
        if path == "/api/corpus-progress":
            return self._send_json(api_corpus_progress())

        # Cover console (Phase π.4-B UI). The image-upload flow lives
        # in do_POST; this route just serves the page shell.
        if path == "/covers" or path == "/covers.html":
            return self._send_html(COVERS_HTML)

        # Static cover-image serving so the /covers UI can render
        # thumbnails. Sandboxed to content/covers/ ; any path that
        # tries to escape (.., absolute, hidden) is rejected with 404.
        # Read-only — uploads go through POST /api/covers/...
        if path.startswith("/content/covers/"):
            # ξ.2 — sandbox via shared safe_path helper. The string
            # after the route prefix is treated as a path RELATIVE
            # TO content/covers/.
            rel = path[len("/content/covers/"):]
            from scripts.core.safe_path import (
                SafePathError, resolve_under,
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

        m = re.match(r"^/api/notes/([a-z0-9]+)$", path)
        if m:
            return self._send_json(api_notes(m.group(1)))

        m = re.match(r"^/api/template/([\w-]+)$", path)
        if m:
            return self._send_json(api_template(m.group(1)))

        self._send_json({"error": "not found", "path": path}, status=404)

    @_safe_request
    def do_PUT(self):
        if not self._check_admin_auth():
            return
        m = re.match(r"^/api/notes/([a-z0-9]+)$", self.path)
        if m:
            try:
                payload = self._read_body()
                return self._send_json(api_save(m.group(1), payload))
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)
        # Save edition kind-toggle state (μ.2)
        m = re.match(r"^/api/edition/([a-z0-9-]+)$", self.path)
        if m:
            try:
                payload = self._read_body()
                result = api_save_edition(m.group(1), payload)
                status = 200 if result.get("ok") else 400
                return self._send_json(result, status=status)
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)
        # Save scenario (μ.2½)
        m = re.match(r"^/api/scenarios/([a-z0-9_-]+)$", self.path)
        if m:
            try:
                payload = self._read_body()
                result = api_save_scenario(m.group(1), payload)
                status = 200 if result.get("ok") else 400
                return self._send_json(result, status=status)
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)
        # Build edition (Phase σ.2)
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
        # Build all editions (Phase ω.2) — runs build_edition for
        # every edition, packages successful EPUBs into one zip.
        # Per-edition errors don't abort the batch (spec).
        if self.path == "/api/build-all":
            try:
                payload = self._read_body() or {}
                version = payload.get("version", "v28a")
                result = api_build_all_editions(version=version)
                # Status 200 if at least one success (partial-ok is
                # a real outcome the UI handles); 500 only when all
                # editions failed.
                status = 200 if result.get("success_count", 0) > 0 else 500
                return self._send_json(result, status=status)
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)
        # Customize: update one category (Phase ν.1)
        m = re.match(r"^/api/category/([a-z0-9-]+)$", self.path)
        if m:
            try:
                payload = self._read_body()
                result = api_save_category(m.group(1), payload)
                status = 200 if result.get("ok") else 400
                return self._send_json(result, status=status)
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)
        # Customize: update one kind (Phase ν.1)
        m = re.match(r"^/api/kind/([a-z0-9-]+)$", self.path)
        if m:
            try:
                payload = self._read_body()
                result = api_save_kind(m.group(1), payload)
                status = 200 if result.get("ok") else 400
                return self._send_json(result, status=status)
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)
        # Customize: update edition metadata (Phase ν.2 — title, audience,
        # verse_popups, verse_marker_glyph, etc. — NOT the kind toggles)
        m = re.match(r"^/api/edition-meta/([a-z0-9-]+)$", self.path)
        if m:
            try:
                payload = self._read_body()
                result = api_save_edition_meta(m.group(1), payload)
                status = 200 if result.get("ok") else 400
                return self._send_json(result, status=status)
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)
        # Phase ν.5 — change-impact preview. Same payload shape as
        # /api/edition-meta save, but read-only: returns the
        # field-by-field diff between current state and proposal.
        # The /customize UI calls this before any save to show a
        # "you're about to change X, Y, Z" modal.
        m = re.match(r"^/api/edition-meta/([a-z0-9-]+)/preview$", self.path)
        if m:
            try:
                payload = self._read_body()
                result = api_preview_edition_changes(m.group(1), payload)
                status = 200 if "error" not in result else 400
                return self._send_json(result, status=status)
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)
        # Per-note toggle (Phase ρ.1) — add/remove a note ID from an
        # edition's disabled_note_ids list.
        m = re.match(r"^/api/edition/([a-z0-9-]+)/note-toggle$", self.path)
        if m:
            try:
                payload = self._read_body()
                result = api_save_note_toggle(m.group(1), payload)
                status = 200 if result.get("ok") else 400
                return self._send_json(result, status=status)
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)
        # Publisher console save (Phase π.1)
        m = re.match(r"^/api/publisher/([a-z0-9-]+)$", self.path)
        if m:
            try:
                payload = self._read_body()
                result = api_save_publisher_meta(m.group(1), payload)
                status = 200 if result.get("ok") else 400
                return self._send_json(result, status=status)
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)
        return self._send_json({"error": "not found"}, status=404)

    @_safe_request
    def do_DELETE(self):
        if not self._check_admin_auth():
            return
        m = re.match(r"^/api/notes/([a-z0-9]+)/(\d+)$", self.path)
        if m:
            try:
                return self._send_json(api_delete(m.group(1), int(m.group(2))))
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)
        # Delete scenario (μ.2½)
        m = re.match(r"^/api/scenarios/([a-z0-9_-]+)$", self.path)
        if m:
            try:
                result = api_delete_scenario(m.group(1))
                status = 200 if result.get("ok") else 400
                return self._send_json(result, status=status)
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)
        # Delete a main cover (Phase π.4-B)
        m = re.match(r"^/api/covers/([a-z0-9-]+)/main$", self.path)
        if m:
            try:
                result = api_delete_cover_main(m.group(1))
                status = 200 if result.get("ok") else 400
                return self._send_json(result, status=status)
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)
        # Delete a per-book cover (Phase π.4-B)
        m = re.match(
            r"^/api/covers/([a-z0-9-]+)/book/([a-z0-9]+)$", self.path
        )
        if m:
            try:
                result = api_delete_cover_book(m.group(1), m.group(2))
                status = 200 if result.get("ok") else 400
                return self._send_json(result, status=status)
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)
        # Clear a source cache (Phase υ.1)
        m = re.match(r"^/api/sources/cache/([a-z0-9_-]+)$", self.path)
        if m:
            result = api_sources_cache_clear(m.group(1))
            return self._send_dict_result(result)
        return self._send_json({"error": "not found"}, status=404)

    @_safe_request
    def do_POST(self):
        if not self._check_admin_auth():
            return
        # Cover uploads (Phase π.4-B) — multipart/form-data, distinct
        # from the JSON-bodied PUT/POST endpoints below. Routed here
        # first so the multipart body isn't read as JSON.
        m = re.match(r"^/api/covers/([a-z0-9-]+)/main$", self.path)
        if m:
            return self._handle_cover_upload(m.group(1), None)
        m = re.match(
            r"^/api/covers/([a-z0-9-]+)/book/([a-z0-9]+)$", self.path
        )
        if m:
            return self._handle_cover_upload(m.group(1), m.group(2))
        # Source cache uploads (Phase υ.1) — multipart JSON drop
        m = re.match(r"^/api/sources/cache/([a-z0-9_-]+)/upload$", self.path)
        if m:
            return self._handle_sources_cache_upload(m.group(1))
        # Source cache fetch / fetch-all (Phase υ.1) — JSON body
        if self.path == "/api/sources/cache/_all/fetch":
            try:
                payload = self._read_body() or {}
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)
            result = api_sources_cache_fetch_all(force=bool(payload.get("force")))
            return self._send_dict_result(result)
        m = re.match(r"^/api/sources/cache/([a-z0-9_-]+)/fetch$", self.path)
        if m:
            try:
                payload = self._read_body() or {}
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)
            result = api_sources_cache_fetch(
                m.group(1),
                force=bool(payload.get("force")),
                url_override=payload.get("url_override") or None,
                parser_override=payload.get("parser_override") or None,
            )
            return self._send_dict_result(result)
        # Edition cloning (Phase ν.4) — JSON body, distinct path
        if self.path == "/api/editions/clone":
            try:
                payload = self._read_body()
                result = api_clone_edition(payload)
                status = 200 if result.get("ok") else 400
                return self._send_json(result, status=status)
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)
        # Backup restore (Phase ω.1) — POST {file, snapshot_id}
        if self.path == "/api/backups/restore":
            try:
                payload = self._read_body() or {}
            except Exception as e:
                return self._send_json({"error": str(e)}, status=400)
            result = api_restore_backup(
                payload.get("file") or "",
                payload.get("snapshot_id") or "",
            )
            if result.get("status") == "ok":
                return self._send_json(result)
            http_code = result.get("http") or 500
            return self._send_json({
                "error": result.get("code") or "internal_error",
                "message": result.get("message") or "",
            }, status=http_code)
        # Everything else: same as PUT — front-end uses POST for create
        return self.do_PUT()

    def _handle_sources_cache_upload(self, source_id: str):
        """Multipart JSON drop for /api/sources/cache/<id>/upload.
        Reads the body within a generous size cap and dispatches to
        api_sources_cache_upload (which validates JSON shape and
        atomically writes the cache file)."""
        try:
            length_header = self.headers.get("Content-Length", "")
            try:
                length = int(length_header)
            except ValueError:
                return self._send_json(
                    {"error": "missing or invalid Content-Length"},
                    status=400,
                )
            # Hard cap at twice the per-file limit (defensive against a
            # hostile client streaming an unbounded body).
            if length > SOURCES_UPLOAD_MAX_BYTES * 2:
                return self._send_json(
                    {"error": (
                        f"request too large: {length} bytes "
                        f"(max {SOURCES_UPLOAD_MAX_BYTES * 2})"
                    )}, status=413,
                )
            body = self.rfile.read(length) if length > 0 else b""
            content_type = self.headers.get("Content-Type", "")
            result = api_sources_cache_upload(source_id, body, content_type)
            return self._send_dict_result(result)
        except Exception as e:
            return self._send_json({"error": str(e)}, status=400)

    def _handle_cover_upload(self, edition_id: str,
                              book_code: str | None):
        """Read a multipart request body within the configured size
        cap, then dispatch to api_upload_cover_*."""
        try:
            length_header = self.headers.get("Content-Length", "")
            try:
                length = int(length_header)
            except ValueError:
                return self._send_json(
                    {"error": "missing or invalid Content-Length"},
                    status=400,
                )
            # Hard cap at twice the per-file limit so a hostile
            # client can't tie up the server with an unbounded read.
            from scripts.core.covers import UPLOAD_MAX_BYTES
            if length > UPLOAD_MAX_BYTES * 2:
                return self._send_json(
                    {"error": (
                        f"request too large: {length} bytes "
                        f"(max {UPLOAD_MAX_BYTES * 2})"
                    )}, status=413,
                )
            body = self.rfile.read(length) if length > 0 else b""
            content_type = self.headers.get("Content-Type", "")
            if book_code is None:
                result = api_upload_cover_main(
                    edition_id, body, content_type
                )
            else:
                result = api_upload_cover_book(
                    edition_id, book_code, body, content_type
                )
            status = 200 if result.get("ok") else 400
            return self._send_json(result, status=status)
        except Exception as e:
            return self._send_json({"error": str(e)}, status=400)


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




def main() -> int:
    p = argparse.ArgumentParser(description="Local web UI for the E-Bible note corpus.")
    p.add_argument("--host", default="127.0.0.1",
                   help="bind address (default: 127.0.0.1, localhost-only)")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--no-browser", action="store_true",
                   help="don't auto-open the browser")
    args = p.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.port}/"
    print(f"\n  E-Bible web — note editor")
    print(f"  serving at: {url}")
    print(f"  Ctrl-C to stop\n")

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
