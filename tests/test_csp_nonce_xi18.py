"""ξ.18 — CSP nonce pins (2026-05-12).

Per PROPOSAL §6 Track G: "Replace 'unsafe-inline' with per-request
nonces. Significantly hardens XSS." Month 6 #3 (Month-6 non-money).

Coverage:
- TestXi18NonceGeneration:        `_generate_nonce` returns
  freshly-random base64-urlsafe strings, ≥22 chars (≥128 bits
  of entropy), distinct on consecutive calls.
- TestXi18CspWithNonce:           `_csp_with_nonce(nonce)` builds
  a CSP that DROPS 'unsafe-inline' from script-src and ADDS
  'nonce-X'; style-src deliberately keeps 'unsafe-inline'
  (Tailwind CDN compat); other directives preserved.
- TestXi18ScriptInjection:        `_inject_script_nonces(html,
  nonce)` adds `nonce="X"` to every <script tag variant —
  no-attr, src=, async, multi-tag, mixed-attribute-order;
  idempotent on re-application; tags like <scripts> /
  <scripting> NOT incorrectly matched (regex boundary check).
- TestXi18SendHtmlContract:       `_send_html` generates a fresh
  nonce per call, injects it into the HTML body, emits the
  strict CSP header carrying the matching nonce-X; consecutive
  calls produce DIFFERENT nonces.
- TestXi18LegacyPolicyPreserved:   The legacy `_CSP_POLICY`
  constant is unchanged (ξ.3 tests + JSON/file response paths
  still rely on it).
- TestXi18JsonResponsesUseLegacyCsp: `_send_security_headers()`
  without nonce arg still emits the legacy policy.

Pinning rationale: ξ.18 tightens the script-src CSP directive
from 'unsafe-inline' to per-request nonce. Drift in the nonce
injection or the policy build would silently re-open the XSS
surface that ξ.18 closes. The legacy `_CSP_POLICY` constant
stays so the ξ.3 contract tests remain green and the
non-HTML response paths (JSON, file, zip) keep their existing
defense-in-depth CSP.
"""

from __future__ import annotations


class TestXi18NonceGeneration:
    def test_returns_string(self):
        from scripts.web import Handler

        n = Handler._generate_nonce()
        assert isinstance(n, str)

    def test_minimum_entropy(self):
        # secrets.token_urlsafe(16) → 22-char base64-urlsafe string
        # = 128 bits of entropy. Pin the floor.
        from scripts.web import Handler

        n = Handler._generate_nonce()
        assert len(n) >= 22

    def test_fresh_per_call(self):
        # Two consecutive calls must produce different nonces (the
        # cryptographic generator). Defensive against any future
        # refactor that accidentally caches.
        from scripts.web import Handler

        a = Handler._generate_nonce()
        b = Handler._generate_nonce()
        assert a != b


class TestXi18CspWithNonce:
    def test_drops_unsafe_inline_from_script_src(self):
        from scripts.web import Handler

        policy = Handler._csp_with_nonce("ABCxyz")
        # script-src must NOT carry 'unsafe-inline' anymore.
        # Find the script-src directive substring; assert
        # 'unsafe-inline' is absent within it.
        # The directive is delimited by ';' so we slice on that.
        directives = {d.split(" ", 1)[0]: d for d in (s.strip() for s in policy.split(";"))}
        assert "script-src" in directives
        assert "'unsafe-inline'" not in directives["script-src"]

    def test_includes_nonce_in_script_src(self):
        from scripts.web import Handler

        nonce = "secret-nonce-value"
        policy = Handler._csp_with_nonce(nonce)
        assert f"'nonce-{nonce}'" in policy

    def test_style_src_keeps_unsafe_inline(self):
        # Tailwind compat — see core module docstring. Pin so a
        # future contributor who tightens script-src doesn't
        # accidentally tighten style-src and break the Play CDN.
        from scripts.web import Handler

        policy = Handler._csp_with_nonce("X")
        directives = {d.split(" ", 1)[0]: d for d in (s.strip() for s in policy.split(";"))}
        assert "'unsafe-inline'" in directives["style-src"]

    def test_other_directives_preserved(self):
        from scripts.web import Handler

        policy = Handler._csp_with_nonce("X")
        for required in (
            "default-src 'self'",
            "img-src 'self' data:",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ):
            assert required in policy, f"missing directive: {required!r}"

    def test_allows_tailwind_cdn(self):
        # The Tailwind CDN must still load — invariant I.1 prohibits
        # a build step, so the Play CDN is the canonical script
        # source. Pin it stays allow-listed.
        from scripts.web import Handler

        policy = Handler._csp_with_nonce("X")
        assert "https://cdn.tailwindcss.com" in policy


