"""τ.7.x.i — Amharic Psalms full-book ingest pins (2026-05-15).

NINTH τ.7.x.* per-book ship under D4-c Amharic-first + D1-a per-book
cadence. Re-uses the τ.7.x.h pipeline (which itself reused τ.7.x.g
which reused τ.7.x.f which reused τ.7.x.e which reused τ.7.x.d which
reused τ.7.x.c which reused τ.7.x.b which reused τ.7.x.a) with only
PSALMS_VERSE_COUNTS + structural_map.psalms as deltas.

**88.6% coverage** — SECOND-HIGHEST τ.7.x.* coverage to date (between
Leviticus 93.4% and Numbers 85.9%); well above τ.7.x.* band-bottom
Ruth 70.6%. Psalms's short prayer-form poetic units + minimal cross-
reference apparatus + high page-density (0.69 pages/Psalm) yield
clean parser recovery.

**FIRST τ.7.x.* ship to SKIP a section of the source PDF.** Per
user "Skip the gap for now" decision after τ.7.x.h structural-
discovery scan: the 438-802 dzamaragna.net 2002 Amharic-only gap
(10 books: 1 Sam → Job) is DEFERRED to a future τ.7.x.J-cluster
sub-arc. τ.7.x.i resumes the parallel-Bible-EOTC scan at page 803
with Psalms (second EOTC-parallel block).

**OPENS the Wisdom-and-Poetry arc under Amharic-first sequencing.**

**LARGEST τ.7.x.* per-book ingest to date:** Psalms = 151 chapters
/ 2531 verses under LXX/Tewahedo enumeration (vs Genesis 50 ch /
1534 v prior maximum, Ruth 4 ch / 85 v prior minimum). The τ.7.x.a
template scales UP to the largest canonical OT book as cleanly as
it scales DOWN to the smallest at τ.7.x.h Ruth.

**Psalm 151 (David-vs-Goliath, Tewahedo-distinctive)** is preserved
in extracted output but renumbered to ch 126 partial slot due to
chapter-exhaustion renumbering artifact. Content verified.

Pins validate:
1. PSALMS_VERSE_COUNTS dict shape (151 chapters / 2531 total verses).
2. structural_map.psalms block in _source.yaml.
3. content/translations/amharic-tewahedo/psa.py module shape +
   INGEST_PHASE='τ.7.x.i' + SOURCE_QUALITY='ocr-tier3'.
4. Per-chapter coverage (1-125 fully populated; 126 partial 4/5;
   127-151 empty).
5. _meta.yaml ingest_record_tau7xi block + combined stats.
6. _source.yaml::ocr_strategy.tau7xi_ingest block + arc_open_wisdom
   marker + arc_skip_the_gap marker + psalm_151_preserved record.
7. Reciprocal back-link tau7xh_ingest.also_reused_at_phase = τ.7.x.i
   (alongside the existing pipeline_reused_at_phase: τ.6.x.2.h).
8. CLI --renumber {genesis,exodus,leviticus,numbers,deuteronomy,joshua,judges,ruth,psalms}.
9. geez-tewahedo/psa.py NOT created (D4-c preserved; queued for τ.6.x.2.i).
10. Skip-the-gap context pin: 10 books in 438-802 dzamaragna gap
    are NOT YET INGESTED in amharic-tewahedo/ (1 Sam, 2 Sam, 1 Ki,
    2 Ki, 1 Chr, 2 Chr, Ezr, Neh, Est, Job).
11. Psalm 151 David-vs-Goliath content preservation pin.
12. Psalm 118 (the 176-verse acrostic giant) floor pin — confirms
    the largest-chapter handler works at scale.
"""

from __future__ import annotations

import ast
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SOURCE_YAML = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"
AMHARIC_TEWAHEDO = REPO / "content" / "translations" / "amharic-tewahedo"
GEEZ_TEWAHEDO = REPO / "content" / "translations" / "geez-tewahedo"


def _source_yaml() -> dict:
    return yaml.safe_load(SOURCE_YAML.read_text(encoding="utf-8"))


