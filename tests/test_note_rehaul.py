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


# ======================================================================
# S2 — group by CATEGORY -> SOURCE -> emit the cascade markup.
# Decision (2026-06-09, after the drift investigation): the source byline
# is sourced by a BUILD-TIME LIVE attribution lookup keyed by note id, NOT
# a base re-bake (drift is kind=0 / ids 100% stable -> live attribution is
# base-consistent; the re-bake path is HIGH-risk + has no clean entrypoint).
# ======================================================================


class TestNoteRehaulS2SourceKey:
    """``source_key`` (grouping) + ``source_display`` (byline) — the spec §3
    S1/S2 attribution canonicalisation, calibrated against the real corpus
    forms (Strong's-dictionary, bare Strong's, Nave/Easton/Torrey, TSK)."""

    def test_strong_dictionary_variants_collapse_to_one_key(self):
        from scripts.build_edition import _source_display, _source_key

        a = "Strong's H1254, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD."
        b = "Strong's H136, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD."
        # the per-instance Strong's number is stripped -> both group as ONE source
        assert _source_key(a) == _source_key(b)
        # the display names the dictionary once, number + PD boilerplate removed
        assert _source_display(a) == "A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894)"

    def test_tsk_license_tail_is_loop_stripped(self):
        from scripts.build_edition import _source_display

        tsk = "Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0."
        # both ". PD." AND ". Digital edition …, CC-BY 4.0." removed (loop-until-stable)
        assert _source_display(tsk) == "Treasury of Scripture Knowledge (1830s)"

    def test_public_domain_sources_strip_to_work_author_year(self):
        from scripts.build_edition import _source_display

        assert (
            _source_display("Nave's Topical Bible, Orville J. Nave (1896). Public domain.")
            == "Nave's Topical Bible, Orville J. Nave (1896)"
        )
        assert (
            _source_display("Easton's Illustrated Bible Dictionary, M. G. Easton (1897). Public domain.")
            == "Easton's Illustrated Bible Dictionary, M. G. Easton (1897)"
        )
        assert (
            _source_display("Torrey's New Topical Textbook, R.A. Torrey (1897). Public domain.")
            == "Torrey's New Topical Textbook, R.A. Torrey (1897)"
        )

    def test_bare_strong_with_only_pd_falls_back_to_strongs(self):
        from scripts.build_edition import _source_display, _source_key

        # "Strong's H7779 (PD)" has no dictionary name; stripping the locator + (PD)
        # leaves nothing -> a sensible "Strong's" byline rather than the unattributed bucket
        assert _source_display("Strong's H7779 (PD)") == "Strong's"
        assert _source_key("Strong's H7779 (PD)") == "strong's"

    def test_unrelated_sources_do_not_share_a_key(self):
        from scripts.build_edition import _source_key

        keys = {
            _source_key("Nave's Topical Bible, Orville J. Nave (1896). Public domain."),
            _source_key("Easton's Illustrated Bible Dictionary, M. G. Easton (1897). Public domain."),
            _source_key("Torrey's New Topical Textbook, R.A. Torrey (1897). Public domain."),
            _source_key(
                "Strong's H1254, A Concise Dictionary of the Words in the Hebrew Bible, James Strong (1894). PD."
            ),
            _source_key("Treasury of Scripture Knowledge (1830s). PD. Digital edition by openbible.info, CC-BY 4.0."),
        }
        # five distinct sources -> five distinct keys (no over-merge)
        assert len(keys) == 5

    def test_empty_or_none_attribution_is_the_unattributed_bucket(self):
        from scripts.build_edition import _source_display, _source_key

        for empty in (None, "", "   "):
            assert _source_key(empty) == ""
            assert _source_display(empty) == ""

    def test_source_key_over_the_real_corpus_does_not_over_collapse(self):
        # Run source_key over every distinct live attribution: it must never raise,
        # must keep many distinct sources distinct (no aggressive regex that melts
        # everything into one stub), and must perform the intended Strong's collapse.
        from scripts.build_edition import _source_key
        from scripts.core import config as _c
        from scripts.core.notes_io import load_notes

        notes_dir = REPO / "content" / "notes"
        distinct_attrs = set()
        for book in _c.load_books():
            p = notes_dir / f"{book['code']}.py"
            if not p.is_file():
                continue
            for tup in load_notes(p) or []:
                a = _c.note_attribution(tup)
                if a:
                    distinct_attrs.add(a)
        assert len(distinct_attrs) > 200, "fixture sanity: expected a rich attribution corpus"
        keys = {_source_key(a) for a in distinct_attrs}
        # not melted to a handful, not 1:1-with-no-collapse either
        assert len(keys) > 100
        # the intended Strong's-dictionary collapse really happens (many distinct
        # numbered strings -> far fewer keys)
        strong_attrs = {a for a in distinct_attrs if a.startswith("Strong's H") and "Concise Dictionary" in a}
        if strong_attrs:
            assert len({_source_key(a) for a in strong_attrs}) == 1


