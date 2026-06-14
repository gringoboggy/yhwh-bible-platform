"""ω.27 follow-on (2026-05-11) — ξ.15 + ξ.16 + ξ.17 late-session
security cluster test classes, split out of the monolithic
``tests/test_scripts.py`` into a topic file alongside the other
ω.27 follow-on splits.

Ninth topic extraction. The late-session security hardening
cluster shipped three phases together:

- ξ.15  AI-output HTML sandbox — strict allowlist sanitizer for
        χ-AI-notes / χ-AI-xrefs output; companion safety phase to
        the χ-AI generation infrastructure
- ξ.16  security sweep — adversarial review findings (SSRF
        boundaries, multipart parser hardening, log redaction,
        rate-limit knobs, etc.)
- ξ.17  remaining security punch list — closing items from the
        2026-05-10 audit's SECURITY findings (the final cleanup
        before v1.0 ship)

The cluster is the closing arc of the v1.0 security hardening
push. Pairs with the earlier ξ.1/.2/.4 input-validation +
path-traversal + XSS-prevention foundations (which are still
in test_scripts.py — separately-shipped foundations that
don't share a cohesive late-session cluster).

Every class lazy-imports its dependencies inside test method
bodies, so this file has no top-level imports from the project.
"""

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------- Phase ξ.15 : AI-output HTML sandbox ----------------------


