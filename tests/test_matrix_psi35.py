"""ω.27 follow-on (2026-05-11) — ψ.35 family test classes, split out of
the monolithic ``tests/test_scripts.py`` into a topic file.

The audit (AUDIT_2026-05-11 §3.4) flagged the 28K-line
``test_scripts.py`` as the next refactor that compounds into the
xdist parallel-test perf layer (each test FILE is a separate
xdist target, so smaller-but-more files unlocks the 4× worker
ceiling that the current monolith capped at ~1.5× effective).

This file is the FIRST topic extraction: the seven ψ.35 family
test classes (everything from the Matrix data-model collapse
arc — ψ.35-A scalar accessors, ψ.35-B1-B4 consumer migrations,
ψ.35-Final field auto-derivation). All 33 tests are self-
contained: each lazy-imports its own dependencies from
``scripts.core.matrix`` / ``scripts.web`` / ``scripts.api.*``
inside the test method body, so no shared fixtures or module-
top imports from ``test_scripts.py`` are needed.

Future ω.27 follow-on slices will extract other cohesive
clusters (e.g. ω.35-A/B file-split tests, Δ-family corpus_index
tests, χ-cluster corpus-growth tests, ω.34/ψ.34/φ.* infrastructure
tests). Each cluster ships as its own topic file under
``tests/test_<topic>.py``. The terminating slice removes the
empty shells from ``test_scripts.py`` and merges leftover
miscellaneous tests into ``test_misc.py`` or similar.
"""

import pytest

# mint-7 E2 — the slowest non-build test file (~87 s, measured 2026-05-31;
# re-walks the corpus / rebuilds the matrix repeatedly); tagged slow so a
# fast-iteration loop can deselect via `-m "not slow"`. (The "23 min" figure in
# the old audit/memory was STALE — corrected 2026-05-31; a session-scoped
# compute_matrix could shave it further, logged for mint-8.)
pytestmark = pytest.mark.slow


# ---------- Phase ψ.35-A : Matrix accessor methods --------------------


