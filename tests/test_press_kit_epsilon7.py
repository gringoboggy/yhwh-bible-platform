"""ε.7 — press kit auto-build pins (2026-05-11).

Month 5 #6. Per-edition cover variants + blurb persistence + ZIP
deliverable for the publisher.

Coverage:
- TestEpsilon7Constants:           SCHEMA_VERSION, PRESS_KIT_FIELDS,
  COVER_VARIANTS, FIELD_LIMITS pinned.
- TestEpsilon7LoadSave:            empty-state default, malformed JSON
  tolerance, round-trip, whitelist drops unknown entry fields.
- TestEpsilon7SetBlurbs:            merge-update semantics; empty string
  clears a field + prunes empty edition row; rejects over-limit values;
  partial update preserves untouched fields.
- TestEpsilon7ResizeCover:          PIL roundtrip — output is PNG at
  exact target dimensions; aspect preserved via letterbox; small input
  scales up; non-RGB input handled.
- TestEpsilon7BuildZip:             ZIP contains expected files; manifest
  reports has_cover correctly; placeholder text appears when blurbs
  empty; ZIP-without-cover still valid.
- TestEpsilon7ApiGet:                payload shape; cover_present flag
  reflects edition state; unknown edition still returns ok with
  edition_known=False.
- TestEpsilon7ApiSave:               happy-path persists; unknown
  edition rejected; over-limit field returns HTTP-413-style envelope;
  partial save preserves untouched fields.
- TestEpsilon7BuildZipHelper:        api_press_kit.build_press_kit_zip
  returns (filename, bytes) on success and error envelope on unknown
  edition.
- TestEpsilon7ExecTemplate:          press-kit section present; per-
  field counters wired; save + download buttons present; references
  the right endpoints.
- TestEpsilon7RouteRegistration:     GET /api/press-kit/<edition> in
  _REGEX_GET_ROUTES; PUT /api/press-kit/<edition> in _PUT_ROUTES.

Tests redirect `press_kit._press_kit_path()` to tmp so the real
content/press_kit.json is never touched.
"""

from __future__ import annotations

import io
import json
import zipfile

import pytest


def _isolate_press_kit(monkeypatch, tmp_path):
    """Redirect the press-kit state file to tmp."""
    from scripts.core import press_kit

    p = tmp_path / "press_kit.json"
    monkeypatch.setattr(press_kit, "_press_kit_path", lambda: p)
    return p


def _make_test_png(width: int = 480, height: int = 720, color: tuple = (180, 100, 50)) -> bytes:
    """Build a tiny in-memory PNG so resize tests don't depend on
    on-disk fixtures."""
    from PIL import Image

    im = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


# --------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------


class TestEpsilon7Constants:
    def test_schema_version_pinned(self):
        from scripts.core import press_kit

        assert press_kit.SCHEMA_VERSION == 1

    def test_press_kit_fields_pinned(self):
        from scripts.core import press_kit

        assert press_kit.PRESS_KIT_FIELDS == (
            "blurb_150",
            "blurb_500",
            "sample_chapter_html",
        )

    def test_cover_variants_pinned(self):
        from scripts.core import press_kit

        # Pin exact set + dimensions — downstream consumers (manifest
        # readers, archive.org auto-upload) hard-code these.
        assert press_kit.COVER_VARIANTS == {
            "thumb": (200, 300),
            "web": (600, 900),
            "social": (1080, 1080),
            "print": (2400, 3600),
        }

    def test_field_limits_present_for_every_field(self):
        from scripts.core import press_kit

        for field in press_kit.PRESS_KIT_FIELDS:
            assert field in press_kit.FIELD_LIMITS
            assert press_kit.FIELD_LIMITS[field] > 0


# --------------------------------------------------------------------
# load / save
# --------------------------------------------------------------------


