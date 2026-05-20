"""τ.6.x.5.a — Patrologia Orientalis ingest pipeline pins (2026-05-20).

Pins for ``scripts/extract_patrologia_pdf.py``, the new ingest pipeline
built per ``docs/superpowers/specs/2026-05-20-patrologia-ingest-design.md``.

The pipeline OCRs the bilingual Ge'ez/French Patrologia Orientalis
critical-edition PDFs (PO 2/9/13/23) into per-book Python modules at
``content/translations/geez-tewahedo/{job,est,ezr,neh,1ch,2ch}.py`` with
``SOURCE_QUALITY = "patrologia-printed-tier1"`` (higher than the
parallel-Bible-EOTC ``ocr-tier3``).

Under test:

1. **Module surface** — constants (OCR_DPI, GEEZ_LANG, FRA_LANG,
   ENGINE_*, TARGET_*, SOURCE_QUALITY, PO_SOURCES) are at module scope
   with the spec-authorized values.

2. **POSource registry** — the 6 known sources (job, est, ezr, neh,
   1ch, 2ch) are registered with the correct PO volume / fascicle /
   editor / year metadata per the design spec §1 source-inventory
   table.

3. **roman_to_int** — converts banner Roman numerals (I/II/.../XLII)
   to integers; rejects garbage.

4. **parse_banner_chapter** — extracts the chapter number from a PO
   French banner string like "LE LIVRE DE JOB, I, 6-12"; survives the
   OCR-mangled variants ("LE LIVRE-DE", "LE LINRE DE").

5. **_render_strip_to_png** — produces a PNG file when given a PDF
   page (mocked via pymupdf's Pixmap save).

6. **split_geez_body_into_fragments** — splits a Ge'ez-body OCR
   blob by ``።``, drops ASCII-only French-banner garbage that leaked
   into the strip, drops fragments < 10 chars, preserves the ``።``
   terminator on output.

7. **parse_patrologia_pages** — walks a list of per-page strip dicts,
   tracks the current chapter via banner OCR, accumulates verses
   sequentially per chapter.

8. **renumber_against_canonical** — wraps the parallel-PDF
   `renumber_against_floor` helper, sourcing the floor from
   ``scripts.core.canonical_verse_counts.canonical_book_shape``.

9. **CLI smoke** — ``--help`` returns 0; required-arg validation
   triggers SystemExit.

10. **write_book_module_patrologia** — writes a module with the
    expected SOURCE_QUALITY + SOURCE_PROVENANCE strings.

11. **normalize_verse_numerals reuse** — the parallel-PDF helper still
    works through the patrologia pipeline (regression check; we did not
    fork or shadow the function).
"""

from __future__ import annotations

import ast
import io
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


REPO = Path(__file__).resolve().parent.parent


# ──────────────────────────────────────────────────────────────────
# τ.6.x.5.a — module surface
# ──────────────────────────────────────────────────────────────────