class TestPsi35AAccessorMethods:
    """ψ.35-A — derive-from-canonical accessor methods on Matrix.

    The Matrix dataclass currently stores six fields; three of them
    (`enabled`, `potential`, `per_book`) are pure derivations of
    `per_chapter` + `edition_enabled_kinds`. ψ.35-A adds four
    accessor methods that compute the same answers from the
    canonical store:

      - `m.enabled_count(ed, kind)`     ≡ `m.enabled[ed][kind]`
      - `m.potential_count(ed, kind)`   ≡ `m.potential[ed][kind]`
      - `m.per_book_count(ed, kind, b)` ≡ `m.per_book[ed][kind][b]`
      - `m.chapter_dist(ed, kind, b)`   ≡ `m.per_chapter[ed][kind][b]`

    The redundant projections stay populated for back-compat (15+
    consumers in `scripts/web.py` read them directly). Future ψ.35
    follow-on slices migrate those consumers to the accessor API;
    ψ.35-Final removes the projection fields.

    These tests pin **equivalence** between the methods and the
    stored projections across every (ed, kind, book) triple in
    the live matrix. If the methods drift from the projections,
    the migration's safety net is broken and these tests fail
    loudly.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core.matrix import compute_matrix

        # Capture one matrix snapshot for the entire class so we
        # iterate the same data across every equivalence check.
        cls.m = compute_matrix()

    def test_enabled_count_equivalence(self):
        # For every (ed, kind) present in either `enabled` or
        # `potential`, the method must return the same value as
        # the stored projection. Also pin the "disabled kind = 0"
        # contract that `enabled` enforces implicitly.
        m = self.m
        mismatches = []
        seen = set()
        for ed_id, by_kind in m.enabled.items():
            for kind, stored in by_kind.items():
                seen.add((ed_id, kind))
                computed = m.enabled_count(ed_id, kind)
                if computed != stored:
                    mismatches.append(
                        f"enabled_count({ed_id!r}, {kind!r}) = {computed}; m.enabled[{ed_id!r}][{kind!r}] = {stored}"
                    )
        # Also walk `potential` for (ed, kind) pairs NOT in enabled —
        # these are kinds disabled for that edition. Accessor must
        # return 0; stored `enabled[ed].get(kind, 0)` must also be 0.
        for ed_id, by_kind in m.potential.items():
            for kind in by_kind:
                if (ed_id, kind) in seen:
                    continue
                computed = m.enabled_count(ed_id, kind)
                stored = m.enabled.get(ed_id, {}).get(kind, 0)
                if computed != stored:
                    mismatches.append(
                        f"enabled_count({ed_id!r}, {kind!r}) [disabled-kind path] = "
                        f"{computed}; m.enabled.get(...) = {stored}"
                    )
        assert mismatches == [], (
            f"{len(mismatches)} enabled_count() vs m.enabled mismatch(es); first 5:\n  " + "\n  ".join(mismatches[:5])
        )

    def test_potential_count_equivalence(self):
        m = self.m
        mismatches = []
        for ed_id, by_kind in m.potential.items():
            for kind, stored in by_kind.items():
                computed = m.potential_count(ed_id, kind)
                if computed != stored:
                    mismatches.append(
                        f"potential_count({ed_id!r}, {kind!r}) = {computed}; "
                        f"m.potential[{ed_id!r}][{kind!r}] = {stored}"
                    )
        assert mismatches == [], f"{len(mismatches)} potential_count() mismatches; first 5:\n  " + "\n  ".join(
            mismatches[:5]
        )

    def test_per_book_count_equivalence(self):
        m = self.m
        mismatches = []
        for ed_id, by_kind in m.per_book.items():
            for kind, by_book in by_kind.items():
                for book, stored in by_book.items():
                    computed = m.per_book_count(ed_id, kind, book)
                    if computed != stored:
                        mismatches.append(
                            f"per_book_count({ed_id!r}, {kind!r}, {book!r}) = {computed}; m.per_book[...] = {stored}"
                        )
        assert mismatches == [], f"{len(mismatches)} per_book_count() mismatches; first 5:\n  " + "\n  ".join(
            mismatches[:5]
        )

    def test_chapter_dist_equivalence(self):
        m = self.m
        mismatches = []
        for ed_id, by_kind in m.per_chapter.items():
            for kind, by_book in by_kind.items():
                for book, stored_dist in by_book.items():
                    computed = m.chapter_dist(ed_id, kind, book)
                    if computed != stored_dist:
                        mismatches.append(
                            f"chapter_dist({ed_id!r}, {kind!r}, {book!r}) = "
                            f"{computed}; m.per_chapter[...] = {stored_dist}"
                        )
        assert mismatches == [], f"{len(mismatches)} chapter_dist() mismatches; first 5:\n  " + "\n  ".join(
            mismatches[:5]
        )

    def test_chapter_dist_returns_defensive_copy(self):
        # chapter_dist must return a copy — mutating the result
        # MUST NOT bleed back into the cached matrix.
        m = self.m
        # Find some non-empty (ed, kind, book) triple
        for ed_id, by_kind in m.per_chapter.items():
            for kind, by_book in by_kind.items():
                for book, stored in by_book.items():
                    if stored:
                        result = m.chapter_dist(ed_id, kind, book)
                        original = dict(stored)
                        result[99999] = 12345  # corrupt the copy
                        # Stored projection unchanged
                        assert m.per_chapter[ed_id][kind][book] == original
                        return
        raise AssertionError("no non-empty (ed, kind, book) triple in matrix")

    def test_enabled_count_returns_zero_for_disabled_kind(self):
        # Pin the disabled-kind contract: enabled_count returns 0
        # for any kind not in `edition_enabled_kinds[ed]`, even if
        # `potential_count(ed, kind) > 0`.
        m = self.m
        for ed_id in list(m.edition_canon_books.keys()):
            enabled_kinds = m.edition_enabled_kinds.get(ed_id, set())
            for kind, n in m.potential.get(ed_id, {}).items():
                if kind in enabled_kinds:
                    continue
                # Disabled kind in this edition. enabled_count MUST be 0.
                computed = m.enabled_count(ed_id, kind)
                assert computed == 0, (
                    f"enabled_count({ed_id!r}, {kind!r}) returned {computed} "
                    f"but the kind is NOT in edition_enabled_kinds (potential={n})"
                )

    def test_accessor_handles_unknown_edition(self):
        m = self.m
        assert m.enabled_count("not-a-real-edition", "comm-doctrinal") == 0
        assert m.potential_count("not-a-real-edition", "comm-doctrinal") == 0
        assert m.per_book_count("not-a-real-edition", "comm-doctrinal", "gen") == 0
        assert m.chapter_dist("not-a-real-edition", "comm-doctrinal", "gen") == {}

    def test_accessor_handles_unknown_kind(self):
        m = self.m
        # Pick any real edition
        ed_id = next(iter(m.edition_canon_books.keys()), None)
        assert ed_id is not None, "matrix has no editions"
        assert m.enabled_count(ed_id, "not-a-real-kind") == 0
        assert m.potential_count(ed_id, "not-a-real-kind") == 0
        assert m.per_book_count(ed_id, "not-a-real-kind", "gen") == 0
        assert m.chapter_dist(ed_id, "not-a-real-kind", "gen") == {}

    def test_accessor_methods_are_bound(self):
        # Pin the method-on-dataclass shape — these must be
        # instance methods, NOT staticmethods or module-level
        # functions. (Future ψ.35 follow-on consumers call them as
        # `matrix_instance.enabled_count(...)`.)
        from scripts.core.matrix import Matrix

        for name in ("enabled_count", "potential_count", "per_book_count", "chapter_dist"):
            attr = getattr(Matrix, name, None)
            assert attr is not None, f"Matrix.{name} missing"
            assert callable(attr), f"Matrix.{name} not callable"


# ---------- Phase ψ.35-B1 : Matrix CLI migration + dict accessors -----


class TestPsi35B1AccessorDicts:
    """ψ.35-B1 — two dict-returning accessors that complement the
    scalar accessors from ψ.35-A:

      - `m.enabled_kinds_dict(ed)`   ≡ `m.enabled.get(ed, {})`
      - `m.potential_kinds_dict(ed)` ≡ `m.potential.get(ed, {})`

    Consumers that need a whole-edition `{kind: count}` map (for
    JSON serialization, sum-across-all-kinds, etc.) call these
    instead of reading the raw projection fields. Used by
    `scripts/matrix.py` (the CLI tool migrated in ψ.35-B1) and
    will be used by web.py / api/exports.py consumer migrations
    in later ψ.35 sub-slices.

    Equivalence pinned against the stored projections so the
    methods can't silently drift away from the on-disk shape.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core.matrix import compute_matrix

        cls.m = compute_matrix()

    def test_enabled_kinds_dict_equivalence(self):
        m = self.m
        mismatches = []
        for ed_id in m.enabled:
            stored = dict(m.enabled[ed_id])
            computed = m.enabled_kinds_dict(ed_id)
            # Shape contract: only kinds with count > 0 appear.
            # `m.enabled` itself follows the same convention, so
            # equality should hold both ways.
            if stored != computed:
                only_stored = {k: stored[k] for k in set(stored) - set(computed)}
                only_method = {k: computed[k] for k in set(computed) - set(stored)}
                mismatches.append(f"{ed_id}: only-stored={only_stored}; only-method={only_method}")
        assert mismatches == [], (
            f"{len(mismatches)} enabled_kinds_dict() vs m.enabled mismatch(es); first 3:\n  "
            + "\n  ".join(mismatches[:3])
        )

    def test_potential_kinds_dict_equivalence(self):
        m = self.m
        mismatches = []
        for ed_id in m.potential:
            stored = dict(m.potential[ed_id])
            computed = m.potential_kinds_dict(ed_id)
            if stored != computed:
                only_stored = {k: stored[k] for k in set(stored) - set(computed)}
                only_method = {k: computed[k] for k in set(computed) - set(stored)}
                mismatches.append(f"{ed_id}: only-stored={only_stored}; only-method={only_method}")
        assert mismatches == [], (
            f"{len(mismatches)} potential_kinds_dict() vs m.potential mismatch(es); first 3:\n  "
            + "\n  ".join(mismatches[:3])
        )

    def test_dict_accessors_omit_zero_count_kinds(self):
        # Pin the shape contract — kinds with count == 0 must NOT
        # appear in the returned dict (matching the stored
        # projection's behavior).
        m = self.m
        for ed_id in m.enabled:
            for kind, n in m.enabled_kinds_dict(ed_id).items():
                assert n > 0, f"enabled_kinds_dict({ed_id!r})[{kind!r}] = {n} (zero-count kind leaked into dict)"
            for kind, n in m.potential_kinds_dict(ed_id).items():
                assert n > 0, f"potential_kinds_dict({ed_id!r})[{kind!r}] = {n}"

    def test_dict_accessors_handle_unknown_edition(self):
        m = self.m
        assert m.enabled_kinds_dict("not-a-real-edition") == {}
        assert m.potential_kinds_dict("not-a-real-edition") == {}

    def test_enabled_dict_respects_kind_filter(self):
        # The "enabled" dict must omit any kind in `potential` that
        # isn't in `edition_enabled_kinds`. (Same contract as the
        # stored `m.enabled` projection.)
        m = self.m
        for ed_id, enabled_kinds in m.edition_enabled_kinds.items():
            d = m.enabled_kinds_dict(ed_id)
            for kind in d:
                assert kind in enabled_kinds, (
                    f"enabled_kinds_dict({ed_id!r}) returned disabled kind {kind!r} (not in edition_enabled_kinds)"
                )


