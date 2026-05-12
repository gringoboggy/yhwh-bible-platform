"""χ.4 — Catholic (Catena Aurea) commentary corpus + detector pins.

Topic file (created alongside the χ.4 ship). Mirrors γ.3 / γ.4 / χ.2:
seed JSON validation + loader pins + detector contract + kinds.yaml
registration.

Coverage:
- TestChi4DataFile:                  the seed JSON parses, has the
  promised Catena Aurea entries from Aquinas-curated Fathers, every
  entry carries full attribution and "Catena Aurea" provenance string.
- TestChi4CatholicCommentariesLoader: the loader indexes by verse +
  by father, returns frozen dataclass instances, surfaces
  SourceMissingError gracefully.
- TestChi4DetectorContract:          `CatholicCommentaryDetector`
  emits the right Candidate shape; confidence 0.95; empty list for
  verses with no commentary; registered in ALL_DETECTORS *after*
  ProtestantCommentaryDetector so candidate ordering follows the
  γ.3 → γ.4 → χ.2 → χ.4 lineage (patristic → tewahedo → protestant →
  catholic); body builder escapes HTML; BC/AD-aware year display
  (mirrors γ.4's pattern since some Catena Fathers like Origen sit
  near the AD transition).
- TestChi4KindIsRegistered:          `comm-catholic` exists in
  `content/kinds.yaml` (pre-existed; χ.4 is the first phase to
  emit it). Pin so a future kinds-cleanup doesn't drop it silently.
- TestChi4Coverage:                  seed entries span all four
  Gospels (Matthew + Mark + Luke + John); include the signature
  Catholic anchor (Mt 16:18 "Tu es Petrus"); include ≥1 Augustine
  entry (Catena's heaviest voice) and ≥1 Chrysostom entry (the
  Greek balance).

Pinning rationale: χ.4 opens the Catena Aurea commentary track for
Catholic / Anglican-BCP editions. Drift in the attribution format
(every entry must mention "Catena Aurea"), the detector confidence,
the four-Gospel coverage, the "Tu es Petrus" papal-primacy pin, or
the kind registration would break the χ.4.x expansion pipeline
silently.
"""

from __future__ import annotations


class TestChi4DataFile:
    """The seed JSON at content/sources/catholic_commentaries.json
    parses and carries the promised Aquinas-curated Catena Aurea
    entries."""

    @classmethod
    def setup_class(cls):
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        cls.path = repo / "content" / "sources" / "catholic_commentaries.json"
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
        # Pin: _meta documents Aquinas (d. 1274) + the Newman/Pusey
        # Oxford 1841-1845 translation as the PD anchors. Both
        # translator and source author predate every PD cutoff.
        meta = self.data["_meta"]
        pd = meta["public_domain_basis"]
        assert "Aquinas" in pd
        assert "1274" in pd
        assert "Newman" in pd
        assert "1841" in pd or "1845" in pd

    def test_meta_names_catena_aurea(self):
        # Pin: _meta declares the source IS the Catena Aurea (not a
        # generic patristic compilation). This is what distinguishes
        # χ.4 from γ.3.
        meta = self.data["_meta"]
        assert "Catena Aurea" in meta["source"]

    def test_has_entries_list(self):
        assert "entries" in self.data
        assert isinstance(self.data["entries"], list)
        assert len(self.data["entries"]) >= 12, "expected ≥12 seed entries for χ.4"

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

    def test_every_entry_cites_catena_aurea(self):
        # Pin: every entry's attribution mentions "Catena Aurea" so
        # downstream consumers can tell the comm-catholic note's
        # provenance is Aquinas's compilation, not a freestanding
        # patristic source.
        for entry in self.data["entries"]:
            attr = entry["attribution"]
            assert "Catena Aurea" in attr, f"entry not attributed to Catena Aurea: {attr!r}"
            assert "PD" in attr, f"entry attribution missing PD marker: {attr!r}"

    def test_every_entry_gospel_only(self):
        # Pin: Catena Aurea is Gospels-only per Aquinas's original
        # scope (Mt / Mk / Lk / Jn). A future χ.4.x adding non-Gospel
        # content would need a different source corpus.
        gospel_codes = {"mat", "mar", "luk", "joh"}
        for entry in self.data["entries"]:
            assert entry["book"] in gospel_codes, (
                f"entry book {entry['book']!r} is not a Gospel — Catena Aurea is Gospels-only"
            )

    def test_matthew_1_1_present(self):
        # Canonical opening of Matthew — buyers' first sanity-check verse.
        for entry in self.data["entries"]:
            if entry["book"] == "mat" and entry["chapter"] == 1 and entry["verse"] == 1:
                return
        raise AssertionError("seed corpus missing Matthew 1:1")


