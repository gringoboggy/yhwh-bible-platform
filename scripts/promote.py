#!/usr/bin/env python3
"""
promote.py — Review prospect.py candidates and convert chosen ones into
real notes in ``content/notes/<book>.py``.

Two modes:

  Interactive review (default):
    python3 scripts/promote.py content/candidates/gen_ch_003.json
    → walks pending candidates, prompts [s]kip / [p]romote / [v]iew / [q]uit

  Direct promotion (scriptable / sandbox-friendly):
    python3 scripts/promote.py content/candidates/gen_ch_003.json \\
        --promote-id gen-3-15-002
    → promotes one candidate by id, no prompts

Promotion writes a tuple to the target ``<book>.py`` at the correct
sort position (by chapter, verse, suffix), then updates the candidate's
``status`` field in the queue file so re-runs skip already-promoted items.

Suffix selection: lowest free single-letter (a..z) not already used on
the (chapter, verse). Falls back to empty if no notes exist on that verse.

Exit codes:
    0  one or more candidates promoted (or queue completed)
    1  no candidates promoted
    2  setup error
"""

from __future__ import annotations

import argparse
import ast
import json
import logging
import re
import sys
import warnings
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.find_anchor import load_existing_anchors  # noqa: E402
from scripts.core.notes_io import ensure_backup, atomic_write  # noqa: E402  (Phase χ.6 fix)
from scripts.core.html_sandbox import sandbox_ai_html  # noqa: E402  (Phase ξ.15)
from scripts.core.matrix import AI_DRAFTED_KINDS  # noqa: E402  (Phase ξ.15)
from scripts.core.canonical_verse_counts import (  # noqa: E402  (coord guards)
    coord_in_canonical_extent,
    html_chapter_count,
)

NOTES_DIR = REPO_ROOT / "content" / "notes"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


# ----------------------------------------------------------------------
# Suffix selection
# ----------------------------------------------------------------------


def pick_free_suffix(existing_suffixes: set[str]) -> str:
    """Pick the lowest single-letter suffix not in use. If '' is free,
    returns '' (the natural default for first note on a verse)."""
    if "" not in existing_suffixes:
        return ""
    for ch in "abcdefghijklmnopqrstuvwxyz":
        if ch not in existing_suffixes:
            return ch
    raise RuntimeError("All a..z suffixes used on this verse — extend the suffix scheme.")


def note_already_exists(
    notes_path: Path,
    chapter: int,
    verse: int,
    kind: str,
    body: str,
    attribution: str | None,
) -> bool:
    """N-W4 fix (γ.4.6.B follow-up) — return True iff a tuple with
    identical (chapter, verse, kind, body, attribution) already exists
    in ``notes_path``.

    Without this check, re-running batch-style promotion on a candidate
    set that was already promoted produces duplicate tuples with the
    NEXT free suffix letter ('c' after 'a'+'b'), because pick_free_suffix
    only checks slot occupation, not content equality. This caused the
    χ-cluster promote bug discovered during γ.4.6.B: 2630 attempted /
    2630 promoted should have been ~50 promoted + ~880 skipped.

    Body comparison is exact-equal (no normalization); attribution
    comparison handles None ↔ '' equivalence for the pre-9th-field
    legacy 8-tuple form. Different body or different attribution on the
    same (ch, v, kind) is treated as a legitimately-distinct note
    (e.g., topic-nave routinely has multiple bodies per verse with
    different topic lists).
    """
    if not notes_path.is_file():
        return False
    try:
        tree = ast.parse(notes_path.read_text(encoding="utf-8"))
    except SyntaxError:
        return False
    notes = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "NOTES":
                    try:
                        notes = ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        return False
                    break
    norm_attr = (attribution or "").strip()
    for tup in notes:
        if not isinstance(tup, tuple) or len(tup) < 8:
            continue
        tch, tv, _tsuffix, _tanchor, tkind = tup[:5]
        if tch != chapter or tv != verse or tkind != kind:
            continue
        tbody = tup[7] if len(tup) > 7 else ""
        if tbody != body:
            continue
        tattr = (tup[8] if len(tup) > 8 else "") or ""
        if tattr.strip() != norm_attr:
            continue
        return True
    return False


