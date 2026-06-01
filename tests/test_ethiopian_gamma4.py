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
        #   - "Cramer" — J.A. Cramer's *Catenae Graecorum Patrum in
        #     Novum Testamentum* (Oxford 1840 — PD), the authoritative
        #     PD edition of Cyril's Matthew commentary fragments
        #     (Cramer d. 1848). Added γ.4.6.
        #   - "Horovitz" — Josef Horovitz, "Das äthiopische Maccabäerbuch"
        #     (Zeitschrift für Assyriologie XIX, 1905, pp. 194-233) — the
        #     PD primary scholarly study of Meqabyan, integrated as
        #     apparatus source for γ.4.8 Mäqabyan seed. Added γ.4.8.
        #   - "CC0" — Creative Commons CC0 1.0 Universal Public Domain
        #     Dedication, the license under which the 2026-05-14 user-
        #     contributed Three Books of Meqabyan English translation
        #     (archive.org/details/three-books-of-meqabyan-cc0-translation)
        #     was released. CC0 is functionally equivalent to PD for the
        #     project's canonical-source-licensing requirement. Added
        #     γ.4.8.
        pd_anchors = ("NPNF", "Charles", "Payne Smith", "Cramer", "Horovitz", "CC0")
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
        # State-aware empty-lookup pin per CLAUDE_PROJECT_RULES §8:
        # do not assume any particular verse stays empty (γ.4.6.D
        # arc-close added Mt 28:1 women-first-witnesses; γ.4.x will
        # continue filling). Pick a (book, ch, v) that the loader's
        # for_verse cannot index — a non-corpus book with arbitrary
        # coordinates — and verify the empty-list contract.
        empty = ec.for_verse("nonexistent-book-xyz", 99, 99)
        assert empty == [], f"for_verse on a non-corpus book must return []; got {empty}"

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

    # γ.4.6.x quartet added at γ.4.6.D arc-close per §8.1 (FIFTH instance
    # after γ.4.4.E, γ.4.5.E, γ.4.2.D, γ.4.3.D). Future drift gets caught
    # at commit time.

    def test_meta_documents_gamma_4_6(self):
        self._assert_phase_mentioned("γ.4.6")

    def test_meta_documents_gamma_4_6_b(self):
        self._assert_phase_mentioned("γ.4.6.B")

    def test_meta_documents_gamma_4_6_c(self):
        self._assert_phase_mentioned("γ.4.6.C")

    def test_meta_documents_gamma_4_6_d(self):
        self._assert_phase_mentioned("γ.4.6.D")

    # γ.4.7.x quartet added at γ.4.7.D arc-close per §8.1 (SIXTH instance
    # after γ.4.4.E, γ.4.5.E, γ.4.2.D, γ.4.3.D, γ.4.6.D). Future drift
    # gets caught at commit time. With γ.4.7.D, ALL FOUR canonical-Gospel
    # Cyrillian arcs are closed: John γ.4.1-D, Luke γ.4.3-D, Matthew
    # γ.4.6-D, Mark γ.4.7-D.

    def test_meta_documents_gamma_4_7(self):
        self._assert_phase_mentioned("γ.4.7")

    def test_meta_documents_gamma_4_7_b(self):
        self._assert_phase_mentioned("γ.4.7.B")

    def test_meta_documents_gamma_4_7_c(self):
        self._assert_phase_mentioned("γ.4.7.C")

    def test_meta_documents_gamma_4_7_d(self):
        self._assert_phase_mentioned("γ.4.7.D")

    # γ.4.9 (Athanasius seed) added 2026-05-13 — OPENS A FIFTH PATRISTIC
    # VOICE alongside the four-voice composition (Cyril + Jubilees + 1 Enoch
    # + Ephrem) codified at ω.41 §1. Athanasius is the Tewahedo apostolic-
    # bridge: 20th Patriarch of the See of Mark + consecrator (c. 330) of
    # Frumentius + author of Festal Letter 39 (367 NT canon). The seed pairs
    # structurally with the γ.4.7-D Cyril-on-Mark arc-close: both are See-of-
    # Mark patriarchal-succession Christology. The _meta sync pin guards
    # against future drift in the γ.4.9.x detail-wave family if/when those
    # ship; for now γ.4.9 alone is pinned.

    def test_meta_documents_gamma_4_9(self):
        self._assert_phase_mentioned("γ.4.9")

    def test_meta_documents_gamma_4_9_b(self):
        self._assert_phase_mentioned("γ.4.9.B")

    def test_meta_documents_gamma_4_9_c(self):
        self._assert_phase_mentioned("γ.4.9.C")

    def test_meta_documents_gamma_4_9_d(self):
        self._assert_phase_mentioned("γ.4.9.D")

    def test_meta_documents_gamma_4_8(self):
        self._assert_phase_mentioned("γ.4.8")

    def test_meta_documents_gamma_4_8_b(self):
        self._assert_phase_mentioned("γ.4.8.B")

    def test_meta_documents_gamma_4_8_c(self):
        self._assert_phase_mentioned("γ.4.8.C")

    def test_meta_documents_gamma_4_8_d(self):
        self._assert_phase_mentioned("γ.4.8.D")

    def test_meta_documents_gamma_4_8_e(self):
        self._assert_phase_mentioned("γ.4.8.E")

    def test_meta_documents_gamma_4_8_f(self):
        # γ.4.8.F (2026-05-14) — Mäṣḥafä Mäqabyan Tier-2 audit integration
        # (post-arc-close apparatus refinement). Pinned for drift-detection.
        self._assert_phase_mentioned("γ.4.8.F")


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
        # away from 93% Cyril dominance. RULES §8.1 forbids share pins
        # (a denominator-relative pin silently flips as the corpus grows
        # via other fathers). Pin an ABSOLUTE Cyril ceiling instead; the
        # Ephrem floor (test_ephrem_now_substantively_present) already
        # guards the rebalance from the other side.
        cyril = self.ec.by_father("Cyril of Alexandria")
        # Live count at pin-time (2026-05-31) = 668; ceiling set just above
        # with small headroom (700) so honest ongoing Cyril ingest doesn't
        # trip it, but a runaway Cyril regression still fails.
        assert len(cyril) <= 700, f"γ.4.2 wave-1 Cyril ceiling: expected ≤700 Cyril entries; found {len(cyril)}"

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


class TestGamma46CyrilMatthewSeedWave:
    """γ.4.6 — Cyril of Alexandria on Matthew seed wave (2026-05-13).
    Opens the THIRD major Cyril Gospel arc after γ.4.1 (Cyril-on-John,
    closed at γ.4.1.D modulo Jn 8-10 manuscript gap) and γ.4.3 (Cyril-
    on-Luke, closed at γ.4.3.D four-wave parity). 45 verse-keyed entries
    spanning all 28 Matthean chapters. Source: Cyril's Matthew commentary
    survives only as catena fragments — authoritative PD edition is
    J.A. Cramer, *Catenae Graecorum Patrum in Novum Testamentum, Vol. I:
    In Evangelia S. Matthaei et S. Marci* (Oxford: University Press,
    1840 — PD); supplemented by Cyril fragments in PG 72 cols. 365-474
    (Migne, 1859 — PD).

    Seed wave (not arc-close). Detail waves γ.4.6.B/C/D to follow on the
    γ.4.3 cadence (~40-60 entries per wave, three-to-four waves for arc
    closure at ≥160-280 Matt entries).

    Pins (NOT arc-close — seed-wave standard pin set):
    - Matt 1-28 substantively seeded (≥45 Cyril entries on mat).
    - Major Matthean narrative blocks covered: Infancy (1-2), Baptism
      and Wilderness (3-4), Sermon-on-the-Mount (5-7), Galilean ministry
      (8-12), Parables (13), Mid-ministry (14-15), Caesarea Philippi +
      Transfiguration (16-17), Discourse (18-20), Jerusalem entry
      (21-23), Olivet eschatology (24-25), Passion (26-27), Resurrection
      (28).
    - Cyril absolute-count milestone ≥320 entries (per
      `feedback_share_pin_pattern` — absolute count, not share).
      γ.4.1.A-D shipped 116 Cyril-on-John + γ.4.3.A-D shipped 160 Cyril-
      on-Luke + γ.4.6 adds 45 Cyril-on-Matthew + 2 Cyril seed (gen, ps)
      = 323 floor at ≥320.
    - Signature passages: 1:1 (genealogy-biblos-geneseos), 1:23 (Emmanuel
      hypostatic-union), 2:11 (Magi gifts threefold-confession), 3:16
      (Trinitarian Jordan theophany), 5:17 (Law-fulfilled anti-Marcionite),
      5:48 (theosis-summons), 11:27 (homoousion-locus), 16:16 (Peter's
      Christological confession), 16:18 (rock-as-confession), 17:2
      (Transfiguration uncreated-light), 18:20 (ecclesiological-presence),
      26:26 (Eucharistic real-presence), 26:39 (Gethsemane two-wills
      Miaphysite), 27:46 (impassible-passion locus), 28:6 (Fasika
      resurrection-proclamation), 28:19 (Trinitarian baptismal-formula),
      28:20 (Emmanuel-inclusio).
    - _meta.source sync pin: γ.4.6 referenced + Cyril-on-Matthew
      signature + Cramer-Catenae source cited.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def test_matthew_substantively_seeded(self):
        cyril_mat = []
        for chapter in range(1, 29):
            for verse in range(1, 100):
                cyril_mat.extend(
                    e for e in self.ec.for_verse("mat", chapter, verse) if e.father == "Cyril of Alexandria"
                )
        assert len(cyril_mat) >= 45, f"γ.4.6 expected ≥45 Cyril entries on Matt 1-28; found {len(cyril_mat)}"

    def test_all_major_matthean_blocks_covered(self):
        def has_cyril_in(start, end):
            for chapter in range(start, end + 1):
                for verse in range(1, 100):
                    for entry in self.ec.for_verse("mat", chapter, verse):
                        if entry.father == "Cyril of Alexandria":
                            return True
            return False

        assert has_cyril_in(1, 2), "γ.4.6 missing Matthean Infancy narrative (Matt 1-2)"
        assert has_cyril_in(3, 4), "γ.4.6 missing Baptism + Wilderness (Matt 3-4)"
        assert has_cyril_in(5, 7), "γ.4.6 missing Sermon on the Mount (Matt 5-7)"
        assert has_cyril_in(8, 12), "γ.4.6 missing Galilean ministry (Matt 8-12)"
        assert has_cyril_in(13, 13), "γ.4.6 missing Kingdom parables (Matt 13)"
        assert has_cyril_in(14, 15), "γ.4.6 missing Mid-ministry (Matt 14-15)"
        assert has_cyril_in(16, 17), "γ.4.6 missing Caesarea Philippi + Transfiguration (Matt 16-17)"
        assert has_cyril_in(18, 20), "γ.4.6 missing Discourse + Discipleship (Matt 18-20)"
        assert has_cyril_in(21, 23), "γ.4.6 missing Jerusalem entry + Temple (Matt 21-23)"
        assert has_cyril_in(24, 25), "γ.4.6 missing Olivet eschatology (Matt 24-25)"
        assert has_cyril_in(26, 27), "γ.4.6 missing Passion narrative (Matt 26-27)"
        assert has_cyril_in(28, 28), "γ.4.6 missing Resurrection (Matt 28)"

    def test_cyril_milestone_count_at_or_above_matthew_seed(self):
        # γ.4.1.A-D shipped 116 Cyril-on-John + γ.4.3.A-D shipped 160
        # Cyril-on-Luke + γ.4 seed (2 misc) = 278. γ.4.6 adds 45 Cyril-
        # on-Matthew = 323. Floor at ≥320 as conservative post-γ.4.6
        # milestone. Absolute count per feedback_share_pin_pattern;
        # invariant under future voice-broadening waves.
        cyril_count = sum(
            1
            for verse_entries in self.ec._by_verse.values()
            for entry in verse_entries
            if entry.father == "Cyril of Alexandria"
        )
        assert cyril_count >= 320, (
            f"γ.4.6 expected Cyril count ≥320 (Matthew-seed close milestone); found {cyril_count}"
        )

    def test_all_twenty_eight_matthean_chapters_covered(self):
        # Stronger than block-coverage: every single Matthean chapter
        # has ≥1 Cyril entry. Prevents a future "I'll backfill Matt 9
        # later" silently leaving a chapter gap at seed time.
        chapters_seen = set()
        for chapter in range(1, 29):
            for verse in range(1, 100):
                for entry in self.ec.for_verse("mat", chapter, verse):
                    if entry.father == "Cyril of Alexandria":
                        chapters_seen.add(chapter)
                        break
        missing = sorted(set(range(1, 29)) - chapters_seen)
        assert not missing, f"γ.4.6 expected every Matt chapter 1-28 seeded; missing: {missing}"

    def test_genealogy_biblos_geneseos_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 1, 1) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6 missing Matt 1:1 — biblos-geneseos (Solomonic-Davidic Kǝbrä-Nägäśt anchor)"

    def test_emmanuel_hypostatic_union_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 1, 23) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6 missing Matt 1:23 — Emmanuel (hypostatic-union nomen-locus)"

    def test_magi_gifts_threefold_confession_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 2, 11) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6 missing Matt 2:11 — Magi gifts (gold/incense/myrrh threefold-confession Tewahedo Genna)"

    def test_jordan_trinitarian_theophany_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 3, 16) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6 missing Matt 3:16 — Jordan theophany (Trinitarian baptismal-locus Tewahedo Tǝmqät)"

    def test_law_fulfilled_anti_marcionite_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 5, 17) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6 missing Matt 5:17 — 'not to destroy but to fulfill' (anti-Marcionite Law-Prophets)"

    def test_theosis_summons_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 5, 48) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6 missing Matt 5:48 — 'be ye perfect' (Cyrillian theosis-summons)"

    def test_homoousion_locus_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 11, 27) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6 missing Matt 11:27 — 'no one knows the Son save the Father' (homoousion-locus)"

    def test_peters_confession_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 16, 16) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6 missing Matt 16:16 — Peter's confession (Christological summit anchor)"

    def test_rock_as_confession_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 16, 18) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6 missing Matt 16:18 — 'upon this rock' (rock-as-confession Tewahedo ecclesiology)"

    def test_transfiguration_uncreated_light_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 17, 2) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6 missing Matt 17:2 — Transfiguration Tabor (uncreated-light Tewahedo Buhe anchor)"

    def test_ecclesiological_presence_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 18, 20) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6 missing Matt 18:20 — 'where two or three' (ecclesiological-presence Qǝddāse-opening)"

    def test_hosanna_entry_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 21, 9) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6 missing Matt 21:9 — Hosanna-entry (Tewahedo Hosa'innā Sunday Zech-9 fulfillment)"

    def test_mesqel_eschatological_cross_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 24, 30) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6 missing Matt 24:30 — 'sign of the Son of Man' (Tewahedo Mäsqäl Cross-as-eschatological-sign)"

    def test_eucharistic_real_presence_matthean_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 26, 26) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6 missing Matt 26:26 — 'this IS my body' (Cyrillian real-presence Matthean-locus)"

    def test_gethsemane_two_wills_miaphysite_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 26, 39) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6 missing Matt 26:39 — 'let this cup pass' (Miaphysite two-wills Mahǝlet anchor)"

    def test_impassible_passion_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 27, 46) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6 missing Matt 27:46 — 'Eli Eli lama sabachthani' (Cyrillian impassible-passion Ps-22)"

    def test_fasika_resurrection_proclamation_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 28, 6) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6 missing Matt 28:6 — 'he is not here, he is risen' (Tewahedo Fasika kerygmatic-opening)"

    def test_trinitarian_baptismal_formula_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 28, 19) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6 missing Matt 28:19 — 'baptizing them in the name' (singular onoma Trinitarian-formula)"

    def test_emmanuel_inclusio_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 28, 20) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6 missing Matt 28:20 — 'lo I am with you always' (Emmanuel-inclusio with 1:23)"

    def test_meta_documents_gamma_4_6_expansion(self):
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_source = data["_meta"]["source"]
        assert "γ.4.6" in meta_source, "γ.4.6 must be referenced in _meta.source"
        assert "Cyril on Matthew" in meta_source or "Cyril-on-Matthew" in meta_source, (
            "γ.4.6 _meta.source should describe Cyril-on-Matthew"
        )
        assert "Cramer" in meta_source, "γ.4.6 _meta.source should cite J.A. Cramer (Catenae source)"


class TestGamma46BSermonOnMountWave:
    """γ.4.6.B — Cyril of Alexandria on Matthew detail wave I:
    Sermon-on-the-Mount (Matt 5-7). 50 verse-keyed entries deepening
    the 6 seed anchors (5:3 + 5:17 + 5:48 + 6:9 + 6:24 + 7:21);
    brings Sermon-on-the-Mount Cyrillian coverage to 56 entries.
    Mirrors γ.4.3.B Cyril-on-Luke Infancy-Galilean detail-wave
    structure (58 entries on Lk 1-9 after γ.4.3 seed).

    Pins (detail-wave standard set — NOT arc-close):
    - Sermon-on-the-Mount substantively detailed (≥50 NEW Cyril
      entries on Matt 5-7, exclusive of seed anchors).
    - All three Sermon chapters covered with substantive density
      (≥15 entries on Matt 5, ≥10 on Matt 6, ≥7 on Matt 7).
    - Cyril-on-Matthew absolute-count milestone ≥95 entries
      (per `feedback_share_pin_pattern`).
    - Beatitudes coverage: all eight macarisms 5:3-5:10 surfaced
      (5:3 from seed + 5:4-5:10 from this wave).
    - Lord's-Prayer petitions covered: 6:9 (seed) + 6:10 (kingdom/
      will) + 6:11 (epiousios) + 6:12 (forgive-as) + 6:13 (lead-
      us-not / deliver-from-evil-one).
    - Antitheses coverage: anger (5:22) + reconciliation (5:24) +
      lust (5:28) + divorce (5:32) + oaths (5:34) + non-
      retaliation (5:39) + love-enemies (5:44).
    - Signature Cyrillian-Cramer anchors: 5:8 pure-heart-theosis,
      5:18 iota-keraia, 5:24 Eucharistic-prerequisite reconciliation,
      6:11 epiousios super-substantial bread, 6:12 conditional-
      forgiveness, 7:7 ask-seek-knock, 7:12 Golden-Rule, 7:24
      wise-builder rock-foundation, 7:28 exousia-not-as-scribes.
    - _meta.source sync pin: γ.4.6.B + Sermon-on-the-Mount.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def test_sermon_on_mount_substantively_detailed(self):
        cyril_sermon = []
        for chapter in range(5, 8):
            for verse in range(1, 100):
                cyril_sermon.extend(
                    e for e in self.ec.for_verse("mat", chapter, verse) if e.father == "Cyril of Alexandria"
                )
        # γ.4.6 seed shipped 6 anchors on Matt 5-7 (5:3, 5:17, 5:48,
        # 6:9, 6:24, 7:21); γ.4.6.B adds 50 detail entries = 56 total.
        assert len(cyril_sermon) >= 56, (
            f"γ.4.6.B expected ≥56 Cyril entries on Matt 5-7 (Sermon); found {len(cyril_sermon)}"
        )

    def test_each_sermon_chapter_substantively_covered(self):
        per_chapter = {}
        for chapter in range(5, 8):
            n = 0
            for verse in range(1, 100):
                for entry in self.ec.for_verse("mat", chapter, verse):
                    if entry.father == "Cyril of Alexandria":
                        n += 1
            per_chapter[chapter] = n
        # γ.4.6 seed: Matt 5 had 3, Matt 6 had 2, Matt 7 had 1.
        # γ.4.6.B: Matt 5 +27 (→30), Matt 6 +13 (→15), Matt 7 +10 (→11).
        assert per_chapter[5] >= 25, f"γ.4.6.B Matt 5 expected ≥25 Cyril entries; got {per_chapter[5]}"
        assert per_chapter[6] >= 13, f"γ.4.6.B Matt 6 expected ≥13 Cyril entries; got {per_chapter[6]}"
        assert per_chapter[7] >= 10, f"γ.4.6.B Matt 7 expected ≥10 Cyril entries; got {per_chapter[7]}"

    def test_cyril_on_matthew_milestone_count_at_or_above_sermon_detail(self):
        cyril_mat = 0
        for chapter in range(1, 29):
            for verse in range(1, 100):
                for entry in self.ec.for_verse("mat", chapter, verse):
                    if entry.father == "Cyril of Alexandria":
                        cyril_mat += 1
        assert cyril_mat >= 95, f"γ.4.6.B expected ≥95 Cyril-on-Matthew entries; found {cyril_mat}"

    def test_all_eight_beatitudes_covered(self):
        # Mt 5:3-5:10 — the eight makarisms. 5:3 from seed; 5:4-5:10
        # from γ.4.6.B. (5:11-5:12 are extension blessings, not the
        # canonical eight.) Exhaustiveness pin.
        beatitude_verses = list(range(3, 11))
        missing = []
        for v in beatitude_verses:
            c = [e for e in self.ec.for_verse("mat", 5, v) if e.father == "Cyril of Alexandria"]
            if not c:
                missing.append(v)
        assert not missing, f"γ.4.6.B expected all eight Beatitudes (Mt 5:3-10) covered; missing 5:{missing}"

    def test_lords_prayer_petitions_covered(self):
        # The Lord's Prayer petitions: 6:9 (Our Father — seed) +
        # 6:10 (kingdom/will) + 6:11 (daily bread) + 6:12 (forgive)
        # + 6:13 (lead-us-not / deliver-from-evil-one).
        petition_verses = [9, 10, 11, 12, 13]
        missing = []
        for v in petition_verses:
            c = [e for e in self.ec.for_verse("mat", 6, v) if e.father == "Cyril of Alexandria"]
            if not c:
                missing.append(v)
        assert not missing, f"γ.4.6.B expected all Lord's-Prayer petitions covered; missing 6:{missing}"

    def test_antitheses_covered(self):
        # The six Antitheses of Mt 5: anger (5:22), lust (5:28),
        # divorce (5:32), oaths (5:34), non-retaliation (5:39),
        # love-enemies (5:44).
        antithesis_verses = [22, 28, 32, 34, 39, 44]
        missing = []
        for v in antithesis_verses:
            c = [e for e in self.ec.for_verse("mat", 5, v) if e.father == "Cyril of Alexandria"]
            if not c:
                missing.append(v)
        assert not missing, f"γ.4.6.B expected all six Antitheses covered; missing 5:{missing}"

    def test_pure_in_heart_theosis_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 5, 8) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.B missing Matt 5:8 — pure-in-heart see-God (theosis-precondition)"

    def test_iota_keraia_torah_immutability_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 5, 18) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.B missing Matt 5:18 — iota-keraia (Torah-immutability)"

    def test_eucharistic_prerequisite_reconciliation_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 5, 24) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.B missing Matt 5:24 — leave-thy-gift-at-altar (Tewahedo Pax Eucharistic-prerequisite)"

    def test_epiousios_super_substantial_bread_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 6, 11) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.B missing Matt 6:11 — epiousios super-substantial bread (Tewahedo Qǝddāse fraction-rite)"

    def test_conditional_forgiveness_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 6, 12) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.B missing Matt 6:12 — forgive-us-as-we-forgive (conditional-petition)"

    def test_ask_seek_knock_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 7, 7) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.B missing Matt 7:7 — ask-seek-knock (perseverant-prayer triplet)"

    def test_golden_rule_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 7, 12) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.B missing Matt 7:12 — Golden Rule (whole-Law-and-Prophets summary)"

    def test_wise_builder_rock_foundation_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 7, 24) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.B missing Matt 7:24 — wise-builder Christological-Petra (foundation-on-rock)"

    def test_exousia_not_as_scribes_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 7, 28) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.B missing Matt 7:28 — exousia-not-as-scribes (authority Sermon-conclusion)"

    def test_love_enemies_divine_imitation_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 5, 44) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.B missing Matt 5:44 — love-enemies (divine-imitation summit)"

    def test_universal_providence_sun_rain_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 5, 45) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.B missing Matt 5:45 — sun-on-good-and-evil (universal-providence ground)"

    def test_single_eye_haplotēs_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 6, 22) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.B missing Matt 6:22 — single-eye haplotēs (undivided-intention)"

    def test_seek_first_kingdom_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 6, 33) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.B missing Matt 6:33 — seek-first-kingdom (orderly-desire-rule)"

    def test_narrow_gate_two_ways_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 7, 13) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.B missing Matt 7:13 — narrow-gate two-ways (renunciation-charter)"

    def test_false_prophets_sheeps_clothing_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 7, 15) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.B missing Matt 7:15 — false-prophets-in-sheep's-clothing (Tewahedo discernment-of-teaching)"

    def test_meta_documents_gamma_4_6_b_expansion(self):
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_source = data["_meta"]["source"]
        assert "γ.4.6.B" in meta_source, "γ.4.6.B must be referenced in _meta.source"
        assert "Sermon-on-the-Mount" in meta_source or "Sermon on the Mount" in meta_source, (
            "γ.4.6.B _meta.source should describe the Sermon-on-the-Mount wave"
        )


