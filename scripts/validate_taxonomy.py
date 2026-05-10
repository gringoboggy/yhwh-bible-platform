#!/usr/bin/env python3
"""
validate_taxonomy.py — Sanity-check the kind / category / edition schema.

Catches the kinds of bugs that creep in as the taxonomy grows: kinds
pointing at categories that don't exist, duplicate codes, edition
profiles referencing missing kinds, CSS classes colliding, etc.

Examples:
    python3 scripts/validate_taxonomy.py
        # full report

    python3 scripts/validate_taxonomy.py --strict
        # exit 1 on warnings too

    python3 scripts/validate_taxonomy.py --quiet
        # only the summary line

Exit codes:
    0  schema is sound
    1  warnings found (or errors with --strict)
    2  errors found
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config  # noqa: E402

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

VALID_PHASES = {"legacy", "mvp", "phase2", "phase3"}
KIND_REQUIRED_FIELDS = {
    "code",
    "category",
    "symbol",
    "note_class",
    "marker_class",
    "label",
    "title_attr",
}
CATEGORY_REQUIRED_FIELDS = {"id", "label", "symbol", "description", "sort_order"}


def check_kinds(kinds, categories_by_id, errors, warnings):
    seen_codes: Counter = Counter()
    seen_note_classes: Counter = Counter()
    for k in kinds:
        code = k.get("code") or "<no code>"
        # Required fields
        missing = KIND_REQUIRED_FIELDS - set(k)
        if missing:
            errors.append(f"kind {code!r}: missing required fields: {sorted(missing)}")
        # Category exists
        cat = k.get("category")
        if cat and cat not in categories_by_id:
            errors.append(f"kind {code!r}: category {cat!r} does not exist in categories.yaml")
        # Phase valid
        phase = k.get("phase")
        if phase and phase not in VALID_PHASES:
            warnings.append(f"kind {code!r}: phase {phase!r} not in {sorted(VALID_PHASES)}")
        # Track duplicates
        seen_codes[code] += 1
        nc = k.get("note_class")
        if nc:
            seen_note_classes[nc] += 1
    for code, n in seen_codes.items():
        if n > 1:
            errors.append(f"duplicate kind code {code!r} ({n} occurrences)")
    for nc, n in seen_note_classes.items():
        if n > 1:
            errors.append(f"duplicate note_class {nc!r} ({n} occurrences)")


def check_categories(categories, errors, warnings):
    seen_ids: Counter = Counter()
    seen_orders: Counter = Counter()
    for c in categories:
        cid = c.get("id") or "<no id>"
        missing = CATEGORY_REQUIRED_FIELDS - set(c)
        if missing:
            errors.append(f"category {cid!r}: missing required fields: {sorted(missing)}")
        seen_ids[cid] += 1
        so = c.get("sort_order")
        if so is not None:
            seen_orders[so] += 1
    for cid, n in seen_ids.items():
        if n > 1:
            errors.append(f"duplicate category id {cid!r} ({n} occurrences)")
    for so, n in seen_orders.items():
        if n > 1:
            warnings.append(f"sort_order {so} used by {n} categories — display order ambiguous")


def check_editions(editions, kinds_by_code, categories_by_id, errors, warnings):
    seen_ids: Counter = Counter()
    for e in editions:
        eid = e.get("id") or "<no id>"
        seen_ids[eid] += 1
        if not e.get("title"):
            warnings.append(f"edition {eid!r}: no title set")
        # Validate enabled_categories
        for cat in e.get("enabled_categories") or []:
            if cat not in categories_by_id:
                errors.append(f"edition {eid!r}: enabled_categories references missing category {cat!r}")
        # Validate enabled_kinds
        for kc in e.get("enabled_kinds") or []:
            if kc not in kinds_by_code:
                errors.append(f"edition {eid!r}: enabled_kinds references missing kind {kc!r}")
        # Validate disabled_kinds
        for kc in e.get("disabled_kinds") or []:
            if kc not in kinds_by_code:
                warnings.append(f"edition {eid!r}: disabled_kinds references missing kind {kc!r}")
        # max_phase
        mp = e.get("max_phase")
        if mp and mp not in VALID_PHASES:
            warnings.append(f"edition {eid!r}: max_phase {mp!r} not in {sorted(VALID_PHASES)}")
    for eid, n in seen_ids.items():
        if n > 1:
            errors.append(f"duplicate edition id {eid!r} ({n} occurrences)")


def check_existing_notes_use_known_kinds(kinds_by_code, errors, warnings):
    """Walk content/notes/*.py via AST and ensure every note's kind is in
    the registry. Also count attribution coverage (the optional 9th tuple
    field, v28a-4 schema). Returns (kind_usage_counter, attribution_stats).

    Attribution coverage policy (v28a-7+): every note must carry a
    non-empty attribution. Missing attribution emits an error.
    """
    import ast

    notes_dir = REPO_ROOT / "content" / "notes"
    used: Counter = Counter()
    unknown: Counter = Counter()
    attr_stats = {"total": 0, "attributed": 0, "missing": 0, "by_book": {}}
    if not notes_dir.is_dir():
        return used, attr_stats
    for f in sorted(notes_dir.glob("*.py")):
        if f.name == "__init__.py":
            continue
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError:
            warnings.append(f"could not parse {f.name}")
            continue
        book_total = 0
        book_attributed = 0
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name) and tgt.id == "NOTES":
                        try:
                            value = ast.literal_eval(node.value)
                        except (ValueError, SyntaxError):
                            continue
                        if not isinstance(value, list):
                            continue
                        for tup in value:
                            if isinstance(tup, tuple) and len(tup) >= 5:
                                kind = tup[4]
                                used[kind] += 1
                                if kind not in kinds_by_code:
                                    unknown[kind] += 1
                                # Attribution check (9th field)
                                book_total += 1
                                attr_stats["total"] += 1
                                attribution_present = len(tup) >= 9 and isinstance(tup[8], str) and tup[8].strip()
                                if attribution_present:
                                    attr_stats["attributed"] += 1
                                    book_attributed += 1
                                else:
                                    attr_stats["missing"] += 1
        if book_total:
            attr_stats["by_book"][f.stem] = (book_attributed, book_total)
    for kind, n in unknown.items():
        errors.append(f"{n} existing note(s) use unregistered kind {kind!r}")
    if attr_stats["missing"] > 0:
        errors.append(
            f"{attr_stats['missing']} note(s) lack the optional attribution field "
            f"(9th tuple element). Run `python3 scripts/attribute.py --all-books` "
            f"to assign provenance to all notes."
        )
    return used, attr_stats


def main() -> None:
    p = argparse.ArgumentParser(
        description="Validate the kind / category / edition taxonomy.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--strict", action="store_true", help="exit 1 on warnings too")
    p.add_argument("--quiet", action="store_true", help="only print summary")
    args = p.parse_args()

    kinds = config.load_kinds()
    categories = config.load_categories()
    editions = config.load_editions()
    kinds_by_code = config.kinds_by_code()
    categories_by_id = config.categories_by_id()

    errors: list = []
    warnings: list = []

    check_categories(categories, errors, warnings)
    check_kinds(kinds, categories_by_id, errors, warnings)
    check_editions(editions, kinds_by_code, categories_by_id, errors, warnings)
    used, attr_stats = check_existing_notes_use_known_kinds(kinds_by_code, errors, warnings)

    # Output
    if not args.quiet:
        print(f"\n  {BOLD}Schema overview{RESET}")
        print(f"    categories: {len(categories)}")
        print(f"    kinds:      {len(kinds)}")
        print(f"    editions:   {len(editions)}")
        if used:
            print(f"\n  {BOLD}Kind usage in existing notes{RESET}")
            for k, n in sorted(used.items(), key=lambda x: -x[1]):
                marker = GREEN + "✓" + RESET if k in kinds_by_code else RED + "✗" + RESET
                print(f"    {marker} {k:30}  {n:>5} note(s)")
        if attr_stats["total"]:
            t = attr_stats["total"]
            a = attr_stats["attributed"]
            m = attr_stats["missing"]
            pct = (a / t * 100) if t else 0
            colour = GREEN if m == 0 else (YELLOW if m < t * 0.5 else RED)
            sym = "✓" if m == 0 else "⚠"
            print(f"\n  {BOLD}Attribution coverage{RESET}  {colour}{sym} {a}/{t} ({pct:.1f}%){RESET}")
            if m and not args.quiet:
                # Show worst-covered books (those with missing > 0)
                missing_books = [(b, attr, total) for b, (attr, total) in attr_stats["by_book"].items() if attr < total]
                missing_books.sort(key=lambda x: x[1] / max(x[2], 1))
                for b, attr, total in missing_books[:5]:
                    print(f"    {RED}✗{RESET} {b:6}  {attr}/{total} attributed")
                if len(missing_books) > 5:
                    print(f"    {DIM}({len(missing_books) - 5} more book(s) with missing attribution){RESET}")

        if errors:
            print(f"\n  {RED}Errors ({len(errors)}){RESET}")
            for e in errors:
                print(f"    {RED}✗{RESET} {e}")
        if warnings:
            print(f"\n  {YELLOW}Warnings ({len(warnings)}){RESET}")
            for w in warnings:
                print(f"    {YELLOW}⚠{RESET} {w}")

    # Summary
    if errors:
        print(f"\n  {RED}✗ validate_taxonomy: {len(errors)} error(s), {len(warnings)} warning(s){RESET}")
        sys.exit(2)
    if warnings:
        color = RED if args.strict else YELLOW
        sym = "✗" if args.strict else "⚠"
        print(f"\n  {color}{sym} validate_taxonomy: 0 errors, {len(warnings)} warning(s){RESET}")
        sys.exit(1 if args.strict else 0)
    print(f"\n  {GREEN}✓ validate_taxonomy: schema is sound{RESET}")
    sys.exit(0)


if __name__ == "__main__":
    main()