class TestPatrologiaModuleSurface:
    """Constants + key callables are importable at module scope with
    the spec-authorized values."""

    def test_engine_default_is_tesseract(self):
        from scripts.extract_patrologia_pdf import ENGINE_DEFAULT, ENGINE_TESSERACT

        assert ENGINE_DEFAULT == ENGINE_TESSERACT == "tesseract"

    def test_engine_choices_includes_both(self):
        from scripts.extract_patrologia_pdf import (
            ENGINE_CHOICES,
            ENGINE_TESSERACT,
            ENGINE_TEXT_LAYER,
        )

        assert ENGINE_TESSERACT in ENGINE_CHOICES
        assert ENGINE_TEXT_LAYER in ENGINE_CHOICES

    def test_ocr_dpi_is_350(self):
        from scripts.extract_patrologia_pdf import OCR_DPI

        assert OCR_DPI == 350

    def test_geez_lang_is_script_ethiopic(self):
        from scripts.extract_patrologia_pdf import GEEZ_LANG

        assert GEEZ_LANG == "script/Ethiopic"

    def test_fra_lang_is_fra(self):
        from scripts.extract_patrologia_pdf import FRA_LANG

        assert FRA_LANG == "fra"

    def test_source_quality_is_patrologia_tier1(self):
        from scripts.extract_patrologia_pdf import SOURCE_QUALITY

        assert SOURCE_QUALITY == "patrologia-printed-tier1"

    def test_source_quality_is_registered_tier(self):
        """SOURCE_QUALITY must be a tier registered in
        ``scripts.core.provenance_tiers.TIERS`` so the lint check
        ``provenance_tier_known`` passes."""
        from scripts.core.provenance_tiers import is_known_tier
        from scripts.extract_patrologia_pdf import SOURCE_QUALITY

        assert is_known_tier(SOURCE_QUALITY), f"{SOURCE_QUALITY!r} must be registered in provenance_tiers.TIERS"

    def test_targets_present(self):
        from scripts.extract_patrologia_pdf import (
            TARGET_CHOICES,
            TARGET_FRA,
            TARGET_GEEZ,
        )

        assert TARGET_GEEZ == "geez"
        assert TARGET_FRA == "fra"
        assert TARGET_GEEZ in TARGET_CHOICES
        assert TARGET_FRA in TARGET_CHOICES

    def test_top_strip_fractions(self):
        from scripts.extract_patrologia_pdf import (
            BANNER_TOP_FRACTION,
            FRA_BOTTOM_FRACTION,
            GEEZ_TOP_FRACTION,
        )

        assert 0.4 < GEEZ_TOP_FRACTION < 0.9
        assert 0.1 < FRA_BOTTOM_FRACTION < 0.6
        assert 0.0 < BANNER_TOP_FRACTION < 0.2

    def test_public_callables_importable(self):
        from scripts.extract_patrologia_pdf import (
            build_argparser,
            extract_patrologia,
            parse_banner_chapter,
            parse_patrologia_pages,
            renumber_against_canonical,
            roman_to_int,
            split_geez_body_into_fragments,
            tesseract_extract_strips,
            write_book_module_patrologia,
        )

        for fn in (
            build_argparser,
            extract_patrologia,
            parse_banner_chapter,
            parse_patrologia_pages,
            renumber_against_canonical,
            roman_to_int,
            split_geez_body_into_fragments,
            tesseract_extract_strips,
            write_book_module_patrologia,
        ):
            assert callable(fn), f"{fn.__name__} must be callable"


# ──────────────────────────────────────────────────────────────────
# τ.6.x.5.a — POSource registry
# ──────────────────────────────────────────────────────────────────


class TestPOSourceRegistry:
    """``PO_SOURCES`` holds the 6 known sources from spec §1."""

    def test_six_sources_registered(self):
        from scripts.extract_patrologia_pdf import PO_SOURCES

        assert set(PO_SOURCES.keys()) == {"job", "est", "ezr", "neh", "1ch", "2ch"}

    def test_job_metadata(self):
        from scripts.extract_patrologia_pdf import PO_SOURCES

        src = PO_SOURCES["job"]
        assert src.volume == 2
        assert src.fascicle == 5
        assert src.editor == "Pereira"
        assert src.year == 1907

    def test_chronicles_editor_is_grebaut(self):
        """Per spec §1 + GAPS/SOURCES.md: Chronicles is the Grébaut
        fascicle, NOT Pereira. The other 3 PO sources are all
        Pereira."""
        from scripts.extract_patrologia_pdf import PO_SOURCES

        assert PO_SOURCES["1ch"].editor == "Grebaut"
        assert PO_SOURCES["2ch"].editor == "Grebaut"
        # Pereira fascicles:
        assert PO_SOURCES["job"].editor == "Pereira"
        assert PO_SOURCES["est"].editor == "Pereira"
        assert PO_SOURCES["ezr"].editor == "Pereira"
        assert PO_SOURCES["neh"].editor == "Pereira"

    def test_ezra_and_neh_share_volume(self):
        """PO 13 fasc 5 contains BOTH Ezra and Nehemiah per spec §1."""
        from scripts.extract_patrologia_pdf import PO_SOURCES

        assert PO_SOURCES["ezr"].volume == 13
        assert PO_SOURCES["ezr"].fascicle == 5
        assert PO_SOURCES["neh"].volume == 13
        assert PO_SOURCES["neh"].fascicle == 5

    def test_chronicles_share_volume(self):
        """PO 23 fasc 4 contains BOTH 1 and 2 Chronicles per spec §1."""
        from scripts.extract_patrologia_pdf import PO_SOURCES

        assert PO_SOURCES["1ch"].volume == 23
        assert PO_SOURCES["1ch"].fascicle == 4
        assert PO_SOURCES["2ch"].volume == 23
        assert PO_SOURCES["2ch"].fascicle == 4

    def test_provenance_string_shape(self):
        from scripts.extract_patrologia_pdf import PO_SOURCES

        prov = PO_SOURCES["job"].provenance
        assert "patrologia-orientalis" in prov
        assert "vol2" in prov
        assert "fasc5" in prov
        assert "pereira" in prov.lower()
        assert "1907" in prov

    def test_archive_url_is_archive_org(self):
        from scripts.extract_patrologia_pdf import PO_SOURCES

        for src in PO_SOURCES.values():
            assert src.archive_url.startswith("https://archive.org/"), (
                f"PO source {src.book!r} archive URL must be archive.org "
                f"(public domain attribution); got {src.archive_url!r}"
            )

    def test_job_default_page_range_calibrated(self):
        """Job's default page range was verified empirically at
        τ.6.x.5.a (OCR-probe of the PDF located Job content
        spanning roughly p584-697)."""
        from scripts.extract_patrologia_pdf import PO_SOURCES

        start, end = PO_SOURCES["job"].default_page_range
        assert start > 0, "Job default page range must be calibrated"
        assert end > start
        assert end - start > 50, (
            "Job spans ~110 pages of Ge'ez body; verify default page range is in the right ballpark"
        )


