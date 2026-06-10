"""K-R2 reader targeting (user-directed 2026-06-09).

The wizard asks WHERE the EPUB will be read as the first real choice (step 1) and
gates optional features the chosen target can't render (grayed + reason). The pick
persists as the edition's ``target_reader``; the one gated feature so far — the
expandable Contents page — maps to ``reader_toc_collapsible``, which is now a STRICT
opt-in (`=== true` keeps the base ToC's ``<details>``; anything else builds the flat
always-visible-pills form every reader can use — the beta-3 (b) shipped default).
"""

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

_TOC_PAGE = (
    "<?xml version='1.0' encoding='utf-8'?>\n"
    '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>T</title></head><body>\n'
    '<div class="toc-wrap"><h1 class="toc-title">Contents</h1><ol class="toc-books">\n'
    '<li class="toc-book"><details><summary><a href="index_split_000.html#bp-00">Genesis</a></summary>'
    '<ol class="toc-chapters"><li><a href="index_split_000.html#page_4">1</a></li></ol></details></li>\n'
    "</ol></div>\n</body></html>"
)


class TestWizardReaderTargetStep:
    """Step 1 leads with the reader-target picker; later steps gray gated controls."""

    def test_wizard_has_target_picker_with_all_five_targets(self):
        from scripts.templates.wizard import WIZARD_HTML

        assert "Where will you read it?" in WIZARD_HTML
        for target in ("everywhere", "eink", "tablet", "computer", "kindle"):
            assert f'data-target="{target}"' in WIZARD_HTML, f"target card {target!r} missing"
        # default pre-pick = the safest build
        assert 'target-card picked" data-target="everywhere"' in WIZARD_HTML

    def test_target_picker_renders_before_the_profile_cards(self):
        from scripts.templates.wizard import WIZARD_HTML

        assert WIZARD_HTML.index("Where will you read it?") < WIZARD_HTML.index('id="start-cards"'), (
            "the reader target must be one of the FIRST choices (before the profile pick)"
        )

    def test_capability_map_gates_expandable_toc_to_tablet_only(self):
        from scripts.templates.wizard import WIZARD_HTML

        assert "const TARGET_CAPS" in WIZARD_HTML
        # tablet is the only target offering the expandable Contents (count inside
        # the capability map — STATE carries its own toc_expandable default)
        caps = WIZARD_HTML[WIZARD_HTML.index("const TARGET_CAPS") : WIZARD_HTML.index("function applyTargetGating")]
        assert caps.count("toc_expandable: true") == 1
        assert caps.count("toc_expandable: false") == 4  # everywhere/eink/computer/kindle

    def test_gating_disables_and_explains(self):
        from scripts.templates.wizard import WIZARD_HTML

        assert "function applyTargetGating()" in WIZARD_HTML
        # the gated control is disabled + grayed and the REASON is shown inline
        assert "box.disabled = true" in WIZARD_HTML
        assert "gate_reason" in WIZARD_HTML
        assert 'id="w-toc-expandable"' in WIZARD_HTML
        assert 'id="toc-expand-hint"' in WIZARD_HTML

    def test_state_defaults(self):
        from scripts.templates.wizard import WIZARD_HTML

        assert "target: 'everywhere'" in WIZARD_HTML
        assert "toc_expandable: false" in WIZARD_HTML

    def test_build_payload_carries_target_and_collapsible(self):
        from scripts.templates.wizard import WIZARD_HTML

        assert "target_reader: STATE.target" in WIZARD_HTML
        assert "reader_toc_collapsible: !!STATE.toc_expandable" in WIZARD_HTML

    def test_review_shows_made_for_card(self):
        from scripts.templates.wizard import WIZARD_HTML

        assert "Made for" in WIZARD_HTML


class TestTargetReaderField:
    """target_reader flows save → schema → customize surface."""

    def test_api_accepts_target_reader_and_validates_values(self):
        from scripts.api.editions import api_save_edition_meta

        bad = api_save_edition_meta("ethiopian-tewahedo", {"target_reader": "smartfridge"})
        assert "error" in bad and "target_reader" in bad["error"]

    def test_save_target_reader_does_not_clobber_chapter_number_format(self):
        """round-7 regression pin: the target_reader branch used to assign the
        normalized value to payload["chapter_number_format"] (copy-paste slip)
        — a wizard reader-target save CLOBBERED the chapter-number format with
        "eink"/"tablet"/…, sidestepping that field's own validation. Saves
        against the REAL editions.yaml, restored BYTE-EXACTLY in finally."""
        from scripts.api.editions import api_save_edition_meta
        from scripts.core import config

        yaml_path = REPO / "content" / "editions.yaml"
        original = yaml_path.read_bytes()
        try:
            r = api_save_edition_meta("catholic-study", {"target_reader": "eink"})
            assert "error" not in r, r
            text = yaml_path.read_text(encoding="utf-8")
            assert 'chapter_number_format: "eink"' not in text, "reader-target save clobbered chapter_number_format"
            assert 'target_reader: "eink"' in text
        finally:
            yaml_path.write_bytes(original)
            config.load_editions.cache_clear()

    def test_schema_has_target_reader_fieldspec(self):
        src = (REPO / "scripts" / "validate_schemas.py").read_text(encoding="utf-8")
        assert 'FieldSpec("target_reader", type=str, required=False)' in src

    def test_customize_data_surfaces_reader_fields(self):
        from scripts.web_editions import api_customize_data

        ed = api_customize_data()["editions"][0]
        assert ed.get("target_reader", None) is not None
        assert "reader_toc_collapsible" in ed
        assert "reader_toc_default_open" in ed
        assert "book_toc_ornament" in ed

    def test_customize_template_has_target_select_and_honest_checkbox(self):
        from scripts.templates.customize import CUSTOMIZE_HTML

        assert 'data-field="target_reader"' in CUSTOMIZE_HTML
        # the checkbox reflects ONLY an explicit true (the old `!== false` rendered
        # the missing field as checked while every edition ships flat)
        assert "e.reader_toc_collapsible === true" in CUSTOMIZE_HTML
        assert "e.reader_toc_collapsible !== false" not in CUSTOMIZE_HTML


class TestExpandableTocStrictOptIn:
    """reader_toc_collapsible is a strict opt-in: only `true` keeps <details>."""

    def test_unset_defaults_to_flat_pills_kept(self, tmp_path):
        from scripts.build_edition import apply_reader_toc_transforms

        (tmp_path / "index_split_000.html").write_text(_TOC_PAGE, encoding="utf-8")
        apply_reader_toc_transforms(tmp_path, {})
        out = (tmp_path / "index_split_000.html").read_text(encoding="utf-8")
        assert "<details" not in out, "an edition without the opt-in builds the flat form"
        assert 'class="toc-chapters"' in out, "chapter pills stay visible"

    def test_explicit_true_wins_over_legacy_books_only(self, tmp_path):
        # the old coupling silently overrode the /customize checkbox on every
        # edition (all ship reader_toc_books_only: true) — an explicit opt-in
        # must win over the vestigial flag.
        from scripts.build_edition import apply_reader_toc_transforms

        (tmp_path / "index_split_000.html").write_text(_TOC_PAGE, encoding="utf-8")
        apply_reader_toc_transforms(tmp_path, {"reader_toc_collapsible": True, "reader_toc_books_only": True})
        out = (tmp_path / "index_split_000.html").read_text(encoding="utf-8")
        assert "<details" in out, "explicit opt-in keeps the expandable Contents"
