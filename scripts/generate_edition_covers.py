"""Generate 9 edition main cover JPGs by compositing typography onto
the existing `content/covers/templates/` family.

ω.38 (C6 closure — 2026-05-13).

The audit (`AUDIT_2026-05-12-C`) flagged C6: `editions.yaml` declares
`cover_image: "covers/<edition-id>.jpg"` for every edition, but those
files did not exist — the wizard's BUILD step emitted EPUBs whose
cover slot resolved to a missing path. This script generates the
missing 9 main covers using the existing 25-template library
(5 design families × 5 colors) by compositing each edition's
title + short-title + publisher mark onto a tradition-appropriate
template.

Mapping rationale:

- ethiopian-tewahedo  → 05_missal_central_red    (Tewahedo red/gold)
- catholic-study      → 02_classical_corner_navy (traditional Catholic)
- evangelical-reformed→ 03_beadline_black        (Reformed restraint)
- jewish-study        → 02_classical_corner_brown(parchment / Tanakh)
- scholarly-academic  → 03_beadline_forest       (academic dignity)
- eastern-orthodox    → 01_ornate_leafy_red      (Byzantine red/gold)
- anglican-bcp        → 03_beadline_navy         (Anglican BCP blue)
- lutheran-confessional→02_classical_corner_black(Lutheran black)
- coptic-orthodox     → 01_ornate_leafy_brown    (Coptic earth tones)

Note: 04_minimal_lines_* templates carry a central jewel/cross
ornament that visually clashes with subtitle text; avoid for
editions that need a subtitle line below the title.

The colour-to-tradition mapping is editorially defensible; publishers
can swap to a bespoke cover via `api_save_edition_meta` (the
`cover_image` field accepts any path under `content/covers/`).

Run: `python scripts/generate_edition_covers.py`
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parent.parent
COVERS_DIR = REPO_ROOT / "content" / "covers"
TEMPLATES_DIR = COVERS_DIR / "templates"

# Edition → (template stem, title, short_title, publisher mark).
# Title is the full marketing title; short_title is the spine/badge
# variant. Publisher mark sits at the bottom — "Bible Builder" by
# default; per-edition overrides could come from editions.yaml in a
# future iteration.
EDITIONS: list[tuple[str, str, str, str, str]] = [
    (
        "ethiopian-tewahedo",
        "05_missal_central_red",
        "The Ethiopian Tewahedo\nStudy Bible",
        "Tewahedo Study Bible",
        "Bible Builder",
    ),
    (
        "catholic-study",
        "02_classical_corner_navy",
        "The Catholic Study Bible\nEthiopian Edition",
        "Catholic Study Bible",
        "Bible Builder",
    ),
    (
        "evangelical-reformed",
        "03_beadline_black",
        "The Reformed\nStudy Bible",
        "Reformed Study Bible",
        "Bible Builder",
    ),
    (
        "jewish-study",
        "02_classical_corner_brown",
        "The Jewish\nStudy Tanakh",
        "Jewish Study Tanakh",
        "Bible Builder",
    ),
    (
        "scholarly-academic",
        "03_beadline_forest",
        "The Annotated\nEthiopian Bible",
        "Scholar's Edition",
        "Bible Builder",
    ),
    (
        "eastern-orthodox",
        "01_ornate_leafy_red",
        "The Eastern Orthodox\nStudy Bible",
        "Orthodox Study Bible",
        "Bible Builder",
    ),
    (
        "anglican-bcp",
        "03_beadline_navy",
        "The Anglican Study Bible\nBCP Edition",
        "Anglican BCP",
        "Bible Builder",
    ),
    (
        "lutheran-confessional",
        "02_classical_corner_black",
        "The Lutheran\nConfessional Study Bible",
        "Lutheran Confessional",
        "Bible Builder",
    ),
    (
        "coptic-orthodox",
        "01_ornate_leafy_brown",
        "The Coptic Orthodox\nStudy Bible",
        "Coptic Study Bible",
        "Bible Builder",
    ),
]

# Final cover dimensions — match the existing _book_defaults pattern.
# Templates are 1792×2688; downscaling to 1024×1536 keeps file size
# reasonable and matches what `epubcheck` expects for EPUB covers.
FINAL_WIDTH = 1024
FINAL_HEIGHT = 1536

# Title typography: warm cream/parchment so it reads against the
# dark backgrounds and harmonises with the gold accents on each
# template. Slight transparency in shadow gives subtle depth.
TITLE_COLOR = (245, 230, 195)  # warm cream
TITLE_SHADOW = (0, 0, 0, 130)
PUBLISHER_COLOR = (210, 195, 165)  # muted gold

# Font paths — Times New Roman + Georgia ship with Windows.
FONT_TITLE_PATH = r"C:\Windows\Fonts\timesbd.ttf"
FONT_SUBTITLE_PATH = r"C:\Windows\Fonts\times.ttf"
FONT_PUBLISHER_PATH = r"C:\Windows\Fonts\georgia.ttf"


def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a Windows truetype font; fall back to PIL's default at the
    requested size if the path resolves elsewhere."""
    p = Path(path)
    if p.is_file():
        return ImageFont.truetype(str(p), size=size)
    # Cross-platform fallback — won't match Windows aesthetic but
    # produces a readable cover.
    return ImageFont.load_default(size=size)


