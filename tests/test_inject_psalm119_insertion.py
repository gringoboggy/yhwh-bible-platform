"""Regression (mint-11 audit LOW): find_aside_insertion_point must order
asides correctly for 3-digit verses (Psalm 119 v100-176).

An aside id is ``note-{prefix}{ch:02d}{v:02d}{s}``, so Psalm 119:170 renders
``note-b30119170``. _aside_existing_re's greedy chapter group ``(\\d+)`` steals
a digit from the 3-digit verse (parsing it as ch=1191, v=70), so the old code
mis-sorted: a new high-verse note landed BEFORE the existing lower-verse asides
instead of in (verse, suffix) order. The fix re-splits the digits on the KNOWN
target chapter. This is latent today (the already-in short-circuit skips
re-injecting existing notes, so no EPUB byte change) but activates on a fresh
base-HTML regen or a new verse>=100 note.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts import inject  # noqa: E402


def _aside(prefix, ch, v, suffix=""):
    return f'<aside class="note note-comm" id="note-{prefix}{ch:02d}{v:02d}{suffix}" epub:type="footnote">v{v}</aside>'


def test_high_verse_insertion_lands_between_existing_asides():
    # Psalm 119 (prefix b30) region holding v103 and v170 in order.
    a1 = _aside("b30", 119, 103)
    a2 = _aside("b30", 119, 170)
    region = a1 + a2
    html = "<x>" + region + "</x>"
    start = html.index(a1)
    section = (start, start + len(region))

    # Insert v=150: must land BETWEEN v103 and v170, i.e. at a2's start
    # (just after a1's </aside>) — NOT at the region start (the pre-fix bug).
    pos = inject.find_aside_insertion_point(html, section, ch=119, v=150, suffix="", prefix="b30")
    assert pos == html.index(a2), f"v=150 should land between v103 and v170; got offset {pos}"
    assert pos > html.index(a1), "must not land before the lower-verse aside (the pre-fix bug)"


def test_low_verse_insertion_still_lands_first():
    # A genuinely-earlier verse still sorts before both.
    a1 = _aside("b30", 119, 103)
    a2 = _aside("b30", 119, 170)
    region = a1 + a2
    html = "<x>" + region + "</x>"
    start = html.index(a1)
    section = (start, start + len(region))
    pos = inject.find_aside_insertion_point(html, section, ch=119, v=50, suffix="", prefix="b30")
    assert pos == start, "v=50 precedes both v103 and v170, so it lands at the region start"
