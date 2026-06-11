"""One-shot triage: orphan footnote asides (Mac turn-71 TRIAGE→WIN).

Counts <aside epub:type="footnote"> ids never referenced by any href anchor /
noteref anchor, grouped by book code. Read-only. Pass an .epub/.kepub.epub
path to scan an artifact; default scans epub_working/.
"""

import collections
import io
import pathlib
import re
import sys
import zipfile

base = pathlib.Path("epub_working")
aside_re = re.compile(r'<aside[^>]*?id="([^"]+)"[^>]*?epub:type="footnote"')
aside_re2 = re.compile(r'<aside[^>]*?epub:type="footnote"[^>]*?id="([^"]+)"')
href_re = re.compile(r'href="(?:[^"#]*)#([^"]+)"')

noteref_re = re.compile(r'<a[^>]*epub:type="noteref"[^>]*href="(?:[^"#]*)#([^"]+)"')
noteref_re2 = re.compile(r'<a[^>]*href="(?:[^"#]*)#([^"]+)"[^>]*epub:type="noteref"')


def iter_docs():
    if len(sys.argv) > 1:
        with zipfile.ZipFile(sys.argv[1]) as z:
            for name in sorted(z.namelist()):
                if name.endswith((".html", ".xhtml")):
                    yield name, io.TextIOWrapper(z.open(name), encoding="utf-8").read()
    else:
        for f in sorted(base.glob("*.html")):
            yield f.name, f.read_text(encoding="utf-8")


ids: dict[str, str] = {}
hrefs: set[str] = set()
noteref_targets: set[str] = set()
for fname, t in iter_docs():
    for rx in (aside_re, aside_re2):
        for m in rx.finditer(t):
            ids[m.group(1)] = fname
    hrefs.update(href_re.findall(t))
    for rx in (noteref_re, noteref_re2):
        noteref_targets.update(rx.findall(t))

for label, refset in (("href", hrefs), ("noteref", noteref_targets)):
    orph = [(i, fn) for i, fn in ids.items() if i not in refset]
    print(f"total footnote asides: {len(ids)} | no-{label} orphans: {len(orph)}")
    cnt: collections.Counter[str] = collections.Counter()
    for i, _fn in orph:
        m = re.match(r"(?:vnotes?|v)-([a-z0-9]+)-", i)
        cnt[m.group(1) if m else i[:24]] += 1
    print(" ", cnt.most_common(10))
    print("  sample ids:", [i for i, _ in orph[:6]])