class TestXi18ScriptInjection:
    def test_no_attr_script_tag(self):
        from scripts.web import Handler

        out = Handler._inject_script_nonces("<script>doStuff()</script>", "X")
        assert '<script nonce="X">' in out

    def test_src_attr_script_tag(self):
        from scripts.web import Handler

        out = Handler._inject_script_nonces('<script src="https://cdn.tailwindcss.com"></script>', "X")
        assert '<script nonce="X" src="https://cdn.tailwindcss.com">' in out

    def test_async_attr_script_tag(self):
        from scripts.web import Handler

        out = Handler._inject_script_nonces('<script async src="x.js"></script>', "X")
        assert '<script nonce="X" async src="x.js">' in out

    def test_multiple_script_tags_all_get_nonce(self):
        from scripts.web import Handler

        html = "<script>a</script><script>b</script><script src='c.js'></script>"
        out = Handler._inject_script_nonces(html, "ABC")
        assert out.count('nonce="ABC"') == 3

    def test_internal_whitespace_preserved(self):
        from scripts.web import Handler

        # Multi-line <script tag — common in templates.
        html = '<script\n  src="x.js"></script>'
        out = Handler._inject_script_nonces(html, "X")
        # Nonce inserted right after `<script`, before the newline.
        assert '<script nonce="X"\n  src="x.js">' in out

    def test_scripts_word_not_matched(self):
        # `<scripts>` is a hypothetical custom element; the regex
        # must NOT incorrectly add a nonce to it. (Boundary check.)
        from scripts.web import Handler

        html = "<scripts>data</scripts>"
        out = Handler._inject_script_nonces(html, "X")
        assert "nonce" not in out, "regex incorrectly matched <scripts>"

    def test_scripting_word_not_matched(self):
        from scripts.web import Handler

        html = "<scripting>foo</scripting>"
        out = Handler._inject_script_nonces(html, "X")
        assert "nonce" not in out

    def test_existing_nonce_not_duplicated(self):
        # Re-running the injection on already-noncified HTML must
        # not double-add the attribute.
        from scripts.web import Handler

        html = "<script>hello</script>"
        once = Handler._inject_script_nonces(html, "X")
        twice = Handler._inject_script_nonces(once, "X")
        # Only one nonce attr, not two.
        assert twice.count('nonce="X"') == 1
        # And no leftover bare `<script>` either.
        assert "<script>" not in twice.replace('<script nonce="X">', "")

    def test_real_exec_html_gets_nonces(self):
        # Sanity: the actual /exec template has multiple <script>
        # tags after design-system substitution. All must receive
        # nonces.
        from scripts.templates.exec import EXEC_HTML
        from scripts.web import Handler

        out = Handler._inject_script_nonces(EXEC_HTML, "TESTNONCE")
        # At least one script tag was present and got nonced.
        assert 'nonce="TESTNONCE"' in out
        # No bare `<script>` (with `>` immediately after) survives.
        # `<scripts>` is allowed; `<script src=` was nonced; `<script>`
        # was nonced. Search for the unnonced form.
        # (Use a regex compatible with the same boundary semantics.)
        import re

        bare_script_re = re.compile(r"<script(?![a-zA-Z0-9-_])(?! nonce=)")
        leftover = bare_script_re.findall(out)
        assert not leftover, f"some <script tags still lack nonce: {leftover[:3]}"