# ──────────────────────────────────────────────────────────────────
# τ.6.x.5.a — roman_to_int
# ──────────────────────────────────────────────────────────────────


class TestRomanToInt:
    """``roman_to_int`` converts Roman numeral strings to int."""

    @pytest.mark.parametrize(
        ("roman", "expected"),
        [
            ("I", 1),
            ("II", 2),
            ("III", 3),
            ("IV", 4),
            ("V", 5),
            ("VI", 6),
            ("IX", 9),
            ("X", 10),
            ("XL", 40),
            ("XLII", 42),
            ("L", 50),
            ("LXX", 70),
            ("XCIX", 99),
            ("C", 100),
        ],
    )
    def test_valid_romans(self, roman, expected):
        from scripts.extract_patrologia_pdf import roman_to_int

        assert roman_to_int(roman) == expected

    def test_lowercase_accepted(self):
        from scripts.extract_patrologia_pdf import roman_to_int

        assert roman_to_int("xlii") == 42

    def test_empty_returns_none(self):
        from scripts.extract_patrologia_pdf import roman_to_int

        assert roman_to_int("") is None

    def test_garbage_returns_none(self):
        from scripts.extract_patrologia_pdf import roman_to_int

        assert roman_to_int("hello") is None
        assert roman_to_int("12") is None


# ──────────────────────────────────────────────────────────────────
# τ.6.x.5.a — parse_banner_chapter
# ──────────────────────────────────────────────────────────────────


