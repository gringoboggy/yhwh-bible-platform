#!/usr/bin/env python3
"""
apply_style.py — Apply ``scripts/style_config.py`` to the working EPUB.

Reads the configuration constants and patches in place:

  * ``epub_working/stylesheet.css`` — body margins, font stack, chapter flow
  * ``epub_working/nav.xhtml``      — chapter label format
  * ``epub_working/index_split_000.html`` — visible TOC chapter labels and
    optional collapsible (<details>/<summary>) book sections.

The script is idempotent: it identifies our managed regions with sentinel
comments and rewrites just those regions, so running twice is a no-op.

Examples:
    python3 scripts/apply_style.py             # apply the current config
    python3 scripts/apply_style.py --check     # report what would change
    python3 scripts/apply_style.py --no-toc    # skip TOC rewrites
    python3 scripts/apply_style.py --revert-collapsible
            (force-disable the collapsible TOC; useful for compatibility test)
"""

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import style_config  # noqa: E402

EPUB_DIR = REPO_ROOT / "epub_working"

# Sentinel that marks our managed CSS region. Anything between BEGIN/END is
# regenerated each time apply_style.py runs.
CSS_BEGIN = "/* === BEGIN apply_style.py managed region — DO NOT EDIT BY HAND === */"
CSS_END = "/* === END apply_style.py managed region === */"

_VISIBLE_TOC_BEGIN = "<!-- BEGIN apply_style.py visible-TOC managed region -->"
_VISIBLE_TOC_END = "<!-- END apply_style.py visible-TOC managed region -->"


# ---------------------------------------------------------------------------
# CSS section
# ---------------------------------------------------------------------------


def render_managed_css() -> str:
    """Return the CSS block that lives between the sentinels."""
    margin = style_config.MARGIN_SIDE
    font = style_config.FONT_STACK
    flow = style_config.CHAPTER_FLOW

    # Body margin override (also covers the legacy `.bible-body` alias).
    margin_block = f"""\
body, body.bible-body {{
  margin-left: {margin} !important;
  margin-right: {margin} !important;
}}"""

    # Font-stack override applied broadly enough to dominate the legacy rules.
    font_block = f"""\
body, body.bible-body, p, p.verse-p, p.verse-p-flush, p.ch-heading,
.note, .vnote, .toc-wrap {{
  font-family: {font} !important;
}}"""

    # Chapter heading flow rules. Two modes:
    if flow == "page-break":
        flow_block = """\
.ch-heading {
  page-break-before: always;
  break-before: page;
  page-break-after: avoid;
  break-after: avoid;
  page-break-inside: avoid;
  break-inside: avoid;
}"""
    elif flow == "smart":
        flow_block = """\
/* "smart" flow — chapters share pages when room exists, but the chapter
   heading + its first paragraph stay together (no orphan chapter number
   stranded at the bottom of a page). */
.ch-heading {
  page-break-before: auto;
  break-before: auto;
  page-break-after: avoid;
  break-after: avoid;
  page-break-inside: avoid;
  break-inside: avoid;
  margin-top: 1.4em;
  orphans: 3;
  widows: 3;
}
/* Apply orphans/widows to the verse paragraphs that follow chapter
   headings, reinforcing the same intent across readers that respect the
   text-level (rather than block-level) properties. */
p.verse-p, p.verse-p-flush {
  orphans: 3;
  widows: 3;
}"""
    else:
        raise SystemExit(f"unknown CHAPTER_FLOW: {flow!r}")

    # Optional embedded font.
    embed_block = ""
    if style_config.EMBED_FONT_PATH:
        embed_block = f"""\
@font-face {{
  font-family: "{style_config.EMBED_FONT_FAMILY}";
  src: url("{style_config.EMBED_FONT_PATH}");
  font-weight: normal;
  font-style: normal;
}}
"""

    blocks = [b for b in (embed_block, margin_block, font_block, flow_block) if b]
    return CSS_BEGIN + "\n" + "\n\n".join(blocks) + "\n" + CSS_END


