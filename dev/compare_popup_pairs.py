#!/usr/bin/env python3
"""Compare working vs failing popup pairs in ONE kepub piece (gen 1)."""

from __future__ import annotations

import re
import sys
import zipfile
from html import unescape
from pathlib import Path

PAIRS = (
    ("WORK translation", "v-gen-1-12", "vnote-gen-1-12"),
    ("FAIL study", "vbadge-gen-1-12-s1", "vnotes-gen-1-12-s1"),
    ("WORK study s6", "vbadge-gen-1-1-s6", "vnotes-gen-1-1-s6"),
    ("FAIL study s7", "vbadge-gen-1-1-s7", "vnotes-gen-1-1-s7"),
)


def _strip(html: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", html))).strip()


def main(path: Path) -> int:
    with zipfile.ZipFile(path) as zf:
        name = next(n for n in zf.namelist() if "index_split_000_02" in n)
        text = zf.read(name).decode("utf-8", "replace")

    print(f"file: {name} ({len(text):,} B)\n")
    for label, rid, aid in PAIRS:
        rm = re.search(rf'<a\b[^>]*\bid="{re.escape(rid)}"[^>]*>', text)
        am = re.search(
            rf'<aside\b[^>]*\bid="{re.escape(aid)}"[^>]*>.*?</aside>',
            text,
            re.DOTALL,
        )
        print(f"=== {label}: {rid} → {aid} ===")
        if not rm or not am:
            print("  missing ref or aside\n")
            continue
        aside = am.group(0)
        print(f"  ref @{rm.start():,} aside @{am.start():,}")
        chunk = text[rm.end() : rm.end() + 300]
        nxt_vn = re.search(r'<a class="vn-link" id="([^"]+)"', chunk)
        print(f"  next_is_vn_link: {bool(nxt_vn)} ({nxt_vn.group(1) if nxt_vn else '-'})")
        # region tail in file after badge
        tail = text[rm.end() : rm.end() + 80]
        print(f"  after ref: {tail.replace(chr(10), ' ')!r}")
        print()
    return 0


if __name__ == "__main__":
    p = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("G:/YHWH-koboQA.kepub.epub")
    raise SystemExit(main(p))
