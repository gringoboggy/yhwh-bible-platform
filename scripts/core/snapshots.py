"""ω.16 — edition snapshots: frozen point-in-time records.

A snapshot captures an edition's full record from `editions.yaml`
plus a corpus fingerprint at write time, persists it to
`content/snapshots/<edition_id>/<version>/edition.yaml`, and lets
the live edition keep evolving while the snapshot stays
reproducible.

Use cases:
- **Retail audit trail.** Ship v1.0 of an edition, snapshot it,
  edit freely toward v1.1; the v1.0 build remains reproducible
  from the snapshot.
- **Reviewer hand-off.** Snapshot before sending to an editor /
  approver; restore if they reject the changes.
- **Diff-by-version.** Compare the v1.0 snapshot against the
  current state to see exactly what's drifted.

Storage layout::

    content/snapshots/
      <edition_id>/
        <version>/                # e.g. "v1.0", "2026-05-09",
                                  #   "before-cover-redesign"
          edition.yaml            # frozen edition record (YAML)
          metadata.yaml           # label + notes + created + corpus_hash

Pure functions only; HTTP layer in scripts/web.py wraps these for
the route adapters. Atomic writes via notes_io.

Naming: `version` follows the same name regex as scenarios
(`[a-z0-9][a-z0-9._-]{0,40}`) so URL-safety is uniform across
the project's content-addressable surfaces.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from . import config
from . import notes_io
from . import paths


_VERSION_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,40}$")
_EDITION_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,60}$")


def snapshots_dir() -> Path:
    """Absolute path to ``content/snapshots/`` (created on first use)."""
    return paths.content_root() / "snapshots"


def _validate_edition_id(edition_id: str) -> None:
    if not _EDITION_ID_RE.match(edition_id or ""):
        raise ValueError(f"invalid edition id {edition_id!r} — use lowercase a-z, 0-9, ., -, _ (max 61 chars)")


def _validate_version(version: str) -> None:
    if not _VERSION_NAME_RE.match(version or ""):
        raise ValueError(f"invalid version {version!r} — use lowercase a-z, 0-9, ., -, _ (max 41 chars)")


def _snapshot_root(edition_id: str, version: str) -> Path:
    """Path to one snapshot's directory (edition.yaml + metadata.yaml).

    Validates both ids; raises ValueError on bad input.
    """
    _validate_edition_id(edition_id)
    _validate_version(version)
    return snapshots_dir() / edition_id / version


@dataclass(frozen=True)
class SnapshotMeta:
    edition_id: str
    version: str
    label: str
    notes: str
    created: str  # ISO 8601 UTC
    corpus_hash: str  # SHA-1 hex of (notes_dir mtime fingerprint)

    def to_dict(self) -> dict:
        return {
            "edition_id": self.edition_id,
            "version": self.version,
            "label": self.label,
            "notes": self.notes,
            "created": self.created,
            "corpus_hash": self.corpus_hash,
        }


# ----------------------------------------------------------------------
# Corpus fingerprint
# ----------------------------------------------------------------------


def _corpus_fingerprint() -> str:
    """SHA-256 of every notes/<book>.py file's content.

    ω.34 fix: previously this hashed (stem, mtime_ns) — fast but
    unsafe. A `git checkout` that resets every notes file's mtime
    to identical values, or a refactor that preserves mtime (rare
    but possible on Windows reflinks/copy-on-write), produced
    identical "corpus_hash" for genuinely different corpora.
    Snapshots taken before and after such a state change would
    appear equivalent — exactly the regression class snapshots are
    meant to catch.

    Now: read each file's bytes and fold into a single rolling
    sha256. Two snapshots match iff every byte matches. The cost
    is ~50K notes × ~90 bytes/line = a few MB of I/O at snapshot
    time. Snapshots are an interactive operation (the user clicks
    a button); a few hundred ms for correctness is the right
    trade.
    """
    notes_dir = paths.notes_dir()
    if not notes_dir.is_dir():
        return ""
    h = hashlib.sha256()
    for p in sorted(notes_dir.glob("*.py")):
        # Stem framing prevents two adjacent files' bytes from
        # being concatenated and hashing identically to a single
        # larger file. Length-prefix the content as well.
        try:
            data = p.read_bytes()
        except OSError:
            data = b""
        header = f"{p.stem}:{len(data)}\n".encode("utf-8")
        h.update(header)
        h.update(data)
        h.update(b"\n")
    return h.hexdigest()


# ----------------------------------------------------------------------
# Read paths
# ----------------------------------------------------------------------


def list_snapshots(edition_id: str) -> list[SnapshotMeta]:
    """Return every snapshot for ``edition_id``, oldest first.

    An empty edition / missing snapshots dir returns ``[]``. Each
    snapshot's ``metadata.yaml`` is parsed; corrupt records are
    skipped (the directory might still be useful as a backup but
    not as a structured snapshot).
    """
    _validate_edition_id(edition_id)
    root = snapshots_dir() / edition_id
    if not root.is_dir():
        return []
    import yaml

    out: list[SnapshotMeta] = []
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        meta_path = d / "metadata.yaml"
        if not meta_path.is_file():
            continue
        try:
            data = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        out.append(
            SnapshotMeta(
                edition_id=edition_id,
                version=d.name,
                label=str(data.get("label") or d.name),
                notes=str(data.get("notes") or ""),
                created=str(data.get("created") or ""),
                corpus_hash=str(data.get("corpus_hash") or ""),
            )
        )
    return out


def read_snapshot(edition_id: str, version: str) -> Optional[dict]:
    """Return the full snapshot record (edition + metadata).

    Returns ``None`` if the snapshot doesn't exist. Raises
    ``ValueError`` on invalid id/version.
    """
    root = _snapshot_root(edition_id, version)
    edition_path = root / "edition.yaml"
    # Treat the snapshot as gone if its load-bearing file is gone —
    # the directory itself may persist because notes_io.ensure_backup
    # leaves a .backups/ subdir behind on delete.
    if not edition_path.is_file():
        return None
    import yaml

    meta_path = root / "metadata.yaml"
    edition = None
    metadata: dict = {}
    try:
        edition = yaml.safe_load(edition_path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        edition = None
    if meta_path.is_file():
        try:
            metadata = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            metadata = {}
    return {
        "edition_id": edition_id,
        "version": version,
        "edition": edition,
        "metadata": metadata,
    }


# ----------------------------------------------------------------------
# Write paths
# ----------------------------------------------------------------------


def create_snapshot(
    edition_id: str,
    version: str,
    *,
    label: Optional[str] = None,
    notes: Optional[str] = None,
    overwrite: bool = False,
) -> dict:
    """Create a snapshot of the named edition's current record.

    Returns ``{"status": "ok", "edition_id", "version", "metadata"}``
    on success; ``{"status": "error", "code", "http", "message"}``
    on bad input or conflict.

    Edition must exist in editions.yaml. Snapshot files are written
    atomically via ``notes_io.atomic_write``.
    """
    try:
        _validate_edition_id(edition_id)
        _validate_version(version)
    except ValueError as e:
        return {"status": "error", "code": "invalid_name", "http": 400, "message": str(e)}

    editions = config.editions_by_id()
    if edition_id not in editions:
        return {"status": "error", "code": "unknown_edition", "http": 400, "message": f"unknown edition: {edition_id}"}

    root = snapshots_dir() / edition_id / version
    edition_path = root / "edition.yaml"
    meta_path = root / "metadata.yaml"
    if edition_path.is_file() and not overwrite:
        return {
            "status": "error",
            "code": "conflict",
            "http": 409,
            "message": f"snapshot {edition_id!r}/{version!r} already exists",
        }

    edition_record = editions[edition_id]
    created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    corpus_hash = _corpus_fingerprint()
    metadata = {
        "label": label or version,
        "notes": notes or "",
        "created": created,
        "corpus_hash": corpus_hash,
    }

    root.mkdir(parents=True, exist_ok=True)
    import yaml

    edition_text = yaml.safe_dump(
        edition_record,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
    meta_text = yaml.safe_dump(
        metadata,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
    if edition_path.is_file():
        notes_io.ensure_backup(edition_path)
    notes_io.atomic_write(edition_path, edition_text)
    if meta_path.is_file():
        notes_io.ensure_backup(meta_path)
    notes_io.atomic_write(meta_path, meta_text)

    return {
        "status": "ok",
        "edition_id": edition_id,
        "version": version,
        "metadata": metadata,
    }


def delete_snapshot(edition_id: str, version: str) -> dict:
    """Remove a snapshot directory after backing up its files.

    Returns ``{"status": "ok"}`` or an error envelope.
    """
    try:
        root = _snapshot_root(edition_id, version)
    except ValueError as e:
        return {"status": "error", "code": "invalid_name", "http": 400, "message": str(e)}
    if not root.is_dir():
        return {
            "status": "error",
            "code": "not_found",
            "http": 404,
            "message": f"snapshot {edition_id!r}/{version!r} not found",
        }
    for f in (root / "edition.yaml", root / "metadata.yaml"):
        if f.is_file():
            notes_io.ensure_backup(f)
            f.unlink()
    # Drop the directory if it's now empty (best-effort; leftover
    # files from earlier extension phases are preserved).
    try:
        root.rmdir()
    except OSError:
        pass
    return {"status": "ok", "edition_id": edition_id, "version": version}


# ----------------------------------------------------------------------
# Diff path
# ----------------------------------------------------------------------


def diff_snapshot(
    edition_id: str,
    version: str,
    *,
    against_version: Optional[str] = None,
) -> dict:
    """Compute a structural diff between a snapshot and either
    another snapshot or the live edition record.

    `against_version=None` (default) compares the snapshot vs the
    current live edition. Otherwise compares snapshot↔snapshot.

    Returns ``{"status": "ok", "from": ..., "to": ..., "added":
    {field: value}, "removed": {field: value}, "changed":
    {field: {"from": ..., "to": ...}}}`` on success.
    """
    base = read_snapshot(edition_id, version)
    if base is None:
        return {
            "status": "error",
            "code": "not_found",
            "http": 404,
            "message": f"snapshot {edition_id!r}/{version!r} not found",
        }
    a = base["edition"] or {}
    if against_version is None:
        editions = config.editions_by_id()
        b = editions.get(edition_id, {})
        b_label = "current"
    else:
        other = read_snapshot(edition_id, against_version)
        if other is None:
            return {
                "status": "error",
                "code": "not_found",
                "http": 404,
                "message": f"snapshot {edition_id!r}/{against_version!r} not found",
            }
        b = other["edition"] or {}
        b_label = against_version

    if not isinstance(a, dict):
        a = {}
    if not isinstance(b, dict):
        b = {}

    added: dict = {}
    removed: dict = {}
    changed: dict = {}
    keys = set(a.keys()) | set(b.keys())
    for k in sorted(keys):
        if k not in a:
            added[k] = b[k]
        elif k not in b:
            removed[k] = a[k]
        elif a[k] != b[k]:
            changed[k] = {"from": a[k], "to": b[k]}
    return {
        "status": "ok",
        "edition_id": edition_id,
        "from": version,
        "to": b_label,
        "added": added,
        "removed": removed,
        "changed": changed,
        "identical": not (added or removed or changed),
    }


# ----------------------------------------------------------------------
# Restore path
# ----------------------------------------------------------------------


def _dump_scalar(v) -> str:
    """Serialize a scalar in the format `_parse_yaml_records` accepts.

    The project's custom YAML parser expects bare values (no quotes)
    for most strings, JSON-quoted strings when the value contains
    `:` / `#` / leading dash / etc. Bools as `true`/`false`; ints
    bare; None as `null`.
    """
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    # Quote if value would parse ambiguously bare. Conservative
    # ruleset; over-quoting is harmless for the project parser.
    needs_quote = (
        s == ""
        or s in ("null", "true", "false", "yes", "no")
        or any(c in s for c in ":#\"'\n\t")
        or s.startswith("- ")
        or s.startswith("[")
        or s.startswith("{")
        or s.startswith("&")
        or s.startswith("*")
        or s.startswith("!")
        or s.startswith("|")
        or s.startswith(">")
        or s.startswith("@")
        or s.lstrip("-").replace(".", "", 1).isdigit()
    )
    if needs_quote:
        import json

        return json.dumps(s, ensure_ascii=False)
    return s


def _dump_edition_record(record: dict) -> str:
    """Produce one edition record in the project's editions.yaml shape.

    Format (matches `_parse_yaml_records` expectations):
        ``  - id: foo\\n    title: Foo\\n    enabled_categories:\\n      - lang``

    Lists become block-sequence sub-blocks indented 6 spaces. Dict-
    valued fields are rejected (project format is flat).
    """
    if "id" not in record:
        raise ValueError("record must have an `id` field")
    keys = list(record.keys())
    # `id` first (must be the leading line so the parser sees the
    # record start); everything else in the order we received.
    keys = ["id"] + [k for k in keys if k != "id"]
    lines: list[str] = []
    for i, key in enumerate(keys):
        prefix = "  - " if i == 0 else "    "
        value = record[key]
        if isinstance(value, dict):
            raise ValueError(
                f"field {key!r} has a dict value; project YAML format "
                f"is flat. Snapshot may have been taken from a "
                f"non-standard editions.yaml."
            )
        if isinstance(value, list):
            lines.append(f"{prefix}{key}:")
            for item in value:
                lines.append(f"      - {_dump_scalar(item)}")
        else:
            lines.append(f"{prefix}{key}: {_dump_scalar(value)}")
    return "\n".join(lines) + "\n"


def restore_snapshot(edition_id: str, version: str) -> dict:
    """Overwrite the live edition record from a snapshot.

    Uses the project's custom YAML output format (matching
    `_parse_yaml_records`), backs up the current editions.yaml,
    and validates the rewritten file by re-parsing it before
    declaring success — if the new file would fail the project
    parser, the write is aborted before any damage.

    Out of scope (deferred): granular field-level restore (only
    the kinds, not the cover, etc.). v1 is full-record restore.
    """
    try:
        _validate_edition_id(edition_id)
        _validate_version(version)
    except ValueError as e:
        return {"status": "error", "code": "invalid_name", "http": 400, "message": str(e)}

    snap = read_snapshot(edition_id, version)
    if snap is None or snap.get("edition") is None:
        return {
            "status": "error",
            "code": "not_found",
            "http": 404,
            "message": f"snapshot {edition_id!r}/{version!r} not found",
        }
    snap_record = snap["edition"]
    if not isinstance(snap_record, dict):
        return {
            "status": "error",
            "code": "corrupt_snapshot",
            "http": 422,
            "message": "snapshot edition.yaml is not a mapping",
        }

    editions_path = paths.content_root() / "editions.yaml"
    if not editions_path.is_file():
        return {"status": "error", "code": "no_editions_yaml", "http": 503, "message": "editions.yaml missing"}

    # Splice the new record into the existing file, replacing the
    # block whose `  - id: <edition_id>` matches. Each record's
    # block runs from its leading `  - id:` line up to the next
    # `  - id:` (or end of file). Comments + structural quirks
    # everywhere else are preserved.
    text = editions_path.read_text(encoding="utf-8")
    try:
        new_record_text = _dump_edition_record(snap_record)
    except ValueError as e:
        return {"status": "error", "code": "corrupt_snapshot", "http": 422, "message": str(e)}

    import re as _re

    block_re = _re.compile(
        rf"(^  - id: {_re.escape(edition_id)}(?:\s|$).*?\n)"
        rf"(.*?)"
        rf"(?=^  - id:|\Z)",
        _re.MULTILINE | _re.DOTALL,
    )
    m = block_re.search(text)
    appended = False
    if m:
        new_text = text[: m.start()] + new_record_text + text[m.end() :]
    else:
        # Edition not present in the live file — append at the end.
        # Ensure trailing newline so the next `  - id:` anchor sits
        # at column 2 of its own line.
        if not text.endswith("\n"):
            text += "\n"
        new_text = text + new_record_text
        appended = True

    # Validate the new content with the SAME parser the project uses
    # to read editions.yaml — if it can't be parsed, abort before
    # writing to disk. Defense in depth.
    try:
        parsed = config._parse_yaml_records(new_text)
    except Exception as e:  # pragma: no cover - defensive
        return {
            "status": "error",
            "code": "format_validation_failed",
            "http": 422,
            "message": f"rewritten editions.yaml would not parse: {e}",
        }
    parsed_ids = {e.get("id") for e in parsed if isinstance(e, dict)}
    if edition_id not in parsed_ids:
        return {
            "status": "error",
            "code": "format_validation_failed",
            "http": 422,
            "message": f"rewritten editions.yaml lost {edition_id!r} after re-parse",
        }

    notes_io.ensure_backup(editions_path)
    notes_io.atomic_write(editions_path, new_text)

    # Drop caches so the next /api/matrix sees the restored state.
    config.load_editions.cache_clear()
    try:
        from . import matrix as matrix_mod

        matrix_mod.compute_matrix.cache_clear()
    except Exception:  # pragma: no cover - defensive
        pass

    return {
        "status": "ok",
        "edition_id": edition_id,
        "version": version,
        "appended": appended,
    }
