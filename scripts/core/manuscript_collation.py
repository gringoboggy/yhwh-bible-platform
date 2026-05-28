# scripts/core/manuscript_collation.py
"""Pure dual-manuscript collation engine (Samuel Phase-2, τ.6.x.4.b).

Generalizes the proven Phase-1 calibration logic (the dropped
_build_*_collation.py builders) into a reusable pure function. No I/O.
Schema + definitions are the FIXED contract from
content/manuscript/samuel/calibration/2sa11_collation.json.

ARCHITECTURE — ENGINE vs HUMAN CALIBRATION (Task 5 — τ.6.x.4.b,
spec-revision 2026-05-17 §3). This module is the deterministic *forward*
collator: one general, token-conserving algorithm (no per-chapter
hard-coding) that maps two witness records onto the canonical KJV spine and
measures agreement honestly. The four calibration ``*_collation.json``
(1sa1/1sa3/1sa17/2sa11) are immutable *human philological reference*: their
``alignment[]`` is per-token human adjudication, produced during a
measurement exercise, that yielded the 2026-05-17 GO (diplomatic-parallel,
base=CAM). That hand adjudication is INTENTIONALLY NOT machine-reproduced —
it is an answer key, not an algorithm (proven thrice: no pure ``f(gg,cam)``
can match 1sa1, which hand-demotes fold-identical pairs while promoting
fold-different ones, and the four chapters demand contradictory thresholds).
The engine's strict/skeleton/both-confident bases are therefore its OWN
honest, reproducible measurement — distinct from, and never claimed equal
to, the hand counts (cf. spec-revision §3.2 R8: agreement % is not a
pass/fail oracle). The engine's correctness on those four chapters is the
*reproducible* invariant contract (spec-revision §3.2 R1-R9): evidence
validity, token-conservation (HARD gate), exact semantic-pass, exact
lacuna-counts, base=CAM by the honest §3.3 rule + decision of record,
byte-stable ``definitions``, and the structural failure-modes — all of
which the engine does satisfy 4/4.
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
    # NOTE — collate() seam: compute_metrics is pure over the rows it is
    # given. collate() attaches the real per-row gg_flag/cam_flag (from each
    # witness's uncertain[] map) BEFORE calling this; if a caller passes rows
    # without those flags, a.get(...) is None (falsy) so every non-empty
    # non-lacuna row counts as confident (interim bc_rows == den). That is
    # INTENTIONAL. The correctness anchor is the R1-R9 calibration-invariant
    # contract (TestCalibrationInvariants), which exercises the real flags via
    # collate(). Do NOT add flag-derivation logic here to match any interim
    # numbers — flagging is collate()'s responsibility, not compute_metrics'.
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


@functools.cache
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


def _pick_base(gg_rec, cam_rec):
    """Honest base-pick (spec-revision 2026-05-17 §3.3). Two clauses + a
    decision of record; NO illegible/flagged-ratio derivation, NO fitted
    threshold. base=CAM is the user-ratified project decision
    (dev/CALIBRATION_2026-05-16-samuel-widened.md §4 'Decision (user)',
    2026-05-17 GO). Returns (base, rationale)."""
    gv = len(gg_rec["verses"])
    cv = len(cam_rec["verses"])
    bigger, smaller = max(gv, cv), min(gv, cv)
    # Clause 1: materially-different extent -> the more complete recension.
    if bigger and smaller < 0.70 * bigger:
        base = "GG" if gv > cv else "CAM"
        rationale = (
            f"{base} transmits the more complete recension "
            f"(GG {gv}v vs CAM {cv}v; shorter < 0.70x longer -> material "
            f"extent split, spec-revision 2026-05-17 §3.3 clause 1). "
            f"base=CAM remains the project decision of record "
            f"(2026-05-17 GO)."
        )
        # Clause 3 safeguard: a non-CAM clause-1 pick is surface-to-user.
        if base != "CAM":
            rationale += (
                " SURFACE-TO-USER: clause 1 selected a non-CAM base; flag "
                "for the user, never a silent flip (§3.3 clause 3)."
            )
        return base, rationale
    # Clause 2: otherwise base = CAM, asserted as the decision of record.
    return "CAM", (
        "CAM by the project decision of record "
        "(dev/CALIBRATION_2026-05-16-samuel-widened.md §4 'Decision "
        "(user)'; base=CAM ratified project-wide by the 2026-05-17 GO; "
        "spec-revision 2026-05-17 §3.3 clause 2) - extents not materially "
        f"different (GG {gv}v / CAM {cv}v)."
    )


def collate(gg, cam, kjv, *, book, chapter):
    """Assemble the full dual-manuscript collation for one chapter.

    Pure (no I/O beyond the already-loaded args).  Steps: validate both
    witnesses; pick the base via the honest two-clause + decision-of-record
    rule (:func:`_pick_base`, spec-revision 2026-05-17 §3.3); build the KJV
    spine; map both
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

    base, rationale = _pick_base(gg, cam)
    base_rec = cam if base == "CAM" else gg
    other_rec = gg if base == "CAM" else cam
    base_rationale = rationale

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
        f"base={base} ({base_rationale}); witnesses' sense-objects mapped onto the spine by "
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


