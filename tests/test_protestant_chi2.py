"""χ.2 — Protestant commentary corpus + detector pins.

Topic file (created alongside the χ.2 ship). Mirrors γ.3 / γ.4 shape:
seed JSON validation + loader pins + detector contract + kinds.yaml
registration.

Coverage:
- TestChi2DataFile:                  the seed JSON parses, has the
  promised Matthew Henry entries, every entry carries full
  attribution and PD marker.
- TestChi2ProtestantCommentariesLoader: the loader indexes by verse
  + by commentator, returns frozen dataclass instances, surfaces
  SourceMissingError gracefully.
- TestChi2DetectorContract:          `ProtestantCommentaryDetector`
  emits the right Candidate shape; confidence 0.95; empty list for
  verses with no commentary; registered in ALL_DETECTORS *after*
  EthiopianCommentaryDetector so candidate ordering stays
  Father-canonical first / Tewahedo-distinctive second / English-
  Protestant third; body builder escapes HTML; plain year display
  (no BC/AD branching needed since all Protestant expositors are
  post-Reformation).
- TestChi2KindIsRegistered:          `comm-protestant` exists in
  `content/kinds.yaml` (added by χ.2 — distinct from the narrower
  `comm-reformation` for 16th c. magisterial Reformers); pin so a
  future kinds-cleanup doesn't drop it silently.
- TestChi2Coverage:                  seed entries span Genesis +
  Psalms + John, include the protoevangelium (Gen 3:15) and the
  total-depravity anchor (Gen 6:5) which are the load-bearing
  Reformed-Protestant pins for Matthew Henry's reading.

Pinning rationale: χ.2 opens the χ-commentary cluster for Protestant
expositors (Matthew Henry seed → χ.2.x full CCEL ETL). Drift in the
attribution format, the detector confidence, the protoevangelium /
total-depravity coverage, or the kind registration would break the
χ.2.x expansion pipeline silently.
"""

from __future__ import annotations


class TestChi2DataFile:
    """The seed JSON at content/sources/protestant_commentaries.json
    parses and carries the promised Matthew Henry entries."""

    @classmethod
    def setup_class(cls):
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        cls.path = repo / "content" / "sources" / "protestant_commentaries.json"
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
        # Buyer-facing claim: Henry died 1714, every entry is PD by
        # age. Pin _meta documents the death year + the standard PD
        # citation anchors (CCEL host).
        meta = self.data["_meta"]
        pd = meta["public_domain_basis"]
        assert "Matthew Henry" in pd
        assert "1714" in pd
        assert "CCEL" in pd or "Project Gutenberg" in pd or "Revell" in pd

    def test_has_entries_list(self):
        assert "entries" in self.data
        assert isinstance(self.data["entries"], list)
        assert len(self.data["entries"]) >= 12, "expected ≥12 seed entries for χ.2"

    def test_every_entry_has_required_fields(self):
        for entry in self.data["entries"]:
            for field in (
                "book",
                "chapter",
                "verse",
                "commentator",
                "work",
                "year",
                "summary",
                "attribution",
            ):
                assert field in entry, f"entry missing field {field!r}: {entry!r}"

    def test_every_entry_cites_pd_source(self):
        # Pin: every entry's attribution names Matthew Henry's
        # Exposition + carries the explicit "PD" marker.
        for entry in self.data["entries"]:
            attr = entry["attribution"]
            assert "Matthew Henry" in attr, f"entry not attributed to Henry: {attr!r}"
            assert "PD" in attr, f"entry attribution missing PD marker: {attr!r}"

    def test_every_entry_post_reformation(self):
        # All Protestant seed entries should be post-Reformation
        # (year > 1500). Matthew Henry's Exposition spans 1706-1721.
        # This pin guards against accidental cross-contamination
        # with the comm-reformation kind (Luther / Calvin / Zwingli
        # in the 16th c.).
        for entry in self.data["entries"]:
            year = int(entry["year"])
            assert year >= 1700, (
                f"entry year {year} predates Henry — should be in comm-reformation, not comm-protestant"
            )
            assert year <= 1721, (
                f"entry year {year} postdates Henry's death (1714 + posthumous completion through 1721)"
            )

    def test_genesis_1_1_present(self):
        # Canonical opening — buyers' first sanity-check verse.
        for entry in self.data["entries"]:
            if entry["book"] == "gen" and entry["chapter"] == 1 and entry["verse"] == 1:
                return
        raise AssertionError("seed corpus missing Gen 1:1")


