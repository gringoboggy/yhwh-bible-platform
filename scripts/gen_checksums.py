#!/usr/bin/env python3
"""Generate ``SHA256SUMS.txt`` for the release artifacts.

Run this after building the binaries, pointing it at the directory that holds
them (the ``dist/`` output of ``dev/build_dmg.sh`` / ``dev/build_appimage.sh`` /
``dev/installer.iss``). It writes a ``SHA256SUMS.txt`` in the standard
``<hex>  <filename>`` format that ``sha256sum -c SHA256SUMS.txt`` (Linux/macOS)
verifies, then attach that file to the GitHub Release alongside the binaries.

A checksum proves a download is *intact* (it matches what was posted) — not who
built it; that is what code-signing adds. Hand-typed checksums are worse than
none, so this is the one source of truth.

Usage::

    python3 scripts/gen_checksums.py <dir> [--out <path>] [--ext .exe .dmg ...]
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

# ".epub" also covers ".kepub.epub" (suffix-tuple match on the full filename) —
# round-7 3.1: its absence silently dropped the EPUB + kepub asset families from
# every default-invocation SHA256SUMS (notary_autofinish.sh passes no --ext).
DEFAULT_EXTS: tuple[str, ...] = (".exe", ".dmg", ".AppImage", ".msi", ".zip", ".tar.gz", ".epub")
_CHUNK = 1 << 20  # 1 MiB — stream so large binaries never load whole into RAM


def sha256_file(path: Path) -> str:
    """Return the hex SHA-256 of a file, read in chunks."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(_CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def gen_checksums(directory: Path, exts: tuple[str, ...] = DEFAULT_EXTS) -> list[tuple[str, str]]:
    """Return ``[(hexdigest, filename), ...]`` for matching artifacts, name-sorted.

    Skips ``SHA256SUMS.txt`` itself so re-running is idempotent.
    """
    arts = sorted(
        p for p in directory.iterdir() if p.is_file() and p.name != "SHA256SUMS.txt" and p.name.endswith(exts)
    )
    return [(sha256_file(p), p.name) for p in arts]


def render(rows: list[tuple[str, str]]) -> str:
    """Render rows as ``sha256sum``-compatible lines (two spaces = binary mode)."""
    return "".join(f"{digest}  {name}\n" for digest, name in rows)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Generate SHA256SUMS.txt for release artifacts.")
    p.add_argument("directory", type=Path, help="directory holding the built artifacts")
    p.add_argument("--out", type=Path, default=None, help="output path (default: <dir>/SHA256SUMS.txt)")
    p.add_argument(
        "--ext",
        nargs="+",
        default=list(DEFAULT_EXTS),
        help="artifact extensions to include",
    )
    args = p.parse_args(argv)

    if not args.directory.is_dir():
        print(f"error: not a directory: {args.directory}", file=sys.stderr)
        return 2

    rows = gen_checksums(args.directory, tuple(args.ext))
    if not rows:
        print(
            f"error: no artifacts matching {args.ext} in {args.directory}",
            file=sys.stderr,
        )
        return 1

    out = args.out or (args.directory / "SHA256SUMS.txt")
    out.write_text(render(rows), encoding="utf-8")
    for digest, name in rows:
        print(f"{digest}  {name}")
    print(f"\nwrote {out} ({len(rows)} file(s))", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
