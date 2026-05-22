#!/usr/bin/env python3
"""
citation_index.py — Inverse cross-reference graph for the apparatus.

For each verse-popover target, lists the notes that cross-reference it.
Useful for spotting:

  * **Over-cited passages**   verses cited from 10+ notes (the apparatus
                              is leaning on them; consider whether each
                              citation is earning its keep).
  * **Asymmetries**           if Genesis links abundantly to NT but NT
                              links rarely to Genesis, the reverse links
                              are missing.
  * **Coverage**              quickly see which key passages have no
                              inbound cross-refs at all.

Sources: hand-authored ``href="...vnote-CODE-CH-V"`` references in note
bodies (cross-canon links). Notes are loaded via ``ast.literal_eval`` —
no code execution. The same pattern that ``link_xrefs.py`` produces and
``check_xrefs.py`` validates.

Examples:
    python3 scripts/citation_index.py
        # default: top 20 most-cited targets

    python3 scripts/citation_index.py --top 50
    python3 scripts/citation_index.py --target gen 1 1
        # who cites Genesis 1:1?

    python3 scripts/citation_index.py --asymmetries
        # books cited far more than they cite (or vice versa)

    python3 scripts/citation_index.py --book gen
        # only consider citations originating in gen.py

    python3 scripts/citation_index.py --csv > citations.csv
        # full graph dump

Exit codes:
    0  ok
    2  setup error (unknown book, etc.)
"""

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config  # noqa: E402
from scripts.core.notes_io import load_notes_from_text