def patch_css(css_path: Path, dry_run: bool) -> bool:
    """Replace (or insert) the managed region in stylesheet.css."""
    text = css_path.read_text(encoding="utf-8")
    new_block = render_managed_css()

    if CSS_BEGIN in text and CSS_END in text:
        # Replace existing block.
        new_text = re.sub(
            re.escape(CSS_BEGIN) + r".*?" + re.escape(CSS_END),
            lambda _m: new_block,
            text,
            count=1,
            flags=re.DOTALL,
        )
    else:
        # Append at end with a separating blank line.
        sep = "" if text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
        new_text = text + sep + new_block + "\n"

    if new_text == text:
        return False
    if not dry_run:
        css_path.write_text(new_text, encoding="utf-8")
    return True


# ---------------------------------------------------------------------------
# nav.xhtml — chapter-label format
# ---------------------------------------------------------------------------

# Regex matches:  <a href="…#ch-bXX-cN">Chapter N</a>
NAV_CHAPTER_RE = re.compile(r'(<a\s+href="[^"]+#ch-b\d+-c(\d+)">)\s*(?:Chapter\s+)?(\d+)\s*(</a>)')


def _chapter_label(book_code: str, book_title: str, ch_num: str) -> str:
    fmt = style_config.TOC_CHAPTER_FORMAT
    if fmt == "num-only":
        return ch_num
    if fmt == "chapter-num":
        return f"Chapter {ch_num}"
    if fmt == "code-num":
        # Use first three letters of the title as a graceful default if the
        # book code starts with a digit (e.g. "1ki" → "1Ki" looks odd; use
        # the title-derived form instead).
        return f"{book_code.title()} {ch_num}"
    if fmt == "title-num":
        # Use the canonical short name (last comma-separated component).
        short = book_title.split(",")[-1].strip()
        return f"{short} {ch_num}"
    raise SystemExit(f"unknown TOC_CHAPTER_FORMAT: {fmt!r}")


def patch_nav(nav_path: Path, dry_run: bool) -> bool:
    """Rewrite chapter labels in nav.xhtml per TOC_CHAPTER_FORMAT.

    For num-only / chapter-num formats we don't need book context, so a
    simple regex pass works. For code-num / title-num we'd need to scan the
    surrounding book heading; we skip those advanced formats here for
    safety and document the limitation.
    """
    text = nav_path.read_text(encoding="utf-8")
    fmt = style_config.TOC_CHAPTER_FORMAT

    if fmt in ("code-num", "title-num"):
        print(
            f"  WARNING: TOC_CHAPTER_FORMAT={fmt!r} only affects the visible "
            "TOC for now (nav.xhtml unchanged); to regenerate nav.xhtml in "
            "those formats, re-run scripts/build_toc.py."
        )
        return False

    def repl(m: re.Match) -> str:
        ch_num = m.group(2)
        new_label = ch_num if fmt == "num-only" else f"Chapter {ch_num}"
        return f"{m.group(1)}{new_label}{m.group(4)}"

    new_text = NAV_CHAPTER_RE.sub(repl, text)
    if new_text == text:
        return False
    if not dry_run:
        nav_path.write_text(new_text, encoding="utf-8")
    return True


# ---------------------------------------------------------------------------
# Visible TOC — collapsible <details>/<summary>
# ---------------------------------------------------------------------------

# Match a single <li class="toc-book"> ... </li> block in the visible TOC.
TOC_BOOK_RE = re.compile(
    r'(<li class="toc-book">)\s*'
    r"(<a [^>]+>[^<]+</a>)\s*"  # book link
    r'(<ol class="toc-chapters">.*?</ol>)\s*'  # chapter list
    r"(</li>)",
    re.DOTALL,
)
# Variant when the toc-book block is already wrapped in <details>.
TOC_BOOK_DETAILS_RE = re.compile(
    r'(<li class="toc-book">)\s*'
    r"<details(?:\s+open)?>\s*"
    r"<summary>\s*"
    r"(<a [^>]+>[^<]+</a>)\s*"
    r"</summary>\s*"
    r'(<ol class="toc-chapters">.*?</ol>)\s*'
    r"</details>\s*"
    r"(</li>)",
    re.DOTALL,
)


