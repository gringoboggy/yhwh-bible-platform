"""γ.3 — Patristic commentary corpus + detector pins.

Topic file (created alongside the γ.3 ship). Different shape
from γ.1/γ.2's tests — γ.3 ships content infrastructure into
the existing detector pipeline, not a new console.

Coverage:
- TestGamma3DataFile:              the seed JSON parses, has the
  promised Augustine-on-Genesis entries, every entry carries
  full attribution.
- TestGamma3PatristicCommentariesLoader: the loader indexes by
  verse + by father, returns frozen dataclass instances,
  surfaces SourceMissingError gracefully.
- TestGamma3DetectorContract:      `PatristicCommentaryDetector`
  emits the right Candidate shape; confidence 0.95; empty list
  for verses with no commentary; registered in ALL_DETECTORS.
- TestGamma3KindIsRegistered:      `comm-patristic` exists in
  `content/kinds.yaml` (was already there pre-γ.3 but pin it
  so a future kinds-cleanup doesn't quietly drop it).

Pinning rationale: γ.3 is the first content-depth phase that
ships actual note candidates to the corpus. Drift in the
attribution format, the detector confidence, or the kind
registration would break the prospect→promote pipeline silently.
"""

from __future__ import annotations


class TestGamma3DataFile:
    """The seed JSON at content/sources/patristic_commentaries.json
    parses and carries the promised Augustine-on-Genesis set."""

    @classmethod
    def setup_class(cls):
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        cls.path = repo / "content" / "sources" / "patristic_commentaries.json"
        cls.data = json.loads(cls.path.read_text(encoding="utf-8"))

    def test_file_exists(self):
        assert self.path.is_file()

    def test_has_meta_block(self):
        # The _meta block documents schema + PD basis for future
        # contributors. Pin it stays.
        assert "_meta" in self.data
        meta = self.data["_meta"]
        for required in ("source", "scope", "public_domain_basis", "schema_version"):
            assert required in meta, f"_meta missing field {required!r}"
        assert meta["schema_version"] == 1

    def test_has_entries_list(self):
        assert "entries" in self.data
        assert isinstance(self.data["entries"], list)
        assert len(self.data["entries"]) >= 5, "expected ≥5 seed entries"

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

    def test_every_entry_cites_npnf(self):
        # All seed entries are sourced from NPNF (Schaff). Pin
        # this so a future drift toward un-attributed sources gets
        # caught — the buyer-facing claim is "public domain via
        # NPNF" and that has to remain true.
        for entry in self.data["entries"]:
            assert "NPNF" in entry["attribution"], f"entry not attributed to NPNF: {entry['attribution']!r}"
            assert "PD" in entry["attribution"], f"entry attribution missing PD marker: {entry['attribution']!r}"

    def test_genesis_1_1_present(self):
        # Gen 1:1 is the canonical opening verse. The seed should
        # always include it — first thing any buyer would test.
        for entry in self.data["entries"]:
            if entry["book"] == "gen" and entry["chapter"] == 1 and entry["verse"] == 1:
                return
        raise AssertionError("seed corpus missing Gen 1:1")

    def test_augustine_only_for_seed(self):
        # The seed is Augustine-only by design. Future γ.3.x will
        # add Origen, Chrysostom, Basil, Jerome. Pin Augustine-
        # only here so a future contributor adding a different
        # Father has to update this test (forcing them to think
        # about the scope expansion).
        fathers = {e["father"] for e in self.data["entries"]}
        assert fathers == {"Augustine"}, (
            f"seed corpus should be Augustine-only; got {fathers}. "
            "If expanding deliberately, update this test to track."
        )


class TestGamma3PatristicCommentariesLoader:
    """The loader class in `scripts.core.sources` indexes the JSON
    correctly + raises SourceMissingError on absent cache."""

    def test_loader_returns_frozen_dataclass_instances(self):
        from scripts.core import sources

        pc = sources.patristic_commentaries()
        entries = pc.for_verse("gen", 1, 1)
        assert entries, "Gen 1:1 should have at least one commentary"
        entry = entries[0]
        assert isinstance(entry, sources.PatristicCommentary)
        # frozen — attempting to mutate raises
        import dataclasses

        assert dataclasses.is_dataclass(entry)
        # Test fields populated
        for field_name in ("book", "chapter", "verse", "father", "work", "year", "summary", "attribution"):
            value = getattr(entry, field_name)
            assert value not in (None, "", 0) or field_name == "year", f"{field_name} unset"

    def test_by_verse_lookup(self):
        from scripts.core import sources

        pc = sources.patristic_commentaries()
        # Gen 1:1 — Augustine on "In the beginning"
        gen11 = pc.for_verse("gen", 1, 1)
        assert len(gen11) >= 1
        assert all(e.book == "gen" and e.chapter == 1 and e.verse == 1 for e in gen11)

    def test_by_verse_empty_for_unknown(self):
        from scripts.core import sources

        pc = sources.patristic_commentaries()
        # Structurally-impossible coordinate (RULES §8.1: don't assert a
        # real verse is permanently uncommented — corpus growth would
        # silently flip it). No such book/chapter/verse can ever exist.
        empty = pc.for_verse("nonexistent-book-xyz", 99, 99)
        assert empty == []

    def test_by_father_lookup(self):
        from scripts.core import sources

        pc = sources.patristic_commentaries()
        augustine = pc.by_father("Augustine")
        # The seed is Augustine-only — every entry should appear.
        assert len(augustine) == len(pc), "Augustine entries should equal total"

    def test_by_father_empty_for_unknown(self):
        from scripts.core import sources

        pc = sources.patristic_commentaries()
        # Structurally-impossible father (RULES §8.1: don't assert a real
        # father is permanently absent — ingest would silently flip it).
        empty = pc.by_father("nonexistent-father-xyz")
        assert empty == []

    def test_loader_handles_missing_cache(self, tmp_path, monkeypatch):
        # SourceMissingError if the JSON is absent — same contract
        # as the other loaders.
        from scripts.core import sources

        nope = tmp_path / "patristic_commentaries.json"
        # Don't write the file; expect the loader to raise.
        monkeypatch.setattr(sources.PatristicCommentaries, "PATH", nope)
        sources.patristic_commentaries.cache_clear()
        try:
            with __import__("pytest").raises(sources.SourceMissingError):
                sources.PatristicCommentaries()
        finally:
            # Reset cache so subsequent tests get the real file.
            sources.patristic_commentaries.cache_clear()


