#!/usr/bin/env python3
"""Gate G4 — badge-conservation / orphan-marker integrity of a built EPUB (no rebuild).

A study/badge edition (``marker_style=badge``, the §4.1 default) collapses every
verse's per-note inline markers — the raw ``<a class="note-ref note-{kind}"
id="ref-…">`` anchors — into ONE ``verse-notes-badge`` (popup layout) or one
``study-glossary-jump`` per category (eink backmatter layout), merging the
matching ``<aside class="note">`` bodies into one ``verse-notes`` aside. When a
verse carries a marker whose aside is MISSING, ``apply_badge_markers`` bails on
that verse: it bumps ``stats["badges_skipped"]`` and **leaves the raw markers in
place** — a silently degraded EPUB that is structurally valid yet ships an
un-collapsed leaf marker with no popup, no gate firing (program dim P2 /
propagation row 2). ``build_one`` surfaces the counter as
``stats["badge_verses_skipped"]`` and ``_write_stats_sidecar`` records it in the
sibling ``<epub>.stats.json``.

This gate closes that gap two ways — the build's own counter AND a post-hoc scan
of the product:
  1. SIDECAR — resolve the built epub's sibling ``<epub>.stats.json`` and assert
     ``badge_verses_skipped == 0`` (the build saw no orphan-marker bail). Absent
     sidecar → ``--require-sidecar`` makes it FAIL, else WARN + skip this check.
  2. ORPHAN MARKERS — scan the built epub: a badge edition (≥1 ``verse-notes-
     badge`` / ``study-glossary-jump`` anchor present) must hold **0** raw
     ``<a class="note-ref …">`` inline markers — every one is collapsed into a
     badge. A surviving leaf marker is the orphan symptom. Verified against the
     round-14 catholic-study builds: a clean eink build has 0 note-ref +
     10,695 study-glossary-jump; a clean everywhere build has 0 note-ref +
     9,023 verse-notes-badge. A ``numbers`` edition (no badges present) keeps
     its inline markers by design → the orphan check is skipped (WARN-noted), so
     the gate never false-FAILs a non-badge edition.

Standalone stdlib only (mirrors ``audit_idmap_frags.py`` / ``audit_glossary_
contract.py``) → light + OOM-safe; the scan reads each (x)html member once.

Usage:
    py -3 dev/audit_badge_conservation.py <epub> [<epub> ...]
        [--json OUT.json] [--max-show N] [--require-sidecar]
Exit 0 = badge_verses_skipped == 0 (or sidecar-absent WARN) AND no orphan
markers; 1 = any FAIL.
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

# The raw per-note inline marker the badge pass collapses: ``<a class="note-ref
# note-{kind}" id="ref-{full_id}" …>…</a>`` (scripts/inject.py:make_marker /
# build_edition._BADGE_MARKER_RE). Group 1 = the ref-id, for reporting. Mirrors
# build_edition._ORPHAN_INLINE_MARKER_RE exactly so a surviving leaf is named
# the same way the build names it.
_ORPHAN_MARKER_RE = re.compile(r'<a class="note-ref [^"]*" id="(ref-[^"]+)"')
# A collapsed badge anchor — either layout. Their presence ⇒ this edition built
# in badge mode, so every note-ref marker MUST have been collapsed.
_BADGE_ANCHOR_RE = re.compile(r'<a class="(?:verse-notes-badge|study-glossary-jump)\b')

SIDECAR_KEY = "badge_verses_skipped"


@dataclass
class BadgeConservationResult:
    path: str
    fails: list[str] = field(default_factory=list)
    warns: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)

    @property
    def green(self) -> bool:
        return not self.fails


def _base(name: str) -> str:
    return name.replace("\\", "/").rsplit("/", 1)[-1]


def _sidecar_path(epub_path: str) -> Path:
    """The build writes ``<epub>.stats.json`` (suffix appended, not replaced)."""
    p = Path(epub_path)
    return p.with_suffix(p.suffix + ".stats.json")


def _check_sidecar(epub_path: str, *, require_sidecar: bool) -> tuple[list[str], list[str], dict[str, int]]:
    """Check 1 — the build's ``badge_verses_skipped`` counter == 0. Returns
    (fails, warns, stat-deltas)."""
    fails: list[str] = []
    warns: list[str] = []
    stats: dict[str, int] = {"sidecar_present": 0, "badge_verses_skipped": 0}
    side = _sidecar_path(epub_path)
    if not side.is_file():
        msg = f"sidecar {side.name} not found beside the epub (cannot read {SIDECAR_KEY})"
        (fails if require_sidecar else warns).append(msg)
        return fails, warns, stats
    stats["sidecar_present"] = 1
    try:
        data = json.loads(side.read_text(encoding="utf-8"))
    except Exception as exc:  # malformed/locked sidecar → can't verify the counter
        (fails if require_sidecar else warns).append(f"sidecar {side.name} unreadable ({exc})")
        return fails, warns, stats
    if SIDECAR_KEY not in data:
        warns.append(
            f"sidecar {side.name} predates the G4 instrument (no {SIDECAR_KEY} key) — treating as 0; "
            f"rebuild to record the counter"
        )
        return fails, warns, stats
    skipped = int(data.get(SIDECAR_KEY, 0) or 0)
    stats["badge_verses_skipped"] = skipped
    if skipped > 0:
        fails.append(
            f"sidecar {SIDECAR_KEY}={skipped} (the build bailed on {skipped} verse(s) whose aside was "
            f"missing → raw markers left, badge dropped)"
        )
    return fails, warns, stats


def _scan_markers(path: str) -> tuple[int, list[tuple[str, str]]]:
    """Read every (x)html member once. Returns (badge_anchor_count, orphan list of
    (member, ref_id)). A kepub's koboSpan wrapping never touches the ``<a …>``
    opening tag, so both regexes match the source .epub and the .kepub.epub."""
    badges = 0
    orphans: list[tuple[str, str]] = []
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if not name.endswith((".html", ".xhtml")):
                continue
            text = zf.read(name).decode("utf-8", "replace")
            badges += len(_BADGE_ANCHOR_RE.findall(text))
            for m in _ORPHAN_MARKER_RE.finditer(text):
                orphans.append((name, m.group(1)))
    return badges, orphans


def _check_orphans(path: str) -> tuple[list[str], list[str], dict[str, int]]:
    """Check 2 — no orphan inline marker survives in a badge edition. Returns
    (fails, warns, stat-deltas)."""
    fails: list[str] = []
    warns: list[str] = []
    badges, orphans = _scan_markers(path)
    stats = {
        "badge_anchors": badges,
        "orphan_markers": len(orphans),
        "is_badge_edition": int(badges > 0),
    }
    if badges == 0:
        # No badges ⇒ marker_style=numbers (or a notes-free edition). Inline
        # markers are legitimate there, so the orphan invariant does not apply.
        if orphans:
            warns.append(
                f"no badge anchors present — inferred non-badge (numbers) edition; "
                f"its {len(orphans)} inline marker(s) are by-design, orphan check skipped"
            )
        return fails, warns, stats
    for member, ref_id in orphans:
        fails.append(
            f"orphan inline marker {ref_id} in {_base(member)} — a badge edition collapses every "
            f"note-ref marker; this leaf was left un-collapsed (badge/aside desync)"
        )
    return fails, warns, stats


def audit_epub(path: str, *, require_sidecar: bool = False) -> BadgeConservationResult:
    res = BadgeConservationResult(path=path)
    s_fails, s_warns, s_stats = _check_sidecar(path, require_sidecar=require_sidecar)
    o_fails, o_warns, o_stats = _check_orphans(path)
    res.fails.extend(s_fails)
    res.fails.extend(o_fails)
    res.warns.extend(s_warns)
    res.warns.extend(o_warns)
    res.stats = {**s_stats, **o_stats}
    return res


def _print(res: BadgeConservationResult, max_show: int) -> None:
    name = _base(res.path)
    s = res.stats
    status = "PASS" if res.green else "FAIL"
    print(f"\n=== {name} — G4 badge-conservation {status} ===")
    if s:
        print(
            f"  sidecar_present={s.get('sidecar_present', 0)} "
            f"badge_verses_skipped={s.get('badge_verses_skipped', 0)} "
            f"badge_anchors={s.get('badge_anchors', 0)} "
            f"orphan_markers={s.get('orphan_markers', 0)} "
            f"is_badge_edition={s.get('is_badge_edition', 0)}"
        )
    for f in res.fails[:max_show]:
        print("  ✗", f)
    if len(res.fails) > max_show:
        print(f"  ✗ … +{len(res.fails) - max_show} more FAIL(s)")
    for w in res.warns[:max_show]:
        print("  ⚠", w)


def _arg(argv: list[str], flag: str, default: str | None = None) -> str | None:
    return argv[argv.index(flag) + 1] if flag in argv else default


def main(argv: list[str]) -> int:
    paths = [a for a in argv if not a.startswith("--")]
    # drop the value tokens that follow valued flags so they are not read as epub paths
    for flag in ("--json", "--max-show"):
        if flag in argv:
            val = argv[argv.index(flag) + 1]
            if val in paths:
                paths.remove(val)
    json_out = _arg(argv, "--json")
    max_show = int(_arg(argv, "--max-show", "50"))
    require_sidecar = "--require-sidecar" in argv
    if not paths:
        print(__doc__)
        return 2
    results = [audit_epub(p, require_sidecar=require_sidecar) for p in paths]
    for r in results:
        _print(r, max_show)
    if json_out:
        with open(json_out, "w", encoding="utf-8") as fh:
            json.dump(
                [
                    {"path": r.path, "green": r.green, "stats": r.stats, "fails": r.fails, "warns": r.warns}
                    for r in results
                ],
                fh,
                indent=1,
            )
        print(f"\nwrote {json_out}")
    any_fail = any(not r.green for r in results)
    print(f"\nTOTAL: {sum(r.green for r in results)}/{len(results)} artifact(s) badge-conservation-clean")
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
