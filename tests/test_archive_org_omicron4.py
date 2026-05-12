"""ο.4 — archive.org auto-upload pins (2026-05-11).

Month 5 #7 (closes Month 5). Composes ε.7 press-kit ZIP +
archive.org S3-style PUT + ε.6 distribution mark side-effect.

All upload paths use injectable `http_fn` so no test ever touches
the real network. Distribution + press-kit state files are
monkeypatched to tmp_path so production JSON is never touched.

Coverage:
- TestOmicron4Constants:           ENV_ACCESS_KEY / ENV_SECRET_KEY /
  DISTRIBUTION_CHANNEL / IDENTIFIER_PREFIX_DEFAULT pinned.
- TestOmicron4IsConfigured:         True/False based on env vars;
  whitespace-only treated as unconfigured.
- TestOmicron4SanitizeIdentifier:   prefix applied; invalid chars
  collapsed; empty input falls back; long input trimmed.
- TestOmicron4MetadataHeaders:      title/description/mediatype
  pinned; newlines stripped from values; falls back when blurbs
  empty.
- TestOmicron4UploadPressKit:        injects http_fn → returns
  ok:True envelope on 2xx; ok:False on 4xx; ok:False on exception
  raised by http_fn (network failure); identifier + URL shape
  pinned; raises RuntimeError when credentials missing.
- TestOmicron4ApiStatus:             returns configured flag +
  env-var names + identifier prefix.
- TestOmicron4ApiUpload:             missing-credentials → 503
  envelope; unknown-edition → 404 envelope; happy path runs full
  composition (build_zip + upload + distribution.mark_shipped);
  upload failure surfaces but distribution is NOT marked;
  distribution side-effect failure surfaces in envelope but
  upload itself is reported successful.
- TestOmicron4ExecTemplate:          archive-org banner + upload
  button present in EXEC_HTML; references the right endpoints.
- TestOmicron4RouteRegistration:     GET /api/archive-org/status in
  _SIMPLE_GET_ROUTES; POST /api/archive-org/upload/<edition> in
  _POST_ROUTES with correct handler binding.
- TestOmicron4HttpPutHelper:         scripts.core.http.put exposes
  retry semantics + accepts injected urlopen.
"""

from __future__ import annotations

import io
import json
import urllib.error
import urllib.request
import zipfile

import pytest


def _isolate_distribution(monkeypatch, tmp_path):
    from scripts.core import distribution

    p = tmp_path / "distribution.json"
    monkeypatch.setattr(distribution, "_distribution_path", lambda: p)
    return p


def _isolate_press_kit(monkeypatch, tmp_path):
    from scripts.core import press_kit

    p = tmp_path / "press_kit.json"
    monkeypatch.setattr(press_kit, "_press_kit_path", lambda: p)
    return p


def _set_creds(monkeypatch):
    from scripts.core import archive_org

    monkeypatch.setenv(archive_org.ENV_ACCESS_KEY, "test-access")
    monkeypatch.setenv(archive_org.ENV_SECRET_KEY, "test-secret")


def _clear_creds(monkeypatch):
    from scripts.core import archive_org

    monkeypatch.delenv(archive_org.ENV_ACCESS_KEY, raising=False)
    monkeypatch.delenv(archive_org.ENV_SECRET_KEY, raising=False)


# --------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------


class TestOmicron4Constants:
    def test_env_var_names_pinned(self):
        from scripts.core import archive_org

        # Pin so the api layer + UI status surface agree on the
        # exact variable names the publisher needs to set.
        assert archive_org.ENV_ACCESS_KEY == "EBIBLE_ARCHIVE_ORG_ACCESS_KEY"
        assert archive_org.ENV_SECRET_KEY == "EBIBLE_ARCHIVE_ORG_SECRET_KEY"

    def test_distribution_channel_matches_epsilon_6(self):
        from scripts.core import archive_org, distribution

        assert archive_org.DISTRIBUTION_CHANNEL == "archive_org"
        assert archive_org.DISTRIBUTION_CHANNEL in distribution.DISTRIBUTION_CHANNELS

    def test_identifier_prefix_default(self):
        from scripts.core import archive_org

        # Default prefix pinned so identifiers stay stable across
        # uploads (archive.org identifiers must NOT change after
        # publication).
        assert archive_org.IDENTIFIER_PREFIX_DEFAULT == "yhwh-bible-"

    def test_s3_base_url(self):
        from scripts.core import archive_org

        assert archive_org.ARCHIVE_S3_BASE == "https://s3.us.archive.org"


