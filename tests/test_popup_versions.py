"""Multi-version popup registry — single source of truth for which translation
versions a verse popup can carry, how each is rendered, and how its coordinate
maps onto the canonical (KJV) verse system. See
docs/superpowers/specs/2026-05-22-themes-and-multitranslation-popups-design.md."""

from __future__ import annotations

from scripts.core import popup_versions as pv


class TestVersionRegistry:
    def test_core_versions_present(self):
        for vid in ("kjv", "wlc", "lxx-greek"):
            assert vid in pv.VERSION_REGISTRY, f"{vid} missing from registry"

    def test_kjv_keeps_legacy_content_class(self):
        # back-compat: KJV English stays in the recovered-base 'vnote-text'
        assert pv.VERSION_REGISTRY["kjv"]["content_class"] == "vnote-text"
        assert pv.VERSION_REGISTRY["wlc"]["content_class"] == "vnote-hebrew"
        assert pv.VERSION_REGISTRY["lxx-greek"]["content_class"] == "vnote-greek"

    def test_each_version_has_required_fields(self):
        for vid, spec in pv.VERSION_REGISTRY.items():
            for key in ("label", "content_class", "lang", "dir", "has_label_para", "translation_id"):
                assert key in spec, f"{vid} registry entry missing {key!r}"
            assert spec["dir"] in ("ltr", "rtl")

    def test_legacy_aliases_resolve(self):
        assert pv.resolve_version_id("english") == "kjv"
        assert pv.resolve_version_id("hebrew") == "wlc"
        assert pv.resolve_version_id("greek") == "lxx-greek"
        assert pv.resolve_version_id("kjv") == "kjv"  # identity for real ids
        assert pv.resolve_version_id("nope") is None  # unknown -> None

    def test_normalize_coord_identity_default(self):
        # B1: no per-source remaps yet — every adapter is identity.
        assert pv.normalize_coord("lxx-greek", "psa", 23, 1) == ("psa", 23, 1)
        assert pv.normalize_coord("kjv", "gen", 1, 1) == ("gen", 1, 1)

    def test_bakes_now_versions_with_full_data(self):
        # Phase 1 baked kjv/wlc/lxx-greek; Phase 2 added greek-nt (Byzantine NT),
        # then the translation spine: arabic (Van Dyck) + jps (JPS 1917 Tanakh),
        # then douay (Douay-Rheims) + vulgate (Clementine Vulgate), table-driven.
        for vid in ("kjv", "wlc", "lxx-greek", "greek-nt", "arabic", "jps", "douay", "vulgate"):
            assert pv.bakes_now(vid), f"{vid} should bake (full data ingested)"
        for vid in ("brenton-en",):
            assert not pv.bakes_now(vid), f"{vid} must NOT bake until its full data lands"

    def test_trusted_html_flags(self):
        # Original-language sources (WLC <em>-per-word; LXX/Byzantine plain accented) -> raw.
        for vid in ("wlc", "lxx-greek", "greek-nt"):
            assert pv.is_trusted_html(vid), f"{vid} should be trusted pre-formatted HTML"
        for vid in ("kjv", "douay", "jps", "vulgate", "arabic"):
            assert not pv.is_trusted_html(vid), f"{vid} (plain text) must be escaped"


class TestBuildVnoteAsideListBased:
    def _versions(self):
        return [
            {
                "id": "kjv",
                "label": "King James Version",
                "lang": "en",
                "dir": "ltr",
                "has_label_para": False,
                "content_class": "vnote-text",
                "text": "In the beginning...",
            },
            {
                "id": "wlc",
                "label": "Hebrew (Masoretic / WLC)",
                "lang": "he",
                "dir": "rtl",
                "has_label_para": True,
                "content_class": "vnote-hebrew",
                "text": "בְּרֵאשִׁית",
            },
        ]

    def test_renders_one_paragraph_per_version(self):
        from scripts.generate_verse_popups import build_vnote_aside

        html = build_vnote_aside(code="gen", ch=1, vs=1, title="Genesis", versions=self._versions())
        assert 'id="vnote-gen-1-1"' in html
        assert 'epub:type="footnote"' in html
        assert '<p class="vnote-text">In the beginning...</p>' in html
        assert '<p class="vnote-source-label">Hebrew (Masoretic / WLC)</p>' in html
        assert '<p class="vnote-hebrew" dir="rtl" lang="he">בְּרֵאשִׁית</p>' in html
        # KJV has_label_para False -> no source-label before vnote-text
        assert '<p class="vnote-source-label">King James Version</p>' not in html
        assert 'href="#v-gen-1-1"' in html  # back-link preserved

    def test_empty_versions_yields_placeholder(self):
        from scripts.generate_verse_popups import build_vnote_aside

        html = build_vnote_aside(code="gen", ch=1, vs=1, title="Genesis", versions=[])
        assert "vnote-empty" in html

    def test_trusted_html_passes_markup_raw_else_escapes(self):
        from scripts.generate_verse_popups import build_vnote_aside

        versions = [
            {
                "id": "wlc",
                "label": "Hebrew",
                "lang": "he",
                "dir": "rtl",
                "has_label_para": True,
                "content_class": "vnote-hebrew",
                "trusted_html": True,
                "text": "<em>שָׁלוֹם</em>",
            },
            {
                "id": "douay",
                "label": "Douay",
                "lang": "en",
                "dir": "ltr",
                "has_label_para": True,
                "content_class": "vnote-douay",
                "trusted_html": False,
                "text": "a <b>bold</b> claim",
            },
        ]
        html = build_vnote_aside(code="gen", ch=1, vs=1, title="Genesis", versions=versions)
        assert "<em>שָׁלוֹם</em>" in html  # trusted -> raw markup preserved
        assert "a &lt;b&gt;bold&lt;/b&gt; claim" in html  # untrusted -> escaped


