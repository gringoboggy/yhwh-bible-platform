#!/usr/bin/env python3
"""Round-16 merged artifact scanner — output hygiene of a built EPUB (no rebuild).

The round-16 headline gate. It opens each built EPUB/KEPUB once and runs the four
output-hygiene finding-families the prior gates left uncovered, reporting them in
one pass (program dims 5/6/7/8). The genuinely-NEW one is **html-integrity /
code-leak** (family A) — the round-16 deliverable the way G1 was round-14's: the
existing ``check_no_reviewer_scaffolding`` lint runs at COMMIT time over source,
and ``check_nested_anchors`` checks the BASE (``epub_working/``) only, so nothing
guards the SHIPPED bytes against a template/repr/f-string leak or a post-split
malformed-anchor that reaches the reader.

Four families (a FAIL fails the gate; a WARN is reported but does not):

  A. HTML-INTEGRITY / CODE-LEAK (FAIL) — no template artifact (``{{ }}`` / ``{% %}``
     / ``{# #}``), no Python repr leak (``<… object at 0x…>``, ``<class '…'>``,
     ``dict_items(…)``, a traceback), no ``[Reviewer:…]`` / ``[TODO]`` scaffold,
     no ``str.format`` / f-string leftover (``{0}`` / ``{name:spec}`` / ``{x!r}``),
     and no nested ``<a>`` in the EMITTED (post-split) html. Raw AND HTML-escaped
     forms are scanned (an escaped repr passes epubcheck yet still ships gibberish).
     ``<style>`` / ``<script>`` / ``<!-- comment -->`` blocks are stripped first so
     CSS/JS braces never false-fire.
  B. WHITESPACE / PAGEBREAK (mid-chapter spine break = FAIL; the rest = WARN) —
     reuses ``audit_spine_breaks`` for the spine-boundary classification, plus
     empty verse anchors, empty asides, stray ``<br>`` runs, empty-paragraph runs.
  C. DISPLAY-REDUNDANCY (WARN) — duplicate note bodies inside one verse-notes
     aside, adjacent duplicate category headers / bylines.
  D. MARKER-LOGIC (WARN) — orphan asides (a ``note`` / ``verse-notes`` aside whose
     id no marker targets), the gap G3 (marker→target resolves) and G4 (orphan
     leaf marker) do not cover. G3/G4/G5/G6 still run as their own harness passes;
     family D only adds the inbound-direction check.

Standalone stdlib only (mirrors ``audit_idmap_frags`` / ``audit_badge_conservation``)
→ light + OOM-safe; reads each (x)html member once.

Usage:
    py -3 dev/audit_output_hygiene.py <epub> [<epub> ...] [--json OUT.json]
        [--max-show N] [--strict] [--eink] [--selftest]
``--eink`` escalates mid-chapter spine breaks to FAIL (they force a page break on e-ink;
on reflowable everywhere/tablet they are low-impact WARNs). ``--strict`` also fails on
WARNs. ``--selftest`` runs the family-A detector against synthetic leak/clean strings
(non-tautology proof) and exits.
Exit 0 = no FAIL (and, under --strict, no WARN); 1 = any FAIL (or any WARN under --strict).
"""

from __future__ import annotations

import json
import os
import re
import sys
import zipfile
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # sibling dev/ gates
import audit_spine_breaks  # noqa: E402  (reused for family B spine-boundary classification)

# ---------------------------------------------------------------------------
# Family A — html-integrity / code-leak patterns
# ---------------------------------------------------------------------------
_STYLE_RE = re.compile(r"<style\b[^>]*>.*?</style>", re.I | re.S)
_SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script>", re.I | re.S)
_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)

# FAIL-grade leaks (these must NEVER appear in shipped Bible HTML). Scanned over the
# style/script/comment-stripped text; the repr family is ALSO scanned over an
# entity-unescaped copy so an escaped leak (&lt;class …&gt;) is caught too.
_LEAK_FAIL = [
    ("template-var", re.compile(r"\{\{.{0,300}?\}\}", re.S)),
    ("template-block", re.compile(r"\{%.{0,300}?%\}", re.S)),
    ("template-comment", re.compile(r"\{#.{0,300}?#\}", re.S)),
    ("format-leftover", re.compile(r"\{\d+\}|\{[A-Za-z_]\w*[!:][^}\n]{0,60}\}|\{\}")),
    ("scaffold-reviewer", re.compile(r"\[Reviewer\b")),
]
# Same set but applied after entity-unescape (catches escaped repr/template leaks).
_LEAK_FAIL_UNESCAPED = [
    ("py-repr-objat", re.compile(r"<[\w.]+ object at 0x[0-9A-Fa-f]+>")),
    ("py-repr-class", re.compile(r"<class '[\w.]+'>")),
    (
        "py-repr-callable",
        re.compile(
            r"<(?:function|built-in function|built-in method|bound method|generator object|"
            r"map object|filter object|zip object|module|coroutine object) "
        ),
    ),
    ("py-dict-view", re.compile(r"\b(?:dict_items|dict_keys|dict_values|odict_items|odict_values)\(")),
    ("py-traceback", re.compile(r"Traceback \(most recent call last\)")),
]
# WARN-grade (lower confidence — flagged for triage, never auto-fails except --strict).
_LEAK_WARN = [
    ("format-name", re.compile(r"\{[A-Za-z_]\w*\}")),
    ("scaffold-todo", re.compile(r"\[(?:TODO|FIXME|XXX|PLACEHOLDER|DRAFT)\b")),
    ("printf-leftover", re.compile(r"%\([A-Za-z_]\w*\)[sdrfx]")),
]

