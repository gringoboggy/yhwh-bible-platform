"""τ.7.x.s — Amharic Daniel-additions cluster (paz + bel) full-book
ingest pins + the Susanna structural-discovery deferral (2026-05-16).

TWENTY-FIRST + TWENTY-SECOND τ.7.x.* per-book ships under D4-c
Amharic-first + D1-a per-book cadence — a multi-small-book ship
(the τ.7.x.n Mäqabyan-trilogy precedent; user "continue" → advance
per PLAN). Drains the EOTC "ተረፈ ዳንኤል" (Rest of Daniel) cluster:

- **τ.7.x.s Prayer of Azariah + Song of the Three** (`paz`):
  p1449-1451; PRAYER_OF_AZARIAH_VERSE_COUNTS (1 ch / 68 v; NRSV
  "The Prayer of Azariah and the Song of the Three Jews"; books.yaml
  `paz` ch_count:1 b45). Deuterocanonical. OPENS the cluster.
  Content-confirmed via dry-run: p1449 carries the verbatim
  Pr-Azar v.15 `በዚህ ወራት አለቃ የለም ነቢይም የለም ንጉሥም የለም … መሥዋዕትም
  … ዕጣን`; Song of the Three GEZ `መዝሙረ ሠለስቱ` + `አናንያ አዛርያ
  ሚሳኤል` p1450-1451. 30/68 = 44.1% (deep-PDF deuterocanon band).
- **τ.7.x.s Bel and the Dragon** (`bel`): p1452-1453;
  BEL_AND_THE_DRAGON_VERSE_COUNTS (1 ch / 42 v; NRSV; books.yaml
  `bel` ch_count:1 b47). Deuterocanonical. DRAINS the cluster.
  Content-confirmed: GEZ `ተረፈ ዳንኤል ምፅራፍ ፲፫` + Bel idol-food /
  clay-and-bronze / priests + the `ዘንዶ` dragon; the p1453 colophon
  `… ቢዩ ዳንኤል የተናገረው … ተፈጸመ`. 23/42 = 54.8%.

STRUCTURAL-DISCOVERY FINDING (the τ.7.x.q `lje` + `laodiceans`
precedent): Susanna (`sus`, b46) is NOT distinctly present in this
parallel-Bible PDF's ተረፈ-ዳንኤል cluster (zero Susanna/elders/garden/
Joachim markers in the deep p1440-1455 scan). EOTC tradition
commonly embeds Susanna inside the Book of Daniel proper (the
not-yet-ingested `dan` block, b44). Per the τ.6.x.0b honesty
contract `sus` is DECLARED present_in_pdf:false / pdf_page_range:
null (SUSANNA_VERSE_COUNTS pre-staged, infra-ready), extraction
DEFERRED to τ.6.x.3 / the future `dan` ingest — no fabricated data.

Jubilees opens p1454 (`።ኩፉሌ።`) EXACTLY matching the pre-existing
Π.1 structural_map.jubilees [1454,1514] — decisive cross-validation
(the Π.1 jubilees section is NOT modified, only cross-validated).

Pins validate: the 3 floor dicts (paz/bel + the pre-staged sus),
the 3 structural_map blocks (incl. susanna present_in_pdf:false +
its clean SystemExit guard), paz.py/bel.py modules, coverage shape,
the honest-low / anomaly-check documentation, the Susanna-absence
deferral, the Jubilees-p1454 cross-validation-unchanged invariant,
the _source.yaml + _meta.yaml records, the back-link chain
tau7xr→s, and prior-pin preservation.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest
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
    from extract_parallel_pdf import (
        BEL_AND_THE_DRAGON_VERSE_COUNTS,
        PRAYER_OF_AZARIAH_VERSE_COUNTS,
        SUSANNA_VERSE_COUNTS,
    )

    return (
        PRAYER_OF_AZARIAH_VERSE_COUNTS,
        SUSANNA_VERSE_COUNTS,
        BEL_AND_THE_DRAGON_VERSE_COUNTS,
    )


# ──────────────────────────── floor dicts ──────────────────────────


class TestTau7XSPrayerOfAzariahVerseCounts:
    def test_symbol_present(self):
        paz, _, _ = _floors()
        assert isinstance(paz, dict)

    def test_single_chapter(self):
        paz, _, _ = _floors()
        assert sorted(paz.keys()) == [1]

    def test_total_verses_68(self):
        paz, _, _ = _floors()
        assert sum(paz.values()) == 68

    def test_books_yaml_paz_ch_count_1(self):
        books = yaml.safe_load((REPO / "content" / "books.yaml").read_text(encoding="utf-8"))["books"]
        rec = next(b for b in books if b["code"] == "paz")
        assert rec["ch_count"] == 1
        assert rec["bxx"] == "b45"
        assert "Azariah" in rec["title"] or "Three Holy Children" in rec["title"]


class TestTau7XSSusannaVerseCounts:
    """sus floor is PRE-STAGED (infra-ready) but content is DEFERRED
    at τ.7.x.s — Susanna is not distinctly present in this PDF's
    ተረፈ-ዳንኤል cluster (the τ.7.x.q lje + laodiceans precedent)."""

    def test_symbol_present(self):
        _, sus, _ = _floors()
        assert isinstance(sus, dict)

    def test_single_chapter(self):
        _, sus, _ = _floors()
        assert sorted(sus.keys()) == [1]

    def test_total_verses_64(self):
        _, sus, _ = _floors()
        assert sum(sus.values()) == 64

    def test_books_yaml_sus_ch_count_1(self):
        books = yaml.safe_load((REPO / "content" / "books.yaml").read_text(encoding="utf-8"))["books"]
        rec = next(b for b in books if b["code"] == "sus")
        assert rec["ch_count"] == 1
        assert rec["bxx"] == "b46"
        assert "Susanna" in rec["title"]


class TestTau7XSBelAndTheDragonVerseCounts:
    def test_symbol_present(self):
        _, _, bel = _floors()
        assert isinstance(bel, dict)

    def test_single_chapter(self):
        _, _, bel = _floors()
        assert sorted(bel.keys()) == [1]

    def test_total_verses_42(self):
        _, _, bel = _floors()
        assert sum(bel.values()) == 42

    def test_books_yaml_bel_ch_count_1(self):
        books = yaml.safe_load((REPO / "content" / "books.yaml").read_text(encoding="utf-8"))["books"]
        rec = next(b for b in books if b["code"] == "bel")
        assert rec["ch_count"] == 1
        assert rec["bxx"] == "b47"
        assert "Bel" in rec["title"] and "Dragon" in rec["title"]


# ─────────────────────────── structural_map ────────────────────────


class TestTau7XSStructuralMapPrayerOfAzariah:
    def _blk(self) -> dict:
        return _source_yaml()["structural_map"]["prayer_of_azariah"]

    def test_block_present(self):
        assert "prayer_of_azariah" in _source_yaml()["structural_map"]

    def test_book_codes(self):
        assert self._blk()["book_codes"] == ["paz"]

    def test_pdf_page_range_1449_1451(self):
        assert self._blk()["pdf_page_range"] == [1449, 1451]

    def test_verified_at_tau7xs(self):
        assert self._blk()["verified"] is True
        assert self._blk()["verified_at_phase"] == "τ.7.x.s"

    def test_chapter_count_expected_1(self):
        assert self._blk()["chapter_count_expected"] == 1

    def test_notes_document_pr_azar_v15(self):
        notes = self._blk()["notes"]
        assert "ተረፈ" in notes and "ዳንኤል" in notes
        assert "v.15" in notes or "አለቃ የለም" in notes


class TestTau7XSStructuralMapBelAndTheDragon:
    def _blk(self) -> dict:
        return _source_yaml()["structural_map"]["bel_and_the_dragon"]

    def test_block_present(self):
        assert "bel_and_the_dragon" in _source_yaml()["structural_map"]

    def test_book_codes(self):
        assert self._blk()["book_codes"] == ["bel"]

    def test_pdf_page_range_1452_1453(self):
        assert self._blk()["pdf_page_range"] == [1452, 1453]

    def test_verified_at_tau7xs(self):
        assert self._blk()["verified"] is True
        assert self._blk()["verified_at_phase"] == "τ.7.x.s"

    def test_chapter_count_expected_1(self):
        assert self._blk()["chapter_count_expected"] == 1

    def test_notes_document_jubilees_crossvalidation(self):
        notes = self._blk()["notes"]
        assert "1454" in notes and "ኩፉሌ" in notes
        assert "1454,1514" in notes or "[1454, 1514]" in notes


class TestTau7XSStructuralMapSusannaDeferred:
    """Susanna mirrors the `laodiceans` slot — DECLARED but
    present_in_pdf:false / pdf_page_range:null (the τ.6.x.0b
    honesty contract: no fabricated page range)."""

    def _blk(self) -> dict:
        return _source_yaml()["structural_map"]["susanna"]

    def test_block_present(self):
        assert "susanna" in _source_yaml()["structural_map"]

    def test_book_codes(self):
        assert self._blk()["book_codes"] == ["sus"]

    def test_present_in_pdf_false(self):
        assert self._blk()["present_in_pdf"] is False

    def test_pdf_page_range_null(self):
        assert self._blk()["pdf_page_range"] is None

    def test_verified_false(self):
        assert self._blk()["verified"] is False
        assert self._blk()["verified_at_phase"] == "τ.7.x.s"

    def test_deferred_to_tau6x3(self):
        assert self._blk()["deferred_to_phase"] == "τ.6.x.3"

    def test_notes_document_absence_finding(self):
        notes = " ".join(self._blk()["notes"].split())
        assert "NOT distinctly present" in notes
        assert "laodiceans" in notes and "lje" in notes
        assert "no fabricated page range" in notes


class TestTau7XSSusannaSectionCleanSystemExit:
    """`--section susanna` triggers a clean SystemExit by design
    (the _resolve_section present_in_pdf:false guard, identical to
    `laodiceans`) — Susanna ingest must NOT silently proceed."""

    def test_resolve_section_susanna_raises_systemexit(self):
        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import _resolve_section, load_source_config

        cfg = load_source_config()
        with pytest.raises(SystemExit) as exc:
            _resolve_section(cfg, "susanna")
        assert "present_in_pdf" in str(exc.value) or "ALTERNATE SOURCE" in str(exc.value)

    def test_susanna_still_a_declared_extraction_section(self):
        """present_in_pdf:false does NOT filter it out of the
        declared inventory (it has book_codes) — same as laodiceans."""
        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import _extraction_sections, load_source_config

        assert "susanna" in _extraction_sections(load_source_config())


class TestTau7XSJubileesSectionUnchanged:
    """The Π.1 structural_map.jubilees [1454,1514] page-range was
    only CROSS-VALIDATED by the τ.7.x.s scan (NOT modified at
    τ.7.x.s). CONVERTED at τ.7.x.t: that phase legitimately
    INGESTS Jubilees and upgrades the section verified:tentative→
    true / verified_at_phase Π.1→τ.7.x.t — the documented prior-
    pin-conversion-as-part-of-the-triggering-ship pattern (the
    τ.7.x.m est-skip-pin precedent + memory feedback_share_pin_
    pattern). The DURABLE invariant the τ.7.x.q/r/s cross-
    validations established is the [1454,1514] page-range anchor +
    book_codes — it never moves; only the verification confidence
    advanced when the book was actually ingested. The τ.7.x.s
    INGEST-RECORD historical `jubilees_section_unchanged` flag is
    NOT rewritten (it WAS unchanged at τ.7.x.s)."""

    def test_jubilees_page_range_anchor_unchanged(self):
        jub = _source_yaml()["structural_map"]["jubilees"]
        assert jub["book_codes"] == ["jub"]
        assert jub["pdf_page_range"] == [1454, 1514]
        assert jub["verified_at_phase"] in ("Π.1", "τ.7.x.t")


# ──────────────────────────── output modules ───────────────────────


class TestTau7XSPazPy:
    def test_paz_py_exists(self):
        assert (AMHARIC_TEWAHEDO / "paz.py").is_file()

    def test_constants(self):
        c = _constants("paz")
        assert c.get("TRANSLATION") == "amharic-tewahedo"
        assert c.get("BOOK") == "paz"
        assert c.get("SOURCE_QUALITY") == "ocr-tier3"
        assert c.get("INGEST_PHASE") == "τ.7.x.s"

    def test_total_verse_floor(self):
        # Empirical at ship: 30 (44.1% of the 68-v NRSV ceiling).
        # Floor 28 guards regression while tolerating OCR reparse drift.
        assert len(_verses("paz")) >= 28

    def test_first_verse_is_1_1(self):
        ch, v, text = _verses("paz")[0]
        assert (ch, v) == (1, 1)
        assert text


class TestTau7XSBelPy:
    def test_bel_py_exists(self):
        assert (AMHARIC_TEWAHEDO / "bel.py").is_file()

    def test_constants(self):
        c = _constants("bel")
        assert c.get("TRANSLATION") == "amharic-tewahedo"
        assert c.get("BOOK") == "bel"
        assert c.get("SOURCE_QUALITY") == "ocr-tier3"
        assert c.get("INGEST_PHASE") == "τ.7.x.s"

    def test_total_verse_floor(self):
        # Empirical at ship: 23 (54.8% of the 42-v NRSV ceiling).
        # Floor 21 guards regression.
        assert len(_verses("bel")) >= 21

    def test_first_verse_is_1_1(self):
        ch, v, text = _verses("bel")[0]
        assert (ch, v) == (1, 1)
        assert text


class TestTau7XSSusNotCreated:
    """sus is DEFERRED (present_in_pdf:false) — no amharic-tewahedo/
    sus.py module must exist at τ.7.x.s (the honest-deferral
    contract; reconciled at τ.6.x.3 / the future `dan` ingest)."""

    def test_sus_py_not_created(self):
        assert not (AMHARIC_TEWAHEDO / "sus.py").exists()

    def test_geez_sus_not_created(self):
        assert not (GEEZ_TEWAHEDO / "sus.py").exists()


# ─────────────────────────── coverage shape ────────────────────────


class TestTau7XSPazCoverage:
    """Empirical: single combined ch 1 partial (30/68); 0 overflow.
    Honest-low 44.1% (deep-PDF deuterocanon band, cf. jdt 35.4% /
    bar 33.3%), NOT a boundary error (τ.7.x.n discipline — content
    confirmed Pr-Azar v.15 + Song of the Three)."""

    def test_chapter_1_partial(self):
        paz, _, _ = _floors()
        got = len(_by_chapter("paz").get(1, []))
        assert 1 <= got < paz[1]

    def test_no_overflow_above_chapter_1(self):
        by = _by_chapter("paz")
        assert sum(len(v) for ch, v in by.items() if ch > 1) == 0


class TestTau7XSBelCoverage:
    """Empirical: single ch 1 partial (23/42); 0 overflow. 54.8%
    deuterocanon band; content-confirmed Bel + the dragon."""

    def test_chapter_1_partial(self):
        _, _, bel = _floors()
        got = len(_by_chapter("bel").get(1, []))
        assert 1 <= got < bel[1]

    def test_no_overflow_above_chapter_1(self):
        by = _by_chapter("bel")
        assert sum(len(v) for ch, v in by.items() if ch > 1) == 0


# ───────────────────── _source.yaml ingest block ───────────────────


class TestTau7XSSourceYamlIngestBlock:
    def _blk(self) -> dict:
        return _source_yaml()["ocr_strategy"]["tau7xs_ingest"]

    def test_block_exists(self):
        assert "tau7xs_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert self._blk()["shipped_at_phase"] == "τ.7.x.s"

    def test_structural_map_addition(self):
        sma = self._blk()["structural_map_addition"]
        assert sma["sections"] == ["prayer_of_azariah", "susanna", "bel_and_the_dragon"]
        assert sma["prayer_of_azariah"]["pdf_page_range"] == [1449, 1451]
        assert sma["bel_and_the_dragon"]["pdf_page_range"] == [1452, 1453]
        assert sma["susanna"]["present_in_pdf"] is False

    def test_susanna_absence_finding_documented(self):
        sma = self._blk()["structural_map_addition"]
        finding = " ".join(sma["susanna_absence_finding"].split())
        assert "NOT distinctly present" in finding
        assert "lje" in finding and "laodiceans" in finding

    def test_empirical_validation(self):
        ev = self._blk()["empirical_validation"]
        assert ev["paz"]["renumbered_verse_count"] == 30
        assert ev["paz"]["coverage_pct"] == 44.1
        assert ev["bel"]["renumbered_verse_count"] == 23
        assert ev["bel"]["coverage_pct"] == 54.8
        assert ev["sus"]["status"] == "deferred-present_in_pdf-false"

    def test_honest_low_not_boundary_error_documented(self):
        band = " ".join(self._blk()["empirical_validation"]["coverage_band_position"].split())
        assert "NOT" in band and "boundary error" in band and "τ.7.x.n" in band

    def test_parser_api_change_zero(self):
        api = self._blk()["parser_api_change"]
        assert "No parser API changes" in api
        assert "29-ship" in api

    def test_next_phase_tau7xt(self):
        assert self._blk()["next_phase"] == "τ.7.x.t"

    def test_pipeline_reused_back_link(self):
        assert self._blk()["pipeline_reused_at_phase"] == "τ.7.x.s"

    def test_jubilees_section_unchanged_contract(self):
        contracts = self._blk()["closed_arc_contracts_preserved"]
        assert contracts.get("jubilees_section_unchanged") is True

    def test_daniel_additions_cluster_drained(self):
        assert self._blk()["daniel_additions_cluster_drained"] == "p1449-1453"


# ─────────────────────── _meta.yaml ingest record ──────────────────


class TestTau7XSMetaYamlIngestRecord:
    def test_stats_books_at_least_twenty_two(self):
        assert _meta()["stats"]["books"] >= 22

    def test_stats_verses_at_least_10810(self):
        assert _meta()["stats"]["verses"] >= 10810

    def test_stats_books_outside_kjv_twelve(self):
        """+paz +bel (both deuterocanonical Daniel-additions) on
        top of the prior 10. sus DEFERRED — not counted."""
        assert _meta()["stats"]["books_outside_kjv"] >= 12

    def test_tau7xs_ingest_record(self):
        r = _meta()["ingest_record_tau7xs"]
        assert r["phase"] == "τ.7.x.s"
        assert r["ingested_book_codes"] == ["paz", "bel"]
        assert r["coverage"]["paz"]["verses_extracted"] == 30
        assert r["coverage"]["bel"]["verses_extracted"] == 23
        assert r.get("deuterocanonical") is True

    def test_tau7xs_susanna_deferral_documented(self):
        r = _meta()["ingest_record_tau7xs"]
        finding = " ".join(r["susanna_structural_discovery_finding"].split())
        assert "NOT distinctly present" in finding
        assert "DEFERRED" in finding

    def test_tau7xr_pipeline_reused_back_link_added(self):
        # τ.7.x.r record gains the back-link to τ.7.x.s.
        assert _meta()["ingest_record_tau7xr"]["next_book"] == "paz"

    def test_prior_ingest_records_present(self):
        m = _meta()
        assert "ingest_record" in m
        for tag in ("tau7xh", "tau7xn", "tau7xo", "tau7xp", "tau7xq", "tau7xr"):
            assert f"ingest_record_{tag}" in m, f"prior ingest record missing: {tag}"


# ───────────── zero-API-delta + prior-pin preservation ─────────────


class TestTau7XSZeroApiDeltaAndPriorPins:
    def test_cli_renumber_choices_extended(self):
        src = (REPO / "scripts" / "extract_parallel_pdf.py").read_text(encoding="utf-8")
        assert '"prayer_of_azariah"' in src
        assert '"susanna"' in src
        assert '"bel_and_the_dragon"' in src
        # def + comments + 2 elif sites + help → ≥3 each
        assert src.count("PRAYER_OF_AZARIAH_VERSE_COUNTS") >= 3
        assert src.count("SUSANNA_VERSE_COUNTS") >= 3
        assert src.count("BEL_AND_THE_DRAGON_VERSE_COUNTS") >= 3

    def test_parser_api_functions_untouched(self):
        src = (REPO / "scripts" / "extract_parallel_pdf.py").read_text(encoding="utf-8")
        assert "def parse_verses_from_text(" in src
        assert "def _parse_paragraph_mode(" in src
        assert "def renumber_against_floor(" in src

    def test_prior_floor_dicts_untouched(self):
        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import BARUCH_VERSE_COUNTS, WISDOM_OF_SOLOMON_VERSE_COUNTS

        assert sum(BARUCH_VERSE_COUNTS.values()) == 141
        assert sum(WISDOM_OF_SOLOMON_VERSE_COUNTS.values()) == 436

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
        ):
            assert (AMHARIC_TEWAHEDO / f"{book}.py").is_file(), f"prior τ.7.x.* book {book} must persist"

    def test_geez_paz_bel_jub_1en_ingested_catchup_complete(self):
        """MIGRATED at the τ.6.x.2.u ship-time (2026-05-20) per memory
        `feedback_share_pin_pattern` + the τ.6.x.2.j-t precedent.
        Originally asserted the Geʽez `paz.py` AND `bel.py` must NOT
        exist (τ.7.x.s was --lang amharic; D4-c deferral). τ.6.x.2.s
        flipped both `paz` and `bel` halves; τ.6.x.2.t flipped the
        `jub` half (Jubilees / Mäṣḥafä Kufāle — sixth catchup ship,
        ninth EOTC-parallel block); τ.6.x.2.u (the SEVENTH and FINAL
        ship of the deuterocanon Geʽez catchup) wrote the ocr-tier3
        parallel-PDF Geʽez 1en.py, draining the tenth (and final)
        EOTC-parallel block and CLOSING the τ.6.x.2.* OT catchup
        queue (sir → 4ba → bar → wis → paz+bel → jub → 1en). All
        four halves now durable positive invariants: paz/bel exist
        at τ.6.x.2.s, jub at τ.6.x.2.t, 1en at τ.6.x.2.u (all
        ocr-tier3). Susanna (sus) DEFERRED to τ.6.x.3 (not present
        in PDF)."""
        import ast

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

    def test_tau7xq_tau7xr_pins_preserved(self):
        s = _source_yaml()
        assert s["structural_map"]["baruch"]["pdf_page_range"] == [1429, 1431]
        assert s["structural_map"]["wisdom_of_solomon"]["pdf_page_range"] == [1432, 1448]
        assert s["ocr_strategy"]["tau7xr_ingest"]["block_major_pair_drained"] == "p1429-1448"

    def test_tau7xn_meqabyan_correction_preserved(self):
        s = _source_yaml()
        assert s["structural_map"]["meqabyan"]["subsections"]["mq2"] == [1351, 1368]
        assert (AMHARIC_TEWAHEDO / "mq1.py").is_file()

    def test_back_link_chain_tau7xr_to_s(self):
        """tau7xr.next_phase == τ.7.x.s and tau7xs exists + points
        forward to τ.7.x.t — the unbroken per-book back-link chain."""
        s = _source_yaml()
        assert s["ocr_strategy"]["tau7xr_ingest"]["next_phase"] == "τ.7.x.s"
        assert s["ocr_strategy"]["tau7xs_ingest"]["next_phase"] == "τ.7.x.t"
