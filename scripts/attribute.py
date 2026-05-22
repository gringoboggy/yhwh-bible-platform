#!/usr/bin/env python3
"""
attribute.py — Assign provenance attribution to existing notes.

Walks each book's notes file, infers an attribution string from each note's
body (regex-based detection of cited PD-era sources and named modern
scholars), and inserts that string as the optional 9th tuple field.

The attribution is *descriptive of what's in the body*, not an editorial
claim about derivative authorship — it documents which sources are
referenced or summarised, so any reader can verify the attribution by
reading the note. Categories produced:

  "User original"
      No PD-era source or modern scholar named in the body.
  "User paraphrase; references Augustine"
      Body cites one or more PD-era sources only.
  "User paraphrase; summarises Westermann, Walton"
      Body names one or more modern scholars only.
  "User paraphrase; references Rashi, Targum; summarises Westermann"
      Both PD-era and modern scholarship cited.

Notes that already carry a 9th field are skipped untouched.

Modes:
    --dry-run         show what would change, don't write
    --auto-accept     write all suggestions without prompting (default)
    --interactive     prompt per book ([y]es / [n]o / [q]uit)

Targets:
    --book gen        operate on one book
    --all-books       walk every book in canonical order

Examples:
    python3 scripts/attribute.py --book gen --dry-run
    python3 scripts/attribute.py --book gen
    python3 scripts/attribute.py --all-books --interactive
    python3 scripts/attribute.py --all-books --auto-accept

Exit codes:
    0  all targeted books processed (or nothing to do)
    1  one or more books failed integrity check (rolled back)
    2  setup error (unknown book, file missing)
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config  # noqa: E402
from scripts.core.notes_io import atomic_write, ensure_backup  # noqa: E402

NOTES_DIR = REPO_ROOT / "content" / "notes"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


# ----------------------------------------------------------------------
# Curated detection vocabularies
# ----------------------------------------------------------------------

# Modern (still-copyrighted) scholars — paraphrase + name-attribution is
# academic-standard fair use. We document the citation explicitly so the
# reader can audit it.
MODERN_SCHOLARS = [
    "Westermann",
    "Wenham",
    "Brueggemann",
    "von Rad",
    "Childs",
    "Walton",
    "Sailhamer",
    "Sarna",
    "Fox",
    "Levenson",
    "Kugel",
    "Alter",
    "Goldingay",
    "Bauckham",
    "Hays",
    "Levine",
    "Dunn",
    "Witherington",
    "Carson",
    "Beale",
    "Sanders",
    "Hahn",
    "Pannenberg",
    "Moltmann",
    "Ratzinger",
    "Schnackenburg",
    "N.T. Wright",
    "Tom Wright",
    "G.E. Wright",
    "Davies",
    "Stuhlmacher",
    "Fitzmyer",
    "Brown",
    "Meyers",
    "Collins",
    "Coogan",
    "Knoppers",
    "Cogan",
    "Tadmor",
    "Milgrom",
    "Sarna",
    "Schiffman",
    "VanderKam",
    "Nickelsburg",
    "Stuckenbruck",
    "Charlesworth",
    "Sparks",
]

# Pre-1928 / public-domain authors and sources. Mentions here are
# uncontroversial — the works are PD and the names are part of the
# scholarly tradition.
PD_SOURCES = [
    # Patristic
    "Augustine",
    "Origen",
    "Jerome",
    "Chrysostom",
    "Aquinas",
    "Basil",
    "Tertullian",
    "Irenaeus",
    "Cyprian",
    "Athanasius",
    "Cyril",
    "Theodoret",
    "Bede",
    "Anselm",
    "Bonaventure",
    "Gregory of Nyssa",
    "Gregory of Nazianzus",
    "Pseudo-Dionysius",
    "Eusebius",
    "Ambrose",
    "Hilary",
    "Lactantius",
    # Reformation
    "Luther",
    "Calvin",
    "Zwingli",
    "Melanchthon",
    "Wycliffe",
    "Tyndale",
    # Jewish — medieval
    "Rashi",
    "Maimonides",
    "Rambam",
    "Ibn Ezra",
    "Nachmanides",
    "Ramban",
    "Sforno",
    "Saadia",
    "Rashbam",
    "Radak",
    # Jewish — Second Temple / rabbinic
    "Targum",
    "Targumim",
    "Onqelos",
    "Pseudo-Jonathan",
    "Talmud",
    "Mishnah",
    "Midrash",
    "Genesis Rabbah",
    "Tanhuma",
    "Pirke Avot",
    "Tosefta",
    "Mekhilta",
    "Sifra",
    "Sifre",
    "Philo",
    "Josephus",
    # Pseudepigrapha (PD via Charles 1913)
    "1 Enoch",
    "Jubilees",
    "4 Ezra",
    "2 Baruch",
    "Apocalypse of Abraham",
    "Testament of",
    # Versions
    "Septuagint",
    "LXX",
    "Vulgate",
    "Peshitta",
    "Old Latin",
    "Aquila",
    "Symmachus",
    "Theodotion",
    # ANE primary sources (PD)
    "Enuma Elish",
    "Gilgamesh",
    "Atrahasis",
    "Code of Hammurabi",
    "Hammurabi",
    "Sumerian",
    "Akkadian text",
    "Ugaritic",
    "Baal Cycle",
    "Ras Shamra",
    # Ethiopian distinctive
    "Andemta",
    "Synaxarium",
    "Fetha Nagast",
    "Kebra Nagast",
    # Other early Christian / Gnostic
    "Gospel of Thomas",
    "Nag Hammadi",
    "Apocryphon",
]


def _build_pattern(names: list[str]) -> re.Pattern:
    """Whole-word, case-insensitive multi-name pattern."""
    # Sort longer names first so 'von Rad' wins over 'Rad' if both were listed.
    sorted_names = sorted(set(names), key=len, reverse=True)
    parts = [re.escape(n) for n in sorted_names]
    return re.compile(r"\b(" + "|".join(parts) + r")\b", re.IGNORECASE)


_MODERN_RE = _build_pattern(MODERN_SCHOLARS)
_PD_RE = _build_pattern(PD_SOURCES)


def _strip_html(s: str) -> str:
    """Quick-and-dirty HTML strip for text-content matching."""
    return re.sub(r"<[^>]+>", " ", s)


def _format_list(items: list[str], cap: int = 3) -> str:
    if len(items) <= cap:
        return ", ".join(items)
    return ", ".join(items[:cap]) + ", et al."


def infer_attribution(body_html: str) -> str:
    """Build an attribution string from a note's body. Always returns a
    non-empty descriptor — at minimum 'User original'."""
    plain = _strip_html(body_html)

    # Preserve original casing of matches but de-dupe by lowercase.
    seen = set()
    pd_hits = []
    for m in _PD_RE.finditer(plain):
        canon = m.group(1)
        key = canon.lower()
        if key not in seen:
            seen.add(key)
            pd_hits.append(canon)

    seen_m = set()
    modern_hits = []
    for m in _MODERN_RE.finditer(plain):
        canon = m.group(1)
        key = canon.lower()
        if key not in seen_m:
            seen_m.add(key)
            modern_hits.append(canon)

    parts = []
    if pd_hits:
        parts.append(f"references {_format_list(pd_hits)}")
    if modern_hits:
        parts.append(f"summarises {_format_list(modern_hits)}")

    if not parts:
        return "User original"
    return "User paraphrase; " + "; ".join(parts)


# ----------------------------------------------------------------------
# Per-book rewrite
# ----------------------------------------------------------------------


def _q(s: str) -> str:
    """Emit a Python string literal, single-quoted unless the string
    itself contains a single quote (then double-quoted with escaping)."""
    if "'" not in s:
        return f"'{s}'"
    if '"' not in s:
        return f'"{s}"'
    return '"' + s.replace('"', '\\"') + '"'


def attribute_book(book_path: Path, dry_run: bool) -> dict:
    """Process one book file. Returns stats dict with keys:
    scanned        — total tuples in the file
    already_attr   — tuples that already had a 9th field (skipped)
    attributed     — tuples newly attributed (changed)
    skipped        — tuples skipped because of unparseable shape
    breakdown      — {'User original': N, 'User paraphrase; …': N, …}
    """
    text = book_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        return {"error": f"syntax error in {book_path.name}: {e}"}

    notes_assign = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "NOTES":
                    notes_assign = node
                    break
        if notes_assign:
            break

    if not notes_assign or not isinstance(notes_assign.value, ast.List):
        return {"error": f"no NOTES list found in {book_path.name}"}

    stats = {
        "scanned": 0,
        "already_attr": 0,
        "attributed": 0,
        "skipped": 0,
        "breakdown": {},
    }

    # Collect insertion ops: (line_number_to_insert_before, attribution_text)
    # We insert the attribution line just before the `),` (end_lineno) line.
    insertions: list[tuple[int, str]] = []

    for tup_node in notes_assign.value.elts:
        if not isinstance(tup_node, ast.Tuple):
            stats["skipped"] += 1
            continue
        stats["scanned"] += 1
        n_fields = len(tup_node.elts)

        if n_fields >= 9:
            stats["already_attr"] += 1
            continue
        if n_fields < 8:
            stats["skipped"] += 1
            continue

        # Read out the body field (index 7) to infer attribution
        try:
            body = ast.literal_eval(tup_node.elts[7])
        except (ValueError, SyntaxError):
            stats["skipped"] += 1
            continue
        if not isinstance(body, str):
            stats["skipped"] += 1
            continue

        attribution = infer_attribution(body)
        stats["breakdown"][attribution] = stats["breakdown"].get(attribution, 0) + 1
        stats["attributed"] += 1

        # The line containing `),` is tup_node.end_lineno (1-indexed).
        # We want to insert the attribution line BEFORE that line.
        insertions.append((tup_node.end_lineno, attribution))

    if dry_run:
        return stats

    if not insertions:
        return stats

    # Apply insertions in reverse order so earlier line numbers remain valid.
    lines = text.splitlines(keepends=True)
    insertions.sort(key=lambda x: -x[0])

    for end_lineno, attribution in insertions:
        # end_lineno is 1-indexed. The `),` is on that line. We insert one
        # line BEFORE it (so it sits between the body and the closing).
        insert_idx = end_lineno - 1  # 0-indexed list position of `),` line
        attr_line = f"        {_q(attribution)},\n"
        lines.insert(insert_idx, attr_line)

    new_text = "".join(lines)

    # Sanity-check that the file still parses.
    try:
        ast.parse(new_text)
    except SyntaxError as e:
        stats["error"] = f"insertion produced invalid Python in {book_path.name}: {e}"
        return stats

    ensure_backup(book_path)
    atomic_write(book_path, new_text)
    return stats


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def render_breakdown(breakdown: dict) -> str:
    if not breakdown:
        return ""
    items = sorted(breakdown.items(), key=lambda kv: -kv[1])
    lines = []
    for k, v in items[:5]:
        # Truncate very long attribution strings
        kt = k if len(k) <= 80 else k[:77] + "…"
        lines.append(f"      {v:>4}  {kt}")
    if len(items) > 5:
        lines.append(f"      {DIM}({len(items) - 5} more distinct attributions){RESET}")
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser(
        description="Assign provenance attribution to existing notes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--book", help="single book code (e.g. 'gen', '1ki')")
    g.add_argument("--all-books", action="store_true", help="every book in canonical order")
    p.add_argument("--dry-run", action="store_true", help="show what would change, don't write")
    p.add_argument("--interactive", action="store_true", help="prompt per book before applying")
    args = p.parse_args()

    if args.book:
        try:
            config.get_book(args.book)
        except KeyError:
            print(f"{RED}✗ unknown book {args.book!r}{RESET}", file=sys.stderr)
            sys.exit(2)
        targets = [args.book]
    else:
        targets = [b["code"] for b in config.load_books()]

    print(f"\n{BOLD}attribute{RESET} {DIM}{len(targets)} book(s){'  (dry-run)' if args.dry_run else ''}{RESET}\n")

    grand_total = {"scanned": 0, "already_attr": 0, "attributed": 0, "skipped": 0}
    grand_breakdown: dict = {}
    failed = []

    for code in targets:
        path = NOTES_DIR / f"{code}.py"
        if not path.is_file():
            print(f"  {YELLOW}–{RESET} {code:6}  no notes file")
            continue

        if args.interactive and not args.dry_run:
            try:
                ans = input(f"  process {code}? [y/n/q] ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print()
                break
            if ans == "q":
                break
            if ans != "y":
                print(f"  {DIM}skipped {code}{RESET}")
                continue

        stats = attribute_book(path, dry_run=args.dry_run)
        if "error" in stats:
            print(f"  {RED}✗ {code}: {stats['error']}{RESET}")
            failed.append(code)
            continue

        s, aa, a, sk = stats["scanned"], stats["already_attr"], stats["attributed"], stats["skipped"]
        verb = "would attribute" if args.dry_run else "attributed"
        print(
            f"  {GREEN}✓{RESET} {code:6}  "
            f"{s:>4} scanned · "
            f"{a:>4} {verb} · "
            f"{aa:>3} already had attribution · "
            f"{sk:>3} skipped"
        )

        for k in ("scanned", "already_attr", "attributed", "skipped"):
            grand_total[k] += stats.get(k, 0)
        for k, v in stats.get("breakdown", {}).items():
            grand_breakdown[k] = grand_breakdown.get(k, 0) + v

    print(
        f"\n  {BOLD}TOTAL{RESET}: "
        f"{grand_total['scanned']} scanned · "
        f"{grand_total['attributed']} {'would-attribute' if args.dry_run else 'attributed'} · "
        f"{grand_total['already_attr']} already · "
        f"{grand_total['skipped']} skipped"
    )

    if grand_breakdown:
        print("\n  Attribution breakdown:")
        print(render_breakdown(grand_breakdown))

    print()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