def _classify_apparatus(other_tok: str, base_tok: str) -> str:
    """Classify one base-structured apparatus cell (Phase A2).

    Cell semantics: ``base_tok`` is the base witness's token, ``other_tok`` the
    other witness's aligned token; ``""`` marks an indel on that side. Yields
    exactly the class set {agree, disagree, lacuna, insertion}:

    * either side illegible -> ``"lacuna"`` (a physical ⟦illegible⟧ slot);
    * both present (neither illegible) -> ``"agree"`` if fold-equal else
      ``"disagree"``;
    * other present, base empty -> ``"insertion"`` (other adds a token the
      base lacks);
    * other empty, base present -> ``"disagree"`` (base token the other omits:
      one-sided recensional minus; never ``"lacuna"``).
    """
    if other_tok == ILLEGIBLE or base_tok == ILLEGIBLE:
        return "lacuna"
    if other_tok != "" and base_tok != "":
        return "agree" if fold_skeleton(other_tok) == fold_skeleton(base_tok) else "disagree"
    if other_tok != "" and base_tok == "":
        return "insertion"
    # other_tok == "" and base_tok != ""
    return "disagree"


def collate_base_structured(gg, cam, *, book, chapter):
    """Return the base witness's own sense-units as primary verses (Phase A1)
    with the other witness aligned to them as a per-verse apparatus (Phase A2).

    Does NOT map onto the KJV spine. Primary verses are the base witness's own
    sense-objects in reading order (A1). The OTHER witness is aligned to that
    spine by a SINGLE whole-chapter Ge'ez↔Ge'ez token alignment
    (:func:`align_verse`), and each aligned cell is attributed to the base verse
    its base token belongs to (A2 ``apparatus``). No metrics / agreement % /
    KJV-coverage are built here — that is A3. Pure (no I/O beyond the
    already-loaded args).
    """
    from scripts.core.manuscript_records import validate_witness

    for label, rec in (("GG", gg), ("CAM", cam)):
        ok, errs = validate_witness(rec)
        if not ok:
            raise ValueError(f"invalid {label} witness record: {errs}")

    base, rationale = _pick_base(gg, cam)
    base_rec = cam if base == "CAM" else gg
    other_rec = gg if base == "CAM" else cam

    primary_verses = [
        {
            "geez_v": v["v"],
            "geez_text": v["geez"],
            "tokens": list(v["tokens"]),
        }
        for v in base_rec["verses"]
    ]

    # Flat base-token stream WITH verse attribution (primary_verses order) and
    # the flat other-token stream in reading order.
    base_stream = [(verse_idx, tok) for verse_idx, pv in enumerate(primary_verses) for tok in pv["tokens"]]
    base_flat = [tok for (_, tok) in base_stream]
    other_flat = [tok for v in other_rec["verses"] for tok in v["tokens"]]

    # Align the WHOLE chapter ONCE. align_verse's first positional arg is the
    # OTHER witness's tokens, the second the BASE witness's tokens, so each
    # returned cell is (other_tok, base_tok) with "" for an indel.
    cells = align_verse(other_flat, base_flat)

    # Walk the cells, attributing each to the base verse its base token belongs
    # to (a GG/other insertion attaches to the preceding base verse).
    bi = 0
    for other_tok, base_tok in cells:
        if base_tok != "":
            verse_idx = base_stream[bi][0]
            bi += 1
        else:
            verse_idx = base_stream[bi - 1][0] if bi > 0 else 0
        cls = _classify_apparatus(other_tok, base_tok)
        primary_verses[verse_idx].setdefault("apparatus", []).append(
            {"base": base_tok, "other": other_tok, "class": cls}
        )

    # Sanity guard: every base token consumed exactly once (do not silently
    # continue on drift).
    if bi != len(base_stream):
        raise AssertionError(f"base-token cursor drift: consumed {bi} of {len(base_stream)} base tokens")

    # Ensure EVERY primary verse carries an apparatus key (default [] for any
    # verse that received no cells).
    for pv in primary_verses:
        pv.setdefault("apparatus", [])

    return {
        "book": book,
        "chapter": chapter,
        "base_witness": base,
        "base_rationale": rationale,
        "primary_verses": primary_verses,
    }


