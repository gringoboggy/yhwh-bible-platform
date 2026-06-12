"""K-KIN (B)+(C) — per-reader popup-language cap + kindle popup compaction (TDD).

Board-ratified design (2026-06-11, user-refined ×2):
  - `max_popup_languages` cap per reader target (kindle = 2, others uncapped;
    explicit per-edition value wins anywhere).
  - The builder picks WHICH language groups fill the cap (any of
    hebrew/greek/latin/arabic) via `popup_languages_capped`; ready-made
    default = Hebrew + Greek.
  - The capped pick is BIBLE-WIDE: per-book/chapter/verse tiers are bypassed
    under a cap. Uncapped readers keep the fine-grained machinery untouched.
  - (B) zero-loss compaction is kindle-gated at the emitter: full source
    labels -> compact codes (Heb/Grc/Lat/Ara/Eng), the per-verse header ->
    "<Book> N:M" from the canonical english book name.

Oracle grounding: the rung-LANGCAP staged artifact (48.7MB raw) is the exact
zip-level simulation of this design; these tests pin the in-build equivalent.
"""

import importlib

be = importlib.import_module("scripts.build_edition")


def _ed(**kw):
    base = {"id": "t"}
    base.update(kw)
    return base


WITNESS_DEFAULT = ["wlc", "lxx-greek", "greek-nt", "vulgate", "arabic"]


class TestResolvePopupLanguageCap:
    def test_uncapped_by_default(self):
        assert be.resolve_popup_language_cap(_ed()) is None

    def test_kindle_target_defaults_to_two(self):
        assert be.resolve_popup_language_cap(_ed(target_reader="kindle")) == 2

    def test_other_targets_uncapped(self):
        for tr in ("everywhere", "eink", "tablet", "computer"):
            assert be.resolve_popup_language_cap(_ed(target_reader=tr)) is None

    def test_explicit_wins_on_any_target(self):
        assert be.resolve_popup_language_cap(_ed(max_popup_languages=3)) == 3
        assert be.resolve_popup_language_cap(_ed(target_reader="kindle", max_popup_languages=1)) == 1
        assert be.resolve_popup_language_cap(_ed(target_reader="kindle", max_popup_languages=4)) == 4

    def test_invalid_cap_raises(self):
        import pytest

        for bad in (0, -1, 5, "two"):
            with pytest.raises(ValueError):
                be.resolve_popup_language_cap(_ed(max_popup_languages=bad))


class TestResolvePopupLanguagePick:
    def test_uncapped_returns_empty(self):
        assert be.resolve_popup_language_pick(_ed()) == ()

    def test_kindle_default_is_hebrew_greek(self):
        assert be.resolve_popup_language_pick(_ed(target_reader="kindle")) == ("hebrew", "greek")

    def test_cap_one_default_is_hebrew(self):
        assert be.resolve_popup_language_pick(_ed(target_reader="kindle", max_popup_languages=1)) == ("hebrew",)

    def test_explicit_pick_wins(self):
        ed = _ed(target_reader="kindle", popup_languages_capped=["latin", "arabic"])
        assert be.resolve_popup_language_pick(ed) == ("latin", "arabic")

    def test_pick_deduped_preserving_order(self):
        ed = _ed(target_reader="kindle", popup_languages_capped=["greek", "greek"])
        assert be.resolve_popup_language_pick(ed) == ("greek",)

    def test_pick_longer_than_cap_raises(self):
        import pytest

        ed = _ed(target_reader="kindle", popup_languages_capped=["hebrew", "greek", "latin"])
        with pytest.raises(ValueError):
            be.resolve_popup_language_pick(ed)

    def test_unknown_group_raises(self):
        import pytest

        ed = _ed(target_reader="kindle", popup_languages_capped=["klingon"])
        with pytest.raises(ValueError):
            be.resolve_popup_language_pick(ed)

    def test_group_version_map(self):
        assert be.POPUP_LANGUAGE_GROUPS == {
            "hebrew": ("wlc",),
            "greek": ("lxx-greek", "greek-nt"),
            "latin": ("vulgate",),
            "arabic": ("arabic",),
        }


