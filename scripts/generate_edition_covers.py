"""Generate the 9 edition main cover JPGs by compositing the cover text
onto the existing `content/covers/templates/` family.

ω.38 (C6 closure — 2026-05-13); title-only recenter (Wave 2 — 2026-05-25);
σ.2 HOLY-BIBLE + subtitle redesign (2026-06-04).

The audit (`AUDIT_2026-05-12-C`) flagged C6: `editions.yaml` declares
`cover_image: "covers/<edition-id>.jpg"` for every edition, but those
files did not exist — the wizard's BUILD step emitted EPUBs whose cover
slot resolved to a missing path. This script generates the 8 main covers
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
- eastern-orthodox    → 01_ornate_leafy_red      (Byzantine red/gold)
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
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))  # CLI runs put scripts/ on sys.path, not the repo root

from scripts.core.config import EDITION_COVER_TEMPLATES  # noqa: E402

COVERS_DIR = REPO_ROOT / "content" / "covers"
TEMPLATES_DIR = COVERS_DIR / "templates"

# Edition → factory cover-template stem. σ.2 dropped the hard-coded title
# strings (the cover text now comes from editions.yaml via
# ``cover_text_for_edition``). The map's ONE home is scripts/core/config.py
# (``EDITION_COVER_TEMPLATES``) so cover-free consumers — build_edition's
# catalog signature, the release-catalog generator — never import Pillow;
# this module re-exports it for batch regen + the /customize "reset to
# factory template" path. The colour-to-tradition rationale lives in the
# module docstring above.
EDITION_TEMPLATES: dict[str, str] = EDITION_COVER_TEMPLATES

# The standard editions, in declaration order, for batch regeneration.
STANDARD_EDITION_IDS: list[str] = list(EDITION_TEMPLATES.keys())


def template_for_edition(edition_id: str) -> str:
    """The cover template stem for ``edition_id`` — the edition's recorded
    ``cover_template`` from editions.yaml when set, else its factory default
    from ``EDITION_TEMPLATES``, else the project-wide default template.
    Delegates to the one-home resolver in scripts/core/config.py."""
    from scripts.core import config

    return config.edition_cover_template(edition_id)


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

# σ.4.4 — VERTICAL safe band. fit_text_block guarantees only HORIZONTAL fit;
# without a vertical bound a pathological main/subtitle (now enterable on the
# /customize name card) could push the centered stack off the top or bottom,
# where Pillow silently clips it. The drawn text block is clamped to stay
# inside [TOP_SAFE_Y, BOTTOM_SAFE_Y]. These margins clear the templates'
# top/bottom border ornament AND sit far outside every real cover's stack
# (real top_y ≈ 419-450, bottom ≈ 630-662), so the clamp is a strict no-op for
# the 9 shipped covers (byte-neutral) and only ever engages for absurd input.
TOP_SAFE_Y = 100
BOTTOM_SAFE_Y = FINAL_HEIGHT - 100  # 1436

# Font path — Times New Roman bold ships with Windows; non-Windows boxes (the
# Mac lane, CI runners) fall back to the repo's own Cardo Bold so the title
# font is always a REAL face on disk, never PIL's pathless default (which
# breaks the σ.5.1 path-identity contract the tests pin). First existing
# candidate wins (the FONT_ETHIOPIC_CANDIDATES pattern); Windows output is
# unchanged — timesbd.ttf always exists there and stays first.
FONT_TITLE_CANDIDATES: tuple[str, ...] = (
    r"C:\Windows\Fonts\timesbd.ttf",
    str(REPO_ROOT / "content" / "assets" / "fonts" / "Cardo-Bold.ttf"),
)
FONT_TITLE_PATH = next((c for c in FONT_TITLE_CANDIDATES if Path(c).is_file()), FONT_TITLE_CANDIDATES[0])

# σ.5.1 — Ethiopic-capable title font. The 2 standalone Bibles carry main
# titles in Ge'ez/Amharic script (Ethiopic block U+1200–U+137F), and Times New
# Roman has NO Ethiopic glyphs — it would render the title as tofu (.notdef)
# boxes, which still have width so ``fit_text_block`` could not catch them.
# Ethiopic text is therefore drawn in a system Ethiopic face. Nyala (the
# primary Windows Ethiopic font) is the first choice; Ebrima (which also covers
# Ethiopic) is the fallback for boxes that ship without Nyala; PIL's default is
# the last resort. The first path that exists on disk wins.
FONT_ETHIOPIC_CANDIDATES: tuple[str, ...] = (
    r"C:\Windows\Fonts\nyala.ttf",  # Nyala — full Ethiopic coverage (primary)
    r"C:\Windows\Fonts\ebrima.ttf",  # Ebrima — also covers Ethiopic (fallback)
    # Repo-shipped Ethiopic face — the non-Windows/CI resort, LAST so Windows
    # rendering is unchanged.
    str(REPO_ROOT / "content" / "assets" / "fonts" / "NotoSerifEthiopic-Regular.ttf"),
)

# Ethiopic Unicode block (and its supplement is U+1380–U+139F; the core block
# U+1200–U+137F covers every Ge'ez/Amharic syllable used in the cover titles).
_ETHIOPIC_LO, _ETHIOPIC_HI = 0x1200, 0x137F


def _font_path_ethiopic() -> str:
    """The first available Ethiopic-capable font path (Nyala → Ebrima), or
    ``FONT_TITLE_PATH`` if neither ships on this box (``_load_font`` then falls
    back to PIL's default — degrade legibly rather than crash)."""
    for cand in FONT_ETHIOPIC_CANDIDATES:
        if Path(cand).is_file():
            return cand
    return FONT_TITLE_PATH


def _has_ethiopic(text: str) -> bool:
    """True iff ``text`` contains any codepoint in the Ethiopic block."""
    return any(_ETHIOPIC_LO <= ord(c) <= _ETHIOPIC_HI for c in (text or ""))


def _font_path_for_text(text: str) -> str:
    """Pick the font *path* for ``text``: an Ethiopic face when the text carries
    Ethiopic codepoints, else Times (``FONT_TITLE_PATH``). Threaded through the
    fitter so width measurement and drawing use the SAME font (a Times-measured,
    Ethiopic-drawn mismatch would break the fit guarantee)."""
    return _font_path_ethiopic() if _has_ethiopic(text) else FONT_TITLE_PATH


def _font_for_text(text: str, size: int) -> ImageFont.FreeTypeFont:
    """Load the size-``size`` font appropriate for ``text`` — an Ethiopic face
    for Ethiopic text, else Times. The σ.5.1 entrypoint the cover composer +
    tests use to guarantee Ge'ez/Amharic titles render real glyphs, not tofu."""
    return _load_font(_font_path_for_text(text), size)


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
    font_path: str | None = None,
) -> tuple[list[str], ImageFont.FreeTypeFont]:
    """Wrap-then-shrink text fitter with a HARD guarantee: every returned line's
    rendered width is ≤ ``max_width`` (HORIZONTAL fit only — the VERTICAL bound
    is enforced separately by ``_compose_cover_layout`` via the safe band).

    For each size from ``max_pt`` down to ``min_pt`` (1pt steps), greedily
    word-wrap ``text`` into lines that each fit ``max_width``; the first size at
    which every line fits wins. If even ``min_pt`` can't fit some word by
    wrapping alone, that word is hard-broken at ``min_pt`` so every final line
    still fits. Empty/blank text returns ``([], font@max_pt)``.

    ``font_path`` selects the typeface (σ.5.1): None auto-picks via
    ``_font_path_for_text`` (Ethiopic face for Ge'ez/Amharic titles, else
    Times), so width measurement and the returned font are the SAME face — a
    Times-measured / Ethiopic-drawn mismatch would void the fit guarantee.

    This replaces the old ``_fit_title_font``, whose bug was returning the
    minimum size *without re-checking fit* — letting long titles overrun the
    cover's gold border (the reported defect)."""
    text = (text or "").strip()
    fp = font_path if font_path is not None else _font_path_for_text(text)
    if not text:
        return [], _load_font(fp, max_pt)

    for size in range(max_pt, min_pt - 1, -1):
        font = _load_font(fp, size)
        lines, all_fit = _wrap_at_size(draw, text, max_width, font)
        if all_fit:
            return lines, font

    # Floor reached: wrap at min_pt, then hard-break any line still too wide so
    # the guarantee holds even for a pathological single unbreakable word.
    font = _load_font(fp, min_pt)
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


