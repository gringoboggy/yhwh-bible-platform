"""ω.27 follow-on (2026-05-11) — v1.0 console-polish bundle test
classes, split out of the monolithic ``tests/test_scripts.py``
into a topic file alongside the other ω.27 follow-on splits.

Fourteenth topic extraction. The v1.0 console-polish bundle
shipped six phases together that all touched the templates
package — header nav, buyer-arc CSS, edition templates,
status-dashboard polish, wizard branding, design-system
consolidation:

- ψ.15   editor-console header nav + buyer-arc polish CSS
- ψ.7-A  four built-in editions (eastern-orthodox, anglican-bcp,
         lutheran-confessional, coptic-orthodox)
- ψ.7-B  edition template starter packs + wizard "from template"
         button
- ψ.16   status-dashboard substitution + polish CSS + index
         editor polish CSS (lifts /matrix /publisher etc. to
         13-console parity)
- ν.2.8  customize visual sections (collapsible cards per
         CLAUDE_PROJECT_RULES §9 "Surface a developer-only
         style knob")
- ψ.11   wizard branding polish (logo + tagline + nav alignment)
- ψ.13.5 design-system consolidation (f-string sweep across
         the 14 template files; one source of truth per knob)

Every class lazy-imports its dependencies inside test method
bodies, so this file has no top-level imports from the project.
"""


class TestPsi15EditorConsoleHeaderNavSubstitution:
    """ψ.15: cross-link nav in /customize, /publisher, /covers,
    /matrix, /sources is sourced from `_design.HEADER_NAV_LINKS()`
    at module load — same pattern as ψ.14's buyer-arc consoles.

    Side-effect: nav labels become uniform across all 13 consoles
    (was hand-rolled "matrix" inline, now "symbol matrix" via
    _design.CONSOLES)."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.customize import CUSTOMIZE_HTML
        from scripts.templates.publisher import PUBLISHER_HTML
        from scripts.templates.covers import COVERS_HTML
        from scripts.templates.matrix import MATRIX_HTML
        from scripts.templates.sources import SOURCES_HTML
        from scripts.templates._design import (
            HEADER_NAV_LINKS,
            BUYER_ARC_POLISH_CSS,
            CONSOLES,
        )

        cls.htmls = {
            "customize": CUSTOMIZE_HTML,
            "publisher": PUBLISHER_HTML,
            "covers": COVERS_HTML,
            "matrix": MATRIX_HTML,
            "sources": SOURCES_HTML,
        }
        cls.HEADER_NAV_LINKS = HEADER_NAV_LINKS
        cls.BUYER_ARC_POLISH_CSS = BUYER_ARC_POLISH_CSS
        cls.CONSOLES = CONSOLES

    def test_marker_is_fully_replaced(self):
        # Substitution failure would leave the literal comment.
        for name, html in self.htmls.items():
            assert "<!-- HEADER_NAV_LINKS -->" not in html, f"{name}: HEADER_NAV_LINKS marker not substituted"

    def test_polish_css_marker_is_replaced(self):
        for name, html in self.htmls.items():
            assert "<!-- BUYER_ARC_POLISH_CSS -->" not in html, f"{name}: BUYER_ARC_POLISH_CSS marker not substituted"

    def test_current_console_marked_font_semibold(self):
        # The console rendering its own page should mark its own
        # link with font-semibold (the "you are here" indicator).
        cases = {
            "customize": '<a href="/customize" class="font-semibold">',
            "publisher": '<a href="/publisher" class="font-semibold">',
            "covers": '<a href="/covers" class="font-semibold">',
            "matrix": '<a href="/matrix" class="font-semibold">',
            "sources": '<a href="/sources" class="font-semibold">',
        }
        for name, expected in cases.items():
            assert expected in self.htmls[name], f"{name}: missing self-link with font-semibold"

    def test_other_consoles_marked_text_blue_600(self):
        # Non-current links use the underline-on-hover style.
        # Sample one cross-pair per console.
        cases = {
            "customize": '<a href="/publisher" class="text-blue-600 hover:underline">',
            "publisher": '<a href="/customize" class="text-blue-600 hover:underline">',
            "covers": '<a href="/sources" class="text-blue-600 hover:underline">',
            "matrix": '<a href="/wizard" class="text-blue-600 hover:underline">',
            "sources": '<a href="/matrix" class="text-blue-600 hover:underline">',
        }
        for name, expected in cases.items():
            assert expected in self.htmls[name], f"{name}: missing other-link with text-blue-600"

    def test_substitution_includes_all_consoles(self):
        # Every route in CONSOLES appears as an href in each
        # substituted editor template.
        for name, html in self.htmls.items():
            for route, _label in self.CONSOLES:
                assert f'href="{route}"' in html, f"{name}: missing href={route} after substitution"

    def test_canonical_label_symbol_matrix_present(self):
        # Side-effect of switching to _design.CONSOLES: the
        # canonical label for /matrix is "symbol matrix", not
        # "matrix". Verify the new label rides through every
        # editor template.
        for name, html in self.htmls.items():
            if name == "matrix":
                continue  # this is its own self-link case (above)
            assert ">symbol matrix<" in html, f"{name}: missing canonical 'symbol matrix' label"

    def test_design_module_imported(self):
        # Each editor template imports HEADER_NAV_LINKS +
        # BUYER_ARC_POLISH_CSS from _design — verify by loading
        # the module and checking attributes are present.
        import importlib

        for name in self.htmls:
            mod = importlib.import_module(f"scripts.templates.{name}")
            assert hasattr(mod, "HEADER_NAV_LINKS"), f"{name}: HEADER_NAV_LINKS not imported"
            assert hasattr(mod, "BUYER_ARC_POLISH_CSS"), f"{name}: BUYER_ARC_POLISH_CSS not imported"


class TestPsi15EditorConsoleBuyerArcPolishCSS:
    """ψ.15: BUYER_ARC_POLISH_CSS layer is injected into the 5
    editor consoles — same focus-ring + transition + click-feedback
    polish that ψ.14 gave the buyer-arc consoles."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.customize import CUSTOMIZE_HTML
        from scripts.templates.publisher import PUBLISHER_HTML
        from scripts.templates.covers import COVERS_HTML
        from scripts.templates.matrix import MATRIX_HTML
        from scripts.templates.sources import SOURCES_HTML

        cls.htmls = {
            "customize": CUSTOMIZE_HTML,
            "publisher": PUBLISHER_HTML,
            "covers": COVERS_HTML,
            "matrix": MATRIX_HTML,
            "sources": SOURCES_HTML,
        }

    def test_focus_visible_outline_present(self):
        for name, html in self.htmls.items():
            assert "*:focus-visible" in html, f"{name}: missing focus-visible outline rule"

    def test_button_active_scale_feedback(self):
        for name, html in self.htmls.items():
            assert "button:active:not(:disabled)" in html, f"{name}: missing button :active feedback"
            assert "scale(0.98)" in html, f"{name}: missing button scale-down rule"

    def test_psi14_pending_pill_class(self):
        for name, html in self.htmls.items():
            assert ".psi14-pending::after" in html, f"{name}: missing .psi14-pending pill rule"

    def test_step_fade_in_keyframes(self):
        for name, html in self.htmls.items():
            assert "@keyframes psi14StepFadeIn" in html, f"{name}: missing psi14StepFadeIn keyframe"


