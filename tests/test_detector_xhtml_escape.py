"""5.11 (2026-06-10 audit) — topical detectors must HTML-escape topic
headings before weaving them into the XHTML note body.

Torrey's source data carries raw ampersands in 2 topic headings (e.g.
"Herbs, & C"), which previously flowed into ``draft_body`` unescaped — an
XHTML well-formedness defect (the epubcheck RSC-016 class the Easton
re-ingest already guards against). The same latent pattern existed in
``NaveTopicalDetector`` (0 affected bodies today — fixed as a class, not an
instance). Both detectors now escape each topic via ``html.escape``,
mirroring the γ.3+ patristic/protestant ``_html.escape`` pattern, so
store == detector == baked base converge on the escaped form.

Fixture shape mirrors the project precedent for wiring a stub topical
index without touching disk (``scripts/_reingest_torrey_topics.py::
_detector_for`` uses the same ``__new__`` + attribute-assignment shape;
``tests/test_scripts.py::TestNaveTopicalDetector`` stubs ``topics_for``
the same way via monkeypatch).
"""

from __future__ import annotations

import re

# Raw non-entity ampersand — the store/base damage signature (same regex
# as the Easton twin's _xhtml_bad screen).
RAW_AMP = re.compile(r"&(?!(amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)")


class _StubTopical:
    """Minimal stand-in for the Torrey/Nave topical index — only the
    ``topics_for()`` surface the detectors consume."""

    def __init__(self, mapping: dict):
        self._verses = mapping

    def topics_for(self, book, chapter, verse, *, top_n=5):
        return self._verses.get(book, {}).get(chapter, {}).get(verse, [])[:top_n]


def _torrey_detector(mapping: dict):
    from scripts.core.detectors import TorreyTopicalDetector

    det = TorreyTopicalDetector.__new__(TorreyTopicalDetector)
    det.torrey = _StubTopical(mapping)
    det.top_n = 5
    det.min_topics = 1
    return det


def _nave_detector(mapping: dict):
    from scripts.core.detectors import NaveTopicalDetector

    det = NaveTopicalDetector.__new__(NaveTopicalDetector)
    det.naves = _StubTopical(mapping)
    det.top_n = 5
    det.min_topics = 1
    return det


class TestTorreyTopicalEscape:
    def test_ampersand_topic_escaped_in_body(self):
        # The real damaged heading from Torrey's source data.
        det = _torrey_detector({"exo": {12: {8: ["Herbs, & C", "Passover"]}}})
        (cand,) = det.detect("exo", 12, 8, "")
        assert "Herbs, &amp; C" in cand.draft_body
        assert not RAW_AMP.search(cand.draft_body), cand.draft_body

    def test_angle_brackets_escaped_in_body(self):
        # Fix the CLASS: any markup-significant character in a topic
        # heading must be neutralized, not just '&'.
        det = _torrey_detector({"gen": {1: {1: ["A <b>bold</b> topic"]}}})
        (cand,) = det.detect("gen", 1, 1, "")
        assert "&lt;b&gt;" in cand.draft_body
        assert "<b>" not in cand.draft_body

    def test_plain_topics_byte_identical(self):
        # Zero drift for the 21k+ clean bodies: escaping is a no-op on
        # plain topic headings (store↔detector lockstep depends on this).
        det = _torrey_detector({"jdg": {6: {19: ["Altars", "Offerings"]}}})
        (cand,) = det.detect("jdg", 6, 19, "")
        assert "<strong>Topics.</strong> This verse appears under: Altars, Offerings." == cand.draft_body


class TestNaveTopicalEscape:
    def test_ampersand_topic_escaped_in_body(self):
        det = _nave_detector({"exo": {12: {8: ["Herbs, & C"]}}})
        (cand,) = det.detect("exo", 12, 8, "")
        assert "Herbs, &amp; C" in cand.draft_body
        assert not RAW_AMP.search(cand.draft_body), cand.draft_body

    def test_angle_brackets_escaped_in_body(self):
        det = _nave_detector({"gen": {1: {1: ["A <b>bold</b> topic"]}}})
        (cand,) = det.detect("gen", 1, 1, "")
        assert "&lt;b&gt;" in cand.draft_body
        assert "<b>" not in cand.draft_body

    def test_plain_topics_byte_identical(self):
        det = _nave_detector({"heb": {11: {1: ["Faith", "Hope"]}}})
        (cand,) = det.detect("heb", 11, 1, "")
        assert "<strong>Topics.</strong> This verse appears under: Faith, Hope." == cand.draft_body
