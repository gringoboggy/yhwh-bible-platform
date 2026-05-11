"""ω.27 follow-on (2026-05-11) — ψ.18 + ψ.18.1 symbol-totals sidebar
test classes, split out of the monolithic ``tests/test_scripts.py``
into a topic file alongside the other ω.27 follow-on splits.

Thirteenth topic extraction. The ψ.18 arc added the matrix
sidebar's per-book + per-chapter drilldown:

- ψ.18   per_book field on Matrix + per-book sparklines
- ψ.18.1 per_chapter field + chapter drilldown

These are the matrix sidebar's data foundations; later ψ.18
sub-slices add the chapter expand-all interaction (still in
test_scripts.py for now).

Every class lazy-imports its dependencies inside test method
bodies, so this file has no top-level imports from the project.

The ``_matrix_html_and_js()`` helper is duplicated here (originally
in test_scripts.py) — it concatenates MATRIX_HTML with the
externalized matrix_app.js content so tests written against the
pre-ψ.34 inline form keep working post-extraction.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _matrix_html_and_js() -> str:
    """ψ.34: return MATRIX_HTML concatenated with matrix_app.js.

    Before ψ.34 the matrix JS lived inline in MATRIX_HTML; after
    ψ.34 it lives in scripts/templates/matrix_app.js. Many tests
    grep cls.html for JS code strings — they were written against
    the inline form. This helper preserves those tests' pattern by
    returning the union.
    """
    from scripts.templates.matrix import MATRIX_HTML

    js_path = REPO_ROOT / "scripts" / "templates" / "matrix_app.js"
    js_text = js_path.read_text(encoding="utf-8") if js_path.is_file() else ""
    return MATRIX_HTML + "\n" + js_text


# ============================================================
# Phase ψ.18 — Symbol-totals sidebar on /matrix
# ============================================================


class TestPsi18MatrixPerBookField:
    """ψ.18: Matrix dataclass gains a per_book field, populated by
    compute_matrix() with per-edition / per-kind / per-book counts
    in the same scope as `potential` (every kind, every canon book,
    regardless of enabled-kind toggles)."""

    @classmethod
    def setup_class(cls):
        from scripts.core.matrix import compute_matrix

        cls.matrix = compute_matrix()

    def test_per_book_field_present(self):
        assert hasattr(self.matrix, "per_book")
        assert isinstance(self.matrix.per_book, dict)

    def test_per_book_keyed_by_edition(self):
        # Every edition that's in `potential` should also be in
        # per_book. (Editions with no canon match might be empty
        # but should still have a key.)
        assert set(self.matrix.per_book.keys()) == set(self.matrix.potential.keys())

    def test_per_book_kind_count_matches_potential(self):
        # For each edition: every kind that has a non-zero
        # potential count must also appear in per_book.
        for ed_id, kind_counts in self.matrix.potential.items():
            for kind, total in kind_counts.items():
                if total == 0:
                    continue
                assert kind in self.matrix.per_book[ed_id], f"{ed_id}: kind {kind} in potential but not in per_book"

    def test_per_book_sum_matches_potential_total(self):
        # The sum of per-book counts for one (edition, kind) must
        # equal the kind's `potential` total. That's the load-bearing
        # invariant — if the sum drifts, the sparkline lies.
        for ed_id, kind_counts in self.matrix.potential.items():
            for kind, total in kind_counts.items():
                book_counts = self.matrix.per_book[ed_id].get(kind, {})
                summed = sum(book_counts.values())
                assert summed == total, f"{ed_id}/{kind}: per_book sum={summed} but potential={total}"

    def test_per_book_only_includes_canon_books(self):
        # A book outside the edition's canon must NOT appear in
        # per_book[edition] for any kind.
        for ed_id, by_kind in self.matrix.per_book.items():
            canon = self.matrix.edition_canon_books[ed_id]
            for kind, book_counts in by_kind.items():
                for book in book_counts:
                    assert book in canon, f"{ed_id}/{kind}: book {book} not in canon set ({len(canon)} books)"

    def test_per_book_values_are_positive(self):
        # Books with zero notes-of-this-kind are absent (not stored
        # as 0). Verify no zero entries in case the helper changes.
        for ed_id, by_kind in self.matrix.per_book.items():
            for kind, book_counts in by_kind.items():
                for book, count in book_counts.items():
                    assert count > 0, f"{ed_id}/{kind}/{book}: stored zero count (should be absent)"


class TestPsi18ApiMatrixPerBookSurface:
    """ψ.18: /api/matrix exposes per_book + canon_book_order so
    the JS sidebar can render the totals panel without a second
    request."""

    @classmethod
    def setup_class(cls):
        import importlib

        cls.web = importlib.import_module("scripts.web")
        cls.api = cls.web.api_matrix()

    def test_response_includes_per_book(self):
        for ed_id, ed_data in self.api["matrix"].items():
            assert "per_book" in ed_data, f"{ed_id}: missing per_book key"
            assert isinstance(ed_data["per_book"], dict)

    def test_response_includes_canon_book_order(self):
        for ed_id, ed_data in self.api["matrix"].items():
            assert "canon_book_order" in ed_data
            order = ed_data["canon_book_order"]
            assert isinstance(order, list)
            # Ordering: must match the edition's canon set
            assert set(order) == set(ed_data["canon_book_order"])  # tautology — but pins the type

    def test_canon_book_order_is_canonical(self):
        # The order must follow content/books.yaml — i.e. Genesis
        # before Exodus before ... before Revelation. Verify by
        # comparing against the books-yaml load order.
        from scripts.core import config

        books_in_order = [b["code"] for b in config.load_books()]
        for ed_id, ed_data in self.api["matrix"].items():
            order = ed_data["canon_book_order"]
            # Each book in the order must appear in books_in_order
            # with strictly-increasing index.
            indexes = [books_in_order.index(c) for c in order if c in books_in_order]
            assert indexes == sorted(indexes), f"{ed_id}: canon_book_order is not in canonical book-order"

    def test_per_book_counts_match_matrix_module(self):
        # The API's per_book values must match what
        # compute_matrix().per_book returns — the API is just a
        # JSON shadow of the same data.
        from scripts.core.matrix import compute_matrix

        m = compute_matrix()
        for ed_id, ed_data in self.api["matrix"].items():
            api_per_book = ed_data["per_book"]
            mod_per_book = m.per_book.get(ed_id, {})
            for kind, books in api_per_book.items():
                assert mod_per_book.get(kind) == books, f"{ed_id}/{kind}: API + module per_book differ"


class TestPsi18MatrixHtmlSidebar:
    """ψ.18: matrix.py template HTML smoke tests for the totals
    sidebar section."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.matrix import MATRIX_HTML

        cls.html = _matrix_html_and_js()

    def test_totals_section_present(self):
        # The sidebar slot must be in the rendered HTML.
        assert 'id="totals-section"' in self.html
        assert 'id="totals-list"' in self.html
        assert "Symbol totals" in self.html

    def test_totals_edition_label(self):
        # The whole-edition label sits at the top of the panel.
        assert 'id="totals-edition"' in self.html

    def test_render_symbol_totals_function_present(self):
        # JS function must be defined in the template.
        assert "function renderSymbolTotals" in self.html

    def test_sparkline_charset_present(self):
        # 8-level Unicode block characters for sparklines (plus
        # leading space for "no notes").
        assert "SPARK_CHARS" in self.html
        # Verify all 9 chars are in the source (one of them is a
        # space, which we can't easily assert raw, but the
        # constant declaration should match).
        assert "▁▂▃▄▅▆▇█" in self.html

    def test_render_called_from_refresh(self):
        # renderSymbolTotals must be called at the end of
        # refreshActiveEdition so an edition switch updates the
        # sidebar.
        # Find the function body and confirm the call appears
        # between its braces.
        func_start = self.html.find("function refreshActiveEdition")
        assert func_start >= 0
        # Take ~5000 chars of the function body and check
        body = self.html[func_start : func_start + 5000]
        assert "renderSymbolTotals()" in body

    def test_render_called_from_toggle_handlers(self):
        # Live toggle updates: kind toggle + category toggle
        # both must call renderSymbolTotals.
        kind_toggle = self.html.find("function onToggleKind")
        cat_toggle = self.html.find("function onToggleCategory")
        assert kind_toggle >= 0 and cat_toggle >= 0
        kind_body = self.html[kind_toggle : kind_toggle + 1500]
        cat_body = self.html[cat_toggle : cat_toggle + 2000]
        assert "renderSymbolTotals()" in kind_body
        assert "renderSymbolTotals()" in cat_body

    def test_escape_helpers_present(self):
        # XSS hardening: render uses escapeText / escapeAttr around
        # user-controlled values (kind labels, sparkline tooltips).
        assert "function escapeText" in self.html
        assert "function escapeAttr" in self.html


