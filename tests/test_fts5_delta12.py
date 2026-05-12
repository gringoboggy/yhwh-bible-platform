"""Δ.12 — FTS5 full-text search pins.

Topic file (created alongside the Δ.12 ship). FTS5 is the first
phase that uses Δ.10's migration framework beyond its baseline,
so several test classes here verify both the migration mechanics
AND the FTS5-specific search semantics.

Coverage:
- TestDelta12Migration:           migration #2 (`notes_fts`) lives
  in MIGRATIONS, has the expected version + name + FTS5 schema
  with porter tokenization + external content reference.
- TestDelta12FtsTableExists:      after rebuild(), the notes_fts
  virtual table exists in the corpus_index DB and is populated
  with rows from notes.
- TestDelta12Fts5SearchSemantics:  `fts5_search()` returns hits
  for common queries; bare-word queries auto-prefix-match;
  empty / whitespace queries return []; malformed FTS5 queries
  raise ValueError.
- TestDelta12Fts5SearchFilters:   kind / book filters work;
  limit caps result count.
- TestDelta12Fts5HitShape:        each hit dict carries the same
  fields as `search()`'s output so consumers can swap call sites.

Pinning rationale: FTS5 is the buyer-facing speed unlock for
search. Drift in tokenization (e.g., losing porter stemmer),
the rebuild population step, or the hit-dict shape would
silently degrade search quality or break the
api_search_notes rewire that Δ.12.x will do.
"""

from __future__ import annotations


class TestDelta12Migration:
    """Migration #2 in `scripts.core.migrations.MIGRATIONS`."""

    @classmethod
    def setup_class(cls):
        from scripts.core.migrations import MIGRATIONS

        cls.migrations = MIGRATIONS

    def test_two_migrations_now(self):
        # Migration #1 is the baseline (Δ.10), #2 is the FTS5 layer
        # (Δ.12). A third migration would extend this list.
        assert len(self.migrations) >= 2

    def test_migration_2_is_notes_fts(self):
        # Pin version 2 name to "notes_fts" so a future migration
        # renumbering doesn't quietly shift the slot.
        m = next((m for m in self.migrations if m[0] == 2), None)
        assert m is not None, "migration #2 missing"
        version, name, _sql = m
        assert version == 2
        assert name == "notes_fts"

    def test_migration_2_uses_fts5_virtual_table(self):
        # Pin the FTS5 marker — if a future contributor switches to
        # FTS4 or a regular table, search semantics change.
        m = next((m for m in self.migrations if m[0] == 2), None)
        sql_lc = m[2].lower()
        assert "virtual table" in sql_lc
        assert "using fts5" in sql_lc

    def test_migration_2_uses_porter_tokenizer(self):
        # Porter stemming is the difference between "running" matching
        # "run" and only matching "running". Buyer-facing search
        # quality depends on it.
        m = next((m for m in self.migrations if m[0] == 2), None)
        sql = m[2]
        assert "porter" in sql, "porter tokenizer missing — search loses stemming"

    def test_migration_2_uses_unicode_diacritics_folding(self):
        # `remove_diacritics 1` lets users search Greek/Hebrew
        # transliterations without typing the accented forms.
        m = next((m for m in self.migrations if m[0] == 2), None)
        sql = m[2]
        assert "remove_diacritics" in sql, "diacritics-folding missing — Greek/Hebrew search broken for ASCII queries"

    def test_migration_2_uses_external_content(self):
        # External-content tables don't duplicate the source data —
        # saves disk and keeps the index in sync with notes
        # automatically.
        m = next((m for m in self.migrations if m[0] == 2), None)
        sql = m[2]
        assert "content='notes'" in sql, "FTS5 not configured as external-content (would duplicate data)"
        assert "content_rowid='rowid'" in sql

    def test_migration_2_indexes_the_right_columns(self):
        m = next((m for m in self.migrations if m[0] == 2), None)
        sql = m[2]
        # Searched fields (title, label, kind, attribution, body_plain).
        # `body` (HTML) deliberately omitted — body_plain is the clean
        # ASCII equivalent.
        for field in ("title", "label", "kind", "attribution", "body_plain"):
            assert field in sql, f"FTS5 schema missing {field!r}"


class TestDelta12FtsTableExists:
    """After rebuild(), notes_fts is populated. Fresh conn per test
    method — caching the conn at class level fails when another
    fixture invalidates the corpus_index conn between methods."""

    def test_notes_fts_table_exists(self):
        from scripts.core import corpus_index

        conn = corpus_index.connection()
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notes_fts'")
        assert cur.fetchone() is not None, "notes_fts virtual table not present after rebuild"

    def test_notes_fts_is_populated(self):
        # After the rebuild's `INSERT INTO notes_fts(notes_fts)
        # VALUES('rebuild')`, the index should match the notes-table
        # row count.
        from scripts.core import corpus_index

        conn = corpus_index.connection()
        notes_count = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
        fts_count = conn.execute("SELECT COUNT(*) FROM notes_fts").fetchone()[0]
        assert notes_count == fts_count, f"FTS5 row count {fts_count} != notes row count {notes_count}"
        assert fts_count > 0, "FTS5 empty after rebuild — population step didn't run"


