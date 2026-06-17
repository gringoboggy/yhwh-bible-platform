#!/usr/bin/env python3
"""IIIF-acquire missing CAM hires JPGs referenced by samuel/manifest.yaml.

One folio side fetched once; copies to every manifest path sharing that folio id.
View arithmetic: f106r = view 215 → view = 215 + (folio_num - 106) * 2 (+1 for verso).
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

from scripts.acquire_cudl_master import fetch_master
from scripts.core import manuscript_manifest as mm

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "GAPS/1_Samuel/Cambridge-Add-1570-hires"
FOLIO_RE = re.compile(r"MS-ADD-01570_(f\d+[rv])_")
VIEW_RE = re.compile(r"MS-ADD-01570_view(\d+)_")


def _view_id(folio: str) -> int:
    num = int(folio[1:-1])
    side = 0 if folio.endswith("r") else 1
    return 215 + (num - 106) * 2 + side


def main() -> int:
    man = mm.load_manifest(track="samuel")
    by_folio: dict[str, list[Path]] = {}
    by_view: dict[int, list[Path]] = {}
    for book in ("1sa", "2sa"):
        nch = 31 if book == "1sa" else 24
        for ch in range(1, nch + 1):
            e = mm.chapter_entry(man, book, ch) or {}
            for rel in (e.get("CAM") or {}).get("views") or []:
                p = REPO / rel
                if p.is_file():
                    continue
                m = FOLIO_RE.search(rel)
                if m:
                    by_folio.setdefault(m.group(1), []).append(p)
                    continue
                vm = VIEW_RE.search(rel)
                if vm:
                    by_view.setdefault(int(vm.group(1)), []).append(p)
                    continue
                print(f"skip unparseable: {rel}", file=sys.stderr)

    folios = sorted(by_folio, key=lambda f: (int(f[1:-1]), f[-1]))
    views = sorted(by_view)
    n_paths = sum(len(v) for v in by_folio.values()) + sum(len(v) for v in by_view.values())
    print(f"acquiring {len(folios)} folio sides + {len(views)} view ids → {n_paths} paths")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    step = 0
    total = len(folios) + len(views)
    for folio in folios:
        step += 1
        view = _view_id(folio)
        staging = OUT_DIR / f"MS-ADD-01570_{folio}_hires.jpg"
        print(f"[{step}/{total}] {folio} view={view} …", flush=True)
        if not staging.is_file():
            fetch_master(view_id=view, output_path=str(staging))
        for dest in by_folio[folio]:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.resolve() != staging.resolve():
                shutil.copy2(staging, dest)
    for view in views:
        step += 1
        staging = OUT_DIR / f"MS-ADD-01570_view{view}_hires.jpg"
        print(f"[{step}/{total}] view{view} …", flush=True)
        if not staging.is_file():
            fetch_master(view_id=view, output_path=str(staging))
        for dest in by_view[view]:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.resolve() != staging.resolve():
                shutil.copy2(staging, dest)
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
