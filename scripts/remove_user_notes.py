#!/usr/bin/env python3
"""Remove every 'User original' / 'User paraphrase…' note from content/notes/*.py.

These are machine-authored editorial notes that carry no public-domain source.
Per the 2026-06-28 user decision the shipped Bibles must carry ONLY genuinely
PD-sourced study notes, so this tool deletes exactly the note tuples whose
attribution (the optional 9th field) classifies as ``user`` — mirroring
``corpus_index._classify_attribution`` (attribution lower-strips to a
"user original" / "user paraphrase…" prefix).

It is surgical and reproducible: it removes each matching tuple by its AST
line-range (leaving every other byte of the file untouched) and then VERIFIES
the result by re-parsing — the remaining note count must equal the original
minus the removals, zero ``user`` notes may remain, and every kept note must be
byte-for-byte identical to before.

Usage::

    py -3 scripts/remove_user_notes.py --dry-run   # report only, write nothing
    py -3 scripts/remove_user_notes.py             # apply the removals
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
NOTES_DIR = REPO / "content" / "notes"


def _is_user_attr(attr: object) -> bool:
    """True iff this attribution is a machine-authored 'User' note.

    Mirrors ``corpus_index._classify_attribution`` returning ``'user'``.
    """
    s = (str(attr) if attr is not None else "").strip().lower()
    return s.startswith("user original") or s.startswith("user paraphrase")


def _notes_list_node(text: str, path: Path) -> ast.List | None:
    """Return the ``NOTES = [...]`` list node, or None."""
    tree = ast.parse(text, filename=str(path))
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "NOTES"
            and isinstance(node.value, ast.List)
        ):
            return node.value
    return None


def _user_elements(list_node: ast.List) -> list[ast.expr]:
    """The element nodes whose attribution classifies as 'user'."""
    out: list[ast.expr] = []
    for elt in list_node.elts:
        try:
            val = ast.literal_eval(elt)
        except (ValueError, SyntaxError):
            continue
        if isinstance(val, tuple) and len(val) >= 9 and _is_user_attr(val[8]):
            out.append(elt)
    return out


def process(path: Path, *, apply: bool) -> tuple[int, int]:
    """Remove 'user' notes from one file. Returns (removed, original_total)."""
    text = path.read_text(encoding="utf-8")
    list_node = _notes_list_node(text, path)
    if list_node is None:
        return 0, 0
    total = len(list_node.elts)
    remove = _user_elements(list_node)
    if not remove:
        return 0, total

    # Delete each matching tuple by its full line span (lineno..end_lineno,
    # inclusive — the line that holds ``),`` carries the list separator too).
    del_lines: set[int] = set()
    for elt in remove:
        assert elt.end_lineno is not None
        for ln in range(elt.lineno, elt.end_lineno + 1):
            del_lines.add(ln)
    lines = text.splitlines(keepends=True)
    new_text = "".join(l for i, l in enumerate(lines, start=1) if i not in del_lines)

    # --- verify (fail loudly rather than write a damaged file) ---
    old_notes = [ast.literal_eval(e) for e in list_node.elts]
    kept_old = [n for n in old_notes if not (isinstance(n, tuple) and len(n) >= 9 and _is_user_attr(n[8]))]
    new_list = _notes_list_node(new_text, path)
    assert new_list is not None, f"{path.name}: NOTES list lost after edit"
    new_notes = [ast.literal_eval(e) for e in new_list.elts]
    assert len(new_notes) == total - len(remove), (
        f"{path.name}: count mismatch {len(new_notes)} != {total - len(remove)}"
    )
    assert not _user_elements(new_list), f"{path.name}: user notes remain after edit"
    assert new_notes == kept_old, f"{path.name}: a kept note changed content"

    if apply:
        path.write_text(new_text, encoding="utf-8")
    return len(remove), total


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="report only; write nothing")
    args = ap.parse_args()

    files = sorted(NOTES_DIR.glob("*.py"))
    per: list[tuple[str, int, int]] = []
    total_removed = total_notes = 0
    for f in files:
        removed, total = process(f, apply=not args.dry_run)
        total_removed += removed
        total_notes += total
        if removed:
            per.append((f.name, removed, total))

    for name, removed, total in per:
        print(f"  {name:14} -{removed:<5} ({total} -> {total - removed})")
    verb = "WOULD remove" if args.dry_run else "removed"
    print(
        f"\n{verb} {total_removed} 'User' notes from {len(per)}/{len(files)} books "
        f"(corpus {total_notes} -> {total_notes - total_removed})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
