#!/usr/bin/env python3
"""
check_a11y.py — Accessibility audit for the unpacked EPUB.

Targets WCAG 2.1 AA and EPUB Accessibility 1.1 fundamentals. Apple Books
surfaces a11y issues directly to readers, and libraries / academic
institutions increasingly require WCAG conformance before adopting an EPUB,
so failing any of these checks is a real blocker for distribution.

Checks
------

ERROR-severity:

  * **lang**             ``<html>`` element on every page must carry
                         ``lang`` and/or ``xml:lang``.
  * **alt-text**         Every ``<img>`` needs an ``alt=`` attribute
                         (empty alt is allowed for decorative images).
  * **contrast**         Foreground/background pairs in the kind-marker
                         palette must meet WCAG AA: 4.5:1 for normal text.

WARN-severity:

  * **heading-skip**     Heading levels must not skip downward inside a
                         single document (h1 → h3 is a skip; h3 → h2 is
                         allowed).
  * **presentational**   ``<b>``/``<i>`` used where ``<strong>``/``<em>``
                         carry meaning. Some occurrences are intentional
                         (e.g. PDF-derived italics for transliteration);
                         this check is informational by default.

Examples:
    python3 scripts/check_a11y.py
    python3 scripts/check_a11y.py --check lang
    python3 scripts/check_a11y.py --bg-color "#fff"
    python3 scripts/check_a11y.py --strict       # fail on WARN too
    python3 scripts/check_a11y.py --quiet
    python3 scripts/check_a11y.py --verbose

Exit codes:
    0  no ERROR findings (or --strict not set and only WARNs found)
    1  ERROR findings, or WARNs under --strict
    2  setup error (epub_working/ missing, parse failure)
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EPUB_DIR = REPO_ROOT / "epub_working"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

SEVERITY = {
    "lang": "ERROR",
    "alt-text": "ERROR",
    "contrast": "ERROR",
    "heading-skip": "WARN",
    "presentational": "WARN",
}
CHECKS = list(SEVERITY.keys())


# ----------------------------------------------------------------------
# CSS color → relative luminance → contrast ratio (WCAG)
# ----------------------------------------------------------------------


def parse_hex(s: str) -> tuple[int, int, int] | None:
    s = s.strip().lstrip("#")
    if len(s) == 3 and all(c in "0123456789abcdefABCDEF" for c in s):
        return (int(s[0] * 2, 16), int(s[1] * 2, 16), int(s[2] * 2, 16))
    if len(s) == 6 and all(c in "0123456789abcdefABCDEF" for c in s):
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    return None


def parse_rgb(s: str) -> tuple[int, int, int] | None:
    m = re.match(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", s)
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def parse_color(s: str) -> tuple[int, int, int] | None:
    s = s.strip()
    if s.startswith("#"):
        return parse_hex(s)
    if s.startswith("rgb"):
        return parse_rgb(s)
    named = {
        "white": (255, 255, 255),
        "black": (0, 0, 0),
        "red": (255, 0, 0),
        "green": (0, 128, 0),
        "blue": (0, 0, 255),
    }
    return named.get(s.lower())


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    """WCAG 2.1 relative luminance."""

    def chan(c: int) -> float:
        v = c / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * chan(r) + 0.7152 * chan(g) + 0.0722 * chan(b)


def contrast_ratio(c1: tuple[int, int, int], c2: tuple[int, int, int]) -> float:
    l1 = relative_luminance(c1)
    l2 = relative_luminance(c2)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)


# ----------------------------------------------------------------------
# CSS parsing — extract marker rules
# ----------------------------------------------------------------------


# Match `.marker-foo { color: #abc; ... }` and similar; returns (rule_name, decls).
RULE_RE = re.compile(
    r"\.(marker-\w+|note-\w+)\s*(?:,\s*\.[^{]*)?\s*\{([^}]+)\}",
    re.MULTILINE,
)
COLOR_DECL_RE = re.compile(r"\bcolor\s*:\s*([^;]+);", re.IGNORECASE)
BG_DECL_RE = re.compile(r"\bbackground(?:-color)?\s*:\s*([^;]+);", re.IGNORECASE)


def extract_marker_colors(css_text: str) -> dict[str, dict[str, str]]:
    """Return {selector: {'color': '...', 'background': '...'}} for marker/note rules."""
    rules: dict[str, dict[str, str]] = {}
    for m in RULE_RE.finditer(css_text):
        sel = m.group(1)
        decls = m.group(2)
        cm = COLOR_DECL_RE.search(decls)
        bm = BG_DECL_RE.search(decls)
        entry = rules.setdefault(sel, {})
        if cm:
            entry["color"] = cm.group(1).strip()
        if bm:
            entry["background"] = bm.group(1).strip()
    return rules


def find_body_bg(css_text: str, fallback: str = "#ffffff") -> str:
    m = re.search(r"\bbody\s*\{([^}]+)\}", css_text, re.IGNORECASE)
    if m:
        bm = BG_DECL_RE.search(m.group(1))
        if bm:
            return bm.group(1).strip()
    return fallback


# ----------------------------------------------------------------------
# Per-file checks
# ----------------------------------------------------------------------


HTML_TAG_RE = re.compile(r"<html\b([^>]*)>", re.IGNORECASE)
IMG_RE = re.compile(r"<img\b([^>]*)/?>", re.IGNORECASE | re.DOTALL)
HEADING_RE = re.compile(r"<h([1-6])\b", re.IGNORECASE)
PRESENT_RE = re.compile(r"<(/?)([ib])\b[^>]*>")
ATTR_RE = re.compile(r'(\w[\w:-]*)\s*=\s*"([^"]*)"')


def check_lang(text: str) -> str | None:
    """Return None if conformant, else a description of what's missing."""
    m = HTML_TAG_RE.search(text)
    if not m:
        return "no <html> root tag found"
    attrs = dict(ATTR_RE.findall(m.group(1)))
    if "lang" in attrs or "xml:lang" in attrs:
        return None
    return "missing lang and xml:lang attributes"