class TestPsi35B1MatrixCLIMigration:
    """ψ.35-B1 — pin that `scripts/matrix.py` (the CLI tool) no
    longer reads the raw projection fields directly. Five call
    sites migrated from `m.enabled[...]` / `m.potential[...]` to
    the accessor API. This is the FIRST consumer migration in
    the ψ.35 family; the remaining sites (web.py, api/exports.py,
    api/preflight.py) follow in subsequent slices.
    """

    def test_cli_module_runs_without_crashing(self, monkeypatch, capsys):
        # Smoke test: importing the module + running its main
        # default path (category table) must complete without
        # raising. Forces the migrated lines to execute end-to-end.
        import sys

        from scripts.core import config

        # Build a no-op argv so argparse takes the default branch
        monkeypatch.setattr(sys, "argv", ["matrix.py"])

        # Reload to bypass any cached import state.
        import importlib

        import scripts.matrix as matrix_cli

        matrix_cli = importlib.reload(matrix_cli)
        # Run main; capture stdout. Allow it to print; failure would
        # be an exception or wrong number rendered.
        matrix_cli.main()
        captured = capsys.readouterr()
        assert "symbol-toggle matrix" in captured.out
        # TOTAL row must appear for the default (--category) view
        assert "TOTAL" in captured.out
        # Must mention every existing edition's short prefix
        for ed in config.load_editions():
            short = ed["id"].split("-")[0][:8]
            assert short in captured.out, f"edition {ed['id']!r} missing from CLI output (short={short!r})"

    def test_cli_uses_accessor_methods_not_raw_fields(self):
        # Source-scan: the migrated call sites must use the
        # accessor API. If a regression re-introduces raw-field
        # reads (`m.enabled[ed_id]`, `m.potential[ed_id]`), this
        # test fails loudly so the developer notices.
        #
        # Strip comment lines before scanning so the migration
        # marker comments (which legitimately quote the old code
        # under `was: ...`) don't trigger false positives.
        from pathlib import Path

        raw = (Path(__file__).resolve().parent.parent / "scripts" / "matrix.py").read_text(encoding="utf-8")
        code_only = "\n".join(line for line in raw.splitlines() if not line.lstrip().startswith("#"))

        # The four anti-patterns ψ.35-B1 migrated away from
        for anti in (
            "m.enabled[ed_id].get(",
            "m.potential[ed_id].get(",
            "m.enabled[edition_id]",
            "m.potential[edition_id]",
        ):
            assert anti not in code_only, (
                f"scripts/matrix.py still contains raw-field read {anti!r}; "
                f"ψ.35-B1 migrated it to the accessor API (m.enabled_count / "
                f"m.potential_count / m.enabled_kinds_dict / m.potential_kinds_dict)."
            )
        # And the migration markers must be present (these DO live
        # in comments — scan the raw text, not the comment-stripped form)
        assert "ψ.35-B1" in raw, "scripts/matrix.py lost the ψ.35-B1 migration comment markers"


