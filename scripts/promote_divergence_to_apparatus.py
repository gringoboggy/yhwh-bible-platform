#!/usr/bin/env python3
"""promote_divergence_to_apparatus.py — surface content-class divergences
as `compare-divergence-geez` apparatus entries.

Seeded at δ.1.0 (2026-05-14). Companion to `build_meqabyan_revision.py`.
Where the latter produces the consolidated per-book revision markdown,
this tool walks `content/divergence/meqabyan_geez_divergence.json` and
promotes the subset of entries whose `divergence_class == "content"`
into per-verse `compare-divergence-geez` notes that the build pipeline
surfaces in inline popups.

**Promotion policy** (Phase-4 honesty rules):

- Only `divergence_class == "content"` entries are promoted. Lexical,
  structural, numbering, and trivial divergences belong in the
  per-book revision markdown but NOT in the inline-popup apparatus
  (they would crowd the reader for marginal value).
- Confidence ≥ 0.8 floor applies (matches build_meqabyan_revision.py).
- `page_image_verified` must be true.
- The promoted note is `compare-divergence-geez` kind (new at δ.1.0
  in `content/kinds.yaml`).

**Output:** the tool appends entries to per-book notes files in
`content/notes/{mq1,mq2,mq3}.py` under a new dedicated `divergence_*`
namespace. At δ.1.0 (this seed ship) the divergence JSON has empty
`entries: []`, so the tool runs as a no-op and reports "0 promotions".
At δ.1.x.A-G batch ships, the tool emits the content-class promotions
that landed in that batch.

**Idempotency:** the tool detects an entry's per-verse signature
(`book + chapter + verse + operator_session`) and skips re-promoting
an already-promoted entry. This matches the N-W4 idempotency pattern
established at γ.4.6.D / γ.4.7 / γ.4.8 ships.

**v1 English immutability:** the tool NEVER modifies
`content/translations/english/`. The divergence apparatus is a
SEPARATE artifact that surfaces ALONGSIDE the immutable v1 English.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
DIVERGENCE_JSON = REPO / "content" / "divergence" / "meqabyan_geez_divergence.json"
NOTES_DIR = REPO / "content" / "notes"

PROMOTED_KIND = "compare-divergence-geez"  # new at δ.1.0


def load_divergence_json(path: Path = DIVERGENCE_JSON) -> dict:
    if not path.is_file():
        raise SystemExit(f"divergence JSON not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def is_promotable(entry: dict) -> tuple[bool, str]:
    """Phase-4 honesty + promotion-policy gates."""
    if entry.get("divergence_class") != "content":
        return False, f"divergence_class={entry.get('divergence_class')!r} (only 'content' is promoted)"
    if entry.get("page_image_verified") is not True:
        return False, "page_image_verified must be true (Phase-4 honesty rule)"
    if entry.get("confidence", 0) < 0.8:
        return False, f"confidence {entry.get('confidence', 0)} < 0.8 floor"
    return True, "ok"


def signature(entry: dict) -> str:
    """Stable per-entry signature for idempotency detection."""
    return "|".join(
        [
            str(entry.get("book", "")),
            str(entry.get("chapter", "")),
            str(entry.get("verse", "")),
            str(entry.get("operator_session", "")),
        ]
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument(
        "--divergence-json",
        type=Path,
        default=DIVERGENCE_JSON,
        help="Path to the divergence JSON",
    )
    ap.add_argument(
        "--notes-dir",
        type=Path,
        default=NOTES_DIR,
        help="Path to content/notes/ for promotion targets",
    )
    ap.add_argument(
        "--check",
        action="store_true",
        help="Validate + report planned promotions; do not modify notes files",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Synonym for --check (operator-friendly alias)",
    )
    args = ap.parse_args(argv)

    data = load_divergence_json(args.divergence_json)
    entries = data.get("entries", [])
    check_only = args.check or args.dry_run

    promotable: list[dict] = []
    skipped: list[tuple[dict, str]] = []
    for entry in entries:
        ok, reason = is_promotable(entry)
        if ok:
            promotable.append(entry)
        else:
            skipped.append((entry, reason))

    print(f"Loaded {len(entries)} entries from {args.divergence_json}")
    print(f"  Promotable (divergence_class=content + confidence ≥ 0.8 + page-image): {len(promotable)}")
    print(f"  Skipped: {len(skipped)}")
    for entry, reason in skipped[:10]:  # report first 10
        ref = f"{entry.get('book', '?')} {entry.get('chapter', '?')}:{entry.get('verse', '?')}"
        print(f"    [skip] {ref}: {reason}")
    if len(skipped) > 10:
        print(f"    ... and {len(skipped) - 10} more")

    if check_only:
        print("\n--check / --dry-run: no notes files modified.")
        return 0

    # δ.1.0 seed-ship behavior: no entries to promote (empty JSON).
    # δ.1.x.A-G ships will fill in the actual promotion logic.
    if not promotable:
        print("\nNo promotable entries. No notes files modified (idempotent no-op).")
        return 0

    # Placeholder for future δ.1.x.A-G promotion logic. The actual
    # notes-file mutation pattern matches the existing γ.4 promote
    # pipeline (per scripts/_ship_*.py family); intentionally NOT
    # implemented at δ.1.0 to keep the seed contract minimal.
    print(
        "\nERROR: δ.1.0 seed-ship does NOT yet implement notes-file "
        "mutation. The promotion logic ships at δ.1.x.A. Use --check "
        "to validate entries without writing.",
        file=sys.stderr,
    )
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