class TestEpsilon7LoadSave:
    def test_empty_state_when_missing(self, monkeypatch, tmp_path):
        from scripts.core import press_kit

        _isolate_press_kit(monkeypatch, tmp_path)
        state = press_kit.load_press_kit()
        assert state == {"schema_version": 1, "editions": {}}

    def test_malformed_yields_empty(self, monkeypatch, tmp_path):
        from scripts.core import press_kit

        path = _isolate_press_kit(monkeypatch, tmp_path)
        path.write_text("not json", encoding="utf-8")
        state = press_kit.load_press_kit()
        assert state["editions"] == {}

    def test_round_trip(self, monkeypatch, tmp_path):
        from scripts.core import press_kit

        _isolate_press_kit(monkeypatch, tmp_path)
        state = {
            "editions": {
                "ed-x": {
                    "blurb_150": "Short blurb.",
                    "blurb_500": "Longer description.",
                    "sample_chapter_html": "<p>Sample.</p>",
                }
            }
        }
        press_kit.save_press_kit(state)
        round_tripped = press_kit.load_press_kit()
        assert round_tripped["editions"]["ed-x"]["blurb_150"] == "Short blurb."

    def test_save_drops_unknown_fields(self, monkeypatch, tmp_path):
        from scripts.core import press_kit

        _isolate_press_kit(monkeypatch, tmp_path)
        state = {
            "editions": {
                "ed-x": {
                    "blurb_150": "ok",
                    "rogue": "drop me",
                }
            }
        }
        press_kit.save_press_kit(state)
        round_tripped = press_kit.load_press_kit()
        entry = round_tripped["editions"]["ed-x"]
        assert "rogue" not in entry
        assert entry["blurb_150"] == "ok"


# --------------------------------------------------------------------
# set_blurbs
# --------------------------------------------------------------------


class TestEpsilon7SetBlurbs:
    def test_writes_partial_update(self, monkeypatch, tmp_path):
        from scripts.core import press_kit

        _isolate_press_kit(monkeypatch, tmp_path)
        entry = press_kit.set_blurbs("ed-x", blurb_150="A short one.")
        assert entry["blurb_150"] == "A short one."
        # blurb_500 + sample_chapter_html absent from state.
        assert "blurb_500" not in entry

    def test_merge_preserves_untouched_fields(self, monkeypatch, tmp_path):
        from scripts.core import press_kit

        _isolate_press_kit(monkeypatch, tmp_path)
        press_kit.set_blurbs("ed-x", blurb_150="A", blurb_500="B")
        # Update only blurb_500.
        entry = press_kit.set_blurbs("ed-x", blurb_500="C")
        assert entry["blurb_150"] == "A"  # preserved
        assert entry["blurb_500"] == "C"  # updated

    def test_empty_string_clears_field(self, monkeypatch, tmp_path):
        from scripts.core import press_kit

        _isolate_press_kit(monkeypatch, tmp_path)
        press_kit.set_blurbs("ed-x", blurb_150="A")
        entry = press_kit.set_blurbs("ed-x", blurb_150="")
        assert "blurb_150" not in entry

    def test_clearing_last_field_prunes_edition(self, monkeypatch, tmp_path):
        from scripts.core import press_kit

        _isolate_press_kit(monkeypatch, tmp_path)
        press_kit.set_blurbs("ed-x", blurb_150="A")
        press_kit.set_blurbs("ed-x", blurb_150="")
        state = press_kit.load_press_kit()
        assert "ed-x" not in state["editions"]

    def test_rejects_oversized_field(self, monkeypatch, tmp_path):
        from scripts.core import press_kit

        _isolate_press_kit(monkeypatch, tmp_path)
        too_long = "x" * (press_kit.FIELD_LIMITS["blurb_150"] + 1)
        with pytest.raises(ValueError, match="blurb_150 exceeds"):
            press_kit.set_blurbs("ed-x", blurb_150=too_long)


# --------------------------------------------------------------------
# resize_cover
# --------------------------------------------------------------------


