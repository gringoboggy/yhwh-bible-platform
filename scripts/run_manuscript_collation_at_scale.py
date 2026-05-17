#!/usr/bin/env python3
"""Phase τ.6.x.4.b — Samuel dual-manuscript collation at-scale driver.

The book-wide harness for the Phase-2 collation TOOL (Units A-E,
shipped Tasks 1-8). Walks the folio manifest over every chapter of
1 Samuel (1-31) and 2 Samuel (1-24) and, for each chapter that is
ALREADY calibrated AND whose two witness records exist on disk,
runs the proven engine (validate → collate → reconcile) and persists
the per-chapter collation + the per-book critical apparatus.

Mirrors the established at-scale driver pattern (rules §9 —
``scripts/run_ethiopian_at_scale.py`` / ``run_naves_at_scale.py`` /
``run_ai_notes_at_scale.py``): a pure-stats ``run(dry=...)`` core +
a ``main()`` that prints the report and exits 0; ``dry=True`` is
strictly report-only (writes nothing, mutates nothing). Same
idempotent shape, same per-book stats dict.

WHAT IS / IS NOT THIS DRIVER'S JOB
----------------------------------
A chapter is **collatable** iff its manifest entry is
``status == "calibrated"`` with non-empty GG+CAM folios AND its two
witness JSONs exist under
``content/manuscript/samuel/calibration/``. As of τ.6.x.4.b that is
exactly the four Phase-1 calibration chapters (1sa 1, 1sa 3,
1sa 17, 2sa 11). Every other chapter (51 of them) is **pending** —
it still needs the Phase-1 blind dual-witness procedure (isolated
GG vision-transcribe → adversarial review → CUDL-IIIF CAM hi-res
via the ``cudl-iiif-access`` method → isolated CAM vision-
transcribe → adversarial review → collate), one chapter at a time,
manifest-tracked, via subagent-driven-development exactly as
Phase-1 did. This driver does **not** itself run that vision
marathon — it reports precisely which chapters await it
(``pending_needs_transcription``) and collates the ones already
calibrated. The marathon is the downstream effort (Phase-2.5/3).

Output (``dry=False`` ONLY):
    content/manuscript/samuel/collation/<ref>_collation.json
        — per-chapter engine collation (the NEW collation dir; the
        Task-1..8 ``calibration/`` dir is IMMUTABLE and is never
        written here).
    content/apparatus/<book>.json
        — the per-book critical apparatus (atomic-write, rules §7.1;
        the ``content/apparatus/`` dir contract is the Task-7
        ``content/apparatus/.gitkeep``).

Usage:
    python3 scripts/run_manuscript_collation_at_scale.py          # report (dry)
    python3 scripts/run_manuscript_collation_at_scale.py --write  # collate+persist
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import manuscript_manifest as mm  # noqa: E402
from scripts.core import manuscript_collation as mc  # noqa: E402
from scripts.core import manuscript_reconcile as mr  # noqa: E402
from scripts.core.manuscript_records import validate_witness  # noqa: E402

CALIBRATION_DIR = REPO_ROOT / "content" / "manuscript" / "samuel" / "calibration"
# The NEW per-chapter collation output dir — distinct from (and never
# written in place of) the IMMUTABLE Task-1..8 ``calibration/`` dir.
COLLATION_DIR = REPO_ROOT / "content" / "manuscript" / "samuel" / "collation"

# Books in the Samuel track and their chapter counts (1 Samuel 1-31,
# 2 Samuel 1-24 — the manifest is seeded for exactly this range).
BOOK_CHAPTERS = {"1sa": 31, "2sa": 24}

# The four Phase-1 calibration chapters: (book, ch) → witness-file ref
# stem. Only these have witness JSONs on disk today; every other
# chapter is pending the blind dual-witness transcription marathon.
CALIBRATED_REFS = {
    ("1sa", 1): "1sa1",
    ("1sa", 3): "1sa3",
    ("1sa", 17): "1sa17",
    ("2sa", 11): "2sa11",
}

# The downstream Phase-1 procedure each pending chapter still needs.
# Named so the report is self-documenting (and so a reader knows the
# driver is NOT the thing that runs it).
PENDING_PROCEDURE = (
    "Phase-1 blind dual-witness procedure: isolated GG vision-transcribe "
    "→ adversarial review → CUDL-IIIF CAM hi-res (via the cudl-iiif-access "
    "method) → isolated CAM vision-transcribe → adversarial review → "
    "collate; one chapter at a time, manifest-tracked, via "
    "subagent-driven-development (exactly as Phase-1 did). The driver does "
    "NOT run this marathon — it is the downstream effort (Phase-2.5/3)."
)

GREEN = "\033[92m"
DIM = "\033[2m"
RESET = "\033[0m"


def _ref_for(book: str, ch: int) -> str | None:
    """The witness-file ref stem for ``(book, ch)``, or ``None`` if this
    chapter is not one of the four Phase-1 calibration chapters."""
    return CALIBRATED_REFS.get((book, ch))


def _witness_paths(ref: str) -> tuple[Path, Path]:
    """GG + CAM(hires) witness JSON paths for a calibration ref.

    The CAM witness is always the hi-res transcription
    (``<ref>_witnessCAM_hires.json``) — the only CAM file the engine
    and the calibration goldens consume (see the test suite's
    ``TestCalibrationInvariants``)."""
    return (
        CALIBRATION_DIR / f"{ref}_witnessGG.json",
        CALIBRATION_DIR / f"{ref}_witnessCAM_hires.json",
    )


def _is_collatable(entry: dict, ref: str | None) -> bool:
    """A chapter is collatable iff its manifest entry is calibrated with
    non-empty GG+CAM folios AND its two witness JSONs exist on disk.

    Pure predicate — no mutation, no engine call (the report path must
    stay side-effect-free)."""
    if ref is None:
        return False
    if entry.get("status") != "calibrated":
        return False
    gg_folios = (entry.get("GG") or {}).get("folios") or []
    cam_folios = (entry.get("CAM") or {}).get("folios") or []
    if not gg_folios or not cam_folios:
        return False
    gg_path, cam_path = _witness_paths(ref)
    return gg_path.is_file() and cam_path.is_file()


def _collate_chapter(book: str, ch: int, ref: str) -> tuple[dict, list]:
    """Run the proven engine for one calibrated chapter.

    validate both witnesses (HARD gate) → ``collate`` → ``reconcile``.
    Returns ``(collation, apparatus)``. Pure w.r.t. the filesystem —
    persistence is the caller's job (and only when ``dry=False``)."""
    gg_path, cam_path = _witness_paths(ref)
    gg = json.loads(gg_path.read_text(encoding="utf-8"))
    cam = json.loads(cam_path.read_text(encoding="utf-8"))

    for label, rec in (("GG", gg), ("CAM", cam)):
        ok, errs = validate_witness(rec)
        if not ok:
            raise ValueError(f"{ref} {label} witness invalid: {errs}")

    kjv = mc.load_kjv_skeleton(book, ch)
    collation = mc.collate(gg, cam, kjv, book=book, chapter=ch)
    _reconciled, apparatus = mr.reconcile(collation)
    return collation, apparatus


