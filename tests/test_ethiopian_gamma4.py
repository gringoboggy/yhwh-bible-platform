"""γ.4 — Ethiopian Tewahedo commentary corpus + detector pins.

Topic file (created alongside the γ.4 ship). Mirrors γ.3's
test shape: seed JSON validation + loader pins + detector
contract + kinds.yaml registration.

Coverage:
- TestGamma4DataFile:                the seed JSON parses, has the
  promised Ephrem + Cyril + 1 Enoch entries, every entry carries
  full attribution.
- TestGamma4EthiopianCommentariesLoader: the loader indexes by
  verse + by father, returns frozen dataclass instances, surfaces
  SourceMissingError gracefully.
- TestGamma4DetectorContract:        `EthiopianCommentaryDetector`
  emits the right Candidate shape; confidence 0.95; empty list
  for verses with no commentary; registered in ALL_DETECTORS;
  body builder escapes HTML; BC/AD era display correct for
  pre-Christian sources (1 Enoch ~200 BC).
- TestGamma4KindIsRegistered:        `comm-ethiopian` exists in
  `content/kinds.yaml` (was already there pre-γ.4); pin so a
  future kinds-cleanup doesn't drop it silently.
- TestGamma4Coverage:                seed entries span Genesis +
  Psalms + John, include at least one 1 Enoch entry (the
  Tewahedo-canonical distinctive), and at least one Cyril entry
  (the Miaphysite anchor).

Pinning rationale: γ.4 is the flagship payload for the Tewahedo
Bible's primary differentiator. Drift in the attribution format,
the detector confidence, the 1 Enoch inclusion, or the kind
registration would break the buyer-facing distinctiveness claim
silently.
"""

from __future__ import annotations


class TestGamma4DataFile:
    """The seed JSON at content/sources/ethiopian_commentaries.json
    parses and carries the promised Ephrem + Cyril + 1 Enoch set."""

    @classmethod
    def setup_class(cls):
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        cls.path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        cls.data = json.loads(cls.path.read_text(encoding="utf-8"))

    def test_file_exists(self):
        assert self.path.is_file()

    def test_has_meta_block(self):
        assert "_meta" in self.data
        meta = self.data["_meta"]
        for required in ("source", "scope", "public_domain_basis", "schema_version"):
            assert required in meta, f"_meta missing field {required!r}"
        assert meta["schema_version"] == 1

    def test_meta_documents_pd_basis(self):
        # The buyer-facing claim is that every source is PD; pin the
        # _meta documents Ephrem (NPNF Series 2 vol 13) + Cyril (NPNF
        # vols 7 + 14) + Charles (1912) as the PD anchors.
        meta = self.data["_meta"]
        pd = meta["public_domain_basis"]
        assert "Ephrem" in pd
        assert "Cyril" in pd
        assert "Charles" in pd
        assert "1912" in pd

    def test_has_entries_list(self):
        assert "entries" in self.data
        assert isinstance(self.data["entries"], list)
        assert len(self.data["entries"]) >= 10, "expected ≥10 seed entries for γ.4 flagship"

    def test_every_entry_has_required_fields(self):
        for entry in self.data["entries"]:
            for field in (
                "book",
                "chapter",
                "verse",
                "father",
                "work",
                "year",
                "summary",
                "attribution",
            ):
                assert field in entry, f"entry missing field {field!r}: {entry!r}"

    def test_every_entry_cites_pd_source(self):
        # Pin: every entry's attribution mentions either NPNF (the
        # Schaff series anchoring Ephrem + Cyril) or "Charles" (the
        # R.H. Charles 1912 1 Enoch translation), and every one
        # carries the explicit "PD" marker.
        for entry in self.data["entries"]:
            attr = entry["attribution"]
            assert "NPNF" in attr or "Charles" in attr, f"entry not attributed to NPNF or Charles: {attr!r}"
            assert "PD" in attr, f"entry attribution missing PD marker: {attr!r}"

    def test_genesis_1_1_present(self):
        # Canonical opening — buyers' first sanity-check verse.
        for entry in self.data["entries"]:
            if entry["book"] == "gen" and entry["chapter"] == 1 and entry["verse"] == 1:
                return
        raise AssertionError("seed corpus missing Gen 1:1")


