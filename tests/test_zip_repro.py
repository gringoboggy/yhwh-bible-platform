"""Round-12 zipfile-byte-repro — a shared reproducible-zip helper + the two
previously-unpinned SHIPPING zip writers (press_kit.build_zip, the exports
All-Editions bundle). Extends the W2/W5 byte-determinism class so a build over
identical input yields a byte-identical archive.
"""

from __future__ import annotations

import io
import zipfile


class TestReproducibleZipinfo:
    def test_pins_epoch_and_perms(self):
        from scripts.core.zip_repro import ZIP_EPOCH, reproducible_zipinfo

        info = reproducible_zipinfo("foo.txt")
        assert info.date_time == ZIP_EPOCH == (1980, 1, 1, 0, 0, 0)
        assert info.external_attr == (0o644 << 16)
        assert info.compress_type == zipfile.ZIP_DEFLATED
        # round-13 #6: create_system pinned to 0 (FAT) so the archive is
        # byte-identical regardless of the build host OS (default is 3/UNIX on
        # macOS/Linux, 0 on Windows).
        assert info.create_system == 0
        stored = reproducible_zipinfo("mimetype", stored=True)
        assert stored.compress_type == zipfile.ZIP_STORED
        assert stored.create_system == 0

    def test_bundle_via_helper_is_byte_reproducible(self):
        # The exports All-Editions pattern: writestr(reproducible_zipinfo(name), data).
        from scripts.core.zip_repro import reproducible_zipinfo

        def _bundle():
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for name, data in (("a.epub", b"AAA"), ("b.epub", b"BBB")):
                    zf.writestr(reproducible_zipinfo(name), data)
            return buf.getvalue()

        assert _bundle() == _bundle(), "reproducible_zipinfo bundle not byte-identical"


class TestPressKitZipReproducible:
    def test_build_zip_byte_identical_with_fixed_now(self):
        from datetime import datetime, timezone

        from scripts.core import press_kit

        edition = {"id": "probe-edition-xyz", "title": "Probe Edition"}
        blurbs = {"blurb_150": "one", "blurb_500": "two"}
        fixed = datetime(2026, 1, 1, tzinfo=timezone.utc)
        a = press_kit.build_zip(edition, blurbs, now=fixed)
        b = press_kit.build_zip(edition, blurbs, now=fixed)
        assert a == b, "press_kit build_zip not byte-reproducible with a fixed now="
        with zipfile.ZipFile(io.BytesIO(a)) as zf:
            assert "manifest.json" in zf.namelist()
            for zi in zf.infolist():
                assert zi.date_time == (1980, 1, 1, 0, 0, 0), f"{zi.filename} not epoch-pinned"


class TestOcfMemberBytes:
    """Round-14 A1 — the ``ocf_member_bytes`` CRLF->LF chokepoint that makes a
    packaged EPUB byte-identical regardless of the BUILD host OS. Text members
    are normalized to LF; binary members and the extensionless ``mimetype``
    entry are returned byte-for-byte unchanged; the replace is a no-op on bytes
    that are already LF, so macOS/Linux output does NOT change — only a Windows
    CRLF build converges onto the POSIX baseline."""

    def test_text_members_crlf_collapsed(self):
        from scripts.core.zip_repro import ocf_member_bytes

        # one member per normalized extension (.html .xhtml .xml .opf .ncx .css .svg)
        for name in (
            "OEBPS/index.html",
            "OEBPS/ch1.xhtml",
            "META-INF/container.xml",
            "content.opf",
            "toc.ncx",
            "OEBPS/style.css",
            "OEBPS/cover.svg",
        ):
            assert ocf_member_bytes(name, b"a\r\nb\r\nc") == b"a\nb\nc", name

    def test_extension_match_is_case_insensitive(self):
        from scripts.core.zip_repro import ocf_member_bytes

        assert ocf_member_bytes("OEBPS/CH1.XHTML", b"x\r\ny") == b"x\ny"

    def test_binary_members_untouched(self):
        from scripts.core.zip_repro import ocf_member_bytes

        raw = b"\x89PNG\r\n\x1a\n\x00\r\n"  # a CRLF pair inside true binary bytes
        for name in ("OEBPS/fonts/Cardo.ttf", "OEBPS/img/cover.jpg", "OEBPS/img/p.png"):
            assert ocf_member_bytes(name, raw) == raw, name

    def test_mimetype_untouched(self):
        from scripts.core.zip_repro import ocf_member_bytes

        # no extension -> never matched (and it must stay byte-exact + STORED).
        assert ocf_member_bytes("mimetype", b"application/epub+zip") == b"application/epub+zip"

    def test_lf_only_is_a_noop(self):
        from scripts.core.zip_repro import ocf_member_bytes

        lf = b"<p>a</p>\n<p>b</p>\n"
        assert ocf_member_bytes("OEBPS/x.xhtml", lf) == lf

    def test_lone_cr_preserved(self):
        from scripts.core.zip_repro import ocf_member_bytes

        # only the exact \r\n pair collapses; a lone \r inside content survives.
        assert ocf_member_bytes("OEBPS/x.xhtml", b"a\rb\r\nc") == b"a\rb\nc"
