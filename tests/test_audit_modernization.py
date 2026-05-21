"""Pin: audit.py reads book metadata from content/books.yaml (via
config.books_by_code()), NOT the retired kings_session/book_meta.py.

kings_session/{book_meta,strategy_b_inject}.py were lost in the 2026-05-08
re-init; books.yaml — into which book_meta's BOOK_META was generated — is the
single source of truth. audit.py was the one downstream script that still
imported the deleted module, which made verify.py / ship-check / ebible doctor
emit 4 spurious ERRORs ("expected script missing" + "cannot load"). Fixed
2026-05-21. These pins keep the dead dependency from creeping back.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


class TestAuditNoKingsSessionDependency:
    def test_audit_does_not_path_depend_on_kings_session(self):
        text = (REPO / "audit.py").read_text(encoding="utf-8")
        # Prose mentions in comments/docstrings are fine (historical context);
        # what must not come back is a *path/import dependency* on the deleted
        # dir — i.e. kings_session used as a quoted path segment.
        assert 'kings_session"' not in text and "kings_session'" not in text, (
            "audit.py still constructs a path into the retired kings_session/ dir"
        )
        assert "config.books_by_code" in text, "audit.py should read book metadata via config.books_by_code()"

    def test_book_meta_source_carries_the_fields_b_checks_read(self):
        # audit._load_book_meta() now returns config.books_by_code(); confirm
        # that source carries bp/bxx/ch_count so the repoint can't silently
        # break the Category-B structural checks.
        from scripts.core import config

        books = config.books_by_code()
        assert len(books) >= 80, f"expected the full ~87-book canon, got {len(books)}"
        gen = books.get("gen")
        assert gen is not None, "Genesis missing from books_by_code()"
        for key in ("bp", "bxx", "ch_count"):
            assert key in gen, f"book meta missing {key!r} — audit.py Category-B checks depend on it"
