"""item-② root cause (2026-06-11, Mac turn 71): `restore_snapshot` re-dumped
the edition record from parsed YAML, silently DROPPING in-block comments
(e.g. the RX P4a comment above catholic-study's `reader_toc_collapsible`).
The write was value-identical but byte-different — the protected-paths
session guard then fired or not depending on whether a byte-restoring test
ran later, which IS the CI ordering-flake pair.

Fix: snapshots capture the record's RAW BLOCK TEXT (`block.yaml`) at create
time; restore splices it back byte-exact. Old snapshots without the raw
block fall back to the historical `_dump_edition_record` path.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from scripts.core import config, snapshots

REPO = Path(config.__file__).resolve().parents[2]
EDITIONS = REPO / "content" / "editions.yaml"
EDITION = "catholic-study"
VERSION = "blocktest_rs1"


def _cleanup_snapshot() -> None:
    root = snapshots.snapshots_dir() / EDITION / VERSION
    if root.is_dir():
        shutil.rmtree(root, ignore_errors=True)


class TestSnapshotRawBlock:
    def test_create_captures_raw_block_with_comments(self):
        before = EDITIONS.read_bytes()
        try:
            r = snapshots.create_snapshot(EDITION, VERSION)
            assert r["status"] == "ok"
            block_path = snapshots.snapshots_dir() / EDITION / VERSION / "block.yaml"
            assert block_path.is_file(), "snapshot must capture the raw editions.yaml block"
            block = block_path.read_text(encoding="utf-8")
            assert block.startswith(f"  - id: {EDITION}")
            # the in-block comment that the old dump path dropped
            assert "#" in block, "raw block must carry the record's comments"
            assert block in EDITIONS.read_text(encoding="utf-8")
        finally:
            _cleanup_snapshot()
            EDITIONS.write_bytes(before)
            config.load_editions.cache_clear()

    def test_restore_is_byte_identical_round_trip(self):
        """THE flake-killer pin: snapshot-then-restore with no intervening
        edit must leave editions.yaml BYTE-identical (comments included)."""
        before = EDITIONS.read_bytes()
        try:
            snapshots.create_snapshot(EDITION, VERSION)
            r = snapshots.restore_snapshot(EDITION, VERSION)
            assert r["status"] == "ok"
            assert EDITIONS.read_bytes() == before, (
                "restore_snapshot must round-trip byte-identically — "
                "a value-identical/byte-different write is the item-② flake class"
            )
        finally:
            _cleanup_snapshot()
            EDITIONS.write_bytes(before)
            config.load_editions.cache_clear()

    def test_restore_falls_back_for_old_snapshots_without_block(self):
        before = EDITIONS.read_bytes()
        try:
            snapshots.create_snapshot(EDITION, VERSION)
            block_path = snapshots.snapshots_dir() / EDITION / VERSION / "block.yaml"
            if block_path.is_file():
                block_path.unlink()  # simulate a pre-fix snapshot
            r = snapshots.restore_snapshot(EDITION, VERSION)
            assert r["status"] == "ok"
            after = dict(config.editions_by_id()[EDITION])
            assert after["id"] == EDITION  # record still parses + matches
        finally:
            _cleanup_snapshot()
            EDITIONS.write_bytes(before)
            config.load_editions.cache_clear()