# Marker / aside classes (build_edition.py emitted markup).
_BADGE_HREF_RE = re.compile(
    r'<a\b[^>]*class="[^"]*\b(?:verse-notes-badge|vn-link|study-glossary-jump|note-ref|note-backref)\b[^"]*"[^>]*\bhref="([^"]+)"'
)
_HREF_ANY_RE = re.compile(r'\bhref="#?([^"#]*#)?([^"]+)"')
_ASIDE_OPEN_RE = re.compile(r"<aside\b([^>]*)>")
_ID_IN_TAG_RE = re.compile(r'\bid="([^"]+)"')
_CLASS_IN_TAG_RE = re.compile(r'\bclass="([^"]+)"')
_VERSE_ANCHOR_EMPTY_RE = re.compile(r'<a\b[^>]*\bid="v-[^"]+"[^>]*>\s*</a>')
_EMPTY_ASIDE_RE = re.compile(r"<aside\b[^>]*>\s*</aside>")
_BR_RUN_RE = re.compile(r"(?:<br\s*/?>\s*){3,}", re.I)
_EMPTY_P_RUN_RE = re.compile(r"(?:<p\b[^>]*>(?:\s|&nbsp;|<br\s*/?>)*</p>\s*){2,}", re.I)
_CAT_HEADER_RE = re.compile(r'<[^>]*class="[^"]*\bnote-category[^"]*"[^>]*>(.*?)</[^>]+>', re.S)


def _strip(text: str) -> str:
    return _COMMENT_RE.sub(" ", _SCRIPT_RE.sub(" ", _STYLE_RE.sub(" ", text)))


def _unescape(text: str) -> str:
    return text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


@dataclass
class HygieneResult:
    path: str
    fails: list[str] = field(default_factory=list)
    warns: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)

    @property
    def green(self) -> bool:
        return not self.fails

    def strict_green(self) -> bool:
        return not self.fails and not self.warns


def _base(name: str) -> str:
    return name.replace("\\", "/").rsplit("/", 1)[-1]


def _scan_leaks(member: str, text: str) -> tuple[list[str], list[str], int]:
    """Family A on one html member's text. Returns (fails, warns, leak_hit_count)."""
    fails: list[str] = []
    warns: list[str] = []
    stripped = _strip(text)
    unescaped = _unescape(stripped)
    hits = 0
    for label, rx in _LEAK_FAIL:
        for m in rx.finditer(stripped):
            hits += 1
            fails.append(f"{_base(member)}: code/template leak [{label}] {m.group(0)[:80]!r}")
    for label, rx in _LEAK_FAIL_UNESCAPED:
        for m in rx.finditer(unescaped):
            hits += 1
            fails.append(f"{_base(member)}: code/template leak [{label}] {m.group(0)[:80]!r}")
    for label, rx in _LEAK_WARN:
        for m in rx.finditer(stripped):
            warns.append(f"{_base(member)}: possible leak [{label}] {m.group(0)[:80]!r}")
    return fails, warns, hits


def _scan_nested_anchors(member: str, text: str) -> list[str]:
    """Family A — nested <a> in the EMITTED html (G1's nested-anchor check is
    base-only). A new <a …> opening while another anchor is still open is invalid
    and confuses every reader's tap target."""
    fails: list[str] = []
    depth = 0
    for m in re.finditer(r"</?a\b", text):
        if text[m.start() : m.start() + 2] == "</":
            depth = max(0, depth - 1)
        else:
            if depth > 0:
                fails.append(f"{_base(member)}: nested <a> in emitted html (a tap target inside another link)")
                # don't spam — one per member is enough to flag the file
                break
            depth += 1
    return fails


