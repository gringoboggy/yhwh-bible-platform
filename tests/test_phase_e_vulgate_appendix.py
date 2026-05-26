"""Phase E — Clementine Latin appendix (man/1es/2es) ingest tests.

TDD coverage: wikitext parser · versification remap (drop-unmapped) · pipeline floor.
Data stores are parsed as literals only, never run as code (RULES §7.1).
"""

from scripts.extract_vulgate_appendix import parse_clementine_wikitext

_SAMPLE = """{{titulus2|OperaeTitulus=Vulgata Clementina|SubTitulus=Oratio}}
{{Liber|Ante=X|Post=Y}}

==Caput 1==
<sup>1</sup> Domine omnipotens, Deus patrum nostrorum, [[Abraham]], et Isaac.
<sup>2</sup> Qui fecisti '''caelum''' et terram.

==Caput 2==
<sup>1</sup> Peccavi Domine, peccavi.
"""


def test_parses_chapters_verses_and_strips_markup():
    out = parse_clementine_wikitext(_SAMPLE)
    assert out == [
        (1, 1, "Domine omnipotens, Deus patrum nostrorum, Abraham, et Isaac."),
        (1, 2, "Qui fecisti caelum et terram."),
        (2, 1, "Peccavi Domine, peccavi."),
    ]


def test_drops_templates_and_collapses_whitespace():
    out = parse_clementine_wikitext("==Caput 1==\n<sup>1</sup>  A  {{ref|x}} B \n")
    assert out == [(1, 1, "A B")]


def test_remap_drops_unmapped_and_keeps_canonical():
    from scripts.extract_vulgate_appendix import build_verses

    # man is identity + in-extent (1 ch / 15 v); verse 99 is out-of-extent -> dropped
    parsed = [(1, 1, "Domine"), (1, 99, "out of extent")]
    assert build_verses("man", parsed) == [(1, 1, "Domine")]


# --- Versification corrections (1es/2es) ---------------------------------
# la.wikisource's Clementine 1es/2es do NOT share the canonical KJV-Apocrypha
# verse boundaries (vulgate_to_kjv's segment table is tuned for the Douay source
# and misaligns this one — proven 1es 1:13). Most chapters are identity; a few
# carry a single verified split where the Vulgate divides one canonical verse in
# two (_JOIN_PREV); multi-shift name-list chapters are deferred, not guessed.
# These pin the corrections derived by reading each chapter against the KJV text.


def _canon_map(code):
    from scripts.extract_vulgate_appendix import extract

    return {(c, v): t for c, v, t in extract(code)}


def test_man_is_clean_identity():
    d = _canon_map("man")
    assert len(d) == 15
    assert d[(1, 1)].startswith("Domine omnipotens")
    assert d[(1, 15)].startswith("et laudabo te semper")


def test_1es_ch2_trailing_split_concatenated_into_canon_30():
    d = _canon_map("1es")
    assert (2, 31) not in d  # canon ch2 has only 30 verses
    assert d[(2, 30)].startswith("Tunc recitatis")  # source 2:30 head
    assert "ædificantes prohibere" in d[(2, 30)]  # source 2:31 folded into 2:30


def test_1es_ch9_split_concatenated_into_canon_48():
    d = _canon_map("1es")
    assert "docebant legem Domini" in d[(9, 48)]  # source 9:49 folded into canon 48
    assert d[(9, 49)].startswith("Et dixit Atharathes")  # source 9:50 -> canon 49


def test_2es_ch16_single_split_realigns_after_v18():
    d = _canon_map("2es")
    assert d[(16, 19)].startswith("Ecce fames et plaga")  # source 16:20 -> canon 19
    assert "constringuntur a peccatis" in d[(16, 77)]  # source 16:78 -> canon 77
    assert (16, 78) not in d  # canon 78 is a gap (Latin merged the field/fire metaphor)


def test_2es_ch10_trailing_split_no_text_loss():
    d = _canon_map("2es")
    assert (10, 60) not in d  # canon ch10 has only 59 verses
    assert "dormivi illam noctem" in d[(10, 59)]  # source 10:60 folded in, not dropped


def test_multishift_chapters_deferred_not_guessed():
    from scripts.extract_vulgate_appendix import extract

    chs_1es = {c for c, _, _ in extract("1es")}
    assert 5 not in chs_1es and 8 not in chs_1es  # deferred (omitted, flagged)
    assert {1, 2, 3, 4, 6, 7, 9} <= chs_1es  # the rest ship
    chs_2es = {c for c, _, _ in extract("2es")}
    assert 14 not in chs_2es  # deferred
    assert {5, 7, 9, 10, 16} <= chs_2es


def test_extraction_meets_floor():
    from scripts.extract_vulgate_appendix import extract

    assert len(extract("man")) == 15
    assert len(extract("1es")) >= 270  # 7 of 9 chapters (ch5/ch8 deferred)
    assert len(extract("2es")) >= 800  # 15 of 16 chapters (ch14 deferred)
