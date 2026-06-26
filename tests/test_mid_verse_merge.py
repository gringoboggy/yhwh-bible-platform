"""WS1 mid-verse-break merge (Kobo deep-audit, 2026-06-24) — `build_edition._merge_mid_verse_breaks`.

The eink-only fix that re-joins a narrative verse the calibre base split across a
<p class="verse-p"> boundary (gen 19:1's "Lot saw them…" opens a 2nd paragraph that then
carries v2). Poetry / wisdom / poetic-prophet + irregular apocrypha keep their verse-per-line
layout (user decision 2026-06-25). The 9-KJV/tablet base is untouched (eink-gated by caller).
"""

import re

from scripts import build_edition as be

DOC = "<?xml version='1.0' encoding='utf-8'?>\n<html><body>\n{rows}\n</body></html>\n"


def _vn(book, ch, v):
    return f'<a class="vn-link" id="v-{book}-{ch}-{v}" href="#vnote-{book}-{ch}-{v}" epub:type="noteref"><span class="vn">{v}</span></a>'


def _vp(*chunks):
    return '<p class="verse-p">' + "".join(chunks) + "</p>"


def _write(tmp, *rows, stem="index_split_001"):
    p = tmp / f"{stem}.html"
    p.write_text(DOC.format(rows="\n".join(rows)), encoding="utf-8")
    return p


def _verse_p_inners(text):
    return re.findall(r'<p\b[^>]*class="[^"]*\bverse-p\b[^"]*"[^>]*>(.*?)</p>', text, re.DOTALL)


class TestNarrativeMerge:
    def test_gen_break_is_merged(self, tmp_path):
        p = _write(
            tmp_path,
            _vp(_vn("gen", 19, 1), " The two angels came to Sodom at evening. Lot sat in the gate of Sodom."),
            _vp(
                "Lot saw them, and rose up to meet them. He bowed himself with his face to the earth,",
                _vn("gen", 19, 2),
                " and he said, “See now, my lords.”",
            ),
        )
        n = be._merge_mid_verse_breaks(tmp_path)
        assert n == 1
        inners = _verse_p_inners(p.read_text(encoding="utf-8"))
        # verse 1's spilled tail now lives in v1's paragraph, before any v2 anchor.
        assert "Lot saw them, and rose up to meet them." in inners[0]
        assert "v-gen-19-2" not in inners[0]
        # the 2nd paragraph now opens cleanly at the v2 marker (no leading prose).
        assert inners[1].lstrip().startswith('<a class="vn-link" id="v-gen-19-2"')
        # a separating space was inserted (no "Sodom.Lot" run-on).
        assert "Sodom. Lot saw them" in inners[0]

    def test_no_verse_spans_a_paragraph_after_merge(self, tmp_path):
        p = _write(
            tmp_path,
            _vp(_vn("num", 16, 49), " Now those who died by the plague were fourteen thousand seven hundred,"),
            _vp("in addition to those who died about the matter of Korah.", _vn("num", 16, 50), " Aaron returned."),
        )
        assert be._merge_mid_verse_breaks(tmp_path) == 1
        text = p.read_text(encoding="utf-8")
        # every verse-p paragraph now starts (after tags) with a verse marker — no prose lead-in.
        for inner in _verse_p_inners(text):
            m = re.search(r'<span class="vn">', inner)
            head = re.sub(r"<[^>]+>", "", inner[: m.start()] if m else inner)
            assert not re.search(r"[A-Za-z]{2,}", head), f"prose still leads a paragraph: {head!r}"

    def test_ids_preserved(self, tmp_path):
        p = _write(
            tmp_path,
            _vp(_vn("gen", 19, 1), " head.<a class='note-ref' id='ref-x1'><sup>1</sup></a>"),
            _vp("spilled tail prose,", _vn("gen", 19, 2), " next verse."),
        )
        before = set(re.findall(r'id=[\'"]([^\'"]+)[\'"]', p.read_text(encoding="utf-8")))
        be._merge_mid_verse_breaks(tmp_path)
        after = set(re.findall(r'id=[\'"]([^\'"]+)[\'"]', p.read_text(encoding="utf-8")))
        assert before == after  # every anchor id survives (just relocated)


class TestKeepClasses:
    def test_poetry_not_merged(self, tmp_path):
        p = _write(
            tmp_path,
            _vp(_vn("psa", 18, 1), " I love you, Yahweh, my strength."),
            _vp("Yahweh is my rock, my fortress, and my deliverer;", _vn("psa", 18, 2), " my God, my rock."),
        )
        before = p.read_text(encoding="utf-8")
        assert be._merge_mid_verse_breaks(tmp_path) == 0
        assert p.read_text(encoding="utf-8") == before  # byte-identical no-op

    def test_irregular_apocrypha_not_merged(self, tmp_path):
        p = _write(
            tmp_path,
            _vp(_vn("1en", 27, 1), " Then said I."),
            _vp("continuation prose of the vision,", _vn("1en", 27, 2), " and he answered."),
        )
        before = p.read_text(encoding="utf-8")
        assert be._merge_mid_verse_breaks(tmp_path) == 0
        assert p.read_text(encoding="utf-8") == before


