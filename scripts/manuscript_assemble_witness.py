#!/usr/bin/env python3
"""Assemble + validate + write a witness JSON from a converged model_out.

The agent path's write step (P1 of the Sam/Kings cloud plan
``plans/2026-06-02-samkings-cloud-agent-workflow-and-run-plan.md``). It is a
drop-in for the API path's write: it reuses the EXISTING pure
``scripts.run_manuscript_transcribe_at_scale.assemble_witness`` so the on-disk
artifact is byte-identical to what the ``--book/--chapter/--witness`` API driver
produces — only the *source* of ``model_out`` differs (a vision sub-agent's
converged output instead of ``client.messages.create``). The batch Workflow
shells out to this CLI, piping the converged ``model_out`` JSON on stdin.

CLI::

    echo '<model_out json>' | python scripts/manuscript_assemble_witness.py \\
        --book 1ki --chapter 5 --witness GG \\
        --source-image GAPS/2_Kings/GG-00106/1-Kings/1-Kings_f030v.jpg \\
        --folio f030v [--out PATH]

Default ``--out``: ``content/manuscript/<track>/calibration/<book><ch>_witness<W>.json``
(the exact path the at-scale review/collation drivers read).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core.manuscript_records import validate_witness  # noqa: E402
from scripts.run_manuscript_transcribe_at_scale import assemble_witness  # noqa: E402


def _track_for(book: str) -> str:
    return "kings" if book.endswith("ki") else "samuel" if book.endswith("sa") else "other"


def assemble_and_write(
    model_out: dict,
    *,
    book: str,
    chapter: int,
    witness: str,
    source_images,
    folios=None,
    out_path: str | None = None,
) -> tuple[bool, str, list[str]]:
    """Assemble → validate → write a witness JSON. Returns ``(ok, path, errors)``.

    Writes the witness REGARDLESS of validity (mirroring the at-scale driver —
    the C-3 / Track-1 QA review reconciles invalids), but reports ``ok`` +
    ``errors`` so the caller can flag ``needs_qa``. ``tokens`` are computed from
    ``geez`` by :func:`assemble_witness`, so the geez↔tokens invariant holds by
    construction; ``validate_witness`` mainly catches non-Ethiopic contamination
    and structural issues.
    """
    rec = assemble_witness(
        model_out,
        book=book,
        chapter=chapter,
        witness_sig=witness,
        source_images=list(source_images),
        folio_sigla=list(folios or source_images),
    )
    ok, errors = validate_witness(rec)
    out = (
        Path(out_path)
        if out_path
        else REPO_ROOT
        / "content"
        / "manuscript"
        / _track_for(book)
        / "calibration"
        / f"{book}{chapter}_witness{witness}.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    return ok, str(out), errors


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Assemble+write a witness JSON from a model_out on stdin.")
    p.add_argument("--book", required=True)
    p.add_argument("--chapter", type=int, required=True)
    p.add_argument("--witness", required=True, choices=["GG", "CAM"])
    p.add_argument("--source-image", action="append", default=[], dest="source_image")
    p.add_argument("--folio", action="append", default=[])
    p.add_argument("--out", default=None)
    args = p.parse_args(argv)

    model_out = json.load(sys.stdin)
    ok, path, errors = assemble_and_write(
        model_out,
        book=args.book,
        chapter=args.chapter,
        witness=args.witness,
        source_images=args.source_image,
        folios=args.folio,
        out_path=args.out,
    )
    print(path)
    for e in errors[:8]:
        print(f"  - {e}", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