class TestCappedResolution:
    """_resolve_popup_languages under a cap: bible-wide early-return."""

    def test_kindle_caps_to_pick_groups(self):
        ed = _ed(target_reader="kindle", popup_languages_default=list(WITNESS_DEFAULT))
        assert be._resolve_popup_languages(ed, "gen") == {"wlc", "lxx-greek", "greek-nt"}

    def test_per_book_tier_bypassed_under_cap(self):
        ed = _ed(
            target_reader="kindle",
            popup_languages_default=list(WITNESS_DEFAULT),
            popup_languages_per_book=["jer=arabic"],
        )
        assert be._resolve_popup_languages(ed, "jer") == {"wlc", "lxx-greek", "greek-nt"}

    def test_per_chapter_and_verse_tiers_bypassed_under_cap(self):
        ed = _ed(
            target_reader="kindle",
            popup_languages_default=list(WITNESS_DEFAULT),
            popup_languages_per_chapter=["jer:25=arabic"],
            popup_languages_per_verse=["jer:25:1=vulgate"],
        )
        assert be._resolve_popup_languages(ed, "jer", chapter=25, verse=1) == {
            "wlc",
            "lxx-greek",
            "greek-nt",
        }

    def test_pick_latin_arabic(self):
        ed = _ed(
            target_reader="kindle",
            popup_languages_default=list(WITNESS_DEFAULT),
            popup_languages_capped=["latin", "arabic"],
        )
        assert be._resolve_popup_languages(ed, "gen") == {"vulgate", "arabic"}

    def test_kjv_rides_along_when_in_baseline(self):
        # English is the edition's base language, not one of the 4 pick
        # groups; when the bible-wide baseline includes it, it survives
        # the cap untouched.
        ed = _ed(target_reader="kindle", popup_languages_default=["english", "wlc", "vulgate"])
        assert be._resolve_popup_languages(ed, "gen") == {"kjv", "wlc", "lxx-greek", "greek-nt"}

    def test_no_default_uses_witness_default_no_kjv(self):
        ed = _ed(target_reader="kindle")
        assert be._resolve_popup_languages(ed, "gen") == {"wlc", "lxx-greek", "greek-nt"}

    def test_uncapped_resolution_unchanged(self):
        # Inertness: without a cap the fine-grained tiers behave exactly
        # as before.
        ed = _ed(
            popup_languages_default=list(WITNESS_DEFAULT),
            popup_languages_per_book=["jer=arabic"],
        )
        assert be._resolve_popup_languages(ed, "jer") == {"arabic"}
        assert be._resolve_popup_languages(ed, "gen") == set(WITNESS_DEFAULT)


# A synthetic aside mirroring the real epub_working base shape (header tight
# against the opening tag + vnote-text; witnesses on indented lines).
def _aside(book="jer", ch=25, vs=1):
    return (
        f'<aside class="vnote" id="vnote-{book}-{ch}-{vs}" epub:type="footnote">'
        f"<p><strong>The Book of Jeremiah {ch}:{vs}.</strong></p>"
        f'<p class="vnote-text">KJV text here</p>\n'
        f'  <p class="vnote-source-label">Hebrew (Masoretic / WLC)</p>\n'
        f'  <p class="vnote-hebrew" dir="rtl" lang="he"><em>א</em></p>\n'
        f'  <p class="vnote-source-label">Greek (Septuagint / Swete)</p>\n'
        f'  <p class="vnote-greek" lang="grc">Ὁ λόγος</p>\n'
        f'  <p class="vnote-source-label">Douay-Rheims</p>\n'
        f'  <p class="vnote-douay" lang="en">Douay text</p>\n'
        f'  <p class="vnote-source-label">Latin (Clementine Vulgate)</p>\n'
        f'  <p class="vnote-vulgate" lang="la">Verbum</p>\n'
        f'  <p class="vnote-source-label">Arabic (Van Dyck)</p>\n'
        f'  <p class="vnote-arabic" dir="rtl" lang="ar">الكلام</p>\n'
        f'<p><a href="#v-{book}-{ch}-{vs}" class="vnote-back" title="Back">↩</a></p></aside>'
    )


