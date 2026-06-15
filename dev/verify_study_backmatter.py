#!/usr/bin/env python3
"""Quick check: K-R9 study glossary present; prose has badges not inline asides."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg:
        p = Path(arg)
    else:
        builds = sorted((REPO / "build" / "kobo-marker-ab").glob("*.kepub.epub"))
        p = builds[-1] if builds else None
    if not p or not p.is_file():
        print("FAIL: no kepub")
        return 1
    with zipfile.ZipFile(p) as z:
        study = [n for n in z.namelist() if "900" in n and n.endswith(".html")]
        print(f"artifact: {p.name}")
        print(f"study_glossary_files: {len(study)}")
        if not study:
            print("FAIL: no index_split_900* study glossary")
            return 1
        body = z.read(study[0]).decode("utf-8")
        print(f"glossary_has_heading: {'Study Notes' in body}")
        print(f"glossary_has_return: {'study-return' in body}")
        prose_inline = False
        badge_in_prose = False
        for name in sorted(z.namelist()):
            if not name.endswith(".html") or "900" in name:
                continue
            t = z.read(name).decode("utf-8")
            if "vbadge-gen-1-1-" in t or "vbadge-gen-1-12-" in t:
                badge_in_prose = True
                if 'aside class="verse-notes"' in t and "study-notes-index" not in t:
                    prose_inline = True
                break
        print(f"badge_in_prose: {badge_in_prose}")
        print(f"inline_aside_in_prose: {prose_inline}")
        ok = "Study Notes" in body and "study-return" in body and badge_in_prose and not prose_inline
        print("PASS" if ok else "FAIL")
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
