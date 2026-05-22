import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


class TestBuildVnoteAside:
    def test_english_only_floor(self):
        from scripts.generate_verse_popups import build_vnote_aside

        html = build_vnote_aside(
            code="1ki",
            ch=1,
            vs=1,
            title="The First Book of Kings",
            english="And king David was old.",
            hebrew=None,
            greek=None,
        )
        assert 'id="vnote-1ki-1-1"' in html
        assert 'class="vnote"' in html
        assert "<strong>The First Book of Kings 1:1.</strong>" in html
        assert '<p class="vnote-text">And king David was old.</p>' in html
        assert "vnote-hebrew" not in html
        assert "vnote-greek" not in html
        assert '<a href="#v-1ki-1-1" class="vnote-back" title="Back">↩</a>' in html

    def test_includes_hebrew_and_greek_when_present(self):
        from scripts.generate_verse_popups import build_vnote_aside

        html = build_vnote_aside(
            code="gen",
            ch=1,
            vs=3,
            title="Genesis",
            english="God said, Let there be light.",
            hebrew="<em>וַיֹּ֥אמֶר</em>",
            greek="Καὶ εἶπεν ὁ Θεὸς",
        )
        assert '<p class="vnote-source-label">Hebrew (Masoretic / WLC)</p>' in html
        assert '<p class="vnote-hebrew" dir="rtl" lang="he"><em>וַיֹּ֥אמֶר</em></p>' in html
        assert '<p class="vnote-source-label">Greek (Septuagint / Brenton)</p>' in html
        assert '<p class="vnote-greek" lang="grc">Καὶ εἶπεν ὁ Θεὸς</p>' in html

    def test_empty_english_uses_placeholder(self):
        from scripts.generate_verse_popups import build_vnote_aside

        html = build_vnote_aside(code="gen", ch=1, vs=1, title="Genesis", english=None, hebrew=None, greek=None)
        assert 'class="vnote-text vnote-empty"' in html
        assert "verse marker only" in html

    def test_english_is_html_escaped(self):
        from scripts.generate_verse_popups import build_vnote_aside

        html = build_vnote_aside(
            code="gen", ch=1, vs=1, title="Genesis", english='A < B & "q"', hebrew=None, greek=None
        )
        assert "A &lt; B &amp;" in html
        assert '<p class="vnote-text">A &lt; B' in html


class TestWrapVerseNumber:
    def test_wraps_bare_span(self):
        from scripts.generate_verse_popups import wrap_verse_number

        chunk = '<p class="verse-p"><span class="vn">1</span>And king David was old.'
        out, changed = wrap_verse_number(chunk, code="1ki", ch=1, vs=1, title="The First Book of Kings")
        assert changed is True
        assert (
            '<a id="v-1ki-1-1" epub:type="noteref" '
            'title="The First Book of Kings 1:1" href="#vnote-1ki-1-1">'
            '<span class="vn">1</span></a>'
        ) in out

    def test_idempotent_when_already_wrapped(self):
        from scripts.generate_verse_popups import wrap_verse_number

        already = (
            '<a id="v-1ki-1-1" epub:type="noteref" '
            'title="The First Book of Kings 1:1" href="#vnote-1ki-1-1">'
            '<span class="vn">1</span></a>And king David was old.'
        )
        out, changed = wrap_verse_number(already, code="1ki", ch=1, vs=1, title="The First Book of Kings")
        assert changed is False
        assert out == already

    def test_only_first_matching_span_in_chunk(self):
        from scripts.generate_verse_popups import wrap_verse_number

        chunk = '<span class="vn">2</span>text with a stray "2" inside.'
        out, changed = wrap_verse_number(chunk, code="1ki", ch=1, vs=2, title="The First Book of Kings")
        assert out.count('id="v-1ki-1-2"') == 1


class TestHarvestExistingLangs:
    SAMPLE = (
        '<aside class="vnote" id="vnote-gen-1-3" epub:type="footnote">'
        "<p><strong>Genesis 1:3.</strong></p>"
        '<p class="vnote-text">God said...</p>'
        '<p class="vnote-source-label">Hebrew (Masoretic / WLC)</p>'
        '<p class="vnote-hebrew" dir="rtl" lang="he"><em>וַיֹּ֥אמֶר</em></p>'
        '<p class="vnote-source-label">Greek (Septuagint / Brenton)</p>'
        '<p class="vnote-greek" lang="grc">Καὶ εἶπεν</p>'
        '<p><a href="#v-gen-1-3" class="vnote-back" title="Back">↩</a></p></aside>'
    )

    def test_extracts_inner_html_keyed_by_vnote_id(self):
        from scripts.generate_verse_popups import harvest_existing_langs

        got = harvest_existing_langs(self.SAMPLE)
        assert got["vnote-gen-1-3"]["hebrew"] == "<em>וַיֹּ֥אמֶר</em>"
        assert got["vnote-gen-1-3"]["greek"] == "Καὶ εἶπεν"

    def test_absent_languages_are_none(self):
        from scripts.generate_verse_popups import harvest_existing_langs

        text = '<aside class="vnote" id="vnote-1ki-1-1" epub:type="footnote"><p class="vnote-text">x</p></aside>'
        got = harvest_existing_langs(text)
        assert got["vnote-1ki-1-1"]["hebrew"] is None
        assert got["vnote-1ki-1-1"]["greek"] is None