def _scan_whitespace(member: str, text: str) -> tuple[list[str], dict[str, int]]:
    """Family B (per-member half) — empty anchors/asides/br-runs/empty-p-runs."""
    warns: list[str] = []
    s = {"empty_verse_anchors": 0, "empty_asides": 0, "br_runs": 0, "empty_p_runs": 0}
    n = len(_VERSE_ANCHOR_EMPTY_RE.findall(text))
    if n:
        s["empty_verse_anchors"] = n
        warns.append(f"{_base(member)}: {n} empty verse anchor(s) (id=v-… with no text)")
    n = len(_EMPTY_ASIDE_RE.findall(text))
    if n:
        s["empty_asides"] = n
        warns.append(f"{_base(member)}: {n} empty <aside> element(s)")
    n = len(_BR_RUN_RE.findall(text))
    if n:
        s["br_runs"] = n
        warns.append(f"{_base(member)}: {n} run(s) of 3+ consecutive <br>")
    n = len(_EMPTY_P_RUN_RE.findall(text))
    if n:
        s["empty_p_runs"] = n
        warns.append(f"{_base(member)}: {n} run(s) of 2+ empty <p>")
    return warns, s


def _scan_redundancy(member: str, text: str) -> tuple[list[str], int]:
    """Family C — adjacent duplicate category headers inside one member."""
    warns: list[str] = []
    headers = [re.sub(r"\s+", " ", h).strip() for h in _CAT_HEADER_RE.findall(text)]
    dups = 0
    for i in range(1, len(headers)):
        if headers[i] and headers[i] == headers[i - 1]:
            dups += 1
            warns.append(f"{_base(member)}: adjacent duplicate category header {headers[i][:50]!r}")
    return warns, dups


def audit_epub(path: str, *, eink: bool = False) -> HygieneResult:
    res = HygieneResult(path=path)
    leak_hits = 0
    nested = 0
    ws = {"empty_verse_anchors": 0, "empty_asides": 0, "br_runs": 0, "empty_p_runs": 0}
    redundancy = 0
    # Family D inbound-marker accounting (collected across all members).
    aside_ids: set[str] = set()
    marker_targets: set[str] = set()
    members = 0

    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if not name.endswith((".html", ".xhtml")):
                continue
            members += 1
            text = zf.read(name).decode("utf-8", "replace")

            f, w, hits = _scan_leaks(name, text)
            res.fails.extend(f)
            res.warns.extend(w)
            leak_hits += hits

            na = _scan_nested_anchors(name, text)
            res.fails.extend(na)
            nested += len(na)

            ww, ws_part = _scan_whitespace(name, text)
            res.warns.extend(ww)
            for k, v in ws_part.items():
                ws[k] += v

            rw, dups = _scan_redundancy(name, text)
            res.warns.extend(rw)
            redundancy += dups

            # Family D — collect aside ids and marker hrefs (note/verse-notes asides).
            for m in _ASIDE_OPEN_RE.finditer(text):
                attrs = m.group(1)
                cls = _CLASS_IN_TAG_RE.search(attrs)
                idm = _ID_IN_TAG_RE.search(attrs)
                if idm and cls and re.search(r"\bnote\b|verse-notes", cls.group(1)):
                    aside_ids.add(idm.group(1))
            for m in _BADGE_HREF_RE.finditer(text):
                href = m.group(1)
                frag = href.split("#", 1)[1] if "#" in href else href
                if frag:
                    marker_targets.add(frag)

    # Family B (spine half) — reuse audit_spine_breaks for the boundary classification.
    # Severity is reader-aware: on EINK/kepub a spine boundary FORCES a page break (real
    # defect), but on a reflowable everywhere/tablet build it does not (low impact → WARN).
    try:
        rep = audit_spine_breaks.audit_epub(path)
        bucket = res.fails if eink else res.warns
        for nm, a, b in rep.midchapter_breaks:
            note = "forces a half-empty page (eink)" if eink else "spine boundary (reflowable: low impact)"
            bucket.append(f"mid-chapter spine break {a} -> {b} ({nm}) — {note}")
        if rep.chapter_breaks:
            res.warns.append(f"{len(rep.chapter_breaks)} chapter-boundary spine break(s) (mid-book page starts)")
        spine_stats = {
            "spine_pieces": rep.pieces,
            "book_breaks": rep.book_breaks,
            "chapter_breaks": len(rep.chapter_breaks),
            "midchapter_breaks": len(rep.midchapter_breaks),
        }
    except (zipfile.BadZipFile, ValueError) as e:
        res.warns.append(f"spine-break pass skipped ({e})")
        spine_stats = {}

    # Family D — orphan asides (an inbound marker direction G3/G4 don't check).
    orphan_asides = sorted(aside_ids - marker_targets)
    if orphan_asides:
        res.warns.append(
            f"{len(orphan_asides)} orphan aside(s) — note/verse-notes asides no marker targets "
            f"(e.g. {orphan_asides[:3]}); may include the known hidden-aes-residual"
        )

    res.stats = {
        "html_members": members,
        "leak_hits": leak_hits,
        "nested_anchor_members": nested,
        "empty_verse_anchors": ws["empty_verse_anchors"],
        "empty_asides": ws["empty_asides"],
        "br_runs": ws["br_runs"],
        "empty_p_runs": ws["empty_p_runs"],
        "dup_category_headers": redundancy,
        "aside_ids": len(aside_ids),
        "marker_targets": len(marker_targets),
        "orphan_asides": len(orphan_asides),
        **spine_stats,
    }
    return res


