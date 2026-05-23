"""Phase 2 — LXX Greek ingestion (Swete 1909-1930, via the eliranwong digitization).

PD basis: Swete's text is public domain by age (d. 1917; editions 1907-1930). Only
the public-domain Greek TEXT (the ``00`` verse refs + ``01`` words) is extracted;
eliranwong's GPL-licensed additions (SBL transliteration ``03``, morphology,
pronunciation) are NOT used. See ATTRIBUTIONS.md for the provenance chain.

Reconstruction characterization: the Swete source stores the text as a flat word
list (``01-Swete_word_with_punctuations.csv``: ``word_id -> word``) plus a
versification index (``00-Swete_versification.csv``: ``word_id -> Book.Ch:Vs``
giving each verse's first word). A verse is the words from its start id up to (not
including) the next verse's start id, space-joined. Greek is stored PLAIN (not
em-per-word — matching the recovered base + the Brenton seed). The expected fixture
was auto-reconstructed from the real source slice, not hand-transcribed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
FX = REPO / "tests" / "fixtures"
FX_VERS = FX / "swete_gen_versification.tsv"
FX_WORDS = FX / "swete_gen_words.tsv"
FX_EXPECTED = FX / "swete_gen_expected.json"

_EXPECTED = json.loads(FX_EXPECTED.read_text(encoding="utf-8"))


@pytest.mark.parametrize("ref", sorted(_EXPECTED))
def test_reconstruct_verse_text_from_word_list(ref):
    """Each verse = its words (start-id .. next-start-id) joined by single spaces,
    reproducing the Swete source's plain Greek with attached punctuation."""
    from scripts.extract_lxx_swete import parse_versification, parse_words, reconstruct

    vers = parse_versification(FX_VERS)
    words = parse_words(FX_WORDS)
    got = dict(reconstruct(vers, words))
    assert got[ref] == _EXPECTED[ref]


def test_reconstruct_is_plain_greek_not_em_wrapped():
    """LXX Greek is plain text (space-joined), NOT the em-per-word markup WLC uses
    — matching the recovered base's vnote-greek format."""
    from scripts.extract_lxx_swete import parse_versification, parse_words, reconstruct

    got = dict(reconstruct(parse_versification(FX_VERS), parse_words(FX_WORDS)))
    assert "<em>" not in got["Gen.1:1"]
    assert got["Gen.1:1"].startswith("ΕΝ ΑΡΧΗ")  # Swete caps the opening words
