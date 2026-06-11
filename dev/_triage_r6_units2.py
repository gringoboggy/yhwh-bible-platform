"""Round-6b: structural diff of gen 1:1's three popup units. Read-only."""

import collections
import io
import re
import sys
import zipfile

art = sys.argv[1]
with zipfile.ZipFile(art) as z:
    t = io.TextIOWrapper(z.open("index_split_000_02.html"), encoding="utf-8").read()

for uid in ("vnotes-gen-1-1", "vnotes-gen-1-1-s2", "vnotes-gen-1-1-s3"):
    m = re.search(rf'<aside[^>]*id="{uid}"[^>]*>(.*?)</aside>', t, re.DOTALL)
    body = m.group(1)
    tags = collections.Counter(tg.split()[0].strip("<>/") for tg in re.findall(r"<[a-zA-Z][^>]*>", body))
    links = re.findall(r'<a[^>]*href="([^"]+)"', body)
    eptypes = re.findall(r'epub:type="([^"]+)"', body)
    print(f"=== {uid} ===")
    print("  tags:", dict(tags))
    print("  links:", len(links), "->", [ln[:40] for ln in links[:6]])
    print("  epub:type inside:", collections.Counter(eptypes))
    print("  head 220:", repr(body[:220]))
    print("  tail 160:", repr(body[-160:]))