class TestChi4CatholicCommentariesLoader:
    """The loader class in `scripts.core.sources` indexes the JSON
    correctly + raises SourceMissingError on absent cache."""

    def test_loader_returns_frozen_dataclass_instances(self):
        from scripts.core import sources

        cc = sources.catholic_commentaries()
        entries = cc.for_verse("mat", 1, 1)
        assert entries, "Mt 1:1 should have at least one Catena entry"
        entry = entries[0]
        assert isinstance(entry, sources.CatholicCommentary)
        import dataclasses

        assert dataclasses.is_dataclass(entry)
        for field_name in ("book", "chapter", "verse", "father", "work", "year", "summary", "attribution"):
            value = getattr(entry, field_name)
            assert value not in (None, "", 0), f"{field_name} unset"

    def test_dataclass_is_frozen(self):
        import dataclasses

        import pytest

        from scripts.core import sources

        cc = sources.catholic_commentaries()
        entry = cc.for_verse("mat", 1, 1)[0]

        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            entry.book = "mar"  # type: ignore[misc]

    def test_by_verse_lookup(self):
        from scripts.core import sources

        cc = sources.catholic_commentaries()
        mat11 = cc.for_verse("mat", 1, 1)
        assert len(mat11) >= 1
        assert all(e.book == "mat" and e.chapter == 1 and e.verse == 1 for e in mat11)

    def test_by_verse_empty_for_non_gospel(self):
        from scripts.core import sources

        cc = sources.catholic_commentaries()
        # Genesis 1:1 has nothing — Catena Aurea is Gospels-only.
        empty = cc.for_verse("gen", 1, 1)
        assert empty == []
        # Acts 1:1 also empty for the same reason (Aquinas's Catena
        # excludes Acts even though it's a New Testament book).
        empty2 = cc.for_verse("act", 1, 1)
        assert empty2 == []

    def test_by_father_lookup_augustine(self):
        # Augustine is the Catena's heaviest single voice — pin he
        # appears at least once.
        from scripts.core import sources

        cc = sources.catholic_commentaries()
        augustine = cc.by_father("Augustine")
        assert len(augustine) >= 1, "Augustine must appear in the seed (Catena's heaviest voice)"
        for entry in augustine:
            assert entry.father == "Augustine"

    def test_by_father_empty_for_unknown(self):
        from scripts.core import sources

        cc = sources.catholic_commentaries()
        empty = cc.by_father("Martin Luther")  # not a Catena voice
        assert empty == []

    def test_loader_handles_missing_cache(self, tmp_path, monkeypatch):
        from scripts.core import sources

        nope = tmp_path / "catholic_commentaries.json"
        monkeypatch.setattr(sources.CatholicCommentaries, "PATH", nope)
        sources.catholic_commentaries.cache_clear()
        try:
            import pytest

            with pytest.raises(sources.SourceMissingError):
                sources.CatholicCommentaries()
        finally:
            sources.catholic_commentaries.cache_clear()


