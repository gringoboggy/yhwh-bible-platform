"""Tests for scripts/core/* — the foundational helpers everything depends on."""

import time
from pathlib import Path

import pytest

from scripts.core import config, html_utils, notes_io


# ============================================================
# notes_io.py
# ============================================================


class TestNotesIO:
    def test_atomic_write_creates_file(self, tmp_path: Path):
        target = tmp_path / "atomic.txt"
        notes_io.atomic_write(target, "hello")
        assert target.read_text() == "hello"

    def test_atomic_write_replaces_existing(self, tmp_path: Path):
        target = tmp_path / "atomic.txt"
        target.write_text("original")
        notes_io.atomic_write(target, "replaced")
        assert target.read_text() == "replaced"

    def test_atomic_write_no_partial_state(self, tmp_path: Path):
        """No `.tmp` siblings should be left behind on success."""
        target = tmp_path / "atomic.txt"
        notes_io.atomic_write(target, "x")
        siblings = list(tmp_path.iterdir())
        assert len(siblings) == 1
        assert siblings[0].name == "atomic.txt"

    def test_ensure_backup_copies_existing(self, tmp_path: Path):
        target = tmp_path / "data.txt"
        target.write_text("v1")
        backup = notes_io.ensure_backup(target)
        assert backup is not None and backup.is_file()
        assert backup.read_text() == "v1"

    def test_ensure_backup_skips_missing(self, tmp_path: Path):
        target = tmp_path / "missing.txt"
        result = notes_io.ensure_backup(target)
        assert result is None

    def test_load_notes_from_text_parses_NOTES(self):
        src = """
NOTES = [
    (1, 1, '', 'a', 'comm', 'T', 'L.', '<p>body</p>', {}),
]
"""
        notes = notes_io.load_notes_from_text(src)
        assert isinstance(notes, list)
        assert len(notes) == 1
        assert notes[0][4] == "comm"

    def test_load_notes_from_text_handles_no_assignment(self):
        assert notes_io.load_notes_from_text("# no NOTES here") == []

    def test_load_notes_from_text_returns_None_on_syntax_error(self):
        assert notes_io.load_notes_from_text("def NOTES(") is None

    def test_load_notes_caching_invalidates_on_mtime_change(self, sample_notes_module: Path):
        """The mtime-aware LRU cache must observe file rewrites."""
        notes_io.clear_load_notes_cache()
        first = notes_io.load_notes(sample_notes_module)
        assert first is not None and len(first) == 2

        # After a short sleep (so the rewrite lands on a new observable mtime),
        # rewrite the module as a single-note version — the cache must miss.
        time.sleep(0.05)
        sample_notes_module.write_text(
            'NOTES = [(1, 1, "", "a", "comm", "T", "L.", "<p>x</p>", {})]\n',
            encoding="utf-8",
        )
        second = notes_io.load_notes(sample_notes_module)
        assert second is not None and len(second) == 1

    def test_load_notes_cache_speeds_up_warm_calls(self, sample_notes_module: Path):
        """Warm calls (cache hit) should not re-read disk."""
        notes_io.clear_load_notes_cache()
        # Cold
        notes_io.load_notes(sample_notes_module)
        info_after_cold = notes_io._load_notes_cached.cache_info()
        # Warm — call again, hit count should bump by 1
        notes_io.load_notes(sample_notes_module)
        info_after_warm = notes_io._load_notes_cached.cache_info()
        assert info_after_warm.hits == info_after_cold.hits + 1


# ============================================================
# content/notes/__init__.py — the per-book NOTES loader
# ============================================================


