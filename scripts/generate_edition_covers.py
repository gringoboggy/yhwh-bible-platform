"""Generate the 9 edition main cover JPGs by compositing the edition title
onto the existing `content/covers/templates/` family.

ω.38 (C6 closure — 2026-05-13); title-only recenter (Wave 2 — 2026-05-25).

The audit (`AUDIT_2026-05-12-C`) flagged C6: `editions.yaml` declares
`cover_image: "covers/<edition-id>.jpg"` for every edition, but those
files did not exist — the wizard's BUILD step emitted EPUBs whose cover
slot resolved to a missing path. This script generates the 9 main covers
from the 25-template library (5 design families × 5 colors) by compositing
each edition's title onto a tradition-appropriate template.

Per spec §4.6 (user-confirmed 2026-05-24) the cover is TITLE-ONLY: the
former subtitle/short-title line and the "Bible Builder" publisher mark
were dropped (that descriptive detail now lives on the "About this Edition"
front-matter page), leaving a single centered title block that places
cleanly across every design.

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

The colour-to-tradition mapping is editorially defensible; publishers can
swap to a bespoke cover via `api_save_edition_meta` (the `cover_image`
field accepts any path under `content/covers/`).

Run: `python scripts/generate_edition_covers.py`
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parent.parent
COVERS_DIR = REPO_ROOT / "content" / "covers"
TEMPLATES_DIR = COVERS_DIR / "templates"

# Edition → (template stem, title). The title's newline-separated lines
# render as a centered block. Cover is title-only (see module docstring), so
# no subtitle/short-title or publisher mark is carried here.
EDITIONS: list[tuple[str, str, str]] = [
    ("ethiopian-tewahedo", "05_missal_central_red", "The Ethiopian Tewahedo\nStudy Bible"),
    ("catholic-study", "02_classical_corner_navy", "The Catholic Study Bible\nEthiopian Edition"),
    ("evangelical-reformed", "03_beadline_black", "The Reformed\nStudy Bible"),
    ("jewish-study", "02_classical_corner_brown", "The Jewish\nStudy Tanakh"),
    ("scholarly-academic", "03_beadline_forest", "The Annotated\nEthiopian Bible"),
    ("eastern-orthodox", "01_ornate_leafy_red", "The Eastern Orthodox\nStudy Bible"),
    ("anglican-bcp", "03_beadline_navy", "The Anglican Study Bible\nBCP Edition"),
    ("lutheran-confessional", "02_classical_corner_black", "The Lutheran\nConfessional Study Bible"),
    ("coptic-orthodox", "01_ornate_leafy_brown", "The Coptic Orthodox\nStudy Bible"),
]


def title_for_edition(edition_id: str) -> str:
    """The cover title for ``edition_id`` — the bespoke (often multi-line)
    title from ``EDITIONS`` when the edition is one of the nine mapped above,
    else the edition's configured ``title`` from editions.yaml, else the id.

    The /customize cover picker uses this to recompose a chosen template so
    re-picking an edition's factory template reproduces its exact cover."""
    for ed_id, _stem, title in EDITIONS:
        if ed_id == edition_id:
            return title
    from scripts.core import config

    ed = config.editions_by_id().get(edition_id, {})
    return ed.get("title") or edition_id


# Final cover dimensions — match the existing _book_defaults pattern.
# Templates are 1792×2688; downscaling to 1024×1536 keeps file size
# reasonable and matches what `epubcheck` expects for EPUB covers.
FINAL_WIDTH = 1024
FINAL_HEIGHT = 1536

# Title typography: warm cream/parchment reads against the dark template
# backgrounds and harmonises with their gold accents; a soft drop-shadow
# adds depth + legibility.
TITLE_COLOR = (245, 230, 195)  # warm cream
TITLE_SHADOW = (0, 0, 0, 130)
# Title-only covers center a single block. Its vertical midpoint sits in the
# upper third — above any central template ornament, below the top border —
# so 1-, 2-, and 3-line titles all balance identically.
TITLE_CENTER_Y = 540
TITLE_LINE_SPACING = 18
# Auto-fit: a long title shrinks (TITLE_FONT_MAX→MIN in 4pt steps) until its
# widest line fits within TITLE_MAX_WIDTH, so it never runs past the cover
# edges. The margin keeps the block clear of the side ornaments most templates
# carry. Short titles keep the full size, so well-fitting covers are unchanged.
TITLE_FONT_MAX = 72
TITLE_FONT_MIN = 28
# Generous side margin so the title sits in the central "safe zone" (~71% of
# the width) well clear of the templates' decorative border art — the longest
# edition titles otherwise crowd the ornamental frame (user-reported 2026-05-25).
TITLE_MARGIN_X = 150
TITLE_MAX_WIDTH = FINAL_WIDTH - 2 * TITLE_MARGIN_X

