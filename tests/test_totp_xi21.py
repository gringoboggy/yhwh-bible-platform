"""ξ.21 — TOTP-based 2FA for admin auth pins (2026-05-12).

Stdlib-only (no pyotp) TOTP implementation + persisted enrollment
state + admin-auth gate extension. Month 6 #4 (Month-6 non-money).

Coverage:
- TestXi21Rfc6238Vectors:           current_code() matches RFC 6238
  Appendix B HMAC-SHA1 test vectors at the canonical T values.
- TestXi21SecretGeneration:         generate_secret() returns a
  base32 string of expected length; calls are random (different
  each invocation); accepts a length override; rejects non-positive
  length.
- TestXi21ProvisioningUri:           otpauth://totp/Issuer:Label?...
  shape; URL-encodes label + issuer; carries secret + algorithm +
  digits + period; round-trips through urllib.parse.
- TestXi21VerifyCode:                accepts current code; accepts ±1
  drift step; rejects ±2 (outside default window); rejects malformed
  (non-digit, wrong length, empty); rejects garbage secret without
  raising.
- TestXi21AuthStateLoadSave:        empty-state default for missing /
  malformed file; round-trip; whitelist drops unknown fields.
- TestXi21EnrollDisable:             enroll_totp persists state;
  disable_totp idempotent; is_totp_enabled + get_totp_secret
  reflect persisted state.
- TestXi21ApiBegin:                  generates a fresh secret + URI;
  refuses when already enrolled.
- TestXi21ApiConfirm:                happy path persists; rejects
  invalid code; rejects missing secret/code; rejects when already
  enrolled.
- TestXi21ApiDisable:                requires valid current code;
  idempotent on already-disabled; refuses on invalid code.
- TestXi21ApiStatus:                 surfaces enrollment metadata;
  never reveals the secret.
- TestXi21AdminAuthGate:             back-compat (neither factor
  enabled); token-only (existing test still passes); token+TOTP
  (Bearer token:code parses); TOTP-only (Bearer :code).
- TestXi21RouteRegistration:         GET /api/auth/status in
  _SIMPLE_GET_ROUTES; 3 POST routes (/begin /confirm /disable) in
  _POST_ROUTES.

Tests isolate `auth._auth_path` to tmp so the production
content/auth.json is never touched.
"""

from __future__ import annotations

import base64

import pytest


# RFC 6238 Appendix B test secret (HMAC-SHA1 column): the ASCII bytes
# "12345678901234567890" (20 bytes). Reproduced here in base32 so
# our verify path covers the canonical input.
RFC_SECRET_ASCII = b"12345678901234567890"
RFC_SECRET_B32 = base64.b32encode(RFC_SECRET_ASCII).decode("ascii").rstrip("=")


def _isolate_auth(monkeypatch, tmp_path):
    from scripts.core import auth

    p = tmp_path / "auth.json"
    monkeypatch.setattr(auth, "_auth_path", lambda: p)
    return p


# --------------------------------------------------------------------
# RFC 6238 Appendix B vectors (HMAC-SHA1)
# --------------------------------------------------------------------


class TestXi21Rfc6238Vectors:
    """RFC 6238 Appendix B vectors (HMAC-SHA1 column).

    The RFC's test secret is the ASCII bytes "12345678901234567890".
    Test values: time T → 8-digit code → expected 6-digit truncated.
    """

    # (unix_time, expected_6_digit_code)
    VECTORS = [
        (59, "287082"),
        (1111111109, "081804"),
        (1111111111, "050471"),
        (1234567890, "005924"),
        (2000000000, "279037"),
        (20000000000, "353130"),
    ]

    @pytest.mark.parametrize("unix_time,expected", VECTORS)
    def test_rfc6238_vector(self, unix_time, expected):
        from scripts.core import totp

        got = totp.current_code(RFC_SECRET_B32, now=unix_time)
        assert got == expected, f"T={unix_time}: expected {expected}, got {got}"


# --------------------------------------------------------------------
# secret generation
# --------------------------------------------------------------------


class TestXi21SecretGeneration:
    def test_default_length(self):
        from scripts.core import totp

        s = totp.generate_secret()
        # 20 bytes → 32-char base32 with no padding (since 20*8=160,
        # 160/5=32, exact).
        assert len(s) == 32

    def test_distinct_per_call(self):
        from scripts.core import totp

        a = totp.generate_secret()
        b = totp.generate_secret()
        assert a != b

    def test_length_override(self):
        from scripts.core import totp

        s = totp.generate_secret(length_bytes=10)
        # 10 bytes → 16-char base32 (10*8=80, 80/5=16).
        assert len(s) == 16

    def test_rejects_non_positive_length(self):
        from scripts.core import totp

        with pytest.raises(ValueError):
            totp.generate_secret(length_bytes=0)
        with pytest.raises(ValueError):
            totp.generate_secret(length_bytes=-1)

    def test_secret_is_base32(self):
        from scripts.core import totp

        s = totp.generate_secret()
        # base32 alphabet: A-Z + 2-7
        for c in s:
            assert c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567", f"bad char {c!r}"