def _stack_height(
    main_font: ImageFont.FreeTypeFont,
    n_main: int,
    sub_font: ImageFont.FreeTypeFont | None,
    n_sub: int,
) -> int:
    """Total height of the main + (rule + subtitle) stack, matching the layout
    ``_compose_cover_layout`` / ``_draw_centered_block`` produce."""
    total = _block_height(main_font, n_main)
    if n_sub and sub_font is not None:
        total += RULE_GAP + RULE_THICKNESS + SUBTITLE_GAP + _block_height(sub_font, n_sub)
    return total


def _compose_cover_layout(main_title: str, subtitle: str = "") -> dict:
    """Lay out the cover text WITHOUT drawing it — the geometry half of
    ``_compose_cover``, factored out so the vertical-overflow guard is unit-
    testable on its pixel bounds (Pillow silently clips, so ``img.size`` proves
    nothing — see ``tests/test_cover_fit.py``).

    Returns ``{main_lines, main_font, main_top_y, sub_lines, sub_font,
    sub_top_y, rule_y}``. ``sub_*`` are empty / None when there is no subtitle.

    Two guarantees:
      • HORIZONTAL — every line fits the safe width (``fit_text_block``).
      • VERTICAL (σ.4.4) — the whole drawn stack stays inside the safe band
        ``[TOP_SAFE_Y, BOTTOM_SAFE_Y]``. The stack is centered about
        ``TITLE_CENTER_Y``; if that pushes its top above ``TOP_SAFE_Y`` it is
        clamped down, and if the stack is still taller than the band the
        subtitle then the main are progressively re-fit at smaller point sizes
        until it fits (degrading legibly rather than clipping off-frame).

    For every real cover the centered top sits far below ``TOP_SAFE_Y`` and the
    short stack fits the band, so NONE of the clamp/re-fit branches engage —
    the layout (and therefore the rendered bytes) is identical to pre-σ.4.4."""
    draw = ImageDraw.Draw(Image.new("RGB", (FINAL_WIDTH, FINAL_HEIGHT)))
    subtitle = (subtitle or "").strip()

    main_max, main_min = TITLE_FONT_MAX, TITLE_FONT_MIN
    sub_max, sub_min = SUBTITLE_FONT_MAX, SUBTITLE_FONT_MIN

    band_h = BOTTOM_SAFE_Y - TOP_SAFE_Y

    # σ.5.1 — resolve each block's typeface ONCE (Ethiopic face for Ge'ez/Amharic
    # titles, else Times) and thread it through every (re-)fit so measurement and
    # drawing always use the same font.
    main_fp = _font_path_for_text(main_title)
    sub_fp = _font_path_for_text(subtitle)

    main_lines, main_font = fit_text_block(
        draw, main_title, TITLE_MAX_WIDTH, max_pt=main_max, min_pt=main_min, font_path=main_fp
    )
    sub_lines: list[str] = []
    sub_font: ImageFont.FreeTypeFont | None = None
    if subtitle:
        sub_lines, sub_font = fit_text_block(
            draw, subtitle, TITLE_MAX_WIDTH, max_pt=sub_max, min_pt=sub_min, font_path=sub_fp
        )

    # VERTICAL re-fit loop: shrink the subtitle first (it's the secondary line),
    # then the main, until the stack fits the band. Bounded by the pt ranges so
    # it always terminates; at the floor we accept whatever fits best.
    total_h = _stack_height(main_font, len(main_lines), sub_font, len(sub_lines))
    while total_h > band_h:
        if subtitle and sub_font is not None and sub_max > sub_min:
            sub_max -= 2
            if sub_max < sub_min:
                sub_max = sub_min
            sub_lines, sub_font = fit_text_block(
                draw, subtitle, TITLE_MAX_WIDTH, max_pt=sub_max, min_pt=sub_min, font_path=sub_fp
            )
        elif main_max > main_min:
            main_max -= 2
            if main_max < main_min:
                main_max = main_min
            main_lines, main_font = fit_text_block(
                draw, main_title, TITLE_MAX_WIDTH, max_pt=main_max, min_pt=main_min, font_path=main_fp
            )
        else:
            break  # both at floor — drawn clamped to the band; nothing more to do
        total_h = _stack_height(main_font, len(main_lines), sub_font, len(sub_lines))

    # Center about TITLE_CENTER_Y, then clamp the top into the safe band so the
    # block never draws above the frame. (For real covers top_y ≫ TOP_SAFE_Y, so
    # this max() is a strict no-op — byte-neutral.)
    top_y = TITLE_CENTER_Y - total_h // 2
    top_y = max(top_y, TOP_SAFE_Y)
    # If the (clamped) bottom would still exceed the band — only possible when
    # both fonts hit their floor on truly absurd input — pull the top up just
    # enough to keep the bottom on-frame (never above TOP_SAFE_Y if avoidable).
    if top_y + total_h > BOTTOM_SAFE_Y:
        top_y = max(TOP_SAFE_Y, BOTTOM_SAFE_Y - total_h)

    main_h = _block_height(main_font, len(main_lines))
    rule_y = top_y + main_h + RULE_GAP if sub_lines else top_y + main_h
    sub_top_y = rule_y + RULE_THICKNESS + SUBTITLE_GAP if sub_lines else rule_y

    return {
        "main_lines": main_lines,
        "main_font": main_font,
        "main_top_y": top_y,
        "sub_lines": sub_lines,
        "sub_font": sub_font,
        "sub_top_y": sub_top_y,
        "rule_y": rule_y,
    }


