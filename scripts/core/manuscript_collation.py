# scripts/core/manuscript_collation.py
"""Pure dual-manuscript collation engine (Samuel Phase-2, τ.6.x.4.b).

Generalizes the proven Phase-1 calibration logic (the dropped
_build_*_collation.py builders) into a reusable pure function. No I/O.
Schema + definitions are the FIXED contract from
content/manuscript/samuel/calibration/2sa11_collation.json.
"""

from __future__ import annotations

DEFINITIONS = {
    "strict": "exact literal token-string identity / (agree+disagree) aligned pairs",
    "skeleton": "diacritic/order-folded + near-homograph-folded token equality (class==agree) / (agree+disagree) aligned pairs, full aligned denominator",
    "both_confident": "skeleton-equal / aligned pairs where neither witness flagged that token uncertain or illegible (gap/insertion cells and lacuna rows also excluded from this denominator)",
}
ILLEGIBLE = "⟦illegible⟧"  # ⟦illegible⟧


# Ge'ez fidel → consonant base (orders 1..7 collapse). Built from the
# Ethiopic block: each 8-codepoint row shares a consonant; fold to row head.
def _fold_char(ch: str) -> str:
    o = ord(ch)
    if 0x1200 <= o <= 0x135A:  # Ethiopic syllables
        return chr(0x1200 + ((o - 0x1200) // 8) * 8)
    return ch


def fold_skeleton(token: str) -> str:
    """Diacritic/order-folded + light near-homograph-folded form."""
    if token == ILLEGIBLE or token == "":
        return token
    folded = "".join(_fold_char(c) for c in token)
    # near-homograph classes (laryngeals/sibilants that scribes interchange)
    for cls in ("ሀሐጀ", "ሰሸ", "ዐአ"):
        head = cls[0]
        for c in cls[1:]:
            folded = folded.replace(c, head)
    return folded


def is_strict(gg: str, cam: str) -> bool:
    return gg != "" and cam != "" and gg == cam


def classify_pair(gg: str, cam: str) -> str:
    if gg == "" or cam == "":
        return "disagree"  # one-sided recensional/scribal minus
    if gg == ILLEGIBLE and cam == ILLEGIBLE:
        return "lacuna-both"
    if gg == ILLEGIBLE:
        return "lacuna-gg"
    if cam == ILLEGIBLE:
        return "lacuna-cam"
    return "agree" if fold_skeleton(gg) == fold_skeleton(cam) else "disagree"
