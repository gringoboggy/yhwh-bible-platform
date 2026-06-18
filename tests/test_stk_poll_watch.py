"""STK background poll watch — library snapshot helper."""

from pathlib import Path

from dev.reader_sim.kindle_library import iter_library_files, kindle_data_root


def test_iter_library_files_on_real_lassen_when_present():
    root = kindle_data_root()
    if root is None:
        return
    files = iter_library_files(root)
    assert isinstance(files, list)
    assert all(isinstance(p, Path) for p in files)
