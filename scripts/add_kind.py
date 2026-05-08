#!/usr/bin/env python3
"""
add_kind.py — register a new commentary note kind.

A "kind" is a category of note with its own inline glyph and CSS styling
(e.g. comm=◇, word=⌘, source=✧). Adding a new kind makes it immediately
available to scripts/add_note.py and to both injectors.

What this script does:
  1. Validate that the new kind code doesn't already exist.
  2. Append the entry to content/kinds.yaml.
  3. Append matching CSS rules to epub_working/stylesheet.css —
     a `.marker-<code>` rule (color + light bg for the inline glyph)
     and a `.note-<code>` rule (border-left accent for the aside).
  4. Optionally re-audit the project (--verify).

The injectors load kinds dynamically from kinds.yaml, so no code changes
are needed once the registration is complete.

Examples:
  # Add a "variant" kind with the dagger glyph and a forest-green accent:
  python3 scripts/add_kind.py --code variant --symbol "†" \\
      --label "Variant" --color "#2D5A3D" --verify

  # Preview only — show what would change, don't write:
  python3 scripts/add_kind.py --code variant --symbol "†" --label V --color "#2D5A3D" --dry-run
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import config

KINDS_YAML = REPO_ROOT / "content" / "kinds.yaml"
STYLESHEET = REPO_ROOT / "epub_working" / "stylesheet.css"


def err(msg):
    print(f"\033[91merror:\033[0m {msg}", file=sys.stderr)
    sys.exit(1)


def hex_to_rgb_alpha(hex_color, alpha):
    """'#0B3D91' + 0.12 → 'rgba(11, 61, 145, 0.12)'."""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        err(f"--color must be a 6-digit hex like #0B3D91, got {hex_color!r}")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def append_to_kinds_yaml(code, symbol, note_class, marker_class, label, title_attr):
    """Append a new entry block to content/kinds.yaml. Format mirrors existing entries."""
    text = KINDS_YAML.read_text()
    if not text.endswith("\n"):
        text += "\n"

    def jdump(v):
        return json.dumps(v, ensure_ascii=False)

    block = (
        f"  - code: {code}\n"
        f"    symbol: {jdump(symbol)}\n"
        f"    note_class: {jdump(note_class)}\n"
        f"    marker_class: {jdump(marker_class)}\n"
        f"    label: {jdump(label)}\n"
        f"    title_attr: {jdump(title_attr)}\n"
    )
    # Ensure exactly one blank line before our new block
    if not text.endswith("\n\n"):
        text += "\n"
    text += block
    KINDS_YAML.write_text(text)
    return block


def append_to_stylesheet(code, color):
    """Append marker-<code> and note-<code> CSS rules to stylesheet.css."""
    text = STYLESHEET.read_text()
    bg = hex_to_rgb_alpha(color, 0.13)
    rules = (
        f"\n/* Added by scripts/add_kind.py — kind: {code} */\n"
        f".marker-{code} {{ color: {color}; background: {bg}; }}\n"
        f".note-{code}   {{ border-left: 3px solid {color}; padding-left: 0.7em; }}\n"
    )
    if not text.endswith("\n"):
        text += "\n"
    text += rules
    STYLESHEET.write_text(text)
    return rules


def main():
    p = argparse.ArgumentParser(
        description="Register a new commentary note kind.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n", 2)[2] if __doc__ else "",
    )
    p.add_argument(
        "--code",
        required=True,
        help="short identifier, e.g. 'variant' (lowercase letters/digits/underscore)",
    )
    p.add_argument("--symbol", required=True, help="single-character inline glyph (e.g. '†', '※', '◆')")
    p.add_argument("--label", required=True, help='label inside the aside (e.g. "Variant")')
    p.add_argument("--title-attr", default=None, help="tooltip for the noteref (defaults to --label)")
    p.add_argument(
        "--color",
        required=True,
        help="accent color in #RRGGBB hex (used for marker text and aside border)",
    )
    p.add_argument("--note-class", default=None, help="CSS class for the aside (default: note-<code>)")
    p.add_argument(
        "--marker-class",
        default=None,
        help="CSS class for the inline glyph (default: marker-<code>)",
    )
    p.add_argument("--dry-run", action="store_true", help="preview only — don't write any files")
    p.add_argument("--verify", action="store_true", help="run audit.py after registration")
    args = p.parse_args()

    # --- Validate ---
    if not re.fullmatch(r"[a-z][a-z0-9_]*", args.code):
        err(f"--code must be lowercase letters/digits/underscore starting with a letter, got {args.code!r}")
    existing = config.kinds_by_code()
    if args.code in existing:
        err(f"kind {args.code!r} already exists. Existing kinds: {sorted(existing)}")
    if len(args.symbol) > 4:
        err(f"--symbol should be a short glyph (1–2 chars typical), got {args.symbol!r} ({len(args.symbol)} chars)")
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", args.color):
        err(f"--color must be #RRGGBB hex, got {args.color!r}")
    note_class = args.note_class or f"note-{args.code}"
    marker_class = args.marker_class or f"marker-{args.code}"
    title_attr = args.title_attr or args.label

    # --- Preview ---
    print("Will register new kind:")
    print(f"  code         {args.code}")
    print(f"  symbol       {args.symbol}")
    print(f"  label        {args.label}")
    print(f"  title_attr   {title_attr}")
    print(f"  note_class   .{note_class}")
    print(f"  marker_class .{marker_class}")
    print(f"  color        {args.color}")
    print("\nPlanned CSS additions (stylesheet.css):")
    print(f"  .marker-{args.code} {{ color: {args.color}; background: {hex_to_rgb_alpha(args.color, 0.13)}; }}")
    print(f"  .note-{args.code}   {{ border-left: 3px solid {args.color}; padding-left: 0.7em; }}")

    if args.dry_run:
        print("\n(dry-run: no files modified)")
        return

    # --- Write ---
    yaml_block = append_to_kinds_yaml(args.code, args.symbol, note_class, marker_class, args.label, title_attr)
    print(f"\n✓ appended to {KINDS_YAML.relative_to(REPO_ROOT)}:")
    for ln in yaml_block.splitlines():
        print(f"    {ln}")

    css_block = append_to_stylesheet(args.code, args.color)
    print(f"\n✓ appended to {STYLESHEET.relative_to(REPO_ROOT)}:")
    for ln in css_block.splitlines():
        print(f"    {ln}")

    # --- Invalidate config cache so changes are visible to subsequent imports ---
    config.load_kinds.cache_clear()
    print(f"\nNew kind {args.code!r} is live. Use it with: scripts/add_note.py --kind {args.code} ...")

    if args.verify:
        import subprocess

        print("\n→ running audit ...")
        result = subprocess.run(["python3", "audit.py"], cwd=str(REPO_ROOT), capture_output=True, text=True)
        # Print last 8 lines
        print("\n".join(result.stdout.splitlines()[-8:]))


if __name__ == "__main__":
    main()
