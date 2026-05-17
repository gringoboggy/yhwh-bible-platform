#!/usr/bin/env python3
"""Phase τ.6.x.4.b/c — Dual-manuscript collation at-scale driver (Samuel + Kings).

The book-wide harness for the Phase-2 collation TOOL (Units A-E,
shipped Tasks 1-8). Walks the folio manifest over every chapter of a
given track (default: Samuel 1-31 + 2 Samuel 1-24; Kings via
``--track kings`` / ``run(track="kings")``) and, for each chapter that
is ALREADY calibrated AND whose two witness records exist on disk,
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
``content/manuscript/<track>/calibration/``. For Samuel (τ.6.x.4.b)
that is exactly the four Phase-1 calibration chapters (1sa 1, 1sa 3,
1sa 17, 2sa 11). For Kings (τ.6.x.4.c) all chapters are pending until
each is collated under the same marathon. Every other chapter is
**pending** — it still needs the Phase-1 blind dual-witness procedure
(isolated GG vision-transcribe → adversarial review → CUDL-IIIF CAM
hi-res via the ``cudl-iiif-access`` method → isolated CAM vision-
transcribe → adversarial review → collate), one chapter at a time,
manifest-tracked, via subagent-driven-development exactly as Phase-1
did. This driver does **not** itself run that vision marathon — it
reports precisely which chapters await it
(``pending_needs_transcription``) and collates the ones already
calibrated. The marathon is the downstream effort (Phase-2.5/3).

Output (``dry=False`` ONLY):
    content/manuscript/<track>/collation/<ref>_collation.json
        — per-chapter engine collation (the NEW collation dir; the
        Task-1..8 ``calibration/`` dir is IMMUTABLE and is never
        written here).
    content/apparatus/<book>.json
        — the per-book critical apparatus (atomic-write, rules §7.1;
        the ``content/apparatus/`` dir contract is the Task-7
        ``content/apparatus/.gitkeep``).

Usage:
    python3 scripts/run_manuscript_collation_at_scale.py                      # report (dry, samuel)
    python3 scripts/run_manuscript_collation_at_scale.py --write              # collate+persist (samuel)
    python3 scripts/run_manuscript_collation_at_scale.py --track kings        # report (dry, kings)
    python3 scripts/run_manuscript_collation_at_scale.py --track kings --write  # collate+persist (kings)
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
from scripts.core.notes_io import atomic_write  # noqa: E402

CALIBRATION_DIR = REPO_ROOT / "content" / "manuscript" / "samuel" / "calibration"
# The NEW per-chapter collation output dir — distinct from (and never
# written in place of) the IMMUTABLE Task-1..8 ``calibration/`` dir.
COLLATION_DIR = REPO_ROOT / "content" / "manuscript" / "samuel" / "collation"

# Track registry: each entry maps a track name to its chapter counts
# and the subdirectory under content/manuscript/.
TRACKS: dict[str, dict] = {
    "samuel": {"chapters": {"1sa": 31, "2sa": 24}, "dir": "samuel"},
    "kings": {"chapters": {"1ki": 22, "2ki": 25}, "dir": "kings"},
}

# Books in the Samuel track and their chapter counts (1 Samuel 1-31,
# 2 Samuel 1-24 — the manifest is seeded for exactly this range).
# Kept at module level for back-compat with any external importer.
BOOK_CHAPTERS = TRACKS["samuel"]["chapters"]

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
RED = "\033[91m"
DIM = "\033[2m"
RESET = "\033[0m"


def _dirs(track: str) -> tuple[Path, Path]:
    """Return ``(cal_dir, coll_dir)`` for *track*.

    The calibration dir is always under the track's subdirectory and is
    IMMUTABLE — this driver never writes to it. The collation dir is the
    NEW per-chapter output dir (distinct from calibration)."""
    if track not in TRACKS:
        raise ValueError(f"Unknown track {track!r}; known: {list(TRACKS)}")
    base = REPO_ROOT / "content" / "manuscript" / TRACKS[track]["dir"]
    return base / "calibration", base / "collation"


# Runtime state: run() sets these before each loop so that the
# monkeypatched-signature-stable helpers (_collate_chapter,
# _write_collation) can resolve the correct dirs for the active track
# without a signature change (the TestScaleDriver monkeypatch test
# replaces these functions entirely and must not see a different call
# protocol).
_cal, _coll = _dirs("samuel")
_RUNTIME: dict[str, Path] = {"cal_dir": _cal, "coll_dir": _coll}


def _ref_for(book: str, ch: int) -> str:
    """Generic witness-file ref stem for ``(book, ch)``.

    Produces ``"<book><ch>"`` (e.g. ``"1sa1"``, ``"1sa3"``, ``"1ki1"``,
    ``"2ki25"``). For Samuel this is behavior-identical to the former
    CALIBRATED_REFS dict for the four Phase-1 chapters; returns a
    (non-None) string for every chapter so ``_is_collatable`` gates
    purely on file existence + manifest status."""
    return f"{book}{ch}"


def _witness_paths(ref: str, cal_dir: Path | None = None) -> tuple[Path, Path]:
    """GG + CAM(hires) witness JSON paths for a calibration ref.

    The CAM witness is always the hi-res transcription
    (``<ref>_witnessCAM_hires.json``) — the only CAM file the engine
    and the calibration goldens consume (see the test suite's
    ``TestCalibrationInvariants``).

    ``cal_dir`` defaults to the module-level ``CALIBRATION_DIR`` (Samuel)
    when not supplied, preserving back-compat for any direct caller."""
    d = cal_dir if cal_dir is not None else CALIBRATION_DIR
    return (
        d / f"{ref}_witnessGG.json",
        d / f"{ref}_witnessCAM_hires.json",
    )


def _is_collatable(entry: dict, ref: str, cal_dir: Path | None = None) -> bool:
    """A chapter is collatable iff its manifest entry is calibrated with
    non-empty GG+CAM folios AND its two witness JSONs exist on disk.

    Pure predicate — no mutation, no engine call (the report path must
    stay side-effect-free).

    ``cal_dir`` defaults to the module-level ``CALIBRATION_DIR`` (Samuel)
    when not supplied."""
    if entry.get("status") != "calibrated":
        return False
    gg_folios = (entry.get("GG") or {}).get("folios") or []
    cam_folios = (entry.get("CAM") or {}).get("folios") or []
    if not gg_folios or not cam_folios:
        return False
    gg_path, cam_path = _witness_paths(ref, cal_dir)
    return gg_path.is_file() and cam_path.is_file()


def _collate_chapter(book: str, ch: int, ref: str) -> tuple[dict, list]:
    """Run the proven engine for one calibrated chapter.

    validate both witnesses (HARD gate) → ``collate`` → ``reconcile``.
    Returns ``(collation, apparatus)``. Pure w.r.t. the filesystem —
    persistence is the caller's job (and only when ``dry=False``).

    Reads the active calibration dir from ``_RUNTIME["cal_dir"]`` which
    ``run()`` sets before the chapter loop (preserves the 3-arg
    signature required by the TestScaleDriver monkeypatch contract)."""
    gg_path, cam_path = _witness_paths(ref, _RUNTIME["cal_dir"])
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
    mid-write cannot leave a half-written collation.

    Reads the active collation dir from ``_RUNTIME["coll_dir"]`` which
    ``run()`` sets before the chapter loop (preserves the 2-arg
    signature required by the TestScaleDriver monkeypatch contract)."""
    path = _RUNTIME["coll_dir"] / f"{ref}_collation.json"
    text = json.dumps(collation, ensure_ascii=False, indent=2)
    return Path(atomic_write(str(path), text))