# --------------------------------------------------------------------
# is_configured
# --------------------------------------------------------------------


class TestOmicron4IsConfigured:
    def test_true_when_both_vars_set(self, monkeypatch):
        from scripts.core import archive_org

        _set_creds(monkeypatch)
        assert archive_org.is_configured() is True

    def test_false_when_either_missing(self, monkeypatch):
        from scripts.core import archive_org

        _clear_creds(monkeypatch)
        monkeypatch.setenv(archive_org.ENV_ACCESS_KEY, "only-access")
        assert archive_org.is_configured() is False
        monkeypatch.delenv(archive_org.ENV_ACCESS_KEY)
        monkeypatch.setenv(archive_org.ENV_SECRET_KEY, "only-secret")
        assert archive_org.is_configured() is False

    def test_whitespace_only_treated_as_unset(self, monkeypatch):
        from scripts.core import archive_org

        monkeypatch.setenv(archive_org.ENV_ACCESS_KEY, "   ")
        monkeypatch.setenv(archive_org.ENV_SECRET_KEY, "valid")
        assert archive_org.is_configured() is False


# --------------------------------------------------------------------
# sanitize_identifier
# --------------------------------------------------------------------


class TestOmicron4SanitizeIdentifier:
    def test_applies_default_prefix(self):
        from scripts.core import archive_org

        assert archive_org.sanitize_identifier("catholic-study") == "yhwh-bible-catholic-study"

    def test_invalid_chars_collapsed(self):
        from scripts.core import archive_org

        assert archive_org.sanitize_identifier("Hello World! 2026") == "yhwh-bible-hello-world-2026"

    def test_empty_falls_back(self):
        from scripts.core import archive_org

        assert archive_org.sanitize_identifier("") == "yhwh-bible-untitled"

    def test_long_input_trimmed_to_100(self):
        from scripts.core import archive_org

        ident = archive_org.sanitize_identifier("x" * 200)
        assert len(ident) <= 100

    def test_min_length_when_no_prefix(self):
        from scripts.core import archive_org

        # Edge case — caller supplies empty prefix + short slug.
        # Result must still be ≥5 chars per archive.org rules.
        ident = archive_org.sanitize_identifier("a", prefix="")
        assert len(ident) >= 5


# --------------------------------------------------------------------
# Metadata headers
# --------------------------------------------------------------------


class TestOmicron4MetadataHeaders:
    def test_title_and_description_pinned(self):
        from scripts.core import archive_org

        edition = {"id": "x", "title": "Catholic Study Bible"}
        blurbs = {"blurb_500": "Long description.", "blurb_150": "Short."}
        headers = archive_org.build_metadata_headers(edition, blurbs)
        assert headers["x-archive-meta-title"] == "Catholic Study Bible"
        assert headers["x-archive-meta-description"] == "Long description."

    def test_falls_back_to_blurb_150_then_default(self):
        from scripts.core import archive_org

        edition = {"id": "x", "title": "X"}
        # No blurb_500.
        headers = archive_org.build_metadata_headers(edition, {"blurb_150": "Short."})
        assert headers["x-archive-meta-description"] == "Short."
        # Empty blurbs → synthetic description from title.
        headers2 = archive_org.build_metadata_headers(edition, {})
        assert "X" in headers2["x-archive-meta-description"]

    def test_newlines_stripped(self):
        from scripts.core import archive_org

        edition = {"id": "x", "title": "Multi\r\nLine\tTitle"}
        headers = archive_org.build_metadata_headers(edition, {})
        # No CR/LF/tab in the final header value.
        for ch in ("\r", "\n", "\t"):
            assert ch not in headers["x-archive-meta-title"]

    def test_required_fields_present(self):
        from scripts.core import archive_org

        headers = archive_org.build_metadata_headers({"id": "x", "title": "X"}, {})
        for required in (
            "x-archive-meta-title",
            "x-archive-meta-description",
            "x-archive-meta-mediatype",
            "x-archive-meta-collection",
            "x-archive-meta-language",
            "x-archive-meta-creator",
            "x-archive-meta-licenseurl",
        ):
            assert required in headers, f"missing {required!r}"
        assert headers["x-archive-meta-mediatype"] == "texts"


# --------------------------------------------------------------------
# upload_press_kit (core)
# --------------------------------------------------------------------


