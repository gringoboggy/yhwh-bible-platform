"""
paths.py — Single source of truth for project paths (Phase ω.5).

Two file roots in this project:

1. **Repo root** — where the source code lives. Always the parent of
   ``scripts/``. Read-only at runtime; this is where ``scripts/``,
   ``tests/``, ``dev/``, and the bundled ``content/`` template live.
   Compiled into a desktop binary as a read-only resource.

2. **Content root** — where user-mutable data lives. In a development
   checkout this is the in-tree ``<repo>/content/`` directory (so
   editing during development feels seamless). In an installed
   desktop binary, this is the platform's user-data dir
   (``%APPDATA%\\YHWH`` on Windows, ``~/Library/Application
   Support/YHWH`` on macOS, ``~/.local/share/YHWH`` on Linux).

The resolver in this module makes the right choice automatically:

- If ``YHWH_CONTENT_ROOT`` env var is set, use that (CI, tests, manual
  override).
- Else if ``<repo>/content/`` exists with the canonical ``editions.yaml``
  inside it, use the in-tree dir (dev mode).
- Else use the platform user-data dir (installed mode), bootstrapping
  it from the bundled template if it doesn't yet exist (the bootstrap
  is the migration helper's job; this module just *reports* the path).

Why this matters:

- The ω.5 phase exists so θ.1/θ.2 (the desktop binary) can ship.
  Bundled .app/.exe payloads are read-only on macOS (Gatekeeper) and
  on Windows (Program Files); user-mutable data must live elsewhere.
- A single resolver beats 97 occurrences of
  ``Path(__file__).resolve().parent.parent / "content"`` scattered
  through the codebase. Each occurrence is a place a future migration
  could miss.
- Tests use ``set_content_root_for_testing(path)`` to point at a
  ``tmp_path`` without touching real user data.

Migration approach (rolling, ω.5 → ω.5.x):
- ω.5 ships this module + the canonical ``scripts/core/`` consumers
  (sources, translations, config, covers, traditions) migrated to
  the resolver.
- ω.5.1+ migrate the at-scale drivers and ``scripts/web.py`` (the
  bulk of the remaining 97 occurrences) as rolling sub-phases. The
  in-tree fallback means un-migrated call sites continue to work
  during the rolling migration.
"""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path

__all__ = [
    "repo_root",
    "user_data_root",
    "content_root",
    "set_content_root_for_testing",
    "reset_content_root",
    "notes_dir",
    "candidates_dir",
    "sources_dir",
    "translations_dir",
    "covers_dir",
    "audio_dir",
    "books_yaml",
    "kinds_yaml",
    "categories_yaml",
    "themes_yaml",
    "canons_yaml",
    "editions_yaml",
    "traditions_yaml",
    "exports_dir",
    "epub_working_dir",
    "builds_dir",
    "backups_dir",
    "tesseract_binary",
    "reset_tesseract_binary",
]


# Override hooks. Production code never sets these directly; tests use
# ``set_content_root_for_testing``; CLI users may set
# ``YHWH_CONTENT_ROOT`` in the environment.
_TEST_OVERRIDE: Path | None = None
_ENV_VAR = "YHWH_CONTENT_ROOT"
# Writable build-output root override (exports/, builds/, backups). Lets a
# user relocate regenerable output to a roomier drive; honored in every mode.
_DATA_DIR_ENV = "YHWH_DATA_DIR"


def repo_root() -> Path:
    """Return the on-disk location of the repository (read-only at
    runtime). This is the parent of ``scripts/`` — i.e., one level
    above this module's parent. Stable across dev and installed
    builds; in an installed binary this points at the bundled
    read-only resource directory."""
    # paths.py lives at <repo>/scripts/core/paths.py → up 3 → <repo>
    return Path(__file__).resolve().parent.parent.parent


