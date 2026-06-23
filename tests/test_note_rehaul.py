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

    def test_self_attribution_detected_on_the_baked_row_not_the_stored_aside(self):
        from scripts.build_edition import _is_self_attributing_comm_ethiopian

        # PRODUCTION REALITY (Mac S2-cascade review, BYLINE-1): apply_badge_markers sees the
        # BAKED row, where the sanitizer has stripped the stored body's inner
        # <aside class="note-comm-ethiopian"> (aside is not in html_sanitize.ALLOWED_TAGS).
        # Only the kind's note-comm-ethiopian wrapper class and the father->work->(date)
        # <strong>/<em>/<small> byline triad survive — detect THAT, never the <aside> prefix.
        baked_self_attr = (
            '<div class="vn-item note-comm-ethiopian"><div>'
            '<a class="note-sym" href="legend.xhtml#legend-comm">◇</a> '
            "<strong>Cyril of Alexandria</strong> <em>Commentary on John</em> "
            "<small>(430)</small><p>...</p></div></div>"
        )
        assert _is_self_attributing_comm_ethiopian(baked_self_attr) is True
        # a real BAKED *plain* comm-ethiopian row (note-comm-ethiopian wrapper, only a bold
        # lead-in — NO em/small byline) must NOT be treated as self-attributing (it keeps its
        # byline). This is the actual epub_working shape of note-1e7901.
        baked_plain = (
            '<div class="vn-item note-comm-ethiopian"><p>'
            '<span class="note-label">Note.</span> '
            "<strong>The end of the Astronomical Book.</strong> 1 Enoch 72-82 ...</p></div>"
        )
        assert _is_self_attributing_comm_ethiopian(baked_plain) is False
        # the stored <aside> form still detects True (the helper is a superset, so a
        # stored-body caller stays correct)
        stored = (
            '<aside class="note-comm-ethiopian"><strong>Cyril of Alexandria</strong> '
            "<em>Commentary on John</em> <small>(430)</small><p>...</p></aside>"
        )
        assert _is_self_attributing_comm_ethiopian("   \n" + stored) is True
        # the triad must belong to a comm-ethiopian row — a strong/em/small triad in some
        # OTHER kind is not a comm-ethiopian self-attribution
        assert (
            _is_self_attributing_comm_ethiopian(
                '<div class="vn-item note-lang-greek"><strong>x</strong> <em>y</em> <small>(z)</small></div>'
            )
            is False
        )
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
        # inner byline already names the source -> the label restatement is redundant.
        # REAL BAKED shape: the sanitizer stripped the stored inner <aside>, so only the
        # surviving father->work->(date) triad + the note-comm-ethiopian wrapper remain.
        row = (
            '<div class="vn-item note-comm-ethiopian"><div>'
            '<a class="note-sym" href="legend.xhtml#legend-comm">◇</a> '
            '<span class="note-label">Cyril of Alexandria (430).</span> '
            "<strong>Cyril of Alexandria</strong> <em>Commentary on John</em> "
            "<small>(430)</small><p>...</p></div></div>"
        )
        out, changed = _strip_redundant_note_label(row, "comm-ethiopian", defaults)
        assert changed is True and 'class="note-label"' not in out
        # the body's OWN inner byline survives the label strip
        assert "Cyril of Alexandria</strong>" in out and "<em>Commentary on John</em>" in out

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
            if 'id="vbadge-gen-1-1-s1"' in t:
                return t
        raise AssertionError("gen 1 badge file not found")

    def _badge_counts(self, tmp, book):
        import re as _re

        counts = {}
        for f in book["files"]:
            text = (tmp / f).read_text(encoding="utf-8")
            # round-7 -s split: a verse's notes spread across -sN badges with
            # titles like `5 notes (part 1 of 2)`. Match the leading count (NO
            # trailing quote, so split titles match too) and SUM the parts so the
            # value is the verse TOTAL — what S2 (group/dedup) conserves.
            for vv, cnt in _re.findall(r'id="vbadge-gen-1-(\d+)(?:-s\d+)?"[^>]*title="(\d+) notes?', text):
                counts[vv] = counts.get(vv, 0) + int(cnt)
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

    def test_customize_data_exposes_the_field_mirroring_registry_default_false(self):
        from scripts.web import api_customize_data
        from scripts.core import config

        reg = {e["id"]: e for e in config.load_editions()}
        eds = {e["id"]: e for e in api_customize_data()["editions"]}
        for eid, e in eds.items():
            v = e.get("note_attribution_dedup")
            # Plumbed for every customize edition as a bool (RULES §9) …
            assert isinstance(v, bool), f"{eid}: note_attribution_dedup not a bool"
            # … mirroring the registry pin, with the code default False when the
            # edition doesn't pin it (web_editions.py `e.get(..., False)`).
            # Derived from the registry so a rollout pin flip (e.g. the
            # 2026-06-22 Kobo redundancy fix) can't re-stale this assertion.
            assert v == bool(reg[eid].get("note_attribution_dedup", False)), eid

    def test_customize_template_has_the_checkbox(self):
        src = (REPO / "scripts" / "templates" / "customize.py").read_text(encoding="utf-8")
        assert 'data-field="note_attribution_dedup"' in src

    def test_field_is_an_editable_bool_not_text(self):
        # EDITABLE_TEXT_FIELDS / EDITABLE_BOOL_FIELDS are frozensets now (was an
        # inline `EDITABLE_TEXT = {` dict) — assert membership, not a source scan.
        from scripts.api.editions import EDITABLE_BOOL_FIELDS, EDITABLE_TEXT_FIELDS

        assert "note_attribution_dedup" in EDITABLE_BOOL_FIELDS
        assert "note_attribution_dedup" not in EDITABLE_TEXT_FIELDS


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

    def test_locator_strip_absorbs_a_structural_book_word(self):
        from scripts.build_edition import _source_display

        # SK-2: the per-locator citation must strip WHOLE — not leave a dangling structural
        # word. "…, Bk I.11 (NPNF S2 V14). PD." -> the work title, no trailing "Bk".
        assert (
            _source_display("Cyril of Alexandria, Commentary on John, Bk I.11 (NPNF S2 V14). PD.")
            == "Cyril of Alexandria, Commentary on John"
        )
        # a plain roman locator still strips (Ephrem "Commentary on Genesis I.11")
        assert (
            _source_display("Ephrem the Syrian, Commentary on Genesis I.11. PD.")
            == "Ephrem the Syrian, Commentary on Genesis"
        )
        # the "Homily" / "Book" structural words too
        assert _source_display("John Chrysostom, Homily III.2. PD.") == "John Chrysostom"
        assert _source_display("Irenaeus, Against Heresies, Book V.2. PD.") == "Irenaeus, Against Heresies"

    def test_series_strip_loops_to_a_fixpoint(self):
        from scripts.build_edition import _source_display

        # POLISH-1: a single series-strip pass consumes the trailing "…, vol. N" first and
        # leaves a dangling "NPNF Series N"; loop to a fixpoint so BOTH boilerplate tokens go.
        assert (
            _source_display("Augustine, Tractates on John, on 6:4-9. NPNF Series 2, vol. 13. PD.")
            == "Augustine, Tractates on John, on 6:4-9"
        )

    def test_source_display_leaves_no_dangling_structural_fragment_on_the_corpus(self):
        # SK-2 + POLISH-1 over every distinct live attribution: a trimmed byline must never
        # END on a dangling structural citation fragment — the SK-2 ("…, Bk"/"Book"/"Hom"/
        # "Homily") and POLISH-1 (a trailing "NPNF Series N" / "Series N" / "vol. N") tails.
        # (A full NPNF citation with an editor/year tail AFTER it is legitimate, not dangling.)
        import re as _re

        from scripts.build_edition import _source_display
        from scripts.core import config as _c
        from scripts.core.notes_io import load_notes

        notes_dir = REPO / "content" / "notes"
        tail = _re.compile(
            r"(?:(?:,\s*)?\b(?:Bk|Book|Hom\.?|Homily)|\bNPNF\b[\s\w]*|\bSeries\s+\d+|\bvol\.?\s*\d+)\s*$",
            _re.IGNORECASE,
        )
        bad: list[tuple[str, str, str]] = []
        for book in _c.load_books():
            p = notes_dir / f"{book['code']}.py"
            if not p.is_file():
                continue
            for tup in load_notes(p) or []:
                a = _c.note_attribution(tup)
                if not a:
                    continue
                d = _source_display(a)
                if tail.search(d):
                    bad.append((book["code"], a, d))
        assert not bad, f"{len(bad)} byline(s) end on a dangling structural fragment, e.g. {bad[:3]}"


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

    def test_mixed_source_bucket_keeps_a_non_self_attributing_byline(self):
        from scripts.build_edition import _emit_cascade_sections

        # BYLINE-4: a source bucket with ONE self-attributing row (suppress) AND one that is
        # NOT must STILL print the byline — all(), not any(): a self-attributing row must
        # never hide a co-bucketed plain row's source byline.
        rows = [
            {
                "cat": "comm",
                "source_key": "k",
                "source_display": "Some Source (1900)",
                "suppress_byline": True,
                "row": '<div class="vn-item note-comm-ethiopian">A</div>',
            },
            {
                "cat": "comm",
                "source_key": "k",
                "source_display": "Some Source (1900)",
                "suppress_byline": False,
                "row": '<div class="vn-item note-comm">B</div>',
            },
        ]
        out = _emit_cascade_sections(rows, {"comm": ("◇", "Commentary")})
        assert out.count('class="vn-source-byline"') == 1
        assert out.count("Some Source (1900)") == 1

    def test_leaf_count_counts_wrappers_not_a_body_substring(self):
        from scripts.build_edition import _count_cascade_leaves

        # S2-GUARD-3: the §4 conservation guard counts the .vn-item WRAPPER, so a note body
        # that merely contains the literal text class="vn-item must not inflate the count
        # (a latent false-FAIL that would HALT the eth build).
        html = (
            '<div class="vn-item note-comm">a note mentioning class="vn-item in its prose</div>\n'
            '<div class="vn-item note-lang-greek">another</div>\n'
        )
        assert _count_cascade_leaves(html) == 2


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
            if 'id="vbadge-gen-1-1-s1"' in t:
                return t
        raise AssertionError("gen 1 badge file not found")

    def _badge_counts(self, tmp, book):
        import re as _re

        counts = {}
        for f in book["files"]:
            text = (tmp / f).read_text(encoding="utf-8")
            # round-7 -s split: a verse's notes spread across -sN badges with
            # titles like `5 notes (part 1 of 2)`. Match the leading count (NO
            # trailing quote, so split titles match too) and SUM the parts so the
            # value is the verse TOTAL — what S2 (group/dedup) conserves.
            for vv, cnt in _re.findall(r'id="vbadge-gen-1-(\d+)(?:-s\d+)?"[^>]*title="(\d+) notes?', text):
                counts[vv] = counts.get(vv, 0) + int(cnt)
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

    def test_customize_data_exposes_both_fields_mirroring_registry_default_false(self):
        from scripts.web import api_customize_data
        from scripts.core import config

        reg = {e["id"]: e for e in config.load_editions()}
        eds = {e["id"]: e for e in api_customize_data()["editions"]}
        # Both fields plumbed as bools, each mirroring its registry pin with the
        # code default False when absent — derived from the registry so a rollout
        # pin flip (e.g. the 2026-06-22 Kobo redundancy fix) can't re-stale this.
        for field in ("note_group_by_category", "note_topic_dedup"):
            for eid, e in eds.items():
                v = e.get(field)
                assert isinstance(v, bool), f"{eid}: {field} not a bool"
                assert v == bool(reg[eid].get(field, False)), f"{eid}: {field}"

    def test_customize_template_has_both_checkboxes(self):
        src = (REPO / "scripts" / "templates" / "customize.py").read_text(encoding="utf-8")
        assert 'data-field="note_group_by_category"' in src
        assert 'data-field="note_topic_dedup"' in src

    def test_both_fields_are_editable_bools_not_text(self):
        from scripts.api.editions import EDITABLE_BOOL_FIELDS, EDITABLE_TEXT_FIELDS

        for field in ("note_group_by_category", "note_topic_dedup"):
            assert field in EDITABLE_BOOL_FIELDS, f"{field} must be in EDITABLE_BOOL_FIELDS"
            assert field not in EDITABLE_TEXT_FIELDS, f"{field} must NOT be in EDITABLE_TEXT_FIELDS"