class TestParseBannerChapter:
    """``parse_banner_chapter`` extracts the chapter from a PO French
    banner string."""

    def test_clean_banner(self):
        from scripts.extract_patrologia_pdf import parse_banner_chapter

        assert parse_banner_chapter("LE LIVRE DE JOB, I, 6-12") == 1
        assert parse_banner_chapter("LE LIVRE DE JOB, II, 4-9") == 2
        assert parse_banner_chapter("LE LIVRE DE JOB, XLII, 1") == 42

    def test_banner_with_page_number_prefix(self):
        """The PO banner is preceded by a page number on each spread:
        '576 LE LIVRE DE JOB, I, 6-12.'"""
        from scripts.extract_patrologia_pdf import parse_banner_chapter

        assert parse_banner_chapter("576 LE LIVRE DE JOB, I, 6-12.") == 1
        assert parse_banner_chapter("[15] LE LIVRE DE JOB, XLII, 1") == 42

    def test_ocr_mangled_keyword(self):
        """OCR sometimes mangles ``LIVRE`` to ``LINRE`` or adds a
        hyphen. The looser fallback should still catch the chapter."""
        from scripts.extract_patrologia_pdf import parse_banner_chapter

        assert parse_banner_chapter("LE LINRE DE JOB, I, 6-12") == 1
        # 'LE LIVRE-DE JOB' is observed at PO Job p697.
        assert parse_banner_chapter("LE LIVRE-DE JOB, XLI, 17") == 41

    def test_no_match_returns_none(self):
        from scripts.extract_patrologia_pdf import parse_banner_chapter

        assert parse_banner_chapter("") is None
        assert parse_banner_chapter("random ascii text with no banner") is None
        # Ge'ez-only string (banner OCR ran on a French strip and
        # picked up nothing).
        assert parse_banner_chapter("ዘኢዮብ።") is None

    def test_apostrophe_form_esdras_esther(self):
        """τ.6.x.5.b/τ.6.x.5.c: the PO Esther + PO Ezra volumes print
        the banner as ``LE LIVRE D'ESTHER`` / ``LE LIVRE D'ESDRAS``
        (apostrophe contraction). The original regex was hardcoded for
        ``LE LIVRE DE <BOOK>`` (with space) and missed these forms — the
        Esther agent flagged it as a defensive-fix to land in
        τ.6.x.5.c."""
        from scripts.extract_patrologia_pdf import parse_banner_chapter

        assert parse_banner_chapter("LE LIVRE D'ESTHER, I, 1-5") == 1
        assert parse_banner_chapter("LE LIVRE D'ESDRAS, I, 1-3") == 1
        assert parse_banner_chapter("LE LIVRE D'ESDRAS, X, 7-44") == 10

    def test_accented_form_nehemie(self):
        """τ.6.x.5.c: defensive coverage of the hypothetical
        ``LE LIVRE DE NÉHÉMIE`` (accented É) banner. Python 3's ``\\w``
        is Unicode-aware by default but we explicitly enable
        ``re.UNICODE`` on the compiled regex to make this contract
        load-bearing. The actual PO 13 fasc 5 volume does NOT print this
        banner (see test_troisieme_livre_de_ezra), but other PO volumes
        or future ingest sources may."""
        from scripts.extract_patrologia_pdf import parse_banner_chapter

        assert parse_banner_chapter("LE LIVRE DE NÉHÉMIE, I, 1-2") == 1
        assert parse_banner_chapter("LE LIVRE DE NÉHÉMIE, V, 1-2") == 5
        assert parse_banner_chapter("LE LIVRE DE NÉHÉMIE, X, 30-39") == 10
        # Also tolerate the de-accented OCR variant (some scans render
        # NÉHÉMIE without the diacritic).
        assert parse_banner_chapter("LE LIVRE DE NEHEMIE, I, 1-2") == 1

    def test_troisieme_livre_de_ezra(self):
        """τ.6.x.5.c: the PO 13 fasc 5 volume prints its banner as
        ``TROISIÈME (LIVRE) DE 'EZRA`` (no "LE" leader; OCR sometimes
        parenthesizes LIVRE; apostrophe before EZRA). The original
        ``LE\\s+LIVRE\\s+DE\\s+\\w+`` regex couldn't match this. The
        τ.6.x.5.c fix extends the prefix to ``(?:LE\\s+|\\w+\\s+)?``
        and allows ``\\(?LIVRE\\)?`` for the parenthesized form.

        The PO 13 volume's chapter numbering runs I-XXIII (= canonical
        Ezra 10ch + canonical Nehemiah 13ch combined into the Ethiopian
        single-work 'Third Book of Ezra')."""
        from scripts.extract_patrologia_pdf import parse_banner_chapter

        assert parse_banner_chapter("TROISIÈME (LIVRE) DE 'EZRA, I, 5-11") == 1
        assert parse_banner_chapter("[13] TROISIÈME (LIVRE) DE 'EZRA, II, 1-14") == 2
        # Ezra→Nehemiah volume-boundary spread (canonical Ezra ch X →
        # canonical Nehemiah ch 1 = volume ch XI).
        assert parse_banner_chapter("686 TROISIÈME (LIVRE) DE 'EZRA, X, 34-44 — XI, 1-3") == 10
        assert parse_banner_chapter("[47] TROISIÈME (LIVRE) DE 'EZRA, XI, 4-9") == 11
        assert parse_banner_chapter("[89] = TROISIÈME (LIVRE) DE 'EZRA, XXII, 23-29") == 22
        # Smart-quote variant ‘EZRA (OCR sometimes emits it).
        assert parse_banner_chapter("[91] TROISIÈME (LIVRE) DE ‘EZRA, XXI, 39-44") == 21
        # OCR mangle: "TROISIEME" without accent.
        assert parse_banner_chapter("| 688 TROISIEME (LIVRE) DE 'EZRA, XI, 10-11 -— XII, 1-5.") == 11


# ──────────────────────────────────────────────────────────────────
# τ.6.x.5.a — split_geez_body_into_fragments
# ──────────────────────────────────────────────────────────────────


