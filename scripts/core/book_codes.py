"""scripts.core.book_codes — single legacy→canonical book-code resolver.

Every path that accepts a book code from a user, API, or CLI should
normalize through ``canonical_book_code()`` so legacy aliases (joh, php,
jas, …) resolve to the ``content/books.yaml`` / ``content/notes/<code>.py``
stems. Commentary loaders and at-scale drivers delegate here via
``sources_base._normalize_book_code``; web/API/CLI entry points call
``config.resolve_book_code`` (re-export).
"""

from __future__ import annotations

# ω.36 / mint-7 — legacy SBL / commentary / detector codes → canonical stems.
BOOK_CODE_ALIASES: dict[str, str] = {
    "joh": "jhn",
    "ps": "psa",
    "jas": "jam",
    "mar": "mrk",
    "jol": "joe",
    "ezk": "eze",
    "nam": "nah",
    "php": "phi",
}


def canonical_book_code(code: str) -> str:
    """Map a legacy alias to its canonical books.yaml code; passthrough otherwise."""
    return BOOK_CODE_ALIASES.get(code, code)