class TestXi15HtmlSandbox:
    """ξ.15 — strict HTML sandbox for AI-emitted note bodies.

    Threat model: the LLM hallucinates an unsafe construct in
    `comm-ai` draft prose at scale. The sandbox is a strict subset of
    publisher-grade `sanitize_html` — only em/strong/b/i/sup/sub/code/
    br/span/p and in-document anchors on <a> survive. Defense in
    depth: sandbox runs at detector emit-time AND at
    promote.promote_candidate before insertion.
    """

    # ---- module-level: function contract ----

    def test_empty_input_returns_empty(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        assert sandbox_ai_html("") == ""
        assert sandbox_ai_html(None) == ""  # type: ignore[arg-type]

    def test_idempotent(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        for payload in [
            "<em>plain</em>",
            "<script>alert(1)</script>hello",
            "<a href='#anchor'>x</a>",
            "<p>para <strong>bold</strong></p>",
        ]:
            once = sandbox_ai_html(payload)
            twice = sandbox_ai_html(once)
            assert once == twice

    # ---- XSS payload classes ----

    def test_script_tag_dropped_with_content(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        out = sandbox_ai_html("hello<script>alert(1)</script>world")
        assert "<script" not in out
        assert "alert(1)" not in out
        # Outer text survives
        assert "hello" in out
        assert "world" in out

    def test_iframe_dropped(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        out = sandbox_ai_html("<iframe src='https://evil.com'></iframe>safe")
        assert "<iframe" not in out
        assert "evil.com" not in out
        assert "safe" in out

    def test_javascript_url_on_anchor_rejected(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        out = sandbox_ai_html('<a href="javascript:alert(1)">click</a>')
        # The tag may survive but href must be stripped
        assert "javascript:" not in out
        assert "alert(1)" not in out
        # Inner text preserved
        assert "click" in out

    def test_javascript_url_with_whitespace_bypass_rejected(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        # Older browsers tolerate leading whitespace inside the scheme
        out = sandbox_ai_html("<a href='\tjavascript:alert(1)'>x</a>")
        assert "javascript:" not in out

    def test_data_url_rejected(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        out = sandbox_ai_html("<a href='data:text/html,<script>1</script>'>x</a>")
        assert "data:" not in out

    def test_vbscript_url_rejected(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        out = sandbox_ai_html("<a href='vbscript:msgbox 1'>x</a>")
        assert "vbscript:" not in out

    def test_on_event_handlers_stripped(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        for payload in [
            '<em onclick="alert(1)">x</em>',
            '<strong onerror="alert(1)">x</strong>',
            '<a href="#a" onmouseover="alert(1)">x</a>',
        ]:
            out = sandbox_ai_html(payload)
            assert "onclick" not in out
            assert "onerror" not in out
            assert "onmouseover" not in out
            assert "alert(1)" not in out

    def test_style_attribute_stripped(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        out = sandbox_ai_html('<em style="color:red">x</em>')
        assert "style=" not in out
        assert "color:red" not in out
        # Tag itself survives
        assert "<em" in out

    def test_object_embed_dropped(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        out1 = sandbox_ai_html("<object data='evil.swf'>fallback</object>")
        out2 = sandbox_ai_html("<embed src='evil.swf' />after")
        assert "<object" not in out1
        assert "evil.swf" not in out1
        assert "<embed" not in out2

    def test_form_input_dropped(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        out = sandbox_ai_html("<form action='evil.com'><input name='x' /></form>safe")
        assert "<form" not in out
        assert "<input" not in out
        assert "evil.com" not in out
        assert "safe" in out

    def test_doctype_stripped(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        out = sandbox_ai_html("<!DOCTYPE html><em>x</em>")
        assert "DOCTYPE" not in out
        assert "<em>x</em>" in out

    def test_html_comment_stripped(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        out = sandbox_ai_html("<!-- malicious --><em>x</em>")
        assert "malicious" not in out
        assert "<em>x</em>" in out

    def test_conditional_comment_with_script_stripped(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        out = sandbox_ai_html("<!--[if IE]><script>alert(1)</script><![endif]--><em>x</em>")
        assert "alert(1)" not in out
        assert "<script" not in out

    # ---- AI allowlist (narrower than publisher sanitize) ----

    def test_allowed_inline_tags_preserved(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        for tag in ("em", "strong", "b", "i", "sup", "sub", "code", "span"):
            out = sandbox_ai_html(f"<{tag}>x</{tag}>")
            assert f"<{tag}>x</{tag}>" == out

    def test_allowed_block_paragraph_preserved(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        out = sandbox_ai_html("<p>hello</p>")
        assert out == "<p>hello</p>"

    def test_void_br_preserved(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        out = sandbox_ai_html("a<br />b")
        assert "<br" in out
        assert "a" in out
        assert "b" in out

    def test_publisher_tags_outside_ai_allowlist_dropped(self):
        # h1-h6, table, blockquote, ul, ol, li — allowed by sanitize_html
        # for publisher content but NOT in the AI allowlist (too much
        # surface area for the model to hallucinate misuse).
        from scripts.core.html_sandbox import sandbox_ai_html

        for tag in ("h1", "h2", "blockquote", "ul", "ol", "li", "table", "tr", "td"):
            out = sandbox_ai_html(f"<{tag}>inner</{tag}>")
            assert f"<{tag}" not in out
            assert "inner" in out  # content preserved

    def test_anchor_with_in_doc_href_preserved(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        out = sandbox_ai_html('<a href="#xref-1">see</a>')
        assert 'href="#xref-1"' in out
        assert "see" in out

    def test_anchor_with_relative_path_preserved(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        out = sandbox_ai_html('<a href="notes/gen-1.html#x">see</a>')
        assert "notes/gen-1.html#x" in out

    def test_anchor_with_external_http_url_rejected(self):
        # AI surface is stricter than publisher: no http/https/mailto
        # external links. The model has no business linking out.
        from scripts.core.html_sandbox import sandbox_ai_html

        for url in ("http://example.com", "https://example.com", "mailto:a@b.com", "tel:+1"):
            out = sandbox_ai_html(f'<a href="{url}">x</a>')
            assert url not in out
            assert "<a" in out  # tag survives
            assert "x" in out  # text survives

    def test_anchor_with_protocol_relative_url_rejected(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        out = sandbox_ai_html('<a href="//evil.com/x">x</a>')
        assert "evil.com" not in out

    def test_target_attr_stripped(self):
        # Publisher allowlist allows target="_blank"; AI surface drops
        # it (no need for new-window opens in note prose).
        from scripts.core.html_sandbox import sandbox_ai_html

        out = sandbox_ai_html('<a href="#x" target="_blank">x</a>')
        assert "target=" not in out

    def test_dir_and_title_attrs_stripped(self):
        # Narrower global attrs than publisher: only class/lang/id.
        from scripts.core.html_sandbox import sandbox_ai_html

        out = sandbox_ai_html('<em dir="rtl" title="hint">x</em>')
        assert "dir=" not in out
        assert "title=" not in out

    def test_class_lang_id_preserved(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        out = sandbox_ai_html('<em class="hl" lang="grc" id="t1">x</em>')
        assert 'class="hl"' in out
        assert 'lang="grc"' in out
        assert 'id="t1"' in out

    def test_id_with_unsafe_chars_sanitized(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        out = sandbox_ai_html('<em id="a;b<c">x</em>')
        # Unsafe chars stripped; safe portion kept
        assert 'id="abc"' in out

    def test_img_dropped(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        out = sandbox_ai_html('<img src="evil.png" onerror="alert(1)">x')
        assert "<img" not in out
        assert "evil.png" not in out
        assert "alert(1)" not in out

    def test_media_tags_dropped(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        for payload in [
            "<video src='evil.mp4'>fallback</video>after",
            "<audio src='evil.mp3'></audio>after",
        ]:
            out = sandbox_ai_html(payload)
            assert "<video" not in out
            assert "<audio" not in out
            assert "evil." not in out
            assert "after" in out

    def test_text_passes_through(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        out = sandbox_ai_html("plain prose with no markup")
        assert out == "plain prose with no markup"

    def test_text_special_chars_escaped(self):
        from scripts.core.html_sandbox import sandbox_ai_html

        out = sandbox_ai_html("a < b & c > d")
        assert "&lt;" in out
        assert "&amp;" in out
        assert "&gt;" in out

    # ---- subset invariant relative to publisher sanitize ----

    def test_sandbox_output_is_subset_of_publisher_output(self):
        # The invariant: sandbox_ai_html(x) only contains tags also
        # present in sanitize_html(x). Stronger phrasing of "AI sandbox
        # is strictly tighter than publisher sanitize."
        import re

        from scripts.core.html_sanitize import sanitize_html
        from scripts.core.html_sandbox import sandbox_ai_html

        payloads = [
            "<em>x</em>",
            "<a href='#a'>x</a>",
            "<h1>x</h1>",
            "<table><tr><td>x</td></tr></table>",
            "<p>x</p><blockquote>y</blockquote>",
        ]
        tag_re = re.compile(r"<\s*([a-zA-Z][a-zA-Z0-9]*)\b")
        for p in payloads:
            pub_tags = set(tag_re.findall(sanitize_html(p)))
            ai_tags = set(tag_re.findall(sandbox_ai_html(p)))
            assert ai_tags.issubset(pub_tags), f"{p}: ai={ai_tags} pub={pub_tags}"

    # ---- AINoteDetector integration ----

    def _make_detector_with_draft(self, draft):
        """Stub client mirroring AnthropicNoteClient surface."""
        from scripts.core.detectors import AINoteDetector

        class StubClient:
            attribution = "AI: stub"

            def draft_note(self, *a, **kw):
                return draft

        return AINoteDetector(client=StubClient(), min_confidence=0.0)

    def test_detector_sandboxes_body_html(self):
        det = self._make_detector_with_draft(
            {
                "kind_class": "explanatory",
                "label": "Term",
                "body_html": "<script>alert(1)</script>real text",
                "confidence": 0.9,
                "reviewer_flags": [],
            }
        )
        cands = det.detect("gen", 1, 1, "verse text")
        assert len(cands) == 1
        body = cands[0].draft_body
        assert "<script" not in body
        assert "alert(1)" not in body
        assert "real text" in body

    def test_detector_sandboxes_label(self):
        det = self._make_detector_with_draft(
            {
                "kind_class": "explanatory",
                "label": "<script>alert(1)</script>Term",
                "body_html": "body",
                "confidence": 0.9,
                "reviewer_flags": [],
            }
        )
        cands = det.detect("gen", 1, 1, "verse text")
        assert len(cands) == 1
        body = cands[0].draft_body
        assert "<script" not in body
        assert "alert(1)" not in body
        assert "Term" in body

    def test_detector_strips_javascript_href_from_body(self):
        det = self._make_detector_with_draft(
            {
                "kind_class": "explanatory",
                "label": "L",
                "body_html": '<a href="javascript:alert(1)">click</a>',
                "confidence": 0.9,
                "reviewer_flags": [],
            }
        )
        cands = det.detect("gen", 1, 1, "verse text")
        body = cands[0].draft_body
        assert "javascript:" not in body
        assert "alert(1)" not in body
        assert "click" in body

    def test_detector_preserves_allowed_inline_tags(self):
        det = self._make_detector_with_draft(
            {
                "kind_class": "explanatory",
                "label": "Term",
                "body_html": "<em>nuance</em> and <strong>weight</strong>",
                "confidence": 0.9,
                "reviewer_flags": [],
            }
        )
        cands = det.detect("gen", 1, 1, "verse text")
        body = cands[0].draft_body
        assert "<em>nuance</em>" in body
        assert "<strong>weight</strong>" in body

    def test_detector_emits_candidate_even_when_body_fully_sandboxed(self):
        # An AI body that is ENTIRELY hostile (e.g. only <script> +
        # iframe) sandboxes to empty. Detector still emits the
        # candidate so the reviewer queue surfaces it for inspection
        # rather than silently swallowing.
        det = self._make_detector_with_draft(
            {
                "kind_class": "explanatory",
                "label": "L",
                "body_html": "<script>1</script><iframe></iframe>",
                "confidence": 0.9,
                "reviewer_flags": [],
            }
        )
        cands = det.detect("gen", 1, 1, "verse text")
        assert len(cands) == 1
        # RX Phase 1: the editorial scaffold no longer ships in the body, but
        # the candidate is still emitted and the AI-generated reviewer flag
        # survives in reviewer_notes= even with an empty (fully-sandboxed) body.
        assert "[Reviewer:" not in cands[0].draft_body
        assert "AI-generated" in cands[0].reviewer_notes

    # ---- promote.promote_candidate belt-and-braces ----

    def test_promote_sandboxes_ai_drafted_kind_body(self, tmp_path, monkeypatch):
        # If a malicious body somehow reaches promote_candidate (e.g. a
        # candidate file that bypassed the detector's sandbox), the
        # second-pass at promote-time strips it before insertion.
        from scripts import promote

        # Set up a minimal book file
        book_path = tmp_path / "gen.py"
        book_path.write_text(
            "NOTES = (\n)\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(promote, "NOTES_DIR", tmp_path)

        captured = {}

        def fake_insert(path, ch, v, suffix, anchor, kind, title, label, body, *, attribution=None):
            captured["body"] = body
            return True

        monkeypatch.setattr(promote, "insert_note_into_book_file", fake_insert)
        monkeypatch.setattr(promote, "load_existing_anchors", lambda *a, **kw: [])
        monkeypatch.setattr(promote, "pick_free_suffix", lambda used: "a")

        cand = {
            "id": "gen-1-1-001",
            "chapter": 1,
            "verse": 1,
            "kind": "comm-ai",
            "anchor": "",
            "draft_title": "Note",
            "draft_label": "L",
            "draft_body": "<script>alert(1)</script><em>kept</em>",
            "source_attribution": "AI: stub",
        }
        ok, suffix = promote.promote_candidate("gen", cand)
        assert ok
        assert "<script" not in captured["body"]
        assert "alert(1)" not in captured["body"]
        assert "<em>kept</em>" in captured["body"]

    def test_promote_does_not_sandbox_non_ai_kind(self, tmp_path, monkeypatch):
        # Non-AI kinds use the publisher pipeline; their bodies are
        # not run through the AI-strict sandbox (which would mangle
        # legitimate publisher apparatus like <h2>, <ul>, etc.).
        from scripts import promote

        book_path = tmp_path / "gen.py"
        book_path.write_text("NOTES = (\n)\n", encoding="utf-8")
        monkeypatch.setattr(promote, "NOTES_DIR", tmp_path)

        captured = {}

        def fake_insert(path, ch, v, suffix, anchor, kind, title, label, body, *, attribution=None):
            captured["body"] = body
            return True

        monkeypatch.setattr(promote, "insert_note_into_book_file", fake_insert)
        monkeypatch.setattr(promote, "load_existing_anchors", lambda *a, **kw: [])
        monkeypatch.setattr(promote, "pick_free_suffix", lambda used: "a")

        cand = {
            "id": "gen-1-1-001",
            "chapter": 1,
            "verse": 1,
            "kind": "xref-citation",  # NOT in AI_DRAFTED_KINDS
            "anchor": "",
            "draft_title": "Cross-reference",
            "draft_label": "See",
            "draft_body": "<h2>Section</h2><ul><li>x</li></ul>",
            "source_attribution": "TSK",
        }
        ok, _ = promote.promote_candidate("gen", cand)
        assert ok
        # h2/ul/li are publisher-allowed; the sandbox would have
        # stripped them. The body must reach insert untouched.
        assert "<h2>" in captured["body"]
        assert "<ul>" in captured["body"]
        assert "<li>" in captured["body"]


# ---------- Phase ξ.16 : security sweep --------------------------------


class TestXi16Security:
    """ξ.16 — security sweep closing 5 audit findings.

    Pinned attack vectors:
      - SEC-001: SVG / wrong-extension served as image/svg+xml
      - SEC-002: 2 GB Content-Length DoS on JSON routes
      - SEC-002: oversized multipart per-part header
      - SEC-003: Host-header reflection in RSS feed
      - SEC-006: subprocess.run hangs forever on stuck build
      - SEC-007: empty / oversized multipart boundary
    """

    # ---- SEC-003 — RSS Host header reflection ----

    def test_rss_base_url_rejects_attacker_host(self, monkeypatch):
        from scripts.web import _safe_rss_base_url

        monkeypatch.delenv("YHWH_PUBLIC_BASE_URL", raising=False)
        # Attacker sends crafted Host header
        for evil in [
            "evil.com",
            "evil.com:80",
            "javascript:alert(1)",
            "//attacker.tld",
            "localhost.evil.com",
            "127.0.0.1.evil.com",
            "localhost\\evil.com",
            "localhost\nlocation: evil.com",
        ]:
            assert _safe_rss_base_url("http", evil) == "http://localhost"

    def test_rss_base_url_accepts_localhost_variants(self, monkeypatch):
        from scripts.web import _safe_rss_base_url

        monkeypatch.delenv("YHWH_PUBLIC_BASE_URL", raising=False)
        for ok_host in ["localhost", "localhost:8765", "127.0.0.1", "127.0.0.1:8000", "[::1]", "[::1]:443"]:
            base = _safe_rss_base_url("http", ok_host)
            assert base.endswith(ok_host), f"{ok_host!r} → {base!r}"
            assert base.startswith("http://")

    def test_rss_base_url_clamps_proto(self, monkeypatch):
        from scripts.web import _safe_rss_base_url

        monkeypatch.delenv("YHWH_PUBLIC_BASE_URL", raising=False)
        for evil_proto in ["javascript", "data", "vbscript", "file", "ftp", ""]:
            base = _safe_rss_base_url(evil_proto, "localhost")
            assert base == "http://localhost"
        # https stays https
        assert _safe_rss_base_url("https", "localhost") == "https://localhost"

    def test_rss_base_url_honors_configured_env(self, monkeypatch):
        from scripts.web import _safe_rss_base_url

        monkeypatch.setenv("YHWH_PUBLIC_BASE_URL", "https://bible.example.com/v1/")
        # Configured wins over evil host
        assert _safe_rss_base_url("http", "evil.com") == "https://bible.example.com/v1"

    def test_rss_base_url_configured_rejects_nonhttp_scheme(self, monkeypatch):
        # mint-11 audit: an operator-set base URL with a dangerous scheme must
        # NOT be syndicated verbatim (auto-navigating RSS readers could execute
        # `javascript:`/`data:`); fall back to http://localhost like the other
        # guards. A scheme-less or non-http(s) value is rejected too.
        from scripts.web import _safe_rss_base_url

        for bad in ["javascript:alert(1)", "data:text/html,x", "vbscript:x", "evil.com", "ftp://h/x"]:
            monkeypatch.setenv("YHWH_PUBLIC_BASE_URL", bad)
            assert _safe_rss_base_url("http", "localhost") == "http://localhost", bad
        # A legitimate https configured URL still passes (trailing slash stripped).
        monkeypatch.setenv("YHWH_PUBLIC_BASE_URL", "https://bible.example.com/v1/")
        assert _safe_rss_base_url("http", "evil.com") == "https://bible.example.com/v1"

    def test_rss_base_url_rejects_control_chars(self, monkeypatch):
        from scripts.web import _safe_rss_base_url

        monkeypatch.delenv("YHWH_PUBLIC_BASE_URL", raising=False)
        # Header injection — \r\n, NUL, tabs
        for payload in ["localhost\r\nLocation: evil.com", "localhost\x00", "localhost\t:80", "localhost ", "lo cal"]:
            assert _safe_rss_base_url("http", payload) == "http://localhost"

    # ---- SEC-007 — multipart boundary ----

    def test_extract_boundary_rejects_empty(self):
        from scripts.web import _extract_boundary

        assert _extract_boundary("multipart/form-data; boundary=") is None
        assert _extract_boundary('multipart/form-data; boundary=""') is None

    def test_extract_boundary_rejects_oversized(self):
        from scripts.web import _extract_boundary

        # RFC 2046 caps at 70 chars
        big = "x" * 71
        assert _extract_boundary(f"multipart/form-data; boundary={big}") is None
        # 70 is the legal max
        seventy = "x" * 70
        assert _extract_boundary(f"multipart/form-data; boundary={seventy}") == seventy.encode()

    def test_extract_boundary_rejects_control_chars(self):
        from scripts.web import _extract_boundary

        assert _extract_boundary("multipart/form-data; boundary=ab\x00cd") is None
        assert _extract_boundary("multipart/form-data; boundary=ab\rcd") is None

    def test_extract_boundary_accepts_normal(self):
        from scripts.web import _extract_boundary

        assert _extract_boundary("multipart/form-data; boundary=abc123") == b"abc123"

    # ---- SEC-002 — multipart per-part header cap ----

    def test_multipart_oversized_part_header_skipped(self):
        from scripts.web import _parse_multipart

        # Construct a part with a 16 KB header — past the 8 KB cap.
        oversized_header = b"X-Junk: " + (b"x" * 16384) + b"\r\n"
        body = (
            b"--BNDRY\r\n"
            + oversized_header
            + b'Content-Disposition: form-data; name="f"; filename="a.png"\r\n'
            + b"\r\n"
            + b"\x89PNG\r\n\x1a\nfile-bytes"
            + b"\r\n--BNDRY--\r\n"
        )
        parts = _parse_multipart(body, b"BNDRY")
        # Oversized headers cause the part to be skipped, not parsed
        assert len(parts) == 0

    def test_multipart_normal_part_still_works(self):
        from scripts.web import _parse_multipart

        body = (
            b"--BNDRY\r\n"
            b'Content-Disposition: form-data; name="f"; filename="a.png"\r\n'
            b"Content-Type: image/png\r\n"
            b"\r\n"
            b"\x89PNG\r\n\x1a\nfile-bytes"
            b"\r\n--BNDRY--\r\n"
        )
        parts = _parse_multipart(body, b"BNDRY")
        assert len(parts) == 1
        assert parts[0]["name"] == "f"
        assert parts[0]["filename"] == "a.png"
        assert parts[0]["data"].startswith(b"\x89PNG")

    # ---- SEC-002 — _read_body cap ----

    def test_read_body_rejects_oversized_content_length(self):
        # Construct a fake handler with the cap; verify no rfile read
        # is attempted when length exceeds cap.
        from scripts.web import Handler as EBibleHandler

        class FakeRfile:
            def read(self, n):
                # Reaching here means the cap was bypassed
                raise AssertionError(f"rfile.read({n}) was called despite over-cap length")

        class FakeHandler:
            JSON_BODY_MAX_BYTES = EBibleHandler.JSON_BODY_MAX_BYTES
            headers = {"Content-Length": str(EBibleHandler.JSON_BODY_MAX_BYTES + 1)}
            rfile = FakeRfile()

        # Bind the unbound method to the fake handler
        import pytest

        with pytest.raises(ValueError, match="too large"):
            EBibleHandler._read_body(FakeHandler())

    def test_read_body_rejects_invalid_content_length(self):
        from scripts.web import Handler as EBibleHandler

        class FakeRfile:
            def read(self, n):
                raise AssertionError("should not read")

        class FakeHandler:
            JSON_BODY_MAX_BYTES = EBibleHandler.JSON_BODY_MAX_BYTES
            headers = {"Content-Length": "abc"}
            rfile = FakeRfile()

        import pytest

        with pytest.raises(ValueError, match="invalid Content-Length"):
            EBibleHandler._read_body(FakeHandler())

    def test_read_body_rejects_negative_content_length(self):
        from scripts.web import Handler as EBibleHandler

        class FakeRfile:
            def read(self, n):
                raise AssertionError("should not read")

        class FakeHandler:
            JSON_BODY_MAX_BYTES = EBibleHandler.JSON_BODY_MAX_BYTES
            headers = {"Content-Length": "-1"}
            rfile = FakeRfile()

        import pytest

        with pytest.raises(ValueError, match="negative"):
            EBibleHandler._read_body(FakeHandler())

    def test_read_body_accepts_under_cap(self):
        from scripts.web import Handler as EBibleHandler

        payload = b'{"hello": "world"}'

        class FakeRfile:
            def __init__(self, p):
                self._p = p

            def read(self, n):
                assert n == len(self._p)
                return self._p

        class FakeHandler:
            JSON_BODY_MAX_BYTES = EBibleHandler.JSON_BODY_MAX_BYTES
            headers = {"Content-Length": str(len(payload))}
            rfile = FakeRfile(payload)

        result = EBibleHandler._read_body(FakeHandler())
        assert result == {"hello": "world"}

    def test_read_body_returns_empty_dict_on_zero_length(self):
        from scripts.web import Handler as EBibleHandler

        class FakeRfile:
            def read(self, n):
                raise AssertionError("should not read on length=0")

        class FakeHandler:
            JSON_BODY_MAX_BYTES = EBibleHandler.JSON_BODY_MAX_BYTES
            headers = {}
            rfile = FakeRfile()

        result = EBibleHandler._read_body(FakeHandler())
        assert result == {}

    # ---- SEC-001 — _send_file format/extension validation ----

    def test_send_file_rejects_svg_extension(self, tmp_path):
        # Even if a hostile .svg lands under content/covers/ (via
        # backup/restore, scenario import, hand placement), the
        # serving route must refuse to serve it.
        from scripts.web import Handler as EBibleHandler

        svg_file = tmp_path / "evil.svg"
        svg_file.write_bytes(b'<svg xmlns="..."><script>alert(1)</script></svg>')

        # Build a fake handler that captures the response status
        captured = {}

        class FakeHandler:
            wfile = type("W", (), {"write": lambda self, b: None})()

            def send_response(self, code):
                captured["status"] = code

            def send_header(self, k, v):
                captured.setdefault("headers", {})[k] = v

            def end_headers(self):
                pass

            def _send_json(self, payload, status=200):
                captured["json"] = payload
                captured["status"] = status

            def _send_security_headers(self):
                pass

        EBibleHandler._send_file(FakeHandler(), svg_file)
        # 415 = unsupported media type
        assert captured["status"] == 415
        assert "media type" in captured["json"]["error"].lower() or "unsupported" in captured["json"]["error"].lower()

    def test_send_file_rejects_extension_magic_mismatch(self, tmp_path):
        # PNG extension but JPEG bytes — refuse.
        from scripts.web import Handler as EBibleHandler

        f = tmp_path / "fake.png"
        f.write_bytes(b"\xff\xd8\xff\xe0fake-jpeg")  # JPEG magic

        captured = {}

        class FakeHandler:
            wfile = type("W", (), {"write": lambda self, b: None})()

            def send_response(self, code):
                captured["status"] = code

            def send_header(self, k, v):
                captured.setdefault("headers", {})[k] = v

            def end_headers(self):
                pass

            def _send_json(self, payload, status=200):
                captured["json"] = payload
                captured["status"] = status

            def _send_security_headers(self):
                pass

        EBibleHandler._send_file(FakeHandler(), f)
        assert captured["status"] == 415

    def test_send_file_serves_legitimate_png(self, tmp_path):
        from scripts.web import Handler as EBibleHandler

        f = tmp_path / "ok.png"
        # Real PNG magic + minimal payload
        f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

        captured = {}

        class FakeWfile:
            def write(self, b):
                captured["body_written"] = True

        class FakeHandler:
            wfile = FakeWfile()

            def send_response(self, code):
                captured["status"] = code

            def send_header(self, k, v):
                captured.setdefault("headers", {})[k] = v

            def end_headers(self):
                pass

            def _send_json(self, payload, status=200):
                captured["json_status"] = status
                captured["json_payload"] = payload

            def _send_security_headers(self):
                pass

        EBibleHandler._send_file(FakeHandler(), f)
        assert captured.get("status") == 200
        assert captured["headers"]["Content-Type"] == "image/png"
        assert captured["body_written"] is True
        # SEC-001 — the CSP sandbox header must be present
        assert "default-src 'none'" in captured["headers"]["Content-Security-Policy"]
        assert "sandbox" in captured["headers"]["Content-Security-Policy"]
        # SEC-010 — Cache-Control is private, not public
        assert "private" in captured["headers"]["Cache-Control"]
        assert "public" not in captured["headers"]["Cache-Control"]

    def test_send_file_rejects_gif_format(self, tmp_path):
        # GIF was in the old MIME map but isn't in
        # UPLOAD_ALLOWED_FORMATS. Refuse to serve.
        from scripts.web import Handler as EBibleHandler

        f = tmp_path / "anim.gif"
        f.write_bytes(b"GIF89a" + b"\x00" * 50)

        captured = {}

        class FakeHandler:
            wfile = type("W", (), {"write": lambda self, b: None})()

            def send_response(self, code):
                captured["status"] = code

            def send_header(self, k, v):
                captured.setdefault("headers", {})[k] = v

            def end_headers(self):
                pass

            def _send_json(self, payload, status=200):
                captured["status"] = status

            def _send_security_headers(self):
                pass

        EBibleHandler._send_file(FakeHandler(), f)
        assert captured["status"] == 415

    # ---- SEC-006 — subprocess timeout shape ----

    def test_api_export_build_translates_timeout_to_504(self, tmp_path, monkeypatch):
        # Verify the timeout path is wired correctly. Patch
        # subprocess.run directly (web.py imports it locally inside
        # api_export_build, so the global subprocess module is what
        # gets called).
        import subprocess

        from scripts import web

        def fake_run(cmd, **kw):
            raise subprocess.TimeoutExpired(cmd=cmd, timeout=kw.get("timeout", 0))

        monkeypatch.setattr(subprocess, "run", fake_run)
        # Stub out EXPORTS_DIR so the function can mkdir without
        # touching the real exports/ dir
        monkeypatch.setattr(web, "EXPORTS_DIR", tmp_path / "exports")
        result = web.api_export_build("ethiopian-tewahedo")
        assert result.get("error") == "build timed out"
        assert result.get("code") == "build_timeout"
        assert result.get("http") == 504
        assert result.get("timeout_seconds") >= 60


# ---------- Phase ξ.17 : remaining security punch list ------------------


class TestXi17Security:
    """ξ.17 — closes the 5 remaining audit findings from §1 of
    `dev/AUDIT_2026-05-10.md` that ξ.16 deferred:

      - SEC-008: Windows drive-letter explicit reject in
        `_resolve_content_path`
      - SEC-004: `cache_path` validation in `fetcher_config`
      - SEC-009: `python3` literals replaced with `sys.executable`
        across 9 dev scripts
      - SEC-011: YAML billion-laughs guard in
        `api_import_scenario_yaml`
      - SEC-005: audit-log integrity hash chain + redaction
    """

    # ---- SEC-008 — Windows drive-letter reject ----

    def test_resolve_content_path_rejects_drive_letter(self):
        from scripts.web import _resolve_content_path

        path, err = _resolve_content_path("C:\\Windows\\System32")
        assert path is None
        assert "drive-letter" in err.lower()

    def test_resolve_content_path_rejects_drive_relative(self):
        # `C:foo` is drive-relative on Windows — also rejected.
        from scripts.web import _resolve_content_path

        path, err = _resolve_content_path("C:foo.txt")
        assert path is None
        assert "drive-letter" in err.lower()

    def test_resolve_content_path_rejects_lowercase_drive(self):
        from scripts.web import _resolve_content_path

        path, err = _resolve_content_path("d:something")
        assert path is None

    def test_resolve_content_path_accepts_normal_relative(self):
        from scripts.web import _resolve_content_path

        # Normal relative path under content/ should still work
        path, err = _resolve_content_path("editions.yaml")
        # Either ok (resolves) or err is about file existence, not
        # the drive-letter rule
        assert err is None or "drive-letter" not in err.lower()

    # ---- SEC-004 — cache_path validation ----

    def test_fetcher_config_rejects_cache_path_with_separator(self):
        from scripts.core.fetcher_config import _validate_and_build, FetcherConfigError

        bad = {
            "version": 1,
            "sources": [
                {
                    "id": "test",
                    "name": "Test",
                    "cache_path": "../etc/passwd",
                    "license": "PD",
                    "required": True,
                    "candidates": [{"url": "https://example.com", "parser": "tsk-zip-tsv"}],
                }
            ],
        }
        try:
            _validate_and_build(bad)
        except FetcherConfigError as e:
            assert "cache_path" in str(e)
            return
        raise AssertionError("expected FetcherConfigError")

    def test_fetcher_config_rejects_cache_path_with_drive_letter(self):
        from scripts.core.fetcher_config import _validate_and_build, FetcherConfigError

        bad = {
            "version": 1,
            "sources": [
                {
                    "id": "test",
                    "name": "Test",
                    "cache_path": "C:evil",
                    "license": "PD",
                    "required": True,
                    "candidates": [{"url": "https://example.com", "parser": "tsk-zip-tsv"}],
                }
            ],
        }
        try:
            _validate_and_build(bad)
        except FetcherConfigError as e:
            assert "drive-letter" in str(e).lower() or "cache_path" in str(e)
            return
        raise AssertionError("expected FetcherConfigError")

    def test_fetcher_config_rejects_cache_path_with_backslash(self):
        from scripts.core.fetcher_config import _validate_and_build, FetcherConfigError

        bad = {
            "version": 1,
            "sources": [
                {
                    "id": "test",
                    "name": "Test",
                    "cache_path": "evil\\file.json",
                    "license": "PD",
                    "required": True,
                    "candidates": [{"url": "https://example.com", "parser": "tsk-zip-tsv"}],
                }
            ],
        }
        try:
            _validate_and_build(bad)
        except FetcherConfigError as e:
            assert "cache_path" in str(e)
            return
        raise AssertionError("expected FetcherConfigError")

    def test_fetcher_config_accepts_bare_filename(self):
        from scripts.core.fetcher_config import _validate_and_build

        ok = {
            "version": 1,
            "sources": [
                {
                    "id": "test",
                    "name": "Test",
                    "cache_path": "test_data.json",
                    "license": "PD",
                    "required": True,
                    "candidates": [{"url": "https://example.com", "parser": "tsk-zip-tsv"}],
                }
            ],
        }
        cfg = _validate_and_build(ok)
        assert len(cfg.sources) == 1

    # ---- SEC-009 — python3 literals replaced with sys.executable ----

    def test_no_python3_literal_in_handler_reachable_scripts(self):
        # Source-level pin: scripts that subprocess back into Python
        # use `sys.executable`, not the literal "python3" / 'python3'.

        scripts_dir = REPO_ROOT / "scripts"
        offenders = []
        for f in [
            "add_kind.py",
            "add_note.py",
            "build_edition.py",
            "bulk_edit.py",
            "run.py",
            "release.py",
            "verify.py",
        ]:
            p = scripts_dir / f
            if not p.is_file():
                continue
            text = p.read_text(encoding="utf-8")
            if '"python3"' in text or "'python3'" in text:
                offenders.append(f)
        assert offenders == [], f"python3 literal still present in: {offenders}"

    # ---- SEC-011 — YAML billion-laughs guard ----

    def test_scenario_yaml_rejects_high_anchor_density(self):
        from scripts.web import api_import_scenario_yaml

        # 100 anchors triggers the guard
        bomb = "&a " * 100 + "\n"
        result = api_import_scenario_yaml(yaml_text=bomb)
        assert result.get("code") == "yaml_anchor_density"
        assert result.get("http") == 400

    def test_scenario_yaml_rejects_high_alias_density(self):
        from scripts.web import api_import_scenario_yaml

        bomb = "*a " * 100 + "\n"
        result = api_import_scenario_yaml(yaml_text=bomb)
        assert result.get("code") == "yaml_anchor_density"

    def test_scenario_yaml_accepts_normal_yaml(self):
        from scripts.web import api_import_scenario_yaml

        # A scenario with zero anchors should pass through
        # (assuming other validation succeeds; we just need to
        # confirm the anchor guard doesn't fire).
        normal = "name: test\nenabled_kinds:\n  - comm\n  - word\n"
        result = api_import_scenario_yaml(yaml_text=normal)
        # If it errors, it must NOT be on yaml_anchor_density
        assert result.get("code") != "yaml_anchor_density"

    # ---- SEC-005 — audit-log integrity chain + redaction ----

    def test_audit_log_appends_prev_hash(self, tmp_path):
        from scripts.core import audit_log

        audit_log.append(endpoint="x", action="test", result="ok", base_dir=tmp_path)
        # Read the file directly and parse the line
        ndjson = next(tmp_path.glob("*.ndjson"))
        line = ndjson.read_text(encoding="utf-8").strip()
        entry = json.loads(line)
        assert "prev_hash" in entry
        # First line in a fresh log → genesis seed
        assert entry["prev_hash"] == "0" * 64

    def test_audit_log_chain_links_consecutive_entries(self, tmp_path):
        import hashlib

        from scripts.core import audit_log

        audit_log.append(endpoint="a", action="t1", result="ok", base_dir=tmp_path)
        audit_log.append(endpoint="b", action="t2", result="ok", base_dir=tmp_path)
        ndjson = next(tmp_path.glob("*.ndjson"))
        lines = [ln for ln in ndjson.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) == 2
        first_hash = hashlib.sha256(lines[0].encode("utf-8")).hexdigest()
        entry2 = json.loads(lines[1])
        assert entry2["prev_hash"] == first_hash

    def test_verify_chain_returns_ok_for_clean_log(self, tmp_path):
        from scripts.core import audit_log

        for i in range(5):
            audit_log.append(endpoint=f"e{i}", action="x", result="ok", base_dir=tmp_path)
        result = audit_log.verify_chain(base_dir=tmp_path)
        assert result["status"] == "ok"
        assert result["checked"] == 5
        assert result["first_break"] is None
        assert result["ungated_lines"] == 0

    def test_verify_chain_detects_tampering(self, tmp_path):
        from scripts.core import audit_log

        audit_log.append(endpoint="a", action="x", result="ok", base_dir=tmp_path)
        audit_log.append(endpoint="b", action="x", result="ok", base_dir=tmp_path)
        # Tamper with line 1 (rewrite history)
        ndjson = next(tmp_path.glob("*.ndjson"))
        lines = ndjson.read_text(encoding="utf-8").splitlines()
        # Change one byte of the first line — chain must break
        e0 = json.loads(lines[0])
        e0["endpoint"] = "TAMPERED"
        lines[0] = json.dumps(e0)
        ndjson.write_text("\n".join(lines) + "\n", encoding="utf-8")

        result = audit_log.verify_chain(base_dir=tmp_path)
        assert result["status"] == "broken"
        assert result["first_break"] is not None
        assert result["first_break"]["line_number"] == 2

    def test_verify_chain_handles_pre_xi17_lines(self, tmp_path):
        # A line without prev_hash (pre-ξ.17 history) is counted but
        # not treated as a break.
        from scripts.core import audit_log

        ndjson = tmp_path / "2026-05.ndjson"
        ndjson.write_text(
            json.dumps({"endpoint": "old", "action": "pre-ξ.17"}) + "\n",
            encoding="utf-8",
        )
        # Now append one new line — chain seeds from old line's hash
        audit_log.append(endpoint="new", action="post", result="ok", base_dir=tmp_path)

        result = audit_log.verify_chain(base_dir=tmp_path)
        assert result["status"] == "ok"
        assert result["checked"] == 2
        assert result["ungated_lines"] == 1

    def test_verify_chain_continuous_across_month_rollover(self, tmp_path):
        # Regression (mint-10): a new month's first line must chain to the
        # PRIOR month's last line, not the genesis seed. verify_chain carries
        # its expected hash *across* monthly files, so a genesis-seeded
        # rollover used to read "broken". _last_line_hash now falls back to
        # the most-recent prior monthly sibling when this month's file
        # doesn't exist yet.
        import hashlib
        from datetime import datetime, timezone

        from scripts.core import audit_log

        may = datetime(2026, 5, 31, 12, 0, 0, tzinfo=timezone.utc)
        jun = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
        audit_log.append(endpoint="a", action="x", result="ok", base_dir=tmp_path, when=may)
        audit_log.append(endpoint="b", action="x", result="ok", base_dir=tmp_path, when=jun)

        # Two separate monthly files were written (the rollover happened).
        assert sorted(p.name for p in tmp_path.glob("*.ndjson")) == [
            "2026-05.ndjson",
            "2026-06.ndjson",
        ]

        # June's first prev_hash == sha256 of May's last line (continuous chain).
        may_last = [ln for ln in (tmp_path / "2026-05.ndjson").read_text(encoding="utf-8").splitlines() if ln.strip()][
            -1
        ]
        jun_first = json.loads(
            [ln for ln in (tmp_path / "2026-06.ndjson").read_text(encoding="utf-8").splitlines() if ln.strip()][0]
        )
        assert jun_first["prev_hash"] == hashlib.sha256(may_last.encode("utf-8")).hexdigest()

        # The whole chain verifies across the rollover.
        result = audit_log.verify_chain(base_dir=tmp_path)
        assert result["status"] == "ok"
        assert result["checked"] == 2
        assert result["first_break"] is None

    def test_audit_log_redacts_sensitive_kwargs(self, tmp_path):
        from scripts.core import audit_log

        @audit_log.audit_endpoint(action="login")
        def fake_login(*, username, api_key, password, token):
            return {"ok": True}

        # Override the audit dir for this test by patching the module
        original = audit_log._audit_dir
        audit_log._audit_dir = lambda: tmp_path
        try:
            fake_login(username="alice", api_key="sk-abc-123", password="hunter2", token="t-deadbeef")
        finally:
            audit_log._audit_dir = original

        ndjson = next(tmp_path.glob("*.ndjson"))
        text = ndjson.read_text(encoding="utf-8")
        # Sensitive values must NOT appear
        assert "sk-abc-123" not in text
        assert "hunter2" not in text
        assert "t-deadbeef" not in text
        # Non-sensitive values DO appear
        assert "alice" in text
        # The redaction marker is present
        assert "[REDACTED]" in text

    def test_audit_log_redacts_sensitive_positional_args(self, tmp_path):
        # Hardening (laundry P1): _summarize_args redacted only kwargs, so a
        # secret passed POSITIONALLY (e.g. api_auth_totp_confirm's payload, or any
        # future positional-string secret) would log in the clear. Redact by the
        # wrapped function's PARAM NAME, not just keyword name.
        from scripts.core import audit_log

        @audit_log.audit_endpoint(action="totp")
        def fake_confirm(username, secret, token):
            return {"ok": True}

        original = audit_log._audit_dir
        audit_log._audit_dir = lambda: tmp_path
        try:
            fake_confirm("alice", "JBSWY3DPEHPK3PXP", "t-deadbeef")  # all POSITIONAL
        finally:
            audit_log._audit_dir = original

        text = next(tmp_path.glob("*.ndjson")).read_text(encoding="utf-8")
        assert "JBSWY3DPEHPK3PXP" not in text  # positional secret redacted
        assert "t-deadbeef" not in text  # positional token redacted
        assert "alice" in text  # non-sensitive positional kept
        assert "[REDACTED]" in text


class TestG2PreviewSanitizesNoteBody:
    """G2 / B2a.7 — the /preview render path MUST sanitize note bodies.

    `preview._render_note_aside` interpolated the note ``body`` into HTML
    **unescaped** (a "publisher-trusted" comment that the deep audit
    refuted — AI-authored bodies share the same note store, and the route
    `GET /api/preview` is reachable UNAUTHENTICATED). It must mirror the
    build-path sanitizer (`inject.build_aside` → `sanitize_html`), which
    whitelists inline markup and strips `<script>`, `on*` handlers, etc.
    Note tuple layout: (ch, v, suffix, anchor, kind, label, title, body, attr).
    """

    def test_script_tag_in_body_is_stripped(self):
        from scripts.core.preview import _render_note_aside

        note = (1, 1, "", "", "comm", "Label", "Title", "<script>alert(1)</script><em>ok</em>", "Attr")
        out = _render_note_aside(note, 0, "*")
        assert "<script" not in out.lower(), "preview must strip <script> from note bodies"
        assert "alert(1)" not in out, "sanitize_html drops <script> content, not just the tag"
        assert "<em>ok</em>" in out, "whitelisted inline markup must survive"

    def test_event_handler_attribute_is_stripped(self):
        from scripts.core.preview import _render_note_aside

        note = (1, 1, "", "", "comm", "Label", "Title", '<a href="#" onclick="evil()">x</a>', "Attr")
        out = _render_note_aside(note, 0, "*")
        assert "onclick" not in out.lower(), "preview must strip on* event-handler attributes"


class TestG1SchemeAllowlist:
    """G1 / B2a.12 — the egress SSRF guard must enforce a SCHEME allowlist.

    `_check_allowlist` returned (allowed) when the URL had no host, so
    `file:///etc/passwd` bypassed the guard entirely → local-file read
    (LFI). The fix adds a positive `{http, https}` scheme allowlist that
    runs BEFORE the host-membership check, so a disallowed scheme can
    never slip through via an allowlisted host.
    """

    def test_file_scheme_blocked(self):
        from scripts.core.http import SSRFBlockedError, _check_allowlist

        try:
            _check_allowlist("file:///etc/passwd", {"data.example.com"})
        except SSRFBlockedError:
            return
        raise AssertionError("file:// must be blocked by the scheme allowlist")

    def test_non_http_scheme_blocked_even_with_allowlisted_host(self):
        from scripts.core.http import SSRFBlockedError, _check_allowlist

        # The host IS allowlisted, but ftp is not an allowed scheme — the
        # scheme check must fire first.
        try:
            _check_allowlist("ftp://data.example.com/x", {"data.example.com"})
        except SSRFBlockedError:
            return
        raise AssertionError("non-http(s) scheme must be blocked before the host check")

    def test_hostless_http_blocked(self):
        from scripts.core.http import SSRFBlockedError, _check_allowlist

        try:
            _check_allowlist("http:///nohost", {"data.example.com"})
        except SSRFBlockedError:
            return
        raise AssertionError("hostless http URL must be blocked")

    def test_allowlisted_https_host_still_allowed(self):
        from scripts.core.http import _check_allowlist

        # Regression: legitimate https egress to an allowlisted host (and a
        # subdomain) must still pass without raising.
        _check_allowlist("https://data.example.com/file.json", {"data.example.com"})
        _check_allowlist("https://cdn.data.example.com/x", {"data.example.com"})

    def test_offlist_host_still_blocked(self):
        from scripts.core.http import SSRFBlockedError, _check_allowlist

        try:
            _check_allowlist("https://evil.com/x", {"data.example.com"})
        except SSRFBlockedError:
            return
        raise AssertionError("off-allowlist host must still be blocked")


class TestCheckA11yRunAll:
    """★C2.deadchecks — check_a11y.run_all() exposes the standard meta-tool
    contract ({checks, summary}) so the WCAG/EPUB-accessibility audit can be
    composed into /preflight (it was a built-but-uninvoked dead check). The
    function is behavioral: it must FLAG real violations and stay clean on a
    conformant or empty build."""

    def test_returns_standard_meta_tool_shape(self, tmp_path):
        from scripts.check_a11y import run_all

        result = run_all(epub_dir=tmp_path)
        assert set(result) == {"checks", "summary"}
        for c in result["checks"]:
            assert {"id", "name", "status", "message", "violations"} <= set(c)
            assert c["status"] in ("pass", "warn", "fail")
        s = result["summary"]
        assert {"total", "pass", "warn", "fail", "clean"} <= set(s)

    def test_empty_dir_is_all_pass(self, tmp_path):
        from scripts.check_a11y import run_all

        # No built EPUB → nothing to audit → no spurious red on a clean tree.
        result = run_all(epub_dir=tmp_path)
        assert result["summary"]["fail"] == 0
        assert result["summary"]["warn"] == 0

    def test_flags_missing_lang_and_alt_text(self, tmp_path):
        from scripts.check_a11y import run_all

        # A page with no <html lang> and an <img> without alt — both ERROR-
        # severity → must surface as 'fail' with violations.
        (tmp_path / "bad.html").write_text("<html><body><img src='x.png'><p>hi</p></body></html>", encoding="utf-8")
        result = run_all(epub_dir=tmp_path)
        by_id = {c["id"]: c for c in result["checks"]}
        assert by_id["lang"]["status"] == "fail"
        assert by_id["lang"]["violations"]
        assert by_id["alt-text"]["status"] == "fail"
        assert by_id["alt-text"]["violations"]
        assert result["summary"]["fail"] >= 2

    def test_conformant_page_passes_lang_and_alt(self, tmp_path):
        from scripts.check_a11y import run_all

        (tmp_path / "ok.html").write_text(
            '<html lang="en"><body><img src="x.png" alt="A figure"><p>hi</p></body></html>',
            encoding="utf-8",
        )
        result = run_all(epub_dir=tmp_path)
        by_id = {c["id"]: c for c in result["checks"]}
        assert by_id["lang"]["status"] == "pass"
        assert by_id["alt-text"]["status"] == "pass"
