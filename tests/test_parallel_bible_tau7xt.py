"""τ.7.x.t — Amharic Jubilees (Mäṣḥafä Kufāle) full-book ingest
pins + the structural_map.jubilees upgrade + prior-pin conversion
+ the write_book_module repr()-serialization root-fix (2026-05-16).

TWENTY-THIRD τ.7.x.* per-book ship under D4-c Amharic-first + D1-a
per-book cadence (user "back to work ... much to render still" →
advance per PLAN; τ.7.x.s recorded next_book=jubilees). FIRST of
the two LARGE Π.1-mapped Tewahedo-distinctive books (1 Enoch
τ.7.x.u follows). The standalone-Amharic-Bible rendering FOUNDATION
per dev/SCOPE_2026-05-16-parallel-bible-standalone-bibles.md +
CLAUDE_PROJECT_RULES §1 — NOT a popup-language slot.

- `jub` p1454-1514; JUBILEES_VERSE_COUNTS (50 ch / 1306 v; R.H.
  Charles 1913 / VanderKam 1989 CSCO canonical CEILING; books.yaml
  `jub` ch_count:50 b15). 1075/1306 = 82.3% — HIGH band
  (protocanonical-class, cf. deu 81.4%; FAR above the deuterocanon-
  deep-PDF band). Content-confirmed (Jubilees = "The Little
  Genesis": creation-retelling at the first recovered verse). NOT
  a boundary error (τ.7.x.s already cross-validated p1454 `።ኩፉሌ።`
  + p1515→1 Enoch).

STRUCTURAL_MAP UPGRADE (not addition — jubilees pre-existed
Π.1-tentative): verified tentative→true, verified_at_phase
Π.1→τ.7.x.t; pdf_page_range [1454,1514] UNCHANGED (the durable
cross-validation anchor, cross-validated 3× at τ.7.x.q/r/s). The
prior τ.7.x.q + τ.7.x.s LIVE-state `jubilees_section_unchanged`
pins are CONVERTED by this ship → test_jubilees_page_range_anchor_
unchanged (the documented prior-pin-conversion-as-part-of-the-
triggering-ship pattern; τ.7.x.m est-skip precedent + memory
feedback_share_pin_pattern). The τ.7.x.r/s INGEST-RECORD
historical flags are NOT rewritten.

WRITER FIX: write_book_module previously escaped only single-
quotes — an OCR backslash produced an invalid escape (a
SyntaxWarning for backslash-space; silent corruption risk for
backslash-n / backslash-t / backslash-x). Root-fixed to repr()
serialization. Parser API (parse/paragraph/renumber) UNCHANGED;
the WRITER is hardened (honestly flagged, not claimed
zero-writer-delta).
"""

from __future__ import annotations

import ast
import sys
import warnings
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


