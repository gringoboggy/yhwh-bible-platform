"""Verse-popup version registry — the single source of truth for which
translation versions a popup can carry, how each renders, and how its
coordinate maps onto the canonical (KJV/WEB) verse numbering.

Both the bake (scripts/generate_verse_popups.py) and the per-edition build
(scripts/build_edition.py) import from here, so adding a version is one entry
plus its ingested data — no model change.

``content_class`` is the literal CSS class of the version's content ``<p>``.
KJV keeps the recovered-base ``vnote-text`` for byte-compatibility; every other
version gets ``vnote-<id>``. ``translation_id`` is the id in
scripts.core.translations. ``order`` ascending = render order within a popup.
"""

from __future__ import annotations

# id -> spec. Versions with no ingested data simply never appear (the bake
# includes a version only when get_verse returns text).
VERSION_REGISTRY: dict[str, dict] = {
    "kjv": {
        "label": "King James Version",
        "content_class": "vnote-text",
        "lang": "en",
        "dir": "ltr",
        "has_label_para": False,
        "translation_id": "kjv",
        "order": 10,
    },
    "wlc": {
        "label": "Hebrew (Masoretic / WLC)",
        "content_class": "vnote-hebrew",
        "lang": "he",
        "dir": "rtl",
        "has_label_para": True,
        "translation_id": "wlc",
        "order": 20,
    },
    "lxx-greek": {
        "label": "Greek (Septuagint / Swete)",
        "content_class": "vnote-greek",
        "lang": "grc",
        "dir": "ltr",
        "has_label_para": True,
        "translation_id": "lxx-swete-greek",
        "order": 30,
    },
    "greek-nt": {
        "label": "Greek (Textus Receptus)",
        "content_class": "vnote-greek-nt",
        "lang": "grc",
        "dir": "ltr",
        "has_label_para": True,
        "translation_id": "byzantine-greek",
        "order": 35,
    },
    "brenton-en": {
        "label": "English (Brenton LXX)",
        "content_class": "vnote-brenton-en",
        "lang": "en",
        "dir": "ltr",
        "has_label_para": True,
        "translation_id": "lxx-brenton-english",
        "order": 40,
    },
    "douay": {
        "label": "Douay-Rheims",
        "content_class": "vnote-douay",
        "lang": "en",
        "dir": "ltr",
        "has_label_para": True,
        "translation_id": "douay-rheims",
        "order": 50,
    },
    "jps": {
        "label": "JPS (1917)",
        "content_class": "vnote-jps",
        "lang": "en",
        "dir": "ltr",
        "has_label_para": True,
        "translation_id": "jps",
        "order": 60,
    },
    "vulgate": {
        "label": "Latin (Clementine Vulgate)",
        "content_class": "vnote-vulgate",
        "lang": "la",
        "dir": "ltr",
        "has_label_para": True,
        "translation_id": "vulgate-clementine",
        "order": 70,
    },
    "arabic": {
        "label": "Arabic (Van Dyck)",
        "content_class": "vnote-arabic",
        "lang": "ar",
        "dir": "rtl",
        "has_label_para": True,
        "translation_id": "arabic-vandyke",
        "order": 80,
    },
}

# Legacy popup-language ids (pre-B1 editions / baked asides) -> version id.
_ALIASES = {"english": "kjv", "hebrew": "wlc", "greek": "lxx-greek"}

ALL_VERSION_IDS: tuple[str, ...] = tuple(VERSION_REGISTRY.keys())

# Versions whose FULL data is ingested AND already baked into the shared base
# (epub_working/). Phase 1 bakes only these three (matching the recovered base),
# so a regen stays byte-identical. Phase 2 flips each remaining version on here
# as its full, versification-aligned PD data lands — seed-only data (e.g. the
# Genesis-only douay/jps/vulgate/arabic samples) is deliberately NOT baked.
_BAKED_NOW: frozenset[str] = frozenset({"kjv", "wlc", "lxx-greek"})


def bakes_now(version_id: str) -> bool:
    """True if this version's full data is baked into the shared base today."""
    return version_id in _BAKED_NOW


# Versions passed through the aside renderer RAW (not HTML-escaped). WLC Hebrew
# wraps each word in <em> for word-level styling, so it MUST be raw. LXX Greek
# (Swete) is plain text but verified free of HTML-special chars at ingest (0 of
# 22,893 verses contain <>&), so raw passthrough is a safe no-op and matches the
# recovered-base contract (the old bake escaped english, passed hebrew/greek
# raw). Each new source's format is verified at ingest before its id is added.
_TRUSTED_HTML: frozenset[str] = frozenset({"wlc", "lxx-greek", "greek-nt"})


def is_trusted_html(version_id: str) -> bool:
    """True if this version's data is trusted pre-formatted HTML (passed raw)."""
    return version_id in _TRUSTED_HTML


def resolve_version_id(token: str) -> str | None:
    """Map a legacy language id or a version id to a registry id, else None."""
    if token in VERSION_REGISTRY:
        return token
    return _ALIASES.get(token)


def normalize_coord(version_id: str, book: str, ch: int, vs: int) -> tuple[str, int, int]:
    """Map a canonical (KJV) coordinate to the version's own coordinate.

    B1: identity for every version (no per-source remaps yet). Phases 2-3 add
    per-source remap tables here for the known Hebrew/LXX/Vulgate divergence
    loci (Psalm titles, Daniel additions, Joel/Malachi splits, ...).
    """
    return (book, ch, vs)
