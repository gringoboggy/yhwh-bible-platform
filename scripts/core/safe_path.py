"""
safe_path.py — path-traversal defense for user-supplied path inputs.

Phase ξ.2 (2026-05-08). Multiple endpoints accept a relative path
from a user (cover serve route, future audio asset routes, future
download routes) and resolve it inside a known-safe root. Each
endpoint reinvented the same string-level rejection + Path.resolve()
+ relative_to() check; ξ.2 extracts the proven pattern as a single
helper so new routes can call one function instead of copying the
recipe.

Public API:
    SafePathError          — raised on any traversal-class violation
    resolve_under(safe_root, user_path) -> Path
        Resolve ``user_path`` against ``safe_root``, verify it stays
        under that root, and return the absolute resolved path.

Threat model (recap from CLAUDE_PROJECT_RULES §9 + ξ.2):

    A user-controllable string segment ends up as part of a filesystem
    path the server reads or writes. Without sanitization, attackers
    (or innocent typos) can supply ``../../etc/passwd``, an absolute
    path, or hidden-directory segments to escape the safe root. We
    reject at the cheap string layer first AND verify via filesystem
    resolve() — defense in depth.

Rejection classes:
    - empty input
    - absolute paths (POSIX `/foo` or Windows `C:\\foo`)
    - parent-traversal segments (``..``)
    - hidden segments (``.foo``) — keeps the storage area clean and
      defends against ``.git``, ``.ssh``, etc. shenanigans
    - control characters / NUL bytes
    - resolved path that, after Path.resolve(), no longer lives
      under the safe root (catches symlink trickery)
"""

from __future__ import annotations

from pathlib import Path

# Reject NUL and any C0 control character. These can confuse OS-level
# path APIs and have shown up in real-world traversal payloads.
_FORBIDDEN_CHARS = {chr(c) for c in range(32)} | {chr(127)}


class SafePathError(ValueError):
    """Raised when ``user_path`` violates any traversal-class rule."""


def _check_string_safety(user_path: str) -> None:
    """Cheap string-level rejection before touching the filesystem.
    Order of checks matters: we want to reject obvious attack
    payloads BEFORE Path.resolve() (which could itself misbehave on
    pathological input)."""
    if not isinstance(user_path, str):
        raise SafePathError(
            f"path must be a string, got {type(user_path).__name__}"
        )
    if not user_path:
        raise SafePathError("path must not be empty")
    if len(user_path) > 1024:
        raise SafePathError("path too long (max 1024 chars)")

    # NUL / control chars — sanity reject before any further parsing.
    bad = [c for c in user_path if c in _FORBIDDEN_CHARS]
    if bad:
        raise SafePathError(
            f"path contains control character(s) (codepoints "
            f"{', '.join(str(ord(c)) for c in bad[:3])})"
        )

    # Normalize separators: accept both `/` and `\`, store/check as
    # posix-style for consistency.
    norm = user_path.replace("\\", "/")

    # Absolute paths — POSIX or Windows drive-letter form.
    if norm.startswith("/"):
        raise SafePathError(
            f"path must be relative, not absolute: {user_path!r}"
        )
    # Windows drive-letter (e.g. `C:/foo`).
    if len(norm) >= 2 and norm[1] == ":":
        raise SafePathError(
            f"path must be relative, not absolute: {user_path!r}"
        )

    # UNC-style paths — `//host/share/...` already caught by the
    # leading-slash check above; explicit just in case.
    if norm.startswith("//"):
        raise SafePathError(
            f"UNC paths are not allowed: {user_path!r}"
        )

    parts = [p for p in norm.split("/") if p]
    if any(p == ".." for p in parts):
        raise SafePathError(
            f"path may not contain '..': {user_path!r}"
        )
    # Hidden segments — `.git`, `.ssh`, dotfile-by-mistake. The
    # current `.` segment is implicitly stripped by the filter above.
    if any(p.startswith(".") for p in parts):
        raise SafePathError(
            f"path may not contain hidden segments: {user_path!r}"
        )


def resolve_under(safe_root: Path | str, user_path: str) -> Path:
    """Resolve ``user_path`` inside ``safe_root`` with full traversal
    defense.

    Returns the absolute, resolved Path. Raises SafePathError on any
    violation — the caller turns that into a 403 / 404 response (the
    §9 "Add a new static-file route" recipe specifies 403/404 to
    avoid information disclosure about which path failed).

    Defense layers:
      1. String-level rejection of empty, oversized, absolute,
         control-char, ``..``, hidden, UNC.
      2. Filesystem resolve() to canonicalize.
      3. Path.relative_to(safe_root) to verify the resolved path
         hasn't escaped via symlinks or other indirection.

    Note: the resolved file may or may not exist; this helper is
    responsible only for the *path* being safe. Callers check
    ``.is_file()`` / ``.is_dir()`` themselves and emit 404 as
    appropriate.
    """
    _check_string_safety(user_path)

    safe_root_resolved = Path(safe_root).resolve()
    if not safe_root_resolved.exists():
        # safe_root must exist before we can sandbox under it. This
        # is a programmer error (calling code passed a bogus root),
        # not a user error — still raise SafePathError so the route
        # can return 500 cleanly.
        raise SafePathError(
            f"safe_root does not exist: {safe_root_resolved}"
        )

    candidate = (safe_root_resolved / user_path).resolve()

    # Final containment check — this is the defense against symlink
    # trickery. Even if the path looked safe at the string layer,
    # resolve() may have followed a symlink that pointed outside the
    # safe root.
    try:
        candidate.relative_to(safe_root_resolved)
    except ValueError:
        raise SafePathError(
            f"resolved path escapes safe_root: {user_path!r}"
        ) from None

    return candidate
