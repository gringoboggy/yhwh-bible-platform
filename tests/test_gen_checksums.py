"""Tests for the release-artifact SHA-256 manifest generator."""

import hashlib

from scripts.gen_checksums import gen_checksums, render, sha256_file


def test_sha256_matches_hashlib(tmp_path):
    f = tmp_path / "YHWH-1.0.0-beta.1.dmg"
    f.write_bytes(b"hello manuscript")
    assert sha256_file(f) == hashlib.sha256(b"hello manuscript").hexdigest()


def test_picks_artifacts_and_skips_non_artifacts(tmp_path):
    (tmp_path / "YHWH-Setup-1.0.0-beta.1.exe").write_bytes(b"win")
    (tmp_path / "YHWH-1.0.0-beta.1.dmg").write_bytes(b"mac")
    (tmp_path / "YHWH-1.0.0-beta.1-x86_64.AppImage").write_bytes(b"lin")
    (tmp_path / "notes.txt").write_text("ignore me")  # non-artifact extension
    (tmp_path / "SHA256SUMS.txt").write_text("stale")  # must skip itself (idempotent)

    names = [name for _, name in gen_checksums(tmp_path)]
    assert names == sorted(
        [
            "YHWH-1.0.0-beta.1-x86_64.AppImage",
            "YHWH-1.0.0-beta.1.dmg",
            "YHWH-Setup-1.0.0-beta.1.exe",
        ]
    )
    assert "notes.txt" not in names
    assert "SHA256SUMS.txt" not in names


def test_render_is_sha256sum_compatible(tmp_path):
    (tmp_path / "a.dmg").write_bytes(b"x")
    line = render(gen_checksums(tmp_path))
    assert line == f"{hashlib.sha256(b'x').hexdigest()}  a.dmg\n"  # two-space binary mode


def test_no_artifacts_returns_empty(tmp_path):
    (tmp_path / "readme.md").write_text("nothing to hash")
    assert gen_checksums(tmp_path) == []


def test_epub_and_kepub_included_by_default(tmp_path):
    """round-7 3.1: .epub was missing from DEFAULT_EXTS, so the EPUB + kepub
    asset families were silently absent from every default-invocation
    SHA256SUMS (notary_autofinish.sh passes no --ext). The suffix-tuple match
    makes one ".epub" entry cover ".kepub.epub" too."""
    (tmp_path / "Ethiopian_Bible_ethiopian-tewahedo_v0.1.0.epub").write_bytes(b"epub")
    (tmp_path / "Ethiopian_Bible_ethiopian-tewahedo_v0.1.0.kepub.epub").write_bytes(b"kepub")
    (tmp_path / "YHWH-0.1.0.dmg").write_bytes(b"mac")

    names = [name for _, name in gen_checksums(tmp_path)]
    assert "Ethiopian_Bible_ethiopian-tewahedo_v0.1.0.epub" in names
    assert "Ethiopian_Bible_ethiopian-tewahedo_v0.1.0.kepub.epub" in names
    assert "YHWH-0.1.0.dmg" in names