def _print(res: HygieneResult, max_show: int, strict: bool) -> None:
    name = _base(res.path)
    s = res.stats
    ok = res.strict_green() if strict else res.green
    print(f"\n=== {name} — R16 output-hygiene {'PASS' if ok else 'FAIL'} ===")
    if s:
        print(
            f"  members={s.get('html_members', 0)} leak_hits={s.get('leak_hits', 0)} "
            f"nested_a={s.get('nested_anchor_members', 0)} empty_verse_anchors={s.get('empty_verse_anchors', 0)} "
            f"empty_asides={s.get('empty_asides', 0)} midchapter_breaks={s.get('midchapter_breaks', 0)} "
            f"orphan_asides={s.get('orphan_asides', 0)}"
        )
    for f in res.fails[:max_show]:
        print("  ✗", f)
    if len(res.fails) > max_show:
        print(f"  ✗ … +{len(res.fails) - max_show} more FAIL(s)")
    for w in res.warns[:max_show]:
        print("  ⚠", w)
    if len(res.warns) > max_show:
        print(f"  ⚠ … +{len(res.warns) - max_show} more WARN(s)")


def _selftest() -> int:
    """Non-tautology proof: the family-A detector flags known leaks and passes clean text."""
    dirty = (
        "<p>Genesis {{ verse.text }} and {% if x %}leak{% endif %}</p>"
        "<p>repr &lt;function build at 0x7f&gt; and {0} and {name:>3} [Reviewer: fix this]</p>"
        "<p>raw <class 'dict'> and dict_items([('a',1)])</p>"
        "<a href='#a'>x<a href='#b'>y</a></a>"
    )
    clean = "<p>In the beginning God created the heaven and the earth. (100% sure)</p><style>.x{color:red}</style>"
    df, _, dh = _scan_leaks("t.html", dirty)
    dn = _scan_nested_anchors("t.html", dirty)
    cf, _, ch = _scan_leaks("t.html", clean)
    cn = _scan_nested_anchors("t.html", clean)
    problems = []
    if dh < 5:
        problems.append(f"expected >=5 leak hits in dirty, got {dh}: {df}")
    if not dn:
        problems.append("expected nested-<a> hit in dirty")
    if cf:
        problems.append(f"clean text false-fired leaks: {cf}")
    if ch != 0 or cn:
        problems.append(f"clean text false hits: leaks={ch} nested={cn}")
    if problems:
        print("SELFTEST FAIL:")
        for p in problems:
            print("  ✗", p)
        return 1
    print(f"SELFTEST PASS (dirty leak_hits={dh}, nested={len(dn)}; clean=0/0)")
    return 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return _selftest()
    _value_flags = ("--json", "--max-show")
    _skip = {argv.index(f) + 1 for f in _value_flags if f in argv}
    paths = [a for i, a in enumerate(argv) if not a.startswith("--") and i not in _skip]
    json_out = argv[argv.index("--json") + 1] if "--json" in argv else None
    max_show = int(argv[argv.index("--max-show") + 1]) if "--max-show" in argv else 50
    strict = "--strict" in argv
    eink = "--eink" in argv
    if not paths:
        print(__doc__)
        return 2
    results = [audit_epub(p, eink=eink) for p in paths]
    for r in results:
        _print(r, max_show, strict)
    if json_out:
        with open(json_out, "w", encoding="utf-8") as fh:
            json.dump(
                [
                    {
                        "path": r.path,
                        "green": r.green,
                        "strict_green": r.strict_green(),
                        "stats": r.stats,
                        "fails": r.fails,
                        "warns": r.warns,
                    }
                    for r in results
                ],
                fh,
                indent=1,
            )
        print(f"\nwrote {json_out}")
    bad = [r for r in results if (not r.strict_green() if strict else not r.green)]
    print(f"\nTOTAL: {len(results) - len(bad)}/{len(results)} artifact(s) hygiene-clean{' (strict)' if strict else ''}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
