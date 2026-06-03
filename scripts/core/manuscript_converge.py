# scripts/core/manuscript_converge.py
"""Convergence gate over two blind transcription passes (the agent-path's
auto-converge step — P1 of the Sam/Kings cloud plan
``plans/2026-06-02-samkings-cloud-agent-workflow-and-run-plan.md``).

Each pass is a *model_out* dict — the structure a vision sub-agent returns under
``TRANSCRIBE_OUTPUT_SCHEMA``::

    {"verses": [{"v": int, "geez": str, "column": str, "line_start": int,
                 "uncertain": [...]}, ...], "transcription_notes": str}

Two verses **converge** iff their ``geez`` tokenises (via the canonical
:func:`scripts.core.manuscript_records._geez_to_tokens`) to
:func:`scripts.core.manuscript_collation.fold_skeleton`-equal sequences — the
SAME equality the collation engine measures with, so "same reading" means the
same thing end-to-end. Glyph-identical is tracked separately (``identical_pct``)
as the (v)-guard's load-bearing-glyph signal.

Draft-at-scale policy (spec §2 keystone 1): where the two passes agree → a clean
draft; where they diverge → record the locus and flag the chapter ``needs_qa``
for the Track-1 QA wave. The accepted draft uses **pass A** for divergent verses
so the chapter still carries best-effort content (the divergence is flagged, not
silently dropped). Honesty-contract guards travel in the vision prompt, not here:
(q) recite-not-read and (u) verse-ending pluses surface as divergences; (v)
load-bearing glyphs are re-verified even on agreement (``identical_pct`` < 100
on an "agreed" chapter is the signal to look).

Pure: no I/O.
"""

from __future__ import annotations

import re

from scripts.core.manuscript_collation import fold_skeleton
from scripts.core.manuscript_records import ILLEGIBLE, _geez_to_tokens

# Rubric-only marks that are NOT verse text and which ``validate_witness``
# rejects in ``geez`` (the body cross ✣ U+2723 IS kept, per the transcription
# protocol). ❈ U+2748 is the rubric knot / section divider.
_RUBRIC_ONLY = "❈"


def _verse_map(model_out: dict) -> dict[int, dict]:
    """Map verse-number → verse dict for the verses a pass actually read."""
    out: dict[int, dict] = {}
    for mv in model_out.get("verses") or []:
        if isinstance(mv, dict) and mv.get("v") is not None:
            out[mv["v"]] = mv
    return out


def _folded(geez: str) -> list[str]:
    """fold_skeleton of each canonical token — the 'same reading' form."""
    return [fold_skeleton(t) for t in _geez_to_tokens(geez or "")]


def sanitize_model_out(model_out: dict) -> dict:
    """Normalise a raw vision pass to the witness contract (``validate_witness``)
    before converge/assemble. Returns a NEW model_out; input is not mutated.

    Raw vision output drifts from the contract in three ways the 1Ki1 proof
    surfaced:
    - **rubric-only marks in ``geez``** — ❈ (U+2748) is a section divider, not
      verse text; strip it (the body cross ✣ U+2723 stays, per the protocol).
    - **out-of-range ``token_index``** — the model counts words differently from
      ``_geez_to_tokens`` (which strips ✣/separators and splits numerals), so
      its ``uncertain[]`` indices can exceed the token count; clamp into range,
      and drop entries when the verse has no tokens to attach to.
    - **orphan ``illegible`` markers** — the model transcribes a best-guess glyph
      rather than leaving a ⟦illegible⟧ lacuna, so an ``illegible`` marker with
      no matching ⟦illegible⟧ token breaks the honesty bijection; downgrade such
      markers to ``damaged`` (the note is preserved).
    """
    out_verses: list[dict] = []
    for v in model_out.get("verses") or []:
        if not isinstance(v, dict):
            continue
        geez = (v.get("geez") or "").replace(_RUBRIC_ONLY, " ")
        geez = re.sub(r"  +", " ", geez).strip()
        tokens = _geez_to_tokens(geez)
        n = len(tokens)
        unc_out: list[dict] = []
        for u in v.get("uncertain") or []:
            if not isinstance(u, dict):
                continue
            ti = u.get("token_index")
            marker = u.get("marker", "uncertain")
            if marker not in ("uncertain", "damaged", "illegible"):
                marker = "uncertain"
            # 'illegible' only survives if it actually points at a ⟦illegible⟧ token
            if marker == "illegible" and not (isinstance(ti, int) and 0 <= ti < n and tokens[ti] == ILLEGIBLE):
                marker = "damaged"
            if not isinstance(ti, int) or n == 0:
                continue  # no valid token to attach to → drop (keeps the draft valid)
            ti = max(0, min(ti, n - 1))
            unc_out.append({"token_index": ti, "marker": marker, "note": u.get("note", "")})
        nv = dict(v)
        nv["geez"] = geez
        nv["uncertain"] = unc_out
        out_verses.append(nv)
    out = dict(model_out)
    out["verses"] = out_verses
    return out


