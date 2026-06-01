#!/usr/bin/env python3
"""Determinism guard for the EPUB packager (M14).

``build_epub.build`` must produce a BYTE-IDENTICAL .epub regardless of the
on-disk mtimes of the working-dir inputs. Pre-fix, ``zipfile.ZipFile.write``
inherited each entry's ``date_time`` from the file mtime, so the central
directory drifted across checkouts. The fix pins every entry's ``date_time``
to the zip epoch minimum (1980-01-01). These tests fail pre-fix, pass post-fix.

Everything here runs against a tiny FIXTURE working dir in ``tmp_path`` — it
never touches the real ``epub_working/`` tree and never runs a real build.
"""

import os
import sys
import zipfile
from pathlib import Path

# build_epub lives in scripts/ (not an installed package); make it importable.
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_epub  # noqa: E402

ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)


def _make_fixture(root: Path) -> Path:
    """Create the minimal working dir validate_working_dir() accepts."""
    epub = root / "epub_working"
    epub.mkdir()
    # mimetype: exact content required by validate_working_dir().
    (epub / "mimetype").write_text("application/epub+zip", encoding="utf-8")
    (epub / "content.opf").write_text(
        '<?xml version="1.0"?>\n<package><metadata/></package>\n',
        encoding="utf-8",
    )
    meta = epub / "META-INF"
    meta.mkdir()
    (meta / "container.xml").write_text(
        '<?xml version="1.0"?>\n<container/>\n',
        encoding="utf-8",
    )
    return epub


def test_build_is_byte_identical_across_mtimes(tmp_path):
    """Two builds of the same content with different input mtimes match byte-for-byte."""
    epub = _make_fixture(tmp_path)

    out1 = tmp_path / "out1.epub"
    build_epub.build(epub, out1, bump=False)

    # Perturb input mtimes: a naive packager would bake these into date_time.
    os.utime(epub / "content.opf", (100_000_000, 100_000_000))
    os.utime(epub / "mimetype", (200_000_000, 200_000_000))
    os.utime(epub / "META-INF" / "container.xml", (300_000_000, 300_000_000))

    out2 = tmp_path / "out2.epub"
    build_epub.build(epub, out2, bump=False)

    assert out1.read_bytes() == out2.read_bytes(), "EPUB output is not reproducible across input mtimes (M14)"


def test_mimetype_first_stored_and_dates_pinned(tmp_path):
    """First entry is mimetype/ZIP_STORED and every entry's date_time is the zip epoch."""
    epub = _make_fixture(tmp_path)
    out = tmp_path / "out.epub"
    build_epub.build(epub, out, bump=False)

    with zipfile.ZipFile(out) as zf:
        infos = zf.infolist()

    assert infos, "EPUB has no entries"
    first = infos[0]
    assert first.filename == "mimetype", f"first entry is {first.filename!r}, not mimetype"
    assert first.compress_type == zipfile.ZIP_STORED, "mimetype must be ZIP_STORED"

    for zi in infos:
        assert zi.date_time == ZIP_EPOCH, f"entry {zi.filename!r} date_time={zi.date_time} (expected {ZIP_EPOCH})"
