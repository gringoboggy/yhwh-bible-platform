"""γ.4.9.B post-promote dedup fixup.

The γ.4.9.B at-scale + promote pass re-promoted the 40 γ.4.9 seed
Athanasius entries because the candidates JSON files still carried the
OLD pre-NPNF-fixup attribution while the notes files had been
NPNF-fixed (so promote.note_already_exists treated them as
legitimately-distinct attribution-divergent notes). Result: 80
promoted (40 legit γ.4.9.B + 40 duplicate γ.4.9 seed entries) instead
of the expected 40.

The duplicates are identifiable: they're Athanasius entries in the
notes files whose attribution lacks the "(NPNF)" abbreviation
(every legitimate γ.4.9 + γ.4.9.B attribution has "(NPNF)" after
the post-ship fixup ran on the source JSON + ship script).

Fix: remove every Athanasius-of-Alexandria tuple from
content/notes/*.py whose attribution does NOT contain "(NPNF)".
Per-book + chapter-verse-aware removal preserves the legitimate
entries (which all carry "(NPNF)").

Also cleans up the candidates JSON files: mark Athanasius candidates
with old attribution as status="rejected" so re-runs don't repeat.

One-shot. Run once. Idempotent re-run safe (no-op after the first
pass clears the OLD-attribution duplicates).

Usage: python scripts/_fix_gamma49b_dedup.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
NOTES_DIR = REPO / "content" / "notes"
CANDIDATES_DIR = REPO / "content" / "candidates"

# Books touched by γ.4.9 + γ.4.9.B
TOUCHED_BOOKS = [
    "gen",
    "exo",
    "psa",
    "pro",
    "isa",
    "mat",
    "jhn",
    "rom",
    "1co",
    "2co",
    "gal",
    "eph",
    "phi",
    "col",
    "heb",
    "1pe",
    "2pe",
    "1jn",
    "rev",
]


def fix_notes_file(path: Path) -> int:
    """Remove Athanasius tuples whose attribution lacks '(NPNF)'.
    Returns count of tuples removed."""
    text = path.read_text(encoding="utf-8")

    # Match a tuple containing Athanasius-of-Alexandria attribution
    # WITHOUT "(NPNF)". The tuple starts with `    (` on its own line
    # and ends with `    ),` on its own line. We use a regex with
    # DOTALL to span lines.
    #
    # A tuple is removed only if:
    #   (a) it contains "Athanasius of Alexandria" — narrows scope
    #   (b) it contains "Nicene and Post-Nicene Fathers, Series 2"
    #       WITHOUT the "(NPNF)" abbreviation
    pattern = re.compile(
        r"^    \(\n"  # tuple opening
        r"(?:.*\n)*?"  # body (non-greedy)
        r"    \),\n",  # tuple close
        re.MULTILINE,
    )

    removed = 0
    new_chunks: list[str] = []
    cursor = 0
    for m in pattern.finditer(text):
        tuple_text = m.group(0)
        # Only consider Athanasius tuples
        if "Athanasius of Alexandria" not in tuple_text:
            continue
        # Only remove if attribution lacks "(NPNF)" — duplicates
        if "(NPNF)" in tuple_text:
            continue
        # This is a duplicate-promote artifact — remove
        new_chunks.append(text[cursor : m.start()])
        cursor = m.end()
        removed += 1

    if removed == 0:
        return 0

    new_chunks.append(text[cursor:])
    new_text = "".join(new_chunks)
    path.write_text(new_text, encoding="utf-8")
    return removed


def fix_candidates_file(path: Path) -> int:
    """Mark Athanasius candidates with OLD attribution as rejected.
    Returns count of candidates updated."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return 0

    if "candidates" not in data:
        return 0

    updated = 0
    for c in data["candidates"]:
        attr = c.get("source_attribution", "") or ""
        if "Athanasius" not in attr:
            continue
        if "(NPNF)" in attr:
            continue
        # OLD-attribution Athanasius candidate — mark rejected
        if c.get("status") != "rejected":
            c["status"] = "rejected"
            updated += 1

    if updated == 0:
        return 0

    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return updated


def main() -> None:
    notes_removed = 0
    notes_files_touched = 0
    for book in TOUCHED_BOOKS:
        path = NOTES_DIR / f"{book}.py"
        if not path.is_file():
            continue
        n = fix_notes_file(path)
        if n > 0:
            notes_files_touched += 1
            notes_removed += n
            print(f"  notes/{book}.py: removed {n} duplicate(s)")
    print(f"NOTES: removed {notes_removed} duplicate Athanasius tuples across {notes_files_touched} files")
    print()

    cands_updated = 0
    cands_files_touched = 0
    for path in sorted(CANDIDATES_DIR.glob("*.json")):
        n = fix_candidates_file(path)
        if n > 0:
            cands_files_touched += 1
            cands_updated += n
    print(
        f"CANDIDATES: marked {cands_updated} OLD-attribution Athanasius candidate(s) as rejected across {cands_files_touched} files"
    )


if __name__ == "__main__":
    main()
