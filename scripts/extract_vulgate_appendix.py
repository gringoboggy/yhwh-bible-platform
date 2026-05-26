"""Phase E — extract the Clementine Vulgate appendix (man/1es/2es) from
la.wikisource raw wikitext into the vulgate-clementine store.

The eBible/Tweedale Vulgate source (the body of the 74 baked books) omits this
post-NT appendix; the three deuterocanonical appendix books are fetched as raw
wikitext from la.wikisource "Vulgata Clementina" (Public Domain) and remapped to
canonical KJV coordinates via the existing scripts.core.versification.vulgate_to_kjv.
See PLAN_2026-05-21.md:210 and docs/superpowers/specs/2026-05-26-phase-e-clementine-latin-design.md.
"""

from __future__ import annotations

import re
from pathlib import Path

from scripts.core import config
from scripts.core.canonical_verse_counts import canonical_book_shape
from scripts.core.versification import vulgate_to_kjv

REPO = Path(config.__file__).resolve().parents[2]
_SRC = REPO / "content" / "translations" / "sources" / "vulgate-appendix"
_STORE = REPO / "content" / "translations" / "vulgate-clementine"
_PAGES = {"man": "oratio_manasse", "1es": "esdras_iii", "2es": "esdras_iv"}

_TEMPLATE = re.compile(r"\{\{[^{}]*\}\}")
_CHAPTER = re.compile(r"==\s*Caput\s+(\d+)\s*==")
_VERSE = re.compile(r"<sup>\s*(\d+)\s*</sup>")


def _strip(s: str) -> str:
    """Strip wiki markup and normalize whitespace; keep the Latin verbatim."""
    prev = None
    while prev != s:  # collapse {{templates}} until stable (handles one-level nesting)
        prev = s
        s = _TEMPLATE.sub("", s)
    s = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", s)  # [[target|display]] -> display
    s = re.sub(r"\[\[([^\]]*)\]\]", r"\1", s)  # [[target]] -> target
    s = s.replace("'''", "").replace("''", "")  # bold / italic markup
    s = re.sub(r"<[^>]+>", "", s)  # stray tags (e.g. <br>)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_clementine_wikitext(text: str) -> list[tuple[int, int, str]]:
    """Return [(chapter, verse, latin_text), …] from Clementine wikitext.

    Chapters are marked ``==Caput N==``; verses ``<sup>N</sup>`` running to the
    next verse marker or chapter end. Empty verses (markup only) are dropped.
    """
    out: list[tuple[int, int, str]] = []
    parts = _CHAPTER.split(text)  # [pre, ch1, body1, ch2, body2, …]
    for i in range(1, len(parts), 2):
        ch = int(parts[i])
        vparts = _VERSE.split(parts[i + 1])  # [pre, n1, t1, n2, t2, …]
        for j in range(1, len(vparts), 2):
            vtext = _strip(vparts[j + 1])
            if vtext:
                out.append((ch, int(vparts[j]), vtext))
    return out


