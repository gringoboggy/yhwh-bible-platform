"""γ.1 — Hebrew interlinear UI pins.

Topic file (created alongside the γ.1 ship, follows the ω.27
follow-on convention).

Coverage:
- TestGamma1ApiLookup:         `api_hebrew_lookup` normalizes input
  (H1/h1/1/H0001 all map to H1), returns the full entry shape on
  success, 400 on bogus format, 404 on unknown number.
- TestGamma1HebrewTemplate:    HEBREW_HTML composes the full ζ
  foundation (theme tokens + dark mode + icons + toasts + cmd
  palette markers all substituted at module load).
- TestGamma1RouteRegistration: /hebrew HTML route + /api/hebrew/<num>
  regex route both registered in scripts/web.py's route tables.
- TestGamma1CrossLinkPropagated: every existing console's nav now
  includes the /hebrew link (via the CONSOLES list + HEADER_NAV_LINKS
  substitution).
- TestGamma1FullDataAvailable: the Strong's Hebrew cache file is
  populated (sanity guard — γ.1 would otherwise silently degrade
  to 503 on every lookup).

Pinning rationale: γ.1 is the first Month 3 content-depth ship +
the first phase to add a new console since ψ.* extensions. Drift
in the route registration, the cross-link nav, or the lookup
handler would break the foundational pattern that γ.2 Greek (and
future γ.* phases) will mirror. Pin each contract piece explicitly.
"""

from __future__ import annotations


class TestGamma1ApiLookup:
    """`api_hebrew_lookup` handles normalization + error envelopes."""

    def test_canonical_h_number(self):
        from scripts.api.hebrew import api_hebrew_lookup

        r = api_hebrew_lookup("H1")
        assert r["status"] == "ok"
        assert r["number"] == "H1"
        assert r["lemma"], "lemma should be non-empty for H1"
        assert r["xlit"], "transliteration should be present"
        assert "Strong's" in r["attribution"], "attribution must cite Strong's"

    def test_bare_number(self):
        from scripts.api.hebrew import api_hebrew_lookup

        r = api_hebrew_lookup("1")
        assert r["status"] == "ok"
        assert r["number"] == "H1"

    def test_lowercase_h(self):
        from scripts.api.hebrew import api_hebrew_lookup

        r = api_hebrew_lookup("h1")
        assert r["status"] == "ok"
        assert r["number"] == "H1"

    def test_zero_padded(self):
        from scripts.api.hebrew import api_hebrew_lookup

        r = api_hebrew_lookup("H0001")
        assert r["status"] == "ok"
        assert r["number"] == "H1"

    def test_unknown_number_returns_404(self):
        from scripts.api.hebrew import api_hebrew_lookup

        r = api_hebrew_lookup("99999")
        assert r["status"] == "error"
        assert r["code"] == "unknown_number"
        assert r["http"] == 404

    def test_invalid_format_returns_400(self):
        from scripts.api.hebrew import api_hebrew_lookup

        for bogus in ("abc", "H", "Hxyz", "", "1.5"):
            r = api_hebrew_lookup(bogus)
            assert r["status"] == "error", f"bogus input {bogus!r} should error"
            assert r["http"] == 400, f"bogus input {bogus!r} should be 400, got {r.get('http')}"

    def test_zero_returns_400(self):
        # Strong's numbers start at 1 — H0 is invalid.
        from scripts.api.hebrew import api_hebrew_lookup

        r = api_hebrew_lookup("H0")
        assert r["status"] == "error"
        assert r["http"] == 400

    def test_response_shape_has_all_fields(self):
        # Pin the full shape so a future schema-change is intentional.
        from scripts.api.hebrew import api_hebrew_lookup

        r = api_hebrew_lookup("H1")
        for field in (
            "status",
            "number",
            "lemma",
            "xlit",
            "pron",
            "derivation",
            "definition",
            "kjv_def",
            "attribution",
        ):
            assert field in r, f"response missing field {field!r}"

    def test_known_word_genesis_1_1(self):
        # H7225 = רֵאשִׁית ("beginning") — Genesis 1:1's first
        # significant word. Pinning a real, well-known entry
        # catches lexicon-data drift (e.g., if the JSON cache were
        # accidentally truncated, this would fail loudly).
        from scripts.api.hebrew import api_hebrew_lookup

        r = api_hebrew_lookup("H7225")
        assert r["status"] == "ok"
        assert r["number"] == "H7225"
        # The lemma is "רֵאשִׁית" (or similar diacritic-variants); just
        # check it's non-trivial Hebrew text.
        assert r["lemma"] and any(0x0590 <= ord(c) <= 0x05FF for c in r["lemma"]), (
            "expected Hebrew characters in H7225's lemma"
        )


