"""Kindle-for-Mac library path discovery (STK channel)."""

from pathlib import Path

from dev.reader_sim.kindle_library import (
    LASSEN_CONTAINER,
    LEGACY_KINDLE_CONTAINER,
    iter_library_files,
    kindle_container_id,
    kindle_data_root,
    library_scan_dirs,
)


def _fake_container(tmp_path: Path, container_id: str) -> Path:
    data = tmp_path / "Library" / "Containers" / container_id / "Data"
    (data / "Library" / "eBooks" / "BOOK").mkdir(parents=True)
    (data / "Documents").mkdir(parents=True)
    return data


class TestKindleLibrary:
    def test_prefers_lassen_over_legacy(self, tmp_path: Path):
        _fake_container(tmp_path, LEGACY_KINDLE_CONTAINER)
        lassen = _fake_container(tmp_path, LASSEN_CONTAINER)
        assert kindle_data_root(tmp_path) == lassen
        assert kindle_container_id(tmp_path) == LASSEN_CONTAINER

    def test_legacy_fallback(self, tmp_path: Path):
        legacy = _fake_container(tmp_path, LEGACY_KINDLE_CONTAINER)
        assert kindle_data_root(tmp_path) == legacy
        assert kindle_container_id(tmp_path) == LEGACY_KINDLE_CONTAINER

    def test_missing_returns_none(self, tmp_path: Path):
        assert kindle_data_root(tmp_path) is None
        assert kindle_container_id(tmp_path) is None

    def test_library_scan_dirs(self, tmp_path: Path):
        data = _fake_container(tmp_path, LASSEN_CONTAINER)
        dirs = library_scan_dirs(data)
        assert data / "Library" in dirs
        assert data / "Documents" in dirs

    def test_iter_library_files_finds_kfx_and_epub(self, tmp_path: Path):
        data = _fake_container(tmp_path, LASSEN_CONTAINER)
        kfx = data / "Library" / "eBooks" / "BOOK" / "BookManifest.kfx"
        kfx.write_text("x")
        epub = data / "Documents" / "test.epub"
        epub.write_bytes(b"PK")
        files = iter_library_files(data)
        assert kfx in files
        assert epub in files