def build_verses(code: str, parsed: list[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
    """Identity remap via ``vulgate_to_kjv`` (man: source numbering == canonical,
    verified verse-by-verse against KJV). Drops out-of-extent coords; never
    fabricates. 1es/2es use :func:`build_verses_aligned` instead (their
    la.wikisource numbering diverges from canonical — see module docstring)."""
    out: list[tuple[int, int, str]] = []
    for ch, vs, text in sorted(parsed):
        coord = vulgate_to_kjv(code, ch, vs)
        if coord is None:
            continue
        _, kch, kvs = coord
        out.append((kch, kvs, text))
    return sorted(out)


# Verified per-chapter versification corrections for the la.wikisource Clementine
# 1es/2es, whose verse numbering diverges from canonical KJV-Apocrypha. Default is
# IDENTITY (source verse N -> canonical N). `_JOIN_PREV[code][ch]` = source verses
# the Vulgate split off that concatenate into the PREVIOUS canonical verse (which
# uniformly shifts the rest of the chapter). Each was derived by reading the
# divergent chapter against the canonical KJV text (see the design/journal doc):
#   1es 2:31  -> tail of canon 2:30 ("cœperuntque ædificantes prohibere")
#   1es 9:49  -> tail of canon 9:48 ("qui docebant legem Domini")
#   2es 10:60 -> tail of canon 10:59 ("Et dormivi illam noctem et aliam")
#   2es 16:19 -> tail of canon 16:18; LA 20..78 then map to canon 19..77 (78 = gap)
_JOIN_PREV: dict[str, dict[int, set[int]]] = {
    "1es": {2: {31}, 9: {49}},
    "2es": {10: {60}, 16: {19}},
}

# Chapters whose verse-perfect alignment cannot be certified without guessing. Their
# Latin is OMITTED (never shipped misaligned) and surfaced for a future dedicated
# versification pass — the no-guessing / no-fabrication carve-out.
#
# RE-VERIFIED 2026-05-26 against the real Latin↔KJV text (deferral CONFIRMED — two
# distinct, genuine un-alignable structures, neither expressible by `_JOIN_PREV`
# without re-segmenting scripture by hand):
#   * 2es 14 — SUB-VERSE splits: Latin v2 ("vox … de rubo … Esdra Esdra / Ecce ego
#     Domine / Et dixit ad me") spans the tail of KJV 1, all of KJV 2, and the head of
#     KJV 3; v42|43 is likewise mid-Latin-verse. Aligning would require cutting a single
#     Latin verse mid-text → a synthetic verse division present in no source.
#   * 1es 5, 1es 8 — NAME-LIST grouping divergence: the census/genealogy family lists
#     pack a different number of families per verse than the KJV, and the transliterated
#     names (Phœmo, Choraba, Aderectis, Azoroc, …) don't match KJV equivalents, so the
#     internal split points can't be determined without guessing which group = which verse.
_DEFER_CHAPTERS: dict[str, set[int]] = {
    "1es": {5, 8},  # census list (ch5) + commission/genealogy (ch8): name-list grouping divergence
    "2es": {14},  # burning-bush narrative: sub-verse split at the opening (vv1-3) + at vv42-43
}


def build_verses_aligned(code: str, parsed: list[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
    """Map 1es/2es Latin to canonical coords via the verified `_JOIN_PREV` table
    (identity by default). Walks each chapter's source verses in order, advancing
    the canonical counter per verse except for `_JOIN_PREV` verses, which the
    Vulgate split and which concatenate into the previous canonical verse. Chapters
    in `_DEFER_CHAPTERS` are skipped (omitted). Canonical verses left unassigned are
    gaps (the Latin has no distinct verse there)."""
    by_ch: dict[int, dict[int, str]] = {}
    for ch, vs, text in parsed:
        by_ch.setdefault(ch, {})[vs] = text
    shape = canonical_book_shape(code)
    join = _JOIN_PREV.get(code, {})
    defer = _DEFER_CHAPTERS.get(code, set())
    out: list[tuple[int, int, str]] = []
    for ch in sorted(by_ch):
        n = shape.get(ch, 0)
        if ch in defer or not n:
            continue
        join_prev = join.get(ch, set())
        slot: dict[int, str] = {}
        canon = 0
        for s in sorted(by_ch[ch]):
            if s in join_prev and canon >= 1:
                slot[canon] = (slot[canon] + " " + by_ch[ch][s]).strip()
            else:
                canon += 1
                if canon > n:  # extent guard — Vulgate has more verses than canonical
                    break
                slot[canon] = by_ch[ch][s]
        out.extend((ch, v, t) for v, t in slot.items())
    return sorted(out)


def write_store(code: str, verses: list[tuple[int, int, str]]) -> Path:
    """Write content/translations/vulgate-clementine/<code>.py (canonical coords).

    Matches the sibling stores' header so the appendix books are not editor-edited
    outliers. ruff format normalizes quotes/wrapping at the save gate (RULES §4).
    """
    lines = [
        f'"""Translation: vulgate-clementine · Book: {code}',
        "",
        "AUTO-GENERATED by scripts/extract_vulgate_appendix.py (Clementine appendix, la.wikisource).",
        "Do not edit by hand — re-run extraction to regenerate.",
        '"""',
        "",
        'TRANSLATION = "vulgate-clementine"',
        f'BOOK = "{code}"',
        "VERSES = [",
    ]
    lines += [f"    ({ch}, {vs}, {text!r})," for ch, vs, text in verses]
    lines.append("]")
    path = _STORE / f"{code}.py"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def extract(code: str) -> list[tuple[int, int, str]]:
    """Parse the committed .wiki source for ``code`` and map to canonical coords.
    man is clean identity; 1es/2es are aligned to the canonical KJV text."""
    raw = parse_clementine_wikitext((_SRC / f"{_PAGES[code]}.wiki").read_text(encoding="utf-8"))
    return build_verses(code, raw) if code == "man" else build_verses_aligned(code, raw)


def _report(code: str) -> list[tuple[int, int, str]]:
    """Print a per-chapter coverage report (mapped vs canonical + the gap list)
    and return the canonical-coord verses. Gaps = canonical slots with no aligned
    Latin (surfaced for review, never fabricated)."""
    from collections import Counter

    mapped = extract(code)
    shape = canonical_book_shape(code)
    defer = _DEFER_CHAPTERS.get(code, set())
    pmap = Counter(c for c, _, _ in mapped)
    have = {(c, v) for c, v, _ in mapped}
    gaps = sorted((c, v) for c in shape if c not in defer for v in range(1, shape[c] + 1) if (c, v) not in have)
    print(f"=== {code}  (canonical {len(shape)} ch / {sum(shape.values())} v) ===")
    for ch in sorted(shape):
        if ch in defer:
            print(f"   ch{ch:>2}: DEFERRED (omitted, flagged — multi-shift)")
            continue
        g = [v for c, v in gaps if c == ch]
        print(f"   ch{ch:>2}: mapped={pmap.get(ch, 0):>3} canonical={shape[ch]:>3}{'  gaps@' + str(g) if g else ''}")
    deferred_v = sum(shape[c] for c in defer)
    print(
        f"   TOTAL mapped={len(mapped)} canonical={sum(shape.values())} | "
        f"gaps={len(gaps)} | deferred={sorted(defer)} ({deferred_v} v)"
    )
    return mapped


def main() -> None:
    """Run extraction for man/1es/2es: print alignment reports + write stores."""
    for code in _PAGES:
        verses = _report(code)
        path = write_store(code, verses)
        print(f"   -> wrote {path.relative_to(REPO)} ({len(verses)} verses)\n")


if __name__ == "__main__":
    main()
