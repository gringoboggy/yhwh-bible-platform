import json
from pathlib import Path

import pytest

from scripts.core import translations as tx

REPO = Path(__file__).resolve().parent.parent
COLL = REPO / "content" / "manuscript" / "kings" / "collation"


class TestVersificationAttr:
    def test_parser_reads_own(self):
        assert tx._load_book_attr_from_text('VERSIFICATION = "own"\nVERSES = []', "VERSIFICATION") == "own"

    def test_parser_none_when_absent(self):
        assert tx._load_book_attr_from_text("VERSES = []", "VERSIFICATION") is None

    def test_parser_ignores_non_string(self):
        assert tx._load_book_attr_from_text("VERSIFICATION = 3\nVERSES = []", "VERSIFICATION") is None

    def test_versification_of_defaults_canonical(self):
        assert tx.versification_of("kjv", "gen") == "canonical"

    def test_versification_of_missing_book_is_canonical(self):
        assert tx.versification_of("kjv", "zzz") == "canonical"

    def test_psalms_is_own_versified(self):
        assert tx.versification_of("geez-tewahedo", "psa") == "own"


from scripts.core import standalone_store as ss


class TestStandaloneStore:
    def test_collation_to_entries_uses_own_numbering(self):
        coll = json.loads((COLL / "1ki6_collation_v2.json").read_text(encoding="utf-8"))
        verses, appmap = ss.collation_to_store_entries(coll)
        assert len(verses) == 33  # CAM's own sense-units, NOT 38 KJV
        assert verses[0] == (6, 1, coll["primary_verses"][0]["geez_text"])
        assert appmap["1"]["kjv"] == [["1ki", 6, 1]]  # v1 anchored to KJV 6:1
        assert appmap["1"]["confidence"] == "anchored"
        assert appmap["1"]["apparatus"]  # the GG-vs-CAM variant rows

    def test_build_book_store_writes_module_and_sidecar(self, tmp_path):
        paths = [COLL / f"1ki{n}_collation_v2.json" for n in range(1, 7)]
        res = ss.build_book_store("1ki", paths, tmp_path)
        assert res["book"] == "1ki" and res["chapters"] == 6 and res["verses"] > 0
        text = (tmp_path / "1ki.py").read_text(encoding="utf-8")
        verses = tx.load_book_verses_from_text(text)
        assert verses and all(len(t) == 3 for t in verses)
        assert tx._load_book_attr_from_text(text, "VERSIFICATION") == "own"
        am = json.loads((tmp_path / "1ki_apparatus.json").read_text(encoding="utf-8"))
        assert "6" in am and "1" in am["6"] and am["6"]["1"]["kjv"] == [["1ki", 6, 1]]


from scripts import build_standalone as bs


class TestBodyRender:
    def _sample(self):
        verses = [(1, "ወእምዝ ፡ በ፬፻ ፡ ወ፹ ፡ ዓመት"), (2, "ወቤት ፡ ዘሐነፀ ፡ ሰሎሞን")]
        appmap = {
            "1": {
                "kjv": [["1ki", 6, 1]],
                "confidence": "anchored",
                "apparatus": [{"base": "ወእምዝ", "other": "ወውእቱ", "class": "disagree"}],
            },
            "2": {"kjv": [["1ki", 6, 2]], "confidence": "interpolated", "apparatus": []},
        }
        return bs.render_chapter_body("1ki", 6, verses, appmap)

    def test_verse_uses_own_number_and_vnlink(self):
        html = self._sample()
        assert '<a class="vn-link" id="v-1ki-6-1" href="#vnote-1ki-6-1"' in html
        assert '<span class="vn">1</span>' in html
        assert "ወእምዝ ፡ በ፬፻ ፡ ወ፹ ፡ ዓመት" in html

    def test_popup_carries_kjv_xref_with_confidence(self):
        html = self._sample()
        assert '<aside class="vnote" id="vnote-1ki-6-1"' in html
        assert "1 Kings 6:1" in html
        assert "anchored" in html
        assert "interpolated" in html

    def test_popup_carries_apparatus_variants(self):
        html = self._sample()
        assert "ወውእቱ" in html
        assert "vnote-text" not in html


