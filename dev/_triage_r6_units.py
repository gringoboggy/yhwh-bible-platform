"""One-shot round-6b forensics: gen 1:1 split units + title-page caption spacing.

Read-only scan of a built artifact. Usage: py -3 dev/_triage_r6_units.py <artifact>
"""

import io
import re
import sys
import zipfile

art = sys.argv[1]
TAG_RE = re.compile(r"<[^>]+>")

docs: dict[str, str] = {}
with zipfile.ZipFile(art) as z:
    for name in sorted(z.namelist()):
        if name.endswith((".html", ".xhtml")):
            docs[name] = io.TextIOWrapper(z.open(name), encoding="utf-8").read()

# --- gen 1:1 units: every aside whose id mentions gen-1-1, + every noteref to it
aside_re = re.compile(r'<aside[^>]*id="([^"]*gen-1-1[^"]*)"[^>]*>(.*?)</aside>', re.DOTALL)
for fname, t in docs.items():
    for m in aside_re.finditer(t):
        body = m.group(2)
        stripped = TAG_RE.sub("", body)
        kobo = body.count('class="koboSpan"')
        print(
            f"ASIDE {m.group(1):32s} file={fname:28s} raw={len(body):7,d} stripped={len(stripped):6,d} koboSpans={kobo}"
        )
    for m in re.finditer(r'<a[^>]*href="(?:[^"#]*)#([^"]*gen-1-1[^"]*)"[^>]*>(.*?)</a>', t):
        if "noteref" in m.group(0):
            inner = TAG_RE.sub("", m.group(2))
            print(f"NOTEREF -> {m.group(1):30s} file={fname:28s} label={inner!r}")

# --- title-page caption: BOOK + roman numeral spacing
cap_re = re.compile(r">([^<]*BOOK[^<]{0,12})<")
seen = set()
for fname, t in docs.items():
    if "book-title-page" not in t:
        continue
    for m in cap_re.finditer(t):
        s = m.group(1)
        if s not in seen:
            seen.add(s)
            if len(seen) <= 6:
                i = m.start()
                print(f"CAPTION {s!r} in {fname}: ...{t[max(0, i - 160) : i + 80]!r}")
print("distinct BOOK caption text nodes:", len(seen))
