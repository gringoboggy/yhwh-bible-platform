#!/usr/bin/env python3
"""Round-16 gate (dim 9) — /customize options completeness + wiring (build-free).

The §7 "Add a new edition feature" contract says every customization field travels a
five-point path: schema → loader (``api_customize_data``) → validator
(``api_save_edition_meta`` EDITABLE_* allow-lists) → UI control → BUILD READ. A field
can fall off the END of that path — validated + savable + echoed back to the UI, yet
NOTHING in the build consumes it, so the control silently does nothing. epubcheck and a
per-edition build never notice (the field just has no effect). This gate reconstructs
the path from the one-home tables and flags the breaks.

Checks:
  1. UI ⊆ VALIDATOR — every reader-facing ``data-field`` in the /customize template is
     an editable field the validator accepts (EDITABLE_TEXT_FIELDS ∪ EDITABLE_BOOL_FIELDS
     ∪ the per-field validators). A UI control the save path rejects is un-savable.
  2. VALIDATOR → BUILD READ — every validated field is READ somewhere on the build path
     (``build_edition.py`` / ``matter_pages.py`` / ``scripts/core/*.py``). A validated
     field with no build consumer AND not on the documented metadata/deferred allow-list
     is an ORPHAN OPTION (a control that does nothing). (Round-16 seed: ``verse_marker_glyph``.)
  3. NO DEAD ALLOW-LIST — every name on the metadata/deferred allow-list is still a real
     validated field (so the allow-list can't silently mask a newly-broken field).

Imports the validator allow-lists + reads the build-path sources as text (no rebuild, no
EPUB). Ships ``--selftest`` (non-tautology: asserts the known orphan is caught + a wired
field is not). Mirrors the round-14/15 build-free gate house style.

Usage:
    py -3 dev/audit_customize_completeness.py [--json OUT.json] [--max-show N] [--selftest]
Exit 0 = every UI field validated + every validated field build-read (or allow-listed); 1 = any FAIL.
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
_DATA_FIELD_RE = re.compile(r'data-field="([a-z_]+)"')

# Build-path source files a field must be READ in to count as wired (the consumer set —
# the loader/validator/API echo do NOT count; they are upstream of "does it affect output").
# The cover IS shipped product, so generate_edition_covers.py is a legitimate consumer
# (e.g. cover_main_title / display_name set the cover headings — round-16 false-positive fix).
BUILD_CONSUMER_GLOBS = [
    "scripts/build_edition.py",
    "scripts/matter_pages.py",
    "scripts/generate_edition_covers.py",
]
BUILD_CONSUMER_DIRS = ["scripts/core"]

# Fields that are LEGITIMATELY not read on the build path (read by the cover API / front-
# matter / pure metadata), with the reason — so the gate never false-flags them. Audited
# 2026-06-27 (round-16): each verified to have a non-build consumer or to be pure metadata.
METADATA_ONLY = {
    "short_title": "UI display fallback only (safe-title)",
    "target_audience": "editorial metadata, no build effect",
    "notes": "editorial metadata, no build effect",
    "dedication": "optional front-matter page rendered via matter_pages (kept if read there)",
    "display_name": "cover subtitle / Your-Edition page — composed via the /api/covers path, not the EPUB build",
}
# Fields stored + validated but whose build wiring is DEFERRED by decision (not orphans).
DEFERRED = {
    "enabled_reading_plans": "schema-only flag; ToC build integration deferred to ψ.19.1 (web_editions.py)",
}
# data-field names that belong to the category/kind sub-editors, not the edition record.
NON_EDITION_FIELDS = {"symbol", "label"}


@dataclass
class CompletenessResult:
    fails: list[str] = field(default_factory=list)
    warns: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)

    @property
    def green(self) -> bool:
        return not self.fails


def _ui_fields() -> list[str]:
    text = CUSTOMIZE_TEMPLATE.read_text(encoding="utf-8")
    seen: list[str] = []
    for f in _DATA_FIELD_RE.findall(text):
        if f not in seen and f not in NON_EDITION_FIELDS:
            seen.append(f)
    return seen


def _build_consumer_text() -> str:
    parts: list[str] = []
    for rel in BUILD_CONSUMER_GLOBS:
        p = REPO_ROOT / rel
        if p.is_file():
            parts.append(p.read_text(encoding="utf-8", errors="replace"))
    for d in BUILD_CONSUMER_DIRS:
        for p in (REPO_ROOT / d).glob("*.py"):
            parts.append(p.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def _is_build_read(field_name: str, src: str) -> bool:
    """A field counts as build-read if it appears as a dict-key / attribute access in the
    build-path source (``"field"`` / ``'field'`` / ``.get("field"``)."""
    return (f'"{field_name}"' in src) or (f"'{field_name}'" in src)


def audit_completeness() -> CompletenessResult:
    from scripts.api.editions import EDITABLE_BOOL_FIELDS, EDITABLE_TEXT_FIELDS

    res = CompletenessResult()
    ui = _ui_fields()
    validated = set(EDITABLE_TEXT_FIELDS) | set(EDITABLE_BOOL_FIELDS)
    # Fields validated by a dedicated per-field validator (not in the flat allow-lists)
    # — list/state fields. They ARE accepted; treat as validated for check 1.
    state_validated = {
        "popup_translation",
        "popup_languages_capped",
        "popup_languages_default",
        "popup_languages_per_book",
        "traditions_default",
        "traditions_per_book",
        "enabled_reading_plans",
        "max_popup_languages",
    }
    accepted = validated | state_validated
    src = _build_consumer_text()

    # Check 1 — every UI field is savable (validator-accepted).
    for f in ui:
        if f not in accepted:
            res.fails.append(
                f"check1 UI field {f!r} has a /customize control but is NOT in the validator "
                f"allow-lists (EDITABLE_TEXT/BOOL_FIELDS) — its value cannot be saved"
            )

    # Check 2 — every validated field is read on the build path (else orphan option).
    allow = set(METADATA_ONLY) | set(DEFERRED)
    for f in sorted(accepted):
        if f in allow:
            continue
        if not _is_build_read(f, src):
            res.fails.append(
                f"check2 ORPHAN OPTION: validated field {f!r} is accepted + saved + echoed to the UI "
                f"but is READ nowhere on the build path (build_edition/matter_pages/core) — the control "
                f"does nothing (round-16 'verse_marker_glyph' seed)"
            )

    # Check 3 — no dead allow-list entry (the allow-list can't mask a broken field).
    for f in sorted(allow):
        if f not in accepted:
            res.warns.append(f"check3 allow-list entry {f!r} is no longer a validated field — stale allow-list")

    res.stats = {
        "ui_fields": len(ui),
        "validated_fields": len(accepted),
        "metadata_only_allow": len(METADATA_ONLY),
        "deferred_allow": len(DEFERRED),
        "orphan_options": sum(1 for x in res.fails if "ORPHAN OPTION" in x),
        "unsavable_ui": sum(1 for x in res.fails if "cannot be saved" in x),
    }
    return res


def _print(res: CompletenessResult, max_show: int) -> None:
    s = res.stats
    print(f"\n=== R16 customize-completeness {'PASS' if res.green else 'FAIL'} ===")
    if s:
        print(
            f"  ui_fields={s['ui_fields']} validated={s['validated_fields']} "
            f"orphan_options={s['orphan_options']} unsavable_ui={s['unsavable_ui']} "
            f"(allow: metadata={s['metadata_only_allow']} deferred={s['deferred_allow']})"
        )
    for f in res.fails[:max_show]:
        print("  ✗", f)
    for w in res.warns[:max_show]:
        print("  ⚠", w)


def _selftest() -> int:
    """Non-tautology proof — SYNTHETIC (robust to remediation): the build-read detector
    distinguishes a field that IS read on the build path from one that is not. Exercises
    the core predicate directly so it does not depend on the real tree's current orphan."""
    src = 'theme = edition.get("theme")\nif edition["marker_style"] == "badge": ...'
    problems = []
    if not _is_build_read("theme", src):
        problems.append("expected a '.get(\"theme\")' read to be detected")
    if not _is_build_read("marker_style", src):
        problems.append('expected a subscript ["marker_style"] read to be detected')
    if _is_build_read("verse_marker_glyph", src):
        problems.append("a field absent from the source was falsely detected as read")
    if problems:
        print("SELFTEST FAIL:")
        for p in problems:
            print("  ✗", p)
        return 1
    print("SELFTEST PASS (synthetic: reads detected; absent field not detected)")
    return 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return _selftest()
    json_out = argv[argv.index("--json") + 1] if "--json" in argv else None
    max_show = int(argv[argv.index("--max-show") + 1]) if "--max-show" in argv else 50
    res = audit_completeness()
    _print(res, max_show)
    if json_out:
        with open(json_out, "w", encoding="utf-8") as fh:
            json.dump({"green": res.green, "stats": res.stats, "fails": res.fails, "warns": res.warns}, fh, indent=1)
        print(f"\nwrote {json_out}")
    print(f"\nRESULT: {'PASS' if res.green else 'FAIL'} ({len(res.fails)} fail, {len(res.warns)} warn)")
    return 1 if not res.green else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
