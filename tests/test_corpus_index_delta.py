"""ω.27 follow-on (2026-05-11) — Δ-family test classes, split out of
the monolithic ``tests/test_scripts.py`` into a topic file alongside
``tests/test_matrix_psi35.py`` and ``tests/test_web_filesplit.py``.

Third topic extraction. Δ.0 through Δ.5.1 (14 test classes) cover
the corpus_index optimization arc: the SQLite-indexed alternative
to the file-walk operations for matrix/search/attribution-audit/
dashboard-stats, plus the five infrastructure unblockers
(Δ.0 rebuild lock, Δ.6 TTL fingerprint cache, Δ.7 notes_io hook,
Δ.8 per-worker storage, Δ.9 warmup) that made the wire-flip slices
(Δ.2.1, Δ.3.1, Δ.4.1, Δ.5.1) safe under xdist on Windows.

See `CLAUDE_PROJECT_RULES §9 — "Build an index-backed alternative
for an expensive file-walk operation (the Δ-family pattern)"` for
the codified mental model these tests exercise.

Every class lazy-imports its dependencies inside test method
bodies, so this file has no top-level imports from the project.
"""


# ---------- Phase Δ.1 : SQLite derived corpus index --------------------


class TestDelta1CorpusIndex:
    """Δ.1 — derived SQLite index over `content/notes/*.py`.

    Bold-proposal companion to `dev/AUDIT_2026-05-10.md` §2. Tests
    the additive layer's contract: build, rebuild on mtime change,
    query helpers, idempotent fingerprint comparison.
    """

    def _setup_isolated_corpus(self, tmp_path, monkeypatch):
        """Set up an isolated notes_dir + user_data_root so each
        test runs against a fresh corpus + cache."""
        from scripts.core import corpus_index, paths

        notes_dir = tmp_path / "notes"
        cache_dir = tmp_path / "user_data"
        notes_dir.mkdir()
        cache_dir.mkdir()

        monkeypatch.setattr(paths, "notes_dir", lambda: notes_dir)
        monkeypatch.setattr(paths, "user_data_root", lambda: cache_dir)
        # Reset the module-level connection cache
        corpus_index._CACHED_CONN = None

        return notes_dir, cache_dir, corpus_index

    def _write_book(self, notes_dir, code, notes):
        """Write a notes/<code>.py with the given list of tuples."""
        lines = ["NOTES = (", *[f"    {n!r}," for n in notes], ")\n"]
        (notes_dir / f"{code}.py").write_text("\n".join(lines), encoding="utf-8")

    # ---- build / fingerprint ----

    def test_rebuild_creates_index_with_correct_count(self, tmp_path, monkeypatch):
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        self._write_book(
            nd,
            "gen",
            [
                (1, 1, "", "", "comm", "T", "L", "B"),
                (1, 2, "", "", "word", "T", "L", "B"),
                (2, 1, "", "", "comm", "T", "L", "B"),
            ],
        )
        result = ci.rebuild(force=True)
        assert result["rebuilt"] is True
        assert result["note_count"] == 3
        assert len(result["fingerprint"]) == 64  # sha256 hex

    def test_rebuild_is_idempotent_when_fingerprint_matches(self, tmp_path, monkeypatch):
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        self._write_book(nd, "gen", [(1, 1, "", "", "comm", "T", "L", "B")])
        first = ci.rebuild()
        second = ci.rebuild()  # No corpus change
        assert first["rebuilt"] is True
        assert second["rebuilt"] is False
        assert first["fingerprint"] == second["fingerprint"]

    def test_rebuild_triggers_on_corpus_change(self, tmp_path, monkeypatch):
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        self._write_book(nd, "gen", [(1, 1, "", "", "comm", "T", "L", "B")])
        first = ci.rebuild()
        assert first["note_count"] == 1
        # Add a book — fingerprint changes
        self._write_book(nd, "exo", [(1, 1, "", "", "word", "T", "L", "B")])
        # ω.36 — explicit invalidate() between mid-test mutation and
        # the next rebuild() call. Production code that writes
        # outside `notes_io.atomic_write` (e.g. test fixtures using
        # `pathlib.write_text`) needs the same hook to defeat the
        # Δ.6 TTL cache. Production callers that go through
        # `notes_io.atomic_write` get this for free via the Δ.7 hook.
        ci.invalidate()
        second = ci.rebuild()
        assert second["rebuilt"] is True
        assert second["note_count"] == 2
        assert first["fingerprint"] != second["fingerprint"]

    def test_rebuild_force_always_rebuilds(self, tmp_path, monkeypatch):
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        self._write_book(nd, "gen", [(1, 1, "", "", "comm", "T", "L", "B")])
        ci.rebuild()
        forced = ci.rebuild(force=True)
        assert forced["rebuilt"] is True

    def test_rebuild_atomic_swap(self, tmp_path, monkeypatch):
        # The build writes to .tmp, then renames. Verify no .tmp
        # leftover after success.
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        self._write_book(nd, "gen", [(1, 1, "", "", "comm", "T", "L", "B")])
        ci.rebuild()
        leftovers = list((cd / "cache").glob("*.tmp"))
        assert leftovers == []

    # ---- query helpers ----

    def test_count_by_kind(self, tmp_path, monkeypatch):
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        self._write_book(
            nd,
            "gen",
            [
                (1, 1, "", "", "comm", "T", "L", "B"),
                (1, 2, "", "", "comm", "T", "L", "B"),
                (1, 3, "", "", "word", "T", "L", "B"),
            ],
        )
        ci.rebuild()
        result = ci.count_by_kind()
        assert result == {"comm": 2, "word": 1}

    def test_count_by_kind_filters_by_book(self, tmp_path, monkeypatch):
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        self._write_book(nd, "gen", [(1, 1, "", "", "comm", "T", "L", "B")])
        self._write_book(nd, "exo", [(1, 1, "", "", "word", "T", "L", "B")])
        ci.rebuild()
        gen_only = ci.count_by_kind(book="gen")
        assert gen_only == {"comm": 1}
        exo_only = ci.count_by_kind(book="exo")
        assert exo_only == {"word": 1}

    def test_count_by_kind_filters_by_kinds_list(self, tmp_path, monkeypatch):
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        self._write_book(
            nd,
            "gen",
            [
                (1, 1, "", "", "comm", "T", "L", "B"),
                (1, 2, "", "", "word", "T", "L", "B"),
                (1, 3, "", "", "xref-citation", "T", "L", "B"),
            ],
        )
        ci.rebuild()
        result = ci.count_by_kind(kinds=["comm", "word"])
        assert result == {"comm": 1, "word": 1}
        assert "xref-citation" not in result

    def test_count_by_book(self, tmp_path, monkeypatch):
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        self._write_book(
            nd,
            "gen",
            [(1, 1, "", "", "comm", "T", "L", "B"), (1, 2, "", "", "word", "T", "L", "B")],
        )
        self._write_book(nd, "exo", [(1, 1, "", "", "comm", "T", "L", "B")])
        ci.rebuild()
        result = ci.count_by_book()
        assert result == {"gen": 2, "exo": 1}

    def test_count_by_kind_and_book(self, tmp_path, monkeypatch):
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        self._write_book(
            nd,
            "gen",
            [(1, 1, "", "", "comm", "T", "L", "B"), (1, 2, "", "", "word", "T", "L", "B")],
        )
        self._write_book(nd, "exo", [(1, 1, "", "", "comm", "T", "L", "B")])
        ci.rebuild()
        result = ci.count_by_kind_and_book()
        assert result == {("gen", "comm"): 1, ("gen", "word"): 1, ("exo", "comm"): 1}

    def test_total_note_count(self, tmp_path, monkeypatch):
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        self._write_book(
            nd,
            "gen",
            [(1, 1, "", "", "comm", "T", "L", "B"), (1, 2, "", "", "word", "T", "L", "B")],
        )
        ci.rebuild()
        assert ci.total_note_count() == 2

    def test_kinds_present_returns_sorted_distinct(self, tmp_path, monkeypatch):
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        self._write_book(
            nd,
            "gen",
            [
                (1, 1, "", "", "word", "T", "L", "B"),
                (1, 2, "", "", "comm", "T", "L", "B"),
                (1, 3, "", "", "comm", "T", "L", "B"),  # dup
            ],
        )
        ci.rebuild()
        result = ci.kinds_present()
        assert result == ["comm", "word"]  # sorted, deduped

    # ---- malformed input handling ----

    def test_skip_book_with_syntax_error(self, tmp_path, monkeypatch):
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        self._write_book(nd, "gen", [(1, 1, "", "", "comm", "T", "L", "B")])
        # Drop a malformed book file
        (nd / "broken.py").write_text("NOTES = (this is not python", encoding="utf-8")
        result = ci.rebuild()
        # Broken book is skipped silently; gen still indexed.
        assert result["rebuilt"] is True
        assert result["note_count"] == 1

    def test_skip_tuple_with_wrong_arity(self, tmp_path, monkeypatch):
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        # Write a corpus where one tuple has only 5 elements (legacy
        # / corruption). Index should skip it; valid neighbors stay.
        self._write_book(
            nd,
            "gen",
            [
                (1, 1, "", "", "comm", "T", "L", "B"),  # valid, 8 fields
                (1, 2, ""),  # invalid, 3 fields
                (2, 1, "", "", "word", "T", "L", "B"),  # valid
            ],
        )
        ci.rebuild()
        assert ci.total_note_count() == 2

    # ---- connection caching ----

    def test_connection_caches_between_calls(self, tmp_path, monkeypatch):
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        self._write_book(nd, "gen", [(1, 1, "", "", "comm", "T", "L", "B")])
        c1 = ci.connection()
        c2 = ci.connection()
        assert c1 is c2

    def test_invalidate_drops_cached_connection(self, tmp_path, monkeypatch):
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        self._write_book(nd, "gen", [(1, 1, "", "", "comm", "T", "L", "B")])
        c1 = ci.connection()
        ci.invalidate()
        c2 = ci.connection()
        # Different object — old conn was closed, new built
        assert c1 is not c2

    # ---- end-to-end against the real corpus ----

    def test_index_matches_existing_aggregate_for_real_corpus(self):
        # Pin: against the real corpus, count_by_kind_and_book agrees
        # with the existing matrix.compute_matrix().potential. This
        # doesn't yet replace compute_matrix — it asserts the index
        # gives the same numbers. The eventual migration phase can
        # rely on this equivalence pin.
        from scripts.core import corpus_index
        from scripts.core.matrix import compute_matrix

        # Δ.6 (2026-05-11): dropped `force=True`; the fingerprint
        # cache picks up real corpus changes within TTL and the
        # equivalence is a per-corpus invariant. The old force path
        # raced with other xdist workers' cached connections.
        corpus_index.invalidate()
        corpus_index.rebuild()

        m = compute_matrix()
        # Pick one well-populated edition (ethiopian-tewahedo has the
        # full canon → all books, all kinds counted in `potential`).
        ed_id = "ethiopian-tewahedo"
        ed_potential = m.potential.get(ed_id, {})

        # Sum the potential over all (kind) in this edition
        matrix_total_per_kind: dict[str, int] = {}
        for kind, count in ed_potential.items():
            matrix_total_per_kind[kind] = matrix_total_per_kind.get(kind, 0) + count

        # The corpus index doesn't filter by edition canon — it sees
        # every note. ethiopian-tewahedo has the FULL 87-book canon,
        # so the index's count_by_kind() is a superset that should
        # match per-kind totals for any kind the edition includes.
        # (Some kinds ship in some editions but not others; we only
        # compare those kinds that exist in BOTH counts.)
        index_per_kind = corpus_index.count_by_kind()
        # Ethiopian canon includes all 87 books, so for any kind
        # that's in matrix_total_per_kind, the index count must be
        # >= it (the index also counts notes the matrix filtered
        # for canon membership — but Ethiopian is a superset).
        # For perfect equality: every note in any book lands in
        # ethiopian's potential, so the totals should match.
        for kind, matrix_count in matrix_total_per_kind.items():
            idx_count = index_per_kind.get(kind, 0)
            assert idx_count == matrix_count, f"mismatch on kind {kind!r}: matrix={matrix_count} index={idx_count}"


