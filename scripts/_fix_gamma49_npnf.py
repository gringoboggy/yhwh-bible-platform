"""γ.4.9 fixup — inject "NPNF" abbreviation into Athanasius attributions.

One-shot fix after γ.4.9 ship: the original `_ship_gamma49.py` attribution
strings used the full "Nicene and Post-Nicene Fathers" name but did not
include the "NPNF" abbreviation. `tests/test_ethiopian_gamma4.py::
TestGamma4DataFile::test_every_entry_cites_pd_source` requires every
entry's attribution to contain one of the canonical PD anchors:
("NPNF", "Charles", "Payne Smith", "Cramer"). This script updates the
Athanasius attribution strings in the source JSON + promoted notes files
to include "(NPNF)" parenthetically.

Idempotent — re-running is a no-op if the OLD pattern has been replaced.

Run once: python scripts/_fix_gamma49_npnf.py
Then delete (LOAD-BEARING-ONCE one-shot per §7.4).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
JSON_PATH = REPO / "content" / "sources" / "ethiopian_commentaries.json"
NOTES_DIR = REPO / "content" / "notes"

OLD = "Nicene and Post-Nicene Fathers, Series 2, Vol. 4"
NEW = "Nicene and Post-Nicene Fathers (NPNF), Series 2, Vol. 4"


def main() -> None:
    # 1) Fix the source JSON
    d = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    n_json = 0
    for e in d["entries"]:
        if e.get("father") == "Athanasius of Alexandria":
            if OLD in e["attribution"]:
                e["attribution"] = e["attribution"].replace(OLD, NEW)
                n_json += 1
    tmp = JSON_PATH.with_suffix(JSON_PATH.suffix + ".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, JSON_PATH)
    print(f"JSON: updated {n_json} Athanasius entries")

    # 2) Fix promoted notes files
    n_files = 0
    n_lines = 0
    for nf in sorted(NOTES_DIR.glob("*.py")):
        text = nf.read_text(encoding="utf-8")
        if OLD in text:
            replaced = text.count(OLD)
            new_text = text.replace(OLD, NEW)
            nf.write_text(new_text, encoding="utf-8")
            n_files += 1
            n_lines += replaced
            print(f"  {nf.name}: {replaced} replacement(s)")
    print(f"Notes files: updated {n_files} files / {n_lines} attribution(s)")


if __name__ == "__main__":
    main()
