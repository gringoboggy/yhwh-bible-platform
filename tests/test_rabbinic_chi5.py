"""χ.5 — Rabbinic (Rashi) commentary corpus + detector pins.

Topic file (created alongside the χ.5 ship — CLOSES the χ.2-5
commentary cluster). Mirrors γ.3 / γ.4 / χ.2 / χ.4 / χ.3: seed JSON
validation + loader pins + detector contract + kinds.yaml registration.

Coverage:
- TestChi5DataFile:                  the seed JSON parses, has the
  promised Rashi entries, every entry carries full attribution and
  the Hebrew-text-PD provenance.
- TestChi5RabbinicCommentariesLoader: the loader indexes by verse +
  by commentator, returns frozen dataclass instances, surfaces
  SourceMissingError gracefully.
- TestChi5DetectorContract:          `RabbinicCommentaryDetector`
  emits the right Candidate shape; confidence 0.95; empty list for
  verses with no commentary; registered in ALL_DETECTORS *after*
  ReformationCommentaryDetector so candidate ordering follows the
  γ.3 → γ.4 → χ.2 → χ.4 → χ.3 → χ.5 lineage; body builder escapes
  HTML; plain year display (all χ.5 seed voices post-AD).
- TestChi5KindIsRegistered:          `comm-rabbinic` exists in
  `content/kinds.yaml` (pre-existed; χ.5 is the first phase to
  emit it). Pin so a future kinds-cleanup doesn't drop it silently.
- TestChi5Coverage:                  seed entries are Pentateuch-
  heavy (Rashi's most-studied work) with key Jewish-distinctive
  readings: Isa 53 corporate-Israel pin + Ps 22 historical-not-
  Christological pin; Shema (Deu 6:4) + V'ahavta (Deu 6:5);
  Lev 19:18 Akiva pin; Gen 49:10 Shiloh prophecy Jewish read;
  Akedah (Gen 22:1); the famous Rashi opening note on Gen 1:1.

Pinning rationale: χ.5 CLOSES the χ.2-5 commentary cluster (χ.2
Protestant + χ.3 Reformation + χ.4 Catholic + χ.5 Jewish — all
four major Western denominational lenses now have at least seed
coverage). Drift in the Jewish-distinctive readings (Isa 53 / Ps 22
must NOT be Christological), the year range (anti-merge with χ.2's
1700-1721 and χ.3's 1540-1564 ranges), or the kind registration
would break the χ.5.x expansion pipeline silently.
"""

from __future__ import annotations


class TestChi5DataFile:
    """The seed JSON at content/sources/rabbinic_commentaries.json
    parses and carries the promised Rashi entries."""

    @classmethod
    def setup_class(cls):
        import json
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        cls.path = repo / "content" / "sources" / "rabbinic_commentaries.json"
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
        # Pin: _meta documents Rashi (d. 1105) — the Hebrew text is
        # PD by age. The PD basis note explicitly addresses the
        # English-translation issue (most modern Rashi translations
        # are in copyright; seed paraphrases avoid quoting them).
        meta = self.data["_meta"]
        pd = meta["public_domain_basis"]
        assert "Rashi" in pd
        assert "1105" in pd
        assert "Hebrew" in pd

    def test_has_entries_list(self):
        assert "entries" in self.data
        assert isinstance(self.data["entries"], list)
        assert len(self.data["entries"]) >= 12, "expected ≥12 seed entries for χ.5"

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

    def test_every_entry_cites_hebrew_pd(self):
        # Pin: every entry's attribution names Rashi + carries the
        # explicit "PD" marker (medieval Hebrew is PD by age).
        for entry in self.data["entries"]:
            attr = entry["attribution"]
            assert "Rashi" in attr, f"entry not attributed to Rashi: {attr!r}"
            assert "PD" in attr, f"entry attribution missing PD marker: {attr!r}"

    def test_every_entry_in_rashi_lifetime(self):
        # All χ.5 entries should be within Rashi's commentary period
        # (~1070-1105). Pin against accidental merge with χ.2 (1700-
        # 1721 Henry) or χ.3 (1540-1564 Calvin) or future χ.5.x
        # post-Rashi voices (Maimonides 1138-1204, Ramban 1194-1270)
        # that would need their own commentator entries.
        for entry in self.data["entries"]:
            year = int(entry["year"])
            assert year >= 1070, f"entry year {year} predates Rashi's commentary period (~1070-1105)"
            assert year <= 1105, (
                f"entry year {year} postdates Rashi's death (1105) — should be a new χ.5.x phase for Maimonides/Ramban/etc."
            )

    def test_genesis_1_1_present(self):
        # The famous Rashi opening note ("this verse cries out,
        # explain me!") — Rashi's most-quoted single comment.
        for entry in self.data["entries"]:
            if entry["book"] == "gen" and entry["chapter"] == 1 and entry["verse"] == 1:
                return
        raise AssertionError("seed corpus missing Gen 1:1 — Rashi's most-iconic comment")


