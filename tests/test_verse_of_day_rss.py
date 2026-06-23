"""Security regression for the verse-of-the-day RSS feed.

The RSS ``<description>`` embeds a note body inside a CDATA section.
Note bodies are AI-authored and share the note store, and the feed is
unauthenticated, so an attacker-controlled body must not be able to:

  * smuggle executable markup (``<script>`` etc.) into a feed consumer, or
  * break out of the CDATA section with a literal ``]]>`` and inject raw XML.

``rss_feed`` must sanitize the body and neutralize ``]]>`` before it
reaches the description. See ``scripts/core/verse_of_day.py``.
"""

from __future__ import annotations

from scripts.core import verse_of_day


def _build_feed_with_body(monkeypatch, body_html: str) -> str:
    """Render a one-day feed whose single item carries ``body_html`` as
    the headline note body, bypassing the real corpus pick so the test
    is deterministic and independent of on-disk notes."""

    def fake_verse_of_day(date_iso=None, *, edition_id=None):
        return {
            "ref": "Genesis 1:1",
            "book_code": "gen",
            "book_title": "Genesis",
            "chapter": 1,
            "verse": 1,
            "notes": [
                {
                    "label": "Test note",
                    "body_html": body_html,
                }
            ],
        }

    monkeypatch.setattr(verse_of_day, "verse_of_day", fake_verse_of_day)
    return verse_of_day.rss_feed(days=1, today="2026-01-01")


def test_rss_description_strips_script(monkeypatch):
    """A ``<script>`` in the note body must not survive into the feed."""
    xml = _build_feed_with_body(monkeypatch, "<p>hello</p><script>alert(1)</script>")
    assert "<script>" not in xml
    assert "alert(1)" not in xml
    # Legitimate inline markup is preserved.
    assert "hello" in xml


def test_rss_description_neutralizes_cdata_breakout(monkeypatch):
    """A literal ``]]>`` in the body must be neutralized so it cannot close the
    CDATA section early and inject raw XML. round-11 gap-3: enforced once on the
    whole description by the ``_cdata`` chokepoint, not per field."""
    import xml.dom.minidom as minidom

    # the ]]> is followed by sanitizer-preserved markup, so a real breakout
    # would leave a stray </p> after the CDATA and make the doc UNPARSEABLE.
    xml = _build_feed_with_body(monkeypatch, "<p>x]]>y</p>")
    minidom.parseString(xml)  # must remain well-formed XML (no breakout)
    # the section still closes exactly at the template boundary
    assert "]]></description>" in xml


def test_cdata_chokepoint_round_trips_embedded_terminator():
    """``_cdata`` splits any embedded ``]]>`` transparently: the CDATA content
    reassembles to the exact payload, and the wrapped form parses as XML."""
    import xml.dom.minidom as minidom

    payload = "before]]>after <b>x</b>"
    wrapped = verse_of_day._cdata(payload)
    doc = minidom.parseString(f"<r>{wrapped}</r>")
    text = "".join(n.data for n in doc.documentElement.childNodes)
    assert text == payload
