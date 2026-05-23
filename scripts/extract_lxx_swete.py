"""scripts/extract_lxx_swete.py — ingest the Greek Septuagint (Swete 1909-1930)
from the eliranwong/LXX-Swete-1930 digitization into the project's translation
store (Phase 2 of the fully-customizable-builder roadmap; the LXX-Greek spine).

PD basis + license: Swete's Greek text is public domain by age (Henry Barclay
Swete d. 1917; editions Vol I 1909/1925, Vol II 1907, Vol III 1912/1930). The
eliranwong repository is GPL-3.0, but that covers its *added* layers (SBL
transliteration, morphology tagging, pronunciation). This extractor reads ONLY the
public-domain Greek text — the ``00-Swete_versification.csv`` (verse -> first
word-id) and ``01-Swete_word_with_punctuations.csv`` (word-id -> Greek word) — and
never the transliteration/morphology. Mechanical digitization of a PD text creates
no new copyright, so the emitted text is public domain (parallels the WLC ingest,
which used morphhb's PD text but not its CC-BY morphology). The provenance chain
(Swete -> Amicarelli -> eliranwong -> archive.org) is recorded in ATTRIBUTIONS.md.

Pipeline (parallels scripts/extract_wlc_morphhb.py):

    _acquire/LXX-Swete-1930/{00-versification, 01-words}.csv  (TSV: id<TAB>value)
        -> reconstruct                 plain space-joined Greek per verse
        -> versification remap          Swete LXX coords -> canonical KJV
        -> content/translations/lxx-swete-greek/<code>.py   VERSES = [(ch, vs, text)]

Greek is stored PLAIN (space-joined words with attached punctuation), matching the
recovered base's ``vnote-greek`` format — NOT the em-per-word markup WLC uses.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))  # allow `python scripts/extract_lxx_swete.py`
TRANSLATIONS_DIR = REPO / "content" / "translations"
# The eliranwong digitization, cloned into the gitignored staging dir.
DEFAULT_SOURCE = REPO.parent / "_acquire" / "LXX-Swete-1930"


def parse_versification(path) -> list[tuple[int, str]]:
    """Parse ``00-Swete_versification.csv`` (``word_id<TAB>Book.Ch:Vs``) into a
    list of ``(start_word_id, ref)`` sorted by word id — each entry gives the
    first word of a verse."""
    out: list[tuple[int, str]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        wid, ref = line.split("\t", 1)
        out.append((int(wid), ref))
    out.sort(key=lambda r: r[0])
    return out


def parse_words(path) -> dict[int, str]:
    """Parse ``01-Swete_word_with_punctuations.csv`` (``word_id<TAB>word``) into a
    ``{word_id: greek_word}`` map. Punctuation is already attached to its word."""
    out: dict[int, str] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        wid, word = line.split("\t", 1)
        out[int(wid)] = word
    return out


def reconstruct(versification: list[tuple[int, str]], words: dict[int, str]) -> list[tuple[str, str]]:
    """Rebuild ``[(ref, verse_text), ...]``: each verse is the words from its start
    id up to (not including) the next verse's start id, joined by single spaces.
    Verses with no available words (e.g. past a fixture slice) are omitted."""
    if not words:
        return []
    last = max(words)
    out: list[tuple[str, str]] = []
    for i, (start, ref) in enumerate(versification):
        end = versification[i + 1][0] if i + 1 < len(versification) else last + 1
        toks = [words[w] for w in range(start, end) if w in words]
        if toks:
            out.append((ref, " ".join(toks)))
    return out


# --- Driver: reconstruct -> versification remap -> translation store ---------

TRANSLATION_ID = "lxx-swete-greek"


def parse_ref(ref: str) -> tuple[str, int, int]:
    """``'Gen.1:1'`` -> ``('Gen', 1, 1)``."""
    book, chvs = ref.split(".", 1)
    ch, vs = chvs.split(":", 1)
    return book, int(ch), int(vs)


# Swete's textual-critical sigla (the Unicode "Supplemental Punctuation" block,
# ⸀⸁⸂⸃⸄⸅⸆⸇…) and the digitization's embedded ``[n]`` verse markers are editorial
# apparatus, not readable text — strip them so popups show clean Greek.
_SIGLA_RE = re.compile(r"[⸀-⹿]")
_BRACKET_MARKER_RE = re.compile(r"\[\d+\]")


def _clean_greek(text: str) -> str:
    text = _SIGLA_RE.sub("", text)
    text = _BRACKET_MARKER_RE.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def build_verses(vers_path, words_path) -> tuple[dict[str, list[tuple[int, int, str]]], dict]:
    """Reconstruct the Swete text, remap every verse to canonical KJV coordinates
    via ``versification.lxx_swete_to_kjv``, and group by project book code.

    Returns ``({code: [(ch, vs, text), ...] sorted}, stats)``. Verses the map omits
    (out-of-scope books, dropped superscriptions, Additions, out-of-extent) are
    counted in ``stats['omitted']``. When the LXX splits ONE canonical verse into
    two adjacent Greek verses (e.g. Sirach 34:10 = Greek 31:10 + 31:11, or Baruch
    3:34 = Greek 3:34 + 3:35), both are mapped to the same canonical coord and
    their Greek is CONCATENATED in source order — so the popup shows the WHOLE
    verse, never a truncated half. The count is recorded in ``stats['merged']``.
    """
    from scripts.core.versification import lxx_swete_to_kjv

    vers = parse_versification(vers_path)
    words = parse_words(words_path)
    by_code: dict[str, dict[tuple[int, int], str]] = {}
    omitted = 0
    merged: list[tuple] = []
    for ref, text in reconstruct(vers, words):
        try:
            book, ch, vs = parse_ref(ref)
        except ValueError:
            omitted += 1  # non-integer (letter) sub-verse ref — not in scope
            continue
        mapped = lxx_swete_to_kjv(book, ch, vs)
        if mapped is None:
            omitted += 1
            continue
        code, kch, kvs = mapped
        cleaned = _clean_greek(text)
        slot = by_code.setdefault(code, {})
        if (kch, kvs) in slot:
            # LXX-split canonical verse: concatenate the second half (source order
            # is verse order, so the join reads correctly) instead of dropping it.
            merged.append((code, kch, kvs, ref))
            slot[(kch, kvs)] = (slot[(kch, kvs)] + " " + cleaned).strip()
            continue
        slot[(kch, kvs)] = cleaned
    out = {code: sorted((c, v, t) for (c, v), t in d.items()) for code, d in by_code.items()}
    stats = {
        "written": sum(len(v) for v in out.values()),
        "omitted": omitted,
        "merged": len(merged),
        "merged_detail": merged[:20],
        "books": len(out),
    }
    return out, stats


def write_translation(by_code: dict[str, list[tuple[int, int, str]]], dest_dir, verse_total: int) -> None:
    """Write ``<code>.py`` (TRANSLATION/BOOK/VERSES) for each book + ``_meta.yaml``."""
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    for code in sorted(by_code):
        lines = [
            f'"""Translation: {TRANSLATION_ID} · Book: {code}',
            "",
            "AUTO-GENERATED by scripts/extract_lxx_swete.py.",
            "Do not edit by hand — re-run extraction to regenerate.",
            '"""',
            "",
            f'TRANSLATION = "{TRANSLATION_ID}"',
            f'BOOK = "{code}"',
            "VERSES = [",
        ]
        lines += [f"    ({c}, {v}, {t!r})," for c, v, t in by_code[code]]
        lines.append("]")
        (dest / f"{code}.py").write_text("\n".join(lines) + "\n", encoding="utf-8")

    meta = f"""# Translation metadata — generated by scripts/extract_lxx_swete.py
# Greek Septuagint (Swete 1909-1930) via the eliranwong/LXX-Swete-1930 digitization.

id: {TRANSLATION_ID}
title: "Greek Septuagint (Swete)"
short_title: "LXX (Swete)"
license: "Public Domain"
source:
  publisher: "H. B. Swete, The Old Testament in Greek (Cambridge, 1909-1930), via eliranwong/LXX-Swete-1930"
  url: "https://github.com/eliranwong/LXX-Swete-1930"
  package: "00-Swete_versification.csv + 01-Swete_word_with_punctuations.csv (PD text only)"
  fetched: 2026-05-23
  source_date: 1930
stats:
  books: {len(by_code)}
  verses: {verse_total}
notes: |
  39 standard OT books + the COMPLETE content-verified deuterocanon subset (Wisdom,
  Susanna, Bel & the Dragon, Baruch, Letter of Jeremiah, Sirach, Tobit, Judith,
  1 Esdras, Prayer of Manasseh, Prayer of Azariah / Song of the Three) of Swete's
  Septuagint, remapped from LXX numbering to canonical KJV coordinates via
  scripts/core/versification.lxx_swete_to_kjv (Psalms renumbering, Jeremiah's OAN
  reorder, Theodotion Daniel's Additions, Proverbs 24/29 reorder, the 1 Kings
  20<->21 swap, the Baruch 3:34 + Letter-of-Jeremiah head splits, the Sirach
  30:25-36:16a transposition, the Tobit ch6/7 boundary, the Judith 15/16 song
  boundary, the 1 Esdras scattered intra-chapter combines, and the two cross-book
  canticles man (Swete Ode 8) + paz (Theodotion Dat 3:24-90, with its reordered
  Benedicite). sus/bel use the Theodotion recension (Sut/Bet) the KJV/Vulgate
  tradition follows. Out of scope: aes (editorial WEB↔KJV concordance), 1En (no KJV
  skeleton + base render gap), the Exodus 36-39 tabernacle account (LXX-reordered +
  abbreviated), and the unused recension dups (Tbs, Old-Greek Sus/Bel/Dan).
  Greek is stored PLAIN (space-joined, NOT em-per-word). PD basis: Swete d. 1917;
  only the public-domain text is used (the repo's GPL transliteration/morphology
  layers are not). Regenerable: re-run the extractor.
"""
    (dest / "_meta.yaml").write_text(meta, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    source = DEFAULT_SOURCE
    by_code, stats = build_verses(
        source / "00-Swete_versification.csv",
        source / "01-Swete_word_with_punctuations.csv",
    )
    write_translation(by_code, TRANSLATIONS_DIR / TRANSLATION_ID, stats["written"])
    print(
        f"wrote {stats['written']} verses across {stats['books']} books "
        f"(omitted {stats['omitted']}; merged {stats['merged']} LXX-split verses) -> {TRANSLATION_ID}/"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
