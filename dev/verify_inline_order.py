#!/usr/bin/env python3
"""Verify eink study aside sits BEFORE the next verse vn-link in document order."""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.build_edition import apply_badge_markers  # noqa: E402
from scripts.core import config  # noqa: E402


def main() -> int:
    book = config.get_book("gen")
    epub = REPO / "epub_working"
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for f in book["files"]:
            (tmp / f).write_text((epub / f).read_text(encoding="utf-8"), encoding="utf-8")
        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge", "target_reader": "eink"})
        fname = next(f for f in book["files"] if 'id="v-gen-1-12"' in (tmp / f).read_text(encoding="utf-8"))
        text = (tmp / fname).read_text(encoding="utf-8")
    pairs = (
        ("gen 1:12", "vbadge-gen-1-12-s1", "vnotes-gen-1-12-s1", "v-gen-1-13"),
        ("gen 1:1 s7", "vbadge-gen-1-1-s7", "vnotes-gen-1-1-s7", "v-gen-1-2"),
    )
    ok = True
    for label, bid, aid, nxt in pairs:
        bm = re.search(rf'id="{re.escape(bid)}"', text)
        am = re.search(rf'id="{re.escape(aid)}"', text)
        vm = re.search(rf'id="{re.escape(nxt)}"', text)
        if not bm or not am or not vm:
            print(f"FAIL {label}: missing anchor")
            ok = False
            continue
        order_ok = bm.start() < am.start() < vm.start()
        print(f"{label}: badge@{bm.start():,} aside@{am.start():,} {nxt}@{vm.start():,} order_ok={order_ok}")
        ok = ok and order_ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
