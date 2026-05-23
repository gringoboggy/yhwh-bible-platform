"""Per-edition cover application — build_edition must swap the base master
cover (epub_working/cover.jpeg) for the edition's declared cover_image so each
built EPUB ships its own curated cover. Fixes visual-QA finding (b): 9/11
editions declare a distinct cover that the build previously ignored. The 2
standalone bibles (empty cover_image) + any unset edition keep the master."""

from __future__ import annotations

import zipfile
from pathlib import Path

from scripts.core import config

REPO = Path(config.__file__).resolve().parents[2]
COVERS = REPO / "content" / "covers"


class TestApplyEditionCover:
    def test_declared_cover_replaces_master(self, tmp_path):
        from scripts.build_edition import apply_edition_cover

        dst = tmp_path / "cover.jpeg"
        dst.write_bytes(b"MASTER-COVER-PLACEHOLDER")
        applied = apply_edition_cover({"cover_image": "covers/catholic-study.jpg"}, tmp_path)

        assert applied == "covers/catholic-study.jpg"
        assert dst.read_bytes() == (COVERS / "catholic-study.jpg").read_bytes()
        assert dst.read_bytes() != b"MASTER-COVER-PLACEHOLDER"

    def test_empty_cover_image_keeps_master(self, tmp_path):
        """Standalone bibles declare cover_image: '' — the master cover stays
        (back-compat: builds for editions without a cover are byte-identical)."""
        from scripts.build_edition import apply_edition_cover

        dst = tmp_path / "cover.jpeg"
        dst.write_bytes(b"MASTER-COVER-PLACEHOLDER")
        applied = apply_edition_cover({"cover_image": ""}, tmp_path)

        assert applied is None
        assert dst.read_bytes() == b"MASTER-COVER-PLACEHOLDER"

    def test_missing_cover_file_keeps_master(self, tmp_path):
        from scripts.build_edition import apply_edition_cover

        dst = tmp_path / "cover.jpeg"
        dst.write_bytes(b"MASTER-COVER-PLACEHOLDER")
        applied = apply_edition_cover({"cover_image": "covers/does-not-exist.jpg"}, tmp_path)

        assert applied is None
        assert dst.read_bytes() == b"MASTER-COVER-PLACEHOLDER"

    def test_no_cover_jpeg_in_build_dir_is_a_noop(self, tmp_path):
        """If the base has no cover.jpeg to replace, never create a stray one."""
        from scripts.build_edition import apply_edition_cover

        applied = apply_edition_cover({"cover_image": "covers/catholic-study.jpg"}, tmp_path)
        assert applied is None
        assert not (tmp_path / "cover.jpeg").exists()


class TestCoverReachesEpub:
    """The fix must reach the built EPUB: a declared cover edition's packaged
    cover.jpeg should be the edition's curated cover, not the master."""

    def test_declared_cover_build_ships_edition_cover(self, tmp_path, monkeypatch):
        import scripts.build_edition as be
        from scripts.core import build_cache

        monkeypatch.setattr(build_cache, "cache_lookup", lambda *a, **k: None)
        monkeypatch.setattr(build_cache, "cache_store", lambda *a, **k: None)

        all_kinds = config.load_kinds()
        stats = be.build_one("catholic-study", tmp_path, "cover-test", all_kinds, force=True)
        epub = Path(stats["output_path"])
        assert epub.is_file()
        assert stats.get("cover_applied") == "covers/catholic-study.jpg"

        with zipfile.ZipFile(epub) as zf:
            cover_name = next(n for n in zf.namelist() if n.endswith("cover.jpeg"))
            epub_cover = zf.read(cover_name)

        assert epub_cover == (COVERS / "catholic-study.jpg").read_bytes()