class TestGamma46CGalileanMinistryWave:
    """γ.4.6.C — Cyril of Alexandria on Matthew detail wave II:
    Galilean Ministry (Matt 8-13). 50 verse-keyed entries deepening
    the 7 thin seed anchors (8:11 + 9:13 + 10:32 + 11:27 + 12:8 +
    13:30 + 13:44); brings Galilean-ministry Cyrillian coverage to
    57 entries — parity with γ.4.6.B Sermon-on-Mount density.
    Mirrors γ.4.6.B Sermon-on-Mount + γ.4.3.B Cyril-on-Luke Infancy-
    Galilean detail-wave structure.

    Per §8.1 this is a DETAIL wave, NOT an arc-close — γ.4.6.D
    (Matt 14-28 Passion + Resurrection) will close the Matthew arc
    with full §8.1 pins (count milestone ≥260, all-NT-narrative-
    blocks-covered, _meta sync per sub-phase).

    Pins (detail-wave standard set):
    - Galilean-ministry substantively detailed (≥57 Cyril entries
      on Matt 8-13, inclusive of seed; seed had 7).
    - All six chapters covered with substantive density
      (≥8 on Matt 8, ≥7 on Matt 9, ≥6 on Matt 10, ≥5 on Matt 11,
      ≥7 on Matt 12, ≥10 on Matt 13).
    - Cyril-on-Matthew absolute-count milestone ≥145 entries
      (per `feedback_share_pin_pattern` — never a share-pin).
    - Healing-cycle exhaustiveness: leper (8:2-3) + centurion's-
      servant (8:8) + Peter's-mother-in-law (8:15) + Isa-53-
      fulfillment (8:17) + storm-stilling (8:26) + Gadarene-
      demoniacs (8:29) + paralytic-forgiveness (9:2) + authority-
      to-forgive (9:6) + hemorrhaging-woman (9:21).
    - Mission-Discourse exhaustiveness: apostolic-authority (10:1)
      + freely-give (10:8) + sheep-among-wolves (10:16) + endure-
      to-end (10:22) + fear-not-body-killers (10:28) + not-peace-
      but-sword (10:34) + lose-life-find-life (10:39).
    - Rest-invitation exhaustiveness (Mt 11:28-30 SIGNATURE
      Tewahedo-rest doctrine): 11:28 come-unto-me-all + 11:29 take-
      my-yoke + 11:30 yoke-easy-burden-light.
    - Kingdom-Parables exhaustiveness — the five Mt 13 parables NOT
      in γ.4.6 seed (seed covered 13:30 tares + 13:44 treasure):
      Sower (13:3) + Mustard-Seed (13:31) + Leaven (13:33) + Pearl
      (13:45) + Dragnet (13:47).
    - Signature Cyrillian-Cramer anchors: 8:8 centurion-Qǝddāse-
      confession-anchor, 8:17 Isa-53-fulfillment Christological key,
      11:28 come-unto-me-all rest-invitation, 11:29 take-my-yoke
      meek-and-lowly, 11:30 yoke-easy Chrēstos-pun, 12:28 Spirit-of-
      God-kingdom-come pneumatological-eschatology, 12:31 blasphemy-
      against-Spirit unforgivable, 13:43 shine-as-sun Tabor-Anaphora,
      13:45 pearl-of-great-price Mary-as-Pearl Tewahedo-Mäshafä-
      Bǝrhān anchor.
    - _meta.source sync pin: γ.4.6.C + Galilean-ministry.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def test_galilean_ministry_substantively_detailed(self):
        cyril_galilean = []
        for chapter in range(8, 14):
            for verse in range(1, 100):
                cyril_galilean.extend(
                    e for e in self.ec.for_verse("mat", chapter, verse) if e.father == "Cyril of Alexandria"
                )
        # γ.4.6 seed shipped 7 anchors on Matt 8-13 (8:11, 9:13, 10:32,
        # 11:27, 12:8, 13:30, 13:44); γ.4.6.C adds 50 detail entries = 57 total.
        assert len(cyril_galilean) >= 57, (
            f"γ.4.6.C expected ≥57 Cyril entries on Matt 8-13 (Galilean ministry); found {len(cyril_galilean)}"
        )

    def test_each_galilean_chapter_substantively_covered(self):
        per_chapter = {}
        for chapter in range(8, 14):
            n = 0
            for verse in range(1, 100):
                for entry in self.ec.for_verse("mat", chapter, verse):
                    if entry.father == "Cyril of Alexandria":
                        n += 1
            per_chapter[chapter] = n
        # γ.4.6 seed: Matt 8-13 each had 1, Matt 13 had 2.
        # γ.4.6.C: +9 / +8 / +7 / +6 / +8 / +12 = +50.
        assert per_chapter[8] >= 8, f"γ.4.6.C Matt 8 expected ≥8 Cyril entries; got {per_chapter[8]}"
        assert per_chapter[9] >= 7, f"γ.4.6.C Matt 9 expected ≥7 Cyril entries; got {per_chapter[9]}"
        assert per_chapter[10] >= 6, f"γ.4.6.C Matt 10 expected ≥6 Cyril entries; got {per_chapter[10]}"
        assert per_chapter[11] >= 5, f"γ.4.6.C Matt 11 expected ≥5 Cyril entries; got {per_chapter[11]}"
        assert per_chapter[12] >= 7, f"γ.4.6.C Matt 12 expected ≥7 Cyril entries; got {per_chapter[12]}"
        assert per_chapter[13] >= 10, f"γ.4.6.C Matt 13 expected ≥10 Cyril entries; got {per_chapter[13]}"

    def test_cyril_on_matthew_milestone_count_at_or_above_galilean_detail(self):
        cyril_mat = 0
        for chapter in range(1, 29):
            for verse in range(1, 100):
                for entry in self.ec.for_verse("mat", chapter, verse):
                    if entry.father == "Cyril of Alexandria":
                        cyril_mat += 1
        # γ.4.6 seed: 45 + γ.4.6.B Sermon: +50 → 95 + γ.4.6.C Galilean: +50 → 145.
        # Use absolute count per `feedback_share_pin_pattern`.
        assert cyril_mat >= 145, (
            f"γ.4.6.C expected ≥145 Cyril-on-Matthew entries (45 seed + 50 γ.4.6.B + 50 γ.4.6.C); found {cyril_mat}"
        )

    def test_healing_cycle_substantively_covered(self):
        # Matt 8-9 healing cycle: leper (8:2-3), centurion-servant (8:8),
        # Peter's-mother-in-law (8:15), Isa-53-fulfillment (8:17), storm
        # (8:26), Gadarene-demoniacs (8:29), paralytic-forgiveness (9:2),
        # authority-to-forgive (9:6), hemorrhaging-woman (9:21). Nine pivotal
        # verses across the healing-cycle should each carry Cyrillian
        # commentary. Exhaustiveness pin.
        healing_verses = [
            (8, 2),
            (8, 8),
            (8, 15),
            (8, 17),
            (8, 26),
            (8, 29),
            (9, 2),
            (9, 6),
            (9, 21),
        ]
        missing = []
        for ch, v in healing_verses:
            c = [e for e in self.ec.for_verse("mat", ch, v) if e.father == "Cyril of Alexandria"]
            if not c:
                missing.append(f"{ch}:{v}")
        assert not missing, f"γ.4.6.C expected full healing-cycle coverage in Matt 8-9; missing {missing}"

    def test_mission_discourse_substantively_covered(self):
        # Matt 10 Mission Discourse — apostolic-authority (10:1) +
        # freely-give (10:8) + sheep-among-wolves (10:16) + endure-to-
        # end (10:22) + fear-not-body-killers (10:28) + not-peace-but-
        # sword (10:34) + lose-life-find-life (10:39). Seven pivotal
        # verses across the mission charter.
        mission_verses = [1, 8, 16, 22, 28, 34, 39]
        missing = []
        for v in mission_verses:
            c = [e for e in self.ec.for_verse("mat", 10, v) if e.father == "Cyril of Alexandria"]
            if not c:
                missing.append(v)
        assert not missing, f"γ.4.6.C expected full Mission-Discourse coverage in Matt 10; missing 10:{missing}"

    def test_rest_invitation_full_triplet_covered(self):
        # Mt 11:28-30 is the Cyrillian-Tewahedo-rest signature locus —
        # the three verses MUST all be present for the doctrine to be
        # substantively grounded. Signature exhaustiveness pin.
        rest_verses = [28, 29, 30]
        missing = []
        for v in rest_verses:
            c = [e for e in self.ec.for_verse("mat", 11, v) if e.father == "Cyril of Alexandria"]
            if not c:
                missing.append(v)
        assert not missing, (
            f"γ.4.6.C expected full come-unto-me-all rest-invitation (Mt 11:28-30); missing 11:{missing}"
        )

    def test_kingdom_parables_substantively_covered(self):
        # The five Mt 13 parables NOT covered by γ.4.6 seed: Sower
        # (13:3), Mustard-Seed (13:31), Leaven (13:33), Pearl (13:45),
        # Dragnet (13:47). γ.4.6 seed covered Tares (13:30) and
        # Treasure (13:44 — labeled "pearl of great price" in seed
        # though the verse is actually the treasure-in-the-field
        # parable). γ.4.6.C surfaces the five missing kingdom-parables.
        parable_verses = [3, 31, 33, 45, 47]
        missing = []
        for v in parable_verses:
            c = [e for e in self.ec.for_verse("mat", 13, v) if e.father == "Cyril of Alexandria"]
            if not c:
                missing.append(v)
        assert not missing, (
            f"γ.4.6.C expected all five non-seed Kingdom-parables covered "
            f"(Sower 13:3 + Mustard 13:31 + Leaven 13:33 + Pearl 13:45 + Dragnet 13:47); "
            f"missing 13:{missing}"
        )

    def test_centurion_qeddase_confession_anchor_present(self):
        # Mt 8:8 is the Tewahedo Qǝddāse pre-communion confession-anchor
        # ("I am not worthy that thou shouldest enter under the roof of
        # my soul"). Signature pin.
        c = [e for e in self.ec.for_verse("mat", 8, 8) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.6.C missing Matt 8:8 — centurion 'speak the word only' (Tewahedo "
            "Qǝddāse pre-communion confession-anchor)"
        )

    def test_isaiah_53_fulfillment_anchor_present(self):
        # Mt 8:17's Isa 53 citation is the Cyrillian christological key
        # interpreting the Galilean healings as proleptic Passion-events.
        c = [e for e in self.ec.for_verse("mat", 8, 17) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.C missing Matt 8:17 — 'himself took our infirmities' (Isa-53 Christological-fulfillment key)"

    def test_come_unto_me_all_anchor_present(self):
        # Mt 11:28 — the Cyrillian-Tewahedo-rest signature locus. The
        # central anchor of monastic-rest theology and Sänbätä-Krǝstiyan
        # Sabbath-in-Christ doctrine.
        c = [e for e in self.ec.for_verse("mat", 11, 28) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.C missing Matt 11:28 — 'come unto me all ye that labour' (Tewahedo signature-rest-invitation)"

    def test_take_my_yoke_meek_and_lowly_anchor_present(self):
        # Mt 11:29 — the praos-tapeinos-tē-kardia (meek-and-lowly-in-
        # heart) Christological-humility self-description.
        c = [e for e in self.ec.for_verse("mat", 11, 29) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.C missing Matt 11:29 — 'take my yoke / I am meek and lowly' (Christological-humility doctrine)"

    def test_yoke_easy_chrestos_pun_anchor_present(self):
        # Mt 11:30 — the Cyrillian Chrēstos / Christos near-homonymy
        # play: Christ's-yoke is Chrēstos-yoke (kindly), the bearer
        # shares the carrying.
        c = [e for e in self.ec.for_verse("mat", 11, 30) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.C missing Matt 11:30 — 'my yoke is easy' (Chrēstos-pun + Tewahedo monastic-rule prologue)"

    def test_spirit_of_god_kingdom_come_anchor_present(self):
        # Mt 12:28 — pneumatological-eschatology summary; Spirit-driven
        # exorcism manifests present-irrupting kingdom.
        c = [e for e in self.ec.for_verse("mat", 12, 28) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.6.C missing Matt 12:28 — 'if I cast out devils by the Spirit of God' (pneumatological-eschatology)"
        )

    def test_blasphemy_against_spirit_unforgivable_anchor_present(self):
        # Mt 12:31 — the Cyrillian unforgivable-disposition locus, key
        # for distinguishing the unforgivable from ordinary post-
        # baptismal sin in Tewahedo sacramental-confession theology.
        c = [e for e in self.ec.for_verse("mat", 12, 31) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.C missing Matt 12:31 — blasphemy-against-Holy-Spirit (unforgivable-disposition locus)"

    def test_shine_as_sun_tabor_anaphora_anchor_present(self):
        # Mt 13:43 — eschatological-glorification deification-language;
        # paired with Mt 17:2 Tabor transfiguration as Tewahedo
        # iconographic sun-halo-of-saints prooftext.
        c = [e for e in self.ec.for_verse("mat", 13, 43) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.6.C missing Matt 13:43 — 'righteous shall shine as the sun' "
            "(eschatological-deification + Tabor-Anaphora pair)"
        )

    def test_pearl_of_great_price_mary_anchor_present(self):
        # Mt 13:45 — the Cyrillian-Tewahedo Pearl-of-Great-Price as
        # Mary-as-the-Pearl signature; the Mäshafä-Bǝrhān cites
        # Mt 13:45-46 in the Theotokos-titulature.
        c = [e for e in self.ec.for_verse("mat", 13, 45) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.C missing Matt 13:45 — pearl-of-great-price (Mary-as-Pearl Tewahedo-Mäshafä-Bǝrhān anchor)"

    def test_dragnet_corpus_permixtum_anchor_present(self):
        # Mt 13:47 — the sagēnē mixed-ecclesiology text; ecclesia-
        # militans is mixed-by-intent; ecclesia-triumphans is
        # eschaton-purified.
        c = [e for e in self.ec.for_verse("mat", 13, 47) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.C missing Matt 13:47 — dragnet (corpus-permixtum mixed-ecclesiology)"

    def test_meta_documents_gamma_4_6_c_expansion(self):
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_source = data["_meta"]["source"]
        assert "γ.4.6.C" in meta_source, "γ.4.6.C must be referenced in _meta.source"
        assert "Galilean-ministry" in meta_source or "Galilean ministry" in meta_source, (
            "γ.4.6.C _meta.source should describe the Galilean-ministry wave"
        )


class TestGamma46DCyrilMatthewArcClose:
    """γ.4.6.D — Cyril of Alexandria on Matthew arc-close wave
    (Matt 14-28: Galilean miracles + Jerusalem entry + Olivet
    discourse + Passion narrative + Resurrection + Great
    Commission). CLOSING WAVE of the four-wave Cyril-on-Matthew
    arc per §8.1 arc-close convention. 50 verse-keyed entries
    distributed across all 15 chapters Matt 14-28. Closes the
    THIRD Cyril Gospel arc:

        Cyril-on-John   γ.4.1-D  116 entries (closed earlier)
        Cyril-on-Luke   γ.4.3-D  160 entries (closed 2026-05-13)
        Cyril-on-Matthew γ.4.6-D 195 entries (closed by γ.4.6.D)
                                (45 seed + 50 γ.4.6.B + 50 γ.4.6.C
                                 + 50 γ.4.6.D)
        Cumulative Cyril-on-Gospels: 471 entries.

    FIFTH instance of §8.1 arc-close convention (after γ.4.4.E
    Mäṣḥafä Hēnok, γ.4.5.E Mäṣḥafä Kufāle, γ.4.2.D Pentateuch,
    γ.4.3.D Cyril-on-Luke).

    Per §8.1 the closing wave's test class MUST add the three
    specific pin types:
    (1) _meta synchronization pin per sub-phase tag with regex
        word-boundary matching;
    (2) absolute-count milestone pin at cumulative arc-close
        count;
    (3) all_N_sections_covered exhaustiveness pin asserting every
        section the arc was supposed to cover has substantive
        coverage at planned depth.

    Pins:
    - Matt 14-28 substantively detailed (≥72 total Cyril entries
      on Matt 14-28 = 22 seed + 50 arc-close detail).
    - Every chapter Matt 14-28 carries ≥2 Cyril entries (parity
      floor — even the lightest-coverage chapters get arc-close
      depth).
    - **§8.1 ARC-CLOSE PIN #1 — count milestone:** Cyril-on-Matthew
      absolute-count ≥190 entries (per `feedback_share_pin_pattern`
      — never a share-pin; durable against future voice-broadening).
    - **§8.1 ARC-CLOSE PIN #2 — all_N_sections_covered
      exhaustiveness:**
      test_all_four_cyril_matthew_waves_substantively_covered
      asserts γ.4.6 seed (≥45) + γ.4.6.B Matt 5-7 (≥56) + γ.4.6.C
      Matt 8-13 (≥57) + γ.4.6.D Matt 14-28 (≥72) — every section
      the Cyril-on-Matthew arc was supposed to cover has
      substantive coverage at planned depth.
    - **§8.1 ARC-CLOSE PIN #3 — _meta synchronization:** pin per
      sub-phase tag (γ.4.6, γ.4.6.B, γ.4.6.C, γ.4.6.D) with regex
      word-boundary; `test_meta_synchronization_at_arc_close`.
    - 12 signature-passage pins for new Tewahedo anchors at the
      arc-close: 14:25 walking-on-water egō-eimi + 16:19 binding-
      loosing keys + 17:1 Tabor mountain-selection + 17:20 mustard-
      seed-faith + 19:6 one-flesh marital-indissolubility + 21:5
      king-meek-on-ass Zech 9:9 + 21:42 stone-rejected-cornerstone
      Ps 118:22-23 + 22:21 render-to-Caesar dual-jurisdiction +
      25:6 midnight-cry-bridegroom vigil + 26:28 blood-of-covenant
      Anaphora-form + 26:41 watch-and-pray Gethsemane + 28:18 all-
      authority-given Cosmic-Christ.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def _cyril_in_chapter(self, chapter):
        out = []
        for verse in range(1, 100):
            out.extend(e for e in self.ec.for_verse("mat", chapter, verse) if e.father == "Cyril of Alexandria")
        return out

    def _cyril_in_range(self, ch_start, ch_end):
        return sum(len(self._cyril_in_chapter(c)) for c in range(ch_start, ch_end + 1))

    def test_matt_14_28_substantively_detailed(self):
        total = self._cyril_in_range(14, 28)
        # γ.4.6 seed shipped 22 anchors on Matt 14-28; γ.4.6.D adds 50.
        assert total >= 72, (
            f"γ.4.6.D expected ≥72 Cyril entries on Matt 14-28 (22 seed + 50 arc-close detail); found {total}"
        )

    def test_every_arc_close_chapter_has_minimum_coverage(self):
        # Parity floor: every chapter Matt 14-28 should carry ≥2
        # Cyril entries after γ.4.6.D arc-close. Prevents a future
        # "I'll cover Matt 24 later" from silently leaving a chapter
        # in seed-only depth.
        per_chapter = {ch: len(self._cyril_in_chapter(ch)) for ch in range(14, 29)}
        below_floor = {ch: n for ch, n in per_chapter.items() if n < 2}
        assert not below_floor, (
            f"γ.4.6.D arc-close: every Matt 14-28 chapter should have ≥2 "
            f"Cyril entries; below-floor chapters: {below_floor}"
        )

    def test_cyril_on_matthew_arc_close_count_milestone(self):
        # §8.1 ARC-CLOSE PIN #2: absolute-count milestone at arc close.
        # Per feedback_share_pin_pattern: never a share pin.
        # Cumulative: 45 (γ.4.6 seed) + 50 (γ.4.6.B Sermon) + 50
        # (γ.4.6.C Galilean) + 50 (γ.4.6.D arc-close) = 195. ≥190 floor.
        cyril_mat = 0
        for chapter in range(1, 29):
            for verse in range(1, 100):
                for entry in self.ec.for_verse("mat", chapter, verse):
                    if entry.father == "Cyril of Alexandria":
                        cyril_mat += 1
        assert cyril_mat >= 190, (
            f"γ.4.6.D arc-close: Cyril-on-Matthew count ≥190 expected "
            f"(cumulative four-wave arc-close milestone: 45 seed + 50 "
            f"γ.4.6.B + 50 γ.4.6.C + 50 γ.4.6.D = 195); found {cyril_mat}"
        )

    def test_all_four_cyril_matthew_waves_substantively_covered(self):
        # §8.1 ARC-CLOSE PIN #3: all_N_sections_covered exhaustiveness.
        # Every section of the Cyril-on-Matthew arc must have substantive
        # coverage at planned depth. The four waves are:
        # γ.4.6 seed (45 entries across all 28 chapters)
        # γ.4.6.B Matt 5-7 Sermon-on-Mount detail (≥56 cumulative)
        # γ.4.6.C Matt 8-13 Galilean-ministry detail (≥57 cumulative)
        # γ.4.6.D Matt 14-28 arc-close detail (≥72 cumulative)
        # This pin prevents a future "I'll ship Matt 14-28 later" from
        # silently leaving the arc partially closed.
        total_cyril_mat = self._cyril_in_range(1, 28)
        mat_5_7 = self._cyril_in_range(5, 7)
        mat_8_13 = self._cyril_in_range(8, 13)
        mat_14_28 = self._cyril_in_range(14, 28)

        assert total_cyril_mat >= 190, (
            f"γ.4.6.D arc-close: total Cyril-on-Matthew ≥190 expected (four waves); found {total_cyril_mat}"
        )
        assert mat_5_7 >= 56, f"γ.4.6.D arc-close: Matt 5-7 below γ.4.6.B parity (need ≥56, have {mat_5_7})"
        assert mat_8_13 >= 57, f"γ.4.6.D arc-close: Matt 8-13 below γ.4.6.C parity (need ≥57, have {mat_8_13})"
        assert mat_14_28 >= 72, f"γ.4.6.D arc-close: Matt 14-28 below γ.4.6.D parity (need ≥72, have {mat_14_28})"

    def test_meta_synchronization_at_arc_close(self):
        # §8.1 ARC-CLOSE PIN #1: _meta synchronization. Pin per
        # sub-phase tag with regex word-boundary so γ.4.6 doesn't
        # accidentally match γ.4.6.B/C/D. Granular failures (per
        # sub-phase) are easier to diagnose than a combined pin.
        import json
        import re
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_source = data["_meta"]["source"]
        assert re.search(r"γ\.4\.6(?![.A-Z])", meta_source), "γ.4.6 seed wave must be in _meta.source"
        assert re.search(r"γ\.4\.6\.B(?![A-Z])", meta_source), (
            "γ.4.6.B Sermon-on-Mount detail wave must be in _meta.source"
        )
        assert re.search(r"γ\.4\.6\.C(?![A-Z])", meta_source), (
            "γ.4.6.C Galilean-ministry detail wave must be in _meta.source"
        )
        assert re.search(r"γ\.4\.6\.D(?![A-Z])", meta_source), "γ.4.6.D arc-close wave must be in _meta.source"
        # arc-close must describe Matt 14-28 scope explicitly
        assert (
            "Matt 14-28" in meta_source
            or "Passion narrative" in meta_source
            or "Resurrection + Great Commission" in meta_source
        ), "γ.4.6.D _meta.source should describe the Matt 14-28 (Passion + Resurrection + Great Commission) scope"
        # arc-close must record arc-close status explicitly
        assert (
            "Cyril-on-Matthew arc is CLOSED" in meta_source
            or "CLOSING WAVE of the four-wave Cyril-on-Matthew arc" in meta_source
        ), "γ.4.6.D _meta.source should record the arc-close explicitly"

    # ---- Signature passage pins (12 anchors for Tewahedo distinctives) ----

    def test_walking_on_water_ego_eimi_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 14, 25) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.D missing Matt 14:25 — walking-on-water 'It is I' (egō-eimi Christological-divine-name claim)"

    def test_binding_and_loosing_keys_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 16, 19) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.6.D missing Matt 16:19 — keys-of-the-kingdom binding-and-loosing (apostolic-magisterial donation)"
        )

    def test_tabor_mountain_selection_anchor_present(self):
        # Mt 17:2 is γ.4.6 seed (Transfiguration body); 17:1 is the
        # γ.4.6.D mountain-selection + six-day-typology anchor.
        c = [e for e in self.ec.for_verse("mat", 17, 1) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.6.D missing Matt 17:1 — Tabor mountain-selection + six-day-creation-"
            "typology (Tewahedo Buhe iconographic-mountain anchor)"
        )

    def test_mustard_seed_faith_quality_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 17, 20) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.D missing Matt 17:20 — mustard-seed-faith (quality-not-quantity kenōsis-faith couplet)"

    def test_one_flesh_marital_indissolubility_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 19, 6) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.6.D missing Matt 19:6 — one-flesh-not-twain (Tewahedo marital-indissolubility anchor)"

    def test_king_meek_on_ass_zech_9_9_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 21, 5) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.6.D missing Matt 21:5 — king-meek-on-ass (Zech 9:9 prophetic-"
            "fulfillment; Tewahedo Hosanna-Sunday liturgy)"
        )

    def test_stone_rejected_cornerstone_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 21, 42) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.6.D missing Matt 21:42 — stone-rejected-becomes-cornerstone "
            "(Ps 118:22-23 four-fold cornerstone-prooftext)"
        )

    def test_render_to_caesar_dual_jurisdiction_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 22, 21) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.6.D missing Matt 22:21 — render-to-Caesar-and-God (Tewahedo twofold-jurisdiction political-theology)"
        )

    def test_midnight_cry_bridegroom_vigil_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 25, 6) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.6.D missing Matt 25:6 — midnight-cry bridegroom-cometh "
            "(Tewahedo Mahǝlet-Mǝsǝṭǝs midnight-office vigil)"
        )

    def test_blood_of_covenant_anaphora_form_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 26, 28) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.6.D missing Matt 26:28 — blood-of-covenant shed-for-many "
            "(Tewahedo Anaphora-institution words-of-institution)"
        )

    def test_watch_and_pray_gethsemane_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 26, 41) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.6.D missing Matt 26:41 — watch-and-pray spirit-willing-flesh-weak (Tewahedo monastic-vigil discipline)"
        )

    def test_all_authority_given_cosmic_christ_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 28, 18) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.6.D missing Matt 28:18 — all-authority-given-in-heaven-and-earth "
            "(Cosmic-Christ cosmocrator; Great-Commission ground)"
        )


