"""Machine pins for the versification claims MATRIX_MAP records as "verified
manually" (round-7 laundry item 4, turn-66 board).

Three claims, three pins:

  (a) ``parse_versemap`` surfaces the Psalm-superscription renumbering (the WLC
      counts the title as Hebrew verse 1, so the body runs +1 vs the KJV).
  (b) ``wlc_to_kjv_map`` carries the Genesis 31/32 chapter-boundary shift
      (WLC Gen 32:1 = KJV Gen 31:55).
  (c) the hand-built LXX map carries Jeremiah's Oracles-Against-the-Nations
      reorder (Swete Jer 27 = KJV Jer 50, the Babylon oracle).

(a)/(b) read the REAL morphhb ``VerseMap.xml`` from the out-of-repo source tree
(``_acquire/morphhb/wlc`` — present on both dev boxes, absent on CI runners), so
they skip with a visible reason where the source data is missing; (c) is pure
in-repo code and runs everywhere.
"""

from __future__ import annotations

import pytest

from scripts.core import versification as vsf
from scripts.extract_wlc_morphhb import DEFAULT_SOURCE

_VERSEMAP = DEFAULT_SOURCE / "VerseMap.xml"

needs_versemap = pytest.mark.skipif(
    not _VERSEMAP.is_file(),
    reason="morphhb VerseMap.xml not on this box (out-of-repo dev-box source data)",
)


@needs_versemap
def test_parse_versemap_returns_psalm_superscription_pair():
    entries = vsf.parse_versemap(_VERSEMAP)
    # Psalm 3: the WLC counts the superscription as Hebrew verse 1, so WLC 3:2
    # is KJV 3:1 — the exact pair the module docstring + MATRIX_MAP cite ...
    assert (("Ps", 3, 2), ("Ps", 3, 1), "full") in entries
    # ... and the offset persists to the psalm's last verse (WLC 3:9 = KJV 3:8).
    assert (("Ps", 3, 9), ("Ps", 3, 8), "full") in entries


@needs_versemap
def test_wlc_to_kjv_map_contains_gen_31_32_boundary():
    mapping = vsf.wlc_to_kjv_map(_VERSEMAP)
    # The Masoretic chapter break: WLC Gen 32:1 is KJV Gen 31:55, so the whole
    # WLC chapter 32 runs one verse ahead of the KJV.
    assert mapping[("Gen", 32, 1)] == ("Gen", 31, 55)
    assert mapping[("Gen", 32, 2)] == ("Gen", 32, 1)


def test_lxx_map_contains_jeremiah_oan_reorder():
    # The LXX places the Oracles Against the Nations mid-book: Swete Jer 27/28
    # are the Babylon oracles = KJV Jer 50/51, while KJV Jer 27's content sits
    # at Swete 34 — all whole-chapter ``_JER_SEGMENTS`` relocations.
    assert vsf.lxx_swete_to_kjv("Jer", 27, 1) == ("jer", 50, 1)
    assert vsf.lxx_swete_to_kjv("Jer", 28, 1) == ("jer", 51, 1)
    assert vsf.lxx_swete_to_kjv("Jer", 34, 1) == ("jer", 27, 2)