# ======================================================================
# S3a — topic-note dedup + Nave's/Torrey union (vocab-aware; terms carry
# internal commas, so longest-match against the authoritative vocab — NOT a
# comma-split, which mis-parses 36.9% of topic notes).
# ======================================================================


class TestNoteRehaulS3aHelpers:
    """Pure helpers for S3a: the topic vocab, the longest-match term parser, the
    Title-case normaliser, and the case-insensitive union."""

    def test_topic_vocab_loads_both_sources_casefolded(self):
        from scripts.build_edition import _topic_vocab

        v = _topic_vocab()
        assert len(v) > 4000  # ~5,232 combined Nave + Torrey topic names
        assert "creation" in v and "god" in v
        # a comma-bearing name is in the vocab (the whole reason for longest-match)
        assert "accusation, false" in v

    def test_parse_splits_simple_comma_list(self):
        from scripts.build_edition import _parse_topic_terms, _topic_vocab

        out = _parse_topic_terms("CREATION, EARTH, GOD, HEAVEN", _topic_vocab())
        assert out == ["CREATION", "EARTH", "GOD", "HEAVEN"]

    def test_parse_longest_match_keeps_comma_bearing_terms_whole(self):
        from scripts.build_edition import _parse_topic_terms, _topic_vocab

        # "ACCUSATION, FALSE" is ONE Nave topic — a naive comma-split would break it
        out = _parse_topic_terms("ACCUSATION, FALSE, GOD, CREATION", _topic_vocab())
        assert out == ["ACCUSATION, FALSE", "GOD", "CREATION"]

    def test_parse_unknown_term_falls_back_to_token(self):
        from scripts.build_edition import _parse_topic_terms, _topic_vocab

        # a term not in the vocab is kept as its own token (defensive, never dropped)
        out = _parse_topic_terms("ZZZNOTATOPIC, GOD", _topic_vocab())
        assert out == ["ZZZNOTATOPIC", "GOD"]

    def test_parse_five_token_compound_topic_stays_whole(self):
        # round-7 5.1: the span window was capped at 3 tokens, so Nave's real
        # 5-token compound "MANASSEH, NAPHTALI, REUBEN, SIMEON, ZEBULUN" (a
        # topics key in naves_topical.json) could never longest-match and
        # fragmented into single-token topics. The window is now uncapped;
        # vocab membership still gates every candidate span.
        from scripts.build_edition import _parse_topic_terms, _topic_vocab

        out = _parse_topic_terms("MANASSEH, NAPHTALI, REUBEN, SIMEON, ZEBULUN", _topic_vocab())
        assert out == ["MANASSEH, NAPHTALI, REUBEN, SIMEON, ZEBULUN"]

    def test_title_topic_handles_caps_commas_and_apostrophes(self):
        from scripts.build_edition import _title_topic

        assert _title_topic("CREATION") == "Creation"
        assert _title_topic("GOD, TITLES AND NAMES OF") == "God, Titles And Names Of"
        assert _title_topic("LORD'S SUPPER") == "Lord's Supper"

    def test_union_dedups_caseinsensitive_first_appearance_titlecased(self):
        from scripts.build_edition import _topic_union

        nave = ["CREATION", "GOD", "HEAVEN", "HEAVEN"]  # Nave UPPER, repeats HEAVEN
        torrey = ["Creation", "Heaven", "Faith"]  # Torrey Title, overlaps Creation/Heaven
        out = _topic_union([nave, torrey])
        # union, first-appearance order, Title-cased, deduped case-insensitively
        assert out == ["Creation", "God", "Heaven", "Faith"]