class TestGamma47CyrilMarkSeedWave:
    """γ.4.7 — Cyril of Alexandria on Mark (seed wave, 2026-05-13).
    Opens the FOURTH and final canonical-Gospel Cyrillian arc after
    the three closed arcs:

        Cyril-on-John   γ.4.1-D   116 entries (closed earlier)
        Cyril-on-Luke   γ.4.3-D   160 entries (closed 2026-05-13 AM)
        Cyril-on-Matthew γ.4.6-D  195 entries (closed 2026-05-13)
        Cyril-on-Mark   γ.4.7      40 entries  ← opened by γ.4.7

    Cumulative Cyril-on-Gospels post-γ.4.7: 511 entries across all
    4 canonical Gospels at substantive seed-or-detail depth.

    Source: Cyril's Mark commentary survives only as catena fragments.
    Authoritative PD edition is J.A. Cramer, *Catenae Graecorum Patrum
    in Novum Testamentum, Vol. I: In Evangelia S. Matthaei et S. Marci*
    (Oxford: University Press, 1840 — PD); supplemented by Cyril
    fragments in PG 72 (Migne, 1859 — PD).

    Mark is the Coptic-Alexandrian Gospel par excellence. Tradition
    attributes to John Mark, founder of the Coptic Church via the
    Alexandrian see. The apostolic succession runs Mark → Anianus →
    … → Athanasius → … → Frumentius (Tewahedo founder, consecrated by
    Athanasius c. 330). Cyril is the 24th Patriarch of the See of Mark.
    Reading Cyril on Mark closes a hermeneutical loop: the Alexandrian-
    Coptic patriarch comments on the Gospel attributed to the
    Alexandrian-Coptic founder, in the tradition that birthed Tewahedo.

    Seed wave (NOT arc-close — γ.4.7.B/C/D detail-waves to follow per
    γ.4.1 + γ.4.3 + γ.4.6 precedent). Pins (seed-wave standard set):
    - Mark 1-16 substantively seeded (≥40 Cyril entries on mrk).
    - Major Markan narrative blocks covered: Prologue + Baptism (1),
      Galilean Ministry (2-3), Kingdom-Parables (4), Miracles (5-6),
      Defilement + Syrophoenician (7), Petrine-confession + Passion-
      prediction (8-9), Discipleship-Discourse (10), Jerusalem Entry
      + Temple (11-12), Olivet (13), Passion (14-15), Resurrection
      (16).
    - Every single Markan chapter Mark 1-16 covered (stronger than
      block-coverage).
    - Cyril absolute-count milestone ≥510 entries (471 prior + 40 new
      = 511; ≥510 conservative floor per `feedback_share_pin_pattern`).
    - Signature passages: 1:10 Trinitarian-baptism Jordan-theophany +
      1:15 kingdom-near metanoia-pisteue + 3:35 obedient-family Marian-
      double-kinship + 4:31 mustard-seed Frumentius-founding-
      fulfillment + 6:7 two-by-two sending Frumentius-Edesius pattern
      + 7:28 Syrophoenician Cushite-Gentile-inclusion + 8:29 Petrine-
      confession sy-ei-ho-Christos + 9:24 'help-mine-unbelief' proto-
      catechumen-prayer + 10:45 ransom-for-many atonement-summit +
      11:17 house-of-prayer-for-all-nations Coptic-Tewahedo-
      fulfillment + 13:32 'neither-the-Son' communicatio-idiomatum +
      14:36 Abba-Father two-wills Miaphysite-Christology + 15:39
      centurion-confession structural-inclusio + 16:6 'He-is-risen'
      Fasika-proclamation.
    - _meta.source sync pin: γ.4.7 referenced + Cyril-on-Mark signature
      + Cramer-Catenae source cited.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def test_mark_substantively_seeded(self):
        cyril_mrk = []
        for chapter in range(1, 17):
            for verse in range(1, 100):
                cyril_mrk.extend(
                    e for e in self.ec.for_verse("mrk", chapter, verse) if e.father == "Cyril of Alexandria"
                )
        assert len(cyril_mrk) >= 40, f"γ.4.7 expected ≥40 Cyril entries on Mark 1-16; found {len(cyril_mrk)}"

    def test_all_major_markan_blocks_covered(self):
        def has_cyril_in(start, end):
            for chapter in range(start, end + 1):
                for verse in range(1, 100):
                    for entry in self.ec.for_verse("mrk", chapter, verse):
                        if entry.father == "Cyril of Alexandria":
                            return True
            return False

        assert has_cyril_in(1, 1), "γ.4.7 missing Markan Prologue + Baptism (Mark 1)"
        assert has_cyril_in(2, 3), "γ.4.7 missing Galilean Ministry (Mark 2-3)"
        assert has_cyril_in(4, 4), "γ.4.7 missing Kingdom Parables (Mark 4)"
        assert has_cyril_in(5, 6), "γ.4.7 missing Miracles + Mid-ministry (Mark 5-6)"
        assert has_cyril_in(7, 7), "γ.4.7 missing Defilement + Syrophoenician (Mark 7)"
        assert has_cyril_in(8, 9), "γ.4.7 missing Petrine-confession + Passion-prediction + Transfiguration (Mark 8-9)"
        assert has_cyril_in(10, 10), "γ.4.7 missing Discipleship Discourse (Mark 10)"
        assert has_cyril_in(11, 12), "γ.4.7 missing Jerusalem Entry + Temple (Mark 11-12)"
        assert has_cyril_in(13, 13), "γ.4.7 missing Olivet eschatology (Mark 13)"
        assert has_cyril_in(14, 15), "γ.4.7 missing Passion narrative (Mark 14-15)"
        assert has_cyril_in(16, 16), "γ.4.7 missing Resurrection (Mark 16)"

    def test_all_sixteen_markan_chapters_covered(self):
        # Stronger than block-coverage: every single Markan chapter
        # must carry at least one Cyril entry after the γ.4.7 seed.
        missing = []
        for chapter in range(1, 17):
            found = False
            for verse in range(1, 100):
                for entry in self.ec.for_verse("mrk", chapter, verse):
                    if entry.father == "Cyril of Alexandria":
                        found = True
                        break
                if found:
                    break
            if not found:
                missing.append(chapter)
        assert not missing, f"γ.4.7 expected every Markan chapter 1-16 covered by seed; missing chapters: {missing}"

    def test_cyril_milestone_count_at_or_above_mark_seed(self):
        # γ.4.1.A-D shipped 116 Cyril-on-John + γ.4.3.A-D shipped 160
        # Cyril-on-Luke + γ.4.6.A-D shipped 195 Cyril-on-Matthew + γ.4
        # seed 5 misc (2 gen, 2 ps, etc.) = 476 (rounded down for safety).
        # γ.4.7 adds 40 Cyril-on-Mark = 516. Floor at ≥510 conservative
        # post-γ.4.7 milestone. Absolute count per
        # feedback_share_pin_pattern; invariant under future voice-
        # broadening waves.
        cyril_count = sum(
            1
            for verse_entries in self.ec._by_verse.values()
            for entry in verse_entries
            if entry.father == "Cyril of Alexandria"
        )
        assert cyril_count >= 510, (
            f"γ.4.7 expected Cyril count ≥510 (Mark-seed milestone, "
            f"cumulative across all 4 Gospels); found {cyril_count}"
        )

    # ---- Signature passage pins (14 anchors for Coptic-Tewahedo distinctives) ----

    def test_trinitarian_baptism_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 1, 10) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.7 missing Mark 1:10 — Trinitarian-baptism Jordan-theophany (Tewahedo Tǝmqät anchor)"

    def test_kingdom_near_metanoia_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 1, 15) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.7 missing Mark 1:15 — kingdom-near metanoia-pisteue (kerygmatic Markan incipit)"

    def test_obedient_family_marian_double_kinship_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 3, 35) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.7 missing Mark 3:35 — doing-God's-will family (Marian-double-kinship anchor)"

    def test_mustard_seed_frumentius_fulfillment_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 4, 31) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.7 missing Mark 4:31 — mustard-seed kingdom-growth (Frumentius-founding fulfillment-pattern)"

    def test_two_by_two_sending_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 6, 7) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7 missing Mark 6:7 — two-by-two sending (Frumentius-Edesius + Nine-Saints Tewahedo missionary-pattern)"
        )

    def test_syrophoenician_cushite_gentile_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 7, 28) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7 missing Mark 7:28 — Syrophoenician crumbs "
            "(Cushite-Gentile-inclusion Tewahedo Aksumite-origin anchor)"
        )

    def test_petrine_confession_markan_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 8, 29) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7 missing Mark 8:29 — Petrine confession sy-ei-ho-Christos (terse-Markan discipleship-confession)"
        )

    def test_help_mine_unbelief_proto_catechumen_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 9, 24) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.7 missing Mark 9:24 — 'Lord, I believe; help thou mine unbelief' (proto-catechumen-prayer)"

    def test_ransom_for_many_atonement_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 10, 45) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7 missing Mark 10:45 — ransom-for-many (atonement-summit; Tewahedo Anaphora cites at institution)"
        )

    def test_house_of_prayer_all_nations_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 11, 17) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7 missing Mark 11:17 — house of prayer for all nations "
            "(Markan-distinctive; Coptic-Tewahedo Gentile-mission fulfillment)"
        )

    def test_neither_the_son_communicatio_idiomatum_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 13, 32) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7 missing Mark 13:32 — 'neither the Son' (communicatio-idiomatum Cyrillian Miaphysite-Christology)"
        )

    def test_abba_father_two_wills_miaphysite_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 14, 36) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7 missing Mark 14:36 — Abba Father two-wills "
            "(Miaphysite Gethsemane; baptismal-adoption Rom 8:15 anchor)"
        )

    def test_markan_centurion_inclusio_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 15, 39) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7 missing Mark 15:39 — Markan centurion confession "
            "(structural-inclusio with Mk 1:1; Gentile-inclusion-at-Cross)"
        )

    def test_he_is_risen_fasika_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 16, 6) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7 missing Mark 16:6 — 'He is risen; he is not here' "
            "(Fasika dawn-Eucharist proclamation; Markan-priority lectionary anchor)"
        )

    def test_meta_documents_gamma_4_7_expansion(self):
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_source = data["_meta"]["source"]
        assert "γ.4.7" in meta_source, "γ.4.7 must be referenced in _meta.source"
        assert "Cyril on Mark" in meta_source or "Cyril-on-Mark" in meta_source or "seed wave" in meta_source, (
            "γ.4.7 _meta.source should describe the Cyril-on-Mark seed wave"
        )
        assert "Cramer" in meta_source, "γ.4.7 _meta.source should cite Cramer-Catenae source"


class TestGamma47BCyrilMarkGalileanWave:
    """γ.4.7.B — Cyril of Alexandria on Mark detail wave I:
    Galilean ministry first half (Mark 1-5). 51 verse-keyed entries
    deepening the 13 thin γ.4.7 seed anchors on Mark 1-5 to 64-entry
    detail-wave coverage. Mirrors γ.4.6.B Sermon-on-Mount detail-
    wave shape (50 entries on Matt 5-7 deepening 6 γ.4.6 anchors to
    56-entry coverage).

    Per ω.41 §1 "Patristic-source voice composition" rule
    (CLAUDE_PROJECT_RULES, codified at AUDIT_2026-05-13-EOD EOD-W3):
    this wave pushes Cyril past the 50% single-father-majority
    threshold (48.5% → ~50.8%). Cyril-led-patristic-chorus character
    is intentional per the apostolic-succession rationale (Cyril =
    24th Patriarch of See of Mark; standing in apostolic succession
    to John Mark + Athanasius + Frumentius).

    Pins (detail-wave standard set — NOT arc-close; γ.4.7.D will be
    the closing wave with §8.1 arc-close pins applied):
    - Mark 1-5 substantively detailed (≥64 Cyril entries on Mark
      1-5 = 13 γ.4.7 seed + 51 γ.4.7.B detail).
    - Every chapter Mark 1-5 substantively covered with detail-wave
      density floor (≥10 per chapter; tighter than seed-wave
      ≥2-per-chapter).
    - Cyril-on-Mark absolute-count milestone ≥90 entries (40 seed
      + 51 detail = 91 actual; ≥90 floor per
      `feedback_share_pin_pattern`).
    - Cumulative-Cyril milestone ≥555 entries (471 prior arcs + 91
      Cyril-on-Mark + ~2 incidental seed = 564 actual; ≥555 floor).
    - Signature anchors (12): 1:8 baptism-with-Spirit + 1:11 Father's-
      voice + 1:13 Edenic-restoration-with-beasts + 1:41 splanchnistheis-
      leper + 2:28 Son-of-Man Lord-of-Sabbath + 3:27 binding-strong-
      man + 4:14 sower-soweth-the-word + 4:39 peace-be-still + 5:9
      'My name is Legion' + 5:19 first-Gentile-evangelist + 5:36
      'fear not, only believe' + 5:41 Talitha-cumi.
    - _meta.source sync pin: γ.4.7.B + Mark 1-5 + Galilean ministry
      first half.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def _cyril_in_chapter(self, chapter):
        out = []
        for verse in range(1, 100):
            out.extend(e for e in self.ec.for_verse("mrk", chapter, verse) if e.father == "Cyril of Alexandria")
        return out

    def _cyril_in_range(self, ch_start, ch_end):
        return sum(len(self._cyril_in_chapter(c)) for c in range(ch_start, ch_end + 1))

    def test_mark_1_5_substantively_detailed(self):
        total = self._cyril_in_range(1, 5)
        assert total >= 64, f"γ.4.7.B expected ≥64 Cyril entries on Mark 1-5 (13 seed + 51 detail); found {total}"

    def test_every_galilean_chapter_has_detail_depth(self):
        # Detail-wave parity floor: each of Mark 1-5 should have ≥10
        # Cyril entries post-γ.4.7.B (vs seed-wave ≥2-per-chapter floor).
        per_chapter = {ch: len(self._cyril_in_chapter(ch)) for ch in range(1, 6)}
        below_floor = {ch: n for ch, n in per_chapter.items() if n < 10}
        assert not below_floor, (
            f"γ.4.7.B detail-wave: each Mark 1-5 chapter should have ≥10 "
            f"Cyril entries; below-floor chapters: {below_floor}"
        )

    def test_cyril_on_mark_milestone_count_at_or_above_galilean_detail(self):
        cyril_mrk = 0
        for chapter in range(1, 17):
            for verse in range(1, 100):
                for entry in self.ec.for_verse("mrk", chapter, verse):
                    if entry.father == "Cyril of Alexandria":
                        cyril_mrk += 1
        assert cyril_mrk >= 90, (
            f"γ.4.7.B expected ≥90 Cyril-on-Mark entries (40 seed + 51 detail = 91); found {cyril_mrk}"
        )

    def test_cumulative_cyril_milestone_at_or_above_galilean_detail(self):
        # Cumulative across all books. γ.4.7 seed milestone was ≥510;
        # γ.4.7.B adds 51 entries → 562 actual; ≥555 floor.
        cyril_count = sum(
            1
            for verse_entries in self.ec._by_verse.values()
            for entry in verse_entries
            if entry.father == "Cyril of Alexandria"
        )
        assert cyril_count >= 555, (
            f"γ.4.7.B expected Cyril cumulative ≥555 (post-γ.4.7.B milestone); found {cyril_count}"
        )

    # ---- Signature passage pins (12 anchors) ----

    def test_baptism_with_spirit_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 1, 8) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.B missing Mark 1:8 — baptism-with-Holy-Spirit (Tewahedo Tǝmqät dual-element water-and-Spirit anchor)"
        )

    def test_fathers_voice_beloved_son_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 1, 11) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.B missing Mark 1:11 — Father's-voice 'Thou art my beloved Son' "
            "(Ps 2:7 + Isa 42:1 royal-anointing + Servant-vocation conflation)"
        )

    def test_edenic_restoration_wild_beasts_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 1, 13) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.B missing Mark 1:13 — 'with the wild beasts' "
            "(Markan-distinctive Edenic-restoration sign; Tewahedo Hudadē-Lent anchor)"
        )

    def test_splanchnistheis_leper_compassion_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 1, 41) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.B missing Mark 1:41 — splanchnistheis (moved-with-compassion) "
            "leper-healing (deepest Markan compassion-verb)"
        )

    def test_son_of_man_lord_of_sabbath_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 2, 28) if e.father == "Cyril of Alexandria"]
        assert c, "γ.4.7.B missing Mark 2:28 — Son of Man Lord of Sabbath (Sabbath-Christology summit)"

    def test_binding_strong_man_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 3, 27) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.B missing Mark 3:27 — binding-the-strong-man (apostolic-authority over demons; Heb 2:14 anchor)"
        )

    def test_sower_soweth_the_word_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 4, 14) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.B missing Mark 4:14 — sower-soweth-the-word "
            "(seed-as-Logos hermeneutic; Tewahedo monastic-lectio-divina anchor)"
        )

    def test_peace_be_still_storm_rebuke_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 4, 39) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.B missing Mark 4:39 — 'Peace, be still' storm-rebuke "
            "(divine-prerogative speech to elements; Tewahedo natural-disaster-prayer anchor)"
        )

    def test_my_name_is_legion_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 5, 9) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.B missing Mark 5:9 — 'My name is Legion, for we are many' (multi-demon-possession self-disclosure)"
        )

    def test_first_gentile_evangelist_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 5, 19) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.B missing Mark 5:19 — 'go home and tell' "
            "(formerly-possessed becomes first Gentile evangelist in Decapolis; "
            "Tewahedo Aksumite-origin proto-missionary anchor)"
        )

    def test_fear_not_only_believe_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 5, 36) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.B missing Mark 5:36 — 'Fear not, only believe' "
            "(faith-against-death-itself charge; Tewahedo deathbed-pastoral anchor)"
        )

    def test_talitha_cumi_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 5, 41) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.B missing Mark 5:41 — Talitha cumi (preserved-Aramaic) "
            "(Christic-power-over-death; Tewahedo Fasika resurrection-anticipation anchor)"
        )

    def test_meta_documents_gamma_4_7_b_expansion(self):
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_source = data["_meta"]["source"]
        assert "γ.4.7.B" in meta_source, "γ.4.7.B must be referenced in _meta.source"
        assert "Mark 1-5" in meta_source or "Galilean ministry first half" in meta_source, (
            "γ.4.7.B _meta.source should describe the Mark 1-5 Galilean-first-half scope"
        )


class TestGamma47CCyrilMarkCaesareaTransfigurationWave:
    """γ.4.7.C — Cyril of Alexandria on Mark detail wave II:
    Galilean ministry second half + Caesarea Philippi + Transfiguration
    + journey-to-Jerusalem (Mark 6-10). 50 verse-keyed entries
    deepening the 14 γ.4.7 seed anchors on Mark 6-10 to 64-entry
    detail-wave coverage. Mirrors γ.4.7.B Mark 1-5 detail-wave shape.

    Per ω.41 §1 voice-composition rule: post-γ.4.7.C Cyril share
    rises 50.8% → ~52.5%; Cyril-led-patristic-chorus character
    continues per the apostolic-succession rationale.

    Pins (detail-wave standard set — NOT arc-close; γ.4.7.D will
    close the arc):
    - Mark 6-10 substantively detailed (≥64 Cyril entries = 14
      γ.4.7 seed + 50 γ.4.7.C detail).
    - Every chapter Mark 6-10 detail-density ≥10 entries.
    - Cyril-on-Mark absolute-count milestone ≥140 (40 seed + 51
      γ.4.7.B + 50 γ.4.7.C = 141 actual; ≥140 floor).
    - Cumulative-Cyril milestone ≥610 (562 prior + 50 γ.4.7.C +
      ~2 incidental seed = 614 actual; ≥610 floor).
    - Signature anchors (12): 6:50 walking-on-sea egō-eimi parallel
      + 7:34 Ephphatha preserved-Aramaic baptismal-rite + 8:25
      Bethsaida-blind second-stage completion + 8:36 'gain world,
      lose soul' moral-summit + 9:2 Transfiguration mountain-
      selection + 9:5 Peter's-three-tabernacles + 9:23 'if-thou-
      canst-believe' faith-prerequisite + 9:29 prayer-and-fasting
      deliverance + 10:14 'suffer-little-children' infant-baptism +
      10:18 'why-callest-thou-me-good' hidden-Christology + 10:21
      'one-thing-thou-lackest' Christic-love counsel-of-perfection
      + 10:27 'with-God-all-things-possible' grace-monergism.
    - _meta.source sync pin: γ.4.7.C + Mark 6-10 + Galilean-second-
      half OR Caesarea-Transfiguration scope.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def _cyril_in_chapter(self, chapter):
        out = []
        for verse in range(1, 100):
            out.extend(e for e in self.ec.for_verse("mrk", chapter, verse) if e.father == "Cyril of Alexandria")
        return out

    def _cyril_in_range(self, ch_start, ch_end):
        return sum(len(self._cyril_in_chapter(c)) for c in range(ch_start, ch_end + 1))

    def test_mark_6_10_substantively_detailed(self):
        total = self._cyril_in_range(6, 10)
        assert total >= 64, f"γ.4.7.C expected ≥64 Cyril entries on Mark 6-10 (14 seed + 50 detail); found {total}"

    def test_every_caesarea_chapter_has_detail_depth(self):
        per_chapter = {ch: len(self._cyril_in_chapter(ch)) for ch in range(6, 11)}
        below_floor = {ch: n for ch, n in per_chapter.items() if n < 10}
        assert not below_floor, (
            f"γ.4.7.C detail-wave: each Mark 6-10 chapter should have ≥10 "
            f"Cyril entries; below-floor chapters: {below_floor}"
        )

    def test_cyril_on_mark_milestone_count_at_or_above_caesarea_detail(self):
        cyril_mrk = 0
        for chapter in range(1, 17):
            for verse in range(1, 100):
                for entry in self.ec.for_verse("mrk", chapter, verse):
                    if entry.father == "Cyril of Alexandria":
                        cyril_mrk += 1
        assert cyril_mrk >= 140, (
            f"γ.4.7.C expected ≥140 Cyril-on-Mark entries (40 seed + 51 γ.4.7.B + 50 γ.4.7.C = 141); found {cyril_mrk}"
        )

    def test_cumulative_cyril_milestone_at_or_above_caesarea_detail(self):
        cyril_count = sum(
            1
            for verse_entries in self.ec._by_verse.values()
            for entry in verse_entries
            if entry.father == "Cyril of Alexandria"
        )
        assert cyril_count >= 610, (
            f"γ.4.7.C expected Cyril cumulative ≥610 (post-γ.4.7.C milestone); found {cyril_count}"
        )

    # ---- Signature passage pins (12 anchors) ----

    def test_walking_on_sea_ego_eimi_markan_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 6, 50) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.C missing Mark 6:50 — 'It is I; be not afraid' egō-eimi "
            "(parallels Mt 14:27 + Jn 6:20; Septuagintal Ex 3:14 I-AM claim)"
        )

    def test_ephphatha_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 7, 34) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.C missing Mark 7:34 — Ephphatha (preserved-Aramaic) "
            "(Tewahedo baptismal-rite gesture explicitly preserves this Coptic-Markan-Aramaic)"
        )

    def test_bethsaida_second_stage_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 8, 25) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.C missing Mark 8:25 — Bethsaida-blind second-stage completion "
            "(two-stage spiritual-sight pedagogy; precedes Peter's partial-confession)"
        )

    def test_gain_world_lose_soul_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 8, 36) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.C missing Mark 8:36 — 'what shall it profit to gain world and lose soul' "
            "(universal-moral-summit; Tewahedo wealth-ethics triple-anchor)"
        )

    def test_transfiguration_mountain_markan_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 9, 2) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.C missing Mark 9:2 — Transfiguration high-mountain six-days-typology "
            "(Tewahedo Buhe feast Näḥase 13 anchor; parallel to Mt 17:1 γ.4.6.D)"
        )

    def test_peter_three_tabernacles_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 9, 5) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.C missing Mark 9:5 — Peter's three-tabernacles eschatological-anticipation-error "
            "(Cross must precede tabernacle-building)"
        )

    def test_if_thou_canst_believe_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 9, 23) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.C missing Mark 9:23 — 'if thou canst believe, all things possible' "
            "(faith-as-divine-power-channel; Christic reverse-of-conditional)"
        )

    def test_prayer_and_fasting_deliverance_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 9, 29) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.C missing Mark 9:29 — 'this kind by prayer and fasting' "
            "(Markan-distinctive deliverance-charter; Tewahedo Mahǝbär-fast tradition anchor)"
        )

    def test_suffer_little_children_infant_baptism_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 10, 14) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.C missing Mark 10:14 — 'suffer little children to come unto me' "
            "(Tewahedo infant-baptism Coptic-tradition warrant)"
        )

    def test_why_callest_thou_me_good_hidden_christology_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 10, 18) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.C missing Mark 10:18 — 'why callest thou me good' "
            "(hidden-Christological-divinity claim under apparent humility)"
        )

    def test_one_thing_thou_lackest_christic_love_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 10, 21) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.C missing Mark 10:21 — 'beholding-him-loved-him; one thing thou lackest' "
            "(only Gospel-passage where Christ loves an individual; Tewahedo monastic-vocation "
            "love-prompting-of-the-calling anchor)"
        )

    def test_with_god_all_things_possible_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 10, 27) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.C missing Mark 10:27 — 'with God all things possible' "
            "(grace-monergism; Tewahedo soteriology of grace anchor)"
        )

    def test_meta_documents_gamma_4_7_c_expansion(self):
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_source = data["_meta"]["source"]
        assert "γ.4.7.C" in meta_source, "γ.4.7.C must be referenced in _meta.source"
        assert (
            "Mark 6-10" in meta_source
            or "Galilean ministry second half" in meta_source
            or "Caesarea Philippi" in meta_source
            or "Transfiguration" in meta_source
        ), "γ.4.7.C _meta.source should describe the Mark 6-10 Galilean-second-half / Caesarea-Transfiguration scope"


class TestGamma47DCyrilMarkArcClose:
    """γ.4.7.D — Cyril of Alexandria on Mark ARC-CLOSE wave (Mark
    11-16: Jerusalem entry + temple cleansing + Olivet eschatology
    + Passion narrative + Resurrection + Great Commission). CLOSING
    WAVE of the four-wave Cyril-on-Mark arc per §8.1 arc-close
    convention. 51 verse-keyed entries distributed across all 6
    chapters Mark 11-16. CLOSES the FOURTH and FINAL canonical-
    Gospel Cyrillian arc:

        Cyril-on-John     γ.4.1-D   116 entries (closed earlier)
        Cyril-on-Luke     γ.4.3-D   160 entries (closed 2026-05-13)
        Cyril-on-Matthew  γ.4.6-D   195 entries (closed 2026-05-13)
        Cyril-on-Mark     γ.4.7-D   192 entries (closed by γ.4.7.D)
                                    (40 seed + 51 γ.4.7.B + 50 γ.4.7.C
                                     + 51 γ.4.7.D)
        Cumulative Cyril-on-Gospels: 663 entries across all 4
                                      canonical Gospels at closed-
                                      arc substantive-detail depth.

    SIXTH instance of §8.1 arc-close convention (after γ.4.4.E
    Mäṣḥafä Hēnok, γ.4.5.E Mäṣḥafä Kufāle, γ.4.2.D Pentateuch,
    γ.4.3.D Cyril-on-Luke, γ.4.6.D Cyril-on-Matthew).

    Per §8.1 the closing wave's test class MUST add the three
    specific pin types:
    (1) _meta synchronization pin per sub-phase tag with regex
        word-boundary matching;
    (2) absolute-count milestone pin at cumulative arc-close count;
    (3) all_N_sections_covered exhaustiveness pin asserting every
        section the arc was supposed to cover has substantive
        coverage at planned depth.

    Pins:
    - Mark 11-16 substantively detailed (≥63 total Cyril entries
      on Mark 11-16 = 13 seed + 50 arc-close detail).
    - Every chapter Mark 11-16 carries ≥5 Cyril entries (parity
      floor preserved at arc-close).
    - **§8.1 ARC-CLOSE PIN #1 — count milestone:** Cyril-on-Mark
      absolute-count ≥190 entries (per `feedback_share_pin_pattern`
      — never a share-pin; durable against future voice-broadening).
    - **§8.1 ARC-CLOSE PIN #2 — all_N_sections_covered
      exhaustiveness:**
      test_all_four_cyril_mark_waves_substantively_covered asserts
      γ.4.7 seed (≥40) + γ.4.7.B Mark 1-5 (≥64) + γ.4.7.C Mark
      6-10 (≥64) + γ.4.7.D Mark 11-16 (≥63) — every section the
      Cyril-on-Mark arc was supposed to cover has substantive
      coverage at planned depth.
    - **§8.1 ARC-CLOSE PIN #3 — _meta synchronization:** pin per
      sub-phase tag (γ.4.7, γ.4.7.B, γ.4.7.C, γ.4.7.D) with regex
      word-boundary; arc-close status recorded explicitly.
    - 14 signature-passage pins for arc-close Tewahedo anchors:
      11:10 Davidic-kingdom-cometh + 11:25 forgive-when-praying +
      12:17 render-to-Caesar-and-to-God + 12:29 Shema Lord-our-God-
      is-one + 12:30 fourfold-love-of-God + 13:26 Son-of-Man-coming-
      in-clouds Parousia + 13:31 heaven-and-earth-pass-words-not-
      pass + 14:24 blood-of-covenant-shed-for-many Anaphora + 14:25
      not-drink-fruit-of-vine-until-kingdom eschatological-banquet +
      14:51 young-man-fled-naked Markan-John-Mark-tradition + 14:62
      'I am: Son-of-Man-on-right-hand-of-power' triple-Christological-
      claim + 15:21 Simon-of-Cyrene Tewahedo-Aksumite-African-cross-
      bearer + 15:38 veil-rent schizō bookend-to-Mk-1:10 + 16:7
      'tell his disciples AND PETER' Petrine-restoration + 16:15
      Markan-Great-Commission preach-to-every-creature.

    With this class, ALL FOUR canonical-Gospel Cyrillian arcs are
    pinned at closed-arc depth (John γ.4.1-D + Luke γ.4.3-D +
    Matthew γ.4.6-D + Mark γ.4.7-D).
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def _cyril_in_chapter(self, chapter):
        out = []
        for verse in range(1, 100):
            out.extend(e for e in self.ec.for_verse("mrk", chapter, verse) if e.father == "Cyril of Alexandria")
        return out

    def _cyril_in_range(self, ch_start, ch_end):
        return sum(len(self._cyril_in_chapter(c)) for c in range(ch_start, ch_end + 1))

    def test_mark_11_16_substantively_detailed(self):
        total = self._cyril_in_range(11, 16)
        assert total >= 63, (
            f"γ.4.7.D expected ≥63 Cyril entries on Mark 11-16 (13 seed + 50 arc-close detail); found {total}"
        )

    def test_every_arc_close_chapter_has_minimum_coverage(self):
        # Parity floor: every chapter Mark 11-16 should carry ≥5
        # Cyril entries after γ.4.7.D arc-close.
        per_chapter = {ch: len(self._cyril_in_chapter(ch)) for ch in range(11, 17)}
        below_floor = {ch: n for ch, n in per_chapter.items() if n < 5}
        assert not below_floor, (
            f"γ.4.7.D arc-close: every Mark 11-16 chapter should have ≥5 "
            f"Cyril entries; below-floor chapters: {below_floor}"
        )

    def test_cyril_on_mark_arc_close_count_milestone(self):
        # §8.1 ARC-CLOSE PIN #2: absolute-count milestone at arc close.
        # Per feedback_share_pin_pattern: never a share pin.
        # Cumulative: 40 (γ.4.7 seed) + 51 (γ.4.7.B) + 50 (γ.4.7.C)
        # + 51 (γ.4.7.D) = 192. ≥190 floor.
        cyril_mrk = 0
        for chapter in range(1, 17):
            for verse in range(1, 100):
                for entry in self.ec.for_verse("mrk", chapter, verse):
                    if entry.father == "Cyril of Alexandria":
                        cyril_mrk += 1
        assert cyril_mrk >= 190, (
            f"γ.4.7.D arc-close: Cyril-on-Mark count ≥190 expected "
            f"(cumulative four-wave arc-close milestone: 40 seed + 51 "
            f"γ.4.7.B + 50 γ.4.7.C + 51 γ.4.7.D = 192); found {cyril_mrk}"
        )

    def test_all_four_cyril_mark_waves_substantively_covered(self):
        # §8.1 ARC-CLOSE PIN #3: all_N_sections_covered exhaustiveness.
        # Every section of the Cyril-on-Mark arc must have substantive
        # coverage at planned depth. The four waves are:
        # γ.4.7    seed         (40 entries across all 16 chapters)
        # γ.4.7.B  Mark 1-5     (≥64 cumulative)
        # γ.4.7.C  Mark 6-10    (≥64 cumulative)
        # γ.4.7.D  Mark 11-16   (≥63 cumulative)
        # This pin prevents a future "I'll ship Mark 11-16 later" from
        # silently leaving the arc partially closed.
        total_cyril_mrk = self._cyril_in_range(1, 16)
        mrk_1_5 = self._cyril_in_range(1, 5)
        mrk_6_10 = self._cyril_in_range(6, 10)
        mrk_11_16 = self._cyril_in_range(11, 16)

        assert total_cyril_mrk >= 190, (
            f"γ.4.7.D arc-close: total Cyril-on-Mark ≥190 expected (four waves); found {total_cyril_mrk}"
        )
        assert mrk_1_5 >= 64, f"γ.4.7.D arc-close: Mark 1-5 below γ.4.7.B parity (need ≥64, have {mrk_1_5})"
        assert mrk_6_10 >= 64, f"γ.4.7.D arc-close: Mark 6-10 below γ.4.7.C parity (need ≥64, have {mrk_6_10})"
        assert mrk_11_16 >= 63, f"γ.4.7.D arc-close: Mark 11-16 below γ.4.7.D parity (need ≥63, have {mrk_11_16})"

    def test_meta_synchronization_at_arc_close(self):
        # §8.1 ARC-CLOSE PIN #1: _meta synchronization. Pin per
        # sub-phase tag with regex word-boundary so γ.4.7 doesn't
        # accidentally match γ.4.7.B/C/D.
        import json
        import re
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_source = data["_meta"]["source"]
        assert re.search(r"γ\.4\.7(?![.A-Z])", meta_source), "γ.4.7 seed wave must be in _meta.source"
        assert re.search(r"γ\.4\.7\.B(?![A-Z])", meta_source), "γ.4.7.B Mark 1-5 detail wave must be in _meta.source"
        assert re.search(r"γ\.4\.7\.C(?![A-Z])", meta_source), "γ.4.7.C Mark 6-10 detail wave must be in _meta.source"
        assert re.search(r"γ\.4\.7\.D(?![A-Z])", meta_source), "γ.4.7.D arc-close wave must be in _meta.source"
        # arc-close must describe Mark 11-16 scope explicitly
        assert (
            "Mark 11-16" in meta_source
            or "Passion narrative" in meta_source
            or "Resurrection + Great Commission" in meta_source
        ), "γ.4.7.D _meta.source should describe the Mark 11-16 (Passion + Resurrection + Great Commission) scope"
        # arc-close must record arc-close status explicitly
        assert (
            "Cyril-on-Mark arc is CLOSED" in meta_source
            or "CLOSING WAVE of the four-wave Cyril-on-Mark arc" in meta_source
        ), "γ.4.7.D _meta.source should record the arc-close explicitly"

    # ---- Signature passage pins (14 anchors for Tewahedo distinctives) ----

    def test_davidic_kingdom_cometh_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 11, 10) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.D missing Mark 11:10 — 'blessed is the kingdom of our father David that cometh' "
            "(Markan-distinctive Davidic-messianic anticipation; Tewahedo Solomonic-Davidic anchor)"
        )

    def test_forgive_when_praying_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 11, 25) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.D missing Mark 11:25 — 'when ye stand praying, forgive' "
            "(prayer-condition; Tewahedo sacramental-confession + Pax anchor)"
        )

    def test_render_to_caesar_markan_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 12, 17) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.D missing Mark 12:17 — 'render to Caesar and to God' "
            "(dual-jurisdiction; Tewahedo Solomonic-political-theology anchor)"
        )

    def test_shema_lord_our_god_is_one_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 12, 29) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.D missing Mark 12:29 — 'Hear O Israel, the Lord our God is one' "
            "(Shema; Tewahedo Trinitarian-monotheism unity anchor)"
        )

    def test_fourfold_love_of_god_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 12, 30) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.D missing Mark 12:30 — fourfold love-of-God heart+soul+mind+strength "
            "(Markan-distinctive; comprehensive-anthropological formation anchor)"
        )

    def test_son_of_man_coming_in_clouds_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 13, 26) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.D missing Mark 13:26 — Son-of-Man coming in clouds great power and glory "
            "(Dan 7:13 Parousia-fulfillment; Tewahedo Mäshafä-Bǝrhän eschatological anchor)"
        )

    def test_heaven_earth_pass_words_not_pass_markan_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 13, 31) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.D missing Mark 13:31 — 'heaven and earth shall pass; my words shall not' "
            "(Christological-Logology summit; Tewahedo Word-eternity anchor)"
        )

    def test_blood_of_covenant_markan_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 14, 24) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.D missing Mark 14:24 — blood-of-covenant shed-for-many "
            "(Markan-Anaphora institution-form; Ex 24:8 + Isa 53:11-12 echo)"
        )

    def test_not_drink_fruit_of_vine_until_kingdom_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 14, 25) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.D missing Mark 14:25 — 'not drink henceforth fruit of vine until kingdom' "
            "(eschatological-banquet anticipation; Marriage-Supper-of-the-Lamb anchor)"
        )

    def test_young_man_fled_naked_markan_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 14, 51) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.D missing Mark 14:51 — young-man-fled-naked "
            "(Markan-distinctive; Coptic-Tewahedo John-Mark-eyewitness-tradition anchor; "
            "the evangelist-author's signature presence in the Gospel)"
        )

    def test_caiaphas_trial_son_of_man_right_hand_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 14, 62) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.D missing Mark 14:62 — 'I am: Son-of-Man-on-right-hand-of-power' "
            "(TRIPLE-Christological-claim: divine-I-AM + Ps 110:1 + Dan 7:13; "
            "Tewahedo Trinitarian-Christological summit anchor)"
        )

    def test_simon_of_cyrene_aksumite_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 15, 21) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.D missing Mark 15:21 — Simon of Cyrene cross-bearer "
            "(FIRST African-figure to bear-the-Cross; Tewahedo Aksumite-African-Coptic "
            "proto-discipleship anchor)"
        )

    def test_veil_rent_schizo_bookend_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 15, 38) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.D missing Mark 15:38 — veil-rent top-to-bottom (schizō) "
            "(Markan-bookend with Mk 1:10 heaven-rent schizō; "
            "Heb 10:19-20 new-covenant-access; Tewahedo maqdas-Tabot-veil anchor)"
        )

    def test_tell_disciples_AND_PETER_markan_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 16, 7) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.D missing Mark 16:7 — 'tell his disciples AND PETER' "
            "(Markan-distinctive explicit Petrine-restoration mention; "
            "Mark = Peter's-translator preserves the personal restoration-touch)"
        )

    def test_markan_great_commission_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 16, 15) if e.father == "Cyril of Alexandria"]
        assert c, (
            "γ.4.7.D missing Mark 16:15 — 'go into all the world, preach the gospel to every creature' "
            "(Markan-Great-Commission preserved in Coptic-Tewahedo longer-ending; "
            "Tewahedo missionary-mandate Frumentius-mission warrant)"
        )


