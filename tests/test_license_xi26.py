"""ξ.26 — license-key validation pins (2026-05-12).

Stdlib-only HMAC-SHA256 license signing (substituted for the
PROPOSAL-spec'd Ed25519 because the cryptography library
conflicts with the §6.3 no-build-step invariant; soft
enforcement at v1 per §9.5 doesn't justify asymmetric crypto).

Coverage:
- TestXi26Constants:                LICENSE_PREFIX = "LK1";
  ENV_SIGNING_KEY = "EBIBLE_LICENSE_SIGNING_KEY".
- TestXi26EnforcementToggle:        is_enforced() True iff env
  var set + non-empty; whitespace-only treated as unset.
- TestXi26Mint:                     mint() returns LK1-prefixed
  string; rejects empty edition_id / colon in edition_id /
  empty expires / missing signing key.
- TestXi26Verify:                   round-trip (mint + verify =
  valid); rejects bad signature; rejects expired key; rejects
  malformed string (wrong format, unsupported version, missing);
  fail-open when no signing key configured.
- TestXi26LicenseStateLoadSave:     empty-state default;
  malformed-JSON tolerance; round-trip; whitelist drops unknown
  entry fields.
- TestXi26SetRemove:                set_license writes; get_license
  reads; remove_license idempotent; rejects empty inputs.
- TestXi26ApiStatus:                payload shape; lists every
  edition with has_key + valid + reason; never reveals stored
  key string.
- TestXi26ApiSet:                   happy path persists; refuses
  invalid key (signature fails) so a bad key isn't stored;
  refuses edition mismatch; refuses unknown edition.
- TestXi26ApiRemove:                idempotent; happy path
  removes; unknown edition → ok:True removed:False.
- TestXi26RouteRegistration:        GET /api/license/status in
  _SIMPLE_GET_ROUTES; PUT /api/license/<edition> in _PUT_ROUTES;
  DELETE /api/license/<edition> in _DELETE_ROUTES.

Tests isolate license_state._licenses_path to tmp so the real
content/licenses.json is never touched. Signing-key env var is
managed via monkeypatch.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest


# Test signing key — used throughout. A real publisher would generate
# a random base64 string.
TEST_SECRET = "test-signing-secret-do-not-use-in-prod"


def _isolate_license_state(monkeypatch, tmp_path):
    from scripts.core import license_state

    p = tmp_path / "licenses.json"
    monkeypatch.setattr(license_state, "_licenses_path", lambda: p)
    return p


def _set_secret(monkeypatch, value: str = TEST_SECRET):
    from scripts.core import license_key

    monkeypatch.setenv(license_key.ENV_SIGNING_KEY, value)


def _clear_secret(monkeypatch):
    from scripts.core import license_key

    monkeypatch.delenv(license_key.ENV_SIGNING_KEY, raising=False)


# --------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------


class TestXi26Constants:
    def test_prefix_pinned(self):
        from scripts.core import license_key

        # Format prefix is load-bearing for future LK2 migration.
        # Pin so accidental bump is a deliberate decision.
        assert license_key.LICENSE_PREFIX == "LK1"

    def test_env_var_name_pinned(self):
        from scripts.core import license_key

        assert license_key.ENV_SIGNING_KEY == "EBIBLE_LICENSE_SIGNING_KEY"


# --------------------------------------------------------------------
# is_enforced
# --------------------------------------------------------------------


class TestXi26EnforcementToggle:
    def test_unset_means_unenforced(self, monkeypatch):
        from scripts.core import license_key

        _clear_secret(monkeypatch)
        assert license_key.is_enforced() is False

    def test_set_means_enforced(self, monkeypatch):
        from scripts.core import license_key

        _set_secret(monkeypatch)
        assert license_key.is_enforced() is True

    def test_whitespace_only_unenforced(self, monkeypatch):
        from scripts.core import license_key

        monkeypatch.setenv(license_key.ENV_SIGNING_KEY, "   ")
        assert license_key.is_enforced() is False


# --------------------------------------------------------------------
# mint
# --------------------------------------------------------------------


class TestXi26Mint:
    def test_returns_lk1_string(self, monkeypatch):
        from scripts.core import license_key

        _set_secret(monkeypatch)
        future = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        key = license_key.mint("catholic-study", expires_iso=future)
        assert key.startswith("LK1:")

    def test_carries_edition_id(self, monkeypatch):
        from scripts.core import license_key

        _set_secret(monkeypatch)
        future = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        key = license_key.mint("catholic-study", expires_iso=future)
        assert ":catholic-study:" in key

    def test_rejects_empty_edition(self, monkeypatch):
        from scripts.core import license_key

        _set_secret(monkeypatch)
        future = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        with pytest.raises(ValueError, match="edition_id"):
            license_key.mint("", expires_iso=future)

    def test_rejects_colon_in_edition(self, monkeypatch):
        from scripts.core import license_key

        _set_secret(monkeypatch)
        future = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        # A colon would break the LK1 string-format parser.
        with pytest.raises(ValueError, match="':'"):
            license_key.mint("bad:edition", expires_iso=future)

    def test_rejects_empty_expires(self, monkeypatch):
        from scripts.core import license_key

        _set_secret(monkeypatch)
        with pytest.raises(ValueError, match="expires_iso"):
            license_key.mint("catholic-study", expires_iso="")

    def test_rejects_missing_signing_key(self, monkeypatch):
        from scripts.core import license_key

        _clear_secret(monkeypatch)
        future = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        with pytest.raises(ValueError, match="signing key"):
            license_key.mint("catholic-study", expires_iso=future)

    def test_secret_override_works(self, monkeypatch):
        from scripts.core import license_key

        _clear_secret(monkeypatch)
        future = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        # Explicit secret override lets a mint succeed without the env var.
        key = license_key.mint("catholic-study", expires_iso=future, secret="explicit")
        assert key.startswith("LK1:")


# --------------------------------------------------------------------
# verify
# --------------------------------------------------------------------


class TestXi26Verify:
    def test_round_trip_valid(self, monkeypatch):
        from scripts.core import license_key

        _set_secret(monkeypatch)
        future = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        key = license_key.mint("catholic-study", expires_iso=future)
        result = license_key.verify(key)
        assert result["valid"] is True
        assert result["reason"] == "ok"
        assert result["edition_id"] == "catholic-study"

    def test_rejects_bad_signature(self, monkeypatch):
        from scripts.core import license_key

        _set_secret(monkeypatch)
        future = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        key = license_key.mint("catholic-study", expires_iso=future)
        # Tamper with the signature suffix.
        tampered = key[:-4] + "AAAA"
        result = license_key.verify(tampered)
        assert result["valid"] is False
        assert result["reason"] == "bad_signature"

    def test_rejects_expired(self, monkeypatch):
        from scripts.core import license_key

        _set_secret(monkeypatch)
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        key = license_key.mint("catholic-study", expires_iso=past)
        result = license_key.verify(key)
        assert result["valid"] is False
        assert result["reason"] == "expired"

    def test_rejects_wrong_secret(self, monkeypatch):
        from scripts.core import license_key

        _set_secret(monkeypatch, "secret-a")
        future = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        key = license_key.mint("catholic-study", expires_iso=future)
        # Switch secret; signature no longer verifies.
        _set_secret(monkeypatch, "secret-b")
        result = license_key.verify(key)
        assert result["valid"] is False
        assert result["reason"] == "bad_signature"

    def test_rejects_unsupported_version(self, monkeypatch):
        from scripts.core import license_key

        _set_secret(monkeypatch)
        # LK2 doesn't exist yet.
        result = license_key.verify("LK2:catholic-study:2030-01-01T00:00:00+00:00:foo:bar")
        assert result["valid"] is False
        assert result["reason"] == "unsupported_version"

    def test_rejects_malformed(self, monkeypatch):
        from scripts.core import license_key

        _set_secret(monkeypatch)
        # Missing parts.
        result = license_key.verify("LK1:only-prefix")
        assert result["valid"] is False
        assert result["reason"] == "wrong_format"

    def test_rejects_missing_string(self, monkeypatch):
        from scripts.core import license_key

        _set_secret(monkeypatch)
        result = license_key.verify("")
        assert result["valid"] is False
        assert result["reason"] == "missing"

    def test_fail_open_when_unenforced(self, monkeypatch):
        from scripts.core import license_key

        _clear_secret(monkeypatch)
        # Even a totally invalid string verifies when enforcement is off.
        result = license_key.verify("garbage")
        assert result["valid"] is True
        assert result["reason"] == "no_enforcement"

    def test_now_injection(self, monkeypatch):
        from scripts.core import license_key

        _set_secret(monkeypatch)
        # Mint a key that expires in 2030.
        expires = "2030-01-01T00:00:00+00:00"
        key = license_key.mint("catholic-study", expires_iso=expires)
        # Verify "now" is 2031 — expired.
        future = datetime(2031, 1, 1, tzinfo=timezone.utc)
        result = license_key.verify(key, now=future)
        assert result["valid"] is False
        assert result["reason"] == "expired"
        # Verify "now" is 2029 — still valid.
        past = datetime(2029, 1, 1, tzinfo=timezone.utc)
        result2 = license_key.verify(key, now=past)
        assert result2["valid"] is True


# --------------------------------------------------------------------
# license_state load/save
# --------------------------------------------------------------------


class TestXi26LicenseStateLoadSave:
    def test_empty_when_missing(self, monkeypatch, tmp_path):
        from scripts.core import license_state

        _isolate_license_state(monkeypatch, tmp_path)
        state = license_state.load_licenses()
        assert state == {"schema_version": 1, "editions": {}}

    def test_malformed_yields_empty(self, monkeypatch, tmp_path):
        from scripts.core import license_state

        p = _isolate_license_state(monkeypatch, tmp_path)
        p.write_text("not json", encoding="utf-8")
        state = license_state.load_licenses()
        assert state["editions"] == {}

    def test_round_trip(self, monkeypatch, tmp_path):
        from scripts.core import license_state

        _isolate_license_state(monkeypatch, tmp_path)
        state = {
            "editions": {
                "catholic-study": {
                    "key": "LK1:catholic-study:...:sig",
                    "stored_at": "2026-05-12T00:00:00+00:00",
                }
            }
        }
        license_state.save_licenses(state)
        round_tripped = license_state.load_licenses()
        assert round_tripped["editions"]["catholic-study"]["key"].startswith("LK1:")

    def test_save_drops_unknown_entry_fields(self, monkeypatch, tmp_path):
        from scripts.core import license_state

        _isolate_license_state(monkeypatch, tmp_path)
        state = {
            "editions": {
                "x": {
                    "key": "LK1:...",
                    "rogue_field": "drop me",
                }
            }
        }
        license_state.save_licenses(state)
        round_tripped = license_state.load_licenses()
        assert "rogue_field" not in round_tripped["editions"]["x"]
        assert round_tripped["editions"]["x"]["key"] == "LK1:..."

    def test_save_drops_keyless_entries(self, monkeypatch, tmp_path):
        from scripts.core import license_state

        _isolate_license_state(monkeypatch, tmp_path)
        # A keyless entry doesn't survive a save — keeps state sparse.
        state = {"editions": {"empty-row": {"stored_at": "t"}}}
        license_state.save_licenses(state)
        round_tripped = license_state.load_licenses()
        assert "empty-row" not in round_tripped["editions"]


# --------------------------------------------------------------------
# set / remove / get
# --------------------------------------------------------------------


class TestXi26SetRemove:
    def test_set_writes(self, monkeypatch, tmp_path):
        from scripts.core import license_state

        _isolate_license_state(monkeypatch, tmp_path)
        entry = license_state.set_license("catholic-study", "LK1:catholic-study:...:sig")
        assert "stored_at" in entry
        assert license_state.get_license("catholic-study") == "LK1:catholic-study:...:sig"

    def test_remove_idempotent(self, monkeypatch, tmp_path):
        from scripts.core import license_state

        _isolate_license_state(monkeypatch, tmp_path)
        assert license_state.remove_license("x") is False
        license_state.set_license("x", "LK1:x:...:sig")
        assert license_state.remove_license("x") is True
        assert license_state.remove_license("x") is False  # second call is idempotent

    def test_get_returns_none_when_missing(self, monkeypatch, tmp_path):
        from scripts.core import license_state

        _isolate_license_state(monkeypatch, tmp_path)
        assert license_state.get_license("nope") is None

    def test_set_rejects_empty(self, monkeypatch, tmp_path):
        from scripts.core import license_state

        _isolate_license_state(monkeypatch, tmp_path)
        with pytest.raises(ValueError):
            license_state.set_license("", "key")
        with pytest.raises(ValueError):
            license_state.set_license("x", "")


# --------------------------------------------------------------------
# API endpoints
# --------------------------------------------------------------------


class TestXi26ApiStatus:
    def test_payload_shape(self, monkeypatch, tmp_path):
        from scripts.api.license import api_license_status

        _isolate_license_state(monkeypatch, tmp_path)
        _clear_secret(monkeypatch)
        result = api_license_status()
        assert result["status"] == "ok"
        assert "enforcement_enabled" in result
        assert "signing_key_env" in result
        assert "license_prefix" in result
        assert "editions" in result
        assert isinstance(result["editions"], list)

    def test_lists_every_edition(self, monkeypatch, tmp_path):
        from scripts.api.license import api_license_status
        from scripts.core import config

        _isolate_license_state(monkeypatch, tmp_path)
        _clear_secret(monkeypatch)
        result = api_license_status()
        edition_ids = {row["id"] for row in result["editions"]}
        expected_ids = {str(e["id"]) for e in config.load_editions()}
        assert edition_ids == expected_ids

    def test_missing_keys_marked_missing(self, monkeypatch, tmp_path):
        from scripts.api.license import api_license_status

        _isolate_license_state(monkeypatch, tmp_path)
        _clear_secret(monkeypatch)
        result = api_license_status()
        for row in result["editions"]:
            assert row["has_key"] is False
            # When unenforced, missing keys still show missing (since
            # nothing is stored). The valid flag is False but the
            # reason indicates "missing", not "no_enforcement".
            assert row["reason"] == "missing"

    def test_never_reveals_stored_key(self, monkeypatch, tmp_path):
        from scripts.api.license import api_license_status
        from scripts.core import license_state, license_key

        _isolate_license_state(monkeypatch, tmp_path)
        _set_secret(monkeypatch)
        from scripts.core import config

        ed_id = str(config.load_editions()[0]["id"])
        future = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        key = license_key.mint(ed_id, expires_iso=future)
        license_state.set_license(ed_id, key)

        result = api_license_status()
        # The stored key string must not appear anywhere in the
        # status payload (the buyer can read the JSON; no need to
        # leak the signed token).
        import json

        serialised = json.dumps(result)
        assert key not in serialised


class TestXi26ApiSet:
    def _real_edition_id(self):
        from scripts.core import config

        return str(config.load_editions()[0]["id"])

    def test_happy_path_persists(self, monkeypatch, tmp_path):
        from scripts.api.license import api_license_set
        from scripts.core import license_key, license_state

        _isolate_license_state(monkeypatch, tmp_path)
        _set_secret(monkeypatch)
        ed_id = self._real_edition_id()
        future = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        key = license_key.mint(ed_id, expires_iso=future)
        result = api_license_set(ed_id, {"key": key})
        assert result["ok"] is True
        # Persisted on disk.
        assert license_state.get_license(ed_id) == key

    def test_refuses_unknown_edition(self, monkeypatch, tmp_path):
        from scripts.api.license import api_license_set

        _isolate_license_state(monkeypatch, tmp_path)
        _set_secret(monkeypatch)
        result = api_license_set("def-not-real", {"key": "LK1:..."})
        assert result["ok"] is False
        assert result["error"] == "unknown_edition"

    def test_refuses_missing_key(self, monkeypatch, tmp_path):
        from scripts.api.license import api_license_set

        _isolate_license_state(monkeypatch, tmp_path)
        _set_secret(monkeypatch)
        result = api_license_set(self._real_edition_id(), {})
        assert result["ok"] is False
        assert result["error"] == "missing_key"

    def test_refuses_invalid_key(self, monkeypatch, tmp_path):
        from scripts.api.license import api_license_set
        from scripts.core import license_state

        _isolate_license_state(monkeypatch, tmp_path)
        _set_secret(monkeypatch)
        ed_id = self._real_edition_id()
        result = api_license_set(ed_id, {"key": "LK1:catholic-study:bogus:bogus:bogus"})
        assert result["ok"] is False
        assert result["error"] == "invalid_key"
        # Nothing persisted.
        assert license_state.get_license(ed_id) is None

    def test_refuses_edition_mismatch(self, monkeypatch, tmp_path):
        from scripts.api.license import api_license_set
        from scripts.core import license_key

        _isolate_license_state(monkeypatch, tmp_path)
        _set_secret(monkeypatch)
        # Mint a key for edition A but try to store it under B.
        future = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        key_for_a = license_key.mint(self._real_edition_id(), expires_iso=future)
        # Find a DIFFERENT edition id to mis-store under.
        from scripts.core import config

        eds = config.load_editions()
        if len(eds) < 2:
            pytest.skip("test requires ≥2 editions in editions.yaml")
        other_id = str(eds[1]["id"]) if str(eds[0]["id"]) == self._real_edition_id() else str(eds[0]["id"])
        result = api_license_set(other_id, {"key": key_for_a})
        assert result["ok"] is False
        assert result["error"] == "edition_mismatch"


class TestXi26ApiRemove:
    def _real_edition_id(self):
        from scripts.core import config

        return str(config.load_editions()[0]["id"])

    def test_removes_existing(self, monkeypatch, tmp_path):
        from scripts.api.license import api_license_remove
        from scripts.core import license_state

        _isolate_license_state(monkeypatch, tmp_path)
        license_state.set_license("x", "LK1:...")
        result = api_license_remove("x")
        assert result["ok"] is True
        assert result["removed"] is True

    def test_idempotent_on_missing(self, monkeypatch, tmp_path):
        from scripts.api.license import api_license_remove

        _isolate_license_state(monkeypatch, tmp_path)
        result = api_license_remove("nope")
        assert result["ok"] is True
        assert result["removed"] is False


# --------------------------------------------------------------------
# Route registration
# --------------------------------------------------------------------


class TestXi26RouteRegistration:
    def test_status_in_simple_get_table(self):
        from scripts import web

        routes = {p: h for (p, h) in web._SIMPLE_GET_ROUTES}
        assert "/api/license/status" in routes
        assert routes["/api/license/status"] is web.api_license_status

    def test_put_route_present(self):
        from scripts import web

        patterns = [r.pattern for (r, _h) in web._PUT_ROUTES]
        assert any("/api/license/" in p for p in patterns)

    def test_delete_route_present(self):
        from scripts import web

        patterns = [r.pattern for (r, _h) in web._DELETE_ROUTES]
        assert any("/api/license/" in p for p in patterns)
