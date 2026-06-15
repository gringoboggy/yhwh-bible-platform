#!/usr/bin/env python3
"""K-R9 crash forensics — study glossary size, badge hrefs, duplicate asides."""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    p = Path(sys.argv[1]) if len(sys.argv) > 1 else sorted((REPO / "build" / "kobo-marker-ab").glob("*.kepub.epub"))[-1]
    print(f"artifact: {p.name} ({p.stat().st_size:,} B)")
    with zipfile.ZipFile(p) as z:
        htmls = [(n, z.getinfo(n).file_size) for n in z.namelist() if n.endswith(".html")]
        htmls.sort(key=lambda x: -x[1])
        print("\nLargest HTML files:")
        for n, sz in htmls[:12]:
            print(f"  {sz:>10,}  {n}")

        study = [(n, sz) for n, sz in htmls if "900" in n]
        print(f"\nStudy glossary files: {len(study)}")
        for n, sz in study:
            print(f"  {sz:>10,}  {n}")

        opf = next(n for n in z.namelist() if n.endswith(".opf"))
        opf_t = z.read(opf).decode("utf-8")
        refs = re.findall(r'<itemref idref="([^"]+)"', opf_t)
        items = dict(re.findall(r'<item id="([^"]+)"[^>]*href="([^"]+)"', opf_t))
        study_refs = [r for r in refs if r.startswith("studynotes") or "900" in items.get(r, "")]
        print(f"\nSpine study positions: {[refs.index(r) for r in study_refs if r in refs]}")
        print(f"Spine tail: {refs[-10:]}")
        for r in study_refs:
            print(f"  item {r} -> {items.get(r)}")

        # Gen 1:1 badges
        badge_re = re.compile(r'id="(vbadge-gen-1-1-s\d)"[^>]*href="([^"]+)"')
        for n, _ in sorted(htmls, key=lambda x: x[0]):
            t = z.read(n).decode("utf-8", errors="replace")
            if "vbadge-gen-1-1-s1" not in t:
                continue
            print(f"\nGen 1:1 in {n}:")
            for bid, href in badge_re.findall(t):
                print(f"  {bid} -> {href}")
            aside_count = t.count("vnotes-gen-1-1-s")
            inline_asides = len(re.findall(r'<aside class="verse-notes', t))
            print(f"  vnotes id mentions: {aside_count}, inline asides: {inline_asides}")
            if '<aside class="notes-section"' in t:
                print("  HAS notes-section in this file")

        # Nav / ncx study entry
        for nav_name in (n for n in z.namelist() if n.endswith(("nav.xhtml", "toc.ncx"))):
            nav_t = z.read(nav_name).decode("utf-8", errors="replace")
            if "Study Notes" in nav_t or "900" in nav_t:
                print(f"\n{nav_name} mentions Study Notes / 900: yes")
                for line in nav_t.splitlines():
                    if "Study" in line or "900" in line:
                        print(" ", line.strip()[:120])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