# ----------------------------------------------------------------------
# Tuple formatting (matches existing gen.py / others)
# ----------------------------------------------------------------------


def format_tuple_text(
    chapter: int,
    verse: int,
    suffix: str,
    anchor: str,
    kind: str,
    title: str,
    label: str,
    body: str,
    attribution: str | None = None,
) -> str:
    """Emit a Python tuple literal as a string, matched to the project's
    indentation style (4 spaces, multi-line for readability).

    Emits the 8-field legacy form when ``attribution`` is None or empty
    (keeps diffs minimal for unattributed notes during the migration
    phase). Emits the 9-field form when an attribution is provided.
    """

    # Helper: emit a Python string, preferring single quotes, escaping when
    # the string contains a single quote.
    def py_str(s: str) -> str:
        # Escape backslash FIRST (mint-9 #3 root cause), then embedded newlines,
        # so a body containing a literal "\" or newline can't produce an invalid
        # one-line Python string literal that silently drops the whole batch
        # (batch_insert_notes' post-splice ast.parse guard). Order matters: the
        # backslash pass must precede the \n/\r pass or it would double-escape
        # the escape sequences this function introduces.
        s = s.replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "\\r")
        if "'" not in s:
            return f"'{s}'"
        if '"' not in s:
            return f'"{s}"'
        # Both quote types present: use double quotes and escape interior "
        return '"' + s.replace('"', '\\"') + '"'

    base = (
        "    (\n"
        f"        {chapter}, {verse}, {py_str(suffix)}, {py_str(anchor)},\n"
        f"        {py_str(kind)}, {py_str(title)},\n"
        f"        {py_str(label)},\n"
        f"        {py_str(body)},\n"
    )
    if attribution and attribution.strip():
        base += f"        {py_str(attribution)},\n"
    return base + "    ),\n"


# ----------------------------------------------------------------------
# Insertion into <book>.py
# ----------------------------------------------------------------------


def insert_note_into_book_file(
    book_path: Path,
    chapter: int,
    verse: int,
    suffix: str,
    anchor: str,
    kind: str,
    title: str,
    label: str,
    body: str,
    attribution: str | None = None,
) -> bool:
    """Insert the new note tuple at the right sort position. Returns True
    on success, False if the file structure doesn't match expectations.

    ``attribution`` is the optional 9th tuple field (v28a-4 schema). When
    set, the emitted tuple is 9-field; when None or empty, 8-field legacy.
    """

    text = book_path.read_text(encoding="utf-8")

    # Parse to find the NOTES list and its existing tuples
    try:
        tree = ast.parse(text)
    except SyntaxError:
        print(f"  {RED}✗ {book_path.name} has a syntax error{RESET}", file=sys.stderr)
        return False

    notes_assign = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "NOTES":
                    notes_assign = node
                    break

    if not notes_assign or not isinstance(notes_assign.value, ast.List):
        print(f"  {RED}✗ {book_path.name} has no recognisable NOTES list{RESET}", file=sys.stderr)
        return False

    # Determine the insertion line (1-indexed) by scanning existing tuples.
    # Strategy: walk tuples in order, find the index where ours sorts in.
    # Sort key: (chapter, verse, suffix_rank).
    def suffix_rank(s: str) -> tuple:
        # '' sorts first; then 'a','b','c'... in alphabetical order.
        return (0, "") if s == "" else (1, s)

    new_key = (chapter, verse, suffix_rank(suffix))

    insert_after_lineno = None  # if None, insert at start of list
    elts = notes_assign.value.elts

    for tup in elts:
        if not isinstance(tup, ast.Tuple) or len(tup.elts) < 8:
            continue
        try:
            tch = ast.literal_eval(tup.elts[0])
            tv = ast.literal_eval(tup.elts[1])
            tsuf = ast.literal_eval(tup.elts[2])
        except (ValueError, SyntaxError):
            continue
        existing_key = (tch, tv, suffix_rank(tsuf))
        if existing_key < new_key:
            insert_after_lineno = tup.end_lineno  # last line of the tuple
        # else: keep scanning (existing list may be unsorted)

    if insert_after_lineno is None:
        # Insert at the start of the list (after `NOTES = [`)
        # Find the line of NOTES = [ and insert after it.
        list_open_line = notes_assign.value.lineno
        insert_after_lineno = list_open_line

    # Build the new tuple text
    new_tuple_text = format_tuple_text(chapter, verse, suffix, anchor, kind, title, label, body, attribution)

    # Splice into the file
    lines = text.splitlines(keepends=True)
    new_lines = lines[:insert_after_lineno] + [new_tuple_text] + lines[insert_after_lineno:]
    new_text = "".join(new_lines)

    # Sanity: the file should still parse
    try:
        ast.parse(new_text)
    except SyntaxError as e:
        print(f"  {RED}✗ insertion produced invalid Python: {e}{RESET}", file=sys.stderr)
        return False

    ensure_backup(book_path)
    atomic_write(book_path, new_text)
    return True