class TestKindleCompaction:
    """(B) compaction, kindle-gated inside _apply_popup_languages_and_translation."""

    KINDLE_ED = {
        "id": "k",
        "target_reader": "kindle",
        "popup_languages_default": list(WITNESS_DEFAULT),
        "verse_popups": True,
    }

    def test_full_kindle_transform_exact(self):
        out, stats = be._apply_popup_languages_and_translation(_aside(), self.KINDLE_ED, "", "")
        expected = (
            '<aside class="vnote" id="vnote-jer-25-1" epub:type="footnote">'
            "<p><strong>Jeremiah 25:1</strong></p>\n"
            '<p class="vnote-source-label">Heb</p>'
            '<p class="vnote-hebrew" dir="rtl" lang="he"><em>א</em></p>\n'
            '<p class="vnote-source-label">Grc</p>'
            '<p class="vnote-greek" lang="grc">Ὁ λόγος</p>\n'
            '<p><a href="#v-jer-25-1" class="vnote-back" title="Back">↩</a></p></aside>'
        )
        assert out == expected
        assert stats["headers_compacted"] == 1
        assert stats["labels_compacted"] == 2

    def test_dropped_languages_gone(self):
        out, _ = be._apply_popup_languages_and_translation(_aside(), self.KINDLE_ED, "", "")
        for gone in ("vnote-vulgate", "vnote-arabic", "vnote-douay", "vnote-text", "Van Dyck", "Clementine"):
            assert gone not in out

    def test_header_uses_canonical_english_book_name(self):
        # gen -> "Genesis" (the comma-prefix book the rung handled by
        # string surgery; in-build derives from the book code).
        gen_aside = _aside(book="gen", ch=1, vs=1).replace(
            "The Book of Jeremiah 1:1.", "The First Book of Moses, Genesis 1:1."
        )
        out, stats = be._apply_popup_languages_and_translation(gen_aside, self.KINDLE_ED, "", "")
        assert "<p><strong>Genesis 1:1</strong></p>" in out
        assert stats["headers_compacted"] == 1

    def test_unknown_book_code_keeps_header(self):
        weird = _aside(book="zz9", ch=1, vs=2).replace("The Book of Jeremiah 1:2.", "Mystery Book 1:2.")
        out, stats = be._apply_popup_languages_and_translation(weird, self.KINDLE_ED, "", "")
        assert "<p><strong>Mystery Book 1:2.</strong></p>" in out
        assert stats["headers_compacted"] == 0
        assert stats["headers_kept"] == 1

    def test_kjv_fallback_kept_under_cap(self):
        # A verse whose only witnesses are capped away keeps the English
        # text para (4.3 fallback) so the popup is never emptied.
        aside = (
            '<aside class="vnote" id="vnote-jer-25-2" epub:type="footnote">'
            "<p><strong>The Book of Jeremiah 25:2.</strong></p>"
            '<p class="vnote-text">KJV only here</p>\n'
            '  <p class="vnote-source-label">Arabic (Van Dyck)</p>\n'
            '  <p class="vnote-arabic" dir="rtl" lang="ar">عن</p>\n'
            '<p><a href="#v-jer-25-2" class="vnote-back" title="Back">↩</a></p></aside>'
        )
        out, stats = be._apply_popup_languages_and_translation(aside, self.KINDLE_ED, "", "")
        assert "KJV only here" in out
        assert "vnote-arabic" not in out
        assert stats["kjv_fallbacks"] == 1

    def test_compact_label_map_covers_all_groups(self):
        assert be.COMPACT_SOURCE_LABELS == {
            "vnote-hebrew": "Heb",
            "vnote-greek": "Grc",
            "vnote-greek-nt": "Grc",
            "vnote-vulgate": "Lat",
            "vnote-arabic": "Ara",
            "vnote-text": "Eng",
        }

    def test_non_kindle_output_inert_exact(self):
        # Byte-level inertness off-kindle: full labels, untouched header,
        # vulgate+arabic kept; only the pre-existing strip semantics apply
        # (vnote-text dropped because witnesses are present, douay not in
        # the default set).
        ed = {"id": "e", "popup_languages_default": list(WITNESS_DEFAULT), "verse_popups": True}
        out, stats = be._apply_popup_languages_and_translation(_aside(), ed, "", "")
        expected = (
            '<aside class="vnote" id="vnote-jer-25-1" epub:type="footnote">'
            "<p><strong>The Book of Jeremiah 25:1.</strong></p>\n"
            '  <p class="vnote-source-label">Hebrew (Masoretic / WLC)</p>\n'
            '  <p class="vnote-hebrew" dir="rtl" lang="he"><em>א</em></p>\n'
            '  <p class="vnote-source-label">Greek (Septuagint / Swete)</p>\n'
            '  <p class="vnote-greek" lang="grc">Ὁ λόγος</p>\n'
            '  <p class="vnote-source-label">Latin (Clementine Vulgate)</p>\n'
            '  <p class="vnote-vulgate" lang="la">Verbum</p>\n'
            '  <p class="vnote-source-label">Arabic (Van Dyck)</p>\n'
            '  <p class="vnote-arabic" dir="rtl" lang="ar">الكلام</p>\n'
            '<p><a href="#v-jer-25-1" class="vnote-back" title="Back">↩</a></p></aside>'
        )
        assert out == expected
        assert stats.get("headers_compacted", 0) == 0
        assert stats.get("labels_compacted", 0) == 0


