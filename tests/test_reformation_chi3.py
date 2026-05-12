"""χ.3 — Reformation (Calvin) commentary corpus + detector pins.

Topic file (created alongside the χ.3 ship). Mirrors γ.3 / γ.4 /
χ.2 / χ.4: seed JSON validation + loader pins + detector contract +
kinds.yaml registration.

Coverage:
- TestChi3DataFile:                  the seed JSON parses, has the
  promised Calvin entries, every entry carries full attribution and
  Calvin Translation Society provenance.
- TestChi3ReformationCommentariesLoader: the loader indexes by verse +
  by commentator, returns frozen dataclass instances, surfaces
  SourceMissingError gracefully.
- TestChi3DetectorContract:          `ReformationCommentaryDetector`
  emits the right Candidate shape; confidence 0.95; empty list for
  verses with no commentary; registered in ALL_DETECTORS *after*
  CatholicCommentaryDetector so candidate ordering follows the
  γ.3 → γ.4 → χ.2 → χ.4 → χ.3 lineage; body builder escapes HTML;
  plain year display (mirrors χ.2 — all magisterial Reformers
  post-1500, no BC/AD branching needed).
- TestChi3KindIsRegistered:          `comm-reformation` exists in
  `content/kinds.yaml` (pre-existed; χ.3 is the first phase to
  emit it). Pin so a future kinds-cleanup doesn't drop it silently.
- TestChi3Coverage:                  seed entries span Old + New
  Testament (both halves of Calvin's commentary coverage); pin the
  signature Reformed anchors — sola fide (Rom 3:21 + Gal 2:16),
  sola gratia (Eph 2:8), accommodation (Gen 1:1), idolatry
  (Exo 20:3), providence (Rom 8:28), covenant theology (Jer 31:33);
  Calvin is sole seed voice (χ.3.x adds Luther / Zwingli).

Pinning rationale: χ.3 closes the 3rd of 4 χ-commentary cluster seeds
(χ.2 + χ.4 + χ.3 shipped; χ.5 Rashi remains). Drift in the year-range
(pin against accidental merge with χ.2 comm-protestant 1700-1721),
the sola fide / sola gratia coverage, or the kind registration
would break the χ.3.x expansion pipeline silently.
"""

from __future__ import annotations


class TestChi3DataFile:
    """The seed JSON at content/sources/reformation_commentaries.json
    parses and carries the promised Calvin entries."""

    @classmethod
    def setup_class(cls):
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        cls.path = repo / "content" / "sources" / "reformation_commentaries.json"
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
        # Pin: _meta documents Calvin (d. 1564) + the Calvin
        # Translation Society Edinburgh 1843-1855 translation as
        # the PD anchors. Both source author and translators predate
        # every PD cutoff.
        meta = self.data["_meta"]
        pd = meta["public_domain_basis"]
        assert "Calvin" in pd
        assert "1564" in pd
        assert "Calvin Translation Society" in pd or "Edinburgh" in pd

    def test_has_entries_list(self):
        assert "entries" in self.data
        assert isinstance(self.data["entries"], list)
        assert len(self.data["entries"]) >= 12, "expected ≥12 seed entries for χ.3"

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

    def test_every_entry_cites_calvin_translation_society(self):
        # Pin: every entry's attribution names the Calvin Translation
        # Society edition + carries the explicit "PD" marker.
        for entry in self.data["entries"]:
            attr = entry["attribution"]
            assert "Calvin" in attr, f"entry not attributed to Calvin: {attr!r}"
            assert "PD" in attr, f"entry attribution missing PD marker: {attr!r}"

    def test_every_entry_in_calvin_lifetime(self):
        # All Reformation seed entries should be within Calvin's
        # commentary period (1540 = Calvin's first published commentary
        # on Romans; 1564 = Calvin's death). This pin guards against
        # accidental cross-contamination with χ.2's comm-protestant
        # kind (1700-1721 Matthew Henry range) and against post-
        # Calvin Reformers being added without an explicit χ.3.x phase.
        for entry in self.data["entries"]:
            year = int(entry["year"])
            assert year >= 1540, f"entry year {year} predates Calvin's commentary period (1540 Romans onward)"
            assert year <= 1564, f"entry year {year} postdates Calvin's death (1564) — should be a new χ.3.x phase"

    def test_genesis_1_1_present(self):
        # Canonical opening — buyers' first sanity-check verse.
        for entry in self.data["entries"]:
            if entry["book"] == "gen" and entry["chapter"] == 1 and entry["verse"] == 1:
                return
        raise AssertionError("seed corpus missing Gen 1:1")


