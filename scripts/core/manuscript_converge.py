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

from scripts.core.manuscript_collation import fold_skeleton
from scripts.core.manuscript_records import _geez_to_tokens


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


def converge_passes(pass_a: dict, pass_b: dict) -> dict:
    """Converge two blind transcription passes. Returns a dict::

        {"needs_qa": bool, "convergence_pct": float, "identical_pct": float,
         "divergent_loci": [{"v", "reason", "a"?, "b"?}], "accepted": <pass_a>,
         "verse_count": int}

    ``convergence_pct`` = fold-equal verses / all verses; ``identical_pct`` =
    glyph-identical verses / all verses. ``needs_qa`` is True iff any verse
    diverges (token-level, or present in only one pass).
    """
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
        "accepted": pass_a,
        "verse_count": n,
    }
