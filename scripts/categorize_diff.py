#!/usr/bin/env python3
"""categorize_diff.py — the categorize-diff verification technique.

A re-bake of the shared base HTML touches tens of thousands of markers/asides.
Rather than trust the transform, PROVE it. ``categorize`` snapshots the baked
note inventory (counts by kind + an id→kind map for markers and asides);
``prove_marker_rebake`` diffs a before/after pair and confirms the re-bake
changed ONLY the intended regions:

  1. No note added, dropped (the id sets are identical for markers and asides).
  2. No note silently recategorized (every id keeps its kind).
  3. Everything OUTSIDE the intended marker/aside regions — the inline marker
     ``<sup>`` and the aside back-link/note-sym — is byte-identical. The
     intended regions are blanked to a placeholder before the equality check,
     so changing them is allowed but changing anything else is caught.

Used by ``resync_marker_glyphs.py`` to self-verify the Wave-3 re-bake; reusable
for any future surgical base transform.
"""

from __future__ import annotations

import re

_MARKER_RE = re.compile(r'<a class="note-ref note-(?P<kind>[^"]+)" id="ref-(?P<id>[^"]+)"')
_ASIDE_RE = re.compile(r'<aside class="note note-(?P<kind>[^"]+)" id="note-(?P<id>[^"]+)"')

# The intended-change regions, blanked to a constant before the byte-equality
# check so the transform is free to rewrite them but nothing else.
_NORM_SUP = re.compile(r'<sup class="marker-[^"]*">[^<]*</sup>')
_NORM_BACK = re.compile(r'(class="note-back" title="Back">)[^<]*</a>( <a class="note-sym"[^>]*>[^<]*</a>)?')


def categorize(html: str) -> dict:
    """Snapshot the baked note inventory: per-kind marker/aside counts, the id
    sets, and id→kind maps (the maps catch a silent recategorization)."""
    markers: dict[str, int] = {}
    marker_kind_by_id: dict[str, str] = {}
    for m in _MARKER_RE.finditer(html):
        kind, rid = m.group("kind"), m.group("id")
        markers[kind] = markers.get(kind, 0) + 1
        marker_kind_by_id[rid] = kind
    asides: dict[str, int] = {}
    aside_kind_by_id: dict[str, str] = {}
    for m in _ASIDE_RE.finditer(html):
        kind, nid = m.group("kind"), m.group("id")
        asides[kind] = asides.get(kind, 0) + 1
        aside_kind_by_id[nid] = kind
    return {
        "markers": markers,
        "asides": asides,
        "marker_ids": set(marker_kind_by_id),
        "aside_ids": set(aside_kind_by_id),
        "marker_kind_by_id": marker_kind_by_id,
        "aside_kind_by_id": aside_kind_by_id,
    }


def _normalize(html: str) -> str:
    html = _NORM_SUP.sub('<sup class="marker-X">X</sup>', html)
    html = _NORM_BACK.sub(r"\1X</a>", html)
    return html


def _first_divergence(a: str, b: str) -> int:
    for i in range(min(len(a), len(b))):
        if a[i] != b[i]:
            return i
    return min(len(a), len(b))


def prove_marker_rebake(before: str, after: str) -> dict:
    """Prove ``after`` differs from ``before`` ONLY in the intended marker/aside
    regions. Returns ``{"ok": bool, "reason": str|None, ...}``."""
    cb, ca = categorize(before), categorize(after)

    if cb["marker_ids"] != ca["marker_ids"]:
        added = sorted(ca["marker_ids"] - cb["marker_ids"])[:5]
        dropped = sorted(cb["marker_ids"] - ca["marker_ids"])[:5]
        return {"ok": False, "reason": f"marker id set changed (added={added}, dropped={dropped})"}
    if cb["aside_ids"] != ca["aside_ids"]:
        added = sorted(ca["aside_ids"] - cb["aside_ids"])[:5]
        dropped = sorted(cb["aside_ids"] - ca["aside_ids"])[:5]
        return {"ok": False, "reason": f"aside id set changed (added={added}, dropped={dropped})"}
    if cb["marker_kind_by_id"] != ca["marker_kind_by_id"]:
        return {"ok": False, "reason": "a marker kept its id but changed kind (recategorization)"}
    if cb["aside_kind_by_id"] != ca["aside_kind_by_id"]:
        return {"ok": False, "reason": "an aside kept its id but changed kind (recategorization)"}

    nb, na = _normalize(before), _normalize(after)
    if nb != na:
        i = _first_divergence(nb, na)
        return {
            "ok": False,
            "reason": (
                f"bytes diverge outside marker/aside regions at offset {i}: "
                f"{nb[max(0, i - 40) : i + 40]!r} vs {na[max(0, i - 40) : i + 40]!r}"
            ),
        }
    return {
        "ok": True,
        "reason": None,
        "markers": sum(ca["markers"].values()),
        "asides": sum(ca["asides"].values()),
    }
