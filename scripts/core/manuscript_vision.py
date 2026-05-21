"""Vision-backed manuscript client + compact crop/encode helper.

This module is the root-cause fix for the 2026-05-20/21 OOM crash class.
Manuscript transcription (C-2) and review (R-rounds) were performed by
*agents* that read LANCZOS-upscaled PNG crops; every image accumulated in
the parent harness buffer for the full agent duration. A single review
agent at ~117k tokens carried ~30-60 MB of image bytes there and the Rust
allocator panicked (`memory allocation of 17919552 bytes failed`).

Running the same vision work from a *standalone script* via the Anthropic
SDK keeps every image byte in the script's own process — the bytes go
straight to the API and never enter the agent/harness buffer. The script
writes only text artifacts (witness JSON, review markdown, defect JSON),
which are cheap to read back.

Two hard invariants the crash taught us, enforced by ``crop_and_encode``:

1. **Never upscale.** Claude's vision pipeline downsamples any image whose
   longest edge exceeds ~1568 px, so the old 4-8x LANCZOS upscale in
   ``_p2_crop.py`` produced megabytes of bytes the model immediately threw
   away. We crop at native resolution and only ever scale *down*.
2. **Cap the longest edge** at :data:`MAX_IMAGE_EDGE` so no single content
   block can blow the budget regardless of source folio resolution.

Construction mirrors :class:`scripts.core.sources.AnthropicXrefClient`:
an injected ``completion_fn`` makes the client fully testable with no
network or API key; the default fn uses the shared cached SDK client with
prompt caching on the system prompt and ``last_usage`` telemetry.

Optional deps (per CLAUDE_PROJECT_RULES §10, both already accepted by the
manuscript tooling): ``Pillow`` for cropping, ``anthropic`` for the real
SDK path. Both are imported lazily so this module loads without them.
"""

from __future__ import annotations

import base64
import io
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Optional

from . import sources

# Claude downsamples vision inputs whose longest edge exceeds ~1568 px.
# Sending anything larger is pure buffer waste — the exact mistake that
# turned a one-agent review into an OOM. Crop helpers cap to this.
MAX_IMAGE_EDGE = 1568

# Paleographic Ge'ez transcription/review is the project's highest-stakes
# vision task — default to the strongest model. The at-scale drivers expose
# --model so a cheaper survey pass (e.g. claude-sonnet-4-6) can override.
DEFAULT_VISION_MODEL = "claude-opus-4-7"

# 1-hour TTL on the cached system prompt. Same trade as the χ-AI-* clients:
# the 2x cache-write premium amortizes after a few reads, and a per-chapter
# vision pass issues enough calls to stay warm.
VISION_CACHE_TTL = "1h"

_JPEG_MEDIA_TYPE = "image/jpeg"


@lru_cache(maxsize=8)
def load_image(path: str):
    """Open *path* as an RGB ``PIL.Image`` (cached).

    Folio masters are immutable, so repeated per-verse crops of one folio
    decode the JPEG only once. ``maxsize=8`` covers a chapter that spans a
    handful of folios without holding the whole codex in memory.
    """
    from PIL import Image  # lazy: Pillow is an optional dep

    return Image.open(path).convert("RGB")


def crop_and_encode(
    image: Any,
    box: tuple[int, int, int, int],
    *,
    max_edge: int = MAX_IMAGE_EDGE,
    quality: int = 85,
) -> dict:
    """Crop *box* from *image* and return an Anthropic image content block.

    Parameters
    ----------
    image
        A ``PIL.Image`` or a path to a folio image. Paths go through the
        cached :func:`load_image`.
    box
        ``(left, top, right, bottom)`` in source pixels. Clamped to the
        image bounds so an overrun never pads black bytes.
    max_edge
        Longest output edge. The crop is scaled *down* to fit; it is
        **never upscaled** (a sub-``max_edge`` crop passes through at
        native size).
    quality
        JPEG quality (1-95). 85 is visually lossless for glyph-level
        paleography at a fraction of PNG's bytes.

    Returns
    -------
    ``{"type": "image", "source": {"type": "base64",
    "media_type": "image/jpeg", "data": "<b64>"}}`` — ready to drop into a
    ``messages`` content list.
    """
    from PIL import Image  # lazy: Pillow is an optional dep

    if isinstance(image, (str, Path)):
        img = load_image(str(image))
    else:
        img = image if image.mode == "RGB" else image.convert("RGB")

    w, h = img.size
    left, top, right, bottom = box
    # Clamp to bounds — PIL.crop() otherwise fills out-of-range with black,
    # inflating bytes for no information.
    left = max(0, min(left, w))
    top = max(0, min(top, h))
    right = max(left, min(right, w))
    bottom = max(top, min(bottom, h))

    crop = img.crop((left, top, right, bottom))

    longest = max(crop.size)
    if longest > max_edge:
        scale = max_edge / longest
        new_size = (
            max(1, int(round(crop.size[0] * scale))),
            max(1, int(round(crop.size[1] * scale))),
        )
        crop = crop.resize(new_size, Image.LANCZOS)
    # else: leave as-is. Never upscale.

    buf = io.BytesIO()
    crop.save(buf, format="JPEG", quality=quality)
    data = base64.b64encode(buf.getvalue()).decode("ascii")
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": _JPEG_MEDIA_TYPE,
            "data": data,
        },
    }