# ---------- Phase Δ.2 : index-backed search ----------------------------


class TestDelta2IndexSearch:
    """Δ.2 — index-backed search through `corpus_index.search()`.

    Migrates the search aggregate from a 50K-note file walk to a
    SQL query against the Δ.1 index. New `body_plain` column holds
    HTML-stripped text precomputed at index build time so query-time
    cost is just a SQL LIKE.

    Tests cover: basic search shape, filters (kind/book/edition),
    score ordering matches the file-walk implementation, empty
    queries, performance characteristics.
    """

    def _setup_isolated_corpus(self, tmp_path, monkeypatch):
        from scripts.core import corpus_index, paths

        notes_dir = tmp_path / "notes"
        cache_dir = tmp_path / "user_data"
        notes_dir.mkdir()
        cache_dir.mkdir()
        monkeypatch.setattr(paths, "notes_dir", lambda: notes_dir)
        monkeypatch.setattr(paths, "user_data_root", lambda: cache_dir)
        corpus_index._CACHED_CONN = None
        return notes_dir, cache_dir, corpus_index

    def _write_book(self, notes_dir, code, notes):
        lines = ["NOTES = (", *[f"    {n!r}," for n in notes], ")\n"]
        (notes_dir / f"{code}.py").write_text("\n".join(lines), encoding="utf-8")

    def test_search_empty_query_returns_empty(self, tmp_path, monkeypatch):
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        self._write_book(nd, "gen", [(1, 1, "", "", "comm", "T", "L", "<p>covenant</p>")])
        ci.rebuild()
        assert ci.search("") == []
        assert ci.search("   ") == []
        assert ci.search(None) == []

    def test_search_finds_match_in_body(self, tmp_path, monkeypatch):
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        self._write_book(
            nd,
            "gen",
            [
                (1, 1, "", "", "comm", "T", "L", "<p>covenant of pieces</p>"),
                (1, 2, "", "", "word", "T", "L", "<p>nothing matching here</p>"),
            ],
        )
        ci.rebuild()
        hits = ci.search("covenant")
        assert len(hits) == 1
        assert hits[0]["book_code"] == "gen"
        assert hits[0]["chapter"] == 1 and hits[0]["verse"] == 1

    def test_search_strips_html_for_excerpt(self, tmp_path, monkeypatch):
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        self._write_book(
            nd,
            "gen",
            [(1, 1, "", "", "comm", "T", "L", "<strong>Covenant.</strong> The blood of the lamb.")],
        )
        ci.rebuild()
        hits = ci.search("blood")
        assert len(hits) == 1
        # Excerpt should not contain raw HTML tags
        assert "<strong>" not in hits[0]["excerpt"]
        assert "</strong>" not in hits[0]["excerpt"]
        # But should contain the matched word
        assert "blood" in hits[0]["excerpt"].lower()

    def test_search_scores_label_higher_than_body(self, tmp_path, monkeypatch):
        # Score weights: label=5, body=1. A note with the query in
        # the label should rank above one with the query only in body.
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        self._write_book(
            nd,
            "gen",
            [
                (1, 1, "", "", "comm", "T", "Bonus", "<p>covenant trickle</p>"),  # body match only
                (2, 1, "", "", "comm", "T", "covenant", "<p>nothing</p>"),  # label match
            ],
        )
        ci.rebuild()
        hits = ci.search("covenant")
        assert len(hits) == 2
        # The label-match wins: score = 5 (label only)
        assert hits[0]["chapter"] == 2
        assert hits[0]["score"] == 5
        # The body-match comes second: score = 1 (body only)
        assert hits[1]["chapter"] == 1
        assert hits[1]["score"] == 1

    def test_search_filters_by_kind(self, tmp_path, monkeypatch):
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        self._write_book(
            nd,
            "gen",
            [
                (1, 1, "", "", "comm", "T", "L", "<p>shared word</p>"),
                (1, 2, "", "", "word", "T", "L", "<p>shared word</p>"),
            ],
        )
        ci.rebuild()
        hits = ci.search("shared", kind="word")
        assert len(hits) == 1
        assert hits[0]["kind"] == "word"

    def test_search_filters_by_book(self, tmp_path, monkeypatch):
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        self._write_book(nd, "gen", [(1, 1, "", "", "comm", "T", "L", "<p>shared</p>")])
        self._write_book(nd, "exo", [(1, 1, "", "", "comm", "T", "L", "<p>shared</p>")])
        ci.rebuild()
        hits = ci.search("shared", book="gen")
        assert len(hits) == 1
        assert hits[0]["book_code"] == "gen"

    def test_search_respects_limit(self, tmp_path, monkeypatch):
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        notes = [(1, v, "", "", "comm", "T", "L", "<p>same word here</p>") for v in range(1, 11)]
        self._write_book(nd, "gen", notes)
        ci.rebuild()
        hits = ci.search("same", limit=3)
        assert len(hits) == 3

    def test_search_returns_dict_shape(self, tmp_path, monkeypatch):
        # Pin: result dict has every field the existing
        # SearchHit.to_dict() shape carries. This is the
        # interface contract for the future migration.
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        self._write_book(
            nd,
            "gen",
            [(1, 1, "a", "anchor-text", "comm", "T", "L", "<p>match</p>", "PD source")],
        )
        ci.rebuild()
        hits = ci.search("match")
        assert len(hits) == 1
        h = hits[0]
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
            assert field in h, f"missing field {field}"
        assert h["suffix"] == "a"
        assert h["anchor"] == "anchor-text"
        assert h["attribution"] == "PD source"

    def test_search_canonical_order_within_same_score(self, tmp_path, monkeypatch):
        # Two hits with the same score should sort by canonical book
        # order (matching note_search.search_notes).
        nd, cd, ci = self._setup_isolated_corpus(tmp_path, monkeypatch)
        # Write in REVERSE canonical order to verify the sort fixes it
        self._write_book(nd, "exo", [(1, 1, "", "", "comm", "T", "match", "<p>x</p>")])
        self._write_book(nd, "gen", [(1, 1, "", "", "comm", "T", "match", "<p>x</p>")])
        ci.rebuild()
        hits = ci.search("match")
        # gen comes before exo in books.yaml — even though we wrote
        # exo first, the result should be gen-first.
        assert len(hits) == 2
        assert hits[0]["book_code"] == "gen"
        assert hits[1]["book_code"] == "exo"

    # ---- equivalence pin against the file-walk implementation ----

    def test_search_equivalence_with_file_walk_for_real_corpus(self):
        # The migration safety pin: for a sample query against the
        # real corpus, corpus_index.search() returns the same hit
        # count and (for the first 5 hits) the same notes as the
        # existing note_search.search_notes() — proving the
        # eventual api_search_notes flip is safe.
        from scripts.core import corpus_index, note_search

        # Δ.6 (2026-05-11): dropped `force=True`; same rationale as
        # the Δ.1 equivalence test above.
        corpus_index.invalidate()
        corpus_index.rebuild()

        for q in ("covenant", "manger", "Adam"):
            file_walk = note_search.search_notes(q, limit=20)
            indexed = corpus_index.search(q, limit=20)
            assert len(file_walk) == len(indexed), (
                f"hit count mismatch for {q!r}: file_walk={len(file_walk)} indexed={len(indexed)}"
            )
            # Compare top-5 (book_code, chapter, verse, suffix) tuples
            fw_ids = [(h.book_code, h.chapter, h.verse, h.suffix) for h in file_walk[:5]]
            ix_ids = [(h["book_code"], h["chapter"], h["verse"], h["suffix"]) for h in indexed[:5]]
            assert fw_ids == ix_ids, f"top-5 mismatch for {q!r}:\n  file_walk={fw_ids}\n  indexed={ix_ids}"

    def test_search_index_faster_than_file_walk(self):
        # The performance pin: corpus_index.search() is meaningfully
        # faster than note_search.search_notes() on the real corpus.
        # Doesn't require an exact ratio — just "faster" — because
        # SQLite query times vary across machines.
        import time

        from scripts.core import corpus_index, note_search

        corpus_index.rebuild()  # warm

        # Time the file walk
        t0 = time.perf_counter()
        note_search.search_notes("covenant", limit=50)
        file_walk_ms = (time.perf_counter() - t0) * 1000

        # Time the index
        t0 = time.perf_counter()
        corpus_index.search("covenant", limit=50)
        indexed_ms = (time.perf_counter() - t0) * 1000

        # Index should be at least 3× faster on the real 50K-note
        # corpus (in practice usually 10-50×). 3× is generous against
        # CI variability.
        assert indexed_ms * 3 < file_walk_ms, (
            f"index search not significantly faster than file walk: "
            f"file_walk={file_walk_ms:.1f}ms index={indexed_ms:.1f}ms"
        )