class TestXi18SendHtmlContract:
    """Smoke-test `_send_html` end-to-end using a fake handler."""

    def _fake_handler(self):
        """Build a minimal fake of the request-handler interface so we
        can drive `_send_html` without standing up a real socket."""
        from scripts.web import Handler

        captured = {"status": None, "headers": [], "body": b""}

        class Fake:
            send_response = lambda self, code: captured.__setitem__("status", code)  # noqa: E731

            def send_header(self, k, v):
                captured["headers"].append((k, v))

            def end_headers(self):
                pass

            class _Wfile:
                def write(self, b):
                    captured["body"] += b

            wfile = _Wfile()

        # Bind the Handler's methods to our Fake instance so `self`
        # resolves correctly.
        fake = Fake()
        fake._generate_nonce = Handler._generate_nonce
        fake._inject_script_nonces = Handler._inject_script_nonces
        fake._csp_with_nonce = Handler._csp_with_nonce
        fake._CSP_POLICY = Handler._CSP_POLICY
        fake._send_security_headers = Handler._send_security_headers.__get__(fake, type(fake))
        fake._send_html = Handler._send_html.__get__(fake, type(fake))
        return fake, captured

    def test_html_response_includes_nonce_in_body(self):
        fake, captured = self._fake_handler()
        fake._send_html("<html><body><script>x</script></body></html>")
        body_str = captured["body"].decode("utf-8")
        assert "<script nonce=" in body_str

    def test_csp_header_contains_matching_nonce(self):
        fake, captured = self._fake_handler()
        fake._send_html("<html><body><script>x</script></body></html>")
        body_str = captured["body"].decode("utf-8")
        # Extract nonce from body.
        import re

        m = re.search(r'<script nonce="([^"]+)"', body_str)
        assert m, "no nonce in body"
        body_nonce = m.group(1)
        # The CSP header must reference the same value.
        csp_value = next(v for (k, v) in captured["headers"] if k == "Content-Security-Policy")
        assert f"'nonce-{body_nonce}'" in csp_value, "CSP nonce doesn't match body nonce"

    def test_consecutive_calls_use_different_nonces(self):
        fake1, captured1 = self._fake_handler()
        fake2, captured2 = self._fake_handler()
        fake1._send_html("<script>a</script>")
        fake2._send_html("<script>b</script>")
        import re

        nonce1 = re.search(r'<script nonce="([^"]+)"', captured1["body"].decode()).group(1)
        nonce2 = re.search(r'<script nonce="([^"]+)"', captured2["body"].decode()).group(1)
        assert nonce1 != nonce2

    def test_response_status_is_200(self):
        fake, captured = self._fake_handler()
        fake._send_html("<html></html>")
        assert captured["status"] == 200


class TestXi18LegacyPolicyPreserved:
    """ξ.3's `_CSP_POLICY` constant must remain unchanged — the
    JSON / file / zip response paths rely on it as their CSP."""

    def test_legacy_policy_still_unsafe_inline_for_compat(self):
        # The legacy policy is intentionally less strict — it's the
        # fallback for response types where we don't (or can't)
        # noncify. Pin that ξ.18 didn't accidentally tighten it.
        from scripts.web import Handler

        assert "'unsafe-inline'" in Handler._CSP_POLICY

    def test_legacy_policy_has_all_directives(self):
        # Defense in depth — ξ.3's contract.
        from scripts.web import Handler

        for required in (
            "default-src 'self'",
            "script-src",
            "style-src",
            "img-src",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ):
            assert required in Handler._CSP_POLICY


class TestXi18JsonResponsesUseLegacyCsp:
    """JSON / file / zip responses don't inject nonces (no inline
    scripts in those payloads); pin `_send_security_headers()` without
    a nonce kwarg still emits the legacy policy."""

    def test_no_nonce_kwarg_means_legacy_policy(self):
        from scripts.web import Handler

        captured = []

        class Fake:
            def send_header(self, k, v):
                captured.append((k, v))

        fake = Fake()
        fake._CSP_POLICY = Handler._CSP_POLICY
        fake._csp_with_nonce = Handler._csp_with_nonce
        Handler._send_security_headers(fake)
        csp = next(v for (k, v) in captured if k == "Content-Security-Policy")
        # Legacy policy carries 'unsafe-inline' on script-src.
        assert "'unsafe-inline'" in csp
        assert "nonce-" not in csp

    def test_explicit_none_means_legacy_policy(self):
        # Belt-and-braces: explicit `nonce=None` also triggers legacy.
        from scripts.web import Handler

        captured = []

        class Fake:
            def send_header(self, k, v):
                captured.append((k, v))

        fake = Fake()
        fake._CSP_POLICY = Handler._CSP_POLICY
        fake._csp_with_nonce = Handler._csp_with_nonce
        Handler._send_security_headers(fake, nonce=None)
        csp = next(v for (k, v) in captured if k == "Content-Security-Policy")
        assert "'unsafe-inline'" in csp
        assert "nonce-" not in csp

    def test_explicit_nonce_means_strict_policy(self):
        from scripts.web import Handler

        captured = []

        class Fake:
            def send_header(self, k, v):
                captured.append((k, v))

        fake = Fake()
        fake._CSP_POLICY = Handler._CSP_POLICY
        fake._csp_with_nonce = Handler._csp_with_nonce
        Handler._send_security_headers(fake, nonce="mytest")
        csp = next(v for (k, v) in captured if k == "Content-Security-Policy")
        assert "'nonce-mytest'" in csp
        # script-src no longer carries 'unsafe-inline'.
        sd_directives = {d.split(" ", 1)[0]: d for d in (s.strip() for s in csp.split(";"))}
        assert "'unsafe-inline'" not in sd_directives["script-src"]
