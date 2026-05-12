"""ξ.21 — admin auth + 2FA API handlers (2026-05-12).

Four endpoints for the publisher's /ops 2FA enrollment workflow:

- `api_auth_status()` — GET; reports {token_enabled, totp_enabled,
  enrolled_at?, label?, issuer?}. Read-only; never reveals the
  secret.
- `api_auth_totp_begin(payload)` — POST; generates a new secret +
  provisioning URI BUT does NOT persist yet. The publisher scans
  the otpauth URL into their authenticator app, types a code from
  the app, and POSTs to `/confirm` to seal the enrollment. Until
  confirmation, 2FA stays disabled.
- `api_auth_totp_confirm(payload)` — POST; receives the pending
  secret + a 6-digit code generated from it. Verifies the code
  against the secret; on success, persists the secret + flips
  `enabled=True`. Prevents the "enrolled a secret I never proved
  I have" failure mode.
- `api_auth_totp_disable(payload)` — DELETE / POST; disables 2FA
  if the supplied code verifies. Refuses to disable without proof
  the caller has the current secret (prevents an attacker who
  already broke past the token gate from also disabling 2FA).

The endpoints sit BEHIND the existing `_check_admin_auth` gate —
enrolling 2FA still requires the admin token (if one is set). The
gate's TOTP-acceptance behavior is wired in
`scripts.web.Handler._check_admin_auth`; see ξ.21 there.
"""

from __future__ import annotations

from scripts.core import audit_log


def api_auth_status() -> dict:
    """Read-only auth-configuration status.

    Surfaces enough for the /ops UI to render the enrollment banner
    without ever exposing the secret. Specifically:

      - `token_enabled`: True iff EBIBLE_ADMIN_TOKEN env var is set
        (caller knows whether mutations need a Bearer token).
      - `totp_enabled`: True iff a TOTP secret is enrolled.
      - `enrolled_at` / `issuer` / `label`: enrollment metadata
        (only when totp_enabled).
    """
    import os

    from scripts.core import auth

    state = auth.load_auth()
    token_enabled = bool(os.environ.get("EBIBLE_ADMIN_TOKEN", "").strip())
    totp_enabled = auth.is_totp_enabled(state)
    result: dict = {
        "status": "ok",
        "token_enabled": token_enabled,
        "totp_enabled": totp_enabled,
    }
    if totp_enabled:
        totp = state.get("totp", {})
        result["enrolled_at"] = totp.get("enrolled_at", "")
        result["issuer"] = totp.get("issuer", auth.DEFAULT_ISSUER)
        result["label"] = totp.get("label", auth.DEFAULT_LABEL)
    return result


@audit_log.audit_endpoint(action="auth_totp_begin")
def api_auth_totp_begin(payload: dict | None) -> dict:
    """Generate a pending TOTP secret + provisioning URI.

    Does NOT persist the secret. The publisher scans the otpauth
    URL into their authenticator app, types a code, and POSTs to
    `/confirm` with both the secret AND the code. This two-step
    enrollment prevents the "enrolled a secret I never proved I
    have" failure mode (where a network glitch leaves the publisher
    locked out).

    Payload (all optional):
        issuer:   defaults to auth.DEFAULT_ISSUER
        label:    defaults to auth.DEFAULT_LABEL

    Returns `{ok, secret, provisioning_uri, issuer, label}` — the
    SECRET is returned in clear text to the trusted authenticated
    admin so they can type it into their app. The follow-on
    `/confirm` call returns it to the server to be persisted.
    """
    from scripts.core import auth, totp

    payload = payload or {}
    issuer = str(payload.get("issuer", "")).strip() or auth.DEFAULT_ISSUER
    label = str(payload.get("label", "")).strip() or auth.DEFAULT_LABEL

    if auth.is_totp_enabled():
        return {
            "ok": False,
            "error": "already_enrolled",
            "message": "TOTP is already enabled; disable it first to re-enroll",
        }

    secret = totp.generate_secret()
    uri = totp.provisioning_uri(secret, label=label, issuer=issuer)
    return {
        "ok": True,
        "secret": secret,
        "provisioning_uri": uri,
        "issuer": issuer,
        "label": label,
    }


@audit_log.audit_endpoint(action="auth_totp_confirm")
def api_auth_totp_confirm(payload: dict | None) -> dict:
    """Confirm + persist the pending TOTP enrollment.

    Payload:
        secret:   the base32 secret from `/begin` (required)
        code:     6-digit TOTP code generated from the secret in the
                  authenticator app (required)
        issuer:   optional override
        label:    optional override

    Verifies that `code` is valid for `secret` (with the standard
    ±30s drift window). On success: persists the secret + flips
    `enabled=True`. On failure: nothing is written; the publisher
    can retry.
    """
    from scripts.core import auth, totp

    payload = payload or {}
    secret = str(payload.get("secret", "")).strip()
    code = str(payload.get("code", "")).strip()
    if not secret:
        return {"ok": False, "error": "missing_secret", "message": "payload.secret required"}
    if not code:
        return {"ok": False, "error": "missing_code", "message": "payload.code required"}

    if auth.is_totp_enabled():
        return {
            "ok": False,
            "error": "already_enrolled",
            "message": "TOTP is already enabled; disable it first to re-enroll",
        }

    if not totp.verify_code(secret, code):
        return {
            "ok": False,
            "error": "invalid_code",
            "message": "TOTP code doesn't match; check the authenticator app and retry",
        }

    issuer = str(payload.get("issuer", "")).strip() or auth.DEFAULT_ISSUER
    label = str(payload.get("label", "")).strip() or auth.DEFAULT_LABEL
    auth.enroll_totp(secret, issuer=issuer, label=label)
    return {
        "ok": True,
        "totp_enabled": True,
        "issuer": issuer,
        "label": label,
        "message": "TOTP enrolled. Mutating endpoints now require Authorization: Bearer <token>:<code>.",
    }


@audit_log.audit_endpoint(action="auth_totp_disable")
def api_auth_totp_disable(payload: dict | None) -> dict:
    """Disable TOTP if the supplied code verifies against the current
    secret. Refuses to disable without proof — prevents an attacker
    who somehow bypassed the gate from also nuking 2FA.

    Payload:
        code: 6-digit TOTP code (required)
    """
    from scripts.core import auth, totp

    payload = payload or {}
    code = str(payload.get("code", "")).strip()
    if not code:
        return {"ok": False, "error": "missing_code", "message": "payload.code required"}

    if not auth.is_totp_enabled():
        return {
            "ok": True,
            "totp_enabled": False,
            "removed": False,
            "message": "TOTP was not enabled; nothing to disable.",
        }

    secret = auth.get_totp_secret()
    if not secret or not totp.verify_code(secret, code):
        return {
            "ok": False,
            "error": "invalid_code",
            "message": "TOTP code doesn't match; refusing to disable",
        }

    auth.disable_totp()
    return {
        "ok": True,
        "totp_enabled": False,
        "removed": True,
        "message": "TOTP disabled. Admin token alone now gates mutations.",
    }