class TestChi3ReformationCommentariesLoader:
    """The loader class in `scripts.core.sources` indexes the JSON
    correctly + raises SourceMissingError on absent cache."""

    def test_loader_returns_frozen_dataclass_instances(self):
        from scripts.core import sources

        rc = sources.reformation_commentaries()
        entries = rc.for_verse("gen", 1, 1)
        assert entries, "Gen 1:1 should have at least one Reformation entry"
        entry = entries[0]
        assert isinstance(entry, sources.ReformationCommentary)
        import dataclasses

        assert dataclasses.is_dataclass(entry)
        for field_name in ("book", "chapter", "verse", "commentator", "work", "year", "summary", "attribution"):
            value = getattr(entry, field_name)
            assert value not in (None, "", 0), f"{field_name} unset"

    def test_dataclass_is_frozen(self):
        import dataclasses

        import pytest

        from scripts.core import sources

        rc = sources.reformation_commentaries()
        entry = rc.for_verse("gen", 1, 1)[0]

        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            entry.book = "exo"  # type: ignore[misc]

    def test_by_verse_lookup(self):
        from scripts.core import sources

        rc = sources.reformation_commentaries()
        gen11 = rc.for_verse("gen", 1, 1)
        assert len(gen11) >= 1
        assert all(e.book == "gen" and e.chapter == 1 and e.verse == 1 for e in gen11)

    def test_by_verse_empty_for_unknown(self):
        from scripts.core import sources

        rc = sources.reformation_commentaries()
        # Revelation has nothing — Calvin never wrote a commentary on it.
        empty = rc.for_verse("rev", 1, 1)
        assert empty == []

    def test_by_commentator_lookup_calvin(self):
        # Calvin is the sole seed voice for χ.3.
        from scripts.core import sources

        rc = sources.reformation_commentaries()
        calvin = rc.by_commentator("John Calvin")
        assert len(calvin) >= 1, "John Calvin must appear in the seed (sole χ.3 expositor)"
        for entry in calvin:
            assert entry.commentator == "John Calvin"

    def test_by_commentator_empty_for_unknown(self):
        from scripts.core import sources

        rc = sources.reformation_commentaries()
        # Luther isn't in the seed (χ.3.x candidate, not χ.3 itself).
        empty = rc.by_commentator("Martin Luther")
        assert empty == []

    def test_loader_handles_missing_cache(self, tmp_path, monkeypatch):
        from scripts.core import sources

        nope = tmp_path / "reformation_commentaries.json"
        monkeypatch.setattr(sources.ReformationCommentaries, "PATH", nope)
        sources.reformation_commentaries.cache_clear()
        try:
            import pytest

            with pytest.raises(sources.SourceMissingError):
                sources.ReformationCommentaries()
        finally:
            sources.reformation_commentaries.cache_clear()