class TestGamma49AthanasiusSeedWave:
    """γ.4.9 — Athanasius of Alexandria seed wave (2026-05-13).
    OPENS A FIFTH PATRISTIC VOICE in the γ.4 corpus alongside the
    four-voice composition codified at ω.41 §1:

        Cyril of Alexandria   668 entries  54.7% → 53.1%
        Jubilees              200 entries  16.4% → 15.9%
        1 Enoch               192 entries  15.7% → 15.3%
        Ephrem the Syrian     157 entries  12.9% → 12.5%
        + Athanasius (γ.4.9)   40 entries   3.2%  ← THIS SHIP

    Patristic-anchor majority (Cyril + Ephrem + Athanasius) rises
    67.6% → 68.8%. Per ω.41 §1: the Cyril-led-patristic-chorus
    character is intentional per apostolic-succession rationale; the
    fifth-voice opening DEEPENS the patristic plurality without
    displacing the Cyril-led plurality.

    Athanasius is the Tewahedo apostolic-bridge:
    - 20th Patriarch of the See of Mark (328-373 AD)
    - Consecrator (c. 330 AD) of Frumentius the Tewahedo founder
    - Author of Festal Letter 39 (367 AD) establishing the 27-book
      NT canon the Tewahedo Church receives in its canonical form

    The seed pairs structurally with the γ.4.7-D Cyril-on-Mark
    arc-close: both are See-of-Mark patriarchal-succession
    Christology. γ.4.9 extends the apostolic-lineage hermeneutical
    reading BACKWARDS from Cyril (24th Patriarch) to Athanasius
    (20th Patriarch).

    Sources (all fully PD): Select Writings and Letters of Athanasius,
    NPNF Series 2 Vol. 4 (ed. Robertson, Oxford/T&T Clark 1892) —
    contains De Incarnatione + Contra Arianos I-IV + De Decretis +
    Festal Letters (incl. Letter 39) + Epistola ad Epictetum + Letter
    to Adelphius. Greek text in Migne PG 25-28 (1857-1887, PD).

    Distribution (40 entries across 19 books — THEMATIC-MULTI-BOOK
    pattern, NOT single-book like prior γ.4.6/γ.4.7 Cyril-on-Gospel
    arcs; Athanasius's works are doctrinal-treatises commenting on
    christological-anchor verses across the canon):
    - OT Christological Anticipations (8 entries across 5 books):
      gen × 2 + exo × 1 + psa × 2 + pro × 1 + isa × 2
    - Canonical Gospel Christology (8 entries across 2 books):
      mat × 3 + jhn × 5
    - Pauline Christology (16 entries across 8 books):
      rom × 3 + 1co × 2 + 2co × 1 + gal × 1 + eph × 1 + phi × 3 +
      col × 3 + heb × 2
    - Petrine + Johannine + Apocalyptic (8 entries across 4 books):
      1pe × 2 + 2pe × 1 + 1jn × 2 + rev × 3

    Pins (seed-wave standard set — NOT arc-close; γ.4.9.B/C/D may
    follow as detail waves per γ.4.1/γ.4.3/γ.4.6/γ.4.7 precedent):
    - Athanasius substantively seeded (≥40 entries across all books).
    - All four thematic groups substantively covered (≥1 Athanasius
      entry in each: OT + Gospels + Pauline + Petrine/Johannine/Apoc).
    - Multi-book coverage ≥18 (19 actual — thematic-spread invariant).
    - Athanasius absolute-count milestone ≥40 (40 actual; floor per
      `feedback_share_pin_pattern.md` — never share-pin).
    - Signature passages — 13 christological/theosis/Trinitarian
      anchors covering the Athanasian-Tewahedo doctrinal architecture.
    - _meta.source sync pin: γ.4.9 referenced + Athanasius signature
      + NPNF S2 V4 source cited.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def _all_athanasius(self):
        out = []
        for verse_entries in self.ec._by_verse.values():
            out.extend(e for e in verse_entries if e.father == "Athanasius of Alexandria")
        return out

    def _athanasius_in_book(self, book):
        out = []
        for chapter in range(1, 200):
            for verse in range(1, 200):
                out.extend(e for e in self.ec.for_verse(book, chapter, verse) if e.father == "Athanasius of Alexandria")
        return out

    def test_athanasius_substantively_seeded(self):
        ath = self._all_athanasius()
        assert len(ath) >= 40, f"γ.4.9 expected ≥40 Athanasius entries across the canon; found {len(ath)}"

    def test_athanasius_milestone_count(self):
        # Absolute-count milestone per `feedback_share_pin_pattern.md`:
        # use count, NEVER share. γ.4.9 seed ships exactly 40 entries;
        # the ≥40 floor preserves the historical-achievement against
        # any future voice-broadening wave (subsequent fathers or
        # γ.4.9.B/C/D detail-wave expansion may dilute Athanasius's
        # share without violating this milestone).
        ath = self._all_athanasius()
        assert len(ath) >= 40, f"γ.4.9 Athanasius count milestone ≥40 not met; found {len(ath)}"

    def test_athanasius_thematic_groups_all_substantively_covered(self):
        # All four thematic groups must carry ≥1 Athanasius entry.
        # Multi-book pattern: γ.4.9 IS the seed-wave per group; future
        # detail waves (γ.4.9.B/C/D) would deepen the count per group.
        ot_books = {"gen", "exo", "psa", "pro", "isa"}
        gospel_books = {"mat", "jhn"}
        pauline_books = {"rom", "1co", "2co", "gal", "eph", "phi", "col", "heb"}
        petrine_johannine_apoc_books = {"1pe", "2pe", "1jn", "rev"}

        ath = self._all_athanasius()

        def _book_hit(book_set):
            return any(e.book in book_set for e in ath)

        assert _book_hit(ot_books), "γ.4.9 missing OT Christological Anticipations group (gen/exo/psa/pro/isa)"
        assert _book_hit(gospel_books), "γ.4.9 missing Canonical Gospel Christology group (mat/jhn)"
        assert _book_hit(pauline_books), "γ.4.9 missing Pauline Christology group (rom/1co/2co/gal/eph/phi/col/heb)"
        assert _book_hit(petrine_johannine_apoc_books), (
            "γ.4.9 missing Petrine + Johannine + Apocalyptic group (1pe/2pe/1jn/rev)"
        )

    def test_athanasius_multi_book_coverage(self):
        # Thematic-spread invariant: Athanasius's doctrinal treatises
        # comment across the canon. The seed must span ≥18 books
        # (19 actual). Any reduction below this floor in a future
        # γ.4.9 maintenance ship would indicate the multi-book
        # signature has been compromised.
        ath = self._all_athanasius()
        books_touched = {e.book for e in ath}
        assert len(books_touched) >= 18, (
            f"γ.4.9 expected Athanasius entries across ≥18 books (multi-book seed); "
            f"found {len(books_touched)}: {sorted(books_touched)}"
        )

    # ---- Signature passage pins (13 anchors covering Athanasian-Tewahedo doctrinal architecture) ----

    def test_trinitarian_lets_make_man_anchor_present(self):
        c = [e for e in self.ec.for_verse("gen", 1, 26) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9 missing Gen 1:26 — Trinitarian 'let us make man in our image' "
            "(De Decretis §22 intra-Trinitarian-deliberation anchor)"
        )

    def test_i_am_burning_bush_anchor_present(self):
        c = [e for e in self.ec.for_verse("exo", 3, 14) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9 missing Ex 3:14 — egō eimi ho ōn (LXX I-AM the-Being-One; Burning-Bush divine-name Jn 8:58 anchor)"
        )

    def test_prov_8_22_arian_controversy_anchor_present(self):
        c = [e for e in self.ec.for_verse("pro", 8, 22) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9 missing Pr 8:22 — 'the LORD created me' "
            "(THE Arian-controversy prooftext; Contra Arianos II.18-82 refutation)"
        )

    def test_almah_parthenos_isa_7_14_anchor_present(self):
        c = [e for e in self.ec.for_verse("isa", 7, 14) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9 missing Isa 7:14 — almah/parthenos virgin-conception (De Incarnatione §33 Mt 1:23 prophetic anchor)"
        )

    def test_johannine_logos_in_beginning_anchor_present(self):
        c = [e for e in self.ec.for_verse("jhn", 1, 1) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9 missing Jn 1:1 — 'in the beginning was the Word' "
            "(De Incarnatione §1 Johannine prologue Logos-eternal-existence anchor)"
        )

    def test_word_made_flesh_athanasian_signature_anchor_present(self):
        c = [e for e in self.ec.for_verse("jhn", 1, 14) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9 missing Jn 1:14 — ho Logos sarx egeneto "
            "(THE Athanasian signature-verse; De Incarnatione §8; DI §54 'God-became-man "
            "that man might become God' is the soteriological corollary)"
        )

    def test_i_and_father_are_one_anchor_present(self):
        c = [e for e in self.ec.for_verse("jhn", 10, 30) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9 missing Jn 10:30 — egō kai ho patēr hen esmen (Contra Arianos III.1-25 homoousion neuter-hen anchor)"
        )

    def test_kenotic_emptied_himself_anchor_present(self):
        c = [e for e in self.ec.for_verse("phi", 2, 7) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9 missing Phil 2:7 — heauton ekenōsen "
            "(Contra Arianos I.41-45 kenosis-is-assumption-not-subtraction anchor)"
        )

    def test_image_of_invisible_god_anchor_present(self):
        c = [e for e in self.ec.for_verse("col", 1, 15) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9 missing Col 1:15 — eikōn tou theou tou aoratou "
            "(Contra Arianos II.62-64 perfect-image firstborn-over-creation anchor)"
        )

    def test_express_image_heb_1_3_anchor_present(self):
        c = [e for e in self.ec.for_verse("heb", 1, 3) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9 missing Heb 1:3 — apaugasma tēs doxēs + charaktēr tēs hypostaseōs "
            "(Contra Arianos I.13 light-from-fire perfect-image-of-Father anchor)"
        )

    def test_theosis_2_peter_1_4_anchor_present(self):
        c = [e for e in self.ec.for_verse("2pe", 1, 4) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9 missing 2 Pet 1:4 — theias koinōnoi physeōs "
            "(De Incarnatione §54 THEOSIS-summit; 'He was made man that we might be made God' anchor)"
        )

    def test_we_shall_be_like_him_anchor_present(self):
        c = [e for e in self.ec.for_verse("1jn", 3, 2) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9 missing 1 Jn 3:2 — homoioi autō esometha "
            "(De Incarnatione §54 eschatological theosis-fulfillment + beatific-vision anchor)"
        )

    def test_alpha_omega_apocalyptic_anchor_present(self):
        c = [e for e in self.ec.for_verse("rev", 1, 8) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9 missing Rev 1:8 — egō eimi to alpha kai to ō "
            "(Contra Arianos II.13 Apocalyptic-Christ divine-self-predication; "
            "Tewahedo Christ-Pantocrator iconography anchor)"
        )

    def test_meta_documents_gamma_4_9_expansion(self):
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_source = data["_meta"]["source"]
        assert "γ.4.9" in meta_source, "γ.4.9 must be referenced in _meta.source"
        assert "Athanasius" in meta_source, "γ.4.9 _meta.source should name Athanasius"
        assert "NPNF" in meta_source or "Robertson" in meta_source, (
            "γ.4.9 _meta.source should cite NPNF S2 V4 (Robertson 1892) source"
        )
        assert (
            "FIFTH PATRISTIC VOICE" in meta_source
            or "fifth patristic voice" in meta_source.lower()
            or ("Frumentius" in meta_source and "consecrator" in meta_source)
        ), "γ.4.9 _meta.source should describe the fifth-voice / Frumentius-consecrator apostolic-bridge rationale"


class TestGamma49BAthanasiusPaulineDetailWave:
    """γ.4.9.B — Athanasius of Alexandria Pauline detail wave I (2026-05-13).
    40 verse-keyed entries across all 8 Pauline books deepening the 16 γ.4.9
    seed Pauline anchors to 56-entry detail-wave coverage. Mirrors γ.4.7.B
    Galilean-detail-wave shape (51 entries deepening 13 seed anchors to
    64-entry coverage).

    Distribution (40 entries):
    - Romans (10): Rom 1:4 + 3:25 + 5:14 + 5:19 + 6:3 + 8:3 + 8:9 + 8:17
                   + 8:29 + 11:36
    - 1 Corinthians (6): 1Co 1:30 + 2:8 + 10:4 + 11:25 + 15:21 + 15:45
    - 2 Corinthians (3): 2Co 3:18 + 5:19 + 13:14
    - Galatians (3): Gal 3:13 + 3:20 + 4:6
    - Ephesians (4): Eph 1:21 + 2:14 + 4:9 + 4:10
    - Philippians (4): Phi 2:5 + 2:8 + 2:10 + 3:21
    - Colossians (4): Col 1:17 + 1:18 + 1:19 + 2:14
    - Hebrews (6): Heb 1:5 + 1:6 + 1:8 + 2:14 + 4:15 + 9:14

    Themes covered: Adam-Christ typology (Rom 5:14-19, 1 Cor 15:21, 45) +
    Spirit-of-Son adoption (Rom 8:9, Gal 4:6) + kenotic-completion (Phi 2:5,
    8, 10, 3:21) + cosmic-sustainer (Col 1:17-19) + Hebrews-citation-chain
    (Heb 1:5-8) + Trinitarian-atonement (Heb 9:14).

    Voice mix post-γ.4.9.B (1297 entries): Cyril 51.5% / Jubilees 15.4% /
    1 Enoch 14.8% / Ephrem 12.1% / Athanasius 6.2% (40 seed + 40 detail =
    80). Patristic-anchor majority 67.6% → 69.8%. Per ω.41 §1: Cyril-led-
    plurality preserved (51.5% remains intentional).

    Pins (detail-wave standard set, NOT arc-close):
    - Pauline-Athanasius substantively detailed (≥56 entries across all 8
      Pauline books).
    - Every Pauline book has ≥1 γ.4.9.B detail-wave entry (8-book
      thematic-spread invariant).
    - Athanasius absolute-count milestone ≥80 (40 seed + 40 detail).
    - Romans + Hebrews density milestones (≥13 + ≥8 respectively).
    - 8 signature-anchor pins (one per Pauline book covering the most
      distinctive Athanasian-Pauline-Tewahedo theme for that book).
    - _meta.source sync pin: γ.4.9.B referenced + Athanasius named +
      Pauline detail named.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def _athanasius_in_book(self, book):
        out = []
        for chapter in range(1, 30):
            for verse in range(1, 100):
                out.extend(e for e in self.ec.for_verse(book, chapter, verse) if e.father == "Athanasius of Alexandria")
        return out

    def _all_athanasius(self):
        out = []
        for verse_entries in self.ec._by_verse.values():
            out.extend(e for e in verse_entries if e.father == "Athanasius of Alexandria")
        return out

    def test_pauline_athanasius_substantively_detailed(self):
        # 16 seed (γ.4.9) + 40 detail (γ.4.9.B) = 56 entries across the 8 Pauline books
        pauline_books = {"rom", "1co", "2co", "gal", "eph", "phi", "col", "heb"}
        total = sum(len(self._athanasius_in_book(b)) for b in pauline_books)
        assert total >= 56, f"γ.4.9.B expected ≥56 Pauline-Athanasius entries (16 seed + 40 detail); found {total}"

    def test_every_pauline_book_has_detail_depth(self):
        per_book = {
            b: len(self._athanasius_in_book(b)) for b in ["rom", "1co", "2co", "gal", "eph", "phi", "col", "heb"]
        }
        empty = {b: n for b, n in per_book.items() if n < 1}
        assert not empty, (
            f"γ.4.9.B detail-wave: each Pauline book should have ≥1 Athanasius entry; empty books: {empty}"
        )

    def test_romans_substantively_detailed(self):
        rom = self._athanasius_in_book("rom")
        assert len(rom) >= 13, (
            f"γ.4.9.B expected ≥13 Athanasius entries on Romans (3 seed + 10 detail); found {len(rom)}"
        )

    def test_hebrews_substantively_detailed(self):
        heb = self._athanasius_in_book("heb")
        assert len(heb) >= 8, f"γ.4.9.B expected ≥8 Athanasius entries on Hebrews (2 seed + 6 detail); found {len(heb)}"

    def test_athanasius_milestone_count(self):
        ath = self._all_athanasius()
        assert len(ath) >= 80, f"γ.4.9.B expected ≥80 Athanasius entries total (40 seed + 40 detail); found {len(ath)}"

    # ---- Signature passage pins (8 anchors — one per Pauline book) ----

    def test_rom_5_19_obedience_of_one_anchor_present(self):
        c = [e for e in self.ec.for_verse("rom", 5, 19) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9.B missing Rom 5:19 — 'by obedience of one shall many be made righteous' "
            "(DI §7 Adam-Christ obedience-soteriology anchor)"
        )

    def test_1co_2_8_lord_of_glory_crucified_anchor_present(self):
        c = [e for e in self.ec.for_verse("1co", 2, 8) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9.B missing 1 Cor 2:8 — kyrios tēs doxēs estaurōsan (CA III.32 communicatio-idiomatum Pauline-anchor)"
        )

    def test_2co_13_14_trinitarian_benediction_anchor_present(self):
        c = [e for e in self.ec.for_verse("2co", 13, 14) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9.B missing 2 Cor 13:14 — grace-love-koinonia Trinitarian-benediction "
            "(CA III.6 Pauline-closing-doxology anchor)"
        )

    def test_gal_3_13_became_curse_anchor_present(self):
        c = [e for e in self.ec.for_verse("gal", 3, 13) if e.father == "Athanasius of Alexandria"]
        assert c, "γ.4.9.B missing Gal 3:13 — genomenos hyper hēmōn katara (DI §25 substitutionary-summit anchor)"

    def test_eph_4_9_descent_anchor_present(self):
        c = [e for e in self.ec.for_verse("eph", 4, 9) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9.B missing Eph 4:9 — descended into lower parts "
            "(CA III.46 descent-into-Sheol/harrowing-of-hades Tewahedo anchor)"
        )

    def test_phi_2_10_every_knee_bow_anchor_present(self):
        c = [e for e in self.ec.for_verse("phi", 2, 10) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9.B missing Phil 2:10 — pan gony kampsē "
            "(CA I.42 universal-knee-bow Isa 45:23 + Pauline-incarnational-anchor)"
        )

    def test_col_1_17_cosmic_sustainer_anchor_present(self):
        c = [e for e in self.ec.for_verse("col", 1, 17) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9.B missing Col 1:17 — ta panta en autō synestēken "
            "(CA II.63 cosmic-sustainer-of-all-things present-continuous anchor)"
        )

    def test_heb_1_8_thy_throne_o_god_anchor_present(self):
        c = [e for e in self.ec.for_verse("heb", 1, 8) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9.B missing Heb 1:8 — ho thronos sou ho theos "
            "(CA I.61 direct-address-to-Son-as-ho-theos Pauline-Hebrews-anchor)"
        )

    def test_meta_documents_gamma_4_9_b_expansion(self):
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_source = data["_meta"]["source"]
        assert "γ.4.9.B" in meta_source, "γ.4.9.B must be referenced in _meta.source"
        assert "Pauline" in meta_source, "γ.4.9.B _meta.source should name Pauline detail wave"
        assert "Athanasius" in meta_source, "γ.4.9.B _meta.source should name Athanasius"


