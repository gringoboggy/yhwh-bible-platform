"""LOAD-BEARING-NO-LONGER as of Ω.0 free-public pivot (2026-05-14).
Tracks per-edition distribution state for the surviving FREE surfaces
(archive.org / own site). The commercial channels were removed in Phase 4
(decommercialize); the data file content/distribution.json is preserved on
disk for archival/audit purposes. Retained per §7.4.

ε.6 — distribution channel checklist (2026-05-11).

Tracks per-edition shipped-to-channel state so the publisher can see
which editions have been pushed to archive.org or their own site.

**Storage**: `content/distribution.json` (machine-managed JSON; sibling
to `content/sources/*.json`). Atomic write via `notes_io.atomic_write`
with backup snapshot, so a partial write can never leave the file
half-mutated.

**Channels** (`DISTRIBUTION_CHANNELS`): archive_org, own_site — the
free distribution surfaces. archive.org auto-marks after a successful
upload (scripts/api/archive_org.py); own_site is a manual mark.

**Schema** (v1):

    {
      "schema_version": 1,
      "editions": {
        "<edition_id>": {
          "<channel_id>": {
            "shipped_at": "<iso-8601 utc>",
            "url": "<optional>",
            "notes": "<optional>"
          }
        }
      }
    }

Missing edition / missing channel = not shipped (rather than an
explicit `false` flag — sparse store).

**Public API**:
    DISTRIBUTION_CHANNELS                            tuple of channel ids
    CHANNEL_LABELS                                   {id: human label}
    SCHEMA_VERSION                                   current schema version
    load_distribution()                              dict (whole file)
    save_distribution(state)                         atomic write
    is_shipped(state, edition_id, channel_id)        bool
    mark_shipped(edition_id, channel_id, **fields)   write helper
    mark_unshipped(edition_id, channel_id)           write helper
    rollup(state, editions)                          {state, coverage, ...}
    edition_channels(state, edition_id)              dict[channel_id, entry]

Foundation for ε.7 (press kit auto-build consumes the channel state
to know which formats to package), ο.4 (archive.org auto-upload
auto-marks `archive_org` after a successful push), and any future
"channels to ship to" UI in the workflow consoles.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Iterable

from . import notes_io


DISTRIBUTION_CHANNELS: tuple[str, ...] = (
    "archive_org",
    "own_site",
)

CHANNEL_LABELS: dict[str, str] = {
    "archive_org": "Archive.org",
    "own_site": "Own site",
}

SCHEMA_VERSION = 1

# Per-entry fields that callers may store. Anything else is dropped on
# save (defensive against future schema drift from a stale client).
ENTRY_FIELDS: tuple[str, ...] = ("shipped_at", "url", "notes")


_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _distribution_path() -> Path:
    """Canonical path. Function (not constant) so tests can monkeypatch
    via a single attribute — mirrors the pattern in event_log.py."""
    return _REPO_ROOT / "content" / "distribution.json"


def _now_iso() -> str:
    """ISO-8601 UTC timestamp. Mirrors event_log._now_iso so the
    on-disk format is identical to the event-log timestamp format."""
    return datetime.now(timezone.utc).isoformat()


def _empty_state() -> dict:
    """The canonical empty state."""
    return {"schema_version": SCHEMA_VERSION, "editions": {}}


def load_distribution() -> dict:
    """Load `content/distribution.json`. Returns the empty state when
    the file doesn't exist or is malformed (so callers don't need to
    error-handle each read).

    Schema-version drift is logged on load (returns the file as-is
    even if `schema_version` is unexpected — caller can decide to
    migrate). Currently the only known schema version is 1.
    """
    path = _distribution_path()
    if not path.is_file():
        return _empty_state()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return _empty_state()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return _empty_state()
    if not isinstance(data, dict):
        return _empty_state()
    # Defensive: rehydrate missing keys so callers can index into the
    # state without per-key guards.
    if "schema_version" not in data:
        data["schema_version"] = SCHEMA_VERSION
    if "editions" not in data or not isinstance(data["editions"], dict):
        data["editions"] = {}
    return data


def save_distribution(state: dict) -> Path:
    """Persist `state` to `content/distribution.json` atomically.

    `state` is normalized before write: schema_version is forced to the
    current `SCHEMA_VERSION`; editions and per-channel entries are
    filtered to known fields only (drops stale clients' extras).
    """
    cleaned: dict = {"schema_version": SCHEMA_VERSION, "editions": {}}
    editions = state.get("editions", {}) if isinstance(state, dict) else {}
    if isinstance(editions, dict):
        for ed_id, channels in editions.items():
            if not isinstance(channels, dict):
                continue
            ed_id_str = str(ed_id)
            cleaned_channels: dict = {}
            for ch_id, entry in channels.items():
                if ch_id not in DISTRIBUTION_CHANNELS:
                    continue
                if not isinstance(entry, dict):
                    continue
                cleaned_entry = {k: entry[k] for k in ENTRY_FIELDS if k in entry}
                cleaned_channels[ch_id] = cleaned_entry
            if cleaned_channels:
                cleaned["editions"][ed_id_str] = cleaned_channels

    path = _distribution_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        notes_io.ensure_backup(path)
    text = json.dumps(cleaned, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    notes_io.atomic_write(path, text)
    return path


def is_shipped(state: dict, edition_id: str, channel_id: str) -> bool:
    """True iff `state` records a shipped entry for the edition/channel
    pair. Missing edition + missing channel both return False."""
    if channel_id not in DISTRIBUTION_CHANNELS:
        return False
    eds = state.get("editions", {}) if isinstance(state, dict) else {}
    entry = eds.get(edition_id, {}).get(channel_id) if isinstance(eds, dict) else None
    return isinstance(entry, dict)


def edition_channels(state: dict, edition_id: str) -> dict:
    """Return the per-channel state dict for one edition. Empty dict
    when the edition has no shipped channels yet."""
    eds = state.get("editions", {}) if isinstance(state, dict) else {}
    entry = eds.get(edition_id, {}) if isinstance(eds, dict) else {}
    return dict(entry) if isinstance(entry, dict) else {}


def mark_shipped(
    edition_id: str,
    channel_id: str,
    *,
    url: str | None = None,
    notes: str | None = None,
    shipped_at: str | None = None,
) -> dict:
    """Mark `edition_id × channel_id` as shipped. Loads → mutates →
    saves the whole state file. Returns the entry that was written.

    `shipped_at` defaults to now (UTC) when omitted. Existing entries
    are preserved: re-marking with no override keeps the existing
    `shipped_at` and merges new optional fields without dropping prior
    ones. To wipe an entry use `mark_unshipped`.
    """
    if channel_id not in DISTRIBUTION_CHANNELS:
        raise ValueError(f"unknown distribution channel: {channel_id!r} (known: {', '.join(DISTRIBUTION_CHANNELS)})")
    state = load_distribution()
    editions = state.setdefault("editions", {})
    channels = editions.setdefault(edition_id, {})
    entry = dict(channels.get(channel_id, {}))
    if "shipped_at" not in entry:
        entry["shipped_at"] = shipped_at or _now_iso()
    elif shipped_at:
        entry["shipped_at"] = shipped_at
    if url is not None:
        entry["url"] = url
    if notes is not None:
        entry["notes"] = notes
    channels[channel_id] = entry
    save_distribution(state)
    return entry


def mark_unshipped(edition_id: str, channel_id: str) -> bool:
    """Remove the entry for `edition_id × channel_id`. Returns True
    when something was removed, False otherwise (idempotent — already-
    absent entries silently return False)."""
    if channel_id not in DISTRIBUTION_CHANNELS:
        return False
    state = load_distribution()
    editions = state.get("editions", {}) if isinstance(state, dict) else {}
    channels = editions.get(edition_id, {}) if isinstance(editions, dict) else {}
    if channel_id not in channels:
        return False
    del channels[channel_id]
    if not channels:
        # Drop the whole edition row when it has no channels left so
        # the JSON stays sparse.
        editions.pop(edition_id, None)
    save_distribution(state)
    return True


def rollup(state: dict, editions: Iterable[dict]) -> dict:
    """Compose a UI-friendly view: per-edition channel grid + per-channel
    coverage % + overall coverage.

    `editions` is the canonical edition list (typically
    `config.load_editions()`); the rollup uses the FULL edition list so
    an edition with zero shipped channels still appears as a row of
    "not shipped" cells.

    Shape:
        {
          "channels": [{"id": str, "label": str}, ...],
          "editions": [{"id": str, "title": str,
                        "channels": {ch_id: {shipped: bool,
                                             url?, notes?,
                                             shipped_at?}}}],
          "by_channel_coverage": {ch_id: {"shipped": int, "total": int,
                                          "percent": float}},
          "overall": {"shipped_cells": int, "total_cells": int,
                      "percent": float},
        }
    """
    eds_list = list(editions)
    eds_state = state.get("editions", {}) if isinstance(state, dict) else {}
    if not isinstance(eds_state, dict):
        eds_state = {}

    out_channels = [{"id": ch, "label": CHANNEL_LABELS[ch]} for ch in DISTRIBUTION_CHANNELS]
    out_editions: list[dict] = []
    channel_totals = {ch: 0 for ch in DISTRIBUTION_CHANNELS}
    shipped_cells = 0
    total_cells = len(eds_list) * len(DISTRIBUTION_CHANNELS)

    for ed in eds_list:
        ed_id = str(ed.get("id", ""))
        title = str(ed.get("title", ed_id))
        per_channel: dict = {}
        ed_channels = eds_state.get(ed_id, {}) if isinstance(eds_state, dict) else {}
        if not isinstance(ed_channels, dict):
            ed_channels = {}
        for ch in DISTRIBUTION_CHANNELS:
            entry = ed_channels.get(ch)
            if isinstance(entry, dict):
                cell = {"shipped": True}
                for f in ENTRY_FIELDS:
                    if f in entry:
                        cell[f] = entry[f]
                per_channel[ch] = cell
                channel_totals[ch] += 1
                shipped_cells += 1
            else:
                per_channel[ch] = {"shipped": False}
        out_editions.append({"id": ed_id, "title": title, "channels": per_channel})

    n_editions = len(eds_list)
    by_channel_coverage = {
        ch: {
            "shipped": channel_totals[ch],
            "total": n_editions,
            "percent": round((channel_totals[ch] / n_editions * 100.0) if n_editions else 0.0, 2),
        }
        for ch in DISTRIBUTION_CHANNELS
    }
    overall = {
        "shipped_cells": shipped_cells,
        "total_cells": total_cells,
        "percent": round((shipped_cells / total_cells * 100.0) if total_cells else 0.0, 2),
    }
    return {
        "channels": out_channels,
        "editions": out_editions,
        "by_channel_coverage": by_channel_coverage,
        "overall": overall,
    }
