"""Pins for scripts/prune_orphan_base_notes.py — safe orphan stripping."""

from __future__ import annotations

from scripts.prune_orphan_base_notes import prune_text


class TestPruneOrphanBaseNotes:
    def test_strips_removed_kind_only(self):
        html = (
            '<p>word<a class="note-ref note-comm-rabbinic" id="ref-g0101" '
            'href="#note-g0101" epub:type="noteref" title="Rabbinic">'
            '<sup class="marker-num">1</sup></a></p>'
            '<aside class="note note-comm-rabbinic" id="note-g0101" epub:type="footnote">'
            "<p>rabbi</p></aside>"
            '<aside class="note note-word" id="note-g0102" epub:type="footnote">'
            "<p>keep</p></aside>"
        )
        out, stats = prune_text(html, prefixes=["g"], sync_prefixes=frozenset(), valid_by_prefix={})
        assert stats["ids"] == 1
        assert "comm-rabbinic" not in out
        assert "note-g0102" in out

    def test_syncs_missing_corpus_id_for_tracked_prefix(self):
        html = (
            '<a class="note-ref note-comm" id="ref-g0999" href="#note-g0999" '
            'epub:type="noteref" title="Note"><sup class="marker-num">1</sup></a>'
            '<aside class="note note-comm" id="note-g0999" epub:type="footnote">'
            "<p>gone</p></aside>"
        )
        out, stats = prune_text(
            html,
            prefixes=["g"],
            sync_prefixes=frozenset({"g"}),
            valid_by_prefix={"g": {"g0101"}},
        )
        assert stats["ids"] == 1
        assert "g0999" not in out
