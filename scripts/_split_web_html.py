#!/usr/bin/env python3
"""One-shot extractor for the web.py split refactor.

Reads scripts/web.py, finds all <NAME>_HTML = r-string-triple-quote
constants, extracts each into scripts/templates/<lowername>.py,
and replaces the original definition with an import.

Re-exports preserve existing `from scripts.web import OPS_HTML`
call sites — no test or downstream module needs to change.

Usage:
    python3 scripts/_split_web_html.py            # dry-run
    python3 scripts/_split_web_html.py --apply    # commit
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WEB_PY = REPO / "scripts" / "web.py"
TEMPLATES_DIR = REPO / "scripts" / "templates"


def find_html_constants(text: str) -> list[tuple[str, int, int, str]]:
    """Find every _HTML constant. Returns list of (name, start_byte,
    end_byte_inclusive_of_closing_quotes, body_string)."""
    out = []
    # Match `^NAME_HTML = r"""` then find the matching closing triple-quote
    pattern = re.compile(r'^([A-Z_]+_HTML)\s*=\s*r"""', re.MULTILINE)
    for m in pattern.finditer(text):
        name = m.group(1)
        body_start = m.end()
        # Find the next triple-quote (raw strings can't contain """)
        close = text.find('"""', body_start)
        if close == -1:
            raise RuntimeError(f"unclosed triple-quote for {name}")
        body = text[body_start:close]
        decl_start = m.start()
        decl_end = close + 3  # include the closing """
        out.append((name, decl_start, decl_end, body))
    return out


def template_filename(name: str) -> str:
    """OPS_HTML → ops, INDEX_HTML → index, APIHELP_HTML → apihelp"""
    return name.removesuffix("_HTML").lower()


def main(apply: bool) -> int:
    if not WEB_PY.is_file():
        print(f"ERROR: {WEB_PY} not found")
        return 1

    text = WEB_PY.read_text(encoding="utf-8")
    constants = find_html_constants(text)

    if not constants:
        print("No _HTML constants found — nothing to do")
        return 0

    print(f"Found {len(constants)} HTML constants in {WEB_PY.name}:")
    for name, _, _, body in constants:
        line_count = body.count("\n") + 1
        fname = template_filename(name)
        print(f"  {name:20} → scripts/templates/{fname}.py  ({line_count} lines)")
    print()

    # Build the imports block to insert in web.py (alphabetical by source path)
    template_names = sorted([(template_filename(n), n) for n, _, _, _ in constants])
    imports_block = "\n".join(
        f"from scripts.templates.{fname} import {const_name}" for fname, const_name in template_names
    )

    if not apply:
        print("DRY-RUN — pass --apply to commit. Plan:")
        print(f"  1. Create {TEMPLATES_DIR}/__init__.py (empty)")
        print(f"  2. Create {len(constants)} files under {TEMPLATES_DIR}/")
        print(f"  3. Replace each constant block in web.py with an import line")
        print(f"  4. Re-export block (for `from scripts.web import X` callers)")
        print(f"  5. Inserted imports block (sample):")
        for line in imports_block.split("\n")[:5]:
            print(f"     {line}")
        if len(imports_block.split("\n")) > 5:
            print(f"     ... ({len(constants) - 5} more)")
        return 0

    # APPLY
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    init_path = TEMPLATES_DIR / "__init__.py"
    if not init_path.exists():
        init_path.write_text(
            '"""Template HTML modules — extracted from scripts/web.py\n'
            "during the web.py split refactor (2026-05-07).\n"
            "\n"
            "Each module exports a single <NAME>_HTML constant. The\n"
            "parent scripts/web.py re-imports them so existing\n"
            "`from scripts.web import <NAME>_HTML` call sites continue\n"
            "to work without modification.\n"
            '"""\n'
        )

    # Write each template file
    for name, _, _, body in constants:
        fname = template_filename(name)
        out_path = TEMPLATES_DIR / f"{fname}.py"
        out_path.write_text(
            f'"""HTML for /{fname} console — extracted from scripts/web.py\n'
            f"during the web.py split refactor (2026-05-07).\n"
            f"\n"
            f"Re-imported by scripts/web.py for back-compat with existing\n"
            f"`from scripts.web import {name}` callers.\n"
            f'"""\n'
            f"\n"
            f'{name} = r"""{body}"""\n',
            encoding="utf-8",
        )
        print(f"  wrote {out_path.relative_to(REPO)}")

    # Now rewrite web.py: replace each constant block with NOTHING (we'll
    # insert one consolidated imports block at the top of the constants
    # area). Walk constants in REVERSE order so byte offsets remain valid.
    new_text = text
    for name, decl_start, decl_end, _ in sorted(constants, key=lambda x: -x[1]):
        new_text = new_text[:decl_start] + new_text[decl_end:]

    # Insert the consolidated imports block at the position of the FIRST
    # constant's old start. Find that position in the new_text by
    # locating the surrounding context.
    # Simpler: find the first `_HTML = r"""` we just deleted by looking for
    # the leading section header comment. Use a known anchor: the
    # UI_DEFENSE_PRELUDE definition stays put; insert imports right after it.
    anchor = 'UI_DEFENSE_PRELUDE = r"""'
    anchor_pos = new_text.find(anchor)
    if anchor_pos == -1:
        # Fallback: find end of imports block
        # Insert after last `import ` line at module top
        m = re.search(r"^(import|from)\s.*\n(?!(import|from))", new_text, re.MULTILINE)
        if not m:
            raise RuntimeError("can't locate insertion point")
        anchor_pos = m.end()
        insert_at = anchor_pos
    else:
        # Find the closing """ of UI_DEFENSE_PRELUDE
        prelude_close = new_text.find('"""', anchor_pos + len(anchor))
        if prelude_close == -1:
            raise RuntimeError("UI_DEFENSE_PRELUDE not closed")
        insert_at = prelude_close + 3
        # Skip past trailing newlines so block lands on its own
        while insert_at < len(new_text) and new_text[insert_at] == "\n":
            insert_at += 1

    block = (
        "\n\n"
        "# ω.0.8 — web.py split refactor: HTML constants moved to\n"
        "# scripts/templates/<name>.py during the 2026-05-07 split.\n"
        "# These imports preserve back-compat with existing\n"
        "# `from scripts.web import <NAME>_HTML` callers.\n"
        f"{imports_block}\n\n"
    )
    new_text = new_text[:insert_at] + block + new_text[insert_at:]

    WEB_PY.write_text(new_text, encoding="utf-8")
    print(f"\n  wrote scripts/web.py: removed {sum(c[2] - c[1] for c in constants)} bytes, inserted {len(block)} bytes")
    print(f"  template files: {len(constants)}")
    return 0


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    sys.exit(main(apply))
