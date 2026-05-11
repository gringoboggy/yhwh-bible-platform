"""γ.2 — Greek interlinear UI pins.

Topic file (created alongside the γ.2 ship). Mirror of
`tests/test_hebrew_gamma1.py` — Greek-specific assertions where
the data differs (G-prefix, LTR, λόγος canonical example).

Coverage:
- TestGamma2ApiLookup:           input normalization, error
  envelopes, full response shape, λόγος (G3056) canonical entry.
- TestGamma2GreekTemplate:        GREEK_HTML composes the full
  ζ foundation; LTR (no RTL); pron field rendered conditionally.
- TestGamma2RouteRegistration:    /greek HTML route +
  /api/greek/<num> regex route registered.
- TestGamma2CrossLinkPropagated:  /greek in CONSOLES,
  bidirectional with /hebrew (γ.1) — both link to each other.
- TestGamma2FullDataAvailable:    Strong's Greek cache populated.
"""

from __future__ import annotations


def _clear_greek_lexicon_cache():
    """Defensive cache reset.

    `tests/test_corpus_chi1.py` monkeypatches `StrongsGreek.PATH` to
    tiny synthetic JSON cache files in several tests. The monkeypatch
    auto-reverts the PATH attribute at test teardown, but the
    `sources.strongs_greek` `lru_cache` retains the stale tiny
    `StrongsGreek` instance — so subsequent tests calling
    `sources.strongs_greek()` get the leftover tiny lexicon instead
    of the real ~5,523-entry one. Calling `.cache_clear()` at setup
    re-resolves PATH (which is now the canonical path) and reloads
    the full cache.
    """
    from scripts.core import sources

    sources.strongs_greek.cache_clear()


class TestGamma2ApiLookup:
    """`api_greek_lookup` handles normalization + error envelopes
    (parallel to γ.1's TestGamma1ApiLookup)."""

    @classmethod
    def setup_class(cls):
        _clear_greek_lexicon_cache()

    def test_canonical_g_number(self):
        from scripts.api.greek import api_greek_lookup

        r = api_greek_lookup("G1")
        assert r["status"] == "ok"
        assert r["number"] == "G1"
        assert r["lemma"], "lemma should be non-empty for G1"

    def test_bare_number(self):
        from scripts.api.greek import api_greek_lookup

        r = api_greek_lookup("1")
        assert r["status"] == "ok"
        assert r["number"] == "G1"

    def test_lowercase_g(self):
        from scripts.api.greek import api_greek_lookup

        r = api_greek_lookup("g1")
        assert r["status"] == "ok"
        assert r["number"] == "G1"

    def test_zero_padded(self):
        from scripts.api.greek import api_greek_lookup

        r = api_greek_lookup("G0001")
        assert r["status"] == "ok"
        assert r["number"] == "G1"

    def test_unknown_number_returns_404(self):
        from scripts.api.greek import api_greek_lookup

        r = api_greek_lookup("99999")
        assert r["status"] == "error"
        assert r["code"] == "unknown_number"
        assert r["http"] == 404

    def test_invalid_format_returns_400(self):
        from scripts.api.greek import api_greek_lookup

        for bogus in ("abc", "G", "Gxyz", "", "1.5"):
            r = api_greek_lookup(bogus)
            assert r["status"] == "error", f"bogus input {bogus!r} should error"
            assert r["http"] == 400, f"bogus input {bogus!r} should be 400, got {r.get('http')}"

    def test_zero_returns_400(self):
        # Strong's numbers start at 1 — G0 is invalid.
        from scripts.api.greek import api_greek_lookup

        r = api_greek_lookup("G0")
        assert r["status"] == "error"
        assert r["http"] == 400

    def test_response_shape_has_all_fields(self):
        # Pin shape parity with γ.1 — same fields, same names.
        from scripts.api.greek import api_greek_lookup

        r = api_greek_lookup("G1")
        for field in (
            "status",
            "number",
            "lemma",
            "xlit",  # normalized from upstream `translit`
            "pron",
            "derivation",
            "definition",
            "kjv_def",
            "attribution",
        ):
            assert field in r, f"response missing field {field!r}"

    def test_logos_canonical_example(self):
        # G3056 = λόγος — the canonical Greek philosophical term;
        # well-known and useful as a data-sanity pin.
        from scripts.api.greek import api_greek_lookup

        r = api_greek_lookup("G3056")
        assert r["status"] == "ok"
        assert r["number"] == "G3056"
        assert r["lemma"] == "λόγος", f"unexpected lemma for G3056: {r['lemma']!r}"
        # Transliteration is normalized from upstream `translit` →
        # we expose it as `xlit` for shape parity with γ.1.
        assert "logos" in r["xlit"].lower() or "lógos" in r["xlit"]

    def test_agape_canonical_example(self):
        # G26 = ἀγάπη ("love") — another well-known NT term.
        from scripts.api.greek import api_greek_lookup

        r = api_greek_lookup("G26")
        assert r["status"] == "ok"
        # Check that the lemma contains Greek characters (Unicode
        # range U+0370–U+03FF for Greek and Coptic).
        assert any(0x0370 <= ord(c) <= 0x03FF for c in r["lemma"]), "expected Greek characters in G26's lemma"