class TestXhtmlDocAndOpf:
    def test_wrap_xhtml_doc_is_wellformed(self):
        import xml.dom.minidom as md

        frag = bs.render_chapter_body("1ki", 6, [(1, "ወእምዝ")], {"1": {"kjv": [], "apparatus": []}})
        doc = bs.wrap_xhtml_doc("1 Kings 6", frag)
        md.parseString(doc.encode("utf-8"))  # raises if not well-formed XML
        assert "xmlns:epub" in doc and "verse-p" in doc and 'class="bible-body"' in doc

    def test_build_spine_manifest_lists_generated_files(self):
        items = [("geez_1ki_6", "geez_1ki_6.xhtml")]
        manifest, spine = bs.build_manifest_and_spine(items)
        assert 'id="geez_1ki_6"' in manifest and 'href="geez_1ki_6.xhtml"' in manifest
        assert 'media-type="application/xhtml+xml"' in manifest
        assert 'idref="geez_1ki_6"' in spine

    def test_patch_standalone_opf_drops_body_keeps_resources(self):
        opf = (
            "<package><manifest>\n"
            '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>\n'
            '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>\n'
            '<item id="css" href="stylesheet.css" media-type="text/css"/>\n'
            '<item id="cover" href="cover.jpeg" media-type="image/jpeg"/>\n'
            '<item id="titlepage" href="titlepage.xhtml" media-type="application/xhtml+xml"/>\n'
            '<item id="id161" href="index_split_000.html" media-type="application/xhtml+xml"/>\n'
            '<item id="id160" href="index_split_001.html" media-type="application/xhtml+xml"/>\n'
            '</manifest>\n<spine toc="ncx">\n'
            '<itemref idref="titlepage"/>\n<itemref idref="id161"/>\n<itemref idref="id160"/>\n'
            "</spine></package>"
        )
        out = bs.patch_standalone_opf(opf, [("geez_1ki_6", "geez_1ki_6.xhtml")])
        assert "index_split_000.html" not in out and "index_split_001.html" not in out
        assert 'id="id161"' not in out and 'idref="id161"' not in out and 'idref="id160"' not in out
        for keep in (
            'id="css"',
            'id="nav"',
            'id="cover"',
            'id="ncx"',
            'id="titlepage"',
            'idref="titlepage"',
            '<spine toc="ncx">',
        ):
            assert keep in out, f"dropped a resource it should keep: {keep}"
        assert 'id="geez_1ki_6"' in out and 'href="geez_1ki_6.xhtml"' in out and 'idref="geez_1ki_6"' in out


class TestBuildStandalone:
    def test_build_standalone_produces_epub(self, tmp_path):
        out = bs.build_standalone("standalone-geez", tmp_path, "v28a")
        assert out["status"] == "ok", out
        epub = Path(out["output_path"])
        assert epub.is_file() and epub.suffix == ".epub" and epub.stat().st_size > 10_000
        import zipfile

        with zipfile.ZipFile(epub) as z:
            names = z.namelist()
            assert names[0] == "mimetype"  # OCF: mimetype first
            assert any(n == "geez_1ki_6.xhtml" for n in names)  # a generated body file is packaged
            assert not any("index_split_" in n for n in names)  # original body fully swapped out
        assert out["chapters"] == 165  # 10 (1ki) + 3 (1sa) + 1 (2sa) + 151 (psa)


class TestStandaloneCoverReachesEpub:
    """σ.5.3 — the standalone build must ship the composed Ethiopic-script
    cover. build_standalone calls build_edition.apply_edition_cover, which (now
    that cover_image is non-empty) swaps the base master cover.jpeg for the
    edition's composed cover. Mirrors test_covers.TestCoverReachesEpub for the
    standalone path."""

    def test_standalone_geez_build_ships_composed_cover(self, tmp_path):
        import zipfile

        composed = REPO / "content" / "covers" / "standalone-geez.jpg"
        assert composed.is_file(), "σ.5.2 cover must exist before the build can ship it"

        out = bs.build_standalone("standalone-geez", tmp_path, "v28a")
        assert out["status"] == "ok", out
        epub = Path(out["output_path"])
        with zipfile.ZipFile(epub) as z:
            cover_name = next((n for n in z.namelist() if n.endswith("cover.jpeg")), None)
            assert cover_name is not None, "no cover.jpeg in the standalone EPUB"
            epub_cover = z.read(cover_name)

        # The packaged cover is byte-identical to the composed standalone cover
        # — not the base master cover that ships in epub_working/.
        assert epub_cover == composed.read_bytes(), "standalone EPUB cover != composed standalone-geez.jpg"