class TestChi5RabbinicCommentariesLoader:
    """The loader class in `scripts.core.sources` indexes the JSON
    correctly + raises SourceMissingError on absent cache."""

    def test_loader_returns_frozen_dataclass_instances(self):
        from scripts.core import sources

        rb = sources.rabbinic_commentaries()
        entries = rb.for_verse("gen", 1, 1)
        assert entries, "Gen 1:1 should have at least one Rashi entry"
        entry = entries[0]
        assert isinstance(entry, sources.RabbinicCommentary)
        import dataclasses

        assert dataclasses.is_dataclass(entry)
        for field_name in ("book", "chapter", "verse", "commentator", "work", "year", "summary", "attribution"):
            value = getattr(entry, field_name)
            assert value not in (None, "", 0), f"{field_name} unset"

    def test_dataclass_is_frozen(self):
        import dataclasses

        import pytest

        from scripts.core import sources

        rb = sources.rabbinic_commentaries()
        entry = rb.for_verse("gen", 1, 1)[0]

        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            entry.book = "exo"  # type: ignore[misc]

    def test_by_verse_lookup(self):
        from scripts.core import sources

        rb = sources.rabbinic_commentaries()
        gen11 = rb.for_verse("gen", 1, 1)
        assert len(gen11) >= 1
        assert all(e.book == "gen" and e.chapter == 1 and e.verse == 1 for e in gen11)

    def test_by_verse_empty_for_unknown(self):
        from scripts.core import sources

        rb = sources.rabbinic_commentaries()
        # NT books have no Rashi commentary by definition.
        empty = rb.for_verse("mat", 1, 1)
        assert empty == []
        empty2 = rb.for_verse("rev", 1, 1)
        assert empty2 == []

    def test_by_commentator_lookup_rashi(self):
        from scripts.core import sources

        rb = sources.rabbinic_commentaries()
        rashi = rb.by_commentator("Rashi")
        assert len(rashi) >= 1, "Rashi must appear in the seed (sole χ.5 voice)"
        for entry in rashi:
            assert entry.commentator == "Rashi"

    def test_by_commentator_empty_for_unknown(self):
        from scripts.core import sources

        rb = sources.rabbinic_commentaries()
        # Maimonides is a χ.5.x candidate, not present in χ.5 seed.
        empty = rb.by_commentator("Maimonides")
        assert empty == []

    def test_loader_handles_missing_cache(self, tmp_path, monkeypatch):
        from scripts.core import sources

        nope = tmp_path / "rabbinic_commentaries.json"
        monkeypatch.setattr(sources.RabbinicCommentaries, "PATH", nope)
        sources.rabbinic_commentaries.cache_clear()
        try:
            import pytest

            with pytest.raises(sources.SourceMissingError):
                sources.RabbinicCommentaries()
        finally:
            sources.rabbinic_commentaries.cache_clear()


