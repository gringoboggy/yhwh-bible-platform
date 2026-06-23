#!/usr/bin/env python3
"""
web_helpers.py — shared low-level helpers for the web.py UI server,
extracted in the god-module split (2026-05-26).

Pure relocation: every function/constant here was moved verbatim from
``scripts/web.py``. This module imports only stdlib + existing project
modules (never the other ``web_*`` modules, never ``web.py``) so it sits
at the bottom of the import DAG. ``scripts/web.py`` re-exports every
public name here so existing call sites — both ``from scripts import
web; web.X`` and ``from scripts.web import X`` — keep working unchanged.
The underscore names (``_files_signature``, ``_notes_dir_signature``,
``_patch_yaml_entry``, ``parse_note_id``, ``html_ref_id_from_note_id``,
...) are lazy-imported externally by ``scripts/api/*`` and by tests
via ``scripts.web``.
"""

from __future__ import annotations

import ast
import functools
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

from scripts.core import config, html_utils, notes_io  # noqa: E402

NOTES_DIR = REPO / "content" / "notes"


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


# note_quality + new_note are sibling scripts in the `scripts` package.
# Import them as normal package modules — NOT via spec_from_file_location
# on a REPO-relative path. A frozen PyInstaller build has no loose
# `scripts/*.py` on disk (the source lives in the bundled archive), so the
# old file-path loader raised FileNotFoundError at request time in the
# desktop app — breaking every endpoint that funnels through _nq()/_nn():
# /api/kinds (book-list load → "failed to load" toast), /api/template
# (new-note scaffold), and quality_for via /api/notes. A package import
# resolves from the archive when frozen and from disk in dev, and
# PyInstaller's static analysis detects these function-body imports so the
# modules get bundled. Kept lazy + cached via _nq()/_nn().
def _load_note_quality_helpers():
    from scripts import note_quality

    return note_quality


def _load_new_note_helpers():
    from scripts import new_note

    return new_note


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
        "attribution": attribution or "",
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
        d.get("attribution") or None,
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
    # Serialise in canonical note order (chapter, verse, suffix) so web-UI
    # writes stay sorted. Bare-verse (suffix == "") sorts before suffixed.
    for tup in sorted(notes, key=lambda t: (t[0], t[1], (0, "") if t[2] == "" else (1, t[2]))):
        ch, v, suffix, anchor, kind, title, label, body, *rest = tup
        attribution = rest[0] if rest else None
        lines.append("    (\n")
        lines.append(f"        {ch}, {v}, {suffix!r},\n")
        lines.append(f"        {anchor!r},\n")
        lines.append(f"        {kind!r},\n")
        lines.append(f"        {title!r},\n")
        lines.append(f"        {label!r},\n")
        lines.append(f"        {body!r},\n")
        # Only emit the 9th (attribution) field when it is a real, non-empty
        # string — never serialise an absent attribution as `{}`/None, which
        # would turn an 8-field note into a schema-violating 9-field tuple.
        if isinstance(attribution, str) and attribution.strip():
            lines.append(f"        {attribution!r},\n")
        lines.append("    ),\n")
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
    # Normalize a legacy alias (joh→jhn, …) before the canonical-keyed lookup,
    # else a user-supplied note_id with an alias book yields None and the web
    # editor can't navigate to the note. round-11 gap-1.
    book = books_idx.get(config.resolve_book_code(parsed["book"]))
    if not book:
        return None
    # mint-10: Strategy-B books have no id_prefix; fall back to bxx as the id base
    # (matches build_edition.py:139/336 + inject.py:691), or the web editor can't
    # navigate to notes in 2ch/ezr/neh/… whose live HTML ref-id is ref-<bxx>…
    prefix = book.get("id_prefix") or book.get("bxx")
    if not prefix:
        return None
    return f"ref-{prefix}{parsed['chapter']:02d}{parsed['verse']:02d}{parsed['suffix']}"


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
                lambda mm, quoted=quoted: f"{mm.group(1)}{quoted}{mm.group(3)}",
                new_body,
                count=1,
            )
        else:
            # Insert at the head of the body (after the key line)
            new_body = f"    {field}: {quoted}\n" + new_body

    return text[: m.start()] + head + new_body + text[m.end() :]


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


@functools.lru_cache(maxsize=1)
def _canons_index() -> dict:
    """Singleton load of canons.yaml — {canon_id: {label, description, books}}.

    §7.1 project-internal published data: canons.yaml is config that ships via a
    process restart, so it is cached for the process lifetime (mint-10: the prior
    docstring claimed "Cached load" but there was no cache). A test that swaps
    canons.yaml must call ``_canons_index.cache_clear()``."""
    canons_path = REPO / "content" / "canons.yaml"
    if not canons_path.is_file():
        return {}
    import yaml

    data = yaml.safe_load(canons_path.read_text(encoding="utf-8")) or {}
    return data.get("canons", {}) or {}
