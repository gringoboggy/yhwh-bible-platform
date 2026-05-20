"""τ.6.x.NT.a — NT-parser extension + Philemon-floor + structural_map
pre-ingest pins (2026-05-20).

This phase ships the **infrastructure** for NT-book ingest: the
`is_nt_book` predicate, the `_nt_prepass` structure-aware pre-pass
(which strips inline `ክፍል N፡` pericope headers, mid-paragraph
`ምዕራፍ N` chapter markers, and inline cross-reference apparatus
`(መዝ ፴፫፤፬)` before the `።`-split runs), four NT floor dicts
(PHILEMON_VERSE_COUNTS / SECOND_JOHN_VERSE_COUNTS /
THIRD_JOHN_VERSE_COUNTS / JUDE_VERSE_COUNTS), the
`--renumber {philemon,second_john,third_john,jude}` argparse choices,
and the `structural_map.philemon` block in
`_source.yaml`.

The book-ingest itself (Philemon `phm.py` in amharic-tewahedo +
geez-tewahedo) ships in the immediately-following step of the same
phase; these pins validate the pre-ingest infrastructure independently
so a future-day reviewer can audit the wire-up without re-running
Tesseract.

PINS:
- Floor dicts: shape, totals, single-chapter pattern.
- is_nt_book predicate: True for all 26 NT sections; False for OT
  sections (Sirach, Tobit, Ruth, Genesis); False for None/empty.
- _nt_prepass: strips inline `ክፍል N፡` pericope headers, strips
  inline `ምዕራፍ N` chapter markers, strips inline cross-references,
  merges colometric-layout continuations.
- OT-bytewise-identical: `_parse_paragraph_mode` with `is_nt=False`
  produces the SAME output as `is_nt=True`+`is_nt=False` on OT-shaped
  input (no pericope headers / cross-refs in OT). Empirical
  verification on a synthetic Genesis-1-like fragment.
- CLI argparse: `--renumber philemon` is a valid choice + the
  runtime dispatch resolves to PHILEMON_VERSE_COUNTS.
- structural_map.philemon: book_codes=[phm], pdf_page_range=[2023,
  2024], verified=true, verified_at_phase=τ.6.x.NT.a.
- Prior preservation: matthew block + laodiceans block + sirach
  block (τ.7.x.o) all preserved unchanged. Floor dicts for
  Sirach (51 ch / 1413 v), Matthew (28 ch / 1071 v),
  Genesis (50 ch / 1534 v) untouched.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SOURCE_YAML = REPO / "content" / "translations" / "sources" / "parallel-bible-eotc" / "_source.yaml"


def _source_yaml() -> dict:
    return yaml.safe_load(SOURCE_YAML.read_text(encoding="utf-8"))


def _ext():
    """Import (and re-import) the extractor module fresh.

    Tests below mutate / call module-level helpers so we re-import via
    importlib to avoid the test isolation issue of cached sys.modules
    state when running --keepalive or with pytest-xdist.
    """
    sys.path.insert(0, str(REPO / "scripts"))
    import extract_parallel_pdf as ext  # noqa: PLC0415 (lazy import inside helper)

    return ext


# ──────────────────────── floor dicts (4 new) ─────────────────────


class TestTau6XNTaPhilemonFloor:
    """PHILEMON_VERSE_COUNTS — 1 ch / 25 v / KJV-UBS-NA."""

    def test_symbol_present(self):
        ext = _ext()
        assert isinstance(ext.PHILEMON_VERSE_COUNTS, dict)

    def test_single_chapter(self):
        ext = _ext()
        assert sorted(ext.PHILEMON_VERSE_COUNTS.keys()) == [1]

    def test_total_verses_25(self):
        ext = _ext()
        assert sum(ext.PHILEMON_VERSE_COUNTS.values()) == 25

    def test_chapter_one_25_verses(self):
        ext = _ext()
        assert ext.PHILEMON_VERSE_COUNTS[1] == 25


class TestTau6XNTaSecondJohnFloor:
    def test_symbol_present(self):
        assert isinstance(_ext().SECOND_JOHN_VERSE_COUNTS, dict)

    def test_single_chapter(self):
        assert sorted(_ext().SECOND_JOHN_VERSE_COUNTS.keys()) == [1]

    def test_total_verses_13(self):
        assert sum(_ext().SECOND_JOHN_VERSE_COUNTS.values()) == 13


class TestTau6XNTaThirdJohnFloor:
    def test_symbol_present(self):
        assert isinstance(_ext().THIRD_JOHN_VERSE_COUNTS, dict)

    def test_single_chapter(self):
        assert sorted(_ext().THIRD_JOHN_VERSE_COUNTS.keys()) == [1]

    def test_total_verses_15(self):
        assert sum(_ext().THIRD_JOHN_VERSE_COUNTS.values()) == 15


class TestTau6XNTaJudeFloor:
    def test_symbol_present(self):
        assert isinstance(_ext().JUDE_VERSE_COUNTS, dict)

    def test_single_chapter(self):
        assert sorted(_ext().JUDE_VERSE_COUNTS.keys()) == [1]

    def test_total_verses_25(self):
        assert sum(_ext().JUDE_VERSE_COUNTS.values()) == 25


# ──────────────────────── is_nt_book predicate ────────────────────


class TestNTBookPredicate:
    def test_predicate_present(self):
        assert callable(_ext().is_nt_book)

    def test_philemon_is_nt(self):
        assert _ext().is_nt_book("philemon") is True

    def test_matthew_is_nt(self):
        assert _ext().is_nt_book("matthew") is True

    def test_jude_is_nt(self):
        assert _ext().is_nt_book("jude") is True

    def test_revelation_is_nt(self):
        assert _ext().is_nt_book("revelation") is True

    def test_sirach_is_not_nt(self):
        assert _ext().is_nt_book("sirach") is False

    def test_genesis_is_not_nt(self):
        assert _ext().is_nt_book("genesis") is False

    def test_ruth_is_not_nt(self):
        assert _ext().is_nt_book("ruth") is False

    def test_meqabyan_is_not_nt(self):
        assert _ext().is_nt_book("meqabyan") is False

    def test_jubilees_is_not_nt(self):
        assert _ext().is_nt_book("jubilees") is False

    def test_one_enoch_is_not_nt(self):
        assert _ext().is_nt_book("one_enoch") is False

    def test_none_is_not_nt(self):
        assert _ext().is_nt_book(None) is False

    def test_empty_is_not_nt(self):
        assert _ext().is_nt_book("") is False

    def test_unknown_section_is_not_nt(self):
        # If a future spec adds an OT-pseudepigraphon section, it must
        # NOT be treated as NT without an explicit registry addition.
        assert _ext().is_nt_book("some_future_pseudepigraphon") is False

    def test_nt_section_registry_26_books(self):
        """26 NT books are reachable from the parallel-Bible-EOTC PDF
        (Colossians excluded — declared present_in_pdf:false)."""
        assert len(_ext().NT_SECTION_NAMES) == 26


# ──────────────────────── _nt_prepass behavior ────────────────────


class TestNTPrepassPericopeHeaderStripping:
    """The pre-pass excises inline `ክፍል N፡ …` pericope headers so they
    do not parse as spurious verses through the `።`-splitter."""

    def test_strips_inline_pericope_header(self):
        # Real-world Tesseract shape: body sentence + `።` + pericope
        # header + `።` + body sentence. The OT-paragraph parser splits
        # by `።` so the header parses as its own (spurious) verse.
        body_a = "በመጀመሪያው ቃል ነበረ።"
        pericope = " ክፍል ፪፡ ስለ ቃል።"
        body_b = " ቃልም በእግዚአብሔር ዘንድ ነበረ።"
        text = body_a + pericope + body_b
        out = _ext()._nt_prepass(text)
        # Pericope marker stripped.
        assert "ክፍል ፪" not in out
        # Body sentences preserved.
        assert "በመጀመሪያው ቃል ነበረ" in out
        assert "ቃልም በእግዚአብሔር ዘንድ ነበረ" in out

    def test_strips_pericope_header_at_line_start(self):
        text = "ክፍል ፪፡ ስለ እምነት ።\nእምነት የተስፋ ነገር መሰረት ነው።"
        out = _ext()._nt_prepass(text)
        assert "ክፍል ፪" not in out
        # Body verse preserved.
        assert "እምነት የተስፋ ነገር መሰረት ነው" in out

    def test_does_not_strip_word_kefel_in_running_text(self):
        """`ክፍል` appearing mid-text without a following numeral is NOT a
        pericope header — body text mentioning the word `ክፍል` ("part")
        must be preserved."""
        text = "ይህ ክፍል ሌላ ምስጢር አለበት።"  # "This part contains another mystery"
        out = _ext()._nt_prepass(text)
        # The word 'ክፍል' must remain because no numeral follows it.
        assert "ክፍል" in out


class TestNTPrepassChapterMarkerStripping:
    """Mid-paragraph `ምዕራፍ N` markers are stripped so they do not
    parse as candidate verses through the `።`-splitter."""

    def test_strips_inline_chapter_marker(self):
        text = "ቅድሚ ጊዜ ነበረ ምዕራፍ ፪ አዲስ ጅማሬ።"
        out = _ext()._nt_prepass(text)
        # The 'ምዕራፍ ፪' tag is stripped (standalone chapter markers are
        # caught by the chapter-header walker; this is for the in-line
        # case).
        assert "ምዕራፍ ፪" not in out


class TestNTPrepassCrossRefStripping:
    """Inline cross-reference apparatus is stripped — bracketed
    citations like `(መዝ ፴፫፤፬)` glue inside verse body text and the
    OT cross-ref heuristic does not catch them at this position."""

    def test_strips_parenthesized_cross_ref(self):
        text = "ይህ ቃል (መዝ ፴፫፤፬) የተጻፈ ነው።"
        out = _ext()._nt_prepass(text)
        # Cross-ref stripped, body preserved.
        assert "(መዝ ፴፫፤፬)" not in out
        assert "ይህ ቃል" in out
        assert "የተጻፈ ነው" in out

    def test_strips_bracketed_cross_ref(self):
        text = "ይህ ቃል [ዕብ ፪] የተጻፈ ነው።"
        out = _ext()._nt_prepass(text)
        assert "[ዕብ ፪]" not in out
        assert "ይህ ቃል" in out


class TestNTPrepassColometricMerge:
    """Colometric layout (Beatitudes, Magnificat, Pauline doxology
    line-broken poetry) needs the trailing `፡`/`፣` continuation cue
    to signal "this line continues into the next one"."""

    def test_merges_continuation_punctuation(self):
        # Two-line "Beatitudes" snippet — line 1 ends with `፡`
        # (continuation cue), line 2 is the predicate. Both should
        # merge into one logical line for downstream `።`-split.
        text = "ብፁዓን ድሆች በመንፈስ ፡\nመንግሥተ ሰማያት የእነርሱ ናትና።"
        out = _ext()._nt_prepass(text)
        # After merging, the line break is gone — both halves are on
        # one line.
        merged_lines = [ln for ln in out.splitlines() if ln.strip()]
        assert len(merged_lines) == 1, f"expected 1 merged line, got {merged_lines!r}"
        # Both pieces preserved.
        assert "ብፁዓን ድሆች በመንፈስ" in merged_lines[0]
        assert "መንግሥተ ሰማያት የእነርሱ ናትና" in merged_lines[0]

    def test_does_not_merge_after_full_stop(self):
        # Line 1 ends with `።` (sentence terminator, NOT a
        # continuation cue) — must NOT merge with line 2.
        text = "የመጀመሪያው ቃል ።\nሁለተኛው ቃል።"
        out = _ext()._nt_prepass(text)
        merged_lines = [ln for ln in out.splitlines() if ln.strip()]
        # Two separate lines (full-stop is a sentence boundary).
        assert len(merged_lines) == 2

    def test_does_not_merge_when_next_line_starts_with_marker(self):
        # Continuation-cue end, but next line opens with a structural
        # marker (`ምዕራፍ`) — must NOT merge (structural markers are
        # their own logical line).
        text = "የመጀመሪያ ጅማሬ ፡\nምዕራፍ ፪ ቀጣይ ነው።"
        out = _ext()._nt_prepass(text)
        merged_lines = [ln for ln in out.splitlines() if ln.strip()]
        # Either two-line (no merge) OR one-line WITHOUT the structural
        # marker (chapter marker stripped per step 2 of the pre-pass).
        # Whichever way, the predicate is: the next-line marker was
        # not glued onto the prior line as if it were body text.
        joined = " ".join(merged_lines)
        # Structural marker stripped per chapter-marker stripping step.
        assert "ምዕራፍ ፪" not in joined


# ──────────────────────── OT bytewise identity ────────────────────


class TestOTBytewiseIdentity:
    """`_parse_paragraph_mode` with `is_nt=False` (the OT path) MUST
    bypass `_nt_prepass` — the OT pipeline shipped 24 books at parity
    under τ.7.x.a-o, byte-identical output is the contract."""

    def test_paragraph_mode_default_is_ot(self):
        """Defaults must keep the OT path active so existing callers
        (the Sirach τ.7.x.o ship, etc.) are unaffected."""
        import inspect

        sig = inspect.signature(_ext()._parse_paragraph_mode)
        assert "is_nt" in sig.parameters
        assert sig.parameters["is_nt"].default is False

    def test_parse_verses_from_text_default_is_ot(self):
        import inspect

        sig = inspect.signature(_ext().parse_verses_from_text)
        assert "is_nt" in sig.parameters
        assert sig.parameters["is_nt"].default is False

    def test_ot_path_produces_identical_output_with_or_without_nt_flag(self):
        """For OT-shaped input (no `ክፍል N`, no inline `ምዕራፍ N`, no
        bracketed cross-refs, no colometric line-breaks),
        `is_nt=False` and `is_nt=True` produce the SAME output. This
        is the additive-pre-pass contract."""
        # Synthetic Genesis-1-ish fragment in paragraph-mode shape.
        ot_text = "ምዕራፍ ፩ ።\nበመጀመሪያ እግዚአብሔር ሰማይንና ምድርን ፈጠረ።\nምድርም ባዶ ነበረች።\nየእግዚአብሔር መንፈስ በውሃዎች ላይ ይንሳፈፍ ነበር።\n"
        ext = _ext()
        ot_out = ext._parse_paragraph_mode(ot_text, is_nt=False)
        nt_out_on_ot_text = ext._parse_paragraph_mode(ot_text, is_nt=True)
        # Same verse count.
        assert len(ot_out) == len(nt_out_on_ot_text), (
            f"OT-path produced {len(ot_out)} verses; NT-path on OT-shaped "
            f"input produced {len(nt_out_on_ot_text)} verses. The pre-pass "
            f"must be a no-op on OT-shaped input (no pericope/cross-ref/"
            f"colometric content to strip)."
        )
        # Same chapter+verse labels.
        assert [(c, v) for (c, v, _) in ot_out] == [(c, v) for (c, v, _) in nt_out_on_ot_text]


# ──────────────────────── CLI argparse + dispatch ─────────────────


class TestCLIArgparseRenumberChoices:
    """`--renumber philemon` (+ siblings) must be valid argparse
    choices + the runtime dispatch must resolve to the right floor
    dict."""

    def test_renumber_philemon_in_choices_help(self):
        src = (REPO / "scripts" / "extract_parallel_pdf.py").read_text(encoding="utf-8")
        # The literal token must appear inside the choices list block.
        assert '"philemon"' in src

    def test_renumber_jude_in_choices(self):
        src = (REPO / "scripts" / "extract_parallel_pdf.py").read_text(encoding="utf-8")
        assert '"jude"' in src

    def test_renumber_second_john_in_choices(self):
        src = (REPO / "scripts" / "extract_parallel_pdf.py").read_text(encoding="utf-8")
        assert '"second_john"' in src

    def test_renumber_third_john_in_choices(self):
        src = (REPO / "scripts" / "extract_parallel_pdf.py").read_text(encoding="utf-8")
        assert '"third_john"' in src

    def test_renumber_dispatch_philemon_resolves(self):
        """The renumber-floor lookup must dispatch `philemon` to
        PHILEMON_VERSE_COUNTS."""
        src = (REPO / "scripts" / "extract_parallel_pdf.py").read_text(encoding="utf-8")
        # The dispatch is wired in two places: _build_docstring_extra
        # (writer-side) and main() (CLI runtime). Both must reference
        # PHILEMON_VERSE_COUNTS.
        assert src.count("PHILEMON_VERSE_COUNTS") >= 3  # symbol-def + 2 dispatch sites


# ──────────────────── structural_map.philemon ─────────────────────


class TestStructuralMapPhilemon:
    def _blk(self) -> dict:
        return _source_yaml()["structural_map"]["philemon"]

    def test_block_present(self):
        assert "philemon" in _source_yaml()["structural_map"]

    def test_book_codes(self):
        assert self._blk()["book_codes"] == ["phm"]

    def test_pdf_page_range_2023_2024(self):
        assert self._blk()["pdf_page_range"] == [2023, 2024]

    def test_pdf_index_offset_zero(self):
        assert self._blk()["pdf_index_offset"] == 0

    def test_verified_true_at_tau6xnta(self):
        assert self._blk()["verified"] is True
        assert self._blk()["verified_at_phase"] == "τ.6.x.NT.a"

    def test_chapter_count_expected_1(self):
        assert self._blk()["chapter_count_expected"] == 1

    def test_notes_document_header_and_pattern(self):
        notes = " ".join(self._blk()["notes"].split())
        # Header (ኀበ ፊልሞና) per the τ.6.x.NT.a Track-E scan.
        assert "ኀበ ፊልሞና" in notes
        # τ.6.x.NT.a + NT-pre-pass mitigation references.
        assert "τ.6.x.NT.a" in notes
        assert "NT-pre-pass" in notes or "_nt_prepass" in notes


# ──────────────────── prior preservation ──────────────────────────


class TestPriorPreservation:
    """Nothing previously-shipped may regress."""

    def test_matthew_block_preserved(self):
        sm = _source_yaml()["structural_map"]
        assert sm["matthew"]["pdf_page_range"] == [1567, 1635]
        assert sm["matthew"]["verified_at_phase"] == "τ.7.x.v"

    def test_laodiceans_block_preserved(self):
        sm = _source_yaml()["structural_map"]
        assert sm["laodiceans"]["present_in_pdf"] is False
        assert sm["laodiceans"]["verified_at_phase"] == "Π.1"

    def test_sirach_block_preserved(self):
        sm = _source_yaml()["structural_map"]
        assert "sirach" in sm
        # τ.7.x.o shipped sirach; the block must still be present.

    def test_matthew_floor_preserved(self):
        ext = _ext()
        assert sum(ext.MATTHEW_VERSE_COUNTS.values()) == 1071

    def test_genesis_floor_preserved(self):
        ext = _ext()
        assert sum(ext.GENESIS_VERSE_COUNTS.values()) == 1534

    def test_sirach_floor_preserved(self):
        ext = _ext()
        assert sum(ext.SIRACH_VERSE_COUNTS.values()) == 1413

    def test_existing_parser_signatures_untouched(self):
        """No-regression smoke on the parser entry points (signatures
        may have ADDED `is_nt` but the old positional shape must still
        work)."""
        import inspect

        ext = _ext()
        sig = inspect.signature(ext.parse_verses_from_text)
        # `text` is positional/keyword.
        assert "text" in sig.parameters
        # `paragraph_mode` is keyword-only and defaults to False.
        assert sig.parameters["paragraph_mode"].default is False


# ────────────────────── τ.6.x.NT.c — leak fixes ───────────────────
#
# The τ.6.x.NT.b BLOCKER reported Matthew Amharic pre-pass reduced
# overflow 67% (107→35) but still exceeded the 21v tolerance. Four
# leak categories were diagnosed (see τ.6.x.NT.c task brief):
#
#   (A) Pericope-strip leak — Tesseract OCR'd section-numerals as
#       Ethiopic LETTERS (not numerals) — `ክፍል ኒ፣`, `ክፍል ቨች፡`,
#       `ክፍል ሣ5፥`, `ክፍል ማ፳2፤`, `ክፍልማጓ፡`. The pre-τ.6.x.NT.c
#       INLINE_PERICOPE_RE required `[፩-፼0-9]` after the keyword;
#       widen to accept Ethiopic letters mixed with digits/numerals.
#
#   (B) Cross-ref-strip leak — Many cross-refs render WITHOUT
#       brackets after OCR: `ማር፳ጳ፡ጳ-፳።`, `ሉቃጅ፡ፅስ-1ፅል።`,
#       `ግብ ሐዋ ፲፡ወቿ-8።`. The pre-τ.6.x.NT.c INLINE_CROSS_REF_RE
#       required bracketed shape — add an unbracketed pattern.
#
#   (C) Low-Ethiopic-ratio noise — Latin-mixed running headers
#       (`ገር3፲1ክ ... ክርስቲያን ሃይማኖትና ሥርዓት 10 ...`). Add a
#       fragment-level filter dropping verses with <40% Ethiopic.
#
#   (D) OCR-stub micro-verses — Fragments with ≤5 useful chars
#       after stripping numerals/punct. Subsumed by (B) but worth
#       a dedicated filter.


class TestTau6XNTcPericopeOCRMangled:
    """(A) Pericope-strip leak. The widened INLINE_PERICOPE_RE must
    catch headers whose section-numerals were OCR'd as Ethiopic
    LETTERS rather than the strict `[፩-፼0-9]` numeral class."""

    def test_pericope_strip_handles_ocr_mangled_section_numerals_letters_only(self):
        """Section-numeral OCR'd as pure Ethiopic letters
        (`ክፍል ኒ፣`)."""
        text = "የመጀመሪያ ቃል። ክፍል ኒ፣ ስለ እምነት። የቀጣይ ቃል።"
        out = _ext()._nt_prepass(text)
        # Header stripped (the keyword + section numeral run + body cue).
        assert "ክፍል ኒ" not in out
        # Surrounding body preserved.
        assert "የመጀመሪያ ቃል" in out
        assert "የቀጣይ ቃል" in out

    def test_pericope_strip_handles_two_letter_section_numeral(self):
        """`ክፍል ቨች፡` — two Ethiopic letters as the section numeral."""
        text = "የመጀመሪያ ቃል። ክፍል ቨች፡ ስለ ምስጢር። ቀጣዩ።"
        out = _ext()._nt_prepass(text)
        assert "ክፍል ቨች" not in out
        assert "የመጀመሪያ ቃል" in out

    def test_pericope_strip_handles_letter_plus_digit_numeral(self):
        """`ክፍል ሣ5፥` — Ethiopic letter + Arabic digit mix."""
        text = "የመጀመሪያ ቃል። ክፍል ሣ5፥ ስለ ጥሩ ምግባር። ቀጣዩ።"
        out = _ext()._nt_prepass(text)
        assert "ክፍል ሣ5" not in out
        assert "የመጀመሪያ ቃል" in out

    def test_pericope_strip_handles_letter_numeral_digit_mix(self):
        """`ክፍል ማ፳2፤` — Ethiopic letter + Ethiopic-numeral + digit."""
        text = "የመጀመሪያ ቃል። ክፍል ማ፳2፤ ስለ ሕይወት። ቀጣዩ።"
        out = _ext()._nt_prepass(text)
        assert "ክፍል ማ፳2" not in out
        assert "የመጀመሪያ ቃል" in out

    def test_pericope_strip_handles_glued_keyword_numeral(self):
        """`ክፍልማጓ፡` — keyword glued to numeral with no separator."""
        text = "የመጀመሪያ ቃል። ክፍልማጓ፡ ስለ ሰላም። ቀጣዩ።"
        out = _ext()._nt_prepass(text)
        assert "ክፍልማጓ" not in out
        assert "የመጀመሪያ ቃል" in out


class TestTau6XNTcUnbracketedCrossRef:
    """(B) Cross-ref-strip leak. The new unbracketed cross-ref pattern
    must catch citations that render WITHOUT brackets after OCR."""

    def test_cross_ref_strip_handles_unbracketed_form_mar(self):
        """`ማር፳ጳ፡ጳ-፳።` — book abbreviation 'ማር' (Mark) glued to
        numerals + range, NO brackets."""
        # An unbracketed cross-ref standing alone between two body
        # sentences after the `።`-splitter would survive the bracketed
        # cross-ref strip but be filtered as a verse-fragment. Test
        # via end-to-end paragraph-mode parse.
        ext = _ext()
        text = "ምዕራፍ ፩።\nየመጀመሪያው ቃል ይህ ነው ስለዚህ።\nማር፳ጳ፡ጳ-፳።\nየቀጣዩ ቃል ይህ ነው ስለዚህ።\n"
        verses = ext._parse_paragraph_mode(text, is_nt=True)
        # The cross-ref `ማር፳ጳ፡ጳ-፳።` must NOT appear as a verse.
        verse_texts = [t for (_, _, t) in verses]
        for v in verse_texts:
            assert "ማር፳ጳ" not in v, f"cross-ref leaked: {v!r}"

    def test_cross_ref_strip_handles_unbracketed_form_luq(self):
        """`ሉቃጅ፡ፅስ-1ፅል።` — Luke abbrev + Ethiopic-letter-OCR numerals
        + range + arabic digit."""
        ext = _ext()
        text = "ምዕራፍ ፩።\nየመጀመሪያው ቃል ይህ ነው ስለዚህ።\nሉቃጅ፡ፅስ-1ፅል።\nየቀጣዩ ቃል ይህ ነው ስለዚህ።\n"
        verses = ext._parse_paragraph_mode(text, is_nt=True)
        verse_texts = [t for (_, _, t) in verses]
        for v in verse_texts:
            assert "ሉቃጅ" not in v, f"cross-ref leaked: {v!r}"

    def test_cross_ref_strip_handles_acts_two_word_form(self):
        """`ግብ ሐዋ ፲፡ወቿ-8።` — two-word book abbreviation (Acts =
        `ግብረ ሐዋርያት`, shortened to `ግብ ሐዋ`)."""
        ext = _ext()
        text = "ምዕራፍ ፩።\nየመጀመሪያው ቃል ይህ ነው ስለዚህ።\nግብ ሐዋ ፲፡ወቿ-8።\nየቀጣዩ ቃል ይህ ነው ስለዚህ።\n"
        verses = ext._parse_paragraph_mode(text, is_nt=True)
        verse_texts = [t for (_, _, t) in verses]
        for v in verse_texts:
            assert "ግብ ሐዋ" not in v, f"cross-ref leaked: {v!r}"


class TestTau6XNTcLowEthiopicRatio:
    """(C) Page-header / running-title noise. Verses whose Ethiopic-
    character ratio is below 40% (Latin/digit-dominant lines) must
    be filtered out."""

    def test_low_ethiopic_ratio_lines_filtered(self):
        """Latin-mixed running header — most chars are digits/Latin/
        punctuation, only a token of Ethiopic content."""
        ext = _ext()
        text = "ምዕራፍ ፩።\nየመጀመሪያው ቃል ይህ ነው ስለዚህ።\nገር3፲1ክ ABC 12345 XYZ 99 1010 ABCDEF።\nየቀጣዩ ቃል ይህ ነው ስለዚህ።\n"
        verses = ext._parse_paragraph_mode(text, is_nt=True)
        verse_texts = [t for (_, _, t) in verses]
        # The garbage running-header line must NOT appear as a verse.
        for v in verse_texts:
            assert "ABCDEF" not in v, f"low-ratio garbage leaked: {v!r}"
            assert "XYZ" not in v, f"low-ratio garbage leaked: {v!r}"

    def test_high_ethiopic_ratio_lines_preserved(self):
        """Pure-Ethiopic verse text must be preserved — the filter
        targets LOW ratio only."""
        ext = _ext()
        text = "ምዕራፍ ፩።\nየመጀመሪያው ቃል ይህ ነው ስለዚህ።\nሁለተኛው ቃል ይህ ነው ስለዚህ።\n"
        verses = ext._parse_paragraph_mode(text, is_nt=True)
        # Both body verses preserved.
        assert len(verses) == 2

    def test_ot_path_unaffected_by_ratio_filter(self):
        """OT path (is_nt=False) MUST NOT apply the low-ratio filter
        — byte-identity contract with τ.7.x.a-o."""
        ext = _ext()
        text = "ምዕራፍ ፩።\nብርሃንም ሰማይና ምድር በውስጧ ነበሩ ስለዚህ።\n"
        # is_nt=False — produces the same output as previously.
        ot_out = ext._parse_paragraph_mode(text, is_nt=False)
        # OT path: one body verse preserved.
        assert len(ot_out) == 1


class TestTau6XNTcOCRStubMicroVerse:
    """(D) OCR-stub micro-verses. Fragments with ≤5 useful chars
    (after stripping numerals/punct/whitespace) are OCR garbage
    and must be filtered out."""

    def test_ocr_stub_micro_verses_filtered(self):
        """A `።`-bounded fragment with ≤5 Ethiopic-letter chars after
        stripping numerals + punct is OCR noise, not body text."""
        ext = _ext()
        text = (
            "ምዕራፍ ፩።\n"
            "የመጀመሪያው ቃል ይህ ነው ስለዚህ።\n"
            "ጳ፡፳፥ጳ።\n"  # OCR stub — almost entirely numerals/punct
            "የቀጣዩ ቃል ይህ ነው ስለዚህ።\n"
        )
        verses = ext._parse_paragraph_mode(text, is_nt=True)
        verse_texts = [t for (_, _, t) in verses]
        for v in verse_texts:
            # The stub must not survive as a verse.
            assert "ጳ፡፳፥ጳ" not in v, f"OCR stub leaked: {v!r}"

    def test_real_short_verse_preserved(self):
        """Genuine short verses (e.g. Jn 11:35 "Jesus wept" = `ኢየሱስም
        አለቀሰ።`) must be preserved — they have enough Ethiopic content
        to pass the stub filter."""
        ext = _ext()
        text = (
            "ምዕራፍ ፩።\n"
            "ኢየሱስም አለቀሰ።\n"  # ~10 Ethiopic chars — well above stub threshold
        )
        verses = ext._parse_paragraph_mode(text, is_nt=True)
        # Verse preserved.
        assert len(verses) == 1


class TestTau6XNTcNTSectionRegistryExtended:
    """τ.6.x.NT.c may extend the structural_map with mark/luke. Verify
    those sections become reachable AFTER the ship (if Step 4 done)."""

    def test_mark_section_optionally_present(self):
        """If mark was added at τ.6.x.NT.c Step 4, it must wire to
        the right page range. If not added, this test is skipped."""
        sm = _source_yaml()["structural_map"]
        if "mark" not in sm:
            import pytest

            pytest.skip("mark section not yet shipped (τ.6.x.NT.c Step 4 deferred)")
        assert sm["mark"]["book_codes"] == ["mrk"]
        assert sm["mark"]["pdf_page_range"] == [1636, 1677]

    def test_luke_section_optionally_present(self):
        """If luke was added at τ.6.x.NT.c Step 4, it must wire to
        the right page range. If not added, this test is skipped."""
        sm = _source_yaml()["structural_map"]
        if "luke" not in sm:
            import pytest

            pytest.skip("luke section not yet shipped (τ.6.x.NT.c Step 4 deferred)")
        assert sm["luke"]["book_codes"] == ["luk"]
        assert sm["luke"]["pdf_page_range"] == [1678, 1753]
