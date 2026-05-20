"""τ.7.x.o + τ.7.x.p — Amharic Sirach + Paralipomena Jeremiah
(4 Baruch) full-book ingest pins (2026-05-15).

SEVENTEENTH + EIGHTEENTH τ.7.x.* per-book ships under D4-c Amharic-
first + D1-a per-book cadence. Together they drain the SIXTH EOTC-
parallel block p1379-1428 (user "commit and continue" → advance per
PLAN):
- **τ.7.x.o Sirach** (`sir`, Ecclesiasticus): p1379-1418;
  SIRACH_VERSE_COUNTS (51 ch / 1413 v; NRSV/Göttingen-Ziegler LXX;
  books.yaml `sir` ch_count:51 b36). Deuterocanonical. OPENS the
  sixth EOTC-parallel block.
- **τ.7.x.p Paralipomena Jeremiah / 4 Baruch** (`4ba`): p1419-1428;
  FOUR_BARUCH_VERSE_COUNTS (9 ch / 191 v; Kraft-Purintun 1972;
  books.yaml `4ba` ch_count:9 b42). EOTC broader-canon
  pseudepigraphon; the Ethiopic ch-9 Christian expansion is
  empirically visible at 1:3. DRAINS the sixth block.

Structural discovery (τ.7.x.o scan p1376-1440, the same running-
header + opening-verse + colophon method that corrected the Mäqabyan
subsections at τ.7.x.n): mq3 ends p1378 (τ.7.x.n-confirmed); Sir 2:1
`ልጄ ስእግዚአብሔር ትገዛ ዘንድ` at p1380; Sir 6:18 at p1383; 4 Baruch 9
Jeremiah-stoning at p1426; Wisdom of Solomon (the seventh block)
Wis 2:6-7 content at p1432-1433. The τ.7.x.h coarse "p1368-1421"
estimate is SUPERSEDED.

Coverage: Sirach 52.2% (deep-PDF deuterocanon band, cf. tob 48.0%;
Sir 1/Prologue partially lost — honest ocr-tier3 leading-content
loss per τ.6.x.0b, NOT a boundary error; the τ.7.x.n anomaly-check
discipline was applied and passed), 4 Baruch 88.0% (highest since
τ.7.x.i Psalms 88.6%; only ch 9 partial, NO empty chapters). Both
renumber cleanly. Zero-parser-API-delta preserved (17th + 18th
consecutive; 26-ship across both columns).

Pins validate: floor dicts, the 2 structural_map blocks, sir.py/
4ba.py modules, coverage shape, _source.yaml + _meta.yaml records,
the back-link chain tau7xn→o→p, and that all prior τ.7.x.a-n +
τ.6.x.2.a-h closed-arc pins remain green.
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


def _floors():
    sys.path.insert(0, str(REPO / "scripts"))
    from extract_parallel_pdf import FOUR_BARUCH_VERSE_COUNTS, SIRACH_VERSE_COUNTS

    return SIRACH_VERSE_COUNTS, FOUR_BARUCH_VERSE_COUNTS


# ──────────────────────────── floor dicts ──────────────────────────


class TestTau7XOSirachVerseCounts:
    def test_symbol_present(self):
        sir, _ = _floors()
        assert isinstance(sir, dict)

    def test_fifty_one_chapters(self):
        sir, _ = _floors()
        assert sorted(sir.keys()) == list(range(1, 52))

    def test_total_verses_1413(self):
        sir, _ = _floors()
        assert sum(sir.values()) == 1413

    def test_books_yaml_sir_ch_count_51(self):
        books = yaml.safe_load((REPO / "content" / "books.yaml").read_text(encoding="utf-8"))["books"]
        rec = next(b for b in books if b["code"] == "sir")
        assert rec["ch_count"] == 51
        assert rec["bxx"] == "b36"
        assert "Sirach" in rec["title"] or "Ecclesiasticus" in rec["title"]


class TestTau7XPFourBaruchVerseCounts:
    def test_symbol_present(self):
        _, fba = _floors()
        assert isinstance(fba, dict)

    def test_nine_chapters(self):
        _, fba = _floors()
        assert sorted(fba.keys()) == list(range(1, 10))

    def test_total_verses_191(self):
        _, fba = _floors()
        assert sum(fba.values()) == 191

    def test_books_yaml_4ba_ch_count_9(self):
        books = yaml.safe_load((REPO / "content" / "books.yaml").read_text(encoding="utf-8"))["books"]
        rec = next(b for b in books if b["code"] == "4ba")
        assert rec["ch_count"] == 9
        assert rec["bxx"] == "b42"
        assert "Baruch" in rec["title"] or "Paralipomena" in rec["title"]


# ─────────────────────────── structural_map ────────────────────────


class TestTau7XOStructuralMapSirach:
    def _blk(self) -> dict:
        return _source_yaml()["structural_map"]["sirach"]

    def test_block_present(self):
        assert "sirach" in _source_yaml()["structural_map"]

    def test_book_codes(self):
        assert self._blk()["book_codes"] == ["sir"]

    def test_pdf_page_range_1379_1418(self):
        assert self._blk()["pdf_page_range"] == [1379, 1418]

    def test_verified_at_tau7xo(self):
        assert self._blk()["verified"] is True
        assert self._blk()["verified_at_phase"] == "τ.7.x.o"

    def test_chapter_count_expected_51(self):
        assert self._blk()["chapter_count_expected"] == 51

    def test_notes_document_boundary(self):
        notes = self._blk()["notes"]
        assert "1378" in notes and "Sir 2:1" in notes


class TestTau7XPStructuralMapParalipomena:
    def _blk(self) -> dict:
        return _source_yaml()["structural_map"]["paralipomena_jeremiah"]

    def test_block_present(self):
        assert "paralipomena_jeremiah" in _source_yaml()["structural_map"]

    def test_book_codes(self):
        assert self._blk()["book_codes"] == ["4ba"]

    def test_pdf_page_range_1419_1428(self):
        assert self._blk()["pdf_page_range"] == [1419, 1428]

    def test_verified_at_tau7xp(self):
        assert self._blk()["verified"] is True
        assert self._blk()["verified_at_phase"] == "τ.7.x.p"

    def test_chapter_count_expected_9(self):
        assert self._blk()["chapter_count_expected"] == 9

    def test_notes_document_recension_and_next_block(self):
        notes = self._blk()["notes"]
        assert "Kraft-Purintun" in notes
        assert "Wisdom of Solomon" in notes


# ──────────────────────────── output modules ───────────────────────


class TestTau7XOSirPy:
    def test_sir_py_exists(self):
        assert (AMHARIC_TEWAHEDO / "sir.py").is_file()

    def test_constants(self):
        c = _constants("sir")
        assert c.get("TRANSLATION") == "amharic-tewahedo"
        assert c.get("BOOK") == "sir"
        assert c.get("SOURCE_QUALITY") == "ocr-tier3"
        assert c.get("INGEST_PHASE") == "τ.7.x.o"

    def test_total_verse_floor(self):
        # Empirical at ship: 737. Floor 650 guards regression.
        assert len(_verses("sir")) >= 650

    def test_first_verse_is_1_1(self):
        ch, v, text = _verses("sir")[0]
        assert (ch, v) == (1, 1)
        assert text


class TestTau7XP4baPy:
    def test_4ba_py_exists(self):
        assert (AMHARIC_TEWAHEDO / "4ba.py").is_file()

    def test_constants(self):
        c = _constants("4ba")
        assert c.get("TRANSLATION") == "amharic-tewahedo"
        assert c.get("BOOK") == "4ba"
        assert c.get("SOURCE_QUALITY") == "ocr-tier3"
        assert c.get("INGEST_PHASE") == "τ.7.x.p"

    def test_total_verse_floor(self):
        # Empirical at ship: 168. Floor 150 guards regression.
        assert len(_verses("4ba")) >= 150

    def test_first_verse_is_1_1(self):
        ch, v, text = _verses("4ba")[0]
        assert (ch, v) == (1, 1)
        assert text


# ─────────────────────────── coverage shape ────────────────────────


class TestTau7XOSirCoverage:
    """Empirical: ch 1-26 full; 27 partial (18/30); 28-51 empty;
    0 overflow. Honest deep-PDF deuterocanon band per τ.6.x.0b."""

    def test_chapters_1_through_26_fully_populated(self):
        sir, _ = _floors()
        by = _by_chapter("sir")
        for ch in range(1, 27):
            assert len(by.get(ch, [])) == sir[ch], (
                f"τ.7.x.o sir ch {ch} must have exactly {sir[ch]} verses; got {len(by.get(ch, []))}"
            )

    def test_chapter_27_partial(self):
        sir, _ = _floors()
        got = len(_by_chapter("sir").get(27, []))
        assert 1 <= got < sir[27]

    def test_chapters_28_through_51_empty(self):
        by = _by_chapter("sir")
        for ch in range(28, 52):
            assert len(by.get(ch, [])) == 0, f"τ.7.x.o sir ch {ch} should be empty at ocr-tier3"

    def test_no_overflow_above_chapter_51(self):
        by = _by_chapter("sir")
        assert sum(len(v) for ch, v in by.items() if ch > 51) == 0


class TestTau7XP4baCoverage:
    """Empirical: ch 1-8 full; 9 partial (9/32); NO empty chapters;
    0 overflow. Strong 88.0% — 4 Baruch is short narrative."""

    def test_chapters_1_through_8_fully_populated(self):
        _, fba = _floors()
        by = _by_chapter("4ba")
        for ch in range(1, 9):
            assert len(by.get(ch, [])) == fba[ch], (
                f"τ.7.x.p 4ba ch {ch} must have exactly {fba[ch]} verses; got {len(by.get(ch, []))}"
            )

    def test_chapter_9_partial(self):
        _, fba = _floors()
        got = len(_by_chapter("4ba").get(9, []))
        assert 1 <= got < fba[9]

    def test_no_empty_chapters(self):
        by = _by_chapter("4ba")
        for ch in range(1, 10):
            assert len(by.get(ch, [])) > 0, f"τ.7.x.p 4ba ch {ch} must be non-empty (88% coverage, all 9 ch present)"

    def test_no_overflow_above_chapter_9(self):
        by = _by_chapter("4ba")
        assert sum(len(v) for ch, v in by.items() if ch > 9) == 0


# ───────────────────── _source.yaml ingest blocks ──────────────────


class TestTau7XOSourceYamlIngestBlock:
    def _blk(self) -> dict:
        return _source_yaml()["ocr_strategy"]["tau7xo_ingest"]

    def test_block_exists(self):
        assert "tau7xo_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert self._blk()["shipped_at_phase"] == "τ.7.x.o"

    def test_structural_map_addition(self):
        sma = self._blk()["structural_map_addition"]
        assert sma["section"] == "sirach"
        assert sma["pdf_page_range"] == [1379, 1418]
        assert sma["chapter_count_expected"] == 51

    def test_empirical_validation(self):
        ev = self._blk()["empirical_validation"]
        assert ev["coverage_pct"] == 52.2
        assert ev["renumbered_verse_count"] == 737

    def test_anomaly_check_documented(self):
        """The τ.7.x.n anomaly-check discipline was applied — Sirach's
        honest-low 52.2% is documented as NOT a boundary error.
        (Whitespace-normalized: the YAML `|` literal block preserves
        line breaks, so the phrase may span a newline.)"""
        band = " ".join(self._blk()["empirical_validation"]["coverage_band_position"].split())
        assert "NOT a boundary error" in band and "τ.7.x.n" in band

    def test_parser_api_change_zero(self):
        assert "No parser API changes" in self._blk()["parser_api_change"]
        assert "25-ship" in self._blk()["parser_api_change"]

    def test_next_phase_tau7xp(self):
        assert self._blk()["next_phase"] == "τ.7.x.p"

    def test_pipeline_reused_back_link(self):
        assert self._blk()["pipeline_reused_at_phase"] == "τ.7.x.p"


class TestTau7XPSourceYamlIngestBlock:
    def _blk(self) -> dict:
        return _source_yaml()["ocr_strategy"]["tau7xp_ingest"]

    def test_block_exists(self):
        assert "tau7xp_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert self._blk()["shipped_at_phase"] == "τ.7.x.p"

    def test_structural_map_addition(self):
        sma = self._blk()["structural_map_addition"]
        assert sma["section"] == "paralipomena_jeremiah"
        assert sma["pdf_page_range"] == [1419, 1428]
        assert sma["chapter_count_expected"] == 9

    def test_empirical_validation(self):
        ev = self._blk()["empirical_validation"]
        assert ev["coverage_pct"] == 88.0
        assert ev["renumbered_verse_count"] == 168
        assert ev["chapters_missing_count"] == 0

    def test_block_drained_p1379_1428(self):
        assert self._blk()["block_drained"] == "p1379-1428"

    def test_recension_context_documented(self):
        rc = self._blk()["structural_map_addition"]["recension_context"]
        assert "Kraft-Purintun" in rc and "Ethiopic" in rc

    def test_next_phase_tau7xq(self):
        assert self._blk()["next_phase"] == "τ.7.x.q"


# ─────────────────────── _meta.yaml ingest records ─────────────────


class TestTau7XOPMetaYamlIngestRecords:
    def test_stats_books_at_least_eighteen(self):
        assert _meta()["stats"]["books"] >= 18

    def test_stats_verses_at_least_10456(self):
        assert _meta()["stats"]["verses"] >= 10456

    def test_stats_books_outside_kjv_eight(self):
        """+sir (deuterocanonical) +4ba (EOTC broader-canon) on top
        of the prior 6 (2es/tob/jdt/mq1/mq2/mq3)."""
        assert _meta()["stats"]["books_outside_kjv"] >= 8

    def test_tau7xo_ingest_record(self):
        r = _meta()["ingest_record_tau7xo"]
        assert r["phase"] == "τ.7.x.o"
        assert r["ingested_book_codes"] == ["sir"]
        assert r["coverage"]["verses_extracted"] == 737
        assert r.get("deuterocanonical") is True

    def test_tau7xp_ingest_record(self):
        r = _meta()["ingest_record_tau7xp"]
        assert r["phase"] == "τ.7.x.p"
        assert r["ingested_book_codes"] == ["4ba"]
        assert r["coverage"]["verses_extracted"] == 168
        assert r.get("block_drained") == "p1379-1428"

    def test_tau7xn_pipeline_reused_back_link_added(self):
        assert _meta()["ingest_record_tau7xn"]["pipeline_reused_at_phase"] == "τ.7.x.o"

    def test_prior_ingest_records_present(self):
        m = _meta()
        assert "ingest_record" in m
        for tag in ("tau7xh", "tau7xl", "tau7xm", "tau7xn"):
            assert f"ingest_record_{tag}" in m, f"prior ingest record missing: {tag}"


# ───────────── zero-API-delta + prior-pin preservation ─────────────


class TestTau7XOPZeroApiDeltaAndPriorPins:
    def test_cli_renumber_choices_extended(self):
        src = (REPO / "scripts" / "extract_parallel_pdf.py").read_text(encoding="utf-8")
        assert '"sirach"' in src and '"four_baruch"' in src
        assert src.count("SIRACH_VERSE_COUNTS") >= 3
        assert src.count("FOUR_BARUCH_VERSE_COUNTS") >= 3

    def test_parser_api_functions_untouched(self):
        src = (REPO / "scripts" / "extract_parallel_pdf.py").read_text(encoding="utf-8")
        assert "def parse_verses_from_text(" in src
        assert "def _parse_paragraph_mode(" in src
        assert "def renumber_against_floor(" in src

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
        ):
            assert (AMHARIC_TEWAHEDO / f"{book}.py").is_file(), f"prior τ.7.x.* book {book} must persist"

    def test_geez_sir_4ba_bar_wis_paz_bel_jub_ingested_one_enoch_still_deferred(self):
        """MIGRATED at the τ.6.x.2.t ship-time (2026-05-20) per memory
        `feedback_share_pin_pattern` + the τ.6.x.2.j-s precedent.
        Originally asserted the Geʽez `sir.py` AND `4ba.py` must NOT
        exist (τ.7.x.o/τ.7.x.p were --lang amharic; D4-c deferral).
        τ.6.x.2.o flipped the `sir` half; τ.6.x.2.p flipped the `4ba`
        half; τ.6.x.2.q flipped the `bar` half; τ.6.x.2.r flipped the
        `wis` half; τ.6.x.2.s flipped the Daniel-additions cluster
        paz+bel of the eighth EOTC-parallel block; τ.6.x.2.t (the
        SIXTH ship of the deuterocanon Geʽez catchup — opens the
        ninth EOTC-parallel block with the Tewahedo-distinctive
        Jubilees / Mäṣḥafä Kufāle) wrote the ocr-tier3 parallel-PDF
        Geʽez jub.py. The `jub` half is now flipped to a durable
        positive invariant (jub.py exists at ocr-tier3 with
        INGEST_PHASE τ.6.x.2.t NOT τ.7.x.t). The `one_enoch` (1en —
        FINAL book in the catchup queue) is the NEW deferred pin —
        to be flipped at the next τ.6.x.2.* ship when the Geʽez
        1 Enoch ship drains the tenth (and final) EOTC-parallel
        block (per the catchup queue: sir → 4ba → bar → wisdom →
        daniel-additions → jubilees → 1 enoch). Susanna (sus)
        DEFERRED to τ.6.x.3 (not present in this PDF)."""
        import ast

        assert (GEEZ_TEWAHEDO / "sir.py").is_file(), "Geʽez sir.py must EXIST after the τ.6.x.2.o catchup ship"
        tree = ast.parse((GEEZ_TEWAHEDO / "sir.py").read_text(encoding="utf-8"))
        consts = {
            t.id: ast.literal_eval(n.value)
            for n in ast.walk(tree)
            if isinstance(n, ast.Assign)
            for t in n.targets
            if isinstance(t, ast.Name) and t.id in ("SOURCE_QUALITY", "INGEST_PHASE", "BOOK", "TRANSLATION")
        }
        assert consts.get("SOURCE_QUALITY") == "ocr-tier3"
        assert consts.get("INGEST_PHASE") == "τ.6.x.2.o"
        assert consts.get("BOOK") == "sir"
        assert consts.get("TRANSLATION") == "geez-tewahedo"
        # 4ba half FLIPPED at τ.6.x.2.p — same durable positive invariant
        assert (GEEZ_TEWAHEDO / "4ba.py").is_file(), "Geʽez 4ba.py must EXIST after the τ.6.x.2.p catchup ship"
        tree4ba = ast.parse((GEEZ_TEWAHEDO / "4ba.py").read_text(encoding="utf-8"))
        consts4ba = {
            t.id: ast.literal_eval(n.value)
            for n in ast.walk(tree4ba)
            if isinstance(n, ast.Assign)
            for t in n.targets
            if isinstance(t, ast.Name) and t.id in ("SOURCE_QUALITY", "INGEST_PHASE", "BOOK", "TRANSLATION")
        }
        assert consts4ba.get("SOURCE_QUALITY") == "ocr-tier3"
        assert consts4ba.get("INGEST_PHASE") == "τ.6.x.2.p"
        assert consts4ba.get("BOOK") == "4ba"
        assert consts4ba.get("TRANSLATION") == "geez-tewahedo"
        # bar half FLIPPED at τ.6.x.2.q — same durable positive invariant
        assert (GEEZ_TEWAHEDO / "bar.py").is_file(), "Geʽez bar.py must EXIST after the τ.6.x.2.q catchup ship"
        treebar = ast.parse((GEEZ_TEWAHEDO / "bar.py").read_text(encoding="utf-8"))
        constsbar = {
            t.id: ast.literal_eval(n.value)
            for n in ast.walk(treebar)
            if isinstance(n, ast.Assign)
            for t in n.targets
            if isinstance(t, ast.Name) and t.id in ("SOURCE_QUALITY", "INGEST_PHASE", "BOOK", "TRANSLATION")
        }
        assert constsbar.get("SOURCE_QUALITY") == "ocr-tier3"
        assert constsbar.get("INGEST_PHASE") == "τ.6.x.2.q"
        assert constsbar.get("BOOK") == "bar"
        assert constsbar.get("TRANSLATION") == "geez-tewahedo"
        # wis half FLIPPED at τ.6.x.2.r — same durable positive invariant
        assert (GEEZ_TEWAHEDO / "wis.py").is_file(), "Geʽez wis.py must EXIST after the τ.6.x.2.r catchup ship"
        treewis = ast.parse((GEEZ_TEWAHEDO / "wis.py").read_text(encoding="utf-8"))
        constswis = {
            t.id: ast.literal_eval(n.value)
            for n in ast.walk(treewis)
            if isinstance(n, ast.Assign)
            for t in n.targets
            if isinstance(t, ast.Name) and t.id in ("SOURCE_QUALITY", "INGEST_PHASE", "BOOK", "TRANSLATION")
        }
        assert constswis.get("SOURCE_QUALITY") == "ocr-tier3"
        assert constswis.get("INGEST_PHASE") == "τ.6.x.2.r"
        assert constswis.get("BOOK") == "wis"
        assert constswis.get("TRANSLATION") == "geez-tewahedo"
        # paz half FLIPPED at τ.6.x.2.s — same durable positive invariant
        assert (GEEZ_TEWAHEDO / "paz.py").is_file(), "Geʽez paz.py must EXIST after the τ.6.x.2.s catchup ship"
        treepaz = ast.parse((GEEZ_TEWAHEDO / "paz.py").read_text(encoding="utf-8"))
        constspaz = {
            t.id: ast.literal_eval(n.value)
            for n in ast.walk(treepaz)
            if isinstance(n, ast.Assign)
            for t in n.targets
            if isinstance(t, ast.Name) and t.id in ("SOURCE_QUALITY", "INGEST_PHASE", "BOOK", "TRANSLATION")
        }
        assert constspaz.get("SOURCE_QUALITY") == "ocr-tier3"
        assert constspaz.get("INGEST_PHASE") == "τ.6.x.2.s"
        assert constspaz.get("BOOK") == "paz"
        assert constspaz.get("TRANSLATION") == "geez-tewahedo"
        # bel half ALSO FLIPPED at τ.6.x.2.s — combined ship drains Daniel-additions cluster
        assert (GEEZ_TEWAHEDO / "bel.py").is_file(), "Geʽez bel.py must EXIST after the τ.6.x.2.s catchup ship"
        treebel = ast.parse((GEEZ_TEWAHEDO / "bel.py").read_text(encoding="utf-8"))
        constsbel = {
            t.id: ast.literal_eval(n.value)
            for n in ast.walk(treebel)
            if isinstance(n, ast.Assign)
            for t in n.targets
            if isinstance(t, ast.Name) and t.id in ("SOURCE_QUALITY", "INGEST_PHASE", "BOOK", "TRANSLATION")
        }
        assert constsbel.get("SOURCE_QUALITY") == "ocr-tier3"
        assert constsbel.get("INGEST_PHASE") == "τ.6.x.2.s"
        assert constsbel.get("BOOK") == "bel"
        assert constsbel.get("TRANSLATION") == "geez-tewahedo"
        # jub half FLIPPED at τ.6.x.2.t — same durable positive invariant
        assert (GEEZ_TEWAHEDO / "jub.py").is_file(), "Geʽez jub.py must EXIST after the τ.6.x.2.t catchup ship"
        treejub = ast.parse((GEEZ_TEWAHEDO / "jub.py").read_text(encoding="utf-8"))
        constsjub = {
            t.id: ast.literal_eval(n.value)
            for n in ast.walk(treejub)
            if isinstance(n, ast.Assign)
            for t in n.targets
            if isinstance(t, ast.Name) and t.id in ("SOURCE_QUALITY", "INGEST_PHASE", "BOOK", "TRANSLATION")
        }
        assert constsjub.get("SOURCE_QUALITY") == "ocr-tier3"
        assert constsjub.get("INGEST_PHASE") == "τ.6.x.2.t"
        assert constsjub.get("BOOK") == "jub"
        assert constsjub.get("TRANSLATION") == "geez-tewahedo"
        # `one_enoch` (1en — FINAL book in the catchup queue) is the new deferred pin
        assert not (GEEZ_TEWAHEDO / "1en.py").exists(), (
            "Geʽez 1en.py must NOT exist yet — deferred to next τ.6.x.2.* ship"
        )

    def test_tau7xn_meqabyan_pins_preserved(self):
        s = _source_yaml()
        assert s["ocr_strategy"]["tau7xn_ingest"]["block_drained"] == "p1318-1378"
        assert s["structural_map"]["meqabyan_i"]["pdf_page_range"] == [1318, 1350]
        assert s["structural_map"]["meqabyan"]["subsections"]["mq2"] == [1351, 1368]

    def test_tau7xm_pins_preserved(self):
        s = _source_yaml()
        assert s["structural_map"]["esther"]["pdf_page_range"] == [1308, 1317]
        assert (AMHARIC_TEWAHEDO / "est.py").is_file()


class TestTau7XOPStateDocs:
    def test_session_state_mentions_tau7xo(self):
        txt = (REPO / "dev" / "SESSION_STATE.md").read_text(encoding="utf-8")
        assert "τ.7.x.o" in txt

    def test_changelog_records_tau7xo(self):
        txt = (REPO / "dev" / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "τ.7.x.o" in txt

    def test_plan_ledger_records_tau7xo(self):
        txt = (REPO / "dev" / "PLAN_2026-05-09.md").read_text(encoding="utf-8")
        assert "τ.7.x.o" in txt
