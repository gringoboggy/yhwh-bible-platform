"""τ.7.x.q + τ.7.x.r — Amharic Baruch + Wisdom of Solomon full-book
ingest pins (2026-05-15).

NINETEENTH + TWENTIETH τ.7.x.* per-book ships under D4-c Amharic-
first + D1-a per-book cadence. Together they drain the two MAJOR
books of the SEVENTH EOTC-parallel block (user "continue" → advance
per PLAN):
- **τ.7.x.q Baruch** (`bar`): p1429-1431; BARUCH_VERSE_COUNTS
  (5 ch / 141 v; NRSV/LXX; books.yaml `bar` ch_count:5 b40).
  Deuterocanonical. OPENS the seventh block. Highly compressed in
  the PDF (3 pp / 5 ch) → honest-low 33.3% (NOT a boundary error;
  the τ.7.x.n anomaly-check discipline applied — content confirmed
  Baruch via dry-run: Bar 2:3 siege + Bar 3 wisdom + Bar 5
  restoration). The Letter of Jeremiah (lje) is the SEPARATE
  books.yaml b41 book — no distinct banner in scan, deferred to
  τ.6.x.3.
- **τ.7.x.r Wisdom of Solomon** (`wis`): p1432-1448;
  WISDOM_OF_SOLOMON_VERSE_COUNTS (19 ch / 436 v; NRSV/Göttingen-
  Ziegler LXX; books.yaml `wis` ch_count:19 b33). Deuterocanonical.
  DRAINS the bar+wis major-book pair. 58.3% (deep-PDF band, cf.
  sir 52.2%; content confirmed via dry-run: Wis 7:1 "I also am
  mortal").

Structural discovery (τ.7.x.q scan p1426-1456, same method as
τ.7.x.o + the τ.7.x.n correction): 4ba ends p1428 (τ.7.x.p-
confirmed); Baruch p1429-1431; Wisdom p1432-1448; the Daniel-
additions cluster paz/sus/bel (`ተረፈ ዳንኤል`) p1449-1453 (a SEPARATE
later ship); Jubilees opens p1454 (`።ኩፉሌ።`) EXACTLY matching the
pre-existing Π.1 structural_map.jubilees [1454,1514] — decisive
cross-validation (Π.1 jubilees section NOT modified).

Floors per the τ.6.x.0b honesty contract: no project-internal
bar/wis enumeration (no candidates/notes, like sir/4ba) — NRSV/LXX
canonical CEILING; τ.6.x.3 reconciles recension + the lje-as-
Baruch-6 ambiguity. Zero-parser-API-delta preserved (19th + 20th
consecutive; 28-ship across both columns).

Pins validate: floor dicts, the 2 structural_map blocks, bar.py/
wis.py modules, coverage shape, the honest-low documentation, the
Jubilees cross-validation, _source.yaml + _meta.yaml records, the
back-link chain tau7xp→q→r, and prior-pin preservation.
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
    from extract_parallel_pdf import BARUCH_VERSE_COUNTS, WISDOM_OF_SOLOMON_VERSE_COUNTS

    return BARUCH_VERSE_COUNTS, WISDOM_OF_SOLOMON_VERSE_COUNTS


# ──────────────────────────── floor dicts ──────────────────────────


class TestTau7XQBaruchVerseCounts:
    def test_symbol_present(self):
        bar, _ = _floors()
        assert isinstance(bar, dict)

    def test_five_chapters(self):
        bar, _ = _floors()
        assert sorted(bar.keys()) == list(range(1, 6))

    def test_total_verses_141(self):
        bar, _ = _floors()
        assert sum(bar.values()) == 141

    def test_books_yaml_bar_ch_count_5(self):
        books = yaml.safe_load((REPO / "content" / "books.yaml").read_text(encoding="utf-8"))["books"]
        rec = next(b for b in books if b["code"] == "bar")
        assert rec["ch_count"] == 5
        assert rec["bxx"] == "b40"
        assert "Baruch" in rec["title"]

    def test_letter_of_jeremiah_is_separate_book(self):
        """The lje (Letter of Jeremiah / LXX Baruch-6) is a SEPARATE
        books.yaml book — NOT folded into the 5-chapter bar floor."""
        books = yaml.safe_load((REPO / "content" / "books.yaml").read_text(encoding="utf-8"))["books"]
        lje = next(b for b in books if b["code"] == "lje")
        assert "Jeremiah" in lje["title"]
        assert lje["code"] != "bar"


class TestTau7XRWisdomOfSolomonVerseCounts:
    def test_symbol_present(self):
        _, wis = _floors()
        assert isinstance(wis, dict)

    def test_nineteen_chapters(self):
        _, wis = _floors()
        assert sorted(wis.keys()) == list(range(1, 20))

    def test_total_verses_436(self):
        _, wis = _floors()
        assert sum(wis.values()) == 436

    def test_books_yaml_wis_ch_count_19(self):
        books = yaml.safe_load((REPO / "content" / "books.yaml").read_text(encoding="utf-8"))["books"]
        rec = next(b for b in books if b["code"] == "wis")
        assert rec["ch_count"] == 19
        assert rec["bxx"] == "b33"
        assert "Wisdom of Solomon" in rec["title"]


# ─────────────────────────── structural_map ────────────────────────


class TestTau7XQStructuralMapBaruch:
    def _blk(self) -> dict:
        return _source_yaml()["structural_map"]["baruch"]

    def test_block_present(self):
        assert "baruch" in _source_yaml()["structural_map"]

    def test_book_codes(self):
        assert self._blk()["book_codes"] == ["bar"]

    def test_pdf_page_range_1429_1431(self):
        assert self._blk()["pdf_page_range"] == [1429, 1431]

    def test_verified_at_tau7xq(self):
        assert self._blk()["verified"] is True
        assert self._blk()["verified_at_phase"] == "τ.7.x.q"

    def test_chapter_count_expected_5(self):
        assert self._blk()["chapter_count_expected"] == 5

    def test_notes_document_lje_ambiguity(self):
        notes = self._blk()["notes"]
        assert "lje" in notes and "SEPARATE" in notes


class TestTau7XRStructuralMapWisdom:
    def _blk(self) -> dict:
        return _source_yaml()["structural_map"]["wisdom_of_solomon"]

    def test_block_present(self):
        assert "wisdom_of_solomon" in _source_yaml()["structural_map"]

    def test_book_codes(self):
        assert self._blk()["book_codes"] == ["wis"]

    def test_pdf_page_range_1432_1448(self):
        assert self._blk()["pdf_page_range"] == [1432, 1448]

    def test_verified_at_tau7xr(self):
        assert self._blk()["verified"] is True
        assert self._blk()["verified_at_phase"] == "τ.7.x.r"

    def test_chapter_count_expected_19(self):
        assert self._blk()["chapter_count_expected"] == 19

    def test_notes_document_jubilees_crossvalidation(self):
        notes = self._blk()["notes"]
        assert "1454" in notes and "ኩፉሌ" in notes
        assert "1454,1514" in notes or "[1454, 1514]" in notes


class TestTau7XQRJubileesSectionUnchanged:
    """The Π.1 structural_map.jubilees [1454,1514] page-range was
    only CROSS-VALIDATED by the τ.7.x.q scan (NOT modified at
    τ.7.x.q/r). CONVERTED at τ.7.x.t: that phase legitimately
    INGESTS Jubilees and upgrades verified:tentative→true /
    verified_at_phase Π.1→τ.7.x.t — the documented prior-pin-
    conversion-as-part-of-the-triggering-ship pattern (the
    τ.7.x.m est-skip-pin precedent + memory feedback_share_pin_
    pattern). The DURABLE invariant is the [1454,1514] page-range
    anchor + book_codes — it never moves; only the verification
    confidence advanced. The tau7xr_ingest historical
    `jubilees_section_unchanged` flag is NOT rewritten (it WAS
    unchanged at τ.7.x.q/r)."""

    def test_jubilees_page_range_anchor_unchanged(self):
        jub = _source_yaml()["structural_map"]["jubilees"]
        assert jub["book_codes"] == ["jub"]
        assert jub["pdf_page_range"] == [1454, 1514]
        assert jub["verified_at_phase"] in ("Π.1", "τ.7.x.t")


# ──────────────────────────── output modules ───────────────────────


class TestTau7XQBarPy:
    def test_bar_py_exists(self):
        assert (AMHARIC_TEWAHEDO / "bar.py").is_file()

    def test_constants(self):
        c = _constants("bar")
        assert c.get("TRANSLATION") == "amharic-tewahedo"
        assert c.get("BOOK") == "bar"
        assert c.get("SOURCE_QUALITY") == "ocr-tier3"
        assert c.get("INGEST_PHASE") == "τ.7.x.q"

    def test_total_verse_floor(self):
        # Empirical at ship: 47 (highly compressed source). Floor 40.
        assert len(_verses("bar")) >= 40

    def test_first_verse_is_1_1(self):
        ch, v, text = _verses("bar")[0]
        assert (ch, v) == (1, 1)
        assert text


class TestTau7XRWisPy:
    def test_wis_py_exists(self):
        assert (AMHARIC_TEWAHEDO / "wis.py").is_file()

    def test_constants(self):
        c = _constants("wis")
        assert c.get("TRANSLATION") == "amharic-tewahedo"
        assert c.get("BOOK") == "wis"
        assert c.get("SOURCE_QUALITY") == "ocr-tier3"
        assert c.get("INGEST_PHASE") == "τ.7.x.r"

    def test_total_verse_floor(self):
        # Empirical at ship: 254. Floor 220 guards regression.
        assert len(_verses("wis")) >= 220

    def test_first_verse_is_1_1(self):
        ch, v, text = _verses("wis")[0]
        assert (ch, v) == (1, 1)
        assert text


# ─────────────────────────── coverage shape ────────────────────────


class TestTau7XQBarCoverage:
    """Empirical: ch 1 full; 2 partial (25/35); 3-5 empty; 0
    overflow. Honest-low 33.3% from extreme source compression
    (3 pp / 5 ch), NOT a boundary error (τ.7.x.n discipline)."""

    def test_chapter_1_fully_populated(self):
        bar, _ = _floors()
        assert len(_by_chapter("bar").get(1, [])) == bar[1]

    def test_chapter_2_partial(self):
        bar, _ = _floors()
        got = len(_by_chapter("bar").get(2, []))
        assert 1 <= got < bar[2]

    def test_chapters_3_through_5_empty(self):
        by = _by_chapter("bar")
        for ch in (3, 4, 5):
            assert len(by.get(ch, [])) == 0

    def test_no_overflow_above_chapter_5(self):
        by = _by_chapter("bar")
        assert sum(len(v) for ch, v in by.items() if ch > 5) == 0


class TestTau7XRWisCoverage:
    """Empirical: ch 1-11 full; 12 partial (11/27); 13-19 empty;
    0 overflow. Deep-PDF deuterocanon band 58.3%."""

    def test_chapters_1_through_11_fully_populated(self):
        _, wis = _floors()
        by = _by_chapter("wis")
        for ch in range(1, 12):
            assert len(by.get(ch, [])) == wis[ch], (
                f"τ.7.x.r wis ch {ch} must have exactly {wis[ch]} verses; got {len(by.get(ch, []))}"
            )

    def test_chapter_12_partial(self):
        _, wis = _floors()
        got = len(_by_chapter("wis").get(12, []))
        assert 1 <= got < wis[12]

    def test_chapters_13_through_19_empty(self):
        by = _by_chapter("wis")
        for ch in range(13, 20):
            assert len(by.get(ch, [])) == 0

    def test_no_overflow_above_chapter_19(self):
        by = _by_chapter("wis")
        assert sum(len(v) for ch, v in by.items() if ch > 19) == 0


# ───────────────────── _source.yaml ingest blocks ──────────────────


class TestTau7XQSourceYamlIngestBlock:
    def _blk(self) -> dict:
        return _source_yaml()["ocr_strategy"]["tau7xq_ingest"]

    def test_block_exists(self):
        assert "tau7xq_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert self._blk()["shipped_at_phase"] == "τ.7.x.q"

    def test_structural_map_addition(self):
        sma = self._blk()["structural_map_addition"]
        assert sma["section"] == "baruch"
        assert sma["pdf_page_range"] == [1429, 1431]
        assert sma["chapter_count_expected"] == 5

    def test_lje_ambiguity_documented(self):
        assert "lje_ambiguity" in self._blk()["structural_map_addition"]

    def test_empirical_validation(self):
        ev = self._blk()["empirical_validation"]
        assert ev["coverage_pct"] == 33.3
        assert ev["renumbered_verse_count"] == 47

    def test_honest_low_not_boundary_error_documented(self):
        band = " ".join(self._blk()["empirical_validation"]["coverage_band_position"].split())
        assert "NOT a boundary error" in band and "τ.7.x.n" in band

    def test_parser_api_change_zero(self):
        assert "No parser API changes" in self._blk()["parser_api_change"]
        assert "27-ship" in self._blk()["parser_api_change"]

    def test_next_phase_tau7xr(self):
        assert self._blk()["next_phase"] == "τ.7.x.r"

    def test_pipeline_reused_back_link(self):
        assert self._blk()["pipeline_reused_at_phase"] == "τ.7.x.r"


class TestTau7XRSourceYamlIngestBlock:
    def _blk(self) -> dict:
        return _source_yaml()["ocr_strategy"]["tau7xr_ingest"]

    def test_block_exists(self):
        assert "tau7xr_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert self._blk()["shipped_at_phase"] == "τ.7.x.r"

    def test_structural_map_addition(self):
        sma = self._blk()["structural_map_addition"]
        assert sma["section"] == "wisdom_of_solomon"
        assert sma["pdf_page_range"] == [1432, 1448]
        assert sma["chapter_count_expected"] == 19

    def test_empirical_validation(self):
        ev = self._blk()["empirical_validation"]
        assert ev["coverage_pct"] == 58.3
        assert ev["renumbered_verse_count"] == 254

    def test_block_major_pair_drained(self):
        assert self._blk()["block_major_pair_drained"] == "p1429-1448"

    def test_jubilees_crossvalidation_invariant(self):
        contracts = self._blk()["closed_arc_contracts_preserved"]
        assert contracts.get("jubilees_section_unchanged") is True

    def test_next_phase_tau7xs(self):
        assert self._blk()["next_phase"] == "τ.7.x.s"


# ─────────────────────── _meta.yaml ingest records ─────────────────


class TestTau7XQRMetaYamlIngestRecords:
    def test_stats_books_at_least_twenty(self):
        assert _meta()["stats"]["books"] >= 20

    def test_stats_verses_at_least_10757(self):
        assert _meta()["stats"]["verses"] >= 10757

    def test_stats_books_outside_kjv_ten(self):
        """+bar +wis (both deuterocanonical) on top of the prior 8."""
        assert _meta()["stats"]["books_outside_kjv"] >= 10

    def test_tau7xq_ingest_record(self):
        r = _meta()["ingest_record_tau7xq"]
        assert r["phase"] == "τ.7.x.q"
        assert r["ingested_book_codes"] == ["bar"]
        assert r["coverage"]["verses_extracted"] == 47
        assert r.get("deuterocanonical") is True

    def test_tau7xr_ingest_record(self):
        r = _meta()["ingest_record_tau7xr"]
        assert r["phase"] == "τ.7.x.r"
        assert r["ingested_book_codes"] == ["wis"]
        assert r["coverage"]["verses_extracted"] == 254
        assert r.get("block_major_pair_drained") == "p1429-1448"

    def test_tau7xp_pipeline_reused_back_link_added(self):
        assert _meta()["ingest_record_tau7xp"]["pipeline_reused_at_phase"] == "τ.7.x.q"

    def test_prior_ingest_records_present(self):
        m = _meta()
        assert "ingest_record" in m
        for tag in ("tau7xh", "tau7xn", "tau7xo", "tau7xp"):
            assert f"ingest_record_{tag}" in m, f"prior ingest record missing: {tag}"


# ───────────── zero-API-delta + prior-pin preservation ─────────────


class TestTau7XQRZeroApiDeltaAndPriorPins:
    def test_cli_renumber_choices_extended(self):
        src = (REPO / "scripts" / "extract_parallel_pdf.py").read_text(encoding="utf-8")
        assert '"baruch"' in src and '"wisdom_of_solomon"' in src
        assert src.count("BARUCH_VERSE_COUNTS") >= 3
        assert src.count("WISDOM_OF_SOLOMON_VERSE_COUNTS") >= 3

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
            "sir",
            "4ba",
        ):
            assert (AMHARIC_TEWAHEDO / f"{book}.py").is_file(), f"prior τ.7.x.* book {book} must persist"

    def test_geez_bar_wis_paz_bel_jub_1en_ingested_catchup_complete(self):
        """MIGRATED at the τ.6.x.2.u ship-time (2026-05-20) per memory
        `feedback_share_pin_pattern` + the τ.6.x.2.j-t precedent.
        Originally asserted the Geʽez `bar.py` AND `wis.py` must NOT
        exist (τ.7.x.q was --lang amharic; D4-c deferral). τ.6.x.2.q
        flipped the `bar` half; τ.6.x.2.r flipped the `wis` half;
        τ.6.x.2.s flipped the Daniel-additions cluster paz+bel of
        the eighth EOTC-parallel block; τ.6.x.2.t flipped the `jub`
        half (Jubilees / Mäṣḥafä Kufāle — opens the ninth EOTC-
        parallel block); τ.6.x.2.u (the SEVENTH and FINAL ship of
        the deuterocanon Geʽez catchup) wrote the ocr-tier3 parallel-
        PDF Geʽez 1en.py, draining the tenth (and final) EOTC-
        parallel block and CLOSING the τ.6.x.2.* OT catchup queue
        (sir → 4ba → bar → wisdom → daniel-additions → jubilees →
        1 enoch). All FIVE halves now durable positive invariants:
        bar at τ.6.x.2.q, wis at τ.6.x.2.r, paz/bel at τ.6.x.2.s,
        jub at τ.6.x.2.t, 1en at τ.6.x.2.u (all ocr-tier3). Susanna
        (sus) DEFERRED to τ.6.x.3 (not present in this PDF)."""
        import ast

        assert (GEEZ_TEWAHEDO / "bar.py").is_file(), "Geʽez bar.py must EXIST after the τ.6.x.2.q catchup ship"
        tree = ast.parse((GEEZ_TEWAHEDO / "bar.py").read_text(encoding="utf-8"))
        consts = {
            t.id: ast.literal_eval(n.value)
            for n in ast.walk(tree)
            if isinstance(n, ast.Assign)
            for t in n.targets
            if isinstance(t, ast.Name) and t.id in ("SOURCE_QUALITY", "INGEST_PHASE", "BOOK", "TRANSLATION")
        }
        assert consts.get("SOURCE_QUALITY") == "ocr-tier3"
        assert consts.get("INGEST_PHASE") == "τ.6.x.2.q"
        assert consts.get("BOOK") == "bar"
        assert consts.get("TRANSLATION") == "geez-tewahedo"
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
        # 1en half FLIPPED at τ.6.x.2.u — same durable positive invariant
        # (FINAL book in the catchup queue — τ.6.x.2.* OT catchup arc CLOSED)
        assert (GEEZ_TEWAHEDO / "1en.py").is_file(), "Geʽez 1en.py must EXIST after the τ.6.x.2.u catchup ship"
        tree1en = ast.parse((GEEZ_TEWAHEDO / "1en.py").read_text(encoding="utf-8"))
        consts1en = {
            t.id: ast.literal_eval(n.value)
            for n in ast.walk(tree1en)
            if isinstance(n, ast.Assign)
            for t in n.targets
            if isinstance(t, ast.Name) and t.id in ("SOURCE_QUALITY", "INGEST_PHASE", "BOOK", "TRANSLATION")
        }
        assert consts1en.get("SOURCE_QUALITY") == "ocr-tier3"
        assert consts1en.get("INGEST_PHASE") == "τ.6.x.2.u"
        assert consts1en.get("BOOK") == "1en"
        assert consts1en.get("TRANSLATION") == "geez-tewahedo"

    def test_tau7xo_tau7xp_pins_preserved(self):
        s = _source_yaml()
        assert s["ocr_strategy"]["tau7xp_ingest"]["block_drained"] == "p1379-1428"
        assert s["structural_map"]["sirach"]["pdf_page_range"] == [1379, 1418]
        assert s["structural_map"]["paralipomena_jeremiah"]["pdf_page_range"] == [1419, 1428]

    def test_tau7xn_meqabyan_correction_preserved(self):
        s = _source_yaml()
        assert s["structural_map"]["meqabyan"]["subsections"]["mq2"] == [1351, 1368]
        assert (AMHARIC_TEWAHEDO / "mq1.py").is_file()


class TestTau7XQRStateDocs:
    def test_session_state_mentions_tau7xq(self):
        txt = (REPO / "dev" / "SESSION_STATE.md").read_text(encoding="utf-8")
        assert "τ.7.x.q" in txt

    def test_changelog_records_tau7xq(self):
        txt = (REPO / "dev" / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "τ.7.x.q" in txt

    def test_plan_ledger_records_tau7xq(self):
        txt = (REPO / "dev" / "PLAN_2026-05-09.md").read_text(encoding="utf-8")
        assert "τ.7.x.q" in txt