class TestChi5DetectorContract:
    """`RabbinicCommentaryDetector` emits proper Candidates and
    is registered in `ALL_DETECTORS`."""

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        sources.rabbinic_commentaries.cache_clear()

    def test_registered_in_all_detectors(self):
        from scripts.core import detectors

        assert detectors.RabbinicCommentaryDetector in detectors.ALL_DETECTORS, (
            "RabbinicCommentaryDetector missing from ALL_DETECTORS — prospect.py won't run it"
        )

    def test_registered_after_reformation(self):
        # Ordering: χ.5 runs after χ.3 so candidate-order lineage is
        # γ.3 → γ.4 → χ.2 → χ.4 → χ.3 → χ.5 (patristic → tewahedo →
        # protestant → catholic → reformation → rabbinic). Pin so a
        # future cleanup doesn't reorder.
        from scripts.core import detectors

        detectors_list = list(detectors.ALL_DETECTORS)
        r_idx = detectors_list.index(detectors.ReformationCommentaryDetector)
        b_idx = detectors_list.index(detectors.RabbinicCommentaryDetector)
        assert b_idx > r_idx, "Rabbinic detector must run after Reformation"

    def test_kind_is_comm_rabbinic(self):
        from scripts.core import detectors

        assert detectors.RabbinicCommentaryDetector.kind == "comm-rabbinic"

    def test_detect_returns_candidate_for_gen_1_1(self):
        from scripts.core import detectors

        d = detectors.RabbinicCommentaryDetector()
        candidates = d.detect("gen", 1, 1, "In the beginning God created the heaven and the earth.")
        assert candidates, "Gen 1:1 should produce at least one candidate"
        c = candidates[0]
        assert c.kind == "comm-rabbinic"
        assert c.book == "gen"
        assert c.chapter == 1
        assert c.verse == 1
        assert c.confidence == 0.95
        assert c.detector == "RabbinicCommentaryDetector"
        assert "<aside" in c.draft_body
        # Body is rendered with the note class for theme styling.
        assert "note-comm-rabbinic" in c.draft_body
        # Candidate title prefixes with the tradition name.
        assert c.draft_title.startswith("Rabbinic —")

    def test_detect_returns_empty_for_uncommented_verse(self):
        from scripts.core import detectors

        d = detectors.RabbinicCommentaryDetector()
        # NT books — Rashi has no commentary on these.
        assert d.detect("mat", 1, 1, "") == []
        # Gen 50:1 — in scope (Rashi commented on all of Gen) but
        # not selected for the seed.
        assert d.detect("gen", 50, 1, "") == []

    def test_detect_ignores_verse_text(self):
        from scripts.core import detectors

        d = detectors.RabbinicCommentaryDetector()
        a = d.detect("gen", 1, 1, "real verse text")
        b = d.detect("gen", 1, 1, "completely different placeholder")
        assert len(a) == len(b)

    def test_body_is_html_escaped(self):
        from scripts.core import detectors
        from scripts.core.sources import RabbinicCommentary

        synthetic = RabbinicCommentary(
            book="gen",
            chapter=1,
            verse=1,
            commentator="<TestRashi>",
            work="<TestWork>",
            year=1095,
            summary="<script>alert(1)</script>",
            attribution="Rashi Test, PD.",
        )
        body = detectors.RabbinicCommentaryDetector._format_body(synthetic)
        assert "<script>" not in body, "summary not escaped — XSS risk"
        assert "&lt;script&gt;" in body
        assert "&lt;TestRashi&gt;" in body

    def test_body_renders_plain_year(self):
        # All χ.5 seed voices are post-AD (Rashi 1040-1105). Plain
        # year display, no BC/AD branching — mirrors χ.2 / χ.3
        # contract.
        from scripts.core import detectors
        from scripts.core.sources import RabbinicCommentary

        synthetic = RabbinicCommentary(
            book="gen",
            chapter=1,
            verse=1,
            commentator="Rashi",
            work="Test",
            year=1095,
            summary="Test.",
            attribution="Rashi Test, PD.",
        )
        body = detectors.RabbinicCommentaryDetector._format_body(synthetic)
        assert "1095" in body
        # No era marker — distinct from γ.4 / χ.4 which render BC/AD.
        assert "AD" not in body
        assert "BC" not in body


class TestChi5KindIsRegistered:
    """The `comm-rabbinic` kind is in `content/kinds.yaml`. It pre-
    existed (kinds-v2 schema description: 'Talmud, Midrash Rabbah,
    Rashi, Maimonides, Targumim'); χ.5 is the first phase to actually
    emit it. Pin its presence so a future kinds-cleanup doesn't drop
    it silently."""

    def test_comm_rabbinic_kind_present_in_yaml(self):
        from pathlib import Path

        import yaml

        repo = Path(__file__).resolve().parent.parent
        kinds_path = repo / "content" / "kinds.yaml"
        data = yaml.safe_load(kinds_path.read_text(encoding="utf-8"))
        codes = {k["code"] for k in data["kinds"]}
        assert "comm-rabbinic" in codes, "comm-rabbinic kind missing from kinds.yaml"

    def test_comm_rabbinic_kind_has_expected_category(self):
        from pathlib import Path

        import yaml

        repo = Path(__file__).resolve().parent.parent
        kinds_path = repo / "content" / "kinds.yaml"
        data = yaml.safe_load(kinds_path.read_text(encoding="utf-8"))
        kind = next(k for k in data["kinds"] if k["code"] == "comm-rabbinic")
        assert kind["category"] == "comm"
        assert kind.get("label") == "Rabbinic"


