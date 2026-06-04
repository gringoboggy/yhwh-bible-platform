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


import scripts.core.config as config

KINDS = [
    {"code": "xref-citation", "category": "xref", "phase": "legacy"},
    {"code": "comm-patristic", "category": "comm", "phase": "legacy"},
    {"code": "comm-rabbinic", "category": "comm", "phase": "legacy"},
    {"code": "future-kind", "category": "comm", "phase": "phase3"},
    {"code": "comm-ai", "category": "comm", "phase": "legacy"},
]


def _ed(**kw):
    base = {"id": "t", "enabled_categories": [], "enabled_kinds": [], "disabled_kinds": []}
    base.update(kw)
    return base


class TestResolverPrecedence:
    def test_no_override_equals_base(self):
        ed = _ed(enabled_categories=["xref"])
        assert config.enabled_kind_codes_for(ed, KINDS, "gen", 1) == config.enabled_kind_codes(ed, KINDS)

    def test_book_off_removes_family(self):
        ed = _ed(enabled_categories=["xref"], note_families_off_per_book=["exo=xref"])
        assert "xref-citation" in config.enabled_kind_codes_for(ed, KINDS, "gen", 1)
        assert "xref-citation" not in config.enabled_kind_codes_for(ed, KINDS, "exo", 3)

    def test_book_on_reenables_edition_disabled_family(self):
        ed = _ed(enabled_categories=[], note_families_on_per_book=["gen=xref"])  # xref OFF edition-wide
        assert "xref-citation" not in config.enabled_kind_codes_for(ed, KINDS, "exo", 1)
        assert "xref-citation" in config.enabled_kind_codes_for(ed, KINDS, "gen", 1)

    def test_chapter_beats_book(self):
        ed = _ed(
            enabled_categories=["comm"],
            note_families_off_per_book=["psa=comm"],
            note_families_on_per_chapter=["psa:23=comm"],
        )
        assert "comm-patristic" not in config.enabled_kind_codes_for(ed, KINDS, "psa", 1)
        assert "comm-patristic" in config.enabled_kind_codes_for(ed, KINDS, "psa", 23)

    def test_kind_token_beats_category_token(self):
        ed = _ed(
            enabled_categories=["comm"],
            note_families_off_per_book=["psa=comm"],
            note_families_on_per_book=["psa=comm-patristic"],
        )
        got = config.enabled_kind_codes_for(ed, KINDS, "psa", 1)
        assert "comm-patristic" in got  # kind ON wins over category OFF
        assert "comm-rabbinic" not in got  # category OFF still applies to the rest

    def test_off_beats_on_at_equal_specificity(self):
        ed = _ed(
            enabled_categories=[],
            note_families_on_per_book=["gen=comm-patristic"],
            note_families_off_per_book=["gen=comm-patristic"],
        )
        assert "comm-patristic" not in config.enabled_kind_codes_for(ed, KINDS, "gen", 1)

    def test_phase_gate_not_bypassed_by_family_on(self):
        ed = _ed(max_phase="mvp", note_families_on_per_book=["gen=comm"])  # future-kind is phase3
        assert "future-kind" not in config.enabled_kind_codes_for(ed, KINDS, "gen", 1)
        assert "comm-patristic" in config.enabled_kind_codes_for(ed, KINDS, "gen", 1)

    def test_ai_gate_not_bypassed_by_family_on(self):
        ed = _ed(enable_ai_notes=False, note_families_on_per_book=["gen=comm-ai"])
        assert "comm-ai" not in config.enabled_kind_codes_for(ed, KINDS, "gen", 1)


class TestResolverInvariant:
    def test_real_editions_unchanged_with_no_override(self):
        all_kinds = config.load_kinds()
        for ed in config.load_editions():
            base = config.enabled_kind_codes(ed, all_kinds)
            assert config.enabled_kind_codes_for(ed, all_kinds, "gen", 1) == base
            assert config.enabled_kind_codes_for(ed, all_kinds, "rev") == base


class TestCorpusIterator:
    def test_yields_8_tuple_with_chapter_kind_category(self):
        rows = list(be._iter_note_ref_symbols())
        assert rows, "expected the on-disk corpus to yield notes"
        ref_id, note_id, book, chapter, verse, suffix, kind, category = rows[0]
        assert ref_id.startswith("ref-")
        assert note_id.count(":") == 3  # book:ch:vs[suffix]:kind
        assert isinstance(chapter, int) and isinstance(verse, int)
        assert note_id == f"{book}:{chapter}:{verse}{suffix}:{kind}"

    def test_note_id_reparses_to_same_ref_id(self):
        from scripts.web_helpers import html_ref_id_from_note_id

        for ref_id, note_id, *_ in list(be._iter_note_ref_symbols())[:200]:
            assert html_ref_id_from_note_id(note_id) == ref_id