# --------------------------------------------------------------------
# Provisioning URI
# --------------------------------------------------------------------


class TestXi21ProvisioningUri:
    def test_otpauth_scheme(self):
        from scripts.core import totp

        uri = totp.provisioning_uri("ABCXYZ234567", label="admin")
        assert uri.startswith("otpauth://totp/")

    def test_carries_secret_and_params(self):
        from scripts.core import totp

        uri = totp.provisioning_uri("ABCXYZ234567", label="admin", issuer="Test App")
        assert "secret=ABCXYZ234567" in uri
        assert "algorithm=SHA1" in uri
        assert "digits=6" in uri
        assert "period=30" in uri
        # issuer query param also present (de-facto standard)
        assert "issuer=Test+App" in uri or "issuer=Test%20App" in uri

    def test_url_encodes_label_and_issuer(self):
        from scripts.core import totp

        uri = totp.provisioning_uri("ABCXYZ234567", label="admin@ebible.app", issuer="Test App")
        # @ is percent-encoded in the path
        assert "admin%40ebible.app" in uri
        # space in issuer is percent-encoded or +-encoded
        assert "Test%20App" in uri or "Test+App" in uri

    def test_round_trips_through_parser(self):
        import urllib.parse

        from scripts.core import totp

        uri = totp.provisioning_uri("ABCXYZ234567", label="admin", issuer="YHWH Bible")
        parsed = urllib.parse.urlparse(uri)
        assert parsed.scheme == "otpauth"
        assert parsed.netloc == "totp"
        qs = urllib.parse.parse_qs(parsed.query)
        assert qs["secret"] == ["ABCXYZ234567"]
        assert qs["algorithm"] == ["SHA1"]


# --------------------------------------------------------------------
# verify_code
# --------------------------------------------------------------------


class TestXi21VerifyCode:
    def test_accepts_current_code(self):
        from scripts.core import totp

        code = totp.current_code(RFC_SECRET_B32, now=1234567890)
        assert totp.verify_code(RFC_SECRET_B32, code, now=1234567890)

    def test_accepts_drift_one_step_back(self):
        from scripts.core import totp

        # Code generated 30s ago is still valid (default drift=1 step).
        code = totp.current_code(RFC_SECRET_B32, now=1234567890 - 30)
        assert totp.verify_code(RFC_SECRET_B32, code, now=1234567890)

    def test_accepts_drift_one_step_forward(self):
        from scripts.core import totp

        # Code generated 30s in the future is also accepted.
        code = totp.current_code(RFC_SECRET_B32, now=1234567890 + 30)
        assert totp.verify_code(RFC_SECRET_B32, code, now=1234567890)

    def test_rejects_two_step_drift(self):
        from scripts.core import totp

        # ±60s is outside default drift window.
        code = totp.current_code(RFC_SECRET_B32, now=1234567890 - 60)
        assert not totp.verify_code(RFC_SECRET_B32, code, now=1234567890)

    def test_rejects_wrong_code(self):
        from scripts.core import totp

        assert not totp.verify_code(RFC_SECRET_B32, "000000", now=1234567890)

    def test_rejects_malformed(self):
        from scripts.core import totp

        assert not totp.verify_code(RFC_SECRET_B32, "abc", now=1234567890)
        assert not totp.verify_code(RFC_SECRET_B32, "12345", now=1234567890)  # wrong length
        assert not totp.verify_code(RFC_SECRET_B32, "1234567", now=1234567890)
        assert not totp.verify_code(RFC_SECRET_B32, "", now=1234567890)
        assert not totp.verify_code(RFC_SECRET_B32, None, now=1234567890)  # type: ignore[arg-type]

    def test_rejects_garbage_secret_without_raising(self):
        from scripts.core import totp

        assert not totp.verify_code("not-base32!", "123456", now=1234567890)


# --------------------------------------------------------------------
# auth state load/save
# --------------------------------------------------------------------