class TestPsi7ANewBuiltInEditions:
    """ψ.7-A — four new built-in editions added to content/editions.yaml:
    eastern-orthodox, anglican-bcp, lutheran-confessional, coptic-orthodox.
    Per CLAUDE_PROJECT_RULES §9 'Add a new edition feature' the additions
    are schema-additive; existing 5 editions remain unchanged.

    Spec: dev/SCOPE_2026-05-09-addendum-edition-templates.md §1."""

    NEW_EDITIONS = (
        "eastern-orthodox",
        "anglican-bcp",
        "lutheran-confessional",
        "coptic-orthodox",
    )

    EXPECTED_CANON = {
        "eastern-orthodox": "orthodox",
        "anglican-bcp": "catholic",
        "lutheran-confessional": "protestant",
        "coptic-orthodox": "ethiopian",
    }

    EXISTING_EDITIONS = (
        "ethiopian-tewahedo",
        "catholic-study",
        "evangelical-reformed",
        "jewish-study",
        "scholarly-academic",
    )

    @classmethod
    def setup_class(cls):
        import yaml
        from pathlib import Path
        from scripts.core import config
        from scripts.core import matrix as matrix_mod

        # Caches may carry stale data from prior tests; reset
        if hasattr(config.load_editions, "cache_clear"):
            config.load_editions.cache_clear()
        matrix_mod.compute_matrix.cache_clear()
        cls.editions = config.load_editions()
        cls.editions_by_id = {e["id"]: e for e in cls.editions}
        # canons.yaml is loaded directly via the matrix module's
        # private helper; replicate inline to avoid private-API churn
        canons_path = Path(__file__).resolve().parent.parent / "content" / "canons.yaml"
        canons_data = yaml.safe_load(canons_path.read_text(encoding="utf-8")) or {}
        cls.canons = canons_data.get("canons", {}) or {}
        cls.matrix = matrix_mod.compute_matrix()

    def test_total_edition_count_is_nine(self):
        # 5 original + 4 ψ.7-A additions = 9.
        # τ.G.constitution.a (2026-05-20) added 2 standalone Bibles
        # (standalone-geez, standalone-amharic) → 11.
        assert len(self.editions) >= 11, f"expected >= 11 editions, found {len(self.editions)}"

    def test_existing_editions_still_present(self):
        for ed_id in self.EXISTING_EDITIONS:
            assert ed_id in self.editions_by_id, f"existing edition {ed_id} disappeared"

    def test_new_editions_loaded(self):
        for ed_id in self.NEW_EDITIONS:
            assert ed_id in self.editions_by_id, f"new edition {ed_id} not loaded"

    def test_each_new_edition_has_canon_field(self):
        for ed_id in self.NEW_EDITIONS:
            ed = self.editions_by_id[ed_id]
            assert ed.get("canon") == self.EXPECTED_CANON[ed_id], (
                f"{ed_id}: canon={ed.get('canon')!r} but expected {self.EXPECTED_CANON[ed_id]!r}"
            )

    def test_each_new_edition_canon_is_defined(self):
        # The canon field must point to a real canon in canons.yaml.
        for ed_id in self.NEW_EDITIONS:
            ed = self.editions_by_id[ed_id]
            canon_id = ed["canon"]
            assert canon_id in self.canons, f"{ed_id}: canon {canon_id!r} not in canons.yaml"

    def test_each_new_edition_has_required_fields(self):
        # Per §9 mental model — every edition has these fields.
        required = {
            "id",
            "canon",
            "title",
            "short_title",
            "target_audience",
            "enabled_categories",
            "max_phase",
            "notes",
        }
        for ed_id in self.NEW_EDITIONS:
            ed = self.editions_by_id[ed_id]
            missing = required - set(ed.keys())
            assert not missing, f"{ed_id}: missing required fields {missing}"

    def test_each_new_edition_yields_nonzero_potential_notes(self):
        # If an edition's canon ∩ enabled_kinds yields no notes, the
        # edition won't render anything useful — fail loudly.
        for ed_id in self.NEW_EDITIONS:
            potential_total = sum(self.matrix.potential.get(ed_id, {}).values())
            assert potential_total > 0, f"{ed_id}: potential count is 0; canon ∩ kinds yields nothing"

    def test_each_new_edition_yields_nonzero_enabled_notes(self):
        # The edition's enabled-kind filter should yield SOME notes
        # — if disabled_kinds + canon together strip everything,
        # the edition is misconfigured.
        for ed_id in self.NEW_EDITIONS:
            enabled_total = sum(self.matrix.enabled.get(ed_id, {}).values())
            assert enabled_total > 0, f"{ed_id}: enabled count is 0; check disabled_kinds isn't stripping every kind"

    def test_eastern_orthodox_uses_previously_unused_orthodox_canon(self):
        # The orthodox canon was defined in canons.yaml but not used
        # by any edition pre-ψ.7-A. Verify eastern-orthodox is now
        # the (sole) consumer.
        orthodox_users = [e["id"] for e in self.editions if e.get("canon") == "orthodox"]
        assert orthodox_users == ["eastern-orthodox"], f"expected exactly [eastern-orthodox], got {orthodox_users}"

    def test_each_new_edition_disables_conflicting_kinds(self):
        # Each new edition has explicit disabled_kinds — verify the
        # tradition-conflict invariant. eastern-orthodox should
        # disable comm-reformation; anglican-bcp should disable
        # dist-mariological per 39 Articles posture; lutheran should
        # disable comm-orthodox; coptic should disable comm-rabbinic.
        cases = {
            "eastern-orthodox": "comm-reformation",
            "anglican-bcp": "dist-mariological",
            "lutheran-confessional": "comm-orthodox",
            "coptic-orthodox": "comm-rabbinic",
        }
        for ed_id, expected_disabled in cases.items():
            ed = self.editions_by_id[ed_id]
            disabled = set(ed.get("disabled_kinds") or [])
            assert expected_disabled in disabled, (
                f"{ed_id}: expected {expected_disabled!r} in disabled_kinds, got {sorted(disabled)}"
            )

    def test_canon_book_counts_match_expectation(self):
        # v0.0.3 folded the empty "Additions to Esther" (aes) out of every
        # canon → the catholic/orthodox/ethiopian-derived editions each −1.
        # eastern-orthodox: orthodox canon (77 books)
        # anglican-bcp: catholic canon (75 books)
        # lutheran-confessional: protestant canon (66 books — no aes)
        # coptic-orthodox: ethiopian canon (86 books)
        expected = {
            "eastern-orthodox": 77,
            "anglican-bcp": 75,
            "lutheran-confessional": 66,
            "coptic-orthodox": 86,
        }
        for ed_id, expected_count in expected.items():
            book_set = self.matrix.edition_canon_books.get(ed_id, set())
            assert len(book_set) == expected_count, (
                f"{ed_id}: canon has {len(book_set)} books (expected {expected_count})"
            )

    def test_new_editions_have_no_isbn_post_pivot(self):
        # Ω.0 pivot (2026-05-14): ISBN dropped from editions.yaml.
        # No edition should carry an isbn field anymore.
        for ed_id in self.NEW_EDITIONS:
            ed = self.editions_by_id[ed_id]
            assert "isbn" not in ed, f"{ed_id}: still has isbn field post-pivot"

    def test_new_editions_appear_in_api_matrix_response(self):
        # End-to-end: api_matrix() should surface all 11 editions
        # (9 multi-tradition + 2 standalone Bibles, per
        # τ.G.constitution.a 2026-05-20).
        from scripts.core import matrix as matrix_mod
        from scripts.core import config

        if hasattr(config.load_editions, "cache_clear"):
            config.load_editions.cache_clear()
        matrix_mod.compute_matrix.cache_clear()
        import importlib

        web = importlib.import_module("scripts.web")
        api = web.api_matrix()
        ed_ids = {e["id"] for e in api["editions"]}
        for ed_id in self.NEW_EDITIONS:
            assert ed_id in ed_ids, f"{ed_id} missing from api_matrix() response"
        assert len(api["editions"]) >= 11