class TestNoteRehaulS2Cascade:
    """``_emit_cascade_sections`` — the pure verse->category->source->note
    emission (spec §2). No HTML build needed."""

    def _rows(self):
        # two categories (hist rank 0, lang rank 4), lang carries two sources with
        # an interleaved repeat of the first source (must regroup, not duplicate).
        return [
            {
                "cat": "hist",
                "source_key": "easton",
                "source_display": "Easton's (1897)",
                "suppress_byline": False,
                "row": '<div class="vn-item note-hist-x">H1</div>',
            },
            {
                "cat": "lang",
                "source_key": "strongs",
                "source_display": "Strong's Dictionary (1894)",
                "suppress_byline": False,
                "row": '<div class="vn-item note-lang-hebrew">L1</div>',
            },
            {
                "cat": "lang",
                "source_key": "paraphrase",
                "source_display": "",
                "suppress_byline": False,
                "row": '<div class="vn-item note-lang-hebrew">L2</div>',
            },
            {
                "cat": "lang",
                "source_key": "strongs",
                "source_display": "Strong's Dictionary (1894)",
                "suppress_byline": False,
                "row": '<div class="vn-item note-lang-hebrew">L3</div>',
            },
        ]

    def _meta(self):
        return {"hist": ("⌂", "Historical / Cultural"), "lang": ("⌘", "Linguistic")}

    def test_one_group_per_category_with_label_text(self):
        from scripts.build_edition import _emit_cascade_sections

        out = _emit_cascade_sections(self._rows(), self._meta())
        assert out.count('<section class="vn-group note-cat-hist">') == 1
        assert out.count('<section class="vn-group note-cat-lang">') == 1
        # the glyph is paired with its category LABEL as text (fonts-off safety)
        assert "Historical / Cultural" in out and "Linguistic" in out
        assert '<span class="vn-cat-sym" aria-hidden="true">⌂</span>' in out
        # hist (rank 0) precedes lang (rank 4) in the emitted order
        assert out.index("note-cat-hist") < out.index("note-cat-lang")

    def test_byline_printed_once_per_source_and_sources_regroup(self):
        from scripts.build_edition import _emit_cascade_sections

        out = _emit_cascade_sections(self._rows(), self._meta())
        # the Strong's byline appears exactly once even though two notes (L1, L3)
        # cite it and a different source (L2) was interleaved between them
        assert out.count("Strong's Dictionary (1894)") == 1
        # L1 and L3 are regrouped under one .vn-source (the two strongs leaves are
        # adjacent in the output, L2 is in its own source block)
        assert out.index("L1") < out.index("L3")
        # an empty display -> no byline element for that source
        assert out.count('class="vn-source-byline"') == 2  # easton + strongs, NOT the paraphrase

    def test_every_leaf_row_is_conserved(self):
        from scripts.build_edition import _emit_cascade_sections

        out = _emit_cascade_sections(self._rows(), self._meta())
        # all four leaves survive exactly once (lossless re-grouping)
        for leaf in ("H1", "L1", "L2", "L3"):
            assert out.count(f">{leaf}<") == 1
        assert out.count('class="vn-item') == 4

    def test_suppressed_byline_source_prints_no_byline(self):
        from scripts.build_edition import _emit_cascade_sections

        rows = [
            {
                "cat": "comm",
                "source_key": "ethiopic",
                "source_display": "Ethiopian Orthodox",
                "suppress_byline": True,
                "row": '<div class="vn-item note-comm-ethiopian">C1</div>',
            },
        ]
        out = _emit_cascade_sections(rows, {"comm": ("◇", "Commentary / Tradition")})
        assert "C1" in out
        assert 'class="vn-source-byline"' not in out  # self-attributing body -> no group byline


class TestNoteRehaulS2Css:
    """``apply_note_cascade_css`` — the gated robust-CSS append (spec §2).
    Reuses the exact per-category hues already in epub_working/stylesheet.css."""

    def test_appends_a_group_spine_for_all_fifteen_categories(self):
        from scripts.build_edition import apply_note_cascade_css

        out = apply_note_cascade_css("/* base */\n")
        for cat in (
            "lang",
            "text",
            "xref",
            "hist",
            "lit",
            "comm",
            "compare",
            "dev",
            "liturgy",
            "apol",
            "modern",
            "ped",
            "vis",
            "dist",
            "topic",
        ):
            assert f".vn-group.note-cat-{cat}" in out, f"missing group spine for {cat}"
        # the hue must match the shipped per-category spine (reuse, don't re-author)
        assert "#8B6508" in out  # lang
        assert "#0B3D91" in out  # comm
        assert "#5A5F7E" in out  # topic (the one new hue)

    def test_carries_hierarchy_with_survivable_properties(self):
        from scripts.build_edition import apply_note_cascade_css

        out = apply_note_cascade_css("")
        # header cue = weight + small-caps + a border-bottom (NOT a background)
        assert ".vn-cat-head" in out and "font-variant-caps" in out and "border-bottom" in out
        # group colour = border-left (survives backgrounds-off)
        assert "border-left" in out
        # cascade indent on source + leaf
        assert ".vn-source" in out and ".vn-source-byline" in out

    def test_is_pure_append(self):
        from scripts.build_edition import apply_note_cascade_css

        base = "/* sentinel base sheet */\n"
        assert apply_note_cascade_css(base).startswith(base)


