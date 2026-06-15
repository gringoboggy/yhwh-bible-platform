#!/usr/bin/env python3
import re
import sys
import zipfile
from pathlib import Path

path = Path(sys.argv[1] if len(sys.argv) > 1 else "G:/YHWH-koboQA.kepub.epub")
with zipfile.ZipFile(path) as zf:
    name = next(n for n in zf.namelist() if "index_split_000_02" in n)
    text = zf.read(name).decode("utf-8", "replace")

pairs = [
    ("FAIL vbadge 1:12", "vbadge-gen-1-12-s1", "vnotes-gen-1-12-s1"),
    ("WORK vn 1:12", "v-gen-1-12", "vnote-gen-1-12"),
    ("WORK vbadge s6", "vbadge-gen-1-1-s6", "vnotes-gen-1-1-s6"),
    ("FAIL vbadge s7", "vbadge-gen-1-1-s7", "vnotes-gen-1-1-s7"),
]
for label, rid, aid in pairs:
    rm = re.search(rf'id="{re.escape(rid)}"', text)
    am = re.search(rf'id="{re.escape(aid)}"', text)
    if not rm or not am:
        print(label, "MISSING")
        continue
    between = text[rm.start() : am.start()]
    ids = re.findall(r'\bid="([^"]+)"', between)
    print(f"{label}: ref@{rm.start():,} aside@{am.start():,} delta={am.start() - rm.start():,} ids_between={len(ids)}")
    print(f"  first ids: {ids[:8]}")
    print(f"  last ids: {ids[-5:]}")
    print()