class TestPsi7BEditionTemplates:
    """ψ.7-B — edition starter-pack templates.

    Templates live in `content/edition_templates/*.yaml` as
    partial-edition records. They surface via
    api_edition_templates_list (GET /api/edition-templates) and
    are cloned into editions.yaml via
    api_create_edition_from_template (POST /api/editions/from-template).

    Spec: dev/SCOPE_2026-05-09-addendum-edition-templates.md §2."""

    EXPECTED_TEMPLATES = (
        "anglican-bcp",
        "children",
        "family-devotional",
        "lutheran-confessional",
        "monastic-daily-office",
        "scholarly-academic-with-apparatus",
        "school-friendly-nrsv",
    )

    @classmethod
    def setup_class(cls):
        from scripts.core import edition_templates as et

        if hasattr(et.load_templates, "cache_clear"):
            et.load_templates.cache_clear()
        cls.et = et
        cls.templates = et.load_templates()
        cls.templates_by_id = {t["template_id"]: t for t in cls.templates}

    def test_template_count(self):
        # All 7 expected templates load
        assert len(self.templates) == 7, f"expected 7 templates, found {len(self.templates)}"

    def test_all_expected_templates_present(self):
        for tid in self.EXPECTED_TEMPLATES:
            assert tid in self.templates_by_id, f"template {tid!r} not found"

    def test_templates_sorted_alphabetically(self):
        ids = [t["template_id"] for t in self.templates]
        assert ids == sorted(ids), f"templates not sorted: {ids}"

    def test_each_template_has_required_template_fields(self):
        # template_id, template_label, template_description
        for t in self.templates:
            assert t.get("template_id"), "missing template_id"
            assert t.get("template_label"), f"{t['template_id']}: missing template_label"
            assert t.get("template_description"), f"{t['template_id']}: missing template_description"

    def test_each_template_has_required_edition_fields(self):
        # canon, title, short_title, target_audience,
        # enabled_categories, max_phase, popup_languages_default
        required = {
            "canon",
            "title",
            "short_title",
            "target_audience",
            "enabled_categories",
            "max_phase",
            "popup_languages_default",
        }
        for t in self.templates:
            missing = required - set(t.keys())
            assert not missing, f"{t['template_id']}: missing edition fields {missing}"

    def test_each_template_canon_is_defined(self):
        # Template canon must point to a real canon in canons.yaml.
        import yaml
        from pathlib import Path

        canons_path = Path(__file__).resolve().parent.parent / "content" / "canons.yaml"
        canons = (yaml.safe_load(canons_path.read_text(encoding="utf-8")) or {}).get("canons", {})
        for t in self.templates:
            assert t["canon"] in canons, f"{t['template_id']}: canon {t['canon']!r} not in canons.yaml"

    def test_get_template_by_id(self):
        t = self.et.get_template("children")
        assert t is not None
        assert t["template_id"] == "children"
        assert self.et.get_template("does-not-exist") is None

    def test_api_edition_templates_list_shape(self):
        from scripts.web import api_edition_templates_list

        out = api_edition_templates_list()
        assert "templates" in out
        assert isinstance(out["templates"], list)
        assert len(out["templates"]) == 7
        for t in out["templates"]:
            assert set(t.keys()) >= {
                "template_id",
                "label",
                "description",
                "canon",
                "target_audience",
            }

    def test_api_edition_templates_list_sorted(self):
        from scripts.web import api_edition_templates_list

        out = api_edition_templates_list()
        ids = [t["template_id"] for t in out["templates"]]
        assert ids == sorted(ids)

    # --- create_from_template rejection paths ---

    def test_create_rejects_unknown_template(self):
        from scripts.web import api_create_edition_from_template

        r = api_create_edition_from_template("does-not-exist", "test-clone", "Test Clone")
        assert r["status"] == "error"
        assert r["code"] == "unknown_template"
        assert r["http"] == 404

    def test_create_rejects_invalid_new_id(self):
        from scripts.web import api_create_edition_from_template

        for bad_id in ("BAD ID", "with space", "Caps", "trailing-", "-leading", "1starts-with-digit"):
            r = api_create_edition_from_template("children", bad_id, "Test Clone")
            assert r["status"] == "error", f"id {bad_id!r} should be rejected"
            assert r["code"] == "invalid_new_id", f"id {bad_id!r}: expected invalid_new_id, got {r['code']}"

    def test_create_rejects_missing_new_id(self):
        from scripts.web import api_create_edition_from_template

        r = api_create_edition_from_template("children", "", "Test Clone")
        assert r["status"] == "error"
        assert r["code"] == "missing_new_id"

    def test_create_rejects_missing_new_title(self):
        from scripts.web import api_create_edition_from_template

        r = api_create_edition_from_template("children", "test-clone", "")
        assert r["status"] == "error"
        assert r["code"] == "missing_new_title"

    def test_create_rejects_duplicate_id(self):
        from scripts.web import api_create_edition_from_template

        # catholic-study is a built-in edition; trying to clone
        # with that id must fail
        r = api_create_edition_from_template("children", "catholic-study", "Duplicate Test")
        assert r["status"] == "error"
        assert r["code"] == "duplicate_id"
        assert r["http"] == 409

    # --- create_from_template happy path (sandbox via tmp file) ---

    def test_create_happy_path_returns_ok(self, tmp_path):
        # Use a temp editions.yaml so we don't pollute the real one.
        # Copy the real file's structure and verify the clone lands.
        import shutil
        from pathlib import Path
        from scripts.core import edition_templates as et

        real_path = Path(__file__).resolve().parent.parent / "content" / "editions.yaml"
        tmp_editions = tmp_path / "editions.yaml"
        shutil.copy(real_path, tmp_editions)

        # Patch the module-level path + clear caches
        try:
            r = et.create_from_template(
                "children",
                new_id="test-children-clone",
                new_title="Test Children's Clone",
                editions_path=tmp_editions,
            )
        finally:
            # Always revert any cache pollution from the test
            et.load_templates.cache_clear()
            from scripts.core import config

            if hasattr(config.load_editions, "cache_clear"):
                config.load_editions.cache_clear()

        assert r["status"] == "ok", r
        assert r["edition_id"] == "test-children-clone"
        assert r["edition"]["title"] == "Test Children's Clone"
        # Verify the new edition was actually appended
        text = tmp_editions.read_text(encoding="utf-8")
        assert "test-children-clone" in text
        assert "Test Children's Clone" in text

    def test_template_does_not_carry_template_fields(self):
        # The cloned edition must NOT have template_id /
        # template_label / template_description in it — those are
        # template-only metadata.
        from scripts.core import edition_templates as et

        t = et.get_template("children")
        cloned = et._strip_template_fields(t)
        for k in ("template_id", "template_label", "template_description"):
            assert k not in cloned, f"cloned edition still has {k}"


