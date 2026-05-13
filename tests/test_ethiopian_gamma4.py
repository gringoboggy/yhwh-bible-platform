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
        # Pin: every entry's attribution cites one of the project's
        # canonical PD translation anchors, and carries the explicit
        # "PD" marker. Accepted anchors:
        #   - "NPNF" — Schaff's NPNF series (anchors Ephrem on Genesis +
        #     Cyril on John).
        #   - "Charles" — R.H. Charles (1912 1 Enoch + 1902 Jubilees).
        #   - "Payne Smith" — R. Payne Smith's 1859 Oxford translation
        #     of Cyril's Commentary on Luke from Syriac (the Greek
        #     original is lost except for catena fragments; Payne Smith
        #     d. 1895, well before 1929). Added γ.4.3.
        pd_anchors = ("NPNF", "Charles", "Payne Smith")
        for entry in self.data["entries"]:
            attr = entry["attribution"]
            assert any(a in attr for a in pd_anchors), f"entry not attributed to any PD anchor {pd_anchors}: {attr!r}"
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


class TestOmega37CrossCanonCommentaryPin:
    """ω.37 (W7 closure) — pin the intentional cross-canon commentary.

    The 2026-05-12-C audit's W7 flagged a count mismatch: 192 entries
    with `father = "1 Enoch (Ethiopian tradition)"` vs only 190 entries
    with `book = "1en"`. Investigation showed the 2 stray entries are
    intentional: 1 Enoch commentary on Gen 6:1 + Gen 6:4 (the sons-of-
    God / nephilim passage that the Watchers narrative in 1En 6-11
    canonically expands). These belong as commentary on both texts —
    Tewahedo readers cross-reference between Gen 6 and 1En 6-11 as
    a single narrative arc.

    This class pins that cross-link to detect regression (someone
    'cleans up' the apparent inconsistency by removing the entries).
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        cls.ec = sources.ethiopian_commentaries()

    def test_enoch_voice_on_genesis_6_1_present(self):
        # 1En 6-11 expands Gen 6:1's "sons of God came in to the
        # daughters of men" as the descent of the Watchers under
        # Šemiḥazah. Tewahedo reading takes the two passages as one
        # narrative.
        entries = [e for e in self.ec.for_verse("gen", 6, 1) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert entries, "ω.37 W7 pin: expected 1 Enoch voice on Gen 6:1 (Watchers descent anchor)"

    def test_enoch_voice_on_genesis_6_4_present(self):
        # 1En 7:2 + 15:8 expand Gen 6:4's "nephilim" / "mighty men"
        # as the giants begotten of the Watcher-women union; their
        # post-flood spirits become the demons (15:8). Tewahedo
        # demonology canonically anchors here.
        entries = [e for e in self.ec.for_verse("gen", 6, 4) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert entries, "ω.37 W7 pin: expected 1 Enoch voice on Gen 6:4 (nephilim / giants anchor)"

    def test_only_intentional_cross_canon_pattern_is_enoch_on_genesis(self):
        # The corpus has EXACTLY ONE cross-canon commentary pattern
        # currently: 1 Enoch commenting on Genesis 6:1 + 6:4.
        # If a future content wave adds another (e.g., Jubilees
        # commentary on Genesis or vice versa), the test will fail
        # and the new pattern must be deliberately added here.
        import json
        from pathlib import Path

        path = Path(__file__).resolve().parent.parent / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        unexpected = []
        for entry in data["entries"]:
            book = entry.get("book", "")
            father = entry.get("father", "")
            father_is_enoch = father.startswith("1 Enoch")
            father_is_jub = father.startswith("Book of Jubilees")
            book_is_enoch = book == "1en"
            book_is_jub = book == "jub"
            # Allowed pattern: 1 Enoch voice on `gen` (the W7 pin).
            # Everything else where tradition doesn't match book code
            # is unexpected.
            if (father_is_enoch and not book_is_enoch) or (father_is_jub and not book_is_jub):
                allowed = father_is_enoch and book == "gen"
                if not allowed:
                    unexpected.append((book, entry.get("chapter"), entry.get("verse"), father))
        assert not unexpected, (
            f"ω.37 W7 pin: unexpected cross-canon entries (only 1 Enoch on Gen is allowed): {unexpected}"
        )


class TestGamma4MetaPhasesCoverage:
    """ω.37 (W10 closure) — _meta scope/source must name every shipped
    γ.4.x sub-phase. The audit flagged the absence of these pins as a
    drift risk: if a future content wave forgets to update _meta along
    with shipping entries, ATTRIBUTIONS and audit-trail readers will
    see stale metadata while the entries-by-count grows underneath.

    Pattern modeled on `test_meta_documents_gamma_4_4_expansion` at
    `TestGamma44EnochFirstWave:test_meta_documents_gamma_4_4_expansion`.
    Each test asserts the phase tag appears in _meta source or scope
    with a regex word boundary so γ.4.4 doesn't match γ.4.4.B.
    """

    @classmethod
    def setup_class(cls):
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta = data["_meta"]
        cls.meta_text = meta.get("source", "") + " " + meta.get("scope", "")

    def _assert_phase_mentioned(self, phase: str) -> None:
        import re

        # Negative lookahead prevents γ.4.4 from matching γ.4.4.B etc.
        pattern = re.escape(phase) + r"(?![.A-Z])"
        assert re.search(pattern, self.meta_text), f"_meta must name phase {phase} in source or scope"

    def test_meta_documents_gamma_4_4_b(self):
        self._assert_phase_mentioned("γ.4.4.B")

    def test_meta_documents_gamma_4_4_c(self):
        self._assert_phase_mentioned("γ.4.4.C")

    def test_meta_documents_gamma_4_4_d(self):
        self._assert_phase_mentioned("γ.4.4.D")

    def test_meta_documents_gamma_4_4_e(self):
        self._assert_phase_mentioned("γ.4.4.E")

    def test_meta_documents_gamma_4_5(self):
        self._assert_phase_mentioned("γ.4.5")

    def test_meta_documents_gamma_4_5_b(self):
        self._assert_phase_mentioned("γ.4.5.B")

    def test_meta_documents_gamma_4_5_c(self):
        self._assert_phase_mentioned("γ.4.5.C")

    def test_meta_documents_gamma_4_5_d(self):
        self._assert_phase_mentioned("γ.4.5.D")

    def test_meta_documents_gamma_4_5_e(self):
        self._assert_phase_mentioned("γ.4.5.E")


class TestOmega37W11JubileesBuildPipelineIntegration:
    """ω.37 (W11 closure) — build-pipeline integration test for
    Jubilees commentary.

    The 2026-05-12-C audit's W11 flagged that no test verified
    Jubilees entries flowing through the detector → candidate →
    comm-ethiopian-kind path that the build pipeline consumes.
    γ.4.5 + .B/.C/.D/.E shipped 200 Jubilees entries; this class
    pins that the **canonical demo anchor** (jub 6:32 — the
    Tewahedo Bāḥrä Ḥasab 364-day-liturgical-year canonical anchor)
    flows through the full pipeline as `comm-ethiopian` content.

    The 364-day calendar (Mäḥǝbär Ḥaddis) is preserved liturgically
    in the Tewahedo Church and is the canonical-OT antecedent for
    Tewahedo Bāḥrä Ḥasab (Sea of Reckoning) computus. Doubled
    canonical anchor with 1En 72:32. If a build-filter regression
    silently dropped Jubilees commentary, this anchor would be the
    most demo-visible casualty.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()

    def test_jub_6_32_produces_jubilees_candidate(self):
        # The detector must produce at least one Candidate at
        # jub 6:32, and the Candidate's father must be Jubilees
        # (NOT 1 Enoch, even though 1En 72:32 is the doubled anchor —
        # 1 Enoch lives under book='1en', Jubilees under book='jub').
        from scripts.core import detectors

        d = detectors.EthiopianCommentaryDetector()
        candidates = d.detect("jub", 6, 32, "")
        assert candidates, (
            "ω.37 W11 pin: jub 6:32 must produce a comm-ethiopian candidate (Bāḥrä Ḥasab canonical anchor)"
        )
        jubilees = [c for c in candidates if "Jubilees" in c.source_name]
        assert jubilees, (
            f"ω.37 W11 pin: jub 6:32 must include a Jubilees voice; "
            f"got sources: {[c.source_name for c in candidates]!r}"
        )

    def test_jub_6_32_candidate_kind_is_comm_ethiopian(self):
        # The kind code is what the build-pipeline filter keys on.
        # If this becomes anything other than "comm-ethiopian",
        # editions with `comm-ethiopian` in enabled_kinds will
        # silently drop Jubilees.
        from scripts.core import detectors

        d = detectors.EthiopianCommentaryDetector()
        candidates = d.detect("jub", 6, 32, "")
        for c in candidates:
            assert c.kind == "comm-ethiopian", (
                f"ω.37 W11 pin: jub 6:32 candidate kind must be 'comm-ethiopian'; got {c.kind!r}"
            )

    def test_jub_6_32_attribution_carries_charles_pd_marker(self):
        # The build pipeline emits the attribution into the EPUB's
        # source-citation footer. The full chain (Charles 1902,
        # Oxford Clarendon, PD) must round-trip from the JSON
        # _meta.public_domain_basis through detector.attribution.
        from scripts.core import detectors

        d = detectors.EthiopianCommentaryDetector()
        candidates = d.detect("jub", 6, 32, "")
        jubilees = [c for c in candidates if "Jubilees" in c.source_name]
        assert jubilees, "no Jubilees voice on jub 6:32"
        c = jubilees[0]
        attr = c.source_attribution
        assert "Charles" in attr, f"ω.37 W11 pin: Jubilees citation must include Charles translator name; got {attr!r}"
        assert "1902" in attr, f"ω.37 W11 pin: Jubilees citation must include 1902 publication date; got {attr!r}"
        assert "PD" in attr, f"ω.37 W11 pin: Jubilees citation must include PD marker; got {attr!r}"

    def test_jub_6_32_body_html_contains_bahra_hasab_marker(self):
        # The Candidate's draft_body is the actual aside HTML that
        # the EPUB renders. The Bāḥrä-Ḥasab-anchor summary text
        # mentions the 364-day liturgical year — verify that survives
        # the html-escape round-trip (any escaping regression that
        # mangled the summary would show up here).
        from scripts.core import detectors

        d = detectors.EthiopianCommentaryDetector()
        candidates = d.detect("jub", 6, 32, "")
        jubilees = [c for c in candidates if "Jubilees" in c.source_name]
        assert jubilees, "no Jubilees voice on jub 6:32"
        body = jubilees[0].draft_body
        # The body must be the aside wrapper used by all comm-* kinds
        # so it flows through filter_html identically to other voices.
        assert "<aside" in body, "draft_body should be aside-wrapped"
        assert "note-comm-ethiopian" in body, "draft_body must carry the note-comm-ethiopian CSS class"
        # Bāḥrä Ḥasab is the canonical Tewahedo-Ge'ez liturgical
        # computus phrase; the 364-day calendar discussion in Jub 6:32
        # is its scriptural anchor. Either the phrase OR the "364"
        # numeric anchor must survive the html-escape pass.
        assert ("Bāḥrä" in body) or ("364" in body), (
            f"ω.37 W11 pin: Jub 6:32 body should reference Bāḥrä Ḥasab OR the 364-day calendar; got: {body[:200]!r}"
        )


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
        # After γ.4.1.A + γ.4.1.B + γ.4.1.C + γ.4.1.D, Cyril has many
        # more entries than any other single Father in the corpus.
        # Cumulative wave: γ.4.1.A 30 + γ.4.1.B 27 + γ.4.1.C 29 + γ.4.1.D
        # 30 = +116 Cyril entries on top of the original γ.4 seed (5).
        cyril = self.ec.by_father("Cyril of Alexandria")
        ephrem = self.ec.by_father("Ephrem the Syrian")
        assert len(cyril) >= 115, f"γ.4.1.A+B+C+D expansion expected ≥115 Cyril entries; found {len(cyril)}"
        assert len(cyril) > len(ephrem), (
            f"After γ.4.1.A+B+C+D Cyril ({len(cyril)}) should outweigh Ephrem ({len(ephrem)})"
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


class TestGamma42EphremGenesisFirstWave:
    """γ.4.2 — Ephrem the Syrian on Genesis (first wave, 32 entries
    covering Gen 1-11). Per AUDIT_2026-05-12-B §ix recommendation,
    γ.4.2 first wave was sequenced BEFORE γ.4.1.D to rebalance the
    corpus voice mix from 93% Cyril (after γ.4.1.C) toward the
    documented dual-anchor (Syriac + Alexandrian) claim. Post-this-
    wave voice distribution: Cyril 91 (70%) / Ephrem 37 (28%) /
    1 Enoch 2 (2%) — substantively closer to the _meta scope's
    documented four-anchor framework.

    Sourced from NPNF Series 2 Vol 13 (Gwynn/Schaff translation,
    Oxford 1898 — both translators died well before 1929 PD cutoff).
    Per the addendum γ.4.2 target ~200-300 entries; this first wave
    lands 32 covering the primeval history (Gen 1-11). Future
    γ.4.2.B-D will extend through Exodus / Numbers / Deuteronomy.

    Pins:
    - Ephrem-on-Genesis chapter coverage (Gen 1-11).
    - Voice rebalance: Cyril share drops below 80%.
    - Ephrem is now substantively present (≥30 entries).
    - The signature Ephremic-Syriac patristic readings:
      Gen 1:26 (Trinitarian council reading; image/likeness
      distinction), Gen 2:21 (Adam's sleep prefigures Christ's
      death; Eve from rib prefigures Church from pierced side),
      Gen 3:15 (protoevangelium — Syriac patristic basis),
      Gen 5:24 (Enoch translated — anchor for Mäṣḥafä Hēnok),
      Gen 6:14 (ark prefigures Church + cross),
      Gen 9:13 (rainbow as covenantal-bow sheathed),
      Gen 11:9 (Babel-Pentecost typological inverse).
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def test_ephrem_now_substantively_present(self):
        # Post-γ.4.2 wave-1: Ephrem should be substantively present
        # (≥30 entries), not just the 5-entry γ.4 seed presence.
        ephrem = self.ec.by_father("Ephrem the Syrian")
        assert len(ephrem) >= 30, f"γ.4.2 wave-1 expected ≥30 Ephrem entries; found {len(ephrem)}"

    def test_voice_rebalance_achieved(self):
        # Per AUDIT_2026-05-12-B §ix recommendation: γ.4.2 first wave
        # was sequenced specifically to rebalance the corpus voice mix
        # away from 93% Cyril dominance. Pin Cyril share now below 80%.
        cyril = self.ec.by_father("Cyril of Alexandria")
        total = len(self.ec)
        cyril_share = len(cyril) / total
        assert cyril_share < 0.80, (
            f"γ.4.2 wave-1 should rebalance Cyril share below 80%; actual {cyril_share:.1%} ({len(cyril)} of {total})"
        )

    def test_ephrem_genesis_chapter_coverage(self):
        # γ.4.2 wave-1 explicitly covers Gen 1-11 (creation through
        # Babel). Pin at least 4 chapters of substantive coverage.
        chapters_covered = set()
        for chapter in range(1, 12):
            for verse in range(1, 100):
                ephrem_here = [e for e in self.ec.for_verse("gen", chapter, verse) if e.father == "Ephrem the Syrian"]
                if ephrem_here:
                    chapters_covered.add(chapter)
        assert len(chapters_covered) >= 8, (
            f"γ.4.2 wave-1 expected ≥8 Genesis chapters covered by Ephrem; found {sorted(chapters_covered)}"
        )

    def test_ephrem_image_and_likeness_present(self):
        # Gen 1:26 — Ephrem's Trinitarian-council reading + image/
        # likeness distinction (foundational for Tewahedo theosis).
        ephrem_126 = [e for e in self.ec.for_verse("gen", 1, 26) if e.father == "Ephrem the Syrian"]
        assert ephrem_126, "γ.4.2 missing Gen 1:26 — image/likeness anchor"

    def test_ephrem_adam_sleep_typology_present(self):
        # Gen 2:21 — Adam's sleep prefigures Christ's death; Eve from
        # rib prefigures Church from pierced side. Foundational Adam-
        # Christ + Eve-Church typology for Tewahedo ecclesiology.
        ephrem_221 = [e for e in self.ec.for_verse("gen", 2, 21) if e.father == "Ephrem the Syrian"]
        assert ephrem_221, "γ.4.2 missing Gen 2:21 — Adam-Christ Eve-Church typology"

    def test_ephrem_protoevangelium_present(self):
        # Gen 3:15 — Syriac patristic basis for early Christological
        # reading of Genesis. Distinct from but complementary to
        # χ.2 (Henry) + χ.3 (Calvin) protoevangelium readings.
        ephrem_315 = [e for e in self.ec.for_verse("gen", 3, 15) if e.father == "Ephrem the Syrian"]
        assert ephrem_315, "γ.4.2 missing Gen 3:15 — Syriac protoevangelium pin"

    def test_ephrem_enoch_translation_present(self):
        # Gen 5:24 — Enoch translated; foundational anchor for the
        # Mäṣḥafä Hēnok (Book of Enoch) that Tewahedo uniquely
        # canonizes. Load-bearing for the v1.x uniqueness angle.
        ephrem_524 = [e for e in self.ec.for_verse("gen", 5, 24) if e.father == "Ephrem the Syrian"]
        assert ephrem_524, "γ.4.2 missing Gen 5:24 — Enoch translation (Mäṣḥafä Hēnok anchor)"

    def test_ephrem_ark_prefigures_church_present(self):
        # Gen 6:14 — ark prefigures Church + cross. Tewahedo
        # Anaphora of Athanasius preserves this typological cluster
        # prominently.
        ephrem_614 = [e for e in self.ec.for_verse("gen", 6, 14) if e.father == "Ephrem the Syrian"]
        assert ephrem_614, "γ.4.2 missing Gen 6:14 — ark-Church typology"

    def test_ephrem_rainbow_covenant_present(self):
        # Gen 9:13 — rainbow as warrior's bow set down in covenantal
        # pledge; Syriac patristic reading that mercy has the last word.
        ephrem_913 = [e for e in self.ec.for_verse("gen", 9, 13) if e.father == "Ephrem the Syrian"]
        assert ephrem_913, "γ.4.2 missing Gen 9:13 — rainbow-bow covenantal pin"

    def test_ephrem_babel_typology_present(self):
        # Gen 11:9 — Babel as inverse of Pentecost; foundation of
        # Syriac patristic anti-Promethean theology of language.
        ephrem_119 = [e for e in self.ec.for_verse("gen", 11, 9) if e.father == "Ephrem the Syrian"]
        assert ephrem_119, "γ.4.2 missing Gen 11:9 — Babel-Pentecost typological inverse"

    def test_meta_documents_gamma_4_2_expansion(self):
        # Pin: _meta scope/source block names γ.4.2 explicitly.
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta = data["_meta"]
        assert "γ.4.2" in meta["source"] or "γ.4.2" in meta["scope"], (
            "_meta must name γ.4.2 expansion in source or scope"
        )

    def test_every_gamma_4_2_attribution_cites_npnf_vol_13(self):
        # γ.4.2 entries (Ephrem-on-Genesis in chapters 1-11) must all
        # cite NPNF Series 2 Vol 13 + explicit PD marker.
        ephrem_in_chs_1_to_11 = []
        for chapter in range(1, 12):
            for verse in range(1, 100):
                ephrem_in_chs_1_to_11.extend(
                    e for e in self.ec.for_verse("gen", chapter, verse) if e.father == "Ephrem the Syrian"
                )
        assert ephrem_in_chs_1_to_11, "γ.4.2 expected Ephrem entries in Gen 1-11"
        # The γ.4 SEED includes some Ephrem-Gen entries (1:1, 1:3, 2:7,
        # 3:1) with a different attribution format ("NPNF Series 2,
        # vol. 13"). γ.4.2 wave-1 uses the abbreviated "NPNF S2 V13"
        # form. Both contain "NPNF" + "13" + "PD".
        for entry in ephrem_in_chs_1_to_11:
            attr = entry.attribution
            assert "NPNF" in attr, f"γ.4.2 entry missing NPNF citation: {attr!r}"
            assert "13" in attr, f"γ.4.2 entry missing Vol 13 citation: {attr!r}"
            assert "PD" in attr, f"γ.4.2 entry missing PD marker: {attr!r}"


class TestGamma41DCyrilJohn15Through21:
    """γ.4.1.D — Cyril of Alexandria on John 15-21 (30 entries).
    CLOSES γ.4.1 modulo the unfillable Jn 8-10 manuscript gap (Cyril's
    Books VII-VIII LOST). Covers the Vine discourse (John 15) + further
    Paraclete promises + sorrow-turned-to-joy (John 16) + the High-
    Priestly Prayer (John 17) + Garden of Gethsemane + arrest + trial
    before Pilate (John 18) + Passion + tetelestai (John 19) +
    Resurrection appearances + breathing of Holy Ghost (John 20) +
    restoration of Peter / Feed-my-sheep (John 21).

    γ.4.1 cumulative wave-totals: A 30 + B 27 + C 29 + D 30 = 116
    Cyril-on-John entries beyond the γ.4 seed of 3 Cyril-on-John.

    Pins:
    - John 15-21 chapter coverage; full Cyrilline John (1-7 + 11-21).
    - Vine + branches anchor (15:1, 15:5 — ecclesial vital-union).
    - Paraclete + pneumatology (15:26 eternal procession;
      16:7 expedient-I-go-away; 16:13 guide-into-all-truth).
    - High-Priestly Prayer (17:3 eternal-life-is-knowing;
      17:5 glory-before-world; 17:21 that-they-all-may-be-one;
      17:24 behold-my-glory).
    - Trinitarian-equality (18:6 ego-eimi-theophany);
    - Christological (18:36 kingdom-not-of-this-world;
      19:30 tetelestai-completed-work).
    - Resurrection + commissioning (20:17 my-Father-and-your-Father;
      20:22 Receive-ye-the-Holy-Ghost; 20:29 blessed-not-seen-yet-believed).
    - Pastoral commission (21:15-17 lovest-thou-me + Feed-my-sheep).
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def test_cyril_john_chapters_15_through_21_covered(self):
        # γ.4.1.D explicitly covers John 15-21.
        for chapter in (15, 16, 17, 18, 19, 20, 21):
            cyril_in_chapter = []
            for verse in range(1, 100):
                cyril_in_chapter.extend(
                    e for e in self.ec.for_verse("joh", chapter, verse) if e.father == "Cyril of Alexandria"
                )
            assert len(cyril_in_chapter) >= 2, (
                f"γ.4.1.D expected ≥2 Cyril entries in John {chapter}; found {len(cyril_in_chapter)}"
            )

    def test_gamma_4_1_now_closed_modulo_jn_8_10_gap(self):
        # γ.4.1 is now CLOSED: Cyril coverage spans the full Gospel
        # of John (Jn 1-7 from γ.4.1.A/B + Jn 11-14 from γ.4.1.C +
        # Jn 15-21 from γ.4.1.D + Jn 19:34 from γ.4 seed). Pin all
        # extant John chapters present except 8-10 (manuscript gap).
        cyril_on_john = [e for e in self.ec.by_father("Cyril of Alexandria") if e.book == "joh"]
        chapters = {e.chapter for e in cyril_on_john}
        expected_present = {1, 2, 3, 4, 5, 6, 7, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21}
        missing = expected_present - chapters
        assert not missing, f"γ.4.1.D should close γ.4.1 except for Jn 8-10; missing chapters: {missing}"

    def test_cyril_vine_present(self):
        # Jn 15:1 — sixth 'I AM' saying; ecclesial vital-union pin.
        cyril_151 = [e for e in self.ec.for_verse("joh", 15, 1) if e.father == "Cyril of Alexandria"]
        assert cyril_151, "γ.4.1.D missing Jn 15:1 — 'I am the true vine'"

    def test_cyril_greater_love_present(self):
        # Jn 15:13 — cross as visible measure of divine love.
        cyril_1513 = [e for e in self.ec.for_verse("joh", 15, 13) if e.father == "Cyril of Alexandria"]
        assert cyril_1513, "γ.4.1.D missing Jn 15:13 — greater love"

    def test_cyril_eternal_procession_present(self):
        # Jn 15:26 — Eastern Orthodox foundation for eternal procession
        # from the Father (Cyrilline reading distinguishing eternal
        # procession from temporal mission — pre-Filioque grounding).
        cyril_1526 = [e for e in self.ec.for_verse("joh", 15, 26) if e.father == "Cyril of Alexandria"]
        assert cyril_1526, "γ.4.1.D missing Jn 15:26 — Spirit's eternal procession"

    def test_cyril_expedient_i_go_away_present(self):
        # Jn 16:7 — pneumatology of progressive economy; Ascension as
        # precondition for Spirit's coming.
        cyril_167 = [e for e in self.ec.for_verse("joh", 16, 7) if e.father == "Cyril of Alexandria"]
        assert cyril_167, "γ.4.1.D missing Jn 16:7 — expedient-I-go-away"

    def test_cyril_eternal_life_is_knowing_present(self):
        # Jn 17:3 — definition of eternal life as participation-by-
        # knowing the only true God + Jesus Christ.
        cyril_173 = [e for e in self.ec.for_verse("joh", 17, 3) if e.father == "Cyril of Alexandria"]
        assert cyril_173, "γ.4.1.D missing Jn 17:3 — eternal life as knowing"

    def test_cyril_glory_before_world_was_present(self):
        # Jn 17:5 — Cyril's strongest single-verse text for the
        # Son's eternal pre-existence; used heavily in Twelve Anathemas.
        cyril_175 = [e for e in self.ec.for_verse("joh", 17, 5) if e.father == "Cyril of Alexandria"]
        assert cyril_175, "γ.4.1.D missing Jn 17:5 — glory before world was"

    def test_cyril_that_they_all_may_be_one_present(self):
        # Jn 17:21 — THE ecclesiological text of the Gospel; ecclesial
        # unity grounded in Trinitarian perichoresis.
        cyril_1721 = [e for e in self.ec.for_verse("joh", 17, 21) if e.father == "Cyril of Alexandria"]
        assert cyril_1721, "γ.4.1.D missing Jn 17:21 — that they all may be one"

    def test_cyril_kingdom_not_of_this_world_present(self):
        # Jn 18:36 — anti-theocratic + anti-revolutionary pin shaping
        # Tewahedo monastic withdrawal ethic.
        cyril_1836 = [e for e in self.ec.for_verse("joh", 18, 36) if e.father == "Cyril of Alexandria"]
        assert cyril_1836, "γ.4.1.D missing Jn 18:36 — my kingdom not of this world"

    def test_cyril_tetelestai_present(self):
        # Jn 19:30 — dominical declaration of completed work; sovereign
        # release of life, not victim's defeat.
        cyril_1930 = [e for e in self.ec.for_verse("joh", 19, 30) if e.father == "Cyril of Alexandria"]
        assert cyril_1930, "γ.4.1.D missing Jn 19:30 — tetelestai"

    def test_cyril_receive_holy_ghost_present(self):
        # Jn 20:22 — new-creation breathing of the Spirit echoing
        # Gen 2:7; Trinitarian-pneumatological climax of the
        # Resurrection appearances.
        cyril_2022 = [e for e in self.ec.for_verse("joh", 20, 22) if e.father == "Cyril of Alexandria"]
        assert cyril_2022, "γ.4.1.D missing Jn 20:22 — Receive ye the Holy Ghost"

    def test_cyril_feed_my_sheep_present(self):
        # Jn 21:17 — third commission to Peter; pastoral office
        # institution; preserved in Tewahedo ordination prayers.
        cyril_2117 = [e for e in self.ec.for_verse("joh", 21, 17) if e.father == "Cyril of Alexandria"]
        assert cyril_2117, "γ.4.1.D missing Jn 21:17 — Feed my sheep"

    def test_meta_documents_gamma_4_1_d_expansion(self):
        # Pin: _meta scope/source block names γ.4.1.D explicitly.
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta = data["_meta"]
        assert "γ.4.1.D" in meta["source"] or "γ.4.1.D" in meta["scope"], (
            "_meta must name γ.4.1.D expansion in source or scope"
        )

    def test_every_gamma_4_1_d_attribution_cites_npnf_vol_14(self):
        # γ.4.1.D entries (Cyril-on-John in chapters 15-21) must all
        # cite NPNF Series 2 Vol 14 + explicit PD marker.
        cyril_in_chs_15_to_21 = []
        for chapter in (15, 16, 17, 18, 19, 20, 21):
            for verse in range(1, 100):
                cyril_in_chs_15_to_21.extend(
                    e for e in self.ec.for_verse("joh", chapter, verse) if e.father == "Cyril of Alexandria"
                )
        assert cyril_in_chs_15_to_21, "γ.4.1.D expected Cyril entries in John 15-21"
        for entry in cyril_in_chs_15_to_21:
            attr = entry.attribution
            assert "NPNF" in attr, f"γ.4.1.D entry missing NPNF citation: {attr!r}"
            assert "14" in attr, f"γ.4.1.D entry missing Vol 14 citation: {attr!r}"
            assert "PD" in attr, f"γ.4.1.D entry missing PD marker: {attr!r}"


class TestGamma44EnochFirstWave:
    """γ.4.4 — 1 Enoch verse-keyed entries (first wave, 30 entries).
    First substantive expansion of the third anchor of the Ethiopian
    corpus — the Mäṣḥafä Hēnok (Book of Enoch) that the Tewahedo
    canon uniquely receives as Scripture among the major Christian
    communions. Pre-γ.4.4 1 Enoch presence: 2 entries (Gen 6:1 +
    6:4 cross-references from γ.4 seed). Post-γ.4.4 wave-1: 32
    entries — 30 of which are verse-keyed to 1 Enoch itself (book
    code "1en"). This is the first time the corpus contains entries
    that use a Tewahedo-only canonical book code.

    Voice distribution post-γ.4.4 wave-1: 64% Cyril / 19% Ephrem /
    17% 1 Enoch — substantively three-anchored, matching the corpus
    _meta scope's documented threefold structure.

    Sourced from R.H. Charles, The Book of Enoch (Oxford: Clarendon,
    1912). Charles died 1931 — UK life+70 makes the work PD as of
    2002; US 95-years-from-publication makes it PD as of 2008. Fully
    PD in every major jurisdiction as of this ship.

    Per the addendum γ.4.4 target ~300 entries; this first wave
    lands 30 covering the canonical five-book structure: Watchers
    (chs 1-36) + Parables (37-71) + Astronomical (72-82) + Dream
    Visions / Animal Apocalypse (83-90) + Epistle of Enoch (91-108).

    Pins:
    - 1en book code now present in corpus (Tewahedo canonical first).
    - All five 1 Enoch books represented (Watchers + Parables +
      Astronomical + Dream Visions + Epistle).
    - 1 Enoch share ≥15% of corpus (substantive third-anchor presence).
    - Signature 1 Enoch passages: 1:9 (Jude quotation pin), 6:1
      (Watchers descent), 14:18 (throne vision), 46:1 (Son of Man
      vision), 71:14 (Enoch-Son-of-Man identification), 90:37
      (Messianic White Bull).
    - Every entry attributed to R.H. Charles 1912 PD trans.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def test_1en_book_code_present(self):
        # First entries to use the Tewahedo-only "1en" book code.
        # Pin its presence so future kinds-cleanup doesn't drop it.
        entries_on_1en = []
        for chapter in range(1, 109):
            for verse in range(1, 100):
                entries_on_1en.extend(self.ec.for_verse("1en", chapter, verse))
        assert len(entries_on_1en) >= 30, (
            f"γ.4.4 wave-1 expected ≥30 entries on book code '1en'; found {len(entries_on_1en)}"
        )

    def test_all_five_1_enoch_books_represented(self):
        # 1 Enoch is composed of 5 separately-redacted "books":
        # Watchers (1-36) + Parables (37-71) + Astronomical (72-82) +
        # Dream Visions / Animal Apocalypse (83-90) + Epistle (91-108).
        # Pin all five represented in the first wave.
        def has_chapter_in_range(start, end):
            for chapter in range(start, end + 1):
                for verse in range(1, 100):
                    for entry in self.ec.for_verse("1en", chapter, verse):
                        if entry.father == "1 Enoch (Ethiopian tradition)":
                            return True
            return False

        assert has_chapter_in_range(1, 36), "γ.4.4 missing Book of the Watchers (1En 1-36)"
        assert has_chapter_in_range(37, 71), "γ.4.4 missing Book of Parables (1En 37-71)"
        assert has_chapter_in_range(72, 82), "γ.4.4 missing Astronomical Book (1En 72-82)"
        assert has_chapter_in_range(83, 90), "γ.4.4 missing Dream Visions / Animal Apocalypse (1En 83-90)"
        assert has_chapter_in_range(91, 108), "γ.4.4 missing Epistle of Enoch (1En 91-108)"

    def test_1_enoch_substantively_present(self):
        # Pre-γ.4.4 1 Enoch was 2 of 130 entries (1%). Post-γ.4.4
        # first wave should be substantively present.
        #
        # Per feedback_share_pin_pattern: converted from γ.4.4 wave-1
        # share-pin (was: share >= 0.15) to absolute-count milestone.
        # The original share-pin would have broken mechanically on the
        # next voice-broadening ship (γ.4.6/.7/.8 Cyril Matt/Mark +
        # Mäqabyan would dilute 1En share below 15% at 192 / 1310);
        # the count-milestone preserves the historical achievement
        # (190+ 1En entries spanning all five sections — Watchers /
        # Parables / Astro / Animal / Epistle) durably against future
        # voice-broadening. Converted in AUDIT_2026-05-13 hygiene
        # cluster as the LAST surviving share-pin in this file.
        enoch_count = sum(
            1
            for verse_entries in self.ec._by_verse.values()
            for entry in verse_entries
            if entry.father == "1 Enoch (Ethiopian tradition)"
        )
        assert enoch_count >= 190, (
            f"γ.4.4 wave-1 1 Enoch count milestone (≥190 — sum across Watchers / "
            f"Parables / Astronomical / Animal Apocalypse / Epistle of Enoch); "
            f"actual {enoch_count}. Per feedback_share_pin_pattern: never a share pin."
        )

    def test_1_enoch_jude_quotation_pin_present(self):
        # 1En 1:9 is THE textual bridge between 1 Enoch and the
        # canonical NT (Jude 1:14-15 quotes it verbatim). Pin presence.
        enoch_19 = [e for e in self.ec.for_verse("1en", 1, 9) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch_19, "γ.4.4 missing 1En 1:9 — the verse Jude 1:14-15 quotes verbatim"

    def test_1_enoch_watchers_descent_present(self):
        # 1En 6:1 — the foundational Watchers narrative; Tewahedo-
        # distinctive expansion of Gen 6:1-4.
        enoch_61 = [e for e in self.ec.for_verse("1en", 6, 1) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch_61, "γ.4.4 missing 1En 6:1 — Watchers descent narrative"

    def test_1_enoch_throne_vision_present(self):
        # 1En 14:18 — Enoch's throne vision combining Ezekiel 1's
        # chariot + Dan 7's Ancient of Days. Foundational template
        # for subsequent Christian apocalyptic literature.
        enoch_1418 = [e for e in self.ec.for_verse("1en", 14, 18) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch_1418, "γ.4.4 missing 1En 14:18 — throne vision template"

    def test_1_enoch_son_of_man_present(self):
        # 1En 46:1 — the foundational Son of Man vision; the most
        # developed pre-Christian Jewish messianic-cosmic-judge
        # figure that the NT "Son of Man" Christology presupposes.
        enoch_461 = [e for e in self.ec.for_verse("1en", 46, 1) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch_461, "γ.4.4 missing 1En 46:1 — Son of Man vision"

    def test_1_enoch_enoch_as_son_of_man_present(self):
        # 1En 71:14 — controversial identification of Enoch with the
        # Son of Man; closes the Parables. Tewahedo reading preserves
        # the typological-not-competitive relationship to Christ.
        enoch_7114 = [e for e in self.ec.for_verse("1en", 71, 14) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch_7114, "γ.4.4 missing 1En 71:14 — Enoch-as-Son-of-Man identification"

    def test_1_enoch_messianic_white_bull_present(self):
        # 1En 90:37 — climactic appearance of the messianic White
        # Bull in the Animal Apocalypse; eschatological New Adam
        # that NT Last-Adam Christology (1 Cor 15:45) fulfills.
        enoch_9037 = [e for e in self.ec.for_verse("1en", 90, 37) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch_9037, "γ.4.4 missing 1En 90:37 — Messianic White Bull"

    def test_meta_documents_gamma_4_4_expansion(self):
        # Pin: _meta scope/source block names γ.4.4 explicitly.
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta = data["_meta"]
        assert "γ.4.4" in meta["source"] or "γ.4.4" in meta["scope"], (
            "_meta must name γ.4.4 expansion in source or scope"
        )

    def test_every_gamma_4_4_attribution_cites_charles_1912(self):
        # γ.4.4 entries must all cite R.H. Charles 1912 trans + PD.
        enoch_on_1en = []
        for chapter in range(1, 109):
            for verse in range(1, 100):
                enoch_on_1en.extend(
                    e for e in self.ec.for_verse("1en", chapter, verse) if e.father == "1 Enoch (Ethiopian tradition)"
                )
        assert enoch_on_1en, "γ.4.4 expected 1 Enoch entries on 1en book code"
        for entry in enoch_on_1en:
            attr = entry.attribution
            assert "Charles" in attr, f"γ.4.4 entry missing Charles citation: {attr!r}"
            assert "1912" in attr, f"γ.4.4 entry missing 1912 date: {attr!r}"
            assert "PD" in attr, f"γ.4.4 entry missing PD marker: {attr!r}"


class TestGamma44BWatchersDetailWave:
    """γ.4.4.B — 1 Enoch Watchers detail expansion (40 entries on
    chs 1-36 beyond the 11 γ.4.4.A entries on that section). Brings
    Watchers coverage from 11 to 51 entries across 30 distinct
    chapters (out of the section's 36). Voice distribution post-
    γ.4.4.B: 53% Cyril / 16% Ephrem / 31% 1 Enoch — 1 Enoch now
    substantively the second-heaviest voice in the corpus.

    Pins:
    - Watchers (chs 1-36) substantively expanded (≥40 1en entries
      in chs 1-36).
    - All five Watchers sub-arcs covered: prologue + descent +
      Enoch's intercession + first journey + second journey.
    - 1 Enoch share ≥25% of corpus.
    - Signature passages: 5:7 (covenant blessing — Mt 5:5 anticipation),
      9:1 (four archangels named), 10:13 (judgment of Azazel),
      13:8 (Enoch's denial of intercession), 15:8 (giants → demons
      etiology), 17:1 (first journey opening), 20:1 (seven archangels
      list), 24:4 (tree of life — Rev 22:2 anticipation), 36:1
      (second journey closes).
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def test_watchers_substantively_expanded(self):
        enoch_watchers = []
        for chapter in range(1, 37):
            for verse in range(1, 100):
                enoch_watchers.extend(
                    e for e in self.ec.for_verse("1en", chapter, verse) if e.father == "1 Enoch (Ethiopian tradition)"
                )
        assert len(enoch_watchers) >= 40, (
            f"γ.4.4.B expected ≥40 Watchers (1En 1-36) entries; found {len(enoch_watchers)}"
        )

    def test_all_five_watchers_subarcs_covered(self):
        def has_entry_in(start, end):
            for chapter in range(start, end + 1):
                for verse in range(1, 100):
                    for entry in self.ec.for_verse("1en", chapter, verse):
                        if entry.father == "1 Enoch (Ethiopian tradition)":
                            return True
            return False

        assert has_entry_in(1, 5), "γ.4.4.B missing Watchers prologue (1En 1-5)"
        assert has_entry_in(6, 11), "γ.4.4.B missing Watchers descent (1En 6-11)"
        assert has_entry_in(12, 16), "γ.4.4.B missing Enoch's intercession (1En 12-16)"
        assert has_entry_in(17, 19), "γ.4.4.B missing first journey (1En 17-19)"
        assert has_entry_in(20, 36), "γ.4.4.B missing second journey (1En 20-36)"

    def test_1_enoch_count_at_or_above_watchers_close(self):
        # Converted share-pin → count-milestone per
        # feedback_share_pin_pattern. The original γ.4.4.B share-pin
        # (≥25% of corpus) broke mechanically at γ.4.3.C as the Cyril
        # detail-wave grew the denominator. The historical achievement
        # (Watchers + Parables + Astro + Animal + Epistle = ~192 entries)
        # is preserved as an absolute floor; future voice-broadening
        # waves no longer mechanically break this pin.
        enoch_count = sum(
            1
            for verse_entries in self.ec._by_verse.values()
            for entry in verse_entries
            if entry.father == "1 Enoch (Ethiopian tradition)"
        )
        assert enoch_count >= 190, (
            f"γ.4.4.B expected 1 Enoch count ≥190 (cumulative Watchers + Parables + Astro + Animal + Epistle floor); found {enoch_count}"
        )

    def test_covenant_blessing_present(self):
        enoch_57 = [e for e in self.ec.for_verse("1en", 5, 7) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch_57, "γ.4.4.B missing 1En 5:7 — covenant blessing / Mt 5:5 anticipation"

    def test_four_archangels_named_present(self):
        enoch_91 = [e for e in self.ec.for_verse("1en", 9, 1) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch_91, "γ.4.4.B missing 1En 9:1 — four archangels intercession"

    def test_azazel_judgment_present(self):
        enoch_1013 = [e for e in self.ec.for_verse("1en", 10, 13) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch_1013, "γ.4.4.B missing 1En 10:13 — Azazel judgment / gehannem"

    def test_intercession_denied_present(self):
        enoch_138 = [e for e in self.ec.for_verse("1en", 13, 8) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch_138, "γ.4.4.B missing 1En 13:8 — Enoch's denied intercession"

    def test_demons_etiology_present(self):
        enoch_158 = [e for e in self.ec.for_verse("1en", 15, 8) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch_158, "γ.4.4.B missing 1En 15:8 — demons-as-disembodied-giants etiology"

    def test_first_journey_opening_present(self):
        enoch_171 = [e for e in self.ec.for_verse("1en", 17, 1) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch_171, "γ.4.4.B missing 1En 17:1 — first journey opening"

    def test_seven_archangels_list_present(self):
        enoch_201 = [e for e in self.ec.for_verse("1en", 20, 1) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch_201, "γ.4.4.B missing 1En 20:1 — seven archangels"

    def test_tree_of_life_present(self):
        enoch_244 = [e for e in self.ec.for_verse("1en", 24, 4) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch_244, "γ.4.4.B missing 1En 24:4 — tree of life / Rev 22:2 anticipation"

    def test_second_journey_closes_present(self):
        enoch_361 = [e for e in self.ec.for_verse("1en", 36, 1) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch_361, "γ.4.4.B missing 1En 36:1 — second journey closes"


class TestGamma44CParablesDetailWave:
    """γ.4.4.C — 1 Enoch Parables detail expansion (40 entries on
    chs 37-71 beyond the 9 γ.4.4.A entries on that section). Brings
    Parables coverage from 9 to 49 entries across 32 distinct
    chapters (out of the section's 35). Voice distribution post-
    γ.4.4.C: 50% Cyril / 15% Ephrem / 35% 1 Enoch — 1 Enoch share
    continues to climb but Cyril remains plurality voice.

    Pins:
    - Parables (chs 37-71) substantively expanded (≥40 1en entries
      in chs 37-71).
    - All four Parables sub-arcs covered: First Parable (38-44) +
      Second Parable (45-57) + Third Parable (58-69) + Translation
      Visions (70-71).
    - 1 Enoch share ≥30% of corpus.
    - Signature passages: 40:9 (Phanuel — angel of repentance),
      42:1 (Wisdom finds no place — Mary-fiat antecedent), 45:3
      (Elect One enthroned for judgment — Mt 25:31 antecedent),
      48:4 (Light of Gentiles — Servant-Son-of-Man identification),
      60:8 (Behemoth — east-of-Eden geography), 61:10
      (Cherubim/Seraphim/Ophannim), 68:1 (Methuselah as first
      Parables scribe), 69:25 (cosmogonic Oath), 69:27 (Son of Man
      receives sum of judgment — Jn 5:22-27 antecedent), 71:11
      (Enoch's transfiguration — theosis witness).
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def test_parables_substantively_expanded(self):
        enoch_parables = []
        for chapter in range(37, 72):
            for verse in range(1, 100):
                enoch_parables.extend(
                    e for e in self.ec.for_verse("1en", chapter, verse) if e.father == "1 Enoch (Ethiopian tradition)"
                )
        assert len(enoch_parables) >= 40, (
            f"γ.4.4.C expected ≥40 Parables (1En 37-71) entries; found {len(enoch_parables)}"
        )

    def test_all_four_parables_subarcs_covered(self):
        def has_entry_in(start, end):
            for chapter in range(start, end + 1):
                for verse in range(1, 100):
                    for entry in self.ec.for_verse("1en", chapter, verse):
                        if entry.father == "1 Enoch (Ethiopian tradition)":
                            return True
            return False

        assert has_entry_in(38, 44), "γ.4.4.C missing First Parable (1En 38-44)"
        assert has_entry_in(45, 57), "γ.4.4.C missing Second Parable (1En 45-57)"
        assert has_entry_in(58, 69), "γ.4.4.C missing Third Parable (1En 58-69)"
        assert has_entry_in(70, 71), "γ.4.4.C missing Translation Visions (1En 70-71)"

    def test_1_enoch_milestone_count_at_or_above_parables_close(self):
        # Per feedback_share_pin_pattern: converted from γ.4.4.C share-pin
        # (1En ≥30%) to absolute-count milestone pin (≥190 entries).
        # Invariant historical-achievement pin; does not refreeze the
        # voice balance when later γ-clusters dilute the 1En share.
        enoch_count = sum(
            1
            for verse_entries in self.ec._by_verse.values()
            for entry in verse_entries
            if entry.father == "1 Enoch (Ethiopian tradition)"
        )
        assert enoch_count >= 190, f"γ.4.4.C milestone: expected 1 Enoch count ≥190 entries; actual {enoch_count}"

    def test_phanuel_repentance_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 40, 9) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.C missing 1En 40:9 — Phanuel, angel of repentance"

    def test_wisdom_finds_no_place_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 42, 1) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.C missing 1En 42:1 — Wisdom finds no place (Mary-fiat antecedent)"

    def test_elect_one_enthroned_for_judgment_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 45, 3) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.C missing 1En 45:3 — Elect One enthroned for judgment (Mt 25:31 antecedent)"

    def test_light_of_gentiles_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 48, 4) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.C missing 1En 48:4 — Light of Gentiles / Servant–Son-of-Man identification"

    def test_behemoth_east_of_eden_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 60, 8) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.C missing 1En 60:8 — Behemoth and east-of-Eden geography"

    def test_threefold_angel_hierarchy_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 61, 10) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.C missing 1En 61:10 — Cherubim / Seraphim / Ophannim hierarchy"

    def test_methuselah_first_scribe_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 68, 1) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.C missing 1En 68:1 — Methuselah as first scribe of the Parables"

    def test_cosmogonic_oath_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 69, 25) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.C missing 1En 69:25 — cosmogonic Oath holding the cosmos together"

    def test_son_of_man_sum_of_judgment_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 69, 27) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.C missing 1En 69:27 — Son of Man receives sum of judgment (Jn 5:22-27 antecedent)"

    def test_enoch_transfiguration_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 71, 11) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.C missing 1En 71:11 — Enoch's transfiguration / theosis witness"


class TestGamma44DAstroDreamsAnimalWave:
    """γ.4.4.D — 1 Enoch Astronomical Book + Dream Visions + Animal
    Apocalypse expansion (40 entries on chs 72-90 beyond the 6
    γ.4.4.A entries on this section). Brings chs 72-90 coverage from
    6 to 46 entries; Mäṣḥafä Hēnok now substantively expanded across
    Watchers (γ.4.4.B), Parables (γ.4.4.C), and Astronomical+Dreams
    +Animal Apocalypse (γ.4.4.D). Voice distribution post-γ.4.4.D:
    ~38% Cyril / ~12% Ephrem / ~50% 1 Enoch — 1 Enoch becomes
    plurality voice in the corpus.

    Pins:
    - chs 72-90 substantively expanded (≥40 1en entries in chs
      72-90).
    - All three sub-arcs covered: Astronomical Book (72-82) +
      First Dream Vision (83-84) + Animal Apocalypse (85-90).
    - 1 Enoch share ≥45% of corpus (becomes plurality voice).
    - Signature passages: 72:32 (364-day liturgical year —
      Bāḥrä Ḥasab calendar anchor), 82:1 (Methuselah-as-scribe
      charge — monastic-scribal lineage warrant), 84:1 (tongue-
      given-for-praise), 85:3 (Adam as white bull — Animal
      Apocalypse foundational allegory), 87:2 (four white men —
      seven-archangel witness), 89:1 (Noah translated from bull
      to man — theosis anticipation), 89:50 (tower upon house —
      temple ecclesiology), 89:59 (seventy shepherds — gentile
      dominion period), 90:28 (new house / new Jerusalem — Rev
      21:2-3 antecedent), 90:38 (white-bull reunification + lamb-
      with-horns Christological climax).
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def test_chs_72_to_90_substantively_expanded(self):
        enoch_range = []
        for chapter in range(72, 91):
            for verse in range(1, 100):
                enoch_range.extend(
                    e for e in self.ec.for_verse("1en", chapter, verse) if e.father == "1 Enoch (Ethiopian tradition)"
                )
        assert len(enoch_range) >= 40, f"γ.4.4.D expected ≥40 entries in 1En 72-90; found {len(enoch_range)}"

    def test_all_three_subarcs_covered(self):
        def has_entry_in(start, end):
            for chapter in range(start, end + 1):
                for verse in range(1, 100):
                    for entry in self.ec.for_verse("1en", chapter, verse):
                        if entry.father == "1 Enoch (Ethiopian tradition)":
                            return True
            return False

        assert has_entry_in(72, 82), "γ.4.4.D missing Astronomical Book (1En 72-82)"
        assert has_entry_in(83, 84), "γ.4.4.D missing First Dream Vision (1En 83-84)"
        assert has_entry_in(85, 90), "γ.4.4.D missing Animal Apocalypse (1En 85-90)"

    def test_1_enoch_milestone_count_at_or_above_astro_dreams_animal_close(self):
        # γ.4.4.D shipped 1 Enoch into plurality at ~152 entries (≥45% of
        # corpus-at-time-of-ship). The original share-pin became
        # incorrect once γ.4.5/B/C deliberately added Jubilees as a
        # fourth voice and diluted 1 Enoch's share — see SESSION_STATE
        # 2026-05-12 entries on the γ.4.5 arc. Replaced with the
        # absolute-count milestone that captures the historical
        # achievement invariantly: 1 Enoch reached the Astro-Dreams-
        # Animal close at ≥150 entries.
        enoch_count = sum(
            1
            for verse_entries in self.ec._by_verse.values()
            for entry in verse_entries
            if entry.father == "1 Enoch (Ethiopian tradition)"
        )
        assert enoch_count >= 150, (
            f"γ.4.4.D expected 1 Enoch count ≥150 (Astro-Dreams-Animal close milestone); found {enoch_count}"
        )

    def test_liturgical_year_anchor_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 72, 32) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.D missing 1En 72:32 — 364-day liturgical year (Bāḥrä Ḥasab anchor)"

    def test_methuselah_scribe_charge_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 82, 1) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.D missing 1En 82:1 — Methuselah-as-scribe charge"

    def test_tongue_given_for_praise_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 84, 1) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.D missing 1En 84:1 — tongue given for praise"

    def test_adam_as_white_bull_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 85, 3) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.D missing 1En 85:3 — Adam as white bull (Animal Apocalypse anchor)"

    def test_four_archangels_in_animal_apocalypse_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 87, 2) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.D missing 1En 87:2 — four white men (seven-archangel witness)"

    def test_noah_translated_bull_to_man_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 89, 1) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.D missing 1En 89:1 — Noah translated from bull to man (theosis anticipation)"

    def test_tower_upon_house_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 89, 50) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.D missing 1En 89:50 — tower upon house (temple ecclesiology)"

    def test_seventy_shepherds_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 89, 59) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.D missing 1En 89:59 — seventy shepherds (gentile dominion period)"

    def test_new_house_new_jerusalem_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 90, 28) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.D missing 1En 90:28 — new house / new Jerusalem (Rev 21:2-3 antecedent)"

    def test_white_bull_reunification_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 90, 38) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.D missing 1En 90:38 — white-bull reunification + lamb-with-horns climax"


class TestGamma44EEpistleOfEnochWave:
    """γ.4.4.E — 1 Enoch Epistle / Apocalypse of Weeks / Birth of Noah
    expansion (40 entries on chs 91-108 beyond the 4 γ.4.4.A entries
    on this section). **CLOSES the Mäṣḥafä Hēnok arc** — all six
    sections of the Ethiopian 1 Enoch (Watchers + Parables +
    Astronomical Book + Dream Visions + Animal Apocalypse + Epistle)
    are now substantively expanded. Voice distribution post-γ.4.4.E:
    ~34% Cyril / ~10% Ephrem / ~56% 1 Enoch — 1 Enoch is the
    dominant voice in the corpus.

    Pins:
    - chs 91-108 substantively expanded (≥40 1en entries in chs
      91-108).
    - All three Epistle-section sub-arcs covered: Apocalypse of
      Weeks (91:11-17 + 93) + Epistle proper exhortation/woes
      (92, 94-105) + Birth of Noah + closing (106-108).
    - 1 Enoch share ≥50% of corpus (dominant voice).
    - Signature passages: 91:14 (tenth-week judgment of watchers —
      closes Watchers arc), 91:16 (sevenfold-light new heaven —
      Rev 21:1 antecedent), 93:6 (Abraham as plant of righteousness),
      94:1 (two-paths exhortation — Didache antecedent), 95:3
      (saints shall judge the world — 1 Cor 6:2 antecedent), 98:4
      (human authorship of sin — anti-Manichaean anchor), 102:4
      (fear-not-ye-souls-of-righteous — Tewahedo funeral formula),
      103:4 (spirits live and rejoice — intermediate-state-as-
      joyful), 104:10 (sinners pervert words — manuscript-
      preservation warrant), 104:12 (books as joy to righteous —
      monastic-scribal joy-form), 105:1 ('I and My son' — Father-
      Son union pre-canonical witness), 106:2 (Noah's radiant
      birth — Tewahedo iconographic anchor), 108:1 ('for those
      who keep the law in the last days' — Tewahedo self-
      identification as addressee of the entire book).
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def test_chs_91_to_108_substantively_expanded(self):
        enoch_range = []
        for chapter in range(91, 109):
            for verse in range(1, 100):
                enoch_range.extend(
                    e for e in self.ec.for_verse("1en", chapter, verse) if e.father == "1 Enoch (Ethiopian tradition)"
                )
        assert len(enoch_range) >= 40, f"γ.4.4.E expected ≥40 entries in 1En 91-108; found {len(enoch_range)}"

    def test_apocalypse_of_weeks_covered(self):
        # Seven-past + three-eschatological weeks scheme.
        # 93:1-10 = weeks 1-7; 91:11-17 = weeks 8-10 + consummation.
        aow_entries = [e for e in self.ec.for_verse("1en", 93, 2) if e.father == "1 Enoch (Ethiopian tradition)"]
        aow_entries += [e for e in self.ec.for_verse("1en", 91, 14) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert len(aow_entries) >= 2, "γ.4.4.E missing Apocalypse of Weeks anchor verses (93:2 + 91:14)"

    def test_epistle_proper_covered(self):
        # Random sample of the Epistle's paths-and-woes section
        paths_woes = []
        for chapter in (94, 95, 98, 102, 103, 104):
            for verse in range(1, 20):
                paths_woes.extend(
                    e for e in self.ec.for_verse("1en", chapter, verse) if e.father == "1 Enoch (Ethiopian tradition)"
                )
        assert len(paths_woes) >= 8, (
            f"γ.4.4.E expected ≥8 entries across Epistle exhortation chapters 94/95/98/102/103/104; found {len(paths_woes)}"
        )

    def test_birth_of_noah_covered(self):
        def has_entry_in(chapter):
            for verse in range(1, 30):
                for entry in self.ec.for_verse("1en", chapter, verse):
                    if entry.father == "1 Enoch (Ethiopian tradition)":
                        return True
            return False

        assert has_entry_in(106), "γ.4.4.E missing Birth of Noah (1En 106)"
        assert has_entry_in(107), "γ.4.4.E missing Birth of Noah continuation (1En 107)"

    def test_closing_inclusio_covered(self):
        enoch = [e for e in self.ec.for_verse("1en", 108, 1) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.E missing 1En 108:1 — closing inclusio of the Mäṣḥafä Hēnok"

    def test_1_enoch_milestone_count_at_or_above_mashafa_henok_arc_close(self):
        # γ.4.4.E closed the Mäṣḥafä Hēnok arc with 1 Enoch at 192
        # entries, briefly the dominant voice (55% of corpus-at-time).
        # The γ.4.5/B/C waves intentionally added Jubilees as a fourth
        # voice and diluted 1 Enoch share — see SESSION_STATE
        # 2026-05-12. The dominance was a phase-transition artifact;
        # the durable invariant is the absolute Mäṣḥafä-Hēnok
        # coverage. Replaced with the absolute-count milestone:
        # 1 Enoch reached the arc-close at ≥190 entries.
        enoch_count = sum(
            1
            for verse_entries in self.ec._by_verse.values()
            for entry in verse_entries
            if entry.father == "1 Enoch (Ethiopian tradition)"
        )
        assert enoch_count >= 190, (
            f"γ.4.4.E expected 1 Enoch count ≥190 (Mäṣḥafä Hēnok arc-close milestone); found {enoch_count}"
        )

    def test_watchers_arc_closed_at_91_14(self):
        enoch = [e for e in self.ec.for_verse("1en", 91, 14) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.E missing 1En 91:14 — tenth-week judgment of watchers (closes Watchers arc)"

    def test_sevenfold_light_new_heaven_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 91, 16) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.E missing 1En 91:16 — sevenfold-light new heaven (Rev 21:1 antecedent)"

    def test_two_paths_exhortation_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 94, 1) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.E missing 1En 94:1 — two-paths exhortation (Didache antecedent)"

    def test_saints_shall_judge_world_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 95, 3) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.E missing 1En 95:3 — saints shall judge the world (1 Cor 6:2 antecedent)"

    def test_human_authorship_of_sin_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 98, 4) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.E missing 1En 98:4 — human authorship of sin (anti-Manichaean anchor)"

    def test_textual_preservation_warrant_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 104, 10) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.E missing 1En 104:10 — sinners pervert words (manuscript-preservation warrant)"

    def test_father_son_union_witness_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 105, 1) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.E missing 1En 105:1 — 'I and My son' (Father-Son union pre-canonical witness)"

    def test_radiant_birth_of_noah_present(self):
        enoch = [e for e in self.ec.for_verse("1en", 106, 2) if e.father == "1 Enoch (Ethiopian tradition)"]
        assert enoch, "γ.4.4.E missing 1En 106:2 — Noah's radiant birth (Tewahedo iconographic anchor)"

    def test_all_six_mashafa_henok_sections_covered(self):
        """γ.4.4.E claims to CLOSE the Mäṣḥafä Hēnok arc — verify
        every one of the six canonical sections has substantive
        1 Enoch coverage."""

        def section_count(start, end):
            n = 0
            for chapter in range(start, end + 1):
                for verse in range(1, 200):
                    for entry in self.ec.for_verse("1en", chapter, verse):
                        if entry.father == "1 Enoch (Ethiopian tradition)":
                            n += 1
            return n

        watchers = section_count(1, 36)
        parables = section_count(37, 71)
        astronomical = section_count(72, 82)
        dream_visions = section_count(83, 84)
        animal_apocalypse = section_count(85, 90)
        epistle = section_count(91, 108)

        for name, n, threshold in [
            ("Watchers (1-36)", watchers, 40),
            ("Parables (37-71)", parables, 40),
            ("Astronomical Book (72-82)", astronomical, 10),
            ("Dream Visions (83-84)", dream_visions, 3),
            ("Animal Apocalypse (85-90)", animal_apocalypse, 20),
            ("Epistle (91-108)", epistle, 40),
        ]:
            assert n >= threshold, f"γ.4.4.E arc-close pin: {name} has {n} entries, expected ≥{threshold}"


class TestGamma42BEphremPatriarchsWave:
    """γ.4.2.B — Ephrem on Genesis 12-50 (patriarchal narrative).
    Continues the γ.4.2 first wave (Gen 1-11, 32 entries shipped
    earlier this session) into Gen 12-50, adding 40 verse-keyed
    Ephrem-the-Syrian entries spanning the Abraham (15), Jacob (12),
    and Joseph (13) cycles. Rebalances Ephrem share from ~10% (under-
    represented after γ.4.4 1 Enoch arc) back toward ~19%.

    Pins:
    - Gen 12-50 substantively expanded (≥40 Ephrem entries on Gen
      12-50).
    - All three patriarchal sub-arcs covered: Abraham cycle (12-25)
      + Jacob cycle (25-36) + Joseph cycle (37-50).
    - Ephrem share ≥17% of corpus (rebalanced upward).
    - Signature passages: 14:18 (Melchizedek bread-and-wine —
      Tewahedo eucharistic anchor), 15:6 (Abraham's faith counted
      for righteousness), 18:1 (Mamre Trinity theophany — Tewahedo
      iconographic anchor), 22:8 (Akedah / 'God will provide
      himself a lamb' — direct Crucifixion prophecy), 28:12
      (Jacob's ladder — Christ-and-Mary type), 32:24 (wrestling
      with pre-incarnate Word), 37:28 (Joseph sold for silver —
      Christ-typology), 41:55 ('go unto Joseph, do what he saith'
      — Marian-Cana prefiguration), 44:18 (Judah's substitutionary
      self-offering), 49:10 (Shiloh-as-Christ prophecy), 50:20
      (providence-formula par excellence).
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def test_gen_12_to_50_substantively_expanded(self):
        ephrem_patriarchs = []
        for chapter in range(12, 51):
            for verse in range(1, 100):
                ephrem_patriarchs.extend(
                    e for e in self.ec.for_verse("gen", chapter, verse) if e.father == "Ephrem the Syrian"
                )
        assert len(ephrem_patriarchs) >= 40, (
            f"γ.4.2.B expected ≥40 Ephrem entries on Gen 12-50; found {len(ephrem_patriarchs)}"
        )

    def test_all_three_patriarchal_cycles_covered(self):
        def has_ephrem_in(start, end):
            for chapter in range(start, end + 1):
                for verse in range(1, 100):
                    for entry in self.ec.for_verse("gen", chapter, verse):
                        if entry.father == "Ephrem the Syrian":
                            return True
            return False

        assert has_ephrem_in(12, 25), "γ.4.2.B missing Abraham cycle (Gen 12-25)"
        assert has_ephrem_in(25, 36), "γ.4.2.B missing Jacob cycle (Gen 25-36)"
        assert has_ephrem_in(37, 50), "γ.4.2.B missing Joseph cycle (Gen 37-50)"

    def test_ephrem_milestone_count_at_or_above_patriarchal_close(self):
        # γ.4.2.B shipped Ephrem coverage of Gen 12-50 with a final
        # Ephrem count of 77 (Gen 1-11 from γ.4.2 + Gen 12-50 from
        # γ.4.2.B). The original share-pin (≥17%, later lowered to
        # ≥15%) was correct at ship-time but fails mechanically on
        # every subsequent voice-broadening wave (γ.4.5.C/D add
        # Jubilees entries that dilute Ephrem's share without removing
        # any Ephrem content). Converted to absolute-count milestone:
        # Ephrem-on-Genesis reached ≥75 entries at γ.4.2.B close.
        # The milestone captures the historical-coverage achievement
        # invariantly across future voice-broadening.
        ephrem_count = sum(
            1
            for verse_entries in self.ec._by_verse.values()
            for entry in verse_entries
            if entry.father == "Ephrem the Syrian"
        )
        assert ephrem_count >= 75, (
            f"γ.4.2.B expected Ephrem count ≥75 (patriarchal-narrative close milestone); found {ephrem_count}"
        )

    def test_melchizedek_eucharistic_anchor_present(self):
        eph = [e for e in self.ec.for_verse("gen", 14, 18) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.B missing Gen 14:18 — Melchizedek bread-and-wine (Tewahedo eucharistic anchor)"

    def test_abrahams_faith_present(self):
        eph = [e for e in self.ec.for_verse("gen", 15, 6) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.B missing Gen 15:6 — Abraham's faith counted for righteousness"

    def test_mamre_trinity_theophany_present(self):
        eph = [e for e in self.ec.for_verse("gen", 18, 1) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.B missing Gen 18:1 — Mamre Trinity theophany (Tewahedo iconographic anchor)"

    def test_akedah_lamb_prophecy_present(self):
        eph = [e for e in self.ec.for_verse("gen", 22, 8) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.B missing Gen 22:8 — Akedah 'God will provide himself a lamb' (Crucifixion prophecy)"

    def test_jacobs_ladder_present(self):
        eph = [e for e in self.ec.for_verse("gen", 28, 12) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.B missing Gen 28:12 — Jacob's ladder (Christ-and-Mary type)"

    def test_wrestling_pre_incarnate_word_present(self):
        eph = [e for e in self.ec.for_verse("gen", 32, 24) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.B missing Gen 32:24 — wrestling with pre-incarnate Word"

    def test_joseph_sold_for_silver_present(self):
        eph = [e for e in self.ec.for_verse("gen", 37, 28) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.B missing Gen 37:28 — Joseph sold for silver pieces (Christ-typology)"

    def test_go_unto_joseph_marian_prefiguration_present(self):
        eph = [e for e in self.ec.for_verse("gen", 41, 55) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.B missing Gen 41:55 — 'go unto Joseph, do what he saith' (Marian-Cana prefiguration)"

    def test_judah_substitutionary_offering_present(self):
        eph = [e for e in self.ec.for_verse("gen", 44, 18) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.B missing Gen 44:18 — Judah's substitutionary self-offering"

    def test_shiloh_prophecy_present(self):
        eph = [e for e in self.ec.for_verse("gen", 49, 10) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.B missing Gen 49:10 — Shiloh-as-Christ prophecy"

    def test_providence_formula_present(self):
        eph = [e for e in self.ec.for_verse("gen", 50, 20) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.B missing Gen 50:20 — providence-formula par excellence"


class TestGamma42CEphremExodusWave:
    """γ.4.2.C — Ephrem on Exodus seed wave. Extends the γ.4.2 +
    γ.4.2.B Genesis coverage into Exodus with 40 verse-keyed entries
    spanning every major Exodus narrative block. Source: Ephrem the
    Syrian, *Commentary on Exodus* + *Sermo de Domino Nostro* +
    *Hymns on the Crucifixion* + *Hymns on the Nativity*, NPNF
    Series 2 vol. 13 (Gwynn / Schaff trans., Oxford 1898 — PD).
    Rebalances Ephrem share from 13.1% (γ.4.5.E corpus state) back
    upward to ~18.6% — recovering parity with Cyril.

    Pins:
    - Exo 1-40 substantively expanded (≥40 Ephrem entries on exo).
    - All twelve major narrative blocks covered: Israel-multiplies
      (Ex 1), Moses' birth + Midian (Ex 2), burning bush + I AM
      (Ex 3), signs + lodging-night (Ex 4), covenantal formula
      (Ex 6) + rod-serpent (Ex 7), Passover (Ex 12), pillar
      (Ex 13), Red Sea (Ex 14), Song + Marah (Ex 15), manna +
      water-from-rock + Amalek (Ex 16-17), Sinai theophany +
      Decalogue + covenant blood (Ex 19-24), tabernacle + mercy
      seat + high priest (Ex 25-28), golden calf + tablets + glory
      + veil + glory-fills (Ex 32-40).
    - Ephrem milestone count ≥110 entries (absolute, per
      feedback_share_pin_pattern — does not break mechanically
      on future voice-broadening waves).
    - Voice mix invariant: Ephrem rises but no existing voice
      loses entries.
    - Signature passages: 2:3 (three-day Moses-ark Pascal-typology
      anchor), 3:2 (burning bush — Theotokos iconographic anchor),
      3:5 (loose-thy-shoe — Tewahedo barefoot-sanctuary canonical
      anchor), 3:14 (I AM ↔ Jn 8:58), 4:24 (Mastema-at-lodging
      Tewahedo theodicy harmony with Jub 48:1-2), 12:13 (blood
      Cross-shape on lintels — Tewahedo eucharistic demonic-defense
      anchor), 12:46 (no bone broken — Jn 19:36 verbatim
      fulfillment), 14:22 (Red Sea = baptism — Tewahedo baptismal
      canonical anchor), 15:25 (Marah-tree = Cross), 16:4 (manna
      = bread-from-heaven Jn 6 anchor), 17:6 (struck rock — Jn
      19:34 anchor), 17:11 (Moses' arms = Cross-posture
      intercession), 20:8 (Sabbath — Tewahedo Saturday-Sabbath-
      and-Sunday-Lord's-Day double-observance canonical anchor),
      24:8 (covenant-blood formula adopted verbatim at Last
      Supper), 25:8 (Tewahedo tabot canonical anchor), 33:20
      (vision-reserved-for-Christ), 40:34 (glory fills tabernacle
      — Rev 21:3 canonical-hope bookend).
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def test_exodus_substantively_seeded(self):
        ephrem_exo = []
        for chapter in range(1, 41):
            for verse in range(1, 100):
                ephrem_exo.extend(
                    e for e in self.ec.for_verse("exo", chapter, verse) if e.father == "Ephrem the Syrian"
                )
        assert len(ephrem_exo) >= 40, f"γ.4.2.C expected ≥40 Ephrem entries on Exodus 1-40; found {len(ephrem_exo)}"

    def test_all_major_exodus_blocks_covered(self):
        def has_ephrem_in(start, end):
            for chapter in range(start, end + 1):
                for verse in range(1, 100):
                    for entry in self.ec.for_verse("exo", chapter, verse):
                        if entry.father == "Ephrem the Syrian":
                            return True
            return False

        assert has_ephrem_in(1, 2), "γ.4.2.C missing Israel-multiplies + Moses' birth (Ex 1-2)"
        assert has_ephrem_in(3, 4), "γ.4.2.C missing burning bush + signs (Ex 3-4)"
        assert has_ephrem_in(6, 7), "γ.4.2.C missing covenantal formula + rod-serpent (Ex 6-7)"
        assert has_ephrem_in(12, 13), "γ.4.2.C missing Passover + pillar (Ex 12-13)"
        assert has_ephrem_in(14, 15), "γ.4.2.C missing Red Sea + Song of Moses (Ex 14-15)"
        assert has_ephrem_in(16, 17), "γ.4.2.C missing manna + water-from-rock + Amalek (Ex 16-17)"
        assert has_ephrem_in(19, 20), "γ.4.2.C missing Sinai theophany + Decalogue (Ex 19-20)"
        assert has_ephrem_in(24, 28), "γ.4.2.C missing covenant + tabernacle + priestly vestments (Ex 24-28)"
        assert has_ephrem_in(32, 34), "γ.4.2.C missing golden calf + tablets + glory + veil (Ex 32-34)"
        assert has_ephrem_in(40, 40), "γ.4.2.C missing glory-fills-tabernacle (Ex 40)"

    def test_ephrem_milestone_count_at_or_above_exodus_close(self):
        # γ.4.2 (Gen 1-11, 32) + γ.4.2.B (Gen 12-50, 40) + γ.4.5.D
        # incidental Ps (1) + γ.4.2.C (Exo 1-40, 40) = ≥113 Ephrem
        # entries. Absolute milestone per feedback_share_pin_pattern;
        # invariant against future voice-broadening waves.
        ephrem_count = sum(
            1
            for verse_entries in self.ec._by_verse.values()
            for entry in verse_entries
            if entry.father == "Ephrem the Syrian"
        )
        assert ephrem_count >= 110, (
            f"γ.4.2.C expected Ephrem count ≥110 (Exodus-arc close milestone); found {ephrem_count}"
        )

    def test_moses_ark_pascal_typology_present(self):
        eph = [e for e in self.ec.for_verse("exo", 2, 3) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.C missing Ex 2:3 — three-day Moses-ark Pascal-typology anchor"

    def test_burning_bush_theotokos_type_present(self):
        eph = [e for e in self.ec.for_verse("exo", 3, 2) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.C missing Ex 3:2 — burning bush (Theotokos iconographic anchor)"

    def test_loose_thy_shoe_barefoot_sanctuary_present(self):
        eph = [e for e in self.ec.for_verse("exo", 3, 5) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.C missing Ex 3:5 — loose-thy-shoe (Tewahedo barefoot-sanctuary anchor)"

    def test_i_am_revelation_present(self):
        eph = [e for e in self.ec.for_verse("exo", 3, 14) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.C missing Ex 3:14 — I AM (canonical anchor for Jn 8:58)"

    def test_mastema_at_lodging_present(self):
        eph = [e for e in self.ec.for_verse("exo", 4, 24) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.C missing Ex 4:24 — lodging-night attack (Tewahedo Jub 48:1-2 harmony)"

    def test_blood_on_lintels_cross_shape_present(self):
        eph = [e for e in self.ec.for_verse("exo", 12, 13) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.C missing Ex 12:13 — blood-on-lintels Cross-shape (eucharistic demonic-defense)"

    def test_no_bone_broken_present(self):
        eph = [e for e in self.ec.for_verse("exo", 12, 46) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.C missing Ex 12:46 — no bone broken (Jn 19:36 verbatim fulfillment)"

    def test_red_sea_baptism_typology_present(self):
        eph = [e for e in self.ec.for_verse("exo", 14, 22) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.C missing Ex 14:22 — Red Sea = baptism (Tewahedo baptismal anchor)"

    def test_marah_tree_cross_present(self):
        eph = [e for e in self.ec.for_verse("exo", 15, 25) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.C missing Ex 15:25 — Marah-tree (Cross typology anchor)"

    def test_manna_bread_from_heaven_present(self):
        eph = [e for e in self.ec.for_verse("exo", 16, 4) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.C missing Ex 16:4 — manna (bread-from-heaven Jn 6 anchor)"

    def test_struck_rock_christ_present(self):
        eph = [e for e in self.ec.for_verse("exo", 17, 6) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.C missing Ex 17:6 — struck rock (Christ + Jn 19:34 anchor)"

    def test_moses_arms_cross_posture_present(self):
        eph = [e for e in self.ec.for_verse("exo", 17, 11) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.C missing Ex 17:11 — Moses' arms (Cross-posture intercession anchor)"

    def test_sabbath_double_observance_present(self):
        eph = [e for e in self.ec.for_verse("exo", 20, 8) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.C missing Ex 20:8 — Sabbath (Tewahedo Saturday + Sunday double observance)"

    def test_covenant_blood_formula_present(self):
        eph = [e for e in self.ec.for_verse("exo", 24, 8) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.C missing Ex 24:8 — covenant-blood (verbatim formula adopted at Last Supper)"

    def test_tabot_anchor_present(self):
        eph = [e for e in self.ec.for_verse("exo", 25, 8) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.C missing Ex 25:8 — sanctuary (Tewahedo tabot canonical anchor)"

    def test_vision_reserved_for_christ_present(self):
        eph = [e for e in self.ec.for_verse("exo", 33, 20) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.C missing Ex 33:20 — vision-reserved-for-Christ (canonical anchor)"

    def test_glory_fills_tabernacle_present(self):
        eph = [e for e in self.ec.for_verse("exo", 40, 34) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.C missing Ex 40:34 — glory fills tabernacle (Rev 21:3 bookend)"

    def test_meta_documents_gamma_4_2_c_expansion(self):
        # Pin the _meta.source string carries the γ.4.2.C signature so
        # future Claude doesn't lose the arc-record. Per the §8.1 arc-
        # close convention (rules) the _meta sync pin is required for
        # multi-wave content arcs.
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_source = data["_meta"]["source"]
        assert "γ.4.2.C" in meta_source, "γ.4.2.C must be referenced in _meta.source"
        assert "Ephrem-on-Exodus" in meta_source, "γ.4.2.C _meta.source should describe Ephrem-on-Exodus"


class TestGamma43CyrilLukeWave:
    """γ.4.3 — Cyril of Alexandria on Luke seed wave. Opens the
    SECOND major Cyril Gospel arc after γ.4.1 (Cyril-on-John, closed
    at γ.4.1.D modulo unfillable Jn 8-10 manuscript gap). 40 verse-
    keyed entries spanning all 24 Lukan chapters. Source: R. Payne
    Smith, *A Commentary upon the Gospel according to S. Luke by
    S. Cyril, Patriarch of Alexandria* (Oxford: University Press,
    1859 — PD; Payne Smith d. 1895). The 156 homilies translated
    from Syriac (original Greek lost except for catena fragments).
    Rebalances Cyril share from 19.2% (γ.4.2.C-close state) back
    upward to ~24.0%.

    Pins:
    - Lk 1-24 substantively seeded (≥40 Cyril entries on luk).
    - All major Lukan narrative blocks covered: Infancy (1-2),
      Galilean ministry (3-9), Journey-to-Jerusalem (10-19),
      Jerusalem teaching (20-21), Passion (22-23), Resurrection-
      and-Ascension (24).
    - Cyril absolute-count milestone ≥160 entries (per
      `feedback_share_pin_pattern` — absolute count, not share).
    - Signature passages: 1:28 (Annunciation Theotokos anchor),
      2:29 (Nunc Dimittis), 2:49 (two-natures Christology),
      4:21 (Is 61 fulfilment), 7:47 (sinful woman loves much —
      absolution-precedes-penance), 9:35 (Transfiguration Father-
      voice), 10:33 (Good Samaritan Christological allegory),
      15:20 (Father-runs-to-meet — Prodigal), 16:23 (Rich Man and
      Lazarus — intermediate state anchor), 17:16 (Samaritan
      leper returns — eucharistic-thanksgiving anchor), 22:19
      (Last Supper real-presence Lukan anchor), 22:44 (Gethsemane
      sweat — true-humanity anchor against Apollinarianism), 23:43
      ('Today shalt thou be with me in paradise' — immediate-
      paradise anchor), 24:30 (Emmaus breaking-of-bread — every-
      Eucharist-is-recognition anchor), 24:51 (Ascension Lukan
      anchor).
    - _meta.source sync pin: γ.4.3 referenced + Cyril-on-Luke
      signature.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def test_luke_substantively_seeded(self):
        cyril_luk = []
        for chapter in range(1, 25):
            for verse in range(1, 100):
                cyril_luk.extend(
                    e for e in self.ec.for_verse("luk", chapter, verse) if e.father == "Cyril of Alexandria"
                )
        assert len(cyril_luk) >= 40, f"γ.4.3 expected ≥40 Cyril entries on Luke 1-24; found {len(cyril_luk)}"

    def test_all_major_lukan_blocks_covered(self):
        def has_cyril_in(start, end):
            for chapter in range(start, end + 1):
                for verse in range(1, 100):
                    for entry in self.ec.for_verse("luk", chapter, verse):
                        if entry.father == "Cyril of Alexandria":
                            return True
            return False

        assert has_cyril_in(1, 2), "γ.4.3 missing Lukan Infancy narrative (Lk 1-2)"
        assert has_cyril_in(3, 9), "γ.4.3 missing Galilean ministry (Lk 3-9)"
        assert has_cyril_in(10, 19), "γ.4.3 missing Journey-to-Jerusalem (Lk 10-19)"
        assert has_cyril_in(20, 21), "γ.4.3 missing Jerusalem teaching (Lk 20-21)"
        assert has_cyril_in(22, 23), "γ.4.3 missing Passion narrative (Lk 22-23)"
        assert has_cyril_in(24, 24), "γ.4.3 missing Resurrection + Ascension (Lk 24)"

    def test_cyril_milestone_count_at_or_above_luke_seed(self):
        # γ.4.1.A-D shipped 116 Cyril-on-John entries; γ.4.3 adds
        # 40 Cyril-on-Luke = 156. Floor at ≥160 as conservative
        # post-γ.4.3 milestone (accommodates seed-wave count + any
        # incidental Cyril references). Absolute count per
        # feedback_share_pin_pattern; invariant under future voice-
        # broadening waves.
        cyril_count = sum(
            1
            for verse_entries in self.ec._by_verse.values()
            for entry in verse_entries
            if entry.father == "Cyril of Alexandria"
        )
        assert cyril_count >= 160, f"γ.4.3 expected Cyril count ≥160 (Luke-seed close milestone); found {cyril_count}"

    def test_annunciation_theotokos_anchor_present(self):
        c = [e for e in self.ec.for_verse("luk", 1, 28) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.3 missing Lk 1:28 — Annunciation (Theotokos canonical anchor)"

    def test_magnificat_present(self):
        c = [e for e in self.ec.for_verse("luk", 1, 46) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.3 missing Lk 1:46 — Magnificat (first NT prophetic hymn)"

    def test_nunc_dimittis_present(self):
        c = [e for e in self.ec.for_verse("luk", 2, 29) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.3 missing Lk 2:29 — Nunc Dimittis (canonical hymn anchor)"

    def test_twelve_year_old_two_natures_present(self):
        c = [e for e in self.ec.for_verse("luk", 2, 49) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.3 missing Lk 2:49 — twelve-year-old (two-natures Christology anchor)"

    def test_nazareth_synagogue_isaiah_61_present(self):
        c = [e for e in self.ec.for_verse("luk", 4, 21) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.3 missing Lk 4:21 — Nazareth synagogue (Isaiah 61 fulfilment anchor)"

    def test_sabbath_lord_present(self):
        c = [e for e in self.ec.for_verse("luk", 6, 5) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.3 missing Lk 6:5 — Son of Man Lord of the Sabbath (Tewahedo Sabbath anchor)"

    def test_sinful_woman_absolution_present(self):
        c = [e for e in self.ec.for_verse("luk", 7, 47) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.3 missing Lk 7:47 — sinful woman (absolution-precedes-penance canonical anchor)"

    def test_transfiguration_father_voice_present(self):
        c = [e for e in self.ec.for_verse("luk", 9, 35) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.3 missing Lk 9:35 — Transfiguration Father-voice (Buhe feast canonical anchor)"

    def test_good_samaritan_allegory_present(self):
        c = [e for e in self.ec.for_verse("luk", 10, 33) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.3 missing Lk 10:33 — Good Samaritan (Christological allegory)"

    def test_prodigal_son_present(self):
        c = [e for e in self.ec.for_verse("luk", 15, 20) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.3 missing Lk 15:20 — Prodigal Son (Father-runs-to-meet canonical anchor)"

    def test_rich_man_lazarus_intermediate_state_present(self):
        c = [e for e in self.ec.for_verse("luk", 16, 23) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.3 missing Lk 16:23 — Rich Man and Lazarus (intermediate state canonical anchor)"

    def test_samaritan_leper_eucharist_present(self):
        c = [e for e in self.ec.for_verse("luk", 17, 16) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.3 missing Lk 17:16 — Samaritan leper returns (eucharistic-thanksgiving anchor)"

    def test_last_supper_real_presence_present(self):
        c = [e for e in self.ec.for_verse("luk", 22, 19) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.3 missing Lk 22:19 — Last Supper institution (real-presence Lukan anchor)"

    def test_gethsemane_humanity_present(self):
        c = [e for e in self.ec.for_verse("luk", 22, 44) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.3 missing Lk 22:44 — Gethsemane sweat (true-humanity anchor against Apollinarianism)"

    def test_good_thief_paradise_present(self):
        c = [e for e in self.ec.for_verse("luk", 23, 43) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.3 missing Lk 23:43 — good thief (immediate-saints-to-paradise canonical anchor)"

    def test_emmaus_breaking_of_bread_present(self):
        c = [e for e in self.ec.for_verse("luk", 24, 30) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.3 missing Lk 24:30 — Emmaus breaking-of-bread (every-Eucharist-recognition anchor)"

    def test_ascension_present(self):
        c = [e for e in self.ec.for_verse("luk", 24, 51) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.3 missing Lk 24:51 — Ascension (Lukan canonical anchor)"

    def test_meta_documents_gamma_4_3_expansion(self):
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_source = data["_meta"]["source"]
        assert "γ.4.3" in meta_source, "γ.4.3 must be referenced in _meta.source"
        assert "Cyril-of-Alexandria-on-Luke" in meta_source or "Cyril-on-Luke" in meta_source, (
            "γ.4.3 _meta.source should describe Cyril-on-Luke"
        )
        assert "Payne Smith" in meta_source, "γ.4.3 _meta.source should cite R. Payne Smith"


class TestGamma45JubileesSeedWave:
    """γ.4.5 — Mäṣḥafä Kufāle / Book of Jubilees seed wave. Opens
    the SECOND uniquely-Tewahedo canonical text on the same Mäṣḥafä-
    Hēnok-style trajectory as γ.4.4. 40 verse-keyed seed entries
    spanning all 50 chapters of Jubilees (book code 'jub'). Mirrors
    the γ.4.4 first-wave pattern: broad coverage now, substantive-
    detail γ.4.5.B-E waves possible later.

    Pins:
    - Jubilees substantively seeded (≥40 jub entries across chs 1-50).
    - All major narrative blocks covered: Sinai prologue + Creation
      + Eden + Watchers + Noahide covenant + Division of earth +
      Mastema + Abraham + Decline-eschatology + Jacob + Joseph +
      Exodus-Passover-Sabbath finale.
    - Jubilees enters the corpus as a distinct voice.
    - Signature passages: 1:1 (Sinai-prologue second-Torah framing),
      4:17 (Enoch as first scribe — parallel to 1En 12:4), 6:32
      (364-day calendar — Tewahedo Bāḥrä Ḥasab doubled-canonical
      anchor with 1En 72:32), 8:19 (Eden/Sinai/Zion three holy
      mountains — Tewahedo sacred-geography), 9:13 (Ham's portion —
      Tewahedo Hamitic identity anchor), 10:8 (Mastema petition —
      Tewahedo non-dualist demonology), 18:9 (Mastema-as-Akedah-
      accuser — Tewahedo theodicy preserved), 21:10 ('books of
      Enoch' cited within Jubilees — inter-canonical-witness),
      32:18 (Levi consecrated to priesthood — Tewahedo priestly
      anchor), 48:9 (Mastema bound during Exodus — Tewahedo Holy-
      Week anchor), 50:6 (Sabbath finale — Tewahedo Saturday-
      Sabbath-and-Sunday-Lord's-Day tradition).
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def test_jubilees_substantively_seeded(self):
        jub_entries = []
        for chapter in range(1, 51):
            for verse in range(1, 100):
                jub_entries.extend(
                    e for e in self.ec.for_verse("jub", chapter, verse) if e.father == "Jubilees (Ethiopian tradition)"
                )
        assert len(jub_entries) >= 40, f"γ.4.5 expected ≥40 Jubilees entries across chs 1-50; found {len(jub_entries)}"

    def test_all_jubilees_narrative_blocks_covered(self):
        def has_entry_in(start, end):
            for chapter in range(start, end + 1):
                for verse in range(1, 100):
                    for entry in self.ec.for_verse("jub", chapter, verse):
                        if entry.father == "Jubilees (Ethiopian tradition)":
                            return True
            return False

        assert has_entry_in(1, 2), "γ.4.5 missing Sinai prologue + Creation (Jub 1-2)"
        assert has_entry_in(3, 4), "γ.4.5 missing Eden + generations (Jub 3-4)"
        assert has_entry_in(5, 6), "γ.4.5 missing Watchers + Noahide covenant (Jub 5-6)"
        assert has_entry_in(7, 10), "γ.4.5 missing Division of earth + Mastema (Jub 7-10)"
        assert has_entry_in(11, 22), "γ.4.5 missing Abraham cycle (Jub 11-22)"
        assert has_entry_in(23, 23), "γ.4.5 missing Decline + eschatology (Jub 23)"
        assert has_entry_in(24, 36), "γ.4.5 missing Jacob cycle (Jub 24-36)"
        assert has_entry_in(37, 45), "γ.4.5 missing Joseph cycle (Jub 37-45)"
        assert has_entry_in(46, 50), "γ.4.5 missing Egypt + Exodus + Passover + Sabbath finale (Jub 46-50)"

    def test_jubilees_milestone_count_at_or_above_seed(self):
        # Per feedback_share_pin_pattern: converted from γ.4.5 share-pin
        # (Jub ≥3% as "distinct voice") to absolute-count milestone pin
        # (≥40 entries = seed wave size). Invariant historical-achievement
        # pin; does not break mechanically when later γ-clusters dilute
        # the Jubilees share.
        jub_count = sum(
            1
            for verse_entries in self.ec._by_verse.values()
            for entry in verse_entries
            if entry.father == "Jubilees (Ethiopian tradition)"
        )
        assert jub_count >= 40, f"γ.4.5 milestone: expected Jubilees count ≥40 entries (seed wave); actual {jub_count}"

    def test_sinai_prologue_second_torah_framing_present(self):
        e = [x for x in self.ec.for_verse("jub", 1, 1) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5 missing Jub 1:1 — Sinai-prologue second-Torah framing"

    def test_enoch_as_first_scribe_present(self):
        e = [x for x in self.ec.for_verse("jub", 4, 17) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5 missing Jub 4:17 — Enoch as first scribe (parallel 1En 12:4)"

    def test_364_day_calendar_doubled_anchor_present(self):
        e = [x for x in self.ec.for_verse("jub", 6, 32) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5 missing Jub 6:32 — 364-day calendar (Tewahedo Bāḥrä Ḥasab doubled anchor)"

    def test_three_holy_mountains_present(self):
        e = [x for x in self.ec.for_verse("jub", 8, 19) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5 missing Jub 8:19 — Eden / Sinai / Zion three holy mountains"

    def test_hamitic_identity_anchor_present(self):
        e = [x for x in self.ec.for_verse("jub", 9, 13) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5 missing Jub 9:13 — Ham's portion (Tewahedo Hamitic identity anchor)"

    def test_mastema_petition_present(self):
        e = [x for x in self.ec.for_verse("jub", 10, 8) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5 missing Jub 10:8 — Mastema petition (Tewahedo non-dualist demonology)"

    def test_mastema_as_akedah_accuser_present(self):
        e = [x for x in self.ec.for_verse("jub", 18, 9) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5 missing Jub 18:9 — Mastema-as-Akedah-accuser (Tewahedo theodicy)"

    def test_books_of_enoch_cited_within_jubilees_present(self):
        e = [x for x in self.ec.for_verse("jub", 21, 10) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5 missing Jub 21:10 — 'books of Enoch' cited within Jubilees (inter-canonical witness)"

    def test_levi_priesthood_present(self):
        e = [x for x in self.ec.for_verse("jub", 32, 18) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5 missing Jub 32:18 — Levi consecrated to priesthood (Tewahedo priestly anchor)"

    def test_mastema_bound_during_exodus_present(self):
        e = [x for x in self.ec.for_verse("jub", 48, 9) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5 missing Jub 48:9 — Mastema bound during Exodus (Tewahedo Holy-Week anchor)"

    def test_sabbath_finale_present(self):
        e = [x for x in self.ec.for_verse("jub", 50, 6) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5 missing Jub 50:6 — Sabbath finale (Tewahedo Saturday-Sabbath tradition)"


class TestGamma45BJubileesWatchersMastemaWave:
    """γ.4.5.B — Mäṣḥafä Kufāle / Book of Jubilees Watchers + Mastema
    detail wave. Substantively expands Jub 5-10 (Watchers cascade
    + Flood judgment + Noahide covenant + 364-day calendar defense
    + Noah's seven commandments + geographic division + binding of
    demons + Mastema 1/10 permission + medical book to Noah + Tower
    of Babel reversal). Mirrors the γ.4.4.B detail-wave pattern.
    +40 entries on chs 5-10 (after γ.4.5 seed already covered 7
    verses in this range, total Jubilees chs 5-10 coverage rises
    from 7 to 47 entries).

    Pins:
    - Jub 5-10 substantively expanded (≥40 NEW entries beyond seed).
    - Day-of-Atonement / Tewahedo-Astereyo anchor (5:17).
    - Tewahedo dietary-law anchor (6:7 — no blood consumption).
    - Feast-of-Weeks pre-Mosaic anchor (6:17 — Pentecost antecedent).
    - 364-day calendar defense / Bāḥrä Ḥasab apologia (6:35).
    - Canaan-not-Ham anti-racial reading (7:13).
    - Inter-canonical witness — Noah cites Enoch (7:34).
    - Shem-blessing-Tewahedo-geography (8:21 — Red Sea = Shem's portion).
    - Anti-conquest oath until judgment (9:14).
    - Binding of all demons (10:7) + Mastema 1/10 permission (10:9) —
      Tewahedo non-dualist demonology with numerical bound.
    - Medical book to Noah (10:11) — Tewahedo mädḫanit tradition warrant.
    - Tower of Babel reversed by divine wind (10:26) — Pentecost antitype.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def _jub_entries_in(self, start_ch: int, end_ch: int):
        out = []
        for chapter in range(start_ch, end_ch + 1):
            for verse in range(1, 100):
                out.extend(
                    e for e in self.ec.for_verse("jub", chapter, verse) if e.father == "Jubilees (Ethiopian tradition)"
                )
        return out

    def test_jub_5_through_10_substantively_expanded(self):
        # γ.4.5 seed covered 7 verses in chs 5-10; γ.4.5.B adds 40
        # more for 47 total. Threshold ≥40 protects the wave intent
        # without locking the exact count.
        entries = self._jub_entries_in(5, 10)
        assert len(entries) >= 40, f"γ.4.5.B expected ≥40 Jubilees entries in chs 5-10; found {len(entries)}"

    def test_watchers_section_substantively_covered(self):
        # Jub 5 — Watcher judgment + Flood — needs broad coverage,
        # not just the 5:1 seed.
        entries = self._jub_entries_in(5, 5)
        assert len(entries) >= 6, (
            f"γ.4.5.B expected ≥6 Jubilees entries in ch 5 (Watcher judgment); found {len(entries)}"
        )

    def test_noahide_covenant_section_substantively_covered(self):
        # Jub 6 — Noahide covenant + calendar legislation — central
        # Tewahedo theological section.
        entries = self._jub_entries_in(6, 6)
        assert len(entries) >= 8, (
            f"γ.4.5.B expected ≥8 Jubilees entries in ch 6 (Noahide covenant + calendar); found {len(entries)}"
        )

    def test_mastema_chapter_substantively_covered(self):
        # Jub 10 — demon-binding + Mastema 1/10 permission +
        # medical book + Tower of Babel — Tewahedo demonology core.
        entries = self._jub_entries_in(10, 10)
        assert len(entries) >= 7, (
            f"γ.4.5.B expected ≥7 Jubilees entries in ch 10 (Mastema + Babel); found {len(entries)}"
        )

    def test_day_of_atonement_astereyo_anchor_present(self):
        # Jub 5:17 — annual atonement-by-turning-once-a-year, set in
        # the Watchers-judgment context. Tewahedo Astereyo warrant.
        e = [x for x in self.ec.for_verse("jub", 5, 17) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.B missing Jub 5:17 — Day of Atonement / Astereyo anchor"

    def test_no_blood_consumption_dietary_anchor_present(self):
        # Jub 6:7 — pre-Mosaic prohibition. Tewahedo dietary law anchor.
        e = [x for x in self.ec.for_verse("jub", 6, 7) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.B missing Jub 6:7 — no blood consumption (Tewahedo dietary anchor)"

    def test_feast_of_weeks_pre_mosaic_anchor_present(self):
        # Jub 6:17 — Pentecost established with Noah, not Moses.
        # Tewahedo Pärräqlēṭos antecedent.
        e = [x for x in self.ec.for_verse("jub", 6, 17) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.B missing Jub 6:17 — Feast of Weeks pre-Mosaic (Pentecost antecedent)"

    def test_364_day_calendar_defense_anchor_present(self):
        # Jub 6:35 — lunar-reckoning critique. Bāḥrä Ḥasab apologia.
        e = [x for x in self.ec.for_verse("jub", 6, 35) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.B missing Jub 6:35 — 364-day calendar defense (Bāḥrä Ḥasab apologia)"

    def test_canaan_not_ham_anti_racial_anchor_present(self):
        # Jub 7:13 — Canaan (not Ham) saw nakedness. Tewahedo anti-
        # racial reading of the Genesis 9 curse.
        e = [x for x in self.ec.for_verse("jub", 7, 13) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.B missing Jub 7:13 — Canaan not Ham (anti-racial reading)"

    def test_noah_cites_enoch_intercanonical_witness_present(self):
        # Jub 7:34 — Noah commands his sons by Enoch's authority.
        # Inter-canonical witness doubled (Jubilees citing Enoch).
        e = [x for x in self.ec.for_verse("jub", 7, 34) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.B missing Jub 7:34 — Noah cites Enoch (inter-canonical witness)"

    def test_anti_conquest_oath_anchor_present(self):
        # Jub 9:14 — Noah binds sons by oath against seizing
        # another's portion. Tewahedo anti-conquest theology.
        e = [x for x in self.ec.for_verse("jub", 9, 14) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.B missing Jub 9:14 — anti-conquest oath until judgment day"

    def test_binding_of_all_demons_anchor_present(self):
        # Jub 10:7 — God's first response is TOTAL binding.
        # Tewahedo theodicy: divine intention is full restraint.
        e = [x for x in self.ec.for_verse("jub", 10, 7) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.B missing Jub 10:7 — binding of all demons (divine intent of full restraint)"

    def test_mastema_one_tenth_permission_anchor_present(self):
        # Jub 10:9 — God grants 1/10 of demons to remain free.
        # Tewahedo numerical-bounded-evil anchor.
        e = [x for x in self.ec.for_verse("jub", 10, 9) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.B missing Jub 10:9 — Mastema 1/10 permission (numerical-bounded-evil)"

    def test_medical_book_to_noah_anchor_present(self):
        # Jub 10:11 — angels teach Noah herbal medicines paired
        # with demonological diagnoses. Tewahedo mädḫanit tradition.
        e = [x for x in self.ec.for_verse("jub", 10, 11) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.B missing Jub 10:11 — medical book to Noah (mädḫanit tradition)"

    def test_tower_of_babel_reversed_by_wind_anchor_present(self):
        # Jub 10:26 — Tower overthrown by mighty wind. Pentecost
        # antitype: the same Spirit reverses Babel at Acts 2.
        e = [x for x in self.ec.for_verse("jub", 10, 26) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.B missing Jub 10:26 — Tower reversed by wind (Pentecost antitype)"


class TestGamma45CJubileesAbrahamCycleWave:
    """γ.4.5.C — Mäṣḥafä Kufāle / Book of Jubilees Abraham-cycle detail
    wave. Substantively expands Jub 11-22 (idolatry decline through
    Serug + Abram's argument to Terah against idols + Haran's death
    in failed idol-rescue + Hebrew tongue restored to Abram by the
    angel of presence + departure from Ur + Bethel altar + Melchizedek
    tithe + covenant of pieces dated to Pentecost + circumcision-on-
    the-eighth-day Tewahedo anchor + angels of presence created
    circumcised + Isaac's birth on Pentecost + pre-Mosaic Feast of
    Tabernacles instituted by Abraham + Akedah at Mt Moriah = Mt Zion
    + Mastema-as-accuser overthrown by angel-of-presence between
    Abraham and Mastema + 7-day Akedah commemorative festival +
    Sarah's Machpelah burial as Marian-Assumption type + Mastema-
    repulsion clause in Abraham's blessing of Jacob + Abraham's
    testament love-of-neighbour command to all sons + Abraham's
    priestly instructions on no-blood-consumption + Abraham's
    celebration of Feast of Weeks with both Isaac and Ishmael at the
    altar + Abraham's direct blessing of Jacob over Isaac's potential
    Esau-favoritism — Tewahedo Solomonic-dynasty Jacobite anchor via
    Kǝbrä Nägäśt tradition). Mirrors the γ.4.4.B + γ.4.5.B detail-
    wave pattern. +40 entries on chs 11-22 (after γ.4.5 seed already
    covered 7 verses in this range, total Jubilees chs 11-22 coverage
    rises from 7 to 47 entries — substantive-detail parity with
    γ.4.5.B Jub 5-10).

    Pins:
    - Jub 11-22 substantively expanded (≥40 NEW entries beyond seed).
    - Pre-Mosaic agrarian-priestly anchor: Abram drives ravens (11:18).
    - Tewahedo language-warrant: Hebrew tongue restored (12:25).
    - Pre-Mosaic legitimate altar: Bethel (13:8) — Tewahedo
      patriarchal-Anaphora warrant.
    - Pre-Mosaic tithe: Melchizedek (13:25) — Tewahedo ǝʾǝsär anchor.
    - Triple-Pentecost: covenant of pieces dated to Pentecost (14:1).
    - Tewahedo distinctive Christian circumcision: 15:14 + 15:25
      + 15:27 (angels of presence created circumcised).
    - Old/New Pentecost doubled: Isaac born on Pentecost (16:13).
    - Pre-Mosaic Feast of Tabernacles instituted by Abraham (16:20).
    - Akedah-as-Passover: Mastema accusation on Passover date (17:15).
    - Eucharistic fourfold-altar anchor: Mt Moriah = Mt Zion (18:13).
    - Tewahedo Holy-Week shape antecedent: 7-day Akedah commemoration
      (18:18).
    - Marian-Assumption type: Sarah's Machpelah burial (19:3).
    - Patriarchal-blessing Mastema-repulsion clause (19:28).
    - Love-of-neighbour patriarchal-testament content (20:2).
    - No-blood-consumption priestly emphasis (21:7) — Tewahedo
      dietary-law TRIPLE witness with 6:7 + 7:34.
    - Tewahedo pastoral inclusivity: Abraham's Feast of Weeks with
      Isaac AND Ishmael (22:1).
    - Solomonic-dynasty Tewahedo-Jacobite anchor: Abraham's direct
      blessing of Jacob (22:11) — Kǝbrä Nägäśt foundational verse.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def _jub_entries_in(self, start_ch: int, end_ch: int):
        out = []
        for chapter in range(start_ch, end_ch + 1):
            for verse in range(1, 100):
                out.extend(
                    e for e in self.ec.for_verse("jub", chapter, verse) if e.father == "Jubilees (Ethiopian tradition)"
                )
        return out

    def test_jub_11_through_22_substantively_expanded(self):
        # γ.4.5 seed covered 7 verses in chs 11-22; γ.4.5.C adds 40
        # more for 47 total. Threshold ≥40 protects the wave intent
        # without locking the exact count.
        entries = self._jub_entries_in(11, 22)
        assert len(entries) >= 40, f"γ.4.5.C expected ≥40 Jubilees entries in chs 11-22; found {len(entries)}"

    def test_abram_early_life_chapters_substantively_covered(self):
        # Jub 11-13 — idolatry decline + Abram's monotheism +
        # departure from Ur. Tewahedo Andǝmta foundational range.
        entries = self._jub_entries_in(11, 13)
        assert len(entries) >= 10, (
            f"γ.4.5.C expected ≥10 Jubilees entries in chs 11-13 (Abram's early life); found {len(entries)}"
        )

    def test_covenant_and_circumcision_chapters_substantively_covered(self):
        # Jub 14-15 — covenant of pieces + circumcision covenant.
        # Tewahedo distinctive Christian circumcision anchor range.
        entries = self._jub_entries_in(14, 15)
        assert len(entries) >= 8, (
            f"γ.4.5.C expected ≥8 Jubilees entries in chs 14-15 (covenant + circumcision); found {len(entries)}"
        )

    def test_isaac_birth_and_tabernacles_chapter_substantively_covered(self):
        # Jub 16 — Isaac's birth on Pentecost + pre-Mosaic Feast of
        # Tabernacles instituted by Abraham. Tewahedo doubled-festal
        # canonical anchor.
        entries = self._jub_entries_in(16, 16)
        assert len(entries) >= 3, (
            f"γ.4.5.C expected ≥3 Jubilees entries in ch 16 (Isaac + Tabernacles); found {len(entries)}"
        )

    def test_akedah_chapters_substantively_covered(self):
        # Jub 17-18 — Akedah preamble + Akedah proper.
        # Tewahedo Pascha / Akedah-as-Passover canonical range.
        entries = self._jub_entries_in(17, 18)
        assert len(entries) >= 6, f"γ.4.5.C expected ≥6 Jubilees entries in chs 17-18 (Akedah); found {len(entries)}"

    def test_testament_and_priestly_chapters_substantively_covered(self):
        # Jub 20-22 — Abraham's testament + priestly instructions +
        # final blessing of Jacob. Tewahedo patriarchal-charge range.
        entries = self._jub_entries_in(20, 22)
        assert len(entries) >= 7, (
            f"γ.4.5.C expected ≥7 Jubilees entries in chs 20-22 (testament + priestly + blessing); found {len(entries)}"
        )

    def test_abram_drives_ravens_anchor_present(self):
        # Jub 11:18 — boy-Abram protects sown seed from Mastema's
        # ravens. Tewahedo agrarian-priestly anchor.
        e = [x for x in self.ec.for_verse("jub", 11, 18) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.C missing Jub 11:18 — Abram drives ravens (agrarian-priestly anchor)"

    def test_hebrew_tongue_restored_anchor_present(self):
        # Jub 12:25 — angel of presence restores pre-Babel Hebrew
        # tongue to Abram. Tewahedo Ge'ez liturgical-language warrant.
        e = [x for x in self.ec.for_verse("jub", 12, 25) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.C missing Jub 12:25 — Hebrew tongue restored by angel of presence"

    def test_bethel_altar_anchor_present(self):
        # Jub 13:8 — pre-Mosaic legitimate altar at Bethel.
        # Tewahedo patriarchal-Anaphora warrant.
        e = [x for x in self.ec.for_verse("jub", 13, 8) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.C missing Jub 13:8 — Bethel altar (patriarchal-Anaphora warrant)"

    def test_melchizedek_tithe_anchor_present(self):
        # Jub 13:25 — first canonical tithe paid to Melchizedek.
        # Tewahedo monastic ǝʾǝsär anchor.
        e = [x for x in self.ec.for_verse("jub", 13, 25) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.C missing Jub 13:25 — Melchizedek tithe (Tewahedo ǝʾǝsär anchor)"

    def test_covenant_of_pieces_pentecost_date_anchor_present(self):
        # Jub 14:1 — covenant of pieces dated to new moon of third
        # month (Pentecost). TRIPLE Pentecost anchor with Jub 6:17
        # (Noah) and Sinai (Ex 19).
        e = [x for x in self.ec.for_verse("jub", 14, 1) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.C missing Jub 14:1 — covenant of pieces on Pentecost (triple-anchor)"

    def test_eighth_day_circumcision_perpetual_anchor_present(self):
        # Jub 15:14 — eighth-day circumcision required, no flexibility.
        # Tewahedo distinctive Christian circumcision anchor.
        e = [x for x in self.ec.for_verse("jub", 15, 14) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.C missing Jub 15:14 — eighth-day circumcision (Tewahedo distinctive)"

    def test_angels_of_presence_circumcised_anchor_present(self):
        # Jub 15:27 — angels of presence and sanctification created
        # circumcised. Tewahedo cosmic-circumcision anchor.
        e = [x for x in self.ec.for_verse("jub", 15, 27) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.C missing Jub 15:27 — angels of presence created circumcised"

    def test_isaac_born_on_pentecost_anchor_present(self):
        # Jub 16:13 — Isaac's birth dated to feast of first-fruits
        # (Pentecost). Tewahedo Old-New-Covenant Pentecost doubled
        # anchor.
        e = [x for x in self.ec.for_verse("jub", 16, 13) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.C missing Jub 16:13 — Isaac born on Pentecost (doubled anchor)"

    def test_pre_mosaic_tabernacles_anchor_present(self):
        # Jub 16:20 — Abraham institutes the FIRST Feast of
        # Tabernacles, seven days, pre-Mosaic. Tewahedo Mäskäl-week
        # canonical antecedent.
        e = [x for x in self.ec.for_verse("jub", 16, 20) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.C missing Jub 16:20 — pre-Mosaic Feast of Tabernacles instituted by Abraham"

    def test_akedah_as_passover_date_anchor_present(self):
        # Jub 17:15 — Mastema accuses Abraham on the eve-of-Passover
        # date (first month, 12th day). Tewahedo Akedah-as-Passover
        # canonical anchor.
        e = [x for x in self.ec.for_verse("jub", 17, 15) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.C missing Jub 17:15 — Mastema accuses on Passover-date (Akedah-as-Passover)"

    def test_moriah_equals_zion_anchor_present(self):
        # Jub 18:13 — explicit identification of Mt Moriah (Akedah)
        # with Mt Zion (Temple mount). Tewahedo eucharistic fourfold-
        # altar canonical anchor (Moriah-Zion-Calvary-Heavenly-Zion).
        e = [x for x in self.ec.for_verse("jub", 18, 13) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.C missing Jub 18:13 — Moriah = Zion (fourfold-altar anchor)"

    def test_seven_day_akedah_festival_anchor_present(self):
        # Jub 18:18 — Abraham institutes a 7-day Akedah-commemoration
        # festival. Tewahedo Holy-Week shape antecedent.
        e = [x for x in self.ec.for_verse("jub", 18, 18) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.C missing Jub 18:18 — 7-day Akedah festival (Holy-Week shape antecedent)"

    def test_mastema_repulsion_in_blessing_anchor_present(self):
        # Jub 19:28 — Abraham's blessing of Jacob includes a Mastema-
        # repulsion clause. Tewahedo patriarchal-blessing template.
        e = [x for x in self.ec.for_verse("jub", 19, 28) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.C missing Jub 19:28 — Mastema-repulsion in patriarchal blessing"

    def test_love_of_neighbour_testament_anchor_present(self):
        # Jub 20:2 — Abraham's testament commands love-of-neighbour.
        # Tewahedo canonical 'second great commandment' antecedent.
        e = [x for x in self.ec.for_verse("jub", 20, 2) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.C missing Jub 20:2 — love-of-neighbour testament command"

    def test_priestly_no_blood_anchor_present(self):
        # Jub 21:7 — Abraham's priestly instructions to Isaac on
        # no-blood-consumption. Tewahedo dietary-law TRIPLE witness
        # with 6:7 + 7:34.
        e = [x for x in self.ec.for_verse("jub", 21, 7) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.C missing Jub 21:7 — priestly no-blood instruction (TRIPLE dietary witness)"

    def test_abraham_feast_of_weeks_inclusivity_anchor_present(self):
        # Jub 22:1 — Abraham celebrates Feast of Weeks with BOTH
        # Isaac and Ishmael at the altar. Tewahedo pastoral
        # inclusivity anchor.
        e = [x for x in self.ec.for_verse("jub", 22, 1) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.C missing Jub 22:1 — Abraham's Feast of Weeks with Isaac AND Ishmael"

    def test_abraham_blesses_jacob_solomonic_anchor_present(self):
        # Jub 22:11 — Abraham's direct blessing of Jacob (his
        # preferred grandson). Tewahedo Solomonic-dynasty-Jacobite
        # anchor via Kǝbrä Nägäśt tradition.
        e = [x for x in self.ec.for_verse("jub", 22, 11) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.C missing Jub 22:11 — Abraham blesses Jacob (Solomonic-Jacobite anchor)"


class TestGamma45DJubileesJacobCycleWave:
    """γ.4.5.D — Mäṣḥafä Kufāle / Book of Jubilees Jacob-cycle detail
    wave. Substantively expands Jub 24-36 (Esau sells birthright +
    Isaac in Gerar + Rebekah's Spirit-inspired blessing of Jacob with
    resurrection-unto-eternal-life clause + Jacob receives Isaac's
    blessing + Jacob's flight + Bethel ladder vision Marian-typology +
    Jacob's pillar + double-tithe vow + Jacob in Haran + Leah-for-
    Rachel substitution + Leah's first conception + Jacob-Esau
    reconciliation with preserved fraternal love + twice-yearly gift-
    sending to parents + Dinah at twelve years + Levi's priesthood
    EARNED by zeal at Shechem + heavenly-tablets righteousness
    inscription + Isaac's blessing of Levi BEFORE Judah priestly-
    precedence + Judah's Davidic-messianic blessing + patriarchal
    manuscript transmission + Jacob's institution of double-tithe at
    Bethel + seven heavenly tablets given to Jacob + Deborah-nurse
    Bethel oak + Rachel's death bearing Benjamin + Reuben's incest +
    Reuben's voluntary confession + Jacob's clemency-by-confession +
    Joseph sold for twenty pieces of gold + Day of Atonement linked
    to Jacob's Joseph-grief + Rebekah's deathbed hope for Esau's
    repentance + Esau and Jacob jointly bury Rebekah at Machpelah +
    Isaac's intermediate-state-as-fellowship phrase + Isaac's love-
    of-brother testament). Mirrors the γ.4.4.B / γ.4.5.B / γ.4.5.C
    detail-wave pattern. +40 entries on chs 24-36 (after γ.4.5 seed
    already covered 7 verses in this range, total Jubilees chs 24-36
    coverage rises from 7 to 47 entries — substantive-detail parity
    with γ.4.5.B Jub 5-10 and γ.4.5.C Jub 11-22).

    Pins:
    - Jub 24-36 substantively expanded (≥40 NEW entries beyond seed).
    - Three-generation patriarchal-altar chain: Isaac's Beersheba
      altar (24:22) joins Abram's Bethel altar (13:8) + Jacob's
      Bethel altar (32:1).
    - Pre-Pentecostal Spirit-inspired blessing: Rebekah (25:14) —
      Tewahedo prophetic-utterance OT-typological anchor.
    - Resurrection-unto-eternal-life clause in Rebekah's blessing
      (25:23) — Tewahedo Tǝnśaʾe matriarchal-canonical anchor.
    - Bethel ladder vision (27:19) — Tewahedo Marian-ladder type
      in Wǝddase Maryam.
    - Jacob's double-tithe vow (27:27 + 32:9) — Tewahedo ǝʾǝsär
      double-pattern canonical anchor.
    - Levi's priesthood EARNED by zeal at Shechem (30:18) —
      Tewahedo priesthood-by-zeal-and-descent doubled warrant.
    - Heavenly-tablets righteousness inscription (30:23) —
      Tewahedo täwlǝd-bä-mäṣǝḥaf book-of-life doctrine anchor.
    - Priestly precedence over royal: Isaac blesses Levi BEFORE
      Judah (31:14) — Tewahedo ecclesiology anchor.
    - Davidic-messianic blessing of Judah (31:18) — Tewahedo
      Solomonic-dynasty Davidic claim via Kǝbrä Nägäśt.
    - Patriarchal manuscript transmission (31:23) — Tewahedo
      monastic-scribal canonical-inheritance warrant.
    - Seven heavenly tablets given to Jacob (32:21) — Tewahedo
      Mäṣḥafä-zä-säma'i doctrine canonical anchor.
    - Reuben's voluntary confession + Jacob's clemency (33:9) —
      Tewahedo näsḫa absolution principle canonical anchor.
    - Day of Atonement linked to Jacob's Joseph-grief (34:18) —
      Tewahedo Astereyo TRIPLED canonical anchor with Jub 5:17
      and Jub 6:10.
    - Rebekah's hope for Esau's repentance (35:6) — Tewahedo
      eschatological-hope canonical anchor.
    - Isaac's 'eternal house with the fathers' phrase (36:1) —
      Tewahedo funeral-liturgy verbal-inheritance canonical anchor.
    - Love-of-brother testament triad: Abraham (Jub 20:2) + Isaac
      (Jub 36:7) + Mosaic Lev 19:18.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def _jub_entries_in(self, start_ch: int, end_ch: int):
        out = []
        for chapter in range(start_ch, end_ch + 1):
            for verse in range(1, 100):
                out.extend(
                    e for e in self.ec.for_verse("jub", chapter, verse) if e.father == "Jubilees (Ethiopian tradition)"
                )
        return out

    def test_jub_24_through_36_substantively_expanded(self):
        # γ.4.5 seed covered 7 verses in chs 24-36; γ.4.5.D adds 40
        # more for 47 total. Threshold ≥40 protects the wave intent
        # without locking the exact count.
        entries = self._jub_entries_in(24, 36)
        assert len(entries) >= 40, f"γ.4.5.D expected ≥40 Jubilees entries in chs 24-36; found {len(entries)}"

    def test_esau_isaac_gerar_chapter_substantively_covered(self):
        # Jub 24 — Esau's birthright + Isaac in Gerar. Tewahedo
        # patriarchal-altar three-generation chain anchor range.
        entries = self._jub_entries_in(24, 24)
        assert len(entries) >= 3, (
            f"γ.4.5.D expected ≥3 Jubilees entries in ch 24 (Esau/Isaac in Gerar); found {len(entries)}"
        )

    def test_rebekah_blessing_chapters_substantively_covered(self):
        # Jub 25-26 — Rebekah's Spirit-inspired blessing + Jacob
        # receives Isaac's blessing. Tewahedo matriarchal-canonical
        # range.
        entries = self._jub_entries_in(25, 26)
        assert len(entries) >= 7, (
            f"γ.4.5.D expected ≥7 Jubilees entries in chs 25-26 (Rebekah + Isaac blessing); found {len(entries)}"
        )

    def test_bethel_vision_and_haran_chapters_substantively_covered(self):
        # Jub 27-28 — Bethel ladder vision + Jacob's pillar + tithe
        # vow + Haran sojourn. Tewahedo täbot canonical-antecedent
        # range.
        entries = self._jub_entries_in(27, 28)
        assert len(entries) >= 6, (
            f"γ.4.5.D expected ≥6 Jubilees entries in chs 27-28 (Bethel vision + Haran); found {len(entries)}"
        )

    def test_levi_priesthood_chapters_substantively_covered(self):
        # Jub 30-32 — Dinah + Shechem + Levi's zeal + Isaac's
        # blessing of Levi + Bethel altar + tithe-of-tithes + seven
        # heavenly tablets. Tewahedo priestly-canonical range.
        entries = self._jub_entries_in(30, 32)
        assert len(entries) >= 13, (
            f"γ.4.5.D expected ≥13 Jubilees entries in chs 30-32 (Levi's priesthood); found {len(entries)}"
        )

    def test_isaac_testament_chapter_substantively_covered(self):
        # Jub 36 — Isaac's testament (eternal-house phrase +
        # love-of-brother triad). Tewahedo funeral-liturgy
        # canonical-verbal range.
        entries = self._jub_entries_in(36, 36)
        assert len(entries) >= 3, (
            f"γ.4.5.D expected ≥3 Jubilees entries in ch 36 (Isaac's testament); found {len(entries)}"
        )

    def test_isaac_beersheba_altar_anchor_present(self):
        # Jub 24:22 — Isaac's Beersheba altar continues the patriarchal-
        # altar chain Abram(13:8) → Isaac → Jacob(32:1). Tewahedo
        # Anaphora-of-Patriarchs canonical warrant.
        e = [x for x in self.ec.for_verse("jub", 24, 22) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.D missing Jub 24:22 — Isaac's Beersheba altar (three-generation chain)"

    def test_rebekah_spirit_inspired_blessing_anchor_present(self):
        # Jub 25:14 — 'spirit of righteousness descended into her
        # mouth' — pre-Pentecostal Spirit-inspired-blessing canonical
        # episode. Tewahedo näfsä-qǝddus OT-typological anchor.
        e = [x for x in self.ec.for_verse("jub", 25, 14) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.D missing Jub 25:14 — Rebekah's Spirit-inspired blessing"

    def test_resurrection_unto_eternal_life_clause_anchor_present(self):
        # Jub 25:23 — explicit resurrection-unto-eternal-life clause
        # in Rebekah's blessing. Tewahedo Tǝnśaʾe matriarchal-canonical
        # anchor; mid-2nd-c. BCE Jewish resurrection witness.
        e = [x for x in self.ec.for_verse("jub", 25, 23) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.D missing Jub 25:23 — resurrection-unto-eternal-life clause"

    def test_bethel_ladder_marian_type_anchor_present(self):
        # Jub 27:19 — Jacob's ladder. Tewahedo Marian-ladder type
        # invoked in Wǝddase Maryam Monday-evening cycle.
        e = [x for x in self.ec.for_verse("jub", 27, 19) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.D missing Jub 27:19 — Bethel ladder (Marian-ladder type)"

    def test_jacob_pillar_double_tithe_vow_anchor_present(self):
        # Jub 27:27 — Jacob's pillar + tithe-of-everything vow.
        # Tewahedo täbot canonical-antecedent + ǝʾǝsär comprehensive-
        # ness anchor.
        e = [x for x in self.ec.for_verse("jub", 27, 27) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.D missing Jub 27:27 — Jacob's pillar + double-tithe vow"

    def test_levi_priesthood_earned_by_zeal_anchor_present(self):
        # Jub 30:18 — Levi's priesthood EARNED by zeal at Shechem
        # (not just inherited). Tewahedo priesthood-by-zeal-AND-descent
        # doubled warrant.
        e = [x for x in self.ec.for_verse("jub", 30, 18) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.D missing Jub 30:18 — Levi's priesthood EARNED by zeal"

    def test_heavenly_tablets_righteousness_inscription_anchor_present(self):
        # Jub 30:23 — Simeon and Levi inscribed on heavenly tablets
        # as righteous. Tewahedo täwlǝd-bä-mäṣǝḥaf book-of-life
        # doctrine canonical anchor.
        e = [x for x in self.ec.for_verse("jub", 30, 23) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.D missing Jub 30:23 — heavenly-tablets righteousness inscription"

    def test_priestly_before_royal_blessing_anchor_present(self):
        # Jub 31:14 — Isaac blesses Levi (priestly) BEFORE Judah
        # (royal). Tewahedo ecclesiology priestly-precedence anchor.
        e = [x for x in self.ec.for_verse("jub", 31, 14) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.D missing Jub 31:14 — Isaac blesses Levi BEFORE Judah (priestly precedence)"

    def test_judah_davidic_messianic_blessing_anchor_present(self):
        # Jub 31:18 — 'in thee shall be found the salvation of
        # Israel' Judah blessing. Tewahedo Solomonic-dynasty Davidic
        # claim via Kǝbrä Nägäśt tradition.
        e = [x for x in self.ec.for_verse("jub", 31, 18) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.D missing Jub 31:18 — Judah's Davidic-messianic blessing"

    def test_patriarchal_manuscript_transmission_anchor_present(self):
        # Jub 31:23 — Isaac transmits 'the books of his fathers
        # Abraham' to Jacob. Tewahedo monastic-scribal canonical-
        # inheritance warrant.
        e = [x for x in self.ec.for_verse("jub", 31, 23) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.D missing Jub 31:23 — patriarchal manuscript transmission"

    def test_jacob_double_tithe_institution_anchor_present(self):
        # Jub 32:9 — Jacob institutes the tithe-to-priest + festive-
        # tithe-consumed-by-offerer double pattern at Bethel.
        # Tewahedo ǝʾǝsär double-pattern canonical anchor.
        e = [x for x in self.ec.for_verse("jub", 32, 9) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.D missing Jub 32:9 — Jacob's double-tithe institution"

    def test_seven_heavenly_tablets_anchor_present(self):
        # Jub 32:21 — angel gives Jacob seven heavenly tablets with
        # the full prophetic future. Tewahedo Mäṣḥafä-zä-säma'i
        # heavenly-book doctrine canonical anchor.
        e = [x for x in self.ec.for_verse("jub", 32, 21) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.D missing Jub 32:21 — seven heavenly tablets given to Jacob"

    def test_reuben_confession_jacob_clemency_anchor_present(self):
        # Jub 33:9 — Reuben's voluntary confession; Jacob 'smote him
        # not because Reuben had confessed.' Tewahedo näsḫa
        # absolution-by-confession principle canonical anchor.
        e = [x for x in self.ec.for_verse("jub", 33, 9) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.D missing Jub 33:9 — Reuben's confession + Jacob's clemency"

    def test_atonement_day_joseph_grief_anchor_present(self):
        # Jub 34:18 — Day of Atonement (10/7) connected to Jacob's
        # day of receiving Joseph-loss news. Tewahedo Astereyo
        # TRIPLED canonical anchor with Jub 5:17 and Jub 6:10.
        e = [x for x in self.ec.for_verse("jub", 34, 18) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.D missing Jub 34:18 — Day of Atonement linked to Jacob's Joseph-grief"

    def test_rebekah_hope_for_esau_repentance_anchor_present(self):
        # Jub 35:6 — Rebekah's deathbed hope that Esau will repent
        # and 'mercy will reach him.' Tewahedo eschatological-hope
        # matriarchal-canonical anchor.
        e = [x for x in self.ec.for_verse("jub", 35, 6) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.D missing Jub 35:6 — Rebekah's hope for Esau's repentance"

    def test_isaac_eternal_house_with_fathers_anchor_present(self):
        # Jub 36:1 — Isaac's 'eternal house where my fathers are.'
        # Tewahedo funeral-liturgy phrase canonical-verbal
        # inheritance anchor.
        e = [x for x in self.ec.for_verse("jub", 36, 1) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.D missing Jub 36:1 — Isaac's eternal-house-with-fathers phrase"

    def test_isaac_love_of_brother_testament_anchor_present(self):
        # Jub 36:7 — Isaac's 'love one another as your own selves'
        # testament. Tewahedo Maḫǝbär Qǝddus monastic-charism
        # canonical anchor; love-of-brother triad with Abraham
        # (Jub 20:2) + Mosaic Lev 19:18.
        e = [x for x in self.ec.for_verse("jub", 36, 7) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.D missing Jub 36:7 — Isaac's love-of-brother testament"


class TestGamma45EJubileesJosephExodusFinaleWave:
    """γ.4.5.E — Mäṣḥafä Kufāle / Book of Jubilees Joseph + Exodus-
    finale wave. CLOSES the γ.4.5 detail arc. Substantively expands
    Jub 37-50 (Esau-Jacob armed conflict + Joseph in Egypt + Potiphar's
    wife + Joseph's chastity grounded in patriarchal catechesis +
    Joseph's marriage to Asenath + Judah and Tamar with 'she is more
    righteous than I' confession + Joseph reveals himself + silver-cup
    test + Jacob's seven-day Beersheba pause + God's Immanuel-promise
    to descend with Jacob + Israelite genealogy at Egypt-descent +
    Jacob blesses Pharaoh + Joseph dies at 110 years with canonical
    biographical precision + new king who knew not Joseph + Moses'
    birth in tribulation period + three-day Moses-ark/Christ-tomb
    Pascal-typology + Pharaoh's-daughter's-compassion + Mastema-not-
    Lord at the lodging-attack + angelic orchestration of plagues +
    Red-Sea-crossing IS Passover + Passover blood-on-lintels restrains
    Mastema's firstborn-slaying + lamb-AND-wine canonical eucharistic-
    OT prototype + Passover-observance acquits-of-guilt + Sabbath as
    foretaste of holy kingdom + jubilee-of-jubilees eschatology with
    Satan permanently removed + strict Sabbath-prohibition list
    anchoring Tewahedo Saturday-Sabbath observance). Mirrors the
    γ.4.4.E arc-close pattern with the explicit all-sections-covered
    pin.

    Pins:
    - Jub 37-50 substantively expanded (≥40 NEW entries beyond seed).
    - γ.4.5 arc-close pin: all six major Jubilees narrative sections
      (1-4, 5-10, 11-22, 24-36, 37-45, 46-50) have substantive
      coverage at canonical-detail-wave depth.
    - Jubilees-arc-close milestone: Jubilees ≥200 entries (40 seed +
      4 × 40 detail waves).
    - Defensive-war canonical anchor: Esau-Jacob war (37:1).
    - Joseph's chastity-via-patriarchal-catechesis (39:10) — Tewahedo
      family-catechism canonical anchor.
    - 'She is more righteous than I' Judah-Tamar confession (41:25) —
      Tewahedo confessor's näsḫa-of-acknowledgment verbal anchor.
    - Jacob's seven-day Beersheba pause (44:1) — Tewahedo monastic-
      departure-pause canonical pattern.
    - God's Immanuel-descent-with-Jacob (44:5) — Tewahedo diaspora-
      presence theological anchor.
    - Patriarch blesses Gentile-king: Jacob blesses Pharaoh (45:13) —
      Tewahedo coronation-prayer canonical-patriarchal warrant.
    - Three-day Moses-ark / Christ-tomb Pascal-typology (47:5) —
      Tewahedo Easter-vigil canonical-OT prefiguration.
    - Mastema-not-Lord at the lodging (48:2) — Tewahedo theodicy
      canonical clarification of Ex 4:24.
    - Red-Sea crossing IS Passover (48:18) — Tewahedo Fasika
      doubled-celebration canonical anchor.
    - Passover blood-on-lintels restrains Mastema (49:2) — Tewahedo
      eucharistic-blood demonic-defense canonical anchor.
    - Lamb-AND-wine eucharistic-OT prototype (49:6) — Tewahedo
      Anaphora canonical-OT eucharistic-prototype anchor.
    - Passover-observance acquits-of-guilt (49:15) — Tewahedo
      liturgical-act-AS-atonement principle canonical anchor.
    - Jubilee-of-jubilees eschatology with Satan removed (50:4) —
      Tewahedo cosmic-territorial-cleansing eschatology anchor.
    - Sabbath as holy-kingdom-day (50:9) — Tewahedo Saturday-Sabbath
      foretaste-of-Kingdom canonical anchor.
    - Strict Sabbath-prohibition list (50:12) — Tewahedo Saturday-
      Sabbath canonical observance preservation anchor.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def _jub_entries_in(self, start_ch: int, end_ch: int):
        out = []
        for chapter in range(start_ch, end_ch + 1):
            for verse in range(1, 100):
                out.extend(
                    e for e in self.ec.for_verse("jub", chapter, verse) if e.father == "Jubilees (Ethiopian tradition)"
                )
        return out

    def test_jub_37_through_50_substantively_expanded(self):
        # γ.4.5 seed covered 11 verses in chs 37-50; γ.4.5.E adds 40
        # more for 51 total. Threshold ≥40 protects the wave intent.
        entries = self._jub_entries_in(37, 50)
        assert len(entries) >= 40, f"γ.4.5.E expected ≥40 Jubilees entries in chs 37-50; found {len(entries)}"

    def test_joseph_in_egypt_chapters_substantively_covered(self):
        # Jub 37-40 — Esau-Jacob war + Joseph in Egypt + Potiphar +
        # Joseph's rise. Tewahedo Joseph-as-Christ Holy-Week typology
        # canonical range.
        entries = self._jub_entries_in(37, 40)
        assert len(entries) >= 8, (
            f"γ.4.5.E expected ≥8 Jubilees entries in chs 37-40 (Esau war + Joseph); found {len(entries)}"
        )

    def test_judah_tamar_and_revelation_chapters_substantively_covered(self):
        # Jub 41-43 — Judah and Tamar + Joseph reveals himself +
        # silver-cup test. Tewahedo Marian-Tamar-Davidic-line range.
        entries = self._jub_entries_in(41, 43)
        assert len(entries) >= 7, (
            f"γ.4.5.E expected ≥7 Jubilees entries in chs 41-43 (Tamar + Joseph reveals); found {len(entries)}"
        )

    def test_jacob_to_egypt_chapters_substantively_covered(self):
        # Jub 44-45 — Jacob's Beersheba pause + Immanuel-descent
        # promise + genealogy + Jacob settled. Tewahedo Immanuel-
        # typology canonical range.
        entries = self._jub_entries_in(44, 45)
        assert len(entries) >= 6, (
            f"γ.4.5.E expected ≥6 Jubilees entries in chs 44-45 (Jacob to Egypt); found {len(entries)}"
        )

    def test_moses_birth_chapter_substantively_covered(self):
        # Jub 47 — Moses' birth + three-day-ark Pascal-typology +
        # Pharaoh's-daughter's-compassion. Tewahedo Moses-as-Christ
        # typology canonical range.
        entries = self._jub_entries_in(47, 47)
        assert len(entries) >= 4, f"γ.4.5.E expected ≥4 Jubilees entries in ch 47 (Moses' birth); found {len(entries)}"

    def test_exodus_passover_chapters_substantively_covered(self):
        # Jub 48-49 — Exodus + Mastema-not-Lord clarification +
        # angelic orchestration of plagues + Red-Sea-as-Passover +
        # Passover institution. Tewahedo Fasika canonical range.
        entries = self._jub_entries_in(48, 49)
        assert len(entries) >= 9, (
            f"γ.4.5.E expected ≥9 Jubilees entries in chs 48-49 (Exodus + Passover); found {len(entries)}"
        )

    def test_sabbath_jubilee_finale_chapter_substantively_covered(self):
        # Jub 50 — Sabbath + Jubilee-of-jubilees eschatology +
        # strict Sabbath-prohibition. Tewahedo Saturday-Sabbath
        # canonical range.
        entries = self._jub_entries_in(50, 50)
        assert len(entries) >= 5, (
            f"γ.4.5.E expected ≥5 Jubilees entries in ch 50 (Sabbath + Jubilee finale); found {len(entries)}"
        )

    def test_all_six_jubilees_sections_substantively_covered(self):
        # γ.4.5 ARC-CLOSE pin — parallel to γ.4.4.E's
        # test_all_six_mashafa_henok_sections_covered. Verifies that
        # every major Jubilees narrative section has substantive-
        # canonical-coverage at the detail-wave depth (≥3 entries for
        # the shortest section, ≥40 for the four largest). After
        # γ.4.5.E ships, the γ.4.5 detail arc is COMPLETE.
        def section_count(start, end):
            return len(self._jub_entries_in(start, end))

        # The four large sections — each at detail-wave parity (≥40
        # NEW entries beyond seed).
        assert section_count(5, 10) >= 40, (
            f"γ.4.5 arc-close: Watchers + Noahide (Jub 5-10) needs ≥40 entries; found {section_count(5, 10)}"
        )
        assert section_count(11, 22) >= 40, (
            f"γ.4.5 arc-close: Abraham cycle (Jub 11-22) needs ≥40 entries; found {section_count(11, 22)}"
        )
        assert section_count(24, 36) >= 40, (
            f"γ.4.5 arc-close: Jacob cycle (Jub 24-36) needs ≥40 entries; found {section_count(24, 36)}"
        )
        assert section_count(37, 50) >= 40, (
            f"γ.4.5 arc-close: Joseph + Exodus-finale (Jub 37-50) needs ≥40 entries; found {section_count(37, 50)}"
        )
        # The short bookend sections — each at seed coverage.
        assert section_count(1, 4) >= 3, (
            f"γ.4.5 arc-close: Sinai prologue + Creation (Jub 1-4) needs ≥3 entries; found {section_count(1, 4)}"
        )
        assert section_count(23, 23) >= 1, (
            f"γ.4.5 arc-close: Decline + eschatology (Jub 23) needs ≥1 entry; found {section_count(23, 23)}"
        )

    def test_jubilees_milestone_count_at_arc_close(self):
        # γ.4.5 arc-close milestone: Jubilees reached 200 entries
        # (γ.4.5 seed 40 + γ.4.5.B 40 + γ.4.5.C 40 + γ.4.5.D 40 +
        # γ.4.5.E 40 = 200). Pin captures the arc-close achievement
        # invariantly.
        jub_count = sum(
            1
            for verse_entries in self.ec._by_verse.values()
            for entry in verse_entries
            if entry.father == "Jubilees (Ethiopian tradition)"
        )
        assert jub_count >= 200, (
            f"γ.4.5.E arc-close: Jubilees expected ≥200 entries (40 seed + 4×40 detail); found {jub_count}"
        )

    def test_esau_jacob_war_anchor_present(self):
        # Jub 37:1 — Esau's clan wars against Jacob. Tewahedo
        # defensive-war canonical anchor.
        e = [x for x in self.ec.for_verse("jub", 37, 1) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.E missing Jub 37:1 — Esau-Jacob war (defensive-war anchor)"

    def test_joseph_chastity_patriarchal_catechesis_anchor_present(self):
        # Jub 39:10 — Joseph remembers Abraham's pre-Mosaic adultery
        # law that Jacob 'used to read.' Tewahedo family-catechism
        # canonical anchor.
        e = [x for x in self.ec.for_verse("jub", 39, 10) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.E missing Jub 39:10 — Joseph's chastity via patriarchal catechesis"

    def test_judah_tamar_confession_anchor_present(self):
        # Jub 41:25 — 'she became more righteous than he.' Tewahedo
        # confessor's näsḫa-of-acknowledgment verbal anchor.
        e = [x for x in self.ec.for_verse("jub", 41, 25) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.E missing Jub 41:25 — Judah's 'she is more righteous than I' confession"

    def test_jacob_beersheba_pause_anchor_present(self):
        # Jub 44:1 — Jacob's seven-day pause at Beersheba before
        # descending to Egypt. Tewahedo monastic-departure-pause
        # canonical pattern.
        e = [x for x in self.ec.for_verse("jub", 44, 1) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.E missing Jub 44:1 — Jacob's seven-day Beersheba pause"

    def test_god_descends_with_jacob_anchor_present(self):
        # Jub 44:5 — 'I will go down with thee, and I will bring
        # thee up.' Tewahedo Immanuel-typology and diaspora-presence
        # canonical anchor.
        e = [x for x in self.ec.for_verse("jub", 44, 5) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.E missing Jub 44:5 — God's Immanuel-descent-with-Jacob promise"

    def test_jacob_blesses_pharaoh_anchor_present(self):
        # Jub 45:13 — Jacob blesses Pharaoh. Tewahedo coronation-
        # prayer canonical-patriarchal warrant.
        e = [x for x in self.ec.for_verse("jub", 45, 13) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.E missing Jub 45:13 — Jacob blesses Pharaoh"

    def test_moses_three_day_ark_pascal_typology_anchor_present(self):
        # Jub 47:5 — Moses 'placed three days' in the ark. Tewahedo
        # Pascal-typology Moses-as-Christ canonical anchor.
        e = [x for x in self.ec.for_verse("jub", 47, 5) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.E missing Jub 47:5 — Moses three-day-ark Pascal-typology"

    def test_mastema_not_lord_at_lodging_anchor_present(self):
        # Jub 48:2 — Mastema (not the Lord) sought to kill Moses at
        # the lodging-night. Tewahedo theodicy canonical clarification
        # of Ex 4:24.
        e = [x for x in self.ec.for_verse("jub", 48, 2) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.E missing Jub 48:2 — Mastema-not-Lord at the lodging"

    def test_red_sea_is_passover_anchor_present(self):
        # Jub 48:18 — Red-Sea crossing dated to Passover. Tewahedo
        # Fasika doubled-celebration canonical anchor.
        e = [x for x in self.ec.for_verse("jub", 48, 18) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.E missing Jub 48:18 — Red-Sea-crossing IS Passover"

    def test_passover_blood_restrains_mastema_anchor_present(self):
        # Jub 49:2 — Mastema's powers restrained by Passover blood
        # on the lintels. Tewahedo eucharistic-blood demonic-defense
        # canonical anchor.
        e = [x for x in self.ec.for_verse("jub", 49, 2) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.E missing Jub 49:2 — Passover blood restrains Mastema"

    def test_lamb_and_wine_eucharistic_prototype_anchor_present(self):
        # Jub 49:6 — explicit lamb-AND-wine Passover pairing.
        # Tewahedo Anaphora canonical-OT eucharistic-prototype anchor.
        e = [x for x in self.ec.for_verse("jub", 49, 6) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.E missing Jub 49:6 — lamb-AND-wine eucharistic-OT prototype"

    def test_passover_observance_acquits_guilt_anchor_present(self):
        # Jub 49:15 — Passover observance acquits-of-guilt. Tewahedo
        # liturgical-act-AS-atonement principle canonical anchor.
        e = [x for x in self.ec.for_verse("jub", 49, 15) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.E missing Jub 49:15 — Passover-observance acquits-of-guilt"

    def test_jubilee_of_jubilees_eschatology_anchor_present(self):
        # Jub 50:4 — jubilee-of-jubilees eschatology with Satan
        # permanently removed and the land cleansed. Tewahedo
        # cosmic-territorial-cleansing eschatology canonical anchor.
        e = [x for x in self.ec.for_verse("jub", 50, 4) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.E missing Jub 50:4 — jubilee-of-jubilees eschatology"

    def test_sabbath_as_holy_kingdom_day_anchor_present(self):
        # Jub 50:9 — Sabbath as 'day of the holy kingdom.' Tewahedo
        # Saturday-Sabbath foretaste-of-Kingdom canonical anchor.
        e = [x for x in self.ec.for_verse("jub", 50, 9) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.E missing Jub 50:9 — Sabbath as holy-kingdom-day"

    def test_strict_sabbath_prohibition_list_anchor_present(self):
        # Jub 50:12 — strict Sabbath-prohibition list with 'shall
        # die' formula. Tewahedo Saturday-Sabbath canonical
        # observance preservation anchor.
        e = [x for x in self.ec.for_verse("jub", 50, 12) if x.father == "Jubilees (Ethiopian tradition)"]
        assert e, "γ.4.5.E missing Jub 50:12 — strict Sabbath-prohibition list"


class TestGamma42DEphremNumDeuWave:
    """γ.4.2.D — Ephrem on Numbers + Deuteronomy seed wave. CLOSES
    the Ephrem-on-Pentateuch arc (γ.4.2 Gen 1-11 + γ.4.2.B Gen 12-50
    + γ.4.2.C Exo 1-40 + γ.4.2.D Num+Deu). 40 verse-keyed entries
    (20 + 20) spanning every major Mosaic narrative block of the
    Pentateuch's back half. Source: Ephrem the Syrian, Commentary
    on Numbers + Commentary on Deuteronomy, NPNF Series 2 vol. 13
    (Gwynn / Schaff trans., Oxford 1898 — PD). Rebalances Ephrem
    share from 17.5% (γ.4.3-close state) upward to ~22.1% —
    recovers near-parity with Cyril (22.7% vs 22.1%, within 0.6 pts).

    Pins (per §8.1 arc-close convention for multi-wave content
    arcs — Ephrem-on-Pentateuch is the closing wave):
    - Numbers + Deuteronomy substantively seeded (≥20 entries each).
    - All major Numbers blocks covered: Levite census (1) + priestly
      vow + Aaronic blessing (6) + Passover repetition + pillar (9)
      + trumpets + 70 elders (10-11) + Moses' meekness + faithful
      (12) + Anakim (13) + slow-to-anger (14) + Korah (16) +
      Aaron's rod (17) + red heifer (19) + struck rock (20) +
      bronze serpent (21) + Balaam (22-24) + Phinehas (25) +
      Joshua succession (27).
    - All major Deuteronomy blocks covered: consuming-fire (4) +
      Decalogue restated (5) + Shema + Greatest Cmt + 3rd
      Temptation citation (6) + 1st Temptation citation (8) +
      heart-circumcision command (10) + chosen place (12) + 3rd
      Mosaic Passover (16) + king's Torah (17) + prophet-like-Moses
      (18) + hung-on-tree (21) + ox-not-muzzled (25) + curse-of-the-
      law (27) + heart-circumcision-promise (30) + word-near-in-
      mouth (30) + kill-and-make-alive (32) + Levi's blessing (33)
      + Moses' hidden grave (34).
    - _meta synchronization pin — _meta.source names γ.4.2.D and
      describes Ephrem on Numbers + Deuteronomy.
    - Ephrem absolute-count milestone ≥155 entries (per
      `feedback_share_pin_pattern` — absolute count, not share;
      invariant against future voice-broadening waves).
    - Pentateuch four-wave coverage pin: Gen + Exo + Num + Deu
      each carry ≥20 Ephrem entries (Lev retained at seed-only).
    - Signature passages: Aaronic blessing (Num 6:24), Aaron's
      rod budding (Num 17:8 — Marian-rod), bronze serpent
      (Num 21:8 — Jn 3:14), star of Jacob (Num 24:17),
      Shema (Deu 6:4), bread-of-life pedagogy (Deu 8:3 — Mt 4:4),
      prophet-like-Moses (Deu 18:15 — Acts 3:22), hung-on-tree
      curse (Deu 21:23 — Gal 3:13), heart-circumcision promise
      (Deu 30:6), kill-and-make-alive (Deu 32:39), Moses' hidden
      grave (Deu 34:6 — Jude 9 + Astə'arǝgya-Mussē).
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def _ephrem_in(self, book, ch_start, ch_end):
        out = []
        for chapter in range(ch_start, ch_end + 1):
            for verse in range(1, 100):
                out.extend(e for e in self.ec.for_verse(book, chapter, verse) if e.father == "Ephrem the Syrian")
        return out

    def test_numbers_substantively_seeded(self):
        eph_num = self._ephrem_in("num", 1, 36)
        assert len(eph_num) >= 20, f"γ.4.2.D expected ≥20 Ephrem entries on Numbers 1-36; found {len(eph_num)}"

    def test_deuteronomy_substantively_seeded(self):
        eph_deu = self._ephrem_in("deu", 1, 34)
        assert len(eph_deu) >= 20, f"γ.4.2.D expected ≥20 Ephrem entries on Deuteronomy 1-34; found {len(eph_deu)}"

    def test_all_major_numbers_blocks_covered(self):
        def has(start, end):
            return bool(self._ephrem_in("num", start, end))

        assert has(1, 1), "γ.4.2.D missing Levite census (Num 1)"
        assert has(6, 6), "γ.4.2.D missing Nazirite vow + Aaronic blessing (Num 6)"
        assert has(9, 10), "γ.4.2.D missing Passover repetition + pillar + trumpets (Num 9-10)"
        assert has(11, 12), "γ.4.2.D missing 70 elders + Moses' meekness/faithfulness (Num 11-12)"
        assert has(13, 14), "γ.4.2.D missing Anakim + slow-to-anger (Num 13-14)"
        assert has(16, 17), "γ.4.2.D missing Korah + Aaron's rod (Num 16-17)"
        assert has(19, 21), "γ.4.2.D missing red heifer + struck rock + bronze serpent (Num 19-21)"
        assert has(22, 25), "γ.4.2.D missing Balaam + star of Jacob + Phinehas (Num 22-25)"
        assert has(27, 27), "γ.4.2.D missing Joshua's commissioning (Num 27)"

    def test_all_major_deuteronomy_blocks_covered(self):
        def has(start, end):
            return bool(self._ephrem_in("deu", start, end))

        assert has(4, 5), "γ.4.2.D missing consuming-fire God + Decalogue prologue (Deu 4-5)"
        assert has(6, 6), "γ.4.2.D missing Shema + Greatest Commandment + 3rd Temptation citation (Deu 6)"
        assert has(8, 8), "γ.4.2.D missing 1st Temptation citation 'man not by bread alone' (Deu 8)"
        assert has(10, 12), "γ.4.2.D missing heart-circumcision + chosen-place (Deu 10-12)"
        assert has(16, 18), "γ.4.2.D missing 3rd Mosaic Passover + king's Torah + prophet-like-Moses (Deu 16-18)"
        assert has(21, 21), "γ.4.2.D missing hung-on-tree curse (Deu 21)"
        assert has(25, 27), "γ.4.2.D missing don't-muzzle-ox + curse-of-the-law (Deu 25-27)"
        assert has(30, 30), "γ.4.2.D missing heart-circumcision promise + word-near-in-mouth (Deu 30)"
        assert has(32, 34), "γ.4.2.D missing Song of Moses + Levi's blessing + Moses' grave (Deu 32-34)"

    def test_ephrem_milestone_count_at_pentateuch_arc_close(self):
        # γ.4.2 (Gen 1-11) + γ.4.2.B (Gen 12-50) + Ps (1) + γ.4.2.C
        # (Exo 1-40) + γ.4.2.D (Num 1-27 + Deu 4-34) = 117 + 40 = 157
        # Ephrem entries at arc-close. Absolute milestone per
        # feedback_share_pin_pattern; invariant against future
        # voice-broadening waves.
        ephrem_count = sum(
            1
            for verse_entries in self.ec._by_verse.values()
            for entry in verse_entries
            if entry.father == "Ephrem the Syrian"
        )
        assert ephrem_count >= 155, (
            f"γ.4.2.D expected Ephrem count ≥155 (Pentateuch-arc close milestone); found {ephrem_count}"
        )

    def test_pentateuch_four_wave_coverage(self):
        # Per §8.1 arc-close: every section of the closed arc must
        # carry substantive coverage. Pentateuch arc = four waves at
        # ≥20 Ephrem entries each (Gen / Exo / Num / Deu). Leviticus
        # retained at seed-only depth per scope; not pinned here.
        gen = len(self._ephrem_in("gen", 1, 50))
        exo = len(self._ephrem_in("exo", 1, 40))
        num = len(self._ephrem_in("num", 1, 36))
        deu = len(self._ephrem_in("deu", 1, 34))
        assert gen >= 20, f"γ.4.2.D arc-close: Ephrem-on-Gen below floor (need ≥20, have {gen})"
        assert exo >= 20, f"γ.4.2.D arc-close: Ephrem-on-Exo below floor (need ≥20, have {exo})"
        assert num >= 20, f"γ.4.2.D arc-close: Ephrem-on-Num below floor (need ≥20, have {num})"
        assert deu >= 20, f"γ.4.2.D arc-close: Ephrem-on-Deu below floor (need ≥20, have {deu})"

    def test_aaronic_blessing_canonical_dismissal_present(self):
        eph = [e for e in self.ec.for_verse("num", 6, 24) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.D missing Num 6:24 — Aaronic blessing (Tewahedo Qǝddase dismissal anchor)"

    def test_aarons_rod_marian_typology_present(self):
        eph = [e for e in self.ec.for_verse("num", 17, 8) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.D missing Num 17:8 — Aaron's rod budding (Marian-rod typology / Wǝddase Maryam)"

    def test_bronze_serpent_christological_typology_present(self):
        eph = [e for e in self.ec.for_verse("num", 21, 8) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.D missing Num 21:8 — bronze serpent (Jn 3:14 verbatim Christological anchor)"

    def test_star_of_jacob_sceptre_messianic_anchor_present(self):
        eph = [e for e in self.ec.for_verse("num", 24, 17) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.D missing Num 24:17 — star of Jacob + scepter of Israel (Mt 2:2 + Solomonic-dynasty)"

    def test_struck_rock_christ_once_anchor_present(self):
        eph = [e for e in self.ec.for_verse("num", 20, 11) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.D missing Num 20:11 — water-from-rock 2nd strike (1 Cor 10:4 / Heb 9-10)"

    def test_shema_trinitarian_seed_anchor_present(self):
        eph = [e for e in self.ec.for_verse("deu", 6, 4) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.D missing Deu 6:4 — Shema (Trinitarian seed-form; Mt 28:19 anchor)"

    def test_great_commandment_old_testament_source_present(self):
        eph = [e for e in self.ec.for_verse("deu", 6, 5) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.D missing Deu 6:5 — love YHWH with all heart (Mt 22:37 anchor)"

    def test_bread_of_life_pedagogy_anchor_present(self):
        eph = [e for e in self.ec.for_verse("deu", 8, 3) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.D missing Deu 8:3 — man not by bread alone (Mt 4:4 + Jn 6:51 anchor)"

    def test_prophet_like_moses_christological_anchor_present(self):
        eph = [e for e in self.ec.for_verse("deu", 18, 15) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.D missing Deu 18:15 — prophet-like-Moses (Acts 3:22 verbatim Christological anchor)"

    def test_hung_on_tree_curse_atonement_anchor_present(self):
        eph = [e for e in self.ec.for_verse("deu", 21, 23) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.D missing Deu 21:23 — hung-on-tree curse (Gal 3:13 verbatim atonement anchor)"

    def test_heart_circumcision_promise_theosis_anchor_present(self):
        eph = [e for e in self.ec.for_verse("deu", 30, 6) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.D missing Deu 30:6 — God will circumcise your heart (Tewahedo theosis anchor)"

    def test_word_near_in_mouth_gospel_of_faith_anchor_present(self):
        eph = [e for e in self.ec.for_verse("deu", 30, 14) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.D missing Deu 30:14 — word-near-in-mouth (Rom 10:8 verbatim gospel-of-faith)"

    def test_resurrection_monotheism_anchor_present(self):
        eph = [e for e in self.ec.for_verse("deu", 32, 39) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.D missing Deu 32:39 — I kill and make alive (resurrection-monotheism canonical anchor)"

    def test_moses_hidden_grave_translation_anchor_present(self):
        eph = [e for e in self.ec.for_verse("deu", 34, 6) if e.father == "Ephrem the Syrian"]
        assert eph, "γ.4.2.D missing Deu 34:6 — Moses' hidden grave (Jude 9 + Astə'arǝgya-Mussē anchor)"

    def test_meta_documents_gamma_4_2_d_pentateuch_arc_close(self):
        # Pin the _meta.source string carries the γ.4.2.D signature so
        # future Claude doesn't lose the arc-record. Per the §8.1 arc-
        # close convention (rules), the _meta sync pin is required for
        # multi-wave content arcs. γ.4.2.D is the closing wave of the
        # four-wave Ephrem-on-Pentateuch arc — synchronization pin
        # checks the closing wave's _meta annotation explicitly.
        import json
        import re
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_source = data["_meta"]["source"]
        assert re.search(r"γ\.4\.2\.D(?![.A-Z])", meta_source), "γ.4.2.D must be referenced in _meta.source"
        assert "Ephrem-on-Numbers-Deuteronomy" in meta_source or "Numbers + Deuteronomy" in meta_source, (
            "γ.4.2.D _meta.source should name Numbers + Deuteronomy explicitly"
        )
        assert "Ephrem-on-Pentateuch arc" in meta_source, "γ.4.2.D _meta.source should record the Pentateuch arc-close"


class TestGamma43BCyrilLukeInfancyGalileanWave:
    """γ.4.3.B — Cyril of Alexandria on Luke detail wave I (Lk 1-9:
    Infancy + Galilean ministry). FIRST detail wave extending the
    γ.4.3 seed coverage from 18 seed-only entries on Lk 1-9 to 58
    substantive-detail entries (mirroring γ.4.1.A Cyril-on-John-1-4
    seed-density pattern). 40 verse-keyed entries distributed across
    all 9 chapters; all 40 verses are distinct from the γ.4.3 seed
    set (no double-occupancy). Source: R. Payne Smith, *A Commentary
    upon the Gospel according to S. Luke by S. Cyril, Patriarch of
    Alexandria* (Oxford: University Press, 1859 — PD; draws on
    Homilies I-LXXI). Rebalances Cyril share from 22.7% to ~26.7%
    — Cyril now slightly edges out Jubilees for the top voice.

    Pins (γ.4.3.B is a first detail wave, not an arc-close — lighter
    pin set than the §8.1 arc-close convention):
    - Lk 1-9 substantively detailed (≥58 total Cyril entries on
      Lk 1-9 = 18 seed + 40 detail).
    - All 9 chapters have detail-depth ≥4 entries each.
    - Cyril absolute-count milestone ≥200 entries (per
      `feedback_share_pin_pattern` — absolute count, not share).
    - 12 signature-passage pins for the new Tewahedo anchors
      introduced by the detail wave: Annunciation cycle 1:35 +
      1:38 (Theotokos pneumatology + New-Eve fiat); 2:14 Gloria-
      in-excelsis (Anaphora opening); 2:21 eighth-day circumcision
      (Tewahedo distinctive); 3:22 'bodily shape' Trinitarian
      epiphany (Timqät anchor); 3:38 Adam-son-of-God (Second-Adam
      universal-Adamic); 4:18 Isaian-Servant Spirit-Anointing;
      5:24 Son-of-Man-forgives (priestly-absolution Jn 20:23);
      6:13 Twelve-apostles (apostolic foundation); 7:22 six
      Messianic signs; 9:23 daily-cross (bahǝtawi anchor); 9:31
      exodon-Transfiguration-Buhe; 9:51 set-face-to-Jerusalem
      voluntary-Passion.
    - _meta synchronization pin — regex word-boundary on γ.4.3.B.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def _cyril_in_chapter(self, chapter):
        out = []
        for verse in range(1, 100):
            out.extend(e for e in self.ec.for_verse("luk", chapter, verse) if e.father == "Cyril of Alexandria")
        return out

    def test_lk_1_9_substantively_detailed(self):
        total = sum(len(self._cyril_in_chapter(c)) for c in range(1, 10))
        assert total >= 58, f"γ.4.3.B expected ≥58 Cyril entries on Lk 1-9 (18 seed + 40 detail); found {total}"

    def test_each_lk_chapter_has_detail_depth(self):
        # Detail-wave parity floor: each of Lk 1-9 should have ≥4
        # Cyril entries after γ.4.3.B (seed had 1-3 per chapter; the
        # detail wave brings each chapter to ≥4).
        for chapter in range(1, 10):
            count = len(self._cyril_in_chapter(chapter))
            assert count >= 4, f"γ.4.3.B Lk {chapter} below detail-depth floor (need ≥4, have {count})"

    def test_cyril_milestone_count_post_detail_wave_b(self):
        # γ.4.1-γ.4.1.D Cyril-on-John (116) + γ.4.3 seed (40) +
        # γ.4.3.B (40) + Gen 1:26 (1) + Ps 23:1 (1) + Joh 19:34/
        # 1:4-13 (3) = 201. Absolute milestone per
        # feedback_share_pin_pattern.
        cyril_count = sum(
            1
            for verse_entries in self.ec._by_verse.values()
            for entry in verse_entries
            if entry.father == "Cyril of Alexandria"
        )
        assert cyril_count >= 200, (
            f"γ.4.3.B expected Cyril count ≥200 (post-detail-wave-B milestone); found {cyril_count}"
        )

    def test_theotokos_pneumatology_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 1, 35) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.B missing Lk 1:35 — Spirit-overshadowing (Theotokos pneumatology anchor)"

    def test_fiat_mihi_new_eve_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 1, 38) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.B missing Lk 1:38 — fiat-mihi (New-Eve Marian-obedience anchor)"

    def test_gloria_in_excelsis_anaphora_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 2, 14) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.B missing Lk 2:14 — Gloria-in-excelsis (Tewahedo Anaphora opening anchor)"

    def test_eighth_day_circumcision_tewahedo_distinctive_present(self):
        eph = [e for e in self.ec.for_verse("luk", 2, 21) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.B missing Lk 2:21 — Christ's circumcision (Tewahedo distinctive anchor)"

    def test_bodily_shape_timqat_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 3, 22) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.B missing Lk 3:22 — 'bodily shape' Spirit-descent (Tewahedo Timqät anchor)"

    def test_adam_son_of_god_second_adam_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 3, 38) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.B missing Lk 3:38 — Adam-son-of-God (Second-Adam universal-Adamic anchor)"

    def test_isaian_servant_spirit_anointing_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 4, 18) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.B missing Lk 4:18 — Isaian-Servant Spirit-Anointed-Messiah anchor"

    def test_son_of_man_forgives_priestly_absolution_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 5, 24) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.B missing Lk 5:24 — Son-of-Man-forgives (priestly absolution Jn 20:23 anchor)"

    def test_twelve_apostles_apostolic_foundation_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 6, 13) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.B missing Lk 6:13 — Twelve apostles (Tewahedo episcopal apostolic-foundation)"

    def test_six_messianic_signs_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 7, 22) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.B missing Lk 7:22 — six Isaian Messianic signs (Christ-identity triple-witness)"

    def test_daily_cross_bahetawi_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 9, 23) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.B missing Lk 9:23 — kath'-hēmeran daily-cross (bahǝtawi daily-renewal anchor)"

    def test_exodon_transfiguration_buhe_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 9, 31) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.B missing Lk 9:31 — exodon Transfiguration-Conversation (Tewahedo Buhe anchor)"

    def test_set_face_to_jerusalem_voluntary_passion_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 9, 51) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.B missing Lk 9:51 — estērisen-to-prosōpon set-face (voluntary-Passion anchor)"

    def test_meta_documents_gamma_4_3_b_detail_wave(self):
        # Per the §8.1 _meta sync convention (extended to detail
        # waves), pin that the JSON _meta.source records γ.4.3.B
        # explicitly and names the Lk 1-9 detail-wave scope.
        import json
        import re
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_source = data["_meta"]["source"]
        assert re.search(r"γ\.4\.3\.B(?![A-Z])", meta_source), "γ.4.3.B must be referenced in _meta.source"
        assert "Cyril-of-Alexandria-on-Luke detail entries" in meta_source or "Cyril-on-Luke detail" in meta_source, (
            "γ.4.3.B _meta.source should name Cyril-on-Luke detail-wave explicitly"
        )
        assert "Lk 1-9" in meta_source or "Infancy" in meta_source, (
            "γ.4.3.B _meta.source should describe the Lk 1-9 (Infancy + Galilean ministry) scope"
        )


class TestGamma43CCyrilLukeJourneyWave:
    """γ.4.3.C — Cyril of Alexandria on Luke detail wave II (Lk 10-19:
    Journey-to-Jerusalem). SECOND detail wave extending the γ.4.3
    seed coverage from 13 seed-only entries on Lk 10-19 to 53
    substantive-detail entries (parity with γ.4.3.B Lk 1-9 detail
    wave). 40 verse-keyed entries distributed across all 10 chapters
    (4 per chapter); all 40 verses are distinct from the γ.4.3 seed
    set (no double-occupancy). Source: R. Payne Smith, *A Commentary
    upon the Gospel according to S. Luke by S. Cyril, Patriarch of
    Alexandria* (Oxford: University Press, 1859 — PD; draws on
    Homilies LXXII-CXXX). Rebalances Cyril share from 26.8% to
    ~30.5% — Cyril now firmly leads the four-voice quartet by 5.2
    points (patristic anchors 50.4% combined vs canonical-text
    voices 49.6%).

    Pins (γ.4.3.C is a detail wave, not arc-close — lighter pin set
    than the §8.1 arc-close convention):
    - Lk 10-19 substantively detailed (≥53 total Cyril entries on
      Lk 10-19 = 13 seed + 40 detail).
    - All 10 chapters have detail-depth ≥4 entries each.
    - Cyril absolute-count milestone ≥240 entries (per
      `feedback_share_pin_pattern` — absolute count, not share).
    - 12 signature-passage pins for the new Tewahedo anchors
      introduced by the detail wave: seventy disciples sent
      (10:1); Trinitarian utterance 'rejoiced in Spirit' (10:21);
      fourfold Greatest Commandment (10:27); reciprocal forgiveness
      (11:4); Holy Spirit answer-to-prayer (11:13); finger-of-God
      (11:20); cosmic peace-in-heaven triumphal-entry doubled with
      Christmas-hymn (Lk 19:38); Christ's death-as-baptism (12:50);
      east-west-north-south Ethiopian-eschatological-inclusion
      (13:29); Eucharistic-eschatological-Great-Supper (14:16);
      Father's-mercy Prodigal full-pericope (15:11); sufficiency-
      of-Scripture (16:31); ceaseless-prayer (18:1); Son-of-Man
      seek-and-save (19:10); house-of-prayer (19:46).
    - _meta synchronization pin — regex word-boundary on γ.4.3.C.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def _cyril_in_chapter(self, chapter):
        out = []
        for verse in range(1, 100):
            out.extend(e for e in self.ec.for_verse("luk", chapter, verse) if e.father == "Cyril of Alexandria")
        return out

    def test_lk_10_19_substantively_detailed(self):
        total = sum(len(self._cyril_in_chapter(c)) for c in range(10, 20))
        assert total >= 53, f"γ.4.3.C expected ≥53 Cyril entries on Lk 10-19 (13 seed + 40 detail); found {total}"

    def test_each_lk_chapter_has_detail_depth(self):
        # Detail-wave parity floor: each of Lk 10-19 should have ≥4
        # Cyril entries after γ.4.3.C (seed had 1-2 per chapter; the
        # detail wave brings each chapter to ≥4).
        for chapter in range(10, 20):
            count = len(self._cyril_in_chapter(chapter))
            assert count >= 4, f"γ.4.3.C Lk {chapter} below detail-depth floor (need ≥4, have {count})"

    def test_cyril_milestone_count_post_detail_wave_c(self):
        # γ.4.1-γ.4.1.D Cyril-on-John (116) + γ.4.3 seed (40) +
        # γ.4.3.B Lk 1-9 detail (40) + γ.4.3.C Lk 10-19 detail (40)
        # + Gen 1:26 (1) + Ps 23:1 (1) + Joh 1:3-5,9-13,19:34 (3) = 241.
        # Absolute milestone per feedback_share_pin_pattern.
        cyril_count = sum(
            1
            for verse_entries in self.ec._by_verse.values()
            for entry in verse_entries
            if entry.father == "Cyril of Alexandria"
        )
        assert cyril_count >= 240, (
            f"γ.4.3.C expected Cyril count ≥240 (post-detail-wave-C milestone); found {cyril_count}"
        )

    def test_seventy_disciples_missionary_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 10, 1) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.C missing Lk 10:1 — seventy disciples sent two-by-two (Tewahedo missionary anchor)"

    def test_trinitarian_rejoiced_in_spirit_present(self):
        eph = [e for e in self.ec.for_verse("luk", 10, 21) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.C missing Lk 10:21 — 'Jesus rejoiced in spirit' (Trinitarian utterance anchor)"

    def test_fourfold_greatest_commandment_present(self):
        eph = [e for e in self.ec.for_verse("luk", 10, 27) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.C missing Lk 10:27 — fourfold heart-soul-strength-mind Greatest Commandment"

    def test_reciprocal_forgiveness_lords_prayer_present(self):
        eph = [e for e in self.ec.for_verse("luk", 11, 4) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.C missing Lk 11:4 — reciprocal forgiveness (Tewahedo penance anchor)"

    def test_father_gives_holy_spirit_present(self):
        eph = [e for e in self.ec.for_verse("luk", 11, 13) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.C missing Lk 11:13 — Holy Spirit as supreme answer-to-prayer (Lukan distinctive)"

    def test_finger_of_god_exodus_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 11, 20) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.C missing Lk 11:20 — finger-of-God (Exodus-Spirit identification anchor)"

    def test_christs_death_as_baptism_present(self):
        eph = [e for e in self.ec.for_verse("luk", 12, 50) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.C missing Lk 12:50 — 'baptism to be baptized with' (Rom 6:3-4 anchor)"

    def test_east_west_ethiopian_inclusion_present(self):
        eph = [e for e in self.ec.for_verse("luk", 13, 29) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.C missing Lk 13:29 — east-west-north-south Ethiopian-eschatological inclusion"

    def test_great_supper_eucharistic_eschatological_present(self):
        eph = [e for e in self.ec.for_verse("luk", 14, 16) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.C missing Lk 14:16 — Great Supper (Eucharistic-eschatological banquet + Rev 19:9)"

    def test_prodigal_full_pericope_present(self):
        eph = [e for e in self.ec.for_verse("luk", 15, 11) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.C missing Lk 15:11 — Prodigal full pericope (Father's threefold-mercy speech)"

    def test_sufficiency_of_scripture_present(self):
        eph = [e for e in self.ec.for_verse("luk", 16, 31) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.C missing Lk 16:31 — 'if they hear not Moses' (sufficiency-of-Scripture Tewahedo bibliology)"

    def test_ceaseless_prayer_seven_office_present(self):
        eph = [e for e in self.ec.for_verse("luk", 18, 1) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.C missing Lk 18:1 — 'always pray, faint not' (Tewahedo Mäshafä-Sǝʾatat anchor)"

    def test_son_of_man_seek_and_save_present(self):
        eph = [e for e in self.ec.for_verse("luk", 19, 10) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.C missing Lk 19:10 — Son of Man seek and save (missio-Dei doubled with Lk 5:32)"

    def test_peace_in_heaven_triumphal_entry_hosanna_present(self):
        eph = [e for e in self.ec.for_verse("luk", 19, 38) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.C missing Lk 19:38 — 'peace in heaven' (Tewahedo Hosanna feast anchor)"

    def test_house_of_prayer_temple_cleansing_present(self):
        eph = [e for e in self.ec.for_verse("luk", 19, 46) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.C missing Lk 19:46 — 'house of prayer' (church-discipline canonical anchor)"

    def test_meta_documents_gamma_4_3_c_detail_wave(self):
        # Per the §8.1 _meta sync convention (extended to detail
        # waves), pin that the JSON _meta.source records γ.4.3.C
        # explicitly and names the Lk 10-19 detail-wave scope.
        import json
        import re
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_source = data["_meta"]["source"]
        assert re.search(r"γ\.4\.3\.C(?![A-Z])", meta_source), "γ.4.3.C must be referenced in _meta.source"
        assert "Lk 10-19" in meta_source or "Journey-to-Jerusalem" in meta_source, (
            "γ.4.3.C _meta.source should describe the Lk 10-19 (Journey-to-Jerusalem) scope"
        )


class TestGamma43DCyrilLukePassionWave:
    """γ.4.3.D — Cyril of Alexandria on Luke detail wave III (Lk 20-24:
    Passion + Resurrection + Ascension). CLOSING WAVE of the four-
    wave Cyril-on-Luke arc per §8.1 arc-close convention. 40 verse-
    keyed entries distributed across all 5 chapters (Lk 20: 7 +
    Lk 21: 7 + Lk 22: 9 + Lk 23: 8 + Lk 24: 9). All 40 verses are
    distinct from the γ.4.3 seed set. Source: R. Payne Smith,
    *A Commentary upon the Gospel according to S. Luke by S. Cyril,
    Patriarch of Alexandria* (Oxford: University Press, 1859 — PD;
    draws on Homilies CXXXI-CLVI). Rebalances Cyril share from
    30.5% to ~33.9% — Cyril now strongly leads the four-voice
    quartet (9.8 points ahead of Jubilees).

    Per §8.1 arc-close convention, the closing wave's test class
    MUST add the three specific pin types: (1) _meta synchronization
    pin per sub-phase tag with regex word-boundary matching; (2)
    absolute-count milestone pin at the cumulative arc-close count;
    (3) all_N_sections_covered exhaustiveness pin asserting every
    section the arc was supposed to cover has substantive coverage.

    Pins:
    - Lk 20-24 substantively detailed (≥49 total Cyril entries on
      Lk 20-24 = 9 seed + 40 detail).
    - All 5 chapters have detail-depth ≥7 entries each.
    - **§8.1 ARC-CLOSE PIN #1 — count milestone:** Cyril absolute-
      count ≥280 entries (cumulative Cyril-on-John 116 + Cyril-on-
      Luke 160 + incidental 5 = 281; ≥280 absolute floor per
      `feedback_share_pin_pattern`).
    - **§8.1 ARC-CLOSE PIN #2 — all_N_sections_covered exhaustiveness:**
      test_all_four_cyril_luke_waves_substantively_covered asserts
      γ.4.3 seed (40), γ.4.3.B Lk 1-9 (≥58), γ.4.3.C Lk 10-19
      (≥53), γ.4.3.D Lk 20-24 (≥49) — every section the
      Cyril-on-Luke arc was supposed to cover has substantive
      coverage at the planned depth.
    - **§8.1 ARC-CLOSE PIN #3 — _meta synchronization:** pin per
      sub-phase tag (γ.4.3, γ.4.3.B, γ.4.3.C, γ.4.3.D) with
      regex word-boundary; tests/`test_meta_synchronization_at_arc_close`.
    - 14 signature-passage pins for new Tewahedo anchors:
      Ps 110:1 right-hand-of-Father (20:42); Spirit-confessor's-
      mouth (21:15); Christ's-eucharistic-desire (22:15);
      new-covenant-blood (22:20); bishop-as-servant (22:24);
      two-wills-in-unity Miaphysite (22:42); angel-strengthening
      (22:43); Adamic-skull-Calvary (23:33); trilingual-titulus
      Solomonic-dynasty (23:38); good-thief deathbed-confession
      (23:42); Temple-veil-rent Heb 10:19-20 (23:45); first-day-
      of-the-week doubled-Sabbath (24:1); Emmaus full-pericope
      Eucharistic-shape (24:13); real-bodily-resurrection (24:39);
      Promise-of-the-Father Pentecost-Pärräqlēṭos (24:49).
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def _cyril_in_chapter(self, chapter):
        out = []
        for verse in range(1, 100):
            out.extend(e for e in self.ec.for_verse("luk", chapter, verse) if e.father == "Cyril of Alexandria")
        return out

    def _cyril_in_range(self, ch_start, ch_end):
        return sum(len(self._cyril_in_chapter(c)) for c in range(ch_start, ch_end + 1))

    def test_lk_20_24_substantively_detailed(self):
        total = self._cyril_in_range(20, 24)
        assert total >= 49, f"γ.4.3.D expected ≥49 Cyril entries on Lk 20-24 (9 seed + 40 detail); found {total}"

    def test_each_lk_passion_chapter_has_detail_depth(self):
        # Detail-wave parity floor: each of Lk 20-24 should have ≥7
        # Cyril entries after γ.4.3.D (Passion chapters get denser
        # coverage than seed-only chapters elsewhere).
        for chapter in range(20, 25):
            count = len(self._cyril_in_chapter(chapter))
            assert count >= 7, f"γ.4.3.D Lk {chapter} below detail-depth floor (need ≥7, have {count})"

    def test_cyril_arc_close_count_milestone(self):
        # §8.1 ARC-CLOSE PIN #2: absolute-count milestone at arc
        # close. Per feedback_share_pin_pattern: never a share pin.
        # Cumulative: Cyril-on-John 116 (γ.4.1-D) + Cyril-on-Luke
        # 40 seed + 40 + 40 + 40 detail = 276 on Gospels + 5
        # incidental (Gen 1:26 + Ps 23:1 + Joh 1:3-5,9-13,19:34
        # earlier) = 281. ≥280 floor.
        cyril_count = sum(
            1
            for verse_entries in self.ec._by_verse.values()
            for entry in verse_entries
            if entry.father == "Cyril of Alexandria"
        )
        assert cyril_count >= 280, (
            f"γ.4.3.D arc-close: Cyril count ≥280 expected (cumulative arc-close milestone); found {cyril_count}"
        )

    def test_all_four_cyril_luke_waves_substantively_covered(self):
        # §8.1 ARC-CLOSE PIN #3: all_N_sections_covered exhaustiveness.
        # Every section of the Cyril-on-Luke arc must have substantive
        # coverage at planned depth. The four waves are: γ.4.3 seed
        # (40 entries across all 24 chapters) + γ.4.3.B Lk 1-9 detail
        # (≥58 cumulative on Lk 1-9) + γ.4.3.C Lk 10-19 detail (≥53
        # cumulative) + γ.4.3.D Lk 20-24 detail (≥49 cumulative).
        # This pin prevents a future "I'll ship Lk 20-24 later" from
        # silently leaving the arc partially closed.
        total_cyril_luke = self._cyril_in_range(1, 24)
        lk_1_9 = self._cyril_in_range(1, 9)
        lk_10_19 = self._cyril_in_range(10, 19)
        lk_20_24 = self._cyril_in_range(20, 24)

        assert total_cyril_luke >= 160, (
            f"γ.4.3.D arc-close: total Cyril-on-Luke ≥160 expected (4 waves × 40); found {total_cyril_luke}"
        )
        assert lk_1_9 >= 58, f"γ.4.3.D arc-close: Lk 1-9 below γ.4.3.B parity (need ≥58, have {lk_1_9})"
        assert lk_10_19 >= 53, f"γ.4.3.D arc-close: Lk 10-19 below γ.4.3.C parity (need ≥53, have {lk_10_19})"
        assert lk_20_24 >= 49, f"γ.4.3.D arc-close: Lk 20-24 below γ.4.3.D parity (need ≥49, have {lk_20_24})"

    def test_meta_synchronization_at_arc_close(self):
        # §8.1 ARC-CLOSE PIN #1: _meta synchronization. Pin per
        # sub-phase tag with regex word-boundary so γ.4.3 doesn't
        # accidentally match γ.4.3.B/C/D. Granular failures (per
        # sub-phase) are easier to diagnose than a combined pin.
        import json
        import re
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_source = data["_meta"]["source"]
        # word-boundary regex: don't accidentally match sub-phase
        # tags as substrings of one another
        assert re.search(r"γ\.4\.3(?![.A-Z])", meta_source), "γ.4.3 seed wave must be in _meta.source"
        assert re.search(r"γ\.4\.3\.B(?![A-Z])", meta_source), "γ.4.3.B detail wave I must be in _meta.source"
        assert re.search(r"γ\.4\.3\.C(?![A-Z])", meta_source), "γ.4.3.C detail wave II must be in _meta.source"
        assert re.search(r"γ\.4\.3\.D(?![A-Z])", meta_source), (
            "γ.4.3.D detail wave III (arc-close) must be in _meta.source"
        )
        # arc-close must describe Lk 20-24 scope explicitly
        assert "Lk 20-24" in meta_source or "Passion + Resurrection + Ascension" in meta_source, (
            "γ.4.3.D _meta.source should describe the Lk 20-24 (Passion + Resurrection + Ascension) scope"
        )
        # arc-close must record arc-close status explicitly
        assert (
            "Cyril-on-Luke arc is CLOSED" in meta_source or "CLOSES the four-wave Cyril-on-Luke arc" in meta_source
        ), "γ.4.3.D _meta.source should record the arc-close explicitly"

    # ---- Signature passage pins (14 anchors for Tewahedo distinctives) ----

    def test_ps_110_right_hand_of_father_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 20, 42) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.D missing Lk 20:42 — Ps 110:1 right-hand-of-Father Christological double-Lordship"

    def test_spirit_confessors_mouth_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 21, 15) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.D missing Lk 21:15 — Spirit-confessor's-mouth (Acts 6:10 anchor)"

    def test_christs_eucharistic_desire_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 22, 15) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.D missing Lk 22:15 — epithymia-epethymēsa Christ's-eucharistic-desire"

    def test_new_covenant_blood_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 22, 20) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.D missing Lk 22:20 — new-covenant-blood (Tewahedo Anaphora institution-form)"

    def test_bishop_as_servant_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 22, 24) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.D missing Lk 22:24 — Last-Supper strife (bishop-as-servant + Jn 13:14)"

    def test_two_wills_miaphysite_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 22, 42) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.D missing Lk 22:42 — 'not my will but thine' (two-wills-in-unity Miaphysite Christology)"

    def test_gethsemane_angel_strengthening_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 22, 43) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.D missing Lk 22:43 — Gethsemane angel-strengthening (Tewahedo angelic-ministry)"

    def test_calvary_adamic_skull_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 23, 33) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.D missing Lk 23:33 — Calvary kranion (Adamic-skull Tewahedo iconographic-tradition)"

    def test_trilingual_titulus_solomonic_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 23, 38) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.D missing Lk 23:38 — trilingual titulus universal-kingship-Tewahedo-Solomonic"

    def test_good_thief_deathbed_confession_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 23, 42) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.D missing Lk 23:42 — good-thief 'Lord, remember me' (deathbed-confession)"

    def test_temple_veil_rent_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 23, 45) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.D missing Lk 23:45 — Temple-veil-rent (Heb 10:19-20 Tewahedo maqdas-curtain)"

    def test_lords_day_doubled_sabbath_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 24, 1) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.D missing Lk 24:1 — 'first day of the week' (Tewahedo Sänbatä-Krǝstiyan doubled-Sabbath)"

    def test_emmaus_eucharistic_shape_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 24, 13) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.D missing Lk 24:13 — Emmaus full pericope (Eucharistic Word-Sacrament-Mystagogy shape)"

    def test_real_bodily_resurrection_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 24, 39) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.D missing Lk 24:39 — 'handle me, flesh and bones' (real-bodily-resurrection)"

    def test_promise_of_the_father_pentecost_anchor_present(self):
        eph = [e for e in self.ec.for_verse("luk", 24, 49) if e.father == "Cyril of Alexandria"]
        assert eph, "γ.4.3.D missing Lk 24:49 — 'Promise of the Father' (Pentecost-Pärräqlēṭos Tewahedo anchor)"