def _verses(book: str) -> list[tuple]:
    tree = ast.parse((AMHARIC_TEWAHEDO / f"{book}.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "VERSES":
                    return ast.literal_eval(node.value)
    raise AssertionError(f"amharic-tewahedo/{book}.py must define VERSES")


def _constants(book: str) -> dict:
    tree = ast.parse((AMHARIC_TEWAHEDO / f"{book}.py").read_text(encoding="utf-8"))
    out: dict = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id != "VERSES":
                    try:
                        out[target.id] = ast.literal_eval(node.value)
                    except Exception:
                        pass
    return out


def _by_chapter(book: str) -> dict[int, list[tuple]]:
    out: dict[int, list[tuple]] = {}
    for ch, v, t in _verses(book):
        out.setdefault(ch, []).append((v, t))
    return out


def _floor():
    sys.path.insert(0, str(REPO / "scripts"))
    from extract_parallel_pdf import JUBILEES_VERSE_COUNTS

    return JUBILEES_VERSE_COUNTS


# ──────────────────────────── floor dict ───────────────────────────


class TestTau7XTJubileesVerseCounts:
    def test_symbol_present(self):
        assert isinstance(_floor(), dict)

    def test_fifty_chapters_contiguous(self):
        assert sorted(_floor().keys()) == list(range(1, 51))

    def test_total_verses_1306(self):
        assert sum(_floor().values()) == 1306

    def test_books_yaml_jub_ch_count_50(self):
        books = yaml.safe_load((REPO / "content" / "books.yaml").read_text(encoding="utf-8"))["books"]
        rec = next(b for b in books if b["code"] == "jub")
        assert rec["ch_count"] == 50
        assert rec["bxx"] == "b15"
        assert "Jubilees" in rec["title"]

    def test_gamma45_floor_coordination_crossvalidation(self):
        """The project's γ.4.5 Mäṣḥafä Kufāle annotation maxima in
        content/notes/jub.py never EXCEED this ceiling and match it
        exactly at the distinctive chapters (the τ.7.x.n δ.1.x-
        floor-coordination-proof discipline)."""
        f = _floor()
        assert f[6] == 38
        assert f[7] == 39
        assert f[9] == 15


# ─────────────────── structural_map.jubilees UPGRADE ───────────────


class TestTau7XTStructuralMapJubileesUpgraded:
    def _blk(self) -> dict:
        return _source_yaml()["structural_map"]["jubilees"]

    def test_book_codes(self):
        assert self._blk()["book_codes"] == ["jub"]

    def test_pdf_page_range_unchanged_anchor(self):
        # The durable cross-validation anchor — NEVER moves.
        assert self._blk()["pdf_page_range"] == [1454, 1514]

    def test_verified_upgraded_to_true(self):
        assert self._blk()["verified"] is True

    def test_verified_at_phase_upgraded_to_tau7xt(self):
        assert self._blk()["verified_at_phase"] == "τ.7.x.t"

    def test_chapter_count_expected_unchanged(self):
        assert self._blk()["chapter_count_expected"] == 50

    def test_notes_preserve_pi1_provenance_and_document_upgrade(self):
        notes = " ".join(self._blk()["notes"].split())
        assert "Discovered at Π.1" in notes  # Π.1 provenance preserved
        assert "UPGRADED tentative→true" in notes
        assert "τ.7.x.t" in notes
        assert "cross-validated THREE times" in notes


# ──────────────────────────── output module ────────────────────────


class TestTau7XTJubPy:
    def test_jub_py_exists(self):
        assert (AMHARIC_TEWAHEDO / "jub.py").is_file()

    def test_constants(self):
        c = _constants("jub")
        assert c.get("TRANSLATION") == "amharic-tewahedo"
        assert c.get("BOOK") == "jub"
        assert c.get("SOURCE_QUALITY") == "ocr-tier3"
        assert c.get("INGEST_PHASE") == "τ.7.x.t"

    def test_total_verse_floor(self):
        # Empirical at ship: 1075 (82.3% of the 1306-v ceiling).
        # Floor 1000 guards regression while tolerating OCR drift.
        assert len(_verses("jub")) >= 1000

    def test_first_verse_is_1_1(self):
        ch, v, text = _verses("jub")[0]
        assert (ch, v) == (1, 1)
        assert text

    def test_geez_jub_not_created(self):
        # D4-c — the Geʽez stream (the standalone Geʽez Bible
        # foundation) follows the Amharic stream at τ.6.x.2.j+.
        assert not (GEEZ_TEWAHEDO / "jub.py").exists()


# ─────────────────────────── coverage shape ────────────────────────


class TestTau7XTJubCoverage:
    """Empirical: ch 1-38 full; 39 partial (10/18); 40-50 empty;
    0 overflow. 82.3% HIGH band (cf. deu 81.4% / gen 85.3%);
    content-confirmed Jubilees ("The Little Genesis")."""

    def test_chapters_1_through_38_fully_populated(self):
        f = _floor()
        by = _by_chapter("jub")
        for ch in range(1, 39):
            assert len(by.get(ch, [])) == f[ch], (
                f"τ.7.x.t jub ch {ch} must have exactly {f[ch]} verses; got {len(by.get(ch, []))}"
            )

    def test_chapter_39_partial(self):
        f = _floor()
        got = len(_by_chapter("jub").get(39, []))
        assert 1 <= got < f[39]

    def test_chapters_40_through_50_empty(self):
        by = _by_chapter("jub")
        for ch in range(40, 51):
            assert len(by.get(ch, [])) == 0

    def test_no_overflow_above_chapter_50(self):
        by = _by_chapter("jub")
        assert sum(len(v) for ch, v in by.items() if ch > 50) == 0


# ───────────────── writer repr()-serialization root-fix ────────────


class TestTau7XTWriterSerializationFix:
    def test_writer_uses_repr_serialization(self):
        src = (REPO / "scripts" / "extract_parallel_pdf.py").read_text(encoding="utf-8")
        assert "({ch}, {v}, {text!r})," in src, "write_book_module must serialize via repr()"
        assert 'text.replace("\'", "\\\\\'")' not in src, "the old single-quote-only escaper must be gone"

    def test_jub_py_has_no_invalid_escape_sequence(self):
        """jub recovered an OCR backslash at 28:25; under the fixed
        writer it must parse with ZERO SyntaxWarning."""
        src = (AMHARIC_TEWAHEDO / "jub.py").read_text(encoding="utf-8")
        with warnings.catch_warnings():
            warnings.simplefilter("error", SyntaxWarning)
            ast.parse(src)  # raises if any invalid escape remains

    def test_jub_28_25_backslash_faithfully_captured(self):
        hits = [r for r in _verses("jub") if r[0] == 28 and r[1] == 25]
        assert hits, "jub 28:25 must exist"
        # ast.literal_eval already decoded the escaped backslash →
        # the actual string carries a literal backslash (faithful
        # ocr-tier3 capture), correctly serialized.
        assert "\\" in hits[0][2]


# ───────────────────── _source.yaml ingest block ───────────────────


class TestTau7XTSourceYamlIngestBlock:
    def _blk(self) -> dict:
        return _source_yaml()["ocr_strategy"]["tau7xt_ingest"]

    def test_block_exists(self):
        assert "tau7xt_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert self._blk()["shipped_at_phase"] == "τ.7.x.t"

    def test_structural_map_upgrade_recorded(self):
        u = self._blk()["structural_map_upgrade"]
        assert u["section"] == "jubilees"
        assert u["pdf_page_range"] == [1454, 1514]
        assert u["verified"] == "tentative→true"
        assert u["verified_at_phase"] == "Π.1→τ.7.x.t"

    def test_prior_pin_conversion_documented(self):
        conv = " ".join(self._blk()["prior_pin_conversion"].split())
        assert "test_jubilees_page_range_anchor_unchanged" in conv
        assert "τ.7.x.q" in conv and "τ.7.x.s" in conv

    def test_writer_serialization_fix_documented(self):
        fix = " ".join(self._blk()["writer_serialization_fix"].split())
        assert "repr()" in fix and "write_book_module" in fix

    def test_parser_api_zero_delta_writer_flagged(self):
        api = " ".join(self._blk()["parser_api_change"].split())
        assert "PARSER API UNCHANGED" in api
        assert "30-ship" in api
        assert "WRITER" in api  # honestly flagged, not claimed zero-writer-delta

    def test_empirical_validation(self):
        ev = self._blk()["empirical_validation"]
        assert ev["renumbered_verse_count"] == 1075
        assert ev["coverage_pct"] == 82.3

    def test_next_phase_tau7xu(self):
        assert self._blk()["next_phase"] == "τ.7.x.u"

    def test_pipeline_reused_back_link(self):
        assert self._blk()["pipeline_reused_at_phase"] == "τ.7.x.t"


# ─────────────────────── _meta.yaml ingest record ──────────────────


class TestTau7XTMetaYamlIngestRecord:
    def test_stats_books_at_least_twenty_three(self):
        assert _meta()["stats"]["books"] >= 23

    def test_stats_verses_at_least_11885(self):
        assert _meta()["stats"]["verses"] >= 11885

    def test_stats_books_outside_kjv_thirteen(self):
        """+jub (Tewahedo-distinctive, outside KJV) on top of 12."""
        assert _meta()["stats"]["books_outside_kjv"] >= 13

    def test_tau7xt_ingest_record(self):
        r = _meta()["ingest_record_tau7xt"]
        assert r["phase"] == "τ.7.x.t"
        assert r["ingested_book_codes"] == ["jub"]
        assert r["coverage"]["verses_extracted"] == 1075
        assert r.get("tewahedo_distinctive") is True

    def test_tau7xs_next_book_was_jubilees(self):
        # The τ.7.x.s prediction came true (not rewritten — history).
        assert _meta()["ingest_record_tau7xs"]["next_book"] == "jubilees"

    def test_prior_ingest_records_present(self):
        m = _meta()
        assert "ingest_record" in m
        for tag in ("tau7xn", "tau7xo", "tau7xp", "tau7xq", "tau7xr", "tau7xs"):
            assert f"ingest_record_{tag}" in m, f"prior ingest record missing: {tag}"


# ────────── prior-pin conversion + preservation ───────────


class TestTau7XTPriorPinConversionAndPreservation:
    def test_tau7xq_jubilees_pin_converted(self):
        src = (REPO / "tests" / "test_parallel_bible_tau7xq.py").read_text(encoding="utf-8")
        assert "def test_jubilees_page_range_anchor_unchanged(" in src
        assert "def test_jubilees_section_unchanged(" not in src
        assert 'in ("Π.1", "τ.7.x.t")' in src

    def test_tau7xs_jubilees_pin_converted(self):
        src = (REPO / "tests" / "test_parallel_bible_tau7xs.py").read_text(encoding="utf-8")
        assert "def test_jubilees_page_range_anchor_unchanged(" in src
        assert "def test_jubilees_section_unchanged(" not in src

    def test_parser_api_functions_untouched(self):
        src = (REPO / "scripts" / "extract_parallel_pdf.py").read_text(encoding="utf-8")
        assert "def parse_verses_from_text(" in src
        assert "def _parse_paragraph_mode(" in src
        assert "def renumber_against_floor(" in src

    def test_prior_floor_dicts_untouched(self):
        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import (
            BEL_AND_THE_DRAGON_VERSE_COUNTS,
            PRAYER_OF_AZARIAH_VERSE_COUNTS,
            WISDOM_OF_SOLOMON_VERSE_COUNTS,
        )

        assert sum(WISDOM_OF_SOLOMON_VERSE_COUNTS.values()) == 436
        assert sum(PRAYER_OF_AZARIAH_VERSE_COUNTS.values()) == 68
        assert sum(BEL_AND_THE_DRAGON_VERSE_COUNTS.values()) == 42

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
        ):
            assert (AMHARIC_TEWAHEDO / f"{book}.py").is_file(), f"prior τ.7.x.* book {book} must persist"

    def test_tau7xs_sus_deferral_preserved(self):
        s = _source_yaml()
        assert s["structural_map"]["susanna"]["present_in_pdf"] is False
        assert not (AMHARIC_TEWAHEDO / "sus.py").exists()

    def test_back_link_chain_tau7xs_to_t(self):
        s = _source_yaml()
        assert s["ocr_strategy"]["tau7xs_ingest"]["next_phase"] == "τ.7.x.t"
        assert s["ocr_strategy"]["tau7xt_ingest"]["next_phase"] == "τ.7.x.u"
