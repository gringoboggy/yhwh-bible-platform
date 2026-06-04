"""Generate the 9 edition main cover JPGs by compositing the cover text
onto the existing `content/covers/templates/` family.

ω.38 (C6 closure — 2026-05-13); title-only recenter (Wave 2 — 2026-05-25);
σ.2 HOLY-BIBLE + subtitle redesign (2026-06-04).

The audit (`AUDIT_2026-05-12-C`) flagged C6: `editions.yaml` declares
`cover_image: "covers/<edition-id>.jpg"` for every edition, but those
files did not exist — the wizard's BUILD step emitted EPUBs whose cover
slot resolved to a missing path. This script generates the 9 main covers
from the 25-template library (5 design families × 5 colors) by compositing
each edition's cover text onto a tradition-appropriate template.

σ.2 (2026-06-04) — the cover now reads a FIXED main title (default
"HOLY BIBLE") plus a small builder-chosen subtitle (the edition's
``display_name``, falling back to its ``title``). This fixes the
user-reported overflow bug: the old single full-title composite shrank the
font 72→28pt and then *returned 28pt without re-checking fit*, so long
titles still ran past the gold border. The new ``fit_text_block``
wrap-then-shrink fitter GUARANTEES every drawn line stays within the safe
width — even a pathological single unbreakable word is hard-broken to fit.

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

# Edition → factory cover-template stem. σ.2 dropped the hard-coded title
# strings (the cover text now comes from editions.yaml via
# ``cover_text_for_edition``); this map is kept ONLY so batch regen + the
# /customize "reset to factory template" path know each edition's default
# template when editions.yaml hasn't recorded a ``cover_template`` yet. The
# colour-to-tradition rationale lives in the module docstring above.
EDITION_TEMPLATES: dict[str, str] = {
    "ethiopian-tewahedo": "05_missal_central_red",
    "catholic-study": "02_classical_corner_navy",
    "evangelical-reformed": "03_beadline_black",
    "jewish-study": "02_classical_corner_brown",
    "scholarly-academic": "03_beadline_forest",
    "eastern-orthodox": "01_ornate_leafy_red",
    "anglican-bcp": "03_beadline_navy",
    "lutheran-confessional": "02_classical_corner_black",
    "coptic-orthodox": "01_ornate_leafy_brown",
}

# The standard editions, in declaration order, for batch regeneration.
STANDARD_EDITION_IDS: list[str] = list(EDITION_TEMPLATES.keys())


def template_for_edition(edition_id: str) -> str:
    """The cover template stem for ``edition_id`` — the edition's recorded
    ``cover_template`` from editions.yaml when set, else its factory default
    from ``EDITION_TEMPLATES``, else the project-wide default template."""
    from scripts.core import config

    ed = config.editions_by_id().get(edition_id, {})
    stem = str(ed.get("cover_template") or "").strip()
    if stem:
        return stem
    return EDITION_TEMPLATES.get(edition_id, "03_beadline_navy")


def cover_text_for_edition(edition_id: str) -> tuple[str, str]:
    """(main_title, subtitle). main_title defaults to 'HOLY BIBLE'; subtitle is
    the builder's display_name (falls back to the edition title; '' → no
    subtitle).

    The /customize cover picker uses this to recompose a chosen template so
    re-picking an edition's factory template reproduces its exact cover."""
    from scripts.core import config

    ed = config.editions_by_id().get(edition_id, {})
    main = (ed.get("cover_main_title") or "HOLY BIBLE").strip()
    subtitle = ed.get("display_name")
    if subtitle is None:
        subtitle = ed.get("title", "")
    return main, subtitle.strip()


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
# The cover text — a big "HOLY BIBLE" main block, a short centered rule, then a
# smaller subtitle block — is centered about TITLE_CENTER_Y, which sits in the
# upper third (above any central template ornament, below the top border).
TITLE_CENTER_Y = 540
TITLE_LINE_SPACING = 18
# Main-title font range (HOLY BIBLE fits at the max on every template; a custom
# cover_main_title that is longer shrinks via fit_text_block).
TITLE_FONT_MAX = 72
TITLE_FONT_MIN = 28
# Subtitle font range — deliberately smaller so the subtitle reads as a
# secondary line beneath the main title.
SUBTITLE_FONT_MAX = 40
SUBTITLE_FONT_MIN = 22
SUBTITLE_COLOR = (235, 222, 190)  # slightly softer cream than the main title
# Vertical gaps (in the final 1024×1536 coordinate space).
RULE_GAP = 26  # main block ↔ rule
SUBTITLE_GAP = 26  # rule ↔ subtitle block
RULE_HALF_WIDTH = 130  # the centered hairline rule extends ±this from center
RULE_THICKNESS = 2
# Generous side margin so the text sits in the central "safe zone" (~71% of the
# width) well clear of the templates' decorative border art — long titles
# otherwise crowd the ornamental frame (user-reported 2026-05-25 / 2026-06-04).
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


