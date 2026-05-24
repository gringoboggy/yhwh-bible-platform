#!/usr/bin/env python3
"""
add_note.py — append one commentary note to a book's content/notes/<code>.py file.

What it does:
  1. Validate book code, kind code, chapter/verse against content/books.yaml
     and content/kinds.yaml.
  2. Validate that the anchor substring exists in the book's body HTML files.
  3. Auto-pick the next free suffix if multiple notes already exist on this verse.
  4. Refuse to insert a duplicate (same ch, v, suffix already present).
  5. Append a properly-formatted tuple to content/notes/<code>.py, preserving
     the file's existing structure.
  6. Optionally run the injector immediately (--inject) and re-audit (--verify).

Examples:
  # The minimum form — adds note, doesn't run injector or audit:
  python3 scripts/add_note.py --book gen --ch 12 --v 5 \\
      --anchor "took Sarai" --kind comm \\
      --title "Departure from Haran" \\
      --body "<strong>The call answered.</strong> Abram leaves..."

  # Add and inject in one command:
  python3 scripts/add_note.py --book 1ki --ch 8 --v 27 \\
      --anchor "the heaven and the heaven of heavens" --kind comm \\
      --title "Cosmology" \\
      --body "<strong>The threefold heavens.</strong> ANE cosmology..." \\
      --inject

  # Just preview — no file writes:
  python3 scripts/add_note.py --book gen --ch 12 --v 5 \\
      --anchor "took Sarai" --kind comm --title T --body B \\
      --dry-run

Conventions (from content/kinds.yaml and the project's existing tuple format):
  kind  =  word | comm | source
  label =  Hebrew | Note | Variant   (auto-set from kind unless --label given)
  title =  free-form short string used as the noteref's `title` attribute (tooltip)
  body  =  inline HTML; SHOULD lead with `<strong>Short title.</strong>`
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config
from scripts.core.notes_io import atomic_write, ensure_backup
from content.notes import load_notes

CONTENT_NOTES = REPO_ROOT / "content" / "notes"
EPUB_DIR = REPO_ROOT / "epub_working"

# Suffix order — matches existing project convention (avoid letters that look like
# the kind glyphs / verse-number suffixes; preserve historical preference for 'm').
SUFFIX_ORDER = ["m", "n", "p", "q", "b", "c", "d", "f", "g", "h", "k", "r", "s", "t"]


def err(msg):
    print(f"\033[91merror:\033[0m {msg}", file=sys.stderr)
    sys.exit(1)


def info(msg):
    print(f"  {msg}")


def pick_suffix(existing_suffixes, requested=None):
    """Return a free suffix for a (ch, v). If `requested` given, validate uniqueness."""
    if requested is not None:
        if requested in existing_suffixes:
            err(f"suffix {requested!r} already used at this (ch, v); used so far: {sorted(existing_suffixes)}")
        return requested
    # First note: empty suffix.
    if "" not in existing_suffixes:
        return ""
    # Otherwise pick first unused letter from the canonical order.
    for s in SUFFIX_ORDER:
        if s not in existing_suffixes:
            return s
    err("all suffix letters exhausted at this verse; manual selection needed")


def _find_verse_scope(text, book, ch, v):
    """Return (start, end) byte offsets for verse `v` of chapter `ch` in `text`.
    Returns None if scope can't be determined.

    Strategy A:  scope is bounded by <a id="v-CODE-CH-V">...next vn anchor or </p>.
    Strategy B:  scope is bounded by <span class="vn">V</span>...next vn span or </p>
                 within the current chapter's region.
    """
    bxx = book.get("bxx")
    strategy = book["strategy"]
    code = book["code"]
    if strategy == "A":
        # Strategy A: find <a ... id="v-CODE-CH-V" ...>...</a> then start AFTER
        # the closing </a> so we land in the verse text proper.
        opener = re.search(rf'id="v-{re.escape(code)}-{ch}-{v}(?:-x\d+)?"', text)
        if not opener:
            return None
        # Walk forward from id-match to the next </a> — this is the closing of
        # the verse-link anchor (verse-link inner content is short: just the vn span).
        close = text.find("</a>", opener.end())
        if close < 0:
            return None
        start = close + len("</a>")
        nxt = re.search(rf'id="v-{re.escape(code)}-{ch}-{v + 1}(?:-x\d+)?"', text[start:])
        if nxt:
            end = start + nxt.start()
        else:
            cp = text.find("</p>", start)
            end = cp if cp > 0 else min(len(text), start + 8000)
        return (start, end)
    # Strategy B: locate chapter scope, then verse-N marker within it
    if not bxx:
        return None
    cm = re.search(rf'id="ch-{bxx}-c{ch}\b', text)
    if not cm:
        return None
    # Chapter ends at next ch-bxx-c(N+1) or next book's bp anchor — be generous,
    # use 'next chapter anchor in same book' as primary.
    after = text[cm.end() :]
    nxt_ch = re.search(rf'id="ch-{bxx}-c{ch + 1}\b', after)
    chap_end = cm.end() + nxt_ch.start() if nxt_ch else min(len(text), cm.end() + 80000)
    chap_text = text[cm.end() : chap_end]
    # Within chap_text, find <span class="vn">V</span> and <span class="vn">V+1</span>
    vm = re.search(rf'<span class="vn">{v}</span>', chap_text)
    if not vm:
        return None
    vm_next = re.search(rf'<span class="vn">{v + 1}</span>', chap_text[vm.end() :])
    vstart = cm.end() + vm.end()
    vend = (cm.end() + vm.end() + vm_next.start()) if vm_next else chap_end
    return (vstart, vend)


def validate_anchor(book, ch, v, anchor):
    """Per-verse-precise anchor check. Returns the file path containing the
    matching verse scope. Errors out with diagnostic guidance on miss."""
    files = book.get("files") or []
    if not files:
        err(f"book {book['code']!r} has no files listed in content/books.yaml — cannot validate anchor")
    for fname in files:
        path = EPUB_DIR / fname
        if not path.exists():
            continue
        text = path.read_text()
        scope = _find_verse_scope(text, book, ch, v)
        if scope is None:
            continue
        start, end = scope
        if anchor in text[start:end]:
            return [fname]
        # Anchor not in verse — produce clean diagnostic.
        verse_snippet = re.sub(r"<[^>]+>", "", text[start:end])
        # Strip any leftover broken tag fragments (incomplete < without > in the
        # cut window) so the diagnostic isn't garbled.
        verse_snippet = re.sub(r"<[^>]*$", "", verse_snippet)
        verse_snippet = verse_snippet.strip()
        if len(verse_snippet) < 5:
            err(
                f"verse {ch}:{v} of {book['code']} appears empty in the body "
                f"(only verse markers, no text). The text 'In the beginning' is in a "
                f"different verse — try {ch}:{v + 1} or check the WEB English numbering."
            )
        err(
            f"anchor {anchor!r} not found inside {book['code']} {ch}:{v} (in {fname}).\n"
            f"      Verse text (first 300 chars): {verse_snippet[:300]}\n"
            f"      Check for: PDF double-spaces, curly vs straight quotes, "
            f"WEB-vocab differences ('young goat' vs 'kid')."
        )
    err(f"could not locate verse {ch}:{v} of {book['code']} in any of {files} — check chapter/verse numbers")


def format_tuple(ch, v, suffix, anchor, kind, title, label, body, attribution=None):
    """Pretty-print a notes tuple matching the existing file style.

    Emits 8-field legacy form when ``attribution`` is None or empty;
    9-field form (v28a-4 schema) when an attribution string is given.
    """

    # Use repr for safe escaping but prefer single quotes (matches existing data).
    def q(s):
        # Python's repr picks single quotes unless string contains apostrophes; force
        # single-quote when possible by manual escaping.
        if "'" not in s:
            return f"'{s}'"
        # Fall back to repr — Python will switch to double quotes or escape.
        return repr(s)

    line = f"    ({ch}, {v}, {q(suffix)}, {q(anchor)}, {q(kind)}, {q(title)}, {q(label)}, \n     {q(body)}"
    if attribution and attribution.strip():
        line += f",\n     {q(attribution)}"
    line += "),"
    return line


def append_to_notes_file(code, tuple_text):
    """Append `tuple_text` immediately before the closing `]` of the NOTES list."""
    fpath = CONTENT_NOTES / f"{code}.py"
    src = fpath.read_text()
    # The notes list is the FIRST top-level `]` (closing NOTES = [...]).
    # Find `NOTES = [` opening, then walk forward to its matching `]` at column 0.
    m = re.search(r"^NOTES\s*=\s*\[", src, re.MULTILINE)
    if not m:
        err(f"could not locate `NOTES = [` in {fpath}")
    # From end of opening, find the line that is exactly `]` at col 0.
    after = src[m.end() :]
    closing_match = re.search(r"^\]", after, re.MULTILINE)
    if not closing_match:
        err(f"could not locate closing `]` for NOTES list in {fpath}")
    closing_pos = m.end() + closing_match.start()
    # Insert tuple_text + newline before the closing `]`. Make sure there's a
    # newline before our insertion (the existing file conventionally has one).
    head = src[:closing_pos]
    tail = src[closing_pos:]
    # Trim trailing whitespace from head, then add proper formatting.
    head_rs = head.rstrip()
    new_src = head_rs + "\n" + tuple_text + "\n" + tail
    ensure_backup(fpath)
    atomic_write(fpath, new_src)
    return fpath


def run_injector(book):
    """Run the unified injector (scripts/inject.py) for this book. It replaces
    the lost source_archive/add_commentary.py + kings_session/strategy_b_inject.py
    and dispatches Strategy A/B internally."""
    code = book["code"]
    cmd = [sys.executable, "scripts/inject.py", "--book", code]
    print(f"\n→ running injector: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(REPO_ROOT), stdin=subprocess.DEVNULL, capture_output=True, text=True)
    if result.returncode != 0:
        err(f"injector failed (rc={result.returncode}):\nstdout: {result.stdout}\nstderr: {result.stderr}")
    print(result.stdout)


def run_audit():
    print("\n→ running audit ...")
    result = subprocess.run(
        [sys.executable, "audit.py", "--quiet"],
        cwd=str(REPO_ROOT),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if "ERROR" in result.stdout or result.returncode != 0:
        err("audit reported new errors — investigate before proceeding")


def main():
    p = argparse.ArgumentParser(
        description="Add one commentary note to a book.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n", 2)[2] if __doc__ else "",
    )
    p.add_argument("--book", required=True, help="book code (e.g. 'gen', '1ki')")
    p.add_argument("--ch", type=int, required=True, help="chapter number")
    p.add_argument("--v", type=int, required=True, help="verse number")
    p.add_argument(
        "--anchor",
        required=True,
        help="exact substring of WEB English in the verse to attach AFTER",
    )
    # --kind choices come from content/kinds.yaml so new kinds auto-register.
    _kind_codes = sorted(config.kinds_by_code().keys())
    p.add_argument(
        "--kind",
        required=True,
        choices=_kind_codes,
        help="note kind (controls inline glyph: "
        + ", ".join(f"{c}={config.get_kind(c)['symbol']}" for c in _kind_codes)
        + ")",
    )
    p.add_argument("--title", required=True, help="tooltip / aria title for the noteref")
    p.add_argument("--body", required=True, help="inline HTML body (start with <strong>Short title.</strong>)")
    p.add_argument("--label", default=None, help="label inside the aside (auto from kind unless given)")
    p.add_argument("--suffix", default=None, help="suffix letter (auto-picked next free if omitted)")
    p.add_argument(
        "--attribution",
        default=None,
        help="optional 9th tuple field: source / provenance string "
        "(e.g. 'User original', 'Strong\\'s H7779 (PD)', "
        "'Paraphrase summarising Westermann, Genesis 1-11 (1984)'). "
        "When set, the tuple is written in the v28a-4 9-field form.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="validate and print the tuple, but don't write the file",
    )
    p.add_argument("--inject", action="store_true", help="also run the injector after writing the note")
    p.add_argument("--verify", action="store_true", help="also run audit.py after injecting")
    args = p.parse_args()

    # 1. Validate book + kind
    try:
        book = config.get_book(args.book)
    except KeyError as e:
        err(str(e))
    try:
        kind = config.get_kind(args.kind)
    except KeyError as e:
        err(str(e))

    if book.get("ch_count", 0) > 0 and (args.ch < 1 or args.ch > book["ch_count"]):
        err(f"chapter {args.ch} out of range for {args.book} (1..{book['ch_count']})")
    if args.v < 1:
        err("verse must be >= 1")

    label = args.label or kind["label"]

    # 2. Validate anchor exists in the body
    print(f"Validating anchor in {book['title']!r} ch {args.ch}:{args.v} ...")
    hits = validate_anchor(book, args.ch, args.v, args.anchor)
    info(f"anchor found in: {', '.join(hits)}")

    # 3. Pick suffix — load existing notes, gather suffixes used at this (ch, v).
    existing = load_notes(args.book)
    used_suffixes = {n[2] for n in existing if n[0] == args.ch and n[1] == args.v}
    suffix = pick_suffix(used_suffixes, args.suffix)
    info(f"suffix chosen: {suffix!r}  (already in use at {args.ch}:{args.v}: {sorted(used_suffixes) or 'none'})")

    # 4. Format the tuple
    tup_text = format_tuple(
        args.ch,
        args.v,
        suffix,
        args.anchor,
        args.kind,
        args.title,
        label,
        args.body,
        args.attribution,
    )
    print(f"\nNew tuple:\n{tup_text}")

    if args.dry_run:
        print("\n(dry-run: file not modified)")
        return

    # 5. Append to content/notes/<code>.py
    fpath = append_to_notes_file(args.book, tup_text)
    print(f"\n✓ appended to {fpath.relative_to(REPO_ROOT)}")
    print(f"   total notes for {args.book}: {len(existing) + 1}")

    # 6. Optional inject + verify
    if args.inject:
        run_injector(book)
        if args.verify:
            run_audit()
    elif args.verify:
        # Verify-without-inject = just static audit (won't reflect new note in HTML)
        run_audit()
    else:
        print("\nNext steps:")
        print(f"  python3 scripts/inject.py --book {args.book} --dry-run")
        print("  python3 scripts/ebible.py verify")


if __name__ == "__main__":
    main()
