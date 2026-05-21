#!/usr/bin/env python3
"""Manuscript R-round adversarial review, run as a standalone script.

This is "lever 4" — the offload that retires the manuscript-review OOM
crash class. Instead of an *agent* reading LANCZOS-upscaled PNG crops
(whose bytes pile up in the parent harness buffer for the whole 15-20 min
run until the Rust allocator panics), this script:

  1. crops each source folio to a single compact, downscaled JPEG
     (``manuscript_vision.crop_and_encode`` — never upscales, caps at
     1568 px, so two folios cost ~300 KB instead of ~30-60 MB);
  2. sends the images + the witness JSON to the vision API under a
     prompt-cached system prompt carrying the review protocol + the
     witness's topology file;
  3. runs the existing deterministic screens (``validate_witness``,
     ``screen_witness_for_class_failures``) and the round-escalation
     controller (``escalate_if_unbounded``);
  4. writes a human ``REVIEW_*.md`` and a machine ``defects_*.json``.

The image bytes live only in *this* process and go straight to the API.
Whatever consumes the result (you, or a fix-apply agent) reads only the
text artifacts — cheap, bounded, crash-proof.

Usage:
    # Dry run — plan + cost, no API key needed, no call made:
    py scripts/run_manuscript_review_at_scale.py \\
        --witness-path content/manuscript/kings/calibration/1ki5_witnessGG.json \\
        --round 2 --dry-run

    # Real review (needs ANTHROPIC_API_KEY + `pip install anthropic Pillow`):
    py scripts/run_manuscript_review_at_scale.py \\
        --witness-path content/manuscript/kings/calibration/1ki5_witnessGG.json \\
        --round 2

Cost: one vision call per chapter. Two ~1568 px folios ≈ ~3.2k image
tokens; the topology system prompt is cached after the first chapter in a
batch. Opus-grade review ≈ $0.05-0.30/chapter. ``--dry-run`` prints the
projection and exits before any call.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core.manuscript_chapter_class import classify  # noqa: E402
from scripts.core.manuscript_records import validate_witness  # noqa: E402
from scripts.core.manuscript_rounds import escalate_if_unbounded  # noqa: E402
from scripts.core.manuscript_self_check import (  # noqa: E402
    screen_witness_for_class_failures,
)

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
DIM = "\033[2m"
RESET = "\033[0m"

_REVIEWER_CONTEXT = REPO_ROOT / "content" / "manuscript" / "_reviewer_context"

# Hard defects = severities that gate another round. MINOR/NIT do not.
_HARD_SEVERITIES = ("CRITICAL", "MAJOR")

# Structured-output contract for the review call. additionalProperties is
# False everywhere so the model can't smuggle fields the renderer ignores.
REVIEW_OUTPUT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "overall_verdict": {"type": "string", "enum": ["NEEDS_FIX", "APPROVE"]},
        "boundary_verdict": {"type": "string"},
        "omission_check": {"type": "string"},
        "defects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "verse": {"type": "integer"},
                    "severity": {
                        "type": "string",
                        "enum": ["CRITICAL", "MAJOR", "MINOR"],
                    },
                    "locus": {"type": "string"},
                    "current": {"type": "string"},
                    "parchment": {"type": "string"},
                    "fix": {"type": "string"},
                    "defect_class": {"type": "string"},
                },
                "required": [
                    "verse",
                    "severity",
                    "locus",
                    "current",
                    "parchment",
                    "fix",
                    "defect_class",
                ],
                "additionalProperties": False,
            },
        },
        "new_ambiguous": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "overall_verdict",
        "boundary_verdict",
        "omission_check",
        "defects",
        "new_ambiguous",
    ],
    "additionalProperties": False,
}

_REVIEW_PROTOCOL = """\
You are a fresh, independent, adversarial reviewer for an Ethiopic (Ge'ez)
biblical manuscript transcription. You have NEVER seen this chapter before.
Do NOT consult any printed Bible, the KJV, the LXX/MT, a parallel edition,
or any other witness — judge ONLY what the parchment images in this message
actually ink, compared against the transcribed witness JSON below.

Method (per the project's manuscript-collation protocol):
- Read each verse's `geez` string against the folio image at the column /
  line the verse record names. Verify glyph by glyph at the high-risk
  positions the topology file flags.
- Distinguish the black wordspace `፡` (two dots) from the RED body cross
  `✣` (U+2723) and the rubric-only `❈`. A word ending in a 2nd-person
  suffix `ከ` followed by `✣` is routinely mis-parsed as `… ፡ ከእ ፡ …`
  (split at the `ከ`, cross promoted to fidel `እ`) — flag every such case.
- Watch the documented confused-fidel families (`ለ`/`ስ`, `ፈ`/`ረ`,
  `ሰ`/`ስ`, vowel-order micro-confusions) and line-break-split mis-merges
  at column and folio turns.
- Check for any mid-chapter scripture omission at every column-bottom →
  column-top and folio turn.

Severity:
- CRITICAL: parchment-anchored hard error (wrong glyph, dropped/added
  token, mis-merged line-break, cross mis-parse) that changes the reading.
- MAJOR: very likely error needing a fix this round, lower certainty.
- MINOR: vowel-order / orthographic nit or honest AMBIGUOUS-PARCHMENT item.

Return ONLY the structured JSON of the required schema:
- `overall_verdict`: NEEDS_FIX if any CRITICAL or MAJOR, else APPROVE.
- `defects[]`: one per locus, with `verse`, `severity`, `locus` (column +
  approximate line), `current` (what the JSON has), `parchment` (what the
  page inks), `fix` (the concrete correction), `defect_class` (the topology
  family, e.g. "le/se", "fa/ra", "body-cross", "line-break-split").
- `boundary_verdict`: confirm or reject the chapter's opening/closing
  rubric boundary identification.
- `omission_check`: state explicitly whether any verse/clause is missing at
  a column or folio turn.
- `new_ambiguous[]`: short labels for any genuinely-new ambiguity classes
  not resolvable at this image resolution.
Be honest about resolution limits — flag, don't guess.
"""


def load_topology(witness_sig: str) -> str:
    """Load the topology context file for the witness sigil (GG / CAM).

    Returns the file text, or an empty string if it's absent (the review
    still runs; the system prompt just lacks the confused-fidel catalog).
    """
    fname = {"GG": "GG_topology.md", "CAM": "CAM_topology.md"}.get(witness_sig)
    if not fname:
        return ""
    p = _REVIEWER_CONTEXT / fname
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def build_system_prompt(topology_text: str, witness_sig: str) -> str:
    """Review protocol + the witness's topology file. This is the cached
    prefix — stable across every chapter of a batch, so per-chapter calls
    only pay for the images + witness text after the first."""
    parts = [_REVIEW_PROTOCOL]
    if topology_text:
        parts.append(
            f"\n\n--- {witness_sig} topology (confirmed failure-class "
            f"catalog; treat as authoritative) ---\n{topology_text}"
        )
    return "".join(parts)


def build_user_text(witness: dict) -> str:
    """The per-chapter instruction: the witness JSON to scrutinise."""
    book = witness.get("book")
    chapter = witness.get("chapter")
    sigla = ", ".join(witness.get("folio_sigla", []))
    body = json.dumps(witness, ensure_ascii=False, indent=2)
    return (
        f"Witness under review: {book} chapter {chapter}, witness "
        f"{witness.get('witness')}, folios {sigla}.\n"
        f"The attached image(s) are those folios, in order.\n\n"
        f"Transcribed witness JSON to verify against the parchment:\n\n{body}"
    )


def run_review(
    witness: dict,
    *,
    vision_client,
    topology_text: str,
    image_blocks: list[dict],
    current_round: int,
    max_tokens: int = 4096,
) -> dict:
    """Assemble a full review result for one chapter.

    Pure orchestration: ``vision_client`` is injected (the production caller
    passes an ``AnthropicVisionClient``; tests pass a stub), so this runs
    with no network. Combines the model's vision findings with the
    deterministic screens and the round-escalation controller.
    """
    book = witness.get("book")
    chapter = witness.get("chapter")
    witness_sig = witness.get("witness")

    validator_ok, validator_errors = validate_witness(witness)
    chapter_class = classify(book, chapter)
    try:
        screen_flags = screen_witness_for_class_failures(witness, chapter_class)
    except Exception:
        screen_flags = []

    system_prompt = build_system_prompt(topology_text, witness_sig)
    user_text = build_user_text(witness)
    model_out = vision_client.analyze(
        system_prompt,
        user_text,
        image_blocks,
        output_schema=REVIEW_OUTPUT_SCHEMA,
        max_tokens=max_tokens,
    )
    if not isinstance(model_out, dict):
        model_out = {}

    defects = model_out.get("defects") or []
    if not isinstance(defects, list):
        defects = []
    hard_defects = sum(1 for d in defects if isinstance(d, dict) and d.get("severity") in _HARD_SEVERITIES)
    new_ambiguous_list = model_out.get("new_ambiguous") or []
    if not isinstance(new_ambiguous_list, list):
        new_ambiguous_list = []
    new_ambiguous = len(new_ambiguous_list)

    verdict = escalate_if_unbounded(chapter_class, current_round, hard_defects, new_ambiguous)

    return {
        "book": book,
        "chapter": chapter,
        "witness": witness_sig,
        "round": current_round,
        "chapter_class": chapter_class,
        "validator_ok": validator_ok,
        "validator_errors": validator_errors,
        "screen_flags": screen_flags,
        "overall_verdict": model_out.get("overall_verdict", ""),
        "boundary_verdict": model_out.get("boundary_verdict", ""),
        "omission_check": model_out.get("omission_check", ""),
        "defects": defects,
        "hard_defects": hard_defects,
        "new_ambiguous": new_ambiguous,
        "new_ambiguous_labels": new_ambiguous_list,
        "escalation": {
            "escalate": verdict.escalate,
            "reason": verdict.reason,
            "recommended_action": verdict.recommended_action,
        },
        "usage": getattr(vision_client, "last_usage", None),
        "model": getattr(vision_client, "model", None),
    }


def _defects_table(defects: list[dict], severity: str) -> list[str]:
    rows = [d for d in defects if d.get("severity") == severity]
    if not rows:
        return []
    out = [f"### {severity} ({len(rows)})", ""]
    for d in rows:
        out.append(
            f"- **v{d.get('verse')}** [{d.get('defect_class')}] "
            f"@ {d.get('locus')}: `{d.get('current')}` → `{d.get('parchment')}` "
            f"— fix: {d.get('fix')}"
        )
    out.append("")
    return out


def render_review_md(result: dict) -> str:
    """Render the human-readable REVIEW markdown from a run_review result."""
    lines: list[str] = []
    lines.append(f"# {result['book']}{result['chapter']} {result['witness']} vision review — Round {result['round']}")
    lines.append("")
    lines.append(f"**Date:** {date.today().isoformat()}")
    lines.append(f"**Chapter class:** {result['chapter_class']}")
    lines.append(f"**Model:** {result.get('model')}")
    lines.append(f"**Overall verdict:** {result.get('overall_verdict') or 'n/a'}")
    lines.append(
        f"**Hard defects (CRITICAL+MAJOR):** {result['hard_defects']} · **new ambiguous:** {result['new_ambiguous']}"
    )
    lines.append("")

    lines.append("## Deterministic screens")
    lines.append("")
    lines.append(f"- `validate_witness`: {'OK' if result['validator_ok'] else 'ERRORS'}")
    for err in result["validator_errors"]:
        lines.append(f"  - {err}")
    flags = result["screen_flags"]
    lines.append(f"- `screen_witness_for_class_failures`: {len(flags)} flag(s)")
    for f in flags:
        lines.append(f"  - {f}")
    lines.append("")

    lines.append("## Defects")
    lines.append("")
    any_def = False
    for sev in ("CRITICAL", "MAJOR", "MINOR"):
        block = _defects_table(result["defects"], sev)
        if block:
            any_def = True
            lines.extend(block)
    if not any_def:
        lines.append("_No defects reported._")
        lines.append("")

    lines.append("## Boundary & omission")
    lines.append("")
    lines.append(f"- **Boundary:** {result.get('boundary_verdict') or 'n/a'}")
    lines.append(f"- **Omission check:** {result.get('omission_check') or 'n/a'}")
    lines.append("")

    esc = result["escalation"]
    lines.append("## Round-escalation controller")
    lines.append("")
    lines.append(f"- **Escalate?** {'YES' if esc['escalate'] else 'no'}")
    if esc["reason"]:
        lines.append(f"- **Reason:** {esc['reason']}")
    if esc["recommended_action"]:
        lines.append(f"- **Action:** {esc['recommended_action']}")
    lines.append("")

    if result.get("usage"):
        u = result["usage"]
        lines.append(
            f"{DIM}_usage: in={u.get('input_tokens')} out={u.get('output_tokens')} "
            f"cache_read={u.get('cache_read_input_tokens')} "
            f"cache_write={u.get('cache_creation_input_tokens')}_{RESET}"
        )
        lines.append("")

    return "\n".join(lines)


def write_outputs(result: dict, *, out_dir: str, current_round: int) -> tuple[Path, Path]:
    """Write REVIEW md + machine defects JSON. Returns (md_path, json_path)."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = f"{result['book']}{result['chapter']}-{result['witness']}-R{current_round}"
    md_path = out / f"REVIEW_{date.today().isoformat()}-{stem}.md"
    json_path = out / f"defects_{result['book']}{result['chapter']}_{result['witness']}_R{current_round}.json"
    md_path.write_text(render_review_md(result), encoding="utf-8")
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return md_path, json_path


def _estimate_cost(n_images: int, model: str) -> float:
    """Coarse per-chapter projection. Opus-grade vision review of two
    ~1568 px folios + cached topology prefix lands in the $0.05-0.30 band;
    cheaper models scale down. Indicative only."""
    base = 0.05 if "opus" in model else 0.015
    return round(base + n_images * 0.03, 3)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--witness-path", required=True, help="Path to the witness JSON")
    p.add_argument("--round", type=int, default=1, help="Round number that just closed (default 1)")
    p.add_argument("--model", default=None, help="Vision model id (default: manuscript_vision.DEFAULT_VISION_MODEL)")
    p.add_argument("--out", default=None, help="Output dir (default: dev/marathon_reviews/<book><ch>)")
    p.add_argument("--max-edge", type=int, default=None, help="Max image edge px (default: 1568)")
    p.add_argument("--dry-run", action="store_true", help="Print plan + cost; no API call")
    args = p.parse_args(argv)

    witness_path = Path(args.witness_path)
    if not witness_path.is_absolute():
        witness_path = REPO_ROOT / witness_path
    if not witness_path.exists():
        print(f"{RED}REFUSING:{RESET} witness not found: {witness_path}", file=sys.stderr)
        return 1
    witness = json.loads(witness_path.read_text(encoding="utf-8"))

    # Lazy import so --dry-run works without Pillow installed.
    from scripts.core import manuscript_vision as mv

    model = args.model or mv.DEFAULT_VISION_MODEL
    max_edge = args.max_edge or mv.MAX_IMAGE_EDGE
    src_images = witness.get("source_images", [])
    out_dir = args.out or str(REPO_ROOT / "dev" / "marathon_reviews" / f"{witness.get('book')}{witness.get('chapter')}")

    print(
        f"Review: {witness.get('book')}{witness.get('chapter')} "
        f"{witness.get('witness')} · round {args.round} · model={model}"
    )
    print(f"  folios: {len(src_images)} · max-edge={max_edge}px · out={out_dir}")
    print(f"  projected cost: ~${_estimate_cost(len(src_images), model):.3f} USD")
    print()

    if args.dry_run:
        print(f"{DIM}--dry-run: no API call made; nothing written.{RESET}")
        return 0

    # Build compact image blocks — whole folio, downscaled, never upscaled.
    image_blocks = []
    for rel in src_images:
        img_path = Path(rel)
        if not img_path.is_absolute():
            img_path = REPO_ROOT / img_path
        if not img_path.exists():
            print(f"{RED}REFUSING:{RESET} source image missing: {img_path}", file=sys.stderr)
            return 1
        # box (0,0,huge,huge) clamps to the full folio inside crop_and_encode.
        image_blocks.append(mv.crop_and_encode(str(img_path), (0, 0, 10**9, 10**9), max_edge=max_edge))

    try:
        client = mv.AnthropicVisionClient(model=model)
    except mv.sources.SourceMissingError as e:
        print(f"{RED}REFUSING:{RESET} {e}", file=sys.stderr)
        return 1

    topology_text = load_topology(witness.get("witness"))
    result = run_review(
        witness,
        vision_client=client,
        topology_text=topology_text,
        image_blocks=image_blocks,
        current_round=args.round,
    )
    md_path, json_path = write_outputs(result, out_dir=out_dir, current_round=args.round)

    color = RED if result["overall_verdict"] == "NEEDS_FIX" else GREEN
    print(
        f"{color}{result['overall_verdict'] or 'n/a'}{RESET} · "
        f"{result['hard_defects']} hard defect(s) · "
        f"{len(result['defects'])} total · "
        f"escalate={result['escalation']['escalate']}"
    )
    print(f"  REVIEW : {md_path}")
    print(f"  defects: {json_path}")
    if result.get("usage"):
        print(f"  {DIM}usage: {result['usage']}{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