class TestGamma4EthiopianCommentariesLoader:
    """The loader class in `scripts.core.sources` indexes the JSON
    correctly + raises SourceMissingError on absent cache."""

    def test_loader_returns_frozen_dataclass_instances(self):
        from scripts.core import sources

        ec = sources.ethiopian_commentaries()
        entries = ec.for_verse("gen", 1, 1)
        assert entries, "Gen 1:1 should have at least one Ethiopian commentary"
        entry = entries[0]
        assert isinstance(entry, sources.EthiopianCommentary)
        import dataclasses

        assert dataclasses.is_dataclass(entry)
        for field_name in ("book", "chapter", "verse", "father", "work", "year", "summary", "attribution"):
            value = getattr(entry, field_name)
            assert value not in (None, "", 0) or field_name == "year", f"{field_name} unset"

    def test_by_verse_lookup(self):
        from scripts.core import sources

        ec = sources.ethiopian_commentaries()
        gen11 = ec.for_verse("gen", 1, 1)
        assert len(gen11) >= 1
        assert all(e.book == "gen" and e.chapter == 1 and e.verse == 1 for e in gen11)

    def test_by_verse_empty_for_unknown(self):
        from scripts.core import sources

        ec = sources.ethiopian_commentaries()
        # Matthew 28:1 has no seed yet.
        empty = ec.for_verse("mat", 28, 1)
        assert empty == []

    def test_by_father_lookup(self):
        from scripts.core import sources

        ec = sources.ethiopian_commentaries()
        ephrem = ec.by_father("Ephrem the Syrian")
        assert len(ephrem) >= 1, "Ephrem must appear in the seed (Syriac anchor)"
        # Every returned entry has the Ephrem father field.
        for entry in ephrem:
            assert entry.father == "Ephrem the Syrian"

    def test_by_father_finds_cyril(self):
        # Cyril is the Miaphysite anchor — pin he appears so a future
        # corpus cleanup doesn't accidentally drop the Christology
        # entries.
        from scripts.core import sources

        ec = sources.ethiopian_commentaries()
        cyril = ec.by_father("Cyril of Alexandria")
        assert len(cyril) >= 1

    def test_by_father_finds_1_enoch_tradition(self):
        # 1 Enoch is THE Tewahedo distinctive — its presence is
        # load-bearing for the v1.x differentiation claim.
        from scripts.core import sources

        ec = sources.ethiopian_commentaries()
        enoch = ec.by_father("1 Enoch (Ethiopian tradition)")
        assert len(enoch) >= 1, "1 Enoch entries are the Tewahedo distinctive — must appear in seed"

    def test_by_father_empty_for_unknown(self):
        from scripts.core import sources

        ec = sources.ethiopian_commentaries()
        empty = ec.by_father("Origen")
        assert empty == []

    def test_loader_handles_missing_cache(self, tmp_path, monkeypatch):
        from scripts.core import sources

        nope = tmp_path / "ethiopian_commentaries.json"
        monkeypatch.setattr(sources.EthiopianCommentaries, "PATH", nope)
        sources.ethiopian_commentaries.cache_clear()
        try:
            import pytest

            with pytest.raises(sources.SourceMissingError):
                sources.EthiopianCommentaries()
        finally:
            sources.ethiopian_commentaries.cache_clear()


