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


class TestKindleSafeCss:
    """E3013 (visible endnotes) + K-KIN-3 (seam) CSS — pure append, kindle-gated."""

    def test_appends_only_the_kindle_block(self):
        from scripts.build_edition import _KINDLE_SAFE_CSS, apply_kindle_safe_css

        base = ".notes-section, .notes-rule { display: none; }\n"
        out = apply_kindle_safe_css(base)
        assert out == base + _KINDLE_SAFE_CSS
        assert out.startswith(base)  # append-only — base rules untouched

    def test_unhides_every_text_bearing_hidden_class(self):
        from scripts.build_edition import _KINDLE_SAFE_CSS as css

        # the E3013 mass (≈486K chars in catholic-study) — both section hides
        assert ".notes-section { display: block;" in css
        assert ".verse-refs-section { display: block;" in css
        # the ~13K note-label hides (base stylesheet.css:227-233) — same selector
        # strings as the base so the artifact gate can pair override with hide
        assert '[class*="note-comm-"] > div > .note-label { display: block; }' in css
        assert ".note-label:where([data-noise])" in css
        # the .vn-sep separators become VISIBLE bullets (useful in endnote flow)
        assert ".vn-sep { display: inline; }" in css

    def test_keeps_the_bottom_notes_heading_hidden(self):
        # inject puts the hr+h3 "Notes" heading at the section BOTTOM (cosmetic
        # inversion in a visible render) — keep it hidden; ~305 chars ≪ 10K
        from scripts.build_edition import _KINDLE_SAFE_CSS as css

        assert ".notes-heading { display: none; }" in css

    def test_seam_fix_rules(self):
        # K-KIN-3: the forced singleton spine file already breaks the page on
        # every renderer — the CSS forced breaks are pure KFX double-break
        # liability; the global h1 break tears the caption band off the title.
        from scripts.build_edition import _KINDLE_SAFE_CSS as css

        assert ".book-title-page { page-break-before: auto;" in css
        assert "h1.bookpage-title { page-break-before: avoid;" in css
        assert ".bookpage-art" in css and "max-height: 12em" in css


_KINDLE_TOC_PAGE = (
    "<?xml version='1.0' encoding='utf-8'?>\n"
    '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>T</title></head><body>\n'
    '<div class="toc-wrap"><h1 class="toc-title">Contents</h1><ol class="toc-books">\n'
    '<li class="toc-book"><p class="toc-book-label"><a href="index_split_000.html#bp-00">Genesis</a></p>'
    '<ol class="toc-chapters"><li><a href="index_split_000.html#page_4">1</a></li>'
    '<li><a href="index_split_000.html#ch-b00-c18">18</a></li></ol></li>\n'
    "</ol></div>\n</body></html>"
)


class TestKindleTocRows:
    """K-KIN-2: KFX drops the li display → one pill per line. Plain inline
    anchors in a <p> are inline text in every renderer including KFX."""

    def test_rewrites_pill_ols_to_plain_rows(self, tmp_path):
        from scripts.build_edition import apply_kindle_toc_rows

        (tmp_path / "index_split_000.html").write_text(_KINDLE_TOC_PAGE, encoding="utf-8")
        stats = apply_kindle_toc_rows(tmp_path, {"target_reader": "kindle"})
        out = (tmp_path / "index_split_000.html").read_text(encoding="utf-8")
        assert stats["toc_rows_rewritten"] == 1
        assert 'class="toc-chapters"' not in out
        assert '<p class="toc-chapter-row">' in out
        # every anchor survives verbatim (mixed #page_N / #ch-bXX-cN hrefs)
        assert '<a href="index_split_000.html#page_4">1</a>' in out
        assert '<a href="index_split_000.html#ch-b00-c18">18</a>' in out
        # the book label row is untouched
        assert '<p class="toc-book-label">' in out

    def test_noop_for_non_kindle_targets(self, tmp_path):
        from scripts.build_edition import apply_kindle_toc_rows

        (tmp_path / "index_split_000.html").write_text(_KINDLE_TOC_PAGE, encoding="utf-8")
        stats = apply_kindle_toc_rows(tmp_path, {})
        out = (tmp_path / "index_split_000.html").read_text(encoding="utf-8")
        assert stats["toc_rows_rewritten"] == 0
        assert out == _KINDLE_TOC_PAGE  # byte-identical

    def test_idempotent(self, tmp_path):
        from scripts.build_edition import apply_kindle_toc_rows

        (tmp_path / "index_split_000.html").write_text(_KINDLE_TOC_PAGE, encoding="utf-8")
        apply_kindle_toc_rows(tmp_path, {"target_reader": "kindle"})
        first = (tmp_path / "index_split_000.html").read_text(encoding="utf-8")
        apply_kindle_toc_rows(tmp_path, {"target_reader": "kindle"})
        assert (tmp_path / "index_split_000.html").read_text(encoding="utf-8") == first

    def test_collapsible_details_shape_also_rewrites(self, tmp_path):
        # /customize can set collapsible=true + kindle; the ol inside <details>
        # must still become a row (the <details> wrapper itself is harmless —
        # Kindle converts it to a permanently-expanded block, K-KIN-4)
        from scripts.build_edition import apply_kindle_toc_rows

        page = _KINDLE_TOC_PAGE.replace(
            '<p class="toc-book-label"><a href="index_split_000.html#bp-00">Genesis</a></p>',
            '<details><summary><a href="index_split_000.html#bp-00">Genesis</a></summary>',
        ).replace("</ol></li>", "</ol></details></li>")
        (tmp_path / "index_split_000.html").write_text(page, encoding="utf-8")
        stats = apply_kindle_toc_rows(tmp_path, {"target_reader": "kindle"})
        assert stats["toc_rows_rewritten"] == 1
        assert 'class="toc-chapters"' not in (tmp_path / "index_split_000.html").read_text(encoding="utf-8")


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


