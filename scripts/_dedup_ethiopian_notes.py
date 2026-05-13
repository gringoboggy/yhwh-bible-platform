"""γ.4.6.B-hotfix — dedup duplicate comm-ethiopian tuples in content/notes/*.py.

Cause: scripts/batch_promote_xrefs.py + scripts/promote.py are non-idempotent.
Each re-run of the χ-cluster (run_ethiopian_at_scale.py → batch_promote_xrefs.py)
re-promotes every source entry with the NEXT available suffix letter ('c', 'd',
'e', ...). γ.4.6's first ship added 45 unique Cyril-on-Matthew. γ.4.6.B's
ship re-ran batch_promote and (a) added 50 new γ.4.6.B Sermon entries, but
ALSO (b) re-duplicated all 45 γ.4.6 entries + similarly polluted every
γ.4 source-book.

This script reads each notes/*.py via ast, identifies comm-ethiopian tuples
that duplicate an earlier-occurring (chapter, verse, kind, body, attribution)
tuple, and removes them by line-slicing the source text. Preserves all
non-tuple formatting (docstring, imports, comments, NOTES_X aliases).
Idempotent — re-running this script on a clean file is a no-op.

Run from project root: python scripts/_dedup_ethiopian_notes.py
"""

from __future__ import annotations

import ast
import os
from pathlib import Path

NOTES_DIR = Path("content") / "notes"


def dedup_one(path: Path) -> tuple[int, int]:
    """Returns (pre_count, post_count) of comm-ethiopian notes."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    # Find the NOTES = [...] assignment
    notes_node = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            tgt = node.targets[0]
            if isinstance(tgt, ast.Name) and tgt.id == "NOTES":
                notes_node = node
                break
    if notes_node is None or not isinstance(notes_node.value, ast.List):
        return (0, 0)

    # Walk tuples, identifying duplicates of comm-ethiopian by
    # (chapter, verse, body, attribution). The kind is implied
    # (we only inspect comm-ethiopian entries).
    seen_keys: set = set()
    drop_ranges: list[tuple[int, int]] = []  # (start_line, end_line), 1-indexed inclusive
    pre_count = 0
    post_count = 0
    for elt in notes_node.value.elts:
        if not isinstance(elt, ast.Tuple):
            continue
        try:
            t = ast.literal_eval(elt)
        except (ValueError, SyntaxError):
            continue
        kind = t[4] if len(t) > 4 else None
        if kind != "comm-ethiopian":
            continue
        pre_count += 1
        body = t[7] if len(t) > 7 else ""
        attr = t[8] if len(t) > 8 else ""
        key = (t[0], t[1], kind, body, attr)
        if key in seen_keys:
            drop_ranges.append((elt.lineno, elt.end_lineno))
        else:
            seen_keys.add(key)
            post_count += 1

    if not drop_ranges:
        return (pre_count, post_count)

    # Slice the source by lines, skipping the drop ranges AND the
    # trailing comma+newline that may follow each tuple's closing
    # paren. Each tuple in the list is followed by ",\n" (with
    # possible whitespace). We need to remove that too, else we get
    # leftover empty separators.
    lines = source.splitlines(keepends=True)
    # 1-indexed line removal — compute drop-line set
    drop_lines: set[int] = set()
    for start, end in drop_ranges:
        for lineno in range(start, end + 1):
            drop_lines.add(lineno)
        # Also drop the trailing ',\n' on the line AFTER the closing
        # paren if it consists ONLY of indent + ',' (the typical
        # ruff-formatted tuple closing pattern for lists).
        # Actually, the closing line is typically '    ),' itself —
        # the comma is on the same line as the close-paren. So we
        # don't need to drop an extra line. But check the NEXT line
        # — if it's blank or whitespace-only, leave it; the file
        # won't have a parse error from a stray blank.

    kept = [line for i, line in enumerate(lines, start=1) if i not in drop_lines]
    new_source = "".join(kept)

    # Verify the result is still parseable. If not, abort this file
    # (don't trash a working file by writing broken content).
    try:
        ast.parse(new_source)
    except SyntaxError as e:
        print(f"  ✗ {path.stem}: dedup produced syntax error: {e}; SKIPPING (no changes written)")
        return (pre_count, pre_count)

    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(new_source, encoding="utf-8")
    os.replace(tmp, path)

    return (pre_count, post_count)


def main() -> None:
    total_pre = 0
    total_post = 0
    for f in sorted(NOTES_DIR.glob("*.py")):
        if f.name == "__init__.py":
            continue
        pre, post = dedup_one(f)
        if pre != post:
            print(f"  {f.stem}: {pre} → {post} (-{pre - post})")
        total_pre += pre
        total_post += post
    print()
    print(f"TOTAL comm-ethiopian: {total_pre} → {total_post} (-{total_pre - total_post})")


if __name__ == "__main__":
    main()