class TestSplitGeezBodyIntoFragments:
    """``split_geez_body_into_fragments`` parses Ge'ez OCR text into
    verse-candidate fragments."""

    def test_splits_by_ethiopic_full_stop(self):
        from scripts.extract_patrologia_pdf import split_geez_body_into_fragments

        text = "ወሀለ ፡ አሐኝ ፡ ብአሰ ፡ በብሔረ ፡ አውስጢድ ፡ ዘስሙ ፡ ኢዮብ ።ወውእቱ ፡ ብእሲ ፡ ራትዕ ።"
        result = split_geez_body_into_fragments(text)
        assert len(result) == 2
        assert all(frag.endswith("።") for frag in result)

    def test_drops_ascii_only_lines(self):
        """ASCII-only lines (French banner garbage that leaked into
        the Ge'ez strip OCR) are dropped, but Ge'ez fragments are
        preserved."""
        from scripts.extract_patrologia_pdf import split_geez_body_into_fragments

        text = "576 LE LIVRE DE JOB, I, 6-12.\nወሀለ ፡ አሐኝ ፡ ብአሰ ፡ በብሔረ ፡ አውስጢድ ።\nSome more english noise here\n"
        result = split_geez_body_into_fragments(text)
        # The French banner + English noise are dropped; one Ge'ez
        # fragment is kept.
        assert len(result) == 1
        assert "።" in result[0]
        assert "LIVRE" not in result[0]

    def test_drops_short_fragments(self):
        """Fragments shorter than 10 chars are likely OCR noise (orphan
        punctuation, lone numerals) and are dropped."""
        from scripts.extract_patrologia_pdf import split_geez_body_into_fragments

        # First and third fragments are tiny; only the middle long one
        # survives.
        text = "ይኤ።ወሀለ ፡ አሐኝ ፡ ብአሰ ፡ በብሔረ ፡ አውስጢድ ።ሀ።"
        result = split_geez_body_into_fragments(text)
        assert len(result) == 1
        assert "አውስጢድ" in result[0]

    def test_empty_input_returns_empty_list(self):
        from scripts.extract_patrologia_pdf import split_geez_body_into_fragments

        assert split_geez_body_into_fragments("") == []
        assert split_geez_body_into_fragments("   \n  \n") == []

    def test_pure_ascii_returns_empty_list(self):
        """A page strip with NO Ethiopic content (e.g. a blank page or
        the Table of Contents past the Job body) returns no fragments."""
        from scripts.extract_patrologia_pdf import split_geez_body_into_fragments

        assert split_geez_body_into_fragments("Hello world. Another line.") == []


# ──────────────────────────────────────────────────────────────────
# τ.6.x.5.a — parse_patrologia_pages
# ──────────────────────────────────────────────────────────────────


class TestParsePatrologiaPages:
    """``parse_patrologia_pages`` walks per-page strip dicts and
    accumulates verses chapter-by-chapter."""

    def test_single_page_single_chapter(self):
        from scripts.extract_patrologia_pdf import parse_patrologia_pages

        pages = [
            {
                "banner": "LE LIVRE DE JOB, I, 1-5",
                "geez": "ወሀለ ፡ አሐኝ ፡ ብአሰ ።ወውእቱ ፡ ብእሲ ፡ ራትዕ ።",
            }
        ]
        out = parse_patrologia_pages(pages)
        assert len(out) == 2
        assert all(c == 1 for (c, _, _) in out)
        # Verses numbered 1, 2 sequentially within ch 1.
        assert [v for (_, v, _) in out] == [1, 2]

    def test_chapter_transition_resets_verse_numbering(self):
        from scripts.extract_patrologia_pdf import parse_patrologia_pages

        pages = [
            {
                "banner": "LE LIVRE DE JOB, I, 1-2",
                "geez": "ወሀለ ፡ አሐኝ ፡ ብአሰ ።ወውእቱ ፡ ብእሲ ።",
            },
            {
                "banner": "LE LIVRE DE JOB, II, 1-2",
                "geez": "ወእምድሣረ ፡ ይእቲ ።ወመጽአ ፡ ሰይጣን ።",
            },
        ]
        out = parse_patrologia_pages(pages)
        # 2 verses in ch1 + 2 verses in ch2 = 4 total.
        assert len(out) == 4
        chapters = [c for (c, _, _) in out]
        assert chapters == [1, 1, 2, 2]
        # Each chapter restarts at verse 1.
        verses = [v for (_, v, _) in out]
        assert verses == [1, 2, 1, 2]

    def test_no_banner_defaults_to_chapter_one(self):
        """If the first page has no detectable banner, default to
        chapter 1 (better than dropping all verses pre-banner)."""
        from scripts.extract_patrologia_pdf import parse_patrologia_pages

        pages = [
            {
                "banner": "garbled ocr nothing matches",
                "geez": "ወሀለ ፡ አሐኝ ፡ ብአሰ ።ወውእቱ ፡ ብእሲ ።",
            },
        ]
        out = parse_patrologia_pages(pages)
        assert len(out) == 2
        assert all(c == 1 for (c, _, _) in out)

    def test_continuation_page_inherits_chapter(self):
        """A page whose banner doesn't match (mid-chapter spread)
        inherits the previous page's chapter."""
        from scripts.extract_patrologia_pdf import parse_patrologia_pages

        pages = [
            {
                "banner": "LE LIVRE DE JOB, II, 1-3",
                "geez": "ወእምድሣረ ፡ ይእቲ ።",
            },
            {
                "banner": "garbled",
                "geez": "ወወሰደ ፡ ሰይጣን ።ወመጽአ ፡ መልአክ ።",
            },
        ]
        out = parse_patrologia_pages(pages)
        # All verses on chapter 2 — second page inherits.
        assert all(c == 2 for (c, _, _) in out)
        # The verse counter continues from where the chapter started.
        verses = [v for (_, v, _) in out]
        assert verses == [1, 2, 3]