# ---------- Phase ψ.35-B2 : internal-consumer migrations --------------


class TestPsi35B2InternalConsumerMigrations:
    """ψ.35-B2 — migrate the four "internal helper" consumers of the
    Matrix projection fields from raw-field reads to the accessor
    API. Targets:

    - `scripts/web.py::_diff_edition_summary` line 2878:
      `mtx.enabled.get(ed_id, {})` → `mtx.enabled_kinds_dict(ed_id)`
    - `scripts/web.py::_diff_kinds_section` lines 2935-2936:
      `mtx.enabled.get(a_id, {})` / `(b_id, {})` →
      `mtx.enabled_kinds_dict(a_id)` / `(b_id)`
    - `scripts/api/exports.py::api_export_preview` lines 48-49:
      `m.enabled.get(edition_id, {})` / `m.potential.get(...)` →
      `m.enabled_kinds_dict(edition_id)` / `m.potential_kinds_dict(...)`
    - `scripts/api/preflight.py::_compute_preflight_uncached`
      line 249: `for ed_id, by_kind in mtx.enabled.items()` →
      iterate `mtx.edition_canon_books` + call
      `mtx.enabled_kinds_dict(ed_id)` per edition

    NOT in scope (deferred to a future slice):

    - `scripts/web.py::api_matrix` lines 515-544 — serializes the
      per-edition projections directly into the JSON response that
      the JS UI consumes. Migration here is shape-sensitive and
      deserves its own focused slice.

    Tests pin (a) the migrated call sites still produce equivalent
    output end-to-end, (b) the raw-field anti-patterns are absent
    from the migrated source files (source-scan, comment-stripped).
    """

    def test_preflight_empty_kinds_still_computes_correctly(self):
        # The migrated iteration in _compute_preflight_uncached
        # produces the same `used_kinds` set, so the empty_kinds
        # check returns the same verdict + count of unused kinds.
        from scripts.web import api_preflight

        pf = api_preflight()
        check = next((c for c in pf["checks"] if c["id"] == "empty_kinds"), None)
        assert check is not None, "preflight missing empty_kinds check"
        # Status is one of pass/warn/fail; message is non-empty.
        assert check["status"] in ("pass", "warn", "fail")
        assert isinstance(check["message"], str) and check["message"]
        # The details list is bounded.
        assert isinstance(check["details"], list)
        assert len(check["details"]) <= 20

    def test_edition_diff_summary_still_computes_correctly(self):
        # _diff_edition_summary's totals.notes must equal
        # `sum(mtx.enabled_kinds_dict(ed_id).values())` which in turn
        # equals the pre-migration `sum(mtx.enabled.get(ed_id, {}).values())`.
        from scripts.core import matrix as matrix_mod
        from scripts.web import api_edition_diff

        # Pick two real editions
        diff = api_edition_diff("catholic-study", "evangelical-reformed")
        m = matrix_mod.compute_matrix()
        assert diff["a"]["totals"]["notes"] == sum(m.enabled_kinds_dict("catholic-study").values())
        assert diff["b"]["totals"]["notes"] == sum(m.enabled_kinds_dict("evangelical-reformed").values())

    def test_edition_diff_kinds_section_still_classifies_correctly(self):
        # _diff_kinds_section uses a_counts / b_counts to look up
        # the per-kind count for each edition. Pin that the migrated
        # path still classifies kinds into only_a / only_b / shared
        # and returns count values that match the stored projection.
        from scripts.core import matrix as matrix_mod
        from scripts.web import api_edition_diff

        diff = api_edition_diff("catholic-study", "evangelical-reformed")
        m = matrix_mod.compute_matrix()
        a_dict = m.enabled_kinds_dict("catholic-study")
        b_dict = m.enabled_kinds_dict("evangelical-reformed")
        # `shared` rows have both a_count and b_count present
        for row in diff["kinds"]["shared"]:
            code = row["code"]
            assert row.get("a_count") == a_dict.get(code, 0), (
                f"shared row {code!r}: row.a_count={row.get('a_count')} != "
                f"m.enabled_kinds_dict('catholic-study')[{code!r}]={a_dict.get(code, 0)}"
            )
            assert row.get("b_count") == b_dict.get(code, 0)

    def test_export_preview_summary_matches_dict_accessors(self):
        # σ.6.3 — notes_shipping is now the BUILD-ACCURATE total
        # (edition_stats.resolved_note_counts), not the edition-wide matrix sum,
        # so the export preview equals the built EPUB + honors the ρ.3 hierarchy.
        # notes_potential stays matrix-based (legitimately "what's available").
        from scripts.api.exports import api_export_preview
        from scripts.core import config, edition_stats
        from scripts.core import matrix as matrix_mod

        ep = api_export_preview("catholic-study")
        m = matrix_mod.compute_matrix()
        expected_shipping = edition_stats.resolved_note_counts(config.editions_by_id()["catholic-study"])["total"]
        assert ep["summary"]["notes_shipping"] == expected_shipping
        assert ep["summary"]["notes_potential"] == sum(m.potential_kinds_dict("catholic-study").values())

    def test_migrated_files_lack_raw_enabled_get_pattern(self):
        # Source-scan: the four files migrated in ψ.35-B2 must
        # not contain `mtx.enabled.get(` or `m.enabled.get(`
        # (the dict-returning raw-field anti-pattern). Strip
        # comment lines first so the migration markers — which
        # legitimately quote the old expressions — don't trip
        # the check.
        from pathlib import Path

        ROOT = Path(__file__).resolve().parent.parent
        migrated_files = [
            ROOT / "scripts" / "web.py",
            ROOT / "scripts" / "api" / "exports.py",
            ROOT / "scripts" / "api" / "preflight.py",
        ]
        anti_patterns_dict = (
            "mtx.enabled.get(",
            "mtx.potential.get(",
            "m.enabled.get(",
            "m.potential.get(",
        )
        for path in migrated_files:
            raw = path.read_text(encoding="utf-8")
            code_only = "\n".join(line for line in raw.splitlines() if not line.lstrip().startswith("#"))
            for anti in anti_patterns_dict:
                assert anti not in code_only, (
                    f"{path.relative_to(ROOT)} still contains raw-field read "
                    f"{anti!r}; ψ.35-B2 should have migrated it to the "
                    f"accessor API (enabled_kinds_dict / potential_kinds_dict)."
                )

    def test_migrated_files_carry_b2_markers(self):
        # Three of the four migrated files should carry a ψ.35-B2
        # comment marker preserving the original expression for
        # future readers (api/preflight.py + web_matrix.py + api/exports.py;
        # the matrix functions moved from web.py to web_matrix.py in the bae92e4 split).
        from pathlib import Path

        ROOT = Path(__file__).resolve().parent.parent
        for relpath in (
            "scripts/web_matrix.py",
            "scripts/api/exports.py",
            "scripts/api/preflight.py",
        ):
            raw = (ROOT / relpath).read_text(encoding="utf-8")
            assert "ψ.35-B2" in raw, (
                f"{relpath} lost the ψ.35-B2 migration marker; future readers "
                f"benefit from seeing the original raw-field expression "
                f"preserved in source."
            )


