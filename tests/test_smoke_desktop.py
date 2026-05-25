"""TIER 1 #3 — tests for dev/smoke_desktop.py PyInstaller _MEI* self-cleanup.

The smoke harness force-kills the frozen one-file binary (`taskkill /F`), which
blocks PyInstaller's bootloader from removing its self-extraction directory,
leaking a `_MEI<random>` dir into the temp dir on every run. These tests pin the
snapshot-diff cleanup contract: list the `_MEI*` extraction dirs, and remove ONLY
the ones that appeared during this run — never a pre-existing one (which could
belong to another live frozen process).

`dev/` is not a package, so it is added to sys.path here (mirroring conftest's
REPO_ROOT insert) and imported as a top-level module.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "dev"))

import smoke_desktop  # noqa: E402  (import follows the sys.path insert above)


class TestMeipassDirListing:
    def test_lists_only_mei_subdirectories(self, tmp_path):
        (tmp_path / "_MEI123456").mkdir()
        (tmp_path / "_MEI999999").mkdir()
        (tmp_path / "unrelated").mkdir()
        (tmp_path / "_MEInotadir.txt").write_text("x", encoding="utf-8")

        found = smoke_desktop.meipass_dirs(tmp_path)

        assert found == {tmp_path / "_MEI123456", tmp_path / "_MEI999999"}

    def test_empty_when_no_mei_dirs(self, tmp_path):
        (tmp_path / "unrelated").mkdir()

        assert smoke_desktop.meipass_dirs(tmp_path) == set()


class TestPruneNewMeipassDirs:
    def test_removes_new_keeps_preexisting(self, tmp_path):
        preexisting = tmp_path / "_MEIold0001"
        preexisting.mkdir()
        before = smoke_desktop.meipass_dirs(tmp_path)

        new_empty = tmp_path / "_MEInew0001"
        new_empty.mkdir()
        new_nonempty = tmp_path / "_MEInew0002"
        new_nonempty.mkdir()
        # a non-empty dir proves the removal is recursive (real extraction
        # dirs hold the unpacked interpreter + bundled data).
        (new_nonempty / "python313.dll").write_text("binary", encoding="utf-8")

        removed = smoke_desktop.prune_new_meipass_dirs(before, tmp_path)

        assert preexisting.is_dir(), "a pre-existing _MEI dir must be left alone"
        assert not new_empty.exists()
        assert not new_nonempty.exists()
        assert set(removed) == {new_empty, new_nonempty}

    def test_noop_when_nothing_new(self, tmp_path):
        preexisting = tmp_path / "_MEIold0001"
        preexisting.mkdir()
        before = smoke_desktop.meipass_dirs(tmp_path)

        removed = smoke_desktop.prune_new_meipass_dirs(before, tmp_path)

        assert removed == []
        assert preexisting.is_dir()