class TestEpsilon7ResizeCover:
    def test_resizes_to_exact_dimensions(self, tmp_path):
        from PIL import Image

        from scripts.core import press_kit

        src = tmp_path / "src.png"
        src.write_bytes(_make_test_png(480, 720))
        out = press_kit.resize_cover(src, (600, 900))
        # Output is PNG at exactly the target canvas size.
        with Image.open(io.BytesIO(out)) as im:
            assert im.size == (600, 900)
            assert im.format == "PNG"

    def test_letterbox_preserves_aspect(self, tmp_path):
        # A 100x100 (square) source resized into a 200x300 (portrait)
        # canvas should be 200x200 of content + 50px white strip top
        # and bottom. We pin that the centre pixel is the source color
        # and edge pixels are white.
        from PIL import Image

        from scripts.core import press_kit

        src = tmp_path / "src.png"
        src.write_bytes(_make_test_png(100, 100, color=(255, 0, 0)))
        out = press_kit.resize_cover(src, (200, 300))
        with Image.open(io.BytesIO(out)) as im:
            assert im.size == (200, 300)
            # Centre pixel is the source red (allow lossy resampling).
            r, g, b = im.getpixel((100, 150))[:3]
            assert r > 200 and g < 50 and b < 50
            # Top edge is white letterbox.
            r2, g2, b2 = im.getpixel((100, 5))[:3]
            assert r2 > 240 and g2 > 240 and b2 > 240

    def test_rgba_source_flattens_to_white(self, tmp_path):
        from PIL import Image

        from scripts.core import press_kit

        src = tmp_path / "src.png"
        im = Image.new("RGBA", (100, 100), (255, 0, 0, 0))  # transparent
        im.save(src, format="PNG")
        out = press_kit.resize_cover(src, (50, 50))
        with Image.open(io.BytesIO(out)) as im2:
            assert im2.mode == "RGB"
            r, g, b = im2.getpixel((25, 25))
            # Transparent flattens to white.
            assert r > 240 and g > 240 and b > 240


# --------------------------------------------------------------------
# build_zip
# --------------------------------------------------------------------


class TestEpsilon7BuildZip:
    def _edition_with_cover(self, tmp_path) -> dict:
        # Build a content/-relative cover_image path that resolves
        # via the press_kit module's content-root helper.
        from scripts.core import press_kit

        content_root = press_kit._content_root()
        covers_dir = content_root / "covers" / "ed-test"
        covers_dir.mkdir(parents=True, exist_ok=True)
        cover_path = covers_dir / "main.png"
        cover_path.write_bytes(_make_test_png(480, 720))
        return {
            "id": "ed-test",
            "title": "Test Edition",
            "cover_image": "covers/ed-test/main.png",
        }, cover_path

    def test_zip_contains_blurbs_and_manifest(self, monkeypatch, tmp_path):
        from scripts.core import press_kit

        _isolate_press_kit(monkeypatch, tmp_path)
        edition = {"id": "ed-x", "title": "X", "cover_image": ""}
        blurbs = {"blurb_150": "Short.", "blurb_500": "Longer.", "sample_chapter_html": "<p>Hi</p>"}
        zip_bytes = press_kit.build_zip(edition, blurbs)
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = set(zf.namelist())
            assert "manifest.json" in names
            assert "blurb_150.txt" in names
            assert "blurb_500.txt" in names
            assert "sample_chapter.html" in names
            assert zf.read("blurb_150.txt").decode() == "Short."

    def test_zip_with_no_cover_records_has_cover_false(self, monkeypatch, tmp_path):
        from scripts.core import press_kit

        _isolate_press_kit(monkeypatch, tmp_path)
        edition = {"id": "ed-x", "title": "X", "cover_image": ""}
        zip_bytes = press_kit.build_zip(edition, {})
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            manifest = json.loads(zf.read("manifest.json"))
            assert manifest["cover"]["has_cover"] is False
            # No cover files in the ZIP.
            assert not any(n.startswith("covers/") for n in zf.namelist())

    def test_zip_with_cover_includes_all_variants(self, monkeypatch, tmp_path):
        # Use a tmp content root so we don't touch the real
        # content/covers/.
        from scripts.core import press_kit

        _isolate_press_kit(monkeypatch, tmp_path)

        fake_content = tmp_path / "content"
        fake_content.mkdir()
        cover_dir = fake_content / "covers" / "ed-test"
        cover_dir.mkdir(parents=True)
        (cover_dir / "main.png").write_bytes(_make_test_png(480, 720))

        monkeypatch.setattr(press_kit, "_content_root", lambda: fake_content)

        edition = {"id": "ed-test", "title": "Test", "cover_image": "covers/ed-test/main.png"}
        zip_bytes = press_kit.build_zip(edition, {})
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = set(zf.namelist())
            for variant in press_kit.COVER_VARIANTS:
                assert f"covers/main_{variant}.png" in names
            manifest = json.loads(zf.read("manifest.json"))
            assert manifest["cover"]["has_cover"] is True
            for variant in press_kit.COVER_VARIANTS:
                assert variant in manifest["cover"]["variants"]

    def test_zip_uses_placeholders_when_blurbs_empty(self, monkeypatch, tmp_path):
        from scripts.core import press_kit

        _isolate_press_kit(monkeypatch, tmp_path)
        edition = {"id": "ed-x", "title": "X", "cover_image": ""}
        zip_bytes = press_kit.build_zip(edition, {})
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            body = zf.read("blurb_150.txt").decode()
            assert "not yet provided" in body

    def test_manifest_contents_lists_every_file(self, monkeypatch, tmp_path):
        from scripts.core import press_kit

        _isolate_press_kit(monkeypatch, tmp_path)
        edition = {"id": "ed-x", "title": "X", "cover_image": ""}
        zip_bytes = press_kit.build_zip(edition, {"blurb_150": "A"})
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            manifest = json.loads(zf.read("manifest.json"))
            for name in zf.namelist():
                assert name in manifest["contents"], f"manifest missing {name!r}"