NOTES_DIR = REPO_ROOT / "content" / "notes"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Match either same-file (#vnote-…) or cross-file (file.html#vnote-…) hrefs.
HREF_RE = re.compile(r'href="(?:[^"]*?#)?vnote-([a-z0-9]+)-(\d+)-(\d+)([a-z]?)"')


# ----------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------


def build_graph(book_filter: str | None = None):
    """Return (citations, totals).

    citations: {(t_code, t_ch, t_v): [(s_code, s_ch, s_v, s_suffix), …]}
    totals:    Counter — note count per source book that has outbound refs.
    """
    citations: dict[tuple, list[tuple]] = defaultdict(list)
    src_book_count: Counter = Counter()

    for f in sorted(NOTES_DIR.glob("*.py")):
        if f.name == "__init__.py":
            continue
        code = f.stem
        if book_filter and code != book_filter:
            continue
        notes = load_notes_from_text(f.read_text(encoding="utf-8"))
        if not notes:
            continue
        for tup in notes:
            if not isinstance(tup, tuple) or len(tup) < 8:
                continue
            ch, v, suffix, _anchor, _kind, _title, _label, body = tup[:8]
            if not isinstance(body, str) or "vnote-" not in body:
                continue
            for m in HREF_RE.finditer(body):
                t_code, t_ch, t_v, _t_suffix = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
                citations[(t_code, t_ch, t_v)].append((code, ch, v, suffix))
            src_book_count[code] += 1

    return citations, src_book_count


# ----------------------------------------------------------------------
# Output modes
# ----------------------------------------------------------------------


def fmt_target(t):
    code, ch, v = t
    return f"{code} {ch}:{v}"


def fmt_source(s):
    code, ch, v, suffix = s
    return f"{code} {ch}:{v}{suffix or ''}"


def cmd_top(citations: dict, top_n: int) -> None:
    counts = Counter({t: len(srcs) for t, srcs in citations.items()})
    print(f"\n  {BOLD}Top {top_n} most-cited targets{RESET}\n")
    for target, n in counts.most_common(top_n):
        srcs = citations[target]
        # Sample of the source locations
        sample = ", ".join(fmt_source(s) for s in srcs[:3])
        more = "" if len(srcs) <= 3 else f"  +{len(srcs) - 3} more"
        # Color by intensity
        color = GREEN if n < 5 else (YELLOW if n < 10 else RED)
        print(f"  {color}{fmt_target(target):<14} {n:>3} {RESET}  {DIM}← {sample}{more}{RESET}")
    print(f"\n  {DIM}{len(citations):,} distinct targets cited overall.{RESET}")


def cmd_target(citations: dict, target: tuple) -> None:
    srcs = citations.get(target, [])
    print(f"\n  {BOLD}{fmt_target(target)}{RESET} is cited from {len(srcs)} note(s):\n")
    if not srcs:
        print(f"  {DIM}(none){RESET}")
        return
    for s in sorted(srcs):
        print(f"    {fmt_source(s)}")


def cmd_asymmetries(citations: dict) -> None:
    """Compute per-book outbound vs. inbound counts."""
    inbound: Counter = Counter()
    outbound: Counter = Counter()
    for target, srcs in citations.items():
        t_code = target[0]
        inbound[t_code] += len(srcs)
        for s in srcs:
            outbound[s[0]] += 1
    all_codes = sorted(set(inbound) | set(outbound))
    print(f"\n  {BOLD}Per-book inbound vs. outbound citations{RESET}\n")
    print(f"  {DIM}{'book':<8} {'in':>6} {'out':>6} {'gap':>7}{RESET}")
    rows = []
    for code in all_codes:
        i, o = inbound[code], outbound[code]
        gap = i - o  # positive = cited more than it cites
        rows.append((abs(gap), code, i, o, gap))
    # Sort by absolute gap, descending — biggest asymmetries first
    rows.sort(reverse=True)
    for _, code, i, o, gap in rows:
        if gap > 0:
            arrow = f"{GREEN}+{gap:>5}{RESET}"
        elif gap < 0:
            arrow = f"{RED}{gap:>6}{RESET}"
        else:
            arrow = f"{DIM}     0{RESET}"
        print(f"  {code:<8} {i:>6} {o:>6} {arrow}")
    print(f"\n  {DIM}gap = inbound - outbound. Positive: cited more than it cites.{RESET}")


def cmd_csv(citations: dict) -> None:
    w = csv.writer(sys.stdout)
    w.writerow(["target_book", "target_ch", "target_v", "source_book", "source_ch", "source_v", "source_suffix"])
    for target, srcs in sorted(citations.items()):
        for s in srcs:
            w.writerow([target[0], target[1], target[2], s[0], s[1], s[2], s[3]])


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(
        description="Inverse cross-reference graph: who cites what?",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--book", help="restrict source notes to one book")
    p.add_argument("--top", type=int, default=20, help="show N most-cited targets (default 20)")
    p.add_argument(
        "--target",
        nargs=3,
        metavar=("CODE", "CH", "V"),
        help="show source notes citing this target verse",
    )
    p.add_argument(
        "--asymmetries",
        action="store_true",
        help="report per-book inbound vs. outbound citation counts",
    )
    p.add_argument(
        "--csv",
        action="store_true",
        help="dump the full citation graph as CSV to stdout",
    )
    args = p.parse_args()

    if args.book and args.book not in config.books_by_code():
        print(f"{RED}ERROR: unknown book code {args.book!r}{RESET}", file=sys.stderr)
        sys.exit(2)

    citations, _ = build_graph(args.book)

    if not citations:
        print(f"{DIM}no cross-references found in scope{RESET}")
        sys.exit(0)

    if args.csv:
        cmd_csv(citations)
        sys.exit(0)
    if args.target:
        try:
            t = (args.target[0], int(args.target[1]), int(args.target[2]))
        except ValueError:
            print(f"{RED}ERROR: --target ch and v must be integers{RESET}", file=sys.stderr)
            sys.exit(2)
        cmd_target(citations, t)
        sys.exit(0)
    if args.asymmetries:
        cmd_asymmetries(citations)
        sys.exit(0)

    cmd_top(citations, args.top)
    sys.exit(0)


if __name__ == "__main__":
    main()
