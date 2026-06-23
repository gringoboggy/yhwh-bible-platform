"""Marker re-bake transformer + categorize-diff verifier (Wave 3 prereq #3).

`inject.py` runs base-wide: it bakes ~67k note markers + asides into the
shared ``epub_working/index_split_*.html`` tree, and the 11 editions filter
down from that one base. Changing ``build_marker`` only affects *future*
injects, so to flip the already-baked corpus to the new presentation
(``marker_style=numbers`` + symbols-into-notes, spec §4.1/§4.4/§12.4) we need a
surgical in-place transformer. Because a re-bake touching the whole base is
high-risk, a categorize-diff verifier PROVES the transform changed ONLY the
intended marker/aside regions (byte-multiset conserved elsewhere; no note
added, dropped, or recategorized).

OLD baked format (verbatim from the recovered base):
  marker: <a class="note-ref note-{kind}" id="ref-{id}" href="#note-{id}"
           epub:type="noteref" title="{t}"><sup class="marker-{kind}">{glyph}</sup></a>
  aside : <aside class="note note-{kind}" id="note-{id}" epub:type="footnote">
            <p><a href="#ref-{id}" class="note-back" title="Back">{glyph}</a>
               <span class="note-label">{label}</span> {body}</p>
          </aside>

NEW format:
  marker: ...><sup class="marker-num">{N}</sup></a>   (sequential, resets per
          chapter; inline category glyph dropped — no tofu on any device)
  aside : ...title="Back">↩</a> <a class="note-sym"
            href="legend.xhtml#legend-{cat}" title="{cat_label}">{glyph}</a>
            <span class="note-label">...   (the stray ‖ back-link becomes a
          fixed ↩; the category symbol moves INTO the note as a clickable
          link to its "A Guide to the Notes" legend row)
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


KIND_TO_CAT = {
    "xref-citation": "xref",
    "lang-greek": "lang",
    "comm-patristic": "comm",
    "topic-nave": "topic",
}
CAT_LABEL = {
    "xref": "Cross-references",
    "lang": "Linguistic",
    "comm": "Commentary / Tradition",
    "topic": "Topical",
}


def _marker(kind, fid, glyph, *, title="T"):
    return (
        f'<a class="note-ref note-{kind}" id="ref-{fid}" href="#note-{fid}" '
        f'epub:type="noteref" title="{title}"><sup class="marker-{kind}">{glyph}</sup></a>'
    )


def _aside(kind, fid, glyph, label, body, *, wrap="p"):
    return (
        f'<aside class="note note-{kind}" id="note-{fid}" epub:type="footnote">\n'
        f'  <{wrap}><a href="#ref-{fid}" class="note-back" title="Back">{glyph}</a> '
        f'<span class="note-label">{label}</span> {body}</{wrap}>\n'
        f"</aside>\n"
    )


def _ch(bxx, c):
    return f'<a class="ch-anchor" id="ch-{bxx}-c{c}"></a>'


# Canonical single-marker / single-aside before→after (byte-exact pins).
OLD_MARKER = _marker("xref-citation", "b740201", "‖", title="Direct citation")
NEW_MARKER = (
    '<a class="note-ref note-xref-citation" id="ref-b740201" href="#note-b740201" '
    'epub:type="noteref" title="Direct citation"><sup class="marker-num">1</sup></a>'
)

OLD_ASIDE = _aside("xref-citation", "b740201", "‖", "Cite.", "<strong>Cross-references.</strong> see Mat 6:9.")
NEW_ASIDE = (
    '<aside class="note note-xref-citation" id="note-b740201" epub:type="footnote">\n'
    '  <p><a href="#ref-b740201" class="note-back" title="Back">↩</a> '
    '<a class="note-sym" href="legend.xhtml#legend-xref" title="Cross-references">‖</a> '
    '<span class="note-label">Cite.</span> <strong>Cross-references.</strong> see Mat 6:9.</p>\n'
    "</aside>\n"
)


# ----------------------------------------------------------------------
# resync_marker_glyphs — the transformer
# ----------------------------------------------------------------------
class TestRenumberMarkers:
    def test_single_marker_becomes_number_one(self):
        from scripts.resync_marker_glyphs import renumber_markers

        ch = _ch("b74", 1)
        out, n = renumber_markers(ch + "<p>x" + OLD_MARKER + "</p>")
        assert n == 1
        assert '<sup class="marker-num">1</sup>' in out
        assert "marker-xref-citation" not in out  # inline category glyph/class dropped

    def test_canonical_marker_byte_exact(self):
        from scripts.resync_marker_glyphs import renumber_markers

        out, _ = renumber_markers(_ch("b74", 2) + OLD_MARKER)
        assert out == _ch("b74", 2) + NEW_MARKER

    def test_preserves_anchor_attributes(self):
        from scripts.resync_marker_glyphs import renumber_markers

        out, _ = renumber_markers(_ch("b74", 1) + OLD_MARKER)
        # id / href / epub:type / title / note-{kind} all survive on the <a>
        assert 'id="ref-b740201"' in out
        assert 'href="#note-b740201"' in out
        assert 'epub:type="noteref"' in out
        assert 'title="Direct citation"' in out
        assert "note-ref note-xref-citation" in out

    def test_numbering_resets_per_chapter(self):
        from scripts.resync_marker_glyphs import renumber_markers

        doc = (
            _ch("b74", 1)
            + "<p>"
            + _marker("xref-citation", "id1", "‖")
            + _marker("lang-greek", "id2", "⌘")
            + "</p>"
            + _ch("b74", 2)
            + "<p>"
            + _marker("comm-patristic", "id3", "◇")
            + "</p>"
        )
        out, n = renumber_markers(doc)
        assert n == 3
        assert 'id="ref-id1" href="#note-id1" epub:type="noteref" title="T"><sup class="marker-num">1</sup>' in out
        assert 'id="ref-id2" href="#note-id2" epub:type="noteref" title="T"><sup class="marker-num">2</sup>' in out
        # new chapter → counter resets to 1
        assert 'id="ref-id3" href="#note-id3" epub:type="noteref" title="T"><sup class="marker-num">1</sup>' in out

    def test_idempotent_second_pass(self):
        from scripts.resync_marker_glyphs import renumber_markers

        once, _ = renumber_markers(_ch("b74", 1) + OLD_MARKER)
        # The returned count is matches-SEEN (the regex re-matches pass-1's own
        # marker-num output), not mutations-made — so this test pins OUTPUT
        # stability only; no useful assertion exists on the second count.
        twice, _ = renumber_markers(once)
        assert twice == once  # numbers stay stable on a second run

    def test_cross_ref_href_does_not_reset_numbering(self):
        # An aside cross-ref href "...#ch-b73-c1" must NOT be read as a chapter
        # boundary (only id="ch-…" headings reset); otherwise a note's marker
        # mid-chapter would wrongly restart the count.
        from scripts.resync_marker_glyphs import renumber_markers

        doc = (
            _ch("b74", 1)
            + "<p>"
            + _marker("xref-citation", "id1", "‖")
            + '<a href="index_split_058.html#ch-b73-c1">x</a>'
            + _marker("lang-greek", "id2", "⌘")
            + "</p>"
        )
        out, _ = renumber_markers(doc)
        assert '<sup class="marker-num">2</sup>' in out  # id2 is still #2, not #1


class TestRewriteAsides:
    def test_back_link_glyph_becomes_return_arrow(self):
        from scripts.resync_marker_glyphs import rewrite_asides

        out, n = rewrite_asides(OLD_ASIDE, kind_to_cat=KIND_TO_CAT, cat_label=CAT_LABEL)
        assert n == 1
        assert 'class="note-back" title="Back">↩</a>' in out
        assert 'title="Back">‖</a>' not in out  # the stray ‖ back-link is gone (now ↩)

    def test_category_symbol_moves_into_note_as_legend_link(self):
        from scripts.resync_marker_glyphs import rewrite_asides

        out, _ = rewrite_asides(OLD_ASIDE, kind_to_cat=KIND_TO_CAT, cat_label=CAT_LABEL)
        assert '<a class="note-sym" href="legend.xhtml#legend-xref" title="Cross-references">‖</a>' in out

    def test_legend_link_targets_kind_category(self):
        from scripts.resync_marker_glyphs import rewrite_asides

        greek = _aside("lang-greek", "g1", "⌘", "Gk.", "logos.")
        out, _ = rewrite_asides(greek, kind_to_cat=KIND_TO_CAT, cat_label=CAT_LABEL)
        assert 'href="legend.xhtml#legend-lang"' in out
        assert ">⌘</a>" in out

    def test_label_and_body_unchanged(self):
        from scripts.resync_marker_glyphs import rewrite_asides

        out, _ = rewrite_asides(OLD_ASIDE, kind_to_cat=KIND_TO_CAT, cat_label=CAT_LABEL)
        assert '<span class="note-label">Cite.</span>' in out
        assert "<strong>Cross-references.</strong> see Mat 6:9." in out

    def test_canonical_aside_byte_exact(self):
        from scripts.resync_marker_glyphs import rewrite_asides

        out, _ = rewrite_asides(OLD_ASIDE, kind_to_cat=KIND_TO_CAT, cat_label=CAT_LABEL)
        assert out == NEW_ASIDE

    def test_div_wrapped_body(self):
        from scripts.resync_marker_glyphs import rewrite_asides

        div = _aside("comm-patristic", "c1", "◇", "Note.", "<ul><li>a</li></ul>", wrap="div")
        out, n = rewrite_asides(div, kind_to_cat=KIND_TO_CAT, cat_label=CAT_LABEL)
        assert n == 1
        assert 'class="note-back" title="Back">↩</a>' in out
        assert 'href="legend.xhtml#legend-comm"' in out

    def test_idempotent_second_pass(self):
        from scripts.resync_marker_glyphs import rewrite_asides

        once, _ = rewrite_asides(OLD_ASIDE, kind_to_cat=KIND_TO_CAT, cat_label=CAT_LABEL)
        twice, n2 = rewrite_asides(once, kind_to_cat=KIND_TO_CAT, cat_label=CAT_LABEL)
        assert n2 == 0  # nothing left to rewrite
        assert twice == once  # no double note-sym appended


class TestResyncHtml:
    def test_full_resync_byte_exact(self):
        from scripts.resync_marker_glyphs import resync_html

        before = _ch("b74", 2) + "<p>" + OLD_MARKER + "</p>" + OLD_ASIDE
        after, stats = resync_html(before, kind_to_cat=KIND_TO_CAT, cat_label=CAT_LABEL)
        assert after == _ch("b74", 2) + "<p>" + NEW_MARKER + "</p>" + NEW_ASIDE
        assert stats["markers"] == 1
        assert stats["asides"] == 1


class TestFilteredEditionStaysGapless:
    """Numbering is base-wide, so a filtered edition (which removes some kinds'
    markers) would otherwise read 1,3,4,7… build_one renumbers the survivors
    per chapter after filter_html, so EVERY edition reads 1,2,3… This pins the
    composition build_one performs (filter → renumber)."""

    def test_renumber_after_filter_closes_the_gaps(self):
        from scripts.build_edition import filter_html
        from scripts.resync_marker_glyphs import renumber_markers

        def m(kind, n):
            return (
                f'<a class="note-ref note-{kind}" id="ref-x{n}" href="#note-x{n}" '
                f'epub:type="noteref" title="T"><sup class="marker-num">{n}</sup></a>'
            )

        doc = (
            _ch("b74", 1)
            + "<p>"
            + m("comm-x", 1)
            + m("lang-y", 2)
            + m("comm-x", 3)
            + m("lang-y", 4)
            + m("comm-x", 5)
            + "</p>"
        )
        filtered, _ = filter_html(doc, {"comm-x"})  # disable comm-x → drop markers 1,3,5
        renumbered, _ = renumber_markers(filtered)
        # the two surviving lang-y markers (orig 2 and 4) now read 1 and 2
        assert 'id="ref-x2" href="#note-x2" epub:type="noteref" title="T"><sup class="marker-num">1</sup>' in renumbered
        assert 'id="ref-x4" href="#note-x4" epub:type="noteref" title="T"><sup class="marker-num">2</sup>' in renumbered
        assert 'marker-num">3</sup>' not in renumbered  # no gap left behind


class TestBuildAsideEmitsNewFormat:
    """The ‖ fix is at the SOURCE (build_aside, spec §12.4) so a future inject
    never re-introduces the stray back-link glyph — and build_aside's output
    must stay byte-identical to what the re-bake tool's rewrite_asides produces,
    or the base and freshly-injected notes would diverge."""

    def test_build_aside_back_link_is_return_arrow_with_legend_symbol(self):
        from scripts.inject import build_aside

        out = build_aside("comm-patristic", "g0101", "Note.", "body.")
        assert 'class="note-back" title="Back">↩</a>' in out
        assert 'title="Back">◇</a>' not in out  # no stray category glyph as back-link
        assert '<a class="note-sym" href="legend.xhtml#legend-comm"' in out
        assert ">◇</a>" in out  # the symbol now lives in the note-sym

    def test_build_aside_matches_rewrite_asides_byte_for_byte(self):
        from scripts.inject import build_aside
        from scripts.resync_marker_glyphs import default_cat_label, default_kind_to_cat, rewrite_asides

        # The OLD-format aside the recovered base holds for this same note...
        old = _aside("comm-patristic", "g0101", "◇", "Note.", "body.")
        rebaked, _ = rewrite_asides(old, kind_to_cat=default_kind_to_cat(), cat_label=default_cat_label())
        # ...must equal what the NEW build_aside emits directly.
        assert build_aside("comm-patristic", "g0101", "Note.", "body.") == rebaked


class TestTitleEscaping:
    """round-13 #9: the note-ref ``title=`` and note-sym ``title=`` attributes are
    html.escaped at BOTH the inject source (build_marker / build_aside) AND the
    re-bake (resync_titles / rewrite_asides), so a future special-char kind title
    or category label can never emit malformed XHTML — and the two paths stay
    byte-identical. A no-op on today's HTML-clean titles (every current kind
    title / category label is verified clean), proven by the byte-exact pins
    above staying green."""

    # The apostrophe MUST survive (valid in a double-quoted attr; "Nave's …" is a
    # real kind title) — escape_attr leaves it, html.escape(quote=True) would not.
    NASTY = 'A & B <x> "q" o\'k'
    ESCAPED = "A &amp; B &lt;x&gt; &quot;q&quot; o'k"

    def test_build_marker_escapes_title(self, monkeypatch):
        from scripts import inject

        monkeypatch.setattr(inject, "html_title_for", lambda kind: self.NASTY)
        out = inject.build_marker("xref-citation", "b010101")
        assert f'title="{self.ESCAPED}"' in out
        assert "<x>" not in out  # raw angle brackets never leak into the markup

    def test_resync_titles_does_not_un_escape_a_fresh_marker(self, monkeypatch):
        # The desync guard: a freshly-injected (escaped) marker, run through the
        # re-bake, must come back byte-identical — never reverted to the raw title.
        from scripts import inject
        from scripts import resync_marker_glyphs as r

        monkeypatch.setattr(inject, "html_title_for", lambda kind: self.NASTY)
        monkeypatch.setattr(r, "html_title_for", lambda kind: self.NASTY)
        marker = inject.build_marker("xref-citation", "b010101")
        rebaked, changed = r.resync_titles(marker)
        assert rebaked == marker
        assert changed == 0
        assert f'title="{self.ESCAPED}"' in rebaked

    def test_resync_titles_upgrades_a_legacy_unescaped_title(self, monkeypatch):
        # An OLD-format marker baked with a raw title is migrated to the escaped
        # form on the next re-bake (the value, not the structure, changes).
        from scripts import resync_marker_glyphs as r

        monkeypatch.setattr(r, "html_title_for", lambda kind: self.NASTY)
        legacy = _marker("xref-citation", "b1", "‖", title="A & B")
        out, changed = r.resync_titles(legacy)
        assert changed == 1
        assert f'title="{self.ESCAPED}"' in out

    def test_rewrite_asides_escapes_note_sym_title(self):
        from scripts.resync_marker_glyphs import rewrite_asides

        old = _aside("xref-citation", "b1", "‖", "Cite.", "body.")
        out, _ = rewrite_asides(old, kind_to_cat=KIND_TO_CAT, cat_label={"xref": "Cross & <refs>"})
        assert 'title="Cross &amp; &lt;refs&gt;"' in out
        assert "<refs>" not in out


# ----------------------------------------------------------------------
# categorize_diff — the verifier
# ----------------------------------------------------------------------
class TestCategorize:
    def test_counts_markers_and_asides_by_kind(self):
        from scripts.categorize_diff import categorize

        html = (
            _ch("b74", 1)
            + OLD_MARKER
            + _marker("lang-greek", "g1", "⌘")
            + OLD_ASIDE
            + _aside("lang-greek", "g1", "⌘", "Gk.", "logos.")
        )
        cat = categorize(html)
        assert cat["markers"]["xref-citation"] == 1
        assert cat["markers"]["lang-greek"] == 1
        assert cat["asides"]["xref-citation"] == 1
        assert cat["marker_ids"] == {"b740201", "g1"}
        assert cat["aside_ids"] == {"b740201", "g1"}


class TestProveRebake:
    def _before(self):
        return _ch("b74", 1) + "<p>" + OLD_MARKER + "</p>" + OLD_ASIDE

    def _after(self):
        from scripts.resync_marker_glyphs import resync_html

        out, _ = resync_html(self._before(), kind_to_cat=KIND_TO_CAT, cat_label=CAT_LABEL)
        return out

    def test_accepts_the_intended_rebake(self):
        from scripts.categorize_diff import prove_marker_rebake

        report = prove_marker_rebake(self._before(), self._after())
        assert report["ok"] is True
        assert report["markers"] == 1
        assert report["asides"] == 1

    def test_rejects_a_dropped_note(self):
        from scripts.categorize_diff import prove_marker_rebake

        after = self._after().replace(NEW_ASIDE, "")  # drop the aside
        report = prove_marker_rebake(self._before(), after)
        assert report["ok"] is False
        assert "aside" in report["reason"].lower()

    def test_rejects_an_added_marker(self):
        from scripts.categorize_diff import prove_marker_rebake

        after = self._after() + _marker("lang-greek", "sneaky", "⌘")
        report = prove_marker_rebake(self._before(), after)
        assert report["ok"] is False

    def test_rejects_a_body_text_change(self):
        from scripts.categorize_diff import prove_marker_rebake

        after = self._after().replace("see Mat 6:9.", "see Mat 7:7.")
        report = prove_marker_rebake(self._before(), after)
        assert report["ok"] is False
        assert "byte" in report["reason"].lower() or "diverge" in report["reason"].lower()

    def test_rejects_recategorized_note(self):
        # A note whose kind silently flips (xref→comm) must be caught even if
        # counts-by-id stay the same length.
        from scripts.categorize_diff import prove_marker_rebake

        after = self._after().replace("note-xref-citation", "note-comm-patristic")
        report = prove_marker_rebake(self._before(), after)
        assert report["ok"] is False
