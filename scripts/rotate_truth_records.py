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

# A journal entry begins with one of these markers; ``**`` distinguishes them
# from a heading that merely uses the glyph (e.g. IN_FLIGHT's "## ➤➤➤ ACTIVE"
# block, a stable trailing section, not a rolling entry). SESSION_STATE uses
# ``➤➤➤``; IN_FLIGHT uses ``▶`` (with status glyphs before the date) plus a few
# legacy ``➤➤➤`` stragglers — both rotate. A bold continuation line inside an
# entry ("> **WIN-LANE steps:** …") starts with neither marker, so it rides
# with its entry.
ENTRY_MARKERS = ("> **➤➤➤", "> **▶")

# Default kept-entry count. Matches ``truth_record_budget``'s max_entries so that
# running the fixer brings the file UNDER budget (a fixer must produce a green
# file). A larger window is available via ``--keep N``.
KEEP_ENTRIES = 2

_DATE_ANY_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")

# rel_live → {archive, kind}. "journal" = blockquote ENTRY_MARKERS entries with a
# stable ``## `` tail (SESSION_STATE / IN_FLIGHT); "board" = YAML frontmatter +
# ``## `` turn sections, newest first, with explicit do-NOT-rotate sections
# (LANE_HANDOFF — mint 3.3). The board archive reuses the pre-existing
# dev/archive/LANE_HANDOFF_LOG.md (one archive home; sentinel-migrated).
RECORDS = {
    "dev/SESSION_STATE.md": {"archive": "dev/archive/SESSION_STATE_archive.md", "kind": "journal"},
    "dev/IN_FLIGHT.md": {"archive": "dev/archive/IN_FLIGHT_archive.md", "kind": "journal"},
    "dev/LANE_HANDOFF.md": {"archive": "dev/archive/LANE_HANDOFF_LOG.md", "kind": "board"},
}

# A board section whose HEADING carries this phrase is standing — never rotated.
_BOARD_PROTECT_RE = re.compile(r"do not rotate", re.IGNORECASE)

# Maintained as the live board's last line so readers know where history went.
_BOARD_POINTER = (
    "> **Older turns archived to `dev/archive/LANE_HANDOFF_LOG.md`** "
    "(rotated by `scripts/rotate_truth_records.py`; newest batch first)."
)


def _clean_section(lines: list[str]) -> list[str]:
    """A board section/preamble minus any prior pointer line, blank edges trimmed."""
    out = [ln for ln in lines if ln != _BOARD_POINTER]
    while out and out[-1].strip() == "":
        out.pop()
    while out and out[0].strip() == "":
        out.pop(0)
    return out


def _split(text: str) -> tuple[list[str], list[int], int | None]:
    """Return (lines, entry_start_indices, tail_idx).

    ``entry_start_indices`` are the line indices of each ``ENTRY_MARKERS`` line
    that lies in the entry region (before the stable trailing section).
    ``tail_idx`` is the line index of the first top-level ``## `` heading
    at/after the first entry (the start of the stable trailing section), or
    ``None`` if there is none."""
    lines = text.split("\n")
    starts = [i for i, ln in enumerate(lines) if ln.startswith(ENTRY_MARKERS)]
    if not starts:
        return lines, [], None
    tail_idx = next((i for i in range(starts[0], len(lines)) if lines[i].startswith("## ")), None)
    end = tail_idx if tail_idx is not None else len(lines)
    bounded = [s for s in starts if s < end]
    return lines, bounded, tail_idx


def _date_range_of_lines(lines: list[str]) -> tuple[str, str]:
    """Min/max ``YYYY-MM-DD`` over the given ENTRY-START / heading lines only
    (never over entry prose — bodies routinely reference other dates)."""
    dates = [m.group(1) for ln in lines for m in [_DATE_ANY_RE.search(ln)] if m]
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

    lo, hi = _date_range_of_lines([lines[s] for s in bounded[keep:]])
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


