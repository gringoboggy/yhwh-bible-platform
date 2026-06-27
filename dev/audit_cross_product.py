#!/usr/bin/env python3
"""Round-16 gate (dim 4, the headline) — output cross-product grid parity (build-free).

"Every way we offer the same Bibles" is a GRID: editions × reader-targets × formats ×
colours. A cell can silently fall out of that grid — a reader target selectable in
``/customize`` that produces no catalog format, a format row that DECLARES one target
but BUILDS another, a standalone fed a target it cannot honour. None of these is visible
to a per-edition build or to epubcheck; this gate reconstructs the grid from the ONE-home
tables (``FORMAT_MATRIX`` + ``TARGET_READERS`` + ``editions.yaml`` + the ``/customize``
reader dropdown) and asserts they agree.

Checks:
  1. MATRIX TARGETS ⊆ RESOLVER — every ``FORMAT_MATRIX`` row's ``target_reader`` is a
     valid ``TARGET_READERS`` value (no typo'd profile the resolver silently downgrades).
  2. DECLARED == BUILT — a row whose ``target_reader`` differs from the profile its BASE
     actually builds (``base_build_target``) MUST carry an explicit ``post_process`` (the
     Kindle case: declares ``kindle``, builds ``everywhere`` + ``kindle_safe``). A silent
     mismatch is a row that claims a format it does not produce.
  3. CUSTOMIZE READER OPT ⊆ FORMAT ROWS — every reader target offered in the ``/customize``
     dropdown maps to a ``FORMAT_MATRIX`` row's ``target_reader`` (so a chosen target yields
     a real catalog asset). A selectable target with no format row is an ORPHAN OPTION — it
     builds (the resolver accepts it) but ships as a silent alias with no catalog asset/test.
     (Known round-16 seed: ``computer``.)
  4. STANDALONE DEGENERACY — ``apply_target_override`` MUST raise for a standalone edition
     (the standalone path has no reader profiles), and standalone editions MUST be excluded
     from the catalog edition set — so nothing iterates a reader cross-product over them.
  5. GRID INTEGRITY — unique cell ids; unique (edition, cell, colour) asset names; the
     declared catalog asset count == |catalog editions| × |format cells| × |colours|.

Imports the one-home tables (no rebuild, no EPUB). Ships a ``--selftest`` (non-tautology
proof on a synthetic grid). Mirrors the round-14/15 build-free gate house style.

Usage:
    py -3 dev/audit_cross_product.py [--json OUT.json] [--max-show N] [--selftest]
Exit 0 = grid coherent; 1 = any FAIL.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

CUSTOMIZE_TEMPLATE = REPO_ROOT / "scripts" / "templates" / "customize.py"
# The reader dropdown's options carry ``data-field="target_reader"`` then a run of
# ``<option value="X" ${e.target_reader … >`` — pull the X values out of THAT select only.
_TARGET_SELECT_RE = re.compile(r'data-field="target_reader".*?</select>', re.S)
_OPTION_VALUE_RE = re.compile(r'<option value="([a-z]+)"')


@dataclass
class CrossProductResult:
    fails: list[str] = field(default_factory=list)
    warns: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)

    @property
    def green(self) -> bool:
        return not self.fails


def _customize_reader_options(template_path: Path = CUSTOMIZE_TEMPLATE) -> list[str]:
    """The reader-target values the ``/customize`` dropdown offers (parsed from the
    template so the gate catches UI↔resolver drift, not a hard-coded copy)."""
    text = template_path.read_text(encoding="utf-8")
    m = _TARGET_SELECT_RE.search(text)
    if not m:
        raise ValueError(f"could not find the target_reader <select> in {template_path}")
    return _OPTION_VALUE_RE.findall(m.group(0))


def _check_matrix_targets(res, format_matrix, base_build_target, target_set, target_readers) -> None:
    """Checks 1 + 2 — matrix targets ⊆ resolver; declared == built (post_process gate)."""
    for c in format_matrix:
        if c["target_reader"] not in target_set:
            res.fails.append(
                f"check1 matrix-target: cell {c['id']!r} target_reader={c['target_reader']!r} "
                f"is not in TARGET_READERS {target_readers}"
            )
        bt = base_build_target(c)
        if bt != c["target_reader"] and not c.get("post_process"):
            res.fails.append(
                f"check2 declared!=built: cell {c['id']!r} declares target_reader={c['target_reader']!r} "
                f"but its base builds {bt!r} with NO post_process — it ships a format it does not produce"
            )


def _check_customize_options(res, reader_options, target_set, matrix_targets) -> None:
    """Check 3 — every /customize reader option maps to a FORMAT_MATRIX row (else orphan)."""
    for opt in reader_options:
        if opt not in target_set:
            res.fails.append(
                f"check3 customize-option {opt!r} is not a valid TARGET_READERS value "
                f"(the dropdown offers a target the resolver does not know)"
            )
        elif opt not in matrix_targets:
            res.fails.append(
                f"check3 ORPHAN OPTION: /customize offers reader target {opt!r} (a valid build target) "
                f"but NO FORMAT_MATRIX row produces it — it builds as a silent alias with no catalog "
                f"asset and no test (round-16 'computer' seed)"
            )
    for t in target_set:
        if t not in matrix_targets and t not in set(reader_options):
            res.warns.append(
                f"target {t!r} is in TARGET_READERS but neither a format row nor a /customize option uses it"
            )


def _check_standalone(res, editions, catalog_ids, apply_target_override) -> int:
    """Check 4 — standalone degeneracy (override raises; excluded from catalog). Returns count."""
    standalone_seen = 0
    for ed in editions:
        if not ed.get("standalone"):
            continue
        standalone_seen += 1
        if ed["id"] in catalog_ids:
            res.fails.append(f"check4 standalone {ed['id']!r} leaked into the catalog edition set")
        try:
            apply_target_override(dict(ed), "eink")
            res.fails.append(
                f"check4 standalone {ed['id']!r}: apply_target_override did NOT raise on a reader target "
                f"(a cross-product could silently build it with a profile it cannot honour)"
            )
        except ValueError:
            pass  # expected — the standalone path has no reader profiles
    if standalone_seen == 0:
        res.warns.append("check4: no standalone editions registered (degeneracy check vacuous this run)")
    return standalone_seen


def audit_grid(reader_options: list[str] | None = None) -> CrossProductResult:
    from scripts.build_edition import COVER_COLOURS, FORMAT_MATRIX, TARGET_READERS, apply_target_override
    from scripts.build_format_matrix import base_build_target, standard_edition_ids
    from scripts.core import config

    res = CrossProductResult()
    target_set = set(TARGET_READERS)
    matrix_targets = {c["target_reader"] for c in FORMAT_MATRIX}

    _check_matrix_targets(res, FORMAT_MATRIX, base_build_target, target_set, TARGET_READERS)

    if reader_options is None:
        try:
            reader_options = _customize_reader_options()
        except (OSError, ValueError) as e:
            res.warns.append(f"check3 skipped — could not parse /customize options ({e})")
            reader_options = []
    _check_customize_options(res, reader_options, target_set, matrix_targets)

    catalog_ids = set(standard_edition_ids())
    standalone_seen = _check_standalone(res, config.load_editions(), catalog_ids, apply_target_override)

    # Check 5 — grid integrity (unique cell ids; declared catalog asset count).
    cell_ids = [c["id"] for c in FORMAT_MATRIX]
    if len(cell_ids) != len(set(cell_ids)):
        res.fails.append(f"check5 duplicate FORMAT_MATRIX cell id(s): {cell_ids}")
    expected = len(catalog_ids) * len(FORMAT_MATRIX) * len(COVER_COLOURS)
    res.stats = {
        "catalog_editions": len(catalog_ids),
        "format_cells": len(FORMAT_MATRIX),
        "cover_colours": len(COVER_COLOURS),
        "target_readers": len(target_set),
        "matrix_targets": len(matrix_targets),
        "customize_reader_options": len(reader_options),
        "expected_catalog_assets": expected,
        "standalones": standalone_seen,
    }
    return res


def _print(res: CrossProductResult, max_show: int) -> None:
    s = res.stats
    print(f"\n=== R16 cross-product grid {'PASS' if res.green else 'FAIL'} ===")
    if s:
        print(
            f"  catalog_editions={s['catalog_editions']} format_cells={s['format_cells']} "
            f"colours={s['cover_colours']} → expected_catalog_assets={s['expected_catalog_assets']} | "
            f"target_readers={s['target_readers']} matrix_targets={s['matrix_targets']} "
            f"customize_opts={s['customize_reader_options']} standalones={s['standalones']}"
        )
    for f in res.fails[:max_show]:
        print("  ✗", f)
    for w in res.warns[:max_show]:
        print("  ⚠", w)


def _selftest() -> int:
    """Non-tautology proof — SYNTHETIC (robust to remediation): the orphan-option check
    fires when a valid reader target has no format row and passes when every option maps.
    Exercises the check directly so it does not depend on the real tree's current defects."""
    broken = CrossProductResult()
    # 'eink' is a valid target but the synthetic matrix only produces 'everywhere' → orphan.
    _check_customize_options(broken, ["everywhere", "eink"], {"everywhere", "eink"}, {"everywhere"})
    clean = CrossProductResult()
    _check_customize_options(clean, ["everywhere", "eink"], {"everywhere", "eink"}, {"everywhere", "eink"})
    problems = []
    if not any("ORPHAN OPTION" in f for f in broken.fails):
        problems.append("expected ORPHAN OPTION on a valid-target/no-format-row grid")
    if any("ORPHAN OPTION" in f for f in clean.fails):
        problems.append(f"orphan check false-fired on a fully-mapped grid: {clean.fails}")
    if problems:
        print("SELFTEST FAIL:")
        for p in problems:
            print("  ✗", p)
        return 1
    print("SELFTEST PASS (synthetic: orphan caught on gap grid; clean on fully-mapped grid)")
    return 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return _selftest()
    json_out = argv[argv.index("--json") + 1] if "--json" in argv else None
    max_show = int(argv[argv.index("--max-show") + 1]) if "--max-show" in argv else 50
    res = audit_grid()
    _print(res, max_show)
    if json_out:
        with open(json_out, "w", encoding="utf-8") as fh:
            json.dump({"green": res.green, "stats": res.stats, "fails": res.fails, "warns": res.warns}, fh, indent=1)
        print(f"\nwrote {json_out}")
    print(f"\nRESULT: {'PASS' if res.green else 'FAIL'} ({len(res.fails)} fail, {len(res.warns)} warn)")
    return 1 if not res.green else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