# Font path — Times New Roman bold ships with Windows.
FONT_TITLE_PATH = r"C:\Windows\Fonts\timesbd.ttf"


def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a Windows truetype font; fall back to PIL's default at the
    requested size if the path resolves elsewhere."""
    p = Path(path)
    if p.is_file():
        return ImageFont.truetype(str(p), size=size)
    # Cross-platform fallback — won't match the Windows aesthetic but
    # produces a readable cover.
    return ImageFont.load_default(size=size)


def _fit_title_font(title: str, draw: ImageDraw.ImageDraw) -> ImageFont.FreeTypeFont:
    """Return the largest title font (TITLE_FONT_MAX→MIN in 4pt steps) whose
    widest line fits within ``TITLE_MAX_WIDTH`` — so a long edition title shrinks
    to stay clear of the cover edges instead of overrunning them. Falls back to
    ``TITLE_FONT_MIN`` if even that overflows (degrade legibly, never overrun)."""
    size = TITLE_FONT_MAX
    while size > TITLE_FONT_MIN:
        font = _load_font(FONT_TITLE_PATH, size)
        bbox = draw.multiline_textbbox((0, 0), title, font=font, align="center", spacing=TITLE_LINE_SPACING)
        if (bbox[2] - bbox[0]) <= TITLE_MAX_WIDTH:
            return font
        size -= 4
    return _load_font(FONT_TITLE_PATH, TITLE_FONT_MIN)


def _compose_cover(template_stem: str, title: str) -> Image.Image:
    """Composite the TITLE ONLY onto a template; return the RGB cover at the
    final dimensions. The title is a single block centered horizontally and
    vertically about ``TITLE_CENTER_Y`` — measured with PIL's multiline bbox so
    1-, 2-, and 3-line titles balance identically (no per-line bearing drift)."""
    template_path = TEMPLATES_DIR / f"{template_stem}.png"
    if not template_path.is_file():
        raise FileNotFoundError(f"template missing: {template_path}")

    base = Image.open(template_path).convert("RGB")
    # Resize to final dimensions BEFORE compositing so the title is laid out
    # in the final coordinate space.
    base = base.resize((FINAL_WIDTH, FINAL_HEIGHT), Image.LANCZOS)
    draw = ImageDraw.Draw(base, "RGBA")
    font = _fit_title_font(title, draw)

    # Measure the whole block, then place its top-left so the block centers at
    # (FINAL_WIDTH/2, TITLE_CENTER_Y). Subtracting bbox[0]/bbox[1] removes the
    # font's left/top bearing, so the centering is exact.
    bbox = draw.multiline_textbbox((0, 0), title, font=font, align="center", spacing=TITLE_LINE_SPACING)
    block_w, block_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (FINAL_WIDTH - block_w) // 2 - bbox[0]
    y = TITLE_CENTER_Y - block_h // 2 - bbox[1]

    draw.multiline_text((x + 4, y + 4), title, font=font, fill=TITLE_SHADOW, align="center", spacing=TITLE_LINE_SPACING)
    draw.multiline_text((x, y), title, font=font, fill=TITLE_COLOR, align="center", spacing=TITLE_LINE_SPACING)
    return base


def _generate_one(edition_id: str, template_stem: str, title: str) -> Path:
    """Compose the title-only cover and write it to ``content/covers/<id>.jpg``."""
    base = _compose_cover(template_stem, title)
    out_path = COVERS_DIR / f"{edition_id}.jpg"
    base.save(out_path, "JPEG", quality=90, optimize=True)
    return out_path


def generate_all() -> list[Path]:
    """Generate every edition's main cover JPG; return the paths produced."""
    out: list[Path] = []
    for edition_id, template_stem, title in EDITIONS:
        out.append(_generate_one(edition_id, template_stem, title))
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