class TestOmicron4UploadPressKit:
    def test_happy_path_returns_ok_envelope(self, monkeypatch):
        from scripts.core import archive_org

        _set_creds(monkeypatch)
        captured = {}

        def fake_http(url, body, headers):
            captured["url"] = url
            captured["body"] = body
            captured["headers"] = headers
            return (200, b"OK")

        edition = {"id": "catholic-study", "title": "Catholic Study Bible"}
        result = archive_org.upload_press_kit(
            edition,
            {"blurb_500": "Description."},
            b"zip-body-bytes",
            http_fn=fake_http,
        )
        assert result["ok"] is True
        assert result["identifier"] == "yhwh-bible-catholic-study"
        assert result["url"].endswith("/yhwh-bible-catholic-study")
        assert result["status_code"] == 200
        assert result["bytes"] == len(b"zip-body-bytes")
        # PUT went to the right URL.
        assert captured["url"] == "https://s3.us.archive.org/yhwh-bible-catholic-study/press-kit-catholic-study.zip"
        # Authorization + Content-Type set.
        assert captured["headers"]["Authorization"] == "LOW test-access:test-secret"
        assert captured["headers"]["Content-Type"] == "application/zip"
        assert captured["headers"]["x-archive-meta-title"] == "Catholic Study Bible"

    def test_4xx_response_returns_ok_false(self, monkeypatch):
        from scripts.core import archive_org

        _set_creds(monkeypatch)
        result = archive_org.upload_press_kit(
            {"id": "x", "title": "X"},
            {},
            b"body",
            http_fn=lambda u, b, h: (403, b"Forbidden"),
        )
        assert result["ok"] is False
        assert result["status_code"] == 403
        assert "403" in result["message"]

    def test_exception_in_http_fn_returns_ok_false(self, monkeypatch):
        from scripts.core import archive_org

        _set_creds(monkeypatch)

        def boom(url, body, headers):
            raise ConnectionError("network down")

        result = archive_org.upload_press_kit(
            {"id": "x", "title": "X"},
            {},
            b"body",
            http_fn=boom,
        )
        assert result["ok"] is False
        assert result["status_code"] == 0
        assert "ConnectionError" in result["message"]
        # Identifier still computed so the audit trail can correlate.
        assert result["identifier"] == "yhwh-bible-x"

    def test_raises_without_creds(self, monkeypatch):
        from scripts.core import archive_org

        _clear_creds(monkeypatch)
        with pytest.raises(RuntimeError, match="credentials not configured"):
            archive_org.upload_press_kit(
                {"id": "x", "title": "X"},
                {},
                b"body",
                http_fn=lambda u, b, h: (200, b""),
            )

    def test_uses_custom_filename(self, monkeypatch):
        from scripts.core import archive_org

        _set_creds(monkeypatch)
        captured = {}

        def fake_http(url, body, headers):
            captured["url"] = url
            return (200, b"")

        archive_org.upload_press_kit(
            {"id": "x", "title": "X"},
            {},
            b"body",
            filename="custom-name.zip",
            http_fn=fake_http,
        )
        assert captured["url"].endswith("/custom-name.zip")


# --------------------------------------------------------------------
# api_archive_org_status
# --------------------------------------------------------------------


class TestOmicron4ApiStatus:
    def test_configured_true(self, monkeypatch):
        from scripts.api.archive_org import api_archive_org_status

        _set_creds(monkeypatch)
        result = api_archive_org_status()
        assert result["status"] == "ok"
        assert result["configured"] is True
        assert result["env_var_access"] == "EBIBLE_ARCHIVE_ORG_ACCESS_KEY"
        assert result["env_var_secret"] == "EBIBLE_ARCHIVE_ORG_SECRET_KEY"
        assert result["identifier_prefix"] == "yhwh-bible-"

    def test_configured_false(self, monkeypatch):
        from scripts.api.archive_org import api_archive_org_status

        _clear_creds(monkeypatch)
        result = api_archive_org_status()
        assert result["configured"] is False
        assert "EBIBLE_ARCHIVE_ORG_ACCESS_KEY" in result["message"]


# --------------------------------------------------------------------
# api_archive_org_upload
# --------------------------------------------------------------------