class TestGamma49CAthanasiusNonPaulineDetailWave:
    """γ.4.9.C — Athanasius of Alexandria non-Pauline detail wave (2026-05-13).
    40 verse-keyed entries across 13 books deepening the 24 non-Pauline γ.4.9
    seed anchors (OT + Gospels + Petrine/Johannine/Apocalyptic) to 64-entry
    detail coverage AND opening Markan + Lukan Athanasian coverage (γ.4.9
    seed had no Mark / Luke entries).

    Distribution (40 entries):
    - Old Testament Christological Anticipations (14):
        gen (4): 2:7 + 3:15 + 14:18 + 22:18
        exo (2): 7:1 + 33:20
        psa (4): 16:10 + 22:1 + 45:6 + 82:6
        pro (2): 8:23 + 8:30
        isa (2): 53:3 + 61:1
    - Canonical Gospels (14):
        mat (4): 3:17 + 16:16 + 26:39 + 27:46
        mrk (3): 1:1 + 13:32 + 14:62  (NEW — opens Markan Athanasian coverage)
        luk (3): 1:35 + 2:52 + 10:22  (NEW — opens Lukan Athanasian coverage)
        jhn (4): 1:3 + 5:23 + 14:28 + 17:5
    - Petrine + Johannine + Apocalyptic (12):
        1pe (3): 1:23 + 2:21 + 3:19
        2pe (2): 1:3 + 3:18
        1jn (3): 3:8 + 4:2 + 4:9
        rev (4): 1:18 + 4:8 + 5:9 + 19:13

    Themes covered: divine-inbreathing Spirit-bestowal (Gen 2:7) + virgin-
    seed protoevangelium (Gen 3:15) + Melchizedek pre-incarnational
    christophany (Gen 14:18) + gods-by-participation hermeneutic (Exo 7:1
    + Psa 82:6) + cry-of-dereliction voiced-by-flesh (Psa 22:1 + Mat 27:46)
    + Wisdom's economic mission (Pro 8:23, 8:30) + Spirit-recipient-and-
    Spirit-sender (Isa 61:1) + baptism-Trinitarian-theophany (Mat 3:17) +
    Annunciation-Trinitarian-overshadowing (Luk 1:35) + qua-flesh-not-
    knowing (Mrk 13:32) + qua-flesh-developmental-increase (Luk 2:52) +
    homotīmion (Jhn 5:23) + Father-greater-as-source-of-deity (Jhn 14:28)
    + harrowing-of-Hades (1Pe 3:19) + monogenēs-from-Father-essence (1Jn
    4:9) + trisagion-Trinitarian-doxology (Rev 4:8) + Apocalyptic-Logos-
    confirmation (Rev 19:13).

    Voice mix post-γ.4.9.C (1337 entries): Cyril 49.96% / Jubilees 14.96%
    / 1 Enoch 14.36% / Ephrem 11.74% / Athanasius 8.97% (40 seed + 40
    Pauline-detail + 40 non-Pauline-detail = 120). Patristic-anchor
    majority 69.8% → 70.68%. Per ω.41 §1 trajectory rule: Cyril DOWNWARD-
    CROSSES the 50% single-father-majority threshold (51.5% → 49.96%) as
    the natural consequence of the fifth-voice-Athanasius two detail-waves
    in succession; Cyril remains plurality-leader at 3.34× the next single-
    father.

    FIFTH Athanasian work-source added: ATTR_SERAP (Epistulae ad
    Serapionem de Spiritu Sancto — Letters to Serapion on the Holy
    Spirit), used at 5 pneumatologically-decisive anchors (Isa 61:1, Mat
    3:17, Luk 1:35, 2Pe 1:3, Rev 4:8).

    FIRST Athanasian entries on Mark (3: Mrk 1:1 + 13:32 + 14:62) and on
    Luke (3: Luk 1:35 + 2:52 + 10:22).

    Pins (detail-wave standard set, NOT arc-close):
    - Non-Pauline-Athanasius substantively detailed (≥64 entries across
      the 13 non-Pauline books — 24 seed + 40 detail).
    - Every non-Pauline book has ≥1 γ.4.9.C detail-wave entry (13-book
      thematic-spread invariant).
    - Markan + Lukan coverage opens (≥3 entries each).
    - Athanasius absolute-count milestone ≥120 (40 seed + 40 Pauline +
      40 non-Pauline).
    - Per-group density milestones (OT ≥22, Gospels ≥22, PJA ≥20).
    - 8 signature-anchor pins (covering the most distinctive Athanasian
      non-Pauline themes: Gen 2:7 Spirit-inbreathing + Exo 7:1 gods-by-
      participation + Psa 82:6 theōsis-by-grace + Mat 3:17 Trinitarian-
      baptism + Mrk 13:32 qua-flesh-not-knowing + Luk 1:35 Annunciation
      + Jhn 14:28 Father-greater-as-source + Rev 4:8 trisagion).
    - _meta.source sync pin: γ.4.9.C referenced + non-Pauline named +
      Athanasius named + ATTR_SERAP/Serapion source named.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def _athanasius_in_book(self, book):
        # Range needs to cover Psalms (150 chapters) — γ.4.9 seed includes
        # Psa 110:1 + γ.4.9.C adds Psa 82:6 + Isa 61:1, all outside the
        # 60-chapter range the γ.4.9.B Pauline helper used.
        out = []
        for chapter in range(1, 160):
            for verse in range(1, 200):
                out.extend(e for e in self.ec.for_verse(book, chapter, verse) if e.father == "Athanasius of Alexandria")
        return out

    def _all_athanasius(self):
        out = []
        for verse_entries in self.ec._by_verse.values():
            out.extend(e for e in verse_entries if e.father == "Athanasius of Alexandria")
        return out

    # ---- Per-group + per-book density ----

    def test_non_pauline_athanasius_substantively_detailed(self):
        # 8 OT seed + 14 OT detail + 8 Gospels seed + 14 Gospels detail +
        # 8 PJA seed + 12 PJA detail = 64 non-Pauline Athanasius entries.
        non_pauline = {
            "gen",
            "exo",
            "psa",
            "pro",
            "isa",
            "mat",
            "mrk",
            "luk",
            "jhn",
            "1pe",
            "2pe",
            "1jn",
            "rev",
        }
        total = sum(len(self._athanasius_in_book(b)) for b in non_pauline)
        assert total >= 64, f"γ.4.9.C expected ≥64 non-Pauline-Athanasius entries (24 seed + 40 detail); found {total}"

    def test_every_non_pauline_book_has_detail_depth(self):
        non_pauline = ["gen", "exo", "psa", "pro", "isa", "mat", "mrk", "luk", "jhn", "1pe", "2pe", "1jn", "rev"]
        per_book = {b: len(self._athanasius_in_book(b)) for b in non_pauline}
        empty = {b: n for b, n in per_book.items() if n < 1}
        assert not empty, (
            f"γ.4.9.C detail-wave: each non-Pauline book should have ≥1 Athanasius entry; empty books: {empty}"
        )

    def test_markan_coverage_opens(self):
        mrk = self._athanasius_in_book("mrk")
        assert len(mrk) >= 3, (
            f"γ.4.9.C expected ≥3 Athanasius entries on Mark (γ.4.9 seed had none; γ.4.9.C opens Markan coverage); "
            f"found {len(mrk)}"
        )

    def test_lukan_coverage_opens(self):
        luk = self._athanasius_in_book("luk")
        assert len(luk) >= 3, (
            f"γ.4.9.C expected ≥3 Athanasius entries on Luke (γ.4.9 seed had none; γ.4.9.C opens Lukan coverage); "
            f"found {len(luk)}"
        )

    def test_ot_group_substantively_detailed(self):
        ot_books = {"gen", "exo", "psa", "pro", "isa"}
        total = sum(len(self._athanasius_in_book(b)) for b in ot_books)
        assert total >= 22, (
            f"γ.4.9.C expected ≥22 Athanasius OT-christological entries (8 seed + 14 detail); found {total}"
        )

    def test_gospels_group_substantively_detailed(self):
        gospels_books = {"mat", "mrk", "luk", "jhn"}
        total = sum(len(self._athanasius_in_book(b)) for b in gospels_books)
        assert total >= 22, (
            f"γ.4.9.C expected ≥22 Athanasius canonical-Gospels entries (8 seed + 14 detail); found {total}"
        )

    def test_pja_group_substantively_detailed(self):
        pja_books = {"1pe", "2pe", "1jn", "rev"}
        total = sum(len(self._athanasius_in_book(b)) for b in pja_books)
        assert total >= 20, (
            f"γ.4.9.C expected ≥20 Athanasius Petrine/Johannine/Apocalyptic entries (8 seed + 12 detail); found {total}"
        )

    def test_athanasius_milestone_count(self):
        ath = self._all_athanasius()
        assert len(ath) >= 120, (
            f"γ.4.9.C expected ≥120 Athanasius entries total "
            f"(40 seed + 40 Pauline-detail + 40 non-Pauline-detail); found {len(ath)}"
        )

    # ---- Signature passage pins (8 anchors — across the three groups) ----

    def test_gen_2_7_spirit_inbreathing_anchor_present(self):
        c = [e for e in self.ec.for_verse("gen", 2, 7) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9.C missing Gen 2:7 — enephysēsen pnoēn zōēs (DI §3 protological Spirit-bestowal paired with "
            "Jn 20:22 apostolic in-breathing anchor)"
        )

    def test_exo_7_1_gods_by_participation_anchor_present(self):
        c = [e for e in self.ec.for_verse("exo", 7, 1) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9.C missing Exo 7:1 — dedōka se theon tō Pharaō "
            "(CA III.19 gods-by-participation-vs-by-nature hermeneutic-key anchor)"
        )

    def test_psa_82_6_theosis_by_grace_anchor_present(self):
        c = [e for e in self.ec.for_verse("psa", 82, 6) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9.C missing Psa 82:6 — egō eipa theoi este "
            "(CA III.19 theōsis-by-grace anchor, Jn 10:34 cross-canonical pair)"
        )

    def test_mat_3_17_trinitarian_baptism_anchor_present(self):
        c = [e for e in self.ec.for_verse("mat", 3, 17) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9.C missing Mat 3:17 — Jordan-baptismal-Trinitarian-theophany "
            "(Letters to Serapion 1.4 first-explicit-NT-Trinitarian-disclosure anchor)"
        )

    def test_mrk_13_32_qua_flesh_not_knowing_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 13, 32) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9.C missing Mrk 13:32 — oude ho Huios "
            "(CA III.42-50 the-Son-knoweth-not qua-flesh-pedagogical, Athanasius's "
            "extensive treatment of the CRUCIAL Arian prooftext)"
        )

    def test_luk_1_35_annunciation_anchor_present(self):
        c = [e for e in self.ec.for_verse("luk", 1, 35) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9.C missing Luk 1:35 — Spirit-overshadows-Virgin "
            "(Letters to Serapion 1.6 Annunciation-Trinitarian-overshadowing Theotokos anchor)"
        )

    def test_jhn_14_28_father_greater_anchor_present(self):
        c = [e for e in self.ec.for_verse("jhn", 14, 28) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9.C missing Jhn 14:28 — ho Patēr meizōn mou estin "
            "(CA I.58-64 Father-greater-as-source-of-deity-not-substantial-inequality, "
            "Athanasius's most-extensive resolution of the hardest Arian prooftext)"
        )

    def test_rev_4_8_trisagion_anchor_present(self):
        c = [e for e in self.ec.for_verse("rev", 4, 8) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9.C missing Rev 4:8 — hagios hagios hagios "
            "(Letters to Serapion 1.28 Apocalyptic-Trinitarian-trisagion + Isa 6:3 echo + "
            "anti-pneumatomachian-Tropici anchor)"
        )

    # ---- _meta sync pin ----

    def test_meta_documents_gamma_4_9_c_expansion(self):
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_source = data["_meta"]["source"]
        assert "γ.4.9.C" in meta_source, "γ.4.9.C must be referenced in _meta.source"
        assert "non-Pauline" in meta_source, "γ.4.9.C _meta.source should name non-Pauline detail wave"
        assert "Athanasius" in meta_source, "γ.4.9.C _meta.source should name Athanasius"
        assert "Serapion" in meta_source, (
            "γ.4.9.C _meta.source should name Letters to Serapion (new ATTR_SERAP work-source)"
        )


class TestGamma49DAthanasiusArcClose:
    """γ.4.9.D — Athanasius of Alexandria ARC-CLOSE wave (2026-05-13).
    30 verse-keyed entries spanning Acts opening (11) + cross-canon
    capstone-synthesis pins (13) + Psalms-Marcellinus pastoral
    coverage (6, via NEW work-source ATTR_MARC). CLOSING WAVE of the
    four-wave Athanasius arc per §8.1 arc-close convention.

    SEVENTH instance of §8.1 arc-close convention (after γ.4.4.E
    Mäṣḥafä Hēnok, γ.4.5.E Mäṣḥafä Kufāle, γ.4.2.D Pentateuch,
    γ.4.3.D Cyril-on-Luke, γ.4.6.D Cyril-on-Matthew, γ.4.7.D Cyril-
    on-Mark).

    After this ship, ALL FIVE PATRISTIC VOICES are at substantively-
    closed-arc depth:
        Cyril of Alexandria    668 entries (4 Gospel arcs closed)
        Jubilees               200 entries (arc closed γ.4.5.E)
        1 Enoch                192 entries (arc closed γ.4.4.E)
        Ephrem the Syrian      157 entries (Pentateuch arc closed γ.4.2.D)
        Athanasius             150 entries (arc closed by γ.4.9.D)
        ───────────────────────────
        Patristic anchor       1367 entries (71.32% of corpus)

    Distribution (30 entries across 12 books, 2 NEW books opened):
    - Acts (11) — NEW book: 1:8 + 2:24 + 2:32 + 2:36 + 4:12 + 7:55
      + 8:38 + 9:5 + 10:38 + 17:31 + 20:28 (Acts 2:36 epoiēsen is
      the PRINCIPAL Arian prooftext addressed CA II.11-18 over 8
      sections; Acts 8:38 is the Ethiopian eunuch's-baptism Tewahedo
      foundational anchor)
    - Capstone synthesis (13): Mrk 16:15 Markan-Great-Commission +
      Mat 22:43 David-in-Spirit + Mat 24:35 divine-word-eternal +
      Mat 25:31 Son-of-Man-in-glory + Jhn 8:58 egō eimi + Jhn 16:13
      Spirit-of-truth + 1Co 15:28 God-all-in-all + Eph 4:5 one-
      Lord-one-faith-one-baptism + Col 3:4 Christ-our-life + Heb
      13:20 Trinitarian-pastoral + Jam 1:17 Father-of-lights
      immutability (NEW book) + 1Jn 5:20 alēthinos theos + 2Pe 3:9
      divine-patience
    - Psalms-Marcellinus (6) — NEW work-source ATTR_MARC: Psa 23:1
      pastoral-comfort + Psa 51:1 penitential + Psa 51:11 anti-
      pneumatomachian (uses ATTR_SERAP) + Psa 88:1 affliction +
      Psa 91:1 divine-protection + Psa 119:11 Word-internalization

    Per §8.1 the closing wave's test class MUST add the three
    specific pin types:
    (1) _meta synchronization pin per sub-phase tag with regex
        word-boundary matching;
    (2) absolute-count milestone pin at cumulative arc-close count;
    (3) all_N_sections_covered exhaustiveness pin asserting every
        section of the arc has substantive coverage at planned depth.

    Pins:
    - Acts substantively detailed (≥11 entries — OPENS Acts coverage).
    - James substantively detailed (≥1 entry — OPENS James coverage).
    - Every Acts entry verse-anchored at expected loci (11 distinct
      verses across 9 chapters).
    - **§8.1 ARC-CLOSE PIN #1 — count milestone:** Athanasius
      absolute-count ≥150 entries (per `feedback_share_pin_pattern`
      — never a share-pin; durable against future voice-broadening).
    - **§8.1 ARC-CLOSE PIN #2 — all_N_sections_covered
      exhaustiveness:** test_all_four_athanasius_waves_substantively_
      covered asserts γ.4.9 seed (≥40) + γ.4.9.B Pauline (≥40) +
      γ.4.9.C non-Pauline (≥40) + γ.4.9.D arc-close (≥30) — every
      section of the Athanasius arc has substantive coverage at
      planned depth.
    - **§8.1 ARC-CLOSE PIN #3 — _meta synchronization:** pin per
      sub-phase tag (γ.4.9, γ.4.9.B, γ.4.9.C, γ.4.9.D) with regex
      word-boundary; arc-close status recorded explicitly.
    - 8 signature-passage pins for arc-close Tewahedo anchors:
      Act 2:36 epoiēsen Arian-prooftext + Act 8:38 Ethiopian eunuch
      Tewahedo-foundation + Act 20:28 divine-blood + Jhn 8:58 egō
      eimi pre-Abrahamic + Mrk 16:15 Markan-Great-Commission paired-
      with-Mt-28:19 + Psa 51:11 anti-pneumatomachian Spirit-anchor
      + 1Jn 5:20 alēthinos theos most-explicit-deity-of-Son anchor
      + Jam 1:17 Father-of-lights immutability NEW-book opening.

    With this class, the Athanasius arc is PINNED at closed-arc depth
    (the FIFTH and FINAL patristic-voice to reach arc-close in the
    γ.4 corpus).
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def _athanasius_in_book(self, book):
        # Wide chapter range to cover Psalms (150) and any other book.
        out = []
        for chapter in range(1, 160):
            for verse in range(1, 200):
                out.extend(e for e in self.ec.for_verse(book, chapter, verse) if e.father == "Athanasius of Alexandria")
        return out

    def _all_athanasius(self):
        out = []
        for verse_entries in self.ec._by_verse.values():
            out.extend(e for e in verse_entries if e.father == "Athanasius of Alexandria")
        return out

    # ---- New-book coverage opens ----

    def test_acts_coverage_opens(self):
        act = self._athanasius_in_book("act")
        assert len(act) >= 11, (
            f"γ.4.9.D expected ≥11 Athanasius entries on Acts (γ.4.9.D opens Acts coverage; "
            f"includes Acts 2:36 the PRINCIPAL Arian prooftext + Acts 8:38 the Tewahedo "
            f"Ethiopian eunuch foundational anchor); found {len(act)}"
        )

    def test_james_coverage_opens(self):
        jam = self._athanasius_in_book("jam")
        assert len(jam) >= 1, (
            f"γ.4.9.D expected ≥1 Athanasius entry on James (γ.4.9.D opens James coverage "
            f"with Jam 1:17 paired with Festal Letter 39 canon-inclusion); found {len(jam)}"
        )

    # ---- §8.1 ARC-CLOSE PIN #1: count milestone ----

    def test_athanasius_arc_close_count_milestone(self):
        # §8.1 ARC-CLOSE PIN: absolute-count milestone at arc close.
        # Per feedback_share_pin_pattern: never a share pin.
        # Cumulative: 40 (γ.4.9 seed) + 40 (γ.4.9.B) + 40 (γ.4.9.C)
        # + 30 (γ.4.9.D) = 150. ≥150 floor.
        ath = self._all_athanasius()
        assert len(ath) >= 150, (
            f"γ.4.9.D arc-close: Athanasius count ≥150 expected "
            f"(cumulative four-wave arc-close milestone: 40 seed + 40 γ.4.9.B + "
            f"40 γ.4.9.C + 30 γ.4.9.D = 150); found {len(ath)}"
        )

    # ---- §8.1 ARC-CLOSE PIN #2: all_N_sections_covered exhaustiveness ----

    def test_all_four_athanasius_waves_substantively_covered(self):
        # §8.1 ARC-CLOSE PIN: all_N_sections_covered exhaustiveness.
        # Every section of the Athanasius arc must have substantive
        # coverage at planned depth. The four waves are:
        # γ.4.9    seed                  (≥40 multi-group entries)
        # γ.4.9.B  Pauline detail        (≥40 entries across 8 Pauline books)
        # γ.4.9.C  non-Pauline detail    (≥40 entries across 13 non-Pauline books)
        # γ.4.9.D  arc-close             (≥30 entries spanning Acts + capstones + Psalms-Marcellinus)
        # This pin prevents future drift from silently leaving any wave under-covered.
        pauline_books = {"rom", "1co", "2co", "gal", "eph", "phi", "col", "heb"}
        non_pauline_books = {
            "gen",
            "exo",
            "psa",
            "pro",
            "isa",
            "mat",
            "mrk",
            "luk",
            "jhn",
            "1pe",
            "2pe",
            "1jn",
            "rev",
        }
        arc_close_books = {"act", "jam"}

        pauline_total = sum(len(self._athanasius_in_book(b)) for b in pauline_books)
        non_pauline_total = sum(len(self._athanasius_in_book(b)) for b in non_pauline_books)
        arc_close_unique_total = sum(len(self._athanasius_in_book(b)) for b in arc_close_books)
        athanasius_total = len(self._all_athanasius())

        # Pauline (γ.4.9 seed Pauline 16 + γ.4.9.B detail 40 = 56)
        assert pauline_total >= 56, (
            f"γ.4.9.D arc-close: Pauline section below γ.4.9.B parity "
            f"(need ≥56 = 16 seed + 40 detail, have {pauline_total})"
        )
        # Non-Pauline (γ.4.9 seed non-Pauline 24 + γ.4.9.C detail 40 = 64)
        assert non_pauline_total >= 64, (
            f"γ.4.9.D arc-close: non-Pauline section below γ.4.9.C parity "
            f"(need ≥64 = 24 seed + 40 detail, have {non_pauline_total})"
        )
        # γ.4.9.D arc-close opens 2 new books (act + jam) — sum 12 entries
        assert arc_close_unique_total >= 12, (
            f"γ.4.9.D arc-close: NEW-books section below planned depth "
            f"(need ≥12 = 11 Acts + 1 James, have {arc_close_unique_total})"
        )
        # Cumulative milestone
        assert athanasius_total >= 150, (
            f"γ.4.9.D arc-close: total Athanasius ≥150 expected (four-wave cumulative); found {athanasius_total}"
        )

    # ---- §8.1 ARC-CLOSE PIN #3: _meta synchronization ----

    def test_meta_synchronization_at_arc_close(self):
        # §8.1 ARC-CLOSE PIN: _meta synchronization. Pin per sub-phase
        # tag with regex word-boundary so γ.4.9 doesn't accidentally
        # match γ.4.9.B/C/D.
        import json
        import re
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        meta_source = json.loads(path.read_text(encoding="utf-8"))["_meta"]["source"]

        # Word-boundary regex for each sub-phase tag — prevents γ.4.9 from
        # matching γ.4.9.B (greedy substring would).
        for tag in ("γ.4.9", "γ.4.9.B", "γ.4.9.C", "γ.4.9.D"):
            pattern = re.compile(re.escape(tag) + r"(?![.\w])")
            assert pattern.search(meta_source), (
                f"γ.4.9.D arc-close: _meta.source must reference {tag} (four-wave arc-close synchronization pin)"
            )
        # Arc-close-status explicit
        assert "arc CLOSED" in meta_source or "ARC CLOSED" in meta_source, (
            "γ.4.9.D _meta.source should explicitly mark Athanasius arc CLOSED"
        )
        # NEW work-source named
        assert "Marcellinus" in meta_source, (
            "γ.4.9.D _meta.source should name Letter to Marcellinus (new ATTR_MARC work-source)"
        )

    # ---- Signature passage pins (8 arc-close anchors) ----

    def test_act_2_36_epoiesen_arian_prooftext_anchor_present(self):
        c = [e for e in self.ec.for_verse("act", 2, 36) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9.D missing Act 2:36 — epoiēsen ho theos kai Kyrion kai Christon "
            "(CA II.11-18 PRINCIPAL Arian prooftext addressed over 8 sections)"
        )

    def test_act_8_38_ethiopian_eunuch_anchor_present(self):
        c = [e for e in self.ec.for_verse("act", 8, 38) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9.D missing Act 8:38 — Ethiopian eunuch's baptism "
            "(DI §40 Tewahedo institutional foundational anchor; Athanasius consecrated Frumentius)"
        )

    def test_act_20_28_divine_blood_anchor_present(self):
        c = [e for e in self.ec.for_verse("act", 20, 28) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9.D missing Act 20:28 — tēn ekklēsian tou theou hēn periepoiēsato dia tou haimatos tou idiou "
            "(CA II.13 divine-blood Pauline-Petrine anchor)"
        )

    def test_jhn_8_58_ego_eimi_pre_abrahamic_anchor_present(self):
        c = [e for e in self.ec.for_verse("jhn", 8, 58) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9.D missing Jhn 8:58 — prin Abraam genesthai egō eimi "
            "(CA III.30 most-explicit Christ-self-divine-Name claim, paired with Exo 3:14 LXX)"
        )

    def test_mrk_16_15_markan_great_commission_anchor_present(self):
        c = [e for e in self.ec.for_verse("mrk", 16, 15) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9.D missing Mrk 16:15 — Markan Great Commission "
            "(Festal Letter 39 canon-mandate paired with Mt 28:19 baptismal-formula)"
        )

    def test_psa_51_11_anti_pneumatomachian_anchor_present(self):
        c = [e for e in self.ec.for_verse("psa", 51, 11) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9.D missing Psa 51:11 — to Pneuma to Hagion sou mē antanelēs ap' emou "
            "(Letters to Serapion 1.9 OT anti-pneumatomachian anchor against Tropici)"
        )

    def test_1jn_5_20_alethinos_theos_anchor_present(self):
        c = [e for e in self.ec.for_verse("1jn", 5, 20) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9.D missing 1Jn 5:20 — houtos estin ho alēthinos theos kai zōē aiōnios "
            "(CA III.5 MOST-EXPLICIT explicit-deity-of-Son Catholic-Epistle anchor)"
        )

    def test_jam_1_17_father_of_lights_immutability_anchor_present(self):
        c = [e for e in self.ec.for_verse("jam", 1, 17) if e.father == "Athanasius of Alexandria"]
        assert c, (
            "γ.4.9.D missing Jam 1:17 — par' hō ouk eni parallagē ē tropēs aposkiasma "
            "(Festal Letter 39 divine-immutability anti-Arian + James-canon-inclusion anchor)"
        )

    # ---- Cyril plurality preservation pin (ω.41 §1 trajectory rule) ----

    def test_cyril_remains_plurality_leader_at_arc_close(self):
        # ω.41 §1 trajectory rule: track Cyril's plurality position
        # at every threshold-crossing point. At γ.4.9.D arc-close,
        # Cyril is at 48.86% (668/1367) — sub-50% but still plurality
        # at 3.34× next single-father. The trajectory is documented
        # in CHANGELOG / SESSION_STATE.
        #
        # mint-9 #25: assert Cyril leads EVERY plausible challenger, not just
        # Jubilees + Athanasius. A future Ephrem / 1-Enoch expansion wave could
        # overtake Cyril while this test, checking only two rivals, stayed green.
        # Count all single-father voices and compare Cyril to the strongest rival.
        from collections import Counter

        def _voice(father: str) -> str:
            # Collapse tradition suffixes so "1 Enoch (Ethiopian tradition)" and
            # "Jubilees (Ethiopian tradition)" group under one voice key.
            for stem in ("Cyril of Alexandria", "Athanasius", "Ephrem", "1 Enoch", "Jubilees"):
                if father == stem or father.startswith(stem):
                    return stem
            return father

        counts: Counter = Counter()
        for verse_entries in self.ec._by_verse.values():
            for e in verse_entries:
                counts[_voice(e.father)] += 1

        cyril_count = counts.get("Cyril of Alexandria", 0)
        challengers = {v: c for v, c in counts.items() if v != "Cyril of Alexandria"}
        top_rival, top_rival_count = max(challengers.items(), key=lambda kv: kv[1], default=("(none)", 0))
        assert cyril_count > top_rival_count, (
            f"ω.41 §1: Cyril must remain single-father plurality-leader over EVERY "
            f"challenger; Cyril={cyril_count} vs strongest rival {top_rival}={top_rival_count}"
        )

    # ---- _meta sync pin (extension of γ.4.9.C pattern) ----

    def test_meta_documents_gamma_4_9_d_expansion(self):
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_source = data["_meta"]["source"]
        assert "γ.4.9.D" in meta_source, "γ.4.9.D must be referenced in _meta.source"
        assert "arc-close" in meta_source.lower() or "ARC-CLOSE" in meta_source, (
            "γ.4.9.D _meta.source should name arc-close"
        )
        assert "Athanasius" in meta_source, "γ.4.9.D _meta.source should name Athanasius"
        assert "Marcellinus" in meta_source, (
            "γ.4.9.D _meta.source should name Letter to Marcellinus (new ATTR_MARC work-source)"
        )
        assert "SEVENTH" in meta_source or "seventh" in meta_source, (
            "γ.4.9.D _meta.source should name this as the SEVENTH §8.1 arc-close instance"
        )


