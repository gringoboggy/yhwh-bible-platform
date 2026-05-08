#!/usr/bin/env python3
"""
bibliography.py — Index every scholarly source cited across the apparatus.

Walks ``content/notes/*.py``, finds occurrences of a curated list of
classical authors, rabbinic works, modern scholars, ANE texts, and
translations/versions, and reports counts plus the notes citing each.

The catalogue (``SOURCES`` below) is editable — add new entries as the
project's apparatus grows.

Examples:
    python3 scripts/bibliography.py
        # terminal summary, all sources

    python3 scripts/bibliography.py --category Rabbinic
        # one category only

    python3 scripts/bibliography.py --source "Rashi"
        # locate every citation of one source

    python3 scripts/bibliography.py --html bibliography.html
        # write a self-contained HTML report

    python3 scripts/bibliography.py --book gen
        # filter source notes to one book

Exit codes:
    0  ok
    2  setup error
"""

import argparse
import html
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config  # noqa: E402
from scripts.core.notes_io import load_notes_from_text
from scripts.core.html_utils import strip_tags

NOTES_DIR = REPO_ROOT / "content" / "notes"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


# ----------------------------------------------------------------------
# Curated source catalogue
# ----------------------------------------------------------------------
#
# Each entry: (display_label, regex_pattern). Patterns are compiled with
# re.UNICODE; use \b for word boundaries (works for ASCII-letter names).
# Add new sources freely as the project grows — order within a category
# only affects display order.

SOURCES: dict[str, list[tuple[str, str]]] = {
    "Patristic / classical Christian": [
        ("Augustine", r"\bAugustine\b"),
        ("Aquinas", r"\bAquinas\b"),
        ("Origen", r"\bOrigen\b"),
        ("Tertullian", r"\bTertullian\b"),
        ("Basil of Caesarea", r"\bBasil\b"),
        ("Jerome", r"\bJerome\b"),
        ("Chrysostom", r"\bChrysostom\b"),
        ("Athanasius", r"\bAthanasius\b"),
        ("Irenaeus", r"\bIrenaeus\b"),
        ("Clement (of Alexandria/Rome)", r"\bClement\b"),
        ("Cyril", r"\bCyril\b"),
        ("Ambrose", r"\bAmbrose\b"),
    ],
    "Hellenistic Jewish": [
        ("Philo", r"\bPhilo\b"),
        ("Josephus", r"\bJosephus\b"),
    ],
    "Rabbinic": [
        ("Rashi", r"\bRashi\b"),
        ("Maimonides / Rambam", r"\b(?:Maimonides|Rambam)\b"),
        ("Nahmanides / Ramban", r"\b(?:Nahmanides|Ramban)\b"),
        ("Ibn Ezra", r"\bIbn Ezra\b"),
        ("Bereshit / Genesis Rabbah", r"\b(?:Bereshit|Genesis)\s+Rabbah\b"),
        ("Sifra", r"\bSifra\b"),
        ("Sifrei", r"\bSifrei\b"),
        ("Mekhilta", r"\bMekhilta\b"),
        ("Mishnah", r"\bMishnah\b"),
        ("Tosefta", r"\bTosefta\b"),
        ("Talmud (Bavli/Yerushalmi)", r"\b(?:Talmud|Bavli|Yerushalmi|Gemara)\b"),
        ("Targum Onkelos", r"\bTargum\s+Onkelos\b|\bTargum\s+Onqelos\b"),
        ("Targum Jonathan", r"\bTargum\s+(?:Pseudo-)?Jonathan\b"),
        ("Zohar", r"\bZohar\b"),
    ],
    "Translations / versions": [
        ("LXX / Septuagint", r"\b(?:LXX|Septuagint)\b"),
        ("Vulgate", r"\bVulgate\b"),
        ("Peshitta", r"\bPeshitta\b"),
        ("Masoretic Text / WLC / MT", r"\b(?:Masoretic|WLC)\b|\bMT\b(?!\.)"),
        ("Aquila", r"\bAquila\b"),
        ("Symmachus", r"\bSymmachus\b"),
        ("Theodotion", r"\bTheodotion\b"),
        ("Samaritan Pentateuch / SP", r"\bSamaritan\s+Pentateuch\b|\bSP\b(?!\.)"),
    ],
    "Pseudepigrapha / Second Temple": [
        ("1 Enoch", r"\b1\s+Enoch\b"),
        ("Jubilees", r"\bJubilees\b"),
        ("Dead Sea Scrolls / Qumran / DSS", r"\bDead Sea Scrolls\b|\bQumran\b|\bDSS\b"),
        ("4Q…", r"\b4Q\d+\b"),
        ("Apocalypse of …", r"\bApocalypse of \w+"),
        ("Testament of …", r"\bTestament of \w+"),
    ],
    "Ancient Near Eastern": [
        ("Enuma Elish", r"\bEnuma\s+Elish\b"),
        ("Atrahasis", r"\bAtrahasis\b|\bAtra-?hasis\b"),
        ("Gilgamesh", r"\bGilgamesh\b"),
        ("Tiamat", r"\bTiamat\b"),
        ("Marduk", r"\bMarduk\b"),
        ("Baal Cycle", r"\bBaal\s+Cycle\b"),
        ("Code of Hammurabi", r"\bHammurabi\b"),
        ("Ugaritic", r"\bUgaritic\b"),
    ],
    "Modern critical scholarship": [
        ("Westermann", r"\bWestermann\b"),
        ("Wenham", r"\bWenham\b"),
        ("Brueggemann", r"\bBrueggemann\b"),
        ("von Rad", r"\bvon\s+Rad\b"),
        ("Cassuto", r"\bCassuto\b"),
        ("Speiser", r"\bSpeiser\b"),
        ("Walton", r"\bWalton\b"),
        ("Sailhamer", r"\bSailhamer\b"),
        ("Sarna", r"\bSarna\b"),
        ("Alter (Robert)", r"\bAlter\b"),
        ("Levenson", r"\bLevenson\b"),
        ("Kugel", r"\bKugel\b"),
        ("Friedman (Richard)", r"\bFriedman\b"),
        ("Smith (Mark)", r"\bMark Smith\b"),
        ("Hamilton", r"\bHamilton\b"),
    ],
}


