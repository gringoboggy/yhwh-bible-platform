"""τ.7.x.n — Amharic Mäqabyan trilogy (mq1 + mq2 + mq3) full-book
ingest pins (2026-05-15).

FOURTEENTH/FIFTEENTH/SIXTEENTH τ.7.x.* per-book ships under D4-c
Amharic-first + D1-a per-book cadence. FIRST Tewahedo-distinctive
book(s) in the τ.7.x.* stream + FIRST multi-book EOTC-parallel block
ingested. Drains the FIFTH EOTC-parallel block p1318-1378:
- **mq1 1 Mäqabyan** (`መጽሐፈ መቃብያን ቀዳማዊ`): p1318-1350;
  MQ1_VERSE_COUNTS (36 ch / 502 v).
- **mq2 2 Mäqabyan** (`መጽሐፈ መቃብያን ካልዕ`): p1351-1368;
  MQ2_VERSE_COUNTS (21 ch / 256 v).
- **mq3 3 Mäqabyan** (`መጽሐፈ መቃብያን ሣልስ`): p1369-1378;
  MQ3_VERSE_COUNTS (10 ch / 188 v). Trilogy = 946 v / 67 ch.

**Structural-discovery correction (τ.7.x.a.0-PILOT-class):** the
τ.6.x.0a `meqabyan.subsections` ranges (mq1[1318,1365]/mq2[1366,
1372]/mq3[1373,1378]) were a coarse approximate scan and WRONG (mq2
recovered an anomalous 5.9% on the old range). τ.7.x.n content-
boundary inspection (running-header ordinal ቀዳማዊ→ካልዕ→ሣልስ +
end-colophons) corrected the internal splits to [1318,1350]/[1351,
1368]/[1369,1378]; outer bounds [1318,1378] unchanged. Both the
declarative subsections + the extract_parallel_pdf.py heuristic
safety-net dict are corrected. Coordination-POSITIVE for δ.1.x.

**Coordination (per PLAN τ.7.x.n NEXT-UP note):**
- vs δ.1.x: τ.7.x.n writes only amharic-tewahedo/mq*.py at ocr-
  tier3 + EXPLICITLY δ.1.x-replaceable; does NOT touch content/
  divergence/* or geez-tewahedo/mq* (Π.1 authoritative slot). The
  MQ{1,2,3}_VERSE_COUNTS floors are derived by the IDENTICAL per-
  chapter-max-verse method the δ.1.x divergence JSON documents;
  mq1 ch1-9 floor EXACTLY matches that JSON (coordination proof).
- vs γ.4.8: independent OCR scripture-text witness; does NOT touch
  content/sources/ethiopian_commentaries.json (212 patristic
  entries) or content/notes/mq*.py (v1 English, immutable in δ.1.x).

Zero-parser-API-delta preserved (14th/15th/16th consecutive;
24-ship across both columns). Pins validate: floors, the 3 new +
1 retained structural_map sections, the structural-discovery
correction, the δ.1.x/γ.4.8 coordination, mq{1,2,3}.py modules,
clean renumber shape, _source.yaml + _meta.yaml records, the
tau7xm→tau7xn back-link, and that all prior τ.7.x.a-m + τ.6.x.2.a-h
closed-arc pins remain green.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SOURCE_YAML = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"
AMHARIC_TEWAHEDO = REPO / "content" / "translations" / "amharic-tewahedo"
GEEZ_TEWAHEDO = REPO / "content" / "translations" / "geez-tewahedo"
DIVERGENCE_JSON = REPO / "content" / "divergence" / "meqabyan_geez_divergence.json"
ETHIOPIAN_COMMENTARIES = REPO / "content" / "sources" / "ethiopian_commentaries.json"

TRILOGY = ("mq1", "mq2", "mq3")


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


def _floors() -> tuple[dict, dict, dict]:
    sys.path.insert(0, str(REPO / "scripts"))
    from extract_parallel_pdf import (
        MQ1_VERSE_COUNTS,
        MQ2_VERSE_COUNTS,
        MQ3_VERSE_COUNTS,
    )

    return MQ1_VERSE_COUNTS, MQ2_VERSE_COUNTS, MQ3_VERSE_COUNTS


# ──────────────────────────── floor dicts ──────────────────────────


class TestTau7XNMeqabyanVerseCounts:
    def test_symbols_present(self):
        m1, m2, m3 = _floors()
        assert isinstance(m1, dict) and isinstance(m2, dict) and isinstance(m3, dict)

    def test_chapter_keys(self):
        m1, m2, m3 = _floors()
        assert sorted(m1) == list(range(1, 37))
        assert sorted(m2) == list(range(1, 22))
        assert sorted(m3) == list(range(1, 11))

    def test_totals(self):
        m1, m2, m3 = _floors()
        assert sum(m1.values()) == 502
        assert sum(m2.values()) == 256
        assert sum(m3.values()) == 188
        assert sum(m1.values()) + sum(m2.values()) + sum(m3.values()) == 946

    def test_books_yaml_ch_counts(self):
        books = yaml.safe_load((REPO / "content" / "books.yaml").read_text(encoding="utf-8"))["books"]
        rec = {b["code"]: b for b in books}
        assert rec["mq1"]["ch_count"] == 36 and rec["mq1"]["bxx"] == "b26"
        assert rec["mq2"]["ch_count"] == 21 and rec["mq2"]["bxx"] == "b27"
        assert rec["mq3"]["ch_count"] == 10 and rec["mq3"]["bxx"] == "b28"
        for c in TRILOGY:
            assert "Meqabyan" in rec[c]["title"]


# ─────────────────── δ.1.x floor-coordination proof ────────────────


class TestTau7XNDelta1xFloorCoordinationProof:
    """The MQ1 floor must be derivable by the IDENTICAL per-chapter-
    max-verse method the δ.1.x divergence JSON documents — and mq1
    ch1-9 must EXACTLY match that JSON's per_chapter_verse_count_floor.
    This is the literal proof that the parallel-Bible ingest, the
    δ.1.x revision, and the γ.4.8 apparatus all align on ONE verse
    structure (PLAN τ.7.x.n coordinate-with-δ.1.x/γ.4.8 requirement)."""

    def test_mq1_ch1_9_floor_exactly_matches_delta1x_json(self):
        d = json.loads(DIVERGENCE_JSON.read_text(encoding="utf-8"))
        delta_floor = d["_meta"]["batch_prep"]["per_chapter_verse_count_floor"]
        m1, _, _ = _floors()
        for ch in range(1, 10):
            assert m1[ch] == delta_floor[str(ch)], (
                f"mq1 ch{ch}: τ.7.x.n floor {m1[ch]} must match the δ.1.x "
                f"divergence JSON floor {delta_floor[str(ch)]} (coordination proof)"
            )

    def test_floor_derivable_from_candidates_max_verse(self):
        """The documented derivation: per-chapter MAX verse across
        content/candidates/mq{N}_ch_*.json. Re-derive + assert equal
        to the shipped floors so the coordination method is pinned."""
        m1, m2, m3 = _floors()
        for floor, book, nch in ((m1, "mq1", 36), (m2, "mq2", 21), (m3, "mq3", 10)):
            for ch in range(1, nch + 1):
                p = REPO / "content" / "candidates" / f"{book}_ch_{ch:03d}.json"
                cand = json.loads(p.read_text(encoding="utf-8"))
                mx = max((c.get("verse", 0) for c in cand.get("candidates", [])), default=0)
                assert floor[ch] == mx, f"{book} ch{ch}: floor {floor[ch]} != candidates max-verse {mx}"

    def test_divergence_json_chapters_per_book_consistent(self):
        d = json.loads(DIVERGENCE_JSON.read_text(encoding="utf-8"))
        cpb = d["_meta"]["chapters_per_book"]
        assert cpb == {"mq1": 36, "mq2": 21, "mq3": 10}

    def test_delta1x_divergence_json_entries_still_empty(self):
        """τ.7.x.n must NOT have touched the δ.1.x divergence JSON —
        its `entries` invariant (empty until δ.1.x.A) is preserved."""
        d = json.loads(DIVERGENCE_JSON.read_text(encoding="utf-8"))
        assert d["entries"] == []


# ───────────────────── γ.4.8 independence (no collision) ───────────


class TestTau7XNGamma48Independence:
    """τ.7.x.n is an INDEPENDENT OCR scripture-text witness; it must
    not have touched the γ.4.8 patristic apparatus nor the v1 English
    Mäqabyan notes (immutable during δ.1.x)."""

    def test_ethiopian_commentaries_meqabyan_voice_intact(self):
        data = json.loads(ETHIOPIAN_COMMENTARIES.read_text(encoding="utf-8"))
        entries = data if isinstance(data, list) else data.get("entries", data.get("sources", []))
        mq = [e for e in entries if isinstance(e, dict) and "meqabyan" in json.dumps(e, ensure_ascii=False).lower()]
        # γ.4.8.F floor: Meqabyan voice ≥ 212 (regression-guarded).
        assert len(mq) >= 212, f"γ.4.8 Meqabyan apparatus voice must remain ≥212; got {len(mq)}"

    def test_v1_english_meqabyan_notes_present_and_untouched(self):
        for c in TRILOGY:
            f = REPO / "content" / "notes" / f"{c}.py"
            assert f.is_file(), f"v1 English notes content/notes/{c}.py must persist"
            assert "NOTES" in f.read_text(encoding="utf-8")

    def test_scripture_text_is_separate_layer_from_apparatus(self):
        """The τ.7.x.n output is VERSES (scripture text) in the
        translation slot — a different layer than the patristic
        apparatus NOTES. Sanity: mq*.py expose VERSES not NOTES."""
        for c in TRILOGY:
            txt = (AMHARIC_TEWAHEDO / f"{c}.py").read_text(encoding="utf-8")
            assert "VERSES = [" in txt and "NOTES = [" not in txt


# ─────────────────────────── structural_map ────────────────────────


class TestTau7XNStructuralMapNewSections:
    def _sm(self) -> dict:
        return _source_yaml()["structural_map"]

    def test_three_new_sections_present(self):
        sm = self._sm()
        for s in ("meqabyan_i", "meqabyan_ii", "meqabyan_iii"):
            assert s in sm, f"τ.7.x.n must add structural_map.{s}"

    def test_book_codes(self):
        sm = self._sm()
        assert sm["meqabyan_i"]["book_codes"] == ["mq1"]
        assert sm["meqabyan_ii"]["book_codes"] == ["mq2"]
        assert sm["meqabyan_iii"]["book_codes"] == ["mq3"]

    def test_corrected_page_ranges(self):
        sm = self._sm()
        assert sm["meqabyan_i"]["pdf_page_range"] == [1318, 1350]
        assert sm["meqabyan_ii"]["pdf_page_range"] == [1351, 1368]
        assert sm["meqabyan_iii"]["pdf_page_range"] == [1369, 1378]

    def test_chapter_counts(self):
        sm = self._sm()
        assert sm["meqabyan_i"]["chapter_count_expected"] == 36
        assert sm["meqabyan_ii"]["chapter_count_expected"] == 21
        assert sm["meqabyan_iii"]["chapter_count_expected"] == 10

    def test_verified_at_tau7xn(self):
        sm = self._sm()
        for s in ("meqabyan_i", "meqabyan_ii", "meqabyan_iii"):
            assert sm[s]["verified"] is True
            assert sm[s]["verified_at_phase"] == "τ.7.x.n"

    def test_notes_document_structural_discovery(self):
        notes = self._sm()["meqabyan_i"]["notes"]
        assert "CORRECTION" in notes and "1350" in notes
        assert "ቀዳማዊ" in notes


class TestTau7XNMeqabyanSectionRetained:
    """The original MULTI-book `meqabyan` section MUST be retained
    untouched for Π.1 page-image extraction + the pilot/subsections
    mechanism — only its subsections are corrected (outer bounds
    unchanged)."""

    def _m(self) -> dict:
        return _source_yaml()["structural_map"]["meqabyan"]

    def test_meqabyan_section_still_present(self):
        assert "meqabyan" in _source_yaml()["structural_map"]

    def test_book_codes_unchanged(self):
        assert self._m()["book_codes"] == ["mq1", "mq2", "mq3"]

    def test_outer_bounds_unchanged(self):
        assert self._m()["pdf_page_range"] == [1318, 1378]

    def test_subsections_corrected(self):
        subs = self._m()["subsections"]
        assert subs["mq1"] == [1318, 1350]
        assert subs["mq2"] == [1351, 1368]
        assert subs["mq3"] == [1369, 1378]


class TestTau7XNHeuristicSafetyNetCorrected:
    def test_script_heuristic_dict_matches_corrected_ranges(self):
        src = (REPO / "scripts" / "extract_parallel_pdf.py").read_text(encoding="utf-8")
        assert '("meqabyan", "mq1"): (1318, 1350)' in src
        assert '("meqabyan", "mq2"): (1351, 1368)' in src
        assert '("meqabyan", "mq3"): (1369, 1378)' in src
        # Old wrong values must be gone.
        assert "(1318, 1365)" not in src
        assert "(1366, 1372)" not in src
        assert "(1373, 1378)" not in src


# ──────────────────────────── output modules ───────────────────────


class TestTau7XNTrilogyModules:
    def test_modules_exist(self):
        for c in TRILOGY:
            assert (AMHARIC_TEWAHEDO / f"{c}.py").is_file()

    def test_constants(self):
        for c in TRILOGY:
            k = _constants(c)
            assert k.get("TRANSLATION") == "amharic-tewahedo"
            assert k.get("BOOK") == c
            assert k.get("SOURCE_QUALITY") == "ocr-tier3"
            assert k.get("SOURCE_PROVENANCE") == "parallel-bible-eotc"
            assert k.get("INGEST_PHASE") == "τ.7.x.n"

    def test_verse_count_floors(self):
        # Empirical at ship: mq1=339, mq2=198, mq3=79. Guard floors.
        assert len(_verses("mq1")) >= 300
        assert len(_verses("mq2")) >= 170
        assert len(_verses("mq3")) >= 65

    def test_first_verse_is_chapter_1_verse_1(self):
        for c in TRILOGY:
            ch, v, text = _verses(c)[0]
            assert (ch, v) == (1, 1), f"{c} first verse must be 1:1"
            assert text


# ─────────────────────────── coverage shape ────────────────────────


class TestTau7XNCleanRenumberShape:
    """Empirical (post structural-discovery correction):
    mq1 1-27 full / 28 partial(14/38) / 29-36 empty / 0 overflow;
    mq2 1-15 full / 16 partial(3/8)   / 17-21 empty / 0 overflow;
    mq3 1-3  full / 4 partial(12/34)  / 5-10 empty  / 0 overflow."""

    CASES = (
        ("mq1", 27, 28, 36),
        ("mq2", 15, 16, 21),
        ("mq3", 3, 4, 10),
    )

    def test_leading_chapters_fully_populated(self):
        m1, m2, m3 = _floors()
        floors = {"mq1": m1, "mq2": m2, "mq3": m3}
        for book, last_full, _partial, _n in self.CASES:
            by = _by_chapter(book)
            for ch in range(1, last_full + 1):
                assert len(by.get(ch, [])) == floors[book][ch], (
                    f"{book} ch{ch} must be full ({floors[book][ch]}); got {len(by.get(ch, []))}"
                )

    def test_partial_chapter(self):
        m1, m2, m3 = _floors()
        floors = {"mq1": m1, "mq2": m2, "mq3": m3}
        for book, _lf, partial, _n in self.CASES:
            got = len(_by_chapter(book).get(partial, []))
            assert 1 <= got < floors[book][partial], (
                f"{book} ch{partial} must be partial (1..{floors[book][partial] - 1}); got {got}"
            )

    def test_trailing_chapters_empty(self):
        for book, _lf, partial, n in self.CASES:
            by = _by_chapter(book)
            for ch in range(partial + 1, n + 1):
                assert len(by.get(ch, [])) == 0, f"{book} ch{ch} must be empty at ocr-tier3"

    def test_no_overflow_above_book_chapter_count(self):
        for book, _lf, _p, n in self.CASES:
            by = _by_chapter(book)
            assert sum(len(v) for ch, v in by.items() if ch > n) == 0, f"{book} must not overflow ch>{n}"

    def test_combined_coverage_band(self):
        total = len(_verses("mq1")) + len(_verses("mq2")) + len(_verses("mq3"))
        # Empirical 616/946 = 65.1%. Guard a sane lower bound (the
        # mq2 anomaly was 15 → the correction must keep us well above).
        assert total >= 580, f"trilogy combined verses regressed: {total} (expect ~616)"


# ───────────────────── _source.yaml ingest block ───────────────────


class TestTau7XNSourceYamlIngestBlock:
    def _blk(self) -> dict:
        return _source_yaml()["ocr_strategy"]["tau7xn_ingest"]

    def test_block_exists(self):
        assert "tau7xn_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert self._blk()["shipped_at_phase"] == "τ.7.x.n"

    def test_books_ingested(self):
        assert self._blk()["books_ingested"] == ["mq1", "mq2", "mq3"]

    def test_structural_map_addition(self):
        sma = self._blk()["structural_map_addition"]
        assert sma["sections"] == ["meqabyan_i", "meqabyan_ii", "meqabyan_iii"]
        assert sma["meqabyan_i"]["pdf_page_range"] == [1318, 1350]
        assert sma["meqabyan_ii"]["pdf_page_range"] == [1351, 1368]
        assert sma["meqabyan_iii"]["pdf_page_range"] == [1369, 1378]

    def test_structural_discovery_correction_documented(self):
        sdc = self._blk()["structural_discovery_correction"]
        assert "τ.6.x.0b honesty contract" in sdc
        assert "5.9%" in sdc and "1350" in sdc

    def test_coordination_documented(self):
        co = self._blk()["coordination"]
        assert "δ.1.x-REPLACEABLE" in co["vs_delta1x_revision_track"]
        assert "ethiopian_commentaries.json" in co["vs_gamma48_patristic_arc"]
        assert "EXACTLY matches" in co["floor_coordination_proof"]

    def test_empirical_validation(self):
        ev = self._blk()["empirical_validation"]
        assert ev["mq1"]["coverage_pct"] == 67.5
        assert ev["mq2"]["coverage_pct"] == 77.3
        assert ev["mq3"]["coverage_pct"] == 42.0

    def test_parser_api_change_zero(self):
        assert "No parser API changes" in self._blk()["parser_api_change"]
        assert "24-ship" in self._blk()["parser_api_change"]

    def test_block_drained(self):
        assert self._blk()["block_drained"] == "p1318-1378"

    def test_closed_arc_contracts_preserved(self):
        contracts = self._blk()["closed_arc_contracts_preserved"]
        for tag in ("tau7xa", "tau7xe", "tau7xh", "tau7xl", "tau7xm", "tau6x2h"):
            assert contracts.get(f"{tag}_ingest") is True
        assert contracts.get("gamma48_meqabyan_apparatus_untouched") is True
        assert contracts.get("delta1x_divergence_json_untouched") is True
        assert contracts.get("meqabyan_section_retained") is True

    def test_next_phase(self):
        assert self._blk()["next_phase"] == "τ.7.x.o"

    def test_tau7xm_pipeline_reused_back_link(self):
        assert _source_yaml()["ocr_strategy"]["tau7xm_ingest"]["pipeline_reused_at_phase"] == "τ.7.x.n"


# ─────────────────────── _meta.yaml ingest record ──────────────────


class TestTau7XNMetaYamlIngestRecord:
    def test_stats_books_at_least_sixteen(self):
        assert _meta()["stats"]["books"] >= 16

    def test_stats_verses_at_least_9551(self):
        assert _meta()["stats"]["verses"] >= 9551

    def test_stats_books_outside_kjv_six(self):
        """2es+tob+jdt (deuterocanon) + mq1+mq2+mq3 (Tewahedo-
        distinctive) = 6 outside the 66-book KJV canon."""
        assert _meta()["stats"]["books_outside_kjv"] >= 6

    def test_tau7xn_ingest_record(self):
        r = _meta()["ingest_record_tau7xn"]
        assert r["phase"] == "τ.7.x.n"
        assert r["ingested_book_codes"] == ["mq1", "mq2", "mq3"]
        assert r["coverage"]["mq1"]["verses_extracted"] == 339
        assert r["coverage"]["mq2"]["verses_extracted"] == 198
        assert r["coverage"]["mq3"]["verses_extracted"] == 79

    def test_tau7xn_markers(self):
        r = _meta()["ingest_record_tau7xn"]
        assert r.get("tewahedo_distinctive") is True
        assert r.get("multi_book_section") is True
        assert r.get("block_drained") == "p1318-1378"

    def test_tau7xm_pipeline_reused_back_link_added(self):
        assert _meta()["ingest_record_tau7xm"]["pipeline_reused_at_phase"] == "τ.7.x.n"

    def test_prior_ingest_records_present(self):
        m = _meta()
        # tau7xa is the bare `ingest_record:` key; later books use
        # `ingest_record_<tag>` (matches test_parallel_bible_tau7xl).
        assert "ingest_record" in m
        for tag in ("tau7xh", "tau7xi", "tau7xk", "tau7xl", "tau7xm"):
            assert f"ingest_record_{tag}" in m, f"prior ingest record missing: {tag}"


# ───────────── zero-API-delta + prior-pin preservation ─────────────


class TestTau7XNZeroApiDeltaAndPriorPins:
    def test_cli_renumber_choices_extended(self):
        src = (REPO / "scripts" / "extract_parallel_pdf.py").read_text(encoding="utf-8")
        assert '"meqabyan_i"' in src and '"meqabyan_ii"' in src and '"meqabyan_iii"' in src
        assert src.count("MQ1_VERSE_COUNTS") >= 3
        assert src.count("MQ2_VERSE_COUNTS") >= 3
        assert src.count("MQ3_VERSE_COUNTS") >= 3

    def test_parser_api_functions_untouched(self):
        """Zero-parser-API-delta: the parser entry points must still
        exist with their established signatures (data-only ship)."""
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
        ):
            assert (AMHARIC_TEWAHEDO / f"{book}.py").is_file(), f"prior τ.7.x.* book {book} must persist"

    def test_geez_mq_ingested_at_tau6x2n_ocr_tier3(self):
        """MIGRATED at the τ.6.x.2.n ship-time (2026-05-16) per memory
        `feedback_share_pin_pattern` + the τ.6.x.2.j-m precedent.
        Originally asserted the Geʽez Mäqabyan slot must NOT exist
        (τ.7.x.n was --lang amharic; D4-c deferral). τ.6.x.2.n (the
        FIRST multi-book Geʽez catchup ship) wrote the ocr-tier3
        parallel-PDF Geʽez mq1/mq2/mq3, so this is FLIPPED to the
        durable positive invariant: all three exist at ocr-tier3 with
        INGEST_PHASE τ.6.x.2.n (NOT τ.7.x.n). The Π.1 page-image
        authoritative Geʽez Mäqabyan remains a SEPARATE δ.1.x track —
        this ocr-tier3 parallel-PDF ingest is δ.1.x-replaceable and
        does NOT claim page-image-tier1 authority."""
        for c in TRILOGY:
            assert (GEEZ_TEWAHEDO / f"{c}.py").is_file(), f"Geʽez {c}.py must EXIST after the τ.6.x.2.n catchup ship"
        import ast

        for c in TRILOGY:
            tree = ast.parse((GEEZ_TEWAHEDO / f"{c}.py").read_text(encoding="utf-8"))
            consts = {
                t.id: ast.literal_eval(n.value)
                for n in ast.walk(tree)
                if isinstance(n, ast.Assign)
                for t in n.targets
                if isinstance(t, ast.Name) and t.id in ("SOURCE_QUALITY", "INGEST_PHASE")
            }
            assert consts.get("SOURCE_QUALITY") == "ocr-tier3", f"{c} must be ocr-tier3 (δ.1.x-replaceable)"
            assert consts.get("INGEST_PHASE") == "τ.6.x.2.n", f"{c} INGEST_PHASE must be τ.6.x.2.n (NOT τ.7.x.n)"

    def test_tau7xl_tau7xm_pins_preserved(self):
        s = _source_yaml()
        assert s["ocr_strategy"]["tau7xl_ingest"]["shipped_at_phase"] == "τ.7.x.l"
        assert s["ocr_strategy"]["tau7xm_ingest"]["block_drained"] == "p1294-1317"
        assert s["structural_map"]["judith"]["pdf_page_range"] == [1294, 1307]
        assert s["structural_map"]["esther"]["pdf_page_range"] == [1308, 1317]

    def test_tau7xi_skip_pins_preserved(self):
        """τ.7.x.n must not disturb the τ.7.x.i 9-still-skipped set."""
        sys.path.insert(0, str(REPO / "tests"))
        from test_parallel_bible_tau7xi import TestTau7XISkipTheGapInvariants as T

        assert len(T.SKIPPED_BOOKS) == 9
        assert "est" not in T.SKIPPED_BOOKS

    def test_psalms_preserved(self):
        assert _source_yaml()["structural_map"]["psalms"]["pdf_page_range"] == [803, 906]
        assert (AMHARIC_TEWAHEDO / "psa.py").is_file()


class TestTau7XNStateDocs:
    # Doc-pins collapsed to the CHANGELOG chokepoint (2026-05-21): the
    # old test_session_state_*/test_in_flight_*/test_plan_ledger_* pins
    # read SESSION_STATE.md / IN_FLIGHT.md (rolling, trimmed) and the
    # moved PLAN_2026-05-09.md. The durable phase record is CHANGELOG.md.
    def test_phase_recorded_in_changelog(self):
        from tests.fixtures import assert_phase_recorded

        assert_phase_recorded("τ.7.x.n")
