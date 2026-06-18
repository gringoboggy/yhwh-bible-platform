"""Kindle-for-Mac library discovery — container paths for STK channel sim.

Modern Kindle for Mac (2024+) uses bundle id ``com.amazon.Lassen``; older builds
used ``com.amazon.Kindle``. Signed-in users may have either (or both).
"""

from __future__ import annotations

from pathlib import Path

# Current Amazon Kindle.app CFBundleIdentifier (Mac App Store / iOS-on-Mac).
LASSEN_CONTAINER = "com.amazon.Lassen"
LEGACY_KINDLE_CONTAINER = "com.amazon.Kindle"

# Order matters: prefer the live app container first.
_CONTAINER_IDS = (LASSEN_CONTAINER, LEGACY_KINDLE_CONTAINER)

# Extensions polled after Send-to-Kindle (Documents may hold .epub pre-conversion).
LIBRARY_FILE_SUFFIXES = (".azw", ".kfx", ".mbp", ".epub")


def kindle_data_root(home: Path | None = None) -> Path | None:
    """Return ``~/Library/Containers/<id>/Data`` for the first installed Kindle app."""
    base = (home or Path.home()) / "Library" / "Containers"
    for cid in _CONTAINER_IDS:
        data = base / cid / "Data"
        if data.is_dir():
            return data
    return None


def kindle_container_id(home: Path | None = None) -> str | None:
    """Bundle id of the detected Kindle container, or None."""
    root = kindle_data_root(home)
    if root is None:
        return None
    return root.parent.name


def library_scan_dirs(data_root: Path) -> list[Path]:
    """Directories to scan for library inventory (recursive find in stk_channel)."""
    out: list[Path] = []
    for name in ("Library", "Documents"):
        p = data_root / name
        if p.is_dir():
            out.append(p)
    return out


def iter_library_files(data_root: Path) -> list[Path]:
    """All library artifact paths under *data_root* (sorted)."""
    found: list[Path] = []
    for scan_dir in library_scan_dirs(data_root):
        for path in scan_dir.rglob("*"):
            if path.is_file() and path.suffix.lower() in LIBRARY_FILE_SUFFIXES:
                found.append(path)
    return sorted(found)
