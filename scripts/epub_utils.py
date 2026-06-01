#!/usr/bin/env python3
"""Shared low-level EPUB-build helpers used by BOTH build_edition.py and
matter_pages.py. Extracted (verbatim) from build_edition.py so the matter-page
module can reuse them without a circular import.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _xml_escape_text(s: str) -> str:
    """Escape verse text for safe inclusion in EPUB XHTML.

    The only characters we need to neutralize are ``&``, ``<``, ``>``;
    quote characters can pass through because they only appear inside
    plain text in XHTML, never inside attribute values here.
    """
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _resolve_publishing(edition: dict) -> dict:
    """Resolve the publishing metadata for an edition, filling defaults
    for any field the user hasn't set yet (Phase π.2). The defaults match
    the `PUBLISHING_DEFAULTS` dict in web.py so the /publisher UI and the
    build pipeline agree on what an unset edition looks like.
    """
    defaults = {
        "publisher_name": "Independent",
        "publisher_url": "",
        "copyright_year": "2026",
        "copyright_holder": "",
        "copyright_notice": "All rights reserved.",
        "publication_date": "2026-05-14",
        "language_code": "en",
        "cover_credit": "",
        "source_text_credit": "Scripture text based on the World English Bible (public domain).",
    }
    out = {}
    for k, v in defaults.items():
        out[k] = edition.get(k) or v
    out["authors"] = list(edition.get("authors") or [])
    out["bisac_codes"] = list(edition.get("bisac_codes") or [])
    return out


def load_canons() -> dict:
    """Read content/canons.yaml and return {canon_id: {label, description, books}}."""
    canons_path = REPO_ROOT / "content" / "canons.yaml"
    if not canons_path.is_file():
        return {}
    import yaml

    data = yaml.safe_load(canons_path.read_text(encoding="utf-8")) or {}
    return data.get("canons", {}) or {}