# --------------------------------------------------------------------
# API endpoints
# --------------------------------------------------------------------


class TestEpsilon7ApiGet:
    def _real_edition_id(self):
        from scripts.core import config

        eds = config.load_editions()
        assert eds, "test depends on at least one real edition existing"
        return str(eds[0]["id"])

    def test_payload_shape(self, monkeypatch, tmp_path):
        from scripts.api.press_kit import api_press_kit_get

        _isolate_press_kit(monkeypatch, tmp_path)
        ed_id = self._real_edition_id()
        result = api_press_kit_get(ed_id)
        assert result["status"] == "ok"
        for key in ("edition_id", "edition_known", "blurbs", "cover_present", "limits", "fields"):
            assert key in result, f"missing {key!r}"
        assert set(result["blurbs"].keys()) == {"blurb_150", "blurb_500", "sample_chapter_html"}

    def test_unknown_edition_still_returns_ok(self, monkeypatch, tmp_path):
        from scripts.api.press_kit import api_press_kit_get

        _isolate_press_kit(monkeypatch, tmp_path)
        result = api_press_kit_get("def-not-real")
        assert result["status"] == "ok"
        assert result["edition_known"] is False
        # Blurbs are empty, cover_present is False, but the call
        # doesn't error — the UI uses this to show a "create one
        # first" message rather than an HTTP error.
        assert result["cover_present"] is False


class TestEpsilon7ApiSave:
    def _real_edition_id(self):
        from scripts.core import config

        return str(config.load_editions()[0]["id"])

    def test_happy_path_persists(self, monkeypatch, tmp_path):
        from scripts.api.press_kit import api_press_kit_save
        from scripts.core import press_kit

        _isolate_press_kit(monkeypatch, tmp_path)
        ed_id = self._real_edition_id()
        result = api_press_kit_save(ed_id, {"blurb_150": "Hello."})
        assert result["ok"] is True
        # Persisted on disk.
        state = press_kit.load_press_kit()
        assert state["editions"][ed_id]["blurb_150"] == "Hello."

    def test_unknown_edition_rejected(self, monkeypatch, tmp_path):
        from scripts.api.press_kit import api_press_kit_save

        _isolate_press_kit(monkeypatch, tmp_path)
        result = api_press_kit_save("def-not-real", {"blurb_150": "X"})
        assert result["ok"] is False
        assert result["error"] == "unknown_edition"

    def test_over_limit_returns_413_envelope(self, monkeypatch, tmp_path):
        from scripts.api.press_kit import api_press_kit_save
        from scripts.core import press_kit

        _isolate_press_kit(monkeypatch, tmp_path)
        ed_id = self._real_edition_id()
        oversized = "x" * (press_kit.FIELD_LIMITS["blurb_150"] + 1)
        result = api_press_kit_save(ed_id, {"blurb_150": oversized})
        assert result["status"] == "error"
        assert result["code"] == "field_too_long"
        assert result["http"] == 413

    def test_partial_save_preserves_untouched_fields(self, monkeypatch, tmp_path):
        from scripts.api.press_kit import api_press_kit_save
        from scripts.core import press_kit

        _isolate_press_kit(monkeypatch, tmp_path)
        ed_id = self._real_edition_id()
        api_press_kit_save(ed_id, {"blurb_150": "A", "blurb_500": "B"})
        # Update only blurb_500; expect blurb_150 preserved.
        api_press_kit_save(ed_id, {"blurb_500": "C"})
        state = press_kit.load_press_kit()
        assert state["editions"][ed_id]["blurb_150"] == "A"
        assert state["editions"][ed_id]["blurb_500"] == "C"


