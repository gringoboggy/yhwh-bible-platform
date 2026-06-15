#!/usr/bin/env python3
"""Build ONE Kobo kepub with a chosen marker_badge_style — manual device QA only.

Usage (repo root):
  py -3 dev/build_kobo_marker_ab.py ethiopian-tewahedo lozenge+count

Copies to OneDrive Desktop as YHWH-MarkerAB-<edition>-<style>.kepub.epub
"""

from __future__ import annotations

import copy
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.build_edition import build_one  # noqa: E402
from scripts.core import config  # noqa: E402

DEFAULT_STYLE = "lozenge+count"
OUT = REPO / "build" / "kobo-marker-ab"
DESK = Path.home() / "OneDrive" / "Desktop"
_ORIG_EDITIONS_BY_ID = config.editions_by_id


def main() -> int:
    edition_id = sys.argv[1] if len(sys.argv) > 1 else "ethiopian-tewahedo"
    style = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_STYLE
    OUT.mkdir(parents=True, exist_ok=True)
    all_kinds = config.load_kinds()
    base_eds = _ORIG_EDITIONS_BY_ID()
    patched = copy.deepcopy(base_eds)
    patched[edition_id] = {
        **patched[edition_id],
        "marker_badge_style": style,
        "reader_eink_verse_lines": True,  # device QA: one verse per line on Kobo
    }
    config.editions_by_id = lambda _p=patched: _p  # type: ignore[method-assign, assignment]

    try:
        print(f"=== {edition_id} / {style} ===", flush=True)
        stats = build_one(
            edition_id,
            OUT,
            "0.1.0",
            all_kinds,
            force=True,
            target_reader="eink",
        )
    finally:
        config.editions_by_id = _ORIG_EDITIONS_BY_ID  # type: ignore[method-assign]
        config.load_editions.cache_clear()

    epub = Path(stats["output_path"])
    kepub = epub.with_suffix(".kepub.epub")
    subprocess.run(["kepubify", "-o", str(kepub), str(epub)], check=True, stdin=subprocess.DEVNULL)
    kobo = Path("G:/")
    if kobo.is_dir():
        for old in kobo.glob("YHWH*.kepub.epub"):
            old.unlink()
        dest = kobo / f"YHWH-koboQA.kepub.epub"
        shutil.copy2(kepub, dest)
        print(f"kobo: wiped + loaded {dest.name}", flush=True)
    print(f"done: {kepub}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
