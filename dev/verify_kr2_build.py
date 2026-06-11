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

# ── 5. kindle_safe (turn-69 ①) ──────────────────────────────────────────
# Runs ONLY when the build stamped the OPF with target-reader=kindle (the
# stamp is patch_opf's, emitted from the one resolver — skew-proof; non-kindle
# artifacts are never judged against the kindle bar). Checks the CONFIRMED
# E999 trigger pair: (a) ≤10,000 chars of text under EFFECTIVE display:none —
# effective = last-rule-wins per selector string across every .css member, so
# the base hides pair with the kindle_safe overrides (which mirror the base
# selector strings verbatim for exactly this reason); (b) exactly one
# dc:language. Plus a fail-fast: the kindle_safe CSS marker must be present at
# all (a stamped-kindle artifact whose variant CSS never got appended is a
# stale/mismatched build regardless of the volume math).
_CSS_RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}")
_CSS_DISPLAY_RE = re.compile(r"display\s*:\s*([a-z-]+)")


def _effective_hidden_selectors(css_texts: list[str]) -> list[str]:
    """Selector strings whose LAST display declaration is none."""
    last: dict[str, str] = {}
    for css in css_texts:
        # comments must go BEFORE rule parsing or they glom into the next
        # selector text and break the hide↔override pairing
        css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
        for m in _CSS_RULE_RE.finditer(css):
            d = _CSS_DISPLAY_RE.search(m.group(2))
            if not d:
                continue
            for sel in m.group(1).split(","):
                sel = " ".join(sel.split())
                if sel:
                    last[sel] = d.group(1)
    return [s for s, v in last.items() if v == "none"]


def _class_token(selector: str) -> str | None:
    """The LAST class token of a selector (conservative element matcher —
    over-counts descendant selectors toward fail-safe); pseudo-element
    selectors return None (no text content)."""
    if "::" in selector:
        return None
    classes = re.findall(r"\.([A-Za-z0-9_-]+)", selector)
    return classes[-1] if classes else None


def _hidden_text_chars(zf: zipfile.ZipFile, names: list[str], tokens: set[str]) -> int:
    """Total tag-stripped text chars inside elements matching a hidden class."""
    total = 0
    docs = [n for n in names if n.endswith((".html", ".xhtml"))]
    open_re = re.compile(
        r"<([a-z][a-z0-9]*)\b[^>]*\bclass=\"[^\"]*\b(?:" + "|".join(sorted(tokens)) + r")\b[^\"]*\"[^>]*>"
    )
    for n in docs:
        t = zf.read(n).decode("utf-8", "replace")
        for m in open_re.finditer(t):
            tag = m.group(1)
            depth, pos = 1, m.end()
            tag_re = re.compile(rf"<{tag}\b[^>]*>|</{tag}>")
            while depth and pos < len(t):
                nm = tag_re.search(t, pos)
                if not nm:
                    break
                depth += -1 if nm.group(0).startswith("</") else 1
                pos = nm.end()
            inner = t[m.end() : pos]
            total += len(re.sub(r"<[^>]+>", "", inner))
    return total


def kindle_safe_checks(zf: zipfile.ZipFile, names: list[str], opf: str) -> list[str]:
    """Gate 5 — kindle_safe. Empty list = green (or not a kindle artifact)."""
    stamp = re.search(r'<meta name="yhwh:target-reader" content="([^"]+)"', opf)
    if not stamp or stamp.group(1) != "kindle":
        return []
    fails: list[str] = []
    if opf.count("<dc:language>") != 1:
        fails.append(f"kindle: OPF carries {opf.count('<dc:language>')} dc:language values (want exactly 1 — E999)")
    css_names = [n for n in names if n.endswith(".css")]
    css_texts = [zf.read(n).decode("utf-8", "replace") for n in css_names]
    if not any("kindle_safe" in c for c in css_texts):
        fails.append(
            "kindle: target stamped kindle but the kindle_safe CSS was never appended (stale/mismatched build)"
        )
    hidden = _effective_hidden_selectors(css_texts)
    tokens = {tok for tok in (_class_token(s) for s in hidden) if tok}
    chars = _hidden_text_chars(zf, names, tokens) if tokens else 0
    if chars > 10_000:
        fails.append(
            f"kindle: {chars:,} chars under effective display:none "
            f"(Amazon hard-fails >10,000 — E3013); hidden selectors: {hidden[:8]}"
        )
    # K-KIN forensics (2026-06-11): the variant physically strips hidden=""
    # from footnote wrappers (Amazon's hidden-text counter is opaque — it may
    # key the raw attribute, not the effective CSS cascade). Any survivor on
    # a kindle artifact = a stale/unsafe build.
    hidden_attrs = 0
    for n in names:
        if not n.endswith((".html", ".xhtml")):
            continue
        t = zf.read(n).decode("utf-8", "replace")
        hidden_attrs += len(
            re.findall(r'<(?:aside|section)\b(?=[^>]*epub:type="footnotes")[^>]*\shidden(?:="[^"]*")?[^>]*>', t)
        )
    if hidden_attrs:
        fails.append(
            f'kindle: {hidden_attrs} footnote wrapper(s) still carry hidden="" '
            "(apply_kindle_unhide never ran — stale/unsafe build)"
        )
    return fails


