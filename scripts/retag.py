#!/usr/bin/env python3
"""
retag.py — Reclassify legacy ``comm`` notes into specific sub-kinds.

Walks each book's notes file, examines every note whose kind is the
legacy ``comm``, and infers a specific sub-kind from the body text:

    comm-ethiopian       Andemta, Synaxarium, Fetha Nagast, Tewahedo

    comm-catholic        Aquinas, Catechism, Trent, Magisterium, Marian
    comm-orthodox        Palamas, John of Damascus, Hesychasm, Cabasilas
    comm-reformation     Luther, Calvin, Zwingli, Tyndale
    comm-patristic       Augustine, Origen, Jerome, Chrysostom, Eusebius,
                         Basil, Tertullian, Irenaeus, Athanasius, Cyril,
                         Ambrose, Gregory of Nyssa / Nazianzus
    comm-modern-critical Westermann, Walton, Brueggemann, von Rad, Childs,
                         Sailhamer, Sarna, Levenson, Kugel, Alter, Bauckham,
                         Hays, Dunn, Witherington
    comm-contextual      Enuma Elish, Gilgamesh, Hammurabi, Ugaritic,
                         Baal Cycle, archaeology, Sumerian, Akkadian

Detection runs in priority order (most distinctive voice first). Notes
that don't trip any specific detector remain as legacy ``comm`` — better
to leave neutral than misclassify.

Tagging reflects the **primary voice** of the note. Editions then filter
by kind: the Catholic edition includes comm-catholic, comm-patristic;
the Reformed edition includes comm-patristic, comm-reformation; the
Ethiopian edition includes comm-ethiopian, comm-patristic; etc.

Modes:
    --dry-run        show what would change (default-safe; recommended first)
    --book gen       single book
    --all-books      every book in canonical order
    --interactive    prompt per book before applying

Examples:
    python3 scripts/retag.py --book gen --dry-run
    python3 scripts/retag.py --book gen
    python3 scripts/retag.py --all-books

Crash-safety: every modified file is backed up via ensure_backup() and
written via atomic_write() (Phase β.1 helpers). On AST-parse failure of
the proposed rewrite, the file is left untouched.
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
# Detection vocabulary — priority-ordered.
# First sub-kind whose pattern set matches wins.
# ----------------------------------------------------------------------

SUBKIND_PRIORITY: list[tuple[str, list[str]]] = [
    (
        "comm-ethiopian",
        [
            r"\bAndemta\b",
            r"\bSynaxarium\b",
            r"\bFetha Nagast\b",
            r"\bKebra Nagast\b",
            r"\bTewahedo\b",
            r"\bMäshafä\b",
            r"\bGädlä\b",
            r"\bDäbrä\b",
        ],
    ),
    (
        [
            r"\bRashi\b",
            r"\bMaimonides\b",
            r"\bRambam\b",
            r"\bIbn Ezra\b",
            r"\bNachmanides\b",
            r"\bRamban\b",
            r"\bSforno\b",
            r"\bRashbam\b",
            r"\bRadak\b",
            r"\bSaadia\b",
            r"\bTargum\b",
            r"\bTargumim\b",
            r"\bOnqelos\b",
            r"\bPseudo-Jonathan\b",
            r"\bTalmud\b",
            r"\bMishnah\b",
            r"\bMishnaic\b",
            r"\bMidrash\b",
            r"\bGenesis Rabbah\b",
            r"\bExodus Rabbah\b",
            r"\bLeviticus Rabbah\b",
            r"\bNumbers Rabbah\b",
            r"\bDeuteronomy Rabbah\b",
            r"\bTanhuma\b",
            r"\bPirke Avot\b",
            r"\bTosefta\b",
            r"\bMekhilta\b",
            r"\bSifra\b",
            r"\bSifre\b",
            r"\bPhilo\b",
        ],
    ),
    (
        "comm-catholic",
        [
            r"\bAquinas\b",
            r"\bThomistic\b",
            r"\bCatholic Catechism\b",
            r"\bCatechism of the Catholic\b",
            r"\bCouncil of Trent\b",
            r"\bTridentine\b",
            r"\bSecond Vatican\b",
            r"\bVatican II\b",
            r"\bMagisterium\b",
            r"\bencyclical\b",
            r"\bpapal\b",
            r"\bMariological\b",
            r"\bAssumption of Mary\b",
            r"\bImmaculate Conception\b",
            r"\bRatzinger\b",
            r"\bBenedict XVI\b",
            r"\bvon Balthasar\b",
            r"\bde Lubac\b",
            r"\bRahner\b",
            r"\bHahn\b",  # Scott Hahn (Catholic biblical theologian)
        ],
    ),
    (
        "comm-orthodox",
        [
            r"\bEastern Orthodox\b",
            r"\bByzantine\b",
            r"\bPalamas\b",
            r"\bGregory Palamas\b",
            r"\bJohn of Damascus\b",
            r"\bDamascene\b",
            r"\bHesychasm\b",
            r"\bHesychast\b",
            r"\bSymeon the New Theologian\b",
            r"\bCabasilas\b",
            r"\bMaximus the Confessor\b",
            r"\bPhilokalia\b",
            r"\bSynodicon\b",
            r"\bAthonite\b",
        ],
    ),
    (
        "comm-reformation",
        [
            r"\bLuther\b",
            r"\bLutheran\b",
            r"\bCalvin\b",
            r"\bCalvinist\b",
            r"\bCalvin's\b",
            r"\bZwingli\b",
            r"\bMelanchthon\b",
            r"\bTyndale\b",
            r"\bWycliffe\b",
            r"\bWestminster Confession\b",
        ],
    ),
    (
        "comm-patristic",
        [
            r"\bAugustine\b",
            r"\bAugustinian\b",
            r"\bOrigen\b",
            r"\bJerome\b",
            r"\bChrysostom\b",
            r"\bEusebius\b",
            r"\bBasil\b",
            r"\bTertullian\b",
            r"\bIrenaeus\b",
            r"\bCyprian\b",
            r"\bAthanasius\b",
            r"\bCyril of Alexandria\b",
            r"\bCyril of Jerusalem\b",
            r"\bTheodoret\b",
            r"\bAmbrose\b",
            r"\bHilary of Poitiers\b",
            r"\bLactantius\b",
            r"\bClement of Alexandria\b",
            r"\bClement of Rome\b",
            r"\bGregory of Nyssa\b",
            r"\bGregory of Nazianzus\b",
            r"\bPseudo-Dionysius\b",
            r"\bAnselm\b",
            r"\bBonaventure\b",
            r"\bBede\b",
            r"\bIsaac of Nineveh\b",
        ],
    ),
    (
        "comm-modern-critical",
        [
            r"\bWestermann\b",
            r"\bWalton\b",
            r"\bBrueggemann\b",
            r"\bvon Rad\b",
            r"\bChilds\b",
            r"\bSailhamer\b",
            r"\bSarna\b",
            r"\bFox\b",
            r"\bLevenson\b",
            r"\bKugel\b",
            r"\bAlter\b",
            r"\bGoldingay\b",
            r"\bBauckham\b",
            r"\bHays\b",
            r"\bLevine\b",
            r"\bDunn\b",
            r"\bWitherington\b",
            r"\bCarson\b",
            r"\bBeale\b",
            r"\bSanders\b",
            r"\bPannenberg\b",
            r"\bMoltmann\b",
            r"\bSchnackenburg\b",
            r"\bN\.T\. Wright\b",
            r"\bTom Wright\b",
            r"\bMilgrom\b",
            r"\bFitzmyer\b",
            r"\bMeyers\b",
            r"\bSchiffman\b",
            r"\bVanderKam\b",
            r"\bNickelsburg\b",
            r"\bStuckenbruck\b",
            r"\bCharlesworth\b",
        ],
    ),
    (
        "comm-contextual",
        [
            r"\bEnuma Elish\b",
            r"\bGilgamesh\b",
            r"\bAtrahasis\b",
            r"\bCode of Hammurabi\b",
            r"\bHammurabi\b",
            r"\bUgaritic\b",
            r"\bBaal Cycle\b",
            r"\bRas Shamra\b",
            r"\bSumerian\b",
            r"\bAkkadian\b",
            r"\b[Aa]rchaeolog(?:y|ical)\b",
            r"\bMesopotamian\b",
            r"\bEgyptian execration\b",
            r"\bAmarna\b",
            r"\bMari texts\b",
            r"\bNuzi\b",
            r"\bAncient Near East(?:ern)?\b",
        ],
    ),
]

# Pre-compile patterns
_COMPILED: list[tuple[str, re.Pattern]] = []
for subkind, patterns in SUBKIND_PRIORITY:
    combined = "|".join(patterns)
    _COMPILED.append((subkind, re.compile(combined, re.IGNORECASE)))


def _strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", " ", s)


def infer_subkind(body_html: str) -> str | None:
    """Return the inferred sub-kind, or ``None`` if no specific match."""
    plain = _strip_html(body_html)
    for subkind, pat in _COMPILED:
        if pat.search(plain):
            return subkind
    return None


# ----------------------------------------------------------------------
# Tuple text formatting (canonical multi-line)
# ----------------------------------------------------------------------


def _q(s: str) -> str:
    if "'" not in s:
        return f"'{s}'"
    if '"' not in s:
        return f'"{s}"'
    return '"' + s.replace('"', '\\"') + '"'


def format_tuple(fields: list) -> str:
    """Emit a canonical multi-line tuple. Handles 8-field and 9-field forms."""
    chapter, verse, suffix, anchor, kind, title, label, body = fields[:8]
    out = (
        "    (\n"
        f"        {chapter}, {verse}, {_q(suffix)}, {_q(anchor)},\n"
        f"        {_q(kind)}, {_q(title)},\n"
        f"        {_q(label)},\n"
        f"        {_q(body)},\n"
    )
    if len(fields) >= 9 and fields[8]:
        out += f"        {_q(fields[8])},\n"
    return out + "    )"


# ----------------------------------------------------------------------
# Per-book retag
# ----------------------------------------------------------------------


def retag_book(book_path: Path, dry_run: bool) -> dict:
    """Walk one book, infer + rewrite kinds for legacy ``comm`` notes.
    Returns stats dict: scanned, comm_count, retagged, kept_legacy,
    breakdown {subkind: N}, error (optional)."""
    text = book_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        return {"error": f"syntax error: {e}"}

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
        return {"error": "no NOTES list"}

    stats = {
        "scanned": 0,
        "comm_count": 0,
        "retagged": 0,
        "kept_legacy": 0,
        "breakdown": {},
    }

    rewrites: list[tuple[int, int, str]] = []  # (start, end, new_text)

    # Translate (lineno, col_offset) → byte offset
    line_starts = [0]
    for _ch in text:
        line_starts.append(line_starts[-1] + 1)
    # Better: build a list of cumulative offsets per line
    line_offsets = [0]
    for line in text.splitlines(keepends=True):
        line_offsets.append(line_offsets[-1] + len(line))

    def to_offset(lineno: int, col: int) -> int:
        return line_offsets[lineno - 1] + col

    for tup_node in notes_assign.value.elts:
        if not isinstance(tup_node, ast.Tuple):
            continue
        stats["scanned"] += 1
        try:
            fields = [ast.literal_eval(e) for e in tup_node.elts]
        except (ValueError, SyntaxError):
            continue
        if len(fields) < 5:
            continue
        kind = fields[4]
        if kind != "comm":
            continue
        stats["comm_count"] += 1

        if len(fields) < 8:
            stats["kept_legacy"] += 1
            continue

        body = fields[7]
        new_kind = infer_subkind(body if isinstance(body, str) else "")
        if not new_kind:
            stats["kept_legacy"] += 1
            continue

        fields[4] = new_kind
        new_tuple = format_tuple(fields)

        start = to_offset(tup_node.lineno, tup_node.col_offset)
        end = to_offset(tup_node.end_lineno, tup_node.end_col_offset)
        rewrites.append((start, end, new_tuple))

        stats["retagged"] += 1
        stats["breakdown"][new_kind] = stats["breakdown"].get(new_kind, 0) + 1

    if dry_run or not rewrites:
        return stats

    # Apply rewrites in REVERSE byte-position order
    rewrites.sort(key=lambda r: -r[0])
    new_text = text
    for start, end, repl in rewrites:
        new_text = new_text[:start] + repl + new_text[end:]

    # Sanity-check parse before write
    try:
        ast.parse(new_text)
    except SyntaxError as e:
        stats["error"] = f"rewrite produced invalid Python: {e}"
        return stats

    ensure_backup(book_path)
    atomic_write(book_path, new_text)
    return stats


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(description="Reclassify legacy comm notes.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--book", help="single book code (e.g. 'gen', '1ki')")
    g.add_argument("--all-books", action="store_true", help="every book")
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

    print(f"\n{BOLD}retag{RESET} {DIM}{len(targets)} book(s){'  (dry-run)' if args.dry_run else ''}{RESET}\n")

    grand = {"scanned": 0, "comm_count": 0, "retagged": 0, "kept_legacy": 0}
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
                print(f"  {DIM}skipped{RESET}")
                continue

        stats = retag_book(path, dry_run=args.dry_run)
        if "error" in stats:
            print(f"  {RED}✗ {code}: {stats['error']}{RESET}")
            failed.append(code)
            continue

        verb = "would retag" if args.dry_run else "retagged"
        c = stats["comm_count"]
        r = stats["retagged"]
        k = stats["kept_legacy"]
        if c == 0:
            print(f"  {DIM}○ {code:6}  no legacy comm notes{RESET}")
        else:
            print(f"  {GREEN}✓{RESET} {code:6}  {c:>4} comm scanned · {r:>4} {verb} · {k:>4} kept as legacy comm")

        for key in ("scanned", "comm_count", "retagged", "kept_legacy"):
            grand[key] += stats.get(key, 0)
        for k_, v in stats.get("breakdown", {}).items():
            grand_breakdown[k_] = grand_breakdown.get(k_, 0) + v

    print(
        f"\n  {BOLD}TOTAL{RESET}: "
        f"{grand['scanned']} notes scanned · "
        f"{grand['comm_count']} legacy comm · "
        f"{grand['retagged']} {'would-retag' if args.dry_run else 'retagged'} · "
        f"{grand['kept_legacy']} kept as legacy comm"
    )

    if grand_breakdown:
        print("\n  Sub-kind breakdown:")
        for sk, n in sorted(grand_breakdown.items(), key=lambda kv: -kv[1]):
            print(f"      {n:>4}  {sk}")

    print()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