class TestGamma4DetectorContract:
    """`EthiopianCommentaryDetector` emits proper Candidates and
    is registered in `ALL_DETECTORS`."""

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()

    def test_registered_in_all_detectors(self):
        from scripts.core import detectors

        assert detectors.EthiopianCommentaryDetector in detectors.ALL_DETECTORS, (
            "EthiopianCommentaryDetector missing from ALL_DETECTORS — prospect.py won't run it on the corpus"
        )

    def test_registered_after_patristic(self):
        # Ordering: γ.4 runs after γ.3 so tradition-specific
        # entries get appended to the canonical Father ones in
        # candidate order. Pin so a future cleanup doesn't reorder.
        from scripts.core import detectors

        detectors_list = list(detectors.ALL_DETECTORS)
        p_idx = detectors_list.index(detectors.PatristicCommentaryDetector)
        e_idx = detectors_list.index(detectors.EthiopianCommentaryDetector)
        assert e_idx > p_idx, "Ethiopian detector must run after Patristic"

    def test_kind_is_comm_ethiopian(self):
        from scripts.core import detectors

        assert detectors.EthiopianCommentaryDetector.kind == "comm-ethiopian"

    def test_detect_returns_candidate_for_gen_1_1(self):
        from scripts.core import detectors

        d = detectors.EthiopianCommentaryDetector()
        candidates = d.detect("gen", 1, 1, "In the beginning God made heaven and earth.")
        assert candidates, "Gen 1:1 should produce at least one candidate"
        c = candidates[0]
        assert c.kind == "comm-ethiopian"
        assert c.book == "gen"
        assert c.chapter == 1
        assert c.verse == 1
        assert c.confidence == 0.95
        assert c.detector == "EthiopianCommentaryDetector"
        assert "<aside" in c.draft_body
        # Body is rendered with the note class for theme styling.
        assert "note-comm-ethiopian" in c.draft_body

    def test_detect_returns_empty_for_uncommented_verse(self):
        from scripts.core import detectors

        d = detectors.EthiopianCommentaryDetector()
        assert d.detect("rev", 1, 1, "") == []  # nothing in seed for Revelation
        assert d.detect("gen", 50, 1, "") == []

    def test_detect_ignores_verse_text(self):
        from scripts.core import detectors

        d = detectors.EthiopianCommentaryDetector()
        a = d.detect("gen", 1, 1, "real verse text")
        b = d.detect("gen", 1, 1, "completely different placeholder")
        assert len(a) == len(b)

    def test_body_is_html_escaped(self):
        from scripts.core import detectors
        from scripts.core.sources import EthiopianCommentary

        synthetic = EthiopianCommentary(
            book="gen",
            chapter=1,
            verse=1,
            father="<TestFather>",
            work="<TestWork>",
            year=400,
            summary="<script>alert(1)</script>",
            attribution="Test, PD.",
        )
        body = detectors.EthiopianCommentaryDetector._format_body(synthetic)
        assert "<script>" not in body, "summary not escaped — XSS risk"
        assert "&lt;script&gt;" in body
        assert "&lt;TestFather&gt;" in body

    def test_body_renders_bc_for_pre_christian_year(self):
        # 1 Enoch is dated c. 200 BC; pin that the body builder
        # emits "BC" for negative years rather than "−200 AD".
        from scripts.core import detectors
        from scripts.core.sources import EthiopianCommentary

        synthetic = EthiopianCommentary(
            book="gen",
            chapter=6,
            verse=1,
            father="1 Enoch (Ethiopian tradition)",
            work="Book of the Watchers",
            year=-200,
            summary="Watchers descend.",
            attribution="Charles 1912. PD.",
        )
        body = detectors.EthiopianCommentaryDetector._format_body(synthetic)
        assert "200 BC" in body
        assert "-200" not in body
        assert "200 AD" not in body

    def test_body_renders_ad_for_post_christian_year(self):
        from scripts.core import detectors
        from scripts.core.sources import EthiopianCommentary

        synthetic = EthiopianCommentary(
            book="gen",
            chapter=1,
            verse=1,
            father="Ephrem the Syrian",
            work="Test",
            year=360,
            summary="Test.",
            attribution="NPNF. PD.",
        )
        body = detectors.EthiopianCommentaryDetector._format_body(synthetic)
        assert "360 AD" in body
        assert "BC" not in body


class TestGamma4KindIsRegistered:
    """The `comm-ethiopian` kind is in `content/kinds.yaml`. It was
    declared pre-γ.4 (anticipated by the original kinds-v2 schema);
    pin its presence so a future kinds-cleanup doesn't drop it
    silently. γ.4 is the first phase to actually emit this kind."""

    def test_comm_ethiopian_kind_present_in_yaml(self):
        from pathlib import Path

        import yaml

        repo = Path(__file__).resolve().parent.parent
        kinds_path = repo / "content" / "kinds.yaml"
        data = yaml.safe_load(kinds_path.read_text(encoding="utf-8"))
        codes = {k["code"] for k in data["kinds"]}
        assert "comm-ethiopian" in codes, "comm-ethiopian kind missing from kinds.yaml"

    def test_comm_ethiopian_kind_has_expected_category(self):
        from pathlib import Path

        import yaml

        repo = Path(__file__).resolve().parent.parent
        kinds_path = repo / "content" / "kinds.yaml"
        data = yaml.safe_load(kinds_path.read_text(encoding="utf-8"))
        kind = next(k for k in data["kinds"] if k["code"] == "comm-ethiopian")
        assert kind["category"] == "comm"
        # Label must remain "Ethiopian" — that's what the popup heading
        # + the audit grouping rely on.
        assert kind.get("label") == "Ethiopian"


class TestGamma4Coverage:
    """The seed has the breadth the buyer-facing claim requires:
    Genesis + Psalms + John, at least one 1 Enoch entry, at least
    one Cyril entry, NPNF coverage spanning Ephrem + Cyril."""

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        cls.ec = sources.ethiopian_commentaries()

    def test_genesis_covered(self):
        # Generators span Gen 1-6 in the seed.
        found = False
        for chapter in range(1, 12):
            for verse in range(1, 50):
                if self.ec.for_verse("gen", chapter, verse):
                    found = True
                    break
            if found:
                break
        assert found, "seed has no Genesis entries"

    def test_psalms_covered(self):
        # Psalm 1 + 23 included.
        assert self.ec.for_verse("ps", 1, 1)
        assert self.ec.for_verse("ps", 23, 1)

    def test_john_covered(self):
        # John 1:1 + 1:14 + 19:34 included.
        assert self.ec.for_verse("joh", 1, 1)
        assert self.ec.for_verse("joh", 1, 14)
        assert self.ec.for_verse("joh", 19, 34)

    def test_1_enoch_distinctive_present(self):
        # Genesis 6:1 / 6:4 are the Watchers-tradition anchor points;
        # these are the buyer-facing "Tewahedo canon distinctive"
        # signals — pin one of them appears in the seed.
        any_enoch = self.ec.for_verse("gen", 6, 1) or self.ec.for_verse("gen", 6, 4)
        assert any_enoch