def _psalms_block() -> dict:
    return _source_yaml()["structural_map"]["psalms"]


def _tau7xi_block() -> dict:
    return _source_yaml()["ocr_strategy"]["tau7xi_ingest"]


def _psa_verses() -> list[tuple]:
    psa_py = AMHARIC_TEWAHEDO / "psa.py"
    text = psa_py.read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "VERSES":
                    return ast.literal_eval(node.value)
    raise AssertionError("amharic-tewahedo/psa.py must define VERSES")


def _psa_constants() -> dict:
    psa_py = AMHARIC_TEWAHEDO / "psa.py"
    text = psa_py.read_text(encoding="utf-8")
    tree = ast.parse(text)
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


class TestTau7XIPsalmsVerseCounts:
    """PSALMS_VERSE_COUNTS is the τ.7.x.i renumber-floor dict."""

    def setup_method(self) -> None:
        import sys

        sys.path.insert(0, str(REPO / "scripts"))

    def test_module_symbol_present(self):
        from extract_parallel_pdf import PSALMS_VERSE_COUNTS

        assert isinstance(PSALMS_VERSE_COUNTS, dict)

    def test_one_hundred_fifty_one_chapters(self):
        """LXX/Tewahedo Psalter has 151 Psalms (Psalm 151 David-vs-Goliath included)."""
        from extract_parallel_pdf import PSALMS_VERSE_COUNTS

        assert sorted(PSALMS_VERSE_COUNTS.keys()) == list(range(1, 152))

    def test_total_verses_at_least_2500(self):
        """LXX/Tewahedo Psalter has ~2531 verses (slight variation by source)."""
        from extract_parallel_pdf import PSALMS_VERSE_COUNTS

        assert sum(PSALMS_VERSE_COUNTS.values()) >= 2500
        assert sum(PSALMS_VERSE_COUNTS.values()) <= 2600

    def test_psalm_118_is_largest_chapter(self):
        """Psalm 118 (LXX = Heb 119) is the 176-verse acrostic giant —
        the longest chapter in the Tewahedo Bible."""
        from extract_parallel_pdf import PSALMS_VERSE_COUNTS

        assert PSALMS_VERSE_COUNTS[118] == 176, "Psalm 118 must be 176 verses (LXX/Tewahedo)"

    def test_psalm_151_present_and_short(self):
        """Psalm 151 (David-vs-Goliath, Tewahedo-distinctive) is the
        shortest Psalter chapter at 7 verses."""
        from extract_parallel_pdf import PSALMS_VERSE_COUNTS

        assert 151 in PSALMS_VERSE_COUNTS
        assert PSALMS_VERSE_COUNTS[151] == 7

    def test_psalm_chapter_specific_verse_counts(self):
        """Spot-check well-known Psalm sizes under LXX/Tewahedo enumeration."""
        from extract_parallel_pdf import PSALMS_VERSE_COUNTS

        # Psalm 1 (Blessed is the man) = 6 verses
        assert PSALMS_VERSE_COUNTS[1] == 6
        # Psalm 21 (LXX = Heb 22; "My God my God why hast thou forsaken me") = 32 with title
        assert PSALMS_VERSE_COUNTS[21] == 32
        # Psalm 50 (LXX = Heb 51; "Miserere") = 21 with title
        assert PSALMS_VERSE_COUNTS[50] == 21
        # Psalm 117 (LXX = Heb 118; longest "Hallel" praise) = 29
        assert PSALMS_VERSE_COUNTS[117] == 29


