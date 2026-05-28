import importlib

gx = importlib.import_module("scripts.core.geez_kjv_xref")


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
