"""Regression: /customize payload lists each edition's books in canonical
(books.yaml) order — Genesis → Revelation → Apocrypha → Ethiopian tail —
NOT alphabetical (CLAUDE_PROJECT_RULES.md §6.1, M3).

The payload is the single source of truth the UI reads for book order; if it
ships alphabetically sorted codes the UI shows e.g. ``deu`` before ``exo``.
"""

from scripts.web_editions import api_customize_data


def _canon_books_by_edition() -> dict[str, list[str]]:
    payload = api_customize_data()
    return payload["edition_canon_books"]


def test_books_listed_in_canonical_not_alphabetical_order():
    """For an edition containing both ``gen`` and ``rev``, Genesis precedes a
    later book which precedes Revelation — i.e. the list follows the canon
    spine, not the alphabet (where ``rev`` would sort before ``gen``)."""
    by_edition = _canon_books_by_edition()

    candidates = [(ed, books) for ed, books in by_edition.items() if "gen" in books and "rev" in books]
    assert candidates, "expected at least one edition spanning gen..rev"

    for ed, books in candidates:
        i_gen = books.index("gen")
        i_rev = books.index("rev")
        assert i_gen < i_rev, f"{ed}: gen ({i_gen}) must precede rev ({i_rev})"

        # A later mid-spine book sits strictly between Genesis and Revelation.
        mid = next((b for b in ("mat", "psa", "isa", "exo") if b in books), None)
        assert mid is not None, f"{ed}: no recognizable mid-spine book present"
        i_mid = books.index(mid)
        assert i_gen < i_mid < i_rev, f"{ed}: expected gen ({i_gen}) < {mid} ({i_mid}) < rev ({i_rev})"


def test_some_edition_order_differs_from_alphabetical():
    """At least one edition's canonical order must differ from a plain
    alphabetical sort — proving the payload is not silently re-sorting."""
    by_edition = _canon_books_by_edition()

    differs = [ed for ed, books in by_edition.items() if books != sorted(books)]
    assert differs, (
        "no edition's canonical book order differs from alphabetical — "
        "the payload appears to still be alphabetically sorted"
    )