class TestChi3DetectorContract:
    """`ReformationCommentaryDetector` emits proper Candidates and
    is registered in `ALL_DETECTORS`."""

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.reformation_commentaries.cache_clear()

    def test_registered_in_all_detectors(self):
        from scripts.core import detectors

        assert detectors.ReformationCommentaryDetector in detectors.ALL_DETECTORS, (
            "ReformationCommentaryDetector missing from ALL_DETECTORS — prospect.py won't run it"
        )

    def test_registered_after_catholic(self):
        # Ordering: χ.3 runs after χ.4 so the candidate-order lineage
        # stays γ.3 → γ.4 → χ.2 → χ.4 → χ.3 (patristic → tewahedo →
        # protestant → catholic → reformation).
        from scripts.core import detectors

        detectors_list = list(detectors.ALL_DETECTORS)
        c_idx = detectors_list.index(detectors.CatholicCommentaryDetector)
        r_idx = detectors_list.index(detectors.ReformationCommentaryDetector)
        assert r_idx > c_idx, "Reformation detector must run after Catholic"

    def test_kind_is_comm_reformation(self):
        from scripts.core import detectors

        assert detectors.ReformationCommentaryDetector.kind == "comm-reformation"

    def test_detect_returns_candidate_for_gen_1_1(self):
        from scripts.core import detectors

        d = detectors.ReformationCommentaryDetector()
        candidates = d.detect("gen", 1, 1, "In the beginning God created the heaven and the earth.")
        assert candidates, "Gen 1:1 should produce at least one candidate"
        c = candidates[0]
        assert c.kind == "comm-reformation"
        assert c.book == "gen"
        assert c.chapter == 1
        assert c.verse == 1
        assert c.confidence == 0.95
        assert c.detector == "ReformationCommentaryDetector"
        assert "<aside" in c.draft_body
        # Body is rendered with the note class for theme styling.
        assert "note-comm-reformation" in c.draft_body
        # Candidate title prefixes with the tradition name.
        assert c.draft_title.startswith("Reformation —")

    def test_detect_returns_empty_for_uncommented_verse(self):
        from scripts.core import detectors

        d = detectors.ReformationCommentaryDetector()
        # Revelation: Calvin never wrote a commentary.
        assert d.detect("rev", 1, 1, "") == []
        # Genesis 50: in the seed range but no entry at 50:1.
        assert d.detect("gen", 50, 1, "") == []

    def test_detect_ignores_verse_text(self):
        from scripts.core import detectors

        d = detectors.ReformationCommentaryDetector()
        a = d.detect("gen", 1, 1, "real verse text")
        b = d.detect("gen", 1, 1, "completely different placeholder")
        assert len(a) == len(b)

    def test_body_is_html_escaped(self):
        from scripts.core import detectors
        from scripts.core.sources import ReformationCommentary

        synthetic = ReformationCommentary(
            book="gen",
            chapter=1,
            verse=1,
            commentator="<TestCommentator>",
            work="<TestWork>",
            year=1554,
            summary="<script>alert(1)</script>",
            attribution="Calvin Test, PD.",
        )
        body = detectors.ReformationCommentaryDetector._format_body(synthetic)
        assert "<script>" not in body, "summary not escaped — XSS risk"
        assert "&lt;script&gt;" in body
        assert "&lt;TestCommentator&gt;" in body

    def test_body_renders_plain_year(self):
        # All magisterial Reformers are post-1500. Plain year display,
        # no BC/AD branching — mirrors χ.2's plain-year contract.
        from scripts.core import detectors
        from scripts.core.sources import ReformationCommentary

        synthetic = ReformationCommentary(
            book="gen",
            chapter=1,
            verse=1,
            commentator="John Calvin",
            work="Test",
            year=1554,
            summary="Test.",
            attribution="Calvin Test, PD.",
        )
        body = detectors.ReformationCommentaryDetector._format_body(synthetic)
        assert "1554" in body
        # No era marker — distinct from γ.4 / χ.4 which render BC/AD.
        assert "AD" not in body
        assert "BC" not in body


class TestChi3KindIsRegistered:
    """The `comm-reformation` kind is in `content/kinds.yaml`. It pre-
    existed (declared with the kinds-v2 schema since pre-χ.3); χ.3 is
    the first phase to actually emit it. Pin its presence + label so a
    future kinds-cleanup doesn't drop it silently, and so a future
    contributor doesn't accidentally fold it into comm-protestant."""

    def test_comm_reformation_kind_present_in_yaml(self):
        from pathlib import Path

        import yaml

        repo = Path(__file__).resolve().parent.parent
        kinds_path = repo / "content" / "kinds.yaml"
        data = yaml.safe_load(kinds_path.read_text(encoding="utf-8"))
        codes = {k["code"] for k in data["kinds"]}
        assert "comm-reformation" in codes, "comm-reformation kind missing from kinds.yaml"

    def test_comm_reformation_kind_has_expected_category(self):
        from pathlib import Path

        import yaml

        repo = Path(__file__).resolve().parent.parent
        kinds_path = repo / "content" / "kinds.yaml"
        data = yaml.safe_load(kinds_path.read_text(encoding="utf-8"))
        kind = next(k for k in data["kinds"] if k["code"] == "comm-reformation")
        assert kind["category"] == "comm"
        assert kind.get("label") == "Reformation"

    def test_comm_reformation_distinct_from_comm_protestant(self):
        # Both kinds exist as siblings (not a rename / merge). Drift
        # check: if a future contributor folds them, this fails loud.
        from pathlib import Path

        import yaml

        repo = Path(__file__).resolve().parent.parent
        kinds_path = repo / "content" / "kinds.yaml"
        data = yaml.safe_load(kinds_path.read_text(encoding="utf-8"))
        codes = {k["code"] for k in data["kinds"]}
        assert "comm-reformation" in codes
        assert "comm-protestant" in codes, "comm-protestant must coexist as the broader post-Reformation kind (χ.2)"


