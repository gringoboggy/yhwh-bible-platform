#!/usr/bin/env python3
"""Manuscript C-2 first-draft transcription, run as a standalone script.

The twin of ``run_manuscript_review_at_scale.py``. Together they retire the
manuscript-vision OOM crash class: both the transcription (C-2) and review
(R-round) steps that used to be performed by *agents reading PNG crops*
(piling image bytes into the parent harness buffer until it OOM'd) now run
in a standalone process whose image bytes go straight to the API.

The model returns each verse's `geez` string (+ column/line/uncertain
notes); this script computes `tokens` from that geez using the validator's
OWN tokenizer (``manuscript_records._geez_to_tokens``), so the geez<->tokens
invariant holds by construction and the draft is structurally valid input
for C-3 review.

Usage:
    py scripts/run_manuscript_transcribe_at_scale.py \\
        --book 1ki --chapter 5 --witness GG \\
        --image GAPS/2_Kings/GG-00106/1-Kings/1-Kings_f030v.jpg \\
        --image GAPS/2_Kings/GG-00106/1-Kings/1-Kings_f031r.jpg \\
        --folio f030v --folio f031r \\
        --dry-run

Drop --dry-run for the real pass (needs ANTHROPIC_API_KEY + `pip install
anthropic Pillow`). Output: content/manuscript/<group>/calibration/
<book><ch>_witness<W>.json (override with --out).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core.manuscript_records import (  # noqa: E402
    _geez_to_tokens,
    validate_witness,
)
from scripts.run_manuscript_review_at_scale import load_topology  # noqa: E402

# mint-9 #19: ANSI colour constants from the shared at_scale_base (driver, not core).
from scripts.core.at_scale_base import DIM, GREEN, RED, RESET  # noqa: E402

TRANSCRIBE_OUTPUT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "verses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "v": {"type": "integer"},
                    "column": {"type": "string"},
                    "line_start": {"type": "integer"},
                    "geez": {"type": "string"},
                    "uncertain": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "token_index": {"type": "integer"},
                                "marker": {
                                    "type": "string",
                                    "enum": ["uncertain", "damaged", "illegible"],
                                },
                                "note": {"type": "string"},
                            },
                            "required": ["token_index", "marker", "note"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["v", "column", "line_start", "geez", "uncertain"],
                "additionalProperties": False,
            },
        },
        "transcription_notes": {"type": "string"},
    },
    "required": ["verses", "transcription_notes"],
    "additionalProperties": False,
}

_TRANSCRIBE_PROTOCOL = """\
You are transcribing an Ethiopic (Ge'ez) biblical manuscript folio. Produce
a faithful first-draft diplomatic transcription of EXACTLY what the
parchment inks — not what a printed Bible says it should say. Transcribe as
written, including scribal variants and apparent errors; flag uncertainty
rather than silently normalising.

Rules:
- Separate words with the black wordspace ` ፡ ` (U+1361, space-padded).
- Preserve the RED body cross `✣` (U+2723) as its own glyph in the geez
  where it appears between words — do NOT collapse it to `፡` and do NOT
  promote it to a fidel like `እ`. Rubric crosses `❈` are rubric-only.
- Read column by column, line by line. Note line-break splits: a word
  broken across a line/column boundary is ONE token, not two.
- For each verse give: `v` (number), `column` (e.g. "f030v-M-L23" =
  folio-column-line), `line_start`, the `geez` string, and `uncertain[]`
  entries (marker ∈ uncertain|damaged|illegible) for anything you cannot
  read confidently. Be honest about resolution limits.
- Do NOT output a `tokens` field — it is computed downstream from `geez`.
Return ONLY the structured JSON of the required schema.
"""


def build_system_prompt(topology_text: str, witness_sig: str) -> str:
    parts = [_TRANSCRIBE_PROTOCOL]
    if topology_text:
        parts.append(
            f"\n\n--- {witness_sig} topology (known scribal-hand failure classes to watch for) ---\n{topology_text}"
        )
    return "".join(parts)


def assemble_witness(
    model_out: dict,
    *,
    book: str,
    chapter: int,
    witness_sig: str,
    source_images: list[str],
    folio_sigla: list[str],
) -> dict:
    """Assemble a full witness record from the model's per-verse output.

    `tokens` is computed from `geez` via the validator's tokenizer so the
    geez<->tokens invariant is guaranteed. Each verse dict is built with
    exactly the six schema keys.
    """
    verses_in = model_out.get("verses") if isinstance(model_out, dict) else None
    if not isinstance(verses_in, list):
        verses_in = []
    verses_out = []
    for mv in verses_in:
        if not isinstance(mv, dict):
            continue
        geez = mv.get("geez", "") or ""
        uncertain = mv.get("uncertain")
        if not isinstance(uncertain, list):
            uncertain = []
        verses_out.append(
            {
                "v": mv.get("v"),
                "column": mv.get("column", ""),
                "line_start": mv.get("line_start", 0),
                "geez": geez,
                "tokens": _geez_to_tokens(geez),
                "uncertain": uncertain,
            }
        )
    notes = ""
    if isinstance(model_out, dict):
        notes = model_out.get("transcription_notes") or ""
    return {
        "witness": witness_sig,
        "book": book,
        "chapter": chapter,
        "source_images": source_images,
        "folio_sigla": folio_sigla,
        "verses": verses_out,
        "transcription_notes": notes,
    }


def run_transcribe(
    *,
    book: str,
    chapter: int,
    witness_sig: str,
    source_images: list[str],
    folio_sigla: list[str],
    vision_client,
    topology_text: str,
    image_blocks: list[dict],
    max_tokens: int = 8192,
) -> dict:
    """Run one C-2 transcription pass and return the assembled witness dict."""
    system_prompt = build_system_prompt(topology_text, witness_sig)
    user_text = (
        f"Transcribe {book} chapter {chapter}, witness {witness_sig}, "
        f"folios {', '.join(folio_sigla)}. The attached image(s) are those "
        f"folios in order. Output every verse you can read on these folios."
    )
    model_out = vision_client.analyze(
        system_prompt,
        user_text,
        image_blocks,
        output_schema=TRANSCRIBE_OUTPUT_SCHEMA,
        max_tokens=max_tokens,
    )
    return assemble_witness(
        model_out if isinstance(model_out, dict) else {},
        book=book,
        chapter=chapter,
        witness_sig=witness_sig,
        source_images=source_images,
        folio_sigla=folio_sigla,
    )


def _estimate_cost(n_images: int, model: str) -> float:
    base = 0.06 if "opus" in model else 0.02
    return round(base + n_images * 0.03, 3)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--book", required=True)
    p.add_argument("--chapter", type=int, required=True)
    p.add_argument("--witness", required=True, choices=["GG", "CAM"])
    p.add_argument("--image", action="append", default=[], help="Folio image path (repeatable, in order)")
    p.add_argument("--folio", action="append", default=[], help="Folio sigil (repeatable, in order)")
    p.add_argument("--model", default=None)
    p.add_argument("--out", default=None)
    p.add_argument("--max-edge", type=int, default=None)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    if not args.image:
        print(f"{RED}REFUSING:{RESET} at least one --image required", file=sys.stderr)
        return 1
    folio_sigla = args.folio or [Path(i).stem for i in args.image]

    from scripts.core import manuscript_vision as mv

    model = args.model or mv.DEFAULT_VISION_MODEL
    max_edge = args.max_edge or mv.MAX_IMAGE_EDGE
    out_path = (
        Path(args.out)
        if args.out
        else REPO_ROOT
        / "content"
        / "manuscript"
        / ("kings" if args.book.endswith("ki") else "samuel" if args.book.endswith("sa") else "other")
        / "calibration"
        / f"{args.book}{args.chapter}_witness{args.witness}.json"
    )

    print(f"Transcribe: {args.book}{args.chapter} {args.witness} · model={model}")
    print(f"  images: {len(args.image)} · max-edge={max_edge}px · out={out_path}")
    print(f"  projected cost: ~${_estimate_cost(len(args.image), model):.3f} USD")
    print()

    if args.dry_run:
        print(f"{DIM}--dry-run: no API call made; nothing written.{RESET}")
        return 0

    image_blocks = []
    src_rel = []
    for i in args.image:
        ip = Path(i)
        if not ip.is_absolute():
            ip = REPO_ROOT / ip
        if not ip.exists():
            print(f"{RED}REFUSING:{RESET} image missing: {ip}", file=sys.stderr)
            return 1
        image_blocks.append(mv.crop_and_encode(str(ip), (0, 0, 10**9, 10**9), max_edge=max_edge))
        src_rel.append(i)

    try:
        client = mv.AnthropicVisionClient(model=model)
    except mv.sources.SourceMissingError as e:
        print(f"{RED}REFUSING:{RESET} {e}", file=sys.stderr)
        return 1

    topology_text = load_topology(args.witness)
    witness = run_transcribe(
        book=args.book,
        chapter=args.chapter,
        witness_sig=args.witness,
        source_images=src_rel,
        folio_sigla=folio_sigla,
        vision_client=client,
        topology_text=topology_text,
        image_blocks=image_blocks,
    )

    ok, errors = validate_witness(witness)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(witness, ensure_ascii=False, indent=2), encoding="utf-8")

    color = GREEN if ok else RED
    print(f"{color}{'VALID' if ok else 'INVALID (C-3 will reconcile)'}{RESET} · {len(witness['verses'])} verses")
    for e in errors[:8]:
        print(f"  - {e}")
    print(f"  witness: {out_path}")
    if client.last_usage:
        print(f"  {DIM}usage: {client.last_usage}{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
