#!/usr/bin/env python3
"""
note_diff.py — Diff two project states.

Compares ``content/notes/`` between two snapshots and reports added, deleted,
and modified notes. Each side can be:

  * A project directory containing ``content/notes/<code>.py``
  * A zip file (e.g. a previous save) — content/notes/*.py is found at any
    depth inside the zip.

Identity = ``(book, chapter, verse, suffix)``. A note appearing in B but
not A is **added**; in A but not B is **deleted**; in both with any tuple
field different is **modified** (sub-classified into anchor / kind / body
changes).

Examples:
    python3 scripts/note_diff.py prev_save.zip .
        # diff a previous save against the current working tree

    python3 scripts/note_diff.py v24.zip v25.zip
        # diff two saves

    python3 scripts/note_diff.py --book gen prev.zip .
        # one book only

    python3 scripts/note_diff.py --body-diff prev.zip .
        # include line-level diffs of changed bodies

Note loading is via ``ast.literal_eval`` — no code execution.

Exit codes:
    0  states identical
    1  differences found
    2  setup error (path doesn't exist, can't parse)
"""

import argparse
import difflib
import re
import sys
import zipfile
from pathlib import Path
from scripts.core.notes_io import load_notes_from_text
from scripts.core.html_utils import strip_tags

REPO_ROOT = Path(__file__).resolve().parent.parent

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BLUE = "\033[94m"
RESET = "\033[0m"


# ----------------------------------------------------------------------
# State loading
# ----------------------------------------------------------------------


NOTES_PATH_RE = re.compile(r"(?:^|/)content/notes/([^/]+)\.py$")


def load_state_from_dir(path: Path) -> dict:
    """Walk content/notes/*.py and return {(code, ch, v, suffix): tuple}."""
    notes_dir = path / "content" / "notes"
    if not notes_dir.is_dir():
        # Maybe path is already content/notes/
        if (path / "gen.py").is_file():
            notes_dir = path
        else:
            raise ValueError(f"no content/notes directory under {path}")
    state: dict = {}
    for f in sorted(notes_dir.glob("*.py")):
        if f.name == "__init__.py":
            continue
        code = f.stem
        notes = load_notes_from_text(f.read_text(encoding="utf-8"))
        if not notes:
            continue
        for tup in notes:
            if isinstance(tup, tuple) and len(tup) >= 8:
                ch, v, suffix = tup[:3]
                state[(code, ch, v, suffix)] = tup
    return state


def load_state_from_zip(path: Path) -> dict:
    state: dict = {}
    with zipfile.ZipFile(path) as zf:
        for info in zf.infolist():
            m = NOTES_PATH_RE.search(info.filename)
            if not m or m.group(1) == "__init__":
                continue
            code = m.group(1)
            with zf.open(info) as f:
                text = f.read().decode("utf-8")
            notes = load_notes_from_text(text)
            if not notes:
                continue
            for tup in notes:
                if isinstance(tup, tuple) and len(tup) >= 8:
                    ch, v, suffix = tup[:3]
                    state[(code, ch, v, suffix)] = tup
    return state


def load_state(p: Path) -> dict:
    if p.is_dir():
        return load_state_from_dir(p)
    if p.is_file() and p.suffix.lower() == ".zip":
        return load_state_from_zip(p)
    raise ValueError(f"not a directory or .zip: {p}")


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def word_count(html: str) -> int:
    return len(re.findall(r"\S+", strip_tags(html)))


def fmt_loc(key: tuple) -> str:
    code, ch, v, suffix = key
    return f"{code} {ch}:{v}{suffix or ''}"