class TestChi2ProtestantCommentariesLoader:
    """The loader class in `scripts.core.sources` indexes the JSON
    correctly + raises SourceMissingError on absent cache."""

    def test_loader_returns_frozen_dataclass_instances(self):
        from scripts.core import sources

        pc = sources.protestant_commentaries()
        entries = pc.for_verse("gen", 1, 1)
        assert entries, "Gen 1:1 should have at least one Protestant commentary"
        entry = entries[0]
        assert isinstance(entry, sources.ProtestantCommentary)
        import dataclasses

        assert dataclasses.is_dataclass(entry)
        for field_name in ("book", "chapter", "verse", "commentator", "work", "year", "summary", "attribution"):
            value = getattr(entry, field_name)
            assert value not in (None, "", 0), f"{field_name} unset"

    def test_dataclass_is_frozen(self):
        import dataclasses

        import pytest

        from scripts.core import sources

        pc = sources.protestant_commentaries()
        entry = pc.for_verse("gen", 1, 1)[0]

        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            entry.book = "exo"  # type: ignore[misc]

    def test_by_verse_lookup(self):
        from scripts.core import sources

        pc = sources.protestant_commentaries()
        gen11 = pc.for_verse("gen", 1, 1)
        assert len(gen11) >= 1
        assert all(e.book == "gen" and e.chapter == 1 and e.verse == 1 for e in gen11)

    def test_by_verse_empty_for_unknown(self):
        from scripts.core import sources

        pc = sources.protestant_commentaries()
        # Matthew 28:1 has no seed yet.
        empty = pc.for_verse("mat", 28, 1)
        assert empty == []

    def test_by_commentator_lookup(self):
        from scripts.core import sources

        pc = sources.protestant_commentaries()
        henry = pc.by_commentator("Matthew Henry")
        assert len(henry) >= 1, "Matthew Henry must appear in the seed (sole χ.2 expositor)"
        for entry in henry:
            assert entry.commentator == "Matthew Henry"

    def test_by_commentator_empty_for_unknown(self):
        from scripts.core import sources

        pc = sources.protestant_commentaries()
        empty = pc.by_commentator("Charles Spurgeon")  # χ.2.x candidate, not in seed
        assert empty == []

    def test_loader_handles_missing_cache(self, tmp_path, monkeypatch):
        from scripts.core import sources

        nope = tmp_path / "protestant_commentaries.json"
        monkeypatch.setattr(sources.ProtestantCommentaries, "PATH", nope)
        sources.protestant_commentaries.cache_clear()
        try:
            import pytest

            with pytest.raises(sources.SourceMissingError):
                sources.ProtestantCommentaries()
        finally:
            sources.protestant_commentaries.cache_clear()


