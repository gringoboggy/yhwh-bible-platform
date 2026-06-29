#!/usr/bin/env python3
"""Detect OCR-extraction noise in study-note bodies (device-QA round-2, cluster H-c).

Scanned public-domain sources occasionally bleed page "furniture" — a running page
header plus its page number, e.g. ``-- THE SEPTUAGINT. 61`` — into the extracted note
text. It surfaces as visible garbage on every reader (the user saw it on Kobo in the
Genesis 1:1 manuscript-witness note: "n Library at Eome ... -- THE SEPTUAGINT. 61 10-13
Ps. 106. 27 133.").

This is a CANDIDATE finder for source-verified corpus cleanup, NOT an auto-fixer: the
project's faith-driven no-guessing rule means each flagged note is corrected against its
actual source by a human / the corpus lane, not rewritten by heuristic. The detector's
job is to enumerate the class so none is missed.

Usage:
    py -3 dev/audit_note_ocr.py                  # scan content/notes/*.py, print candidates
    py -3 dev/audit_note_ocr.py --json OUT.json  # also write a machine-readable findings file
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

import re

REPO = Path(__file__).resolve().parent.parent
NOTES_DIR = REPO / "content" / "notes"

# Running-header OCR noise: a dash, then 2+ ALL-CAPS words (a scanned page's running book
# header), then a period and a 1-4 digit page number — e.g. "-- THE SEPTUAGINT. 61". The
# leading dash + ALL-CAPS-multiword + period + bare page number together are the distinctive
# signature; ordinary emphatic ALL-CAPS prose ("the LORD GOD of Israel") lacks the trailing
# ". <page-number>". Kept deliberately precise (a candidate list, not a recall sweep).
_RUNNING_HEADER_RE = re.compile(r"(?:--|—)\s*[A-Z]{2,}(?:[ '&-]+[A-Z]{2,})+\.\s*\d{1,4}\b")


def detect_note_ocr_noise(body: str) -> list[str]:
    """Return the OCR running-header/page-number snippets in ``body`` (empty == clean)."""
    return [m.group(0).strip() for m in _RUNNING_HEADER_RE.finditer(body)]


def _load_notes(path: Path) -> list:
    """Load a note module's ``NOTES`` list via ast.literal_eval (never exec — RULES §7.1).

    Returns ``[]`` if the file has no literal ``NOTES`` assignment (e.g. composed at
    runtime) — such files are reported as skipped by the caller, never executed."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "NOTES":
                    try:
                        return ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        return []
    return []


def scan_notes_dir(notes_dir: Path = NOTES_DIR) -> list[dict]:
    """Scan every ``content/notes/*.py`` NOTES body for OCR noise; return a findings list."""
    findings: list[dict] = []
    for path in sorted(notes_dir.glob("*.py")):
        for note in _load_notes(path):
            if not isinstance(note, (list, tuple)) or len(note) < 8 or not isinstance(note[7], str):
                continue
            hits = detect_note_ocr_noise(note[7])
            if hits:
                findings.append(
                    {
                        "book": path.stem,
                        "chapter": note[0],
                        "verse": note[1],
                        "suffix": note[2],
                        "kind": note[4],
                        "snippets": hits,
                    }
                )
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Detect OCR running-header/page-number noise in note bodies.")
    ap.add_argument("--json", type=Path, help="write findings to this JSON file")
    args = ap.parse_args(argv)
    findings = scan_notes_dir()
    for f in findings:
        loc = f"{f['book']} {f['chapter']}:{f['verse']}{f['suffix']} [{f['kind']}]"
        print(f"{loc} -> {f['snippets']}")
    print(f"\n{len(findings)} note(s) with OCR running-header/page-number noise.")
    if args.json:
        args.json.write_text(json.dumps(findings, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"findings written to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