class TestChi3Coverage:
    """The seed has the breadth the Reformed tradition requires:
    both Testaments covered (Calvin wrote OT + NT); the signature
    Reformed anchors — sola fide (Rom 3:21 + Gal 2:16), sola gratia
    (Eph 2:8), accommodation (Gen 1:1), idolatry (Exo 20:3),
    providence (Rom 8:28), covenant theology (Jer 31:33)."""

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        cls.rc = sources.reformation_commentaries()

    def test_old_testament_covered(self):
        # Gen 1:1, Gen 3:15, Exo 20:3, Ps 23:1, Isa 7:14, Jer 31:33.
        assert self.rc.for_verse("gen", 1, 1)
        assert self.rc.for_verse("gen", 3, 15)
        assert self.rc.for_verse("exo", 20, 3)
        assert self.rc.for_verse("ps", 23, 1)
        assert self.rc.for_verse("isa", 7, 14)
        assert self.rc.for_verse("jer", 31, 33)

    def test_new_testament_covered(self):
        # Mat 6:9, Joh 1:1, Rom 3:21, Rom 8:28, Gal 2:16, Eph 2:8.
        assert self.rc.for_verse("mat", 6, 9)
        assert self.rc.for_verse("joh", 1, 1)
        assert self.rc.for_verse("rom", 3, 21)
        assert self.rc.for_verse("rom", 8, 28)
        assert self.rc.for_verse("gal", 2, 16)
        assert self.rc.for_verse("eph", 2, 8)

    def test_sola_fide_anchors_present(self):
        # Rom 3:21 + Gal 2:16 are THE Reformed pins — justification
        # by faith apart from works. Both must appear in the seed.
        assert self.rc.for_verse("rom", 3, 21), "seed corpus missing Rom 3:21 — sola fide locus classicus"
        assert self.rc.for_verse("gal", 2, 16), "seed corpus missing Gal 2:16 — sola fide on negative-positive symmetry"

    def test_sola_gratia_anchor_present(self):
        # Eph 2:8 grounds the Reformed sola gratia pillar.
        assert self.rc.for_verse("eph", 2, 8), "seed corpus missing Eph 2:8 — sola gratia pillar"

    def test_accommodation_anchor_present(self):
        # Gen 1:1 carries Calvin's signature hermeneutic of divine
        # accommodation ('God lisps to us as a nurse to her child').
        entries = self.rc.for_verse("gen", 1, 1)
        assert entries, "seed corpus missing Gen 1:1 — Calvin accommodation pin"

    def test_idolatry_anchor_present(self):
        # Exo 20:3 is the textual root of Calvin's regulative
        # principle of worship.
        assert self.rc.for_verse("exo", 20, 3), "seed corpus missing Exo 20:3 — Calvin regulative-principle pin"

    def test_providence_anchor_present(self):
        # Rom 8:28 is the locus classicus of Calvinist providence.
        assert self.rc.for_verse("rom", 8, 28), "seed corpus missing Rom 8:28 — providence locus classicus"

    def test_covenant_theology_anchor_present(self):
        # Jer 31:33 grounds Reformed covenant theology (the new
        # covenant as substantial continuity of the Sinai covenant
        # in a new mode).
        assert self.rc.for_verse("jer", 31, 33), "seed corpus missing Jer 31:33 — Reformed covenant-theology pin"

    def test_calvin_only_voice_in_seed(self):
        # χ.3 ships a Calvin-only seed; χ.3.x will add Luther /
        # Zwingli / Anabaptist expositors. Pin Calvin is the sole
        # seed voice so an accidental future merge doesn't pass
        # silently.
        commentators = set()
        for chapter in range(1, 200):
            for verse in range(1, 200):
                for book in ("gen", "exo", "lev", "ps", "isa", "jer", "mat", "joh", "rom", "gal", "eph"):
                    for entry in self.rc.for_verse(book, chapter, verse):
                        commentators.add(entry.commentator)
        assert commentators == {"John Calvin"}, f"χ.3 seed should be John Calvin only; found {commentators!r}"
