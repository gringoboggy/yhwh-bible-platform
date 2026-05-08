"""
validation.py — input-shape validators for API endpoints.

Phase ξ.1 (2026-05-08). Earlier endpoints validated input ad-hoc
inline; later endpoints (the §9 pure-function-API pattern) use
structured `{status, code, http, message}` returns. ξ.1 extracts
the shared primitive validators that every endpoint can call so
input-validation logic doesn't drift across surfaces.

Public API:
    ValidationError                     — raised on shape failure
    require_string(value, *, name, max_len=…)            -> str
    require_short_string(value, *, name)                 -> str
    validate_book_code(value)                            -> str
    validate_edition_id(value)                           -> str
    validate_kind_code(value)                            -> str
    validate_chapter(value)                              -> int
    validate_verse(value)                                -> int
    validate_path_segment(value)                         -> str

Each validator returns the canonicalized value on success and raises
`ValidationError(message)` on failure. Endpoints translate that into
a structured 400 response (the §9 dict-shape contract).

Format conventions (verified against current content/):
    book code   :  lowercase, 1-4 chars, [a-z0-9] only
                   examples: gen, exo, 1ki, 2ch, 3jn
    edition id  :  lowercase letters + hyphens, 1-64 chars
                   examples: ethiopian-tewahedo, catholic-study
    kind code   :  lowercase letters + hyphens, 1-64 chars
                   examples: lang-hebrew, comm-doctrine, xref-citation
    chapter     :  integer 1-200 (Psalm 119 = max scripture chapter)
    verse       :  integer 1-200 (Ps 119:176 + safety margin)

These bounds are deliberately generous — the platform may host
non-canonical apparatus where chapter/verse numbers run higher than
strict scripture ranges. The point is to reject negative numbers,
absurd values, and attack payloads, not to enforce theology.
"""

from __future__ import annotations

import re

# ----------------------------------------------------------------------
# Patterns and bounds
# ----------------------------------------------------------------------

_BOOK_CODE_RE = re.compile(r"^[a-z0-9]{1,4}$")
_EDITION_ID_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
_KIND_CODE_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
_PATH_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]{1,255}$")

DEFAULT_STRING_MAX = 1024
SHORT_STRING_MAX = 256
CHAPTER_MIN, CHAPTER_MAX = 1, 200
VERSE_MIN, VERSE_MAX = 1, 200


class ValidationError(ValueError):
    """Raised when a validator rejects an input. The message is
    user-safe (no stack traces, no internal-state disclosure) so it
    can be passed straight into a 400-response payload."""


# ----------------------------------------------------------------------
# String primitives
# ----------------------------------------------------------------------


def require_string(value: object, *,
                   name: str,
                   max_len: int = DEFAULT_STRING_MAX,
                   allow_empty: bool = False) -> str:
    """Return value as a string after type + length checks.

    Reject non-string inputs (None, int, list, dict). Reject strings
    longer than `max_len` (defends against memory-exhaustion via
    pathological input). Empty strings rejected by default; pass
    `allow_empty=True` to permit (a few endpoints semantically allow
    "" to mean "clear this field")."""
    if value is None:
        raise ValidationError(f"{name}: required (got None)")
    if not isinstance(value, str):
        raise ValidationError(
            f"{name}: must be a string, got {type(value).__name__}"
        )
    if not allow_empty and not value:
        raise ValidationError(f"{name}: must not be empty")
    if len(value) > max_len:
        raise ValidationError(
            f"{name}: too long ({len(value)} chars; max {max_len})"
        )
    return value


def require_short_string(value: object, *, name: str,
                          allow_empty: bool = False) -> str:
    """Like require_string but with the SHORT_STRING_MAX cap (256).
    Use for labels, short titles, ids — anything that should never
    legitimately be a paragraph. Body-text fields use
    require_string."""
    return require_string(
        value, name=name, max_len=SHORT_STRING_MAX,
        allow_empty=allow_empty,
    )