def batch_insert_notes(book_path: Path, new_notes: list[dict], *, skip_existing: bool = True) -> int:
    """Insert many notes into a ``<book>.py`` NOTES list in ONE read+write.

    Efficient alternative to calling ``insert_note_into_book_file`` per note
    (which is O(filesize) each → O(n²) for a bulk promote). Existing tuples are
    preserved byte-for-byte; new tuples are spliced at their sorted
    ``(chapter, verse, suffix)`` positions. Suffixes are assigned free per verse,
    considering both existing notes AND notes inserted earlier in this batch.

    ``new_notes`` items are dicts with keys: chapter/ch, verse/v, kind, body
    (required) and anchor, title, label, attribution (optional). Returns the
    number inserted. ``skip_existing`` dedupes against an identical
    (chapter, verse, kind, body) already present (mirrors ``note_already_exists``).
    """
    text = book_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        logging.error(
            "batch_insert_notes: skipping %s and dropping its %d pending note(s); "
            "the file has a syntax error and could not be parsed: %s",
            book_path,
            len(new_notes),
            exc,
        )
        return 0
    notes_assign = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "NOTES" for t in node.targets):
            notes_assign = node
            break
    if notes_assign is None or not isinstance(notes_assign.value, ast.List):
        return 0

    def suffix_rank(s: str) -> tuple:
        return (0, "") if s == "" else (1, s)

    existing: list[tuple] = []  # (ch, v, suffix, end_lineno) in file order
    used_suffixes: dict[tuple, set] = {}
    existing_bodies: dict[tuple, set] = {}
    for tup in notes_assign.value.elts:
        if not isinstance(tup, ast.Tuple) or len(tup.elts) < 8:
            continue
        try:
            vals = ast.literal_eval(tup)
        except (ValueError, SyntaxError):
            continue
        ch, v, suf, _anchor, kind = vals[0], vals[1], vals[2], vals[3], vals[4]
        existing.append((ch, v, suf, tup.end_lineno))
        used_suffixes.setdefault((ch, v), set()).add(suf)
        existing_bodies.setdefault((ch, v, kind), set()).add(vals[7] if len(vals) > 7 else "")

    list_open_line = notes_assign.value.lineno
    inserts: list[tuple] = []  # (insert_after_lineno, sort_key, tuple_text)
    dropped = 0  # mint-10: out-of-extent notes silently skipped below; surfaced after the loop
    for n in new_notes:
        ch = n.get("chapter", n.get("ch"))
        v = n.get("verse", n.get("v"))
        if ch is None or v is None:
            warnings.warn(
                f"batch_insert_notes: dropping note for {book_path.stem!r} missing chapter/verse coordinates: {n!r}",
                stacklevel=2,
            )
            continue
        kind = n["kind"]
        body = n["body"]
        attribution = n.get("attribution")
        if not coord_in_canonical_extent(book_path.stem, ch, v):
            dropped += 1
            continue  # boundary guard: drop impossible coordinates (defense in depth)
        _html_chs = html_chapter_count(book_path.stem)
        if _html_chs and ch > _html_chs:
            dropped += 1
            continue  # base-HTML extent guard: chapter has no anchor to inject against
        if skip_existing and body in existing_bodies.get((ch, v, kind), set()):
            continue
        used = used_suffixes.setdefault((ch, v), set())
        suffix = pick_free_suffix(used)
        used.add(suffix)
        new_key = (ch, v, suffix_rank(suffix))
        after = list_open_line
        for ech, ev, esuf, eend in existing:
            if (ech, ev, suffix_rank(esuf)) < new_key:
                after = eend
            # else: keep scanning (existing list may be unsorted)
        txt = format_tuple_text(
            ch,
            v,
            suffix,
            n.get("anchor", ""),
            kind,
            n.get("title", "Note"),
            n.get("label", "Note"),
            body,
            attribution,
        )
        inserts.append((after, new_key, txt))

    if dropped:
        warnings.warn(
            f"batch_insert_notes: dropped {dropped} out-of-extent note(s) for {book_path.stem!r} "
            f"(coordinates outside the book's canonical / base-HTML extent)",
            stacklevel=2,
        )

    if not inserts:
        return 0
    lines = text.splitlines(keepends=True)
    by_line: dict[int, list] = {}
    for after, key, txt in inserts:
        by_line.setdefault(after, []).append((key, txt))
    for after in sorted(by_line, reverse=True):
        group = [t for _, t in sorted(by_line[after], key=lambda x: x[0])]
        lines[after:after] = group
    new_text = "".join(lines)
    try:
        ast.parse(new_text)
    except SyntaxError as exc:
        # Mirror the file-parse guard at the top of this function (mint-9 #3):
        # a post-splice SyntaxError means the GENERATED tuple text is invalid
        # (e.g. a body containing characters format_tuple_text failed to
        # escape), so the whole valid-but-undroppable batch was being discarded
        # SILENTLY. Log loudly before returning 0 so the drop is never invisible.
        logging.error(
            "batch_insert_notes: generated invalid Python for %s; dropping its %d pending note(s) "
            "rather than corrupt the file: %s",
            book_path,
            len(inserts),
            exc,
        )
        return 0
    ensure_backup(book_path)
    atomic_write(book_path, new_text)
    return len(inserts)