def _compose_cover(template_stem: str, main_title: str, subtitle: str = "") -> Image.Image:
    """Composite the cover text — a large ``main_title`` block, a short centered
    rule, then a smaller ``subtitle`` block — onto a template; return the RGB
    cover at the final dimensions.

    The whole stack is vertically centered about ``TITLE_CENTER_Y`` and laid out
    by ``_compose_cover_layout``, which guarantees BOTH that no line runs past
    the safe width (σ.2) AND that the drawn stack stays inside the vertical safe
    band ``[TOP_SAFE_Y, BOTTOM_SAFE_Y]`` (σ.4.4 — clamp + shrink so a pathological
    title can never be clipped off the top/bottom edge). An empty ``subtitle``
    draws the main title only (no rule, no subtitle region)."""
    template_path = TEMPLATES_DIR / f"{template_stem}.png"
    if not template_path.is_file():
        raise FileNotFoundError(f"template missing: {template_path}")

    base = Image.open(template_path).convert("RGB")
    # Resize to final dimensions BEFORE compositing so the text is laid out in
    # the final coordinate space.
    base = base.resize((FINAL_WIDTH, FINAL_HEIGHT), Image.LANCZOS)
    draw = ImageDraw.Draw(base, "RGBA")

    layout = _compose_cover_layout(main_title, subtitle)
    _draw_centered_block(draw, layout["main_lines"], layout["main_font"], layout["main_top_y"], TITLE_COLOR)

    if layout["sub_lines"] and layout["sub_font"] is not None:
        rule_y = layout["rule_y"]
        cx = FINAL_WIDTH // 2
        draw.rectangle(
            (cx - RULE_HALF_WIDTH, rule_y, cx + RULE_HALF_WIDTH, rule_y + RULE_THICKNESS - 1),
            fill=TITLE_COLOR,
        )
        _draw_centered_block(draw, layout["sub_lines"], layout["sub_font"], layout["sub_top_y"], SUBTITLE_COLOR)

    return base


