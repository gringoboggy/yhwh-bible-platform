import importlib

be = importlib.import_module("scripts.build_edition")


class TestPerBookTokens:
    def test_decode_book_tokens_basic(self):
        raw = ["gen=xref,comm-patristic", "exo="]
        assert be.decode_per_book_tokens(raw) == {"gen": ["xref", "comm-patristic"], "exo": []}

    def test_decode_book_tokens_none_and_dict(self):
        assert be.decode_per_book_tokens(None) == {}
        assert be.decode_per_book_tokens({"gen": ["xref"]}) == {"gen": ["xref"]}

    def test_encode_book_tokens_sorts_canonical_and_filters_unknown(self):
        # exo precedes gen alphabetically but FOLLOWS it canonically; unknown token dropped
        out = be.encode_per_book_tokens({"exo": ["xref"], "gen": ["xref", "not-a-real-token"]})
        assert out == ["gen=xref", "exo=xref"]

    def test_book_tokens_roundtrip(self):
        d = {"gen": ["xref"], "psa": ["comm-patristic"]}
        assert be.decode_per_book_tokens(be.encode_per_book_tokens(d)) == d


class TestPerChapterTokens:
    def test_decode_chapter_tokens_basic(self):
        raw = ["gen:1=xref", "exo:3=comm"]
        assert be.decode_per_chapter_tokens(raw) == {"gen:1": ["xref"], "exo:3": ["comm"]}

    def test_encode_chapter_tokens_sorts_canonical_then_numeric(self):
        out = be.encode_per_chapter_tokens({"gen:10": ["xref"], "gen:2": ["xref"], "exo:1": ["xref"]})
        # gen before exo (canonical book order); within gen, chapter 2 before 10 (numeric, not lexical)
        assert out == ["gen:2=xref", "gen:10=xref", "exo:1=xref"]

    def test_chapter_tokens_roundtrip(self):
        d = {"gen:1": ["xref"], "gen:50": ["comm-patristic"]}
        assert be.decode_per_chapter_tokens(be.encode_per_chapter_tokens(d)) == d