class TestPsi7BWizardTemplateButton:
    """ψ.7-B — wizard step 1 'Start from template…' UI presence."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.wizard import WIZARD_HTML

        cls.html = WIZARD_HTML

    def test_from_template_button_present(self):
        assert 'id="from-template-btn"' in self.html

    def test_template_modal_present(self):
        assert 'id="template-modal"' in self.html
        assert 'id="template-list"' in self.html
        assert 'id="template-form"' in self.html

    def test_modal_fields_present(self):
        assert 'id="template-new-id"' in self.html
        assert 'id="template-new-title"' in self.html
        assert 'id="template-error"' in self.html

    def test_modal_handlers_present(self):
        # JS function names referenced
        for fn in (
            "openTemplatePicker",
            "closeTemplatePicker",
            "createFromTemplate",
        ):
            assert fn in self.html, f"missing JS function {fn}"

    def test_modal_calls_correct_api_routes(self):
        assert "/api/edition-templates" in self.html
        assert "/api/editions/from-template" in self.html


class TestPsi16StatusDashboardSubstitution:
    """ψ.16 — cross-link nav in /audit, /preflight, /ops, /diff,
    /apihelp is sourced from `_design.HEADER_NAV_LINKS()` at module
    load — same pattern as ψ.14 (compare/wizard/export) and ψ.15
    (customize/publisher/covers/matrix/sources).

    With ψ.16 landed, all 12 cross-linked consoles share a single
    source of truth for nav + buyer-arc polish CSS. (/index is
    intentionally exempt per §6.2 lint logic — different layout.)"""

    @classmethod
    def setup_class(cls):
        from scripts.templates.audit import AUDIT_HTML
        from scripts.templates.preflight import PREFLIGHT_HTML
        from scripts.templates.ops import OPS_HTML
        from scripts.templates.diff import DIFF_HTML
        from scripts.templates.apihelp import APIHELP_HTML
        from scripts.templates._design import (
            HEADER_NAV_LINKS,
            BUYER_ARC_POLISH_CSS,
            CONSOLES,
        )

        cls.htmls = {
            "audit": AUDIT_HTML,
            "preflight": PREFLIGHT_HTML,
            "ops": OPS_HTML,
            "diff": DIFF_HTML,
            "apihelp": APIHELP_HTML,
        }
        cls.HEADER_NAV_LINKS = HEADER_NAV_LINKS
        cls.BUYER_ARC_POLISH_CSS = BUYER_ARC_POLISH_CSS
        cls.CONSOLES = CONSOLES

    def test_marker_is_fully_replaced(self):
        for name, html in self.htmls.items():
            assert "<!-- HEADER_NAV_LINKS -->" not in html, f"{name}: HEADER_NAV_LINKS marker not substituted"

    def test_polish_css_marker_is_replaced(self):
        for name, html in self.htmls.items():
            assert "<!-- BUYER_ARC_POLISH_CSS -->" not in html, f"{name}: BUYER_ARC_POLISH_CSS marker not substituted"

    def test_current_console_marked_font_semibold(self):
        cases = {
            "audit": '<a href="/audit" class="font-semibold">',
            "preflight": '<a href="/preflight" class="font-semibold">',
            "ops": '<a href="/ops" class="font-semibold">',
            "diff": '<a href="/diff" class="font-semibold">',
            "apihelp": '<a href="/apihelp" class="font-semibold">',
        }
        for name, expected in cases.items():
            assert expected in self.htmls[name], f"{name}: missing self-link with font-semibold"

    def test_other_consoles_marked_text_blue_600(self):
        # Sample one cross-pair per console.
        cases = {
            "audit": '<a href="/sources" class="text-blue-600 hover:underline">',
            "preflight": '<a href="/customize" class="text-blue-600 hover:underline">',
            "ops": '<a href="/wizard" class="text-blue-600 hover:underline">',
            "diff": '<a href="/compare" class="text-blue-600 hover:underline">',
            "apihelp": '<a href="/matrix" class="text-blue-600 hover:underline">',
        }
        for name, expected in cases.items():
            assert expected in self.htmls[name], f"{name}: missing cross-link"

    def test_substitution_includes_all_consoles(self):
        for name, html in self.htmls.items():
            for route, _label in self.CONSOLES:
                assert f'href="{route}"' in html, f"{name}: missing href={route} after substitution"

    def test_design_module_imported(self):
        import importlib

        for name in self.htmls:
            mod = importlib.import_module(f"scripts.templates.{name}")
            assert hasattr(mod, "HEADER_NAV_LINKS"), f"{name}: HEADER_NAV_LINKS not imported"
            assert hasattr(mod, "BUYER_ARC_POLISH_CSS"), f"{name}: BUYER_ARC_POLISH_CSS not imported"


class TestPsi16StatusDashboardPolishCSS:
    """ψ.16 — BUYER_ARC_POLISH_CSS is injected into all 5 status
    dashboard consoles."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.audit import AUDIT_HTML
        from scripts.templates.preflight import PREFLIGHT_HTML
        from scripts.templates.ops import OPS_HTML
        from scripts.templates.diff import DIFF_HTML
        from scripts.templates.apihelp import APIHELP_HTML

        cls.htmls = {
            "audit": AUDIT_HTML,
            "preflight": PREFLIGHT_HTML,
            "ops": OPS_HTML,
            "diff": DIFF_HTML,
            "apihelp": APIHELP_HTML,
        }

    def test_focus_visible_outline_present(self):
        for name, html in self.htmls.items():
            assert "*:focus-visible" in html, f"{name}: missing focus-visible outline rule"

    def test_button_active_scale_feedback(self):
        for name, html in self.htmls.items():
            assert "button:active:not(:disabled)" in html, f"{name}: missing button :active feedback"
            assert "scale(0.98)" in html, f"{name}: missing button scale-down rule"

    def test_psi14_pending_pill_class(self):
        for name, html in self.htmls.items():
            assert ".psi14-pending::after" in html, f"{name}: missing .psi14-pending pill rule"

    def test_step_fade_in_keyframes(self):
        for name, html in self.htmls.items():
            assert "@keyframes psi14StepFadeIn" in html, f"{name}: missing psi14StepFadeIn keyframe"