def renumber_verses(model_out: dict) -> dict:
    """Renumber a pass's verses ``1..N`` by emission (reading) order so the
    witness record satisfies ``validate_witness``'s contiguity rule. Returns a
    NEW model_out; geez/content order is preserved — only the ``v`` index is
    reset. The witness ``v`` is the witness's OWN reading sequence (not a
    canonical number); ``collate_base_structured`` maps to the KJV spine by
    content, so re-indexing is safe and only fixes vision gaps/jumps in the
    model's own numbering."""
    out = dict(model_out)
    out_verses: list[dict] = []
    for idx, v in enumerate(model_out.get("verses") or [], start=1):
        if not isinstance(v, dict):
            continue
        nv = dict(v)
        nv["v"] = idx
        out_verses.append(nv)
    out["verses"] = out_verses
    return out


def converge_passes(pass_a: dict, pass_b: dict) -> dict:
    """Converge two blind transcription passes. Returns a dict::

        {"needs_qa": bool, "convergence_pct": float, "identical_pct": float,
         "divergent_loci": [{"v", "reason", "a"?, "b"?}], "accepted": <pass_a>,
         "verse_count": int}

    ``convergence_pct`` = fold-equal verses / all verses; ``identical_pct`` =
    glyph-identical verses / all verses. ``needs_qa`` is True iff any verse
    diverges (token-level, or present in only one pass).

    Both passes are first run through :func:`sanitize_model_out`, so the
    comparison and the returned ``accepted`` draft conform to the witness
    contract (no rubric-only marks, in-range uncertain indices).
    """
    pass_a = sanitize_model_out(pass_a)
    pass_b = sanitize_model_out(pass_b)
    va, vb = _verse_map(pass_a), _verse_map(pass_b)
    all_v = sorted(set(va) | set(vb))
    divergent: list[dict] = []
    identical = 0
    fold_equal = 0
    for v in all_v:
        a, b = va.get(v), vb.get(v)
        if a is None or b is None:
            divergent.append({"v": v, "reason": "verse present in only one pass"})
            continue
        ag = a.get("geez", "") or ""
        bg = b.get("geez", "") or ""
        if ag == bg:
            identical += 1
            fold_equal += 1
            continue
        if _folded(ag) == _folded(bg):
            fold_equal += 1  # same reading; cosmetic diacritic/order/homograph diff
        else:
            divergent.append({"v": v, "reason": "token divergence", "a": ag, "b": bg})
    n = len(all_v)
    return {
        "needs_qa": bool(divergent),
        "convergence_pct": round(fold_equal / n * 100, 2) if n else 0.0,
        "identical_pct": round(identical / n * 100, 2) if n else 0.0,
        "divergent_loci": divergent,
        "accepted": renumber_verses(pass_a),
        "verse_count": n,
    }