class TestHarvestAllVersions:
    SAMPLE = (
        '<aside class="vnote" id="vnote-gen-1-1" epub:type="footnote">'
        '<p class="vnote-text">In the beginning</p>'
        '<p class="vnote-source-label">Hebrew (Masoretic / WLC)</p>'
        '<p class="vnote-hebrew" dir="rtl" lang="he">בְּרֵאשִׁית</p>'
        '<p class="vnote-source-label">Latin (Clementine Vulgate)</p>'
        '<p class="vnote-vulgate" lang="la">In principio</p>'
        "</aside>"
    )

    def test_harvests_every_registered_version(self):
        from scripts.generate_verse_popups import harvest_existing_langs

        got = harvest_existing_langs(self.SAMPLE)
        entry = got["vnote-gen-1-1"]
        assert entry["wlc"] == "בְּרֵאשִׁית"
        assert entry["vulgate"] == "In principio"
        assert entry["kjv"] == "In the beginning"


class TestAssembleVersionsForVerse:
    def test_includes_only_versions_with_text(self, monkeypatch):
        import scripts.generate_verse_popups as gvp
        from scripts.core import translations as tx

        # kjv + wlc have text for gen 1:1; every other translation returns None.
        def fake_get_verse(tid, code, ch, vs):
            return {"kjv": "In the beginning", "wlc": "בְּרֵאשִׁית"}.get({"kjv": "kjv", "wlc": "wlc"}.get(tid, ""))

        monkeypatch.setattr(tx, "get_verse", fake_get_verse)

        versions = gvp.assemble_versions_for_verse("gen", 1, 1, harvested={})
        ids = [v["id"] for v in versions]
        assert ids == ["kjv", "wlc"]  # registry order, text-only
        assert versions[0]["content_class"] == "vnote-text"
        assert versions[1]["dir"] == "rtl"

    def test_unbaked_version_excluded_even_with_data(self, monkeypatch):
        # brenton-en has a registry entry + ingestible data, but bake=False -> it
        # must NOT appear in the shared base (this is the byte-compat guard).
        import scripts.generate_verse_popups as gvp
        from scripts.core import translations as tx

        def fake_get_verse(tid, code, ch, vs):
            return {"kjv": "In the beginning", "lxx-brenton-english": "In the beginning God made"}.get(tid)

        monkeypatch.setattr(tx, "get_verse", fake_get_verse)
        ids = [v["id"] for v in gvp.assemble_versions_for_verse("gen", 1, 1, harvested={})]
        assert ids == ["kjv"], f"only baked versions expected, got {ids}"
        assert "brenton-en" not in ids


class TestBuildSideRegistry:
    def test_build_edition_popup_languages_includes_every_registry_version(self):
        import scripts.build_edition as be

        for vid in pv.VERSION_REGISTRY:
            assert vid in be.POPUP_LANGUAGES, f"{vid} not exposed in build_edition.POPUP_LANGUAGES"
        assert be.POPUP_LANGUAGES["kjv"]["content_class"] == "vnote-text"

    def test_legacy_slots_preserved_as_superset(self):
        # The parallel-bible / future-language slots must NOT be dropped.
        import scripts.build_edition as be

        for slot in ("latin", "geez", "amharic", "aramaic", "coptic", "syriac"):
            assert slot in be.POPUP_LANGUAGES, f"legacy slot {slot!r} must be preserved"

    def test_resolve_maps_legacy_ids_and_keeps_legacy_slots(self):
        import scripts.build_edition as be

        # english/hebrew/greek alias to version ids; latin (used by anglican-bcp)
        # is a legacy slot that resolves to itself.
        got = be._resolve_popup_languages({"popup_languages_default": ["english", "hebrew", "latin"]}, "gen")
        assert got == {"kjv", "wlc", "latin"}, got
