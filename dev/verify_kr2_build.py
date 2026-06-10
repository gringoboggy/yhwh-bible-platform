"""K-R2 round-3 artifact gates — run against a built EPUB (or .kepub.epub).

Checks the Kobo round-2 fix arc on the real artifact:
  1. piece geometry — every book-title page (bp-NN) LEADS its own piece with no
     verse content (the forced singleton); the in-content ToC piece carries no
     bp-; no piece ends with a bare trailing chapter opener; size distribution.
  2. noteref integrity — every bare-fragment epub:type="noteref" href resolves
     in its own file (the native popup contract).
  3. metadata — OPF dc:description carries "83" (never 88); nav lists ONE
     Colophon + a Copyright entry; no ", or" alt book names in nav/ncx;
     colophonend has no Generated-vX/URN.

Usage:  py -3 dev/verify_kr2_build.py <path-to-epub>
Exit 0 = all gates green; 1 = any failure (details printed).
"""

import re
import statistics
import sys
import zipfile

ALT_NAMES = (
    "Ecclesiastes or, The Preacher",
    "The Song of Songs, or Song of Solomon",
    "The Wisdom of Jesus the Son of Sirach, or Ecclesiasticus",
    "4 Baruch, or Paralipomena of Jeremiah",
)


def main(path: str) -> int:
    fails: list[str] = []
    zf = zipfile.ZipFile(path)
    names = zf.namelist()
    pieces = sorted(n for n in names if re.search(r"index_split_\d+(?:_\d+)?\.html$", n))

    # ── 1. piece geometry ────────────────────────────────────────────────
    sizes = []
    title_pieces = 0
    for n in pieces:
        t = zf.read(n).decode("utf-8", "replace")
        sizes.append(len(t))
        bps = re.findall(r'id="bp-\d+"', t)
        has_scripture = 'class="vn-link' in t
        has_toc = 'class="toc-wrap"' in t
        if bps:
            title_pieces += len(bps)
            if len(bps) > 1:
                fails.append(f"{n}: {len(bps)} book-title pages in ONE piece (must be singletons)")
            if has_scripture:
                # a title piece may carry the book's intro BLURB (verse-p-classed
                # editorial text, e.g. Judith/Manasses) — that belongs on the title
                # page; actual scripture (vn-link anchors) must not.
                fails.append(f"{n}: book-title piece carries scripture (not a singleton)")
            if has_toc:
                fails.append(f"{n}: ToC and a book-title page share a piece (kobo22 regression)")
            body = t[t.find("<body") :]
            first_bp = body.find('id="bp-')
            lead = body[:first_bp]
            if 'class="ch-heading"' in lead or 'class="verse-p' in lead:
                fails.append(f"{n}: content precedes the book-title page in its piece")
        # no piece ends with a bare chapter opener: text after the LAST ch-heading
        # must contain verse content (skip title/front/back pieces without headings)
        last_head = t.rfind('class="ch-heading"')
        if last_head != -1 and 'class="verse-p' in t and 'class="verse-p' not in t[last_head:]:
            fails.append(f"{n}: ends with a stranded chapter opener (orphan numeral seam)")

    expected_titles = 83
    if title_pieces < expected_titles:
        fails.append(f"only {title_pieces} book-title pieces found (expected {expected_titles})")

    # ── 2. noteref same-file resolution ─────────────────────────────────
    unresolved = 0
    total_refs = 0
    for n in pieces:
        t = zf.read(n).decode("utf-8", "replace")
        ids = set(re.findall(r'\bid="([^"]+)"', t))
        for frag in re.findall(r'<a[^>]*href="#([^"]+)"[^>]*epub:type="noteref"', t):
            total_refs += 1
            if frag not in ids:
                unresolved += 1
    if unresolved:
        fails.append(f"{unresolved}/{total_refs} noterefs unresolved in-file")

    # ── 3. metadata ──────────────────────────────────────────────────────
    opf_name = next(n for n in names if n.endswith(".opf"))
    opf = zf.read(opf_name).decode("utf-8", "replace")
    m = re.search(r"<dc:description>([^<]*)</dc:description>", opf)
    desc = m.group(1) if m else ""
    if "88" in desc or "83" not in desc:
        fails.append(f"OPF description wrong: {desc[:100]!r}")
    nav_name = next((n for n in names if n.endswith("nav.xhtml")), None)
    if nav_name:
        nav = zf.read(nav_name).decode("utf-8", "replace")
        if nav.count(">Colophon<") != 1:
            fails.append(f"nav lists {nav.count('>Colophon<')} Colophon entries (want exactly 1)")
        if ">Copyright<" not in nav:
            fails.append("nav missing the Copyright entry (front page retitle)")
        for alt in ALT_NAMES:
            if alt in nav:
                fails.append(f"nav still carries alt name: {alt[:40]}")
    ncx_name = next((n for n in names if n.endswith(".ncx")), None)
    if ncx_name:
        ncx = zf.read(ncx_name).decode("utf-8", "replace")
        for alt in ALT_NAMES:
            if alt in ncx:
                fails.append(f"ncx still carries alt name: {alt[:40]}")
    colo = next((n for n in names if n.endswith("colophonend.xhtml")), None)
    if colo:
        ct = zf.read(colo).decode("utf-8", "replace")
        if "Generated" in ct or "urn:yhwh" in ct:
            fails.append("closing colophon still leaks Generated/URN")
    else:
        fails.append("colophonend.xhtml missing (default keeps it)")

    print(f"pieces: {len(pieces)}  title-singletons: {title_pieces}")
    print(
        f"sizes: min {min(sizes):,}  max {max(sizes):,}  mean {int(statistics.mean(sizes)):,}"
        f"  median {int(statistics.median(sizes)):,}"
    )
    print(f"noterefs: {total_refs:,} all-resolve={unresolved == 0}")
    if fails:
        print("\nFAILURES:")
        for f in fails:
            print("  ✗", f)
        return 1
    print("ALL K-R2 GATES GREEN")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
