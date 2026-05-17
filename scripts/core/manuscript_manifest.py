# scripts/core/manuscript_manifest.py
"""Folio manifest loader for the dual-manuscript track (Phase-2, τ.6.x.4.b+c).

Now track-parameterised: ``load_manifest(track="samuel")`` is the default
(byte-identical back-compat); ``load_manifest(track="kings")`` drives the
τ.6.x.4.c Kings marathon.

The manifest lives in ``content/manuscript/<track>/manifest.yaml`` and records,
for each chapter of the book:

  - ``GG``  : ``{folios: [...], source_images: [...]}``
  - ``CAM`` : ``{folios: [...], views: [...]}``
  - ``status``: ``"calibrated"`` | ``"pending"``

The four Samuel calibration chapters (1sa 1, 3, 17; 2sa 11) are seeded with
real folio sigla and source-image paths drawn directly from the immutable
witness JSONs.  All other chapters are ``pending`` (empty lists) until each is
collated and GO'd under the Phase-2 protocol.

Public API
----------
load_manifest(track="samuel") -> dict
    Returns the full parsed manifest dict (book → chapter-int-key → entry).
    Cached per track via ``@functools.lru_cache(maxsize=4)``.
    Call ``load_manifest.cache_clear()`` in test setUp when needed.

chapter_entry(man, book, ch) -> dict
    Return the entry dict for ``(book, ch)``.  If the chapter is absent from
    the manifest (should not occur for a complete seeding, but is defensive),
    returns a synthesised pending default.
"""

from __future__ import annotations

import functools
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent.parent


def _manifest_path(track: str) -> Path:
    return REPO / "content" / "manuscript" / track / "manifest.yaml"


# Back-compat: external importers that reference MANIFEST_PATH directly keep working.
MANIFEST_PATH = _manifest_path("samuel")

_PENDING_DEFAULT: dict = {
    "status": "pending",
    "GG": {"folios": [], "source_images": []},
    "CAM": {"folios": [], "views": []},
}


@functools.lru_cache(maxsize=4)
def load_manifest(track: str = "samuel") -> dict:
    """Parsed folio manifest for *track* (``"samuel"`` default -> unchanged
    back-compat; ``"kings"`` = the tau.6.x.4.c marathon). Cached per track;
    call ``load_manifest.cache_clear()`` after editing the YAML in tests."""
    raw = yaml.safe_load(_manifest_path(track).read_text(encoding="utf-8")) or {}
    return raw


def chapter_entry(man: dict, book: str, ch: int) -> dict:
    """Return the manifest entry for *(book, ch)*.

    If the chapter is not present in the manifest (defensive fallback only;
    the manifest is fully seeded for 1sa 1-31 and 2sa 1-24), returns a
    synthesised pending entry so callers never receive ``None``.
    """
    book_data = man.get(book, {})
    entry = book_data.get(ch)
    if entry is None:
        return dict(_PENDING_DEFAULT)
    return entry
