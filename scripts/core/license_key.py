"""ξ.26 — license-key signing + verification (2026-05-12).

Per PROPOSAL §6 Track G ξ.26: "Soft enforcement: degraded UI on fail,
not crash." The proposal originally specified Ed25519. This
implementation substitutes HMAC-SHA256 because:

1. **Stdlib-only invariant** (CLAUDE_PROJECT_RULES §6.3) forbids
   the `cryptography` library — its C extensions + ~25 MB install
   conflict with "no build step / stdlib only on backend".
2. **Threat model for soft enforcement** doesn't justify asymmetric
   crypto. A determined attacker can already read the source code
   (this is a single-binary Python deployment). HMAC gives buyers
   a verifiable tag for audit + analytics without pretending to
   stop piracy — which v1 explicitly doesn't try to do per §9.5.
3. **Ed25519 upgrade path** = ξ.26.x. If/when hard enforcement
   becomes a requirement (commercial piracy is measurable per §9.5),
   the format prefix `LK1` becomes `LK2` and the signing path swaps
   for an Ed25519 implementation. Verification side-by-side during
   the transition is straightforward — `verify()` dispatches on the
   prefix.

**License key format** (LK1 — HMAC-SHA256):

    LK1:<edition_id>:<expires_iso>:<issued_at_iso>:<base64-urlsafe-hmac>

    where the HMAC is computed over:
        "LK1:<edition_id>:<expires_iso>:<issued_at_iso>"
    keyed by the publisher's signing secret.

**Configuration**: `EBIBLE_LICENSE_SIGNING_KEY` env var holds the
publisher's signing secret (any non-empty string; longer is better;
random base64 is the conventional shape). When unset:
- `mint()` raises (can't sign without a secret).
- `verify()` returns `{valid: True, reason: "no_enforcement"}` — the
  fail-open default lets development environments + first-run
  installations operate without licensing friction.

**Public API**:
    LICENSE_PREFIX                  current format prefix ("LK1")
    is_enforced()                   bool — signing key configured?
    mint(edition_id, *,
         expires_iso, secret=None,
         issued_at_iso=None)        license string
    verify(license_str, *,
           secret=None,
           now=None)                result envelope dict
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import datetime, timezone


LICENSE_PREFIX = "LK1"
ENV_SIGNING_KEY = "EBIBLE_LICENSE_SIGNING_KEY"


def _now_iso() -> str:
    """ISO-8601 UTC timestamp — same format as event_log + distribution."""
    return datetime.now(timezone.utc).isoformat()


def _get_signing_key(override: str | None = None) -> str | None:
    """Resolve the active signing key. `override` wins; else the
    env var; else None (unconfigured)."""
    if override is not None:
        s = override.strip()
        return s if s else None
    env = (os.environ.get(ENV_SIGNING_KEY) or "").strip()
    return env if env else None


def is_enforced() -> bool:
    """True iff a signing key is configured. False → license
    validation falls open (every license verifies as valid with
    reason='no_enforcement'). Development + first-run install
    convenience."""
    return _get_signing_key() is not None


def _hmac(payload: str, secret: str) -> str:
    """Compute the base64-urlsafe HMAC-SHA256 of `payload` keyed by
    `secret`. Both inputs are utf-8-encoded. Returns the digest
    WITHOUT base64 padding (cleaner in license-key strings)."""
    digest = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def mint(
    edition_id: str,
    *,
    expires_iso: str,
    secret: str | None = None,
    issued_at_iso: str | None = None,
) -> str:
    """Build a signed license key string.

    Args:
        edition_id: the edition this license authorizes (e.g.
            "catholic-study"). Must be non-empty. Colons forbidden
            (would break the LK1 string format).
        expires_iso: ISO-8601 UTC timestamp when the key stops
            validating. Required.
        secret: signing secret override. Defaults to
            `EBIBLE_LICENSE_SIGNING_KEY` env var. Raises ValueError
            if unset.
        issued_at_iso: optional issue timestamp; defaults to now.

    Returns:
        The signed license string in the LK1 format.

    Raises:
        ValueError: edition_id empty / contains colons / signing key
            unset.
    """
    edition_id = (edition_id or "").strip()
    if not edition_id:
        raise ValueError("edition_id must be non-empty")
    if ":" in edition_id:
        raise ValueError("edition_id must not contain ':'")
    if not (expires_iso or "").strip():
        raise ValueError("expires_iso must be non-empty")
    signing_key = _get_signing_key(secret)
    if not signing_key:
        raise ValueError(f"signing key not configured (set {ENV_SIGNING_KEY} env var or pass secret=)")
    issued = (issued_at_iso or "").strip() or _now_iso()
    payload = f"{LICENSE_PREFIX}:{edition_id}:{expires_iso}:{issued}"
    sig = _hmac(payload, signing_key)
    return f"{payload}:{sig}"


def verify(
    license_str: str,
    *,
    secret: str | None = None,
    now: datetime | None = None,
) -> dict:
    """Verify a license string. Returns an envelope dict:

        {
          "valid": bool,
          "edition_id": str (when parseable),
          "expires_iso": str (when parseable),
          "issued_at_iso": str (when parseable),
          "reason": "ok" | "no_enforcement" | "missing" |
                    "wrong_format" | "unsupported_version" |
                    "bad_signature" | "expired"
        }

    `secret` overrides the env-var lookup (used by tests). `now`
    overrides datetime.now (used by tests).

    Fail-open when no signing key is configured: returns
    `{valid: True, reason: "no_enforcement"}` even on a missing or
    malformed `license_str`. Development convenience.
    """
    signing_key = _get_signing_key(secret)
    if signing_key is None:
        return {"valid": True, "reason": "no_enforcement"}

    if not license_str or not isinstance(license_str, str):
        return {"valid": False, "reason": "missing"}

    license_str.split(":")
    # Expected: prefix(1) + edition(1) + expires(1) + issued(1) +
    # sig(1) = 5 colon-separated parts (the ISO timestamps don't
    # contain ':' — we serialise them via isoformat() which uses
    # '-' for date + 'T' for separator + ':' for time-of-day...
    # ACTUALLY iso timestamps DO contain colons: "2026-05-12T18:30:00+00:00".
    # The expires_iso + issued_at_iso fields each have multiple ':' inside.
    #
    # Format is therefore parsed positionally: split into MAX 5
    # parts from the LEFT using rsplit on the signature (which has
    # no colons since it's base64-urlsafe).
    # Re-parse:
    if not license_str.startswith(LICENSE_PREFIX + ":"):
        # Future LK2 prefix dispatch would go here.
        prefix_dot = license_str.split(":", 1)[0]
        if prefix_dot == LICENSE_PREFIX:
            return {"valid": False, "reason": "wrong_format"}
        return {"valid": False, "reason": "unsupported_version"}

    # Strip the prefix; split the remaining "edition_id:expires:issued:sig"
    # from the LEFT. edition_id has no colons; expires/issued/sig are
    # the next three fields.
    body = license_str[len(LICENSE_PREFIX) + 1 :]
    # Rightmost ':' is between issued_at_iso and sig.
    head, _, sig = body.rpartition(":")
    if not sig or not head:
        return {"valid": False, "reason": "wrong_format"}
    # `head` is now "edition_id:expires_iso:issued_at_iso". The
    # rightmost ':' is between expires_iso and issued_at_iso —
    # but iso timestamps contain ':' too. The convention: timestamps
    # serialised via datetime.isoformat() are 19+ chars and contain
    # the canonical 'T' separator. We use the FIRST ':' as the
    # edition_id boundary.
    edition_id, _, ts_part = head.partition(":")
    if not edition_id or not ts_part:
        return {"valid": False, "reason": "wrong_format"}
    # ts_part is "expires_iso:issued_at_iso". The two timestamps are
    # separated by ':' (the same character appearing inside both).
    # Convention: we serialised them in mint() as
    # f"{expires_iso}:{issued_at_iso}" — but expires_iso ends with
    # "+00:00" so the SECOND-to-LAST ':' is the field boundary.
    # Safer: search for the 'T' separator of issued_at_iso.
    # Find the issued_at_iso boundary: it starts with "<YYYY>-<MM>-<DD>T"
    # at some offset. The expires_iso ends just before that pattern.
    import re

    # Look for ":<digit><digit><digit><digit>-<digit><digit>-<digit><digit>T"
    # to find the start of issued_at_iso within ts_part.
    m = re.search(r":(\d{4}-\d{2}-\d{2}T)", ts_part)
    if not m:
        return {"valid": False, "reason": "wrong_format"}
    expires_iso = ts_part[: m.start()]
    issued_at_iso = ts_part[m.start() + 1 :]
    if not expires_iso or not issued_at_iso:
        return {"valid": False, "reason": "wrong_format"}

    payload = f"{LICENSE_PREFIX}:{edition_id}:{expires_iso}:{issued_at_iso}"
    expected_sig = _hmac(payload, signing_key)
    if not hmac.compare_digest(sig, expected_sig):
        return {
            "valid": False,
            "reason": "bad_signature",
            "edition_id": edition_id,
            "expires_iso": expires_iso,
            "issued_at_iso": issued_at_iso,
        }

    # Check expiry.
    now_dt = now or datetime.now(timezone.utc)
    try:
        expires_dt = datetime.fromisoformat(expires_iso)
    except ValueError:
        return {
            "valid": False,
            "reason": "wrong_format",
            "edition_id": edition_id,
        }
    if expires_dt.tzinfo is None:
        expires_dt = expires_dt.replace(tzinfo=timezone.utc)
    if now_dt.tzinfo is None:
        now_dt = now_dt.replace(tzinfo=timezone.utc)
    if now_dt > expires_dt:
        return {
            "valid": False,
            "reason": "expired",
            "edition_id": edition_id,
            "expires_iso": expires_iso,
            "issued_at_iso": issued_at_iso,
        }

    return {
        "valid": True,
        "reason": "ok",
        "edition_id": edition_id,
        "expires_iso": expires_iso,
        "issued_at_iso": issued_at_iso,
    }
