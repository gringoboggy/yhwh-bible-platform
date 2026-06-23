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
  4m/4n. K-R6-2 — the popup anchor namespace is prefix-free (every
     vnotes/vbadge id wears -s<1..9>; no id is a strict prefix of another in
     its file) and, on kepub artifacts, no verse-notes aside serializes past
     the 8,858 B proven-open floor (Nickel refuses above it and navigates).

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
# E999 trigger: ANY text under a RAW display:none / visibility:hidden. Amazon's
# server scan does NOT resolve the CSS cascade, so a later override does not
# clear a base hide (see _raw_hidden_selectors below — the prior "effective /
# last-rule-wins" check gave a false green and is gone). Plus: exactly one
# dc:language, and a fail-fast that the kindle_safe CSS marker is present at all
# (a stamped-kindle artifact whose variant CSS never got appended is stale).
_CSS_RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}")


# K-KIN E999 (2026-06-13): Amazon's Send-to-Kindle / KDP server scan does NOT
# resolve the CSS cascade — a later display:block override does not undo a raw
# display:none over content (the stripped artifact converted to KDP pricing
# where the overridden one did not). So the gate keys on the RAW presence of a
# hide over content, not the effective (last-rule-wins) value, which gave a
# false green (the override "pairs" with the base hide but Amazon never sees it).
_CSS_HIDDEN_DECL_GATE_RE = re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden", re.I)


def _raw_hidden_selectors(css_texts: list[str]) -> list[str]:
    """Selector strings with ANY display:none / visibility:hidden declaration,
    cascade NOT resolved (an override does not clear it for Amazon's server)."""
    out: list[str] = []
    for css in css_texts:
        css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
        for m in _CSS_RULE_RE.finditer(css):
            if _CSS_HIDDEN_DECL_GATE_RE.search(m.group(2)):
                for sel in m.group(1).split(","):
                    sel = " ".join(sel.split())
                    if sel:
                        out.append(sel)
    return out


def _class_token(selector: str) -> str | None:
    """The LAST class token of a selector (conservative element matcher —
    over-counts descendant selectors toward fail-safe); pseudo-element
    selectors return None (no text content)."""
    if "::" in selector:
        return None
    classes = re.findall(r"\.([A-Za-z0-9_-]+)", selector)
    return classes[-1] if classes else None