# ──────────────────────────────────────────────────────────────────
# τ.6.x.5.a — renumber_against_canonical
# ──────────────────────────────────────────────────────────────────


class TestRenumberAgainstCanonical:
    """``renumber_against_canonical`` wraps the parallel-PDF renumber
    helper, sourcing the per-chapter floor from the KJV skeleton."""

    def test_job_floor_uses_kjv_skeleton(self):
        """Job KJV skeleton is 42 chapters / 1070 verses.
        ``canonical_book_shape('job')[1]`` is 22 (KJV Job 1:1-22)."""
        from scripts.core.canonical_verse_counts import canonical_book_shape

        shape = canonical_book_shape("job")
        assert shape[1] == 22, "KJV Job 1 has 22 verses"
        assert shape[42] == 17, "KJV Job 42 has 17 verses"
        assert len(shape) == 42, "KJV Job has 42 chapters"

    def test_renumber_packs_verses_into_chapters(self):
        from scripts.extract_patrologia_pdf import renumber_against_canonical

        # 25 raw verses in source order, all labeled ch 1 by the parser.
        # KJV Job 1 has 22 verses, so 22 go into ch 1 and the rest spill
        # to ch 2.
        raw = [(1, i + 1, f"verse {i + 1} text padding") for i in range(25)]
        out = renumber_against_canonical(raw, "job")
        # ch 1 should get exactly 22 verses; remaining 3 spill to ch 2.
        ch_counts: dict[int, int] = {}
        for c, _, _ in out:
            ch_counts[c] = ch_counts.get(c, 0) + 1
        assert ch_counts[1] == 22, f"Job ch1 should fill to 22; got {ch_counts.get(1)}"
        # Remaining 3 sit in ch 2 (the next canonical bucket).
        assert ch_counts.get(2, 0) == 3

    def test_renumber_with_merge_handles_oversegmentation(self):
        """``renumber_against_canonical_with_merge`` proactively
        merges adjacent fragments when the raw OCR over-segments past
        the canonical total. Job has 1070 canonical verses; if we hand
        it 2500 fragments, it must redistribute + merge so the output
        fits exactly within the canonical chapter shape."""
        from scripts.core.canonical_verse_counts import canonical_total
        from scripts.extract_patrologia_pdf import (
            renumber_against_canonical_with_merge,
        )

        # 2500 raw fragments — well over Job's 1070 canonical total.
        raw = [(1, i + 1, f"frag{i}-text-padding-here") for i in range(2500)]
        out = renumber_against_canonical_with_merge(raw, "job")
        # Output count must be at most the canonical total (we may
        # produce slightly less if the proportional distribution rounds
        # some chapters down).
        assert len(out) <= canonical_total("job") + 1, (
            f"merged output must fit within canonical total; got {len(out)} vs floor {canonical_total('job')}"
        )
        # All chapters from 1 to 42 should be represented.
        chapters = {c for (c, _, _) in out}
        assert chapters == set(range(1, 43)), f"all 42 Job chapters must appear; got {sorted(chapters)}"
        # No chapter exceeds its canonical verse count.
        from scripts.core.canonical_verse_counts import canonical_count

        ch_counts: dict[int, int] = {}
        for c, _, _ in out:
            ch_counts[c] = ch_counts.get(c, 0) + 1
        for ch, n in ch_counts.items():
            assert n <= canonical_count("job", ch), (
                f"ch{ch} has {n} verses but canonical floor is {canonical_count('job', ch)}"
            )

    def test_renumber_with_merge_no_op_when_sparse(self):
        """When raw fragment count <= canonical total, the merge variant
        defers to plain ``renumber_against_canonical`` (no merge needed,
        sparse output is fine)."""
        from scripts.extract_patrologia_pdf import (
            renumber_against_canonical,
            renumber_against_canonical_with_merge,
        )

        raw = [(1, i + 1, f"sparse-verse-{i}-text") for i in range(40)]
        merge_out = renumber_against_canonical_with_merge(raw, "job")
        plain_out = renumber_against_canonical(raw, "job")
        assert merge_out == plain_out


