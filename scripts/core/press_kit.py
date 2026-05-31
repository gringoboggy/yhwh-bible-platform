"""ε.7 — press kit auto-build (2026-05-11).

Month 5 #6. Per-edition press kit ZIP: cover variants (4 standard
sizes) + 150-word blurb + 500-word description + sample chapter HTML
+ manifest.

**Use case**: the publisher submits one ZIP per edition to a reviewer,
journalist, retail buyer, or catalogue site. Today this means
hand-resizing the cover 4 times, copy-pasting blurbs from a notes
app, and PDF-ing a sample chapter. After ε.7, "Download press kit"
on /exec produces a complete deliverable.

**Storage** — `content/press_kit.json` (machine-managed sparse JSON,
sibling to `content/distribution.json` and `content/sources/*.json`).
Schema mirrors distribution.py exactly so the persistence + atomic-
write + backup pattern is uniform:

    {
      "schema_version": 1,
      "editions": {
        "<edition_id>": {
          "blurb_150": "...",
          "blurb_500": "...",
          "sample_chapter_html": "..."
        }
      }
    }

**Cover variants** (PIL-driven, LANCZOS resampling, white-canvas
letterbox to preserve aspect ratio):

| Variant | Pixels       | Use case                               |
|---------|--------------|----------------------------------------|
| thumb   |  200 ×  300  | Catalogue rows, list views             |
| web     |  600 ×  900  | Storefront product page                |
| social  | 1080 × 1080  | Instagram / Twitter square             |
| print   | 2400 × 3600  | print/archival interior minimum; hi-res |

Variants are PNG (lossless) — re-encoding from the source preserves
text clarity better than re-saving JPEGs.

**Public API**:
    SCHEMA_VERSION                                  current schema version
    PRESS_KIT_FIELDS                                whitelisted entry keys
    COVER_VARIANTS                                  {variant_id: (w, h)}
    FIELD_LIMITS                                    {field: max_chars}
    load_press_kit()                                full state dict
    save_press_kit(state)                           atomic write
    get_blurbs(state, edition_id)                   per-edition dict
    set_blurbs(edition_id, **fields)                write helper
    resize_cover(src_path, target_size)             bytes (PNG)
    build_zip(edition, blurbs)                      bytes (the ZIP)

Foundation for ο.4 (archive.org auto-upload composes `build_zip`
output for the upload payload), ε.5 (quarterly report PDF can embed
the press-kit blurbs), and any future "send to reviewer" workflow.
"""

from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from . import notes_io


SCHEMA_VERSION = 1

PRESS_KIT_FIELDS: tuple[str, ...] = (
    "blurb_150",
    "blurb_500",
    "sample_chapter_html",
)

# Per-field maximum character count. 150-word blurb at average 6 chars
# per word + spaces ≈ 1050 chars, rounded up to 1200 for generous
# punctuation. 500-word blurb ≈ 3500. Sample chapter is generous
# because publishers may include 1-2 short chapters of formatted HTML.
FIELD_LIMITS: dict[str, int] = {
    "blurb_150": 1200,
    "blurb_500": 3500,
    "sample_chapter_html": 20000,
}

# Variants in deliberate render order (thumb → web → social → print)
# — smallest first so manifests sort intuitively.
COVER_VARIANTS: dict[str, tuple[int, int]] = {
    "thumb": (200, 300),
    "web": (600, 900),
    "social": (1080, 1080),
    "print": (2400, 3600),
}


_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _press_kit_path() -> Path:
    """Canonical state-file path. Function (not constant) so tests can
    monkeypatch via a single attribute — mirrors event_log + distribution."""
    return _REPO_ROOT / "content" / "press_kit.json"


def _now_iso() -> str:
    """ISO-8601 UTC timestamp — identical format to event_log + distribution."""
    return datetime.now(timezone.utc).isoformat()


def _empty_state() -> dict:
    return {"schema_version": SCHEMA_VERSION, "editions": {}}


# --------------------------------------------------------------------
# State persistence — mirrors distribution.py's load/save discipline.
# --------------------------------------------------------------------


