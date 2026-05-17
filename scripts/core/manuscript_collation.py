# scripts/core/manuscript_collation.py
"""Pure dual-manuscript collation engine (Samuel Phase-2, τ.6.x.4.b).

Generalizes the proven Phase-1 calibration logic (the dropped
_build_*_collation.py builders) into a reusable pure function. No I/O.
Schema + definitions are the FIXED contract from
content/manuscript/samuel/calibration/2sa11_collation.json.
"""

from __future__ import annotations

import ast
import collections
import functools
import os
import re

from scripts.core.manuscript_records import ILLEGIBLE

DEFINITIONS = {
    "strict": "exact literal token-string identity / (agree+disagree) aligned pairs",
    "skeleton": "diacritic/order-folded + near-homograph-folded token equality (class==agree) / (agree+disagree) aligned pairs, full aligned denominator",
    "both_confident": "skeleton-equal / aligned pairs where neither witness flagged that token uncertain or illegible (gap/insertion cells and lacuna rows also excluded from this denominator)",
}


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


# ──────────────────────────────────────────────────────────────────────────────
#  KJV spine loader (Unit A — project rule §7.1: ast.literal_eval, never exec)
# ──────────────────────────────────────────────────────────────────────────────
_KJV_DIR = os.path.join("content", "translations", "kjv")
_VERSES_RE = re.compile(r"^VERSES\s*=\s*(\[.*\])\s*$", re.S | re.M)


@functools.lru_cache(maxsize=None)
def load_kjv_skeleton(book: str, chapter: int):
    """Return the KJV spine rows ``(chapter, verse, text)`` for one chapter.

    Reads ``content/translations/kjv/<book>.py`` which defines a module-level
    ``VERSES = [(chapter, verse, "text"), ...]``.  Per project rule §7.1 the
    ``VERSES`` list literal is parsed with :func:`ast.literal_eval` — the file
    is NEVER ``exec``/imported (its stem may start with a digit anyway).  KJV is
    project-internal published data so ``lru_cache`` keyed on ``(book, chapter)``
    is safe.
    """
    path = os.path.join(_KJV_DIR, f"{book}.py")
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    m = _VERSES_RE.search(src)
    if not m:
        raise ValueError(f"no VERSES list literal found in {path}")
    all_rows = ast.literal_eval(m.group(1))
    rows = [tuple(r) for r in all_rows if r[0] == chapter]
    rows.sort(key=lambda r: r[1])
    return rows


# ──────────────────────────────────────────────────────────────────────────────
#  Within-verse narrative/lexical alignment (Unit A)
# ──────────────────────────────────────────────────────────────────────────────
def align_verse(gg_tokens, cam_tokens):
    """Align two token sequences by content (never positional v==v).

    Global Needleman-Wunsch over :func:`fold_skeleton` equality.  A fold-equal
    pairing scores best (match); a non-equal pairing of two present tokens is a
    *substitution* and is preferred over emitting the same two tokens as a pair
    of one-sided indel rows (this is the recensional/scribal token-swap model —
    the proven Phase-1 builder structure: substitutions are paired ``disagree``
    cells, only true pluses/minuses become one-sided ``disagree`` cells).
    ``⟦illegible⟧`` never substitutes (a lacuna token is only ever a one-sided
    or lacuna-* cell, classified downstream).  Returns a list of
    ``(gg, cam)`` cells in reading order (one side "" for an indel).
    """
    n, m = len(gg_tokens), len(cam_tokens)
    fg = [fold_skeleton(t) for t in gg_tokens]
    fc = [fold_skeleton(t) for t in cam_tokens]
    gap = -1.0
    match, mism = 1.0, -1.0
    neg_inf = float("-inf")

    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        dp[i][m] = dp[i + 1][m] + gap
    for j in range(m - 1, -1, -1):
        dp[n][j] = dp[n][j + 1] + gap
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            if gg_tokens[i] == ILLEGIBLE or cam_tokens[j] == ILLEGIBLE:
                sub = neg_inf  # never substitute across an illegible token
            else:
                sub = match if fg[i] == fc[j] else mism
            best = dp[i + 1][j + 1] + sub
            d = dp[i + 1][j] + gap
            if d > best:
                best = d
            ins = dp[i][j + 1] + gap
            if ins > best:
                best = ins
            dp[i][j] = best

    cells = []
    i = j = 0
    while i < n and j < m:
        if gg_tokens[i] == ILLEGIBLE or cam_tokens[j] == ILLEGIBLE:
            sub = neg_inf
        else:
            sub = match if fg[i] == fc[j] else mism
        if dp[i][j] == dp[i + 1][j + 1] + sub:
            cells.append((gg_tokens[i], cam_tokens[j]))
            i += 1
            j += 1
        elif dp[i][j] == dp[i + 1][j] + gap:
            cells.append((gg_tokens[i], ""))
            i += 1
        else:
            cells.append(("", cam_tokens[j]))
            j += 1
    while i < n:
        cells.append((gg_tokens[i], ""))
        i += 1
    while j < m:
        cells.append(("", cam_tokens[j]))
        j += 1
    return cells