def _draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    *,
    center_x: int,
    y: int,
    fill: tuple[int, int, int],
    shadow: tuple[int, int, int, int] | None = None,
    line_spacing: int = 14,
) -> int:
    """Draw multiline text centered on `center_x`, top-anchored at `y`.
    Returns the final y-coordinate after the last line."""
    lines = text.split("\n")
    cy = y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        line_h = bbox[3] - bbox[1]
        x = center_x - line_w // 2
        if shadow is not None:
            # Composite shadow via a separate transparent layer
            shadow_layer = Image.new("RGBA", (line_w + 30, line_h + 30), (0, 0, 0, 0))
            sd = ImageDraw.Draw(shadow_layer)
            sd.text((15, 15), line, font=font, fill=shadow)
            # Drop-shadow offset
            draw._image.paste(  # type: ignore[attr-defined]
                shadow_layer, (x - 15 + 4, cy - 15 + 4), shadow_layer
            )
        draw.text((x, cy), line, font=font, fill=fill)
        cy += line_h + line_spacing
    return cy


def _generate_one(edition_id: str, template_stem: str, title: str, short_title: str, publisher_mark: str) -> Path:
    """Composite typography onto one template; write the result to
    `content/covers/<edition-id>.jpg`."""
    template_path = TEMPLATES_DIR / f"{template_stem}.png"
    if not template_path.is_file():
        raise FileNotFoundError(f"template missing: {template_path}")

    base = Image.open(template_path).convert("RGB")
    # Resize template to the final dimensions BEFORE compositing so
    # the typography is laid out in the final coordinate space.
    base = base.resize((FINAL_WIDTH, FINAL_HEIGHT), Image.LANCZOS)
    draw = ImageDraw.Draw(base, "RGBA")

    # Title fits the top-third of the inner rectangle. The templates
    # have ~12% borders, so the inner area runs roughly y=180 to
    # y=1380 (out of 1536). Title centerline sits ~y=520.
    font_title = _load_font(FONT_TITLE_PATH, 72)
    font_subtitle = _load_font(FONT_SUBTITLE_PATH, 44)
    font_publisher = _load_font(FONT_PUBLISHER_PATH, 32)

    title_y = 460
    end_y = _draw_centered_text(
        draw,
        title,
        font_title,
        center_x=FINAL_WIDTH // 2,
        y=title_y,
        fill=TITLE_COLOR,
        shadow=TITLE_SHADOW,
        line_spacing=18,
    )

    # Subtitle / short-title sits beneath the title with a small gap.
    subtitle_y = end_y + 50
    _draw_centered_text(
        draw,
        short_title,
        font_subtitle,
        center_x=FINAL_WIDTH // 2,
        y=subtitle_y,
        fill=PUBLISHER_COLOR,
        line_spacing=12,
    )

    # Publisher mark at the bottom — small, restrained, italic-ish
    # spacing via the Georgia regular face.
    bbox = draw.textbbox((0, 0), publisher_mark, font=font_publisher)
    pub_w = bbox[2] - bbox[0]
    pub_y = FINAL_HEIGHT - 200
    draw.text(
        ((FINAL_WIDTH - pub_w) // 2, pub_y),
        publisher_mark,
        font=font_publisher,
        fill=PUBLISHER_COLOR,
    )

    out_path = COVERS_DIR / f"{edition_id}.jpg"
    base.save(out_path, "JPEG", quality=90, optimize=True)
    return out_path


def generate_all() -> list[Path]:
    """Generate every edition's main cover JPG; return the list of
    paths produced (in the order shipped to disk)."""
    out: list[Path] = []
    for edition_id, template_stem, title, short_title, mark in EDITIONS:
        path = _generate_one(edition_id, template_stem, title, short_title, mark)
        out.append(path)
    return out


def main(argv: list[str] | None = None) -> int:
    paths = generate_all()
    print(f"Generated {len(paths)} edition cover JPGs:")
    for p in paths:
        size = p.stat().st_size
        print(f"  {p.relative_to(REPO_ROOT)}  ({size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