class TestGamma41CyrilJohn:
    """γ.4.1 — Cyril of Alexandria's Commentary on John (NPNF S2 V14)
    expansion. γ.4 shipped a 12-entry seed; γ.4.1 added 30 substantive
    Cyril-on-John entries covering chapters 1-4 (Logos prologue + John
    the Baptist + Cana + Temple cleansing + Nicodemus + Samaritan
    woman). Per `dev/SCOPE_2026-05-12-addendum-gamma-4-expansion.md`
    γ.4.1 scope, the target is ~400-600 entries; γ.4.1 (this ship) is
    the first wave (~30 entries), with γ.4.1.B-D extending to John
    5-21.

    Pins:
    - Cyril is now the heaviest single voice in the Ethiopian corpus.
    - Cyril-on-John coverage spans John 1-4 (and the existing 19:34).
    - Every new Cyril entry attribution mentions NPNF + Vol 14 +
      either Pusey or Randell (the PD translators, Oxford 1874-1885).
    - The buyer-facing Christological and pneumatological anchors
      (Jn 1:18 No-man-hath-seen-God, Jn 3:5 born-of-water-and-Spirit,
      Jn 3:16 God-so-loved, Jn 4:24 God-is-Spirit) are all present.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def test_cyril_is_heaviest_voice(self):
        # After γ.4.1.A + γ.4.1.B + γ.4.1.C, Cyril has many more entries
        # than any other single Father in the corpus. Cumulative wave:
        # γ.4.1.A 30 + γ.4.1.B 27 + γ.4.1.C 29 = +86 Cyril entries on top
        # of the original γ.4 seed.
        cyril = self.ec.by_father("Cyril of Alexandria")
        ephrem = self.ec.by_father("Ephrem the Syrian")
        assert len(cyril) >= 80, f"γ.4.1.A+B+C expansion expected ≥80 Cyril entries; found {len(cyril)}"
        assert len(cyril) > len(ephrem), (
            f"After γ.4.1.A+B+C Cyril ({len(cyril)}) should outweigh Ephrem ({len(ephrem)})"
        )

    def test_cyril_john_chapters_1_through_4_covered(self):
        # γ.4.1 wave 1 explicitly covers John 1-4.
        for chapter in (1, 2, 3, 4):
            cyril_in_chapter = []
            for verse in range(1, 100):
                cyril_in_chapter.extend(
                    e for e in self.ec.for_verse("joh", chapter, verse) if e.father == "Cyril of Alexandria"
                )
            assert len(cyril_in_chapter) >= 4, (
                f"γ.4.1 expected ≥4 Cyril entries in John {chapter}; found {len(cyril_in_chapter)}"
            )

    def test_cyril_logos_prologue_coverage(self):
        # John 1 prologue (1:1-18) is the Christological foundation.
        # Pin substantive Cyril coverage in the prologue verses.
        prologue_cyril = 0
        for verse in range(1, 19):
            prologue_cyril += sum(1 for e in self.ec.for_verse("joh", 1, verse) if e.father == "Cyril of Alexandria")
        assert prologue_cyril >= 6, f"γ.4.1 expected ≥6 Cyril entries in John 1:1-18 prologue; found {prologue_cyril}"

    def test_cyril_anti_arian_anchor_present(self):
        # John 1:3 ("all things made through Him") is Cyril's
        # signature anti-Arian Christological pin in his commentary.
        cyril_103 = [e for e in self.ec.for_verse("joh", 1, 3) if e.father == "Cyril of Alexandria"]
        assert cyril_103, "γ.4.1 missing Jn 1:3 — Cyril's anti-Arian Christological anchor"

    def test_cyril_no_man_hath_seen_god_present(self):
        # John 1:18 grounds Cyril's revelatory epistemology.
        cyril_118 = [e for e in self.ec.for_verse("joh", 1, 18) if e.father == "Cyril of Alexandria"]
        assert cyril_118, "γ.4.1 missing Jn 1:18 — Cyril's revelatory-epistemology anchor"

    def test_cyril_lamb_of_god_present(self):
        # John 1:29 is the typological sacrificial pivot.
        cyril_129 = [e for e in self.ec.for_verse("joh", 1, 29) if e.father == "Cyril of Alexandria"]
        assert cyril_129, "γ.4.1 missing Jn 1:29 — Lamb of God typological anchor"

    def test_cyril_baptismal_regeneration_anchor_present(self):
        # John 3:5 ("born of water and the Spirit") is the
        # Cyrilline sacramental-realism pin against spiritualizing
        # readings of baptism.
        cyril_305 = [e for e in self.ec.for_verse("joh", 3, 5) if e.father == "Cyril of Alexandria"]
        assert cyril_305, "γ.4.1 missing Jn 3:5 — baptismal regeneration anchor"

    def test_cyril_god_so_loved_present(self):
        # John 3:16 is the most-cited verse in the Gospel — its
        # Cyrilline reading anchors the Athanasian-Cappadocian
        # Trinitarian framework received by Tewahedo.
        cyril_316 = [e for e in self.ec.for_verse("joh", 3, 16) if e.father == "Cyril of Alexandria"]
        assert cyril_316, "γ.4.1 missing Jn 3:16 — Trinitarian-soteriological anchor"

    def test_cyril_god_is_spirit_present(self):
        # John 4:24 grounds the ontological-theological pin
        # ('God is Spirit') against Anthropomorphite readings.
        cyril_424 = [e for e in self.ec.for_verse("joh", 4, 24) if e.father == "Cyril of Alexandria"]
        assert cyril_424, "γ.4.1 missing Jn 4:24 — God-is-Spirit ontological anchor"

    def test_cyril_communicatio_idiomatum_anchor_present(self):
        # John 3:13 ("Son of man which is in heaven") is Cyril's
        # locus classicus for the communicatio idiomatum doctrine
        # that grounds Miaphysite Christology against Nestorian
        # dilution — load-bearing for Tewahedo Christology.
        cyril_313 = [e for e in self.ec.for_verse("joh", 3, 13) if e.father == "Cyril of Alexandria"]
        assert cyril_313, "γ.4.1 missing Jn 3:13 — communicatio idiomatum anchor"

    def test_every_gamma_4_1_attribution_cites_npnf_vol_14(self):
        # γ.4.1 entries (Cyril-on-John in chapters 1-4) must all cite
        # NPNF Series 2 Vol 14 + the explicit PD marker. The PD
        # translator chain (Pusey / Randell, Oxford 1874-1885) is
        # documented once in _meta.public_domain_basis rather than
        # repeated per-entry — see test_meta_documents_gamma_4_1_expansion.
        cyril_in_chs_1_to_4 = []
        for chapter in (1, 2, 3, 4):
            for verse in range(1, 100):
                cyril_in_chs_1_to_4.extend(
                    e for e in self.ec.for_verse("joh", chapter, verse) if e.father == "Cyril of Alexandria"
                )
        assert cyril_in_chs_1_to_4, "γ.4.1 expected Cyril entries in John 1-4"
        for entry in cyril_in_chs_1_to_4:
            attr = entry.attribution
            assert "NPNF" in attr, f"γ.4.1 entry missing NPNF citation: {attr!r}"
            assert "14" in attr, f"γ.4.1 entry missing Vol 14 citation: {attr!r}"
            assert "PD" in attr, f"γ.4.1 entry missing PD marker: {attr!r}"

    def test_meta_documents_gamma_4_1_expansion(self):
        # Pin: _meta scope block names γ.4.1 explicitly so a future
        # reviewer can identify which entries came from this wave.
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta = data["_meta"]
        assert "γ.4.1" in meta["scope"], "_meta scope block must name γ.4.1 expansion"
        assert "Pusey" in meta["public_domain_basis"] or "Randell" in meta["public_domain_basis"], (
            "_meta PD basis must document the Pusey/Randell PD translation"
        )


class TestGamma41BCyrilJohn5Through7:
    """γ.4.1.B — Cyril of Alexandria on John 5-7 expansion. Adds 27
    entries to the γ.4.1.A wave: Bethesda + discourse on the Son
    (John 5), Bread of Life discourse (John 6), Tabernacles + Living
    Water → Spirit (John 7). Per the addendum's γ.4.1 decomposition,
    γ.4.1.B targets ~20-30 entries; this ship lands 27.

    Pins:
    - John 5-7 chapter coverage present in addition to 1-4.
    - The five most-load-bearing doctrinal anchors:
      Jn 5:18 (equal-with-God), Jn 5:26 (life-in-Himself / eternal
      generation), Jn 6:35 (I-am-Bread-of-Life), Jn 6:51 (flesh-given-
      for-life-of-world), Jn 6:54 (medicine of immortality), Jn 6:63
      (Spirit-quickeneth vs capernaitic misreading), Jn 7:38-39
      (Living Water → Spirit's post-Pentecost gift).
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def test_cyril_john_chapters_5_through_7_covered(self):
        # γ.4.1.B explicitly covers John 5-7.
        for chapter in (5, 6, 7):
            cyril_in_chapter = []
            for verse in range(1, 100):
                cyril_in_chapter.extend(
                    e for e in self.ec.for_verse("joh", chapter, verse) if e.father == "Cyril of Alexandria"
                )
            assert len(cyril_in_chapter) >= 5, (
                f"γ.4.1.B expected ≥5 Cyril entries in John {chapter}; found {len(cyril_in_chapter)}"
            )

    def test_cyril_equal_with_god_present(self):
        # Jn 5:18 — the explicit Trinitarian-equality verse Cyril
        # uses against Arian dilution.
        cyril_518 = [e for e in self.ec.for_verse("joh", 5, 18) if e.father == "Cyril of Alexandria"]
        assert cyril_518, "γ.4.1.B missing Jn 5:18 — 'equal with God' anti-Arian anchor"

    def test_cyril_life_in_himself_present(self):
        # Jn 5:26 grounds Cyril's doctrine of eternal generation:
        # the Son has life in Himself as the Father has it.
        cyril_526 = [e for e in self.ec.for_verse("joh", 5, 26) if e.father == "Cyril of Alexandria"]
        assert cyril_526, "γ.4.1.B missing Jn 5:26 — eternal generation anchor"

    def test_cyril_bread_of_life_present(self):
        # Jn 6:35 — the first of Christ's great 'I am' sayings.
        cyril_635 = [e for e in self.ec.for_verse("joh", 6, 35) if e.father == "Cyril of Alexandria"]
        assert cyril_635, "γ.4.1.B missing Jn 6:35 — 'I am the bread of life' Christological pin"

    def test_cyril_flesh_for_life_of_world_present(self):
        # Jn 6:51 — central eucharistic-Christological text in the
        # entire Gospel of John per Cyril.
        cyril_651 = [e for e in self.ec.for_verse("joh", 6, 51) if e.father == "Cyril of Alexandria"]
        assert cyril_651, "γ.4.1.B missing Jn 6:51 — central eucharistic-Christological pin"

    def test_cyril_eucharistic_realism_present(self):
        # Jn 6:54 anchors the eucharistic medicine-of-immortality
        # doctrine that becomes determinative for Tewahedo Anaphora.
        cyril_654 = [e for e in self.ec.for_verse("joh", 6, 54) if e.father == "Cyril of Alexandria"]
        assert cyril_654, "γ.4.1.B missing Jn 6:54 — medicine-of-immortality pin"

    def test_cyril_spirit_quickeneth_present(self):
        # Jn 6:63 — Cyril's careful pneumatological qualification of
        # eucharistic realism against capernaitic misreading.
        cyril_663 = [e for e in self.ec.for_verse("joh", 6, 63) if e.father == "Cyril of Alexandria"]
        assert cyril_663, "γ.4.1.B missing Jn 6:63 — Spirit-quickeneth qualification pin"

    def test_cyril_living_water_present(self):
        # Jn 7:38 + 7:39 — Cyril's pneumatology of progressive
        # economy (Spirit fully given only after the glorification).
        cyril_738 = [e for e in self.ec.for_verse("joh", 7, 38) if e.father == "Cyril of Alexandria"]
        cyril_739 = [e for e in self.ec.for_verse("joh", 7, 39) if e.father == "Cyril of Alexandria"]
        assert cyril_738, "γ.4.1.B missing Jn 7:38 — Living Water → rivers"
        assert cyril_739, "γ.4.1.B missing Jn 7:39 — Spirit's post-Pentecost gift anchor"

    def test_meta_documents_gamma_4_1_b_expansion(self):
        # Pin: _meta scope block names γ.4.1.B explicitly so a future
        # reviewer can identify which entries came from this wave.
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta = data["_meta"]
        assert "γ.4.1.B" in meta["source"] or "γ.4.1.B" in meta["scope"], (
            "_meta must name γ.4.1.B expansion in source or scope"
        )

    def test_every_gamma_4_1_b_attribution_cites_npnf_vol_14(self):
        # γ.4.1.B entries (Cyril-on-John in chapters 5-7) must all
        # cite NPNF Series 2 Vol 14 + explicit PD marker.
        cyril_in_chs_5_to_7 = []
        for chapter in (5, 6, 7):
            for verse in range(1, 100):
                cyril_in_chs_5_to_7.extend(
                    e for e in self.ec.for_verse("joh", chapter, verse) if e.father == "Cyril of Alexandria"
                )
        assert cyril_in_chs_5_to_7, "γ.4.1.B expected Cyril entries in John 5-7"
        for entry in cyril_in_chs_5_to_7:
            attr = entry.attribution
            assert "NPNF" in attr, f"γ.4.1.B entry missing NPNF citation: {attr!r}"
            assert "14" in attr, f"γ.4.1.B entry missing Vol 14 citation: {attr!r}"
            assert "PD" in attr, f"γ.4.1.B entry missing PD marker: {attr!r}"


class TestGamma41CCyrilJohn11Through14:
    """γ.4.1.C — Cyril of Alexandria on John 11-14 (29 entries). Covers
    the Lazarus pericope (John 11), the anointing/triumphal entry/
    cosmic-judgment cluster (John 12), the foot-washing + Last Supper
    + new commandment (John 13), and the Farewell Discourse I including
    the Trinitarian perichoresis texts + the first Paraclete promise
    (John 14). Per the addendum's γ.4.1 decomposition, γ.4.1.C targets
    ~30-40 entries; this ship lands 29.

    Note: Cyril's Books VII-VIII covering John 8-10 are LOST in the
    manuscript tradition; no Cyril coverage possible for those chapters
    (a future Ephrem-on-John or Andəmta-on-John phase could fill the
    gap).

    Pins:
    - John 11-14 chapter coverage present in addition to 1-7 + 19.
    - The most-load-bearing doctrinal anchors of this wave:
      Jn 11:25 (I-am-the-resurrection — fifth 'I AM'),
      Jn 11:35 (Jesus-wept — Cyril's Miaphysite anti-Apollinarian pin),
      Jn 12:24 (grain-of-wheat — redemptive-suffering theology),
      Jn 12:31 (prince-cast-out — Christus-victor cosmic dimension),
      Jn 13:34 (new-commandment — Christological measure of love),
      Jn 14:6 (Way-Truth-Life — most exhaustive Christological pin),
      Jn 14:9 (seen-me=seen-Father — anti-Sabellian + anti-Arian),
      Jn 14:10 (mutual indwelling — perichoresis foundation),
      Jn 14:16 + 14:17 (Paraclete promise — pneumatology),
      Jn 14:28 (Father-greater — the most-contested Arian polemical
      verse, requiring careful Cyrilline distinction).
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def test_cyril_john_chapters_11_through_14_covered(self):
        # γ.4.1.C explicitly covers John 11-14 (8-10 lost in manuscript).
        for chapter in (11, 12, 13, 14):
            cyril_in_chapter = []
            for verse in range(1, 100):
                cyril_in_chapter.extend(
                    e for e in self.ec.for_verse("joh", chapter, verse) if e.father == "Cyril of Alexandria"
                )
            assert len(cyril_in_chapter) >= 5, (
                f"γ.4.1.C expected ≥5 Cyril entries in John {chapter}; found {len(cyril_in_chapter)}"
            )

    def test_no_coverage_in_lost_chapters_8_through_10(self):
        # Cyril's Books VII-VIII on Jn 8-10 are LOST. This pin guards
        # against accidental fabrication of "Cyril on John 8-10"
        # entries — they would be unsourceable.
        for chapter in (8, 9, 10):
            for verse in range(1, 100):
                cyril_here = [e for e in self.ec.for_verse("joh", chapter, verse) if e.father == "Cyril of Alexandria"]
                assert not cyril_here, (
                    f"Cyril on John {chapter}:{verse} found, but Books VII-VIII are LOST — must not have content here"
                )

    def test_cyril_i_am_resurrection_present(self):
        # Jn 11:25 — fifth of Christ's 'I AM' sayings, the ontological
        # resurrection-Christology pin.
        cyril_1125 = [e for e in self.ec.for_verse("joh", 11, 25) if e.father == "Cyril of Alexandria"]
        assert cyril_1125, "γ.4.1.C missing Jn 11:25 — 'I am the resurrection' Christological pin"

    def test_cyril_jesus_wept_miaphysite_pin_present(self):
        # Jn 11:35 — Cyril's most extended treatment of Christ's true
        # human affections without compromising divine impassibility.
        # This is the Miaphysite anti-Apollinarian / anti-Docetist /
        # anti-Stoic-projection pin all in one verse.
        cyril_1135 = [e for e in self.ec.for_verse("joh", 11, 35) if e.father == "Cyril of Alexandria"]
        assert cyril_1135, "γ.4.1.C missing Jn 11:35 — Miaphysite Christology pin (Jesus wept)"

    def test_cyril_grain_of_wheat_present(self):
        # Jn 12:24 — redemptive-suffering theology root.
        cyril_1224 = [e for e in self.ec.for_verse("joh", 12, 24) if e.father == "Cyril of Alexandria"]
        assert cyril_1224, "γ.4.1.C missing Jn 12:24 — grain-of-wheat redemptive pin"

    def test_cyril_prince_cast_out_present(self):
        # Jn 12:31 — Christus-victor cosmic dimension of the cross.
        cyril_1231 = [e for e in self.ec.for_verse("joh", 12, 31) if e.father == "Cyril of Alexandria"]
        assert cyril_1231, "γ.4.1.C missing Jn 12:31 — prince-of-world cast out (Christus victor)"

    def test_cyril_new_commandment_present(self):
        # Jn 13:34 — Christological measure of love grounding Cyril's
        # ecclesiology of love-community.
        cyril_1334 = [e for e in self.ec.for_verse("joh", 13, 34) if e.father == "Cyril of Alexandria"]
        assert cyril_1334, "γ.4.1.C missing Jn 13:34 — new commandment of love"

    def test_cyril_way_truth_life_present(self):
        # Jn 14:6 — the most exhaustive single-verse Christological
        # self-disclosure; textual root of Christological exclusivism.
        cyril_146 = [e for e in self.ec.for_verse("joh", 14, 6) if e.father == "Cyril of Alexandria"]
        assert cyril_146, "γ.4.1.C missing Jn 14:6 — Way/Truth/Life Christological pin"

    def test_cyril_seen_me_seen_father_present(self):
        # Jn 14:9 — anti-Sabellian + anti-Arian double-pin grounding
        # the Tewahedo iconographic tradition.
        cyril_149 = [e for e in self.ec.for_verse("joh", 14, 9) if e.father == "Cyril of Alexandria"]
        assert cyril_149, "γ.4.1.C missing Jn 14:9 — 'seen me = seen Father' Trinitarian pin"

    def test_cyril_mutual_indwelling_perichoresis_present(self):
        # Jn 14:10 — the Trinitarian perichoresis textual foundation.
        cyril_1410 = [e for e in self.ec.for_verse("joh", 14, 10) if e.father == "Cyril of Alexandria"]
        assert cyril_1410, "γ.4.1.C missing Jn 14:10 — perichoresis foundational pin"

    def test_cyril_paraclete_promise_present(self):
        # Jn 14:16 + 14:17 — the first Paraclete promise, principal
        # Johannine pin for Spirit's personal divinity.
        cyril_1416 = [e for e in self.ec.for_verse("joh", 14, 16) if e.father == "Cyril of Alexandria"]
        cyril_1417 = [e for e in self.ec.for_verse("joh", 14, 17) if e.father == "Cyril of Alexandria"]
        assert cyril_1416, "γ.4.1.C missing Jn 14:16 — Paraclete promise (allon Paraklēton)"
        assert cyril_1417, "γ.4.1.C missing Jn 14:17 — Spirit of truth"

    def test_cyril_father_greater_arian_polemical_present(self):
        # Jn 14:28 — THE most-contested Arian polemical verse in
        # Cyril's John commentary. Required Cyrilline orthodox
        # distinction between the assumed humanity (with respect to
        # which the Father is 'greater') and the eternal divine
        # nature (in which the Son is consubstantial-equal).
        cyril_1428 = [e for e in self.ec.for_verse("joh", 14, 28) if e.father == "Cyril of Alexandria"]
        assert cyril_1428, "γ.4.1.C missing Jn 14:28 — 'Father greater' anti-Arian polemical pin"

    def test_meta_documents_gamma_4_1_c_expansion(self):
        # Pin: _meta scope block names γ.4.1.C explicitly so a future
        # reviewer can identify which entries came from this wave.
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta = data["_meta"]
        assert "γ.4.1.C" in meta["source"] or "γ.4.1.C" in meta["scope"], (
            "_meta must name γ.4.1.C expansion in source or scope"
        )

    def test_every_gamma_4_1_c_attribution_cites_npnf_vol_14(self):
        # γ.4.1.C entries (Cyril-on-John in chapters 11-14) must all
        # cite NPNF Series 2 Vol 14 + explicit PD marker.
        cyril_in_chs_11_to_14 = []
        for chapter in (11, 12, 13, 14):
            for verse in range(1, 100):
                cyril_in_chs_11_to_14.extend(
                    e for e in self.ec.for_verse("joh", chapter, verse) if e.father == "Cyril of Alexandria"
                )
        assert cyril_in_chs_11_to_14, "γ.4.1.C expected Cyril entries in John 11-14"
        for entry in cyril_in_chs_11_to_14:
            attr = entry.attribution
            assert "NPNF" in attr, f"γ.4.1.C entry missing NPNF citation: {attr!r}"
            assert "14" in attr, f"γ.4.1.C entry missing Vol 14 citation: {attr!r}"
            assert "PD" in attr, f"γ.4.1.C entry missing PD marker: {attr!r}"
