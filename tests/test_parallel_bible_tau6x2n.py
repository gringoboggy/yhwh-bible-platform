"""τ.6.x.2.n — Geʽez Mäqabyan trilogy (mq1/mq2/mq3) ingest pins
(2026-05-16).

The FIRST MULTI-BOOK Geʽez catchup ship (3 per-book extractions in
one phase — the Amharic τ.7.x.n precedent). Books 13→16 of
geez-tewahedo/. CONTINUES the post-Psalms Geʽez deuterocanon-
catchup sub-arc (2es → tob → jdt → est → mq1/mq2/mq3). Pipeline
reused VERBATIM from the Amharic τ.7.x.n ship — MQ1/MQ2/MQ3_VERSE_
COUNTS + structural_map.meqabyan_{i,ii,iii} reused, zero-parser-
API-delta, only the `--lang geez` flip differs (one per book).

Mäqabyan is the uniquely-Tewahedo-canonical Maccabees-named-but-
distinct trilogy. Per the extract_parallel_pdf QUALITY POLICY this
parallel-PDF Geʽez Mäqabyan is `ocr-tier3` and explicitly
**δ.1.x-replaceable** (the page-image-tier1 Phase-4 track is a
SEPARATE future operator-mediated effort; the `geez_tewahedo_mq123`
slot is distinct from the Π.1 page-image authoritative Geʽez slot).
Shipping the ocr-tier3 interim here is the documented τ.7.x.n
treatment — no approval gate.

Empirical coverage (clean renumber UNDERFLOWs, all ocr-tier3):
- mq1: 352/502 = 70.1% — ch 1-27 full (cumulative floor 325),
  ch 28 partial (27/38), ch 29-36 empty, no overflow.
- mq2: 188/256 = 73.4% — ch 1-14 full (cumulative floor 184),
  ch 15 partial (4/11), ch 16-21 empty, no overflow.
- mq3: 68/188 = 36.2% — ch 1-3 full (cumulative floor 67),
  ch 4 partial (1/34), ch 5-10 empty, no overflow.
The Geʽez/Amharic columns extract DISTINCT text (verified at ship).
Quality reconciled at the τ.6.x.3 batched audit (+ the δ.1.x
page-image upgrade track) per the τ.6.x.0b honesty contract.

Pins validate the trilogy floors reused-unchanged, structural_map
sections reused-unchanged, the 3 output modules, per-book coverage
shapes, geez _meta (16 books / 7 outside-KJV), _source tau6x2n_
ingest, the tau7xn cross-column geez_tewahedo_mq123 slot update,
prior-arc preservation, and state-docs.
"""

from __future__ import annotations

import ast
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SOURCE_YAML = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"
GEEZ_TEWAHEDO = REPO / "content" / "translations" / "geez-tewahedo"
AMHARIC_TEWAHEDO = REPO / "content" / "translations" / "amharic-tewahedo"

TRILOGY = ("mq1", "mq2", "mq3")
# (book, section, floor-symbol, ch_count, total, full_through, partial_ch,
#  partial_got, partial_exp, empty_from, empty_to, extracted, cov_pct)
SPEC = {
    "mq1": dict(
        section="meqabyan_i",
        floor="MQ1_VERSE_COUNTS",
        chs=36,
        total=502,
        full_through=27,
        partial_ch=28,
        partial_got=27,
        partial_exp=38,
        extracted=352,
        cov=70.1,
        pages=[1318, 1350],
    ),
    "mq2": dict(
        section="meqabyan_ii",
        floor="MQ2_VERSE_COUNTS",
        chs=21,
        total=256,
        full_through=14,
        partial_ch=15,
        partial_got=4,
        partial_exp=11,
        extracted=188,
        cov=73.4,
        pages=[1351, 1368],
    ),
    "mq3": dict(
        section="meqabyan_iii",
        floor="MQ3_VERSE_COUNTS",
        chs=10,
        total=188,
        full_through=3,
        partial_ch=4,
        partial_got=1,
        partial_exp=34,
        extracted=68,
        cov=36.2,
        pages=[1369, 1378],
    ),
}


