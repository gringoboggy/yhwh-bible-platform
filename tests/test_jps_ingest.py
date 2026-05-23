"""JPS 1917 (``jps``) ingest — Phase 2 translation spine.

FINDING (verified vs the real source, REFUTING the runbook's "JPS is Masoretic,
reuse wlc_to_kjv_map" assumption): eBible's ``engjps`` package is ALREADY
KJV-renumbered, NOT Masoretic. A full per-chapter probe of all 39 Tanakh books /
929 chapters vs the canonical KJV skeleton found 0 divergences, and the total is
exactly the KJV OT verse count (23,145). Every Masoretic-divergence locus is
KJV-numbered (Psalm superscriptions unnumbered: Ps 51 = 19 not 21; Joel = 3 ch
not 4; Malachi = 4 ch not 3; Gen 32 = 32 not 33). So JPS is a PURE IDENTITY
ingest — NO versification remap (applying the WLC Masoretic map would double-remap
and silently misplace every post-superscription Psalm verse).
"""

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
JPS_DIR = REPO / "content" / "translations" / "jps"
VPL = REPO / "content" / "translations" / "sources" / "jps" / "engjps_vpl.txt"


def _load(code):
    from scripts.core import translations as tx

    p = JPS_DIR / f"{code}.py"
    return tx.load_book_verses_from_text(p.read_text(encoding="utf-8")) if p.is_file() else None


class TestJpsIsKjvNumberedNotMasoretic:
    """Pin the verified finding: eBible JPS uses KJV numbering. Each assertion
    would FAIL under Masoretic numbering (or a wrong Masoretic remap)."""

    @pytest.mark.parametrize(
        "code,ch,kjv_count",
        [
            ("psa", 51, 19),  # Masoretic Ps 51 = 21 (superscription vv1-2); KJV = 19
            ("psa", 3, 8),  # Masoretic Ps 3 = 9; KJV = 8
            ("joe", 3, 21),  # Masoretic Joel = 4 chapters; KJV keeps joe 3 (21 v)
            ("mal", 4, 6),  # Masoretic Malachi = 3 chapters; KJV has mal 4 (6 v)
            ("gen", 32, 32),  # Masoretic Gen 32 = 33; KJV = 32
        ],
    )
    def test_kjv_chapter_shapes(self, code, ch, kjv_count):
        from scripts.core import translations as tx

        assert len(tx.get_chapter("jps", code, ch)) == kjv_count


class TestJpsIngest:
    """Integration: the committed on-disk jps store (identity, KJV-aligned)."""

    def test_39_tanakh_books(self):
        books = sorted(p.stem for p in JPS_DIR.glob("*.py"))
        assert len(books) == 39, f"expected 39 Tanakh books, got {len(books)}: {books}"

    def test_total_is_kjv_ot_count_identity(self):
        from scripts.extract_translation import parse_vpl

        src_total = sum(len(v) for v in parse_vpl(VPL).values())
        on_disk = sum(len(_load(p.stem) or []) for p in JPS_DIR.glob("*.py"))
        # identity ingest: no merges, no drops; equals the KJV Old-Testament verse count
        assert on_disk == src_total == 23145

    def test_all_coords_in_canonical_extent(self):
        from scripts.core.canonical_verse_counts import coord_in_canonical_extent

        bad = [
            (p.stem, c, v)
            for p in JPS_DIR.glob("*.py")
            for (c, v, _t) in (_load(p.stem) or [])
            if not coord_in_canonical_extent(p.stem, c, v)
        ]
        assert bad == [], f"out-of-extent coords: {bad[:20]}"

    def test_spot_checks_present(self):
        from scripts.core import translations as tx

        assert tx.get_verse("jps", "gen", 1, 1)
        assert tx.get_verse("jps", "psa", 23, 1)
        assert tx.get_verse("jps", "isa", 53, 5)
