import importlib
import json

gx = importlib.import_module("scripts.core.geez_kjv_xref")


def _load_v2(book, ch):
    tr = "kings" if book in {"1ki", "2ki"} else "samuel"
    return json.load(open(f"content/manuscript/{tr}/collation/{book}{ch}_collation_v2.json", encoding="utf-8"))


def test_single_geez_numerals():
    assert gx.numeral_token_value("፬") == 4
    assert gx.numeral_token_value("፲") == 10
    assert gx.numeral_token_value("፳") == 20
    assert gx.numeral_token_value("፴") == 30
    assert gx.numeral_token_value("፷") == 60
    assert gx.numeral_token_value("፻") == 100
    assert gx.numeral_token_value("፬፻") == 400
    assert gx.numeral_token_value("፲፪") == 12
    assert gx.numeral_token_value("ሰሎሞን") is None


def test_verse_numerals_runs():
    toks = ["ወእምዝ", "፬", "፻", "ወ", "፹", "ዓመት", "እስራኤል"]
    assert 480 in gx.verse_numerals(toks)
    toks2 = ["፷", "እመት", "ኑኁ", "ወ", "፳", "ራኅቡ", "ወ", "፴", "እመት"]
    assert {60, 20, 30} <= gx.verse_numerals(toks2)


def test_kjv_number_values():
    assert 480 in gx.kjv_number_values("in the four hundred and eightieth year")
    assert gx.kjv_number_values("threescore cubits was the length") == {60}
    assert gx.kjv_number_values("the breadth thereof twenty cubits") == {20}
    assert gx.kjv_number_values("and the height thereof thirty cubits") == {30}
    assert gx.kjv_number_values("the house of the LORD") == set()


# ── B3: proper_noun_hits ──────────────────────────────────────────────────────


def test_proper_noun_hits_1ki6_v1():
    geez_tokens = ["ወእምዝ", "ሰሎሞን", "እስራኤል", "ግብጽ", "እግዚእብሔር", "ቤተ"]
    kjv = (
        "and it came to pass after the children of israel were come out of "
        "the land of egypt that solomon began to build the house of the lord"
    )
    hits = gx.proper_noun_hits(geez_tokens, kjv)
    assert {"solomon", "israel", "egypt", "lord"} <= hits


def test_proper_noun_prefix_and_forms():
    assert gx.proper_noun_hits(["ኪሩብ"], "the cherubims of olive tree") == {"cherub"}
    assert gx.proper_noun_hits(["ሊባኖስ"], "cedar trees out of lebanon") == {"lebanon"}
    # leading conjunction stripped: ወሰሎሞን -> ሰሎሞን
    assert gx.proper_noun_hits(["ወሰሎሞን"], "and solomon reigned") == {"solomon"}


def test_proper_noun_no_false_hit():
    assert gx.proper_noun_hits(["ቤተ", "ወርሐ"], "solomon built the house") == set()


# ── B4: build_kjv_xref + kjv_coverage ─────────────────────────────────────────


def test_build_kjv_xref_1ki6_anchors():
    from scripts.core.manuscript_collation import load_kjv_skeleton

    col = _load_v2("1ki", 6)
    kjv_rows = load_kjv_skeleton("1ki", 6)
    xref = gx.build_kjv_xref(col, kjv_rows, "1ki")
    # every base verse covered + honestly tagged
    assert set(xref) == {pv["geez_v"] for pv in col["primary_verses"]}
    for e in xref.values():
        assert e["confidence"] in {"anchored", "interpolated"}
        assert e["kjv"] and all(len(t) == 3 for t in e["kjv"])
    # the two known hard anchors (480-year / temple dimensions)
    assert xref[1]["confidence"] == "anchored" and xref[1]["kjv"] == [["1ki", 6, 1]]
    assert xref[2]["confidence"] == "anchored" and [t[2] for t in xref[2]["kjv"]] == [2]
    # monotonic non-decreasing KJV verse across base order
    seq = [xref[pv["geez_v"]]["kjv"][0][2] for pv in col["primary_verses"]]
    assert seq == sorted(seq)


def test_kjv_coverage_shape():
    from scripts.core.manuscript_collation import load_kjv_skeleton

    col = _load_v2("1ki", 6)
    xref = gx.build_kjv_xref(col, load_kjv_skeleton("1ki", 6), "1ki")
    cov = gx.kjv_coverage(xref)
    assert cov["base_verses"] == len(col["primary_verses"])
    assert cov["anchored"] + cov["interpolated"] == cov["base_verses"]
    assert cov["anchored"] >= 2  # at least v1 + v2 anchor