class TestGamma48MeqabyanSeedWave:
    """γ.4.8 — Mäṣḥafä Mäqabyan (Three Books of Meqabyan) SEED WAVE
    (2026-05-14). OPENS THE SIXTH PATRISTIC/CANONICAL VOICE in the γ.4
    corpus — the third uniquely-Tewahedo-canonical text (alongside 1
    Enoch / Mäṣḥafä Hēnok γ.4.4 and Jubilees / Mäṣḥafä Kufāle γ.4.5).

    40 verse-keyed seed entries across the three Mäqabyan books:
    - 1 Mq (20 entries) across 14 chapters — martyrology of Maqabis-
      of-Benjamin and his five sons vs Chaldean king Ṣiruṣaydan;
      contains the EPONYM verse 2:14 from which the entire trilogy
      takes its title.
    - 2 Mq (12 entries) across 11 chapters — Maqabis-of-Moab
      conversion cycle (the longest portrait of a Gentile convert in
      the entire EOTC canon) + a second martyrdom-cycle of his sons
      + the death of Ṣiruṣaydan + the anti-sectarian resurrection-
      polemic.
    - 3 Mq (8 entries) across 5 chapters — homiletic anthology with
      the most theologically distinctive content of the trilogy: the
      first-person speech of the Devil + the Satan-refused-to-worship-
      Adam tradition + the "tenth tribe" angelic hierarchy + the
      four-elements anthropology + the EOTC canonical definition of
      "complete repentance" (ፍጹም ንስሓ).

    γ.4.8 had been DEFERRED across the entire γ.4 corpus history
    pending PD source acquisition. The 2026-05-14 user-contributed
    CC0 1.0 English translation (archive.org/details/three-books-of-
    meqabyan-cc0-translation, translated from Modern Amharic of the
    EOTC Bible at nehemiah-osc.org) is the canonical unblocker.

    Voice mix post-γ.4.8 (1407 entries):
        Cyril       668  47.48%
        Jubilees    200  14.22%
        1 Enoch     192  13.65%
        Ephrem      157  11.16%
        Athanasius  150  10.66%
        Meqabyan     40   2.84%  ← γ.4.8 SEED

    Cyril remains plurality-leader at 3.34× next-single-father (668
    vs 200). Patristic-anchor majority (Cyril + Ephrem + Athanasius)
    holds at ~69.2%; Tewahedo-distinctive-canonical voices (Mäṣḥafä
    Hēnok + Mäṣḥafä Kufāle + Mäqabyan) hold 30.8% — for the first
    time the three uniquely-Tewahedo canonical texts together
    constitute a numerically-significant block.

    Pins (seed-wave standard set, NOT arc-close):
    - Meqabyan substantively seeded (≥40 entries total).
    - All three Mäqabyan books opened (mq1 ≥20, mq2 ≥12, mq3 ≥8 —
      previously all 0-tuple per AUDIT_2026-05-13-DEEP D-C1 finding).
    - Per-book minimum density invariant.
    - 8 signature-anchor pins (most distinctive theological loci):
      mq1 2:14 EPONYM-VERSE + mq1 2:5 creation-confession + mq1 36:22
      Abraham-my-friend triple-formula + mq2 4:15 Maqabis-of-Moab
      conversion + mq2 14:1 four-sectarian-resurrection-errors + mq3
      1:15 SATAN-REFUSED-TO-BOW-TO-ADAM + mq3 4:8 'tenth-tribe'
      angelic hierarchy + mq3 4:34 'complete repentance' EOTC
      sacramental-confession foundation.
    - _meta.source sync pin: γ.4.8 referenced + Meqabyan named +
      Horovitz named (apparatus source) + CC0 / archive.org named.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def _meq_in_book(self, book):
        # Mäqabyan chapter counts: mq1 36 ch, mq2 21 ch, mq3 10 ch.
        # Verses per chapter top out around 50 (1 Mq 28 has 49). Use
        # wide range to be safe.
        out = []
        for chapter in range(1, 50):
            for verse in range(1, 60):
                out.extend(
                    e for e in self.ec.for_verse(book, chapter, verse) if e.father == "Meqabyan (Ethiopian tradition)"
                )
        return out

    def _all_meq(self):
        out = []
        for verse_entries in self.ec._by_verse.values():
            out.extend(e for e in verse_entries if e.father == "Meqabyan (Ethiopian tradition)")
        return out

    # ---- Voice-opening + per-book coverage ----

    def test_meqabyan_voice_opens(self):
        meq = self._all_meq()
        assert len(meq) >= 40, (
            f"γ.4.8 seed expected ≥40 Meqabyan entries (opens SIXTH voice in γ.4 corpus); found {len(meq)}"
        )

    def test_all_three_maqabyan_books_opened(self):
        # Per AUDIT_2026-05-13-DEEP D-C1: mq1.py + mq2.py + mq3.py were
        # all 0-tuple before γ.4.8. After seed they must all have entries.
        books = ["mq1", "mq2", "mq3"]
        per_book = {b: len(self._meq_in_book(b)) for b in books}
        empty = {b: n for b, n in per_book.items() if n < 1}
        assert not empty, (
            f"γ.4.8 seed: each of the three Mäqabyan books must have ≥1 Meqabyan entry "
            f"(opens previously-empty notes-files); empty books: {empty}"
        )

    def test_mq1_substantively_seeded(self):
        mq1 = self._meq_in_book("mq1")
        assert len(mq1) >= 20, (
            f"γ.4.8 seed expected ≥20 entries on 1 Meqabyan (martyrology + EPONYM verse 2:14); found {len(mq1)}"
        )

    def test_mq2_substantively_seeded(self):
        mq2 = self._meq_in_book("mq2")
        assert len(mq2) >= 12, (
            f"γ.4.8 seed expected ≥12 entries on 2 Meqabyan (Maqabis-of-Moab conversion + sons-martyrdom + "
            f"anti-sectarian resurrection-polemic); found {len(mq2)}"
        )

    def test_mq3_substantively_seeded(self):
        mq3 = self._meq_in_book("mq3")
        assert len(mq3) >= 8, (
            f"γ.4.8 seed expected ≥8 entries on 3 Meqabyan (Devil-dialogue + Satan-refused-Adam + complete-"
            f"repentance + resurrection-doctrine); found {len(mq3)}"
        )

    # ---- Signature passage pins (8 anchors) ----

    def test_mq1_2_14_eponym_verse_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq1", 2, 14) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8 missing mq1 2:14 — THE EPONYM VERSE መቃብያንን ('the Meqabyans'); the verse "
            "from which the entire trilogy takes its title"
        )

    def test_mq1_2_5_creation_confession_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq1", 2, 5) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8 missing mq1 2:5 — creation-confession of faith (inverts Ṣiruṣaydan's claim at 1:26-27); "
            "EOTC anti-idolatry creed rooted in Genesis 1"
        )

    def test_mq1_36_22_abraham_my_friend_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq1", 36, 22) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8 missing mq1 36:22 — 'Abraham is my friend; Isaac is my favored one; Jacob is the beloved "
            "of my heart' triple-formula (theological climax of 1 Mq; James 2:23 + Isa 41:8 + 2 Chron 20:7)"
        )

    def test_mq2_4_15_maqabis_of_moab_conversion_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq2", 4, 15) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8 missing mq2 4:15 — Maqabis-of-Moab as righteous-Gentile-convert (longest portrait of "
            "Gentile convert in EOTC canon; Ruth-Rabbah-2:9 + Tg-Ps-J-Ruth-1:16 parallels)"
        )

    def test_mq2_14_1_four_sectarian_errors_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq2", 14, 1) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8 missing mq2 14:1 — four sectarian errors about resurrection (Jews + Samaritans + Pharisees "
            "+ Sadducees); longest chapter in 2 Mq, the anti-sectarian resurrection-polemic"
        )

    def test_mq3_1_15_satan_refused_to_bow_to_adam_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq3", 1, 15) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8 missing mq3 1:15 — SATAN-REFUSED-TO-WORSHIP-ADAM tradition; the MOST DIAGNOSTIC "
            "angelological verse in 3 Mq (Vita Adae §§12-17 + 2 Enoch + Cave of Treasures §2 + Qur'an cluster)"
        )

    def test_mq3_4_8_tenth_tribe_angelic_hierarchy_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq3", 4, 8) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8 missing mq3 4:8 — 'tenth tribe' angelic hierarchy (Pseudo-Dionysius Celestial Hierarchy 6.2 "
            "+ Gregory the Great Hom. Evang. 34 + Augustine Enchiridion §29 + Anselm Cur Deus Homo I.16-18)"
        )

    def test_mq3_4_34_complete_repentance_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq3", 4, 34) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8 missing mq3 4:34 — 'complete repentance' (ፍጹም ንስሓ) definition; foundation of EOTC "
            "sacramental confession (codified later in Fetha Nagast 13th c.)"
        )

    # ---- _meta sync pin ----

    def test_meta_documents_gamma_4_8_expansion(self):
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_source = data["_meta"]["source"]
        assert "γ.4.8" in meta_source, "γ.4.8 must be referenced in _meta.source"
        assert "Mäqabyan" in meta_source or "Meqabyan" in meta_source, (
            "γ.4.8 _meta.source should name Mäqabyan/Meqabyan"
        )
        assert "Horovitz" in meta_source, (
            "γ.4.8 _meta.source should name Josef Horovitz 1905 (apparatus primary scholarly source)"
        )
        assert "CC0" in meta_source or "archive.org" in meta_source or "Public Domain" in meta_source, (
            "γ.4.8 _meta.source should reference the CC0 1.0 / archive.org canonical source for the translation"
        )
        assert "SIXTH" in meta_source or "sixth" in meta_source, (
            "γ.4.8 _meta.source should name this as opening the SIXTH voice in the corpus"
        )


class TestGamma48BMeqabyanIDetailWave:
    """γ.4.8.B — Mäṣḥafä Mäqabyan I DETAIL WAVE (2026-05-14). 40 verse-
    keyed entries deepening the 20 mq1 seed anchors to 60-entry
    substantive-detail coverage. FIRST DETAIL WAVE on the SIXTH-voice
    opened by γ.4.8 seed; mirrors γ.4.4.B Watchers detail + γ.4.5.B-E
    Jubilees chapter-range details + γ.4.9.B-C Athanasius detail-wave
    shapes.

    Distribution (40 entries across 23 chapters, 11 of which are newly
    opened relative to seed):

    - Deepened seed chapters (12): 2(+6), 3(+3), 5(+2), 6(+2), 8(+3),
      10(+1), 13(+2), 14(+2), 28(+2), 33(+1), 34(+1), 36(+2) — 27 detail
      entries.
    - Newly-opened chapters (11): 4(+2), 7(+1), 9(+1), 11(+1), 12(+1),
      15(+1), 16(+1), 18(+1), 19(+1), 25(+2), 29(+1) — 13 detail
      entries.

    Mq1 coverage post-γ.4.8.B: 25 of 36 chapters (70%); per-chapter
    floor varies (Ch 2 deepest at 11 entries; many newly-opened
    chapters at 1-2 entries).

    Voice-mix impact:
        Meqabyan 40 → 80 entries; Cyril 47.48% → 46.16% (continues
        sub-50% trajectory; remains plurality-leader at 3.34× next-
        single-father); Tewahedo-distinctive-canonical block (Mäṣḥafä
        Hēnok + Mäṣḥafä Kufāle + Mäqabyan) → 32.62%.

    Pins (detail-wave standard set):
    - Mq1 substantively detailed (≥60 entries — 20 seed + 40 detail).
    - Meqabyan absolute-count milestone ≥80.
    - Every previously-seeded mq1 chapter still has its seed entry
      (no regression).
    - 11 newly-opened mq1 chapters all carry ≥1 detail-wave entry
      (4, 7, 9, 11, 12, 15, 16, 18, 19, 25, 29).
    - 8 signature-anchor pins (most distinctive detail-wave theology):
      mq1 2:8 warrior-of-martyrs + mq1 3:28 five-brothers-DISTINCTIVE-
      EXPANSION + mq1 4:1 corpses-resist-destruction-OPENS-Ch4 +
      mq1 8:22 STRONGEST 1 Cor 15:36-38 PAULINE PARALLEL + mq1 11:1
      Tyre+Sidon=Ṣiruṣaydan-ETYMOLOGY + mq1 15:6 SECOND-Maqabean-
      trio Frankfurt-Codex + mq1 25:9 ETHIOPIA-NAMED-FIRST + mq1 28:38
      ETHIOPIA-NAMED-SECOND.
    - _meta.source sync pin: γ.4.8.B referenced + "detail" named +
      mq1 named + "TWELFTH" N-W4 named.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def _meq_in_mq1(self):
        out = []
        for chapter in range(1, 40):
            for verse in range(1, 60):
                out.extend(
                    e for e in self.ec.for_verse("mq1", chapter, verse) if e.father == "Meqabyan (Ethiopian tradition)"
                )
        return out

    def _meq_in_mq1_chapter(self, chapter):
        out = []
        for verse in range(1, 60):
            out.extend(
                e for e in self.ec.for_verse("mq1", chapter, verse) if e.father == "Meqabyan (Ethiopian tradition)"
            )
        return out

    def _all_meq(self):
        out = []
        for verse_entries in self.ec._by_verse.values():
            out.extend(e for e in verse_entries if e.father == "Meqabyan (Ethiopian tradition)")
        return out

    # ---- Per-voice + per-book density ----

    def test_mq1_substantively_detailed(self):
        mq1 = self._meq_in_mq1()
        assert len(mq1) >= 60, f"γ.4.8.B expected ≥60 Meqabyan entries on 1 Mq (20 seed + 40 detail); found {len(mq1)}"

    def test_meqabyan_milestone_at_detail_wave(self):
        meq = self._all_meq()
        assert len(meq) >= 80, (
            f"γ.4.8.B expected ≥80 Meqabyan entries total (40 seed + 40 detail = 80); found {len(meq)}"
        )

    def test_all_previously_seeded_mq1_chapters_retained(self):
        # Regression-guard: seed chapters must still have their seed
        # entries after detail-wave ship.
        seed_chapters = [2, 3, 5, 6, 8, 10, 13, 14, 17, 28, 30, 33, 34, 36]
        per_chapter = {ch: len(self._meq_in_mq1_chapter(ch)) for ch in seed_chapters}
        empty = {ch: n for ch, n in per_chapter.items() if n < 1}
        assert not empty, f"γ.4.8.B regression: previously-seeded mq1 chapters must retain entries; empty: {empty}"

    def test_eleven_newly_opened_mq1_chapters_have_detail(self):
        # γ.4.8.B specifically opened 11 previously-seed-empty chapters.
        # Each must have ≥1 entry post-detail-wave.
        newly_opened = [4, 7, 9, 11, 12, 15, 16, 18, 19, 25, 29]
        per_chapter = {ch: len(self._meq_in_mq1_chapter(ch)) for ch in newly_opened}
        empty = {ch: n for ch, n in per_chapter.items() if n < 1}
        assert not empty, f"γ.4.8.B opens 11 newly-empty chapters: each must have ≥1 entry; empty: {empty}"

    # ---- Signature passage pins (8 anchors) ----

    def test_mq1_2_8_warrior_of_martyrs_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq1", 2, 8) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.B missing mq1 2:8 — bear-strangling warrior-of-martyrs motif "
            "(distinctive vs LXX 2 Macc 7 passive-martyr; Samson/David's-mighty-men echoes)"
        )

    def test_mq1_3_28_five_brothers_expansion_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq1", 3, 28) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.B missing mq1 3:28 — five-brothers expansion DISTINCTIVE to Ethiopian narrative "
            "(no parallel in LXX 2 Maccabees seven-sons; mirrors mq2 13:1 five-sons-of-Maqabis-of-Moab)"
        )

    def test_mq1_4_1_corpses_resist_destruction_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq1", 4, 1) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.B missing mq1 4:1 — OPENS Ch 4 (corpses-resist-destruction: fire cannot burn; "
            "Daniel 3:19-27 three-young-men-in-furnace parallel)"
        )

    def test_mq1_8_22_strongest_pauline_parallel_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq1", 8, 22) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.B missing mq1 8:22 — SEED-BURIED-AND-RISING (STRONGEST 1 Cor 15:36-38 Pauline "
            "parallel in entire Meqabyan trilogy per CROSS_REFERENCE_APPENDIX §10)"
        )

    def test_mq1_11_1_tyre_sidon_etymology_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq1", 11, 1) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.B missing mq1 11:1 — OPENS Ch 11 (Ṣiruṣaydan = TYRE + SIDON etymology; "
            "Horovitz 1905 p. 195 fn. 3 + Dillmann Lexicon Linguae Aethiopicae 1865)"
        )

    def test_mq1_15_6_second_maqabean_trio_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq1", 15, 6) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.B missing mq1 15:6 — OPENS Ch 15 (SECOND Maqabean trio Mebkyus/Maqabis/Yehuda; "
            "Horovitz 1905 Frankfurt Codex Rüppel II 7 structural witness for the composite-textual-"
            "history of the trilogy)"
        )

    def test_mq1_25_9_ethiopia_named_first_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq1", 25, 9) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.B missing mq1 25:9 — ETHIOPIA NAMED (first reference in 1 Mq; Tewahedo-uniqueness-"
            "angle per memory `project_v1_terminus` buyer-demo)"
        )

    def test_mq1_28_38_ethiopia_named_second_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq1", 28, 38) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.B missing mq1 28:38 — ETHIOPIA NAMED (second reference; structural anchor "
            "for Aksumite-and-Tewahedo biblical self-understanding)"
        )

    # ---- _meta sync pin ----

    def test_meta_documents_gamma_4_8_b_expansion(self):
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_source = data["_meta"]["source"]
        assert "γ.4.8.B" in meta_source, "γ.4.8.B must be referenced in _meta.source"
        assert "detail" in meta_source.lower(), "γ.4.8.B _meta.source should name 'detail wave'"
        assert "mq1" in meta_source.lower() or "Mäqabyan I" in meta_source, (
            "γ.4.8.B _meta.source should name mq1 / Mäqabyan I"
        )
        assert "TWELFTH" in meta_source or "twelfth" in meta_source, (
            "γ.4.8.B _meta.source should name this as the TWELFTH N-W4 verification"
        )