class TestKindleUnhideAttrs:
    """K-KIN forensics (2026-06-11, the 2nd ~50-min Send-to-Kindle failure):
    the shipped kindle artifact still carried `hidden=""` on all 284 note
    wrappers (24.8M chars under the UA [hidden] rule) and 3 odd-template
    pieces wrap popups in `<section class="verse-refs-section" ... hidden="">`.
    The variant CSS overrides both via author-display:block — but Amazon's
    opaque hidden-text counter may not honor the full cascade. Belt-and-
    braces: the kindle variant physically STRIPS the attribute from the
    footnote wrappers, so no counter model can see hidden text."""

    PIECE = (
        "<html><body><p>scripture</p>"
        '<aside class="notes-section" epub:type="footnotes" hidden="">\n'
        '<aside class="verse-notes" id="vnotes-gen-1-1" epub:type="footnote">n</aside></aside>'
        '<section class="verse-refs-section" epub:type="footnotes" hidden="">'
        '<aside class="vnote" id="vnote-gen-1-1" epub:type="footnote">v</aside></section>'
        '<p hidden="">unrelated hidden element stays</p>'
        "</body></html>"
    )

    def _tree(self, tmp_path):
        tmp = tmp_path / "build"
        tmp.mkdir()
        (tmp / "index_split_000.html").write_text(self.PIECE, encoding="utf-8")
        return tmp

    def test_strips_hidden_from_footnote_wrappers_only(self, tmp_path):
        from scripts.build_edition import apply_kindle_unhide

        tmp = self._tree(tmp_path)
        stats = apply_kindle_unhide(tmp, {"id": "x", "target_reader": "kindle"})
        out = (tmp / "index_split_000.html").read_text(encoding="utf-8")
        assert '<aside class="notes-section" epub:type="footnotes">' in out
        assert '<section class="verse-refs-section" epub:type="footnotes">' in out
        # non-footnote hidden elements are NOT the kindle problem — untouched
        assert '<p hidden="">' in out
        assert stats["hidden_attrs_stripped"] == 2

    def test_noop_for_non_kindle_targets(self, tmp_path):
        from scripts.build_edition import apply_kindle_unhide

        tmp = self._tree(tmp_path)
        before = (tmp / "index_split_000.html").read_text(encoding="utf-8")
        stats = apply_kindle_unhide(tmp, {"id": "x"})
        assert (tmp / "index_split_000.html").read_text(encoding="utf-8") == before
        assert stats["hidden_attrs_stripped"] == 0

    def test_idempotent(self, tmp_path):
        from scripts.build_edition import apply_kindle_unhide

        tmp = self._tree(tmp_path)
        ed = {"id": "x", "target_reader": "kindle"}
        apply_kindle_unhide(tmp, ed)
        once = (tmp / "index_split_000.html").read_text(encoding="utf-8")
        apply_kindle_unhide(tmp, ed)
        assert (tmp / "index_split_000.html").read_text(encoding="utf-8") == once
