"""K-R2/K-R3 artifact gates — run against a built EPUB (or .kepub.epub).

Checks the Kobo fix arcs on the real artifact:
  1. piece geometry — every book-title page (bp-NN) LEADS its own piece with no
     verse content (the forced singleton); the in-content ToC piece carries no
     bp-; no piece ends with a bare trailing chapter opener; size distribution.
  2. noteref integrity — every bare-fragment epub:type="noteref" href resolves
     in its own file (the native popup contract).
  3. metadata — OPF dc:description carries "83" (never 88); nav lists ONE
     Colophon + a Copyright entry; no ", or" alt book names in nav/ncx;
     colophonend has no Generated-vX/URN.
  4. K-R3-4 gates — (a) ZERO promoted (cross-file) noteref hrefs: a cross-file
     noteref NAVIGATES on Kobo instead of popping, so the splitter must never
     separate a badge from its aside; (b) every href-TARGETED id is unique
     across pieces (kepubify's per-file kobo.* span ids are exempt — they are
     file-scoped by design; an untargeted duplicated wrapper id is harmless);
     (c) no verse-notes badge renders past its own chapter's heading (the
     kobo8 badge-cluster / "teleport to chapter 1" class — 264 pre-fix).

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
    all_bp_ids: set[str] = set()
    for n in pieces:
        t = zf.read(n).decode("utf-8", "replace")
        sizes.append(len(t))
        bps = re.findall(r'id="bp-\d+"', t)
        all_bp_ids.update(bps)
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

    # canon-aware + non-tautological (Mac turn-61, review C14): the real
    # invariant is each bp- id occurs EXACTLY ONCE across all pieces (every
    # book present got exactly one title singleton — works for every canon:
    # catholic-study 75, eth 86 incl. the 3 appendix title pages). Comparing
    # a total count against len(all_bp_ids) could never fail.
    bp_occurrences: dict[str, int] = {}
    for n in pieces:
        for bid in re.findall(r'id="(bp-\d+)"', zf.read(n).decode("utf-8", "replace")):
            bp_occurrences[bid] = bp_occurrences.get(bid, 0) + 1
    for bid, cnt in sorted(bp_occurrences.items()):
        if cnt != 1:
            fails.append(f"book-title id {bid} appears {cnt}x across pieces (must be exactly 1)")

    # ── 2. noteref same-file resolution + NO promoted (cross-file) refs ──
    # Review C9/C13: the old href="#…" regex was structurally blind to a
    # PROMOTED noteref (href="piece.html#frag") — the exact form that
    # NAVIGATES instead of popping on Kobo (K-R3-4 class). Match every
    # noteref <a> attribute-order-insensitively, then split its href.
    unresolved = 0
    total_refs = 0
    promoted = 0
    dup_ids: dict[str, int] = {}
    seen_in: dict[str, str] = {}
    for n in pieces:
        t = zf.read(n).decode("utf-8", "replace")
        ids = set(re.findall(r'\sid="([^"]+)"', t))
        for i in ids:
            # kepubify legitimately repeats its own wrapper/span ids per file
            if i.startswith("kobo.") or i in ("book-columns", "book-inner"):
                continue
            if i in seen_in and seen_in[i] != n:
                dup_ids[i] = dup_ids.get(i, 1) + 1
            seen_in.setdefault(i, n)
        for tag in re.findall(r'<a\b[^>]*epub:type="noteref"[^>]*>', t):
            href = re.search(r'href="([^"]*)"', tag)
            if not href:
                continue
            total_refs += 1
            target = href.group(1)
            if "#" in target and target.split("#", 1)[0]:
                promoted += 1
            elif target.startswith("#") and target[1:] not in ids:
                unresolved += 1
    if unresolved:
        fails.append(f"{unresolved}/{total_refs} noterefs unresolved in-file")
    if promoted:
        fails.append(
            f"{promoted}/{total_refs} noterefs PROMOTED to cross-file links "
            "(navigate instead of popping on Kobo — K-R3-4 class)"
        )
    if dup_ids:
        # informational until the reopen-id strip lands (review C16):
        # duplicated ids are legal per-file HTML but poison the idmap.
        print(f"warn: {len(dup_ids)} content id(s) duplicated across pieces: {sorted(dup_ids)[:6]}")

    # ── 3. metadata ──────────────────────────────────────────────────────
    opf_name = next(n for n in names if n.endswith(".opf"))
    opf = zf.read(opf_name).decode("utf-8", "replace")
    m = re.search(r"<dc:description>([^<]*)</dc:description>", opf)
    desc = m.group(1) if m else ""
    # canon-aware: only the stale "88 scriptures" claim is gated here. A stated
    # count is NOT required to equal the bp- count — title pages outnumber the
    # public book count when demoted appendices keep theirs (eth: 86 bp- pages
    # = 83 books + the 3 Daniel-addition appendices, and "83" is the honest
    # public number per the K-R2-8 rule). Canon-filtered descriptions may
    # state no count at all.
    if "88" in desc:
        fails.append(f"OPF description still claims 88: {desc[:100]!r}")
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

    # ── 4. K-R3-4 gates ──────────────────────────────────────────────────
    promoted_re = (
        re.compile(r'<a[^>]*href="index_split_[^"#]+#[^"]+"[^>]*epub:type="noteref"'),
        re.compile(r'<a[^>]*epub:type="noteref"[^>]*href="index_split_[^"#]+#[^"]+"'),
    )
    ch_anchor_re = re.compile(r'id="ch-b\d+-c(\d+)"')
    badge_re = re.compile(r'id="vbadge-([a-z0-9]+)-(\d+)-(\d+)"')
    promoted = 0
    id_home: dict[str, str] = {}
    dup_ids: set[str] = set()
    targeted: set[str] = set()
    spilled: list[str] = []
    for n in pieces:
        t = zf.read(n).decode("utf-8", "replace")
        # 4d/4e — splice-corruption tripwires (the kr3a RSC-016 class): every
        # vbadge id keeps its <a> head, and <aside> tags stay balanced.
        heads = t.count('<a class="verse-notes-badge"')
        vbids = len(re.findall(r'\bid="vbadge-', t))
        if heads != vbids:
            fails.append(f"{n}: {vbids - heads} sheared badge anchor(s) — splice corruption")
        opens = len(re.findall(r"<aside\b", t))
        closes = t.count("</aside>")
        if opens != closes:
            fails.append(f"{n}: unbalanced <aside> ({opens} open / {closes} close)")
        # 4f — no badge nested inside an aside (the silent kr3a variant:
        # well-formed but invisible to the reader).
        walk = sorted(
            [(m.start(), 1) for m in re.finditer(r"<aside\b", t)]
            + [(m.start(), -1) for m in re.finditer(r"</aside>", t)]
            + [(m.start(), 0) for m in re.finditer(r'<a class="verse-notes-badge"', t)]
        )
        depth = 0
        buried = 0
        for _pos, d in walk:
            if d == 0:
                buried += depth > 0
            else:
                depth += d
        if buried:
            fails.append(f"{n}: {buried} verse-notes badge(s) nested inside asides (hidden from the reader)")
        for rx in promoted_re:
            promoted += len(rx.findall(t))
        for m in re.finditer(r'\bid="([^"]+)"', t):
            i = m.group(1)
            if i.startswith("kobo."):
                continue  # kepubify's span ids are file-scoped by design
            if id_home.setdefault(i, n) != n:
                dup_ids.add(i)
        for m in re.finditer(r'href="[^"#]*#([^"]+)"', t):
            targeted.add(m.group(1))
        events: list[tuple[int, str, object]] = []
        for m in ch_anchor_re.finditer(t):
            events.append((m.start(), "ch", int(m.group(1))))
        for m in badge_re.finditer(t):
            events.append((m.start(), "badge", (m.group(1), int(m.group(2)), int(m.group(3)))))
        cur = None
        for _pos, kind, val in sorted(events):
            if kind == "ch":
                cur = val
            elif cur is not None and val[1] < cur:
                spilled.append(f"{n}: {val[0]} {val[1]}:{val[2]} renders inside chapter {cur}")
    if promoted:
        fails.append(f"{promoted} PROMOTED (cross-file) noteref hrefs — popups would navigate, not pop")
    dup_targeted = sorted(i for i in dup_ids if i in targeted)
    if dup_targeted:
        fails.append(f"{len(dup_targeted)} href-targeted ids duplicated across pieces (first 5: {dup_targeted[:5]})")
    if spilled:
        fails.append(f"{len(spilled)} badges render past their chapter's heading (K-R3-4); first 3:")
        fails.extend("  " + s for s in spilled[:3])

    print(f"pieces: {len(pieces)}  title-singletons: {title_pieces}")
    print(
        f"sizes: min {min(sizes):,}  max {max(sizes):,}  mean {int(statistics.mean(sizes)):,}"
        f"  median {int(statistics.median(sizes)):,}"
    )
    print(f"noterefs: {total_refs:,} all-resolve={unresolved == 0}")
    print(f"promoted-noterefs: {promoted}  dup-targeted-ids: {len(dup_targeted)}  ch-spilled-badges: {len(spilled)}")
    if fails:
        print("\nFAILURES:")
        for f in fails:
            print("  ✗", f)
        return 1
    print("ALL K-R2 GATES GREEN")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
