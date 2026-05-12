"""ξ.21 — TOTP (RFC 6238) implementation (2026-05-12).

Pure-stdlib HMAC-SHA1-based time-based one-time password generator
and verifier. Used by the admin-auth gate when 2FA is enabled
(ξ.21); also provides the otpauth:// provisioning URI publishers
paste into their authenticator app (Google Authenticator, Authy,
1Password, etc.).

No external dependencies — the project's stdlib-first invariant
(CLAUDE_PROJECT_RULES §6.3 "no build step") forbids pyotp / qrcode /
similar. RFC 6238's algorithm is ~30 lines.

**Public API**:
    generate_secret(*, length_bytes=20)        — base32 string (default 160 bits)
    current_code(secret, *, now=None)          — 6-digit code as str
    verify_code(secret, code, *, now=None,
                drift_steps=1)                  — bool (±drift_steps × 30s window)
    provisioning_uri(secret, *, label, issuer) — otpauth://totp/... URL

**RFC 6238 conformance**:
    - HMAC-SHA1 (the RFC's default; SHA256/SHA512 are profile
      extensions and not needed for the common authenticator-app
      ecosystem).
    - 30-second time step (X = 30, T0 = 0 = Unix epoch).
    - 6-digit code (the default digit count).
    - Dynamic-truncation per RFC 4226 §5.3 (used by HOTP, which TOTP
      builds on).

Verified against RFC 6238 Appendix B test vectors (HMAC-SHA1 column);
see `tests/test_totp_xi21.py::TestXi21Rfc6238Vectors`.

**Defenses against common pitfalls**:
    - Constant-time string comparison in `verify_code` (hmac.compare_digest).
    - Drift window (default ±1 step = ±30s) so a clock skew of 15-30s
      between server and authenticator app still authenticates.
    - Secret is base32-encoded (the authenticator-app de-facto standard).
    - `provisioning_uri` URL-encodes label + issuer so spaces / special
      chars don't break the otpauth URL parser.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import secrets
import struct
import time
import urllib.parse
from typing import Optional


# RFC 6238 defaults — pinned so changing them is a deliberate decision.
DEFAULT_DIGITS = 6
DEFAULT_STEP_SECONDS = 30
DEFAULT_T0 = 0  # Unix epoch
DEFAULT_ALGORITHM = "SHA1"  # RFC 6238 §4 — also the de-facto authenticator-app standard
DEFAULT_DRIFT_STEPS = 1  # ±1 × 30s window (matches Google Authenticator policy)

SECRET_BYTES_DEFAULT = 20  # 160 bits — RFC 4226 §4 recommended minimum


def generate_secret(*, length_bytes: int = SECRET_BYTES_DEFAULT) -> str:
    """Generate a new base32-encoded shared secret.

    Default 20 bytes (160 bits) — RFC 4226 §4 recommended minimum.
    Base32 is the authenticator-app de-facto encoding (otpauth://
    URLs carry secrets in base32).

    `secrets.token_bytes` uses the OS cryptographic RNG (urandom on
    Linux/Mac, BCryptGenRandom on Windows). Suitable for security
    secrets.
    """
    if length_bytes <= 0:
        raise ValueError("length_bytes must be positive")
    raw = secrets.token_bytes(length_bytes)
    # base32 without padding — authenticator apps tolerate either but
    # unpadded is cleaner in otpauth:// URLs.
    return base64.b32encode(raw).decode("ascii").rstrip("=")


def _decode_secret(secret: str) -> bytes:
    """Decode a base32 secret string to raw bytes. Pads to a multiple
    of 8 characters first (base32 standard requires padding; we accept
    both padded and unpadded for caller convenience)."""
    cleaned = secret.strip().upper().replace(" ", "")
    # Re-pad to a multiple of 8.
    missing = (-len(cleaned)) % 8
    padded = cleaned + ("=" * missing)
    try:
        return base64.b32decode(padded, casefold=False)
    except (ValueError, binascii.Error) as e:
        raise ValueError(f"invalid base32 secret: {e}") from e


def _hotp(secret_bytes: bytes, counter: int, *, digits: int = DEFAULT_DIGITS) -> str:
    """Compute an HOTP code per RFC 4226 §5. Pure function.

    `counter` is an 8-byte big-endian integer; `secret_bytes` is the
    raw shared secret. Returns a `digits`-length zero-padded string.
    """
    msg = struct.pack(">Q", counter)
    digest = hmac.new(secret_bytes, msg, hashlib.sha1).digest()
    # Dynamic truncation per RFC 4226 §5.3.
    offset = digest[-1] & 0x0F
    bin_code = (
        ((digest[offset] & 0x7F) << 24)
        | ((digest[offset + 1] & 0xFF) << 16)
        | ((digest[offset + 2] & 0xFF) << 8)
        | (digest[offset + 3] & 0xFF)
    )
    code = bin_code % (10**digits)
    return str(code).zfill(digits)


def _time_counter(*, now: Optional[float] = None) -> int:
    """Translate the current Unix time to a TOTP counter (30-second
    steps since the epoch). Inject `now` for deterministic tests."""
    current = now if now is not None else time.time()
    return int(current - DEFAULT_T0) // DEFAULT_STEP_SECONDS


def current_code(secret: str, *, now: Optional[float] = None) -> str:
    """Return the current 6-digit TOTP code for `secret`.

    `now` is injectable for tests. Production callers leave it None
    so `time.time()` is used."""
    secret_bytes = _decode_secret(secret)
    counter = _time_counter(now=now)
    return _hotp(secret_bytes, counter)


def verify_code(
    secret: str,
    code: str,
    *,
    now: Optional[float] = None,
    drift_steps: int = DEFAULT_DRIFT_STEPS,
) -> bool:
    """Check whether `code` is a valid TOTP for `secret` at `now` (or
    real-time when `now=None`), tolerating ±`drift_steps × 30s` of
    clock skew between server and authenticator app.

    Constant-time comparison (`hmac.compare_digest`) so timing
    leaks can't bisect the digit space. Returns False on malformed
    code rather than raising — the caller treats every failure as a
    generic "invalid code".
    """
    if not isinstance(code, str):
        return False
    code = code.strip()
    if not code.isdigit() or len(code) != DEFAULT_DIGITS:
        return False
    try:
        secret_bytes = _decode_secret(secret)
    except ValueError:
        return False
    base_counter = _time_counter(now=now)
    for delta in range(-drift_steps, drift_steps + 1):
        candidate = _hotp(secret_bytes, base_counter + delta)
        if hmac.compare_digest(candidate, code):
            return True
    return False


def provisioning_uri(secret: str, *, label: str, issuer: str = "YHWH Bible") -> str:
    """Build an otpauth://totp/... URI for the authenticator app.

    Per the otpauth URI spec (de-facto standard maintained by Google
    Authenticator at github.com/google/google-authenticator/wiki/Key-Uri-Format):

        otpauth://totp/<Issuer>:<Label>?secret=<base32>&issuer=<Issuer>&algorithm=SHA1&digits=6&period=30

    `label` is typically an account identifier (e.g. "admin@ebible").
    `issuer` is the publisher-facing app name shown next to the code
    in the authenticator UI.

    The label + issuer are URL-encoded so spaces / special chars
    don't break the URL parser. The base32 secret is passed as-is
    (already URL-safe).
    """
    encoded_label = urllib.parse.quote(label, safe="")
    encoded_issuer = urllib.parse.quote(issuer, safe="")
    # The path is "issuer:label" so authenticator apps display both.
    path = f"{encoded_issuer}:{encoded_label}"
    params = urllib.parse.urlencode(
        {
            "secret": secret,
            "issuer": issuer,
            "algorithm": DEFAULT_ALGORITHM,
            "digits": DEFAULT_DIGITS,
            "period": DEFAULT_STEP_SECONDS,
        }
    )
    return f"otpauth://totp/{path}?{params}"