class TestGamma1HebrewTemplate:
    """The /hebrew console template composes the full ζ foundation."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.hebrew import HEBREW_HTML

        cls.html = HEBREW_HTML

    def test_is_a_valid_html_doc(self):
        assert self.html.startswith("<!DOCTYPE html>")
        assert "</html>" in self.html

    def test_theme_markers_substituted(self):
        # Every ζ marker is gone — substituted at module load.
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
        # Pin that the ζ foundation is actually in the rendered HTML
        # (not just substituted into nothing — that would be silent
        # failure mode).
        assert "--color-bg-page" in self.html, "ζ.1 tokens missing"
        assert "window.ebibleTheme" in self.html, "ζ.2 dark-mode API missing"
        assert "window.ebibleIcons" in self.html, "ζ.5 icons API missing"
        assert "window.ebibleToast" in self.html, "ζ.6 toast API missing"
        assert "window.ebibleCmdPalette" in self.html, "ζ.8 palette API missing"
        assert ".theme-text-2xl" in self.html or "theme-text-2xl" in self.html, "ζ.4 typography missing"

    def test_hebrew_text_rendered_rtl(self):
        # The Hebrew lemma uses RTL direction so the script reads
        # right-to-left like all proper Hebrew typography.
        assert ".hebrew-lemma" in self.html
        assert "direction: rtl" in self.html

    def test_lookup_form_present(self):
        assert 'id="lookup-form"' in self.html
        assert 'id="num-input"' in self.html

    def test_calls_api_hebrew_endpoint(self):
        assert "/api/hebrew/" in self.html, "JS doesn't reference the JSON endpoint"

    def test_text_inserted_via_textcontent(self):
        # XSS guard — Hebrew data inserted via textContent so any
        # future entry containing a malicious sequence stays safe.
        assert ".textContent = data.lemma" in self.html
        assert ".textContent = data.xlit" in self.html

    def test_supports_hash_deep_link(self):
        # /hebrew#H7225 → auto-populates the input + triggers lookup.
        # Shareable link UX. Pin it stays.
        assert "window.location.hash" in self.html
        assert "lookup(num)" in self.html


class TestGamma1RouteRegistration:
    """Both routes registered correctly in scripts/web.py."""

    def test_html_route_returns_hebrew_html(self):
        # Pin that the /hebrew → HEBREW_HTML wiring is in place.
        # We can't easily exercise do_GET without spinning up the
        # server, so we instead verify the source contains the
        # canonical wiring line.
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        src = (repo / "scripts" / "web.py").read_text(encoding="utf-8")
        assert 'if path == "/hebrew"' in src, "/hebrew HTML route not in web.py"
        assert "self._send_html(HEBREW_HTML)" in src, "/hebrew route doesn't dispatch HEBREW_HTML"

    def test_json_route_in_regex_table(self):
        # The JSON endpoint must be in _REGEX_GET_ROUTES so the
        # parameterized dispatch works.
        from scripts import web

        # _REGEX_GET_ROUTES is a list of (re.Pattern, callable);
        # confirm api_hebrew_lookup is one of the callables.
        callables = [handler for (_re, handler) in web._REGEX_GET_ROUTES]
        assert web.api_hebrew_lookup in callables, "/api/hebrew/<num> not in _REGEX_GET_ROUTES"

    def test_regex_matches_canonical_and_bare_inputs(self):
        # The compiled regex must accept H1 / h1 / 1 / H0001.
        from scripts import web

        hebrew_re = None
        for pat, handler in web._REGEX_GET_ROUTES:
            if handler is web.api_hebrew_lookup:
                hebrew_re = pat
                break
        assert hebrew_re is not None, "couldn't locate /api/hebrew regex"
        for accept in ("/api/hebrew/H1", "/api/hebrew/h1", "/api/hebrew/1", "/api/hebrew/H0001", "/api/hebrew/8674"):
            assert hebrew_re.match(accept), f"regex should accept {accept}"
        for reject in ("/api/hebrew/abc", "/api/hebrew/", "/api/hebrew/1.5"):
            assert not hebrew_re.match(reject), f"regex should reject {reject}"


class TestGamma1CrossLinkPropagated:
    """Adding /hebrew to CONSOLES must propagate to every console's
    nav via the design-system substitution. The §6.2 cross-link
    invariant linter check enforces this in CI; we pin a sample
    of consoles here as belt-and-braces."""

    def test_hebrew_in_consoles_list(self):
        from scripts.templates._design import CONSOLES

        routes = {r for (r, _label) in CONSOLES}
        assert "/hebrew" in routes, "/hebrew not added to CONSOLES"

    def test_preflight_nav_includes_hebrew(self):
        from scripts.templates.preflight import PREFLIGHT_HTML

        assert 'href="/hebrew"' in PREFLIGHT_HTML, (
            "/preflight nav missing /hebrew link — HEADER_NAV_LINKS substitution didn't propagate"
        )

    def test_apihelp_nav_includes_hebrew(self):
        from scripts.templates.apihelp import APIHELP_HTML

        assert 'href="/hebrew"' in APIHELP_HTML

    def test_audit_nav_includes_hebrew(self):
        from scripts.templates.audit import AUDIT_HTML

        assert 'href="/hebrew"' in AUDIT_HTML

    def test_hebrew_self_includes_all_other_consoles(self):
        # The reverse direction: /hebrew's own nav must include
        # every other console (cross-link invariant).
        from scripts.templates._design import CONSOLES
        from scripts.templates.hebrew import HEBREW_HTML

        for route, _label in CONSOLES:
            if route == "/hebrew":
                continue  # self-link styled differently
            assert f'href="{route}"' in HEBREW_HTML, f"/hebrew nav missing link to {route}"


class TestGamma1FullDataAvailable:
    """Sanity guard: the Strong's Hebrew JSON cache file is
    populated. γ.1 would otherwise silently 503 on every request."""

    def test_lexicon_loads(self):
        from scripts.core import sources

        lex = sources.strongs_hebrew()
        # The full dump has 8,674 entries (H1 through H8674).
        assert len(lex) >= 8000, f"lexicon looks truncated; got {len(lex)} entries"

    def test_lexicon_has_expected_entries(self):
        from scripts.core import sources

        lex = sources.strongs_hebrew()
        # H1 (father) and H7225 (beginning) are canonical examples.
        assert "H1" in lex
        assert "H7225" in lex