def user_data_root() -> Path:
    """Platform-specific writable user-data directory for the project.

    - Windows : ``%APPDATA%\\YHWH`` (defaults to
      ``C:\\Users\\<user>\\AppData\\Roaming\\YHWH``).
    - macOS   : ``~/Library/Application Support/YHWH``.
    - Linux   : ``$XDG_DATA_HOME/YHWH`` if set, else ``~/.local/share/YHWH``.

    Does NOT create the directory; that's the migration helper's job.
    Returning the path is enough for the resolver — call sites that
    actually write should ``mkdir(parents=True, exist_ok=True)`` as
    needed (the existing ``notes_io.atomic_write`` already does this
    for its parent directory)."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "YHWH"
        return Path.home() / "AppData" / "Roaming" / "YHWH"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "YHWH"
    # Linux + other POSIX: respect XDG_DATA_HOME if set
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "YHWH"
    return Path.home() / ".local" / "share" / "YHWH"


def _detect_in_tree_content() -> Path | None:
    """Return the in-tree content/ dir IFF it exists AND has the
    canonical ``editions.yaml`` marker (so a bare empty ``content/``
    directory or one missing the marker doesn't shadow a real
    user-data dir). Returns ``None`` otherwise."""
    candidate = repo_root() / "content"
    if (candidate / "editions.yaml").is_file():
        return candidate
    return None


def content_root() -> Path:
    """Resolve the active content root.

    Resolution order (highest precedence first):
      1. The testing override set via
         ``set_content_root_for_testing``.
      2. The ``YHWH_CONTENT_ROOT`` environment variable.
      3. The in-tree ``<repo>/content/`` directory IFF it contains
         the ``editions.yaml`` marker (dev mode).
      4. The platform user-data dir (installed mode).

    The result is cached on first call; tests that change the
    underlying state should call ``reset_content_root()``."""
    if _TEST_OVERRIDE is not None:
        return _TEST_OVERRIDE
    return _content_root_cached()


@lru_cache(maxsize=1)
def _content_root_cached() -> Path:
    env = os.environ.get(_ENV_VAR)
    if env:
        return Path(env).expanduser()
    # Frozen (PyInstaller binary): the bundled content/ lives under the
    # read-only/ephemeral _MEIPASS extraction dir, so it must NOT shadow the
    # writable per-user dir — in-app edits there are lost on exit / blocked on
    # macOS. Return user_data_root()/"content" — the EXACT dir the first-run
    # migration seeds (migrate_to_user_data._dst_content + launcher.py both use
    # user_data_root()/"content"); NOT user_data_root() itself (that is
    # _build_output_root()'s domain for exports/builds — content_root is one
    # level deeper: the dir holding editions.yaml/notes). Returning the parent
    # left a frozen app reading an EMPTY content root. Placed AFTER the explicit
    # YHWH_CONTENT_ROOT override (which still wins) and BEFORE in-tree detection
    # (the bundle's editions.yaml marker would otherwise win). (round-11
    # frozen-app HIGH + the round-13 off-by-one fix Mac caught cross-OS.)
    if getattr(sys, "frozen", False):
        return user_data_root() / "content"
    in_tree = _detect_in_tree_content()
    if in_tree is not None:
        return in_tree
    # Installed (non-frozen) fallback: the same content/ subdir the migration seeds.
    return user_data_root() / "content"


def set_content_root_for_testing(path: Path | str | None) -> None:
    """Pin ``content_root()`` to a specific path for the duration of
    a test. Pass ``None`` to clear the override and fall back to the
    normal resolution. The cache is invalidated either way so the
    next ``content_root()`` call sees the change."""
    global _TEST_OVERRIDE
    _TEST_OVERRIDE = Path(path) if path is not None else None
    _content_root_cached.cache_clear()


def reset_content_root() -> None:
    """Drop any cached content_root() result. Useful when the
    underlying environment changes mid-process (env-var edits in
    tests, etc.). Does not touch the test override."""
    _content_root_cached.cache_clear()


# ----------------------------------------------------------------------
# Sub-path helpers — composed from content_root() so a single override
# point cascades to every directory the project reads or writes.
# ----------------------------------------------------------------------


def notes_dir() -> Path:
    return content_root() / "notes"


def candidates_dir() -> Path:
    return content_root() / "candidates"


def sources_dir() -> Path:
    return content_root() / "sources"


def translations_dir() -> Path:
    return content_root() / "translations"


def covers_dir() -> Path:
    return content_root() / "covers"


def audio_dir() -> Path:
    return content_root() / "audio"


def books_yaml() -> Path:
    return content_root() / "books.yaml"


def kinds_yaml() -> Path:
    return content_root() / "kinds.yaml"


def categories_yaml() -> Path:
    return content_root() / "categories.yaml"


def themes_yaml() -> Path:
    return content_root() / "themes.yaml"


def canons_yaml() -> Path:
    return content_root() / "canons.yaml"


def editions_yaml() -> Path:
    return content_root() / "editions.yaml"


def traditions_yaml() -> Path:
    return content_root() / "traditions.yaml"


# ----------------------------------------------------------------------
# Build-output sub-paths — these can live alongside content/ in dev
# (matching today's layout) or under user_data_root() in an installed
# build. Same resolver pattern; different parent.
# ----------------------------------------------------------------------


def _build_output_root() -> Path:
    """Where regenerable build output (exports/, builds/, backups) lives.

    Resolution (highest precedence first):
      1. ``YHWH_DATA_DIR`` env var — relocate the writable data root to any
         path (e.g. a roomier drive). Honored in every mode.
      2. Frozen (PyInstaller binary): ``user_data_root()`` — a persistent,
         writable per-user dir. The bundled ``content_root()`` lives under
         PyInstaller's read-only/ephemeral ``_MEIPASS`` extraction dir, so
         build output must NOT be rooted there (it would vanish on exit).
      3. Dev: ``content_root().parent`` — the repo root, matching today's
         layout (``exports/`` is a sibling of ``content/``)."""
    env = os.environ.get(_DATA_DIR_ENV)
    if env:
        return Path(env).expanduser()
    if getattr(sys, "frozen", False):
        return user_data_root()
    return content_root().parent


def exports_dir() -> Path:
    return _build_output_root() / "exports"


def epub_working_dir() -> Path:
    return _build_output_root() / "epub_working"


def builds_dir() -> Path:
    return _build_output_root() / "builds"


def backups_dir() -> Path:
    return _build_output_root() / "epub_working" / ".backups"


def state_dir() -> Path:
    """Persistent UX/app state (e.g. the onboarding marker) — a sibling of
    exports_dir() under the same frozen-aware writable data root, so it
    survives app restarts and honors the YHWH_DATA_DIR override."""
    return _build_output_root() / "state"


# ----------------------------------------------------------------------
# External-tool resolvers — Tesseract OCR (τ.6.x.0c).
#
# Resolution order for tesseract_binary():
#   1. TESSERACT_BIN env-var override (highest priority)
#   2. shutil.which("tesseract") — PATH lookup
#   3. Well-known platform install paths (Windows / macOS / Linux)
#   4. None — caller decides how to fail (extract_parallel_pdf.py
#      raises a clear error message pointing at the install docs).
#
# The project does NOT require Tesseract to be on PATH; this resolver
# lets the extractor work whether or not the operator updated their
# shell PATH after installing Tesseract. On Windows the UB-Mannheim
# installer (default for τ.6.x.0c) drops Tesseract at
# ``C:\Program Files\Tesseract-OCR\tesseract.exe``.
# ----------------------------------------------------------------------


_TESSERACT_ENV_VAR = "TESSERACT_BIN"


def _known_tesseract_paths() -> list[Path]:
    """Platform-conventional install paths for Tesseract, ordered by
    likelihood. Returns Path objects (existence not checked here —
    the caller filters)."""
    if sys.platform == "win32":
        return [
            Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
            Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
            Path.home() / "AppData" / "Local" / "Programs" / "Tesseract-OCR" / "tesseract.exe",
        ]
    if sys.platform == "darwin":
        return [
            Path("/opt/homebrew/bin/tesseract"),  # Apple Silicon Homebrew
            Path("/usr/local/bin/tesseract"),  # Intel Homebrew + MacPorts default
        ]
    # Linux + other POSIX
    return [
        Path("/usr/bin/tesseract"),
        Path("/usr/local/bin/tesseract"),
    ]


def tesseract_binary() -> Path | None:
    """Resolve the on-disk location of the Tesseract OCR binary, or
    return ``None`` if it cannot be found. Cached on first call;
    call ``reset_tesseract_binary()`` after environment changes.

    The resolver does NOT verify the binary works (no version probe);
    that is the caller's responsibility. This keeps ``paths.py`` a
    pure path-resolution module; runtime probes belong in the
    extractor."""
    return _tesseract_binary_cached()


@lru_cache(maxsize=1)
def _tesseract_binary_cached() -> Path | None:
    import shutil

    override = os.environ.get(_TESSERACT_ENV_VAR)
    if override:
        candidate = Path(override).expanduser()
        if candidate.is_file():
            return candidate
        # If TESSERACT_BIN is set but invalid, fall through to PATH /
        # known-paths — but the override miss is worth surfacing in
        # logs at the extractor layer (this resolver stays silent).

    on_path = shutil.which("tesseract")
    if on_path:
        return Path(on_path)

    for candidate in _known_tesseract_paths():
        if candidate.is_file():
            return candidate

    return None


def reset_tesseract_binary() -> None:
    """Drop the cached tesseract_binary() result. Useful when the
    environment changes mid-process (env-var edits, PATH updates,
    or tests that monkeypatch the resolver inputs)."""
    _tesseract_binary_cached.cache_clear()
