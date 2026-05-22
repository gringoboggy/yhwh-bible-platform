"""
updates.py — auto-update data plane (Phase θ.3).

Sparkle (macOS) and WinSparkle (Windows) are the standard native
auto-update frameworks. Both consume a Sparkle-compatible
``appcast.xml`` feed: an Atom-style RSS that lists released
versions, their download URLs, and signing metadata. This module
is the **Python-side data plane** for that feed:

  - ``fetch_appcast(url, *, http_fn=None) -> dict``
        Fetch + parse the feed; injectable HTTP fn for tests.
  - ``parse_appcast(xml_bytes) -> dict``
        Pure parser; takes XML bytes, returns the structured form.
  - ``latest_version(appcast) -> str``
  - ``release_url(appcast) -> str | None``
  - ``compare_versions(a, b) -> int``
        Semver-aware (-1 / 0 / 1).
  - ``is_update_available(current, appcast) -> bool``

The native Sparkle/WinSparkle integration is compile-time linking
into the PyInstaller bundle — out of scope for this Python data
plane. A lighter-weight fallback (poll appcast on launcher startup,
surface "update available" via PyWebView toast) is straightforward
to add later: load this module, call ``fetch_appcast``, branch on
``is_update_available``.

Sparkle XML reference:
    https://sparkle-project.org/documentation/publishing/

Network calls go through ``scripts.core.http.get`` to honor the
ω.10 retry/timeout policy and the linter's external-HTTP rule.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Callable

__all__ = [
    "fetch_appcast",
    "parse_appcast",
    "latest_version",
    "release_url",
    "compare_versions",
    "is_update_available",
    "AppcastError",
]

SPARKLE_NS = "http://www.andymatuschak.org/xml-namespaces/sparkle"


class AppcastError(ValueError):
    """Raised on malformed appcast XML. Subclass of ValueError so
    callers can catch ``ValueError`` if they want a single
    "input-was-bad" branch."""


def parse_appcast(xml_bytes: bytes) -> dict:
    """Parse a Sparkle appcast XML document into a structured dict.

    Returns ``{"channel": {...}, "items": [...]}`` where each item
    has ``title``, ``version``, ``url``, ``length``, ``mime``,
    ``pub_date``. Defensive: missing fields land as empty string
    (or 0 for ``length``); unknown elements are ignored.

    Raises ``AppcastError`` if the XML doesn't parse or the root
    element isn't ``<rss>``."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        raise AppcastError(f"appcast XML did not parse: {e}") from e
    if root.tag != "rss":
        raise AppcastError(f"appcast root must be <rss>, got <{root.tag}>")
    channel = root.find("channel")
    if channel is None:
        raise AppcastError("appcast missing <channel>")
    out: dict = {
        "channel": {
            "title": _text(channel.find("title")),
            "description": _text(channel.find("description")),
            "language": _text(channel.find("language")),
        },
        "items": [],
    }
    for item in channel.findall("item"):
        out["items"].append(_parse_item(item))
    return out


def _parse_item(item: ET.Element) -> dict:
    enclosure = item.find("enclosure")
    version = ""
    url = ""
    length = 0
    mime = ""
    if enclosure is not None:
        # Sparkle conventionally puts the version on the
        # <enclosure> element via the sparkle: namespace attribute.
        version = enclosure.get(f"{{{SPARKLE_NS}}}version") or enclosure.get("sparkle:version", "") or ""
        url = enclosure.get("url", "")
        try:
            length = int(enclosure.get("length", "0"))
        except (TypeError, ValueError):
            length = 0
        mime = enclosure.get("type", "")
    return {
        "title": _text(item.find("title")),
        "version": version,
        "url": url,
        "length": length,
        "mime": mime,
        "pub_date": _text(item.find("pubDate")),
    }


def _text(el: ET.Element | None) -> str:
    if el is None or el.text is None:
        return ""
    return el.text.strip()


def fetch_appcast(
    url: str,
    *,
    http_fn: Callable[[str], bytes] | None = None,
) -> dict:
    """Fetch + parse an appcast from ``url``.

    ``http_fn(url) -> bytes`` is injectable for tests; production
    default is ``scripts.core.http.get`` (which carries the ω.10
    retry/timeout policy and is the only allow-listed outbound-HTTP
    surface per the linter rule). Network failures propagate
    through ``http.HttpError``; XML parse failures raise
    ``AppcastError``."""
    if http_fn is None:
        # ξ.10 — pin appcast egress to the desktop-update allowlist.
        # Other call sites use their own allowlist groups.
        from scripts.core.http import (
            get as http_get,
            DEFAULT_DESKTOP_UPDATE_ALLOWLIST,
        )

        http_fn = lambda u: http_get(  # noqa: E731
            u,
            allowlist=DEFAULT_DESKTOP_UPDATE_ALLOWLIST,
        )
    xml_bytes = http_fn(url)
    return parse_appcast(xml_bytes)


def latest_version(appcast: dict) -> str:
    """Return the highest semver among the appcast's items.

    The Sparkle convention is items-newest-first, but defensive
    callers compare by version regardless of order. Returns an
    empty string if no items have a version."""
    versions = [i.get("version", "") for i in appcast.get("items", [])]
    versions = [v for v in versions if v]
    if not versions:
        return ""
    return max(versions, key=_version_key)


def release_url(appcast: dict) -> str | None:
    """Return the download URL for the latest item, or ``None``
    if no items / no enclosure URL."""
    latest = latest_version(appcast)
    if not latest:
        return None
    for item in appcast.get("items", []):
        if item.get("version") == latest:
            return item.get("url") or None
    return None


def compare_versions(a: str, b: str) -> int:
    """Return -1 / 0 / 1 by semver comparison.

    Defensive: non-numeric components are compared lexically; an
    invalid version compares less than any valid version. Empty
    strings compare equal to each other, less than non-empty."""
    if not a and not b:
        return 0
    if not a:
        return -1
    if not b:
        return 1
    ka = _version_key(a)
    kb = _version_key(b)
    if ka < kb:
        return -1
    if ka > kb:
        return 1
    return 0


_VERSION_PART_RE = re.compile(r"(\d+)|([A-Za-z]+)")


def _version_key(v: str) -> tuple:
    """Tuple key for version comparison. Splits on any
    non-alphanumeric (``.``, ``-``, ``_``); numeric components
    sort numerically, alpha components lexically. Used as
    ``max(versions, key=_version_key)``."""
    parts: list[tuple] = []
    for chunk in re.split(r"[^A-Za-z0-9]+", v):
        if not chunk:
            continue
        for m in _VERSION_PART_RE.finditer(chunk):
            num, alpha = m.group(1), m.group(2)
            if num is not None:
                # (0, int_value) — numeric components sort before
                # alpha components of the same chunk so "1.0" >
                # "1.0a" without needing extra rules.
                parts.append((0, int(num)))
            else:
                parts.append((1, alpha.lower()))
    return tuple(parts)


def is_update_available(current: str, appcast: dict) -> bool:
    """True iff the appcast advertises a strictly-newer version
    than ``current``. Missing or unparseable current version
    treats any advertised version as an update."""
    latest = latest_version(appcast)
    if not latest:
        return False
    return compare_versions(current, latest) < 0
