"""Note-presentation rehaul — build-time, lossless, option-gated cascade.

Tests the staged transforms that run inside ``apply_badge_markers`` (badge mode
only), per ``docs/superpowers/specs/2026-06-08-note-presentation-rehaul-design.md``
(re-verified against the live corpus 2026-06-08; the spec's S3a comma-split and
the source-key boilerplate-strip were corrected before implementation).

S1 = attribution/label de-dup (this file's first class). The pure helpers are
unit-tested here; the in-build behaviour is exercised against a real gen-1 temp
tree (the same fixture pattern as ``test_marker_style.TestApplyBadgeMarkersUnit``).
"""

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


class TestNoteRehaulS1Helpers:
    """Pure helpers for S1 (attribution/label de-dup). No HTML build needed."""

    def test_normalize_strips_one_trailing_dot_and_casefolds(self):
        from scripts.build_edition import _normalize_label_text

        assert _normalize_label_text("Hebrew.") == "hebrew"
        assert _normalize_label_text("Ethiopian") == "ethiopian"
        assert _normalize_label_text("  Cite. ") == "cite"
        # only ONE trailing dot is stripped (future-proof against an ellipsis label)
        assert _normalize_label_text("A.B.") == "a.b"
        assert _normalize_label_text("") == ""
        assert _normalize_label_text(None) == ""

    def test_self_attributing_marker_is_exact_and_tolerates_leading_ws(self):
        from scripts.build_edition import _is_self_attributing_comm_ethiopian

        body = (
            '<aside class="note-comm-ethiopian"><strong>Cyril of Alexandria</strong> '
            "<em>Commentary on John</em> <small>(430)</small><p>...</p></aside>"
        )
        assert _is_self_attributing_comm_ethiopian(body) is True
        assert _is_self_attributing_comm_ethiopian("   \n" + body) is True
        # the 10 plain User-authored comm-ethiopian bodies are NOT self-attributing
        assert _is_self_attributing_comm_ethiopian("<strong>Queen of Sheba.</strong> south Arabia...") is False
        assert _is_self_attributing_comm_ethiopian("<p>plain note</p>") is False
        assert _is_self_attributing_comm_ethiopian("") is False

    def test_strip_redundant_label_when_equals_kind_default(self):
        from scripts.build_edition import _strip_redundant_note_label

        defaults = {"lang-hebrew": "hebrew", "comm-ethiopian": "ethiopian"}
        # trigger (a): the RENDERED label merely repeats the kind default -> stripped
        row = (
            '<div class="vn-item note-lang-hebrew"><p>'
            '<a class="note-sym" href="legend.xhtml#legend-lang">⌘</a> '
            '<span class="note-label">Hebrew.</span> <em>בָּרָא</em> to create</p></div>'
        )
        out, changed = _strip_redundant_note_label(row, "lang-hebrew", defaults)
        assert changed is True and 'class="note-label"' not in out and "to create" in out
        # a label that does NOT equal the kind default (no self-attribution) is kept
        row_keep = row.replace(">Hebrew.<", ">Athanasius of Alexandria (350).<")
        out2, changed2 = _strip_redundant_note_label(row_keep, "comm-ethiopian", defaults)
        assert changed2 is False and 'class="note-label"' in out2

    def test_strip_redundant_label_when_body_self_attributes(self):
        from scripts.build_edition import _strip_redundant_note_label

        defaults = {"comm-ethiopian": "ethiopian"}
        # trigger (b): the father label differs from the kind default, BUT the body's own
        # inner byline already names the source -> the label restatement is redundant
        row = (
            '<div class="vn-item note-comm-ethiopian"><p>'
            '<a class="note-sym" href="legend.xhtml#legend-comm">◇</a> '
            '<span class="note-label">Cyril of Alexandria (430).</span> '
            '<aside class="note-comm-ethiopian"><strong>Cyril of Alexandria</strong> '
            "<em>w</em> <small>(430)</small><p>...</p></aside></p></div>"
        )
        out, changed = _strip_redundant_note_label(row, "comm-ethiopian", defaults)
        assert changed is True and 'class="note-label"' not in out
        # the body's OWN inner byline is untouched
        assert '<aside class="note-comm-ethiopian">' in out and "Cyril of Alexandria</strong>" in out

    def test_strip_redundant_label_never_fires_on_empty_default(self):
        from scripts.build_edition import _strip_redundant_note_label

        row = '<div class="vn-item note-weird"><p><span class="note-label">Anything</span> body</p></div>'
        # guard: an empty/missing kind default (and no self-attribution) must not strip
        assert _strip_redundant_note_label(row, "weird-kind", {"weird-kind": ""})[1] is False
        assert _strip_redundant_note_label(row, "unregistered-kind", {})[1] is False
        # a row with no label span is a no-op
        assert _strip_redundant_note_label('<div class="vn-item note-x">no label</div>', "x", {"x": "y"})[1] is False

    def test_strip_note_label_span_removes_only_the_first_label_span(self):
        from scripts.build_edition import _strip_note_label_span

        row = (
            '<div class="vn-item note-lang-hebrew"><p>'
            '<a class="note-sym" href="legend.xhtml#legend-lang">⌘</a> '
            '<span class="note-label">Hebrew.</span> <em>בָּרָא</em> to create</p></div>'
        )
        out, changed = _strip_note_label_span(row)
        assert changed is True
        assert 'class="note-label"' not in out
        # nothing else is touched
        assert "to create" in out and "⌘" in out and "בָּרָא" in out
        # a row with no label span is returned unchanged
        plain = '<div class="vn-item note-x">no label here</div>'
        out2, changed2 = _strip_note_label_span(plain)
        assert changed2 is False and out2 == plain

    def test_body_fingerprint_is_text_invariant(self):
        from scripts.build_edition import _body_fingerprint

        a = _body_fingerprint("<p>In the <em>beginning</em> God created.</p>")
        # same words, different tags / whitespace / case -> same fingerprint
        b = _body_fingerprint("<div>in   the beginning\n god  created.</div>")
        assert a == b
        # a genuinely different point -> different fingerprint
        assert a != _body_fingerprint("<p>A different point entirely.</p>")

    def test_kind_default_labels_cover_the_real_corpus(self):
        from scripts.build_edition import _kind_default_labels

        d = _kind_default_labels()
        assert d["lang-hebrew"] == "hebrew"
        # every registered kind has a non-empty NORMALISED default (no mis-fire path —
        # verified 0/72 kinds have an empty default on the live corpus, 2026-06-08)
        assert d and all(v for v in d.values())


