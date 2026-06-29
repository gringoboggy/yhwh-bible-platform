"""Tests for dev/audit_note_ocr.py — the note OCR-noise candidate detector (device-QA
round-2 cluster H-c).

The detector flags scanned-page "furniture" that bled into note bodies during OCR
extraction — chiefly a running-header + page-number artifact (e.g. ``-- THE SEPTUAGINT.
61``). It is a CANDIDATE finder for source-verified corpus cleanup, not an auto-fixer.
Also pins that the one user-reported corrupted note (Genesis 1:1 manuscript-witness) is
cleaned.
"""

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("audit_note_ocr", REPO / "dev" / "audit_note_ocr.py")
ano = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ano)
sys.modules["audit_note_ocr"] = ano


class TestDetectNoteOcrNoise:
    def test_flags_running_header_page_number(self):
        body = "<strong>Witness.</strong> the best copy. -- THE SEPTUAGINT. 61 10-13 Ps. 106."
        assert ano.detect_note_ocr_noise(body) == ["-- THE SEPTUAGINT. 61"]

    def test_clean_prose_not_flagged(self):
        body = "<strong>Creation.</strong> In the beginning God created the heaven and the earth."
        assert ano.detect_note_ocr_noise(body) == []

    def test_allcaps_phrase_without_trailing_page_number_not_flagged(self):
        # an emphatic ALL-CAPS phrase with no dash + trailing page number is legitimate prose
        body = "The covenant name is the LORD GOD of Israel, blessed forever."
        assert ano.detect_note_ocr_noise(body) == []


class TestGenManuscriptWitnessNoteCleaned:
    def test_no_ocr_noise_in_gen_text_witness_note(self):
        import content.notes.gen as gen

        note = next(n for n in gen.NOTES if n[0] == 1 and n[1] == 1 and n[4] == "text-witness")
        body = note[7]
        assert "Eome" not in body
        assert "THE SEPTUAGINT. 61" not in body
        assert "in the Library at Rome" in body
        assert ano.detect_note_ocr_noise(body) == []


class TestCorpusFreeOfRunningHeaderNoise:
    """Class-level pin (fix-the-class): the same Kenyon Codex-Vaticanus passage was
    ingested at all three of its lacuna loci (gen 1:1, 2ki 2:5, psa 106:27), each carrying
    the '-- THE SEPTUAGINT. 61' page-furniture. After the H-c cleanup NO note in the corpus
    carries the flagged running-header/page-number OCR noise."""

    def test_full_corpus_scan_is_clean(self):
        assert ano.scan_notes_dir() == []
