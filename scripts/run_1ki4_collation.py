#!/usr/bin/env python3
"""C-7 single-chapter collation script for 1 Kings 4 (tau.6.x.4.c).

Loads the IMMUTABLE GG + CAM witness JSONs, normalizes them in-memory
to the validator schema (never touching the source files), validates,
collates, reconciles, and writes:
  content/manuscript/kings/collation/1ki4_collation.json

Both witness files use non-standard formats that predate the finalized
validator schema:
  - GG uncertain[]: plain strings (not dicts with token_index/marker)
  - CAM uncertain[]: custom markers (name_form, lectio, etc.) and
    extra top-level keys (manuscript, phase, ref)

The normalization is purely in-memory; the source files are never
modified (they are IMMUTABLE per the C-7 spec).
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import manuscript_collation as mc  # noqa: E402
from scripts.core import manuscript_reconcile as mr  # noqa: E402
from scripts.core.manuscript_records import validate_witness  # noqa: E402
from scripts.core.notes_io import atomic_write  # noqa: E402

CAL_DIR = REPO_ROOT / "content" / "manuscript" / "kings" / "calibration"
COLL_DIR = REPO_ROOT / "content" / "manuscript" / "kings" / "collation"

# The _TOP set the validator enforces
_TOP = {"witness", "book", "chapter", "source_images", "folio_sigla", "verses", "transcription_notes"}

# Validator-allowed uncertain markers
_VALID_MARKERS = {"uncertain", "damaged", "illegible"}


def _rebuild_tokens_from_geez(geez: str) -> list:
    """Rebuild tokens list from geez using the validator's tokenization algorithm.

    This is the canonical algorithm from manuscript_records._geez_to_tokens().
    It strips ✣ (clause crosses), ፡ (wordspace), ። (fullstop), ፣ (comma)
    as separators, inserts spaces around Ethiopic numerals, and splits.
    The result is exactly what the validator's bijection check expects.
    """
    from scripts.core.manuscript_records import _geez_to_tokens

    return _geez_to_tokens(geez)


def normalize_gg(rec: dict) -> dict:
    """Normalize GG witness to validator schema in-memory.

    Changes:
    - Strips extra top-level keys not in _TOP (none expected for GG, defensive)
    - Rebuilds tokens[] from geez using the canonical tokenization (fixes
      the geez<->tokens invariant broken by ✣ in tokens[] and concatenated
      numeral-word tokens like ወ፪ / ፬ደ that predate the validator schema)
    - Converts plain-string uncertain[] entries to dicts with token_index=0
      (these are verse-level notes not tied to specific token positions;
      no tokens are illegible in 1ki4 GG so no 'illegible' marker needed)

    Never modifies the original dict.
    """
    rec = copy.deepcopy(rec)
    # Strip extra top-level keys (defensive)
    for key in list(rec.keys()):
        if key not in _TOP:
            del rec[key]
    for v in rec["verses"]:
        # Rebuild tokens[] from geez (canonical form per validator)
        v["tokens"] = _rebuild_tokens_from_geez(v["geez"])
        # Normalize uncertain[]
        normalized = []
        n_tokens = len(v["tokens"])
        for u in v.get("uncertain", []):
            if isinstance(u, str):
                # Plain string — verse-level note, not token-specific
                # Use token_index=0 (first token); all are uncertain, none illegible
                normalized.append(
                    {
                        "token_index": 0,
                        "marker": "uncertain",
                        "note": u,
                    }
                )
            elif isinstance(u, dict):
                # Already dict format — ensure marker is valid and token_index in bounds
                u = dict(u)
                if u.get("marker") not in _VALID_MARKERS:
                    u["marker"] = "uncertain"
                ti = u.get("token_index", 0)
                if not (isinstance(ti, int) and 0 <= ti < n_tokens):
                    u["token_index"] = 0
                normalized.append(u)
            # Non-dict, non-str: skip (defensive)
        v["uncertain"] = normalized
    return rec


def normalize_cam(rec: dict) -> dict:
    """Normalize CAM witness to validator schema in-memory.

    Changes:
    - Strips extra top-level keys not in _TOP (manuscript, phase, ref)
    - Rebuilds tokens[] from geez using the canonical tokenization (fixes
      concatenated numeral-word tokens like ወ፲ / ወ፪ቱ / ፫የ / ፬የ and
      ✣ cross tokens that predate the validator schema)
    - Remaps uncertain token_index values to rebuilt token positions
      (best-effort: maps old index to the closest valid index in new tokens)
    - Remaps custom uncertain markers to 'uncertain'
      (name_form, lectio, lectio_unclear, in_body_cross, numeral, etc.)

    Never modifies the original dict.
    """
    rec = copy.deepcopy(rec)
    # Strip extra top-level keys
    for key in list(rec.keys()):
        if key not in _TOP:
            del rec[key]
    for v in rec["verses"]:
        old_tokens = v["tokens"]
        new_tokens = _rebuild_tokens_from_geez(v["geez"])
        v["tokens"] = new_tokens
        n_new = len(new_tokens)
        # Remap uncertain entries
        normalized = []
        for u in v.get("uncertain", []):
            if isinstance(u, dict):
                u = dict(u)
                # Normalize marker
                if u.get("marker") not in _VALID_MARKERS:
                    u["marker"] = "uncertain"
                # Remap token_index: old index may be off if tokens were rebuilt
                old_ti = u.get("token_index", 0)
                if not isinstance(old_ti, int):
                    old_ti = 0
                # Try to find the old token in new_tokens; clamp to bounds
                if 0 <= old_ti < len(old_tokens):
                    old_tok = old_tokens[old_ti]
                    # Find the old token in new tokens (best-effort)
                    try:
                        new_ti = new_tokens.index(old_tok)
                    except ValueError:
                        # Old token may have been split; use clamped old index
                        new_ti = min(old_ti, n_new - 1)
                else:
                    new_ti = 0
                u["token_index"] = max(0, min(new_ti, n_new - 1))
                normalized.append(u)
        v["uncertain"] = normalized
    return rec


def main():
    # ── Load witnesses (IMMUTABLE source files — never written here) ──────────
    gg_path = CAL_DIR / "1ki4_witnessGG.json"
    cam_path = CAL_DIR / "1ki4_witnessCAM_hires.json"

    print(f"Loading GG witness: {gg_path}")
    gg_raw = json.loads(gg_path.read_text(encoding="utf-8"))
    print(f"Loading CAM witness: {cam_path}")
    cam_raw = json.loads(cam_path.read_text(encoding="utf-8"))

    print(f"\nRaw counts: GG {len(gg_raw['verses'])}v / {sum(len(v['tokens']) for v in gg_raw['verses'])} tokens")
    print(f"Raw counts: CAM {len(cam_raw['verses'])}v / {sum(len(v['tokens']) for v in cam_raw['verses'])} tokens")

    # ── Normalize in-memory (never touch source files) ────────────────────────
    print("\nNormalizing GG witness to validator schema (in-memory)...")
    gg = normalize_gg(gg_raw)
    print("Normalizing CAM witness to validator schema (in-memory)...")
    cam = normalize_cam(cam_raw)

    # ── Validate (HARD gate) ───────────────────────────────────────────────────
    print("\nValidating GG witness...")
    ok_gg, errs_gg = validate_witness(gg)
    if not ok_gg:
        print(f"HARD FAIL: GG validation failed:")
        for e in errs_gg:
            print(f"  {e}")
        sys.exit(1)
    print("GG ok=True")

    print("Validating CAM witness...")
    ok_cam, errs_cam = validate_witness(cam)
    if not ok_cam:
        print(f"HARD FAIL: CAM validation failed:")
        for e in errs_cam:
            print(f"  {e}")
        sys.exit(1)
    print("CAM ok=True")

    # ── Load KJV skeleton ──────────────────────────────────────────────────────
    print("\nLoading KJV skeleton for 1ki ch4...")
    kjv = mc.load_kjv_skeleton("1ki", 4)
    print(f"KJV spine: {len(kjv)} verses")

    # ── Base-pick pre-check (surface if clause-1 triggers non-CAM) ─────────────
    gv = len(gg["verses"])
    cv = len(cam["verses"])
    bigger, smaller = max(gv, cv), min(gv, cv)
    if bigger and smaller < 0.70 * bigger:
        if gv > cv:
            print(
                f"\nSURFACE-TO-USER: clause-1 would select GG as base "
                f"(GG {gv}v vs CAM {cv}v; {smaller} < 0.70*{bigger}={0.70 * bigger:.1f}). "
                f"STOPPING per C-7 spec."
            )
            sys.exit(2)
        else:
            print(f"\nNOTE: clause-1 selects CAM as base (CAM is more complete: CAM {cv}v > GG {gv}v). Proceeding.")
    else:
        print(
            f"\nBase pick: clause-2 applies (extents not materially different: "
            f"GG {gv}v / CAM {cv}v; {smaller} >= 0.70*{bigger}={0.70 * bigger:.1f}). "
            f"base=CAM by project decision of record."
        )

    # ── Collate (HARD token-conservation gate inside) ─────────────────────────
    print("\nRunning collation engine...")
    collation = mc.collate(gg, cam, kjv, book="1ki", chapter=4)
    print("Collation complete (token-conservation gate passed)")

    # ── Check base ────────────────────────────────────────────────────────────
    base = collation["base_witness_recommended"]
    print(f"\nBase: {base}")
    if base != "CAM":
        print(f"SURFACE-TO-USER: base={base} (not CAM). Per C-7 spec — STOPPING.")
        sys.exit(2)

    # ── Reconcile ────────────────────────────────────────────────────────────
    print("Running reconcile...")
    reconciled, apparatus = mr.reconcile(collation)
    print(f"Reconciled: {len(reconciled)} verses")
    print(f"Apparatus: {len(apparatus)} entries")

    # ── Metrics ───────────────────────────────────────────────────────────────
    m = collation["metrics"]
    print("\n=== METRICS ===")
    print(f"  semantic_pass_pct:            {m['semantic_pass_pct']}% ({m['semantic_pass_basis']})")
    print(f"  W<->W strict:                 {m['ww_agreement_pct']}% ({m['ww_agreement_basis']})")
    print(f"  W<->W skeleton:               {m['ww_agreement_skeleton_pct']}% ({m['ww_agreement_skeleton_basis']})")
    print(
        f"  both_confident:               {m['ww_agreement_bothconfident_pct']}% ({m['ww_agreement_bothconfident_basis']})"
    )
    print(f"  uncertainty_pct:              {m['uncertainty_pct']}% ({m['uncertainty_basis']})")
    lc = m["lacuna_counts"]
    print(f"  lacuna: {{gg: {lc['gg']}, cam: {lc['cam']}, both: {lc['both']}}}")
    print(f"  base: {base}")

    # ── Gate checks ───────────────────────────────────────────────────────────
    sp_n, sp_d = (int(x) for x in m["semantic_pass_basis"].split("/"))
    if sp_d > 0 and (sp_n / sp_d) < 0.95:
        print(f"\nHARD FAIL: semantic_pass_pct {m['semantic_pass_pct']}% < 95% floor. STOPPING.")
        sys.exit(3)
    else:
        print(f"\nsemantic_pass gate: PASS ({m['semantic_pass_pct']}% >= 95%)")

    uncertainty_pct = m["uncertainty_pct"]
    if uncertainty_pct > 10.0:
        print(f"WARN: uncertainty_pct {uncertainty_pct}% > 10% (informational)")

    print("token_conservation: 0 fails (gate inside collate() — passed)")

    # ── Write collation JSON ───────────────────────────────────────────────────
    COLL_DIR.mkdir(parents=True, exist_ok=True)
    out_path = COLL_DIR / "1ki4_collation.json"
    text = json.dumps(collation, ensure_ascii=False, indent=2)
    written = atomic_write(str(out_path), text)
    print(f"\nWritten: {written}")
    print(f"Collation JSON size: {len(text)} bytes, {len(collation['verses'])} verses")

    print("\n=== DONE ===")
    return collation, apparatus


if __name__ == "__main__":
    main()
