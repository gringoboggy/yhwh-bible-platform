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


class TestResolvePopupLangs:
    def _ed(self, **kw):
        base = {"id": "t"}
        base.update(kw)
        return base

    def test_no_override_two_arg_unchanged(self):
        # Back-compat: the old 2-arg call must behave exactly as before.
        ed = self._ed(popup_languages_default=["wlc", "lxx-greek"])
        assert be._resolve_popup_languages(ed, "gen") == {"wlc", "lxx-greek"}

    def test_no_per_scope_with_chapter_verse_equals_book(self):
        ed = self._ed(popup_languages_per_book=["gen=wlc"])
        # passing chapter/verse but no per-chapter/verse fields → same as per-book
        assert be._resolve_popup_languages(ed, "gen", 1, 1) == be._resolve_popup_languages(ed, "gen")

    def test_per_chapter_overrides_book(self):
        ed = self._ed(
            popup_languages_per_book=["gen=wlc,lxx-greek"],
            popup_languages_per_chapter=["gen:1=wlc"],
        )
        assert be._resolve_popup_languages(ed, "gen", 1, 5) == {"wlc"}
        assert be._resolve_popup_languages(ed, "gen", 2, 5) == {"wlc", "lxx-greek"}

    def test_per_verse_overrides_chapter(self):
        ed = self._ed(
            popup_languages_per_chapter=["gen:1=wlc"],
            popup_languages_per_verse=["gen:1:1=wlc,lxx-greek"],
        )
        assert be._resolve_popup_languages(ed, "gen", 1, 1) == {"wlc", "lxx-greek"}
        assert be._resolve_popup_languages(ed, "gen", 1, 2) == {"wlc"}

    def test_explicit_empty_verse_means_no_popups(self):
        ed = self._ed(
            popup_languages_per_book=["gen=wlc"],
            popup_languages_per_verse=["gen:1:1="],
        )
        assert be._resolve_popup_languages(ed, "gen", 1, 1) == set()
        assert be._resolve_popup_languages(ed, "gen", 1, 2) == {"wlc"}