# Downloads-catalog cover composites (format-matrix spec §4.2 + addendum
# 2026-06-11). The signature catalog assets need NO composite — the base
# build already embeds the edition's own committed cover. Composites exist
# for the M2 COLOUR VARIANTS: the edition's OWN design re-composited in each
# non-signature colour ("HOLY BIBLE" + subtitle on the colour's template; a
# raw template PNG would be wrong twice — title-less art + PNG bytes in the
# OPF's image/jpeg cover slot). Variant composites are generated HERE on the
# canonical fonts and COMMITTED under content/covers/catalog/ — CI swaps
# committed bytes into the built EPUBs and never composites in-runner, so
# the ubuntu font-divergence class the Mac review flagged cannot occur.
CATALOG_DIR = COVERS_DIR / "catalog"


def catalog_colour_variant_plan() -> list[tuple[str, str, str]]:
    """The M2 composite set: every standard edition × its OWN signature
    design × every template colour — ``(edition_id, design, colour)``
    triples, editions in declaration order, colours in COVER_COLOURS order
    within each (the signature colour included: its composite doubles as a
    pinnable rendering of the cover the base build embeds)."""
    from scripts.build_edition import COVER_COLOURS, edition_cover_signature

    plan: list[tuple[str, str, str]] = []
    for e in STANDARD_EDITION_IDS:
        design, _sig_colour = edition_cover_signature(e)
        plan.extend((e, design, c) for c in COVER_COLOURS)
    return plan


def generate_catalog_composite(edition_id: str, design: str, colour: str, out_dir: Path | None = None) -> Path:
    """Composite ``edition_id``'s cover text onto the ``design`` family's
    ``colour`` template and write the catalog JPEG
    ``<edition_id>_<design>_<colour>.jpg`` (final cover dimensions, same
    quality as the shipped edition covers). Unknown colours raise ValueError;
    a design with no on-disk template raises FileNotFoundError (via
    ``_compose_cover``) — a typo'd cell must fail loudly, never ship a wrong
    cover."""
    from scripts.build_edition import COVER_COLOURS

    if colour not in COVER_COLOURS:
        raise ValueError(f"unknown cover colour {colour!r}; valid: {COVER_COLOURS}")
    main_title, subtitle = cover_text_for_edition(edition_id)
    base = _compose_cover(f"{design}_{colour}", main_title, subtitle)
    target_dir = out_dir if out_dir is not None else CATALOG_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / f"{edition_id}_{design}_{colour}.jpg"
    base.save(out_path, "JPEG", quality=90, optimize=True)
    return out_path


def generate_catalog_colour_variants() -> list[Path]:
    """Generate the full committed M2 variant set (20 = 4 editions × their
    own design in all 5 colours)."""
    return [generate_catalog_composite(e, d, c) for (e, d, c) in catalog_colour_variant_plan()]


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