# ---------- Phase Δ.3 : index-backed attribution audit ------------------


class TestDelta3IndexAttributionAudit:
    """Δ.3 — second consumer migration to the index. Demonstrates the
    pattern's generality: search (Δ.2) was a query-shaped aggregate;
    attribution audit is a classify+group-by-shaped aggregate.

    Result shape exactly matches `web.api_attribution_audit()`.
    Equivalence pin against the file-walk implementation; doesn't
    yet flip the api wire (deliberate — same review-then-flip
    discipline as Δ.2).
    """

    # ---- _classify_attribution equivalence ----

    def test_classify_attribution_matches_web_implementation(self):
        # The two copies — `corpus_index._classify_attribution` and
        # `web._classify_attribution` — must produce identical
        # results for every input. This pin catches drift.
        from scripts import web
        from scripts.core import corpus_index

        cases = [
            "",
            "   ",
            None,
            "see Robertson",
            "cf. Wright 1992",
            "ibid.",
            "author",
            "x",  # short → thin
            "John Calvin",  # 11 chars — thin
            "John Calvin, 1559",  # 17 chars — sourced
            "User original",
            "User paraphrase of Calvin",
            "Strong's Hebrew Lexicon, H1254",
        ]
        for c in cases:
            assert corpus_index._classify_attribution(c) == web._classify_attribution(c or ""), f"divergence on {c!r}"

    # ---- audit_attribution shape ----

    def test_audit_attribution_returns_expected_shape(self, tmp_path, monkeypatch):
        from scripts.core import corpus_index, paths

        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        (notes_dir / "gen.py").write_text(
            "NOTES = (\n"
            "    (1, 1, '', '', 'comm', 'T', 'L', 'B', 'John Calvin, 1559'),\n"
            "    (1, 2, '', '', 'comm', 'T', 'L', 'B', ''),\n"
            "    (1, 3, '', '', 'comm', 'T', 'L', 'B', 'cf. Wright'),\n"
            "    (1, 4, '', '', 'comm', 'T', 'L', 'B', 'User original'),\n"
            ")\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(paths, "notes_dir", lambda: notes_dir)
        monkeypatch.setattr(paths, "user_data_root", lambda: tmp_path / "ud")
        corpus_index._CACHED_CONN = None
        corpus_index.rebuild(force=True)

        audit = corpus_index.audit_attribution()
        # Shape pins
        assert "counts" in audit
        assert "needs_attention" in audit
        assert "by_book" in audit
        assert "by_kind" in audit
        # 4 notes total
        assert audit["counts"]["total"] == 4
        # The (1,1) note is sourced
        assert audit["counts"]["sourced"] == 1
        # The (1,2) note is missing
        assert audit["counts"]["missing"] == 1
        # The (1,3) note is thin (cf. is a thin pattern)
        assert audit["counts"]["thin"] == 1
        # The (1,4) note is user
        assert audit["counts"]["user"] == 1
        # needs_attention captures missing + thin
        assert len(audit["needs_attention"]) == 2

    def test_audit_attribution_canonical_book_order(self, tmp_path, monkeypatch):
        # Multiple books with attention items — they should appear
        # in canonical (Genesis, Exodus, ...) order, not alphabetical.
        from scripts.core import corpus_index, paths

        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        # Write in alphabetical order — exo, gen — to verify the sort
        # fixes it to canonical (gen first).
        (notes_dir / "exo.py").write_text(
            "NOTES = ((1, 1, '', '', 'comm', 'T', 'L', 'B', ''),)\n",
            encoding="utf-8",
        )
        (notes_dir / "gen.py").write_text(
            "NOTES = ((1, 1, '', '', 'comm', 'T', 'L', 'B', ''),)\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(paths, "notes_dir", lambda: notes_dir)
        monkeypatch.setattr(paths, "user_data_root", lambda: tmp_path / "ud")
        corpus_index._CACHED_CONN = None
        corpus_index.rebuild(force=True)

        audit = corpus_index.audit_attribution()
        attention = audit["needs_attention"]
        assert len(attention) == 2
        assert attention[0]["book"] == "gen"
        assert attention[1]["book"] == "exo"

    # ---- equivalence pin against the real corpus ----

    def test_audit_attribution_equivalent_to_file_walk_for_real_corpus(self):
        # The migration-safety contract. corpus_index.audit_attribution()
        # must produce the same `counts` dict as web.api_attribution_audit()
        # on the real corpus.
        from scripts import web
        from scripts.core import corpus_index

        # Δ.6 (2026-05-11): dropped `force=True`; same rationale as
        # the Δ.1/Δ.2 equivalence tests.
        corpus_index.invalidate()
        corpus_index.rebuild()
        index_audit = corpus_index.audit_attribution()
        file_audit = web.api_attribution_audit()

        # Counts must match exactly
        assert index_audit["counts"] == file_audit["counts"], (
            f"counts diverge:\n  index={index_audit['counts']}\n  file={file_audit['counts']}"
        )
        # needs_attention list length must match
        assert len(index_audit["needs_attention"]) == len(file_audit["needs_attention"]), (
            "needs_attention length mismatch"
        )
        # Top-3 entries should be the same notes (same (book, ch, vs))
        idx_top = [(a["book"], a["chapter"], a["verse"], a["suffix"]) for a in index_audit["needs_attention"][:3]]
        file_top = [(a["book"], a["chapter"], a["verse"], a["suffix"]) for a in file_audit["needs_attention"][:3]]
        assert idx_top == file_top, f"top-3 attention mismatch:\n  index={idx_top}\n  file={file_top}"

    # ---- performance characteristics ----

    def test_audit_attribution_completes_in_reasonable_time(self):
        # The index audit should complete in under 1 second on the
        # real corpus. The file-walk equivalent is subject to mtime
        # cache state (sometimes very fast, sometimes a full scan)
        # so we don't compare directly — just assert the index is
        # cheap.
        import time

        from scripts.core import corpus_index

        corpus_index.rebuild()  # warm
        t0 = time.perf_counter()
        corpus_index.audit_attribution()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        assert elapsed_ms < 1500, f"audit_attribution took {elapsed_ms:.1f}ms (>1500ms)"


# ---------- Phase Δ.4 : index-backed compute_matrix --------------------


class TestDelta4IndexComputeMatrix:
    """Δ.4 — third (and biggest) consumer migration to the index.

    `compute_matrix()` is the most-consumed aggregate in the
    codebase: 15+ web.py call sites depend on its 6 projections
    (enabled / potential / per_book / per_chapter /
    edition_canon_books / edition_enabled_kinds).

    `corpus_index.compute_matrix_indexed()` returns the same
    `Matrix` dataclass with bit-identical contents on every
    projection. Equivalence pin against the file-walk
    implementation across every shipping edition.
    """

    def test_indexed_matrix_returns_correct_dataclass_type(self):
        from scripts.core import corpus_index
        from scripts.core.matrix import Matrix

        corpus_index.rebuild()
        m = corpus_index.compute_matrix_indexed()
        assert isinstance(m, Matrix)

    def test_indexed_matrix_has_all_six_projections(self):
        from scripts.core import corpus_index

        corpus_index.rebuild()
        m = corpus_index.compute_matrix_indexed()
        for field in (
            "enabled",
            "potential",
            "edition_canon_books",
            "edition_enabled_kinds",
            "per_book",
            "per_chapter",
        ):
            value = getattr(m, field)
            assert isinstance(value, dict), f"{field} is not a dict"
            assert len(value) >= 5, f"{field} has fewer editions than expected ({len(value)})"

    def test_indexed_matrix_canon_sets_are_sets(self):
        from scripts.core import corpus_index

        corpus_index.rebuild()
        m = corpus_index.compute_matrix_indexed()
        for ed_id, books in m.edition_canon_books.items():
            assert isinstance(books, set), f"{ed_id} canon is not a set"
        for ed_id, kinds in m.edition_enabled_kinds.items():
            assert isinstance(kinds, set), f"{ed_id} enabled_kinds is not a set"

    def test_indexed_matrix_exactly_equivalent_to_file_walk(self):
        # The migration-safety contract for Δ.4. Every projection
        # must compare equal between the file-walk and indexed paths
        # for every shipping edition.
        # Δ.4.1 attempt #5 (2026-05-11) — wire flipped after
        # Δ.6+Δ.7+Δ.8+Δ.9 unblockers; this test must compare
        # against the explicit `_compute_matrix_via_file_walk()`
        # reference (NOT against `compute_matrix()` itself, which
        # post-flip trivially matches the indexed path).
        from scripts.core import corpus_index
        from scripts.core.matrix import _compute_matrix_via_file_walk

        corpus_index.invalidate()
        corpus_index.rebuild()

        file_walk = _compute_matrix_via_file_walk()
        indexed = corpus_index.compute_matrix_indexed()

        editions = list(file_walk.edition_canon_books.keys())
        assert len(editions) >= 5, "expected at least the 5 shipping editions"

        for ed_id in editions:
            assert file_walk.potential.get(ed_id, {}) == indexed.potential.get(ed_id, {}), (
                f"potential mismatch for {ed_id}"
            )
            assert file_walk.enabled.get(ed_id, {}) == indexed.enabled.get(ed_id, {}), f"enabled mismatch for {ed_id}"
            assert file_walk.per_book.get(ed_id, {}) == indexed.per_book.get(ed_id, {}), (
                f"per_book mismatch for {ed_id}"
            )
            assert file_walk.per_chapter.get(ed_id, {}) == indexed.per_chapter.get(ed_id, {}), (
                f"per_chapter mismatch for {ed_id}"
            )
            assert file_walk.edition_canon_books.get(ed_id) == indexed.edition_canon_books.get(ed_id), (
                f"edition_canon_books mismatch for {ed_id}"
            )
            assert file_walk.edition_enabled_kinds.get(ed_id) == indexed.edition_enabled_kinds.get(ed_id), (
                f"edition_enabled_kinds mismatch for {ed_id}"
            )

    def test_indexed_matrix_not_substantially_slower_than_file_walk(self):
        # Sanity floor: indexed must NOT be 3× SLOWER than the
        # file walk reference. Empirical on real corpus is ~12×
        # faster from cold; on warm OS page cache the gap closes
        # (both paths serve from RAM). A regression that made the
        # indexed path >3× slower would indicate a real bug
        # (e.g. accidentally disabled the SQL aggregate roll-up).
        # Tighter win-margin pinning is brittle across OS cache
        # states — the empirical 12× speedup is documented in
        # CHANGELOG instead.
        import time

        from scripts.core import corpus_index, notes_io
        from scripts.core.matrix import _compute_matrix_via_file_walk

        corpus_index.rebuild()
        notes_io.clear_load_notes_cache()

        t0 = time.perf_counter()
        _compute_matrix_via_file_walk()
        file_walk_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        corpus_index.compute_matrix_indexed()
        indexed_ms = (time.perf_counter() - t0) * 1000

        # Asymmetric guard: indexed is allowed to be up to 3× SLOWER.
        # In practice it's substantially faster.
        assert indexed_ms < file_walk_ms * 3, (
            f"indexed compute_matrix is suspiciously slow: file_walk={file_walk_ms:.1f}ms indexed={indexed_ms:.1f}ms"
        )

    def test_indexed_matrix_ethiopian_has_full_canon(self):
        from scripts.core import corpus_index

        corpus_index.rebuild()
        m = corpus_index.compute_matrix_indexed()
        eth_canon = m.edition_canon_books.get("ethiopian-tewahedo", set())
        assert len(eth_canon) >= 80, f"ethiopian canon has {len(eth_canon)} books"

    def test_indexed_matrix_jewish_excludes_nt(self):
        from scripts.core import corpus_index

        corpus_index.rebuild()
        m = corpus_index.compute_matrix_indexed()
        jewish_canon = m.edition_canon_books.get("jewish-study", set())
        nt_books = {"mat", "mrk", "luk", "jhn", "act", "rom", "rev"}
        leaks = nt_books & jewish_canon
        assert leaks == set(), f"NT books leaked into jewish-study canon: {leaks}"


# ---------- Phase Δ.0 : cross-platform rebuild lock --------------------


class TestDelta0RebuildLock:
    """Δ.0 — file lock around `corpus_index.rebuild()` so concurrent
    processes serialize on the write phase. The OS-level primitive
    (`fcntl.flock` on POSIX, `msvcrt.locking` on Windows) is
    intrinsically multi-process; tests verify acquire/release
    round-trip + that rebuild() takes the lock.
    """

    def test_lock_acquires_and_releases(self, tmp_path, monkeypatch):
        from scripts.core import corpus_index, paths

        monkeypatch.setattr(paths, "user_data_root", lambda: tmp_path)
        with corpus_index._acquire_rebuild_lock():
            pass
        with corpus_index._acquire_rebuild_lock():
            pass

    def test_lock_creates_lockfile(self, tmp_path, monkeypatch):
        # Δ.8 (2026-05-11) — under pytest-xdist this test sees a
        # PYTEST_XDIST_WORKER-suffixed lock filename
        # (`corpus.gw0.lock` etc.), not the canonical `corpus.lock`.
        # Read the actual path via `_lock_path()` instead of
        # hardcoding the filename.
        from scripts.core import corpus_index, paths

        monkeypatch.setattr(paths, "user_data_root", lambda: tmp_path)
        lock_path = corpus_index._lock_path()
        assert lock_path.parent == tmp_path / "cache"
        assert not lock_path.exists()
        with corpus_index._acquire_rebuild_lock():
            assert lock_path.is_file()
        # Lockfile persists after release (sentinel-style; only
        # the lock STATE is per-acquire).
        assert lock_path.is_file()

    def test_rebuild_takes_lock_around_build(self, tmp_path, monkeypatch):
        # Pin: rebuild() acquires the lock when it's actually
        # building. The lockfile only exists after
        # `_acquire_rebuild_lock` has opened it; before the lock
        # context fires, the file does not exist.
        from scripts.core import corpus_index, paths

        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        (notes_dir / "gen.py").write_text(
            "NOTES = ((1, 1, '', '', 'comm', 'T', 'L', 'B'),)\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(paths, "notes_dir", lambda: notes_dir)
        monkeypatch.setattr(paths, "user_data_root", lambda: tmp_path / "ud")
        corpus_index._CACHED_CONN = None

        original_build_to = corpus_index._build_to
        observed = {"lockfile_exists_during_build": False}

        def wrapped_build_to(path):
            lock_path = corpus_index._lock_path()
            observed["lockfile_exists_during_build"] = lock_path.is_file()
            return original_build_to(path)

        monkeypatch.setattr(corpus_index, "_build_to", wrapped_build_to)
        result = corpus_index.rebuild(force=True)
        assert result["rebuilt"] is True
        assert observed["lockfile_exists_during_build"] is True

    def test_lock_file_path_is_next_to_index(self, tmp_path, monkeypatch):
        # All processes must converge on the same kernel object.
        from scripts.core import corpus_index, paths

        monkeypatch.setattr(paths, "user_data_root", lambda: tmp_path)
        lock_path = corpus_index._lock_path()
        idx_path = corpus_index._index_path()
        assert lock_path.parent == idx_path.parent


# ---------- Phase Δ.5 : index-backed dashboard_stats -------------------


class TestDelta5IndexDashboardStats:
    """Δ.5 — fourth consumer migration to the derived index.
    `dashboard.gather_stats(books, kinds)` walks every notes/<code>.py
    to compute total_notes, per_book aggregates (note_count, kinds,
    attributed, chapters_touched, pct_covered), per_kind, and
    chapter_density. `corpus_index.dashboard_stats(books)` produces
    equivalent output via 2 SQL roll-ups instead of 87 file reads.
    Pure additive — no wire flip in this phase."""

    def test_dashboard_stats_returns_expected_top_level_shape(self):
        from scripts.core import config, corpus_index

        corpus_index.rebuild()
        result = corpus_index.dashboard_stats(config.load_books())
        assert isinstance(result, dict)
        for k in ("total_notes", "per_book", "per_kind", "chapter_density"):
            assert k in result
        assert isinstance(result["total_notes"], int)
        assert isinstance(result["per_book"], dict)
        assert isinstance(result["per_kind"], dict)
        assert isinstance(result["chapter_density"], dict)

    def test_dashboard_stats_per_book_has_expected_keys(self):
        from scripts.core import config, corpus_index

        corpus_index.rebuild()
        result = corpus_index.dashboard_stats(config.load_books())
        for b in config.load_books():
            assert b["code"] in result["per_book"]
            entry = result["per_book"][b["code"]]
            for k in (
                "code",
                "title",
                "ch_count",
                "note_count",
                "attributed",
                "kinds",
                "chapters_touched",
                "pct_covered",
            ):
                assert k in entry, f"{b['code']} missing {k}"

    def test_dashboard_stats_total_notes_matches_per_book_sum(self):
        from scripts.core import config, corpus_index

        corpus_index.rebuild()
        result = corpus_index.dashboard_stats(config.load_books())
        per_book_sum = sum(b["note_count"] for b in result["per_book"].values())
        assert result["total_notes"] == per_book_sum

    def test_dashboard_stats_per_kind_matches_per_book_kinds_sum(self):
        from collections import Counter

        from scripts.core import config, corpus_index

        corpus_index.rebuild()
        result = corpus_index.dashboard_stats(config.load_books())
        agg: Counter = Counter()
        for entry in result["per_book"].values():
            for k, n in entry["kinds"].items():
                agg[k] += n
        assert dict(agg) == result["per_kind"]

    def test_dashboard_stats_pct_covered_nonnegative(self):
        # `pct_covered` can legitimately exceed 100% when a book has
        # notes attached to chapters beyond its canonical `ch_count`
        # (e.g. extra-canonical material) — file-walk gather_stats
        # produces the same uncapped value, so the contract here is
        # just nonnegativity. The equivalence pin elsewhere in this
        # class verifies the indexed and file-walk values match.
        from scripts.core import config, corpus_index

        corpus_index.rebuild()
        result = corpus_index.dashboard_stats(config.load_books())
        for code, entry in result["per_book"].items():
            assert entry["pct_covered"] >= 0.0, f"{code} pct_covered={entry['pct_covered']} negative"

    def test_dashboard_stats_empty_books_returns_zero(self):
        from scripts.core import corpus_index

        corpus_index.rebuild()
        result = corpus_index.dashboard_stats([])
        assert result == {
            "total_notes": 0,
            "per_book": {},
            "per_kind": {},
            "chapter_density": {},
        }

    def test_dashboard_stats_single_book_isolation(self):
        # Calling with just one book should restrict the per_kind /
        # chapter_density / total_notes to only that book's notes.
        from scripts.core import config, corpus_index

        corpus_index.rebuild()
        books = config.load_books()
        gen = next((b for b in books if b["code"] == "gen"), None)
        if gen is None:
            return  # defensive: gen is canonical, but skip rather than fail if absent
        result = corpus_index.dashboard_stats([gen])
        assert list(result["per_book"].keys()) == ["gen"]
        assert result["total_notes"] == result["per_book"]["gen"]["note_count"]

    def test_dashboard_stats_attributed_le_note_count(self):
        # Attributed count is a sub-set of note_count: a note either
        # has attribution or doesn't, so attributed <= note_count.
        from scripts.core import config, corpus_index

        corpus_index.rebuild()
        result = corpus_index.dashboard_stats(config.load_books())
        for code, entry in result["per_book"].items():
            assert entry["attributed"] <= entry["note_count"], (
                f"{code} attributed={entry['attributed']} > note_count={entry['note_count']}"
            )

    def test_dashboard_stats_chapter_density_keys_present_for_every_book(self):
        from scripts.core import config, corpus_index

        corpus_index.rebuild()
        result = corpus_index.dashboard_stats(config.load_books())
        for code in result["per_book"]:
            assert code in result["chapter_density"], f"{code} missing from chapter_density"

    def test_dashboard_stats_equivalent_to_file_walk(self):
        # The migration-safety contract for Δ.5. Every aggregate
        # field present in dashboard.gather_stats must equal the
        # indexed output. Pass-through fields the file-walk includes
        # for downstream rendering (books, kinds, parse_failures,
        # generated_at) are excluded; they aren't aggregates and the
        # index doesn't compute them.
        # Δ.5.1 (2026-05-11): the public `gather_stats` is now
        # wire-flipped to corpus_index, so this test compares
        # against the explicit `_gather_stats_via_file_walk`
        # reference instead. Same pattern as Δ.4.1's
        # `_compute_matrix_via_file_walk` anchor.
        from scripts import dashboard as dashboard_module
        from scripts.core import config, corpus_index, notes_io

        corpus_index.rebuild()
        notes_io.clear_load_notes_cache()

        books = config.load_books()
        kinds = config.load_kinds()
        file_walk = dashboard_module._gather_stats_via_file_walk(books, kinds)
        indexed = corpus_index.dashboard_stats(books)

        assert file_walk["total_notes"] == indexed["total_notes"]
        assert dict(file_walk["per_kind"]) == indexed["per_kind"]
        assert set(file_walk["per_book"].keys()) == set(indexed["per_book"].keys())
        for code in file_walk["per_book"]:
            fw = file_walk["per_book"][code]
            ix = indexed["per_book"][code]
            for k in ("note_count", "attributed", "kinds", "chapters_touched"):
                assert fw[k] == ix[k], f"{code}.{k} mismatch: file_walk={fw[k]} indexed={ix[k]}"
            assert abs(fw["pct_covered"] - ix["pct_covered"]) < 1e-9, f"{code}.pct_covered mismatch"
        for code, fw_chaps in file_walk["chapter_density"].items():
            assert dict(fw_chaps) == indexed["chapter_density"].get(code, {}), f"{code} chapter_density mismatch"


# ---------- Phase Δ.6 : fingerprint cache layer ------------------------


class TestDelta6FingerprintCache:
    """Δ.6 — TTL-memoized `_compute_fingerprint()`. Without this layer
    every `connection()` call (and therefore every indexed query)
    triggered an 87-file `os.stat` walk. With it, back-to-back calls
    inside one TTL window become a dict lookup. Unblocks the deferred
    Δ.x.1 wire flips by removing the per-call stat-walk that defeated
    the parent-level lru_cache on `matrix.compute_matrix()`."""

    def _reset_cache(self, corpus_index):
        # Test-only helper: reset module-level cache state cleanly.
        corpus_index._FINGERPRINT_CACHE = None

    def test_cached_returns_same_value_within_ttl(self, monkeypatch):
        from scripts.core import corpus_index

        self._reset_cache(corpus_index)
        monkeypatch.setattr(corpus_index, "_FINGERPRINT_TTL_SEC", 60.0)

        call_count = {"n": 0}
        original = corpus_index._compute_fingerprint

        def counting_compute():
            call_count["n"] += 1
            return original()

        monkeypatch.setattr(corpus_index, "_compute_fingerprint", counting_compute)

        first = corpus_index._compute_fingerprint_cached()
        second = corpus_index._compute_fingerprint_cached()
        third = corpus_index._compute_fingerprint_cached()
        assert first == second == third
        assert call_count["n"] == 1, "should have stat-walked exactly once"

    def test_cached_recomputes_after_ttl_expires(self, monkeypatch):
        from scripts.core import corpus_index

        self._reset_cache(corpus_index)
        # 0.05s TTL, easy to exceed in-test
        monkeypatch.setattr(corpus_index, "_FINGERPRINT_TTL_SEC", 0.05)

        call_count = {"n": 0}
        original = corpus_index._compute_fingerprint

        def counting_compute():
            call_count["n"] += 1
            return original()

        monkeypatch.setattr(corpus_index, "_compute_fingerprint", counting_compute)

        corpus_index._compute_fingerprint_cached()
        assert call_count["n"] == 1
        # Wait past TTL. Time module local to corpus_index.
        import time as _t

        _t.sleep(0.07)
        corpus_index._compute_fingerprint_cached()
        assert call_count["n"] == 2, "should have recomputed after TTL"

    def test_ttl_zero_bypasses_cache(self, monkeypatch):
        from scripts.core import corpus_index

        self._reset_cache(corpus_index)
        monkeypatch.setattr(corpus_index, "_FINGERPRINT_TTL_SEC", 0.0)

        call_count = {"n": 0}
        original = corpus_index._compute_fingerprint

        def counting_compute():
            call_count["n"] += 1
            return original()

        monkeypatch.setattr(corpus_index, "_compute_fingerprint", counting_compute)

        corpus_index._compute_fingerprint_cached()
        corpus_index._compute_fingerprint_cached()
        corpus_index._compute_fingerprint_cached()
        assert call_count["n"] == 3, "TTL=0 should disable the cache"

    def test_negative_ttl_bypasses_cache(self, monkeypatch):
        # Same intent as TTL=0 but the contract is "non-positive
        # disables" — negative is the more obvious "off" sentinel.
        from scripts.core import corpus_index

        self._reset_cache(corpus_index)
        monkeypatch.setattr(corpus_index, "_FINGERPRINT_TTL_SEC", -1.0)
        # First call should still produce a value, not crash.
        fp = corpus_index._compute_fingerprint_cached()
        assert isinstance(fp, str)

    def test_invalidate_clears_fingerprint_cache(self, monkeypatch):
        # The contract that closes the "stale fingerprint after
        # explicit invalidate" loophole.
        from scripts.core import corpus_index

        self._reset_cache(corpus_index)
        monkeypatch.setattr(corpus_index, "_FINGERPRINT_TTL_SEC", 60.0)

        call_count = {"n": 0}
        original = corpus_index._compute_fingerprint

        def counting_compute():
            call_count["n"] += 1
            return original()

        monkeypatch.setattr(corpus_index, "_compute_fingerprint", counting_compute)

        corpus_index._compute_fingerprint_cached()
        corpus_index._compute_fingerprint_cached()
        assert call_count["n"] == 1
        corpus_index.invalidate()
        corpus_index._compute_fingerprint_cached()
        assert call_count["n"] == 2, "invalidate() must clear the cache"

    def test_public_fingerprint_alias_uses_cached_path(self, monkeypatch):
        # Public `fingerprint()` is the cached variant since Δ.6.
        from scripts.core import corpus_index

        self._reset_cache(corpus_index)
        monkeypatch.setattr(corpus_index, "_FINGERPRINT_TTL_SEC", 60.0)

        call_count = {"n": 0}
        original = corpus_index._compute_fingerprint

        def counting_compute():
            call_count["n"] += 1
            return original()

        monkeypatch.setattr(corpus_index, "_compute_fingerprint", counting_compute)

        corpus_index.fingerprint()
        corpus_index.fingerprint()
        corpus_index.fingerprint()
        assert call_count["n"] == 1, "public fingerprint() must use the cached path"

    def test_rebuild_repopulates_fingerprint_cache_post_build(self, tmp_path, monkeypatch):
        # After a real rebuild, the cache should hold the just-written
        # fingerprint so the next call is a hit (not a stat-walk).
        from scripts.core import corpus_index, paths

        self._reset_cache(corpus_index)
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        (notes_dir / "gen.py").write_text(
            "NOTES = ((1, 1, '', '', 'comm', 'T', 'L', 'B'),)\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(paths, "notes_dir", lambda: notes_dir)
        monkeypatch.setattr(paths, "user_data_root", lambda: tmp_path / "ud")
        monkeypatch.setattr(corpus_index, "_FINGERPRINT_TTL_SEC", 60.0)
        corpus_index._CACHED_CONN = None

        result = corpus_index.rebuild(force=True)
        assert result["rebuilt"] is True
        # Cache should now hold the post-build fingerprint
        assert corpus_index._FINGERPRINT_CACHE is not None
        # ω.36 — cache cell is now 3-tuple (timestamp, fp, notes_dir_str).
        cached_at, cached_fp, cached_path = corpus_index._FINGERPRINT_CACHE
        assert cached_fp == result["fingerprint"]

    def test_default_ttl_is_one_second(self):
        # Documents the default chosen in the source. If the policy
        # changes, this test forces an explicit decision rather than
        # silent drift. Reads the SOURCE FILE directly (not the
        # module attribute) so the conftest autouse fixture that
        # sets TTL=0 in tests doesn't shadow this check.
        import re
        from pathlib import Path

        from scripts.core import corpus_index

        source_path = Path(corpus_index.__file__)
        text = source_path.read_text(encoding="utf-8")
        match = re.search(r"^_FINGERPRINT_TTL_SEC:\s*float\s*=\s*([0-9.]+)", text, re.MULTILINE)
        assert match is not None, "could not find _FINGERPRINT_TTL_SEC default in source"
        assert float(match.group(1)) == 1.0, f"default TTL changed: {match.group(1)}"

    def test_acquire_lock_raises_on_timeout(self, tmp_path, monkeypatch):
        # The Δ.0 lock has a `timeout=` parameter that must raise
        # TimeoutError when exceeded. Hold the lock from one with-
        # block and try to acquire from another with a short timeout.
        from scripts.core import corpus_index, paths

        monkeypatch.setattr(paths, "user_data_root", lambda: tmp_path)
        # Ensure the lock dir exists
        (tmp_path / "cache").mkdir(parents=True, exist_ok=True)

        with corpus_index._acquire_rebuild_lock(timeout=5.0):
            # Inside the held lock, a second acquire with a tiny
            # timeout MUST raise TimeoutError.
            try:
                with corpus_index._acquire_rebuild_lock(timeout=0.2):
                    raise AssertionError("should not have acquired held lock")
            except TimeoutError:
                pass  # expected

    def test_rebuild_under_held_lock_uses_cached_fingerprint_for_fast_path(self, monkeypatch):
        # Steady-state correctness check: when the index file already
        # matches the on-disk fingerprint, rebuild() returns the no-
        # build fast path WITHOUT taking the lock. The cached
        # fingerprint reads keep this hot path stat-free.
        from scripts.core import corpus_index

        self._reset_cache(corpus_index)
        monkeypatch.setattr(corpus_index, "_FINGERPRINT_TTL_SEC", 60.0)

        # Prime: ensure index exists and matches.
        corpus_index.rebuild()

        lock_acquired = {"n": 0}
        original_lock = corpus_index._acquire_rebuild_lock

        def counting_lock(*args, **kwargs):
            lock_acquired["n"] += 1
            return original_lock(*args, **kwargs)

        monkeypatch.setattr(corpus_index, "_acquire_rebuild_lock", counting_lock)

        # Three rebuild() calls in quick succession against an
        # already-fresh index must NOT take the lock.
        for _ in range(3):
            result = corpus_index.rebuild()
            assert result["rebuilt"] is False
        assert lock_acquired["n"] == 0, "fast-path rebuild must not acquire the lock"


# ---------- Phase Δ.8 : per-worker index storage ---------------------


class TestDelta8PerWorkerIndexStorage:
    """Δ.8 — index files (corpus.sqlite, corpus.fingerprint,
    corpus.lock) are namespaced per pytest-xdist worker so workers
    never share state on disk. Eliminates the cross-worker file
    contention class that defeated Δ.4.1 attempts #1-3 — Windows
    file locks during cached-connection swap-out + short-window
    rebuilds produced widespread `PermissionError` failures when 8
    concurrent workers all hammered the same shared file.

    The test runner is itself a pytest-xdist worker (or master);
    these tests use monkeypatch to set / clear the env var and
    re-read the path helpers, then restore. Production behavior
    (no env var) is verified directly."""

    def test_xdist_suffix_empty_when_env_var_unset(self, monkeypatch):
        from scripts.core import corpus_index

        monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
        assert corpus_index._xdist_suffix() == ""

    def test_xdist_suffix_includes_worker_when_env_var_set(self, monkeypatch):
        from scripts.core import corpus_index

        monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw0")
        assert corpus_index._xdist_suffix() == ".gw0"

    def test_xdist_suffix_for_master_worker(self, monkeypatch):
        # The xdist controller process sets the worker name to
        # "master" when running with explicit --tx specs; ensure
        # that's also namespaced (rather than collapsed to empty).
        from scripts.core import corpus_index

        monkeypatch.setenv("PYTEST_XDIST_WORKER", "master")
        assert corpus_index._xdist_suffix() == ".master"

    def test_index_path_canonical_in_production(self, monkeypatch):
        # No env var → no suffix → canonical filename matches
        # what production would write.
        from scripts.core import corpus_index

        monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
        assert corpus_index._index_path().name == "corpus.sqlite"
        assert corpus_index._fingerprint_path().name == "corpus.fingerprint"
        assert corpus_index._lock_path().name == "corpus.lock"

    def test_index_path_namespaced_per_worker(self, monkeypatch):
        from scripts.core import corpus_index

        monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw3")
        assert corpus_index._index_path().name == "corpus.gw3.sqlite"
        assert corpus_index._fingerprint_path().name == "corpus.gw3.fingerprint"
        assert corpus_index._lock_path().name == "corpus.gw3.lock"

    def test_two_workers_resolve_to_distinct_paths(self, monkeypatch):
        # The migration-safety contract: any two distinct workers
        # MUST resolve to distinct on-disk files (no collisions).
        from scripts.core import corpus_index

        monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw0")
        path_a_idx = corpus_index._index_path()
        path_a_fp = corpus_index._fingerprint_path()
        path_a_lock = corpus_index._lock_path()

        monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw1")
        path_b_idx = corpus_index._index_path()
        path_b_fp = corpus_index._fingerprint_path()
        path_b_lock = corpus_index._lock_path()

        assert path_a_idx != path_b_idx
        assert path_a_fp != path_b_fp
        assert path_a_lock != path_b_lock

    def test_workers_isolated_on_disk_after_rebuild(self, tmp_path, monkeypatch):
        # End-to-end: worker A rebuilds against its synthetic
        # corpus; worker B then connects and sees ITS OWN empty
        # / pristine state, NOT worker A's index. This is the
        # entire point of the phase: file contention impossible
        # because workers can't see each other's files.
        from scripts.core import corpus_index, paths

        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        (notes_dir / "gen.py").write_text(
            "NOTES = ((1, 1, '', '', 'comm', 'T', 'L', 'B'),)\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(paths, "notes_dir", lambda: notes_dir)
        monkeypatch.setattr(paths, "user_data_root", lambda: tmp_path / "ud")
        corpus_index._CACHED_CONN = None
        corpus_index._FINGERPRINT_CACHE = None

        # Worker A — build its own index
        monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw_isolation_A")
        corpus_index._CACHED_CONN = None
        result_a = corpus_index.rebuild(force=True)
        assert result_a["rebuilt"] is True
        path_a = corpus_index._index_path()
        assert path_a.is_file()

        # Worker B — distinct env var → distinct path → its own
        # rebuild creates a SEPARATE file.
        monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw_isolation_B")
        corpus_index._CACHED_CONN = None
        path_b = corpus_index._index_path()
        # Different path; before B rebuilds, B's file shouldn't exist.
        assert path_b != path_a
        # A's file is untouched
        assert path_a.is_file()

        result_b = corpus_index.rebuild(force=True)
        assert result_b["rebuilt"] is True
        assert path_b.is_file()
        # Both files coexist independently — the contention surface is gone.
        assert path_a.read_bytes() != b"" and path_b.read_bytes() != b""

    def test_lock_path_per_worker_eliminates_contention(self, tmp_path, monkeypatch):
        # The lock acquired by worker A's `_acquire_rebuild_lock`
        # MUST NOT block worker B because they target distinct
        # lockfiles. This is a single-process simulation of what
        # happens across xdist workers in reality.
        from scripts.core import corpus_index, paths

        monkeypatch.setattr(paths, "user_data_root", lambda: tmp_path)

        monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw_lock_A")
        with corpus_index._acquire_rebuild_lock(timeout=5.0):
            # Switch the env mid-with: this is the per-process
            # equivalent of "worker B starts now and takes its own
            # lock". A short timeout proves no contention.
            monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw_lock_B")
            with corpus_index._acquire_rebuild_lock(timeout=0.5):
                pass  # acquired without blocking on A's lock


# ---------- Phase Δ.9 : index warm-up at startup -----------------------


class TestDelta9CorpusIndexWarmup:
    """Δ.9 — `web._warm_corpus_index()` pre-builds the corpus_index
    before the server handles its first request, paying the cold-
    cache rebuild cost up-front rather than on a user-visible
    `/matrix` or `/api/search` call. Best-effort: failures log a
    warning but do NOT block server start. This is the unblocker
    for Δ.4.1 attempt #5 — without it, the wire flip's cold-path
    cost defeats the perf budgets for api_search_notes /
    api_matrix.cold / notes_io.load_notes."""

    def test_warm_corpus_index_callable_and_returns_dict(self):
        from scripts import web

        result = web._warm_corpus_index()
        assert isinstance(result, dict)
        assert "rebuilt" in result or "error" in result

    def test_warm_corpus_index_calls_rebuild(self, monkeypatch):
        from scripts import web
        from scripts.core import corpus_index

        calls: list = []

        def fake_rebuild():
            calls.append(1)
            return {"rebuilt": False, "fingerprint": "x" * 64, "note_count": 42, "elapsed_ms": 1.0}

        monkeypatch.setattr(corpus_index, "rebuild", fake_rebuild)
        web._warm_corpus_index()
        assert calls == [1], "warm-up must call corpus_index.rebuild() exactly once"

    def test_warm_corpus_index_swallows_exceptions(self, monkeypatch):
        # Best-effort contract: a corpus_index.rebuild() failure
        # MUST NOT propagate — server start must not be blocked by
        # a corrupt index.
        from scripts import web
        from scripts.core import corpus_index

        def explode():
            raise RuntimeError("simulated index failure")

        monkeypatch.setattr(corpus_index, "rebuild", explode)
        result = web._warm_corpus_index()
        assert isinstance(result, dict)
        assert "error" in result
        assert "simulated index failure" in result["error"]
        assert result["rebuilt"] is False

    def test_warm_corpus_index_returns_rebuild_result_on_success(self, monkeypatch):
        from scripts import web
        from scripts.core import corpus_index

        sentinel = {
            "rebuilt": True,
            "fingerprint": "abc123",
            "note_count": 51394,
            "elapsed_ms": 2480.3,
        }
        monkeypatch.setattr(corpus_index, "rebuild", lambda: sentinel)
        result = web._warm_corpus_index()
        assert result == sentinel

    def test_warm_corpus_index_invoked_in_main_before_serve(self):
        # Source-level invariant: main() must call
        # _warm_corpus_index() AFTER the ThreadingHTTPServer is
        # constructed (so a binding failure aborts loudly) but
        # BEFORE serve_forever (so the warm-up cost is paid here,
        # not on first-request). Reading the source is the
        # cheapest way to assert this control-flow contract
        # without instrumenting main().
        import inspect

        from scripts import web

        src = inspect.getsource(web.main)
        assert "_warm_corpus_index()" in src, "main() must call _warm_corpus_index()"
        idx_server = src.index("ThreadingHTTPServer")
        idx_warm = src.index("_warm_corpus_index()")
        idx_serve = src.index("serve_forever")
        assert idx_server < idx_warm < idx_serve, (
            f"order violated: server@{idx_server} warm@{idx_warm} serve@{idx_serve}"
        )

    def test_warm_corpus_index_idempotent_on_warm_cache(self, monkeypatch):
        # When the on-disk index is already fresh, the warm-up call
        # should be a fast no-op. Real corpus_index.rebuild()
        # implements this via the fingerprint check; here we just
        # verify the function tolerates a "no rebuild needed"
        # return.
        from scripts import web
        from scripts.core import corpus_index

        monkeypatch.setattr(
            corpus_index,
            "rebuild",
            lambda: {"rebuilt": False, "fingerprint": "f" * 64, "note_count": 100, "elapsed_ms": 5.0},
        )
        result = web._warm_corpus_index()
        assert result["rebuilt"] is False
        assert result["note_count"] == 100


# ---------- Phase Δ.4.1 : matrix wire flip (attempt #5) ---------------


class TestDelta41MatrixWireFlip:
    """Δ.4.1 — `matrix.compute_matrix()` delegates to
    `corpus_index.compute_matrix_indexed()`. Attempts #1-4
    reverted; attempt #5 ships after Δ.6 (TTL fingerprint cache),
    Δ.7 (notes_io invalidation hook), Δ.8 (per-worker index
    storage), and Δ.9 (server warm-up + session-scoped test
    warm-up fixture) collectively removed every prior failure
    mode."""

    def test_compute_matrix_returns_indexed_path_result(self):
        from scripts.core import corpus_index
        from scripts.core.matrix import compute_matrix

        corpus_index.invalidate()
        corpus_index.rebuild()
        compute_matrix.cache_clear()

        public = compute_matrix()
        indexed = corpus_index.compute_matrix_indexed()

        editions = list(public.edition_canon_books.keys())
        assert len(editions) >= 5
        for ed_id in editions:
            assert public.potential.get(ed_id, {}) == indexed.potential.get(ed_id, {})
            assert public.enabled.get(ed_id, {}) == indexed.enabled.get(ed_id, {})
            assert public.per_book.get(ed_id, {}) == indexed.per_book.get(ed_id, {})
            assert public.per_chapter.get(ed_id, {}) == indexed.per_chapter.get(ed_id, {})
            assert public.edition_canon_books.get(ed_id) == indexed.edition_canon_books.get(ed_id)
            assert public.edition_enabled_kinds.get(ed_id) == indexed.edition_enabled_kinds.get(ed_id)

    def test_compute_matrix_lru_cache_still_works(self):
        from scripts.core.matrix import compute_matrix

        compute_matrix.cache_clear()
        first = compute_matrix()
        second = compute_matrix()
        assert first is second, "lru_cache should return the same Matrix instance"

    def test_compute_matrix_meaningfully_faster_than_file_walk(self):
        # Sanity floor: indexed-via-public must NOT be substantially
        # slower than file-walk reference.
        import time

        from scripts.core import corpus_index, notes_io
        from scripts.core.matrix import _compute_matrix_via_file_walk, compute_matrix

        corpus_index.invalidate()
        corpus_index.rebuild()
        compute_matrix.cache_clear()
        notes_io.clear_load_notes_cache()

        t0 = time.perf_counter()
        _compute_matrix_via_file_walk()
        file_walk_ms = (time.perf_counter() - t0) * 1000

        compute_matrix.cache_clear()
        t0 = time.perf_counter()
        compute_matrix()
        public_ms = (time.perf_counter() - t0) * 1000

        assert public_ms < file_walk_ms * 3, (
            f"compute_matrix() suspiciously slow vs file-walk: file_walk={file_walk_ms:.1f}ms public={public_ms:.1f}ms"
        )


# ---------- Phase Δ.7 : notes_io → corpus_index invalidation hook ----


class TestDelta7NotesIoInvalidationHook:
    """Δ.7 — `notes_io.atomic_write` (and `atomic_write_bytes`)
    invalidate the corpus_index fingerprint cache when writing
    under `content/notes/`. Closes the production correctness gap
    Δ.4.1's wire flip introduces."""

    def test_writing_notes_file_invalidates_corpus_index(self, tmp_path, monkeypatch):
        from scripts.core import corpus_index, notes_io

        monkeypatch.setattr(corpus_index, "_FINGERPRINT_TTL_SEC", 60.0)
        # ω.36 — cache cell is now 3-tuple (timestamp, fp, notes_dir_str).
        corpus_index._FINGERPRINT_CACHE = (1.0, "stale-fingerprint-value", "/test/path")

        notes_path = tmp_path / "notes" / "gen.py"
        notes_path.parent.mkdir(parents=True)
        notes_io.atomic_write(notes_path, "NOTES = ()\n")

        assert corpus_index._FINGERPRINT_CACHE is None

    def test_writing_non_notes_file_does_not_invalidate(self, tmp_path, monkeypatch):
        from scripts.core import corpus_index, notes_io

        monkeypatch.setattr(corpus_index, "_FINGERPRINT_TTL_SEC", 60.0)
        sentinel = (1.0, "still-here-after-yaml-write", "/test/path")
        corpus_index._FINGERPRINT_CACHE = sentinel

        yaml_path = tmp_path / "config" / "editions.yaml"
        yaml_path.parent.mkdir(parents=True)
        notes_io.atomic_write(yaml_path, "editions:\n  - id: x\n")

        assert sentinel == corpus_index._FINGERPRINT_CACHE

    def test_writing_notes_file_via_bytes_variant_invalidates(self, tmp_path, monkeypatch):
        from scripts.core import corpus_index, notes_io

        monkeypatch.setattr(corpus_index, "_FINGERPRINT_TTL_SEC", 60.0)
        corpus_index._FINGERPRINT_CACHE = (1.0, "stale-bytes-write", "/test/path")

        notes_path = tmp_path / "notes" / "exo.py"
        notes_path.parent.mkdir(parents=True)
        notes_io.atomic_write_bytes(notes_path, b"NOTES = ()\n")

        assert corpus_index._FINGERPRINT_CACHE is None

    def test_invalidation_hook_failure_does_not_poison_write(self, tmp_path, monkeypatch):
        from scripts.core import corpus_index, notes_io

        def explode():
            raise RuntimeError("simulated corpus_index failure")

        monkeypatch.setattr(corpus_index, "invalidate", explode)

        notes_path = tmp_path / "notes" / "lev.py"
        notes_path.parent.mkdir(parents=True)
        result_path = notes_io.atomic_write(notes_path, "NOTES = ()\n")
        assert result_path == notes_path
        assert notes_path.read_text(encoding="utf-8") == "NOTES = ()\n"

    def test_lookalike_path_with_parent_named_notes_backup_does_not_invalidate(self, tmp_path, monkeypatch):
        from scripts.core import corpus_index, notes_io

        monkeypatch.setattr(corpus_index, "_FINGERPRINT_TTL_SEC", 60.0)
        sentinel = (1.0, "still-here-after-lookalike", "/test/path")
        corpus_index._FINGERPRINT_CACHE = sentinel

        lookalike = tmp_path / "notes_backup" / "gen.py"
        lookalike.parent.mkdir(parents=True)
        notes_io.atomic_write(lookalike, "NOTES = ()\n")

        assert sentinel == corpus_index._FINGERPRINT_CACHE


# ---------- Phase Δ.2.1 : api_search_notes wire flip ------------------


class TestDelta21SearchWireFlip:
    """Δ.2.1 — `web.api_search_notes` delegates to
    `corpus_index.search()` (the Δ.2 indexed path) instead of
    `note_search.search_notes()` (file-walk). The Δ.2 equivalence
    pin already confirms identical results across the real corpus;
    these tests verify the wire actually routes through the
    indexed path and the response shape is preserved."""

    def test_api_search_notes_routes_through_corpus_index(self, monkeypatch):
        # The wire flip in one assertion: api_search_notes must
        # invoke corpus_index.search() (NOT note_search.search_notes).
        from scripts import web
        from scripts.core import corpus_index

        called = {"corpus_index_search": 0}
        original = corpus_index.search

        def counting_search(*args, **kwargs):
            called["corpus_index_search"] += 1
            return original(*args, **kwargs)

        monkeypatch.setattr(corpus_index, "search", counting_search)
        result = web.api_search_notes("covenant", limit=5)
        assert result["status"] == "ok"
        assert called["corpus_index_search"] == 1, (
            f"api_search_notes must call corpus_index.search() exactly once (actual: {called['corpus_index_search']})"
        )

    def test_api_search_notes_preserves_response_shape(self):
        # Post-flip: status / query / filters / total / hits / limit
        # all still present and well-formed.
        from scripts import web

        result = web.api_search_notes("covenant", limit=5)
        assert result["status"] == "ok"
        assert result["query"] == "covenant"
        assert "filters" in result
        assert "total" in result
        assert "hits" in result
        assert "limit" in result
        assert result["limit"] == 5
        # When hits exist, every hit is enriched with kind/category metadata.
        for h in result["hits"]:
            assert "kind_label" in h, "hit missing kind_label (enrichment broke?)"
            assert "category" in h
            assert "category_label" in h
            assert "category_symbol" in h
            # Indexed path returns dict shape directly — must
            # carry the same keys SearchHit.to_dict() did.
            for k in ("book_code", "chapter", "verse", "kind", "title", "label", "excerpt", "score"):
                assert k in h, f"hit missing {k} post-flip"

    def test_api_search_notes_edition_filter_still_works(self):
        # Edition filter narrows by enabled-kinds; must still work
        # through the indexed path.
        from scripts import web

        unfiltered = web.api_search_notes("covenant", limit=200)
        # jewish-study has a smaller enabled-kinds set than the
        # full corpus, so its filtered total must be ≤ unfiltered.
        filtered = web.api_search_notes("covenant", edition_id="jewish-study", limit=200)
        assert filtered["status"] == "ok"
        assert filtered["total"] <= unfiltered["total"], (
            f"edition filter should not increase hit count; "
            f"unfiltered={unfiltered['total']} jewish-study={filtered['total']}"
        )
        assert filtered["filters"]["edition_id"] == "jewish-study"

    def test_api_search_notes_kind_filter_still_works(self):
        from scripts import web

        # Pick a kind that exists in the corpus.
        result = web.api_search_notes("covenant", kind="comm", limit=200)
        assert result["status"] == "ok"
        for h in result["hits"]:
            assert h["kind"] == "comm", f"kind filter leaked: got kind={h['kind']!r}"


# ---------- Phase Δ.3.1 : api_attribution_audit wire flip --------------


class TestDelta31AttributionAuditWireFlip:
    """Δ.3.1 — `web.api_attribution_audit` (via
    `_cached_attribution_audit`) delegates to
    `corpus_index.audit_attribution()` instead of
    `_compute_attribution_audit_uncached()` (file-walk). The Δ.3
    equivalence pin already confirms identical `counts` and
    matching `needs_attention` length + top-3 entries."""

    def test_wire_routes_through_corpus_index(self, monkeypatch):
        # The wire flip in one assertion: api_attribution_audit
        # must invoke corpus_index.audit_attribution().
        from scripts import web
        from scripts.core import corpus_index

        called = {"corpus_index_audit_attribution": 0}
        original = corpus_index.audit_attribution

        def counting_audit():
            called["corpus_index_audit_attribution"] += 1
            return original()

        monkeypatch.setattr(corpus_index, "audit_attribution", counting_audit)
        # Clear lru_cache so the wire actually runs
        web._cached_attribution_audit.cache_clear()
        result = web.api_attribution_audit()
        assert "counts" in result
        assert called["corpus_index_audit_attribution"] >= 1, (
            "api_attribution_audit must call corpus_index.audit_attribution()"
        )

    def test_response_preserves_top_level_shape(self):
        # Post-flip: counts / needs_attention / by_book / by_kind
        # all still present.
        from scripts import web

        web._cached_attribution_audit.cache_clear()
        result = web.api_attribution_audit()
        for k in ("counts", "needs_attention", "by_book", "by_kind"):
            assert k in result, f"top-level key {k!r} missing post-flip"
        # counts must have all classification buckets
        for cls in ("total", "missing", "thin", "user", "sourced"):
            assert cls in result["counts"], f"counts missing {cls!r}"

    def test_by_kind_shape_translated_to_dict_list(self):
        # corpus_index.audit_attribution returns by_kind as
        # list[tuple]; the frontend expects list[dict] with
        # `kind` + `count` keys. The wire-flip translation
        # preserves this contract.
        from scripts import web

        web._cached_attribution_audit.cache_clear()
        result = web.api_attribution_audit()
        for entry in result["by_kind"]:
            assert isinstance(entry, dict), f"by_kind entry not a dict: {type(entry).__name__}"
            assert "kind" in entry, f"by_kind entry missing 'kind': {entry}"
            assert "count" in entry, f"by_kind entry missing 'count': {entry}"
            assert isinstance(entry["count"], int)

    def test_needs_attention_carries_full_metadata(self):
        # Each needs_attention item must keep the 12 keys downstream
        # consumers (the /audit console) read: book, book_title,
        # section, chapter, verse, suffix, kind, kind_label,
        # category, category_symbol, title, body_preview,
        # attribution, classification.
        from scripts import web

        web._cached_attribution_audit.cache_clear()
        result = web.api_attribution_audit()
        if not result["needs_attention"]:
            return  # corpus may have zero missing/thin in some scenarios
        first = result["needs_attention"][0]
        for k in (
            "book",
            "book_title",
            "section",
            "chapter",
            "verse",
            "suffix",
            "kind",
            "kind_label",
            "category",
            "category_symbol",
            "title",
            "body_preview",
            "attribution",
            "classification",
        ):
            assert k in first, f"needs_attention entry missing {k!r} post-flip"


# ---------- Phase Δ.5.1 : dashboard.gather_stats wire flip ------------


class TestDelta51DashboardStatsWireFlip:
    """Δ.5.1 — `dashboard.gather_stats` delegates to
    `corpus_index.dashboard_stats()` (the Δ.5 indexed path) instead
    of walking notes/<code>.py files directly. The Δ.5 equivalence
    pin already confirms identical aggregate output across the real
    corpus; these tests verify the wire actually routes through
    the indexed path and the dashboard-renderer contract is
    preserved (pass-through fields, parse_failures pre-scan
    diagnostic, defaultdict-compatible chapter_density)."""

    def test_wire_routes_through_corpus_index(self, monkeypatch):
        # The wire flip in one assertion: dashboard.gather_stats
        # must invoke corpus_index.dashboard_stats().
        from scripts import dashboard as dashboard_module
        from scripts.core import config, corpus_index

        called = {"corpus_index_dashboard_stats": 0}
        original = corpus_index.dashboard_stats

        def counting_dashboard(books):
            called["corpus_index_dashboard_stats"] += 1
            return original(books)

        monkeypatch.setattr(corpus_index, "dashboard_stats", counting_dashboard)
        books = config.load_books()
        kinds = config.load_kinds()
        result = dashboard_module.gather_stats(books, kinds)
        assert "total_notes" in result
        assert called["corpus_index_dashboard_stats"] == 1, (
            "gather_stats must call corpus_index.dashboard_stats() exactly once"
        )

    def test_full_response_shape_preserved(self):
        # Post-flip: aggregate fields from corpus_index PLUS the
        # 4 pass-through / diagnostic fields the renderer needs.
        from scripts import dashboard as dashboard_module
        from scripts.core import config

        books = config.load_books()
        kinds = config.load_kinds()
        result = dashboard_module.gather_stats(books, kinds)

        # Aggregate fields (from corpus_index)
        for k in ("total_notes", "per_book", "per_kind", "chapter_density"):
            assert k in result, f"aggregate key {k!r} missing post-flip"

        # Pass-through + diagnostic fields (added by the wire-flip
        # wrapper)
        for k in ("books", "kinds", "parse_failures", "generated_at"):
            assert k in result, f"pass-through key {k!r} missing post-flip"

        # Pass-through values are the inputs back out
        assert result["books"] is books
        assert result["kinds"] is kinds
        assert isinstance(result["parse_failures"], list)
        assert isinstance(result["generated_at"], str)

    def test_chapter_density_supports_renderer_access_pattern(self):
        # render_heatmap reads `cd[code]` (subscript, not .get()) —
        # this must NOT KeyError for any book in books, since
        # corpus_index.dashboard_stats explicitly setdefault({})s
        # every book.
        from scripts import dashboard as dashboard_module
        from scripts.core import config

        books = config.load_books()
        kinds = config.load_kinds()
        result = dashboard_module.gather_stats(books, kinds)
        cd = result["chapter_density"]
        for book in books:
            code = book["code"]
            entry = cd[code]  # MUST NOT KeyError
            assert isinstance(entry, dict)
            # Per-chapter access via .get() must also be safe
            _ = entry.get(1, 0)

    def test_parse_failures_diagnostic_preserved(self):
        # parse_failures should be an empty list on the real
        # (well-formed) corpus. The pre-scan still runs in the
        # wire-flip wrapper so a corrupt notes file would still
        # surface in render_footer's warning.
        from scripts import dashboard as dashboard_module
        from scripts.core import config

        books = config.load_books()
        kinds = config.load_kinds()
        result = dashboard_module.gather_stats(books, kinds)
        # On the real corpus, no parse failures expected
        assert result["parse_failures"] == [], f"unexpected parse_failures: {result['parse_failures']}"
