# scripts/core/manuscript_collation.py
"""Pure dual-manuscript collation engine (Samuel Phase-2, τ.6.x.4.b).

Generalizes the proven Phase-1 calibration logic (the dropped
_build_*_collation.py builders) into a reusable pure function. No I/O.
Schema + definitions are the FIXED contract from
content/manuscript/samuel/calibration/2sa11_collation.json.
"""

from __future__ import annotations

import collections

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


def _flag_set(witness_record):
    """Set of (verse_idx, token_idx) flagged uncertain/illegible by the witness."""
    s = set()
    for vi, v in enumerate(witness_record["verses"]):
        for u in v.get("uncertain", []):
            s.add((vi, u["token_index"]))
    return s


def assert_token_conservation(verses, gg_rec, cam_rec):
    """Verify every evidence token appears exactly once in the aligned output.

    Intentional asymmetry: evidence-token counters include ``⟦illegible⟧``
    tokens; alignment counters exclude ``lacuna-*`` rows — this is correct
    because lacuna evidence tokens are legitimately absent from alignment cells.
    """
    ev_gg = collections.Counter(t for v in gg_rec["verses"] for t in v["tokens"])
    ev_cam = collections.Counter(t for v in cam_rec["verses"] for t in v["tokens"])
    al_gg = collections.Counter(
        a["gg"] for vv in verses for a in vv["alignment"] if a["gg"] != "" and not a["class"].startswith("lacuna")
    )
    al_cam = collections.Counter(
        a["cam"] for vv in verses for a in vv["alignment"] if a["cam"] != "" and not a["class"].startswith("lacuna")
    )
    assert ev_gg == al_gg, f"token-conservation GG drift: {ev_gg - al_gg!r} / {al_gg - ev_gg!r}"
    assert ev_cam == al_cam, f"token-conservation CAM drift: {ev_cam - al_cam!r} / {al_cam - ev_cam!r}"


def _pct(n, d) -> float:
    """Rounded percentage n/d*100; returns 0.0 when denominator is zero."""
    return round(n / d * 100, 2) if d else 0.0


def compute_metrics(verses, gg_rec, cam_rec, base):
    rows = [a for vv in verses for a in vv["alignment"]]
    agree = [a for a in rows if a["class"] == "agree"]
    dis = [a for a in rows if a["class"] == "disagree"]
    den = len(agree) + len(dis)
    strict_n = sum(1 for a in agree if is_strict(a["gg"], a["cam"]))
    # both-confident: both cells non-empty, neither flagged by its witness
    # NOTE — Task-4 seam: until Task-4's collate() attaches per-row gg_flag/cam_flag,
    # a.get(...) returns None (falsy), so every non-empty non-lacuna row counts as
    # confident and interim bc_rows == den.  This is INTENTIONAL.  The Task-5
    # regression oracle is the correctness anchor: it passes because collate() (Task 4)
    # attaches the real flags BEFORE calling compute_metrics.  Do NOT add
    # flag-derivation logic here to match any interim numbers — doing so would break
    # the Task-5 oracle.
    base_rec = cam_rec if base == "CAM" else gg_rec
    bc_rows = 0
    bc_agree = 0
    for vv in verses:
        for a in vv["alignment"]:
            if a["gg"] == "" or a["cam"] == "" or a["class"].startswith("lacuna"):
                continue
            conf = not a.get("gg_flag") and not a.get("cam_flag")
            if conf:
                bc_rows += 1
                if a["class"] == "agree":
                    bc_agree += 1
    sp = sum(1 for vv in verses if vv["semantic_pass"])
    ns = len(verses)
    base_tokens = sum(len(v["tokens"]) for v in base_rec["verses"])
    base_flagged = sum(1 for v in base_rec["verses"] for u in v.get("uncertain", []))
    return {
        "ww_agreement_pct": _pct(strict_n, den),
        "ww_agreement_basis": f"{strict_n}/{den}",
        "ww_agreement_skeleton_pct": _pct(len(agree), den),
        "ww_agreement_skeleton_basis": f"{len(agree)}/{den}",
        "ww_agreement_bothconfident_pct": _pct(bc_agree, bc_rows),
        "ww_agreement_bothconfident_basis": f"{bc_agree}/{bc_rows}",
        "semantic_pass_pct": _pct(sp, ns),
        "semantic_pass_basis": f"{sp}/{ns}",
        "uncertainty_pct": _pct(base_flagged, base_tokens),
        "uncertainty_basis": f"{base_flagged}/{base_tokens} (base={base})",
        "lacuna_counts": {
            "gg": sum(1 for v in gg_rec["verses"] for t in v["tokens"] if t == ILLEGIBLE),
            "cam": sum(1 for v in cam_rec["verses"] for t in v["tokens"] if t == ILLEGIBLE),
            "both": sum(1 for vv in verses for a in vv["alignment"] if a["class"] == "lacuna-both"),
        },
        "lacuna_counts_note": "",  # filled by collate() with the alignment-scheme prose
        "definitions": DEFINITIONS,
    }