class TestGamma2GreekTemplate:
    """The /greek console template composes the full ζ foundation
    AND renders Greek as LTR (no RTL flip vs γ.1's Hebrew)."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.greek import GREEK_HTML

        cls.html = GREEK_HTML

    def test_is_a_valid_html_doc(self):
        assert self.html.startswith("<!DOCTYPE html>")
        assert "</html>" in self.html

    def test_theme_markers_substituted(self):
        for marker in (
            "<!-- THEME_TOKENS_CSS -->",
            "<!-- DARK_MODE_JS -->",
            "<!-- THEME_ICONS_JS -->",
            "<!-- THEME_TOAST_JS -->",
            "<!-- THEME_CMD_PALETTE_JS -->",
            "<!-- BUYER_ARC_POLISH_CSS -->",
            "<!-- HEADER_NAV_LINKS -->",
        ):
            assert marker not in self.html, f"marker {marker!r} leaked"

    def test_composes_zeta_foundation(self):
        assert "--color-bg-page" in self.html
        assert "window.ebibleTheme" in self.html
        assert "window.ebibleIcons" in self.html
        assert "window.ebibleToast" in self.html
        assert "window.ebibleCmdPalette" in self.html

    def test_greek_text_is_ltr_not_rtl(self):
        # Pin that γ.2 does NOT include the RTL direction rule that
        # γ.1 uses for Hebrew. The Greek script reads left-to-right
        # like English.
        assert ".greek-lemma" in self.html
        # The greek-lemma class block should NOT contain rtl
        greek_lemma_idx = self.html.find(".greek-lemma")
        end = self.html.find("}", greek_lemma_idx)
        block = self.html[greek_lemma_idx:end]
        assert "direction: rtl" not in block, ".greek-lemma should not be RTL — Greek reads left-to-right"

    def test_lookup_form_present(self):
        assert 'id="lookup-form"' in self.html
        assert 'id="num-input"' in self.html

    def test_calls_api_greek_endpoint(self):
        assert "/api/greek/" in self.html
        # Specifically NOT calling /api/hebrew/ — pin against
        # copy-paste-from-γ.1 mistakes.
        # Note: 'href="/hebrew"' will be in the cross-link nav, so
        # we don't assert /api/hebrew is absent broadly — just
        # check the form action / fetch URL pattern.
        assert "fetch('/api/greek/'" in self.html

    def test_text_inserted_via_textcontent(self):
        assert ".textContent = data.lemma" in self.html
        assert ".textContent = data.xlit" in self.html

    def test_pron_field_rendered_conditionally(self):
        # γ.2 difference vs γ.1: the Greek lexicon doesn't carry a
        # pron field for most entries, so the renderer guards
        # `if (data.pron)` rather than always rendering.
        assert "if (data.pron)" in self.html

    def test_supports_hash_deep_link(self):
        # /greek#G3056 → auto-populate + lookup
        assert "window.location.hash" in self.html
        assert "lookup(num)" in self.html


class TestGamma2RouteRegistration:
    """Both routes registered in scripts/web.py."""

    def test_html_route_returns_greek_html(self):
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        src = (repo / "scripts" / "web.py").read_text(encoding="utf-8")
        assert 'if path == "/greek"' in src
        assert "self._send_html(GREEK_HTML)" in src

    def test_json_route_in_regex_table(self):
        from scripts import web

        callables = [handler for (_re, handler) in web._REGEX_GET_ROUTES]
        assert web.api_greek_lookup in callables

    def test_regex_matches_canonical_and_bare_inputs(self):
        from scripts import web

        greek_re = None
        for pat, handler in web._REGEX_GET_ROUTES:
            if handler is web.api_greek_lookup:
                greek_re = pat
                break
        assert greek_re is not None
        for accept in ("/api/greek/G1", "/api/greek/g1", "/api/greek/1", "/api/greek/G3056", "/api/greek/5523"):
            assert greek_re.match(accept), f"regex should accept {accept}"
        for reject in ("/api/greek/abc", "/api/greek/", "/api/greek/1.5"):
            assert not greek_re.match(reject), f"regex should reject {reject}"


class TestGamma2CrossLinkPropagated:
    """/greek joins the cross-link nav; bidirectional with /hebrew."""

    def test_greek_in_consoles_list(self):
        from scripts.templates._design import CONSOLES

        routes = {r for (r, _label) in CONSOLES}
        assert "/greek" in routes
        # γ.1 + γ.2 both present — the language pair.
        assert "/hebrew" in routes

    def test_preflight_nav_includes_greek(self):
        from scripts.templates.preflight import PREFLIGHT_HTML

        assert 'href="/greek"' in PREFLIGHT_HTML

    def test_hebrew_nav_includes_greek(self):
        # γ.1 + γ.2 are paired; verify the link goes both ways.
        from scripts.templates.hebrew import HEBREW_HTML

        assert 'href="/greek"' in HEBREW_HTML, "/hebrew nav missing /greek"

    def test_greek_nav_includes_hebrew(self):
        from scripts.templates.greek import GREEK_HTML

        assert 'href="/hebrew"' in GREEK_HTML, "/greek nav missing /hebrew"

    def test_greek_self_includes_all_other_consoles(self):
        from scripts.templates._design import CONSOLES
        from scripts.templates.greek import GREEK_HTML

        for route, _label in CONSOLES:
            if route == "/greek":
                continue
            assert f'href="{route}"' in GREEK_HTML, f"/greek nav missing link to {route}"


class TestGamma2FullDataAvailable:
    """Sanity guard for the Strong's Greek JSON cache."""

    @classmethod
    def setup_class(cls):
        _clear_greek_lexicon_cache()

    def test_lexicon_loads(self):
        from scripts.core import sources

        lex = sources.strongs_greek()
        # Full Greek dump: 5,523 entries.
        assert len(lex) >= 5000, f"Greek lexicon looks truncated; got {len(lex)} entries"

    def test_lexicon_has_expected_entries(self):
        from scripts.core import sources

        lex = sources.strongs_greek()
        # G1 (first entry) + G3056 (λόγος) + G26 (ἀγάπη) — canonical
        # examples that should always exist.
        assert "G1" in lex
        assert "G3056" in lex
        assert "G26" in lex
