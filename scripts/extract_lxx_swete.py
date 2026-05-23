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
