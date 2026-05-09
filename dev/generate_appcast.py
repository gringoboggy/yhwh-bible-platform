#!/usr/bin/env python3
"""Phase θ.3 — Sparkle/WinSparkle appcast generator.

Produces an ``appcast.xml`` feed describing released versions of
the YHWH desktop binary. Sparkle (macOS) / WinSparkle (Windows)
poll this feed on app start and prompt the user to update when a
newer version is advertised.

Reads:
  * ``VERSION`` file at the repo root  → the channel's current version
  * ``git tag`` output                  → the historical release list
  * Optional release-notes URL pattern  → per-version download URLs

Emits a Sparkle-compatible XML document. The output is intended
to be uploaded alongside the binary releases to a stable HTTPS
URL (e.g. ``https://yhwh.example/updates/appcast.xml``); the
PyInstaller-built launcher polls that URL on startup via
``scripts.core.updates.fetch_appcast``.

Usage:
    python3 dev/generate_appcast.py \\
        --base-url https://yhwh.example/releases/ \\
        > dist/appcast.xml

Pure-function shape:
    build_appcast(channel_title, channel_description,
                  base_url, releases) -> str

``releases`` is a list of dicts: ``{version, pub_date, length,
mime, filename}``. ``main()`` is the thin CLI adapter that
discovers the inputs (VERSION + git tags) and calls
``build_appcast``.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TITLE = "YHWH — Bible publishing platform"
DEFAULT_DESCRIPTION = "YHWH desktop binary updates"
DEFAULT_LANGUAGE = "en"
DEFAULT_MIME = "application/octet-stream"


def build_appcast(
    *,
    channel_title: str,
    channel_description: str,
    channel_language: str = DEFAULT_LANGUAGE,
    base_url: str,
    releases: Iterable[dict],
) -> str:
    """Compose a Sparkle-compatible appcast XML document.

    Each ``releases`` entry needs ``version`` and ``filename``;
    optional fields ``pub_date``, ``length``, ``mime``, ``title``
    (defaults derived from version + filename if absent).

    ``base_url`` is the prefix for download URLs. A release with
    filename ``YHWH-1.0.0.dmg`` becomes
    ``<base_url>/YHWH-1.0.0.dmg``. Trailing slash on base_url is
    optional.

    Pure function: no I/O, no environment reads. ``main()``
    handles the inputs."""
    base = base_url.rstrip("/")
    items_xml = []
    for r in releases:
        version = r["version"]
        filename = r["filename"]
        title = r.get("title") or f"Version {version}"
        pub_date = r.get("pub_date", "")
        length = r.get("length", 0)
        mime = r.get("mime") or DEFAULT_MIME
        download_url = f"{base}/{filename}"
        items_xml.append(
            "    <item>\n"
            f"      <title>{escape(title)}</title>\n"
            f"      <pubDate>{escape(pub_date)}</pubDate>\n"
            f"      <enclosure url=\"{escape(download_url)}\""
            f" sparkle:version=\"{escape(version)}\""
            f" length=\"{int(length)}\""
            f" type=\"{escape(mime)}\" />\n"
            "    </item>"
        )
    items_block = "\n".join(items_xml) if items_xml else "    <!-- no releases -->"
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<rss version="2.0"'
        ' xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle">\n'
        '  <channel>\n'
        f"    <title>{escape(channel_title)}</title>\n"
        f"    <description>{escape(channel_description)}</description>\n"
        f"    <language>{escape(channel_language)}</language>\n"
        f"{items_block}\n"
        '  </channel>\n'
        '</rss>\n'
    )


def read_version_file(version_file: Path) -> str:
    """Read the ``VERSION`` file's first non-blank line."""
    if not version_file.is_file():
        return ""
    for line in version_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def discover_git_tags(*, run_fn=None) -> list[str]:
    """Return the project's git tags in reverse-chronological
    order (newest first). Empty list if not a git repo or git
    isn't installed. ``run_fn`` is injectable for tests."""
    if run_fn is None:
        run_fn = _run_git
    try:
        out = run_fn(["tag", "--sort=-creatordate"])
    except FileNotFoundError:
        return []
    if not out:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def _run_git(args: list[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout


def releases_from_version_and_tags(
    *,
    current_version: str,
    tags: list[str],
    filename_pattern: str,
) -> list[dict]:
    """Compose release dicts from the project's VERSION + git
    tags. The current VERSION is always included as the first
    (newest) entry; historical tags follow.

    ``filename_pattern`` is a format string with one
    ``{version}`` placeholder — e.g. ``"YHWH-{version}.dmg"`` for
    macOS, ``"YHWH-Setup-{version}.exe"`` for Windows. Pure
    function — no filesystem access."""
    out: list[dict] = []
    seen: set[str] = set()
    if current_version:
        out.append({
            "version": current_version,
            "filename": filename_pattern.format(version=current_version),
        })
        seen.add(current_version)
    for tag in tags:
        # Strip a leading "v" prefix on tags like "v1.0.0".
        v = tag[1:] if tag.startswith("v") else tag
        if v in seen:
            continue
        out.append({
            "version": v,
            "filename": filename_pattern.format(version=v),
        })
        seen.add(v)
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Generate a Sparkle/WinSparkle appcast.xml for the "
            "YHWH desktop binary."
        ),
    )
    p.add_argument(
        "--base-url",
        required=True,
        help=("URL prefix for the binary downloads, e.g. "
              "https://yhwh.example/releases/"),
    )
    p.add_argument(
        "--filename-pattern",
        default="YHWH-{version}.dmg",
        help=("Filename template with one {version} placeholder. "
              "Default targets macOS DMG; use "
              "'YHWH-Setup-{version}.exe' for Windows or "
              "'YHWH-{version}-x86_64.AppImage' for Linux."),
    )
    p.add_argument(
        "--title",
        default=DEFAULT_TITLE,
        help="Channel title (default: %(default)s).",
    )
    p.add_argument(
        "--description",
        default=DEFAULT_DESCRIPTION,
        help="Channel description (default: %(default)s).",
    )
    p.add_argument(
        "--language",
        default=DEFAULT_LANGUAGE,
        help="Channel language code (default: %(default)s).",
    )
    p.add_argument(
        "--version-file",
        default=str(REPO_ROOT / "VERSION"),
        help="Path to the project's VERSION file.",
    )
    args = p.parse_args(argv)

    current = read_version_file(Path(args.version_file))
    tags = discover_git_tags()
    releases = releases_from_version_and_tags(
        current_version=current,
        tags=tags,
        filename_pattern=args.filename_pattern,
    )
    xml = build_appcast(
        channel_title=args.title,
        channel_description=args.description,
        channel_language=args.language,
        base_url=args.base_url,
        releases=releases,
    )
    sys.stdout.write(xml)
    return 0


if __name__ == "__main__":
    sys.exit(main())