# ── 4g. K-R4-2 — popup-unit stripped-size cap ───────────────────────────
# Round-5 device bracket: pops <= 4,498 / declines >= 5,500 stripped chars.
# Anything ABOVE the proven-pop floor is unproven on-device, so the merged
# verse-notes units (the class the K-R4-2 split caps) FAIL above it; the
# base-baked vnote (translation) asides are a different surface (round-5
# taps showed them all popping) — oversized ones surface as honest WARNS,
# not fails (no-reassert-ratified-bar).
POP_FLOOR = 4_498

_POPUP_ASIDE_RE = re.compile(
    r'<aside class="(verse-notes|vnote)[^"]*" id="([^"]+)"[^>]*>.*?</aside>',
    re.DOTALL,
)


def _stripped_len(aside_html: str) -> int:
    import html as _html

    text = re.sub(r"<[^>]+>", "", aside_html)
    text = _html.unescape(text)
    return len(re.sub(r"\s+", " ", text).strip())


def popup_size_checks(zf: zipfile.ZipFile, names: list[str]) -> tuple[list[str], list[str]]:
    """Gate 4g. Returns (fails, warns)."""
    fails: list[str] = []
    warns: list[str] = []
    for n in names:
        if not n.endswith((".html", ".xhtml")):
            continue
        t = zf.read(n).decode("utf-8", "replace")
        for m in _POPUP_ASIDE_RE.finditer(t):
            size = _stripped_len(m.group(0))
            if size <= POP_FLOOR:
                continue
            if m.group(1) == "verse-notes":
                fails.append(f"{n}: {m.group(2)} strips to {size:,} chars (> pop floor {POP_FLOOR:,} — K-R4-2)")
            else:
                warns.append(f"{n}: vnote {m.group(2)} strips to {size:,} chars (> pop floor; un-probed class)")
    return fails, warns


# ── 4i. badge-mode marker-leak — no per-note note-ref survives ──────────
def badge_mode_leak_checks(zf: zipfile.ZipFile, names: list[str]) -> list[str]:
    """A badge-mode artifact (any verse-notes-badge present) must carry ZERO
    per-note ``note-ref`` markers — a survivor means apply_badge_markers'
    verse-region walk missed it (round-6 catch: rev 22:21's spill markers
    past the bp-87 title div). Numbers-mode artifacts are exempt (markers
    ARE the contract there)."""
    docs = [n for n in names if n.endswith((".html", ".xhtml"))]
    texts = {n: zf.read(n).decode("utf-8", "replace") for n in docs}
    if not any('class="verse-notes-badge"' in t for t in texts.values()):
        return []
    fails: list[str] = []
    for n, t in texts.items():
        leaks = re.findall(r'<a class="note-ref[^"]*" id="(ref-[^"]+)"', t)
        if leaks:
            fails.append(f"{n}: {len(leaks)} per-note note-ref marker(s) leaked in badge mode: {leaks[:4]}")
    return fails


# ── 4j. orphan vnote asides — every footnote popup is reachable ─────────
def orphan_vnote_checks(zf: zipfile.ZipFile, names: list[str]) -> list[str]:
    """No vnote-family footnote aside may be unreferenced by every href
    (WIN triage 2026-06-11: the fold/canon-splice passes dropped a book's
    body+markers but left its vnote asides — eth 206 / catholic-study
    kindle 1,598 unreachable popups; user-visible "[no text]" endnote rows
    on kindle once unhide applies). drop_orphan_vnote_asides is the fix;
    this gate pins it."""
    docs = [n for n in names if n.endswith((".html", ".xhtml"))]
    ids: dict[str, str] = {}
    hrefs: set[str] = set()
    for n in docs:
        t = zf.read(n).decode("utf-8", "replace")
        for m in re.finditer(r'<aside\b(?=[^>]*\bid="(vnotes?-[^"]+)")(?=[^>]*\bepub:type="footnote")', t):
            ids[m.group(1)] = n
        hrefs.update(re.findall(r'href="[^"#]*#([^"]+)"', t))
    orphans = sorted(i for i in ids if i not in hrefs)
    if not orphans:
        return []
    return [f"{len(orphans)} unreachable vnote aside(s) (4j orphan class); first 4: {orphans[:4]}"]