# ----------------------------------------------------------------------
# Loading & scan
# ----------------------------------------------------------------------




def scan(book_filter: str | None = None):
    """Return (counts, citations).

    counts:    {(category, label): count}
    citations: {(category, label): [(book, ch, v, suffix), …]}
    """
    compiled = {
        (cat, label): re.compile(pat, re.UNICODE)
        for cat, items in SOURCES.items()
        for label, pat in items
    }
    counts: Counter = Counter()
    citations: dict = defaultdict(list)

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
            if not isinstance(body, str):
                continue
            # Search the plain-text body so HTML attributes don't trigger matches.
            plain = strip_tags(body)
            for key, rx in compiled.items():
                hits = len(rx.findall(plain))
                if hits:
                    counts[key] += hits
                    citations[key].append((code, ch, v, suffix))
    return counts, citations


# ----------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------


def cmd_terminal(counts: Counter, citations: dict, category_filter: str | None) -> None:
    print()
    if not counts:
        print(f"  {DIM}no sources matched{RESET}")
        return
    for category, items in SOURCES.items():
        if category_filter and category != category_filter:
            continue
        cat_keys = [(category, label) for label, _ in items if counts.get((category, label), 0) > 0]
        if not cat_keys:
            continue
        print(f"  {BOLD}{category}{RESET}")
        for key in cat_keys:
            label = key[1]
            n = counts[key]
            n_notes = len(set(citations[key]))
            color = GREEN if n < 5 else (YELLOW if n < 15 else RED)
            print(f"    {color}{n:>4}{RESET}× {label:<40} {DIM}in {n_notes} note(s){RESET}")
        print()
    total = sum(counts.values())
    distinct = sum(1 for c in counts.values() if c > 0)
    print(f"  {DIM}{total:,} total mentions across {distinct} distinct sources.{RESET}")


def cmd_source(citations: dict, source_label: str) -> None:
    # Find the matching key (case-insensitive label match)
    matches = [k for k in citations if source_label.lower() in k[1].lower()]
    if not matches:
        print(f"  {DIM}no source matches {source_label!r}{RESET}")
        return
    for key in matches:
        category, label = key
        srcs = citations[key]
        print(f"\n  {BOLD}{label}{RESET} ({category}) — cited from {len(srcs)} note(s):\n")
        for s in sorted(set(srcs)):
            book, ch, v, suffix = s
            print(f"    {book} {ch}:{v}{suffix or ''}")