class TestXi21AuthStateLoadSave:
    def test_empty_when_missing(self, monkeypatch, tmp_path):
        from scripts.core import auth

        _isolate_auth(monkeypatch, tmp_path)
        state = auth.load_auth()
        assert state == {"schema_version": 1}

    def test_malformed_yields_empty(self, monkeypatch, tmp_path):
        from scripts.core import auth

        p = _isolate_auth(monkeypatch, tmp_path)
        p.write_text("not json", encoding="utf-8")
        state = auth.load_auth()
        assert "schema_version" in state

    def test_round_trip(self, monkeypatch, tmp_path):
        from scripts.core import auth

        _isolate_auth(monkeypatch, tmp_path)
        state = {
            "totp": {
                "enabled": True,
                "secret": "ABCXYZ234567",
                "enrolled_at": "2026-05-12T00:00:00+00:00",
                "issuer": "Test",
                "label": "admin",
            }
        }
        auth.save_auth(state)
        round_tripped = auth.load_auth()
        assert round_tripped["totp"]["secret"] == "ABCXYZ234567"

    def test_save_drops_unknown_totp_fields(self, monkeypatch, tmp_path):
        from scripts.core import auth

        _isolate_auth(monkeypatch, tmp_path)
        state = {
            "totp": {
                "enabled": True,
                "secret": "X",
                "rogue_field": "drop me",
            }
        }
        auth.save_auth(state)
        round_tripped = auth.load_auth()
        assert "rogue_field" not in round_tripped["totp"]


# --------------------------------------------------------------------
# enroll / disable
# --------------------------------------------------------------------


class TestXi21EnrollDisable:
    def test_enroll_persists(self, monkeypatch, tmp_path):
        from scripts.core import auth

        _isolate_auth(monkeypatch, tmp_path)
        entry = auth.enroll_totp("ABCXYZ234567")
        assert entry["enabled"] is True
        assert entry["secret"] == "ABCXYZ234567"
        # Reload from disk confirms persistence.
        state = auth.load_auth()
        assert state["totp"]["secret"] == "ABCXYZ234567"

    def test_is_totp_enabled_reflects_state(self, monkeypatch, tmp_path):
        from scripts.core import auth

        _isolate_auth(monkeypatch, tmp_path)
        assert auth.is_totp_enabled() is False
        auth.enroll_totp("ABCXYZ234567")
        assert auth.is_totp_enabled() is True

    def test_get_totp_secret(self, monkeypatch, tmp_path):
        from scripts.core import auth

        _isolate_auth(monkeypatch, tmp_path)
        assert auth.get_totp_secret() is None
        auth.enroll_totp("ABCXYZ234567")
        assert auth.get_totp_secret() == "ABCXYZ234567"

    def test_disable_removes(self, monkeypatch, tmp_path):
        from scripts.core import auth

        _isolate_auth(monkeypatch, tmp_path)
        auth.enroll_totp("ABCXYZ234567")
        assert auth.disable_totp() is True
        assert auth.is_totp_enabled() is False

    def test_disable_idempotent(self, monkeypatch, tmp_path):
        from scripts.core import auth

        _isolate_auth(monkeypatch, tmp_path)
        # Not enrolled — disable returns False (nothing to remove).
        assert auth.disable_totp() is False

    def test_enroll_rejects_empty_secret(self, monkeypatch, tmp_path):
        from scripts.core import auth

        _isolate_auth(monkeypatch, tmp_path)
        with pytest.raises(ValueError):
            auth.enroll_totp("")
        with pytest.raises(ValueError):
            auth.enroll_totp("   ")


# --------------------------------------------------------------------
# API endpoints
# --------------------------------------------------------------------


class TestXi21ApiBegin:
    def test_returns_fresh_secret_and_uri(self, monkeypatch, tmp_path):
        from scripts.api.auth import api_auth_totp_begin

        _isolate_auth(monkeypatch, tmp_path)
        result = api_auth_totp_begin({})
        assert result["ok"] is True
        assert len(result["secret"]) > 0
        assert result["provisioning_uri"].startswith("otpauth://totp/")

    def test_refuses_when_already_enrolled(self, monkeypatch, tmp_path):
        from scripts.api.auth import api_auth_totp_begin
        from scripts.core import auth

        _isolate_auth(monkeypatch, tmp_path)
        auth.enroll_totp("ABCXYZ234567")
        result = api_auth_totp_begin({})
        assert result["ok"] is False
        assert result["error"] == "already_enrolled"