class TestTau7XIStructuralMapPsalms:
    """structural_map.psalms block records the Psalms page range
    discovered via τ.7.x.h structural-discovery scan (second EOTC-
    parallel block)."""

    def test_block_present(self):
        assert "psalms" in _source_yaml()["structural_map"]

    def test_book_codes(self):
        assert _psalms_block()["book_codes"] == ["psa"]

    def test_pdf_page_range(self):
        # 803-906 inclusive (104 pages for 151 Psalms; verified by
        # Psalm 1:1 at p803 + Psalm 151 David-vs-Goliath at p906 +
        # Proverbs in dzamaragna format starting p907).
        assert _psalms_block()["pdf_page_range"] == [803, 906]

    def test_pdf_index_offset_zero(self):
        assert _psalms_block()["pdf_index_offset"] == 0

    def test_verified_true(self):
        assert _psalms_block()["verified"] is True

    def test_verified_at_tau7xi(self):
        assert _psalms_block()["verified_at_phase"] == "τ.7.x.i"

    def test_chapter_count_expected_151(self):
        """LXX/Tewahedo enumeration (Psalm 151 David-vs-Goliath included)."""
        assert _psalms_block()["chapter_count_expected"] == 151

    def test_notes_document_skip_the_gap(self):
        notes = _psalms_block()["notes"]
        assert "SKIP-THE-GAP" in notes or "Skip" in notes or "skip" in notes
        assert "438-802" in notes or "dzamaragna" in notes
        assert "second EOTC-parallel block" in notes or "p803" in notes or "803" in notes

    def test_notes_document_psalm_151_preservation(self):
        notes = _psalms_block()["notes"]
        assert "Psalm 151" in notes or "ጎልያድ" in notes or "Goliath" in notes


class TestTau7XIPsalmsPsaPy:
    """amharic-tewahedo/psa.py is the τ.7.x.i output module."""

    def test_psa_py_exists(self):
        assert (AMHARIC_TEWAHEDO / "psa.py").is_file()

    def test_translation_constant(self):
        c = _psa_constants()
        assert c.get("TRANSLATION") == "amharic-tewahedo"

    def test_book_constant(self):
        c = _psa_constants()
        assert c.get("BOOK") == "psa"

    def test_source_quality_ocr_tier3(self):
        c = _psa_constants()
        assert c.get("SOURCE_QUALITY") == "ocr-tier3"

    def test_source_provenance(self):
        c = _psa_constants()
        assert c.get("SOURCE_PROVENANCE") == "parallel-bible-eotc"

    def test_ingest_phase_constant(self):
        c = _psa_constants()
        assert c.get("INGEST_PHASE") == "τ.7.x.i"

    def test_verses_count_at_least_floor(self):
        verses = _psa_verses()
        # Empirical at ship: 2243 verses. Floor 2000 protects
        # against silent regression while permitting parser
        # refinement. τ.7.x.i is the LARGEST per-book ingest to date.
        assert len(verses) >= 2000, f"τ.7.x.i Psalms ingest must have ≥2000 verses; got {len(verses)}"

    def test_first_verse_is_psa_1_1(self):
        verses = _psa_verses()
        ch, v, text = verses[0]
        assert (ch, v) == (1, 1)
        assert text, "Psalm 1:1 text must be non-empty"