class TestChi4DetectorContract:
    """`CatholicCommentaryDetector` emits proper Candidates and
    is registered in `ALL_DETECTORS`."""

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.catholic_commentaries.cache_clear()

    def test_registered_in_all_detectors(self):
        from scripts.core import detectors

        assert detectors.CatholicCommentaryDetector in detectors.ALL_DETECTORS, (
            "CatholicCommentaryDetector missing from ALL_DETECTORS — prospect.py won't run it"
        )

    def test_registered_after_protestant(self):
        # Ordering: χ.4 runs after χ.2 so the candidate-order lineage
        # stays γ.3 → γ.4 → χ.2 → χ.4 (patristic → tewahedo →
        # protestant → catholic). Pin so a future cleanup doesn't
        # reorder.
        from scripts.core import detectors

        detectors_list = list(detectors.ALL_DETECTORS)
        p_idx = detectors_list.index(detectors.ProtestantCommentaryDetector)
        c_idx = detectors_list.index(detectors.CatholicCommentaryDetector)
        assert c_idx > p_idx, "Catholic detector must run after Protestant"

    def test_kind_is_comm_catholic(self):
        from scripts.core import detectors

        assert detectors.CatholicCommentaryDetector.kind == "comm-catholic"

    def test_detect_returns_candidate_for_mat_1_1(self):
        from scripts.core import detectors

        d = detectors.CatholicCommentaryDetector()
        candidates = d.detect("mat", 1, 1, "The book of the generation of Jesus Christ...")
        assert candidates, "Mt 1:1 should produce at least one candidate"
        c = candidates[0]
        assert c.kind == "comm-catholic"
        assert c.book == "mat"
        assert c.chapter == 1
        assert c.verse == 1
        assert c.confidence == 0.95
        assert c.detector == "CatholicCommentaryDetector"
        assert "<aside" in c.draft_body
        # Body is rendered with the note class for theme styling.
        assert "note-comm-catholic" in c.draft_body
        # Candidate title prefixes with the tradition name + Catena marker.
        assert c.draft_title.startswith("Catholic (Catena Aurea) —")
        # Label declares "via Catena Aurea" so downstream UIs can chip it.
        assert "via Catena Aurea" in c.draft_label

    def test_detect_returns_empty_for_uncommented_verse(self):
        from scripts.core import detectors

        d = detectors.CatholicCommentaryDetector()
        # Genesis is OT — Catena Aurea is Gospels-only.
        assert d.detect("gen", 1, 1, "") == []
        # Revelation isn't in the Catena even though it's NT.
        assert d.detect("rev", 1, 1, "") == []

    def test_detect_ignores_verse_text(self):
        from scripts.core import detectors

        d = detectors.CatholicCommentaryDetector()
        a = d.detect("mat", 1, 1, "real verse text")
        b = d.detect("mat", 1, 1, "completely different placeholder")
        assert len(a) == len(b)

    def test_body_is_html_escaped(self):
        from scripts.core import detectors
        from scripts.core.sources import CatholicCommentary

        synthetic = CatholicCommentary(
            book="mat",
            chapter=1,
            verse=1,
            father="<TestFather>",
            work="<TestWork>",
            year=400,
            summary="<script>alert(1)</script>",
            attribution="Test, Catena Aurea, PD.",
        )
        body = detectors.CatholicCommentaryDetector._format_body(synthetic)
        assert "<script>" not in body, "summary not escaped — XSS risk"
        assert "&lt;script&gt;" in body
        assert "&lt;TestFather&gt;" in body

    def test_body_renders_ad_for_post_christian_year(self):
        # Augustine (415 AD) — pin AD rendering.
        from scripts.core import detectors
        from scripts.core.sources import CatholicCommentary

        synthetic = CatholicCommentary(
            book="mat",
            chapter=1,
            verse=1,
            father="Augustine",
            work="Test",
            year=415,
            summary="Test.",
            attribution="Catena Aurea, PD.",
        )
        body = detectors.CatholicCommentaryDetector._format_body(synthetic)
        assert "415 AD" in body
        assert "BC" not in body


