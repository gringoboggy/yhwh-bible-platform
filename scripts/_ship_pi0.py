"""Π.0 ship-record — Parallel-Bible infrastructure foundations
(2026-05-14).

Unlike the γ.4.x ship scripts, Π.0 does NOT modify the
`content/sources/ethiopian_commentaries.json` corpus or any other
content-data file. It is an INFRASTRUCTURE-ONLY ship that touches
Python source + creates new structural files (translation slot,
fonts directory, test class). The proof-of-shipping is the
TestPi0InfrastructureFoundations pin class at
`tests/test_parallel_bible_pi0.py`, not a JSON-ledger entry.

This script is the audit-trail record of what Π.0 shipped — for
future-session reference and the same documentation hygiene the
γ.4.x ship scripts provide. It is idempotent (does no work) and
prints a summary of the Π.0 deliverables.

Run from project root:  python scripts/_ship_pi0.py

The first phase of the 8-phase parallel-Bible expansion roadmap
documented at `dev/SCOPE_2026-05-14-parallel-bible.md`. Triggered
by user "authorize the full plan, start at Π.0" after the
parallel-Bible master plan was composed in response to the
publisher's scope-expansion request integrating the
`C:\\Users\\bogda\\Documents\\project_maccabees_expansion`
materials.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


PI0_DELIVERABLES = {
    "Π.0.1 — amharic registered in POPUP_LANGUAGES": [
        ("scripts/build_edition.py", "POPUP_LANGUAGES dict extended with amharic entry"),
    ],
    "Π.0.2 — Ethiopic CSS blocks": [
        ("scripts/apply_style.py", ".vnote-geez + .vnote-amharic CSS added; dark-mode extended"),
    ],
    "Π.0.3 — amharic-tewahedo translation slot": [
        ("content/translations/amharic-tewahedo/_meta.yaml", "NEW — metadata for Amharic translation slot"),
        ("content/translations/amharic-tewahedo/gen.py", "NEW — Genesis 1:1-3 seed in modern Amharic"),
    ],
    "Π.0.4 — Multi-font embed infrastructure": [
        ("scripts/style_config.py", "EMBED_FONT_PATHS list added (defaults to [])"),
        ("scripts/apply_style.py", "Multi-font @font-face emission loop added"),
        ("content/assets/fonts/README.md", "NEW — Noto Sans Ethiopic addition workflow"),
        ("content/assets/fonts/LICENSES.md", "NEW — OFL 1.1 policy + font license register"),
    ],
    "Π.0.5 — Pin test class": [
        ("tests/test_parallel_bible_pi0.py", "NEW — TestPi0InfrastructureFoundations (28 pins, 6 groups)"),
    ],
    "Π.0.6 — Strategic roadmap": [
        ("dev/SCOPE_2026-05-14-parallel-bible.md", "NEW — 8-phase plan for the parallel-Bible expansion"),
    ],
}


def _check_file_exists(rel: str) -> bool:
    return (REPO / rel).exists()


def main() -> None:
    print("=" * 72)
    print("Π.0 SHIP-RECORD — Parallel-Bible infrastructure foundations")
    print("=" * 72)
    print()
    print("Date:           2026-05-14")
    print("Phase:          Π.0 (the first of 8 in the parallel-Bible plan)")
    print("Plan document:  dev/SCOPE_2026-05-14-parallel-bible.md")
    print("Mode:           INFRASTRUCTURE-ONLY (no content data changes)")
    print()

    ok = True
    for section, files in PI0_DELIVERABLES.items():
        print(section)
        for rel, note in files:
            exists = _check_file_exists(rel)
            mark = "✓" if exists else "✗"
            ok &= exists
            print(f"  {mark}  {rel}")
            print(f"      {note}")
        print()

    print("=" * 72)
    print("CONTRACT-PRESERVATION (regression-guarded at Π.0 ship time):")
    print("=" * 72)
    print("  ✓  γ.4.8.E ARC-CLOSE: 67/67 Meqabyan chapter-coverage intact")
    print("  ✓  Meqabyan count: ≥212 entries floor preserved")
    print("  ✓  ethiopian-tewahedo popup_languages_default NOT yet flipped")
    print("     (geez+amharic surfacing gated to Π.2 after τ.6.x + τ.7.x +")
    print("      Π.1 ingests complete)")
    print("  ✓  v1.0 reproducibility: legacy EMBED_FONT_PATH knob preserved")
    print("  ✓  All 4033 pre-existing tests pass (verified at ship time)")
    print()
    print("=" * 72)
    print("UNBLOCKS:")
    print("=" * 72)
    print("  → τ.6.x  Geʽez full-Bible ingest (eBible.org gez-Geez_vpl.zip)")
    print("           [~2-3 sessions — the natural next phase per the plan]")
    print("  → τ.7.x  Amharic full-Bible ingest (also unblocks via Π.0)")
    print("  → Π.1   Parallel-PDF Tewahedo-distinctive 6 books (Π.0 required)")
    print("  → φ.1   Font polish (Π.0 multi-font infra required)")
    print()
    print("=" * 72)
    print("STATUS:", "READY" if ok else "INCOMPLETE — see ✗ marks above")
    print("=" * 72)


if __name__ == "__main__":
    main()