class TestPsi181MatrixPerChapterField:
    """ψ.18.1: Matrix dataclass gains a per_chapter field, populated
    by compute_matrix() with per-edition / per-kind / per-book /
    per-chapter counts. Same potential scope as per_book."""

    @classmethod
    def setup_class(cls):
        from scripts.core.matrix import compute_matrix

        cls.matrix = compute_matrix()

    def test_per_chapter_field_present(self):
        assert hasattr(self.matrix, "per_chapter")
        assert isinstance(self.matrix.per_chapter, dict)

    def test_per_chapter_keyed_by_edition(self):
        # Same edition keys as per_book / potential.
        assert set(self.matrix.per_chapter.keys()) == set(self.matrix.per_book.keys())

    def test_per_chapter_book_subset_matches_per_book(self):
        # For each (edition, kind), the books that appear in
        # per_chapter must be a subset of per_book — every book with
        # chapter detail must also have a per-book total. (Subset
        # rather than equality because a kind file might in theory
        # have empty chapters; in practice they match.)
        for ed_id, by_kind in self.matrix.per_chapter.items():
            for kind, by_book in by_kind.items():
                pb = self.matrix.per_book.get(ed_id, {}).get(kind, {})
                for book in by_book:
                    assert book in pb, f"{ed_id}/{kind}/{book}: chapter detail without per_book entry"

    def test_per_chapter_sum_matches_per_book(self):
        # Sum of chapter counts per (edition, kind, book) must
        # equal that book's per_book count. Load-bearing invariant
        # — drift here means the drilldown lies.
        for ed_id, by_kind in self.matrix.per_chapter.items():
            for kind, by_book in by_kind.items():
                pb = self.matrix.per_book[ed_id][kind]
                for book, by_ch in by_book.items():
                    summed = sum(by_ch.values())
                    assert summed == pb[book], f"{ed_id}/{kind}/{book}: chapter sum={summed} but per_book={pb[book]}"

    def test_per_chapter_keys_are_ints(self):
        # Chapter keys are ints (Python side; JSON serialization
        # promotes to strings, but the dataclass holds ints).
        for ed_id, by_kind in self.matrix.per_chapter.items():
            for kind, by_book in by_kind.items():
                for book, by_ch in by_book.items():
                    for ch_key in by_ch:
                        assert isinstance(ch_key, int), f"{ed_id}/{kind}/{book}: chapter key {ch_key!r} is not int"

    def test_per_chapter_values_are_positive(self):
        # Chapters with zero notes-of-this-kind are absent (not
        # stored as 0).
        for ed_id, by_kind in self.matrix.per_chapter.items():
            for kind, by_book in by_kind.items():
                for book, by_ch in by_book.items():
                    for ch, count in by_ch.items():
                        assert count > 0, f"{ed_id}/{kind}/{book}/{ch}: stored zero count (should be absent)"

    def test_per_chapter_only_includes_canon_books(self):
        # Same canon-respect invariant as per_book.
        for ed_id, by_kind in self.matrix.per_chapter.items():
            canon = self.matrix.edition_canon_books[ed_id]
            for kind, by_book in by_kind.items():
                for book in by_book:
                    assert book in canon, f"{ed_id}/{kind}: book {book} not in canon"