def load_press_kit() -> dict:
    """Load the press-kit state. Returns empty state on missing or
    malformed file."""
    path = _press_kit_path()
    if not path.is_file():
        return _empty_state()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return _empty_state()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return _empty_state()
    if not isinstance(data, dict):
        return _empty_state()
    if "schema_version" not in data:
        data["schema_version"] = SCHEMA_VERSION
    if "editions" not in data or not isinstance(data["editions"], dict):
        data["editions"] = {}
    return data


def save_press_kit(state: dict) -> Path:
    """Persist the state atomically. Whitelist-filters entry fields so
    stale clients can't sneak unknown keys onto disk."""
    cleaned: dict = {"schema_version": SCHEMA_VERSION, "editions": {}}
    editions = state.get("editions", {}) if isinstance(state, dict) else {}
    if isinstance(editions, dict):
        for ed_id, fields in editions.items():
            if not isinstance(fields, dict):
                continue
            ed_id_str = str(ed_id)
            cleaned_fields = {k: str(fields[k]) for k in PRESS_KIT_FIELDS if k in fields}
            if cleaned_fields:
                cleaned["editions"][ed_id_str] = cleaned_fields

    path = _press_kit_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        notes_io.ensure_backup(path)
    text = json.dumps(cleaned, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    notes_io.atomic_write(path, text)
    return path


def get_blurbs(state: dict, edition_id: str) -> dict:
    """Return the per-edition blurbs dict (empty when nothing saved)."""
    eds = state.get("editions", {}) if isinstance(state, dict) else {}
    entry = eds.get(edition_id, {}) if isinstance(eds, dict) else {}
    if not isinstance(entry, dict):
        return {}
    return {k: str(entry.get(k, "")) for k in PRESS_KIT_FIELDS}


def set_blurbs(
    edition_id: str,
    *,
    blurb_150: str | None = None,
    blurb_500: str | None = None,
    sample_chapter_html: str | None = None,
) -> dict:
    """Merge-update the blurbs for one edition. Returns the entry that
    was written (only the fields actually present after merge).

    Field length is enforced via `FIELD_LIMITS` — values longer than
    the limit raise `ValueError` (api layer translates to HTTP 413).
    """
    updates: dict[str, str] = {}
    if blurb_150 is not None:
        updates["blurb_150"] = str(blurb_150)
    if blurb_500 is not None:
        updates["blurb_500"] = str(blurb_500)
    if sample_chapter_html is not None:
        updates["sample_chapter_html"] = str(sample_chapter_html)

    for field, value in updates.items():
        limit = FIELD_LIMITS.get(field)
        if limit is not None and len(value) > limit:
            raise ValueError(f"{field} exceeds {limit}-character limit (got {len(value)})")

    state = load_press_kit()
    editions = state.setdefault("editions", {})
    entry = dict(editions.get(edition_id, {}))
    entry.update(updates)
    # Drop empty strings on save so the JSON stays clean. The publisher
    # can wipe a field by passing "".
    cleaned_entry = {k: v for k, v in entry.items() if v}
    if cleaned_entry:
        editions[edition_id] = cleaned_entry
    else:
        editions.pop(edition_id, None)
    save_press_kit(state)
    return cleaned_entry


# --------------------------------------------------------------------
# Cover resizer.
# --------------------------------------------------------------------


def resize_cover(src_path: Path, target_size: tuple[int, int]) -> bytes:
    """Resize an image to fit inside `target_size` (W, H) with aspect
    ratio preserved, centred on a white canvas of exactly target_size.
    Returns PNG bytes.

    Lazy PIL import so the module stays importable in environments
    that don't bundle Pillow (the resize call will raise then, but
    blurb persistence + manifest still work).
    """
    from PIL import Image

    # Pillow 9.1+ moved the resampling enum to Image.Resampling.LANCZOS;
    # the bare Image.LANCZOS still works at runtime but mypy doesn't
    # recognise it as a module attribute. Prefer the new name and fall
    # back if running against an older Pillow.
    resample = getattr(Image, "Resampling", None)
    lanczos = resample.LANCZOS if resample is not None else Image.LANCZOS  # type: ignore[attr-defined]

    target_w, target_h = target_size
    with Image.open(src_path) as raw_im:
        # Convert any palette / CMYK / RGBA source to RGB on a white
        # canvas so PNGs render predictably across viewers. The
        # `working` rebind avoids the mypy ImageFile→Image variance
        # complaint that came from reassigning the `with` target.
        if raw_im.mode != "RGB":
            base = Image.new("RGB", raw_im.size, (255, 255, 255))
            if raw_im.mode == "RGBA":
                base.paste(raw_im, mask=raw_im.split()[-1])
            else:
                base.paste(raw_im.convert("RGB"))
            working = base
        else:
            working = raw_im.copy()
        # Fit inside the target box (don't crop).
        working.thumbnail((target_w, target_h), lanczos)
        canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))
        off_x = (target_w - working.width) // 2
        off_y = (target_h - working.height) // 2
        canvas.paste(working, (off_x, off_y))
        buf = io.BytesIO()
        canvas.save(buf, format="PNG", optimize=True)
        return buf.getvalue()