class TestGamma48CMeqabyanIIDetailWave:
    """γ.4.8.C — Mäṣḥafä Mäqabyan II DETAIL WAVE (2026-05-14). 40 verse-
    keyed entries deepening the 12 mq2 seed anchors to 52-entry
    substantive-detail coverage. SECOND DETAIL WAVE on the SIXTH-voice
    opened by γ.4.8 seed; FIRST Mäqabyan WAVE TO ACHIEVE COMPLETE CHAPTER
    COVERAGE of any Mäqabyan book — mq2 12/21 (57%) seeded → 21/21
    (100%) substantively-covered after this ship. Mirrors γ.4.4.B-D +
    γ.4.5.B-E + γ.4.6.B-D + γ.4.7.B-D + γ.4.8.B + γ.4.9.B-C detail-wave
    shapes.

    Distribution (40 entries across 21 chapters — all 21 chapters of 2
    Mq touched post-γ.4.8.C):

    - Deepened seed chapters (9): 1(+3), 2(+1), 3(+2), 4(+2), 6(+1),
      12(+2), 14(+3), 17(+1), 18(+1) — 16 detail entries.
    - Newly-opened chapters (12): 5(+2), 7(+2), 8(+2), 9(+2), 10(+2),
      11(+2), 13(+2), 15(+2), 16(+2), 19(+2), 20(+2), 21(+2) — 24
      detail entries.

    Mq2 coverage post-γ.4.8.C: 21 of 21 chapters (100%) — FIRST 2 Mq
    WAVE TO ACHIEVE COMPLETE CHAPTER COVERAGE.

    Voice-mix impact:
        Meqabyan 80 → 120 entries; Cyril 46.16% → 44.92% (continues
        sub-50% trajectory; remains plurality-leader at 3.34× next-
        single-father); Tewahedo-distinctive-canonical block (Mäṣḥafä
        Hēnok + Mäṣḥafä Kufāle + Mäqabyan) → 34.43%.

    Pins (detail-wave standard set, EXTENDED with full-coverage pin):
    - Mq2 substantively detailed (≥52 entries — 12 seed + 40 detail).
    - Meqabyan absolute-count milestone ≥120 (40 seed + 40 mq1-detail
      + 40 mq2-detail).
    - Every previously-seeded mq2 chapter still has its seed entry
      (no regression).
    - 12 newly-opened mq2 chapters all carry ≥1 detail-wave entry
      (5, 7, 8, 9, 10, 11, 13, 15, 16, 19, 20, 21).
    - **Mq2 full-21-chapter coverage** — every chapter 1..21 has ≥1
      Meqabyan entry post-γ.4.8.C (new pin specific to this wave; the
      arc-completion-depth invariant for 2 Mq).
    - 8 signature-anchor pins (most distinctive detail-wave theology):
      mq2 3:9 thousandth-generation Ex 20:5-6 forgiveness-formula +
      mq2 4:1 JUDGE-PATTERN-ROSTER Joshua+Gideon+Samson+Barak+Deborah+
      JUDITH-deuterocanonical-included + mq2 5:1 captive-children-teach-
      Torah inversion-OPENS-Ch5 + mq2 13:1 FIVE-SONS-OF-MAQABIS-OF-MOAB
      number-symmetry-Frankfurt-Codex-OPENS-Ch13 + mq2 14:23 CORD-OF-
      SHEOL distinctive-Meqabyan-image + mq2 16:1 ANTI-SAMARITAN-
      resurrection-denial-polemic Pentateuch-only-canon-OPENS-Ch16 +
      mq2 19:10 CHRIST-ALLUSION-DEBATED Horovitz-'von-Christus-nirgends-
      die-Rede'-Tier-3-interpretive-OPENS-Ch19 + mq2 21:10 DOUBLE-AMEN
      book-closing-formula MIRRORS 1 Mq 36:45-OPENS-Ch21.
    - _meta.source sync pin: γ.4.8.C referenced + "detail" named +
      mq2 named + "THIRTEENTH" N-W4 named + "100%" or "complete"
      chapter-coverage named.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def _meq_in_mq2(self):
        out = []
        for chapter in range(1, 25):
            for verse in range(1, 60):
                out.extend(
                    e for e in self.ec.for_verse("mq2", chapter, verse) if e.father == "Meqabyan (Ethiopian tradition)"
                )
        return out

    def _meq_in_mq2_chapter(self, chapter):
        out = []
        for verse in range(1, 60):
            out.extend(
                e for e in self.ec.for_verse("mq2", chapter, verse) if e.father == "Meqabyan (Ethiopian tradition)"
            )
        return out

    def _all_meq(self):
        out = []
        for verse_entries in self.ec._by_verse.values():
            out.extend(e for e in verse_entries if e.father == "Meqabyan (Ethiopian tradition)")
        return out

    # ---- Per-voice + per-book density ----

    def test_mq2_substantively_detailed(self):
        mq2 = self._meq_in_mq2()
        assert len(mq2) >= 52, f"γ.4.8.C expected ≥52 Meqabyan entries on 2 Mq (12 seed + 40 detail); found {len(mq2)}"

    def test_meqabyan_milestone_at_second_detail_wave(self):
        meq = self._all_meq()
        assert len(meq) >= 120, (
            f"γ.4.8.C expected ≥120 Meqabyan entries total (40 seed + 40 mq1-detail + 40 mq2-detail = 120); "
            f"found {len(meq)}"
        )

    def test_all_previously_seeded_mq2_chapters_retained(self):
        # Regression-guard: seed chapters must still have their seed
        # entries after detail-wave ship.
        seed_chapters = [1, 2, 3, 4, 6, 12, 14, 17, 18]
        per_chapter = {ch: len(self._meq_in_mq2_chapter(ch)) for ch in seed_chapters}
        empty = {ch: n for ch, n in per_chapter.items() if n < 1}
        assert not empty, f"γ.4.8.C regression: previously-seeded mq2 chapters must retain entries; empty: {empty}"

    def test_twelve_newly_opened_mq2_chapters_have_detail(self):
        # γ.4.8.C specifically opened 12 previously-seed-empty chapters.
        # Each must have ≥1 entry post-detail-wave.
        newly_opened = [5, 7, 8, 9, 10, 11, 13, 15, 16, 19, 20, 21]
        per_chapter = {ch: len(self._meq_in_mq2_chapter(ch)) for ch in newly_opened}
        empty = {ch: n for ch, n in per_chapter.items() if n < 1}
        assert not empty, f"γ.4.8.C opens 12 newly-empty chapters: each must have ≥1 entry; empty: {empty}"

    def test_mq2_full_21_chapter_coverage_achieved(self):
        # γ.4.8.C is the FIRST Mäqabyan WAVE to achieve 100% chapter
        # coverage of any Mäqabyan book. Every chapter 1..21 must have
        # ≥1 Meqabyan entry post-ship. This is the arc-completion-
        # depth invariant for 2 Mq within the larger γ.4.8 arc.
        all_chapters = list(range(1, 22))
        per_chapter = {ch: len(self._meq_in_mq2_chapter(ch)) for ch in all_chapters}
        empty = {ch: n for ch, n in per_chapter.items() if n < 1}
        assert not empty, (
            f"γ.4.8.C: 2 Mq must reach 100% chapter coverage (21 of 21 chapters with ≥1 entry); empty: {empty}"
        )

    # ---- Signature passage pins (8 anchors) ----

    def test_mq2_3_9_thousandth_generation_formula_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq2", 3, 9) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.C missing mq2 3:9 — Ex 20:5-6 third-fourth-generation / thousandth-generation "
            "forgiveness-formula (theological anchor justifying Maqabis-of-Moab's eligibility for conversion)"
        )

    def test_mq2_4_1_judge_pattern_roster_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq2", 4, 1) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.C missing mq2 4:1 — JUDGE-PATTERN ROSTER Joshua + Gideon + Samson + Barak + Deborah + "
            "JUDITH (deuterocanonical-EOTC figure included; deliverer-judge typology extended to Maqabis-of-Moab)"
        )

    def test_mq2_5_1_captive_children_teach_torah_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq2", 5, 1) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.C missing mq2 5:1 — OPENS Ch 5 (captive-Jewish-children TEACH TORAH to Maqabis-of-Moab "
            "household; 2 Kings 5 Naaman + slave-girl inversion topos)"
        )

    def test_mq2_13_1_five_sons_of_maqabis_of_moab_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq2", 13, 1) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.C missing mq2 13:1 — OPENS Ch 13 (FIVE-SONS-OF-MAQABIS-OF-MOAB ROSTER; NUMBER-SYMMETRY "
            "with 1 Mq five-brothers per Horovitz 1905 Frankfurt Codex Rüppel II 7 structural analysis — "
            "one of the most structurally-significant verses in the entire trilogy)"
        )

    def test_mq2_14_23_cord_of_sheol_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq2", 14, 23) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.C missing mq2 14:23 — CORD-OF-SHEOL bond-from-mother's-womb (UNIQUE to Meqabyan among "
            "EOTC canonical literature; Tewahedo doctrine of INHERITED-MORTALITY-FROM-CONCEPTION; Horovitz "
            "1905 p. 220 confirms no biblical/patristic parallel)"
        )

    def test_mq2_16_1_anti_samaritan_polemic_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq2", 16, 1) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.C missing mq2 16:1 — OPENS Ch 16 (ANTI-SAMARITAN resurrection-denial polemic; Pentateuch-"
            "only-canon argument; Christ-with-Sadducees argument-pattern Mt 22:31-32 applied)"
        )

    def test_mq2_19_10_christ_allusion_debated_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq2", 19, 10) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.C missing mq2 19:10 — OPENS Ch 19 (Christ-allusion-debated per Horovitz 1905 'von Christus "
            "nirgends die Rede' Tier-3 interpretive-flagging; canonical-Christian-readerly-overlay reading)"
        )

    def test_mq2_21_10_double_amen_book_closing_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq2", 21, 10) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.C missing mq2 21:10 — OPENS Ch 21 (DOUBLE-AMEN አሜን፥ አሜን book-closing-formula; "
            "MIRRORS 1 Mq 36:45 — completes structural-parity between two book-endings; characteristic "
            "Meqabyan book-closing signature)"
        )

    # ---- _meta sync pin ----

    def test_meta_documents_gamma_4_8_c_expansion(self):
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_source = data["_meta"]["source"]
        assert "γ.4.8.C" in meta_source, "γ.4.8.C must be referenced in _meta.source"
        assert "detail" in meta_source.lower(), "γ.4.8.C _meta.source should name 'detail wave'"
        assert "mq2" in meta_source.lower() or "Mäqabyan II" in meta_source, (
            "γ.4.8.C _meta.source should name mq2 / Mäqabyan II"
        )
        assert "THIRTEENTH" in meta_source or "thirteenth" in meta_source, (
            "γ.4.8.C _meta.source should name this as the THIRTEENTH N-W4 verification"
        )
        assert "100%" in meta_source or "complete chapter coverage" in meta_source.lower(), (
            "γ.4.8.C _meta.source should name the 100% / complete-chapter-coverage achievement on 2 Mq"
        )


class TestGamma48DMeqabyanIIIDetailWave:
    """γ.4.8.D — Mäṣḥafä Mäqabyan III DETAIL WAVE (2026-05-14). 40 verse-
    keyed entries deepening the 8 mq3 seed anchors to 48-entry
    substantive-detail coverage. THIRD DETAIL WAVE on the SIXTH-voice
    opened by γ.4.8 seed; SECOND Mäqabyan WAVE TO ACHIEVE COMPLETE
    CHAPTER COVERAGE of a Mäqabyan book — mq3 4/10 (40%) seeded →
    10/10 (100%) substantively-covered after this ship. TWO OF THREE
    Mäqabyan books now at 100% chapter coverage (mq2 via γ.4.8.C;
    mq3 via γ.4.8.D). Mirrors γ.4.4.B-D + γ.4.5.B-E + γ.4.6.B-D +
    γ.4.7.B-D + γ.4.8.B + γ.4.8.C + γ.4.9.B-C detail-wave shapes.

    Distribution (40 entries across 10 chapters — all 10 chapters of
    3 Mq touched post-γ.4.8.D):

    - Deepened seed chapters (4): 1(+7), 2(+3), 4(+8), 10(+5) — 23
      detail entries (CC0-text-grounded patristic-parallel commentary
      elaborating SEEDED theological loci).
    - Newly-opened chapters (6): 3(+4), 5(+3), 6(+3), 7(+3), 8(+2),
      9(+2) — 17 detail entries (homiletic-genre-anchor framing per
      source-fidelity note in the ship script docstring).

    Source-fidelity note: deepening entries on Chs 1/2/4/10 elaborate
    patristic-parallels for the SEEDED theological loci with CC0-text-
    grounded context; opening entries on Chs 3/5/6/7/8/9 are HOMILETIC-
    GENRE ANCHORS framed as patristic-parallel commentary on the
    chapter's thematic position rather than direct verse-text-quotations.
    Per SOURCES.md §7 Tier-3 interpretive-flagging convention (3
    interpretive-readings-flagged out of 64 citations in
    CROSS_REFERENCE_APPENDIX).

    Mq3 coverage post-γ.4.8.D: 10 of 10 chapters (100%). Per-chapter:
    Ch 4 deepest at 11 entries (theological-anthropology systematics);
    Ch 1 at 10 (cosmological-rebellion narrative); other chapters at
    2-6.

    Voice-mix impact:
        Meqabyan 120 → 160 entries; Cyril 44.92% → 43.75% (continues
        sub-50% trajectory; remains plurality-leader at 3.34× next-
        single-father); **Meqabyan REACHES PARITY WITH ATHANASIUS**
        (160 vs 150) — the SIXTH voice attains the patristic-anchor-
        voice depth-benchmark; Tewahedo-distinctive-canonical block
        (Mäṣḥafä Hēnok + Mäṣḥafä Kufāle + Mäqabyan) → 36.15%.

    Pins (detail-wave standard set + full-coverage pin matching
    γ.4.8.C SECOND-instance):
    - Mq3 substantively detailed (≥48 entries — 8 seed + 40 detail).
    - Meqabyan absolute-count milestone ≥160 (40 seed + 40 mq1-detail
      + 40 mq2-detail + 40 mq3-detail; PARITY with Athanasius 150).
    - Every previously-seeded mq3 chapter still has its seed entry
      (no regression).
    - 6 newly-opened mq3 chapters all carry ≥1 detail-wave entry
      (3, 5, 6, 7, 8, 9).
    - **Mq3 full-10-chapter coverage** — every chapter 1..10 has ≥1
      Meqabyan entry post-γ.4.8.D (SECOND instance of the arc-
      completion-depth invariant after γ.4.8.C achieved it on mq2).
    - **Mäqabyan-trilogy 67% completion** — TWO OF THREE Mäqabyan
      books at 100% chapter coverage (mq2 + mq3); mq1 remains at
      ~70% pending γ.4.8.E arc-close consideration.
    - 8 signature-anchor pins (most distinctive detail-wave theology):
      mq3 1:22 post-fall divine-judgment-pronouncement Gen 3:14-15
      Protoevangelium + mq3 2:15 angelic-replacement Augustine
      Enchiridion §29 + Anselm CDH I.16-18 + mq3 4:15 **PROV 8:22-30
      REAPPLIED TO ADAM Tier-3-interpretive-flagged** + mq3 4:18
      four-elements-Adamic-anthropology Empedoclean-Galenic + mq3 4:28
      repentance-as-image-restoration Athanasius De Inc 32 + mq3 5:1
      OPENS-Ch5 charity-and-mercy Mt 25:31-46 + mq3 7:7 OPENS-Ch7
      humility-inverts-Devil's-pride Phil 2:5-11 kenosis + mq3 10:29
      **TRIPLE-DOXOLOGY** book-closing completes trilogy (1 Mq 36:45
      + 2 Mq 21:10 + 3 Mq 10:29).
    - _meta.source sync pin: γ.4.8.D referenced + "detail" named +
      mq3 named + "FOURTEENTH" N-W4 named + "parity" or "Athanasius"
      named (the milestone-equivalence marker).
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def _meq_in_mq3(self):
        out = []
        for chapter in range(1, 15):
            for verse in range(1, 60):
                out.extend(
                    e for e in self.ec.for_verse("mq3", chapter, verse) if e.father == "Meqabyan (Ethiopian tradition)"
                )
        return out

    def _meq_in_mq3_chapter(self, chapter):
        out = []
        for verse in range(1, 60):
            out.extend(
                e for e in self.ec.for_verse("mq3", chapter, verse) if e.father == "Meqabyan (Ethiopian tradition)"
            )
        return out

    def _meq_in_book(self, book):
        out = []
        for chapter in range(1, 50):
            for verse in range(1, 60):
                out.extend(
                    e for e in self.ec.for_verse(book, chapter, verse) if e.father == "Meqabyan (Ethiopian tradition)"
                )
        return out

    def _all_meq(self):
        out = []
        for verse_entries in self.ec._by_verse.values():
            out.extend(e for e in verse_entries if e.father == "Meqabyan (Ethiopian tradition)")
        return out

    # ---- Per-voice + per-book density ----

    def test_mq3_substantively_detailed(self):
        mq3 = self._meq_in_mq3()
        assert len(mq3) >= 48, f"γ.4.8.D expected ≥48 Meqabyan entries on 3 Mq (8 seed + 40 detail); found {len(mq3)}"

    def test_meqabyan_milestone_at_third_detail_wave(self):
        meq = self._all_meq()
        assert len(meq) >= 160, (
            f"γ.4.8.D expected ≥160 Meqabyan entries total (40 seed + 40 mq1 + 40 mq2 + 40 mq3 = 160 — "
            f"PARITY with Athanasius 150); found {len(meq)}"
        )

    def test_all_previously_seeded_mq3_chapters_retained(self):
        # Regression-guard: seed chapters must still have their seed
        # entries after detail-wave ship.
        seed_chapters = [1, 2, 4, 10]
        per_chapter = {ch: len(self._meq_in_mq3_chapter(ch)) for ch in seed_chapters}
        empty = {ch: n for ch, n in per_chapter.items() if n < 1}
        assert not empty, f"γ.4.8.D regression: previously-seeded mq3 chapters must retain entries; empty: {empty}"

    def test_six_newly_opened_mq3_chapters_have_detail(self):
        # γ.4.8.D specifically opened 6 previously-seed-empty chapters.
        # Each must have ≥1 entry post-detail-wave.
        newly_opened = [3, 5, 6, 7, 8, 9]
        per_chapter = {ch: len(self._meq_in_mq3_chapter(ch)) for ch in newly_opened}
        empty = {ch: n for ch, n in per_chapter.items() if n < 1}
        assert not empty, f"γ.4.8.D opens 6 newly-empty chapters: each must have ≥1 entry; empty: {empty}"

    def test_mq3_full_10_chapter_coverage_achieved(self):
        # γ.4.8.D is the SECOND Mäqabyan wave to achieve 100% chapter
        # coverage of a Mäqabyan book (after γ.4.8.C achieved it on mq2).
        # Every chapter 1..10 must have ≥1 Meqabyan entry post-ship.
        # This is the arc-completion-depth invariant for 3 Mq.
        all_chapters = list(range(1, 11))
        per_chapter = {ch: len(self._meq_in_mq3_chapter(ch)) for ch in all_chapters}
        empty = {ch: n for ch, n in per_chapter.items() if n < 1}
        assert not empty, (
            f"γ.4.8.D: 3 Mq must reach 100% chapter coverage (10 of 10 chapters with ≥1 entry); empty: {empty}"
        )

    def test_meqabyan_trilogy_two_of_three_books_at_complete_coverage(self):
        # Cross-book invariant: post-γ.4.8.D, TWO OF THREE Mäqabyan books
        # are at 100% chapter coverage (mq2 21/21 from γ.4.8.C; mq3 10/10
        # from γ.4.8.D). mq1 remains at partial coverage (25/36 ~ 70%)
        # pending γ.4.8.E arc-close consideration.
        mq2 = self._meq_in_book("mq2")
        mq2_chapters_covered = {e.chapter for e in mq2}
        mq3 = self._meq_in_book("mq3")
        mq3_chapters_covered = {e.chapter for e in mq3}
        assert mq2_chapters_covered >= set(range(1, 22)), (
            f"γ.4.8.D trilogy-completion-state requires mq2 at 21/21 coverage "
            f"(γ.4.8.C invariant); got chapters {sorted(mq2_chapters_covered)}"
        )
        assert mq3_chapters_covered >= set(range(1, 11)), (
            f"γ.4.8.D trilogy-completion-state requires mq3 at 10/10 coverage "
            f"(this-ship invariant); got chapters {sorted(mq3_chapters_covered)}"
        )

    # ---- Signature passage pins (8 anchors) ----

    def test_mq3_1_22_protoevangelium_judgment_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq3", 1, 22) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.D missing mq3 1:22 — post-fall divine-judgment-pronouncement (Gen 3:14-15 Protoevangelium "
            "+ Ezk 28:16-19 king-of-Tyre/Satan-fall + Isa 14:15 + Rev 12:9 + 20:10 final-defeat)"
        )

    def test_mq3_2_15_angelic_replacement_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq3", 2, 15) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.D missing mq3 2:15 — angelic-replacement doctrine (Augustine Enchiridion §29 + Anselm Cur "
            "Deus Homo I.16-18 + Gregory Hom on the Gospels 34 + EOTC Mäṣḥafä Mälaʾek)"
        )

    def test_mq3_4_15_prov_8_reapplied_to_adam_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq3", 4, 15) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.D missing mq3 4:15 — PROV 8:22-30 REAPPLIED TO ADAM (Tier-3 interpretive-flagged per "
            "SOURCES.md §7; creative-midrashic-move vs standard Athanasian/Cyrillian Wisdom-Christology)"
        )

    def test_mq3_4_18_four_elements_adamic_anthropology_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq3", 4, 18) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.D missing mq3 4:18 — four-elements-Adamic-anthropology (Empedoclean/Galenic mediated via "
            "Syriac + Coptic patristic; Ephrem Carmina Nisibena 46 + Severus of Antioch Cathedral Homilies 21)"
        )

    def test_mq3_4_28_repentance_as_image_restoration_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq3", 4, 28) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.D missing mq3 4:28 — repentance-as-image-restoration (Rom 8:29 + 2 Cor 3:18 + Athanasius "
            "De Incarnatione 32 + 54 + Cyril of Alexandria Commentary on John 3 + 17)"
        )

    def test_mq3_5_1_charity_and_mercy_opens_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq3", 5, 1) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.D missing mq3 5:1 — OPENS Ch 5 (charity-and-mercy virtue-catalog following complete-"
            "repentance 4:34; Mt 5:7 + Mt 25:31-46 + Tobit 4:7-11 + EOTC seven-corporal-works-of-mercy)"
        )

    def test_mq3_7_7_humility_inverts_devils_pride_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq3", 7, 7) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.D missing mq3 7:7 — OPENS Ch 7 (humility-inverts-Devil's-pride: Mt 5:3 + Phil 2:5-11 "
            "kenosis-hymn + John Climacus Ladder Step 25; PREREQUISITE-CONDITION for complete-repentance)"
        )

    def test_mq3_10_29_triple_doxology_book_closing_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq3", 10, 29) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.D missing mq3 10:29 — TRIPLE-DOXOLOGY book-closing 'From today and unto eternity, Amen' "
            "(ከዛሬ ጀምሮ እስከ ዘለዓለም አሜን); completes 1 Mq 36:45 + 2 Mq 21:10 + 3 Mq 10:29 trilogy-of-book-"
            "closings — CHARACTERISTIC MEQABYAN BOOK-CLOSING SIGNATURE triply-attested across the trilogy"
        )

    # ---- _meta sync pin ----

    def test_meta_documents_gamma_4_8_d_expansion(self):
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_source = data["_meta"]["source"]
        assert "γ.4.8.D" in meta_source, "γ.4.8.D must be referenced in _meta.source"
        assert "detail" in meta_source.lower(), "γ.4.8.D _meta.source should name 'detail wave'"
        assert "mq3" in meta_source.lower() or "Mäqabyan III" in meta_source, (
            "γ.4.8.D _meta.source should name mq3 / Mäqabyan III"
        )
        assert "FOURTEENTH" in meta_source or "fourteenth" in meta_source, (
            "γ.4.8.D _meta.source should name this as the FOURTEENTH N-W4 verification"
        )
        assert "PARITY" in meta_source or "parity" in meta_source or "ATHANASIUS" in meta_source.upper(), (
            "γ.4.8.D _meta.source should name the parity-with-Athanasius milestone (160 vs 150)"
        )