class TestPsi16IndexEditorPolishCSS:
    """ψ.16 (2026-05-10) — BUYER_ARC_POLISH_CSS reaches the note
    editor (INDEX_HTML) too. The editor keeps its distinctive heavy
    nav (per `check_cross_link_invariant`'s `INDEX_HTML` exemption);
    only the polish CSS is added — universal UX wins (focus rings,
    transitions, button feedback) that don't impose a layout.
    """

    @classmethod
    def setup_class(cls):
        from scripts.templates.index import INDEX_HTML

        cls.html = INDEX_HTML

    def test_focus_visible_outline_present(self):
        assert "*:focus-visible" in self.html, "INDEX_HTML missing focus-visible outline rule"

    def test_button_active_scale_feedback(self):
        assert "button:active:not(:disabled)" in self.html
        assert "scale(0.98)" in self.html

    def test_psi14_pending_pill_class(self):
        assert ".psi14-pending::after" in self.html

    def test_step_fade_in_keyframes(self):
        assert "@keyframes psi14StepFadeIn" in self.html

    def test_marker_was_substituted(self):
        # The raw `<!-- BUYER_ARC_POLISH_CSS -->` marker should be
        # GONE from the rendered HTML (substituted at module load).
        # Pin so a future contributor doesn't drop the substitution
        # call and ship the literal marker to users.
        assert "<!-- BUYER_ARC_POLISH_CSS -->" not in self.html

    def test_editor_keeps_dark_nav(self):
        # Pin: INDEX_HTML keeps its bg-slate-900 brand chrome — we
        # explicitly chose NOT to convert to the light dashboard
        # header. If a future follow-on phase harmonizes the editor
        # with the design system, this test will need updating + a
        # thoughtful decision about the editor's identity.
        assert "bg-slate-900" in self.html, "INDEX_HTML lost its dark brand header"


