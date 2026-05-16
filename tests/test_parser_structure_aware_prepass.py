"""Structure-aware parser pre-pass — characterization + fix tests
(τ.6.x.1.E-class pipeline fix).

Pins the two confirmed structural faults that make the OT-narrative-
tuned paragraph parser break on non-narrative scripture, plus the
renumber overflow-rejection safety gate:

  Fault 1 — the real Matthew-1 chapter marker `ምዕራፍ 8 !` is NOT
            recognized (the text-layer engine emits `!` for `።`,
            which is absent from CHAPTER_HEADER_RE_LENIENT's
            terminator class) → Mt 1-2 silently discarded as
            pre-marker noise.
  Fault 2 — NT Amharic `ክፍል N፡ ስለ …` pericope/section headers
            survive the `።`-split as spurious verses (long Ethiopic
            prose, not numeral-dominated → is_cross_ref_fragment
            misses them) → over-count.
  Fault 3 — renumber_against_floor SILENTLY dumps gross over-
            segmentation (Ge'ez colometric Psalter: 4551 frags vs
            ~2531 floor) into a synthetic ch_max+1 bucket, producing
            distorted scripture + a false "all chapters full"
            signal, in violation of the τ.6.x.0b honesty contract.

Written FIRST per systematic-debugging Phase 4 / TDD: against the
pre-fix parser these assert the DESIRED post-fix behavior and so
FAIL, pinning the bug. They pass once the three-part minimal fix
lands. Unifies the τ.7.x.v NT blocker with the τ.6.x.2.i Ge'ez-
Psalms over-segmentation (same bug class).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))


class TestChapterMarkerBangTerminator:
    """Fault 1 — `!`-terminated chapter marker recognition."""

    def _re(self):
        from scripts.extract_parallel_pdf import CHAPTER_HEADER_RE_LENIENT

        return CHAPTER_HEADER_RE_LENIENT

    def test_bang_terminated_marker_matches(self):
        # Real Matthew-1 marker in the text-layer is `ምዕራፍ 8 !`
        # (OCR emits `!` for `።`). Pre-fix: `!` not in [።፡፣=] → no
        # match → Mt 1-2 discarded as pre-marker noise.
        m = self._re().search("ምዕራፍ 8 !")
        assert m is not None, "Mt-1 `ምዕራፍ 8 !` must match (! is an OCR'd ።)"
        assert m.group(1) == "8"

    def test_pipe_terminated_marker_matches(self):
        # `|` is the other common text-layer OCR substitution for ።.
        m = self._re().search("ምዕራፍ ፫ |")
        assert m is not None
        assert m.group(1) == "፫"

    def test_existing_terminators_still_match(self):
        for marker, tok in (("ምዕራፍ ፪ ።", "፪"), ("ምፅራፍ ፱ =", "፱"), ("ምዕራፍ B ።", "B")):
            m = self._re().search(marker)
            assert m is not None and m.group(1) == tok, f"regression: {marker!r}"

    def test_plain_prose_still_does_not_match(self):
        # Widening the terminator class must NOT create false positives.
        assert self._re().search("በመጀመሪያ እግዚአብሔር ሰማይንና ምድርን ፈጠረ።") is None
        assert self._re().search("እግዚአብሔር ይባረክ ! አሜን።") is None


class TestPericopeHeaderNotAVerse:
    """Fault 2 — `ክፍል N፡` NT section headers are not scripture verses."""

    def _parse(self, text):
        from scripts.extract_parallel_pdf import parse_verses_from_text

        return parse_verses_from_text(text, paragraph_mode=True)

    def test_kifl_section_header_filtered(self):
        body = (
            "ምዕራፍ ፩ ።\n"
            "ይህ የኢየሱስ ክርስቶስ የትውልድ መጽሐፍ ነው የአብርሃም ልጅ የዳዊት ልጅ።\n"
            "ክፍል ፮፡ ስለ መጥምቁ ዮሐንስ።\n"
            "በዚያ ወራት መጥምቁ ዮሐንስ መጣ በይሁዳ ምድረ በዳ እየሰበከ።"
        )
        verses = self._parse(body)
        assert verses, "real verses must still parse"
        assert not any(t.lstrip().startswith("ክፍል") for (_, _, t) in verses), (
            f"`ክፍል …` pericope header must NOT become a verse; got {[t[:25] for *_, t in verses]}"
        )
        assert len(verses) == 2, f"expected the 2 real verses only; got {len(verses)}"

    def test_pericope_predicate(self):
        from scripts.extract_parallel_pdf import is_pericope_header

        assert is_pericope_header("ክፍል ፮፡ ስለ መጥምቁ ዮሐንስ") is True
        assert is_pericope_header("ክፍል ፩ ስለ ጥምቀት") is True
        # A real verse that merely contains the word "ክፍል" is NOT a header.
        assert is_pericope_header("ይህም ክፍል ለእግዚአብሔር የተቀደሰ ነው") is False
        assert is_pericope_header("በመጀመሪያው ቃል ነበረ") is False


class TestRenumberOverflowRejection:
    """Fault 3 — gross over-segmentation must be a hard, honest fail."""

    def _fn(self):
        from scripts.extract_parallel_pdf import renumber_against_floor

        return renumber_against_floor

    def test_gross_overflow_raises(self):
        # Ge'ez Psalms reproduces ~1.8x the floor. Pre-fix renumber
        # silently buckets the excess into a synthetic ch_max+1
        # (distorted scripture + false "all full" signal).
        floor = {c: 6 for c in range(1, 152)}  # shape only
        total = sum(floor.values())
        verses = [(1, i, f"fragment {i} body text long enough") for i in range(1, total * 2)]
        with pytest.raises((ValueError, SystemExit)):
            self._fn()(verses, floor)

    def test_clean_underfill_unaffected(self):
        # Every shipped τ.6.x.2.* / τ.7.x.* book is UNDER floor — that
        # path must be byte-identical (no raise, no synthetic chapter).
        floor = {1: 5, 2: 5, 3: 5}
        verses = [(9, 9, f"verse {i} body text") for i in range(8)]
        out = self._fn()(verses, floor)
        assert len(out) == 8
        assert max(c for c, _, _ in out) <= 3

    def test_trivial_residue_tolerated(self):
        # A handful of colophon fragments past the floor is normal
        # ocr-tier3 noise — must still bucket (NOT hard-fail).
        floor = {1: 5, 2: 5}
        verses = [(9, 9, f"v{i} body text") for i in range(13)]  # 10 floor + 3 residue
        out = self._fn()(verses, floor)
        assert len(out) == 13
        assert max(c for c, _, _ in out) == 3  # ch_max+1 residue bucket
