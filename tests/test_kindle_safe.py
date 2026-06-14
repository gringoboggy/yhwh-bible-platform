"""kindle_safe variant (board turn-69 ①, Kindle E999/E3013 arc).

A ``target_reader: kindle`` edition builds a Send-to-Kindle-survivable EPUB:
visible endnotes (no >10K chars under display:none — Amazon's documented
hard-fail), plain ToC chapter rows (KFX linearizes the pills), no book-seam
shatter (KFX double-break), single dc:language (WIN's half, already shipped).
Everything is gated on ONE resolver; unset ⇒ byte-identical builds (RULES 7.2).
Evidence: docs/superpowers/notes/2026-06-10-kindle-e999-investigation.md.
"""

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class TestTargetReaderResolver:
    """The one resolver both matrix and build call (MATRIX_MAP finding #3)."""

    def test_target_readers_constant_has_five_values(self):
        from scripts.build_edition import TARGET_READERS

        assert TARGET_READERS == ("everywhere", "eink", "tablet", "computer", "kindle")

    def test_resolver_defaults_unset_to_everywhere(self):
        from scripts.build_edition import resolve_target_reader

        assert resolve_target_reader({}) == "everywhere"
        assert resolve_target_reader({"target_reader": ""}) == "everywhere"
        assert resolve_target_reader({"target_reader": "  "}) == "everywhere"

    def test_resolver_passes_valid_values_and_defuses_unknown(self):
        from scripts.build_edition import resolve_target_reader

        assert resolve_target_reader({"target_reader": "kindle"}) == "kindle"
        assert resolve_target_reader({"target_reader": "eink"}) == "eink"
        # an unknown on-disk value must never activate a variant
        assert resolve_target_reader({"target_reader": "smartfridge"}) == "everywhere"

    def test_is_kindle_target(self):
        from scripts.build_edition import is_kindle_target

        assert is_kindle_target({"target_reader": "kindle"}) is True
        assert is_kindle_target({}) is False
        assert is_kindle_target({"target_reader": "eink"}) is False

    def test_api_validator_imports_the_shared_constant(self):
        # one-resolver rule: no inline enum copy in the API layer
        src = (REPO / "scripts" / "api" / "editions.py").read_text(encoding="utf-8")
        assert 'valid_targets = {"everywhere", "eink", "tablet", "computer"}' not in src
        assert "TARGET_READERS" in src

    def test_api_accepts_kindle(self):
        from scripts.api.editions import api_save_edition_meta
        from scripts.core import config

        yaml_path = REPO / "content" / "editions.yaml"
        original = yaml_path.read_bytes()
        try:
            r = api_save_edition_meta("catholic-study", {"target_reader": "kindle"})
            assert "error" not in r, r
            assert 'target_reader: "kindle"' in yaml_path.read_text(encoding="utf-8")
        finally:
            yaml_path.write_bytes(original)
            config.load_editions.cache_clear()

    def test_customize_surface_routes_through_the_resolver(self):
        src = (REPO / "scripts" / "web_editions.py").read_text(encoding="utf-8")
        assert 'e.get("target_reader", "everywhere")' not in src
        assert "resolve_target_reader" in src


class TestKindleWizardSurfaces:
    """The wizard + customize offer the kindle target with Send-to-Kindle copy."""

    def test_wizard_has_kindle_card_naming_send_to_kindle(self):
        from scripts.templates.wizard import WIZARD_HTML

        assert 'data-target="kindle"' in WIZARD_HTML
        assert "Send to Kindle" in WIZARD_HTML

    def test_target_caps_has_kindle_entry_gated_off_expandable(self):
        from scripts.templates.wizard import WIZARD_HTML

        caps = WIZARD_HTML[WIZARD_HTML.index("const TARGET_CAPS") : WIZARD_HTML.index("function applyTargetGating")]
        assert "kindle:" in caps
        assert caps.count("toc_expandable: false") == 4  # everywhere/eink/computer/kindle
        assert caps.count("toc_expandable: true") == 1  # tablet only, unchanged

    def test_customize_select_offers_kindle(self):
        from scripts.templates.customize import CUSTOMIZE_HTML

        assert "'kindle'" in CUSTOMIZE_HTML and 'value="kindle"' in CUSTOMIZE_HTML


class TestOpfTargetStamp:
    """patch_opf stamps the resolved target so the stdlib-only artifact
    verifier can run kindle checks skew-free (editions.yaml is mutable
    post-build; the OPF is not). Additive ONLY when target_reader is set —
    unset editions stay byte-identical."""

    _BASE_OPF = (
        "<?xml version='1.0'?>\n"
        '<package version="3.0">\n'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        '<dc:title>X</dc:title><dc:creator id="creator">PD</dc:creator>\n'
        '<meta refines="#creator" property="role" scheme="marc:relators">aut</meta>\n'
        '<meta refines="#creator" property="file-as">PD</meta>\n'
        '<dc:contributor id="contributor">calibre</dc:contributor>\n'
        "<dc:date>2020-01-01</dc:date><dc:language>en</dc:language>\n"
        "</metadata></package>"
    )

    def test_no_stamp_when_target_unset(self):
        from scripts.build_edition import patch_opf

        opf = patch_opf(self._BASE_OPF, {"id": "catholic-study", "title": "X"}, "v1")
        assert "yhwh:target-reader" not in opf

    def test_stamp_present_when_kindle(self):
        from scripts.build_edition import patch_opf

        opf = patch_opf(self._BASE_OPF, {"id": "catholic-study", "title": "X", "target_reader": "kindle"}, "v1")
        assert '<meta name="yhwh:target-reader" content="kindle"/>' in opf

    def test_stamp_uses_the_resolver_not_the_raw_value(self):
        from scripts.build_edition import patch_opf

        # a stale unknown value resolves to everywhere — and everywhere is the
        # default, so an unknown value stamps NOTHING (defused, not propagated)
        opf = patch_opf(self._BASE_OPF, {"id": "catholic-study", "title": "X", "target_reader": "smartfridge"}, "v1")
        assert "yhwh:target-reader" not in opf


class TestKindleKeepsHiddenFootnoteAttrs:
    """The proven june10recipe.epub (Send-to-Kindle PASS) KEPT all 406 hidden=""
    footnote asides and delivered — Amazon's E3013/E999 scanner counts CSS
    display:none, NOT the HTML hidden attribute, and Kindle's native footnote
    popups USE those hidden asides. So `apply_kindle_unhide` was removed
    2026-06-14; a kindle build must NOT strip them. Guard: the function is gone."""

    def test_apply_kindle_unhide_is_removed(self):
        import scripts.build_edition as be

        assert not hasattr(be, "apply_kindle_unhide")
        assert not hasattr(be, "apply_kindle_safe_css")
        assert not hasattr(be, "apply_kindle_toc_rows")