class TestPsalmsXref:
    def test_lxx_psalms_mapping_known_seams(self):
        f = ss.lxx_psalms_to_kjv
        assert f(5) == [5]  # 1-8 identical
        assert f(9) == [9, 10]  # LXX 9 = KJV 9+10
        assert f(10) == [11]  # LXX one behind through the middle
        assert f(112) == [113]
        assert f(113) == [114, 115]  # LXX 113 = KJV 114+115
        assert f(114) == [116] and f(115) == [116]  # LXX 114+115 = KJV 116
        assert f(117) == [118]
        assert f(146) == [147] and f(147) == [147]  # LXX 146+147 = KJV 147
        assert f(150) == [150]  # 148-150 identical
        assert f(151) == []  # LXX-only, not in KJV

    def test_psa_in_standalone_book_set(self):
        assert "psa" in bs._STANDALONE_BOOKS

    def test_psa_apparatus_sidecar_exists_and_is_xref_only(self):
        p = REPO / "content" / "translations" / "geez-tewahedo" / "psa_apparatus.json"
        assert p.is_file()
        am = json.loads(p.read_text(encoding="utf-8"))
        any_ch = next(iter(am.values()))
        any_v = next(iter(any_ch.values()))
        assert "kjv" in any_v and any_v["apparatus"] == []  # xref only, no manuscript apparatus
        assert any_v["confidence"] in ("interpolated", None)  # honest — never "anchored" for Psalms


class TestDispatchGuard:
    def test_build_one_routes_standalone(self, tmp_path, monkeypatch):
        from scripts import build_edition as be

        called = {}

        def fake(edition_id, output_dir, version):
            called["id"] = edition_id
            return {"status": "ok", "output_path": str(tmp_path / "x.epub")}

        monkeypatch.setattr("scripts.build_standalone.build_standalone", fake)
        be.build_one("standalone-geez", tmp_path, "v28a", [], False, False)
        assert called.get("id") == "standalone-geez"

    def test_build_one_does_not_route_kjv_edition(self, tmp_path, monkeypatch):
        from scripts import build_edition as be
        from scripts.core import config

        tripped = {"v": False}

        def fake(*a, **k):
            tripped["v"] = True
            return {}

        monkeypatch.setattr("scripts.build_standalone.build_standalone", fake)
        try:
            be.build_one("catholic-study", tmp_path, "v28a", config.load_kinds(), True, False)
        except Exception:
            pass  # we only care that the standalone path was NOT taken
        assert tripped["v"] is False


class TestDuplicateVerseIds:
    def test_duplicate_verse_numbers_get_unique_ids(self):
        verses = [(14, "first line"), (14, "second line")]
        appmap = {"14": {"kjv": [["psa", 22, 14]], "confidence": "interpolated", "apparatus": []}}
        html = bs.render_chapter_body("psa", 21, verses, appmap)
        assert html.count('id="v-psa-21-14"') == 1  # first occurrence keeps the plain id
        assert html.count('id="v-psa-21-14-2"') == 1  # second is disambiguated
        assert html.count('id="vnote-psa-21-14"') == 1
        assert html.count('id="vnote-psa-21-14-2"') == 1
        assert html.count('href="#vnote-psa-21-14"') == 1
        assert html.count('href="#vnote-psa-21-14-2"') == 1
        assert html.count('<span class="vn">14</span>') == 2  # BOTH still display "14" (faithful)
        import xml.dom.minidom as md

        md.parseString(bs.wrap_xhtml_doc("Psalms 21", html).encode("utf-8"))  # well-formed


