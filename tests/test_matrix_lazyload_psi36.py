"""ψ.36-A — per-edition matrix slice (lazy-load endpoint).

Topic file (created alongside the ψ.36-A ship, follows the ω.27
follow-on convention).

Coverage:
- TestApiMatrixForEditionShape:     the new function returns the
  expected JSON shape (edition + categories + kinds + matrix slot).
- TestApiMatrixForEditionParity:    the matrix slot equals the
  per-edition slice of /api/matrix's response (byte-for-byte).
- TestApiMatrixForEditionRoute:     /api/matrix/edition/<id> is
  registered in _REGEX_GET_ROUTES.
- TestApiMatrixForEditionErrors:    unknown edition → error envelope
  with http=404.

Every class lazy-imports its dependencies inside test method
bodies, so this file has no top-level imports from the project.
"""

from __future__ import annotations


class TestApiMatrixForEditionShape:
    """ψ.36-A: api_matrix_for_edition returns a self-contained
    payload that lets the client render one edition's matrix view
    without a second /api/matrix round-trip."""

    @classmethod
    def setup_class(cls):
        from scripts.web import api_matrix_for_edition

        cls.result = api_matrix_for_edition("catholic-study")

    def test_response_has_top_level_keys(self):
        expected = {"edition", "categories", "kinds", "matrix"}
        assert set(self.result) == expected, (
            f"matrix-for-edition keys drift: got={set(self.result)}, expected={expected}"
        )

    def test_edition_block_has_metadata(self):
        ed = self.result["edition"]
        for k in ("id", "title", "short_title", "canon", "enabled_categories", "enabled_kinds", "disabled_kinds"):
            assert k in ed, f"edition block missing key {k!r}"
        assert ed["id"] == "catholic-study"
        assert isinstance(ed["enabled_categories"], list)
        assert isinstance(ed["enabled_kinds"], list)
        assert isinstance(ed["disabled_kinds"], list)

    def test_categories_kinds_are_lists_of_dicts(self):
        cats = self.result["categories"]
        kinds = self.result["kinds"]
        assert isinstance(cats, list) and len(cats) > 0
        assert isinstance(kinds, list) and len(kinds) > 0
        for c in cats:
            assert {"id", "label", "symbol", "description", "sort_order"} <= set(c)
        for k in kinds:
            assert {"code", "category", "label"} <= set(k)

    def test_matrix_slot_has_per_edition_shape(self):
        slot = self.result["matrix"]
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
        assert set(slot) == expected_keys

    def test_matrix_slot_totals_are_positive(self):
        slot = self.result["matrix"]
        # Catholic Study has real notes; totals should be > 0
        assert slot["total_enabled"] > 0
        assert slot["total_potential"] > 0
        assert slot["canon_books_count"] > 0
        assert slot["enabled_kinds_count"] > 0


class TestApiMatrixForEditionParity:
    """ψ.36-A: byte-for-byte parity with the per-edition slot of
    /api/matrix's response. The new endpoint is purely a lazy-load
    optimization — the data it returns is the same data /api/matrix
    would return, just sliced to one edition."""

    def test_matrix_slot_matches_full_response(self):
        from scripts.web import api_matrix, api_matrix_for_edition

        full = api_matrix()
        for ed_id in full["matrix"]:
            sliced = api_matrix_for_edition(ed_id)
            assert sliced["matrix"] == full["matrix"][ed_id], f"per-edition slot drifted for edition {ed_id!r}"


class TestApiMatrixForEditionRoute:
    """ψ.36-A: the /api/matrix/edition/<id> route is registered."""

    def test_route_in_regex_get_routes(self):
        from scripts.web import _REGEX_GET_ROUTES, api_matrix_for_edition

        # Find the entry by handler identity
        found = False
        for pattern, handler in _REGEX_GET_ROUTES:
            if handler is api_matrix_for_edition:
                assert pattern.match("/api/matrix/edition/catholic-study"), (
                    f"pattern {pattern.pattern!r} doesn't match a real edition id"
                )
                found = True
                break
        assert found, "api_matrix_for_edition not in _REGEX_GET_ROUTES"


class TestApiMatrixForEditionErrors:
    """ψ.36-A: unknown edition surfaces the standard error envelope
    with http=404 so the route adapter translates correctly."""

    def test_unknown_edition_returns_error(self):
        from scripts.web import api_matrix_for_edition

        r = api_matrix_for_edition("not-a-real-edition-zzz")
        assert "error" in r
        assert "unknown edition" in r["error"]
        assert r.get("http") == 404
