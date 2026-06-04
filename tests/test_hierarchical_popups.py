"""ρ.3 Phase B-1 — per-chapter + per-verse popup-language decode/encode (TDD).

Tests for:
  - decode_per_chapter_languages / encode_per_chapter_languages
  - decode_per_verse_languages   / encode_per_verse_languages
"""

import importlib

be = importlib.import_module("scripts.build_edition")


class TestPerChapterLangs:
    def test_decode_basic(self):
        assert be.decode_per_chapter_languages(["gen:1=wlc,lxx-greek", "exo:3="]) == {
            "gen:1": ["wlc", "lxx-greek"],
            "exo:3": [],
        }

    def test_decode_none_and_dict(self):
        assert be.decode_per_chapter_languages(None) == {}
        assert be.decode_per_chapter_languages({"gen:1": ["wlc"]}) == {"gen:1": ["wlc"]}

    def test_encode_sorts_canonical_then_numeric_and_filters_unknown(self):
        out = be.encode_per_chapter_languages({"gen:10": ["wlc"], "gen:2": ["wlc"], "exo:1": ["wlc", "not-a-lang"]})
        assert out == ["gen:2=wlc", "gen:10=wlc", "exo:1=wlc"]

    def test_roundtrip(self):
        d = {"gen:1": ["wlc"], "gen:50": ["lxx-greek"]}
        assert be.decode_per_chapter_languages(be.encode_per_chapter_languages(d)) == d


class TestPerVerseLangs:
    def test_decode_basic(self):
        assert be.decode_per_verse_languages(["gen:1:1=wlc,lxx-greek", "gen:1:2="]) == {
            "gen:1:1": ["wlc", "lxx-greek"],
            "gen:1:2": [],
        }

    def test_encode_sorts_canonical_then_numeric(self):
        out = be.encode_per_verse_languages({"gen:1:10": ["wlc"], "gen:1:2": ["wlc"], "gen:2:1": ["wlc"]})
        assert out == ["gen:1:2=wlc", "gen:1:10=wlc", "gen:2:1=wlc"]

    def test_roundtrip(self):
        d = {"gen:1:1": ["wlc", "lxx-greek"], "psa:119:1": ["wlc"]}
        assert be.decode_per_verse_languages(be.encode_per_verse_languages(d)) == d
