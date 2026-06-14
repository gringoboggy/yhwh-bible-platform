"""K-KIN E999 (2026-06-13, Send-to-Kindle-confirmed 2026-06-14): a kindle
artifact must carry ZERO content hidden under CSS display:none / visibility:hidden.
`apply_kindle_strip_hidden` PHYSICALLY removes every such declaration (CSS files +
inline `style=`) for the kindle target — no-op (byte-identical) elsewhere.

Why physical strip, not the prior CSS override: Amazon's Send-to-Kindle ingestion
rejects content hidden under display:none over the 10,000-char E3013 cap, and —
unlike Kindle Previewer and epubcheck — does NOT resolve the CSS cascade, so the
`display:block` override appended after the base `display:none` is invisible to it
(the raw `display:none` string still trips the gate, the opaque E999).

It does NOT touch the `.vn-sep` separator spans: the proven june10recipe.epub kept
all 132,949 of them (and the matching `.vn-sep { display:none }` rule was stripped
with every other hide, so they render as visible bullets) and DELIVERED via
Send-to-Kindle (user-confirmed). Dropping the spans was a FIXED.epub (FAIL) behavior;
only the real STK channel is a valid oracle.
(docs/superpowers/plans/2026-06-14-kindle-recipe-productization.md)
"""


def _tree(tmp_path):
    tmp = tmp_path / "build"
    tmp.mkdir()
    (tmp / "stylesheet.css").write_text(
        ".notes-section, .notes-rule { display: none; }\n"
        ".verse-refs-section { display:none; }\n"
        ".vn-sep { display: none; }\n"
        ".thing { visibility: hidden; }\n"
        ".keep { display: block; margin: 1em; }\n",
        encoding="utf-8",
    )
    (tmp / "index_split_000.html").write_text(
        "<html><body><p>scripture</p>"
        '<aside class="verse-notes"><span class="vn-sep"> • </span>note text</aside>'
        '<span class="vn-sep"> ¶ </span>'
        '<p style="color:red;display:none">x</p>'
        "</body></html>",
        encoding="utf-8",
    )
    return tmp


class TestKindleStripHidden:
    def test_strips_all_hidden_decls_from_css_keeps_the_rest(self, tmp_path):
        from scripts.build_edition import apply_kindle_strip_hidden

        tmp = _tree(tmp_path)
        stats = apply_kindle_strip_hidden(tmp, {"id": "x", "target_reader": "kindle"})
        css = (tmp / "stylesheet.css").read_text(encoding="utf-8")
        assert "display: none" not in css and "display:none" not in css
        assert "visibility: hidden" not in css and "visibility:hidden" not in css
        # a non-hidden rule is left intact
        assert ".keep { display: block; margin: 1em; }" in css
        assert stats["css_hidden_stripped"] == 4

    def test_keeps_vn_sep_spans(self, tmp_path):
        # june10recipe.epub (the STK PASS) kept all its vn-sep spans — only the
        # display:none decls are stripped, never the spans.
        from scripts.build_edition import apply_kindle_strip_hidden

        tmp = _tree(tmp_path)
        before = (tmp / "index_split_000.html").read_text(encoding="utf-8")
        apply_kindle_strip_hidden(tmp, {"id": "x", "target_reader": "kindle"})
        html = (tmp / "index_split_000.html").read_text(encoding="utf-8")
        assert html.count('class="vn-sep"') == 2  # both spans survive
        assert "•" in html and "¶" in html  # their separator glyphs are untouched
        assert "note text" in html
        # the vn-sep spans are byte-identical before/after (only display:none goes)
        assert before.count('<span class="vn-sep">') == html.count('<span class="vn-sep">')

    def test_strips_inline_hidden(self, tmp_path):
        from scripts.build_edition import apply_kindle_strip_hidden

        tmp = _tree(tmp_path)
        apply_kindle_strip_hidden(tmp, {"id": "x", "target_reader": "kindle"})
        html = (tmp / "index_split_000.html").read_text(encoding="utf-8")
        assert "display:none" not in html and "display: none" not in html
        assert "color:red" in html  # the rest of the inline style survives

    def test_noop_for_non_kindle_targets(self, tmp_path):
        from scripts.build_edition import apply_kindle_strip_hidden

        tmp = _tree(tmp_path)
        before_css = (tmp / "stylesheet.css").read_text(encoding="utf-8")
        before_html = (tmp / "index_split_000.html").read_text(encoding="utf-8")
        stats = apply_kindle_strip_hidden(tmp, {"id": "x"})
        assert (tmp / "stylesheet.css").read_text(encoding="utf-8") == before_css
        assert (tmp / "index_split_000.html").read_text(encoding="utf-8") == before_html
        assert stats == {"css_hidden_stripped": 0, "inline_hidden_stripped": 0}

    def test_idempotent(self, tmp_path):
        from scripts.build_edition import apply_kindle_strip_hidden

        tmp = _tree(tmp_path)
        ed = {"id": "x", "target_reader": "kindle"}
        apply_kindle_strip_hidden(tmp, ed)
        once_css = (tmp / "stylesheet.css").read_text(encoding="utf-8")
        once_html = (tmp / "index_split_000.html").read_text(encoding="utf-8")
        apply_kindle_strip_hidden(tmp, ed)
        assert (tmp / "stylesheet.css").read_text(encoding="utf-8") == once_css
        assert (tmp / "index_split_000.html").read_text(encoding="utf-8") == once_html
