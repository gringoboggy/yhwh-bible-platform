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