# ----------------------------------------------------------------------
# Promote a single candidate
# ----------------------------------------------------------------------


def promote_candidate(book: str, c: dict) -> tuple[bool, str]:
    """Promote one candidate. Returns (ok, suffix_used).

    The candidate's ``source_attribution`` (set by detectors) flows into
    the note tuple as the optional 9th field. If absent, the tuple is
    written in the legacy 8-field form.

    N-W4 idempotency: if a note with identical (chapter, verse, kind,
    body, attribution) already exists in the target book file, returns
    (False, "") to mark the promote as skipped without writing a
    duplicate tuple. See ``note_already_exists`` for the dedup contract.
    """
    book_path = NOTES_DIR / f"{book}.py"
    if not book_path.is_file():
        return False, ""

    chapter = c.get("chapter") or _chapter_from_id(c["id"])
    verse = c["verse"]

    # Coordinate guard: never promote a note whose (book, ch, v) is beyond the
    # book's canonical extent — OCR/parse noise (e.g. a detector resolving a
    # garbled reference) must not land an unplaceable note in the corpus.
    if not coord_in_canonical_extent(book, chapter, verse):
        return False, ""

    # Base-HTML extent guard: never promote a note whose chapter is beyond the
    # number of chapters the base HTML renders for this book — such a note has
    # no chapter anchor to inject against and is uninjectable (the aes ch11-16
    # parked residual is the motivating case; this stops FUTURE such coords).
    _html_chs = html_chapter_count(book)
    if _html_chs and chapter > _html_chs:
        return False, ""

    # Compose attribution for the note tuple. Prefer a fully-formed
    # ``source_attribution`` string; fall back to ``source_name`` plus a
    # generic PD/CC tag if only the name is present.
    attribution = (c.get("source_attribution") or "").strip() or None
    if not attribution and c.get("source_name"):
        attribution = c["source_name"]

    # ξ.15 belt-and-braces sandbox: any AI-drafted kind gets a second
    # pass through the strict allowlist before its body lands in
    # content/notes/. The detector already sandboxes at emit time;
    # this pass survives a future detector that forgets to sandbox,
    # and protects the interactive promote.py path the same as
    # batch_promote_xrefs.py. Idempotent — clean output is a no-op.
    draft_body = c["draft_body"]
    if c["kind"] in AI_DRAFTED_KINDS:
        draft_body = sandbox_ai_html(draft_body)

    # N-W4 idempotency check — must happen AFTER the sandbox pass
    # (sandbox-pass output is what gets written to the file, so dedup
    # must compare on that canonical form).
    if note_already_exists(book_path, chapter, verse, c["kind"], draft_body, attribution):
        return False, ""

    existing = load_existing_anchors(book_path, chapter, verse)
    used_suffixes = {s for (s, _, _, _) in existing}
    suffix = pick_free_suffix(used_suffixes)

    ok = insert_note_into_book_file(
        book_path,
        chapter,
        verse,
        suffix,
        c.get("anchor", ""),
        c["kind"],
        c.get("draft_title", "Note"),
        c.get("draft_label", "Note"),
        draft_body,
        attribution=attribution,
    )
    return ok, suffix