def fmt_excerpt(body: str, max_chars: int = 70) -> str:
    return strip_tags(body)[:max_chars].strip()


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(
        description="Diff two project states (directory or zip).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("a", type=Path, help="state A (directory or .zip)")
    p.add_argument("b", type=Path, help="state B (directory or .zip)")
    p.add_argument("--book", help="filter to one book code")
    p.add_argument("--body-diff", action="store_true", help="show line-level diff of changed bodies")
    p.add_argument("--quiet", action="store_true", help="only print the summary line")
    p.add_argument("--verbose", action="store_true", help="show all changes (no truncation)")
    p.add_argument("--max-show", type=int, default=20, help="truncate per-section list (default 20)")
    args = p.parse_args()

    try:
        state_a = load_state(args.a)
        state_b = load_state(args.b)
    except (ValueError, zipfile.BadZipFile, OSError) as e:
        print(f"{RED}ERROR: {e}{RESET}", file=sys.stderr)
        sys.exit(2)

    if args.book:
        state_a = {k: v for k, v in state_a.items() if k[0] == args.book}
        state_b = {k: v for k, v in state_b.items() if k[0] == args.book}

    keys_a = set(state_a.keys())
    keys_b = set(state_b.keys())
    added = sorted(keys_b - keys_a)
    deleted = sorted(keys_a - keys_b)
    common = sorted(keys_a & keys_b)
    modified = [(k, state_a[k], state_b[k]) for k in common if state_a[k] != state_b[k]]

    # Sub-classify modifications
    n_anchor = sum(1 for _, a, b in modified if a[3] != b[3])
    n_kind = sum(1 for _, a, b in modified if a[4] != b[4])
    n_body = sum(1 for _, a, b in modified if a[7] != b[7])

    if not args.quiet:
        print(f"\n  comparing {args.a} → {args.b}")
        print(f"  A: {len(state_a):,} notes    B: {len(state_b):,} notes\n")

        limit = None if args.verbose else args.max_show

        if added:
            shown = added if limit is None else added[:limit]
            print(f"  {GREEN}+ ADDED ({len(added)}){RESET}")
            for k in shown:
                tup = state_b[k]
                kind = tup[4]
                anchor = tup[3]
                anchor_str = repr(anchor) if anchor else "(start)"
                print(f"    + {fmt_loc(k)} [{kind}] anchor={anchor_str}  ⟶  {fmt_excerpt(tup[7])!r}")
            if limit is not None and len(added) > limit:
                print(f"    … {len(added) - limit} more")
            print()

        if deleted:
            shown = deleted if limit is None else deleted[:limit]
            print(f"  {RED}- DELETED ({len(deleted)}){RESET}")
            for k in shown:
                tup = state_a[k]
                kind = tup[4]
                anchor = tup[3]
                anchor_str = repr(anchor) if anchor else "(start)"
                print(f"    - {fmt_loc(k)} [{kind}] anchor={anchor_str}  ⟶  {fmt_excerpt(tup[7])!r}")
            if limit is not None and len(deleted) > limit:
                print(f"    … {len(deleted) - limit} more")
            print()

        if modified:
            shown = modified if limit is None else modified[:limit]
            print(
                f"  {YELLOW}~ MODIFIED ({len(modified)}){RESET}  "
                f"{DIM}anchor: {n_anchor}  kind: {n_kind}  body: {n_body}{RESET}"
            )
            for k, a, b in shown:
                changes = []
                if a[3] != b[3]:
                    changes.append(f"anchor {a[3]!r}→{b[3]!r}")
                if a[4] != b[4]:
                    changes.append(f"kind {a[4]}→{b[4]}")
                if a[7] != b[7]:
                    wa, wb = word_count(a[7]), word_count(b[7])
                    delta = f"{wa}→{wb}"
                    changes.append(f"body {delta} words")
                print(f"    ~ {fmt_loc(k)}  {' · '.join(changes)}")
                if args.body_diff and a[7] != b[7]:
                    # Word-level diff using difflib's ndiff on plain text
                    a_words = strip_tags(a[7]).split()
                    b_words = strip_tags(b[7]).split()
                    diff = list(difflib.unified_diff(a_words, b_words, lineterm="", n=2))
                    for line in diff[3:][:12]:  # skip headers, cap at 12 lines
                        if line.startswith("+"):
                            print(f"        {GREEN}{line}{RESET}")
                        elif line.startswith("-"):
                            print(f"        {RED}{line}{RESET}")
                        else:
                            print(f"        {DIM}{line}{RESET}")
            if limit is not None and len(modified) > limit:
                print(f"    … {len(modified) - limit} more")
            print()

    # Summary
    total = len(added) + len(deleted) + len(modified)
    color = GREEN if total == 0 else YELLOW
    sym = "✓" if total == 0 else "⚠"
    print(
        f"  {color}{sym} note_diff: "
        f"+{len(added)}  -{len(deleted)}  ~{len(modified)}  "
        f"{DIM}(anchor:{n_anchor} kind:{n_kind} body:{n_body}){RESET}"
    )

    sys.exit(0 if total == 0 else 1)


if __name__ == "__main__":
    main()