def _line_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> float:
    """Rendered width of a single line, measured the same way the overflow test
    asserts it (``draw.textbbox(...)[2]``) so the fitter's guarantee is exact."""
    return draw.textbbox((0, 0), text, font=font)[2]


def _hard_break_word(draw: ImageDraw.ImageDraw, word: str, max_width: float, font: ImageFont.FreeTypeFont) -> list[str]:
    """Split a single over-long word into the fewest chunks that each fit
    ``max_width`` at ``font``. Guarantees every returned chunk fits (a lone
    character that still exceeds max_width is kept on its own line — degrade
    legibly, never claim a fit we don't have)."""
    chunks: list[str] = []
    cur = ""
    for ch in word:
        candidate = cur + ch
        if cur and _line_width(draw, candidate, font) > max_width:
            chunks.append(cur)
            cur = ch
        else:
            cur = candidate
    if cur:
        chunks.append(cur)
    return chunks


def _wrap_at_size(
    draw: ImageDraw.ImageDraw, text: str, max_width: float, font: ImageFont.FreeTypeFont
) -> tuple[list[str], bool]:
    """Greedily word-wrap ``text`` at ``font`` into lines ≤ ``max_width``.

    Returns ``(lines, all_fit)`` where ``all_fit`` is True only when every line
    fits without hard-breaking a word. The caller uses ``all_fit`` to decide
    whether to keep shrinking; at ``min_pt`` it falls back to hard-breaking so
    the final lines always fit regardless."""
    lines: list[str] = []
    cur = ""
    all_fit = True
    for word in text.split():
        candidate = f"{cur} {word}".strip()
        if not cur:
            # First word on this line. If it alone overflows, this size can't
            # fit it by wrapping — signal not-all-fit.
            if _line_width(draw, word, font) > max_width:
                all_fit = False
            cur = word
        elif _line_width(draw, candidate, font) <= max_width:
            cur = candidate
        else:
            lines.append(cur)
            cur = word
            if _line_width(draw, word, font) > max_width:
                all_fit = False
    if cur:
        lines.append(cur)
    return lines, all_fit


def fit_text_block(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: float,
    *,
    max_pt: int,
    min_pt: int,
) -> tuple[list[str], ImageFont.FreeTypeFont]:
    """Wrap-then-shrink text fitter with a HARD guarantee: every returned line's
    rendered width is ≤ ``max_width``.

    For each size from ``max_pt`` down to ``min_pt`` (1pt steps), greedily
    word-wrap ``text`` into lines that each fit ``max_width``; the first size at
    which every line fits wins. If even ``min_pt`` can't fit some word by
    wrapping alone, that word is hard-broken at ``min_pt`` so every final line
    still fits. Empty/blank text returns ``([], font@max_pt)``.

    This replaces the old ``_fit_title_font``, whose bug was returning the
    minimum size *without re-checking fit* — letting long titles overrun the
    cover's gold border (the reported defect)."""
    text = (text or "").strip()
    if not text:
        return [], _load_font(FONT_TITLE_PATH, max_pt)

    for size in range(max_pt, min_pt - 1, -1):
        font = _load_font(FONT_TITLE_PATH, size)
        lines, all_fit = _wrap_at_size(draw, text, max_width, font)
        if all_fit:
            return lines, font

    # Floor reached: wrap at min_pt, then hard-break any line still too wide so
    # the guarantee holds even for a pathological single unbreakable word.
    font = _load_font(FONT_TITLE_PATH, min_pt)
    raw_lines, _ = _wrap_at_size(draw, text, max_width, font)
    final: list[str] = []
    for line in raw_lines:
        if _line_width(draw, line, font) <= max_width:
            final.append(line)
        else:
            final.extend(_hard_break_word(draw, line, max_width, font))
    return final, font


def _draw_centered_block(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    top_y: int,
    fill: tuple[int, int, int],
) -> int:
    """Draw ``lines`` horizontally centered, stacked from ``top_y`` down, each
    with the soft drop-shadow. Returns the y just below the block."""
    ascent, descent = font.getmetrics()
    line_h = ascent + descent
    y = top_y
    for line in lines:
        w = _line_width(draw, line, font)
        x = (FINAL_WIDTH - w) // 2
        draw.text((x + 3, y + 3), line, font=font, fill=TITLE_SHADOW)
        draw.text((x, y), line, font=font, fill=fill)
        y += line_h + TITLE_LINE_SPACING
    if lines:
        y -= TITLE_LINE_SPACING  # no trailing gap after the last line
    return y


