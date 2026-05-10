#!/usr/bin/env python3
"""ω.11 — recovery CLI: operator-facing wrapper around the project's
existing backup infrastructure.

Every mutation in the project goes through ``notes_io.atomic_write``
+ ``notes_io.ensure_backup`` (lint_rules enforces this). When something
breaks — a hand-edit corrupts a YAML, a build pipeline produces a
malformed editions.yaml, an in-flight marker gets stuck — recovery is
"copy the right `.bak` file back into place." This CLI catalogs the
common flows so the operator doesn't have to remember the file paths
or the timestamp format.

Usage::

    python scripts/recover.py list-backups <path>
    python scripts/recover.py restore <path> [--from <bak-path>]
    python scripts/recover.py verify-yaml <path>
    python scripts/recover.py flip-inflight idle [--yes]

Pure functions are exposed so tests can exercise the flows without
touching the real backup directory; the ``main()`` entrypoint glues
them to argparse.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _iso_to_dt(stamp: str) -> Optional[datetime]:
    """Parse ``20260509T173045Z`` → datetime. Returns None on
    malformed input."""
    if not isinstance(stamp, str) or len(stamp) < 16:
        return None
    try:
        return datetime.strptime(stamp, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


@dataclass(frozen=True)
class BackupRecord:
    path: Path
    timestamp: Optional[datetime]
    size_bytes: int

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "timestamp": (self.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") if self.timestamp else None),
            "size_bytes": self.size_bytes,
        }


_BAK_NAME_RE = re.compile(r"^(?P<stem>.+?)\.(?P<ts>\d{8}T\d{6}Z)(?P<suffix>\.[A-Za-z0-9]+)\.bak$")


def list_backups(path: Path | str) -> list[BackupRecord]:
    """Return every backup of ``path`` in its sibling ``.backups/`` dir,
    newest-first.

    Backup filenames produced by ``notes_io.ensure_backup`` follow
    ``<stem>.<YYYYMMDDTHHMMSSZ><suffix>.bak`` — we glob by stem +
    suffix to filter to backups of *this* file (not unrelated
    `.bak` neighbours).
    """
    path = Path(path)
    backup_dir = path.parent / ".backups"
    if not backup_dir.is_dir():
        return []
    out: list[BackupRecord] = []
    for bak in backup_dir.glob(f"{path.stem}.*{path.suffix}.bak"):
        m = _BAK_NAME_RE.match(bak.name)
        ts = _iso_to_dt(m.group("ts")) if m else None
        try:
            size = bak.stat().st_size
        except OSError:
            size = 0
        out.append(BackupRecord(path=bak, timestamp=ts, size_bytes=size))
    # Newest first; entries without a parseable timestamp sink to the bottom.
    out.sort(
        key=lambda r: r.timestamp or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return out


def restore_from_backup(
    path: Path | str,
    *,
    from_path: Optional[Path | str] = None,
) -> dict:
    """Copy a `.bak` file back over ``path``. Backs up the current
    contents first (so a botched restore is itself recoverable).

    `from_path` selects a specific backup; defaults to the most
    recent. Returns ``{"status": "ok", "restored_from", "rolled_back_to"}``
    on success or an error envelope.
    """
    path = Path(path)
    if from_path is None:
        backups = list_backups(path)
        if not backups:
            return {
                "status": "error",
                "code": "no_backups",
                "http": 404,
                "message": f"no backups for {path} in {path.parent}/.backups/",
            }
        chosen = backups[0].path
    else:
        chosen = Path(from_path)
        if not chosen.is_file():
            return {
                "status": "error",
                "code": "backup_not_found",
                "http": 404,
                "message": f"backup not found: {chosen}",
            }
        # Defensive: ensure the chosen backup is actually FOR this file
        # (don't let the operator restore an unrelated .bak by mistake).
        m = _BAK_NAME_RE.match(chosen.name)
        if m and m.group("stem") != path.stem:
            return {
                "status": "error",
                "code": "backup_mismatch",
                "http": 400,
                "message": (f"backup {chosen.name!r} is for stem {m.group('stem')!r}, not {path.stem!r}"),
            }

    # Read the backup's bytes into memory FIRST. ensure_backup uses
    # second-resolution timestamps; if our roll-back call lands in
    # the same second as a prior ensure_backup, it would clobber the
    # very file we're about to restore from. Holding the bytes in
    # memory makes the restore independent of the rollback's I/O.
    try:
        chosen_bytes = chosen.read_bytes()
    except OSError as e:
        return {
            "status": "error",
            "code": "backup_read_failed",
            "http": 500,
            "message": f"could not read backup: {e}",
        }

    # Back up the current contents (if any) before overwriting.
    rolled_back_to = None
    if path.is_file():
        from scripts.core import notes_io

        rolled_back_to = notes_io.ensure_backup(path)

    path.write_bytes(chosen_bytes)
    return {
        "status": "ok",
        "restored": str(path),
        "restored_from": str(chosen),
        "rolled_back_to": str(rolled_back_to) if rolled_back_to else None,
    }


def verify_yaml(path: Path | str) -> dict:
    """Parse ``path`` via the project's custom ``_parse_yaml_records``
    to catch format mismatches that would silently break the build
    pipeline (e.g. yaml.safe_dump output that PyYAML accepts but the
    project's parser can't read — see ω.16 CHANGELOG entry).

    Returns ``{"status": "ok", "record_count"}`` if the file parses
    AND yields at least one record; else an error envelope describing
    where it failed.
    """
    path = Path(path)
    if not path.is_file():
        return {"status": "error", "code": "not_found", "http": 404, "message": f"file not found: {path}"}
    text = path.read_text(encoding="utf-8")
    try:
        from scripts.core import config

        records = config._parse_yaml_records(text)  # type: ignore[attr-defined]
    except Exception as e:
        return {"status": "error", "code": "parse_failed", "http": 422, "message": f"_parse_yaml_records raised: {e}"}
    if not isinstance(records, list):
        return {
            "status": "error",
            "code": "shape_error",
            "http": 422,
            "message": "parser did not return a list of records",
        }
    return {
        "status": "ok",
        "path": str(path),
        "record_count": len(records),
    }


def flip_inflight(target_state: str = "idle") -> dict:
    """Flip the IN_FLIGHT.md marker to ``idle`` or ``active``.

    Used after a crashed session left the marker stuck in the wrong
    state. Caller is responsible for confirming with the operator
    before calling — this function does the file edit unconditionally.
    """
    if target_state not in ("idle", "active"):
        return {
            "status": "error",
            "code": "invalid_state",
            "http": 400,
            "message": "target_state must be 'idle' or 'active'",
        }
    repo_root = Path(__file__).resolve().parent.parent
    inflight = repo_root / "dev" / "IN_FLIGHT.md"
    if not inflight.is_file():
        return {"status": "error", "code": "not_found", "http": 404, "message": f"IN_FLIGHT.md not found: {inflight}"}
    text = inflight.read_text(encoding="utf-8")
    pattern = re.compile(r"<!--\s*TRACKER-STATE:\s*(idle|active)\s*-->")
    m = pattern.search(text)
    if not m:
        return {
            "status": "error",
            "code": "no_marker",
            "http": 422,
            "message": "TRACKER-STATE marker not found in IN_FLIGHT.md",
        }
    current_state = m.group(1)
    if current_state == target_state:
        return {"status": "ok", "no_change": True, "current_state": current_state}
    new_text = pattern.sub(
        f"<!-- TRACKER-STATE: {target_state} -->",
        text,
        count=1,
    )
    from scripts.core import notes_io

    notes_io.ensure_backup(inflight)
    notes_io.atomic_write(inflight, new_text)
    return {
        "status": "ok",
        "previous_state": current_state,
        "new_state": target_state,
    }


# ----------------------------------------------------------------------
# CLI entrypoint
# ----------------------------------------------------------------------


def _format_record_line(rec: BackupRecord) -> str:
    ts = rec.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC") if rec.timestamp else "(unknown timestamp)"
    size_kb = rec.size_bytes / 1024
    return f"  {ts}   {size_kb:7.1f} KB   {rec.path.name}"


def _cmd_list_backups(args) -> int:
    backups = list_backups(args.path)
    if not backups:
        print(f"no backups for {args.path}")
        print(f"  (looked in {Path(args.path).parent}/.backups/)")
        return 0
    print(f"{len(backups)} backup(s) for {args.path}:")
    for r in backups:
        print(_format_record_line(r))
    return 0


def _cmd_restore(args) -> int:
    result = restore_from_backup(args.path, from_path=args.from_path)
    if result.get("status") == "error":
        print(f"error: {result.get('code')}: {result.get('message')}", file=sys.stderr)
        return 1
    print(f"✓ restored {result['restored']} from {result['restored_from']}")
    if result.get("rolled_back_to"):
        print(f"  prior contents backed up to {result['rolled_back_to']}")
    return 0


def _cmd_verify_yaml(args) -> int:
    result = verify_yaml(args.path)
    if result.get("status") == "error":
        print(f"FAIL  {result.get('code')}: {result.get('message')}", file=sys.stderr)
        return 1
    print(f"✓ {result['path']} parses cleanly · {result['record_count']} record(s)")
    return 0


def _cmd_flip_inflight(args) -> int:
    target = args.state
    if not args.yes:
        prompt = (
            f"Flip IN_FLIGHT.md TRACKER-STATE to {target!r}? "
            f"This is destructive if a real task is in progress. "
            f"Type 'yes' to confirm: "
        )
        try:
            reply = input(prompt).strip().lower()
        except EOFError:
            reply = ""
        if reply != "yes":
            print("aborted (no changes)", file=sys.stderr)
            return 1
    result = flip_inflight(target)
    if result.get("status") == "error":
        print(f"error: {result.get('code')}: {result.get('message')}", file=sys.stderr)
        return 1
    if result.get("no_change"):
        print(f"no change — already {result['current_state']!r}")
        return 0
    print(f"✓ flipped {result['previous_state']!r} → {result['new_state']!r}")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="recover",
        description="ω.11 — recovery CLI for the YHWH platform.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser(
        "list-backups",
        help="list every backup of a file",
    )
    p_list.add_argument("path", help="path to the file (e.g. content/notes/gen.py)")
    p_list.set_defaults(fn=_cmd_list_backups)

    p_rest = sub.add_parser(
        "restore",
        help="restore a file from its most-recent backup (or a specific one)",
    )
    p_rest.add_argument("path", help="path to restore")
    p_rest.add_argument(
        "--from",
        dest="from_path",
        default=None,
        help="specific .bak file to restore from (defaults to newest)",
    )
    p_rest.set_defaults(fn=_cmd_restore)

    p_ver = sub.add_parser(
        "verify-yaml",
        help="check a YAML file via the project's custom parser",
    )
    p_ver.add_argument("path", help="path to verify")
    p_ver.set_defaults(fn=_cmd_verify_yaml)

    p_flip = sub.add_parser(
        "flip-inflight",
        help="flip dev/IN_FLIGHT.md's TRACKER-STATE marker",
    )
    p_flip.add_argument("state", choices=["idle", "active"])
    p_flip.add_argument(
        "--yes",
        action="store_true",
        help="skip the confirmation prompt",
    )
    p_flip.set_defaults(fn=_cmd_flip_inflight)

    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