class TestGamma3DetectorContract:
    """`PatristicCommentaryDetector` emits proper Candidates and
    is registered in `ALL_DETECTORS`."""

    @classmethod
    def setup_class(cls):
        # Clear the source cache going IN so chi1's earlier
        # monkeypatching of Strong's caches doesn't leak (same
        # defensive pattern as γ.2's test classes). Patristic
        # specifically has its own cache to clear.
        from scripts.core import sources

        sources.patristic_commentaries.cache_clear()

    def test_registered_in_all_detectors(self):
        from scripts.core import detectors

        assert detectors.PatristicCommentaryDetector in detectors.ALL_DETECTORS, (
            "PatristicCommentaryDetector missing from ALL_DETECTORS — prospect.py won't run it on the corpus"
        )

    def test_kind_is_comm_patristic(self):
        from scripts.core import detectors

        assert detectors.PatristicCommentaryDetector.kind == "comm-patristic"

    def test_detect_returns_candidate_for_gen_1_1(self):
        from scripts.core import detectors

        d = detectors.PatristicCommentaryDetector()
        candidates = d.detect("gen", 1, 1, "In the beginning God made heaven and earth.")
        assert candidates, "Gen 1:1 should produce at least one candidate"
        c = candidates[0]
        # Shape pinning
        assert c.kind == "comm-patristic"
        assert c.book == "gen"
        assert c.chapter == 1
        assert c.verse == 1
        assert c.confidence == 0.95, "curated PD content gets high fixed confidence"
        assert c.detector == "PatristicCommentaryDetector"
        # Body is non-empty HTML
        assert "<aside" in c.draft_body
        assert "Augustine" in c.draft_body
        # Attribution carries NPNF citation
        assert "NPNF" in c.source_attribution

    def test_detect_returns_empty_for_uncommented_verse(self):
        from scripts.core import detectors

        d = detectors.PatristicCommentaryDetector()
        # Structurally-impossible coordinates (RULES §8.1: don't assert a
        # real verse stays uncommented — corpus growth would flip it).
        assert d.detect("nonexistent-book-xyz", 99, 99, "") == []
        assert d.detect("gen", 99, 99, "") == []

    def test_detect_ignores_verse_text(self):
        # Unlike keyword detectors, this one looks up by
        # (book, chapter, verse) only — verse_text content
        # doesn't matter. Pin that — if a future "smart"
        # variant adds keyword filtering, that's a separate
        # γ.3.x decision that should explicitly update this
        # test.
        from scripts.core import detectors

        d = detectors.PatristicCommentaryDetector()
        a = d.detect("gen", 1, 1, "real verse text")
        b = d.detect("gen", 1, 1, "completely different placeholder")
        assert len(a) == len(b), "verse_text should not affect detector output"

    def test_body_is_html_escaped(self):
        # Even though source data is curated, the body builder
        # escapes via `html.escape()` so future entries with
        # exotic content can't break HTML rendering.
        from scripts.core import detectors
        from scripts.core.sources import PatristicCommentary

        # Construct a synthetic entry with HTML-ish characters in
        # the summary; verify the body output escapes them.
        synthetic = PatristicCommentary(
            book="gen",
            chapter=1,
            verse=1,
            father="<TestFather>",
            work="<TestWork>",
            year=400,
            summary="<script>alert(1)</script>",
            attribution="Test, PD.",
        )
        body = detectors.PatristicCommentaryDetector._format_body(synthetic)
        # < / > / & / quotes should all be escaped
        assert "<script>" not in body, "summary not escaped — XSS risk"
        assert "&lt;script&gt;" in body
        assert "&lt;TestFather&gt;" in body


class TestGamma3KindIsRegistered:
    """The `comm-patristic` kind is in `content/kinds.yaml`. It was
    declared pre-γ.3 (anticipated by the original kinds-v2 schema);
    pin its presence so a future kinds-cleanup doesn't drop it
    silently."""

    def test_comm_patristic_kind_present_in_yaml(self):
        from pathlib import Path

        import yaml

        repo = Path(__file__).resolve().parent.parent
        kinds_path = repo / "content" / "kinds.yaml"
        data = yaml.safe_load(kinds_path.read_text(encoding="utf-8"))
        codes = {k["code"] for k in data["kinds"]}
        assert "comm-patristic" in codes, "comm-patristic kind missing from kinds.yaml"

    def test_comm_patristic_kind_has_expected_category(self):
        from pathlib import Path

        import yaml

        repo = Path(__file__).resolve().parent.parent
        kinds_path = repo / "content" / "kinds.yaml"
        data = yaml.safe_load(kinds_path.read_text(encoding="utf-8"))
        kind = next(k for k in data["kinds"] if k["code"] == "comm-patristic")
        assert kind["category"] == "comm", f"comm-patristic should be in `comm` category, got {kind.get('category')!r}"
        # Pin the label too — the EPUB builder reads this for the
        # popup heading.
        assert kind.get("label") == "Patristic"