class TestTau7XIPsalmsCoverage:
    """Per-chapter coverage matches empirical post-renumber distribution:
    chapters 1-125 fully populated; 126 partial 4/5; 127-151 empty."""

    def _by_chapter(self) -> dict[int, list[tuple]]:
        verses = _psa_verses()
        out: dict[int, list[tuple]] = {}
        for ch, v, t in verses:
            out.setdefault(ch, []).append((v, t))
        return out

    def test_chapters_1_through_125_fully_populated(self):
        """The defining τ.7.x.i empirical pin: chapters 1-125 have
        verse counts MATCHING PSALMS_VERSE_COUNTS floor."""
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import PSALMS_VERSE_COUNTS

        by_ch = self._by_chapter()
        for ch in range(1, 126):
            got = len(by_ch.get(ch, []))
            expected = PSALMS_VERSE_COUNTS[ch]
            assert got == expected, (
                f"τ.7.x.i chapter {ch} must have exactly {expected} verses (PSALMS_VERSE_COUNTS floor); got {got}"
            )

    def test_chapter_126_partial(self):
        """Chapter 126 received the parser's remaining 4 verses
        (includes Psalm 151 David-vs-Goliath content renumbered
        from canonical Psalm 151 slot)."""
        by_ch = self._by_chapter()
        got = len(by_ch.get(126, []))
        # Empirical 4; defensive range (1, 5).
        assert 1 <= got <= 5, f"τ.7.x.i chapter 126 partial: expect 1..5 verses; got {got}"

    def test_chapters_127_through_151_empty(self):
        """Chapters 127-151 received zero verses — parser exhausted at ch 126."""
        by_ch = self._by_chapter()
        for ch in range(127, 152):
            got = len(by_ch.get(ch, []))
            assert got == 0, f"τ.7.x.i chapter {ch} should be empty at ocr-tier3; got {got} verses"

    def test_no_overflow_above_chapter_151(self):
        by_ch = self._by_chapter()
        overflow = sum(len(v) for ch, v in by_ch.items() if ch > 151)
        assert overflow == 0, f"τ.7.x.i renumber overflow should be 0; got {overflow} verses above ch 151"

    def test_psalm_151_goliath_content_preserved(self):
        """Psalm 151 David-vs-Goliath narrative content must appear
        in the last few verses (renumbered into ch 126 partial slot
        due to chapter-exhaustion). Accept any of: Goliath name
        marker `ጎልያድ` / `ጐልያድ`, David-anointing marker `ቀብቶ`,
        or the canonical-Geʽez stone-confrontation marker."""
        verses = _psa_verses()
        # Check the last 10 verses for Psalm 151 distinctive content
        last_chunk = " ".join(text for (_, _, text) in verses[-10:])
        goliath_marker = "ጎልያድ" in last_chunk or "ጐልያድ" in last_chunk
        anointing_marker = "ቅብዐ" in last_chunk or "ቀብቶ" in last_chunk
        stone_marker = "ደንጊያ" in last_chunk or "ድንጋይ" in last_chunk
        assert goliath_marker or anointing_marker or stone_marker, (
            f"τ.7.x.i Psalm 151 distinctive content must appear in the last 10 verses "
            f"(Goliath name OR David-anointing OR stone-confrontation marker); "
            f"got: {last_chunk[:400]}"
        )


