#!/usr/bin/env python3
"""matrix.py — print the symbol-toggle count grid as a terminal table.

Useful even before the web UI exists. Shows you, at a glance:
    - which editions have how many notes of each category
    - what's blocked by the current kind filter
    - which kinds would gain notes if toggled on

Usage:
    python3 scripts/matrix.py                  # category × edition table
    python3 scripts/matrix.py --kinds          # kind × edition table (longer)
    python3 scripts/matrix.py --edition <id>   # detail view for one edition
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config, matrix  # noqa: E402
from scripts.core.ui import GREEN, RED, YELLOW, DIM, BOLD, RESET  # noqa: E402


def _category_table(m: matrix.Matrix, editions: list[dict], categories: list[dict]) -> None:
    """Print a 14 × 5 grid: categories down, editions across."""
    cat_ids = [c["id"] for c in categories]
    cat_symbols = {c["id"]: c.get("symbol", "?") for c in categories}
    cat_labels = {c["id"]: c.get("label", c["id"]) for c in categories}

    # Pre-compute the breakdowns per edition
    breakdowns = {ed["id"]: matrix.breakdown_by_category(ed["id"]) for ed in editions}

    # Header
    ed_ids = [ed["id"] for ed in editions]
    short = {ed_id: ed_id.split("-")[0][:8] for ed_id in ed_ids}
    print()
    print(f"  {BOLD}symbol-toggle matrix · categories × editions{RESET}")
    print()
    head = f"  {'category':<22}"
    for ed_id in ed_ids:
        head += f" {short[ed_id]:>9}"
    print(head)
    print(f"  {'-' * 22}{'-' * (10 * len(ed_ids))}")

    for cid in cat_ids:
        sym = cat_symbols[cid]
        label = cat_labels[cid][:18]
        row = f"  {sym} {label:<20}"
        for ed_id in ed_ids:
            n = breakdowns[ed_id].get(cid, 0)
            color = DIM if n == 0 else ""
            row += f" {color}{n:>9,}{RESET}"
        print(row)

    # Footer: totals per edition
    print(f"  {'-' * 22}{'-' * (10 * len(ed_ids))}")
    total_row = f"  {'TOTAL':<22}"
    for ed_id in ed_ids:
        t = matrix.total_for_edition(ed_id)
        total_row += f" {BOLD}{t:>9,}{RESET}"
    print(total_row)

    # Potential vs enabled
    delta_row = f"  {DIM}{'(filtered out)':<22}{RESET}"
    for ed_id in ed_ids:
        enabled = matrix.total_for_edition(ed_id)
        # ψ.35-B1 — was: sum(m.potential[ed_id].values())
        potential = sum(m.potential_kinds_dict(ed_id).values())
        delta = potential - enabled
        delta_row += f" {DIM}{f'+{delta}' if delta else '·':>9}{RESET}"
    print(delta_row)
    print()


def _kind_table(m: matrix.Matrix, editions: list[dict], kinds: list[dict]) -> None:
    """Full kind × edition grid — longer, scrollable."""
    print()
    print(f"  {BOLD}symbol-toggle matrix · kinds × editions{RESET}")
    print()
    ed_ids = [ed["id"] for ed in editions]
    short = {ed_id: ed_id.split("-")[0][:8] for ed_id in ed_ids}
    head = f"  {'kind':<26}"
    for ed_id in ed_ids:
        head += f" {short[ed_id]:>9}"
    print(head)
    print(f"  {'-' * 26}{'-' * (10 * len(ed_ids))}")

    # Group by category
    cats = config.load_categories()
    cats_by_id = {c["id"]: c for c in cats}
    kinds_by_cat: dict[str, list[dict]] = {}
    for k in kinds:
        kinds_by_cat.setdefault(k.get("category", "?"), []).append(k)

    for cid in [c["id"] for c in cats]:
        if cid not in kinds_by_cat:
            continue
        sym = cats_by_id[cid]["symbol"]
        print(f"\n  {sym} {DIM}{cats_by_id[cid]['label']}{RESET}")
        for k in kinds_by_cat[cid]:
            kind_code = k["code"]
            row = f"    {kind_code:<24}"
            for ed_id in ed_ids:
                # ψ.35-B1 — was: m.enabled[ed_id].get(kind_code, 0)
                enabled = m.enabled_count(ed_id, kind_code)
                # ψ.35-B1 — was: m.potential[ed_id].get(kind_code, 0)
                potential = m.potential_count(ed_id, kind_code)
                if enabled > 0:
                    row += f" {GREEN}{enabled:>9,}{RESET}"
                elif potential > 0:
                    row += f" {YELLOW}{f'({potential:,})':>9}{RESET}"
                else:
                    row += f" {DIM}{'·':>9}{RESET}"
            print(row)
    print()
    print(
        f"  {GREEN}green{RESET} = enabled count   "
        f"{YELLOW}yellow ({{N}}){RESET} = potential if toggled on   "
        f"{DIM}·{RESET} = no notes available"
    )
    print()


def _edition_detail(edition_id: str) -> None:
    """Detail view for a single edition: every kind, sorted by count."""
    editions = config.editions_by_id()
    if edition_id not in editions:
        print(f"  {RED}✗ unknown edition: {edition_id!r}{RESET}", file=sys.stderr)
        print(f"  known: {', '.join(sorted(editions))}", file=sys.stderr)
        sys.exit(2)

    m = matrix.compute_matrix()
    # ψ.35-B1 — was: m.enabled[edition_id] / m.potential[edition_id].
    # Method-derived dicts are equivalent (per TestPsi35B1AccessorDicts
    # equivalence pin) and isolate this CLI from the upcoming
    # projection-field removal in ψ.35-Final.
    enabled = m.enabled_kinds_dict(edition_id)
    potential = m.potential_kinds_dict(edition_id)
    canon_books = m.edition_canon_books[edition_id]
    enabled_kinds = m.edition_enabled_kinds[edition_id]
    total_enabled = sum(enabled.values())
    total_potential = sum(potential.values())

    print()
    print(f"  {BOLD}{edition_id}{RESET}")
    print(f"    canon books:       {len(canon_books)}")
    print(f"    enabled kinds:     {len(enabled_kinds)} of {len(config.load_kinds())}")
    print(f"    notes shipping:    {BOLD}{total_enabled:,}{RESET}")
    print(
        f"    notes potential:   {total_potential:,} "
        f"({DIM}+{total_potential - total_enabled} would be added if all kinds enabled{RESET})"
    )
    print()

    # Sorted by count, descending
    rows = sorted(
        (set(enabled) | set(potential)),
        key=lambda k: (-enabled.get(k, 0), -potential.get(k, 0)),
    )
    print(f"    {'kind':<26} {'enabled':>9} {'potential':>11}")
    print(f"    {'-' * 26} {'-' * 9} {'-' * 11}")
    for kind in rows:
        e = enabled.get(kind, 0)
        p = potential.get(kind, 0)
        if e == 0 and p == 0:
            continue
        e_str = f"{e:,}" if e else "·"
        p_str = f"{p:,}" if p else "·"
        e_color = GREEN if e else DIM
        p_color = "" if p > e else DIM
        print(f"    {kind:<26} {e_color}{e_str:>9}{RESET} {p_color}{p_str:>11}{RESET}")
    print()


def main() -> int:
    p = argparse.ArgumentParser(description="Print the symbol-toggle count grid")
    p.add_argument("--kinds", action="store_true", help="show full kind × edition grid (longer)")
    p.add_argument("--edition", metavar="ID", help="show detailed breakdown for one edition")
    args = p.parse_args()

    editions = config.load_editions()
    if not editions:
        print(f"  {RED}✗ no editions found in content/editions.yaml{RESET}", file=sys.stderr)
        return 1

    if args.edition:
        _edition_detail(args.edition)
        return 0

    m = matrix.compute_matrix()
    if args.kinds:
        _kind_table(m, editions, config.load_kinds())
    else:
        _category_table(m, editions, config.load_categories())

    return 0


if __name__ == "__main__":
    sys.exit(main())