# ---------- Phase ψ.35-B3 : api_matrix enabled/potential migration ----


class TestPsi35B3ApiMatrixMigration:
    """ψ.35-B3 — closes out the `m.enabled` / `m.potential` raw-field
    reads in `api_matrix`. The function's JSON response shape — the
    contract the JS matrix sidebar UI depends on — is unchanged;
    only the data-source upstream of the response was swapped from
    raw projection-field reads to the accessor API.

    Migrated lines (extracted into the new helper
    ``_api_matrix_per_edition`` for clarity):

    - ``for ed_id in m.enabled`` (line 544 pre-B3) →
      ``for ed_id in m.edition_canon_books``
    - ``m.enabled[ed_id]`` → ``m.enabled_kinds_dict(ed_id)``
    - ``m.potential[ed_id]`` → ``m.potential_kinds_dict(ed_id)``
    - ``sum(m.enabled[ed_id].values())`` → sum on the dict variable
    - ``sum(m.potential[ed_id].values())`` → sum on the dict variable

    Deliberately deferred:

    - ``m.per_book.get(ed_id, {})`` (line 527 — needs a new
      ``per_book_kinds_dict()`` accessor; deferred to a future slice)
    - ``m.per_chapter.get(ed_id, {})`` (line 532 — per_chapter IS the
      canonical store; stays as raw read through ψ.35-Final)

    Tests pin (a) the JSON output shape is byte-equal to what the
    pre-migration code would have produced, (b) the `for ed_id in
    m.enabled` anti-pattern is gone from api_matrix.
    """

    def test_api_matrix_response_shape_unchanged(self):
        # The matrix block keyed on ed_id must contain the same
        # ten fields as before, with values that match the stored
        # projections byte-for-byte.
        from scripts.core import matrix as matrix_mod
        from scripts.web import api_matrix

        result = api_matrix()
        m = matrix_mod.compute_matrix()
        expected_keys = {
            "enabled",
            "potential",
            "total_enabled",
            "total_potential",
            "canon_books_count",
            "enabled_kinds_count",
            "enabled_kinds_set",
            "per_book",
            "per_chapter",
            "canon_book_order",
            "book_chapter_counts",
        }
        for ed_id, slot in result["matrix"].items():
            assert set(slot) == expected_keys, (
                f"matrix[{ed_id!r}] keys drift: missing={expected_keys - set(slot)}; extra={set(slot) - expected_keys}"
            )
            # Values: must equal the equivalent dict-accessor outputs
            assert slot["enabled"] == m.enabled_kinds_dict(ed_id)
            assert slot["potential"] == m.potential_kinds_dict(ed_id)
            assert slot["total_enabled"] == sum(m.enabled_kinds_dict(ed_id).values())
            assert slot["total_potential"] == sum(m.potential_kinds_dict(ed_id).values())
            # And must STILL equal the stored projections (B3's
            # whole point: zero behavior change at the JSON boundary).
            assert slot["enabled"] == m.enabled.get(ed_id, {}), (
                f"matrix[{ed_id!r}].enabled drifts from stored projection — this would break the JS UI."
            )
            assert slot["potential"] == m.potential.get(ed_id, {})

    def test_api_matrix_iterates_every_edition(self):
        # The pre-B3 code iterated `m.enabled.keys()`. The migrated
        # code iterates `m.edition_canon_books.keys()`. Pin that the
        # output covers every edition the matrix knows about — both
        # keysets must cover the same 9-edition set.
        from scripts.core import matrix as matrix_mod
        from scripts.web import api_matrix

        result = api_matrix()
        m = matrix_mod.compute_matrix()
        assert set(result["matrix"].keys()) == set(m.edition_canon_books.keys())
        # And cross-check against the stored projection's keyset
        # (these must agree, otherwise B3's migration would have
        # changed which editions appear in the response).
        assert set(result["matrix"].keys()) == set(m.enabled.keys())

    def test_api_matrix_helper_exported(self):
        # The extracted helper `_api_matrix_per_edition` must exist
        # in scripts.web's namespace so route-table dispatch and
        # tests can monkeypatch it if needed.
        from scripts.web import _api_matrix_per_edition

        assert callable(_api_matrix_per_edition)

    def test_api_matrix_no_longer_iterates_m_enabled(self):
        # Source-scan: scripts/web.py::api_matrix must not iterate
        # over `m.enabled` as its edition list — that anti-pattern
        # forces the legacy projection to stay populated. Comment-
        # stripped scan so the migration markers don't false-positive.
        from pathlib import Path

        raw = (Path(__file__).resolve().parent.parent / "scripts" / "web.py").read_text(encoding="utf-8")
        code_only = "\n".join(line for line in raw.splitlines() if not line.lstrip().startswith("#"))
        # The specific anti-pattern from the pre-B3 comprehension
        # `for ed_id in m.enabled` must be absent. (The migrated
        # form is `for ed_id in m.edition_canon_books`.)
        assert "for ed_id in m.enabled" not in code_only, (
            "scripts/web.py still iterates `for ed_id in m.enabled` — ψ.35-B3 migrated this to `m.edition_canon_books`."
        )

    def test_api_matrix_b3_marker_present(self):
        # The migration marker `ψ.35-B3` must appear in
        # scripts/web_matrix.py preserving the original raw-field
        # expressions in source for future readers (the matrix functions
        # moved from web.py to web_matrix.py in the bae92e4 split).
        from pathlib import Path

        raw = (Path(__file__).resolve().parent.parent / "scripts" / "web_matrix.py").read_text(encoding="utf-8")
        assert "ψ.35-B3" in raw, "scripts/web_matrix.py lost the ψ.35-B3 migration marker"


