"""K-KIN E999 (2026-06-13, KDP-confirmed): a kindle artifact must carry ZERO
hidden content. `apply_kindle_strip_hidden` PHYSICALLY removes every
display:none / visibility:hidden (CSS + inline) and the Kobo-eInk-only `.vn-sep`
separator spans for the kindle target — no-op (byte-identical) elsewhere.

Why physical strip, not the prior CSS override: Amazon's Send-to-Kindle / KDP
ingestion rejects content hidden under display:none over the 10,000-char E3013
cap, and — unlike Kindle Previewer and epubcheck — does NOT resolve the CSS
cascade, so the `display:block` override appended after the base `display:none`
is invisible to it (the raw `display:none` string still trips the gate, surfaced
as the opaque E999). The override-stripped artifact converted clean on KDP all
the way to the pricing step (2026-06-13). The Kobo-only `.vn-sep` marks existed
only to be display:none on CSS readers; once nothing hides them they would show
as stray ¶/◦/• glyphs, so the kindle target drops the spans outright.
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

    def test_removes_vn_sep_spans_but_keeps_surrounding_content(self, tmp_path):
        from scripts.build_edition import apply_kindle_strip_hidden

        tmp = _tree(tmp_path)
        stats = apply_kindle_strip_hidden(tmp, {"id": "x", "target_reader": "kindle"})
        html = (tmp / "index_split_000.html").read_text(encoding="utf-8")
        assert 'class="vn-sep"' not in html
        assert "note text" in html
        assert stats["vn_sep_removed"] == 2

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
        assert stats == {"css_hidden_stripped": 0, "vn_sep_removed": 0, "inline_hidden_stripped": 0}

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