class TestChi2DetectorContract:
    """`ProtestantCommentaryDetector` emits proper Candidates and
    is registered in `ALL_DETECTORS`."""

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.protestant_commentaries.cache_clear()

    def test_registered_in_all_detectors(self):
        from scripts.core import detectors

        assert detectors.ProtestantCommentaryDetector in detectors.ALL_DETECTORS, (
            "ProtestantCommentaryDetector missing from ALL_DETECTORS — prospect.py won't run it on the corpus"
        )

    def test_registered_after_ethiopian(self):
        # Ordering: χ.2 runs after γ.4 so the tradition-distinctive
        # Tewahedo entries get appended before the broader Protestant
        # English entries. Pin so a future cleanup doesn't reorder.
        from scripts.core import detectors

        detectors_list = list(detectors.ALL_DETECTORS)
        e_idx = detectors_list.index(detectors.EthiopianCommentaryDetector)
        p_idx = detectors_list.index(detectors.ProtestantCommentaryDetector)
        assert p_idx > e_idx, "Protestant detector must run after Ethiopian"

    def test_kind_is_comm_protestant(self):
        from scripts.core import detectors

        assert detectors.ProtestantCommentaryDetector.kind == "comm-protestant"

    def test_detect_returns_candidate_for_gen_1_1(self):
        from scripts.core import detectors

        d = detectors.ProtestantCommentaryDetector()
        candidates = d.detect("gen", 1, 1, "In the beginning God made heaven and earth.")
        assert candidates, "Gen 1:1 should produce at least one candidate"
        c = candidates[0]
        assert c.kind == "comm-protestant"
        assert c.book == "gen"
        assert c.chapter == 1
        assert c.verse == 1
        assert c.confidence == 0.95
        assert c.detector == "ProtestantCommentaryDetector"
        assert "<aside" in c.draft_body
        # Body is rendered with the note class for theme styling.
        assert "note-comm-protestant" in c.draft_body
        # Candidate title prefixes with the tradition name.
        assert c.draft_title.startswith("Protestant —")

    def test_detect_returns_empty_for_uncommented_verse(self):
        from scripts.core import detectors

        d = detectors.ProtestantCommentaryDetector()
        assert d.detect("rev", 1, 1, "") == []  # nothing in seed for Revelation
        assert d.detect("gen", 50, 1, "") == []

    def test_detect_ignores_verse_text(self):
        from scripts.core import detectors

        d = detectors.ProtestantCommentaryDetector()
        a = d.detect("gen", 1, 1, "real verse text")
        b = d.detect("gen", 1, 1, "completely different placeholder")
        assert len(a) == len(b)

    def test_body_is_html_escaped(self):
        from scripts.core import detectors
        from scripts.core.sources import ProtestantCommentary

        synthetic = ProtestantCommentary(
            book="gen",
            chapter=1,
            verse=1,
            commentator="<TestCommentator>",
            work="<TestWork>",
            year=1710,
            summary="<script>alert(1)</script>",
            attribution="Test, PD.",
        )
        body = detectors.ProtestantCommentaryDetector._format_body(synthetic)
        assert "<script>" not in body, "summary not escaped — XSS risk"
        assert "&lt;script&gt;" in body
        assert "&lt;TestCommentator&gt;" in body

    def test_body_renders_plain_year(self):
        # All Protestant expositors are post-Reformation (1500+). No
        # BC/AD branching needed — pin plain year display.
        from scripts.core import detectors
        from scripts.core.sources import ProtestantCommentary

        synthetic = ProtestantCommentary(
            book="gen",
            chapter=1,
            verse=1,
            commentator="Matthew Henry",
            work="Test",
            year=1710,
            summary="Test.",
            attribution="Henry, PD.",
        )
        body = detectors.ProtestantCommentaryDetector._format_body(synthetic)
        assert "1710" in body
        # No era marker — distinct from γ.4 which renders BC/AD.
        assert "AD" not in body
        assert "BC" not in body


