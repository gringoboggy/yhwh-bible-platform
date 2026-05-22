#!/usr/bin/env python3
"""
LOAD-BEARING-NO-LONGER as of Ω.0 free-public pivot (2026-05-14).
Generates wraparound cover PDFs for print-on-demand uploaders
(Amazon KDP, IngramSpark, Lulu). Back cover includes an ISBN
barcode rectangle keyed to the (now-dropped) edition.isbn field.
With no ISBN and no commercial print sale, this tool has no
downstream consumer. Retained per §7.4 for git-history value (the
canvas layout / bleed math is reference-quality).

print_cover.py — Generate print-on-demand wraparound cover PDFs.

Emits a single wraparound PDF per (edition × variant) combination,
suitable for upload to Amazon KDP, IngramSpark, Lulu, etc. Each PDF
contains: front cover (right pane), spine (computed width), back
cover (left pane with blurb + ISBN barcode).

Layout (canvas coordinate system, origin at bottom-left):
    +-----------+--+-----------+
    |   BACK    |SP|   FRONT   |
    |  (left)   |IN|  (right)  |
    |           |E |           |
    +-----------+--+-----------+
    bleed     trim sp trim  bleed

Per Q6: back-cover blurb pulls from content/onix.py defaults +
per-edition records. Per Q7: ISBN barcode is a placeholder
rectangle when the ISBN is still TODO_*. Per Q8: this tool does
NOT touch the manifest or any integrity tracking.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from io import BytesIO
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config  # noqa: E402
from scripts.core.ui import GREEN, RED, YELLOW, DIM, BOLD, RESET  # noqa: E402

CONTENT_DIR = REPO_ROOT / "content"
EPUB_DIR = REPO_ROOT / "epub_working"
PRINT_OUT_DIR = CONTENT_DIR / "print_covers"
CUSTOM_YAML = CONTENT_DIR / "customization.yaml"

# ----------------------------------------------------------------------
# Paper-weight → pages-per-inch lookup
# ----------------------------------------------------------------------
# Values from Amazon KDP + IngramSpark published spine-width tables.
# pages-per-inch (PPI) = how many physical pages fit in 1 inch of spine.
# Higher PPI = thinner paper = thinner spine for same page count.

PAPER_PPI: dict[str, int] = {
    "white-50lb": 444,
    "cream-50lb": 444,
    "white-55lb": 400,
    "cream-55lb": 400,
    "white-60lb": 360,
    "premium-color-60lb": 360,
}


def spine_width_in(page_count: int, paper: str) -> float:
    ppi = PAPER_PPI.get(paper, 444)
    return page_count / ppi


# ----------------------------------------------------------------------
# Onix metadata loader (per-edition blurb + ISBN)
# ----------------------------------------------------------------------


def load_onix_metadata() -> tuple[dict, dict]:
    """Returns (defaults, editions_by_id). Falls back to empty dicts
    when content/onix.py is unavailable."""
    onix_py = CONTENT_DIR / "onix.py"
    if not onix_py.is_file():
        return {}, {}
    spec = importlib.util.spec_from_file_location("_onix_print", onix_py)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    defaults = getattr(mod, "DEFAULTS", {})
    editions = {e.get("id"): e for e in getattr(mod, "EDITIONS", [])}
    return defaults, editions


# ----------------------------------------------------------------------
# Barcode generation
# ----------------------------------------------------------------------


def render_isbn_barcode(isbn: str) -> bytes | None:
    """Return PNG bytes of an EAN-13 barcode for the ISBN. Returns None
    if the ISBN is a TODO placeholder so the caller can draw a placeholder
    rectangle with a loud warning instead."""
    if not isbn or "TODO" in isbn or "X" in isbn.upper():
        return None
    try:
        from barcode import EAN13
        from barcode.writer import ImageWriter

        digits = "".join(c for c in isbn if c.isdigit())
        if len(digits) != 13:
            return None
        buf = BytesIO()
        EAN13(digits, writer=ImageWriter()).write(buf, options={"write_text": True})
        return buf.getvalue()
    except Exception:
        return None


# ----------------------------------------------------------------------
# Cover generation
# ----------------------------------------------------------------------


def generate_cover_pdf(
    edition_id: str,
    variant: dict,
    defaults: dict,
    editions: dict,
    page_count: int,
) -> tuple[Path, list[str]]:
    """Render a wraparound cover PDF for one (edition, variant). Returns
    (output_path, list_of_warnings)."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    from reportlab.lib.utils import ImageReader
    from reportlab.lib.colors import HexColor, white

    warnings: list[str] = []

    trim_w = float(variant["trim_width_in"])
    trim_h = float(variant["trim_height_in"])
    bleed = float(variant["bleed_in"])
    paper = variant.get("paper", "white-50lb")
    profile = variant["profile"]

    spine = spine_width_in(page_count, paper)

    canvas_w = bleed + trim_w + spine + trim_w + bleed
    canvas_h = bleed + trim_h + bleed

    # x-coordinates of pane edges
    back_x_start = bleed
    spine_x_start = bleed + trim_w
    front_x_start = bleed + trim_w + spine
    bleed + trim_w + spine + trim_w

    # Edition data
    ed = editions.get(edition_id, {})
    title = ed.get("title_full") or ed.get("title", "The Ethiopian Bible")
    subtitle = ed.get("title_subtitle", "")
    contributor = (defaults.get("contributor") or {}).get("name", "Compiled and annotated")
    isbn = ed.get("isbn", "TODO_ISBN_13")
    blurb_default = (ed.get("description") or "").strip()
    blurb_override = (ed.get("print_blurb") or "").strip()
    blurb = blurb_override or blurb_default
    if not blurb:
        warnings.append(f"{edition_id}: no blurb in onix.py (description or print_blurb)")
        blurb = f"[ {edition_id} blurb — set in content/onix.py ]"

    # Output
    PRINT_OUT_DIR.mkdir(exist_ok=True)
    fname = f"Ethiopian_Bible_{edition_id}_{profile}_{page_count}pp.pdf"
    out_path = PRINT_OUT_DIR / fname

    c = canvas.Canvas(
        str(out_path),
        pagesize=(canvas_w * inch, canvas_h * inch),
    )

    # ---- BACKGROUND (full bleed) ----
    bg = HexColor("#1a0d0a")  # default dark walnut; user can override via per-edition cover_bg
    bg_hex = ed.get("print_cover_bg") or defaults.get("print_cover_bg", "#1a0d0a")
    try:
        bg = HexColor(bg_hex)
    except Exception:
        pass
    c.setFillColor(bg)
    c.rect(0, 0, canvas_w * inch, canvas_h * inch, fill=1, stroke=0)

    # ---- FRONT cover (right pane) ----
    cover_img = EPUB_DIR / f"cover-{edition_id}.jpeg"
    if not cover_img.is_file():
        cover_img = EPUB_DIR / "cover.jpeg"
    if cover_img.is_file():
        try:
            c.drawImage(
                ImageReader(str(cover_img)),
                front_x_start * inch,
                bleed * inch,
                width=trim_w * inch,
                height=trim_h * inch,
                preserveAspectRatio=True,
                anchor="c",
                mask="auto",
            )
        except Exception as e:
            warnings.append(f"{edition_id}: front cover image failed: {e}")
    else:
        warnings.append(f"{edition_id}: no cover.jpeg found")

    # ---- SPINE (rotated text) ----
    if spine >= 0.0625:  # at least 1/16" of spine for text
        c.saveState()
        c.translate((spine_x_start + spine / 2) * inch, canvas_h * inch / 2)
        c.rotate(90)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", min(10, spine * inch * 0.6))
        c.drawCentredString(0, -3, title[:60])
        c.setFont("Helvetica", min(8, spine * inch * 0.5))
        c.drawCentredString(0, -trim_h * inch / 2 + 36, contributor[:40])
        c.restoreState()
    else:
        warnings.append(
            f'{edition_id}/{profile}: spine too thin ({spine:.3f}") for text — increase page_count or use thinner paper'
        )

    # ---- BACK cover (left pane: blurb + ISBN barcode) ----
    margin = 0.5  # inches inside trim
    back_text_x = (back_x_start + margin) * inch
    back_text_w = (trim_w - 2 * margin) * inch
    back_text_top = (canvas_h - bleed - margin) * inch

    c.setFillColor(white)
    # Title (smaller on back)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(back_text_x, back_text_top, title[:70])
    if subtitle:
        c.setFont("Helvetica-Oblique", 11)
        c.drawString(back_text_x, back_text_top - 18, subtitle[:90])

    # Blurb body
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT

    body_style = ParagraphStyle(
        "body",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=white,
        alignment=TA_LEFT,
    )
    para = Paragraph(blurb.replace("\n", "<br/>"), body_style)
    blurb_top = back_text_top - (45 if subtitle else 30)
    blurb_h = trim_h * inch * 0.55
    para.wrapOn(c, back_text_w, blurb_h)
    para.drawOn(c, back_text_x, blurb_top - blurb_h)

    # ISBN barcode (bottom-right of back panel)
    bar_w = 1.6 * inch
    bar_h = 0.9 * inch
    bar_x = (back_x_start + trim_w - margin - 1.6) * inch
    bar_y = (bleed + margin) * inch

    barcode_png = render_isbn_barcode(isbn) if variant.get("isbn_barcode", True) else None
    if barcode_png:
        try:
            c.drawImage(
                ImageReader(BytesIO(barcode_png)),
                bar_x,
                bar_y,
                width=bar_w,
                height=bar_h,
                preserveAspectRatio=True,
                anchor="sw",
                mask="auto",
            )
        except Exception as e:
            warnings.append(f"{edition_id}: barcode draw failed: {e}")
    else:
        # PLACEHOLDER (Q7) with loud warning
        warnings.append(
            f"{edition_id}/{profile}: ISBN is placeholder ({isbn}) — barcode rendered as box. "
            f"Re-run after filling in onix.py with real ISBN-13."
        )
        c.setFillColor(white)
        c.setStrokeColor(white)
        c.rect(bar_x, bar_y, bar_w, bar_h, stroke=1, fill=0)
        c.setFont("Helvetica", 8)
        c.drawString(bar_x + 6, bar_y + bar_h / 2, "PLACEHOLDER · ISBN not yet assigned")

    # ---- PRINT MARKS (subtle outlines for proofing) ----
    # Bleed line (very faint, 0.1pt) at the canvas edge — already there, just doc
    c.setStrokeColor(HexColor("#FF00FF"))  # magenta crop marks at bleed
    c.setLineWidth(0.1)
    # Tiny crop ticks at the four corners of the trim
    tick = 12  # 12 pt = ~0.17"
    for x, y in [
        (bleed * inch, bleed * inch),
        ((canvas_w - bleed) * inch, bleed * inch),
        (bleed * inch, (canvas_h - bleed) * inch),
        ((canvas_w - bleed) * inch, (canvas_h - bleed) * inch),
    ]:
        c.line(x - tick, y, x + tick, y)
        c.line(x, y - tick, x, y + tick)

    c.save()
    return out_path, warnings


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(
        description="Generate print-on-demand wraparound cover PDFs.",
    )
    p.add_argument(
        "profile", nargs="?", default="all", help="profile id (e.g. 'kdp-6x9') or 'all' for every enabled variant"
    )
    p.add_argument("--edition", help="generate for a single edition only (default: all 5)")
    p.add_argument("--page-count", type=int, help="override page count (overrides per-variant page_count)")
    args = p.parse_args()

    if not CUSTOM_YAML.is_file():
        print(f"{RED}✗ {CUSTOM_YAML} not found — run customize first{RESET}", file=sys.stderr)
        sys.exit(2)

    import yaml

    with CUSTOM_YAML.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    variants = (cfg.get("print_covers") or {}).get("variants") or []
    enabled = [v for v in variants if v.get("enabled")]
    if args.profile != "all":
        enabled = [v for v in enabled if v.get("profile") == args.profile]
    if not enabled:
        print(f"{YELLOW}⚠ no enabled variants matching '{args.profile}'.{RESET}")
        print("  Flip `enabled: true` in customization.yaml first.")
        sys.exit(0)

    defaults, ed_records = load_onix_metadata()

    target_editions = [args.edition] if args.edition else [e["id"] for e in config.load_editions()]

    print(f"\n{BOLD}print_cover{RESET}  {DIM}{len(enabled)} variant(s) × {len(target_editions)} edition(s){RESET}\n")

    all_warnings: list[str] = []
    generated = 0
    for ed_id in target_editions:
        for variant in enabled:
            page_count = args.page_count or variant.get("page_count") or 0
            if not isinstance(page_count, int) or page_count <= 0 or "TODO" in str(page_count):
                msg = f"{ed_id}/{variant['profile']}: skipping — page_count not set (run --measure first)"
                all_warnings.append(msg)
                print(f"  {YELLOW}⚠{RESET} {msg}")
                continue
            try:
                out, warns = generate_cover_pdf(ed_id, variant, defaults, ed_records, page_count)
                all_warnings.extend(warns)
                generated += 1
                print(
                    f"  {GREEN}✓{RESET} {out.name}  {DIM}({page_count}pp · "
                    f'spine={spine_width_in(page_count, variant.get("paper", "white-50lb")):.3f}"){RESET}'
                )
            except Exception as e:
                print(f"  {RED}✗{RESET} {ed_id}/{variant['profile']}: {e}")

    if all_warnings:
        print(f"\n{YELLOW}⚠ {len(all_warnings)} warning(s):{RESET}")
        for w in all_warnings:
            print(f"  {YELLOW}⚠{RESET} {w}")

    print(f"\n  {BOLD}{generated} cover PDF(s) generated{RESET}")
    print(f"  {DIM}written to {PRINT_OUT_DIR}/{RESET}\n")


if __name__ == "__main__":
    main()
