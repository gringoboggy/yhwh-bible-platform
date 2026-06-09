"""Ω.0 free-public pivot pins (2026-05-14).

The project pivoted on 2026-05-14 from a for-sale publishing platform
to a free public Bible-builder. This pin-test file guards the
post-pivot invariants so subsequent commits can't accidentally
re-introduce ISBN / commercial-publishing machinery into surfaces
where the pivot explicitly removed it.

Coverage:
  - editions.yaml has no ``isbn`` field on any edition
  - edition_templates/*.yaml have no ``isbn`` field
  - validate_schemas.py has no isbn / isbn_epub / isbn_print FieldSpec
  - build_edition.py emits a ``urn:yhwh:edition:<id>`` identifier
    instead of ``urn:isbn:...``
  - build_edition.py copyright page identifies by URN, not ISBN
  - api_build_tracker returns sensible payloads + a 404 for unknowns
  - api_build_tracker_book returns notes per book + 404s for unknowns
  - /build-tracker route exists in BUILD_TRACKER_HTML
  - ONIX / sales / distribution / print_cover modules carry the
    LOAD-BEARING-NO-LONGER banner per §7.4
  - PUBLISHING_DEFAULTS in web.py has no isbn keys
  - editions.yaml ISBN-free pin (regex-based; tighter than presence)
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


# ----------------------------------------------------------------------
# editions.yaml + edition_templates/*.yaml
# ----------------------------------------------------------------------


class TestEditionsYamlIsbnFree:
    """Every for-sale-era ISBN field is gone from edition data."""

    def test_no_isbn_lines_in_editions_yaml(self):
        text = (REPO / "content" / "editions.yaml").read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            assert not stripped.startswith("isbn:"), f"isbn line survives in editions.yaml: {line!r}"

    def test_no_isbn_fields_in_edition_templates(self):
        templates_dir = REPO / "content" / "edition_templates"
        for tpl in sorted(templates_dir.glob("*.yaml")):
            text = tpl.read_text(encoding="utf-8")
            for line in text.splitlines():
                stripped = line.strip()
                # Yaml field gone; "ISBN" in prose comments is fine
                # if it's part of a strikethrough or rationale.
                assert not stripped.startswith("isbn:"), f"isbn line survives in {tpl.name}: {line!r}"


# ----------------------------------------------------------------------
# Schema validator
# ----------------------------------------------------------------------


class TestSchemaHasNoIsbnFieldSpec:
    """validate_schemas.py must not declare any isbn FieldSpec."""

    def test_isbn_fieldspecs_dropped(self):
        text = (REPO / "scripts" / "validate_schemas.py").read_text(encoding="utf-8")
        # FieldSpec("isbn", ...) / FieldSpec("isbn_epub", ...) /
        # FieldSpec("isbn_print", ...) all removed.
        for forbidden in ('FieldSpec("isbn"', 'FieldSpec("isbn_epub"', 'FieldSpec("isbn_print"'):
            assert forbidden not in text, f"residual schema spec: {forbidden}"


# ----------------------------------------------------------------------
# build_edition.py
# ----------------------------------------------------------------------


class TestBuildEditionUrnReplacesIsbn:
    """The EPUB identifier moved from urn:isbn:... to urn:yhwh:edition:<id>."""

    def setup_method(self):
        import importlib

        self.be = importlib.import_module("scripts.build_edition")

    def test_patch_opf_emits_edition_urn_not_isbn(self):
        opf = (
            "<?xml version='1.0'?>\n"
            '<package version="3.0">\n'
            '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
            '<dc:title>X</dc:title><dc:creator id="creator">Public Domain</dc:creator>\n'
            '<meta refines="#creator" property="role" scheme="marc:relators">aut</meta>\n'
            '<meta refines="#creator" property="file-as">Public Domain</meta>\n'
            '<dc:contributor id="contributor">calibre</dc:contributor>\n'
            "<dc:date>2020-01-01</dc:date><dc:language>en</dc:language>\n"
            "</metadata></package>"
        )
        edition = {"id": "test-ed", "title": "X", "publisher_name": "Free Press"}
        out = self.be.patch_opf(opf, edition, "v1")
        assert "urn:yhwh:edition:test-ed" in out
        assert "urn:isbn:" not in out
        # The ONIX codelist5 type=15 (ISBN-13) refinement is also gone.
        assert 'scheme="onix:codelist5">15<' not in out

    def test_render_copyright_page_uses_urn_not_isbn(self):
        edition = {"id": "demo", "title_full": "Demo Edition"}
        publishing = {
            "publisher_name": "Demo Pub",
            "copyright_year": "2026",
            "copyright_holder": "Demo Editor",
        }
        html = self.be.render_copyright_page(edition, publishing, annotation_count=100, category_count=5)
        # 2030e7e0 (device-QA AB②): the URN identity block moved off the front
        # colophon onto the Your Edition page — the colophon is legal/publisher
        # only. The Ω.0 pivot pin is unchanged in spirit: the edition is
        # identified by URN (now on Your Edition), never by ISBN, anywhere.
        assert "urn:yhwh:edition:demo" not in html
        assert "ISBN" not in html
        assert "TODO_ISBN" not in html
        stats = {
            "total": 100,
            "per_book": {"gen": 100},
            "per_category": {"comm": 100},
            "per_kind": {"comm-patristic": 100},
            "popup_languages": [],
        }
        your = self.be.render_your_edition_page(edition, stats, "v1")
        assert "urn:yhwh:edition:demo" in your
        assert "ISBN" not in your

    def test_resolve_publishing_drops_isbn_keys(self):
        ed = {"id": "x", "publisher_name": "P"}
        pub = self.be._resolve_publishing(ed)
        assert "isbn_epub" not in pub
        assert "isbn_print" not in pub


# ----------------------------------------------------------------------
# /build-tracker endpoints
# ----------------------------------------------------------------------


class TestBuildTrackerEndpoint:
    """The Ω.0 enabled-notes tracker API."""

    def setup_method(self):
        from scripts.web import api_build_tracker

        self.api = api_build_tracker

    def test_returns_404_for_unknown_edition(self):
        r = self.api("not-a-real-edition")
        assert "error" in r
        assert r.get("http") == 404

    def test_returns_summary_shape_for_known_edition(self):
        r = self.api("catholic-study")
        assert "edition" in r
        assert r["edition"]["id"] == "catholic-study"
        s = r["summary"]
        for k in (
            "total_enabled_notes",
            "books_covered",
            "books_in_canon",
            "chapters_covered",
            "chapters_in_canon",
            "kinds_enabled",
            "categories_enabled",
            "popup_languages",
        ):
            assert k in s, f"missing summary key {k}"

    def test_per_book_payload_has_chapter_array(self):
        r = self.api("catholic-study")
        assert isinstance(r["per_book"], list)
        assert r["per_book"], "expected at least one book"
        for b in r["per_book"][:3]:
            for k in (
                "book_code",
                "book_label",
                "chapters_in_canon",
                "enabled_notes",
                "enabled_chapters",
                "by_chapter",
            ):
                assert k in b
            assert isinstance(b["by_chapter"], list)
            assert len(b["by_chapter"]) == b["chapters_in_canon"]

    def test_per_category_sorted_desc(self):
        r = self.api("catholic-study")
        counts = [c["enabled_notes"] for c in r["per_category"]]
        assert counts == sorted(counts, reverse=True)

    def test_per_kind_sorted_desc(self):
        r = self.api("catholic-study")
        counts = [k["enabled_notes"] for k in r["per_kind"]]
        assert counts == sorted(counts, reverse=True)
        # No kind appears that isn't actually enabled.
        from scripts.core import matrix as matrix_mod

        m = matrix_mod.compute_matrix()
        enabled = m.edition_enabled_kinds.get("catholic-study", set())
        for k in r["per_kind"]:
            assert k["code"] in enabled, f"kind {k['code']} listed but not enabled"


class TestBuildTrackerBuildAccurate:
    """σ.6.1 — /build-tracker counts come from the build-accurate counter
    (edition_stats.resolved_note_counts), so the live preview equals the built
    EPUB and honors the ρ.3 hierarchy. The old edition-wide matrix path
    over-counted by the base-coverage residual and ignored per-coordinate
    overrides."""

    def test_total_equals_resolved_note_counts(self):
        from scripts.core import config, edition_stats
        from scripts.web import api_build_tracker

        ed = config.editions_by_id()["catholic-study"]
        expected = edition_stats.resolved_note_counts(ed)["total"]
        r = api_build_tracker("catholic-study")
        assert r["summary"]["total_enabled_notes"] == expected
        # per_book + per_category + per_kind all sum to the same total.
        assert sum(b["enabled_notes"] for b in r["per_book"]) == expected
        assert sum(c["enabled_notes"] for c in r["per_category"]) == expected
        assert sum(k["enabled_notes"] for k in r["per_kind"]) == expected

    def test_per_chapter_grid_matches_resolved(self):
        from scripts.core import config, edition_stats
        from scripts.web import api_build_tracker

        ed = config.editions_by_id()["catholic-study"]
        rc = edition_stats.resolved_note_counts(ed)
        pbc = rc["per_book_chapter"]
        r = api_build_tracker("catholic-study")
        for b in r["per_book"]:
            # each heat-grid cell (ch-1 → array idx) equals the resolved
            # per-(book, chapter) count for that coordinate.
            book_chs = pbc.get(b["book_code"], {})
            for idx, n in enumerate(b["by_chapter"]):
                assert n == book_chs.get(idx + 1, 0), f"{b['book_code']} ch{idx + 1}: grid {n} != resolved"

    def test_override_edition_drops_book_count_and_agrees(self, tmp_path):
        import shutil

        from scripts.core import config, edition_stats
        from scripts.web import api_build_tracker

        yml = REPO / "content" / "editions.yaml"
        backup = tmp_path / "ed.bak"
        shutil.copy(yml, backup)

        def _clear():
            config.load_editions.cache_clear()
            from scripts.core import matrix as m

            m.compute_matrix.cache_clear()
            edition_stats.resolved_note_counts.cache_clear()

        try:
            _clear()
            before = api_build_tracker("catholic-study")
            before_gen = next(b["enabled_notes"] for b in before["per_book"] if b["book_code"] == "gen")

            import scripts.web as web

            web.api_save_edition_meta("catholic-study", {"note_families_off_per_book": {"gen": ["xref"]}})
            _clear()

            after = api_build_tracker("catholic-study")
            after_gen = next(b["enabled_notes"] for b in after["per_book"] if b["book_code"] == "gen")

            # The dropped family lowers gen's count + the edition total.
            assert after_gen < before_gen
            assert after["summary"]["total_enabled_notes"] < before["summary"]["total_enabled_notes"]

            # The live total still equals the build-accurate resolved total.
            ed = config.editions_by_id()["catholic-study"]
            assert after["summary"]["total_enabled_notes"] == edition_stats.resolved_note_counts(ed)["total"]
        finally:
            shutil.copy(backup, yml)
            _clear()

    def test_agrees_with_build_my_bible_per_coordinate(self, tmp_path):
        """The build-tracker grid (resolved_note_counts) and the per-coordinate
        /build-my-bible navigator must agree on which (book, chapter) coordinates
        carry notes: a chapter the navigator reports has_notes=False (no enabled
        note survives the hierarchy) must be a 0-cell in the tracker grid, and a
        tracker cell with notes must be has_notes=True. Both resolve via the same
        ρ.3 filter (compute_edition_filter_sets / enabled_kind_codes_for)."""
        import shutil

        from scripts.core import config, edition_stats
        from scripts.web import api_build_my_bible, api_build_tracker

        yml = REPO / "content" / "editions.yaml"
        backup = tmp_path / "ed.bak"
        shutil.copy(yml, backup)

        def _clear():
            config.load_editions.cache_clear()
            from scripts.core import matrix as m

            m.compute_matrix.cache_clear()
            edition_stats.resolved_note_counts.cache_clear()

        try:
            _clear()
            # Use an override edition so the agreement is non-trivial.
            import scripts.web as web

            web.api_save_edition_meta("catholic-study", {"note_families_off_per_book": {"gen": ["xref"]}})
            _clear()

            tracker = api_build_tracker("catholic-study")
            ed = config.editions_by_id()["catholic-study"]
            rc = edition_stats.resolved_note_counts(ed)
            pbc = rc["per_book_chapter"]

            # For gen, every chapter the navigator says has notes must be a
            # non-zero resolved cell, and vice-versa (both honor the per-book OFF).
            book = api_build_my_bible("catholic-study", book="gen")
            gen_chs = pbc.get("gen", {})
            for ch in book["chapters"]:
                nav_has = bool(ch.get("has_notes"))
                resolved_n = gen_chs.get(ch["num"], 0)
                # has_notes is "any enabled-kind note exists" (matrix per_chapter,
                # pre base-coverage gate); resolved_n is build-accurate. So
                # resolved_n>0 ⇒ has_notes must be True (no note ships without one
                # existing). The reverse can differ only by the base-coverage
                # residual, so we assert the strong direction.
                if resolved_n > 0:
                    assert nav_has, f"gen ch{ch['num']}: tracker {resolved_n} notes but navigator has_notes=False"
        finally:
            shutil.copy(backup, yml)
            _clear()


class TestBuildTrackerBookEndpoint:
    def setup_method(self):
        from scripts.web import api_build_tracker_book

        self.api = api_build_tracker_book

    def test_returns_404_for_unknown_edition(self):
        r = self.api("not-a-real-edition", "gen")
        assert r.get("http") == 404

    def test_returns_404_for_unknown_book(self):
        r = self.api("catholic-study", "not-a-real-book")
        assert r.get("http") == 404

    def test_returns_notes_for_known_pair(self):
        r = self.api("catholic-study", "gen")
        assert "notes" in r
        assert isinstance(r["notes"], list)
        # Each note has the documented shape.
        for n in r["notes"][:5]:
            assert set(n.keys()) >= {"id", "chapter", "kind", "title"}
            assert isinstance(n["chapter"], int)


# ----------------------------------------------------------------------
# /build-tracker HTML + console nav
# ----------------------------------------------------------------------


class TestBuildTrackerHtml:
    def setup_method(self):
        from scripts.templates.build_tracker import BUILD_TRACKER_HTML

        self.html = BUILD_TRACKER_HTML

    def test_serves_a_full_html_document(self):
        assert self.html.startswith("<!DOCTYPE html>")
        assert "</html>" in self.html

    def test_carries_cross_link_nav(self):
        # §6.2 invariant — every console nav is cross-linked.
        # apply_design_system substituted HEADER_NAV_LINKS in place
        # of the placeholder comment, so the rendered HTML must
        # carry hrefs to its siblings.
        for sibling in ("/matrix", "/customize", "/preflight"):
            assert f'href="{sibling}"' in self.html

    def test_fetches_build_tracker_endpoint(self):
        # The JS payload calls /api/build-tracker/<edition_id> on
        # select-change. Pin the literal so a future refactor doesn't
        # silently drift the contract.
        assert "/api/build-tracker/" in self.html


class TestBuildTrackerInConsoleList:
    def test_console_list_includes_build_tracker(self):
        from scripts.templates._design import CONSOLES

        routes = [r for r, _ in CONSOLES]
        assert "/build-tracker" in routes


# ----------------------------------------------------------------------
# ONIX / sales / distribution / print_cover removal (Phase 4 decommercialize)
# ----------------------------------------------------------------------


class TestCommercialModulesRemoved:
    """Phase 4 (decommercialize): the dead commercial-era modules are DELETED
    outright — the §7.4 LOAD-BEARING-NO-LONGER banner was only a transitional
    measure. Only scripts/core/distribution.py survives, as an archival library
    that still backs archive.org free distribution, and it keeps its banner."""

    # Deleted on disk in Phase 4 — must not reappear.
    REMOVED = (
        "scripts/build_onix.py",
        "content/onix.py",
        "scripts/core/sales.py",
        "scripts/print_cover.py",
    )
    # NOTE (mint-10): scripts/api/distribution.py is NOT removed — it is the
    # live mint-6 archive.org distribution console module. (It is not in KEPT
    # either; KEPT only tracks the banner-carrying core/distribution.py.)

    # Kept as an archival free-distribution library — banner must remain.
    KEPT = ("scripts/core/distribution.py",)

    @pytest.mark.parametrize("rel", REMOVED)
    def test_deleted_modules_gone(self, rel):
        assert not (REPO / rel).exists(), f"{rel} should be deleted in Phase 4 (decommercialize)"

    @pytest.mark.parametrize("rel", KEPT)
    def test_kept_module_carries_banner(self, rel):
        text = (REPO / rel).read_text(encoding="utf-8")
        assert "LOAD-BEARING-NO-LONGER" in text, f"{rel} missing Ω.0 deprecation banner"
        # Cross-reference to the pivot so future readers find context.
        assert "Ω.0" in text, f"{rel} banner missing Ω.0 phase tag"


# ----------------------------------------------------------------------
# PUBLISHING_DEFAULTS sanity
# ----------------------------------------------------------------------


class TestPublishingDefaultsIsbnFree:
    def test_no_isbn_keys_in_defaults_or_limits(self):
        from scripts.web import PUBLISHING_DEFAULTS, PUBLISHING_TEXT_LIMITS

        for k in PUBLISHING_DEFAULTS:
            assert "isbn" not in k.lower(), f"residual key in PUBLISHING_DEFAULTS: {k}"
        for k in PUBLISHING_TEXT_LIMITS:
            assert "isbn" not in k.lower(), f"residual key in PUBLISHING_TEXT_LIMITS: {k}"


# ----------------------------------------------------------------------
# Project rules
# ----------------------------------------------------------------------


class TestProjectRulesReflectPivot:
    def test_north_star_references_builder_demo(self):
        text = (REPO / "dev" / "CLAUDE_PROJECT_RULES.md").read_text(encoding="utf-8")
        assert "**The builder demo.**" in text
        assert "Ω.0" in text

    def test_session_state_lists_build_tracker_console(self):
        # The build-tracker console (Ω.0 free-public pivot) must appear in
        # SESSION_STATE's console inventory. Accept either the route
        # (/build-tracker) or the canonical constant (BUILD_TRACKER_HTML) —
        # the same equivalence scripts/lint_rules.py::check_session_state_
        # inventory uses. The 2026-05-21 SESSION_STATE trim left the
        # inventory keyed by constant name.
        text = (REPO / "dev" / "SESSION_STATE.md").read_text(encoding="utf-8")
        assert "/build-tracker" in text or "BUILD_TRACKER_HTML" in text


# ----------------------------------------------------------------------
# Live tooling path — de-commercialized (audit 2026-05-21, P1)
# ----------------------------------------------------------------------


class TestLiveToolingDecommercialized:
    """The Ω.0 pivot quarantined the commercial *modules* with
    LOAD-BEARING-NO-LONGER banners, but the live CLI path
    (ship-check.py + ebible.py doctor/status/ship) kept invoking
    build_onix.py and printing "submit to Apple Books / KDP / Kobo"
    retailer advice. The 2026-05-21 "smoother-running" audit (P1)
    unwired that path; these pins keep it unwired so a future edit
    can't silently re-commercialize the live tooling.
    """

    def _read(self, rel: str) -> str:
        return (REPO / rel).read_text(encoding="utf-8")

    def test_ship_check_does_not_invoke_build_onix(self):
        text = self._read("scripts/ship-check.py")
        assert "build_onix" not in text, "ship-check still runs the dead ONIX builder"
        assert "skip-onix" not in text and "skip_onix" not in text, "stale --skip-onix flag survives"

    def test_ship_check_has_no_commercial_framing(self):
        low = self._read("scripts/ship-check.py").lower()
        assert "retail" not in low, "ship-check still carries 'retail' framing"
        assert "submission" not in low, "ship-check still references retailer submission"

    def test_ebible_has_no_onix_or_retailer_advice(self):
        text = self._read("scripts/ebible.py")
        low = text.lower()
        assert "onix" not in low, "ebible.py still references ONIX in the live path"
        for term in ("Apple Books", "KDP", "Kobo"):
            assert term not in text, f"ebible.py still names retailer {term!r}"
        assert "retail" not in low, "ebible.py still carries 'retail' framing"

    def test_ebible_subprocess_helpers_devnull_guarded(self):
        # Windows WinError-6 hazard (memory feedback_w_w1_subprocess_devnull):
        # non-interactive subprocesses must close stdin.
        text = self._read("scripts/ebible.py")
        assert "stdin=subprocess.DEVNULL" in text, "ebible subprocess helpers not DEVNULL-guarded"

    def test_ship_check_run_helper_devnull_guarded(self):
        text = self._read("scripts/ship-check.py")
        assert "stdin=subprocess.DEVNULL" in text, "ship-check run() not DEVNULL-guarded"