class TestXi21ApiConfirm:
    def test_happy_path_persists(self, monkeypatch, tmp_path):
        from scripts.api.auth import api_auth_totp_begin, api_auth_totp_confirm
        from scripts.core import auth, totp

        _isolate_auth(monkeypatch, tmp_path)
        begin = api_auth_totp_begin({})
        secret = begin["secret"]
        code = totp.current_code(secret)
        result = api_auth_totp_confirm({"secret": secret, "code": code})
        assert result["ok"] is True
        assert auth.is_totp_enabled()

    def test_rejects_invalid_code(self, monkeypatch, tmp_path):
        from scripts.api.auth import api_auth_totp_confirm

        _isolate_auth(monkeypatch, tmp_path)
        result = api_auth_totp_confirm({"secret": "ABCXYZ234567", "code": "000000"})
        assert result["ok"] is False
        assert result["error"] == "invalid_code"

    def test_rejects_missing_fields(self, monkeypatch, tmp_path):
        from scripts.api.auth import api_auth_totp_confirm

        _isolate_auth(monkeypatch, tmp_path)
        assert api_auth_totp_confirm({})["error"] == "missing_secret"
        assert api_auth_totp_confirm({"secret": "X"})["error"] == "missing_code"

    def test_refuses_when_already_enrolled(self, monkeypatch, tmp_path):
        from scripts.api.auth import api_auth_totp_confirm
        from scripts.core import auth

        _isolate_auth(monkeypatch, tmp_path)
        auth.enroll_totp("ABCXYZ234567")
        result = api_auth_totp_confirm({"secret": "X", "code": "123456"})
        assert result["ok"] is False
        assert result["error"] == "already_enrolled"


class TestXi21ApiDisable:
    def test_disable_with_valid_code(self, monkeypatch, tmp_path):
        from scripts.api.auth import api_auth_totp_disable
        from scripts.core import auth, totp

        _isolate_auth(monkeypatch, tmp_path)
        secret = totp.generate_secret()
        auth.enroll_totp(secret)
        code = totp.current_code(secret)
        result = api_auth_totp_disable({"code": code})
        assert result["ok"] is True
        assert result["removed"] is True
        assert auth.is_totp_enabled() is False

    def test_disable_idempotent_when_not_enrolled(self, monkeypatch, tmp_path):
        from scripts.api.auth import api_auth_totp_disable

        _isolate_auth(monkeypatch, tmp_path)
        result = api_auth_totp_disable({"code": "000000"})
        assert result["ok"] is True
        assert result["removed"] is False

    def test_refuses_invalid_code(self, monkeypatch, tmp_path):
        from scripts.api.auth import api_auth_totp_disable
        from scripts.core import auth

        _isolate_auth(monkeypatch, tmp_path)
        auth.enroll_totp("ABCXYZ234567")
        result = api_auth_totp_disable({"code": "000000"})
        assert result["ok"] is False
        assert result["error"] == "invalid_code"
        # Still enrolled — refusing didn't wipe.
        assert auth.is_totp_enabled() is True

    def test_requires_code(self, monkeypatch, tmp_path):
        from scripts.api.auth import api_auth_totp_disable
        from scripts.core import auth

        _isolate_auth(monkeypatch, tmp_path)
        auth.enroll_totp("ABCXYZ234567")
        assert api_auth_totp_disable({})["error"] == "missing_code"


class TestXi21ApiStatus:
    def test_returns_both_flags(self, monkeypatch, tmp_path):
        from scripts.api.auth import api_auth_status

        _isolate_auth(monkeypatch, tmp_path)
        monkeypatch.delenv("EBIBLE_ADMIN_TOKEN", raising=False)
        result = api_auth_status()
        assert result["status"] == "ok"
        assert result["token_enabled"] is False
        assert result["totp_enabled"] is False

    def test_surfaces_enrollment_metadata(self, monkeypatch, tmp_path):
        from scripts.api.auth import api_auth_status
        from scripts.core import auth

        _isolate_auth(monkeypatch, tmp_path)
        auth.enroll_totp("ABCXYZ234567", issuer="Test", label="admin@test")
        result = api_auth_status()
        assert result["totp_enabled"] is True
        assert result["issuer"] == "Test"
        assert result["label"] == "admin@test"
        # Critically: never reveals the secret.
        assert "secret" not in result

    def test_token_env_flag(self, monkeypatch, tmp_path):
        from scripts.api.auth import api_auth_status

        _isolate_auth(monkeypatch, tmp_path)
        monkeypatch.setenv("EBIBLE_ADMIN_TOKEN", "some-token")
        result = api_auth_status()
        assert result["token_enabled"] is True


# --------------------------------------------------------------------
# Admin auth gate (ξ.21 extension)
# --------------------------------------------------------------------