class TestNoteRehaulS3aInBuild:
    """S3a inside ``apply_badge_markers`` against a real gen-1 temp tree. The topic
    notes (topic-nave + topic-torrey) merge into ONE Topics row when the flag is on."""

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
            if 'id="vbadge-gen-1-1-s1"' in t:
                return t
        raise AssertionError("gen 1 badge file not found")

    def test_flag_off_keeps_topic_notes_separate(self, tmp_path):
        from scripts.build_edition import apply_badge_markers

        tmp, book = self._gen_tmp(tmp_path / "off")
        stats = apply_badge_markers(tmp, {"id": "x", "marker_style": "badge", "note_group_by_category": True})
        assert stats.get("s3a_topic_notes_merged", 0) == 0

    def test_flag_on_merges_topic_notes_to_one_row(self, tmp_path):
        from scripts.build_edition import apply_badge_markers

        tmp, book = self._gen_tmp(tmp_path / "on")
        stats = apply_badge_markers(
            tmp,
            {
                "id": "x",
                "marker_style": "badge",
                "note_attribution_dedup": True,
                "note_group_by_category": True,
                "note_topic_dedup": True,
            },
        )
        # gen 1:1 carries topic-nave + topic-torrey → merged into one Topics row
        assert stats["s3a_topic_notes_merged"] > 0
        text = self._gen1_text(tmp, book)
        # the merged topic row uses the lossless " · " union separator
        assert " · " in text