# ----------------------------------------------------------------------
# Domain ids
# ----------------------------------------------------------------------


def validate_book_code(value: object, *, name: str = "book_code") -> str:
    """Match the books.yaml `code` field shape (e.g. 'gen', '1ki')."""
    s = require_short_string(value, name=name)
    if not _BOOK_CODE_RE.match(s):
        raise ValidationError(
            f"{name}: must be 1-4 lowercase alphanumeric chars; got {s!r}"
        )
    return s


def validate_edition_id(value: object, *, name: str = "edition_id") -> str:
    """Match the editions.yaml `id` field shape (e.g.
    'ethiopian-tewahedo', 'catholic-study')."""
    s = require_short_string(value, name=name)
    if not _EDITION_ID_RE.match(s):
        raise ValidationError(
            f"{name}: must start with a lowercase letter and contain "
            f"only lowercase letters, digits, and hyphens; got {s!r}"
        )
    return s


def validate_kind_code(value: object, *, name: str = "kind_code") -> str:
    """Match the kinds.yaml `code` field shape (e.g. 'lang-hebrew',
    'comm-doctrine', 'xref-citation')."""
    s = require_short_string(value, name=name)
    if not _KIND_CODE_RE.match(s):
        raise ValidationError(
            f"{name}: must start with a lowercase letter and contain "
            f"only lowercase letters, digits, and hyphens; got {s!r}"
        )
    return s


def validate_path_segment(value: object, *,
                           name: str = "path_segment") -> str:
    """Match a single safe filename: alphanumerics, dot, dash,
    underscore. NO slashes (single segment only). For multi-segment
    paths, use scripts/core/safe_path.resolve_under instead."""
    s = require_short_string(value, name=name)
    if not _PATH_SEGMENT_RE.match(s):
        raise ValidationError(
            f"{name}: must be a single safe filename (alphanumerics, "
            f"dot, dash, underscore only); got {s!r}"
        )
    if s in (".", ".."):
        raise ValidationError(
            f"{name}: must not be '.' or '..'; got {s!r}"
        )
    return s


# ----------------------------------------------------------------------
# Numeric primitives
# ----------------------------------------------------------------------


def _coerce_int(value: object, *, name: str) -> int:
    """Accept int directly or a stringified int. Reject everything else."""
    if isinstance(value, bool):
        # bool is a subclass of int; reject explicitly to avoid
        # surprise (True being treated as chapter 1, etc.).
        raise ValidationError(f"{name}: must be an integer (got bool)")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            raise ValidationError(
                f"{name}: not an integer; got {value!r}"
            ) from None
    raise ValidationError(
        f"{name}: must be an integer; got {type(value).__name__}"
    )


def validate_chapter(value: object, *, name: str = "chapter") -> int:
    n = _coerce_int(value, name=name)
    if not (CHAPTER_MIN <= n <= CHAPTER_MAX):
        raise ValidationError(
            f"{name}: out of range [{CHAPTER_MIN}-{CHAPTER_MAX}]; got {n}"
        )
    return n


def validate_verse(value: object, *, name: str = "verse") -> int:
    n = _coerce_int(value, name=name)
    if not (VERSE_MIN <= n <= VERSE_MAX):
        raise ValidationError(
            f"{name}: out of range [{VERSE_MIN}-{VERSE_MAX}]; got {n}"
        )
    return n


# ----------------------------------------------------------------------
# Composite helper for §9 endpoints
# ----------------------------------------------------------------------


def to_error_dict(exc: ValidationError, *, http: int = 400) -> dict:
    """Translate a ValidationError into the §9 dict-shape contract:
    ``{"status": "error", "code": "validation_error", "http": 400,
       "message": "<exc message>"}``.

    Endpoints catch ValidationError, call this, and pass the result
    to `_send_dict_result` (or equivalent) for a structured 400."""
    return {
        "status": "error",
        "code": "validation_error",
        "http": http,
        "message": str(exc),
    }