def check_images(text: str) -> list[str]:
    """Return a list of <img> snippets that lack alt=."""
    bad = []
    for m in IMG_RE.finditer(text):
        attrs = dict(ATTR_RE.findall(m.group(1)))
        if "alt" not in attrs:
            snippet = m.group(0)[:80]
            bad.append(snippet)
    return bad


def check_heading_hierarchy(text: str) -> list[str]:
    """Return descriptions of any heading-level skips inside the file."""
    levels = [int(m.group(1)) for m in HEADING_RE.finditer(text)]
    skips = []
    seen_max = 0  # highest level (lowest number) we've seen
    for i, lvl in enumerate(levels):
        if seen_max == 0:
            seen_max = lvl
            continue
        # A "skip" is when we go to a deeper level (higher number) more
        # than 1 step beyond what we've established.
        if lvl > seen_max + 1:
            skips.append(f"h{seen_max} → h{lvl} (skipped {seen_max + 1})")
        if lvl < seen_max:
            seen_max = lvl
        elif lvl == seen_max + 1:
            seen_max = lvl
    return skips


def check_presentational(text: str) -> int:
    """Count <b>/<i> opening tags (closing tags excluded)."""
    return sum(
        1
        for m in PRESENT_RE.finditer(text)
        if m.group(1) == ""  # opening tags only
    )


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(
        description="Accessibility audit (WCAG 2.1 / EPUB Accessibility 1.1).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--epub-dir",
        type=Path,
        default=EPUB_DIR,
        help="directory of unpacked EPUB (default: epub_working/)",
    )
    p.add_argument("--check", choices=CHECKS, help="run only one check")
    p.add_argument("--bg-color", default=None, help="override assumed body background (default: from CSS or #fff)")
    p.add_argument("--strict", action="store_true", help="fail on WARN as well as ERROR")
    p.add_argument("--quiet", action="store_true", help="only print the summary line")
    p.add_argument("--verbose", action="store_true", help="show all findings, not first --max-show")
    p.add_argument("--max-show", type=int, default=20, help="cap on findings displayed (default 20)")
    args = p.parse_args()

    if not args.epub_dir.is_dir():
        print(f"{RED}ERROR: not a directory: {args.epub_dir}{RESET}", file=sys.stderr)
        sys.exit(2)

    files = sorted(args.epub_dir.glob("*.html")) + sorted(args.epub_dir.glob("*.xhtml"))
    if not files:
        print(f"{RED}ERROR: no HTML files in {args.epub_dir}{RESET}", file=sys.stderr)
        sys.exit(2)

    findings = []  # (check, severity, where, detail)
    counters: Counter = Counter()

    # --- Per-file checks
    for f in files:
        text = f.read_text(encoding="utf-8")
        rel = f.name

        # lang
        if not args.check or args.check == "lang":
            res = check_lang(text)
            if res:
                findings.append(("lang", "ERROR", rel, res))

        # alt-text
        if not args.check or args.check == "alt-text":
            for snippet in check_images(text):
                findings.append(("alt-text", "ERROR", rel, snippet))

        # heading-skip
        if not args.check or args.check == "heading-skip":
            for skip in check_heading_hierarchy(text):
                findings.append(("heading-skip", "WARN", rel, skip))

        # presentational (count, not per-occurrence)
        if not args.check or args.check == "presentational":
            n = check_presentational(text)
            if n > 0:
                counters[("presentational", rel)] = n

    # presentational rollup
    if not args.check or args.check == "presentational":
        for (check, where), n in sorted(counters.items()):
            findings.append((check, "WARN", where, f"{n} <b>/<i> opening tag(s)"))

    # --- Contrast (CSS-driven, single pass)
    if not args.check or args.check == "contrast":
        css_path = args.epub_dir / "stylesheet.css"
        if not css_path.is_file():
            findings.append(("contrast", "ERROR", "stylesheet.css", "missing"))
        else:
            css_text = css_path.read_text(encoding="utf-8")
            bg_str = args.bg_color or find_body_bg(css_text, fallback="#ffffff")
            bg_rgb = parse_color(bg_str)
            if bg_rgb is None:
                findings.append(("contrast", "ERROR", "stylesheet.css", f"unparseable body bg {bg_str!r}"))
            else:
                rules = extract_marker_colors(css_text)
                for sel in sorted(rules):
                    fg_str = rules[sel].get("color")
                    if not fg_str:
                        continue
                    fg_rgb = parse_color(fg_str)
                    if fg_rgb is None:
                        findings.append(
                            ("contrast", "ERROR", "stylesheet.css", f".{sel}: unparseable color {fg_str!r}")
                        )
                        continue
                    ratio = contrast_ratio(fg_rgb, bg_rgb)
                    if ratio < 4.5:
                        findings.append(
                            (
                                "contrast",
                                "ERROR",
                                "stylesheet.css",
                                f".{sel}: {fg_str} on {bg_str} = {ratio:.2f}:1 (need ≥ 4.5)",
                            )
                        )

    # --- Output
    n_err = sum(1 for f in findings if f[1] == "ERROR")
    n_warn = sum(1 for f in findings if f[1] == "WARN")

    if findings and not args.quiet:
        # Group identical (check, where) descriptions for cleaner output
        limit = None if args.verbose else args.max_show
        shown = findings if limit is None else findings[:limit]
        for check, sev, where, detail in shown:
            color = RED if sev == "ERROR" else YELLOW
            print(f"  {color}{where}: {check}{RESET} — {detail}")
        if limit is not None and len(findings) > limit:
            print(f"  … {len(findings) - limit} more (re-run with --verbose)")

    bad = n_err > 0 or (args.strict and n_warn > 0)
    if bad:
        color, sym = RED, "✗"
    elif findings:
        color, sym = YELLOW, "⚠"
    else:
        color, sym = GREEN, "✓"
    print(f"\n{color}{sym} check_a11y: files={len(files)}  errors={n_err}  warnings={n_warn}{RESET}")
    if findings:
        by_check = Counter(f[0] for f in findings)
        parts = [f"{c}: {n}" for c, n in by_check.most_common()]
        print("  " + "  ".join(parts))

    if bad:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