class TestPsi181ApiMatrixPerChapterSurface:
    """ψ.18.1: /api/matrix surfaces per_chapter + book_chapter_counts
    so the JS sidebar can render full-width chapter sparklines."""

    @classmethod
    def setup_class(cls):
        import importlib

        cls.web = importlib.import_module("scripts.web")
        cls.api = cls.web.api_matrix()

    def test_response_includes_per_chapter(self):
        for ed_id, ed_data in self.api["matrix"].items():
            assert "per_chapter" in ed_data, f"{ed_id}: missing per_chapter key"
            assert isinstance(ed_data["per_chapter"], dict)

    def test_response_includes_book_chapter_counts(self):
        for ed_id, ed_data in self.api["matrix"].items():
            assert "book_chapter_counts" in ed_data
            counts = ed_data["book_chapter_counts"]
            assert isinstance(counts, dict)
            # Every book in canon_book_order with metadata should
            # appear with a positive ch_count.
            for book in ed_data["canon_book_order"]:
                if book in counts:
                    assert counts[book] > 0, f"{ed_id}/{book}: ch_count is 0 or negative"

    def test_per_chapter_counts_match_matrix_module(self):
        # API per_chapter is a JSON shadow of the module's data.
        # JSON int keys become strings; verify by string comparison.
        from scripts.core.matrix import compute_matrix

        m = compute_matrix()
        for ed_id, ed_data in self.api["matrix"].items():
            api_pc = ed_data["per_chapter"]
            mod_pc = m.per_chapter.get(ed_id, {})
            for kind, books in api_pc.items():
                for book, by_ch in books.items():
                    mod_by_ch = mod_pc.get(kind, {}).get(book, {})
                    # Compare totals (key types differ; sum is the
                    # invariant the drilldown depends on).
                    api_sum = sum(by_ch.values())
                    mod_sum = sum(mod_by_ch.values())
                    assert api_sum == mod_sum, f"{ed_id}/{kind}/{book}: API chapter-sum={api_sum} but module={mod_sum}"

    def test_book_chapter_counts_match_books_yaml(self):
        # Cross-check: books.yaml's ch_count is the source of truth.
        from scripts.core import config

        yaml_counts = {b["code"]: int(b.get("ch_count") or 0) for b in config.load_books()}
        for ed_id, ed_data in self.api["matrix"].items():
            for book, ch_count in ed_data["book_chapter_counts"].items():
                assert yaml_counts.get(book) == ch_count, (
                    f"{ed_id}/{book}: API ch_count={ch_count} but books.yaml={yaml_counts.get(book)}"
                )