def cmd_html(counts: Counter, citations: dict, out_path: Path) -> None:
    """Write a self-contained HTML bibliography."""
    rows = []
    for category, items in SOURCES.items():
        cat_rows = []
        for label, _ in items:
            key = (category, label)
            n = counts.get(key, 0)
            if n == 0:
                continue
            n_notes = len(set(citations[key]))
            note_list = sorted(set(citations[key]))
            sample = ", ".join(f"{b} {c}:{v}{s or ''}" for b, c, v, s in note_list[:8])
            more = "" if len(note_list) <= 8 else f" + {len(note_list) - 8} more"
            cat_rows.append(
                f'<tr><td class="src">{html.escape(label)}</td>'
                f'<td class="num">{n}</td>'
                f'<td class="num">{n_notes}</td>'
                f'<td class="cite">{html.escape(sample)}{html.escape(more)}</td></tr>'
            )
        if cat_rows:
            rows.append(f'<h2>{html.escape(category)}</h2><table>'
                        '<thead><tr><th>source</th><th>mentions</th>'
                        '<th>notes</th><th>citations</th></tr></thead>'
                        f'<tbody>{"".join(cat_rows)}</tbody></table>')

    css = """
    :root {
      --paper: #f5f1e6; --ink: #2a2520; --ink-muted: #8a8378;
      --rule: #d4c9ad; --accent: #8b2330;
    }
    body { margin: 0 auto; max-width: 70rem; padding: 3rem clamp(1rem,4vw,4rem) 5rem;
           background: var(--paper); color: var(--ink);
           font-family: "Iowan Old Style", "Charter", "Cambria", Georgia, serif;
           line-height: 1.55; }
    h1 { margin-top: 0; font-weight: 600; letter-spacing: -0.005em;
         border-bottom: 2px solid var(--ink); padding-bottom: 0.5rem; }
    h2 { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.12em;
         color: var(--ink-muted); margin: 2.5rem 0 0.8rem;
         border-bottom: 1px solid var(--rule); padding-bottom: 0.4rem; font-weight: 600; }
    table { width: 100%; border-collapse: collapse; font-size: 0.86rem; }
    th { text-align: left; padding: 0.4rem 0.7rem; color: var(--ink-muted);
         text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.05em;
         border-bottom: 1px solid var(--rule); font-weight: 600; }
    td { padding: 0.4rem 0.7rem; border-bottom: 1px solid rgba(212,201,173,0.5); }
    td.num { text-align: right; font-variant-numeric: tabular-nums;
             font-family: "iA Writer Mono", ui-monospace, monospace;
             color: var(--accent); }
    td.cite { color: var(--ink-muted); font-family: "iA Writer Mono", ui-monospace, monospace;
              font-size: 0.78rem; }
    td.src { font-weight: 500; }
    """
    body = (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>Ethiopian Bible — Bibliography</title>"
        f"<style>{css}</style></head><body>"
        "<h1>Ethiopian Bible · Bibliography</h1>"
        "<p style='color:var(--ink-muted);font-style:italic;'>"
        "Sources cited across the commentary apparatus."
        "</p>" + "".join(rows) + "</body></html>"
    )
    out_path.write_text(body, encoding="utf-8")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(
        description="Index every scholarly source cited across the apparatus.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--book", help="restrict scan to one book")
    p.add_argument("--category", help="show one category only")
    p.add_argument("--source", help="show every citation of a single source (substring match)")
    p.add_argument("--html", type=Path, help="write a self-contained HTML report to this path")
    p.add_argument("--list-categories", action="store_true", help="list known categories and exit")
    args = p.parse_args()

    if args.list_categories:
        for cat in SOURCES:
            print(f"  {cat}  ({len(SOURCES[cat])} entries)")
        sys.exit(0)

    if args.book and args.book not in config.books_by_code():
        print(f"{RED}ERROR: unknown book code {args.book!r}{RESET}", file=sys.stderr)
        sys.exit(2)

    if args.category and args.category not in SOURCES:
        print(
            f"{RED}ERROR: unknown category {args.category!r}. "
            f"Known: {', '.join(SOURCES)}{RESET}",
            file=sys.stderr,
        )
        sys.exit(2)

    counts, citations = scan(args.book)

    if args.html:
        cmd_html(counts, citations, args.html)
        n_distinct = sum(1 for v in counts.values() if v > 0)
        size_kb = args.html.stat().st_size / 1024
        print(
            f"\033[92m✓ bibliography:\033[0m wrote {args.html} "
            f"({size_kb:.1f} KB · {n_distinct} sources · {sum(counts.values()):,} mentions)"
        )
        sys.exit(0)

    if args.source:
        cmd_source(citations, args.source)
        sys.exit(0)

    cmd_terminal(counts, citations, args.category)
    sys.exit(0)


if __name__ == "__main__":
    main()
