#!/usr/bin/env python3
"""rotate_truth_records.py — archive old SESSION_STATE / IN_FLIGHT journal entries.

The bootstrap re-reads ``dev/SESSION_STATE.md`` + ``dev/IN_FLIGHT.md`` every
session; their rolling ``> **➤➤➤ <date>`` journal entries accumulate and dominate
the per-session bootstrap token cost (the 2026-05-29 mint audit found the triad
cost ~200k tokens). This rotator keeps the file's HEADER + the newest
``KEEP_ENTRIES`` journal entries + the file's stable TRAILING sections live, and
moves the older entries into ``dev/archive/<NAME>_archive.md`` (newest batch
first), preserving full history behind a pointer. The marathon's authoritative
ledger lives in ``content/manuscript/**/manifest.yaml``, so trimming the narrative
journal is safe.

This is the registered FIXER for the ``truth_record_budget`` lint check
(``scripts/lint_rules.py`` ``FIXERS``), so ``python scripts/lint_rules.py --fix``
self-heals a budget breach. Dry-run by default; pass ``--apply`` to write.

    py scripts/rotate_truth_records.py             # preview (dry-run)
    py scripts/rotate_truth_records.py --apply      # rotate + archive
    py scripts/rotate_truth_records.py --keep 3 --apply

Writes go through ``notes_io.atomic_write`` (the project's only sanctioned write
path; raw ``open('w')`` trips the ``atomic_writes`` lint check).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.core.notes_io import atomic_write  # noqa: E402

# A journal entry begins with this marker; ``**`` distinguishes it from a
# heading that merely uses the glyph (e.g. IN_FLIGHT's "## ➤➤➤ ACTIVE" block,
# which is a stable trailing section, not a rolling entry).
ENTRY_MARKER = "> **➤➤➤"

# Default kept-entry count. Matches ``truth_record_budget``'s max_entries so that
# running the fixer brings the file UNDER budget (a fixer must produce a green
# file). A larger window is available via ``--keep N``.
KEEP_ENTRIES = 2

_DATE_RE = re.compile(r"➤➤➤\s*(\d{4}-\d{2}-\d{2})")

# rel_live → rel_archive
RECORDS = {
    "dev/SESSION_STATE.md": "dev/archive/SESSION_STATE_archive.md",
    "dev/IN_FLIGHT.md": "dev/archive/IN_FLIGHT_archive.md",
}


def _split(text: str) -> tuple[list[str], list[int], int | None]:
    """Return (lines, entry_start_indices, tail_idx).

    ``entry_start_indices`` are the line indices of each ``> **➤➤➤`` marker that
    lies in the entry region (before the stable trailing section). ``tail_idx`` is
    the line index of the first top-level ``## `` heading at/after the first entry
    (the start of the stable trailing section), or ``None`` if there is none."""
    lines = text.split("\n")
    starts = [i for i, ln in enumerate(lines) if ln.startswith(ENTRY_MARKER)]
    if not starts:
        return lines, [], None
    tail_idx = next((i for i in range(starts[0], len(lines)) if lines[i].startswith("## ")), None)
    end = tail_idx if tail_idx is not None else len(lines)
    bounded = [s for s in starts if s < end]
    return lines, bounded, tail_idx


def _date_range(text: str) -> tuple[str, str]:
    dates = _DATE_RE.findall(text)
    return (min(dates), max(dates)) if dates else ("?", "?")


def plan_rotation(text: str, *, keep: int = KEEP_ENTRIES) -> dict:
    """Compute the rotation for one file's text WITHOUT writing. Returns a dict
    with the proposed ``live`` + appended ``archive_batch`` text, entry counts,
    and whether anything would change. Pure — safe to call in tests / dry-run."""
    lines, bounded, tail_idx = _split(text)
    total = len(bounded)
    if total <= keep:
        return {
            "changed": False,
            "entries_before": total,
            "entries_after": total,
            "archived": 0,
            "live": text,
            "archive_batch": "",
            "date_range": ("?", "?"),
        }
    cut = bounded[keep]  # first line index of the (keep+1)th — first archived — entry
    end = tail_idx if tail_idx is not None else len(lines)

    # archived entries = the entry-region lines from the cut to the tail/end.
    archived_lines = lines[cut:end]
    archived_text = "\n".join(archived_lines).strip("\n")

    # live = header + kept entries + (blank) + stable tail.
    head_keep = lines[:cut]
    while head_keep and head_keep[-1].strip() == "":
        head_keep.pop()
    tail_lines = lines[end:] if tail_idx is not None else []
    while tail_lines and tail_lines[0].strip() == "":
        tail_lines.pop(0)
    live = "\n".join(head_keep)
    if tail_lines:
        live += "\n\n" + "\n".join(tail_lines)
    if not live.endswith("\n"):
        live += "\n"

    lo, hi = _date_range(archived_text)
    batch = f"<!-- archived: {total - keep} entries, {lo}..{hi} (rotate_truth_records.py) -->\n\n{archived_text}\n"
    return {
        "changed": True,
        "entries_before": total,
        "entries_after": keep,
        "archived": total - keep,
        "live": live,
        "archive_batch": batch,
        "date_range": (lo, hi),
    }


_BATCH_SENTINEL = "<!-- BATCHES (newest first) -->"


def _prepend_archive(archive_path: Path, batch: str, name: str) -> str:
    """Build the new archive text: a title/intro (written once) then batches,
    newest first. New batches are inserted directly after the sentinel."""
    intro = (
        f"# {name} — rotated journal archive\n\n"
        f"> Older `> **➤➤➤` journal entries rotated out of the live `dev/{name}.md` by\n"
        f"> `scripts/rotate_truth_records.py` to keep the always-read bootstrap lean.\n"
        f"> Newest archived batch first. Full history; not read at session start.\n\n"
        f"{_BATCH_SENTINEL}\n\n"
    )
    if archive_path.is_file():
        existing = archive_path.read_text(encoding="utf-8")
        anchor = _BATCH_SENTINEL + "\n\n"
        if anchor in existing:
            head, _, body = existing.partition(anchor)
            return head + anchor + batch + "\n" + body
        return intro + batch + "\n" + existing  # legacy archive without sentinel
    return intro + batch


def rotate_all(*, keep: int = KEEP_ENTRIES, dry_run: bool = True) -> dict:
    """Rotate every record. Returns {applied, message, changes:[...], files:[...]}.
    Each per-file result carries entry counts + byte deltas."""
    results: list[dict] = []
    changes: list[dict] = []
    any_change = False
    for rel_live, rel_arch in RECORDS.items():
        live_path = REPO / rel_live
        if not live_path.is_file():
            continue
        text = live_path.read_text(encoding="utf-8")
        plan = plan_rotation(text, keep=keep)
        before_bytes = len(text.encode("utf-8"))
        after_bytes = len(plan["live"].encode("utf-8"))
        results.append(
            {
                "file": rel_live,
                "changed": plan["changed"],
                "entries_before": plan["entries_before"],
                "entries_after": plan["entries_after"],
                "archived": plan["archived"],
                "bytes_before": before_bytes,
                "bytes_after": after_bytes,
                "date_range": plan["date_range"],
            }
        )
        if not plan["changed"]:
            continue
        any_change = True
        changes.append(
            {
                "file": rel_live,
                "archived_to": rel_arch,
                "archived_entries": plan["archived"],
                "bytes": f"{before_bytes:,} -> {after_bytes:,}",
            }
        )
        if not dry_run:
            arch_path = REPO / rel_arch
            arch_path.parent.mkdir(parents=True, exist_ok=True)
            name = Path(rel_live).stem
            atomic_write(arch_path, _prepend_archive(arch_path, plan["archive_batch"], name))
            atomic_write(live_path, plan["live"])
    if not any_change:
        msg = "truth records already within entry budget — nothing to rotate"
    else:
        verb = "rotated" if not dry_run else "would rotate"
        parts = [f"{c['file']} ({c['archived_entries']} entries, {c['bytes']}B)" for c in changes]
        msg = f"{verb}: " + "; ".join(parts) + (" [dry-run]" if dry_run else "")
    return {"applied": (any_change and not dry_run), "ok": True, "message": msg, "changes": changes, "files": results}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--apply", action="store_true", help="write the changes (default: dry-run preview)")
    p.add_argument(
        "--keep", type=int, default=KEEP_ENTRIES, help=f"journal entries to keep live (default {KEEP_ENTRIES})"
    )
    args = p.parse_args(argv)
    res = rotate_all(keep=args.keep, dry_run=not args.apply)
    print(res["message"])
    for f in res["files"]:
        flag = "→ rotate" if f["changed"] else "  ok"
        print(
            f"  {flag}  {f['file']:24} entries {f['entries_before']}→{f['entries_after']}  "
            f"{f['bytes_before']:,}→{f['bytes_after']:,}B"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