def _block_height(font: ImageFont.FreeTypeFont, n_lines: int) -> int:
    """Total stacked height of an ``n_lines`` block at ``font`` (matches
    ``_draw_centered_block``'s layout)."""
    if n_lines <= 0:
        return 0
    ascent, descent = font.getmetrics()
    line_h = ascent + descent
    return n_lines * line_h + (n_lines - 1) * TITLE_LINE_SPACING


def _compose_cover(template_stem: str, main_title: str, subtitle: str = "") -> Image.Image:
    """Composite the cover text — a large ``main_title`` block, a short centered
    rule, then a smaller ``subtitle`` block — onto a template; return the RGB
    cover at the final dimensions.

    The whole stack is vertically centered about ``TITLE_CENTER_Y``. Both blocks
    are laid out with ``fit_text_block`` so NO line can run past the safe width
    (the σ.2 overflow fix). An empty ``subtitle`` draws the main title only (no
    rule, no subtitle region)."""
    template_path = TEMPLATES_DIR / f"{template_stem}.png"
    if not template_path.is_file():
        raise FileNotFoundError(f"template missing: {template_path}")

    base = Image.open(template_path).convert("RGB")
    # Resize to final dimensions BEFORE compositing so the text is laid out in
    # the final coordinate space.
    base = base.resize((FINAL_WIDTH, FINAL_HEIGHT), Image.LANCZOS)
    draw = ImageDraw.Draw(base, "RGBA")

    main_lines, main_font = fit_text_block(
        draw, main_title, TITLE_MAX_WIDTH, max_pt=TITLE_FONT_MAX, min_pt=TITLE_FONT_MIN
    )
    subtitle = (subtitle or "").strip()
    sub_lines: list[str] = []
    sub_font: ImageFont.FreeTypeFont | None = None
    if subtitle:
        sub_lines, sub_font = fit_text_block(
            draw, subtitle, TITLE_MAX_WIDTH, max_pt=SUBTITLE_FONT_MAX, min_pt=SUBTITLE_FONT_MIN
        )

    # Total stack height, then place its top so it centers at TITLE_CENTER_Y.
    main_h = _block_height(main_font, len(main_lines))
    total_h = main_h
    if sub_lines and sub_font is not None:
        sub_h = _block_height(sub_font, len(sub_lines))
        total_h += RULE_GAP + RULE_THICKNESS + SUBTITLE_GAP + sub_h

    top_y = TITLE_CENTER_Y - total_h // 2

    y = _draw_centered_block(draw, main_lines, main_font, top_y, TITLE_COLOR)

    if sub_lines and sub_font is not None:
        rule_y = y + RULE_GAP
        cx = FINAL_WIDTH // 2
        draw.rectangle(
            (cx - RULE_HALF_WIDTH, rule_y, cx + RULE_HALF_WIDTH, rule_y + RULE_THICKNESS - 1),
            fill=TITLE_COLOR,
        )
        sub_top = rule_y + RULE_THICKNESS + SUBTITLE_GAP
        _draw_centered_block(draw, sub_lines, sub_font, sub_top, SUBTITLE_COLOR)

    return base


def _generate_one(edition_id: str, template_stem: str | None = None) -> Path:
    """Compose ``edition_id``'s cover (HOLY BIBLE + its subtitle) and write it to
    ``content/covers/<id>.jpg``. ``template_stem`` defaults to the edition's
    recorded/factory template."""
    stem = template_stem or template_for_edition(edition_id)
    main_title, subtitle = cover_text_for_edition(edition_id)
    base = _compose_cover(stem, main_title, subtitle)
    out_path = COVERS_DIR / f"{edition_id}.jpg"
    base.save(out_path, "JPEG", quality=90, optimize=True)
    return out_path


def generate_all() -> list[Path]:
    """Generate every standard edition's main cover JPG; return the paths
    produced (the 2 standalone Bibles get covers in a separate σ.5 phase)."""
    return [_generate_one(edition_id) for edition_id in STANDARD_EDITION_IDS]


def main(argv: list[str] | None = None) -> int:
    paths = generate_all()
    print(f"Generated {len(paths)} edition cover JPGs:")
    for p in paths:
        size = p.stat().st_size
        print(f"  {p.relative_to(REPO_ROOT)}  ({size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