class TestContentNotesLoader:
    """`content.notes.load_notes(code)` must parse data, never execute it
    (RULES §7.1: notes modules look like Python but must not be executable —
    a corrupted or hostile data file must not run code)."""

    def test_load_notes_does_not_execute_module_body(self):
        """A hostile notes module that writes a sentinel file when its body
        runs must NOT have that body executed by the loader."""
        import content.notes as cn

        notes_dir = Path(cn.__file__).parent
        code = "_exec_canary"
        mod_path = notes_dir / f"{code}.py"
        canary = notes_dir / f"{code}.py.CANARY"
        canary.unlink(missing_ok=True)
        mod_path.write_text(
            "import pathlib as _p\n"
            "_p.Path(__file__ + '.CANARY').write_text('executed')\n"
            "NOTES = [('gen', 1, 1, 'comm', 'T', 'body', 'src', 'tier')]\n",
            encoding="utf-8",
        )
        try:
            result = cn.load_notes(code)
            assert not canary.exists(), "module body was executed — code ran (§7.1 violation)"
            assert result == [("gen", 1, 1, "comm", "T", "body", "src", "tier")]
        finally:
            mod_path.unlink(missing_ok=True)
            canary.unlink(missing_ok=True)

    def test_load_notes_raises_for_unknown_code(self):
        """Missing code must raise FileNotFoundError (contract preserved)."""
        import content.notes as cn

        with pytest.raises(FileNotFoundError):
            cn.load_notes("_no_such_book_code")

    def test_load_notes_returns_real_book_notes_list(self):
        """A real book loads to a non-empty list of note tuples."""
        import content.notes as cn

        notes = cn.load_notes("gen")
        assert isinstance(notes, list)
        assert len(notes) >= 1
        assert all(isinstance(n, tuple) for n in notes)

    def test_notes_corpus_has_no_invalid_escape_sequences(self):
        """No notes module may carry an invalid escape sequence (e.g. '\\ ').
        These are OCR noise from reference-corpus ingest (Kenyon/Nave/Easton),
        render a stray backslash, and break on a future Python. Guards the
        luk/mat class from recurring on the next ingest."""
        import warnings

        import content.notes as cn

        notes_dir = Path(cn.__file__).parent
        offenders = []
        for code in cn.all_codes():
            path = notes_dir / f"{code}.py"
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                compile(path.read_text(encoding="utf-8"), str(path), "exec")
                offenders += [
                    f"{code}.py:{w.lineno}: {w.message}" for w in caught if issubclass(w.category, SyntaxWarning)
                ]
        assert not offenders, "invalid escape sequences in notes corpus:\n" + "\n".join(offenders)


# ============================================================
# html_utils.py
# ============================================================


class TestHtmlUtils:
    def test_strip_tags_removes_basic_tags(self):
        assert html_utils.strip_tags("<p>hello</p>") == "hello"

    def test_strip_tags_handles_attributes(self):
        assert html_utils.strip_tags('<a href="x">y</a>') == "y"

    def test_strip_tags_handles_nested(self):
        out = html_utils.strip_tags("<p>a <strong>bold</strong> word</p>")
        assert "bold" in out and "word" in out

    def test_strip_tags_empty(self):
        assert html_utils.strip_tags("") == ""

    def test_word_count_counts_words(self):
        assert html_utils.word_count("<p>one two three</p>") == 3

    def test_word_count_strips_tags_first(self):
        assert html_utils.word_count("<p><strong>one</strong> two</p>") == 2

    def test_word_count_handles_punctuation(self):
        # Should still count "two" as a separate word despite punctuation
        wc = html_utils.word_count("<p>one, two; three.</p>")
        assert wc == 3


# ============================================================
# config.py
# ============================================================


class TestConfig:
    def test_load_books_returns_list(self):
        books = config.load_books()
        assert isinstance(books, list)
        assert len(books) > 0

    def test_get_book_known_codes(self):
        # gen + rev should always exist in a Bible canon
        gen = config.get_book("gen")
        assert gen.get("code") == "gen"
        assert gen.get("bxx", "").startswith("b")

    def test_get_book_unknown_raises(self):
        with pytest.raises(KeyError):
            config.get_book("xyz_invalid")

    def test_load_kinds_returns_list(self):
        kinds = config.load_kinds()
        assert isinstance(kinds, list)
        assert len(kinds) > 0
        # Each kind dict has at minimum a 'code' field
        assert all("code" in k for k in kinds)
        # Spot-check a couple of expected kinds
        codes = {k["code"] for k in kinds}
        assert "comm" in codes
        assert any(c.startswith("lang-") for c in codes)

    def test_load_editions_has_5_editions(self):
        eds = config.load_editions()
        ids = {e.get("id") for e in eds}
        # The 5 retail SKUs the project ships
        expected = {
            "ethiopian-tewahedo",
            "catholic-study",
            "evangelical-reformed",
            "jewish-study",
            "scholarly-academic",
        }
        assert expected.issubset(ids)