class TestNoteRehaulS1InBuild:
    """S1 inside ``apply_badge_markers`` against a real gen-1 temp tree (the same
    fixture pattern as test_marker_style). Flag absent ⇒ byte-identical to today."""

    def _gen_tmp(self, base):
        from scripts.core import config as _c

        book = _c.get_book("gen")
        epub = REPO / "epub_working"
        base.mkdir(parents=True, exist_ok=True)
        for f in book["files"]:
            (base / f).write_text((epub / f).read_text(encoding="utf-8"), encoding="utf-8")
        return base, book

    def _gen1_text(self, tmp, book):
        for f in book["files"]:
            t = (tmp / f).read_text(encoding="utf-8")
            if 'id="vbadge-gen-1-1"' in t:
                return t
        raise AssertionError("gen 1 badge file not found")

    def _badge_counts(self, tmp, book):
        import re as _re

        counts = {}
        for f in book["files"]:
            text = (tmp / f).read_text(encoding="utf-8")
            for vv, cnt in _re.findall(r'id="vbadge-gen-1-(\d+)"[^>]*title="(\d+) notes?"', text):
                counts[vv] = int(cnt)
        return counts

    def test_flag_off_keeps_note_labels_and_suppresses_nothing(self, tmp_path):
        from scripts.build_edition import apply_badge_markers

        tmp, book = self._gen_tmp(tmp_path / "off")
        stats = apply_badge_markers(tmp, {"id": "x", "marker_style": "badge"})
        # §6.5: an unset field changes nothing — labels stay, suppression count is 0
        assert stats.get("s1_labels_suppressed", 0) == 0
        assert 'class="note-label"' in self._gen1_text(tmp, book)

    def test_flag_on_suppresses_kind_default_labels(self, tmp_path):
        from scripts.build_edition import apply_badge_markers

        tmp, book = self._gen_tmp(tmp_path / "on")
        stats = apply_badge_markers(tmp, {"id": "x", "marker_style": "badge", "note_attribution_dedup": True})
        # gen 1 carries thousands of lang-hebrew ("Hebrew.") + xref ("Cite.") leaves
        # whose label equals the kind default -> suppressed
        assert stats["s1_labels_suppressed"] > 0
        text = self._gen1_text(tmp, book)
        # the redundant kind-default label no longer prints (the ⌘ legend glyph + the
        # Hebrew-word body remain)
        assert '<span class="note-label">Hebrew.</span>' not in text

    def test_flag_on_conserves_every_badge_count(self, tmp_path):
        # S1 is lossless: it relocates/removes a label, never a row. The per-verse
        # badge count is IDENTICAL with the flag on vs off.
        from scripts.build_edition import apply_badge_markers

        off, book = self._gen_tmp(tmp_path / "coff")
        apply_badge_markers(off, {"id": "x", "marker_style": "badge"})
        on, _ = self._gen_tmp(tmp_path / "con")
        apply_badge_markers(on, {"id": "x", "marker_style": "badge", "note_attribution_dedup": True})

        counts_off = self._badge_counts(off, book)
        counts_on = self._badge_counts(on, book)
        assert counts_off, "fixture produced no gen-1 badges"
        assert counts_off == counts_on, "S1 changed a badge count — it dropped or added a row"


class TestNoteRehaulS1Wiring:
    """The ``note_attribution_dedup`` builder option is plumbed exactly like the
    shipped ``verse_popups`` bool (RULES §9): customize-data exposure, a /customize
    checkbox, and EDITABLE + EDITABLE_BOOL (NOT EDITABLE_TEXT) membership."""

    def test_customize_data_exposes_the_field_defaulting_false(self):
        from scripts.web import api_customize_data

        eds = {e["id"]: e for e in api_customize_data()["editions"]}
        # an edition that doesn't pin it surfaces the code default (False) — §6.5
        assert eds["catholic-study"].get("note_attribution_dedup") is False

    def test_customize_template_has_the_checkbox(self):
        src = (REPO / "scripts" / "templates" / "customize.py").read_text(encoding="utf-8")
        assert 'data-field="note_attribution_dedup"' in src

    def test_field_is_an_editable_bool_not_text(self):
        src = (REPO / "scripts" / "api" / "editions.py").read_text(encoding="utf-8")
        # present in BOTH the preview EDITABLE set and the save EDITABLE_BOOL set
        # (mirrors verse_popups); the generic bool-save path then handles it.
        assert src.count('"note_attribution_dedup"') >= 2
        # NOT in EDITABLE_TEXT — that would coerce the bool to a string
        text_block = src.split("EDITABLE_TEXT = {")[1].split("}")[0]
        assert '"note_attribution_dedup"' not in text_block