# ──────────────────────────────────────────────────────────────────
# τ.6.x.5.a — CLI smoke
# ──────────────────────────────────────────────────────────────────


class TestCLISmoke:
    """CLI argument parser builds + accepts the documented flags."""

    def test_argparser_builds(self):
        from scripts.extract_patrologia_pdf import build_argparser

        p = build_argparser()
        assert p is not None

    def test_help_returns(self, capsys):
        """``--help`` should print and exit 0 (SystemExit(0))."""
        from scripts.extract_patrologia_pdf import build_argparser

        p = build_argparser()
        with pytest.raises(SystemExit) as excinfo:
            p.parse_args(["--help"])
        # argparse exits 0 on --help.
        assert excinfo.value.code == 0
        captured = capsys.readouterr()
        assert "--book" in captured.out
        assert "--pdf" in captured.out
        assert "--target" in captured.out
        assert "--engine" in captured.out

    def test_required_book_flag(self):
        from scripts.extract_patrologia_pdf import build_argparser

        p = build_argparser()
        with pytest.raises(SystemExit):
            p.parse_args(["--pdf", "fake.pdf"])  # missing --book

    def test_book_choices_restricted(self):
        from scripts.extract_patrologia_pdf import build_argparser

        p = build_argparser()
        # Valid book passes.
        args = p.parse_args(["--book", "job", "--pdf", "fake.pdf"])
        assert args.book == "job"
        # Invalid book rejected.
        with pytest.raises(SystemExit):
            p.parse_args(["--book", "genesis", "--pdf", "fake.pdf"])

    def test_target_choices(self):
        from scripts.extract_patrologia_pdf import build_argparser

        p = build_argparser()
        for tgt in ("geez", "fra"):
            args = p.parse_args(["--book", "job", "--pdf", "x.pdf", "--target", tgt])
            assert args.target == tgt
        with pytest.raises(SystemExit):
            p.parse_args(["--book", "job", "--pdf", "x.pdf", "--target", "amharic"])


# ──────────────────────────────────────────────────────────────────
# τ.6.x.5.a — _render_strip_to_png (uses mocked pymupdf page)
# ──────────────────────────────────────────────────────────────────


class TestRenderStripToPng:
    """``_render_strip_to_png`` rasterizes a horizontal strip of a PDF
    page to a PNG file."""

    def _fake_page(self):
        """Build a fake pymupdf page object that records pixmap calls."""
        import fitz

        page = MagicMock()
        page.rect = fitz.Rect(0, 0, 484, 747)
        recorder = {"saved": []}

        def fake_get_pixmap(matrix=None, clip=None):
            pix = MagicMock()
            pix.save = lambda path: recorder["saved"].append((path, clip))
            return pix

        page.get_pixmap = fake_get_pixmap
        return page, recorder

    def test_geez_strip_clips_top_middle(self, tmp_path):
        from scripts.extract_patrologia_pdf import _render_strip_to_png

        page, rec = self._fake_page()
        out = _render_strip_to_png(page, "geez", dpi=350, out_path=tmp_path / "geez.png")
        assert out == tmp_path / "geez.png"
        assert len(rec["saved"]) == 1
        _, clip = rec["saved"][0]
        # The Ge'ez strip should span roughly from the banner cutoff
        # down to ~60% of the page height.
        assert clip.y0 > 0  # below the banner
        assert clip.y1 < 747  # above the bottom

    def test_fra_strip_clips_bottom(self, tmp_path):
        from scripts.extract_patrologia_pdf import _render_strip_to_png

        page, rec = self._fake_page()
        _render_strip_to_png(page, "fra", dpi=350, out_path=tmp_path / "fra.png")
        _, clip = rec["saved"][0]
        # The French strip starts where Ge'ez ends and runs to the
        # bottom of the page.
        assert clip.y1 == 747
        assert clip.y0 > 300  # somewhere past the page midpoint

    def test_banner_strip_clips_top_thin(self, tmp_path):
        from scripts.extract_patrologia_pdf import _render_strip_to_png

        page, rec = self._fake_page()
        _render_strip_to_png(page, "banner", dpi=350, out_path=tmp_path / "banner.png")
        _, clip = rec["saved"][0]
        # The banner strip is a thin top slice.
        assert clip.y0 == 0
        assert clip.y1 < 100  # well within the top of the page

    def test_invalid_strip_raises(self, tmp_path):
        from scripts.extract_patrologia_pdf import _render_strip_to_png

        page, _ = self._fake_page()
        with pytest.raises(ValueError):
            _render_strip_to_png(page, "side", dpi=350, out_path=tmp_path / "x.png")