class TestNoteRehaulS2AttributionIndex:
    """The build-time live attribution index (the decision: live-lookup, no
    re-bake). Keyed by inject's full_id so it matches the baked ref-/note- ids."""

    def test_index_maps_fid_to_live_attribution_for_a_real_book(self):
        from scripts.build_edition import _note_attribution_index
        from scripts.core import config as _c

        book = _c.get_book("zep")
        idx = _note_attribution_index(book)
        assert idx, "zep has attributed notes"
        # every value is a non-empty source string
        assert all(v and v.strip() for v in idx.values())
        # at least one Strong's-dictionary source is present (zep is word-study dense)
        assert any("Concise Dictionary" in v for v in idx.values())

    def test_index_key_matches_the_baked_ref_id_form(self):
        from scripts.build_edition import _note_attribution_index
        from scripts.core import config as _c

        book = _c.get_book("zep")
        prefix = book.get("id_prefix") or book.get("bxx")
        idx = _note_attribution_index(book)
        # keys are the inject full_id form: {prefix}{cc}{vv}{suffix} (no "ref-")
        assert all(k.startswith(prefix) for k in idx)


class TestNoteRehaulS2InBuild:
    """S2 inside ``apply_badge_markers`` against a real gen-1 temp tree.
    note_group_by_category absent ⇒ flat output byte-identical to today."""

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

    def test_flag_off_emits_no_cascade(self, tmp_path):
        from scripts.build_edition import apply_badge_markers

        tmp, book = self._gen_tmp(tmp_path / "off")
        apply_badge_markers(tmp, {"id": "x", "marker_style": "badge"})
        assert 'class="vn-group' not in self._gen1_text(tmp, book)

    def test_flag_on_emits_category_groups_and_source_bylines(self, tmp_path):
        from scripts.build_edition import apply_badge_markers

        tmp, book = self._gen_tmp(tmp_path / "on")
        stats = apply_badge_markers(
            tmp,
            {"id": "x", "marker_style": "badge", "note_attribution_dedup": True, "note_group_by_category": True},
        )
        text = self._gen1_text(tmp, book)
        assert 'class="vn-group note-cat-' in text
        assert 'class="vn-cat-head"' in text
        # gen 1:1 is multi-source (Strong's word studies + TSK xrefs + topical) -> a byline shows
        assert 'class="vn-source-byline"' in text
        assert stats.get("s2_groups_emitted", 0) > 0

    def test_flag_on_conserves_every_badge_count(self, tmp_path):
        from scripts.build_edition import apply_badge_markers

        off, book = self._gen_tmp(tmp_path / "coff")
        apply_badge_markers(off, {"id": "x", "marker_style": "badge"})
        on, _ = self._gen_tmp(tmp_path / "con")
        apply_badge_markers(
            on,
            {"id": "x", "marker_style": "badge", "note_attribution_dedup": True, "note_group_by_category": True},
        )
        counts_off = self._badge_counts(off, book)
        counts_on = self._badge_counts(on, book)
        assert counts_off and counts_off == counts_on, "S2 changed a badge count — it dropped or added a row"


class TestNoteRehaulS2Wiring:
    """``note_group_by_category`` (S2) and ``note_topic_dedup`` (S3a) are plumbed
    like ``note_attribution_dedup`` (RULES §9): customize-data, checkboxes,
    EDITABLE + EDITABLE_BOOL (NOT EDITABLE_TEXT)."""

    def test_customize_data_exposes_both_fields_defaulting_false(self):
        from scripts.web import api_customize_data

        eds = {e["id"]: e for e in api_customize_data()["editions"]}
        assert eds["catholic-study"].get("note_group_by_category") is False
        assert eds["catholic-study"].get("note_topic_dedup") is False

    def test_customize_template_has_both_checkboxes(self):
        src = (REPO / "scripts" / "templates" / "customize.py").read_text(encoding="utf-8")
        assert 'data-field="note_group_by_category"' in src
        assert 'data-field="note_topic_dedup"' in src

    def test_both_fields_are_editable_bools_not_text(self):
        src = (REPO / "scripts" / "api" / "editions.py").read_text(encoding="utf-8")
        text_block = src.split("EDITABLE_TEXT = {")[1].split("}")[0]
        for field in ("note_group_by_category", "note_topic_dedup"):
            assert src.count(f'"{field}"') >= 2, f"{field} must be in EDITABLE + EDITABLE_BOOL"
            assert f'"{field}"' not in text_block, f"{field} must NOT be in EDITABLE_TEXT"
