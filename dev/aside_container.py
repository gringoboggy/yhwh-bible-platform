#!/usr/bin/env python3
import re
import sys
import zipfile
from pathlib import Path

path = Path(sys.argv[1] if len(sys.argv) > 1 else "G:/YHWH-koboQA.kepub.epub")
with zipfile.ZipFile(path) as zf:
    name = next(n for n in zf.namelist() if "index_split_000_02" in n)
    text = zf.read(name).decode("utf-8", "replace")

for aid in ("vnote-gen-1-12", "vnotes-gen-1-12-s1", "vnotes-gen-1-1-s6", "vnotes-gen-1-1-s7"):
    i = text.find(f'id="{aid}"')
    pre = text[max(0, i - 400) : i]
    in_notes = "notes-section" in pre.split("<aside")[-1] if i != -1 else False
    in_vrefs = "verse-refs-section" in pre
    print(f"{aid} @{i}: notes-section={in_notes} verse-refs={in_vrefs}")
    if i != -1:
        print("  tail:", pre[-100:].replace("\n", " "))
        print()
