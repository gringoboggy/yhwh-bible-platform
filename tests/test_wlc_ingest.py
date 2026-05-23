"""Phase 2 — WLC Hebrew ingestion (morphhb OSIS → em-per-word, KJV-remapped).

Characterization of the OSIS→<em> transformer against the recovered base's
existing ``vnote-hebrew`` markup (``tests/fixtures/wlc_gen1_em_expected.json``
was auto-extracted from ``epub_working/``, not hand-transcribed).

Source-variance finding (verified): of Genesis 1's 28 already-em-wrapped base
verses, 23 match the morphhb output byte-for-byte and 5 differ *only* in
cantillation accents (te'amim, U+0591–U+05AF) — e.g. Gen 1:7 has QADMA where the
base had PASHTA. Zero consonant/vowel differences. The morphhb / OpenScriptures
Hebrew Bible is the authoritative, roadmap-locked WLC source, so its te'amim
supersede the base's older transcription. The tests therefore pin:

  * **structure + consonants + vowels** for every base verse (te'amim normalized);
  * **byte-exact** rendering on the three format-rule-bearing verses where the
    sources agree, anchoring maqaf / chained-maqaf / paseq / sof-pasuq exactly.

Plain seed verses (Gen 1:1-3) are upgraded to em-wrapped form — Phase 2's
intended additive change — so they are not exact-match targets.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
FIX_OSIS = REPO / "tests" / "fixtures" / "morphhb_gen1_sample.xml"
FIX_EXPECTED = REPO / "tests" / "fixtures" / "wlc_gen1_em_expected.json"
FIX_VERSEMAP = REPO / "tests" / "fixtures" / "versemap_sample.xml"
FIX_PS3 = REPO / "tests" / "fixtures" / "morphhb_ps3_sample.xml"
FIX_GEN3132 = REPO / "tests" / "fixtures" / "morphhb_gen3132_sample.xml"
FIX_DEUT64 = REPO / "tests" / "fixtures" / "morphhb_deut64_sample.xml"
OSIS_NS = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"

_EXPECTED = json.loads(FIX_EXPECTED.read_text(encoding="utf-8"))
_EM_VERSES = sorted(k for k, v in _EXPECTED.items() if v.startswith("<em>"))

# Hebrew cantillation accents (te'amim). NOT niqqud (vowels start at U+05B0).
_TEAMIM_RE = re.compile(r"[֑-֯]")


def _strip_teamim(s: str) -> str:
    return _TEAMIM_RE.sub("", s)


def _verse_elements(path=FIX_OSIS) -> dict:
    root = ET.parse(path).getroot()
    return {v.get("osisID"): v for v in root.iter(OSIS_NS + "verse")}


@pytest.mark.parametrize("osis_id", _EM_VERSES)
def test_transform_preserves_base_consonants_vowels_and_structure(osis_id):
    """Across every em-wrapped base verse, the transform reproduces the base's
    em-structure, consonants, and vowels exactly (te'amim normalized away — see
    module docstring on WLC source variance)."""
    from scripts.extract_wlc_morphhb import verse_to_em_html

    got = verse_to_em_html(_verse_elements()[osis_id])
    assert _strip_teamim(got) == _strip_teamim(_EXPECTED[osis_id])


@pytest.mark.parametrize("osis_id", ["Gen.1.4", "Gen.1.5", "Gen.1.31"])
def test_format_rule_verses_render_byte_exact(osis_id):
    """Byte-exact (te'amim included) on the rule-bearing verses where morphhb and
    the base agree: 1:4 single maqaf + sof-pasuq, 1:5 standalone paseq + dropped
    pe, 1:31 chained maqaf (אֶת־כָּל־אֲשֶׁר) + dropped pe."""
    from scripts.extract_wlc_morphhb import verse_to_em_html

    assert verse_to_em_html(_verse_elements()[osis_id]) == _EXPECTED[osis_id]


def test_seed_plain_verse_upgraded_to_em_wrapped():
    """Gen 1:1 was plain in the 3-verse seed; the full ingest wraps every word."""
    from scripts.extract_wlc_morphhb import verse_to_em_html

    out = verse_to_em_html(_verse_elements()["Gen.1.1"])
    assert out.startswith("<em>") and out.endswith("</em>")
    assert out.count("<em>") == 7  # 7 words, no maqaf in Gen 1:1


def test_large_letter_words_keep_full_consonants_and_drop_notes():
    """Scribal special letters are nested ``<seg type="x-large">`` INSIDE the
    ``<w>`` (Deut 6:4 Shema: ``שְׁמַ<seg>ע</seg>``, ``אֶחָ<seg>ד</seg>``). The
    transform must keep the WHOLE word — not truncate at the nested element —
    and must not leak the sibling ``<note>`` explanation text into the output."""
    from scripts.extract_wlc_morphhb import verse_to_em_html

    out = verse_to_em_html(_verse_elements(FIX_DEUT64)["Deut.6.4"])
    bare = re.sub(r"[֑-ׇ]", "", out)  # strip all points + accents
    assert "<em>שמע</em>" in bare  # the large ע, not the truncated <em>שמ</em>
    assert "אחד" in bare  # final dalet preserved (sof-pasuq glued)
    assert "Large letter" not in out  # sibling <note> body not leaked


# --------------------------------------------------------------------------
# Versification — scripts/core/versification.py (the WLC↔KJV crux)
# --------------------------------------------------------------------------


def test_versemap_full_entries_remap_wlc_masoretic_to_kjv():
    """The 'full' entries map WLC (Masoretic) coords onto canonical KJV coords:
    the Genesis 31/32 chapter-boundary shift and the Psalm 3 superscription
    off-by-one are the named divergence loci."""
    from scripts.core import versification as vsf

    m = vsf.wlc_to_kjv_map(FIX_VERSEMAP)
    assert m[("Gen", 32, 1)] == ("Gen", 31, 55)  # boundary shift
    assert m[("Gen", 32, 2)] == ("Gen", 32, 1)
    assert m[("Ps", 3, 2)] == ("Ps", 3, 1)  # Hebrew superscription = WLC v1
    assert m[("Ps", 3, 9)] == ("Ps", 3, 8)


def test_versemap_omits_unmapped_coords_so_caller_defaults_to_identity():
    """Coords with no entry are absent — the vast majority of verses where WLC
    and KJV agree map identity by the caller's ``.get(coord, coord)``."""
    from scripts.core import versification as vsf

    m = vsf.wlc_to_kjv_map(FIX_VERSEMAP)
    assert ("Gen", 1, 1) not in m
    assert ("Ps", 3, 1) not in m  # WLC superscription has NO KJV slot


def test_kjv_targets_expose_claimed_coords_for_superscription_drop():
    """The set of KJV coords an explicit entry maps onto — used by the extractor
    to drop a WLC superscription verse whose identity coord is already claimed."""
    from scripts.core import versification as vsf

    targets = set(vsf.wlc_to_kjv_map(FIX_VERSEMAP).values())
    assert ("Gen", 31, 55) in targets  # claimed by WLC 32:1
    assert ("Ps", 3, 1) in targets  # claimed by WLC 3:2 → WLC 3:1 (title) drops


# --------------------------------------------------------------------------
# Full-book extraction — extract_book (transform + KJV remap + drop)
# --------------------------------------------------------------------------


def test_extract_book_keys_all_gen1_verses_by_kjv_coord():
    """A whole OSIS book → a sorted ``(ch, vs, html)`` VERSES list. Genesis 1 has
    no remap loci, so all 31 verses key identity, carrying the em-html (seed
    verses upgraded)."""
    from scripts.core.versification import wlc_to_kjv_map
    from scripts.extract_wlc_morphhb import extract_book

    verses = extract_book(FIX_OSIS, wlc_to_kjv_map(FIX_VERSEMAP))
    assert [v for (_c, v, _t) in verses] == list(range(1, 32))
    assert all(c == 1 for (c, _v, _t) in verses)
    d = {(c, v): t for (c, v, t) in verses}
    assert d[(1, 4)] == _EXPECTED["Gen.1.4"]
    assert d[(1, 1)].count("<em>") == 7  # plain seed verse upgraded to em-wrapped


def test_extract_book_genesis_3132_boundary_shifts_wlc_to_kjv():
    """The Genesis 31/32 boundary: WLC 32:1 carries KJV 31:55; WLC 32:2 → KJV
    32:1; the WLC 31:54 identity verse is preserved. Content cross-checked via
    the transformer (no hand-typed Hebrew)."""
    from scripts.core.versification import wlc_to_kjv_map
    from scripts.extract_wlc_morphhb import extract_book, verse_to_em_html

    els = _verse_elements(FIX_GEN3132)
    d = {(c, v): t for (c, v, t) in extract_book(FIX_GEN3132, wlc_to_kjv_map(FIX_VERSEMAP))}
    assert d[(31, 54)] == verse_to_em_html(els["Gen.31.54"])  # identity
    assert d[(31, 55)] == verse_to_em_html(els["Gen.32.1"])  # boundary shift
    assert d[(32, 1)] == verse_to_em_html(els["Gen.32.2"])


def test_extract_book_psalm3_superscription_dropped_and_offbyone():
    """Psalm 3: the Hebrew superscription (WLC 3:1) has no KJV slot and is
    dropped; KJV 3:1-8 carry WLC 3:2-9 (off-by-one). KJV Ps 3 ends at verse 8."""
    from scripts.core.versification import wlc_to_kjv_map
    from scripts.extract_wlc_morphhb import extract_book, verse_to_em_html

    els = _verse_elements(FIX_PS3)
    verses = extract_book(FIX_PS3, wlc_to_kjv_map(FIX_VERSEMAP))
    d = {(c, v): t for (c, v, t) in verses}
    assert sorted(v for (_c, v, _t) in verses) == list(range(1, 9))  # KJV 1..8
    assert d[(3, 1)] == verse_to_em_html(els["Ps.3.2"])  # off-by-one
    assert d[(3, 8)] == verse_to_em_html(els["Ps.3.9"])
    assert d[(3, 1)] != verse_to_em_html(els["Ps.3.1"])  # superscription not mis-placed


# --------------------------------------------------------------------------
# Driver — book-code mapping, module writer, orchestration
# --------------------------------------------------------------------------


def test_osis_book_to_code_covers_39_ot_books_with_valid_codes():
    """Every OSIS book name maps to a real project book code (typo-prone data)."""
    from scripts.core import config
    from scripts.extract_wlc_morphhb import OSIS_BOOK_TO_CODE

    assert len(OSIS_BOOK_TO_CODE) == 39  # the Hebrew canon
    valid = set(config.books_by_code())
    assert set(OSIS_BOOK_TO_CODE.values()) <= valid
    assert len(set(OSIS_BOOK_TO_CODE.values())) == 39  # no dup targets


def test_write_book_module_roundtrips_via_translations_loader(tmp_path):
    """The emitted .py module loads back to the exact VERSES via the runtime
    loader (ast.literal_eval — never executed as code)."""
    from scripts.core import translations as tx
    from scripts.extract_wlc_morphhb import write_book_module

    verses = [(1, 1, "<em>בְּרֵאשִׁ֖ית</em> <em>בָּרָ֣א</em>"), (1, 2, "<em>וְהָאָ֗רֶץ</em>")]
    out = tmp_path / "gen.py"
    write_book_module(out, "wlc", "gen", verses)
    assert tx.load_book_verses_from_text(out.read_text(encoding="utf-8")) == verses


def test_extract_all_writes_per_book_modules_and_meta(tmp_path):
    """End-to-end: a source dir with Gen.xml + VerseMap.xml → content modules +
    _meta.yaml. Other books absent ⇒ skipped, not errored."""
    from scripts.core import translations as tx
    from scripts.extract_wlc_morphhb import extract_all

    src = tmp_path / "src"
    src.mkdir()
    (src / "Gen.xml").write_bytes(FIX_OSIS.read_bytes())
    (src / "VerseMap.xml").write_bytes(FIX_VERSEMAP.read_bytes())
    out = tmp_path / "out"
    out.mkdir()

    stats = extract_all(src, out)
    assert stats["books"] == 1
    assert stats["verses"] == 31
    loaded = tx.load_book_verses_from_text((out / "gen.py").read_text(encoding="utf-8"))
    assert len(loaded) == 31
    assert (out / "_meta.yaml").is_file()