class TestOmicron4ApiUpload:
    def _real_edition_id(self):
        from scripts.core import config

        return str(config.load_editions()[0]["id"])

    def test_missing_credentials_returns_503(self, monkeypatch, tmp_path):
        from scripts.api.archive_org import api_archive_org_upload

        _clear_creds(monkeypatch)
        result = api_archive_org_upload("anything", {})
        assert result["status"] == "error"
        assert result["code"] == "not_configured"
        assert result["http"] == 503

    def test_unknown_edition_returns_404(self, monkeypatch, tmp_path):
        from scripts.api.archive_org import api_archive_org_upload

        _set_creds(monkeypatch)
        _isolate_press_kit(monkeypatch, tmp_path)
        _isolate_distribution(monkeypatch, tmp_path)
        result = api_archive_org_upload("def-not-a-real-edition", {}, http_fn=lambda *a, **k: (200, b""))
        assert result["status"] == "error"
        assert result["code"] == "unknown_edition"

    def test_happy_path_marks_distribution(self, monkeypatch, tmp_path):
        from scripts.api.archive_org import api_archive_org_upload
        from scripts.core import distribution

        _set_creds(monkeypatch)
        _isolate_press_kit(monkeypatch, tmp_path)
        _isolate_distribution(monkeypatch, tmp_path)
        ed_id = self._real_edition_id()

        # Stub the network call.
        result = api_archive_org_upload(ed_id, {}, http_fn=lambda url, body, headers: (200, b""))
        assert result["ok"] is True
        assert result["distribution_marked"] is True
        # Distribution cell flipped.
        state = distribution.load_distribution()
        assert distribution.is_shipped(state, ed_id, "archive_org")
        # The notes field records the auto-mark provenance.
        entry = state["editions"][ed_id]["archive_org"]
        assert "ο.4" in entry.get("notes", "")

    def test_upload_failure_does_not_mark_distribution(self, monkeypatch, tmp_path):
        from scripts.api.archive_org import api_archive_org_upload
        from scripts.core import distribution

        _set_creds(monkeypatch)
        _isolate_press_kit(monkeypatch, tmp_path)
        _isolate_distribution(monkeypatch, tmp_path)
        ed_id = self._real_edition_id()

        result = api_archive_org_upload(ed_id, {}, http_fn=lambda url, body, headers: (500, b"Server Error"))
        assert result["ok"] is False
        assert result["distribution_marked"] is False
        # Distribution unchanged.
        state = distribution.load_distribution()
        assert not distribution.is_shipped(state, ed_id, "archive_org")

    def test_distribution_side_effect_failure_surfaces(self, monkeypatch, tmp_path):
        from scripts.api.archive_org import api_archive_org_upload
        from scripts.core import distribution

        _set_creds(monkeypatch)
        _isolate_press_kit(monkeypatch, tmp_path)
        _isolate_distribution(monkeypatch, tmp_path)
        ed_id = self._real_edition_id()

        # Make distribution.mark_shipped raise.
        def boom(*args, **kwargs):
            raise OSError("disk full")

        monkeypatch.setattr(distribution, "mark_shipped", boom)
        result = api_archive_org_upload(ed_id, {}, http_fn=lambda url, body, headers: (200, b""))
        # Upload reported successful, side-effect failure surfaces.
        assert result["ok"] is True
        assert result["distribution_marked"] is False
        assert result["distribution_error"] is not None
        assert "OSError" in result["distribution_error"]


# --------------------------------------------------------------------
# /exec template
# --------------------------------------------------------------------


class TestOmicron4ExecTemplate:
    @classmethod
    def setup_class(cls):
        from scripts.templates.exec import EXEC_HTML

        cls.html = EXEC_HTML

    def test_banner_and_button_present(self):
        assert 'id="archive-org-banner"' in self.html
        assert 'id="archive-org-upload"' in self.html

    def test_button_disabled_by_default(self):
        # Until status confirms configured, the button must be disabled.
        assert 'id="archive-org-upload"' in self.html
        # Crude but precise: the disabled attr appears on the button element.
        # Look for "Upload to archive.org" near a `disabled` attr in the same fragment.
        upload_section_start = self.html.find('id="archive-org-upload"')
        upload_section_end = self.html.find(">", upload_section_start)
        opening_tag = self.html[upload_section_start:upload_section_end]
        assert "disabled" in opening_tag

    def test_js_helpers_present(self):
        for fn in ("loadArchiveOrgStatus", "uploadToArchiveOrg"):
            assert fn in self.html

    def test_endpoints_referenced(self):
        assert "/api/archive-org/status" in self.html
        assert "/api/archive-org/upload/" in self.html


# --------------------------------------------------------------------
# Route registration
# --------------------------------------------------------------------


