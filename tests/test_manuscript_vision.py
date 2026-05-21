"""Tests for scripts/core/manuscript_vision.py.

The vision-offload client + compact crop/encode helper move manuscript
image bytes OUT of the agent/harness buffer — the root-cause fix for the
2026-05-20/21 OOM crash class (a single image-heavy review agent at 117k
tokens carried ~30-60 MB of upscaled-PNG bytes in the parent buffer).

Two invariants the crash taught us, pinned here:
  1. crop_and_encode NEVER upscales (Claude downsamples to <=1568px anyway,
     so the old 4-8x LANCZOS upscale in _p2_crop.py was pure buffer bloat).
  2. crop_and_encode caps the longest edge at MAX_IMAGE_EDGE so no single
     block can blow the budget regardless of source folio resolution.

Tests inject a stub completion_fn (mirrors AnthropicXrefClient) so no
network or API key is needed.
"""

import base64
import io
import json

import pytest

pytest.importorskip("PIL")  # Pillow is an accepted optional dep (§10)
from PIL import Image  # noqa: E402


def _decode_block(block):
    """Decode an Anthropic image content block back to (media_type, PIL.Image)."""
    assert block["type"] == "image", block
    src = block["source"]
    assert src["type"] == "base64", src
    raw = base64.b64decode(src["data"])
    return src["media_type"], Image.open(io.BytesIO(raw))


class TestCropAndEncode:
    def test_returns_anthropic_image_block(self):
        from scripts.core.manuscript_vision import crop_and_encode

        img = Image.new("RGB", (2000, 1500), (200, 180, 160))
        block = crop_and_encode(img, (100, 100, 700, 400))
        media_type, decoded = _decode_block(block)
        assert media_type == "image/jpeg"
        assert decoded.size[0] > 0 and decoded.size[1] > 0

    def test_downscales_large_crop_to_max_edge(self):
        from scripts.core.manuscript_vision import MAX_IMAGE_EDGE, crop_and_encode

        img = Image.new("RGB", (5000, 4000), (10, 20, 30))
        block = crop_and_encode(img, (0, 0, 4000, 3000))  # 4000x3000 region
        _, decoded = _decode_block(block)
        assert max(decoded.size) == MAX_IMAGE_EDGE
        # aspect ratio preserved (4:3 -> 1568x1176)
        assert decoded.size == (MAX_IMAGE_EDGE, int(round(MAX_IMAGE_EDGE * 3 / 4)))

    def test_does_not_upscale_small_crop(self):
        from scripts.core.manuscript_vision import crop_and_encode

        img = Image.new("RGB", (2000, 1500))
        block = crop_and_encode(img, (0, 0, 300, 120))  # well under the cap
        _, decoded = _decode_block(block)
        assert decoded.size == (300, 120)  # unchanged — never upscales

    def test_clamps_box_to_image_bounds(self):
        from scripts.core.manuscript_vision import crop_and_encode

        img = Image.new("RGB", (400, 300))
        # box overruns right/bottom; must clamp to (0,0,400,300) not pad black
        block = crop_and_encode(img, (0, 0, 9999, 9999))
        _, decoded = _decode_block(block)
        assert decoded.size == (400, 300)

    def test_accepts_path(self, tmp_path):
        from scripts.core.manuscript_vision import crop_and_encode

        p = tmp_path / "folio.jpg"
        Image.new("RGB", (800, 600), (123, 45, 67)).save(p, "JPEG")
        block = crop_and_encode(str(p), (0, 0, 400, 300))
        media_type, decoded = _decode_block(block)
        assert media_type == "image/jpeg"
        assert decoded.size == (400, 300)


class TestAnthropicVisionClient:
    def test_analyze_passes_blocks_and_returns_parsed(self):
        from scripts.core.manuscript_vision import AnthropicVisionClient

        captured = {}

        def stub(system_prompt, content, *, model, output_schema, max_tokens):
            captured.update(system=system_prompt, content=content, model=model)
            return {"defects": [], "ok": True}

        client = AnthropicVisionClient(model="claude-test", completion_fn=stub)
        blocks = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": "AAAA",
                },
            }
        ]
        out = client.analyze("SYS", "look at this", blocks, output_schema={"type": "object"})
        assert out == {"defects": [], "ok": True}
        assert captured["model"] == "claude-test"
        assert captured["system"] == "SYS"
        # image blocks come first, the text instruction last
        assert captured["content"][0]["type"] == "image"
        assert captured["content"][-1] == {"type": "text", "text": "look at this"}

    def test_analyze_defensive_on_bad_output(self):
        from scripts.core.manuscript_vision import AnthropicVisionClient

        def stub(system_prompt, content, *, model, output_schema, max_tokens):
            raise json.JSONDecodeError("boom", "", 0)

        client = AnthropicVisionClient(model="m", completion_fn=stub)
        assert client.analyze("s", "t", [], output_schema={"type": "object"}) == {}

    def test_analyze_non_dict_becomes_empty(self):
        from scripts.core.manuscript_vision import AnthropicVisionClient

        client = AnthropicVisionClient(model="m", completion_fn=lambda *a, **k: ["not", "a", "dict"])
        assert client.analyze("s", "t", [], output_schema={"type": "object"}) == {}

    def test_requires_key_or_stub(self, monkeypatch):
        from scripts.core.manuscript_vision import AnthropicVisionClient
        from scripts.core.sources import SourceMissingError

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(SourceMissingError):
            AnthropicVisionClient()  # no key, no stub -> fail at construction

    def test_last_usage_none_with_stub(self):
        from scripts.core.manuscript_vision import AnthropicVisionClient

        client = AnthropicVisionClient(model="m", completion_fn=lambda *a, **k: {})
        client.analyze("s", "t", [], output_schema={"type": "object"})
        assert client.last_usage is None  # only the real SDK path sets telemetry