class TestApiValidator:
    """api_save_edition_meta + api_preview_edition_changes wiring."""

    def _yaml_guard(self):
        import pathlib

        from scripts.core import config

        edyaml = pathlib.Path(config.__file__).resolve().parents[2] / "content" / "editions.yaml"
        return edyaml, edyaml.read_bytes(), config

    def test_accepts_and_persists_cap(self):
        from scripts.api.editions import api_save_edition_meta

        edyaml, backup, config = self._yaml_guard()
        try:
            res = api_save_edition_meta("catholic-study", {"max_popup_languages": 3})
            assert "error" not in res, res
            config.load_editions.cache_clear()
            assert int(config.editions_by_id()["catholic-study"].get("max_popup_languages")) == 3
        finally:
            edyaml.write_bytes(backup)
            config.load_editions.cache_clear()

    def test_rejects_out_of_range_cap(self):
        from scripts.api.editions import api_save_edition_meta

        edyaml, backup, config = self._yaml_guard()
        try:
            for bad in (0, 5, "two"):
                res = api_save_edition_meta("catholic-study", {"max_popup_languages": bad})
                assert "error" in res and "max_popup_languages" in res["error"], (bad, res)
        finally:
            edyaml.write_bytes(backup)
            config.load_editions.cache_clear()

    def test_clears_cap_with_null(self):
        from scripts.api.editions import api_save_edition_meta

        edyaml, backup, config = self._yaml_guard()
        try:
            res = api_save_edition_meta("catholic-study", {"max_popup_languages": None})
            assert "error" not in res, res
        finally:
            edyaml.write_bytes(backup)
            config.load_editions.cache_clear()

    def test_accepts_and_persists_pick(self):
        from scripts.api.editions import api_save_edition_meta

        edyaml, backup, config = self._yaml_guard()
        try:
            res = api_save_edition_meta(
                "catholic-study",
                {"max_popup_languages": 2, "popup_languages_capped": ["latin", "arabic"]},
            )
            assert "error" not in res, res
            config.load_editions.cache_clear()
            assert config.editions_by_id()["catholic-study"].get("popup_languages_capped") == ["latin", "arabic"]
        finally:
            edyaml.write_bytes(backup)
            config.load_editions.cache_clear()

    def test_accepts_comma_joined_pick_string(self):
        # The /customize hidden-input control submits a comma-joined string.
        from scripts.api.editions import api_save_edition_meta

        edyaml, backup, config = self._yaml_guard()
        try:
            res = api_save_edition_meta(
                "catholic-study",
                {"max_popup_languages": 2, "popup_languages_capped": "hebrew,arabic"},
            )
            assert "error" not in res, res
            config.load_editions.cache_clear()
            assert config.editions_by_id()["catholic-study"].get("popup_languages_capped") == ["hebrew", "arabic"]
        finally:
            edyaml.write_bytes(backup)
            config.load_editions.cache_clear()

    def test_rejects_unknown_group(self):
        from scripts.api.editions import api_save_edition_meta

        edyaml, backup, config = self._yaml_guard()
        try:
            res = api_save_edition_meta("catholic-study", {"popup_languages_capped": ["klingon"]})
            assert "error" in res and "popup_languages_capped" in res["error"]
        finally:
            edyaml.write_bytes(backup)
            config.load_editions.cache_clear()

    def test_rejects_pick_over_cap_cross_field(self):
        # One payload that flips the target AND picks 3 groups: the merged
        # record caps at 2 (kindle default) so the save must refuse — and
        # refuse ATOMICALLY (the valid target_reader half must not be
        # written when the pick half fails: the RED run of this very test
        # leaked `target_reader: kindle` into editions.yaml).
        from scripts.api.editions import api_save_edition_meta

        edyaml, backup, config = self._yaml_guard()
        try:
            res = api_save_edition_meta(
                "catholic-study",
                {"target_reader": "kindle", "popup_languages_capped": ["hebrew", "greek", "latin"]},
            )
            assert "error" in res, res
            assert edyaml.read_bytes() == backup, "a refused save must write NOTHING"
        finally:
            edyaml.write_bytes(backup)
            config.load_editions.cache_clear()

    def test_preview_knows_both_fields(self):
        from scripts.api.editions import api_preview_edition_changes

        res = api_preview_edition_changes(
            "catholic-study",
            {"max_popup_languages": 2, "popup_languages_capped": ["hebrew", "greek"]},
        )
        assert "error" not in res, res
        assert not res.get("unknown_fields"), res.get("unknown_fields")


