"""One-shot: repair OCR end-of-line hyphenation frozen into note bodies
(RX-beta2 ⑥; user: "make sure words are not ram-om-ly spelled like th-is").

The OCR sources (Easton's dictionary, some manuscript notes) broke words at line
ends as ``word- word``. A CURATED map (no blind regex — a wrong join changes a
word) repairs each observed case, distinguishing:
  * BROKEN words      → drop the hyphen + space  ("con- tains" → "contains")
  * REAL compounds    → drop only the space, keep the hyphen ("Maher- shalal" →
    proper names / number words "Maher-shalal", "forty-two")
Applies to BOTH the source `content/notes/*.py` and the baked `epub_working/*.html`
note asides (lockstep, so the base stays consistent). Idempotent.

    py -3 -m scripts._dehyphenate_notes --dry-run
    py -3 -m scripts._dehyphenate_notes --apply
"""

from __future__ import annotations

import argparse
import glob
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Curated: observed "word- word" → repaired form. Reviewed individually 2026-06-06.
REPAIRS = {
    # broken single words (drop hyphen + space)
    "addi- tional": "additional",
    "apo- cryphal": "apocryphal",
    "con- cerning": "concerning",
    "con- sisting": "consisting",
    "con- tains": "contains",
    "damna- tion": "damnation",
    "in- stitution": "institution",
    "indigna- tion": "indignation",
    "lamen- tations": "lamentations",
    "mutila- tion": "mutilation",
    "pre- cise": "precise",
    "recom- pence": "recompence",
    "repre- sentation": "representation",
    "substi- tution": "substitution",
    "sup- plied": "supplied",
    "un- questionably": "unquestionably",
    "Ecclesiasti- cus": "Ecclesiasticus",
    "Magni- ficat": "Magnificat",
    "Lauren- tian": "Laurentian",
    # real hyphenated compounds — names + numbers (drop the SPACE, keep the hyphen)
    "Maher- shalal": "Maher-shalal",
    "Ramoth- gilead": "Ramoth-gilead",
    "Ben- hadad": "Ben-hadad",
    "Merodach- baladan": "Merodach-baladan",
    "Tiglath- pileser": "Tiglath-pileser",
    "natsir- pal": "natsir-pal",
    "forty- two": "forty-two",
    "thirty- five": "thirty-five",
}
# Deliberately NOT repaired (ambiguous): "os- of"/"Gos- of", "measure- ing".


def run(dry: bool) -> dict:
    targets = sorted(glob.glob(str(REPO / "content" / "notes" / "*.py"))) + sorted(
        glob.glob(str(REPO / "epub_working" / "index_split_*.html"))
    )
    tally: dict[str, int] = {}
    files_changed = 0
    for path in targets:
        if "/.backups/" in path.replace("\\", "/"):
            continue
        text = Path(path).read_text(encoding="utf-8")
        new = text
        for bad, good in REPAIRS.items():
            if bad in new:
                n = new.count(bad)
                new = new.replace(bad, good)
                tally[bad] = tally.get(bad, 0) + n
        if new != text:
            files_changed += 1
            if not dry:
                Path(path).write_text(new, encoding="utf-8")
    return {"files_changed": files_changed, "tally": tally, "total": sum(tally.values())}


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)
    dry = not args.apply
    r = run(dry)
    print(f"{'DRY-RUN' if dry else 'APPLIED'}: {r['total']} repair(s) across {r['files_changed']} file(s)")
    for bad, n in sorted(r["tally"].items(), key=lambda kv: -kv[1]):
        print(f"  {n:>3}  {bad!r} -> {REPAIRS[bad]!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