def tokens_conserved(out, gg, cam) -> bool:
    """Every evidence token of BOTH witnesses — INCLUDING ⟦illegible⟧ sentinels
    — appears exactly once across the base-structured apparatus cells (Phase A2).

    The base witness's tokens appear as each cell's ``base``; the other
    witness's as ``other`` ("" indels are not evidence tokens and are excluded).
    For 1ki6 this holds with GG 433==433 and CAM 500==500.
    """
    ev_gg = collections.Counter(t for v in gg["verses"] for t in v["tokens"])
    ev_cam = collections.Counter(t for v in cam["verses"] for t in v["tokens"])
    ap_gg = collections.Counter(c["other"] for pv in out["primary_verses"] for c in pv["apparatus"] if c["other"] != "")
    ap_cam = collections.Counter(c["base"] for pv in out["primary_verses"] for c in pv["apparatus"] if c["base"] != "")
    return ev_gg == ap_gg and ev_cam == ap_cam


# ──────────────────────────────────────────────────────────────────────────────
#  R8 — engine-vs-hand honest divergence (spec-revision 2026-05-17 §3.2 R8).
#  A PURE no-I/O-to-disk-write helper: it reads the immutable calibration
#  reference (json.load only, NO writes anywhere, NO script, NO markdown
#  artifact) and returns the engine's OWN measurement beside the hand
#  calibration's, with an explicit non-equality statement.  This is the
#  reference-comparison surface for the Task-8 QA `engine_vs_hand_divergence`
#  check; it never asserts engine == hand.
# ──────────────────────────────────────────────────────────────────────────────
_R8_CASES = (
    ("1sa1", "_collation_hires", 1, "1sa"),
    ("1sa3", "_collation", 3, "1sa"),
    ("1sa17", "_collation", 17, "1sa"),
    ("2sa11", "_collation", 11, "2sa"),
)

_R8_CAL_DIR = os.path.join("content", "manuscript", "samuel", "calibration")

_HONEST_DIVERGENCE_STATEMENT = (
    "The engine's strict/skeleton/both-confident are a reproducible "
    "deterministic measurement that intentionally differs from the "
    "per-token human philological adjudication in the immutable "
    "calibration collations, which already produced the 2026-05-17 GO "
    "(diplomatic-parallel, base=CAM). The engine reproduces semantic-pass, "
    "lacuna-counts and base exactly; agreement % is the engine's own "
    "honest metric, surfaced by the QA tool and read against the design-"
    "spec §4 reference bar - it is NOT a claim of equality with the hand "
    "calibration and is never claimed equal."
)


def engine_vs_hand_report():
    """Engine-vs-hand honest divergence report (spec-revision §3.2 R8).

    For each calibration ref, run the engine (:func:`collate`) and read the
    immutable hand ``*_collation.json`` ``metrics`` verbatim, returning a
    dict ``{"chapters": {ref: {"engine": {...}, "hand": {...}}},
    "honest_divergence_statement": <str>}``.  Pure: ``json.load`` reads of
    the immutable reference only — NO writes anywhere, NO separate script,
    NO committed markdown.  REPORTS the delta; never asserts engine == hand.
    """
    import json

    chapters = {}
    for ref, suf, ch, book in _R8_CASES:
        with open(os.path.join(_R8_CAL_DIR, f"{ref}_witnessGG.json"), encoding="utf-8") as fh:
            gg = json.load(fh)
        with open(os.path.join(_R8_CAL_DIR, f"{ref}_witnessCAM_hires.json"), encoding="utf-8") as fh:
            cam = json.load(fh)
        with open(os.path.join(_R8_CAL_DIR, f"{ref}{suf}.json"), encoding="utf-8") as fh:
            hand = json.load(fh)
        got = collate(gg, cam, load_kjv_skeleton(book, ch), book=book, chapter=ch)
        em = got["metrics"]
        hm = hand["metrics"]
        chapters[ref] = {
            "engine": {
                "strict_basis": em["ww_agreement_basis"],
                "skeleton_basis": em["ww_agreement_skeleton_basis"],
                "bothconfident_basis": em["ww_agreement_bothconfident_basis"],
                "semantic_pass_basis": em["semantic_pass_basis"],
                "lacuna_counts": em["lacuna_counts"],
                "base": got["base_witness_recommended"],
            },
            "hand": {
                "strict_basis": hm["ww_agreement_basis"],
                "skeleton_basis": hm["ww_agreement_skeleton_basis"],
                "bothconfident_basis": hm["ww_agreement_bothconfident_basis"],
                "semantic_pass_basis": hm["semantic_pass_basis"],
                "lacuna_counts": hm["lacuna_counts"],
                "base": hand["base_witness_recommended"],
            },
        }
    return {
        "chapters": chapters,
        "honest_divergence_statement": _HONEST_DIVERGENCE_STATEMENT,
    }