class TestNu28CustomizeVisualSections:
    """ν.2.8 — /customize edition cards split into <section>
    boundaries: Identity & appearance, Metadata. Plus dynamic
    counts on Editions / Categories / Kinds headings (was hard-
    coded `(5)` / `(14)` / `(63)` — broke after ψ.7-A added 4
    editions)."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.customize import CUSTOMIZE_HTML

        cls.html = CUSTOMIZE_HTML

    def test_ed_section_class_in_css(self):
        # CSS rule for the new section boundary must exist.
        assert ".ed-section {" in self.html
        assert ".ed-section:first-of-type" in self.html

    def test_ed_section_label_class_in_css(self):
        assert ".ed-section-label {" in self.html

    def test_identity_section_in_renderer(self):
        # The renderEditions JS template must wrap the header row
        # in <section class="ed-section ed-identity">.
        assert "ed-section ed-identity" in self.html
        assert "Identity &amp; appearance" in self.html

    def test_metadata_section_in_renderer(self):
        assert "ed-section ed-meta" in self.html
        assert ">Metadata<" in self.html

    def test_dynamic_count_ids_present(self):
        # The hard-coded (5)/(14)/(63) counts are replaced with
        # span placeholders that JS fills in.
        assert 'id="editions-count"' in self.html
        assert 'id="categories-count"' in self.html
        assert 'id="kinds-count"' in self.html

    def test_dynamic_count_js_present(self):
        # The init() function should populate the count placeholders.
        assert "editions-count" in self.html
        assert "DATA.editions" in self.html
        assert "DATA.categories" in self.html
        assert "DATA.kinds" in self.html

    def test_old_hardcoded_counts_removed(self):
        # The literal `(5)` / `(14)` / `(63 — grouped...)` strings
        # in the section headings are gone.
        assert 'font-normal">(5)<' not in self.html
        assert 'font-normal">(14)<' not in self.html
        assert "(63 — grouped by category)" not in self.html


class TestPsi11WizardBrandingPolish:
    """ψ.11 — wizard step 2 branding form: reversibility hint + 3
    fieldset groups (Identity, Publisher, Copyright & authors) for
    field-grouping rhythm. Ω.0 pivot (2026-05-14) dropped the
    former ISBN fieldset; group count went 4 → 3."""

    @classmethod
    def setup_class(cls):
        from scripts.templates.wizard import WIZARD_HTML

        cls.html = WIZARD_HTML

    def test_reversibility_hint_present(self):
        # The emerald-tinted reversibility hint sits at the top of
        # step 2's body and reassures the user that going back
        # preserves entries.
        assert "bg-emerald-50" in self.html
        assert "survive navigation" in self.html
        assert "<strong>BUILD</strong>" in self.html

    def test_psi11_group_class_in_css(self):
        assert ".psi11-group {" in self.html
        assert ".psi11-legend {" in self.html

    def test_three_fieldset_groups_present(self):
        # All 3 group legends rendered in step 2 body post-pivot.
        for legend in ("Identity", "Publisher / imprint", "Copyright &amp; authors"):
            assert legend in self.html, f"missing legend {legend!r}"

    def test_no_isbn_fieldset_post_pivot(self):
        # Ω.0 pivot pin — ISBN fieldset + inputs must not appear.
        assert ">ISBN<" not in self.html
        assert 'id="w-isbn_epub"' not in self.html
        assert 'id="w-isbn_print"' not in self.html

    def test_branding_fields_still_present_under_fieldsets(self):
        # Post-Ω.0 the surviving input ids (6) must remain in
        # the rendered HTML — fieldset wrap is purely structural.
        for input_id in (
            "w-title",
            "w-publisher_name",
            "w-publisher_url",
            "w-copyright_year",
            "w-copyright_holder",
            "w-authors",
        ):
            assert f'id="{input_id}"' in self.html, f"missing input {input_id} after fieldset refactor"

    def test_label_for_attribute_associations(self):
        # ψ.11 added `for=` attributes on every label so screen-
        # readers correctly bind labels to inputs. Post-Ω.0 the
        # surviving input set is the 6 non-ISBN ids.
        for input_id in (
            "w-title",
            "w-publisher_name",
            "w-publisher_url",
            "w-copyright_year",
            "w-copyright_holder",
            "w-authors",
        ):
            assert f'for="{input_id}"' in self.html, f"missing label for={input_id}"


class TestPsi135DesignSystemConsolidation:
    """ψ.13.5 — all 13 design-system-consuming templates use the
    new `_design.apply_design_system(html, route)` helper instead
    of per-file two-replace blocks."""

    @classmethod
    def setup_class(cls):
        from scripts.templates._design import (
            apply_design_system,
            HEADER_NAV_LINKS,
            BUYER_ARC_POLISH_CSS,
        )

        cls.apply_design_system = staticmethod(apply_design_system)
        cls.HEADER_NAV_LINKS = HEADER_NAV_LINKS
        cls.BUYER_ARC_POLISH_CSS = BUYER_ARC_POLISH_CSS

    def test_helper_exists(self):
        from scripts.templates import _design

        assert hasattr(_design, "apply_design_system")
        assert callable(_design.apply_design_system)

    def test_helper_substitutes_header_nav_marker(self):
        html = "before\n    <!-- HEADER_NAV_LINKS -->\nafter\n"
        out = self.apply_design_system(html, "/customize")
        assert "<!-- HEADER_NAV_LINKS -->" not in out
        # The substituted nav must contain the canonical links
        assert 'href="/customize" class="font-semibold"' in out

    def test_helper_substitutes_polish_css_marker(self):
        html = "before <!-- BUYER_ARC_POLISH_CSS --> after"
        out = self.apply_design_system(html, "/customize")
        assert "<!-- BUYER_ARC_POLISH_CSS -->" not in out
        assert "focus-visible" in out

    def test_helper_is_idempotent(self):
        # Running on already-substituted HTML is a no-op.
        html = "before <!-- HEADER_NAV_LINKS --> after"
        once = self.apply_design_system(html, "/customize")
        twice = self.apply_design_system(once, "/customize")
        assert once == twice

    def test_helper_handles_html_with_no_markers(self):
        # No-marker input passes through unchanged.
        html = "<html><body>nothing here</body></html>"
        out = self.apply_design_system(html, "/customize")
        assert out == html

    def test_all_13_templates_import_helper(self):
        # Every design-system-consuming template imports
        # apply_design_system from _design.
        import importlib

        templates = (
            "compare",
            "wizard",
            "export",
            "customize",
            "publisher",
            "covers",
            "matrix",
            "sources",
            "audit",
            "preflight",
            "ops",
            "diff",
            "apihelp",
        )
        for name in templates:
            mod = importlib.import_module(f"scripts.templates.{name}")
            assert hasattr(mod, "apply_design_system"), f"{name}: doesn't import apply_design_system"

    def test_all_13_templates_have_correct_self_links(self):
        # Smoke: each rendered template's nav has its own route
        # marked font-semibold (the "you are here" indicator).
        from scripts.templates.compare import COMPARE_HTML
        from scripts.templates.wizard import WIZARD_HTML
        from scripts.templates.export import EXPORT_HTML
        from scripts.templates.customize import CUSTOMIZE_HTML
        from scripts.templates.publisher import PUBLISHER_HTML
        from scripts.templates.covers import COVERS_HTML
        from scripts.templates.matrix import MATRIX_HTML
        from scripts.templates.sources import SOURCES_HTML
        from scripts.templates.audit import AUDIT_HTML
        from scripts.templates.preflight import PREFLIGHT_HTML
        from scripts.templates.ops import OPS_HTML
        from scripts.templates.diff import DIFF_HTML
        from scripts.templates.apihelp import APIHELP_HTML

        cases = (
            (COMPARE_HTML, "/compare"),
            (WIZARD_HTML, "/wizard"),
            (EXPORT_HTML, "/export"),
            (CUSTOMIZE_HTML, "/customize"),
            (PUBLISHER_HTML, "/publisher"),
            (COVERS_HTML, "/covers"),
            (MATRIX_HTML, "/matrix"),
            (SOURCES_HTML, "/sources"),
            (AUDIT_HTML, "/audit"),
            (PREFLIGHT_HTML, "/preflight"),
            (OPS_HTML, "/ops"),
            (DIFF_HTML, "/diff"),
            (APIHELP_HTML, "/apihelp"),
        )
        for html, route in cases:
            assert f'href="{route}" class="font-semibold"' in html, f"{route}: self-link missing font-semibold marker"

    def test_all_13_templates_have_no_lingering_markers(self):
        # Every template's HEADER_NAV_LINKS + BUYER_ARC_POLISH_CSS
        # markers must be replaced post-import.
        import importlib

        templates = (
            "compare",
            "wizard",
            "export",
            "customize",
            "publisher",
            "covers",
            "matrix",
            "sources",
            "audit",
            "preflight",
            "ops",
            "diff",
            "apihelp",
        )
        for name in templates:
            mod = importlib.import_module(f"scripts.templates.{name}")
            attr = name.upper() + "_HTML"
            html = getattr(mod, attr)
            assert "<!-- HEADER_NAV_LINKS -->" not in html, f"{name}: lingering HEADER_NAV_LINKS marker"
            assert "<!-- BUYER_ARC_POLISH_CSS -->" not in html, f"{name}: lingering BUYER_ARC_POLISH_CSS marker"
