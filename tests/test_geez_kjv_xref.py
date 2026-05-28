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