def _source_yaml() -> dict:
    return yaml.safe_load(SOURCE_YAML.read_text(encoding="utf-8"))


def _geez_meta() -> dict:
    return yaml.safe_load((GEEZ_TEWAHEDO / "_meta.yaml").read_text(encoding="utf-8"))


def _verses(translation_dir: Path, book: str) -> list[tuple]:
    py = translation_dir / f"{book}.py"
    tree = ast.parse(py.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "VERSES":
                    return ast.literal_eval(node.value)
    raise AssertionError(f"{translation_dir.name}/{book}.py must define VERSES")


def _constants(translation_dir: Path, book: str) -> dict:
    py = translation_dir / f"{book}.py"
    tree = ast.parse(py.read_text(encoding="utf-8"))
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


def _by_chapter(translation_dir: Path, book: str) -> dict[int, list[tuple]]:
    out: dict[int, list[tuple]] = {}
    for ch, v, t in _verses(translation_dir, book):
        out.setdefault(ch, []).append((v, t))
    return out


def _floor(symbol: str) -> dict:
    import sys

    sys.path.insert(0, str(REPO / "scripts"))
    import extract_parallel_pdf

    return getattr(extract_parallel_pdf, symbol)


# ─────────────────── floor dicts reused unchanged ──────────────────


class TestTau6X2NMqFloorsReusedUnchanged:
    """MQ1/MQ2/MQ3_VERSE_COUNTS were added at the Amharic τ.7.x.n ship
    and are reused VERBATIM for the Geʽez column — zero-parser-API-
    delta. The trilogy total is 946 (502+256+188)."""

    def test_mq1_36_ch_502(self):
        d = _floor("MQ1_VERSE_COUNTS")
        assert sorted(d.keys()) == list(range(1, 37))
        assert sum(d.values()) == 502

    def test_mq2_21_ch_256(self):
        d = _floor("MQ2_VERSE_COUNTS")
        assert sorted(d.keys()) == list(range(1, 22))
        assert sum(d.values()) == 256

    def test_mq3_10_ch_188(self):
        d = _floor("MQ3_VERSE_COUNTS")
        assert sorted(d.keys()) == list(range(1, 11))
        assert sum(d.values()) == 188

    def test_trilogy_total_946(self):
        assert sum(sum(_floor(s).values()) for s in ("MQ1_VERSE_COUNTS", "MQ2_VERSE_COUNTS", "MQ3_VERSE_COUNTS")) == 946

    def test_cumulative_boundaries_match_empirical(self):
        """The renumber fill points: mq1 ch1-27=325, mq2 ch1-14=184,
        mq3 ch1-3=67 (so the extracted 352/188/68 land partial at
        ch28/ch15/ch4 respectively)."""
        assert sum(_floor("MQ1_VERSE_COUNTS")[c] for c in range(1, 28)) == 325
        assert sum(_floor("MQ2_VERSE_COUNTS")[c] for c in range(1, 15)) == 184
        assert sum(_floor("MQ3_VERSE_COUNTS")[c] for c in range(1, 4)) == 67


# ───────────── structural_map sections reused unchanged ─────────────


class TestTau6X2NStructuralMapReusedUnchanged:
    """structural_map.meqabyan_{i,ii,iii} were verified at τ.7.x.n;
    the Geʽez column reuses them UNCHANGED (same parallel PDF)."""

    def test_meqabyan_i(self):
        b = _source_yaml()["structural_map"]["meqabyan_i"]
        assert b["book_codes"] == ["mq1"]
        assert b["pdf_page_range"] == [1318, 1350]
        assert b["verified"] is True and b["verified_at_phase"] == "τ.7.x.n"
        assert b["chapter_count_expected"] == 36

    def test_meqabyan_ii(self):
        b = _source_yaml()["structural_map"]["meqabyan_ii"]
        assert b["book_codes"] == ["mq2"]
        assert b["pdf_page_range"] == [1351, 1368]
        assert b["verified"] is True and b["verified_at_phase"] == "τ.7.x.n"
        assert b["chapter_count_expected"] == 21

    def test_meqabyan_iii(self):
        b = _source_yaml()["structural_map"]["meqabyan_iii"]
        assert b["book_codes"] == ["mq3"]
        assert b["pdf_page_range"] == [1369, 1378]
        assert b["verified"] is True and b["verified_at_phase"] == "τ.7.x.n"
        assert b["chapter_count_expected"] == 10


# ──────────────────────── output modules ───────────────────────────


class TestTau6X2NMqPy:
    def test_all_three_exist(self):
        for c in TRILOGY:
            assert (GEEZ_TEWAHEDO / f"{c}.py").is_file(), f"geez-tewahedo/{c}.py must exist"

    def test_constants(self):
        for c in TRILOGY:
            k = _constants(GEEZ_TEWAHEDO, c)
            assert k.get("TRANSLATION") == "geez-tewahedo"
            assert k.get("BOOK") == c
            assert k.get("SOURCE_QUALITY") == "ocr-tier3"
            assert k.get("SOURCE_PROVENANCE") == "parallel-bible-eotc"
            assert k.get("INGEST_PHASE") == "τ.6.x.2.n"

    def test_verse_floors(self):
        # Empirical: mq1 352, mq2 188, mq3 68. Conservative regression
        # floors permitting parser refinement.
        floors = {"mq1": 320, "mq2": 170, "mq3": 60}
        for c in TRILOGY:
            n = len(_verses(GEEZ_TEWAHEDO, c))
            assert n >= floors[c], f"τ.6.x.2.n geez {c} must have ≥{floors[c]} verses; got {n}"

    def test_first_verse_each(self):
        for c in TRILOGY:
            ch, v, text = _verses(GEEZ_TEWAHEDO, c)[0]
            assert (ch, v) == (1, 1) and text

    def test_geez_distinct_from_amharic(self):
        for c in TRILOGY:
            assert _verses(GEEZ_TEWAHEDO, c)[0][2] != _verses(AMHARIC_TEWAHEDO, c)[0][2], (
                f"Geʽez {c}[1:1] must differ from Amharic {c}[1:1] (not a misattribution bug)"
            )


# ──────────────────────── coverage shapes ──────────────────────────


class TestTau6X2NCoverageShapes:
    """Per-book clean renumber UNDERFLOW shapes (no overflow)."""

    def test_full_chapters(self):
        for c, spec in SPEC.items():
            floor = _floor(spec["floor"])
            by_ch = _by_chapter(GEEZ_TEWAHEDO, c)
            for ch in range(1, spec["full_through"] + 1):
                assert len(by_ch.get(ch, [])) == floor[ch], (
                    f"τ.6.x.2.n {c} ch {ch} must be full ({floor[ch]}); got {len(by_ch.get(ch, []))}"
                )

    def test_partial_chapter(self):
        for c, spec in SPEC.items():
            by_ch = _by_chapter(GEEZ_TEWAHEDO, c)
            got = len(by_ch.get(spec["partial_ch"], []))
            assert 1 <= got < spec["partial_exp"], (
                f"τ.6.x.2.n {c} ch {spec['partial_ch']} partial expected (1..{spec['partial_exp'] - 1}); got {got}"
            )

    def test_empty_tail_and_no_overflow(self):
        for c, spec in SPEC.items():
            by_ch = _by_chapter(GEEZ_TEWAHEDO, c)
            for ch in range(spec["partial_ch"] + 1, spec["chs"] + 1):
                assert len(by_ch.get(ch, [])) == 0, f"τ.6.x.2.n {c} ch {ch} should be empty"
            overflow = sum(len(v) for ch, v in by_ch.items() if ch > spec["chs"])
            assert overflow == 0, f"τ.6.x.2.n {c} overflow should be 0; got {overflow}"


# ───────────────────── _source.yaml ingest block ───────────────────


class TestTau6X2NSourceYamlIngestBlock:
    def _blk(self) -> dict:
        return _source_yaml()["ocr_strategy"]["tau6x2n_ingest"]

    def test_block_exists(self):
        assert "tau6x2n_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert self._blk()["shipped_at_phase"] == "τ.6.x.2.n"

    def test_multi_book_marker(self):
        assert self._blk()["multi_book"] is True
        assert self._blk()["ingested_book_codes"] == ["mq1", "mq2", "mq3"]

    def test_helpers_reused(self):
        reused = self._blk()["helpers_reused"]
        for s in ("MQ1_VERSE_COUNTS", "MQ2_VERSE_COUNTS", "MQ3_VERSE_COUNTS"):
            assert s in reused
        for s in ("structural_map.meqabyan_i", "structural_map.meqabyan_ii", "structural_map.meqabyan_iii"):
            assert s in reused

    def test_empirical_validation_per_book(self):
        ev = self._blk()["empirical_validation"]
        assert ev["mq1"]["renumbered_verse_count"] == 352 and ev["mq1"]["coverage_pct"] == 70.1
        assert ev["mq2"]["renumbered_verse_count"] == 188 and ev["mq2"]["coverage_pct"] == 73.4
        assert ev["mq3"]["renumbered_verse_count"] == 68 and ev["mq3"]["coverage_pct"] == 36.2

    def test_ocr_tier3_delta1x_replaceable(self):
        assert self._blk()["quality_tier"] == "ocr-tier3"
        assert self._blk()["delta1x_replaceable"] is True

    def test_no_ingest_false(self):
        assert self._blk()["no_ingest_at_this_phase"] is False

    def test_closed_arc_preserved(self):
        contracts = self._blk()["closed_arc_contracts_preserved"]
        for letter in "abcdefghijklm":
            assert contracts.get(f"tau7x{letter}_ingest") is True
        for letter in "abcdefghijklm":
            assert contracts.get(f"tau6x2{letter}_ingest") is True

    def test_next_phase_tau6x2o(self):
        assert self._blk()["next_phase"] == "τ.6.x.2.o"


# ─────────────────── cross-column coherence (tau7xn) ────────────────


class TestTau6X2NCrossColumnCoherence:
    def _tau7xn(self) -> dict:
        return _source_yaml()["ocr_strategy"]["tau7xn_ingest"]

    def test_tau7xn_geez_slot_state_updated(self):
        slot = self._tau7xn()["translation_slot_state"]["geez_tewahedo_mq123"]
        assert "shipped-at-τ.6.x.2.n" in slot
        assert "no-op" not in slot

    def test_tau7xn_geez_catchup_back_link(self):
        assert self._tau7xn().get("geez_catchup_reused_at_phase") == "τ.6.x.2.n"

    def test_tau7xn_pipeline_reused_at_phase_still_tau7xo(self):
        assert self._tau7xn()["pipeline_reused_at_phase"] == "τ.7.x.o"

    def test_pi1_page_image_slot_distinction_preserved(self):
        """The ocr-tier3 parallel-PDF Geʽez Mäqabyan is DISTINCT from
        the Π.1 page-image authoritative Geʽez Meqabyan track (δ.1.x).
        The slot note must still record that distinction."""
        slot = self._tau7xn()["translation_slot_state"]["geez_tewahedo_mq123"]
        assert "δ.1.x" in slot or "Π.1" in slot or "page-image" in slot


# ─────────────────────── geez _meta.yaml record ────────────────────


class TestTau6X2NGeezMetaYaml:
    def test_stats_books_at_least_sixteen(self):
        assert _geez_meta()["stats"]["books"] >= 16

    def test_stats_verses_at_least_8535(self):
        # 7927 (post-τ.6.x.2.m) + 352 + 188 + 68 = 8535.
        assert _geez_meta()["stats"]["verses"] >= 8535

    def test_stats_books_outside_kjv_at_least_seven(self):
        """2es+tob+jdt+est + mq1+mq2+mq3 = 7 Geʽez deuterocanon /
        Tewahedo-distinctive books outside the 66-book KJV canon."""
        assert _geez_meta()["stats"]["books_outside_kjv"] >= 7

    def test_ingest_record_tau6x2n(self):
        rec = _geez_meta()["ingest_record_tau6x2n"]
        assert rec["phase"] == "τ.6.x.2.n"
        assert rec["ingested_book_codes"] == ["mq1", "mq2", "mq3"]
        assert rec["engine"] == "text-layer"
        assert rec["multi_book"] is True
        assert rec["coverage"]["mq1"]["verses_extracted"] == 352
        assert rec["coverage"]["mq2"]["verses_extracted"] == 188
        assert rec["coverage"]["mq3"]["verses_extracted"] == 68
        assert rec["audit_handoff"] == "τ.6.x.3"

    def test_prior_geez_ingest_records_present(self):
        m = _geez_meta()
        for letter in "abcdefghijklm":
            assert f"ingest_record_tau6x2{letter}" in m, f"τ.6.x.2.{letter} record must persist"


# ─────────────────── prior-arc invariants preserved ────────────────


class TestTau6X2NPriorArcsPreserved:
    def test_amharic_mq_trilogy_preserved(self):
        for c in TRILOGY:
            assert (AMHARIC_TEWAHEDO / f"{c}.py").is_file()
            assert _constants(AMHARIC_TEWAHEDO, c).get("INGEST_PHASE") == "τ.7.x.n"

    def test_geez_deuterocanon_predecessors_preserved(self):
        for book, phase in (("2es", "τ.6.x.2.j"), ("tob", "τ.6.x.2.k"), ("jdt", "τ.6.x.2.l"), ("est", "τ.6.x.2.m")):
            assert _constants(GEEZ_TEWAHEDO, book).get("INGEST_PHASE") == phase

    def test_geez_8book_narrative_and_psalms_preserved(self):
        for book in ("gen", "ex", "lev", "num", "deu", "jos", "jdg", "rut"):
            assert (GEEZ_TEWAHEDO / f"{book}.py").is_file()
        assert _constants(GEEZ_TEWAHEDO, "psa").get("INGEST_PHASE") == "τ.6.x.2.i"

    def test_geez_mq_is_a_durable_deuterocanon_milestone(self):
        """ABSOLUTE/POSITIVE milestone-pin (memory
        `feedback_share_pin_pattern`) — positive/monotonic from the
        start (no forward not-yet-shipped enumeration). τ.6.x.2.n
        shipped the Geʽez Mäqabyan trilogy (the FIRST multi-book
        Geʽez catchup ship; the 5th/6th/7th Geʽez deuterocanon-block
        books); the count only grows."""
        for c in TRILOGY:
            assert (GEEZ_TEWAHEDO / f"{c}.py").is_file(), f"τ.6.x.2.n geez {c} must remain shipped"
        assert _geez_meta()["stats"]["books_outside_kjv"] >= 7, (
            "τ.6.x.2.n established ≥7 Geʽez deuterocanon books (monotonic)"
        )


# ───────────────────────────── state docs ──────────────────────────


class TestTau6X2NStateDocs:
    # Doc-pins collapsed to the CHANGELOG chokepoint (2026-05-21): the
    # old test_session_state_*/test_in_flight_*/test_plan_ledger_* pins
    # read SESSION_STATE.md / IN_FLIGHT.md (rolling, trimmed) and the
    # moved PLAN_2026-05-09.md. The durable phase record is CHANGELOG.md.
    def test_phase_recorded_in_changelog(self):
        from tests.fixtures import assert_phase_recorded

        assert_phase_recorded("τ.6.x.2.n")