class TestSourceOrderPreserved:
    def test_psalm36_non_adjacent_dups_keep_source_order(self):
        # The HaCohen Ge'ez Psalter stores Ps 36 with verses 24 & 25 each appearing
        # twice, NON-adjacently (…24,25,24,25…). The render must keep that source order,
        # NOT regroup to 24,24,25,25 (which translations.get_chapter's sort would do).
        by_ch = bs.chapter_verses_in_source_order("geez-tewahedo", "psa")
        nums = [v for v, _t in by_ch[36]]
        assert nums != sorted(nums), "Ps 36 has non-adjacent dup verses; must not be pre-sorted"
        i = nums.index(24)
        assert nums[i : i + 4] == [24, 25, 24, 25], f"source order scrambled: {nums[i : i + 4]}"

    def test_unique_numbered_chapter_unaffected(self):
        # Kings has unique verse numbers → source order is already ascending (sanity).
        by_ch = bs.chapter_verses_in_source_order("geez-tewahedo", "1ki")
        nums = [v for v, _t in by_ch[6]]
        assert nums == sorted(nums) and len(nums) == 33


class TestReviewedTier:
    def test_reviewed_tier3_registered(self):
        from scripts.core import provenance_tiers as pt

        assert pt.is_known_tier("ai-back-translation-reviewed-tier3")
        t = pt.tier_for("ai-back-translation-reviewed-tier3")
        assert t.quality_rank == 3


class TestEnglishRender:
    def test_vnote_emits_english_when_present(self):
        v = bs._render_vnote(
            "vnote-1ki-6-1",
            "1 Kings 6:1",
            {"kjv": [["1ki", 6, 1]], "confidence": "anchored", "apparatus": []},
            english="And it happened in the four hundred and eightieth year...",
        )
        assert '<p class="vnote-text">And it happened in the four hundred and eightieth year...</p>' in v
        assert "KJV cross-reference: 1 Kings 6:1" in v
        assert v.index("vnote-text") < v.index("vnote-xref")

    def test_vnote_no_english_when_absent(self):
        v = bs._render_vnote("vnote-1ki-6-1", "1 Kings 6:1", {"kjv": [], "apparatus": []})
        assert "vnote-text" not in v

    def test_english_is_html_escaped(self):
        v = bs._render_vnote("n", "t", {"kjv": [], "apparatus": []}, english="a & b < c")
        assert "a &amp; b &lt; c" in v

    def test_render_chapter_body_pulls_english_from_en_map(self):
        verses = [(1, "ወእምዝ"), (2, "ወቤት")]
        appmap = {"1": {"kjv": [], "apparatus": []}, "2": {"kjv": [], "apparatus": []}}
        en_map = {(1, 1): "And afterward"}  # occurrence-keyed: (verse_number, nth_occurrence)
        html = bs.render_chapter_body("1ki", 6, verses, appmap, en_map)
        assert '<p class="vnote-text">And afterward</p>' in html
        assert html.count("vnote-text") == 1

    def test_render_chapter_body_graceful_without_en_map(self):
        html = bs.render_chapter_body("1ki", 6, [(1, "ወእምዝ")], {"1": {"kjv": [], "apparatus": []}})
        assert "vnote-text" not in html

    def test_dup_verse_numbers_get_distinct_english_by_occurrence(self):
        # Ps 36-style: two DISTINCT verses share the number 24 (and 25), in source
        # order. Each occurrence must receive its OWN English — keyed by
        # (verse_number, nth_occurrence), not by the colliding verse number (spec §10.6).
        verses = [(24, "ግዕዝ-A"), (25, "ግዕዝ-B"), (24, "ግዕዝ-C"), (25, "ግዕዝ-D")]
        appmap: dict = {}
        en_map = {(24, 1): "first-24", (25, 1): "first-25", (24, 2): "second-24", (25, 2): "second-25"}
        html = bs.render_chapter_body("psa", 36, verses, appmap, en_map)
        for en in ("first-24", "first-25", "second-24", "second-25"):
            assert html.count(f'<p class="vnote-text">{en}</p>') == 1, f"missing/duplicated EN: {en}"
        assert html.count("vnote-text") == 4  # every distinct verse got its own English

    def test_en_occurrence_map_keys_dups_by_occurrence(self, monkeypatch):
        # The loader builds {chapter: {(verse, occurrence): english}} in SOURCE order,
        # so a dup-verse store (Ps 36-style) keys each distinct verse separately.
        fake = [(36, 24, "A"), (36, 25, "B"), (36, 24, "C"), (36, 25, "D"), (37, 1, "E")]
        monkeypatch.setattr(tx, "_load_book", lambda translation, book: fake)
        m = bs.en_occurrence_map("geez-tewahedo-en", "psa")
        assert m[36] == {(24, 1): "A", (25, 1): "B", (24, 2): "C", (25, 2): "D"}
        assert m[37] == {(1, 1): "E"}