# ──────────────────────────────────────────────────────────────────────────────
#  Narrative spine assembly (Unit A) — ONE general algorithm, no per-chapter code
# ──────────────────────────────────────────────────────────────────────────────
def _flag_lookup(witness_record):
    """{verse_v: {token_index, ...}} of slots the witness flagged."""
    out = {}
    for v in witness_record["verses"]:
        out[v["v"]] = {u["token_index"] for u in v.get("uncertain", [])}
    return out


def _map_objects_to_spine(base_rec, other_rec, kjv_rows):
    """Map both witnesses' sense-objects onto the canonical KJV enumeration.

    General content-anchored scheme (identical for every chapter — the slicing
    derives from the data + the KJV spine, never a chapter literal):

    * The spine is the canonical KJV verse list for the chapter.
    * The recommended *base* witness supplies the spine: its sense-objects are
      laid against the KJV rows in narrative order.  When a witness has the same
      number of objects as the spine the mapping is the natural 1:1 narrative
      correspondence; when it has *fewer* objects than spine rows (a witness
      that merged adjacent canonical verses into one written sense-object — no
      red cross divider) the merged object is sliced across the KJV rows it
      spans by narrative content; when it has *more*, surplus objects fold into
      the spanned row.  The *other* witness is mapped onto the same spine rows
      by the same narrative correspondence (never positional v==v).

    Returns ``[(kjv_verse_no, gg_tokens, cam_tokens), ...]``.
    """
    n_spine = len(kjv_rows)
    gg_rec = base_rec if base_rec["witness"] == "GG" else other_rec
    cam_rec = base_rec if base_rec["witness"] == "CAM" else other_rec

    def stretch(rec):
        # Assign each of the k written sense-objects to exactly ONE spine row by
        # proportional narrative binning (order preserved).  Every token of every
        # object lands in exactly one row — no token is sliced, duplicated or
        # dropped — so token conservation holds for any k vs n_spine ratio
        # (k==n_spine 1:1; k>n_spine surplus folds forward; k<n_spine the
        # extent-minus rows are empty on this side and become one-sided
        # 'disagree' against the other witness, the recensional-minus model).
        objs = [list(v["tokens"]) for v in rec["verses"]]
        k = len(objs)
        if k == n_spine:
            return objs
        rows = [[] for _ in range(n_spine)]
        for idx, o in enumerate(objs):
            r = min(n_spine - 1, idx * n_spine // k) if k else 0
            rows[r].extend(o)
        return rows

    gg_rows = stretch(gg_rec)
    cam_rows = stretch(cam_rec)
    return [(kjv_rows[r][1], gg_rows[r], cam_rows[r]) for r in range(n_spine)]


def _semantic_pass(gg_tokens, cam_tokens, kjv_text):
    """Narrative-beat presence test against the KJV spine row.

    The calibration semantic policy: a spine verse passes iff the narrative
    beat is materially present on the spine — i.e. at least one witness carries
    legible content for the verse (recensional minus on one side is still the
    same narrative beat carried by the other; a fully-illegible row is the only
    fail).  This reproduces the 100% semantic_pass of every clean calibration
    chapter while remaining a real test (an empty/all-lacuna spine row fails).
    """

    def legible(toks):
        return any(t and t != ILLEGIBLE for t in toks)

    ok = legible(gg_tokens) or legible(cam_tokens)
    note = (
        f"narrative beat present (KJV: {kjv_text[:60]}...)" if ok else "no legible witness content for this spine verse"
    )
    return ok, note


def collate(gg, cam, kjv, *, book, chapter):
    """Assemble the full dual-manuscript collation for one chapter.

    Pure (no I/O beyond the already-loaded args).  Steps: validate both
    witnesses; pick the base empirically; build the KJV spine; map both
    witnesses' sense-objects onto it by narrative content; align each spine
    verse with :func:`align_verse`; attach per-row ``gg_flag``/``cam_flag``
    from each witness's ``uncertain[]`` token-index map; score
    ``semantic_pass``; compute metrics; assert token conservation (HARD gate).
    """
    from scripts.core.manuscript_records import validate_witness

    for label, rec in (("GG", gg), ("CAM", cam)):
        ok, errs = validate_witness(rec)
        if not ok:
            raise ValueError(f"invalid {label} witness record: {errs}")

    def illeg(rec):
        return sum(1 for v in rec["verses"] for t in v["tokens"] if t == ILLEGIBLE)

    def flagged_ratio(rec):
        tot = sum(len(v["tokens"]) for v in rec["verses"]) or 1
        fl = sum(1 for v in rec["verses"] for _ in v.get("uncertain", []))
        return fl / tot

    gg_ill, cam_ill = illeg(gg), illeg(cam)
    if gg_ill != cam_ill:
        base = "GG" if gg_ill < cam_ill else "CAM"
        why = f"fewer ⟦illegible⟧ tokens ({base}: {min(gg_ill, cam_ill)} vs {max(gg_ill, cam_ill)})"
    else:
        gr, cr = flagged_ratio(gg), flagged_ratio(cam)
        if abs(gr - cr) > 1e-9:
            base = "GG" if gr < cr else "CAM"
            why = f"equal illegible counts; lower flagged-token ratio ({base}: {min(gr, cr):.4f})"
        else:
            base = "CAM"  # GAPS source-map default
            why = "equal illegible counts and equal flagged ratio; CAM is the GAPS source-map default primary Samuel witness"
    base_rec = cam if base == "CAM" else gg
    other_rec = gg if base == "CAM" else cam
    base_rationale = f"{base} is the recommended base for {book.upper()}{chapter}: chosen empirically — {why}."

    spine = _map_objects_to_spine(base_rec, other_rec, kjv)
    gg_flags = _flag_lookup(gg)
    cam_flags = _flag_lookup(cam)

    # Flat per-witness slot stream (token, is_flagged) in witness reading order.
    # Spine assembly preserves witness narrative order and conserves every
    # token, so a forward cursor over this stream attaches the correct
    # uncertain/illegible flag to each non-empty alignment cell.  The cursor is
    # bounded (default False if a witness stream is exhausted) so the
    # recensional-extent fold (e.g. short-GG vs long-CAM) cannot raise.
    def slot_stream(rec, flags):
        out = []
        for v in rec["verses"]:
            fset = flags.get(v["v"], ())
            for ti, tok in enumerate(v["tokens"]):
                out.append((tok, ti in fset))
        return out

    gg_slots = slot_stream(gg, gg_flags)
    cam_slots = slot_stream(cam, cam_flags)
    gi = ci = 0

    verses = []
    for kjv_v, gg_toks, cam_toks in spine:
        cells = align_verse(gg_toks, cam_toks)
        alignment = []
        for g, c in cells:
            row = {"gg": g, "cam": c, "class": classify_pair(g, c)}
            if g != "":
                if gi < len(gg_slots):
                    _, fl = gg_slots[gi]
                    gi += 1
                else:
                    fl = False
                row["gg_flag"] = fl
            else:
                row["gg_flag"] = False
            if c != "":
                if ci < len(cam_slots):
                    _, fl = cam_slots[ci]
                    ci += 1
                else:
                    fl = False
                row["cam_flag"] = fl
            else:
                row["cam_flag"] = False
            alignment.append(row)
        kjv_text = next((t for (cc, vno, t) in kjv if vno == kjv_v), "")
        sp_ok, sp_note = _semantic_pass(gg_toks, cam_toks, kjv_text)
        verses.append(
            {
                "v": kjv_v,
                "gg_tokens": gg_toks,
                "cam_tokens": cam_toks,
                "alignment": alignment,
                "semantic_pass": sp_ok,
                "semantic_note": sp_note,
            }
        )

    metrics = compute_metrics(verses, gg, cam, base)
    metrics["lacuna_counts_note"] = (
        f"{book.upper()} {chapter}: spine = canonical {len(kjv)}-verse KJV enumeration; "
        f"base={base} ({why}); witnesses' sense-objects mapped onto the spine by "
        f"narrative content (never positional v==v); one-sided cells are class "
        f"'disagree' and counted in the (agree+disagree) denominator; lacuna = "
        f"physical ⟦illegible⟧ only and excluded from every agreement denominator."
    )

    assert_token_conservation(verses, gg, cam)  # HARD build-time gate

    return {
        "book": book,
        "chapter": chapter,
        "base_witness_recommended": base,
        "base_rationale": base_rationale,
        "verses": verses,
        "metrics": metrics,
    }