class TestDelta12Fts5SearchSemantics:
    """`fts5_search` query handling."""

    @classmethod
    def setup_class(cls):
        from scripts.core import corpus_index

        corpus_index.invalidate()
        # Warm up the connection.
        corpus_index.connection()

    def test_empty_query_returns_empty(self):
        from scripts.core.corpus_index import fts5_search

        assert fts5_search("") == []
        assert fts5_search("   ") == []

    def test_bare_word_returns_hits(self):
        # "beginning" appears in many notes (esp. Genesis); FTS5
        # should find them.
        from scripts.core.corpus_index import fts5_search

        hits = fts5_search("beginning", limit=10)
        assert hits, "FTS5 search for 'beginning' returned no hits"
        assert len(hits) <= 10

    def test_prefix_match_default_for_bare_words(self):
        # Bare-word queries should match prefixes — "begin" should
        # match notes containing "beginning". This is the LIKE-style
        # UX our users expect.
        from scripts.core.corpus_index import fts5_search

        hits = fts5_search("begin", limit=10)
        assert hits, "prefix matching should produce hits for 'begin' (matches beginning, began, etc.)"

    def test_phrase_query_works(self):
        # "in the beginning" as a quoted phrase should find Genesis
        # 1:1 commentary entries.
        from scripts.core.corpus_index import fts5_search

        hits = fts5_search('"in the beginning"', limit=10)
        # Allow zero hits — the test corpus may or may not have the
        # exact phrase; just verify no exception + valid shape.
        assert isinstance(hits, list)

    def test_malformed_query_raises_value_error(self):
        # FTS5 rejects unbalanced quotes / parens. Our wrapper
        # re-raises as ValueError so callers can catch cleanly.
        from scripts.core.corpus_index import fts5_search

        import pytest

        with pytest.raises(ValueError):
            fts5_search('"unbalanced')


class TestDelta12Fts5SearchFilters:
    """Filter args restrict results correctly."""

    @classmethod
    def setup_class(cls):
        from scripts.core import corpus_index

        corpus_index.invalidate()
        corpus_index.connection()

    def test_book_filter_restricts_results(self):
        from scripts.core.corpus_index import fts5_search

        gen_hits = fts5_search("light", book="gen", limit=50)
        # Every returned hit must be in Genesis
        for h in gen_hits:
            assert h["book_code"] == "gen", f"unexpected book: {h['book_code']}"

    def test_kind_filter_restricts_results(self):
        from scripts.core.corpus_index import fts5_search

        # "lang-hebrew" is a high-volume kind; should have many
        # "spirit" hits.
        hits = fts5_search("spirit", kind="lang-hebrew", limit=20)
        for h in hits:
            assert h["kind"] == "lang-hebrew", f"unexpected kind: {h['kind']}"

    def test_limit_caps_result_count(self):
        from scripts.core.corpus_index import fts5_search

        hits = fts5_search("god", limit=5)
        assert len(hits) <= 5


class TestDelta12Fts5HitShape:
    """Each hit dict has the same shape as the LIKE-based
    `search()` output so consumers can swap call sites."""

    @classmethod
    def setup_class(cls):
        from scripts.core import corpus_index

        corpus_index.invalidate()
        corpus_index.connection()

    def test_hit_carries_all_canonical_fields(self):
        from scripts.core.corpus_index import fts5_search

        hits = fts5_search("beginning", limit=1)
        assert hits
        h = hits[0]
        # Same field set as search() returns
        for field in (
            "book_code",
            "chapter",
            "verse",
            "suffix",
            "anchor",
            "kind",
            "title",
            "label",
            "excerpt",
            "attribution",
            "score",
        ):
            assert field in h, f"hit missing field {field!r}"

    def test_hit_chapter_and_verse_are_ints(self):
        from scripts.core.corpus_index import fts5_search

        h = fts5_search("beginning", limit=1)[0]
        assert isinstance(h["chapter"], int), f"chapter not int: {type(h['chapter']).__name__}"
        assert isinstance(h["verse"], int), f"verse not int: {type(h['verse']).__name__}"

    def test_hit_score_is_positive_int(self):
        # bm25 is internally negative-ish; we normalize to a
        # positive int where higher = better, matching the
        # LIKE-search's convention.
        from scripts.core.corpus_index import fts5_search

        h = fts5_search("god", limit=1)[0]
        assert isinstance(h["score"], int)
        assert h["score"] >= 1

    def test_hit_excerpt_contains_snippet_markers(self):
        # FTS5's snippet() builtin wraps matched terms in `‹›`
        # markers (we use those rather than HTML so the
        # downstream renderer can escape safely).
        from scripts.core.corpus_index import fts5_search

        hits = fts5_search("light", limit=5)
        # At least one hit should have the markers (some excerpts
        # might fall outside the snippet window for very long
        # bodies, so don't require all).
        any_with_markers = any("‹" in h["excerpt"] or "›" in h["excerpt"] for h in hits)
        assert any_with_markers, "no hits had FTS5 snippet markers — snippet() not wired"