# ──────────────────────────────────────────────────────────────────
# τ.6.x.5.a — write_book_module_patrologia
# ──────────────────────────────────────────────────────────────────


class TestWriteBookModulePatrologia:
    """``write_book_module_patrologia`` writes a per-book Python module
    with the patrologia-printed-tier1 SOURCE_QUALITY + the PO citation
    in the docstring."""

    def test_writes_module_with_expected_constants(self, tmp_path, monkeypatch):
        """Mirror the existing geez-tewahedo/<book>.py convention."""
        from scripts import extract_patrologia_pdf as mod

        # Redirect TRANSLATIONS_DIR through monkeypatch so we don't
        # touch the real content/translations tree.
        monkeypatch.setattr(mod, "TRANSLATIONS_DIR", tmp_path)
        # The downstream writer (extract_parallel_pdf.write_book_module)
        # uses its own TRANSLATIONS_DIR, so monkeypatch that too.
        from scripts import extract_parallel_pdf as parallel_mod

        monkeypatch.setattr(parallel_mod, "TRANSLATIONS_DIR", tmp_path)

        verses = [
            (1, 1, "ወሀለ ፡ አሐኝ ፡ ብአሰ።"),
            (1, 2, "ወውእቱ ፡ ብእሲ ፡ ራትዕ።"),
        ]
        out_path = mod.write_book_module_patrologia(
            book="job",
            verses=verses,
            ingest_phase="τ.6.x.5.a",
            extraction_date="2026-05-20",
        )
        assert out_path.is_file()

        text = out_path.read_text(encoding="utf-8")
        # The writer uses ``repr()`` to serialize, so quotes may be
        # single or double; check for the assignment shape, not the
        # exact quote style.
        assert ("TRANSLATION = 'geez-tewahedo'" in text) or ('TRANSLATION = "geez-tewahedo"' in text)
        assert ("BOOK = 'job'" in text) or ('BOOK = "job"' in text)
        assert ("SOURCE_QUALITY = 'patrologia-printed-tier1'" in text) or (
            'SOURCE_QUALITY = "patrologia-printed-tier1"' in text
        )
        assert "patrologia-orientalis-vol2-fasc5" in text  # provenance
        assert "Pereira" in text or "pereira" in text
        assert "1907" in text
        assert "archive.org" in text
        # And VERSES must be a parseable Python list of tuples.
        tree = ast.parse(text)
        verses_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "VERSES":
                        verses_node = node.value
        assert verses_node is not None, "VERSES must be defined"
        parsed = ast.literal_eval(verses_node)
        assert parsed == verses

    def test_unknown_book_raises_systemexit(self, tmp_path, monkeypatch):
        from scripts import extract_patrologia_pdf as mod

        monkeypatch.setattr(mod, "TRANSLATIONS_DIR", tmp_path)
        with pytest.raises(SystemExit):
            mod.write_book_module_patrologia(book="genesis", verses=[])


# ──────────────────────────────────────────────────────────────────
# τ.6.x.5.a — normalize_verse_numerals reuse from extract_parallel_pdf
# ──────────────────────────────────────────────────────────────────


class TestNormalizeVerseNumeralsReuse:
    """Sanity-check that the parallel-PDF helper still works through
    the patrologia pipeline (regression check; we did not fork the
    function, we re-use it)."""

    def test_ethiopic_numeral_at_line_start(self):
        from scripts.extract_parallel_pdf import normalize_verse_numerals

        # `፪፤ ስመ ...` (verse 2: name ...) — Ethiopic numeral + punct.
        text = "፪፤ ስመ ሰብእ"
        result = normalize_verse_numerals(text)
        # The numeral should be replaced with `2:` so the Arabic-digit
        # parser keys off it.
        assert result.startswith("2:")

    def test_no_op_for_clean_arabic_digits(self):
        from scripts.extract_parallel_pdf import normalize_verse_numerals

        text = "1 በመጀመሪያ ቀን"
        assert normalize_verse_numerals(text) == text
