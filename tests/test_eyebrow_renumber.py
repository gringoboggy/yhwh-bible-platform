"""K-R6-4 (Kobo round-6 device QA): every title page rendered "BOOKII" —
the eyebrow's word space is markup-present (one koboSpan) but the
small-caps + letter-spacing + italic CSS combo EATS it on the kepub engine
(pre-existing; CSS byte-identical v0.1.0/r5/r6). Fix at the EMITTER, not the
87 base sites: ``apply_appendix_demotion_and_renumber`` re-writes every
surviving ``BOOK <roman>`` eyebrow text on EVERY build (spine-order
renumber), so base-site edits would be clobbered — the emitter must bake a
NO-BREAK SPACE (U+00A0), which no engine's whitespace handling collapses.
Demoted ``appendix-section`` eyebrows are skipped by design (CSS hides
them) and Apple rendering is unchanged (nbsp == space visually there).
"""

from scripts.build_edition import apply_appendix_demotion_and_renumber

TITLE_PAGE = (
    '<div class="book-title-page" id="bp-{n}" data-book-idx="{n}" epub:type="bodymatter">'
    '<div class="book-title-frame">'
    '<p class="bookpage-eyebrow">{eyebrow}</p>'
    '<h1 class="bookpage-title">Book {n}</h1>'
    "</div></div>"
)


def _write(tmp_path, *divs):
    f = tmp_path / "index_split_000.html"
    f.write_text("<html><body>" + "".join(divs) + "</body></html>", encoding="utf-8")
    return f


class TestEyebrowNbsp:
    def test_renumbered_eyebrows_carry_nbsp_not_space(self, tmp_path):
        f = _write(
            tmp_path,
            TITLE_PAGE.format(n=0, eyebrow="BOOK I"),
            TITLE_PAGE.format(n=1, eyebrow="BOOK XLVI"),
        )
        stats = apply_appendix_demotion_and_renumber(tmp_path, None)
        text = f.read_text(encoding="utf-8")
        assert stats["eyebrows_renumbered"] == 2
        assert '<span class="eyebrow-book">BOOK</span><span class="eyebrow-num">\u00a0I</span>' in text
        assert '<span class="eyebrow-book">BOOK</span><span class="eyebrow-num">\u00a0II</span>' in text
        assert "BOOK I<" not in text and "BOOK XLVI" not in text  # plain-space variants gone

    def test_renumber_is_spine_order_across_files(self, tmp_path):
        a = tmp_path / "index_split_000.html"
        b = tmp_path / "index_split_001.html"
        a.write_text("<html><body>" + TITLE_PAGE.format(n=0, eyebrow="BOOK IX") + "</body></html>", encoding="utf-8")
        b.write_text("<html><body>" + TITLE_PAGE.format(n=1, eyebrow="BOOK V") + "</body></html>", encoding="utf-8")
        apply_appendix_demotion_and_renumber(tmp_path, None)
        assert '<span class="eyebrow-num">\u00a0I</span>' in a.read_text(encoding="utf-8")
        assert '<span class="eyebrow-num">\u00a0II</span>' in b.read_text(encoding="utf-8")

    def test_demoted_appendix_eyebrow_untouched_and_consumes_no_number(self, tmp_path):
        appendix = TITLE_PAGE.format(n=1, eyebrow="BOOK XLVII").replace(
            'class="book-title-page"', 'class="appendix-section"'
        )
        f = _write(
            tmp_path,
            TITLE_PAGE.format(n=0, eyebrow="BOOK I"),
            appendix,
            TITLE_PAGE.format(n=2, eyebrow="BOOK XLVIII"),
        )
        stats = apply_appendix_demotion_and_renumber(tmp_path, None)
        text = f.read_text(encoding="utf-8")
        assert stats["eyebrows_renumbered"] == 2
        # the appendix keeps its original (CSS-hidden) eyebrow text verbatim
        assert "BOOK XLVII</p>" in text
        # the kept neighbours number 1, 2 with no gap for the appendix
        assert (
            '<span class="eyebrow-num">\u00a0I</span>' in text and '<span class="eyebrow-num">\u00a0II</span>' in text
        )