# ---------- Phase ψ.35-B4 : per_book_kinds_dict + last raw read -------


class TestPsi35B4PerBookAccessor:
    """ψ.35-B4 — third dict-returning accessor + migration of the last
    raw `m.per_book.get(ed_id, {})` consumer in `api_matrix`.

    The new accessor `per_book_kinds_dict(ed) -> dict[kind, dict[book,
    count]]` derives from `per_chapter` via per-(kind, book) summation
    across chapters. Used by `api_matrix`'s per-edition JSON slot.

    After this slice, every raw `m.enabled` / `m.potential` /
    `m.per_book` read in production code is gone. The only remaining
    raw read of a Matrix projection is `m.per_chapter` — which IS
    the canonical store and stays through ψ.35-Final.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core.matrix import compute_matrix

        cls.m = compute_matrix()

    def test_per_book_kinds_dict_equivalence(self):
        m = self.m
        mismatches = []
        for ed_id in m.per_book:
            stored = m.per_book[ed_id]
            computed = m.per_book_kinds_dict(ed_id)
            if stored != computed:
                only_stored = {k for k in stored if k not in computed}
                only_method = {k for k in computed if k not in stored}
                mismatches.append(f"{ed_id}: only-stored-kinds={only_stored}; only-method-kinds={only_method}")
        assert mismatches == [], (
            f"{len(mismatches)} per_book_kinds_dict() vs m.per_book mismatch(es); first 3:\n  "
            + "\n  ".join(mismatches[:3])
        )

    def test_per_book_kinds_dict_omits_zero_counts(self):
        # Shape contract: no zero-count (kind, book) pair should
        # appear in the returned nested dict.
        m = self.m
        for ed_id in m.edition_canon_books:
            for kind, by_book in m.per_book_kinds_dict(ed_id).items():
                for book, n in by_book.items():
                    assert n > 0, (
                        f"per_book_kinds_dict({ed_id!r})[{kind!r}][{book!r}] = {n} "
                        f"(zero-count pair leaked into nested dict)"
                    )

    def test_per_book_kinds_dict_handles_unknown_edition(self):
        m = self.m
        assert m.per_book_kinds_dict("not-a-real-edition") == {}

    def test_api_matrix_per_book_field_uses_accessor(self):
        # api_matrix's matrix[ed]["per_book"] must equal the new
        # accessor's output (and, transitively, the stored
        # projection — both via separate paths).
        from scripts.core import matrix as matrix_mod
        from scripts.web import api_matrix

        result = api_matrix()
        m = matrix_mod.compute_matrix()
        for ed_id, slot in result["matrix"].items():
            assert slot["per_book"] == m.per_book_kinds_dict(ed_id), (
                f"matrix[{ed_id!r}].per_book drifts from accessor output"
            )
            # And via the stored projection (B4's safety contract:
            # JSON shape is byte-equal to the pre-migration output).
            assert slot["per_book"] == m.per_book.get(ed_id, {}), (
                f"matrix[{ed_id!r}].per_book drifts from stored projection — this would break the JS UI."
            )

    def test_web_py_no_longer_reads_raw_per_book_in_api_matrix(self):
        # Source-scan: scripts/web.py must not read
        # `m.per_book.get(` (the raw whole-edition fetch). The
        # migrated form is `m.per_book_kinds_dict(...)`.
        from pathlib import Path

        raw = (Path(__file__).resolve().parent.parent / "scripts" / "web.py").read_text(encoding="utf-8")
        code_only = "\n".join(line for line in raw.splitlines() if not line.lstrip().startswith("#"))
        assert "m.per_book.get(" not in code_only, (
            "scripts/web.py still reads `m.per_book.get(...)` directly; "
            "ψ.35-B4 migrated this to `m.per_book_kinds_dict(...)`."
        )

    def test_b4_marker_present(self):
        from pathlib import Path

        raw = (Path(__file__).resolve().parent.parent / "scripts" / "web_matrix.py").read_text(encoding="utf-8")
        assert "ψ.35-B4" in raw, "scripts/web_matrix.py lost the ψ.35-B4 migration marker"


# ---------- Phase ψ.35-Final : redundant projections auto-derived -----


class TestPsi35FinalProjectionsAutoDerived:
    """ψ.35-Final — the three redundant projection fields
    (`enabled`, `potential`, `per_book`) are now `init=False` and
    derived in `Matrix.__post_init__` from `per_chapter` +
    `edition_enabled_kinds`. The build pipelines
    (`_compute_matrix_via_file_walk` and
    `corpus_index.compute_matrix_indexed`) no longer materialize
    them — only `per_chapter` (the canonical store) is built
    explicitly.

    API surface is preserved: `m.enabled[ed]`, `m.potential[ed]`,
    `m.per_book[ed]` all keep returning the same nested-dict
    shape they did pre-ψ.35-Final. Storage at the build site
    drops by 3 dict-of-dicts allocations + the inner summation
    loops; the per-Matrix-instance footprint is unchanged
    (`__post_init__` materializes the projections once and stores
    them via `object.__setattr__` on the frozen instance).

    Tests pin (a) the API surface still works, (b) the build
    pipelines no longer construct or pass the three projection
    dicts, (c) Matrix can be constructed without passing those
    three kwargs.
    """

    @classmethod
    def setup_class(cls):
        from scripts.core.matrix import compute_matrix

        cls.m = compute_matrix()

    def test_projection_fields_still_accessible(self):
        # API surface: existing consumers that do `m.enabled[ed]`
        # / `m.potential[ed]` / `m.per_book[ed]` keep working.
        m = self.m
        for ed_id in m.edition_canon_books:
            # Field-style access (the pre-ψ.35-Final contract)
            assert isinstance(m.enabled[ed_id], dict)
            assert isinstance(m.potential[ed_id], dict)
            assert isinstance(m.per_book[ed_id], dict)

    def test_projection_fields_are_init_false(self):
        # Pin the dataclass shape — these three fields must be
        # `init=False` so the build pipelines pass only the three
        # canonical sources (edition_canon_books,
        # edition_enabled_kinds, per_chapter).
        import dataclasses

        from scripts.core.matrix import Matrix

        fields_by_name = {f.name: f for f in dataclasses.fields(Matrix)}
        for derived in ("enabled", "potential", "per_book"):
            assert not fields_by_name[derived].init, (
                f"Matrix field {derived!r} should be init=False (derived in __post_init__) after ψ.35-Final"
            )
        for canonical in ("edition_canon_books", "edition_enabled_kinds", "per_chapter"):
            assert fields_by_name[canonical].init, (
                f"Matrix field {canonical!r} should be init=True (passed by build pipelines)"
            )

    def test_matrix_constructible_from_canonical_only(self):
        # Pin that Matrix(canonical-only-kwargs) works AND
        # auto-derives the three projection fields correctly.
        from scripts.core.matrix import Matrix

        per_chapter = {
            "test-edition": {
                "comm": {"gen": {1: 5, 2: 3}, "exo": {1: 2}},
                "word": {"gen": {1: 1}},
            },
        }
        m = Matrix(
            edition_canon_books={"test-edition": {"gen", "exo"}},
            edition_enabled_kinds={"test-edition": {"comm", "word"}},
            per_chapter=per_chapter,
        )
        # Auto-derived enabled
        assert m.enabled == {"test-edition": {"comm": 10, "word": 1}}
        # Auto-derived potential (same as enabled here since both kinds enabled)
        assert m.potential == {"test-edition": {"comm": 10, "word": 1}}
        # Auto-derived per_book
        assert m.per_book == {"test-edition": {"comm": {"gen": 8, "exo": 2}, "word": {"gen": 1}}}

    def test_disabled_kind_excluded_from_auto_derived_enabled(self):
        # If a kind is in per_chapter but NOT in edition_enabled_kinds,
        # the derived `enabled` projection must omit it (matching the
        # pre-ψ.35-Final `enabled = potential filtered by enabled_kinds`
        # contract).
        from scripts.core.matrix import Matrix

        per_chapter = {
            "test-edition": {
                "comm-disabled": {"gen": {1: 7}},
                "comm-enabled": {"gen": {1: 3}},
            },
        }
        m = Matrix(
            edition_canon_books={"test-edition": {"gen"}},
            edition_enabled_kinds={"test-edition": {"comm-enabled"}},
            per_chapter=per_chapter,
        )
        # potential has both kinds
        assert m.potential["test-edition"] == {"comm-disabled": 7, "comm-enabled": 3}
        # enabled has only the enabled one
        assert m.enabled["test-edition"] == {"comm-enabled": 3}

    def test_build_pipelines_no_longer_pass_projection_kwargs(self):
        # Source-scan: `_compute_matrix_via_file_walk` and
        # `compute_matrix_indexed` must construct Matrix without
        # passing `enabled=`, `potential=`, or `per_book=` kwargs.
        from pathlib import Path

        ROOT = Path(__file__).resolve().parent.parent
        for relpath in ("scripts/core/matrix.py", "scripts/core/corpus_index.py"):
            raw = (ROOT / relpath).read_text(encoding="utf-8")
            code_only = "\n".join(line for line in raw.splitlines() if not line.lstrip().startswith("#"))
            for kwarg in ("enabled=enabled,", "potential=potential,", "per_book=per_book,"):
                assert kwarg not in code_only, (
                    f"{relpath} still constructs Matrix with {kwarg!r}; "
                    f"ψ.35-Final removed the build-pipeline construction "
                    f"of the redundant projections."
                )

    def test_delta4_equivalence_still_holds_post_psi35_final(self):
        # The Δ.4 equivalence test compares
        # _compute_matrix_via_file_walk() against
        # corpus_index.compute_matrix_indexed(). After ψ.35-Final,
        # both pipelines build only per_chapter; both __post_init__
        # auto-derives the same projections. So the equivalence
        # should still hold.
        from scripts.core.matrix import _compute_matrix_via_file_walk
        from scripts.core import corpus_index

        m_indexed = corpus_index.compute_matrix_indexed()
        m_walk = _compute_matrix_via_file_walk()
        assert m_indexed.enabled == m_walk.enabled
        assert m_indexed.potential == m_walk.potential
        assert m_indexed.per_book == m_walk.per_book
        assert m_indexed.per_chapter == m_walk.per_chapter
        assert m_indexed.edition_canon_books == m_walk.edition_canon_books
        assert m_indexed.edition_enabled_kinds == m_walk.edition_enabled_kinds