class AnthropicVisionClient:
    """LLM vision client for manuscript transcription/review.

    Sibling of :class:`scripts.core.sources.AnthropicXrefClient`: same
    construction contract (raises :class:`~scripts.core.sources.SourceMissingError`
    when neither a real SDK + API key nor an injected ``completion_fn`` is
    available), same prompt-cache discipline, same ``last_usage`` telemetry.

    The injected ``completion_fn(system_prompt, content, *, model,
    output_schema, max_tokens)`` returns the parsed completion as a dict.
    Tests pass a stub so no network call is made.
    """

    def __init__(
        self,
        *,
        model: str = DEFAULT_VISION_MODEL,
        completion_fn: Optional[Callable] = None,
    ) -> None:
        self.model = model
        if completion_fn is not None:
            self._completion_fn = completion_fn
        else:
            # Validate real-SDK preconditions at construction, not first call.
            if not os.environ.get("ANTHROPIC_API_KEY"):
                raise sources.SourceMissingError(
                    "ANTHROPIC_API_KEY environment variable not set. "
                    "Set it (export ANTHROPIC_API_KEY=...) or pass an "
                    "injected completion_fn."
                )
            try:
                import anthropic  # noqa: F401
            except ImportError as e:
                raise sources.SourceMissingError(
                    "The 'anthropic' Python SDK is not installed. "
                    "Install it (pip install anthropic) or pass an "
                    "injected completion_fn."
                ) from e
            self._completion_fn = self._default_completion_fn

        # Telemetry from the most recent _default_completion_fn call. Stub
        # completion_fns leave this None; the real SDK path populates it so
        # a driver can verify cache hits before paying for a long run.
        self.last_usage: Optional[dict] = None

    @property
    def attribution(self) -> str:
        return f"Claude AI vision ({self.model}, Anthropic, 2026); reviewer-curated."

    def analyze(
        self,
        system_prompt: str,
        text: str,
        image_blocks: list[dict],
        *,
        output_schema: dict,
        max_tokens: int = 4096,
    ) -> dict:
        """Send *image_blocks* + *text* to the model under *system_prompt*.

        Images precede the text instruction in the content list (the model
        attends to the images, then follows the instruction). Returns the
        parsed structured-output dict, or ``{}`` on any defensively-handled
        failure (SDK error after retries, malformed JSON, non-dict output).
        Programming errors propagate so tests surface them.
        """
        content: list[dict] = list(image_blocks)
        content.append({"type": "text", "text": text})
        try:
            parsed = self._completion_fn(
                system_prompt,
                content,
                model=self.model,
                output_schema=output_schema,
                max_tokens=max_tokens,
            )
        except (ValueError, OSError):
            # json.JSONDecodeError subclasses ValueError.
            return {}
        except Exception as e:
            # Anthropic SDK exceptions are dynamically-named APIError
            # subclasses; can't import at module top without breaking the
            # no-dep path, so match by module name.
            if type(e).__module__.startswith("anthropic"):
                return {}
            raise
        return parsed if isinstance(parsed, dict) else {}

    def _default_completion_fn(
        self,
        system_prompt: str,
        content: list[dict],
        *,
        model: str,
        output_schema: dict,
        max_tokens: int,
    ) -> dict:
        """Real SDK call. Only reached when the constructor confirmed the
        SDK + API key are present.

        Prompt-caches the system prompt (1h TTL) so per-verse calls amortize
        the topology/protocol prefix, forces structured JSON via
        ``output_config.format``, and reuses the module-level cached client
        from :mod:`scripts.core.sources`. Populates ``self.last_usage``.
        """
        client = sources._anthropic_client()
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {
                        "type": "ephemeral",
                        "ttl": VISION_CACHE_TTL,
                    },
                }
            ],
            messages=[{"role": "user", "content": content}],
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": output_schema,
                },
            },
        )
        usage = response.usage
        self.last_usage = {
            "input_tokens": getattr(usage, "input_tokens", 0),
            "output_tokens": getattr(usage, "output_tokens", 0),
            "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", 0),
            "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0),
            "request_id": getattr(response, "_request_id", None),
        }
        text = next(
            (block.text for block in response.content if block.type == "text"),
            "",
        )
        return json.loads(text)
