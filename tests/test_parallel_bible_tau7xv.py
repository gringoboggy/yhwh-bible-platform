"""τ.7.x.v — Matthew PILOT-discovery + NT-renumber-overflow BLOCKER
(2026-05-16; overnight autonomous-run).

NOT a book ingest. The τ.7.x.a.0-PILOT precedent: a parser-
extension blocker was found before the book can ship cleanly, so
this phase only (a) commits the verified Matthew page-range +
floor as PREPARED INFRA and (b) documents the blocker + defers the
NT ingest. NO mat.py was written; stats were NOT bumped; the
autonomous Amharic render cadence is PAUSED at the NT boundary.

Discovery: Matthew = structural_map.matthew [1567,1635] (NEW
section, the τ.7.x.q baruch pattern — Matthew was never Π.1-
mapped, so NOT a Π.1 upgrade, no prior-pin conversion). Title
p1567, Mt 1 genealogy p1568, Passion/Resurrection p1629-1635;
Mark opens p1636 (`ወንጌል ቅዱስ ማርቆስ` = Mark 1:1) — decisive
end-boundary cross-validation; contiguous after one_enoch
[1515,1566]. MATTHEW_VERSE_COUNTS = standard KJV/UBS-NA (28 ch /
1071 v) — NT versification is standardized so the floor is
authoritative DIRECTLY (content/notes/mat.py is NOT a clean
γ-floor-coordination source for the NT: its (int,int) maxima e.g.
ch6=83 are not plausible KJV verse numbers).

Blocker: a dry-run recovered 1178 verses vs the 1071-v floor →
OVERFLOW; "1:1" was Mt 3:1 content (Mt 1-2 genealogy unparsed).
Root cause: the NT Gospel structure (dense `ክፍል N` pericope-
section headers + the heavy NT inline cross-reference apparatus +
the list-format Mt-1 genealogy) breaks the OT-tuned renumber.
NOT unique to Matthew — ALL remaining parallel-PDF content is NT.
Remedy: an NT-parser extension (tooling) — DEFERRED pending user
authorization; the cadence is PAUSED. mat.py was deliberately NOT
written (shipping it would be distorted scripture — τ.6.x.0b).
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SOURCE_YAML = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"
AMHARIC_TEWAHEDO = REPO / "content" / "translations" / "amharic-tewahedo"
GEEZ_TEWAHEDO = REPO / "content" / "translations" / "geez-tewahedo"


def _source_yaml() -> dict:
    return yaml.safe_load(SOURCE_YAML.read_text(encoding="utf-8"))


def _meta() -> dict:
    return yaml.safe_load((AMHARIC_TEWAHEDO / "_meta.yaml").read_text(encoding="utf-8"))


def _floor():
    sys.path.insert(0, str(REPO / "scripts"))
    from extract_parallel_pdf import MATTHEW_VERSE_COUNTS

    return MATTHEW_VERSE_COUNTS


# ──────────────────────── floor (prepared infra) ───────────────────


class TestTau7XVMatthewVerseCounts:
    def test_symbol_present(self):
        assert isinstance(_floor(), dict)

    def test_28_chapters_contiguous(self):
        assert sorted(_floor().keys()) == list(range(1, 29))

    def test_total_verses_1071(self):
        assert sum(_floor().values()) == 1071

    def test_books_yaml_mat_ch_count_28(self):
        books = yaml.safe_load((REPO / "content" / "books.yaml").read_text(encoding="utf-8"))["books"]
        rec = next(b for b in books if b["code"] == "mat")
        assert rec["ch_count"] == 28
        assert rec["bxx"] == "b60"
        assert "Matthew" in rec["title"]

    def test_kjv_spot_values(self):
        f = _floor()
        assert f[1] == 25 and f[6] == 34 and f[26] == 75 and f[28] == 20

    def test_nt_methodology_note_in_extractor(self):
        """NT floors use the standard enumeration DIRECTLY — NOT
        the γ-notes cross-validation used for jub/1en. Robust
        short-token checks (the extractor comment is `# `-line-
        wrapped, so multi-word phrases are brittle)."""
        src = (REPO / "scripts" / "extract_parallel_pdf.py").read_text(encoding="utf-8")
        assert "MATTHEW_VERSE_COUNTS" in src
        assert "notes/mat.py" in src  # the NT-not-a-clean-source note
        assert "standardized" in src  # the NT-versification-standardized rationale
        assert '"matthew"' in src  # the renumber dispatch wiring


# ───────────────── structural_map.matthew (NEW section) ────────────


class TestTau7XVStructuralMapMatthewNewSection:
    def _blk(self) -> dict:
        return _source_yaml()["structural_map"]["matthew"]

    def test_block_present(self):
        assert "matthew" in _source_yaml()["structural_map"]

    def test_book_codes(self):
        assert self._blk()["book_codes"] == ["mat"]

    def test_pdf_page_range_1567_1635(self):
        assert self._blk()["pdf_page_range"] == [1567, 1635]

    def test_verified_true_at_tau7xv(self):
        assert self._blk()["verified"] is True
        assert self._blk()["verified_at_phase"] == "τ.7.x.v"

    def test_chapter_count_expected_28(self):
        assert self._blk()["chapter_count_expected"] == 28

    def test_contiguous_after_one_enoch(self):
        sm = _source_yaml()["structural_map"]
        assert sm["one_enoch"]["pdf_page_range"] == [1515, 1566]
        assert sm["matthew"]["pdf_page_range"][0] == 1567  # p1567 right after p1566

    def test_notes_document_mark_boundary_crossvalidation(self):
        notes = " ".join(self._blk()["notes"].split())
        # Robust tokens (avoid word-order/wrap brittleness): the
        # notes say "p1636 opens Mark", a NEW section, never Π.1.
        assert "p1636" in notes and "Mark" in notes
        assert "NEW structural_map section" in notes
        assert "never Π.1-mapped" in notes


# ───────────── the NT-overflow blocker + honest deferral ───────────


class TestTau7XVBlockerAndHonestDeferral:
    def test_mat_py_NOT_created(self):
        """mat.py must NOT exist — shipping the overflow output
        would be distorted scripture (τ.6.x.0b). The honest
        deferral, like the τ.7.x.s sus 'not created' pin."""
        assert not (AMHARIC_TEWAHEDO / "mat.py").exists()

    def test_geez_mat_NOT_created(self):
        assert not (GEEZ_TEWAHEDO / "mat.py").exists()

    def test_source_tau7xv_is_pilot_discovery_blocker(self):
        t = _source_yaml()["ocr_strategy"]["tau7xv_ingest"]
        assert t["ship_class"] == "PILOT-discovery-and-blocker"
        assert t["no_ingest_at_this_phase"] is True
        assert t["blocker"]["class"] == "NT-renumber-overflow"

    def test_source_blocker_documents_root_cause_and_remedy(self):
        b = _source_yaml()["ocr_strategy"]["tau7xv_ingest"]["blocker"]
        rc = " ".join(b["root_cause"].split())
        assert "ክፍል" in rc and "cross-reference apparatus" in rc
        nu = " ".join(b["not_unique_to_matthew"].split())
        assert "ALL remaining parallel-PDF content is NT" in nu
        rem = " ".join(b["remedy_required"].split())
        assert "NT-parser extension" in rem and "DEFERRED" in rem

    def test_meta_tau7xv_no_stats_bump(self):
        m = _meta()
        # No book shipped → stats stay at the τ.7.x.u values.
        assert m["stats"]["books"] == 24
        assert m["stats"]["verses"] == 12691
        assert m["stats"]["books_outside_kjv"] == 14
        r = m["ingest_record_tau7xv"]
        assert r["ship_class"] == "PILOT-discovery-and-blocker"
        assert r["ingested_book_codes"] == []
        assert r["no_ingest_at_this_phase"] is True
        assert r["next_book"] == "BLOCKED-NT-parser-extension"

    def test_next_phase_blocked(self):
        t = _source_yaml()["ocr_strategy"]["tau7xv_ingest"]
        assert t["next_phase"] == "τ.7.x.w"
        nd = " ".join(t["next_phase_description"].split())
        assert "BLOCKED" in nd and "PAUSED" in nd


# ───────────── prior preservation (nothing regressed) ──────────────


class TestTau7XVPriorPreservation:
    def test_jubilees_stays_tau7xt(self):
        assert _source_yaml()["structural_map"]["jubilees"]["verified_at_phase"] == "τ.7.x.t"

    def test_one_enoch_stays_tau7xu(self):
        assert _source_yaml()["structural_map"]["one_enoch"]["verified_at_phase"] == "τ.7.x.u"

    def test_laodiceans_still_pi1_present_in_pdf_false(self):
        lao = _source_yaml()["structural_map"]["laodiceans"]
        assert lao["present_in_pdf"] is False
        assert lao["verified_at_phase"] == "Π.1"

    def test_prior_floor_dicts_untouched(self):
        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import JUBILEES_VERSE_COUNTS, ONE_ENOCH_VERSE_COUNTS

        assert sum(JUBILEES_VERSE_COUNTS.values()) == 1306
        assert sum(ONE_ENOCH_VERSE_COUNTS.values()) == 1064

    def test_all_prior_amharic_books_preserved(self):
        for book in (
            "gen",
            "ex",
            "lev",
            "num",
            "deu",
            "jos",
            "jdg",
            "rut",
            "psa",
            "2es",
            "tob",
            "jdt",
            "est",
            "mq1",
            "mq2",
            "mq3",
            "sir",
            "4ba",
            "bar",
            "wis",
            "paz",
            "bel",
            "jub",
            "1en",
        ):
            assert (AMHARIC_TEWAHEDO / f"{book}.py").is_file(), f"prior τ.7.x.* book {book} must persist"

    def test_parser_api_functions_untouched(self):
        src = (REPO / "scripts" / "extract_parallel_pdf.py").read_text(encoding="utf-8")
        assert "def parse_verses_from_text(" in src
        assert "def _parse_paragraph_mode(" in src
        assert "def renumber_against_floor(" in src

    def test_back_link_chain_tau7xu_to_v(self):
        s = _source_yaml()
        assert s["ocr_strategy"]["tau7xu_ingest"]["next_phase"] == "τ.7.x.v"
        assert s["ocr_strategy"]["tau7xv_ingest"]["next_phase"] == "τ.7.x.w"