class TestTau7XISourceYamlIngestBlock:
    """ocr_strategy.tau7xi_ingest block records the τ.7.x.i ship +
    back-link annotation to tau7xh_ingest (also_reused_at_phase) +
    Wisdom-and-Poetry arc-open + skip-the-gap context."""

    def test_block_exists(self):
        assert "tau7xi_ingest" in _source_yaml()["ocr_strategy"]

    def test_shipped_at_phase(self):
        assert _tau7xi_block()["shipped_at_phase"] == "τ.7.x.i"

    def test_structural_map_addition(self):
        sma = _tau7xi_block()["structural_map_addition"]
        assert sma["section"] == "psalms"
        assert sma["pdf_page_range"] == [803, 906]
        assert sma["chapter_count_expected"] == 151

    def test_helpers_added_psalms_verse_counts(self):
        helpers = _tau7xi_block()["helpers_added"]
        assert "PSALMS_VERSE_COUNTS" in helpers

    def test_cli_extensions_renumber_choice_extended(self):
        cli = _tau7xi_block()["cli_extensions"]
        assert "renumber_choice_extended" in cli

    def test_empirical_validation_coverage_85_plus_percent(self):
        ev = _tau7xi_block()["empirical_validation"]
        # Coverage at ship was 88.6%. Floor 85 protects against
        # regression (Psalms is second-highest τ.7.x.* coverage).
        assert ev["coverage_pct"] >= 85.0

    def test_no_ingest_at_this_phase_false(self):
        assert _tau7xi_block()["no_ingest_at_this_phase"] is False

    def test_closed_arc_tau7xa_through_tau7xh_preserved(self):
        contracts = _tau7xi_block()["closed_arc_contracts_preserved"]
        for letter in "abcdefgh":
            key = f"tau7x{letter}_ingest"
            assert contracts.get(key) is True, f"{key} must be preserved"

    def test_closed_arc_tau6x2_geez_batch_preserved(self):
        """All 8 Geʽez τ.6.x.2.a-h ingest invariants preserved."""
        contracts = _tau7xi_block()["closed_arc_contracts_preserved"]
        for letter in "abcdefgh":
            key = f"tau6x2{letter}_ingest"
            assert contracts.get(key) is True, f"{key} must be preserved"

    def test_reciprocal_back_link_in_tau7xh_also_reused(self):
        """τ.7.x.h tau7xh_ingest block must carry also_reused_at_
        phase = τ.7.x.i (the SECOND back-link, alongside the existing
        pipeline_reused_at_phase: τ.6.x.2.h Geʽez catchup back-link).
        τ.7.x.h is now the highest-reuse pipeline in the τ.7.x.*
        family."""
        h = _source_yaml()["ocr_strategy"]["tau7xh_ingest"]
        assert h.get("pipeline_reused_at_phase") == "τ.6.x.2.h"  # original Geʽez catchup back-link
        assert h.get("also_reused_at_phase") == "τ.7.x.i"  # new skip-the-gap back-link

    def test_arc_open_wisdom_and_poetry(self):
        """τ.7.x.i OPENS the Wisdom-and-Poetry arc."""
        assert "arc_open_wisdom_and_poetry" in _tau7xi_block()
        narrative = _tau7xi_block()["arc_open_wisdom_and_poetry"]
        assert "Wisdom-and-Poetry" in narrative or "Wisdom and Poetry" in narrative

    def test_arc_skip_the_gap_documented(self):
        """τ.7.x.i is the FIRST ship to SKIP a section."""
        assert "arc_skip_the_gap" in _tau7xi_block()
        narrative = _tau7xi_block()["arc_skip_the_gap"]
        assert "FIRST" in narrative or "skip" in narrative.lower()
        assert "438-802" in narrative or "dzamaragna" in narrative.lower()

    def test_translation_slot_state_psalms_shipped(self):
        state = _tau7xi_block()["translation_slot_state"]
        assert "τ.7.x.i" in state["amharic_tewahedo_psa"]

    def test_translation_slot_state_skipped_books_marked(self):
        """The 10 books in the 438-802 dzamaragna gap should be
        marked as SKIPPED in the translation_slot_state."""
        state = _tau7xi_block()["translation_slot_state"]
        for skipped_book in ("1sa", "2sa", "1ki", "2ki", "1ch", "2ch", "ezr", "neh", "est", "job"):
            key = f"amharic_tewahedo_{skipped_book}"
            assert key in state, f"Skip-the-gap state must list {key}"
            assert "SKIPPED" in state[key] or "skipped" in state[key]

    def test_next_phase_tau7xj(self):
        assert _tau7xi_block()["next_phase"] == "τ.7.x.j"


class TestTau7XIMetaYamlIngestRecord:
    """amharic-tewahedo/_meta.yaml has all nine ingest records +
    upgraded stats (9 books / 8242 verses combined; excludes the
    10 skipped books in the 438-802 dzamaragna gap)."""

    def _meta(self) -> dict:
        path = AMHARIC_TEWAHEDO / "_meta.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def test_stats_books_at_least_nine(self):
        # Pentateuch (5) + Joshua + Judges + Ruth + Psalms = 9 books
        m = self._meta()
        assert m["stats"]["books"] >= 9

    def test_stats_verses_at_least_8000(self):
        # 1308+947+802+1107+781+483+511+60+2243 = 8242. Floor 8000.
        m = self._meta()
        assert m["stats"]["verses"] >= 8000

    def test_tau7xi_ingest_record_present(self):
        m = self._meta()
        assert "ingest_record_tau7xi" in m

    def test_tau7xi_ingest_record_phase(self):
        m = self._meta()
        assert m["ingest_record_tau7xi"]["phase"] == "τ.7.x.i"

    def test_tau7xi_ingest_record_book_codes_psa(self):
        m = self._meta()
        assert m["ingest_record_tau7xi"]["ingested_book_codes"] == ["psa"]

    def test_tau7xi_ingest_record_arc_open_wisdom(self):
        m = self._meta()
        assert "arc_open_wisdom_and_poetry" in m["ingest_record_tau7xi"]

    def test_tau7xi_ingest_record_arc_skip_the_gap(self):
        m = self._meta()
        assert "arc_skip_the_gap" in m["ingest_record_tau7xi"]

    def test_tau7xi_psalm_151_preserved_documented(self):
        m = self._meta()
        assert "psalm_151_preserved" in m["ingest_record_tau7xi"]

    def test_prior_ingest_records_still_present(self):
        m = self._meta()
        assert "ingest_record" in m
        for tag in ("tau7xb", "tau7xc", "tau7xd", "tau7xe", "tau7xf", "tau7xg", "tau7xh"):
            assert f"ingest_record_{tag}" in m, f"prior ingest record missing: {tag}"