class TestChi5Coverage:
    """The seed is Pentateuch-heavy (Rashi's most-studied work) with
    the load-bearing Jewish-distinctive readings: Isa 53 corporate-
    Israel + Ps 22 historical-not-Christological."""

    @classmethod
    def setup_class(cls):
        from scripts.core import sources

        cls.rb = sources.rabbinic_commentaries()

    def test_pentateuch_weighted(self):
        # Pentateuch (Rashi's most-studied work) gets the largest
        # share. Pin ≥6 of 12 entries in gen/exo/lev/num/deu.
        pentateuch_books = {"gen", "exo", "lev", "num", "deu"}
        pentateuch_count = 0
        for chapter in range(1, 100):
            for verse in range(1, 100):
                for book in pentateuch_books:
                    pentateuch_count += len(self.rb.for_verse(book, chapter, verse))
        assert pentateuch_count >= 6, (
            f"Pentateuch should hold ≥6 of 12 χ.5 entries (Rashi's most-studied work); found {pentateuch_count}"
        )

    def test_rashi_gen_1_1_iconic_note_present(self):
        # The 'zo'ek darshani' opening — Rashi's most-quoted note.
        assert self.rb.for_verse("gen", 1, 1), (
            "seed corpus missing Gen 1:1 — Rashi's iconic 'this verse cries out, explain me' opening"
        )

    def test_akedah_present(self):
        # Gen 22:1 — Rashi's 'achar ha-devarim ha-eleh' Midrashic
        # opening of the Akedah narrative.
        assert self.rb.for_verse("gen", 22, 1), (
            "seed corpus missing Gen 22:1 — Akedah opening (Rashi's signature Midrashic note)"
        )

    def test_shiloh_prophecy_present(self):
        # Gen 49:10 — Jewish-distinctive messianic reading vs the
        # Christian Christological reading.
        assert self.rb.for_verse("gen", 49, 10), (
            "seed corpus missing Gen 49:10 — Shiloh prophecy (Jewish-distinctive vs Christian reading)"
        )

    def test_shema_present(self):
        # Deu 6:4 — Rashi's eschatological reading of 'echad'
        # (citing Zech 14:9).
        assert self.rb.for_verse("deu", 6, 4), "seed corpus missing Deu 6:4 — Shema (Rashi's eschatological reading)"

    def test_akiva_pin_present(self):
        # Lev 19:18 — Akiva's 'zeh klal gadol baTorah' (this is a
        # great principle of the Torah). Signature halakhic pin.
        assert self.rb.for_verse("lev", 19, 18), "seed corpus missing Lev 19:18 — Akiva pin via Rashi"

    def test_psalm_22_jewish_reading_present(self):
        # Ps 22:1 — Rashi's reading as David-Esther-exile, NOT as
        # Christological prefigurement. THE classic Jewish-distinctive
        # reading vs the Christian cross-reading.
        assert self.rb.for_verse("ps", 22, 1), (
            "seed corpus missing Ps 22:1 — Jewish-distinctive 'lama azavtani' reading vs Christological"
        )

    def test_isaiah_53_corporate_israel_present(self):
        # Isa 53:3 — Rashi's corporate-Israel reading of the
        # Suffering Servant. THE most-disputed text between Jewish
        # and Christian interpretive traditions.
        assert self.rb.for_verse("isa", 53, 3), (
            "seed corpus missing Isa 53:3 — Jewish corporate-Israel Suffering Servant reading"
        )

    def test_rashi_only_voice_in_seed(self):
        # χ.5 ships a Rashi-only seed; χ.5.x adds Maimonides / Ibn
        # Ezra / Ramban / Targum. Pin Rashi is sole seed voice so an
        # accidental merge with another rabbinic source doesn't
        # silently pass.
        commentators = set()
        for chapter in range(1, 200):
            for verse in range(1, 200):
                for book in ("gen", "exo", "lev", "num", "deu", "ps", "isa", "jer", "ezk"):
                    for entry in self.rb.for_verse(book, chapter, verse):
                        commentators.add(entry.commentator)
        assert commentators == {"Rashi"}, f"χ.5 seed should be Rashi only; found {commentators!r}"