class TestGamma48EMeqabyanArcClose:
    """γ.4.8.E — Mäṣḥafä Mäqabyan ARC-CLOSE wave (2026-05-14). 40 verse-
    keyed entries closing the FIVE-WAVE Mäqabyan-trilogy detail-wave
    family (γ.4.8 seed + γ.4.8.B + γ.4.8.C + γ.4.8.D + γ.4.8.E arc-
    close). **EIGHTH §8.1 ARC-CLOSE INSTANCE** in γ.4 corpus history
    (after γ.4.4.E Mäṣḥafä Hēnok + γ.4.5.E Mäṣḥafä Kufāle + γ.4.2.D
    Pentateuch + γ.4.3.D Cyril-on-Luke + γ.4.6.D Cyril-on-Matthew +
    γ.4.7.D Cyril-on-Mark + γ.4.9.D Athanasius). CLOSING WAVE of the
    SIXTH-and-final patristic/canonical voice arc in the γ.4 corpus.

    After this ship, ALL SIX γ.4 PATRISTIC/CANONICAL VOICES are at
    substantively-closed-arc depth:
        Cyril of Alexandria    668 entries (4 Gospel arcs closed)
        Jubilees               200 entries (arc closed γ.4.5.E)
        Meqabyan               200 entries (ARC CLOSED γ.4.8.E — THIS)
        1 Enoch                192 entries (arc closed γ.4.4.E)
        Ephrem the Syrian      157 entries (Pentateuch arc closed γ.4.2.D)
        Athanasius             150 entries (arc closed γ.4.9.D)
        ───────────────────────────
        Total γ.4 corpus      1567 entries (100% — all six voices closed)

    Distribution (40 entries across 14 chapters):
    - DEEPENING (6 entries across 3 seeded chapters): Ch 17 (+2), Ch
      30 (+2), Ch 36 (+2) — patristic-parallel deepening of SEEDED
      theological loci with CC0-text-grounded context.
    - OPENING (34 entries across 11 newly-empty chapters): Ch 1 (+4),
      Chs 20-27 (3 each = 24), Chs 31-32 (3 each = 6), Ch 35 (+3) —
      HOMILETIC-GENRE ANCHORS framed as patristic-parallel commentary
      per the source-fidelity convention codified at γ.4.8.D.

    Mq1 coverage post-γ.4.8.E: 36 of 36 chapters (100%) — completing
    the THIRD AND FINAL Mäqabyan book to 100% coverage. All three
    Mäqabyan books at 100% chapter coverage: 67/67 chapters.

    Per §8.1 the closing wave's test class MUST add the three specific
    pin types:

    (1) **PIN #1 — absolute-count milestone** at cumulative arc-close
        count. Per `feedback_share_pin_pattern` use COUNT not share —
        durable against future voice-broadening waves.

    (2) **PIN #2 — all_N_sections_covered exhaustiveness pin** asserting
        every section of the arc has substantive coverage at planned
        depth. The FIVE waves are:
            γ.4.8    seed              (40 entries across 3 Mäqabyan books)
            γ.4.8.B  Mäqabyan I detail (40 entries on mq1)
            γ.4.8.C  Mäqabyan II detail (40 entries on mq2)
            γ.4.8.D  Mäqabyan III detail (40 entries on mq3)
            γ.4.8.E  arc-close         (40 entries on mq1 closing to 36/36)
        Cumulative: 200 Meqabyan entries; 67/67 chapters across the
        entire trilogy (100% coverage).

    (3) **PIN #3 — _meta synchronization pin** asserting JSON _meta
        names every sub-phase tag (γ.4.8 + γ.4.8.B + γ.4.8.C + γ.4.8.D
        + γ.4.8.E) with regex word-boundary, AND records the "ARC
        CLOSED" status explicitly.

    (4) **Cyril-plurality trajectory pin** per ω.41 §1 durable safeguard:
        Cyril remains plurality-leader at arc-close (668 vs Meqabyan-
        or-Jubilees 200 = 3.34× next-single-father).

    Pins:
    - Mq1 substantively detailed (≥100 entries — 20 seed + 40 γ.4.8.B
      + 40 γ.4.8.E).
    - Mq1 100% chapter coverage (36/36 chapters with ≥1 entry).
    - **§8.1 ARC-CLOSE PIN #1 — count milestone:** Meqabyan absolute-
      count ≥200 entries (per feedback_share_pin_pattern — never a
      share-pin; durable against future voice-broadening).
    - **§8.1 ARC-CLOSE PIN #2 — all_N_sections_covered
      exhaustiveness:** test_all_five_meqabyan_waves_substantively_
      covered asserts γ.4.8 seed (≥40 across 3 books) + γ.4.8.B (mq1
      ≥40) + γ.4.8.C (mq2 ≥40) + γ.4.8.D (mq3 ≥40) + γ.4.8.E (mq1
      arc-close ≥40) — every section of the Mäqabyan arc has
      substantive coverage at planned depth.
    - **§8.1 ARC-CLOSE PIN #3 — _meta synchronization:** pin per sub-
      phase tag (γ.4.8, γ.4.8.B, γ.4.8.C, γ.4.8.D, γ.4.8.E) with
      regex word-boundary; arc-close status recorded explicitly.
    - **Cyril plurality preservation pin (ω.41 §1 trajectory rule):**
      Cyril remains single-father plurality-leader at arc-close (Cyril
      > Meqabyan AND Cyril > Jubilees AND Cyril > Athanasius).
    - **Mäqabyan-trilogy ALL-THREE-BOOKS-AT-100%-CHAPTER-COVERAGE pin:**
      cross-book invariant; the trilogy's-completion-state.
    - 8 signature-anchor pins covering the arc-close Tewahedo theology:
      mq1 1:1 Ṣiruṣaydan-introduction Tyre-Sidon-typology + mq1 17:6
      Sebelyanos=Beliar Christian-reception + mq1 20:1 martyr-cult-
      formation + mq1 22:7 Davidic-covenant Tewahedo-Solomonic-Kǝbrä-
      Nägäśt + mq1 24:7 false-vs-true-prophet criterion + mq1 27:7
      messianic-expectation comprehensive-prophetic-catalog + mq1
      30:21 Davidic-Solomonic covenant-honor application + mq1 36:49
      final-capstone-coda Psalter book-ending-doxologies architectural-
      parallel.

    With this class, the Mäqabyan arc is PINNED at closed-arc depth
    (the SIXTH and FINAL γ.4 patristic/canonical voice to reach arc-
    close). The §8.1 instance count reaches 8.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def _meq_in_book(self, book):
        out = []
        for chapter in range(1, 50):
            for verse in range(1, 60):
                out.extend(
                    e for e in self.ec.for_verse(book, chapter, verse) if e.father == "Meqabyan (Ethiopian tradition)"
                )
        return out

    def _meq_in_mq1_chapter(self, chapter):
        out = []
        for verse in range(1, 60):
            out.extend(
                e for e in self.ec.for_verse("mq1", chapter, verse) if e.father == "Meqabyan (Ethiopian tradition)"
            )
        return out

    def _all_meq(self):
        out = []
        for verse_entries in self.ec._by_verse.values():
            out.extend(e for e in verse_entries if e.father == "Meqabyan (Ethiopian tradition)")
        return out

    # ---- Mq1 100% coverage achievement ----

    def test_mq1_substantively_completed(self):
        mq1 = self._meq_in_book("mq1")
        assert len(mq1) >= 100, (
            f"γ.4.8.E arc-close expected ≥100 Meqabyan entries on 1 Mq (20 seed + 40 γ.4.8.B detail "
            f"+ 40 γ.4.8.E arc-close); found {len(mq1)}"
        )

    def test_mq1_full_36_chapter_coverage_achieved(self):
        # γ.4.8.E completes mq1 to 100% chapter coverage — making it
        # the THIRD AND FINAL Mäqabyan book to reach 100%.
        all_chapters = list(range(1, 37))
        per_chapter = {ch: len(self._meq_in_mq1_chapter(ch)) for ch in all_chapters}
        empty = {ch: n for ch, n in per_chapter.items() if n < 1}
        assert not empty, f"γ.4.8.E arc-close: mq1 must reach 100% chapter coverage (36 of 36 chapters); empty: {empty}"

    def test_eleven_newly_opened_mq1_chapters_at_arc_close(self):
        # γ.4.8.E opens the 11 chapters previously uncovered in mq1:
        # 1, 20, 21, 22, 23, 24, 26, 27, 31, 32, 35. Each must have ≥1 entry.
        newly_opened = [1, 20, 21, 22, 23, 24, 26, 27, 31, 32, 35]
        per_chapter = {ch: len(self._meq_in_mq1_chapter(ch)) for ch in newly_opened}
        empty = {ch: n for ch, n in per_chapter.items() if n < 1}
        assert not empty, f"γ.4.8.E opens 11 newly-empty mq1 chapters: each must have ≥1 entry; empty: {empty}"

    # ---- §8.1 ARC-CLOSE PIN #1: absolute-count milestone ----

    def test_meqabyan_arc_close_count_milestone(self):
        # §8.1 ARC-CLOSE PIN #1: absolute-count milestone at arc close.
        # Per feedback_share_pin_pattern: never a share pin. Cumulative
        # five-wave count: 40 (γ.4.8 seed) + 40 (γ.4.8.B) + 40 (γ.4.8.C)
        # + 40 (γ.4.8.D) + 40 (γ.4.8.E) = 200. ≥200 floor.
        meq = self._all_meq()
        assert len(meq) >= 200, (
            f"γ.4.8.E arc-close: Meqabyan count ≥200 expected "
            f"(cumulative five-wave arc-close milestone: 40 seed + 40 γ.4.8.B + "
            f"40 γ.4.8.C + 40 γ.4.8.D + 40 γ.4.8.E = 200; PARITY WITH JUBILEES); found {len(meq)}"
        )

    # ---- §8.1 ARC-CLOSE PIN #2: all_N_sections_covered exhaustiveness ----

    def test_all_five_meqabyan_waves_substantively_covered(self):
        # §8.1 ARC-CLOSE PIN #2: all_N_sections_covered exhaustiveness.
        # Every section of the Mäqabyan arc must have substantive
        # coverage at planned depth. The five waves are:
        # γ.4.8    seed              (40 across 3 Mäqabyan books)
        # γ.4.8.B  Mäqabyan I detail (40 on mq1)
        # γ.4.8.C  Mäqabyan II detail (40 on mq2)
        # γ.4.8.D  Mäqabyan III detail (40 on mq3)
        # γ.4.8.E  arc-close         (40 on mq1 closing to 36/36)
        mq1 = self._meq_in_book("mq1")
        mq2 = self._meq_in_book("mq2")
        mq3 = self._meq_in_book("mq3")

        # γ.4.8 + γ.4.8.B (20 seed + 40 detail) + γ.4.8.E (40 arc-close) on mq1
        assert len(mq1) >= 100, (
            f"γ.4.8.E arc-close: mq1 section below cumulative depth "
            f"(need ≥100 = 20 seed + 40 γ.4.8.B + 40 γ.4.8.E, have {len(mq1)})"
        )
        # γ.4.8 (12 seed) + γ.4.8.C (40 detail) on mq2 = 52
        assert len(mq2) >= 52, (
            f"γ.4.8.E arc-close: mq2 section below γ.4.8.C parity (need ≥52 = 12 seed + 40 γ.4.8.C, have {len(mq2)})"
        )
        # γ.4.8 (8 seed) + γ.4.8.D (40 detail) on mq3 = 48
        assert len(mq3) >= 48, (
            f"γ.4.8.E arc-close: mq3 section below γ.4.8.D parity (need ≥48 = 8 seed + 40 γ.4.8.D, have {len(mq3)})"
        )
        # Trilogy total
        meq_total = len(self._all_meq())
        assert meq_total >= 200, (
            f"γ.4.8.E arc-close: total Meqabyan ≥200 expected (five-wave cumulative); found {meq_total}"
        )

    def test_meqabyan_trilogy_all_three_books_at_complete_coverage(self):
        # The trilogy-completion-state cross-book invariant: ALL THREE
        # Mäqabyan books at 100% chapter coverage post-γ.4.8.E.
        # mq1 36/36 + mq2 21/21 + mq3 10/10 = 67/67 chapters.
        mq1_chapters = {e.chapter for e in self._meq_in_book("mq1")}
        mq2_chapters = {e.chapter for e in self._meq_in_book("mq2")}
        mq3_chapters = {e.chapter for e in self._meq_in_book("mq3")}

        assert mq1_chapters >= set(range(1, 37)), (
            f"γ.4.8.E trilogy-completion-state requires mq1 at 36/36 coverage; got {sorted(mq1_chapters)}"
        )
        assert mq2_chapters >= set(range(1, 22)), (
            f"γ.4.8.E trilogy-completion-state requires mq2 at 21/21 coverage; got {sorted(mq2_chapters)}"
        )
        assert mq3_chapters >= set(range(1, 11)), (
            f"γ.4.8.E trilogy-completion-state requires mq3 at 10/10 coverage; got {sorted(mq3_chapters)}"
        )

    # ---- §8.1 ARC-CLOSE PIN #3: _meta synchronization ----

    def test_meta_synchronization_at_meqabyan_arc_close(self):
        # §8.1 ARC-CLOSE PIN #3: _meta synchronization. Pin per sub-phase
        # tag with regex word-boundary so γ.4.8 doesn't match γ.4.8.B/C/D/E.
        import json
        import re
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        meta_source = json.loads(path.read_text(encoding="utf-8"))["_meta"]["source"]

        # Word-boundary regex for each sub-phase tag — prevents γ.4.8 from
        # matching γ.4.8.B (greedy substring would).
        for tag in ("γ.4.8", "γ.4.8.B", "γ.4.8.C", "γ.4.8.D", "γ.4.8.E"):
            pattern = re.compile(re.escape(tag) + r"(?![.\w])")
            assert pattern.search(meta_source), (
                f"γ.4.8.E arc-close: _meta.source must reference {tag} (five-wave arc-close synchronization pin)"
            )
        # Arc-close status explicit
        assert (
            "MEQABYAN ARC CLOSED" in meta_source or "Mäqabyan ARC CLOSED" in meta_source or "ARC CLOSED" in meta_source
        ), "γ.4.8.E _meta.source should explicitly mark Mäqabyan arc CLOSED"
        # EIGHTH §8.1 instance marker
        assert "EIGHTH" in meta_source or "eighth" in meta_source, (
            "γ.4.8.E _meta.source should name this as the EIGHTH §8.1 arc-close instance"
        )

    # ---- Cyril plurality preservation pin (ω.41 §1 trajectory rule) ----

    def test_cyril_remains_plurality_leader_at_meqabyan_arc_close(self):
        # ω.41 §1 trajectory rule: track Cyril's plurality position at
        # every threshold-crossing point. At γ.4.8.E arc-close, Cyril is
        # at 42.63% (668/1567) — sub-50% but still plurality at 3.34×
        # next-single-father (Jubilees + Meqabyan tied at 200). The
        # trajectory is documented in CHANGELOG / SESSION_STATE.
        cyril_count = 0
        jubilees_count = 0
        for verse_entries in self.ec._by_verse.values():
            for e in verse_entries:
                if e.father == "Cyril of Alexandria":
                    cyril_count += 1
                elif e.father.startswith("Jubilees"):
                    jubilees_count += 1
        meq_count = len(self._all_meq())
        # Cyril must remain plurality-leader (single-father with highest count)
        assert cyril_count > meq_count, (
            f"ω.41 §1: Cyril must remain plurality-leader over Meqabyan even at γ.4.8.E arc-close; "
            f"Cyril={cyril_count} vs Meqabyan={meq_count}"
        )
        assert cyril_count > jubilees_count, (
            f"ω.41 §1: Cyril must remain plurality-leader over Jubilees; "
            f"Cyril={cyril_count} vs Jubilees={jubilees_count}"
        )

    # ---- Signature passage pins (8 arc-close anchors) ----

    def test_mq1_1_1_siruseydan_introduction_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq1", 1, 1) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.E missing mq1 1:1 — OPENS Ch 1 Ṣiruṣaydan-introduction "
            "(Tyre-Sidon-typology cipher per Horovitz 1905 + Dillmann; the trilogy's villain enters)"
        )

    def test_mq1_17_6_sebelyanos_beliar_deepening_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq1", 17, 6) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.E missing mq1 17:6 — Sebelyanos=Beliar deepening "
            "(2 Cor 6:15 + Ascension of Isaiah 4 + Testaments of 12 Patriarchs Beliar-typology)"
        )

    def test_mq1_20_1_martyr_cult_formation_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq1", 20, 1) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.E missing mq1 20:1 — OPENS Ch 20 martyr-cult-formation "
            "(4 Macc 17:8-22 monumentalization + Tewahedo Sǝnkǝsar 1-August feast-day)"
        )

    def test_mq1_22_7_davidic_covenant_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq1", 22, 7) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.E missing mq1 22:7 — Davidic-covenant Tewahedo-Solomonic-dynasty anchor "
            "(2 Sam 7:8-17 + Kǝbrä Nägäśt Menelik-I-Solomonic-succession; key v1.1-publisher-uniqueness-angle)"
        )

    def test_mq1_24_7_true_vs_false_prophet_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq1", 24, 7) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.E missing mq1 24:7 — true-vs-false-prophet criterion "
            "(Deut 18:15-22 + Jer 28 + Athanasius CA I-III orthodox-doctrine-criterion)"
        )

    def test_mq1_27_7_messianic_expectation_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq1", 27, 7) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.E missing mq1 27:7 — messianic-expectation comprehensive-prophetic-catalog "
            "(Gen 49 + Isa 7-11+53 + Eusebius Demonstratio Evangelica patristic-catalog)"
        )

    def test_mq1_30_21_covenant_honor_davidic_solomonic_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq1", 30, 21) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.E missing mq1 30:21 — covenant-honor Davidic-Solomonic application "
            "(1 Sam 2:30 honor-formula extended via 1 Kgs 3 + Kǝbrä Nägäśt Tewahedo-Solomonic-dynasty)"
        )

    def test_mq1_36_49_final_capstone_coda_anchor_present(self):
        c = [e for e in self.ec.for_verse("mq1", 36, 49) if e.father == "Meqabyan (Ethiopian tradition)"]
        assert c, (
            "γ.4.8.E missing mq1 36:49 — final-capstone-coda Psalter book-ending-doxologies "
            "(Ps 41:13 + 72:18-19 + 89:52 + 106:48 — Psalter three-of-five book-ending-doxologies "
            "architectural-parallel anchoring the trilogy's BOOK-CLOSING SIGNATURE)"
        )

    # ---- _meta sync pin (extension of γ.4.8.D pattern) ----

    def test_meta_documents_gamma_4_8_e_arc_close(self):
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_source = data["_meta"]["source"]
        assert "γ.4.8.E" in meta_source, "γ.4.8.E must be referenced in _meta.source"
        assert "arc-close" in meta_source.lower() or "ARC-CLOSE" in meta_source or "ARC CLOSED" in meta_source, (
            "γ.4.8.E _meta.source should name arc-close"
        )
        assert "Mäqabyan" in meta_source or "Meqabyan" in meta_source, (
            "γ.4.8.E _meta.source should name Mäqabyan/Meqabyan"
        )
        assert "FIFTEENTH" in meta_source or "fifteenth" in meta_source, (
            "γ.4.8.E _meta.source should name this as the FIFTEENTH N-W4 verification"
        )
        assert "EIGHTH" in meta_source or "eighth" in meta_source, (
            "γ.4.8.E _meta.source should name this as the EIGHTH §8.1 arc-close instance"
        )


class TestGamma48FTier2AuditIntegration:
    """γ.4.8.F — Mäṣḥafä Mäqabyan Tier-2 audit integration (2026-05-14).
    POST-ARC-CLOSE APPARATUS REFINEMENT — 12 verse-keyed entries
    propagating the v3 CC0-translation bundle's TIER2_AUDIT.md library-
    source verification findings into the Meqabyan apparatus.

    Distribution (12 entries across 3 books):
    - **mq1 (5):** 1:5 Wright 1877 fully-verified + tripartite-witness
      corroboration; 11:3 Horovitz fn-3 corrected list (X 3, XI 9, XV 7,
      XXVI 10, XXVIII 5, XXXI 2, XXXII 1; 'XXX 1' dropped as OCR
      artifact); 15:8 Wright-vs-Frankfurt tripartite-vs-bipartite
      tension; 20:3 Budge Synaxarium vol. 2 Ṭǝr 21 + Ṭǝr 30 Abijā/Silä
      saint-dates route; 36:46 Cowley 1974b date-correction (JES 12,
      no. 1, January 1974, pp. 133-175, JSTOR 44324703).
    - **mq2 (3):** 1:3 Wright's Preface Meqabyan-vs-Vulgate-Maccabees
      external corroboration; 4:17 D'Abbadie no. 55 items 28-30 precise
      locator; 21:11 Tier-2-audit summary-anchor / apparatus-verification
      ledger.
    - **mq3 (4):** 1:17 Wright's Preface 'Liber Adami' (Conflict of
      Adam and Eve) attestation; 2:24 Andǝmta Psalter commentary
      printed-Amharic-book status; 4:17 Tier-3-interpretive-flagging
      stance confirmation; 10:30 Wright 'in three parts' + trilogy
      book-closing-signature Psalter-book-ending-doxologies external
      corroboration.

    Meqabyan voice 200 → 212; **MOVES TO SOLE 2ND-PLACE** surpassing
    Jubilees 200 (was tied at γ.4.8.E arc-close). Tewahedo-distinctive-
    canonical block 37.78% → 38.25% — STRONGEST POSITION IN γ.4 CORPUS
    HISTORY; directly supports the v1.1 publisher-led uniqueness-angle
    pick per memory `project_v1_terminus`.

    γ.4.8.E ARC CLOSED state is preserved as a REGRESSION-GUARDED
    INVARIANT — the 67/67 = 100% chapter coverage across mq1 + mq2 +
    mq3 must remain intact. γ.4.8.F layers Tier-2 findings as inline
    apparatus refinements without reopening or disturbing the closed-
    arc structure.

    Pins (sixteenth N-W4 idempotency verification):
    - Meqabyan ≥212 absolute-count milestone (γ.4.8.E 200 + γ.4.8.F 12).
    - mq1 ≥105 / mq2 ≥55 / mq3 ≥52 per-book floor-pins.
    - Arc-close 67/67 chapter-coverage regression-guard (γ.4.8.E
      invariant preserved).
    - 12 signature-anchor pins (one per Tier-2 finding) verifying each
      finding lands at its target verse with appropriate-content match.
    - Tier-2-substance-named pins (Wright 1877 + Cowley 1974b + Andǝmta
      Psalter + Senkessar Ṭǝr 21/30 + 'XXX 1' OCR-artifact-dropped) —
      ensures the substance of the Tier-2 audit is durably recorded in
      _meta beyond just the phase-tag.
    - Cyril plurality preservation per ω.41 §1 trajectory rule (Cyril
      668 still > Meqabyan 212 at 3.15× next-single-father).
    - Tewahedo-distinctive-canonical-block share-floor pin (≥38.0% per
      v1.1 publisher-uniqueness-angle anchor).
    - _meta synchronization pin for γ.4.8.F.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.ethiopian_commentaries.cache_clear()
        cls.ec = sources.ethiopian_commentaries()

    def _meq_in_book(self, book):
        out = []
        for chapter in range(1, 50):
            for verse in range(1, 60):
                out.extend(
                    e for e in self.ec.for_verse(book, chapter, verse) if e.father == "Meqabyan (Ethiopian tradition)"
                )
        return out

    def _meq_at(self, book, chapter, verse):
        return [e for e in self.ec.for_verse(book, chapter, verse) if e.father == "Meqabyan (Ethiopian tradition)"]

    def _all_meq(self):
        out = []
        for verse_entries in self.ec._by_verse.values():
            out.extend(e for e in verse_entries if e.father == "Meqabyan (Ethiopian tradition)")
        return out

    # ---- Absolute-count milestone (γ.4.8.E 200 + γ.4.8.F 12 = 212) ----

    def test_meqabyan_post_tier2_count_milestone(self):
        meq = self._all_meq()
        assert len(meq) >= 212, (
            f"γ.4.8.F Tier-2 integration: Meqabyan count ≥212 expected "
            f"(γ.4.8.E arc-close 200 + γ.4.8.F Tier-2 12 = 212; "
            f"Meqabyan moves to sole 2nd-place surpassing Jubilees 200); found {len(meq)}"
        )

    def test_mq1_post_tier2_floor(self):
        mq1 = self._meq_in_book("mq1")
        assert len(mq1) >= 105, (
            f"γ.4.8.F: mq1 ≥105 expected (γ.4.8.E arc-close 100 + γ.4.8.F 5 = 105); found {len(mq1)}"
        )

    def test_mq2_post_tier2_floor(self):
        mq2 = self._meq_in_book("mq2")
        assert len(mq2) >= 55, f"γ.4.8.F: mq2 ≥55 expected (γ.4.8.C completion 52 + γ.4.8.F 3 = 55); found {len(mq2)}"

    def test_mq3_post_tier2_floor(self):
        mq3 = self._meq_in_book("mq3")
        assert len(mq3) >= 52, f"γ.4.8.F: mq3 ≥52 expected (γ.4.8.D completion 48 + γ.4.8.F 4 = 52); found {len(mq3)}"

    # ---- Arc-close regression-guard: 67/67 chapter coverage preserved ----

    def test_arc_close_chapter_coverage_regression_guard(self):
        # γ.4.8.F must NOT disturb the γ.4.8.E arc-close invariant:
        # mq1 36/36 + mq2 21/21 + mq3 10/10 = 67/67 = 100%.
        def chapters_with_entries(book, total):
            out = set()
            for ch in range(1, total + 1):
                for v in range(1, 60):
                    if self._meq_at(book, ch, v):
                        out.add(ch)
                        break
            return out

        mq1_chs = chapters_with_entries("mq1", 36)
        mq2_chs = chapters_with_entries("mq2", 21)
        mq3_chs = chapters_with_entries("mq3", 10)
        assert mq1_chs == set(range(1, 37)), (
            f"γ.4.8.F must preserve γ.4.8.E 36/36 mq1 chapter-coverage; "
            f"missing mq1 chapters: {set(range(1, 37)) - mq1_chs}"
        )
        assert mq2_chs == set(range(1, 22)), (
            f"γ.4.8.F must preserve γ.4.8.C 21/21 mq2 chapter-coverage; "
            f"missing mq2 chapters: {set(range(1, 22)) - mq2_chs}"
        )
        assert mq3_chs == set(range(1, 11)), (
            f"γ.4.8.F must preserve γ.4.8.D 10/10 mq3 chapter-coverage; "
            f"missing mq3 chapters: {set(range(1, 11)) - mq3_chs}"
        )

    # ---- 12 signature-anchor pins (one per Tier-2 finding) ----

    def test_mq1_1_5_wright_1877_fully_verified_anchor(self):
        c = self._meq_at("mq1", 1, 5)
        assert c, "γ.4.8.F missing mq1 1:5 — Wright 1877 fully-verified anchor"
        assert any(
            "Wright" in (e.summary or "") and ("1877" in (e.summary or "") or "Catalogue" in (e.summary or ""))
            for e in c
        ), "γ.4.8.F mq1 1:5 should name Wright 1877 Catalogue (Tier-2 audit fully-verified)"

    def test_mq1_11_3_horovitz_fn3_corrected_list_anchor(self):
        c = self._meq_at("mq1", 11, 3)
        assert c, "γ.4.8.F missing mq1 11:3 — Horovitz fn-3 corrected list anchor"
        assert any("XXX 1" in (e.summary or "") and "OCR" in (e.summary or "") for e in c), (
            "γ.4.8.F mq1 11:3 should name 'XXX 1' OCR-artifact-dropped correction"
        )

    def test_mq1_15_8_wright_vs_frankfurt_tension_anchor(self):
        c = self._meq_at("mq1", 15, 8)
        assert c, "γ.4.8.F missing mq1 15:8 — Wright-vs-Frankfurt tripartite-vs-bipartite tension anchor"
        assert any("Frankfurt" in (e.summary or "") and "three parts" in (e.summary or "") for e in c), (
            "γ.4.8.F mq1 15:8 should name Frankfurt-Codex vs 'in three parts' tension"
        )

    def test_mq1_20_3_budge_synaxarium_anchor(self):
        c = self._meq_at("mq1", 20, 3)
        assert c, "γ.4.8.F missing mq1 20:3 — Budge Synaxarium Ṭǝr 21/30 anchor"
        assert any(
            "Budge" in (e.summary or "") and ("Ṭǝr 21" in (e.summary or "") or "Ṭǝr-21" in (e.summary or "")) for e in c
        ), "γ.4.8.F mq1 20:3 should name Budge Synaxarium Ṭǝr 21 saint-dates"

    def test_mq1_36_46_cowley_1974b_date_correction_anchor(self):
        c = self._meq_at("mq1", 36, 46)
        assert c, "γ.4.8.F missing mq1 36:46 — Cowley 1974b date-correction anchor"
        assert any("Cowley" in (e.summary or "") and "1974" in (e.summary or "") for e in c), (
            "γ.4.8.F mq1 36:46 should name Cowley 1974b date-correction"
        )
        assert any("44324703" in (e.summary or "") for e in c), (
            "γ.4.8.F mq1 36:46 should name JSTOR 44324703 stable URL"
        )

    def test_mq2_1_3_wright_meqabyan_vs_vulgate_anchor(self):
        c = self._meq_at("mq2", 1, 3)
        assert c, "γ.4.8.F missing mq2 1:3 — Wright Preface Meqabyan-vs-Vulgate distinction anchor"
        assert any("Vulgate" in (e.summary or "") and "Preface" in (e.summary or "") for e in c), (
            "γ.4.8.F mq2 1:3 should name Wright Preface Meqabyan-vs-Vulgate-Maccabees distinction"
        )

    def test_mq2_4_17_dabbadie_precise_locator_anchor(self):
        c = self._meq_at("mq2", 4, 17)
        assert c, "γ.4.8.F missing mq2 4:17 — D'Abbadie no. 55 items 28-30 anchor"
        assert any("Abbadie" in (e.summary or "") and "55" in (e.summary or "") for e in c), (
            "γ.4.8.F mq2 4:17 should name D'Abbadie Catalogue Raisonné no. 55"
        )

    def test_mq2_21_11_tier2_audit_ledger_anchor(self):
        c = self._meq_at("mq2", 21, 11)
        assert c, "γ.4.8.F missing mq2 21:11 — Tier-2 audit summary-ledger anchor"
        assert any("TIER-2" in (e.summary or "") and "translation body" in (e.summary or "").lower() for e in c), (
            "γ.4.8.F mq2 21:11 should reference Tier-2-audit and the no-translation-body-changes claim"
        )

    def test_mq3_1_17_wright_liber_adami_attestation_anchor(self):
        c = self._meq_at("mq3", 1, 17)
        assert c, "γ.4.8.F missing mq3 1:17 — Wright Preface 'Liber Adami' attestation anchor"
        assert any("Liber Adami" in (e.summary or "") and "Adambuch" in (e.summary or "") for e in c), (
            "γ.4.8.F mq3 1:17 should name Wright Preface 'Liber Adami' + Adambuch"
        )

    def test_mq3_2_24_andamta_psalter_printed_status_anchor(self):
        c = self._meq_at("mq3", 2, 24)
        assert c, "γ.4.8.F missing mq3 2:24 — Andǝmta Psalter printed-Amharic-book status anchor"
        assert any(
            ("Andǝmta" in (e.summary or "") or "Andemta" in (e.summary or ""))
            and "printed" in (e.summary or "").lower()
            for e in c
        ), "γ.4.8.F mq3 2:24 should name Andǝmta Psalter commentary printed-Amharic status"

    def test_mq3_4_17_tier3_interpretive_flagging_confirmed_anchor(self):
        c = self._meq_at("mq3", 4, 17)
        assert c, "γ.4.8.F missing mq3 4:17 — Tier-3-interpretive-flagging stance confirmation anchor"
        assert any("Prov 8" in (e.summary or "") and "Tier-3" in (e.summary or "") for e in c), (
            "γ.4.8.F mq3 4:17 should name Prov-8-reapplied-to-Adam Tier-3-interpretive-flag stability"
        )

    def test_mq3_10_30_wright_tripartite_psalter_doxologies_anchor(self):
        c = self._meq_at("mq3", 10, 30)
        assert c, "γ.4.8.F missing mq3 10:30 — Wright 'in three parts' + Psalter book-ending-doxologies anchor"
        assert any(
            "three parts" in (e.summary or "")
            and ("Psalter" in (e.summary or "") or "book-ending-doxolog" in (e.summary or "").lower())
            for e in c
        ), (
            "γ.4.8.F mq3 10:30 should name Wright 'in three parts' + Psalter-book-ending-doxologies architectural parallel"
        )

    # ---- Cyril plurality preservation per ω.41 §1 trajectory rule ----

    def test_cyril_plurality_preserved_post_tier2(self):
        all_entries = []
        for verse_entries in self.ec._by_verse.values():
            all_entries.extend(verse_entries)
        from collections import Counter

        counts = Counter(e.father for e in all_entries)
        cyril = counts.get("Cyril of Alexandria", 0)
        meq = counts.get("Meqabyan (Ethiopian tradition)", 0)
        jub = counts.get("Jubilees (Ethiopian tradition)", 0)
        enoch = counts.get("1 Enoch (Ethiopian tradition)", 0)
        eph = counts.get("Ephrem the Syrian", 0)
        ath = counts.get("Athanasius of Alexandria", 0)
        # Cyril must remain single-father plurality leader at sub-50% trajectory.
        assert cyril > meq, f"γ.4.8.F: Cyril {cyril} must remain > Meqabyan {meq} (ω.41 §1 trajectory)"
        assert cyril > jub, f"γ.4.8.F: Cyril {cyril} must remain > Jubilees {jub}"
        assert cyril > enoch, f"γ.4.8.F: Cyril {cyril} must remain > 1 Enoch {enoch}"
        assert cyril > eph, f"γ.4.8.F: Cyril {cyril} must remain > Ephrem {eph}"
        assert cyril > ath, f"γ.4.8.F: Cyril {cyril} must remain > Athanasius {ath}"
        # Cyril plurality remains ≥2× next-single-father (was 3.34× at γ.4.8.E
        # arc-close; post-γ.4.8.F is 3.15× — well above 2× threshold).
        next_father = max(meq, jub, enoch, eph, ath)
        assert cyril >= 2 * next_father, (
            f"γ.4.8.F: Cyril plurality must remain ≥2× next-single-father (Cyril {cyril} vs next {next_father})"
        )

    # ---- Tewahedo-distinctive-canonical block count-milestone pin ----

    def test_tewahedo_distinctive_canonical_block_count_milestone(self):
        # Mäṣḥafä Hēnok + Mäṣḥafä Kufāle + Mäqabyan = Tewahedo-distinctive-
        # canonical-block. Post-γ.4.8.F the block stood at 192 + 200 + 212 = 604.
        # mint-9 #6 (RULES §8.1): pin the ABSOLUTE COUNT, not a share. A
        # share-floor (the old `>= 0.38`) breaks mechanically whenever a later
        # voice-broadening wave dilutes the share even though the historical
        # achievement is preserved (memory `feedback_share_pin_pattern`). The
        # count milestone records the achievement durably and only ever grows.
        all_entries = []
        for verse_entries in self.ec._by_verse.values():
            all_entries.extend(verse_entries)
        from collections import Counter

        counts = Counter(e.father for e in all_entries)
        block = (
            counts.get("Meqabyan (Ethiopian tradition)", 0)
            + counts.get("Jubilees (Ethiopian tradition)", 0)
            + counts.get("1 Enoch (Ethiopian tradition)", 0)
        )
        assert block >= 600, (
            f"γ.4.8.F: Tewahedo-distinctive-canonical block count milestone ≥600 expected "
            f"(192+200+212=604 at the arc close; supports the v1.1 publisher-led "
            f"uniqueness-angle anchor, memory project_v1_terminus); got {block}"
        )

    # ---- Tier-2-substance-named pins on _meta ----

    def test_meta_documents_tier2_audit_substance(self):
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        path = repo / "content" / "sources" / "ethiopian_commentaries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        meta_source = data["_meta"]["source"]
        # γ.4.8.F phase tag must be named.
        assert "γ.4.8.F" in meta_source, "γ.4.8.F must be referenced in _meta.source"
        # The five concrete Tier-2-audit findings must each be substantively
        # named in _meta — these are the durable Tier-2 substance-pins.
        assert "Wright 1877" in meta_source, "γ.4.8.F _meta should name Wright 1877 Catalogue verification"
        assert "Cowley 1974b" in meta_source or "1974b" in meta_source, (
            "γ.4.8.F _meta should name Cowley 1974b date-correction"
        )
        assert "44324703" in meta_source, "γ.4.8.F _meta should name JSTOR 44324703 stable URL"
        assert "Andǝmta" in meta_source or "Andemta" in meta_source, (
            "γ.4.8.F _meta should name Andǝmta Psalter commentary status"
        )
        assert "Ṭǝr 21" in meta_source or "Ter 21" in meta_source, (
            "γ.4.8.F _meta should name Senkessar Ṭǝr 21 Abijā/Silä saint-dates route"
        )
        assert "Liber Adami" in meta_source, "γ.4.8.F _meta should name Wright Preface 'Liber Adami' attestation"
        # Tier-2 audit's no-translation-body-change claim must be named.
        assert (
            "NO TRANSLATION-TEXT CHANGES" in meta_source
            or "no translation-text" in meta_source.lower()
            or "no translation body" in meta_source.lower()
        ), "γ.4.8.F _meta should record the Tier-2 audit's no-translation-body-changes claim"
        # SIXTEENTH N-W4 verification phase ordinal
        assert "SIXTEENTH" in meta_source or "sixteenth" in meta_source, (
            "γ.4.8.F _meta should name this as the SIXTEENTH N-W4 verification"
        )