def plan_board_rotation(text: str, *, keep: int = KEEP_ENTRIES) -> dict:
    """Compute the LANE_HANDOFF board rotation WITHOUT writing (mint 3.3).

    The board = YAML frontmatter + ``## `` turn sections (newest first by
    convention). Live keeps: the frontmatter verbatim, any pre-section preamble,
    the newest ``keep`` rotatable sections, EVERY protected section (heading
    contains "do NOT rotate") in original order, and the archive pointer line
    (exactly once). Older rotatable sections move to the archive batch. Pure —
    same return shape as ``plan_rotation``."""
    noop = {
        "changed": False,
        "entries_before": 0,
        "entries_after": 0,
        "archived": 0,
        "live": text,
        "archive_batch": "",
        "date_range": ("?", "?"),
    }
    front = ""
    body = text
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            front = text[: end + len("\n---\n")]
            body = text[end + len("\n---\n") :]
    lines = body.split("\n")
    starts = [i for i, ln in enumerate(lines) if ln.startswith("## ")]
    if not starts:
        return noop
    preamble = lines[: starts[0]]
    sections: list[tuple[list[str], bool]] = []  # (section lines, protected)
    for j, s in enumerate(starts):
        e = starts[j + 1] if j + 1 < len(starts) else len(lines)
        sections.append((lines[s:e], bool(_BOARD_PROTECT_RE.search(lines[s]))))
    rotatable = sum(1 for _, prot in sections if not prot)
    noop["entries_before"] = noop["entries_after"] = rotatable
    if rotatable <= keep:
        return noop

    kept_secs: list[list[str]] = []
    archived_secs: list[list[str]] = []
    n_kept = 0
    for sec, prot in sections:
        if prot or n_kept < keep:
            kept_secs.append(sec)
            n_kept += 0 if prot else 1
        else:
            archived_secs.append(sec)

    # Reassemble: frontmatter + preamble + kept sections + ONE pointer line.
    # The pointer is re-emitted each rotation (_clean_section drops prior copies).
    parts = ["\n".join(b) for b in ([_clean_section(preamble)] + [_clean_section(s) for s in kept_secs]) if b]
    parts.append(_BOARD_POINTER)
    live = (front + "\n" if front else "") + "\n\n".join(parts) + "\n"

    archived_text = "\n\n".join("\n".join(_clean_section(sec)) for sec in archived_secs)
    lo, hi = _date_range_of_lines([sec[0] for sec in archived_secs])
    batch = (
        f"<!-- archived: {len(archived_secs)} sections, {lo}..{hi} (rotate_truth_records.py) -->\n\n{archived_text}\n"
    )
    return {
        "changed": True,
        "entries_before": rotatable,
        "entries_after": keep,
        "archived": rotatable - keep,
        "live": live,
        "archive_batch": batch,
        "date_range": (lo, hi),
    }


def count_entries(rel: str, text: str) -> int | None:
    """Rotatable-entry count for a truth record, or ``None`` if ``rel`` is not a
    rotated record. THE single resolver shared by the rotator and the lint's
    ``truth_record_budget`` entry check — keep them from drifting apart."""
    spec = RECORDS.get(rel.replace("\\", "/"))
    if spec is None:
        return None
    if spec["kind"] == "journal":
        _, bounded, _ = _split(text)
        return len(bounded)
    plan = plan_board_rotation(text, keep=10**9)  # count-only: nothing rotates
    return plan["entries_before"]


_BATCH_SENTINEL = "<!-- BATCHES (newest first) -->"


def _prepend_archive(archive_path: Path, batch: str, name: str, *, kind: str = "journal") -> str:
    """Build the new archive text: a title/intro (written once) then batches,
    newest first. New batches are inserted directly after the sentinel."""
    what = "journal entries" if kind == "journal" else "turn sections"
    intro = (
        f"# {name} — rotated archive\n\n"
        f"> Older {what} rotated out of the live `dev/{name}.md` by\n"
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
    for rel_live, spec in RECORDS.items():
        rel_arch = spec["archive"]
        live_path = REPO / rel_live
        if not live_path.is_file():
            continue
        text = live_path.read_text(encoding="utf-8")
        planner = plan_rotation if spec["kind"] == "journal" else plan_board_rotation
        plan = planner(text, keep=keep)
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
            atomic_write(arch_path, _prepend_archive(arch_path, plan["archive_batch"], name, kind=spec["kind"]))
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