class TestCovers:
    """Phase π.4-A — per-book cover model + image metadata reader."""

    def setup_method(self):
        from scripts.core import covers

        self.mod = covers

    # ---------- encode / decode ----------

    def test_decode_handles_none_and_empty(self):
        assert self.mod.decode_book_covers(None) == {}
        assert self.mod.decode_book_covers([]) == {}
        assert self.mod.decode_book_covers({}) == {}

    def test_decode_parses_encoded_strings(self):
        raw = ["gen=covers/eth/gen.jpg", "mat=covers/eth/mat.png", "tob="]
        out = self.mod.decode_book_covers(raw)
        assert out == {
            "gen": "covers/eth/gen.jpg",
            "mat": "covers/eth/mat.png",
            "tob": "",  # explicit empty preserved
        }

    def test_decode_passes_through_dict(self):
        d = {"gen": "covers/eth/gen.jpg"}
        assert self.mod.decode_book_covers(d) == d

    def test_encode_uses_canonical_book_order(self):
        """Per CLAUDE_PROJECT_RULES.md §6.1, encoded list must be in
        books.yaml order — not alphabetical, not insertion."""
        d = {"mat": "covers/m.jpg", "tob": "covers/t.jpg", "gen": "covers/g.jpg"}
        encoded = self.mod.encode_book_covers(d)
        codes = [s.split("=", 1)[0] for s in encoded]
        assert codes == ["gen", "tob", "mat"]

    def test_encode_decode_round_trip(self):
        original = {
            "gen": "covers/eth/gen.jpg",
            "mat": "covers/eth/mat.png",
            "tob": "",
        }
        encoded = self.mod.encode_book_covers(original)
        decoded = self.mod.decode_book_covers(encoded)
        assert decoded == original

    # ---------- read_image_meta ----------

    def test_read_image_meta_missing_file_returns_none(self):
        assert self.mod.read_image_meta("does/not/exist.jpg") is None
        assert self.mod.read_image_meta("") is None

    def test_read_image_meta_real_png(self, tmp_path):
        """Real PNG header bytes must yield correct dimensions.

        We synthesize a 4x6 PNG by hand-crafting the header — no Pillow
        dependency, just the IHDR chunk every PNG must start with."""
        import struct
        import zlib

        # 8-byte signature
        sig = b"\x89PNG\r\n\x1a\n"
        # IHDR chunk: length(4) + 'IHDR' + width(4) + height(4) + 5 bytes
        ihdr_data = struct.pack(">II", 4, 6) + b"\x08\x02\x00\x00\x00"
        ihdr_crc = zlib.crc32(b"IHDR" + ihdr_data)
        ihdr = struct.pack(">I", 13) + b"IHDR" + ihdr_data + struct.pack(">I", ihdr_crc)
        # Minimal IEND
        iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", zlib.crc32(b"IEND"))
        png_bytes = sig + ihdr + iend

        p = tmp_path / "x.png"
        p.write_bytes(png_bytes)
        meta = self.mod.read_image_meta(str(p))
        assert meta is not None
        assert meta["exists"] is True
        assert meta["format"] == "png"
        assert meta["width"] == 4
        assert meta["height"] == 6
        assert meta["size_kb"] >= 0  # tiny file rounds to 0 kb

    def test_read_image_meta_real_jpeg(self, tmp_path):
        """Real JPEG SOF0 segment must yield correct dimensions.

        Hand-crafted minimal JPEG: SOI + SOF0 + EOI is enough for the
        dimension parser even though it isn't a renderable image."""
        # SOI(0xFFD8) + SOF0(0xFFC0) length=11, precision=8, height=200,
        # width=300, components=1, sample=0x11, qtable=0 + EOI(0xFFD9)
        import struct

        soi = b"\xff\xd8"
        sof_payload = (
            b"\x08"  # precision
            + struct.pack(">H", 200)  # height
            + struct.pack(">H", 300)  # width
            + b"\x01"  # 1 component
            + b"\x01\x11\x00"  # component spec
        )
        sof = b"\xff\xc0" + struct.pack(">H", 2 + len(sof_payload)) + sof_payload
        eoi = b"\xff\xd9"
        jpeg_bytes = soi + sof + eoi

        p = tmp_path / "x.jpg"
        p.write_bytes(jpeg_bytes)
        meta = self.mod.read_image_meta(str(p))
        assert meta is not None
        assert meta["format"] == "jpeg"
        assert meta["width"] == 300
        assert meta["height"] == 200

    def test_read_image_meta_unparseable_format_returns_none_dims(self, tmp_path):
        """A garbage file with .png extension still gets an entry —
        but width/height come back as None so the UI can flag it."""
        p = tmp_path / "broken.png"
        p.write_bytes(b"this is not a png")
        meta = self.mod.read_image_meta(str(p))
        assert meta is not None
        assert meta["exists"] is True
        # detect_format falls back to extension since magic bytes don't match
        assert meta["format"] in ("png", "unknown")
        # Dimensions can't be parsed
        assert meta["width"] is None
        assert meta["height"] is None

    # ---------- Phase π.4-B: upload validation ----------

    def _make_png(self, w, h):
        """Thin delegate to tests.fixtures.make_png — kept so the
        existing call sites (self._make_png(...)) keep working.
        Phase ω.0.3 hoisted the body to tests/fixtures.py."""
        from tests.fixtures import make_png

        return make_png(w, h)

    def test_validate_upload_accepts_proper_cover(self):
        png = self._make_png(1200, 1800)  # perfect 2:3
        ok, err, meta = self.mod.validate_upload_image(png)
        assert ok, err
        assert meta["format"] == "png"
        assert meta["width"] == 1200
        assert meta["height"] == 1800

    def test_validate_upload_rejects_empty_file(self):
        ok, err, _ = self.mod.validate_upload_image(b"")
        assert not ok and "empty" in err

    def test_validate_upload_rejects_oversize_file(self):
        # Larger than 10 MB cap. Make a small valid PNG header,
        # padded to >10 MB so we hit the size check first.
        big = b"\x89PNG\r\n\x1a\n" + b"\x00" * (11 * 1024 * 1024)
        ok, err, _ = self.mod.validate_upload_image(big)
        assert not ok and "too large" in err

    def test_validate_upload_rejects_undersize(self):
        png = self._make_png(400, 600)
        ok, err, _ = self.mod.validate_upload_image(png)
        assert not ok and "too small" in err

    def test_validate_upload_rejects_oversize_dimensions(self):
        png = self._make_png(5000, 7500)
        ok, err, _ = self.mod.validate_upload_image(png)
        assert not ok and "too large" in err

    def test_validate_upload_rejects_wrong_aspect(self):
        # 2000×2100 → roughly square (aspect 0.95), well outside ±20%
        # of 2:3 (0.53–0.80).
        png = self._make_png(2000, 2100)
        ok, err, _ = self.mod.validate_upload_image(png)
        assert not ok and "aspect" in err

    def test_validate_upload_rejects_unsupported_format(self):
        # Bytes that don't match PNG/JPEG/WebP magic numbers
        ok, err, _ = self.mod.validate_upload_image(b"GIF89a" + b"\x00" * 1000)
        assert not ok and "format" in err

    def test_storage_paths_match_spec(self):
        """Storage paths must match the layout specified in the
        covers scope addendum so future migrations stay deterministic."""
        assert self.mod.storage_path_for_main("catholic-study", "jpeg") == "covers/catholic-study/main.jpg"
        assert self.mod.storage_path_for_main("catholic-study", "png") == "covers/catholic-study/main.png"
        assert self.mod.storage_path_for_book("catholic-study", "gen", "webp") == "covers/catholic-study/books/gen.jpg"

    def test_read_webp_dimensions_vp8x(self):
        """Hand-crafted VP8X (extended container) WebP."""
        # RIFF header + VP8X chunk
        # 12 bytes: 'RIFF' + 4-byte size + 'WEBP'
        # Then VP8X chunk: 'VP8X' + size(10) + flags(1) + 3 reserved
        #                  + width-1 (3 LE) + height-1 (3 LE)
        riff = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP"
        # canvas is 1200x1800 → width-1 = 1199 = 0x4AF, height-1 = 1799 = 0x707
        vp8x = (
            b"VP8X"
            + b"\x0a\x00\x00\x00"  # chunk size = 10
            + b"\x00\x00\x00\x00"  # flags + reserved
            + bytes([1199 & 0xFF, (1199 >> 8) & 0xFF, (1199 >> 16) & 0xFF])
            + bytes([1799 & 0xFF, (1799 >> 8) & 0xFF, (1799 >> 16) & 0xFF])
        )
        webp = riff + vp8x
        dims = self.mod._read_webp_dimensions(webp)
        assert dims == (1200, 1800)