def _chapter_from_id(cid: str) -> int:
    # ids are formed as "<book>-<ch>-<v>-<idx>"
    parts = cid.split("-")
    return int(parts[-3])


# ----------------------------------------------------------------------
# Queue rewriting
# ----------------------------------------------------------------------


def update_queue_status(queue_path: Path, candidate_id: str, new_status: str) -> None:
    data = json.loads(queue_path.read_text(encoding="utf-8"))
    for c in data["candidates"]:
        if c["id"] == candidate_id:
            c["status"] = new_status
            break
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(
        queue_path,
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
    )


# ----------------------------------------------------------------------
# Display
# ----------------------------------------------------------------------


def render_candidate(c: dict, idx: int, total: int) -> None:
    print()
    print(f"{DIM}── {idx}/{total} ──{RESET}")
    print(
        f"  {BOLD}{c.get('chapter', '?')}:{c['verse']}{RESET}  "
        f"kind={BOLD}{c['kind']}{RESET}  "
        f"conf={c['confidence']}  "
        f"src={c['source_name']}"
    )
    if c.get("anchor"):
        print(f"  anchor: {YELLOW}{c['anchor']!r}{RESET}")
    print(f"  {DIM}{c.get('source_attribution', '')}{RESET}")
    print()
    body_clean = re.sub(r"<[^>]+>", "", c["draft_body"])
    body_wrapped = body_clean[:280] + ("…" if len(body_clean) > 280 else "")
    print(f"  {body_wrapped}")
    if c.get("reviewer_notes"):
        print(f"\n  {DIM}reviewer: {c['reviewer_notes']}{RESET}")
    print()


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(
        description="Review prospect.py candidates and promote them to real notes.",
    )
    p.add_argument("queue_path", type=Path, help="path to candidates JSON")
    p.add_argument(
        "--promote-id",
        help="non-interactive: promote one candidate by id, no prompt",
    )
    p.add_argument(
        "--promote-top",
        type=int,
        metavar="N",
        help="non-interactive: promote the top-N pending candidates by confidence",
    )
    p.add_argument(
        "--list",
        action="store_true",
        help="list all candidates with status, don't prompt",
    )
    args = p.parse_args()

    if not args.queue_path.is_file():
        print(f"{RED}✗ queue not found: {args.queue_path}{RESET}", file=sys.stderr)
        sys.exit(2)

    data = json.loads(args.queue_path.read_text(encoding="utf-8"))
    book = data["book"]

    # Add chapter back to each candidate (it was at top level in the queue)
    chapter = data["chapter"]
    for c in data["candidates"]:
        c["chapter"] = chapter

    if args.list:
        for c in data["candidates"]:
            anchor = (c.get("anchor") or "")[:30]
            print(
                f"  [{c.get('status', 'pending'):8s}] "
                f"{c['id']:25s}  "
                f"{c['kind']:18s}  "
                f"conf={c['confidence']}  "
                f"anchor={anchor!r}"
            )
        sys.exit(0)

    pending = [c for c in data["candidates"] if c.get("status") == "pending"]

    if args.promote_id:
        target = next((c for c in data["candidates"] if c["id"] == args.promote_id), None)
        if not target:
            print(f"{RED}✗ no candidate with id {args.promote_id!r}{RESET}", file=sys.stderr)
            sys.exit(2)
        ok, suffix = promote_candidate(book, target)
        if ok:
            update_queue_status(args.queue_path, target["id"], "promoted")
            print(
                f"  {GREEN}✓{RESET} promoted {target['id']} to "
                f"{book} {target['chapter']}:{target['verse']}{suffix} "
                f"as {target['kind']}"
            )
            sys.exit(0)
        else:
            print(f"  {RED}✗ promotion failed{RESET}", file=sys.stderr)
            sys.exit(1)

    if args.promote_top:
        pending.sort(key=lambda c: -c["confidence"])
        targets = pending[: args.promote_top]
        n_ok = 0
        for t in targets:
            ok, suffix = promote_candidate(book, t)
            if ok:
                update_queue_status(args.queue_path, t["id"], "promoted")
                print(f"  {GREEN}✓{RESET} {t['id']:25s} → {book} {t['chapter']}:{t['verse']}{suffix} as {t['kind']}")
                n_ok += 1
            else:
                print(f"  {RED}✗ {t['id']} failed{RESET}", file=sys.stderr)
        print(f"\n  {n_ok}/{len(targets)} promoted")
        sys.exit(0 if n_ok > 0 else 1)

    # Interactive
    if not pending:
        print(f"  {DIM}no pending candidates in queue{RESET}")
        sys.exit(0)

    print(f"\n{BOLD}promote{RESET} {DIM}{book} ch {chapter} · {len(pending)} pending{RESET}")

    n_promoted = 0
    for i, c in enumerate(pending, 1):
        render_candidate(c, i, len(pending))
        try:
            choice = input("  [s]kip / [p]romote / [v]iew full body / [q]uit > ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            break
        if choice == "q":
            break
        if choice == "v":
            print()
            print("  " + c["draft_body"])
            try:
                choice = input("  [s]kip / [p]romote / [q]uit > ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                break
        if choice == "p":
            ok, suffix = promote_candidate(book, c)
            if ok:
                update_queue_status(args.queue_path, c["id"], "promoted")
                print(f"  {GREEN}✓{RESET} promoted as {c['chapter']}:{c['verse']}{suffix}")
                n_promoted += 1
            else:
                print(f"  {RED}✗ promotion failed{RESET}")
        else:
            update_queue_status(args.queue_path, c["id"], "skipped")

    print(f"\n  {n_promoted} promoted out of {len(pending)} reviewed.\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
