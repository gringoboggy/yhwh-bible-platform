#!/usr/bin/env python3
"""
web_content.py — translation-compare, sample-HTML, backup
list/restore, ops-dashboard, dev-template-mtime, and corpus-progress
JSON API handlers, extracted from scripts/web.py in the god-module
split (2026-05-26).

Pure relocation: every function/constant here was moved verbatim from
``scripts/web.py``. ``scripts/web.py`` re-exports every name so the
route table + external importers (tests read ``CORPUS_TARGET`` via
``scripts.web``) keep resolving them in web.py's namespace.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

from scripts.api.preflight import api_preflight
from scripts.core import audit_log
from scripts.web_helpers import REPO
from scripts.web_sources import api_attribution_audit

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
    if notes_path.is_file():
        loaded = notes_io.load_notes_checked(notes_path, book=book)
        if isinstance(loaded, dict):
            return {
                "status": "error",
                "code": loaded.get("code", "notes_unparseable"),
                "http": loaded.get("http", 500),
                "message": loaded.get("error", "notes file unparseable"),
                "book": book,
            }
        all_notes = loaded
    else:
        all_notes = []
    # Use the canonical kind resolver (the same one build_edition + the
    # matrix call) so this preview's kind set is IDENTICAL to what the
    # build emits — categories->kinds expansion, the max_phase gate, and
    # the AI double-opt-in are all applied here, not re-hand-rolled.
    enabled_codes = config.enabled_kind_codes(edition, config.load_kinds())
    in_range = []
    for n in all_notes:
        if not n or len(n) < 8:
            continue
        ch = n[0]
        if ch < f or ch > t:
            continue
        kind = n[4]
        if kind not in enabled_codes:
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

    from scripts.core.html_sanitize import sanitize_html

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
                    # Sanitize the stored note body before interpolating: the
                    # /api/sample/ HTML is nonce-injected by _send_html, so an
                    # unsanitized <script> in a note body would receive a valid CSP
                    # nonce and execute (stored XSS). Mirror preview.py:133-135 and
                    # the inject.build_aside build path (mint-7 C1).
                    body = sanitize_html(str(n[7] or ""))
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
        "  Sample generated from the YHWH Ya' Way publishing platform.\n"
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

    # Step 0.5: for .py notes files, validate the snapshot PARSES as a
    # notes module BEFORE touching the live file. A corrupt snapshot
    # (truncated/garbled .bak) would otherwise be written verbatim,
    # leaving the source unparseable until manually fixed. Gate only
    # .py notes; binary restores (covers/images) are untouched.
    if abs_path.suffix == ".py":
        try:
            snapshot_text = snapshot_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return {
                "status": "error",
                "code": "invalid_snapshot",
                "http": 400,
                "message": "snapshot is not valid UTF-8 text",
            }
        if notes_io.load_notes_from_text(snapshot_text) is None:
            return {
                "status": "error",
                "code": "invalid_snapshot",
                "http": 400,
                "message": "snapshot does not parse as a notes file",
            }

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