class TestSurfacing:
    def test_api_customize_data_surfaces_resolved_cap_and_pick(self):
        from scripts.web import api_customize_data

        eds = {e["id"]: e for e in api_customize_data()["editions"]}
        cs = eds["catholic-study"]
        # catholic-study is not kindle-targeted -> uncapped, empty pick.
        assert cs.get("max_popup_languages") is None
        assert cs.get("popup_languages_capped") == []

    def test_customize_template_has_the_controls(self):
        import pathlib

        from scripts.core import config

        repo = pathlib.Path(config.__file__).resolve().parents[2]
        src = (repo / "scripts" / "templates" / "customize.py").read_text(encoding="utf-8")
        assert 'data-field="max_popup_languages"' in src
        assert 'data-field="popup_languages_capped"' in src
        for group in ("hebrew", "greek", "latin", "arabic"):
            assert f'data-cap-group="{group}"' in src

    def test_wizard_target_caps_carry_the_cap(self):
        import pathlib

        from scripts.core import config

        repo = pathlib.Path(config.__file__).resolve().parents[2]
        src = (repo / "scripts" / "templates" / "wizard.py").read_text(encoding="utf-8")
        assert "max_popup_languages: 2" in src  # kindle
        assert "max_popup_languages: null" in src  # uncapped targets
        # The kindle note states the ready-made default honestly.
        assert "Hebrew + Greek" in src


class TestCloneCarriesEditableFields:
    """Clone-whitelist defect class (found in passing wiring K-KIN): the
    clone writer kept its own hand-typed scalar list, silently dropping
    every field added since (target_reader, marker_badge_style, the new
    cap keys, …) — a clone of a kindle edition lost its target. The fix
    derives the clone's copy list from the SAME module-level EDITABLE
    field sets api_save validates against, so a future field cannot
    regress (one source of truth)."""

    def test_editable_sets_are_module_constants(self):
        from scripts.api import editions as ed_api

        assert "target_reader" in ed_api.EDITABLE_TEXT_FIELDS
        assert "max_popup_languages" in ed_api.EDITABLE_TEXT_FIELDS
        assert "closing_colophon" in ed_api.EDITABLE_BOOL_FIELDS
        # The only scalars the clone handles specially (new title, cover
        # override) — everything else MUST flow through automatically.
        assert ed_api.CLONE_SCALAR_SPECIAL == {"title", "cover_image"}

    def test_clone_carries_target_and_cap_fields(self):
        import pathlib

        from scripts.api.editions import api_clone_edition, api_save_edition_meta
        from scripts.core import config

        edyaml = pathlib.Path(config.__file__).resolve().parents[2] / "content" / "editions.yaml"
        backup = edyaml.read_bytes()
        try:
            res = api_save_edition_meta(
                "catholic-study",
                {
                    "target_reader": "kindle",
                    "marker_badge_style": "chip",
                    "max_popup_languages": 2,
                    "popup_languages_capped": ["hebrew", "arabic"],
                },
            )
            assert "error" not in res, res
            config.load_editions.cache_clear()
            res = api_clone_edition({"source_id": "catholic-study", "new_id": "zz-clone-guard"})
            assert "error" not in res, res
            config.load_editions.cache_clear()
            clone = config.editions_by_id()["zz-clone-guard"]
            assert clone.get("target_reader") == "kindle"
            assert clone.get("marker_badge_style") == "chip"
            assert int(clone.get("max_popup_languages")) == 2
            assert clone.get("popup_languages_capped") == ["hebrew", "arabic"]
        finally:
            edyaml.write_bytes(backup)
            config.load_editions.cache_clear()


class TestVnotePassGating:
    def test_kindle_bare_edition_needs_pass(self):
        assert be._vnote_pass_needed(_ed(target_reader="kindle")) is True

    def test_everywhere_bare_edition_skips_pass(self):
        assert be._vnote_pass_needed(_ed()) is False

    def test_popups_off_skips_pass_even_on_kindle(self):
        assert be._vnote_pass_needed(_ed(target_reader="kindle", verse_popups=False)) is False

    def test_existing_triggers_still_fire(self):
        assert be._vnote_pass_needed(_ed(popup_translation="kjv")) is True
        assert be._vnote_pass_needed(_ed(popup_languages_default=["wlc"])) is True
        assert be._vnote_pass_needed(_ed(popup_languages_per_book=["gen=wlc"])) is True
        assert be._vnote_pass_needed(_ed(popup_languages_per_chapter=["gen:1=wlc"])) is True
        assert be._vnote_pass_needed(_ed(popup_languages_per_verse=["gen:1:1=wlc"])) is True