# --------------------------------------------------------------------
# ZIP builder.
# --------------------------------------------------------------------


def build_zip(edition: dict, blurbs: dict, *, now: datetime | None = None) -> bytes:
    """Build the press-kit ZIP for one edition. Returns bytes.

    `edition` is the dict from `config.load_editions()`. `blurbs` is
    the dict from `get_blurbs(state, edition_id)` (possibly empty —
    missing blurbs render as placeholder text in the ZIP so the
    publisher knows what to fill in).

    Contents (variant set + paths pinned for downstream consumers):

        manifest.json          — top-level summary
        blurb_150.txt          — 150-word blurb (or placeholder)
        blurb_500.txt          — 500-word blurb (or placeholder)
        sample_chapter.html    — sample chapter (or placeholder)
        covers/main_thumb.png  — 200 × 300
        covers/main_web.png    — 600 × 900
        covers/main_social.png — 1080 × 1080
        covers/main_print.png  — 2400 × 3600

    Missing cover → the `covers/` directory is empty and the manifest
    records `has_cover: false`. ZIP is still valid.
    """
    edition_id = str(edition.get("id", ""))
    title = str(edition.get("title", edition_id))
    generated_at = (now or datetime.now(timezone.utc)).isoformat()
    from . import covers

    cover_path = covers.resolve_cover_path(edition)

    contents: list[str] = []
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Blurbs (always present — placeholder when missing so the
        # downstream consumer always sees a file).
        for field, default in (
            ("blurb_150", "[150-word blurb not yet provided]"),
            ("blurb_500", "[500-word description not yet provided]"),
            ("sample_chapter_html", "<p>[sample chapter not yet provided]</p>"),
        ):
            name = "sample_chapter.html" if field == "sample_chapter_html" else f"{field}.txt"
            body = (blurbs.get(field) or "").strip() or default
            zf.writestr(name, body)
            contents.append(name)

        # Covers (skipped silently when missing).
        cover_meta: dict = {"has_cover": False, "variants": {}}
        if cover_path is not None:
            cover_meta["has_cover"] = True
            for variant_id, size in COVER_VARIANTS.items():
                try:
                    png_bytes = resize_cover(cover_path, size)
                except Exception as e:
                    # Recording the failure in the manifest is more
                    # useful than crashing the whole ZIP build.
                    cover_meta["variants"][variant_id] = {"error": str(e), "size": list(size)}
                    continue
                arcname = f"covers/main_{variant_id}.png"
                zf.writestr(arcname, png_bytes)
                contents.append(arcname)
                cover_meta["variants"][variant_id] = {
                    "size": list(size),
                    "bytes": len(png_bytes),
                    "arcname": arcname,
                }

        # Manifest comes last so its `contents` field reflects the full
        # set of files actually written.
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "edition_id": edition_id,
            "title": title,
            "generated_at": generated_at,
            "contents": sorted(contents) + ["manifest.json"],
            "cover": cover_meta,
            "blurb_fields_present": [k for k in PRESS_KIT_FIELDS if (blurbs.get(k) or "").strip()],
        }
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

    return buf.getvalue()
