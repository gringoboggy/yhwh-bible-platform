"""Build smoke test — regression guard for the 2026-05-21 base-HTML gap.

The EPUB build *source* (``epub_working/index_split_*.html`` — the World
English Bible scripture text that notes inject into) was lost in the
2026-05-08 repo re-init (never committed) and silently broke every build
until it was recovered + committed (5ee2ad1, 2026-05-21). The
"smoother-running" audit (P1) asked for a smoke test that builds one
edition and asserts a valid EPUB, so the gap can never recur silently.

Two tiers:
  - fast pins: the base scripture HTML is present + substantive on disk
    (these would have flagged the gap the instant it appeared);
  - integration: ``build_one()`` produces a structurally valid EPUB that
    actually *contains* that scripture HTML — exercising the real build
    path (filter -> zip) with no epubcheck/Java dependency.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EPUB_WORKING = REPO / "epub_working"


class TestBaseScriptureHtmlPresent:
    """The build source must exist on disk — the cheap pins that would
    have caught the lost-base-HTML gap immediately."""

    def test_split_html_files_present(self):
        splits = sorted(EPUB_WORKING.glob("index_split_*.html"))
        assert len(splits) >= 50, (
            f"base scripture HTML missing/incomplete: found {len(splits)} "
            "index_split_*.html files in epub_working/ (expected the full WEB text)"
        )

    def test_split_html_is_substantive(self):
        total = sum(p.stat().st_size for p in EPUB_WORKING.glob("index_split_*.html"))
        assert total > 1_000_000, (
            f"base scripture HTML present but tiny ({total} bytes) — likely stubs, "
            "not the real World English Bible text"
        )

    def test_opf_and_nav_present(self):
        assert (EPUB_WORKING / "content.opf").is_file(), "content.opf missing from build source"
        assert (EPUB_WORKING / "nav.xhtml").is_file(), "nav.xhtml missing from build source"


class TestEbibleBuildProducesValidEpub:
    """``ebible build`` for one edition must yield a structurally valid
    EPUB that contains the base scripture HTML. Exercises the real
    ``build_one()`` path; no epubcheck/Java required."""

    EDITION = "ethiopian-tewahedo"

    def test_build_one_yields_valid_epub(self, tmp_path, monkeypatch):
        import scripts.build_edition as be
        from scripts.core import build_cache, config

        # Hermetic: neither read from nor write to the persistent build cache.
        monkeypatch.setattr(build_cache, "cache_lookup", lambda *a, **k: None)
        monkeypatch.setattr(build_cache, "cache_store", lambda *a, **k: None)

        assert self.EDITION in config.editions_by_id(), f"flagship edition {self.EDITION!r} missing"
        all_kinds = config.load_kinds()

        stats = be.build_one(self.EDITION, tmp_path, "smoke-test", all_kinds, force=True)

        epub = Path(stats["output_path"])
        assert epub.is_file(), "build_one reported success but no EPUB landed on disk"
        assert not stats.get("skipped"), "build was skipped — force=True must always build"
        assert stats["size_mb"] > 0.5, f"EPUB suspiciously small ({stats['size_mb']:.2f} MB) — empty shell?"

        with zipfile.ZipFile(epub) as zf:
            assert zf.testzip() is None, "corrupt EPUB zip"
            names = zf.namelist()
            # OCF spec: 'mimetype' must be the first entry AND stored uncompressed.
            assert names[0] == "mimetype", f"first zip entry must be 'mimetype', got {names[0]!r}"
            assert zf.getinfo("mimetype").compress_type == zipfile.ZIP_STORED, "mimetype must be stored, not deflated"
            assert zf.read("mimetype") == b"application/epub+zip"
            assert "META-INF/container.xml" in names, "EPUB missing OCF container.xml"
            assert any(n.endswith("content.opf") for n in names), "no OPF package document in EPUB"
            # The regression pin: the scripture text actually made it into the book.
            splits = [n for n in names if "index_split_" in n and n.endswith(".html")]
            assert len(splits) >= 50, (
                f"EPUB contains only {len(splits)} scripture split files — the base-HTML gap is back"
            )
