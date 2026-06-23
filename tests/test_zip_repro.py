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
        stored = reproducible_zipinfo("mimetype", stored=True)
        assert stored.compress_type == zipfile.ZIP_STORED

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
