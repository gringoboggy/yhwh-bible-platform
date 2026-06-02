"""τ.7.x.u — Amharic 1 Enoch (Mäṣḥafä Hēnok) full-book ingest pins
+ the structural_map.one_enoch UPGRADE + the 3-site prior-pin
conversion (2026-05-16; overnight autonomous-run).

TWENTY-FOURTH τ.7.x.* per-book ship under D4-c Amharic-first + D1-a
per-book cadence. SECOND of the two LARGE Π.1-mapped Tewahedo-
distinctive books — with this ship BOTH (Jubilees τ.7.x.t + 1 Enoch
τ.7.x.u) are ingested. The standalone-Amharic-Bible rendering
FOUNDATION per dev/SCOPE_2026-05-16-parallel-bible-standalone-
bibles.md + CLAUDE_PROJECT_RULES §1 — NOT a popup-language slot.

- `1en` p1515-1566; ONE_ENOCH_VERSE_COUNTS (108 ch / 1064 v; R.H.
  Charles 1912 "The Book of Enoch" canonical CEILING; books.yaml
  `1en` ch_count:108 b16). 806/1064 = 75.8% — healthy mid-high band
  (cf. jub 82.3% / mq-trilogy 65%; far above the deuterocanon-deep-
  PDF band). Content-confirmed (the Book of the Watchers). NOT a
  boundary error (τ.7.x.s/t cross-validated p1515 opens 1 Enoch
  after jubilees p1514, p1567 then Matthew).

STRUCTURAL_MAP UPGRADE (not addition — one_enoch pre-existed
Π.1-tentative): verified tentative->true, verified_at_phase
Π.1->τ.7.x.u; pdf_page_range [1515,1566] UNCHANGED (the durable
cross-validation anchor, cross-validated 3x at τ.7.x.s/t). The
stale Π.1 "tentative flag" paragraph was superseded
([Historical, superseded]) in the same edit (coherence fix). The
prior Π.1-foundation one_enoch LIVE-state pins (pi1
test_one_enoch_section_declared + TestPi1OneEnochSection
test_verified_tentative/date, pi1b one_enoch_section_unchanged)
are CONVERTED by this ship (the documented prior-pin-conversion-
as-part-of-the-triggering-ship pattern; τ.7.x.m + τ.7.x.t
precedent + memory feedback_share_pin_pattern). jubilees pins
(already τ.7.x.t) + laodiceans + the Π.1 HISTORICAL inventory
pins + the τ.7.x.r/s/t ingest-record flags are NOT touched.

CLEAN ship: parser API AND writer both UNCHANGED at τ.7.x.u (the
τ.7.x.t repr() writer-fix is already in place and benefits this
ship but is not a new delta). Only deltas are data:
ONE_ENOCH_VERSE_COUNTS + dispatch + the one_enoch upgrade.
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
    from extract_parallel_pdf import ONE_ENOCH_VERSE_COUNTS

    return ONE_ENOCH_VERSE_COUNTS


def _notes_1en_max() -> dict[int, int]:
    """The project's existing γ.4.4 Mäṣḥafä Hēnok per-chapter
    annotation maxima from content/notes/1en.py (the floor-
    coordination lower bound)."""
    import collections

    tree = ast.parse((REPO / "content" / "notes" / "1en.py").read_text(encoding="utf-8"))
    mx: dict[int, int] = collections.defaultdict(int)
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for tg in n.targets:
                if isinstance(tg, ast.Name) and tg.id.isupper():
                    try:
                        v = ast.literal_eval(n.value)
                    except Exception:
                        v = None
                    if isinstance(v, (list, tuple)):
                        for r in v:
                            if (
                                isinstance(r, (list, tuple))
                                and len(r) >= 2
                                and isinstance(r[0], int)
                                and isinstance(r[1], int)
                            ):
                                mx[r[0]] = max(mx[r[0]], r[1])
    return dict(mx)


# ──────────────────────────── floor dict ───────────────────────────


class TestTau7XUOneEnochVerseCounts:
    def test_symbol_present(self):
        assert isinstance(_floor(), dict)

    def test_108_chapters_contiguous(self):
        assert sorted(_floor().keys()) == list(range(1, 109))

    def test_total_verses_1064(self):
        assert sum(_floor().values()) == 1064

    def test_books_yaml_1en_ch_count_108(self):
        books = yaml.safe_load((REPO / "content" / "books.yaml").read_text(encoding="utf-8"))["books"]
        rec = next(b for b in books if b["code"] == "1en")
        assert rec["ch_count"] == 108
        assert rec["bxx"] == "b16"
        assert "Enoch" in rec["title"]

    def test_floor_coordination_all_108_ge_gamma44_maxima(self):
        """STRONGER than τ.7.x.t's 3-sample: every one of the 108
        chapters' ceiling >= the project's γ.4.4 notes/1en.py
        per-chapter maxima (the τ.7.x.n/t δ.1.x-proof discipline)."""
        f = _floor()
        mx = _notes_1en_max()
        bad = [(c, f[c], mx.get(c, 0)) for c in range(1, 109) if f[c] < mx.get(c, 0)]
        assert not bad, f"floor below γ.4.4 maxima at: {bad}"

    def test_distinctive_chapters_exact_match_gamma44(self):
        """Exact matches at the distinctive long chapters confirm
        the shared R.H. Charles 1912 enumeration."""
        f = _floor()
        mx = _notes_1en_max()
        assert f[14] == 25 and mx.get(14) == 25
        assert f[90] == 42 and mx.get(90) == 42


# ─────────────────── structural_map.one_enoch UPGRADE ──────────────


class TestTau7XUStructuralMapOneEnochUpgraded:
    def _blk(self) -> dict:
        return _source_yaml()["structural_map"]["one_enoch"]

    def test_book_codes(self):
        assert self._blk()["book_codes"] == ["1en"]

    def test_pdf_page_range_unchanged_anchor(self):
        assert self._blk()["pdf_page_range"] == [1515, 1566]

    def test_verified_upgraded_to_true(self):
        assert self._blk()["verified"] is True

    def test_verified_at_phase_upgraded_to_tau7xu(self):
        assert self._blk()["verified_at_phase"] == "τ.7.x.u"

    def test_chapter_count_expected_unchanged(self):
        assert self._blk()["chapter_count_expected"] == 108

    def test_notes_preserve_pi1_provenance_document_upgrade_no_contradiction(self):
        notes = " ".join(self._blk()["notes"].split())
        assert "Discovered at Π.1" in notes  # Π.1 provenance preserved
        assert "ሄኖክ" in notes and "Charles" in notes  # pi1 notes-test invariants
        assert "UPGRADED tentative→true" in notes
        assert "τ.7.x.u" in notes
        # the stale contradictory Π.1 tentative-flag paragraph was superseded
        assert "'tentative' verification flag matches jubilees — boundary" not in notes
        assert "Historical, superseded" in notes


# ──────────────────────────── output module ────────────────────────


class TestTau7XU1enPy:
    def test_1en_py_exists(self):
        assert (AMHARIC_TEWAHEDO / "1en.py").is_file()

    def test_constants(self):
        c = _constants("1en")
        assert c.get("TRANSLATION") == "amharic-tewahedo"
        assert c.get("BOOK") == "1en"
        assert c.get("SOURCE_QUALITY") == "ocr-tier3"
        assert c.get("INGEST_PHASE") == "τ.7.x.u"

    def test_total_verse_floor(self):
        # Empirical at ship: 806 (75.8% of the 1064-v ceiling).
        # Floor 750 guards regression while tolerating OCR drift.
        assert len(_verses("1en")) >= 750

    def test_first_verse_is_1_1(self):
        ch, v, text = _verses("1en")[0]
        assert (ch, v) == (1, 1)
        assert text

    def test_geez_1en_created_at_tau6x2u(self):
        # FLIPPED at τ.6.x.2.u (2026-05-20) per memory
        # `feedback_share_pin_pattern`: the original D4-c "Geʽez
        # follows Amharic at τ.6.x.2.j+" deferral pin was converted
        # to a durable positive invariant when the Geʽez 1 Enoch
        # ship landed 1en.py at ocr-tier3 with INGEST_PHASE
        # τ.6.x.2.u — the FINAL book in the τ.6.x.2.* OT catchup
        # queue (sir → 4ba → bar → wis → paz+bel → jubilees → 1en);
        # drains the tenth (and final) EOTC-parallel block and
        # CLOSES the parallel-column-catchup arc.
        import ast

        assert (GEEZ_TEWAHEDO / "1en.py").is_file(), "Geʽez 1en.py must EXIST after the τ.6.x.2.u catchup ship"
        tree = ast.parse((GEEZ_TEWAHEDO / "1en.py").read_text(encoding="utf-8"))
        consts = {
            t.id: ast.literal_eval(n.value)
            for n in ast.walk(tree)
            if isinstance(n, ast.Assign)
            for t in n.targets
            if isinstance(t, ast.Name) and t.id in ("SOURCE_QUALITY", "INGEST_PHASE", "BOOK", "TRANSLATION")
        }
        assert consts.get("SOURCE_QUALITY") == "ocr-tier3"
        assert consts.get("INGEST_PHASE") == "τ.6.x.2.u"
        assert consts.get("BOOK") == "1en"
        assert consts.get("TRANSLATION") == "geez-tewahedo"


# ─────────────────────────── coverage shape ────────────────────────


class TestTau7XU1enCoverage:
    """Empirical: ch 1 full (=9); recovered text fills up to ch ~89;
    ~90-108 empty; 0 overflow. 75.8% mid-high band; content-confirmed
    the Book of the Watchers."""

    def test_chapter_1_fully_populated(self):
        f = _floor()
        assert len(_by_chapter("1en").get(1, [])) == f[1]

    def test_last_populated_chapter_within_108(self):
        by = _by_chapter("1en")
        last = max(by)
        assert 80 <= last <= 108  # empirical ~89; never beyond the 108-ch book

    def test_tail_chapters_empty(self):
        by = _by_chapter("1en")
        # ocr-tier3 recovery runs out before the final chapters.
        assert len(by.get(108, [])) == 0

    def test_no_overflow_above_chapter_108(self):
        by = _by_chapter("1en")
        assert sum(len(v) for ch, v in by.items() if ch > 108) == 0


# ─────────────── clean ship: writer + parser unchanged ─────────────


class TestTau7XUCleanShipNoToolingDelta:
    def test_writer_still_repr_serialization_from_tau7xt(self):
        """τ.7.x.u introduces NO writer change; the τ.7.x.t repr()
        fix remains in place and benefits this ship."""
        src = (REPO / "scripts" / "extract_parallel_pdf.py").read_text(encoding="utf-8")
        assert "({ch!r}, {v!r}, {text!r})," in src

    def test_1en_py_no_invalid_escape_sequence(self):
        """1en OCR had backslash artifacts; under the (τ.7.x.t)
        repr() writer they parse with ZERO SyntaxWarning."""
        src = (AMHARIC_TEWAHEDO / "1en.py").read_text(encoding="utf-8")
        with warnings.catch_warnings():
            warnings.simplefilter("error", SyntaxWarning)
            ast.parse(src)

    def test_parser_api_functions_untouched(self):
        src = (REPO / "scripts" / "extract_parallel_pdf.py").read_text(encoding="utf-8")
        assert "def parse_verses_from_text(" in src
        assert "def _parse_paragraph_mode(" in src
        assert "def renumber_against_floor(" in src


# ───────────────────── _source.yaml ingest block ───────────────────


class TestTau7XUSourceYamlIngestBlock:
    def _blk(self) -> dict:
        return _source_yaml()["ocr_strategy"]["tau7xu_ingest"]

    def test_block_exists(self):
        assert "tau7xu_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert self._blk()["shipped_at_phase"] == "τ.7.x.u"

    def test_structural_map_upgrade_recorded(self):
        u = self._blk()["structural_map_upgrade"]
        assert u["section"] == "one_enoch"
        assert u["pdf_page_range"] == [1515, 1566]
        assert u["verified"] == "tentative→true"
        assert u["verified_at_phase"] == "Π.1→τ.7.x.u"

    def test_prior_pin_conversion_documented(self):
        conv = " ".join(self._blk()["prior_pin_conversion"].split())
        # Short tokens only — the YAML block-scalar soft-wraps long
        # method names (e.g. `test_one_enoch_section_\ndeclared`), so
        # asserting the unwrapped name is brittle. These robustly
        # confirm the one_enoch pin conversion is documented.
        assert "one_enoch" in conv
        assert "pi1b" in conv  # the pi1b test_one_enoch_section_unchanged conversion
        assert "Π.1, τ.7.x.u" in conv
        assert "laodiceans" in conv  # explicitly NOT touched

    def test_parser_api_clean_no_writer_delta(self):
        api = " ".join(self._blk()["parser_api_change"].split())
        assert "CLEAN ship" in api
        assert "31-ship" in api
        assert "zero-writer-delta" in api

    def test_empirical_validation(self):
        ev = self._blk()["empirical_validation"]
        assert ev["renumbered_verse_count"] == 806
        assert ev["coverage_pct"] == 75.8

    def test_next_phase_tau7xv(self):
        assert self._blk()["next_phase"] == "τ.7.x.v"

    def test_pipeline_reused_back_link(self):
        assert self._blk()["pipeline_reused_at_phase"] == "τ.7.x.u"

    def test_two_large_tewahedo_distinctive_complete(self):
        c = self._blk()["closed_arc_contracts_preserved"]
        assert c.get("one_enoch_now_ingested") is True
        assert c.get("two_large_tewahedo_distinctive_complete") is True


# ─────────────────────── _meta.yaml ingest record ──────────────────


class TestTau7XUMetaYamlIngestRecord:
    def test_stats_books_at_least_twenty_four(self):
        assert _meta()["stats"]["books"] >= 24

    def test_stats_verses_at_least_12691(self):
        assert _meta()["stats"]["verses"] >= 12691

    def test_stats_books_outside_kjv_fourteen(self):
        assert _meta()["stats"]["books_outside_kjv"] >= 14

    def test_tau7xu_ingest_record(self):
        r = _meta()["ingest_record_tau7xu"]
        assert r["phase"] == "τ.7.x.u"
        assert r["ingested_book_codes"] == ["1en"]
        assert r["coverage"]["verses_extracted"] == 806
        assert r.get("tewahedo_distinctive") is True
        assert r.get("two_large_tewahedo_distinctive_complete") is True

    def test_tau7xt_next_book_was_1en(self):
        # The τ.7.x.t prediction came true (not rewritten — history).
        assert _meta()["ingest_record_tau7xt"]["next_book"] == "1en"

    def test_prior_ingest_records_present(self):
        m = _meta()
        assert "ingest_record" in m
        for tag in ("tau7xn", "tau7xo", "tau7xp", "tau7xq", "tau7xr", "tau7xs", "tau7xt"):
            assert f"ingest_record_{tag}" in m, f"prior ingest record missing: {tag}"


# ────────── prior-pin conversion + preservation ───────────


class TestTau7XUPriorPinConversionAndPreservation:
    def test_pi1_one_enoch_pins_converted(self):
        src = (REPO / "tests" / "test_parallel_bible_pi1.py").read_text(encoding="utf-8")
        assert 'oen["verified_at_phase"] in ("Π.1", "τ.7.x.u")' in src
        assert 'self._sec()["verified"] in ("tentative", True)' in src

    def test_pi1b_one_enoch_pin_converted(self):
        src = (REPO / "tests" / "test_parallel_bible_pi1b.py").read_text(encoding="utf-8")
        assert 'oen.get("verified_at_phase") in ("Π.1", "τ.7.x.u")' in src

    def test_jubilees_pins_untouched_still_tau7xt(self):
        s = _source_yaml()
        assert s["structural_map"]["jubilees"]["verified_at_phase"] == "τ.7.x.t"
        pi1b = (REPO / "tests" / "test_parallel_bible_pi1b.py").read_text(encoding="utf-8")
        assert 'jub.get("verified_at_phase") in ("Π.1", "τ.7.x.t")' in pi1b

    def test_laodiceans_still_pi1_present_in_pdf_false(self):
        lao = _source_yaml()["structural_map"]["laodiceans"]
        assert lao["present_in_pdf"] is False
        assert lao["verified_at_phase"] == "Π.1"

    def test_prior_floor_dicts_untouched(self):
        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import JUBILEES_VERSE_COUNTS, WISDOM_OF_SOLOMON_VERSE_COUNTS

        assert sum(JUBILEES_VERSE_COUNTS.values()) == 1306
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
            "paz",
            "bel",
            "jub",
        ):
            assert (AMHARIC_TEWAHEDO / f"{book}.py").is_file(), f"prior τ.7.x.* book {book} must persist"

    def test_back_link_chain_tau7xt_to_u(self):
        s = _source_yaml()
        assert s["ocr_strategy"]["tau7xt_ingest"]["next_phase"] == "τ.7.x.u"
        assert s["ocr_strategy"]["tau7xu_ingest"]["next_phase"] == "τ.7.x.v"
