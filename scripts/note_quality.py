#!/usr/bin/env python3
"""
note_quality.py — Editorial quality flags for ``content/notes/<code>.py``.

Notes vary in depth as they're written across hundreds of chapters. This
script flags individual notes that may need editorial attention before
shipping. It is **advisory only** by default: it returns exit 0 unless an
ERROR-severity check fires (real bugs that would mis-render). Use
``--strict`` to make WARN-level findings fail the run as well.

Notes are read from disk via ``ast.literal_eval`` — no code execution —
so this is safe to run on any state of the working tree.

Checks
------

ERROR-severity (real bugs):

  * **empty-body**           ``body_html`` is empty or whitespace.
  * **whitespace-anchor**    Anchor has leading/trailing whitespace
                             (silently fails to match in the injector).
  * **malformed-html**       Unbalanced or unclosed tags in the body.

WARN-severity (style/depth):

  * **no-opener**            Body does not start with ``<strong>...</strong>``.
                             The convention is to open with a topic phrase.
  * **topic-only**           Has the opener but ≤ 5 words after it.
  * **too-short**            Total word count below ``--min-words`` (default 50).
  * **too-long**             Total word count above ``--max-words`` (default 200).
  * **presentational-tags**  Uses ``<i>`` or ``<b>`` instead of semantic
                             ``<em>`` / ``<strong>``.

Examples:
    python3 scripts/note_quality.py
    python3 scripts/note_quality.py --book gen
    python3 scripts/note_quality.py --check too-short
    python3 scripts/note_quality.py --min-words 30 --max-words 250
    python3 scripts/note_quality.py --strict        # fail on WARN too
    python3 scripts/note_quality.py --quiet
    python3 scripts/note_quality.py --verbose       # show all, not first 30

Exit codes:
    0  no ERROR findings (or empty filter result), or --strict not set
    1  ERROR findings, or WARN findings under --strict
    2  setup error (unknown book, parse failure)
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config  # noqa: E402
from scripts.core.html_utils import strip_tags

NOTES_DIR = REPO_ROOT / "content" / "notes"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

SEVERITY = {
    "empty-body": "ERROR",
    "whitespace-anchor": "ERROR",
    "malformed-html": "ERROR",
    "no-opener": "WARN",
    "topic-only": "WARN",
    "too-short": "WARN",
    "too-long": "WARN",
    "presentational-tags": "WARN",
}

CHECKS = list(SEVERITY.keys())

# ----------------------------------------------------------------------
# Per-body inspectors
# ----------------------------------------------------------------------

TAG_RE = re.compile(r"<(/?)(\w+)\b[^>]*?(/?)>")
VOID_TAGS = {
    "br",
    "hr",
    "img",
    "input",
    "meta",
    "link",
    "area",
    "base",
    "col",
    "embed",
    "param",
    "source",
    "track",
    "wbr",
}


def word_count(html: str) -> int:
    return len(re.findall(r"\S+", strip_tags(html)))


def detect_unclosed(html: str) -> str | None:
    """Return a description of the first imbalance, or None if the body is balanced."""
    stack = []
    for is_close, name, self_close in TAG_RE.findall(html):
        if name.lower() in VOID_TAGS or self_close == "/":
            continue
        if is_close == "/":
            if not stack:
                return f"unexpected </{name}>"
            if stack[-1] != name:
                return f"</{name}> closes <{stack[-1]}>"
            stack.pop()
        else:
            stack.append(name)
    if stack:
        return f"unclosed <{stack[-1]}>"
    return None


def has_opener(html: str) -> bool:
    return bool(re.match(r"^\s*<strong>", html))


def post_opener_words(html: str) -> int:
    """Word count after the leading ``<strong>...</strong>`` opener."""
    m = re.match(r"^\s*<strong>.*?</strong>", html, re.DOTALL)
    if not m:
        return word_count(html)
    return word_count(html[m.end() :])


def _presentational_tags(html: str) -> list[str]:
    """Return the sorted list of presentational tag names in use, e.g. ['b', 'i']."""
    return sorted({m.lower() for m in re.findall(r"<(?:/?)([ib])\b[^>]*>", html)})


# ----------------------------------------------------------------------
# Note loading — delegated to the canonical, LRU-cached loader.
# (ARCH-04 / 2026-05-11) The byte-identical duplicate that lived here
# pre-dated the consolidation work in β.2 + notes_io.load_notes; the
# canonical loader uses ast.literal_eval (same safety guarantee) and
# adds a `(path, mtime_ns)` LRU cache that the dashboard, citation
# index, glossary, and 87-book sweep tools already rely on.
# ----------------------------------------------------------------------

from scripts.core.notes_io import load_notes  # noqa: E402, F401


# ----------------------------------------------------------------------
# Check runner
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
# Per-kind word budgets — calibrated for each kind's typical density
# ----------------------------------------------------------------------
# These override the global --min-words / --max-words when a kind has
# an entry. Tuned empirically against the existing 1,371 notes.

KIND_BUDGETS: dict[str, tuple[int, int]] = {
    # Lexical / language family — terse by nature
    "lang-hebrew": (8, 150),
    "lang-aramaic": (8, 150),
    "lang-greek": (8, 150),
    "lang-amharic": (8, 150),
    "lang-geez": (8, 150),
    "lang-latin": (8, 150),
    "lang-syriac": (8, 150),
    "lang-arabic": (8, 150),
    "word": (5, 100),
    # Parallel / cross-reference — short with framing
    "parallel": (15, 350),
    # Source-critical / textual variant
    "source": (10, 250),
    # Commentary family — substantive
    "comm": (20, 500),
    "comm-ethiopian": (30, 600),
    "comm-catholic": (30, 600),
    "comm-orthodox": (30, 600),
    "comm-reformation": (30, 600),
    "comm-patristic": (30, 600),
    "comm-modern-critical": (30, 700),
    "comm-contextual": (30, 700),
}


def budget_for(kind: str, default_min: int, default_max: int) -> tuple[int, int]:
    """Return (min_words, max_words) for a given kind. Falls back to the
    global defaults if no entry. Sub-kind families inherit from base
    (e.g. comm-something-not-listed inherits from 'comm')."""
    if kind in KIND_BUDGETS:
        return KIND_BUDGETS[kind]
    # Inherit from kind family (the part before the first hyphen)
    if "-" in kind:
        base = kind.split("-", 1)[0]
        if base in KIND_BUDGETS:
            return KIND_BUDGETS[base]
    return (default_min, default_max)


def run_checks(book_code: str, notes, min_words: int, max_words: int, per_kind: bool = True):
    """Yield finding tuples: (book, ch, v, suffix, kind, check_name, detail, excerpt)."""
    for tup in notes:
        if not isinstance(tup, tuple) or len(tup) < 8:
            continue
        ch, v, suffix, anchor, kind, _title, _label, body = tup[:8]
        excerpt = strip_tags(body)[:60].strip()

        if not isinstance(body, str) or not body.strip():
            yield (book_code, ch, v, suffix, kind, "empty-body", "", excerpt)
            continue

        # Anchor whitespace — empty anchor (first note on verse) is intentional.
        if isinstance(anchor, str) and anchor and anchor != anchor.strip():
            yield (book_code, ch, v, suffix, kind, "whitespace-anchor", repr(anchor), excerpt)

        unclosed = detect_unclosed(body)
        if unclosed:
            yield (book_code, ch, v, suffix, kind, "malformed-html", unclosed, excerpt)

        opener = has_opener(body)
        if not opener:
            yield (book_code, ch, v, suffix, kind, "no-opener", "", excerpt)
        else:
            if post_opener_words(body) <= 5:
                yield (
                    book_code,
                    ch,
                    v,
                    suffix,
                    kind,
                    "topic-only",
                    f"{post_opener_words(body)} words after opener",
                    excerpt,
                )

        wc = word_count(body)
        kind_min, kind_max = budget_for(kind, min_words, max_words) if per_kind else (min_words, max_words)
        if wc < kind_min:
            yield (book_code, ch, v, suffix, kind, "too-short", f"{wc} words (kind budget: {kind_min}+)", excerpt)
        elif wc > kind_max:
            yield (book_code, ch, v, suffix, kind, "too-long", f"{wc} words (kind budget: ≤{kind_max})", excerpt)

        pres = _presentational_tags(body)
        if pres:
            yield (
                book_code,
                ch,
                v,
                suffix,
                kind,
                "presentational-tags",
                f"uses <{'>, <'.join(pres)}>",
                excerpt,
            )


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(
        description="Editorial quality flags for content/notes/<code>.py.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--book", help="check one book by code (e.g. 'gen')")
    p.add_argument("--check", choices=CHECKS, help="run only one check")
    p.add_argument("--min-words", type=int, default=50, help="too-short threshold (default 50)")
    p.add_argument("--max-words", type=int, default=200, help="too-long threshold (default 200)")
    p.add_argument(
        "--no-per-kind", action="store_true", help="use global --min/--max-words instead of per-kind budgets"
    )
    p.add_argument("--strict", action="store_true", help="fail on WARN as well as ERROR")
    p.add_argument("--quiet", action="store_true", help="only print the summary line")
    p.add_argument("--verbose", action="store_true", help="show all findings, not first --max-show")
    p.add_argument("--max-show", type=int, default=30, help="cap on findings displayed (default 30)")
    args = p.parse_args()

    books = config.load_books()
    if args.book:
        books = [b for b in books if b["code"] == args.book]
        if not books:
            print(f"{RED}ERROR: unknown book code {args.book!r}{RESET}", file=sys.stderr)
            sys.exit(2)

    findings = []
    total_notes = 0
    parse_failures = []

    for book in books:
        code = book["code"]
        path = NOTES_DIR / f"{code}.py"
        if not path.is_file():
            continue
        notes = load_notes(path)
        if notes is None:
            parse_failures.append(code)
            continue
        total_notes += len(notes)
        for f in run_checks(code, notes, args.min_words, args.max_words, per_kind=not args.no_per_kind):
            if args.check and f[5] != args.check:
                continue
            findings.append(f)

    if parse_failures:
        for code in parse_failures:
            print(f"{RED}ERROR: failed to parse content/notes/{code}.py{RESET}", file=sys.stderr)
        sys.exit(2)

    n_err = sum(1 for f in findings if SEVERITY.get(f[5]) == "ERROR")
    n_warn = sum(1 for f in findings if SEVERITY.get(f[5]) == "WARN")

    # Per-finding output
    if findings and not args.quiet:
        limit = None if args.verbose else args.max_show
        shown = findings if limit is None else findings[:limit]
        for book, ch, v, suffix, kind, check, detail, excerpt in shown:
            sev = SEVERITY.get(check, "INFO")
            color = RED if sev == "ERROR" else (YELLOW if sev == "WARN" else BLUE)
            loc = f"{book} {ch}:{v}{suffix}"
            if kind:
                loc += f" [{kind}]"
            detail_str = f" — {detail}" if detail else ""
            excerpt_str = f"  ⟶ {excerpt!r}" if excerpt else ""
            print(f"  {color}{loc}: {check}{RESET}{detail_str}{excerpt_str}")
        if limit is not None and len(findings) > limit:
            print(f"  … {len(findings) - limit} more (re-run with --verbose)")

    # Summary line
    bad = n_err > 0 or (args.strict and n_warn > 0)
    if bad:
        color, sym = RED, "✗"
    elif findings:
        color, sym = YELLOW, "⚠"
    else:
        color, sym = GREEN, "✓"
    print(
        f"\n{color}{sym} note_quality: "
        f"notes={total_notes}  flagged={len(findings)}  "
        f"errors={n_err}  warnings={n_warn}{RESET}"
    )
    if findings:
        by_check = Counter(f[5] for f in findings)
        parts = [f"{c}: {n}" for c, n in by_check.most_common()]
        print("  " + "  ".join(parts))

    if bad:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