# Void / self-closing elements carry no text: treating them as containers made
# the depth scan swallow everything between the FIRST and LAST <hr
# class="notes-rule"/> in a file (every following <hr/> *incremented* depth) —
# 98,016 phantom hidden chars on the real big-piece kindle build whose only
# change was piece size.
_VOID_TAGS = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
)


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
            if tag in _VOID_TAGS or m.group(0).endswith("/>"):
                continue  # no content — nothing hidden inside
            depth, pos = 1, m.end()
            tag_re = re.compile(rf"<{tag}\b[^>]*>|</{tag}>")
            while depth and pos < len(t):
                nm = tag_re.search(t, pos)
                if not nm:
                    break
                if nm.group(0).startswith("</"):
                    depth -= 1
                elif not nm.group(0).endswith("/>"):
                    depth += 1
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
    hidden = _raw_hidden_selectors(css_texts)
    tokens = {tok for tok in (_class_token(s) for s in hidden) if tok}
    chars = _hidden_text_chars(zf, names, tokens) if tokens else 0
    if chars > 0:
        fails.append(
            f"kindle: {chars:,} chars under RAW display:none/visibility:hidden "
            "(Amazon's server scan ignores the cascade override and rejects it — "
            f"E3013/E999); strip the hide physically. selectors: {hidden[:8]}"
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
            "(old --target-reader kindle variant apply never ran — stale/unsafe build; production uses kindle_post)"
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
GLOSSARY_DECLINE_HI = 7_748

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


# ── 4g-bis. study-glossary-cat decline ceiling ───────────────────────────
_STUDY_GLOSSARY_CAT_RE = re.compile(
    r'<aside[^>]*class="study-glossary-cat[^"]*"[^>]*>.*?</aside>',
    re.DOTALL,
)


def glossary_cat_checks(zf: zipfile.ZipFile, names: list[str]) -> list[str]:
    """Gate 4g-bis — study-glossary-cat footnotes must stay under the Kobo
    decline ceiling (hist monolith class; round-8 Phase 3)."""
    fails: list[str] = []
    for n in names:
        if not n.endswith((".html", ".xhtml")):
            continue
        t = zf.read(n).decode("utf-8", "replace")
        for m in _STUDY_GLOSSARY_CAT_RE.finditer(t):
            size = _stripped_len(m.group(0))
            if size > GLOSSARY_DECLINE_HI:
                aid = re.search(r'\bid="([^"]+)"', m.group(0))
                fails.append(
                    f"{n}: {aid.group(1) if aid else '?'} study-glossary-cat strips to "
                    f"{size:,} chars (> decline ceiling {GLOSSARY_DECLINE_HI:,})"
                )
    return fails


# ── 4g-ter. empty verse-refs-section husks ───────────────────────────────
_EMPTY_VREFS_SECTION_RE = re.compile(r'<section class="verse-refs-section"[^>]*>\s*</section>')


def empty_verse_refs_checks(zf: zipfile.ZipFile, names: list[str]) -> list[str]:
    """Gate 4g-ter — no dead ``verse-refs-section`` shells after vnote harvest."""
    fails: list[str] = []
    for n in names:
        if not n.endswith((".html", ".xhtml")):
            continue
        t = zf.read(n).decode("utf-8", "replace")
        shells = _EMPTY_VREFS_SECTION_RE.findall(t)
        if shells:
            fails.append(f"{n}: {len(shells)} empty verse-refs-section shell(s)")
    return fails


# ── 4m. K-R6-2 leg 1 — prefix-free popup anchor namespace ───────────────
# Nickel measures a tapped popup from its target anchor FORWARD to the next
# anchor whose id does NOT string-extend the tapped id — any strict-prefix
# pair (family head without -s1, cross-verse digit extension like
# jub-7-1 < jub-7-13, an -s10 sibling extending -s1) inflates the measured
# slice and refuses the popup (round-6d: 98/98 heads + the family tails).
_POPUP_ANCHOR_ID_RE = re.compile(r'\bid="((?:vnotes|vbadge)-[^"]+)"')
_UNIT_SUFFIX_RE = re.compile(r"-s[1-9]$")
# K-R13 glossary category footnotes navigate (not popup-slice units) — exempt
# from the inline -sN namespace (ids are vnotes-{book}-{ch}-{v}-{cat}).
_GLOSSARY_CAT_ANCHOR_RE = re.compile(
    r'<aside[^>]*\bclass="[^"]*study-glossary-cat[^"]*"[^>]*\bid="((?:vnotes|vbadge)-[^"]+)"'
)
_STUDY_GLOSSARY_JUMP_RE = re.compile(
    r'<a[^>]*\bclass="[^"]*study-glossary-jump[^"]*"[^>]*\bid="((?:vnotes|vbadge)-[^"]+)"'
)


def anchor_prefix_checks(zf: zipfile.ZipFile, names: list[str]) -> tuple[list[str], list[str]]:
    """Gate 4m. Returns (fails, warns).

    FAIL: any vnotes/vbadge id that is a strict prefix of another in the same
    file, or that lacks the single-digit ``-s<1..9>`` tail (a bare id = a
    stale or mixed artifact; the tail is what makes digit-extension prefixes
    structurally impossible). WARN: an ADJACENT (document-order) prefix pair
    among the base-baked translation ``vnote-`` asides — un-renamed surface,
    the same device mechanism, surfaced honestly (1 known corpus-wide).

    ``study-glossary-cat`` navigate targets (K-R13 backmatter) are excluded —
    they use per-category ids without ``-sN`` by design."""
    fails: list[str] = []
    warns: list[str] = []
    for n in names:
        if not n.endswith((".html", ".xhtml")):
            continue
        t = zf.read(n).decode("utf-8", "replace")
        glossary_nav_ids = {m.group(1) for m in _GLOSSARY_CAT_ANCHOR_RE.finditer(t)}
        glossary_nav_ids.update(m.group(1) for m in _STUDY_GLOSSARY_JUMP_RE.finditer(t))
        ids = sorted(set(_POPUP_ANCHOR_ID_RE.findall(t)) - glossary_nav_ids)
        for i in ids:
            if not _UNIT_SUFFIX_RE.search(i):
                fails.append(f"{n}: popup anchor {i} lacks the -s<1..9> tail (bare-id K-R6-2 class, 4m)")
        # sorted order: if ANY strict-prefix pair exists, the minimal extension
        # sorts immediately after its prefix — consecutive check finds it
        for a, b in zip(ids, ids[1:], strict=False):
            if b.startswith(a):
                fails.append(f"{n}: anchor id {a} is a strict prefix of {b} (K-R6-2 slice-swallow class, 4m)")
        # document-order aside walk: an ADJACENT extending pair is the exact
        # configuration Nickel's forward-scan mismeasures
        aside_ids = [m.group(2) for m in _POPUP_ASIDE_RE.finditer(t)]
        for a, b in zip(aside_ids, aside_ids[1:], strict=False):
            if b.startswith(a) and len(b) > len(a) and a.startswith("vnote-"):
                warns.append(f"{n}: ADJACENT vnote prefix pair {a} < {b} (un-renamed translation surface)")
    return fails, warns


# ── 4n. K-R6-2 leg 2 — per-aside serialized byte budget (kepub only) ─────
# The round-6d bracket: 8,858 B OPENED / 9,273 B REFUSED, measured on the
# real kepub aside serialization. The gate fails the PROVEN-OPEN floor; the
# build's default split cap is now anchored at the same 8,858 floor — the
# estimator's dominance over real kepub bytes (85 B/seg > measured 81.3) is the
# margin, so a splitter-passed unit's real serialized size stays under the floor.
BYTE_FLOOR = 8_858


def popup_byte_checks(zf: zipfile.ZipFile, names: list[str]) -> tuple[list[str], list[str]]:
    """Gate 4n. Returns (fails, warns). Judges ONLY koboSpan-bearing (kepub)
    artifacts — pre-kepubify bytes are not the device measure. verse-notes
    units over the floor FAIL; base-baked vnote (translation) asides over it
    WARN (un-probed class, same convention as 4g)."""
    fails: list[str] = []
    warns: list[str] = []
    docs = [n for n in names if n.endswith((".html", ".xhtml"))]
    texts = {n: zf.read(n).decode("utf-8", "replace") for n in docs}
    if not any("koboSpan" in t for t in texts.values()):
        return [], []
    for n, t in texts.items():
        for m in _POPUP_ASIDE_RE.finditer(t):
            b = len(m.group(0).encode("utf-8"))
            if b <= BYTE_FLOOR:
                continue
            if m.group(1) == "verse-notes":
                fails.append(f"{n}: {m.group(2)} serializes to {b:,} B (> open floor {BYTE_FLOOR:,} — K-R6-2, 4n)")
            else:
                warns.append(f"{n}: vnote {m.group(2)} serializes to {b:,} B (> open floor; un-probed class)")
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
        for m in re.finditer(r'<aside\b[^>]*\bepub:type="footnote"[^>]*>', t):
            tag = m.group(0)
            if "study-glossary-cat" in tag:
                continue  # K-R13 navigate footnotes; continuation chunks lack direct href
            idm = re.search(r'\bid="(vnotes?-[^"]+)"', tag)
            if idm:
                ids[idm.group(1)] = n
        hrefs.update(re.findall(r'href="[^"#]*#([^"]+)"', t))
    orphans = sorted(i for i in ids if i not in hrefs)
    if not orphans:
        return []
    return [f"{len(orphans)} unreachable vnote aside(s) (4j orphan class); first 4: {orphans[:4]}"]


# ── 4k. demoted-appendix husks — no frame-only spine piece ──────────────
def husk_piece_checks(zf: zipfile.ZipFile, names: list[str]) -> list[str]:
    """No spine piece may consist of a demoted appendix-section frame with
    no content (the K-KIN root cause, 2026-06-11: the splitter force-isolated
    the 3 demoted Daniel-addition title frames — bp-45/46/47 Azariah/Susanna/
    Bel — into ~750 B CSS-hidden pieces; Kindle's KFX preprocessor refuses an
    effectively-empty piece as a TOC link target: E24010 "Hyperlink not
    resolved in toc" ×3 → E24001 "TOC could not be built" → Send-to-Kindle
    rejects the whole book). A piece holding an appendix-section frame must
    also carry verse/chapter content. Real book-title-page singletons are
    exempt — Kindle accepts them (38 in every prior artifact)."""
    fails: list[str] = []
    for n in names:
        if not re.search(r"index_split_\d+(?:_\d+)?\.html$", n):
            continue
        t = zf.read(n).decode("utf-8", "replace")
        if 'class="appendix-section"' not in t or 'class="book-title-page"' in t:
            continue
        if 'class="verse-p"' in t or 'class="ch-heading"' in t:
            continue
        bp = re.search(r'id="(bp-\d+)"', t)
        fails.append(
            f"{n}: frame-only appendix-section piece ({bp.group(1) if bp else '?'}) — "
            "the Kindle E24010/E24001 TOC-husk class (4k)"
        )
    return fails


# ── 4l. demoted TOC targets — no TOC entry points at an appendix frame ──
def demoted_toc_target_checks(zf: zipfile.ZipFile, names: list[str]) -> list[str]:
    """No nav.xhtml / toc.ncx / in-book-TOC href may target a demoted
    appendix-section frame id. The Previewer oracle proved KFX refuses the
    frame div as a TOC link target even MERGED mid-content (ship-fix round
    2: E24010 + W14001 ×3 on the content-bearing pieces — the frame's
    leading children are display:none and KFX prunes it), so TOC entries
    for demoted books must point at the book's first content anchor
    (retarget_demoted_toc_anchors)."""
    docs = [n for n in names if n.endswith((".html", ".xhtml", ".ncx"))]
    frame_ids: set[str] = set()
    for n in docs:
        t = zf.read(n).decode("utf-8", "replace")
        frame_ids.update(re.findall(r'<div class="appendix-section" id="(bp-\d+)"', t))
    if not frame_ids:
        return []
    fails: list[str] = []
    for n in docs:
        t = zf.read(n).decode("utf-8", "replace")
        if not (n.endswith(".ncx") or 'epub:type="toc"' in t or 'class="toc-book"' in t):
            continue
        for bp in sorted(frame_ids):
            hits = t.count(f'#{bp}"')
            if hits:
                fails.append(f"{n}: {hits} TOC ref(s) target demoted frame {bp} (KFX E24010 class, 4l)")
    return fails


# ── 4h. K-R5-3 — book-title singletons carry no verse badges/asides ─────
def title_piece_badge_checks(zf: zipfile.ZipFile, names: list[str]) -> list[str]:
    """A piece holding a book-title page must carry NO verse-notes badge or
    aside — in v0.1.0 all 38 title pieces showed the previous book's
    last-verse badge (the K-R5-3 clamp escape). Keyed on the REAL
    book-title-page class, not the bare bp id: a DEMOTED appendix-section
    frame keeps its bp-NN id but deliberately flows mid-content among
    badges/asides (the K-KIN husk fix; gate 4k owns that class).

    For non-split targets (tablet), files legitimately contain multiple
    books, so the check only fails on badges *inside* a book-title-page
    div itself (true bleed) or on singleton title-only pieces that carry
    foreign badges."""
    fails: list[str] = []
    _BP_BLOCK_RE = re.compile(
        r'(<div class="book-title-page"[^>]*>)(.*?)(?=</div>\s*(?:<div class="book-title-page"|<aside class="notes-section"|<section class="verse-refs-section"|</body>|\Z))',
        re.DOTALL | re.IGNORECASE,
    )
    for n in names:
        if not re.search(r"index_split_\d+(?:_\d+)?\.html$", n):
            continue
        t = zf.read(n).decode("utf-8", "replace")
        if 'class="book-title-page"' not in t:
            continue
        # True bleed: badge markup inside any real book-title-page frame
        for m in _BP_BLOCK_RE.finditer(t):
            block = m.group(2) or ""
            if 'class="verse-notes-badge"' in block or 'id="vnotes-' in block:
                bp = re.search(r'id="(bp-\d+)"', m.group(1) or t)
                fails.append(
                    f"{n}: book-title page ({bp.group(1) if bp else '?'}) contains badge/aside inside frame (K-R5-3)"
                )
        # Legacy singleton-piece check: only for pieces that look like pure title singletons
        bps = re.findall(r'<div class="book-title-page"[^>]*>', t)
        has_scripture = 'class="vn-link' in t
        if bps and not has_scripture:
            # This piece is mostly/only title(s); any badge anywhere is foreign
            for needle, what in (
                ('class="verse-notes-badge"', "verse badge"),
                ('id="vnotes-', "verse-notes aside"),
            ):
                if needle in t:
                    bp = re.search(r'id="(bp-\d+)"', t)
                    fails.append(
                        f"{n}: book-title singleton piece ({bp.group(1) if bp else '?'}) carries a {what} (K-R5-3)"
                    )
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
        all_bp_ids.update(re.findall(r'id="bp-\d+"', t))
        # The singleton invariant holds for REAL book-title pages only — a
        # DEMOTED addition keeps its bp-NN id on a class="appendix-section"
        # frame that deliberately flows mid-content (the K-KIN husk fix; a
        # frame-only piece is the Kindle-refused E24010/E24001 husk, gate 4k).
        bps = re.findall(r'<div class="book-title-page" id="bp-\d+"', t)
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
            first_bp = body.find('class="book-title-page"')
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
            # K-R9c: study badges intentionally cross-file navigate to glossary.
            if "study-glossary-jump" in tag:
                continue
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
    badge_re = re.compile(r'id="vbadge-([a-z0-9]+)-(\d+)-(\d+)(?:-(?:s[1-9]|[a-z][a-z0-9]*))?')
    spilled: list[str] = []
    for n in pieces:
        t = zf.read(n).decode("utf-8", "replace")
        # 4d/4e — splice-corruption tripwires (the kr3a RSC-016 class): every
        # vbadge id keeps its <a> head, and <aside> tags stay balanced.
        # Eink backmatter uses study-glossary-jump (not verse-notes-badge).
        heads = len(re.findall(r'<a\b[^>]*\bid="vbadge-', t))
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
            + [(m.start(), 0) for m in re.finditer(r'<a class="(?:verse-notes-badge|study-glossary-jump)"', t)]
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
    fails.extend(glossary_cat_checks(zf, names))
    fails.extend(empty_verse_refs_checks(zf, names))
    fails.extend(title_piece_badge_checks(zf, names))
    fails.extend(badge_mode_leak_checks(zf, names))
    fails.extend(orphan_vnote_checks(zf, names))
    fails.extend(husk_piece_checks(zf, names))
    fails.extend(demoted_toc_target_checks(zf, names))

    # ── 4m. prefix-free anchor namespace + 4n. per-aside byte budget ─────
    prefix_fails, prefix_warns = anchor_prefix_checks(zf, names)
    fails.extend(prefix_fails)
    for w in prefix_warns:
        print(f"WARN (4m): {w}")
    byte_fails, byte_warns = popup_byte_checks(zf, names)
    fails.extend(byte_fails)
    for w in byte_warns:
        print(f"WARN (4n): {w}")

    # ── 5. kindle_safe — only judges artifacts stamped target-reader=kindle ─
    fails.extend(kindle_safe_checks(zf, names, opf))

    print(f"pieces: {len(pieces)}  title-singletons: {title_pieces}")
    print(
        f"sizes: min {min(sizes):,}  max {max(sizes):,}  mean {int(statistics.mean(sizes)):,}"
        f"  median {int(statistics.median(sizes)):,}"
    )
    print(f"noterefs: {total_refs:,} all-resolve={unresolved == 0}")
    print(f"promoted-noterefs: {promoted}  dup-ids: {len(dup_ids)}  ch-spilled-badges: {len(spilled)}")

    # W7 (round-11): non-failing byte-size WARN. Kobo's kepub renderer breaks on
    # pieces past ~881 KB (EREADERS §Kobo); the `sizes` summary above counts
    # CODEPOINTS, but the renderer measures SERIALIZED BYTES — multi-byte Ge'ez
    # inflates ~2-3x, so a piece that looks safe by chars can ship oversized
    # (the round-9 882 KB regression). Flag pieces approaching the break by their
    # true uncompressed byte size so it's caught before a device run.
    KOBO_PIECE_BYTE_WARN = 500_000
    oversize = sorted(
        ((zf.getinfo(n).file_size, n) for n in pieces if zf.getinfo(n).file_size > KOBO_PIECE_BYTE_WARN),
        reverse=True,
    )
    for b, n in oversize:
        print(f"WARN (W7 piece-bytes): {n} is {b:,} bytes (> {KOBO_PIECE_BYTE_WARN:,}; Kobo break ~881 KB)")

    if fails:
        print("\nFAILURES:")
        for f in fails:
            print("  ✗", f)
        return 1
    print("ALL K-R2 GATES GREEN")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
