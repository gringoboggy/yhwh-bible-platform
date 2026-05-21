#!/usr/bin/env python3
"""dev/trace_matrix.py — integrity tracer for the editions x features matrix.

"Ping every variable in editions.yaml and make sure it traces somewhere
logical." Reuses the SAME config loaders the matrix/build use, so this
checks the real data, not a copy. Read-only; prints a report and exits 0
(report-only) — wire into CI later if desired.

Run:
    py dev/trace_matrix.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import yaml  # noqa: E402

from scripts.core import config  # noqa: E402


def load_canons() -> dict:
    data = yaml.safe_load((REPO / "content" / "canons.yaml").read_text(encoding="utf-8")) or {}
    return data.get("canons", {}) or {}


def main() -> int:
    books = config.load_books()
    book_codes = {b["code"] for b in books}
    kinds = config.load_kinds()
    kind_codes = {k["code"] for k in kinds}
    cats = config.load_categories()
    cat_ids = {c["id"] for c in cats}
    editions = config.load_editions()
    canons = load_canons()
    canon_ids = set(canons)

    trans_dir = REPO / "content" / "translations"
    trans_ids = {p.name for p in trans_dir.iterdir() if p.is_dir() and not p.name.startswith(("_", "."))}

    print(
        f"editions={len(editions)} canons={len(canon_ids)} "
        f"categories={len(cat_ids)} kinds={len(kind_codes)} "
        f"books={len(book_codes)} translation_dirs={len(trans_ids)}"
    )
    print(f"canons: {sorted(canon_ids)}")
    print(f"translation dirs: {sorted(trans_ids)}")
    print()

    problems: list[tuple[str, str]] = []
    for ed in editions:
        eid = ed.get("id", "?")
        issues: list[str] = []

        canon = ed.get("canon")
        if canon and canon not in canon_ids:
            issues.append(f"canon '{canon}' not defined in canons.yaml")

        for cat in ed.get("enabled_categories") or []:
            if cat not in cat_ids:
                issues.append(f"enabled_category '{cat}' unknown")
        for k in ed.get("enabled_kinds") or []:
            if k not in kind_codes:
                issues.append(f"enabled_kind '{k}' unknown")
        for k in ed.get("disabled_kinds") or []:
            if k not in kind_codes:
                issues.append(f"disabled_kind '{k}' unknown")

        for slot in ("popup_translation", "base_translation"):
            v = ed.get(slot)
            if v and v not in trans_ids:
                issues.append(f"{slot} '{v}' -> no content/translations/{v}/ dir")

        cov = ed.get("cover_image")
        if cov and not (REPO / "content" / cov).is_file():
            issues.append(f"cover_image '{cov}' missing on disk")

        if canon in canons:
            missing = [b for b in (canons[canon].get("books") or []) if b not in book_codes]
            if missing:
                issues.append(f"canon '{canon}' lists {len(missing)} book(s) absent from books.yaml: {missing[:8]}")

        flag = "OK  " if not issues else "FAIL"
        print(
            f"[{flag}] {eid:<22} canon={str(canon):<11} "
            f"cats={len(ed.get('enabled_categories') or [])} "
            f"+k={len(ed.get('enabled_kinds') or [])} "
            f"-k={len(ed.get('disabled_kinds') or [])} "
            f"popup_tr={ed.get('popup_translation')!r} base_tr={ed.get('base_translation')!r} "
            f"standalone={ed.get('standalone', False)}"
        )
        for i in issues:
            print(f"        - {i}")
            problems.append((eid, i))

    print()
    print(f"TOTAL UNRESOLVED REFERENCES: {len(problems)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
