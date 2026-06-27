#!/usr/bin/env python3
"""Round-15 gate D3 — versification source-coverage validator (build-free, no rebuild).

The Douay-Rheims (English) and Clementine-Vulgate (Latin) parallel-popup stores are
produced by remapping each SOURCE verse through ``vulgate_to_kjv`` and CONCATENATING
same-target collisions (``scripts/extract_translation.apply_remap``). The remap returns
``None`` to OMIT a verse, and ``apply_remap`` then **silently drops it**
(``extract_translation.py:521`` ``if mapped is None: continue``). So a *missing* fold-table
entry — not an error — makes real source scripture vanish from the popup. That is exactly
the round-15 D3 live defect: Douay/Vulgate **Ps 2:13** and **Ps 4:10** had no map key
(``_LXX_PSALM_COUNTS[2]=12`` / ``[4]=9`` and they were absent from ``_VULGATE_PSALM_FIXES``),
so ``vulgate_to_kjv`` returned ``None`` and the closing clause of KJV Ps 2:12 / 4:8 shipped
missing.

The existing tests are OUTPUT-driven (they read the produced ``.py`` stores) and hand-
enumerated, so they cannot see a verse that was dropped on the *input* side. This gate
closes that hole: it walks every SOURCE verse-per-line coordinate (exactly as the extractor
does — eBible code -> project code via ``EBIBLE_VPL_TO_PROJECT`` + the BAR/LJE split) and
asserts each one maps to a non-None, in-canonical-extent KJV coordinate UNLESS it is on the
documented-omit allowlist. Latin and English have different verse counts, so each source is
run independently through the same ``vulgate_to_kjv``.

A tiling-only check would MISS the Ps 2/4 class (they route through ``_VULGATE_PSALM_FIXES``,
not ``_VULGATE_SEGMENTS``); driving every real source coordinate through the actual remap is
what catches them.

Checks:
  1. COVERAGE — every source ``(proj_code, ch, vs)`` maps non-None, OR the book is on the
     book allowlist (``_VULGATE_OMIT`` = tob/jdt/sir, divergent recension), OR the exact
     coord is on the per-coord allowlist (with a documented reason). A non-allowlisted
     ``None`` is a FAIL (a dropped/under-mapped source verse).
  2. IN-EXTENT — every mapped target ``(code, ch, vs)`` is inside the canonical extent
     (``coord_in_canonical_extent``). A map to an impossible coordinate is a FAIL.

Standalone-importable (no rebuild); imports the real extractor + versification so it can
never drift from the shipping remap. ``--selftest`` proves the detector is not tautological
(it flags a synthetic drop and passes full coverage).

Usage:
    py -3 dev/audit_versification_coverage.py [--json OUT.json] [--max-show N]
    py -3 dev/audit_versification_coverage.py --selftest
Exit 0 = every source verse covered (or allowlisted) + in-extent; 1 = any FAIL; 2 = usage.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.core.canonical_verse_counts import coord_in_canonical_extent  # noqa: E402
from scripts.core.versification import _VULGATE_OMIT, vulgate_to_kjv  # noqa: E402
from scripts.extract_translation import (  # noqa: E402
    EBIBLE_VPL_TO_PROJECT,
    TRANSLATIONS_DIR,
    parse_vpl,
    split_baruch_letter_of_jeremiah,
)

# Translations whose source numbering != KJV and that route through ``vulgate_to_kjv``.
_REMAP_TRANSLATIONS = ("douay-rheims", "vulgate-clementine")

# DOCUMENTED-OMIT ALLOWLIST — source coords that map to None BY DESIGN (not a drop bug).
# Whole books with no canonical home in this scheme (divergent recension, text supplied
# by a different store) are allowlisted via _VULGATE_OMIT (tob/jdt/sir).
_ALLOWLIST_BOOKS: frozenset[str] = frozenset(_VULGATE_OMIT)

# Per-coordinate intentional omits — add ONLY with a one-line reason after verifying the
# source verse genuinely has no canonical KJV slot.
_ALLOWLIST_COORDS: dict[tuple[str, int, int], str] = {
    # (proj_code, ch, vs): "reason"
}

# Psalm superscriptions the KJV leaves UNNUMBERED. The Clementine-Vulgate / Douay number
# the title as verse 1 (and, for the four psalms with a two-line historical superscription
# — Ps 50/51/53/59 = KJV 51/52/54/60 — as verses 1 AND 2); the shared ``_psalm_map`` keeps
# the title as its own dropped verse and runs the body 1:1 (versification.py ~L781). The
# psalm BODY maps in full (incl. the trailing folds 2:13/4:10 once the fix lands); ONLY the
# superscription verse drops — verified: psa 50:3 ("Miserere mei, Deus") -> KJV 51:1, so
# 50:1+50:2 are both title. Enumerated (not a clean numeric rule: 62 single + 4 two-line).
_PSALM_TITLE_DROPS: frozenset[tuple[int, int]] = frozenset(
    {
        (3, 1),
        (4, 1),
        (5, 1),
        (6, 1),
        (7, 1),
        (8, 1),
        (9, 1),
        (11, 1),
        (17, 1),
        (18, 1),
        (19, 1),
        (20, 1),
        (21, 1),
        (29, 1),
        (30, 1),
        (33, 1),
        (35, 1),
        (37, 1),
        (38, 1),
        (39, 1),
        (40, 1),
        (41, 1),
        (43, 1),
        (44, 1),
        (45, 1),
        (46, 1),
        (47, 1),
        (48, 1),
        (50, 1),
        (50, 2),
        (51, 1),
        (51, 2),
        (52, 1),
        (53, 1),
        (53, 2),
        (54, 1),
        (55, 1),
        (56, 1),
        (57, 1),
        (58, 1),
        (59, 1),
        (59, 2),
        (60, 1),
        (61, 1),
        (62, 1),
        (63, 1),
        (64, 1),
        (66, 1),
        (67, 1),
        (68, 1),
        (69, 1),
        (74, 1),
        (75, 1),
        (76, 1),
        (79, 1),
        (80, 1),
        (82, 1),
        (83, 1),
        (84, 1),
        (87, 1),
        (88, 1),
        (91, 1),
        (101, 1),
        (107, 1),
        (139, 1),
        (141, 1),
    }
)


def _is_documented_omit(code: str, ch: int, vs: int) -> bool:
    """Structural intentional omits — source verses with no KJV-canonical home (verified)."""
    # Greek Additions to Esther (Douay/Vulgate est 10:4-16:24): KJV Esther ends at 10:3;
    # there is no `aes` parallel-popup store, matching the LXX ``_EST_OMIT`` design — the
    # additions are not carried in the Douay/Vulgate parallels (a scope boundary, not a drop).
    if code == "est" and (ch > 10 or (ch == 10 and vs >= 4)):
        return True
    # Bel & the Dragon: the Vulgate-only closing decree (Douay dan 14:42 "Then the king
    # said: Let all the inhabitants...") has NO KJV bel counterpart — bel 1:1..42 are filled
    # by dan 13:65 + dan 14:1..41 (versification.py ``_vulgate_cross`` ~L1445, documented drop).
    if code == "dan" and ch == 14 and vs == 42:
        return True
    # Psalm superscriptions the KJV leaves unnumbered (see _PSALM_TITLE_DROPS).
    return code == "psa" and (ch, vs) in _PSALM_TITLE_DROPS


def _default_allow(code: str, ch: int, vs: int) -> bool:
    return code in _ALLOWLIST_BOOKS or (code, ch, vs) in _ALLOWLIST_COORDS or _is_documented_omit(code, ch, vs)


@dataclass
class CoverageResult:
    translation: str
    fails: list[str] = field(default_factory=list)
    warns: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)

    @property
    def green(self) -> bool:
        return not self.fails


def _by_project_book(vpl_path: Path) -> dict[str, list[tuple[int, int, str]]]:
    """Replicate ``extract_translation.extract``'s source->project mapping (BAR/LJE split +
    ``EBIBLE_VPL_TO_PROJECT``) so the gate sees exactly the coords the extractor remaps."""
    by_ebible = parse_vpl(vpl_path)
    out: dict[str, list[tuple[int, int, str]]] = {}
    for ebook, verses in by_ebible.items():
        if ebook == "BAR":
            bar_keep, lje_part = split_baruch_letter_of_jeremiah(verses)
            out["bar"] = bar_keep
            if lje_part:
                out["lje"] = lje_part
            continue
        proj = EBIBLE_VPL_TO_PROJECT.get(ebook)
        if proj is None:
            continue  # unmapped source book — never ingested (mirrors the extractor)
        out[proj] = verses
    return out


def coverage_check(
    by_project_book: dict[str, list[tuple[int, int, str]]],
    remap,
    *,
    allow=None,
) -> tuple[list[str], list[str], dict[str, int]]:
    """Pure detector (selftested). Returns (fails, warns, stats).

    For every source coordinate, call ``remap`` and FAIL on a non-allowlisted None or a
    mapped-out-of-extent target. ``allow(code, ch, vs) -> bool`` marks a None as an
    intentional/documented omit; defaults to ``_default_allow``."""
    allow = allow or _default_allow
    fails: list[str] = []
    warns: list[str] = []
    total = dropped_allow = dropped_fail = oob = mapped_ok = 0
    for code in sorted(by_project_book):
        for ch, vs, _text in sorted(by_project_book[code]):
            total += 1
            mapped = remap(code, ch, vs)
            if mapped is None:
                if allow(code, ch, vs):
                    dropped_allow += 1
                else:
                    dropped_fail += 1
                    fails.append(
                        f"{code} {ch}:{vs} -> None (DROPPED): source verse has no KJV target "
                        f"(missing fold-table entry; would vanish from the parallel popup)"
                    )
                continue
            ncode, nch, nvs = mapped
            if not coord_in_canonical_extent(ncode, nch, nvs):
                oob += 1
                fails.append(
                    f"{code} {ch}:{vs} -> {ncode} {nch}:{nvs} OUT-OF-EXTENT (mapped past the canonical verse count)"
                )
            else:
                mapped_ok += 1
    stats = {
        "source_verses": total,
        "mapped_ok": mapped_ok,
        "dropped_fail": dropped_fail,
        "dropped_allowlisted": dropped_allow,
        "out_of_extent": oob,
        "books": len(by_project_book),
    }
    return fails, warns, stats


def audit_translation(translation_id: str) -> CoverageResult:
    res = CoverageResult(translation=translation_id)
    src_dir = TRANSLATIONS_DIR / "sources" / translation_id
    vpls = sorted(src_dir.glob("*_vpl.txt")) if src_dir.is_dir() else []
    if not vpls:
        res.fails.append(f"no *_vpl.txt source found in {src_dir} (cannot verify coverage)")
        return res
    by_book = _by_project_book(vpls[0])
    fails, warns, stats = coverage_check(by_book, vulgate_to_kjv)
    res.fails.extend(fails)
    res.warns.extend(warns)
    res.stats = {"source_file": vpls[0].name, **stats}  # type: ignore[dict-item]
    return res


def _selftest() -> int:
    """Prove the detector catches a drop + an out-of-extent map and passes clean coverage."""
    # All four fixture coords are genuinely IN canonical extent (gen 1:1-2, psa 1:1-2)
    # so the "good" identity remap must produce zero fails.
    books = {"gen": [(1, 1, "a"), (1, 2, "b")], "psa": [(1, 1, "x"), (1, 2, "y")]}

    def good(code, ch, vs):  # full coverage, in extent
        return (code, ch, vs)

    def drops_one(code, ch, vs):  # the Ps 2:13 drop class
        if (code, ch, vs) == ("gen", 1, 2):
            return None
        return (code, ch, vs)

    def oob(code, ch, vs):  # maps gen 1:2 past extent
        if (code, ch, vs) == ("gen", 1, 2):
            return ("gen", 999, 999)
        return (code, ch, vs)

    f_good, _, s_good = coverage_check(books, good)
    f_drop, _, _ = coverage_check(books, drops_one)
    f_allow, _, _ = coverage_check(books, drops_one, allow=lambda c, ch, vs: (c, ch, vs) == ("gen", 1, 2))
    f_oob, _, _ = coverage_check(books, oob)
    ok = True
    if f_good:
        print("  ✗ selftest: full-coverage remap produced FAILs:", f_good)
        ok = False
    if s_good["source_verses"] != 4 or s_good["mapped_ok"] != 4:
        print("  ✗ selftest: stats wrong for full coverage:", s_good)
        ok = False
    if not any("DROPPED" in m for m in f_drop):
        print("  ✗ selftest: a dropped verse was NOT flagged (tautological gate!)")
        ok = False
    if f_allow:
        print("  ✗ selftest: an allowlisted drop should NOT fail:", f_allow)
        ok = False
    if not any("OUT-OF-EXTENT" in m for m in f_oob):
        print("  ✗ selftest: an out-of-extent map was NOT flagged")
        ok = False
    print("  ✓ D3 coverage-gate selftest passed" if ok else "  selftest FAILED")
    return 0 if ok else 1


def _print(res: CoverageResult, max_show: int) -> None:
    s = res.stats
    status = "PASS" if res.green else "FAIL"
    print(f"\n=== {res.translation} — D3 versification coverage {status} ===")
    if s:
        print(
            f"  src={s.get('source_file', '?')} verses={s.get('source_verses', 0)} "
            f"mapped_ok={s.get('mapped_ok', 0)} dropped_fail={s.get('dropped_fail', 0)} "
            f"dropped_allowlisted={s.get('dropped_allowlisted', 0)} "
            f"out_of_extent={s.get('out_of_extent', 0)} books={s.get('books', 0)}"
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
    if "--selftest" in argv:
        return _selftest()
    json_out = _arg(argv, "--json")
    max_show = int(_arg(argv, "--max-show", "50"))
    results = [audit_translation(t) for t in _REMAP_TRANSLATIONS]
    for r in results:
        _print(r, max_show)
    if json_out:
        with open(json_out, "w", encoding="utf-8") as fh:
            json.dump(
                [
                    {
                        "translation": r.translation,
                        "green": r.green,
                        "stats": r.stats,
                        "fails": r.fails,
                        "warns": r.warns,
                    }
                    for r in results
                ],
                fh,
                indent=1,
            )
        print(f"\nwrote {json_out}")
    any_fail = any(not r.green for r in results)
    print(f"\nTOTAL: {sum(r.green for r in results)}/{len(results)} translation(s) versification-coverage-clean")
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
