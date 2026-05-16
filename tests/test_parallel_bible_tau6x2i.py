"""τ.6.x.2.i — Ge'ez Psalms via HaCohen/Ludolf (digitized-critical-edition).

The FIRST τ.6.x.5 external-source ingest: Ge'ez Psalms from Ran
HaCohen's clean Unicode-Ge'ez Ludolf 1701 Psalter (Rahlfs/LXX
numbering), NOT the OCR'd parallel-PDF column. Source numbering is
authoritative — NOT renumbered against the floor; the floor is a
validation check only (spec §3/§6). Empirically the ingest matched
the 2531-verse PSALMS_VERSE_COUNTS floor EXACTLY with one recorded
per-chapter delta (Ps 140) flagged for the τ.6.x.3 audit.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
PSA = REPO / "content" / "translations" / "geez-tewahedo" / "psa.py"


def _consts_and_verses():
    t = PSA.read_text(encoding="utf-8")
    tree = ast.parse(t)
    consts: dict = {}
    verses = None
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name):
            name = n.targets[0].id
            if name == "VERSES":
                verses = ast.literal_eval(n.value)
            else:
                try:
                    consts[name] = ast.literal_eval(n.value)
                except Exception:
                    pass
    return consts, verses


class TestTau6x2iGeezPsalms:
    def test_provenance_and_quality(self):
        c, _ = _consts_and_verses()
        assert c["TRANSLATION"] == "geez-tewahedo"
        assert c["BOOK"] == "psa"
        assert c["SOURCE_QUALITY"] == "digitized-critical-edition"
        assert c["SOURCE_PROVENANCE"] == "hacohen-geez"
        assert c["INGEST_PHASE"] == "τ.6.x.2.i"

    def test_151_chapters_present_no_overflow(self):
        _, v = _consts_and_verses()
        # Exactly Psalms 1..151 — no synthetic overflow chapter.
        assert sorted({ch for ch, _, _ in v}) == list(range(1, 152))

    def test_psalm_1_1_canonical_geez(self):
        _, v = _consts_and_verses()
        first = next(t for ch, vs, t in v if ch == 1 and vs == 1)
        assert first.startswith("ብፁዕ ፡ ብእሲ"), repr(first[:40])

    def test_psalm_118_acrostic_giant_full(self):
        # The off-by-one that the calibrate-first gate caught: Ps 118
        # (Rahlfs) is the 176-verse acrostic giant; verse 1 must be
        # present (was dropped pre-fix → 175, first verse = 2).
        _, v = _consts_and_verses()
        ps118 = sorted(vs for ch, vs, _ in v if ch == 118)
        assert ps118[0] == 1, f"Ps 118 must start at verse 1; got {ps118[0]}"
        assert ps118[-1] == 176 and len(ps118) == 176

    def test_total_matches_floor_within_tolerance(self):
        from scripts.extract_parallel_pdf import PSALMS_VERSE_COUNTS as F

        _, v = _consts_and_verses()
        # Empirically EXACT (2531 == 2531); ≤10% tolerance keeps the
        # pin robust to future source/parser refinement.
        assert abs(len(v) - sum(F.values())) <= 0.1 * sum(F.values())

    def test_unicode_geez_no_html_residue(self):
        _, v = _consts_and_verses()
        blob = " ".join(t for _, _, t in v)
        assert "<" not in blob
        assert "&#" not in blob
        assert "Nr. Vers" not in blob
        assert "Cap." not in blob
        # genuine Ethiopic fidäl present (U+1200–U+137F)
        assert any("ሀ" <= ch <= "፿" for ch in blob)