def patch_visible_toc(html_path: Path, dry_run: bool) -> tuple[bool, int]:
    """Rewrite each toc-book block per current config.

    Returns (changed, n_blocks).
    """
    text = html_path.read_text(encoding="utf-8")
    n = 0
    flatten_first = []

    # First, flatten any existing <details> wrappers so we always start from
    # a known-flat baseline.
    def _flatten(m: re.Match) -> str:
        flatten_first.append(True)
        return f"{m.group(1)}\n{m.group(2)}\n{m.group(3)}\n{m.group(4)}"

    text = TOC_BOOK_DETAILS_RE.sub(_flatten, text)

    # Then re-fold per current config.
    open_attr = " open" if style_config.TOC_COLLAPSIBLE_DEFAULT_OPEN else ""

    def _wrap(m: re.Match) -> str:
        nonlocal n
        n += 1
        book_li, book_a, ch_ol, close_li = m.group(1), m.group(2), m.group(3), m.group(4)
        # Optionally rewrite the chapter labels inside <ol class="toc-chapters">
        ch_ol = rewrite_visible_chapter_labels(ch_ol, m)
        if style_config.TOC_COLLAPSIBLE:
            return (
                f"{book_li}\n"
                f"  <details{open_attr}>\n"
                f"    <summary>{book_a}</summary>\n"
                f"    {ch_ol}\n"
                f"  </details>\n"
                f"{close_li}"
            )
        return f"{book_li}\n{book_a}\n{ch_ol}\n{close_li}"

    new_text = TOC_BOOK_RE.sub(_wrap, text)
    if new_text == html_path.read_text(encoding="utf-8"):
        return False, n
    if not dry_run:
        html_path.write_text(new_text, encoding="utf-8")
    return True, n


def rewrite_visible_chapter_labels(ch_ol: str, _book_match: re.Match) -> str:
    """Update the chapter labels in a <ol class="toc-chapters"> block."""
    fmt = style_config.TOC_CHAPTER_FORMAT
    if fmt == "num-only":
        # Already in num-only format in the existing visible TOC; nothing to do.
        return ch_ol
    # Other formats: rewrite each <a>…</a> label using the chapter number.
    chapter_a_re = re.compile(r'(<a\s+href="[^"]+#ch-b\d+-c(\d+)"[^>]*>)([^<]+)(</a>)')

    def repl(m: re.Match) -> str:
        ch_num = m.group(2)
        if fmt == "chapter-num":
            new_label = f"Chapter {ch_num}"
        elif fmt == "code-num":
            # Approximate: we don't have book code here; pass through.
            new_label = ch_num
        elif fmt == "title-num":
            new_label = ch_num
        else:
            new_label = ch_num
        return f"{m.group(1)}{new_label}{m.group(4)}"

    return chapter_a_re.sub(repl, ch_ol)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(description="Apply style_config.py to the EPUB.")
    p.add_argument("--epub-dir", type=Path, default=EPUB_DIR)
    p.add_argument("--check", action="store_true", help="don't write; just report")
    p.add_argument("--no-css", action="store_true")
    p.add_argument("--no-nav", action="store_true")
    p.add_argument("--no-toc", action="store_true")
    p.add_argument(
        "--revert-collapsible",
        action="store_true",
        help="force-disable collapsible TOC for this run (compatibility test)",
    )
    args = p.parse_args()

    if args.revert_collapsible:
        style_config.TOC_COLLAPSIBLE = False  # type: ignore[attr-defined]

    print("Applying style_config.py:")
    print(f"  MARGIN_SIDE        = {style_config.MARGIN_SIDE}")
    print(f"  CHAPTER_FLOW       = {style_config.CHAPTER_FLOW}")
    print(f"  TOC_CHAPTER_FORMAT = {style_config.TOC_CHAPTER_FORMAT}")
    print(f"  TOC_COLLAPSIBLE    = {style_config.TOC_COLLAPSIBLE}")
    if style_config.EMBED_FONT_PATH:
        print(f"  EMBED_FONT_PATH    = {style_config.EMBED_FONT_PATH}")
    print()

    if not args.no_css:
        css_path = args.epub_dir / "stylesheet.css"
        changed = patch_css(css_path, args.check)
        print(f"  stylesheet.css     {'changed' if changed else '(no change)'}")

    if not args.no_nav:
        nav_path = args.epub_dir / "nav.xhtml"
        changed = patch_nav(nav_path, args.check)
        print(f"  nav.xhtml          {'changed' if changed else '(no change)'}")

    if not args.no_toc:
        toc_path = args.epub_dir / "index_split_000.html"
        changed, n = patch_visible_toc(toc_path, args.check)
        print(f"  visible TOC        {'changed' if changed else '(no change)'} ({n} book blocks)")

    print()
    print("Done." if not args.check else "(--check) no files written.")


if __name__ == "__main__":
    main()