class TestEnglish1Ki6:
    def test_en_1ki6_covers_all_33_verses_at_own_coords(self):
        geez = tx.get_chapter("geez-tewahedo", "1ki", 6)  # [(v, geez)]
        en = tx.get_chapter("geez-tewahedo-en", "1ki", 6)  # [(v, english)]
        assert len(en) == 33 and len(geez) == 33
        assert {v for v, _ in en} == {v for v, _ in geez}  # EN coords == Ge'ez coords
        assert all(text.strip() for _v, text in en)  # no empty renderings
        assert tx.versification_of("geez-tewahedo-en", "1ki") == "own"


class TestEnglishScaledKingsSamuel:
    def test_all_collated_chapters_have_english_at_own_coords(self):
        collated = [("1ki", c) for c in range(1, 7)] + [("1sa", c) for c in (1, 3, 17)] + [("2sa", 11)]
        for book, ch in collated:
            geez = tx.get_chapter("geez-tewahedo", book, ch)
            en = tx.get_chapter("geez-tewahedo-en", book, ch)
            assert len(en) == len(geez) > 0, f"{book} {ch}: en {len(en)} vs geez {len(geez)}"
            assert {v for v, _ in en} == {v for v, _ in geez}, f"{book} {ch}: coord mismatch"
            assert all(t.strip() for _v, t in en), f"{book} {ch}: empty EN rendering"


class TestEnglishPsalmsProofBatch:
    PROOF = (1, 21, 23, 36, 46, 68, 71, 101, 115, 144, 150)

    def test_psa_en_mirrors_geez_source_order_incl_dups(self):
        # EN store keys must mirror the Ge'ez store's per-chapter source order EXACTLY
        # (incl. duplicate verse numbers + gaps), or occurrence-index keying misaligns.
        geez = bs.chapter_verses_in_source_order("geez-tewahedo", "psa")
        en = bs.chapter_verses_in_source_order("geez-tewahedo-en", "psa")
        for ch in self.PROOF:
            assert ch in en, f"Ps {ch} missing from EN store"
            en_seq = [v for v, _ in en[ch]]
            geez_seq = [v for v, _ in geez[ch]]
            assert en_seq == geez_seq, f"Ps {ch}: EN seq {en_seq} != Ge'ez {geez_seq}"
            assert all(t.strip() for _v, t in en[ch]), f"Ps {ch}: empty EN rendering"

    def test_psa_en_versification_is_own(self):
        assert tx.versification_of("geez-tewahedo-en", "psa") == "own"

    def test_psa36_dup_verses_have_distinct_english(self):
        # The keying-fix's real-data case: Ps 36 has two v24 and two v25, non-adjacent.
        en = bs.chapter_verses_in_source_order("geez-tewahedo-en", "psa")[36]
        v24 = [t for v, t in en if v == 24]
        v25 = [t for v, t in en if v == 25]
        assert len(v24) == 2 and len(v25) == 2
        assert v24[0] != v24[1], "the two Ps 36:24 verses must carry distinct English"
        assert v25[0] != v25[1], "the two Ps 36:25 verses must carry distinct English"

    def test_psa_en_occurrence_map_disambiguates_dups(self):
        m = bs.en_occurrence_map("geez-tewahedo-en", "psa")
        assert {(24, 1), (24, 2), (25, 1), (25, 2)} <= set(m[36])
        assert m[36][(24, 1)] != m[36][(24, 2)]
        assert m[36][(25, 1)] != m[36][(25, 2)]

    def test_all_psa_en_chapters_mirror_geez_source_order(self):
        # Durable invariant across every batch: each EN chapter present mirrors the Ge'ez
        # store's source order exactly (so occurrence-index keying never misaligns).
        geez = bs.chapter_verses_in_source_order("geez-tewahedo", "psa")
        en = bs.chapter_verses_in_source_order("geez-tewahedo-en", "psa")
        assert en, "no Psalms EN present"
        for ch, lst in en.items():
            assert [v for v, _ in lst] == [v for v, _ in geez[ch]], f"Ps {ch}: EN seq != Ge'ez"
            assert all(t.strip() for _v, t in lst), f"Ps {ch}: empty EN"