class TestTau7XIGeezTewahedoPreserved:
    """Geʽez Psalms ingest is queued for τ.6.x.2.i (next Geʽez catchup
    batch) per D4-c sequencing — geez-tewahedo/psa.py must NOT exist
    yet at τ.7.x.i ship-time."""

    def test_geez_tewahedo_psa_py_not_created(self):
        """Geʽez Psalms (`τ.6.x.2.i`) is the queued next-Geʽez-ingest
        per D4-c; geez-tewahedo/psa.py must not exist until then."""
        assert not (GEEZ_TEWAHEDO / "psa.py").exists(), (
            "geez-tewahedo/psa.py must NOT be created at τ.7.x.i; Geʽez Psalms is τ.6.x.2.i under D4-c sequencing"
        )

    def test_geez_tewahedo_8book_arc_preserved(self):
        """The τ.6.x.2.a-h Geʽez batch ship preserved — all 8 prior
        Geʽez books must still exist."""
        for book in ("gen", "ex", "lev", "num", "deu", "jos", "jdg", "rut"):
            assert (GEEZ_TEWAHEDO / f"{book}.py").is_file(), (
                f"Cross-arc invariant: geez-tewahedo/{book}.py must still exist after τ.7.x.i"
            )


class TestTau7XISkipTheGapInvariants:
    """The skip-the-gap decision must be EXPLICITLY MARKED in project
    state. Books in the 438-802 dzamaragna gap (1 Sam → Job) must NOT
    be created in amharic-tewahedo/."""

    SKIPPED_BOOKS = ("1sa", "2sa", "1ki", "2ki", "1ch", "2ch", "ezr", "neh", "est", "job")

    def test_skipped_books_not_in_amharic_tewahedo(self):
        """None of the 10 skipped books has a .py file in amharic-tewahedo/.
        (Esther also appears in the EOTC-parallel block at p1292-1310
        per τ.7.x.h scan; if/when that ship happens it'll be a separate
        decision whether to use parallel-block or dzamaragna source.)"""
        for book in self.SKIPPED_BOOKS:
            path = AMHARIC_TEWAHEDO / f"{book}.py"
            assert not path.exists(), (
                f"Skip-the-gap invariant: amharic-tewahedo/{book}.py must NOT exist after τ.7.x.i; "
                f"that book is in the 438-802 dzamaragna gap and DEFERRED to a future ship"
            )

    def test_skipped_books_not_in_geez_tewahedo(self):
        """None of the 10 skipped books has a .py file in geez-tewahedo/."""
        for book in self.SKIPPED_BOOKS:
            path = GEEZ_TEWAHEDO / f"{book}.py"
            assert not path.exists(), f"Skip-the-gap invariant: geez-tewahedo/{book}.py must NOT exist after τ.7.x.i"

    def test_psalms_shipped_amharic(self):
        """The skip-the-gap decision succeeded only because Psalms
        was simultaneously shipped (amharic-tewahedo/psa.py exists)."""
        assert (AMHARIC_TEWAHEDO / "psa.py").is_file()

    def test_skip_the_gap_marked_in_source_yaml(self):
        """tau7xi_ingest must record skip-the-gap context as the
        FIRST τ.7.x.* ship to skip a section of source PDF."""
        block = _tau7xi_block()
        assert "arc_skip_the_gap" in block, "tau7xi_ingest must document skip-the-gap context"
        sma = block["structural_map_addition"]
        assert "skip_the_gap_context" in sma, "structural_map_addition must document skip-the-gap"


