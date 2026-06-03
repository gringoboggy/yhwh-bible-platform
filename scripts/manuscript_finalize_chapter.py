#!/usr/bin/env python3
"""Finalize one dual-witness chapter from four blind passes (the agent path's
deterministic glue — P1 of the Sam/Kings cloud plan).

Composes the already-tested pieces into one step: for each witness, converge its
two blind passes (:func:`scripts.core.manuscript_converge.converge_passes`),
assemble the accepted ``model_out`` into a witness record (the pure
``assemble_witness``), validate + write it, then collate the two witnesses
(:func:`scripts.core.manuscript_collation.collate_base_structured`) and run the
honesty gate (:func:`base_structured_ok`). Returns a metrics dict the batch
Workflow / pilot reads.

Input (stdin JSON)::

    {"track": "kings", "book": "1ki", "chapter": 1,
     "gg":  {"a": <model_out>, "b": <model_out>, "source_images": [...], "folios": [...]},
     "cam": {"a": <model_out>, "b": <model_out>, "source_images": [...], "folios": [...]}}

``--out-dir`` overrides where the witness JSONs are written (the proof writes to
a scratch dir so the immutable calibration reference is never clobbered).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core.manuscript_collation import base_structured_ok, collate_base_structured  # noqa: E402
from scripts.core.manuscript_converge import converge_passes  # noqa: E402
from scripts.core.manuscript_records import validate_witness  # noqa: E402
from scripts.run_manuscript_transcribe_at_scale import assemble_witness  # noqa: E402


def _track_for(book: str) -> str:
    return "kings" if book.endswith("ki") else "samuel" if book.endswith("sa") else "other"


def finalize_chapter(payload: dict, *, out_dir: str | None = None) -> dict:
    """Converge → assemble+write → collate → gate. Returns a metrics dict.

    Writes ``<out_dir or calibration>/<book><ch>_witness<W>.json`` for each
    witness. Does NOT mutate the manifest (that flip is the caller's, only for
    pending chapters — the proof runs on an already-calibrated chapter)."""
    book = payload["book"]
    chapter = int(payload["chapter"])
    out_base = Path(out_dir) if out_dir else REPO_ROOT / "content" / "manuscript" / _track_for(book) / "calibration"
    out_base.mkdir(parents=True, exist_ok=True)

    recs: dict[str, dict] = {}
    conv: dict[str, dict] = {}
    for key, sig in (("gg", "GG"), ("cam", "CAM")):
        w = payload[key]
        c = converge_passes(w["a"], w["b"])
        conv[key] = c
        rec = assemble_witness(
            c["accepted"],
            book=book,
            chapter=chapter,
            witness_sig=sig,
            source_images=list(w.get("source_images") or []),
            folio_sigla=list(w.get("folios") or w.get("source_images") or []),
        )
        ok, errs = validate_witness(rec)
        path = out_base / f"{book}{chapter}_witness{sig}.json"
        path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
        recs[key] = {"rec": rec, "valid": ok, "errors": errs, "path": str(path)}

    gg_rec, cam_rec = recs["gg"]["rec"], recs["cam"]["rec"]
    collation = collate_base_structured(gg_rec, cam_rec, book=book, chapter=chapter)
    cok, creasons = base_structured_ok(collation, gg_rec, cam_rec)

    return {
        "book": book,
        "chapter": chapter,
        "needs_qa": bool(conv["gg"]["needs_qa"] or conv["cam"]["needs_qa"]),
        "gg_convergence_pct": conv["gg"]["convergence_pct"],
        "cam_convergence_pct": conv["cam"]["convergence_pct"],
        "gg_identical_pct": conv["gg"]["identical_pct"],
        "cam_identical_pct": conv["cam"]["identical_pct"],
        "gg_divergent_loci": conv["gg"]["divergent_loci"],
        "cam_divergent_loci": conv["cam"]["divergent_loci"],
        "gg_valid": recs["gg"]["valid"],
        "cam_valid": recs["cam"]["valid"],
        "gg_errors": recs["gg"]["errors"][:8],
        "cam_errors": recs["cam"]["errors"][:8],
        "collation_ok": cok,
        "collation_reasons": creasons,
        "base_witness": collation.get("base_witness"),
        "verse_count": len(collation.get("primary_verses", [])),
        "witness_agreement": collation.get("metrics", {}).get("witness_agreement_basis"),
        "paths": {"GG": recs["gg"]["path"], "CAM": recs["cam"]["path"]},
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Finalize a dual-witness chapter from 4 blind passes (stdin JSON).")
    p.add_argument("--out-dir", default=None)
    args = p.parse_args(argv)
    payload = json.load(sys.stdin)
    result = finalize_chapter(payload, out_dir=args.out_dir)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if (result["gg_valid"] and result["cam_valid"] and result["collation_ok"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