class TestChi4KindIsRegistered:
    """The `comm-catholic` kind is in `content/kinds.yaml`. It pre-
    existed (anticipated by the kinds-v2 schema); χ.4 is the first
    phase to actually emit this kind. Pin its presence so a future
    kinds-cleanup doesn't drop it silently."""

    def test_comm_catholic_kind_present_in_yaml(self):
        from pathlib import Path

        import yaml

        repo = Path(__file__).resolve().parent.parent
        kinds_path = repo / "content" / "kinds.yaml"
        data = yaml.safe_load(kinds_path.read_text(encoding="utf-8"))
        codes = {k["code"] for k in data["kinds"]}
        assert "comm-catholic" in codes, "comm-catholic kind missing from kinds.yaml"

    def test_comm_catholic_kind_has_expected_category(self):
        from pathlib import Path

        import yaml

        repo = Path(__file__).resolve().parent.parent
        kinds_path = repo / "content" / "kinds.yaml"
        data = yaml.safe_load(kinds_path.read_text(encoding="utf-8"))
        kind = next(k for k in data["kinds"] if k["code"] == "comm-catholic")
        assert kind["category"] == "comm"
        # Label must remain "Catholic" — that's what the popup heading
        # + the audit grouping rely on.
        assert kind.get("label") == "Catholic"


class TestChi4Coverage:
    """The seed has the breadth the Catena Aurea requires: all four
    Gospels, the signature Catholic anchor (Mt 16:18 "Tu es Petrus"),
    and the Catena's two heaviest voices (Augustine + Chrysostom)."""

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        cls.cc = sources.catholic_commentaries()

    def test_matthew_covered(self):
        # Matthew 1:1 (genealogy) + 5:3 (Beatitudes) + 16:18 (papal
        # primacy) + 27:46 (cry from the cross) — pin Matthew breadth.
        assert self.cc.for_verse("mat", 1, 1)
        assert self.cc.for_verse("mat", 5, 3)
        assert self.cc.for_verse("mat", 27, 46)

    def test_mark_covered(self):
        # Mark 1:1 (Gospel beginning) + 16:15 (Great Commission).
        assert self.cc.for_verse("mar", 1, 1)
        assert self.cc.for_verse("mar", 16, 15)

    def test_luke_covered(self):
        # Luke 1:46 (Magnificat) + 2:14 (Gloria) + 24:13 (Emmaus).
        assert self.cc.for_verse("luk", 1, 46)
        assert self.cc.for_verse("luk", 2, 14)
        assert self.cc.for_verse("luk", 24, 13)

    def test_john_covered(self):
        # John 1:1 (Logos prologue) + 1:14 (Incarnation) + 20:28
        # (Thomas's confession).
        assert self.cc.for_verse("joh", 1, 1)
        assert self.cc.for_verse("joh", 1, 14)
        assert self.cc.for_verse("joh", 20, 28)

    def test_tu_es_petrus_present(self):
        # Mt 16:18 "Thou art Peter and upon this rock I will build
        # my Church" is THE Catholic exegetical pin — papal primacy
        # anchor. Its presence in the seed is load-bearing for the
        # χ.4 Catholic-tradition coverage claim.
        assert self.cc.for_verse("mat", 16, 18), (
            "seed corpus missing Mt 16:18 — 'Tu es Petrus' is the load-bearing Catholic anchor"
        )

    def test_augustine_present(self):
        # Augustine is the Catena's heaviest single voice.
        augustine = self.cc.by_father("Augustine")
        assert len(augustine) >= 1, "Augustine must appear (Catena's heaviest voice)"

    def test_chrysostom_present(self):
        # Chrysostom is the Catena's Greek balance to Augustine's Latin.
        chrysostom = self.cc.by_father("John Chrysostom")
        assert len(chrysostom) >= 1, "Chrysostom must appear (Catena's Greek balance)"

    def test_jerome_present(self):
        # Jerome wrote the standard Catholic Vulgate AND a Matthew
        # commentary that Aquinas drew heavily from. Pin Jerome's
        # appearance for tradition completeness.
        jerome = self.cc.by_father("Jerome")
        assert len(jerome) >= 1, "Jerome must appear (Latin Vulgate translator + Catena Matthew anchor)"