class TestEpsilon7BuildZipHelper:
    def test_returns_filename_and_bytes_on_success(self, monkeypatch, tmp_path):
        from scripts.api.press_kit import build_press_kit_zip
        from scripts.core import config

        _isolate_press_kit(monkeypatch, tmp_path)
        ed_id = str(config.load_editions()[0]["id"])
        result = build_press_kit_zip(ed_id)
        assert isinstance(result, tuple)
        filename, body = result
        assert filename.startswith("press-kit-")
        assert filename.endswith(".zip")
        # Body is a valid ZIP.
        with zipfile.ZipFile(io.BytesIO(body)) as zf:
            assert "manifest.json" in zf.namelist()

    def test_unknown_edition_returns_error_envelope(self, monkeypatch, tmp_path):
        from scripts.api.press_kit import build_press_kit_zip

        _isolate_press_kit(monkeypatch, tmp_path)
        result = build_press_kit_zip("def-not-real")
        assert isinstance(result, dict)
        assert result["status"] == "error"
        assert result["code"] == "unknown_edition"


# --------------------------------------------------------------------
# Template
# --------------------------------------------------------------------


class TestEpsilon7ExecTemplate:
    @classmethod
    def setup_class(cls):
        from scripts.templates.exec import EXEC_HTML

        cls.html = EXEC_HTML

    def test_press_kit_section_present(self):
        assert 'id="press-kit-section"' in self.html
        assert 'id="press-kit-edition"' in self.html
        assert 'id="press-kit-save"' in self.html
        assert 'id="press-kit-download"' in self.html

    def test_three_textareas_present(self):
        for field in ("blurb_150", "blurb_500", "sample_chapter_html"):
            assert f'id="press-kit-{field}"' in self.html
            assert f'data-counter="{field}"' in self.html
            assert f'data-limit="{field}"' in self.html

    def test_js_helpers_present(self):
        for fn in (
            "loadPressKitEditions",
            "loadPressKitFor",
            "savePressKit",
            "downloadPressKit",
            "updatePressKitCounter",
        ):
            assert fn in self.html, f"missing {fn!r}"

    def test_endpoints_referenced(self):
        assert "/api/press-kit/" in self.html
        # Download URL is constructed by string concat; pin the suffix.
        assert "/download" in self.html


# --------------------------------------------------------------------
# Route registration
# --------------------------------------------------------------------


class TestEpsilon7RouteRegistration:
    def test_get_route_in_regex_table(self):

        from scripts import web

        for regex, handler in web._REGEX_GET_ROUTES:
            if regex.match("/api/press-kit/ed-x"):
                assert handler is web.api_press_kit_get
                return
        pytest.fail("no GET route matches /api/press-kit/<edition>")

    def test_put_route_in_put_table(self):
        import re

        from scripts import web

        for regex, handler in web._PUT_ROUTES:
            if regex.match("/api/press-kit/ed-x"):
                # Calling the lambda with a no-op payload + unknown
                # edition exercises the wiring without depending on
                # the actual edition list.
                result = handler(re.match(regex.pattern, "/api/press-kit/def-not-real"), {})
                assert result["ok"] is False
                assert result["error"] == "unknown_edition"
                return
        pytest.fail("no PUT route matches /api/press-kit/<edition>")

    def test_download_route_helper_present(self):
        # The /download path lives in the legacy cascade (it returns
        # bytes); pin that the helper used to dispatch it is exported
        # from scripts.web.
        from scripts import web

        assert hasattr(web, "build_press_kit_zip")

    def test_send_zip_helper_exists(self):
        # _send_zip lives on the request handler class — search the
        # source rather than instantiating the handler (which needs
        # a socket).
        from pathlib import Path

        repo = Path(__file__).resolve().parent.parent
        src = (repo / "scripts" / "web.py").read_text(encoding="utf-8")
        assert "def _send_zip(" in src, "_send_zip helper missing from web.py"
        assert 'Content-Type", "application/zip"' in src, "_send_zip doesn't send application/zip"
        assert "Content-Disposition" in src, "_send_zip missing attachment header"
