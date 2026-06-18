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
    {"code": "comm-patristic", "category": "comm", "phase": "legacy"},
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
        assert "comm-patristic" not in got  # category OFF still applies to the rest

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
            has_coord_override = any(
                ed.get(field)
                for field in (
                    "note_families_on_per_book",
                    "note_families_off_per_book",
                    "note_families_on_per_chapter",
                    "note_families_off_per_chapter",
                )
            )
            if has_coord_override:
                continue
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


class TestSymbolCompute:
    def test_overridden_kinds_from_tokens_and_force_on(self):
        ed = _ed(
            note_families_off_per_book=["psa=comm"],  # category → all comm kinds
            note_families_on_per_chapter=["gen:1=xref-citation"],  # one kind
            enabled_note_ids=["exo:3:2:comm-patristic"],  # one kind
        )
        ak = config.load_kinds()
        ov = be._symbol_overridden_kinds(ed, ak)
        comm_kinds = {k["code"] for k in ak if k.get("category") == "comm"}
        assert comm_kinds <= ov  # category token expanded
        assert "xref-citation" in ov  # kind token
        assert "comm-patristic" in ov  # force-on kind

    def test_compute_short_circuits_empty(self):
        ed = _ed(enabled_categories=["xref"])  # no per-book/chapter token, no enabled_note_ids
        assert be.compute_symbol_disabled_html_ref_ids(ed, config.load_kinds(), set()) == set()

    def test_compute_disables_off_coordinate_only(self):
        # xref ON edition-wide, OFF in exo only → exo xref ref-ids disabled, gen xref ref-ids not
        ed = _ed(enabled_categories=["xref"], note_families_off_per_book=["exo=xref"])
        ak = config.load_kinds()
        ov = be._symbol_overridden_kinds(ed, ak)
        disabled = be.compute_symbol_disabled_html_ref_ids(ed, ak, ov)
        exo_prefix = config.books_by_code()["exo"].get("id_prefix") or config.books_by_code()["exo"].get("bxx")
        gen_prefix = config.books_by_code()["gen"].get("id_prefix") or config.books_by_code()["gen"].get("bxx")
        # at least one exo ref-id disabled; no gen ref-id disabled (xref still ON in gen)
        assert any(r.startswith(f"ref-{exo_prefix}") for r in disabled)
        assert not any(r.startswith(f"ref-{gen_prefix}") for r in disabled)