class TestSafety:
    def test_clean_scripture_is_byte_identical_no_op(self, tmp_path):
        p = _write(
            tmp_path,
            _vp(_vn("gen", 1, 1), " In the beginning God created the heavens and the earth."),
            _vp(_vn("gen", 1, 2), " The earth was formless and empty."),
        )
        before = p.read_text(encoding="utf-8")
        assert be._merge_mid_verse_breaks(tmp_path) == 0
        assert p.read_text(encoding="utf-8") == before

    def test_non_adjacent_break_not_merged(self, tmp_path):
        # A chapter heading between the two paragraphs → not a simple continuation → leave it.
        p = _write(
            tmp_path,
            _vp(_vn("gen", 1, 31), " God saw everything that he had made, and it was very good."),
            '<p class="ch-heading"><span class="bold-num">2</span></p>',
            _vp("The heavens and the earth were finished.", _vn("gen", 2, 1), " all their vast array."),
        )
        before = p.read_text(encoding="utf-8")
        # gen 2 owner is gen (fixable) but the heading breaks adjacency → no merge.
        assert be._merge_mid_verse_breaks(tmp_path) == 0
        assert p.read_text(encoding="utf-8") == before

    def test_backmatter_glossary_skipped(self, tmp_path):
        # Two paragraphs with a real break, but in the study-glossary backmatter stem → skipped.
        p = _write(
            tmp_path,
            _vp(_vn("gen", 5, 1), " This is the book of the generations of Adam."),
            _vp("spilled prose of the glossary,", _vn("gen", 5, 2), " more."),
            stem=be.EINK_STUDY_BACKMATTER_STEM,
        )
        before = p.read_text(encoding="utf-8")
        assert be._merge_mid_verse_breaks(tmp_path) == 0
        assert p.read_text(encoding="utf-8") == before


class TestDisplacementGuard:
    """Round-14 #6 (HIGH, scripture corruption): the lead before a block's first verse marker
    is NOT always the prior verse's tail — for est 10:2 it is the verse's OWN opening. The WEB
    discriminator skips that displacement (else "Aren't all the acts…" is corrupted into est
    10:1) while still merging a genuine spilled tail (gen 48:2)."""

    def test_est_10_2_own_opening_not_merged(self, tmp_path):
        # est 10:2 OPENS with its own first words "Aren't all the acts…" (a prefix of WEB est 10:2,
        # not a suffix of est 10:1) → the displacement must be SKIPPED, leaving the text intact.
        p = _write(
            tmp_path,
            _vp(_vn("est", 10, 1), " King Ahasuerus laid a tribute on the land and on the islands of the sea."),
            _vp(
                "Aren’t all the acts of his power and of his might,",
                _vn("est", 10, 2),
                " and the full account of the greatness of Mordecai, written in the book"
                " of the chronicles of the kings of Media and Persia?",
            ),
        )
        before = p.read_text(encoding="utf-8")
        assert be._merge_mid_verse_breaks(tmp_path) == 0  # displacement skipped
        # byte-identical: "Aren't all the acts…" stays in est 10:2; est 10:1 unchanged.
        assert p.read_text(encoding="utf-8") == before
        inners = _verse_p_inners(before)
        assert "Aren’t all the acts of his power" in inners[1]
        assert "Aren’t" not in inners[0]
        assert "islands of the sea." in inners[0]

    def test_gen_48_2_genuine_tail_still_merged(self, tmp_path):
        # Counter-example: gen 48:1's tail "He took with him his two sons…" (a suffix of WEB
        # gen 48:1, not a prefix of gen 48:2) genuinely spilled → must STILL be merged.
        p = _write(
            tmp_path,
            _vp(_vn("gen", 48, 1), " After these things, someone said to Joseph, “Behold, your father is sick.”"),
            _vp(
                "He took with him his two sons, Manasseh and Ephraim.",
                _vn("gen", 48, 2),
                " Someone told Jacob, and said, “Behold, your son Joseph comes to you.”",
            ),
        )
        assert be._merge_mid_verse_breaks(tmp_path) == 1  # genuine tail merged
        inners = _verse_p_inners(p.read_text(encoding="utf-8"))
        assert "He took with him his two sons, Manasseh and Ephraim." in inners[0]
        assert "v-gen-48-2" not in inners[0]
        assert inners[1].lstrip().startswith('<a class="vn-link" id="v-gen-48-2"')