def _write_collation(ref: str, collation: dict) -> Path:
    """Persist the per-chapter collation to the NEW collation dir.

    NEVER writes to the immutable ``calibration/`` dir. Goes through
    the project's atomic-write convention (rules §7.1) so a crash
    mid-write cannot leave a half-written collation."""
    from scripts.core.notes_io import atomic_write

    path = COLLATION_DIR / f"{ref}_collation.json"
    text = json.dumps(collation, ensure_ascii=False, indent=2)
    return Path(atomic_write(str(path), text))


def run(dry: bool = True) -> dict:
    """Book-wide collation driver core (rules §9).

    Walks the folio manifest over 1sa 1-31 + 2sa 1-24. For each
    chapter, classifies it collatable (calibrated + witness JSONs on
    disk) or pending (still needs the blind dual-witness marathon).

    ``dry=True`` (default) is **strictly report-only**: it MUST NOT
    write any file and MUST NOT mutate anything under ``content/``.
    It returns the coverage/status dict and stops.

    ``dry=False``: for every collatable chapter it validates both
    witnesses, collates, reconciles, then writes
    ``content/manuscript/samuel/collation/<ref>_collation.json`` and
    ``content/apparatus/<book>.json`` (the NEW collation dir + the
    apparatus dir — NEVER the immutable ``calibration/`` dir).

    Returns a stats dict::

        {
          "dry": <bool>,
          "chapters_total": 55,
          "chapters_collated": <int ≥ 4>,
          "chapters_pending": <int ≥ 1 (51)>,
          "by_book": {
            "1sa": {"total", "collated", "pending",
                    "collated_refs": [...], "pending_chapters": [...]},
            "2sa": {...},
          },
          "collated": [{"book","chapter","ref"}, ...],
          "pending_needs_transcription": [
            {"book","chapter","needs": <PENDING_PROCEDURE>}, ...],
          "written": [<path>, ...],          # [] when dry
          "apparatus_written": [<path>, ...],  # [] when dry
          "pending_procedure": <PENDING_PROCEDURE>,
        }
    """
    mm.load_manifest.cache_clear()
    man = mm.load_manifest()

    by_book: dict[str, dict] = {}
    collated: list[dict] = []
    pending_needs: list[dict] = []
    # Group collatable chapters by book so a single apparatus write
    # per book covers every collated chapter of that book.
    apparatus_by_book: dict[str, list] = {}
    written: list[str] = []
    apparatus_written: list[str] = []

    for book, n_chapters in BOOK_CHAPTERS.items():
        book_stats = {
            "total": n_chapters,
            "collated": 0,
            "pending": 0,
            "collated_refs": [],
            "pending_chapters": [],
        }
        for ch in range(1, n_chapters + 1):
            entry = mm.chapter_entry(man, book, ch)
            ref = _ref_for(book, ch)
            if _is_collatable(entry, ref):
                book_stats["collated"] += 1
                book_stats["collated_refs"].append(ref)
                collated.append({"book": book, "chapter": ch, "ref": ref})
                if not dry:
                    collation, apparatus = _collate_chapter(book, ch, ref)
                    written.append(str(_write_collation(ref, collation)))
                    apparatus_by_book.setdefault(book, []).extend(apparatus)
            else:
                book_stats["pending"] += 1
                book_stats["pending_chapters"].append(ch)
                pending_needs.append({"book": book, "chapter": ch, "needs": PENDING_PROCEDURE})
        by_book[book] = book_stats

    # One apparatus file per book (dry=False only). The immutable
    # calibration/ dir is never touched; apparatus lives under
    # content/apparatus/<book>.json (Task-7 .gitkeep contract).
    if not dry:
        for book, app in apparatus_by_book.items():
            apparatus_written.append(mr.dump_apparatus(book, app))

    return {
        "dry": dry,
        "chapters_total": sum(BOOK_CHAPTERS.values()),
        "chapters_collated": len(collated),
        "chapters_pending": len(pending_needs),
        "by_book": by_book,
        "collated": collated,
        "pending_needs_transcription": pending_needs,
        "written": written,
        "apparatus_written": apparatus_written,
        "pending_procedure": PENDING_PROCEDURE,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Samuel dual-manuscript collation at-scale driver. Default is "
            "a dry report (writes nothing). --write collates every "
            "calibrated chapter and persists the collation + apparatus."
        ),
    )
    p.add_argument(
        "--write",
        action="store_true",
        help=(
            "actually collate every calibrated chapter and persist "
            "content/manuscript/samuel/collation/<ref>_collation.json + "
            "content/apparatus/<book>.json (default: dry report only)."
        ),
    )
    args = p.parse_args(argv)

    rep = run(dry=not args.write)

    mode = "WRITE" if not rep["dry"] else "DRY (report only — nothing written)"
    print(f"Samuel dual-manuscript collation at-scale — {mode}")
    print(
        f"  {rep['chapters_total']} chapters total · "
        f"{GREEN}{rep['chapters_collated']} collatable{RESET} · "
        f"{rep['chapters_pending']} pending the blind-transcription marathon"
    )
    print()
    for book in sorted(rep["by_book"]):
        s = rep["by_book"][book]
        print(
            f"  {GREEN}✓{RESET} {book:4s} {s['collated']:2d}/{s['total']:2d} collated "
            f"({', '.join(s['collated_refs']) or '—'}) · "
            f"{s['pending']:2d} pending"
        )
    print()

    if rep["dry"]:
        print(
            f"{DIM}{rep['chapters_pending']} chapters await the {RESET}"
            f"{DIM}Phase-1 blind dual-witness procedure (one chapter at a "
            f"time, manifest-tracked, via subagent-driven-development; "
            f"CUDL-IIIF per cudl-iiif-access). The driver does NOT run it "
            f"— it is the downstream marathon (Phase-2.5/3).{RESET}"
        )
        print(f"{DIM}Re-run with --write to collate the calibrated chapters.{RESET}")
    else:
        print(f"Collations written under: {COLLATION_DIR}")
        for w in rep["written"]:
            print(f"  {GREEN}✓{RESET} {w}")
        for a in rep["apparatus_written"]:
            print(f"  {GREEN}✓{RESET} apparatus → {a}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