class TestPsi181MatrixHtmlChapterDrilldown:
    """ψ.18.1: matrix.py template renders chapter drilldown inside
    the existing totals-section (no new sidebar slot)."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.matrix import MATRIX_HTML

        cls.html = _matrix_html_and_js()

    def test_drilldown_class_present(self):
        # Each kind row is wrapped in a details.psi181-drilldown.
        assert "psi181-drilldown" in self.html

    def test_drilldown_css_suppresses_global_arrow(self):
        # The global details>summary::before injects an arrow that
        # would conflict with our inline flex-item arrow. Verify the
        # suppression rule is in place.
        assert "details.psi181-drilldown > summary::before" in self.html
        assert "content: none" in self.html

    def test_drilldown_arrow_rotation_rule(self):
        # When the details opens, the inline arrow rotates 90deg.
        assert "psi181-arrow" in self.html
        assert "details.psi181-drilldown[open] > summary .psi181-arrow" in self.html

    def test_renderer_consumes_per_chapter(self):
        # The JS renderer reads m.per_chapter and m.book_chapter_counts
        # from the API response.
        assert "m.per_chapter" in self.html
        assert "m.book_chapter_counts" in self.html

    def test_renderer_iterates_chapters_to_ch_count(self):
        # The chapter-spark loop uses bookChCounts per book to know
        # the upper bound; verify the variable is wired.
        assert "bookChCounts" in self.html

    def test_renderer_renders_chapter_summary_stat(self):
        # The "X chapters · Y books" stat appears in the drilldown.
        assert "chaptersWithNotes" in self.html
        assert "booksWithNotes" in self.html

    def test_renderer_top_n_books_limit(self):
        # The drilldown shows top-N (=5) books per kind to keep the
        # panel compact; pin the constant.
        assert "TOP_N_BOOKS" in self.html
        assert "TOP_N_BOOKS = 5" in self.html