# ── 4h. K-R5-3 — book-title singletons carry no verse badges/asides ─────
def title_piece_badge_checks(zf: zipfile.ZipFile, names: list[str]) -> list[str]:
    """A piece holding a book-title page must carry NO verse-notes badge or
    aside — in v0.1.0 all 38 title pieces showed the previous book's
    last-verse badge (the K-R5-3 clamp escape)."""
    fails: list[str] = []
    for n in names:
        if not re.search(r"index_split_\d+(?:_\d+)?\.html$", n):
            continue
        t = zf.read(n).decode("utf-8", "replace")
        if 'id="bp-' not in t:
            continue
        for needle, what in (
            ('class="verse-notes-badge"', "verse badge"),
            ('id="vnotes-', "verse-notes aside"),
        ):
            if needle in t:
                bp = re.search(r'id="(bp-\d+)"', t)
                fails.append(f"{n}: book-title piece ({bp.group(1) if bp else '?'}) carries a {what} (K-R5-3)")
    return fails


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
    hidden_body_links = 0
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
        # round-7 5.2 — gate 2b: note-BODY links must never target a hidden
        # #vnote- container (href-FIRST attribute order = the body-link class;
        # vn-link noterefs start with class= and never match). A hidden target
        # makes Kobo navigate to file start (the teleport class).
        hidden_body_links += len(re.findall(r'<a href="(?:[A-Za-z0-9_.-]+\.html)?#vnote-', t))
    if unresolved:
        fails.append(f"{unresolved}/{total_refs} noterefs unresolved in-file")
    if hidden_body_links:
        fails.append(
            f"{hidden_body_links} note-body link(s) target hidden #vnote- containers "
            "(Kobo teleport class — retarget to the visible #v- anchors; round-7 5.2)"
        )
    if promoted:
        fails.append(
            f"{promoted}/{total_refs} noterefs PROMOTED to cross-file links "
            "(navigate instead of popping on Kobo — K-R3-4 class)"
        )
    if dup_ids:
        # HARD FAIL since the reopen-id strip landed (review C16): the splitter
        # no longer replays ids in reopen prefixes, so any cross-piece duplicate
        # is a real defect (poisons the idmap's last-writer-wins).
        fails.append(f"{len(dup_ids)} content id(s) duplicated across pieces: {sorted(dup_ids)[:6]}")

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

    # ── 4. K-R3 placement + splice-corruption gates ──────────────────────
    # (promoted-noteref + cross-piece dup-id failing live in gate 2 above —
    # Mac's attr-order-insensitive matching is authoritative there.)
    ch_anchor_re = re.compile(r'id="ch-b\d+-c(\d+)"')
    # (?:-s\d+)? — K-R4-2 split units suffix sibling badges; every unit of a
    # verse must satisfy the same chapter-placement invariant.
    badge_re = re.compile(r'id="vbadge-([a-z0-9]+)-(\d+)-(\d+)(?:-s\d+)?"')
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
    if spilled:
        fails.append(f"{len(spilled)} badges render past their chapter's heading (K-R3-4); first 3:")
        fails.extend("  " + s for s in spilled[:3])

    # ── 4g. K-R4-2 popup-unit size cap + 4h. K-R5-3 title-piece badges ───
    size_fails, size_warns = popup_size_checks(zf, names)
    fails.extend(size_fails)
    for w in size_warns:
        print(f"WARN (4g): {w}")
    fails.extend(title_piece_badge_checks(zf, names))
    fails.extend(badge_mode_leak_checks(zf, names))
    fails.extend(orphan_vnote_checks(zf, names))

    # ── 5. kindle_safe — only judges artifacts stamped target-reader=kindle ─
    fails.extend(kindle_safe_checks(zf, names, opf))

    print(f"pieces: {len(pieces)}  title-singletons: {title_pieces}")
    print(
        f"sizes: min {min(sizes):,}  max {max(sizes):,}  mean {int(statistics.mean(sizes)):,}"
        f"  median {int(statistics.median(sizes)):,}"
    )
    print(f"noterefs: {total_refs:,} all-resolve={unresolved == 0}")
    print(f"promoted-noterefs: {promoted}  dup-ids: {len(dup_ids)}  ch-spilled-badges: {len(spilled)}")
    if fails:
        print("\nFAILURES:")
        for f in fails:
            print("  ✗", f)
        return 1
    print("ALL K-R2 GATES GREEN")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
