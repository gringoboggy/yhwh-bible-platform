"""Idiot-proof app arc (v0.1.0) — the friendly HOME landing + the rich-text editor.

Spec: docs/superpowers/specs/2026-06-09-idiot-proof-app-design.md
Colors: docs/superpowers/notes/2026-06-09-home-html-aa-colors.md (per-element AA contract)

The shipped .exe/.app used to open on the maintainer note editor (dense 3-pane
raw-HTML console) — the north-star complaint. The fix: `/` serves a new CDN-free
HOME_HTML; the editor moves to /notes; the raw-HTML body textarea becomes a
Bold/Italic contenteditable normalized to <strong>/<em> on save.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from scripts.core import config

REPO = Path(config.__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

WEB_PY = REPO / "scripts" / "web.py"
INDEX_PY = REPO / "scripts" / "templates" / "index.py"


class TestMsPalette:
    """MS_PALETTE — the single source of truth the CDN-free HOME builds its
    <style> from (design spec §1 mitigation: no palette drift)."""

    def _palette(self):
        from scripts.templates._design import MS_PALETTE

        return MS_PALETTE

    def test_exports_the_aa_contract_tokens(self):
        pal = self._palette()
        expected = {
            "vellum": "#F4ECD8",
            "parchment": "#FBF6E9",
            "ink": "#2B2118",
            "sepia": "#574532",
            "muted": "#6E5840",
            "gold": "#B8860B",
            "gold_hover": "#C49A2E",  # lighter, NOT darker (H1 fix)
            "gold_line": "#9A6E12",
            "indigo": "#243B6B",
            "antique": "#FCF8EF",
            "red": "#7A1F2B",
            "red_dark": "#5E1722",
        }
        for key, hexval in expected.items():
            assert pal.get(key) == hexval, f"MS_PALETTE[{key!r}] must be {hexval}; got {pal.get(key)!r}"


class TestHomeTemplate:
    """HOME_HTML — one calm CDN-free screen; structurally immune to every
    η.1-skin hazard (no Tailwind, no JS)."""

    def _html(self) -> str:
        from scripts.templates.home import HOME_HTML

        return HOME_HTML

    def test_cdn_free_and_script_free(self):
        html = self._html()
        assert "cdn.tailwindcss.com" not in html, "HOME must NOT load the Tailwind CDN (spec §1)"
        assert "<script" not in html, "HOME needs zero JS — CSP-clean, no nonce dependency"

    def test_social_card_hero(self):
        assert "/static/social-card.png" in self._html()

    def test_self_hosted_fonts_declared(self):
        # CDN-free means HOME never inherits the skin's @font-face — it must
        # declare EB Garamond (+ the Ethiopic fallback) itself off /fonts/.
        html = self._html()
        assert "/fonts/eb-garamond-latin-400-normal.woff2" in html
        assert "/fonts/eb-garamond-latin-700-normal.woff2" in html
        assert "/fonts/noto-serif-ethiopic-ethiopic-400-normal.woff2" in html

    def test_one_gold_primary_cta_to_wizard(self):
        html = self._html()
        assert 'href="/wizard"' in html, "primary CTA = Build my Bible -> /wizard (user default)"
        assert "#B8860B" in html, "gold CTA fill"
        assert "#C49A2E" in html, "gold hover must be the LIGHTER #C49A2E (6.01:1), not darker"
        assert html.count("cta") >= 1

    def test_indigo_links_and_focus(self):
        html = self._html()
        assert "#243B6B" in html, "links/secondary/focus = indigo (user preference + AA)"

    def test_secondary_doors_and_maintainer_footer(self):
        html = self._html()
        assert 'href="/build-my-bible"' in html
        assert 'href="/hebrew"' in html and 'href="/greek"' in html
        assert 'href="/notes"' in html, 'quiet footer "Maintainer tools" -> /notes'

    def test_gold_is_never_a_text_color(self):
        # The L2 guard applied preemptively: gold only as button FILL or hairline.
        html = self._html()
        for m in re.finditer(r"color:\s*(#B8860B|#C49A2E)", html):
            before = html[max(0, m.start() - 60) : m.start()]
            assert "background" in m.group(0) or "background-color" in before, (
                f"gold used as a text color near: …{html[max(0, m.start() - 80) : m.end() + 20]}…"
            )

    def test_built_from_ms_palette(self):
        src = (REPO / "scripts" / "templates" / "home.py").read_text(encoding="utf-8")
        assert "MS_PALETTE" in src, "HOME's <style> must be built from MS_PALETTE (no palette drift)"


class TestRouteSwap:
    """`/` -> HOME; the editor -> /notes (+ /index.html for bookmarks)."""

    def _web(self) -> str:
        return WEB_PY.read_text(encoding="utf-8")

    def test_root_serves_home(self):
        web = self._web()
        assert 'path == "/" or path == "/home"' in web
        idx = web.find('path == "/" or path == "/home"')
        seg = web[idx : idx + 200]
        assert "HOME_HTML" in seg

    def test_notes_serves_the_editor(self):
        web = self._web()
        assert 'path == "/notes" or path == "/index.html"' in web
        idx = web.find('path == "/notes" or path == "/index.html"')
        seg = web[idx : idx + 200]
        assert "INDEX_HTML" in seg

    def test_social_card_static_route(self):
        web = self._web()
        assert "/static/social-card.png" in web
        idx = web.find('"/static/social-card.png"')
        seg = web[idx : idx + 600]
        assert "image/png" in seg

    def test_home_html_imported(self):
        assert "HOME_HTML" in self._web()


class TestConsolesDemotion:
    """One CONSOLES edit demotes the editor across all consoles at once."""

    def _consoles(self):
        from scripts.templates._design import CONSOLES

        return CONSOLES

    def test_home_leads_the_nav(self):
        assert self._consoles()[0] == ("/home", "home")

    def test_editor_relabeled_demoted_to_the_end(self):
        consoles = self._consoles()
        assert ("/", "note editor") not in consoles, "the editor must no longer claim /"
        assert consoles[-1] == ("/notes", "notes (maintainer)"), (
            "the note editor must sit LAST in the nav, labeled as maintainer tooling"
        )


class TestRichTextEditor:
    """The body(HTML) textarea -> Bold/Italic contenteditable + normalizeBody
    allowlist serializer (spec §2). Strictly safer than today: the old textarea
    POSTed arbitrary unsanitized HTML."""

    def _idx(self) -> str:
        return INDEX_PY.read_text(encoding="utf-8")

    def test_contenteditable_body_replaces_the_textarea(self):
        idx = self._idx()
        assert 'contenteditable="true"' in idx
        assert 'id="f-body"' in idx
        assert '<textarea id="f-body"' not in idx, "the raw-HTML textarea must not be the primary editor"

    def test_toolbar_uses_execcommand(self):
        idx = self._idx()
        for cmd in ("'bold'", "'italic'", "'createLink'", "'removeFormat'"):
            assert f"execCommand({cmd}" in idx, f"toolbar missing execCommand({cmd})"

    def test_normalize_body_is_defined_and_used_at_save(self):
        idx = self._idx()
        assert "function normalizeBody" in idx
        # saveNote posts editorBodyHtml(), which is the hatch dispatcher:
        # raw-textarea verbatim while "Advanced: HTML source" is OPEN, else
        # normalizeBody(innerHTML). Never innerHTML verbatim.
        save_idx = idx.find("async function saveNote")
        seg = idx[save_idx : idx.find("}", idx.find("body:", save_idx)) + 1]
        assert "editorBodyHtml()" in seg, "saveNote must NOT post innerHTML verbatim"
        helper_idx = idx.find("function editorBodyHtml")
        helper = idx[helper_idx : idx.find("\n}", helper_idx)]
        assert "normalizeBody" in helper, "the default save path must normalize"

    def test_normalize_handles_webkit_styled_spans(self):
        # WebKit (the shipped macOS engine) emits <span style="font-weight:bold">
        # — span-handling is load-bearing, not optional (spec §2).
        idx = self._idx()
        assert "font-weight" in idx and "font-style" in idx

    def test_normalize_validates_hrefs(self):
        # Scheme-based gate: explicit schemes allowlisted to https?:/mailto:,
        # scheme-LESS hrefs pass — corpus xref links are relative
        # ("index_split_054.html#ch-…", live-data catch 2026-06-09) and a
        # prefix-only allowlist silently unwrapped them.
        idx = self._idx()
        assert "https?:" in idx and "mailto:" in idx, "scheme allowlist missing"
        assert "SCHEME" in idx and "[a-z0-9+.-]*:" in idx, (
            "href gate must be scheme-based so RELATIVE xref hrefs survive normalization"
        )

    def test_normalize_drops_executable_subtrees(self):
        idx = self._idx()
        assert "SCRIPT|STYLE|TEMPLATE|IFRAME|OBJECT|EMBED" in idx

    def test_advanced_html_escape_hatch(self):
        idx = self._idx()
        assert 'id="f-body-raw"' in idx, "collapsed raw-HTML <details> escape hatch missing"
        assert "HTML source" in idx

    def test_separate_preview_pane_deleted(self):
        # The editable surface IS the rendered view now.
        idx = self._idx()
        assert 'id="preview"' not in idx