class TestOmicron4RouteRegistration:
    def test_status_in_simple_get_table(self):
        from scripts import web

        routes = {p: h for (p, h) in web._SIMPLE_GET_ROUTES}
        assert "/api/archive-org/status" in routes
        assert routes["/api/archive-org/status"] is web.api_archive_org_status

    def test_upload_in_post_table(self, monkeypatch):
        import re

        from scripts import web

        # Find the matching POST route + execute it with bypass-friendly
        # input. We can't run the upload itself (would need creds), but
        # we can verify the lambda routes to api_archive_org_upload by
        # observing the not_configured error envelope when creds are
        # absent.
        from scripts.core import archive_org

        monkeypatch.delenv(archive_org.ENV_ACCESS_KEY, raising=False)
        monkeypatch.delenv(archive_org.ENV_SECRET_KEY, raising=False)

        for regex, handler in web._POST_ROUTES:
            if regex.match("/api/archive-org/upload/catholic-study"):
                result = handler(
                    re.match(regex.pattern, "/api/archive-org/upload/catholic-study"),
                    {},
                )
                assert result.get("status") == "error"
                assert result.get("code") == "not_configured"
                return
        pytest.fail("no POST route matches /api/archive-org/upload/<edition>")


# --------------------------------------------------------------------
# http.put helper
# --------------------------------------------------------------------


class TestOmicron4HttpPutHelper:
    def test_put_sends_body_and_returns_status(self):
        from scripts.core import http

        captured = {}

        class FakeResponse:
            status = 200

            def read(self):
                return b"ok"

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_urlopen(req, timeout=None):
            captured["url"] = req.full_url
            captured["data"] = req.data
            captured["method"] = req.get_method()
            captured["headers"] = dict(req.header_items())
            return FakeResponse()

        status, body = http.put(
            "https://s3.us.archive.org/some-id/file.zip",
            b"payload-bytes",
            headers={"Authorization": "LOW x:y"},
            allowlist={"s3.us.archive.org"},
            urlopen=fake_urlopen,
            sleep_fn=lambda _: None,
        )
        assert status == 200
        assert body == b"ok"
        assert captured["data"] == b"payload-bytes"
        assert captured["method"] == "PUT"
        # urllib title-cases the header keys.
        assert any(k.lower() == "authorization" for k in captured["headers"])

    def test_put_retries_on_5xx(self):
        from scripts.core import http

        call_count = {"n": 0}

        def fake_urlopen(req, timeout=None):
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise urllib.error.HTTPError(req.full_url, 503, "Service Unavailable", {}, None)

            class R:
                status = 200

                def read(self):
                    return b"ok"

                def __enter__(self):
                    return self

                def __exit__(self, *a):
                    return False

            return R()

        # 3 attempts (retries=2). First 2 fail with 503 → retried; 3rd succeeds.
        status, _ = http.put(
            "https://s3.us.archive.org/x/y",
            b"",
            headers={},
            allowlist={"s3.us.archive.org"},
            urlopen=fake_urlopen,
            sleep_fn=lambda _: None,
            retries=2,
        )
        assert status == 200
        assert call_count["n"] == 3

    def test_put_respects_allowlist(self):
        from scripts.core import http

        with pytest.raises(http.SSRFBlockedError):
            http.put(
                "https://evil.example.com/file",
                b"",
                headers={},
                allowlist={"s3.us.archive.org"},
                urlopen=lambda *a, **k: None,
                sleep_fn=lambda _: None,
            )


# --------------------------------------------------------------------
# Integration: zip from press_kit is what archive_org uploads.
# --------------------------------------------------------------------


class TestOmicron4Integration:
    def test_uploaded_body_is_valid_zip_from_press_kit(self, monkeypatch, tmp_path):
        from scripts.api.archive_org import api_archive_org_upload
        from scripts.core import config

        _set_creds(monkeypatch)
        _isolate_press_kit(monkeypatch, tmp_path)
        _isolate_distribution(monkeypatch, tmp_path)
        ed_id = str(config.load_editions()[0]["id"])

        captured = {}

        def http_capture(url, body, headers):
            captured["body"] = body
            return (200, b"")

        result = api_archive_org_upload(ed_id, {}, http_fn=http_capture)
        assert result["ok"] is True
        # The body uploaded is a valid ZIP that contains the manifest.
        with zipfile.ZipFile(io.BytesIO(captured["body"])) as zf:
            assert "manifest.json" in zf.namelist()
            manifest = json.loads(zf.read("manifest.json"))
            assert manifest["edition_id"] == ed_id