class TestXi21AdminAuthGate:
    """The gate accepts a 2-factor `Bearer <token>:<code>` header
    when both factors are enabled. Back-compat with the original
    token-only behavior."""

    def _mock_handler(self, headers):
        from scripts import web

        Handler = web.Handler
        captured = {"status": None}

        class _Stub(Handler):
            def __init__(self):
                pass

            def _send_json(self, payload, status=200):
                captured["status"] = status

        h = _Stub()

        class _Hdrs:
            def __init__(self, d):
                self._d = d

            def get(self, k, default=""):
                return self._d.get(k, default)

        h.headers = _Hdrs(headers)
        h._captured = captured
        return h

    def test_back_compat_neither_factor_enabled(self, monkeypatch, tmp_path):
        _isolate_auth(monkeypatch, tmp_path)
        monkeypatch.delenv("EBIBLE_ADMIN_TOKEN", raising=False)
        h = self._mock_handler({})
        assert h._check_admin_auth() is True

    def test_token_only_back_compat(self, monkeypatch, tmp_path):
        _isolate_auth(monkeypatch, tmp_path)
        monkeypatch.setenv("EBIBLE_ADMIN_TOKEN", "tok")
        # Correct token, no TOTP → True.
        h = self._mock_handler({"Authorization": "Bearer tok"})
        assert h._check_admin_auth() is True
        # Wrong token → False.
        h2 = self._mock_handler({"Authorization": "Bearer wrong"})
        assert h2._check_admin_auth() is False
        assert h2._captured["status"] == 401

    def test_token_and_totp_combined(self, monkeypatch, tmp_path):
        from scripts.core import auth, totp

        _isolate_auth(monkeypatch, tmp_path)
        monkeypatch.setenv("EBIBLE_ADMIN_TOKEN", "tok")
        secret = totp.generate_secret()
        auth.enroll_totp(secret)
        code = totp.current_code(secret)

        # Correct token + correct code → True.
        h = self._mock_handler({"Authorization": f"Bearer tok:{code}"})
        assert h._check_admin_auth() is True

        # Correct token + wrong code → False.
        h2 = self._mock_handler({"Authorization": "Bearer tok:000000"})
        assert h2._check_admin_auth() is False
        assert h2._captured["status"] == 401

        # Correct token + missing code → False.
        h3 = self._mock_handler({"Authorization": "Bearer tok"})
        assert h3._check_admin_auth() is False
        assert h3._captured["status"] == 401

    def test_totp_only_no_token(self, monkeypatch, tmp_path):
        from scripts.core import auth, totp

        _isolate_auth(monkeypatch, tmp_path)
        monkeypatch.delenv("EBIBLE_ADMIN_TOKEN", raising=False)
        secret = totp.generate_secret()
        auth.enroll_totp(secret)
        code = totp.current_code(secret)

        # Bearer :code → True (token slot is empty; TOTP carries the auth).
        h = self._mock_handler({"Authorization": f"Bearer :{code}"})
        assert h._check_admin_auth() is True

        # Bearer :wrong → False.
        h2 = self._mock_handler({"Authorization": "Bearer :000000"})
        assert h2._check_admin_auth() is False

    def test_missing_header_rejected_when_factors_enabled(self, monkeypatch, tmp_path):
        _isolate_auth(monkeypatch, tmp_path)
        monkeypatch.setenv("EBIBLE_ADMIN_TOKEN", "tok")
        h = self._mock_handler({})
        assert h._check_admin_auth() is False
        assert h._captured["status"] == 401


# --------------------------------------------------------------------
# Route registration
# --------------------------------------------------------------------


class TestXi21RouteRegistration:
    def test_status_in_simple_get_table(self):
        from scripts import web

        routes = {p: h for (p, h) in web._SIMPLE_GET_ROUTES}
        assert "/api/auth/status" in routes
        assert routes["/api/auth/status"] is web.api_auth_status

    def test_three_post_routes_present(self):
        import re

        from scripts import web

        patterns = [r.pattern for (r, _h) in web._POST_ROUTES]
        joined = "|".join(patterns)
        assert "/api/auth/totp/begin" in joined
        assert "/api/auth/totp/confirm" in joined
        assert "/api/auth/totp/disable" in joined

    def test_begin_route_dispatches(self, monkeypatch, tmp_path):
        import re

        from scripts import web

        _isolate_auth(monkeypatch, tmp_path)
        for regex, handler in web._POST_ROUTES:
            if regex.match("/api/auth/totp/begin"):
                result = handler(
                    re.match(regex.pattern, "/api/auth/totp/begin"),
                    {},
                )
                assert result["ok"] is True
                assert "provisioning_uri" in result
                return
        pytest.fail("no POST route matches /api/auth/totp/begin")