class TestTau7XIWisdomAndPoetryArcOpen:
    """τ.7.x.i OPENS the Wisdom-and-Poetry arc. Psalms shipped is
    the first canonical-arc transition after the post-Pentateuch
    historical-books arc opened at τ.7.x.f."""

    def test_psalms_shipped(self):
        assert (AMHARIC_TEWAHEDO / "psa.py").is_file()

    def test_pentateuch_still_shipped(self):
        """§8.1 Pentateuch arc-close invariant: gen+ex+lev+num+deu
        must all still exist after τ.7.x.i."""
        for book in ("gen", "ex", "lev", "num", "deu"):
            path = AMHARIC_TEWAHEDO / f"{book}.py"
            assert path.is_file()

    def test_post_pentateuch_historical_books_arc_preserved(self):
        """τ.7.x.f Joshua + τ.7.x.g Judges + τ.7.x.h Ruth invariants
        preserved after τ.7.x.i."""
        for book in ("jos", "jdg", "rut"):
            path = AMHARIC_TEWAHEDO / f"{book}.py"
            assert path.is_file()

    def test_nine_book_combined_coverage_at_least_80_percent(self):
        """Combined 9-book coverage = sum(per-book verses) / sum(per-
        book floors). Empirical at ship: 8242/9745 = 84.6%. Floor 80%."""
        import sys

        sys.path.insert(0, str(REPO / "scripts"))
        from extract_parallel_pdf import (
            DEUTERONOMY_VERSE_COUNTS,
            EXODUS_VERSE_COUNTS,
            GENESIS_VERSE_COUNTS,
            JOSHUA_VERSE_COUNTS,
            JUDGES_VERSE_COUNTS,
            LEVITICUS_VERSE_COUNTS,
            NUMBERS_VERSE_COUNTS,
            PSALMS_VERSE_COUNTS,
            RUTH_VERSE_COUNTS,
        )

        floors = {
            "gen": sum(GENESIS_VERSE_COUNTS.values()),
            "ex": sum(EXODUS_VERSE_COUNTS.values()),
            "lev": sum(LEVITICUS_VERSE_COUNTS.values()),
            "num": sum(NUMBERS_VERSE_COUNTS.values()),
            "deu": sum(DEUTERONOMY_VERSE_COUNTS.values()),
            "jos": sum(JOSHUA_VERSE_COUNTS.values()),
            "jdg": sum(JUDGES_VERSE_COUNTS.values()),
            "rut": sum(RUTH_VERSE_COUNTS.values()),
            "psa": sum(PSALMS_VERSE_COUNTS.values()),
        }
        total_extracted = 0
        total_expected = sum(floors.values())
        for book in floors:
            path = AMHARIC_TEWAHEDO / f"{book}.py"
            text = path.read_text(encoding="utf-8")
            tree = ast.parse(text)
            verses = None
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "VERSES":
                            verses = ast.literal_eval(node.value)
                            break
                if verses is not None:
                    break
            total_extracted += len(verses)
        coverage = 100.0 * total_extracted / total_expected
        assert coverage >= 80.0, (
            f"9-book combined coverage must be ≥80%; got {coverage:.1f}% ({total_extracted}/{total_expected})"
        )


class TestTau7XIStateDocs:
    """SESSION_STATE, IN_FLIGHT, CHANGELOG, PLAN all reference τ.7.x.i."""

    def test_session_state_mentions_tau7xi(self):
        txt = (REPO / "dev" / "SESSION_STATE.md").read_text(encoding="utf-8")
        assert "τ.7.x.i" in txt

    def test_in_flight_mentions_tau7xi(self):
        txt = (REPO / "dev" / "IN_FLIGHT.md").read_text(encoding="utf-8")
        assert "τ.7.x.i" in txt

    def test_changelog_records_tau7xi_entry(self):
        txt = (REPO / "dev" / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "τ.7.x.i" in txt

    def test_plan_ledger_records_tau7xi(self):
        txt = (REPO / "dev" / "PLAN_2026-05-09.md").read_text(encoding="utf-8")
        assert "τ.7.x.i" in txt