def run(dry: bool = True, track: str = "samuel") -> dict:
    """Book-wide collation driver core (rules §9).

    Walks the folio manifest over all chapters of *track* (default:
    ``"samuel"`` = 1sa 1-31 + 2sa 1-24, byte-identical back-compat;
    ``"kings"`` = 1ki 1-22 + 2ki 1-25 for τ.6.x.4.c). For each
    chapter, classifies it collatable (calibrated + witness JSONs on
    disk) or pending (still needs the blind dual-witness marathon).

    ``dry=True`` (default) is **strictly report-only**: it MUST NOT
    write any file and MUST NOT mutate anything under ``content/``.
    It returns the coverage/status dict and stops.

    ``dry=False``: for every collatable chapter it validates both
    witnesses, collates, reconciles, then writes
    ``content/manuscript/<track>/collation/<ref>_collation.json`` and
    ``content/apparatus/<book>.json`` (the NEW collation dir + the
    apparatus dir — NEVER the immutable ``calibration/`` dir).

    **Fail-soft (the 50+-chapter unattended marathon contract):** the
    per-chapter collatable body (validate → collate → reconcile →
    write) is isolated in ``try/except``. A single corrupt / missing /
    schema-invalid witness records ``{book, chapter, ref, error}`` into
    the ``failed`` report list and the driver **continues** to the next
    chapter — it never aborts the batch and never loses the apparatus
    already accumulated for chapters that DID succeed (the per-book
    apparatus flush still happens for those). ``failed`` is ALWAYS
    present in the report (an empty list in ``dry=True`` and whenever
    nothing failed); ``main()`` prints it prominently when non-empty
    and still exits 0 (failures are loud in the report, per the
    sibling at-scale convention — not signalled via exit code).

    Returns a stats dict::

        {
          "dry": <bool>,
          "chapters_total": <int>,
          "chapters_collated": <int>,
          "chapters_pending": <int>,
          "by_book": {
            "<book>": {"total", "collated", "pending",
                       "collated_refs": [...], "pending_chapters": [...]},
            ...
          },
          "collated": [{"book","chapter","ref"}, ...],
          "pending_needs_transcription": [
            {"book","chapter","needs": <PENDING_PROCEDURE>}, ...],
          "written": [<path>, ...],          # [] when dry
          "apparatus_written": [<path>, ...],  # [] when dry
          "failed": [                          # ALWAYS present; [] when
            {"book","chapter","ref","error"},  # dry or nothing failed
            ...],
          "pending_procedure": <PENDING_PROCEDURE>,
        }
    """
    cal_dir, coll_dir = _dirs(track)
    book_chapters = TRACKS[track]["chapters"]

    # Set the module-level runtime dirs so that the signature-stable
    # helpers _collate_chapter(book, ch, ref) and _write_collation(ref,
    # collation) use the correct track dirs (the monkeypatch test
    # replaces these functions entirely and must not see a signature
    # change — hence dir resolution via _RUNTIME rather than extra args).
    _RUNTIME["cal_dir"] = cal_dir
    _RUNTIME["coll_dir"] = coll_dir

    mm.load_manifest.cache_clear()
    man = mm.load_manifest(track=track)

    by_book: dict[str, dict] = {}
    collated: list[dict] = []
    pending_needs: list[dict] = []
    # Group collatable chapters by book so a single apparatus write
    # per book covers every collated chapter of that book.
    apparatus_by_book: dict[str, list] = {}
    written: list[str] = []
    apparatus_written: list[str] = []
    # Fail-soft: a chapter whose collate/write raised (corrupt /
    # missing / schema-invalid witness). Recorded here and SKIPPED —
    # the marathon batch is never aborted (rules §9 unattended-run
    # contract). ALWAYS in the report (empty in dry / when clean).
    failed: list[dict] = []

    for book, n_chapters in book_chapters.items():
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
            if _is_collatable(entry, ref, cal_dir):
                book_stats["collated"] += 1
                book_stats["collated_refs"].append(ref)
                collated.append({"book": book, "chapter": ch, "ref": ref})
                if not dry:
                    # Fail-soft per-chapter isolation (rules §9
                    # unattended-marathon contract): validate /
                    # json.loads / collate / reconcile / write may any
                    # raise on a corrupt / missing / schema-invalid
                    # witness. Isolate so one bad chapter is RECORDED
                    # and SKIPPED — the 50+-chapter batch is never
                    # aborted and the apparatus already accumulated for
                    # the chapters that DID succeed is preserved (the
                    # per-book flush below still runs for them).
                    try:
                        collation, apparatus = _collate_chapter(book, ch, ref)
                        written.append(str(_write_collation(ref, collation)))
                        apparatus_by_book.setdefault(book, []).extend(apparatus)
                    except Exception as e:
                        failed.append(
                            {
                                "book": book,
                                "chapter": ch,
                                "ref": ref,
                                "error": repr(e),
                            }
                        )
                        continue
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
        "chapters_total": sum(book_chapters.values()),
        "chapters_collated": len(collated),
        "chapters_pending": len(pending_needs),
        "by_book": by_book,
        "collated": collated,
        "pending_needs_transcription": pending_needs,
        "written": written,
        "apparatus_written": apparatus_written,
        "failed": failed,
        "pending_procedure": PENDING_PROCEDURE,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Dual-manuscript collation at-scale driver (Samuel + Kings). "
            "Default is a dry report (writes nothing). --write collates every "
            "calibrated chapter and persists the collation + apparatus."
        ),
    )
    p.add_argument(
        "--track",
        choices=list(TRACKS),
        default="samuel",
        help=(
            "which manuscript track to process (default: samuel). "
            "samuel = 1 Samuel 1-31 + 2 Samuel 1-24; "
            "kings = 1 Kings 1-22 + 2 Kings 1-25."
        ),
    )
    p.add_argument(
        "--write",
        action="store_true",
        help=(
            "actually collate every calibrated chapter and persist "
            "content/manuscript/<track>/collation/<ref>_collation.json + "
            "content/apparatus/<book>.json (default: dry report only)."
        ),
    )
    args = p.parse_args(argv)

    rep = run(dry=not args.write, track=args.track)

    track_label = args.track.capitalize()
    mode = "WRITE" if not rep["dry"] else "DRY (report only — nothing written)"
    print(f"{track_label} dual-manuscript collation at-scale — {mode}")
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
        _, coll_dir = _dirs(args.track)
        print(f"Collations written under: {coll_dir}")
        for w in rep["written"]:
            print(f"  {GREEN}✓{RESET} {w}")
        for a in rep["apparatus_written"]:
            print(f"  {GREEN}✓{RESET} apparatus → {a}")

    # Fail-soft surfacing: a non-empty ``failed`` list is printed
    # PROMINENTLY (the marathon ran unattended — a skipped chapter
    # must not be silent) but the process still exits 0 per the
    # sibling at-scale convention; failures are loud in the report,
    # not signalled via exit code.
    if rep["failed"]:
        print()
        print(
            f"{RED}⚠ {len(rep['failed'])} chapter(s) FAILED and were skipped "
            f"(batch NOT aborted; succeeded chapters' apparatus preserved):{RESET}"
        )
        for f in rep["failed"]:
            print(f"  {RED}✗{RESET} {f['book']} {f['chapter']} ({f['ref']}): {f['error']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
