"""Orphan vnote asides — the fold/canon-splice filter gap (WIN triage 2026-06-11).

When a pass removes a book's body (superset fold: aes; canon splice: 1es/2es;
the est-10-5 extent single) the body's verse markers — and with them the
``id="v-{code}-{ch}-{v}"`` anchors — disappear, but the book's ``vnote-*``
translation-popup asides ride along unreachable (eth 206 / kindle 1,598;
user-visible "[no text]" endnote rows on kindle once unhide applies).

The fix criterion is the CONJUNCTION, measured on the real artifact:
unreferenced by any href AND backing v-anchor absent. Either alone is wrong:
- anchor-absent alone overreaches: 131 REFERENCED split-unit asides
  (``vnotes-…-s2``) lack a same-suffix anchor;
- unreferenced alone would drop anchor-present asides a later pass (badges)
  may still bind.
Kept books' cross-references to a dropped book's vnote keep that aside alive
(referenced ⇒ kept), preserving the old pass-3 rationale.
"""

from pathlib import Path

from scripts.build_edition import drop_orphan_vnote_asides

ASIDE_GEN = (
    '<aside class="vnote" id="vnote-gen-1-1" epub:type="footnote">'
    "<p><strong>Genesis 1:1.</strong></p>\n<p>body</p></aside>"
)
ASIDE_AES = (
    '<aside class="vnote" id="vnote-aes-1-1" epub:type="footnote">'
    "<p><strong>Additions to Esther 1:1.</strong></p>\n<p>gone book</p></aside>"
)
ASIDE_1ES = '<aside class="vnote" id="vnote-1es-1-1" epub:type="footnote"><p>xref-targeted</p></aside>'
ASIDE_FOO = '<aside class="vnote" id="vnote-foo-2-3" epub:type="footnote"><p>anchor present, no ref yet</p></aside>'
MARKER_GEN = '<a class="vn-link" id="v-gen-1-1" href="#vnote-gen-1-1" epub:type="noteref"><span class="vn">1</span></a>'


def _write(tmp_path: Path) -> tuple[Path, Path]:
    a = tmp_path / "index_split_000.html"
    b = tmp_path / "index_split_001.html"
    a.write_text(
        "<html><body>"
        + MARKER_GEN
        + '<span id="v-foo-2-3">3</span>'
        + ASIDE_GEN
        + ASIDE_AES
        + ASIDE_1ES
        + ASIDE_FOO
        + "</body></html>",
        encoding="utf-8",
    )
    b.write_text(
        '<html><body><p><a href="index_split_000.html#vnote-1es-1-1">see 1 Esdras 1:1</a></p></body></html>',
        encoding="utf-8",
    )
    return a, b


class TestDropOrphanVnoteAsides:
    def test_orphan_with_absent_anchor_is_dropped(self, tmp_path):
        a, _ = _write(tmp_path)
        stats = drop_orphan_vnote_asides(tmp_path)
        text = a.read_text(encoding="utf-8")
        assert 'id="vnote-aes-1-1"' not in text
        assert stats["orphan_vnote_asides_dropped"] == 1

    def test_referenced_aside_survives_even_without_anchor(self, tmp_path):
        a, _ = _write(tmp_path)
        drop_orphan_vnote_asides(tmp_path)
        # cross-file xref keeps the dropped book's popup alive (pass-3 rationale)
        assert 'id="vnote-1es-1-1"' in a.read_text(encoding="utf-8")

    def test_anchor_present_unreferenced_aside_survives(self, tmp_path):
        a, _ = _write(tmp_path)
        drop_orphan_vnote_asides(tmp_path)
        assert 'id="vnote-foo-2-3"' in a.read_text(encoding="utf-8")

    def test_normally_paired_aside_survives(self, tmp_path):
        a, _ = _write(tmp_path)
        drop_orphan_vnote_asides(tmp_path)
        assert 'id="vnote-gen-1-1"' in a.read_text(encoding="utf-8")

    def test_split_unit_suffix_maps_to_base_anchor(self, tmp_path):
        # a -s2 unit whose base anchor exists must be treated as anchored
        f = tmp_path / "index_split_000.html"
        f.write_text(
            '<html><body><span id="v-lev-26-31">31</span>'
            '<aside class="vnote" id="vnotes-lev-26-31-s2" epub:type="footnote">'
            "<p>part 2</p></aside></body></html>",
            encoding="utf-8",
        )
        stats = drop_orphan_vnote_asides(tmp_path)
        assert stats["orphan_vnote_asides_dropped"] == 0
        assert 'id="vnotes-lev-26-31-s2"' in f.read_text(encoding="utf-8")

    def test_no_orphans_is_byte_noop(self, tmp_path):
        f = tmp_path / "index_split_000.html"
        f.write_text(
            "<html><body>" + MARKER_GEN + ASIDE_GEN + "</body></html>",
            encoding="utf-8",
        )
        before = f.read_bytes()
        stats = drop_orphan_vnote_asides(tmp_path)
        assert stats["orphan_vnote_asides_dropped"] == 0
        assert f.read_bytes() == before


class TestVnoteRegexCollisionRegression:
    """a749e99b defined the orphan-drop regex as a SECOND module-level
    ``_VNOTE_ASIDE_RE``, clobbering the 6-group popup-pass regex (line ~818)
    that ``_apply_popup_languages_and_translation`` and
    ``_replace_verse_popup_translation`` depend on → ``IndexError: no such
    group`` in EVERY popup-edition build (caught by the first real build
    after the merge, the M1 --target-reader probe). Pin the popup pass
    end-to-end on a minimal aside so any future module-level name collision
    on this regex fails HERE, not 90 seconds into a build."""

    SAMPLE = (
        '<aside class="vnote" id="vnote-gen-1-1" epub:type="footnote">'
        '<p class="vnote-source-label">English (WEB)</p>'
        '<p class="vnote-text">In the beginning God created.</p>'
        "</aside>"
    )

    def test_popup_language_pass_processes_a_sample_aside(self):
        from scripts import build_edition as be

        edition = {"id": "x", "popup_languages_default": ["kjv"]}
        out, stats = be._apply_popup_languages_and_translation(self.SAMPLE, edition, "", "")
        assert stats["asides_seen"] == 1
        assert 'id="vnote-gen-1-1"' in out

    def test_legacy_translation_swap_pass_walks_asides(self):
        from scripts import build_edition as be

        out, stats = be._replace_verse_popup_translation(self.SAMPLE, "kjv", "KJV")
        # the verse exists in the KJV store → the English paragraph is swapped
        assert stats["replaced"] + stats["missed"] + stats["skipped_no_text_para"] >= 1

    def test_orphan_and_popup_regexes_are_distinct_objects(self):
        from scripts import build_edition as be

        assert be._VNOTE_ASIDE_RE.groups >= 6, (
            "_VNOTE_ASIDE_RE must remain the 6-group popup-pass regex; the orphan-drop pass owns _ORPHAN_VNOTE_ASIDE_RE"
        )
        assert be._ORPHAN_VNOTE_ASIDE_RE.pattern != be._VNOTE_ASIDE_RE.pattern
