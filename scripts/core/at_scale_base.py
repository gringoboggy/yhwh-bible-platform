"""at_scale_base.py — shared helpers for the at-scale candidate-generation drivers.

Extracted (mint-7 D1) from the 10 ``run_*_at_scale.py`` drivers + ``prospect.py``
(which each defined a byte-identical ``candidate_to_dict``), from ``detectors.py`` /
``run_hebrew_at_scale`` / ``run_greek_at_scale`` (which each defined the same 27-code
``NT_BOOKS`` set), and from the ANSI color constants copy-pasted across all of them.

``write_queue`` is deliberately NOT here — each driver has its own append / dedup /
overwrite semantics (the lone exception, ``run_xref``'s former clobber, was fixed in
mint-7 B2). This module is a dependency-free leaf: it imports nothing from ``scripts``,
so every driver + ``detectors.py`` can import it without a circular-import hazard.
"""

from __future__ import annotations

# ANSI color codes for the drivers' progress output.
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

# The 27 canonical New Testament book codes (books.yaml codes). The Hebrew word
# detector skips these (lexicon is OT-only); the Greek detector skips everything
# NOT in this set. Canonical codes throughout (phi/jam, never php/jas).
NT_BOOKS = frozenset(
    {
        "mat",
        "mrk",
        "luk",
        "jhn",
        "act",
        "rom",
        "1co",
        "2co",
        "gal",
        "eph",
        "phi",
        "col",
        "1th",
        "2th",
        "1ti",
        "2ti",
        "tit",
        "phm",
        "heb",
        "jam",
        "1pe",
        "2pe",
        "1jn",
        "2jn",
        "3jn",
        "jud",
        "rev",
    }
)


def candidate_to_dict(c, idx: int) -> dict:
    """Serialize a detector ``Candidate`` into the ``prospect.py`` JSON shape so
    ``promote.py`` / ``batch_promote_xrefs.py`` consume it unchanged. (mint-7 D1:
    was copy-pasted identically across all 10 at-scale drivers + ``prospect.py``.)"""
    return {
        "id": f"{c.book}-{c.chapter}-{c.verse}-{idx:03d}",
        "verse": c.verse,
        "kind": c.kind,
        "anchor": c.anchor,
        "confidence": round(c.confidence, 3),
        "source_name": c.source_name,
        "source_attribution": c.source_attribution,
        "draft_title": c.draft_title,
        "draft_label": c.draft_label,
        "draft_body": c.draft_body,
        "detector": c.detector,
        "reviewer_notes": c.reviewer_notes,
        "status": "pending",
    }