class TestChi2KindIsRegistered:
    """The `comm-protestant` kind was added by χ.2 to `content/kinds.yaml`
    as a sibling of (not replacement for) `comm-reformation`. Pin its
    presence + structure so a future kinds-cleanup doesn't drop it
    silently, and so a future contributor doesn't accidentally fold
    Henry into the narrower comm-reformation kind."""

    def test_comm_protestant_kind_present_in_yaml(self):
        from pathlib import Path

        import yaml

        repo = Path(__file__).resolve().parent.parent
        kinds_path = repo / "content" / "kinds.yaml"
        data = yaml.safe_load(kinds_path.read_text(encoding="utf-8"))
        codes = {k["code"] for k in data["kinds"]}
        assert "comm-protestant" in codes, "comm-protestant kind missing from kinds.yaml"

    def test_comm_protestant_kind_has_expected_category(self):
        from pathlib import Path

        import yaml

        repo = Path(__file__).resolve().parent.parent
        kinds_path = repo / "content" / "kinds.yaml"
        data = yaml.safe_load(kinds_path.read_text(encoding="utf-8"))
        kind = next(k for k in data["kinds"] if k["code"] == "comm-protestant")
        assert kind["category"] == "comm"
        # Label must remain "Protestant" — that's what the popup
        # heading + audit grouping rely on.
        assert kind.get("label") == "Protestant"

    def test_comm_protestant_is_distinct_from_comm_reformation(self):
        # Both kinds exist as siblings (not a rename / merge). Drift
        # check: if a future contributor folds them, this fails loud.
        from pathlib import Path

        import yaml

        repo = Path(__file__).resolve().parent.parent
        kinds_path = repo / "content" / "kinds.yaml"
        data = yaml.safe_load(kinds_path.read_text(encoding="utf-8"))
        codes = {k["code"] for k in data["kinds"]}
        assert "comm-protestant" in codes
        assert "comm-reformation" in codes, "comm-reformation must coexist as the narrower 16th c. magisterial kind"


class TestChi2Coverage:
    """The seed has the breadth the Reformed-Protestant tradition
    requires: Genesis + Psalms + John, plus the protoevangelium
    (Gen 3:15) and the total-depravity anchor (Gen 6:5) — the two
    most load-bearing pins for Matthew Henry's reading."""

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        cls.pc = sources.protestant_commentaries()

    def test_genesis_covered(self):
        # Generators span Gen 1-6 in the seed.
        found = False
        for chapter in range(1, 12):
            for verse in range(1, 50):
                if self.pc.for_verse("gen", chapter, verse):
                    found = True
                    break
            if found:
                break
        assert found, "seed has no Genesis entries"

    def test_psalms_covered(self):
        # Psalm 1 + 23 included.
        assert self.pc.for_verse("ps", 1, 1)
        assert self.pc.for_verse("ps", 23, 1)

    def test_john_covered(self):
        # John 1:1 + 1:14 + 19:34 included.
        assert self.pc.for_verse("joh", 1, 1)
        assert self.pc.for_verse("joh", 1, 14)
        assert self.pc.for_verse("joh", 19, 34)

    def test_protoevangelium_present(self):
        # Gen 3:15 is THE Reformed pin — first promise of the Messiah,
        # signature Henry passage. Its presence is load-bearing for
        # the χ.2 Protestant-tradition coverage claim.
        assert self.pc.for_verse("gen", 3, 15), (
            "seed corpus missing Gen 3:15 — protoevangelium is load-bearing for Reformed reading"
        )

    def test_total_depravity_anchor_present(self):
        # Gen 6:5 is the Reformed proof-text for total depravity
        # (every / only / continually). Pin its inclusion so the
        # χ.2.x expansion preserves it.
        assert self.pc.for_verse("gen", 6, 5), (
            "seed corpus missing Gen 6:5 — total-depravity anchor is load-bearing for Reformed reading"
        )

    def test_henry_only_expositor_in_seed(self):
        # χ.2 ships a Matthew-Henry-only seed; χ.2.x will add
        # Spurgeon / Edwards / Hodge. Pin Henry is the sole seed
        # voice so an accidental future merge with another corpus
        # doesn't silently pass.
        commentators = set()
        for chapter in range(1, 200):
            for verse in range(1, 200):
                for book in ("gen", "exo", "ps", "joh", "mat", "rom"):
                    for entry in self.pc.for_verse(book, chapter, verse):
                        commentators.add(entry.commentator)
        assert commentators == {"Matthew Henry"}, f"χ.2 seed should be Matthew Henry only; found {commentators!r}"
