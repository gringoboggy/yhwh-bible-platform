"""bulk_inject — modify many ``*_HTML = r'''...'''`` constants at once.

Refactors the inline Python heredoc pattern that was used three times
during the omega series rollouts (corpus-progress widget, UI defense
prelude, and /compare nav link). Two operations:

  insert(file_path, content, *, before, marker, exempt={...})
      Insert `content` before `before` (a regex or literal substring)
      in every `*_HTML = r-string` constant body, idempotently.
      `marker` is a comment string already present in `content`; if
      it's already in the constant body, that constant is skipped
      (so re-runs don't double-inject).

  replace_between_markers(file_path, open_marker, close_marker,
                          new_content, *, exempt={...})
      Find `open_marker` … `close_marker` in each `*_HTML` constant
      body and replace the content between them with `new_content`.
      Used to update an already-injected block (like the UI defense
      prelude when it gains a new helper).

Both functions return a `{modified: int, skipped: int, file: str}`
stats dict. Both leave the file unchanged if no constants matched.

Phase ω.0.7 — added so the rollout pattern has a single source
of truth instead of three near-identical inline scripts.
"""

from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

# Match `<NAME>_HTML = r"""...content...""" `. Captures:
#   group(1)  the entire `NAME_HTML = r"""` opening
#   group(2)  the constant name (without _HTML suffix? — no, with)
#   group(3)  the body content
#   group(4)  the closing `"""`
HTML_CONSTANT_RE = re.compile(
    r'(^([A-Z_]+_HTML)\s*=\s*r""")(.*?)(""")',
    re.MULTILINE | re.DOTALL,
)

DEFAULT_EXEMPT = frozenset({
    # The editor at / has a different chrome and is intentionally
    # not part of the consoles cluster. Same exemption pattern as
    # ψ.3 (corpus widget) and ω.0.6 (UI defense prelude).
    "INDEX_HTML",
    # The shared prelude constant is itself an HTML-ish string but
    # not a console; never inject into it.
    "UI_DEFENSE_PRELUDE",
})


def insert(
    file_path: Path | str,
    content: str,
    *,
    before: str,
    marker: str,
    exempt: set[str] = None,
) -> dict:
    """Insert `content` before `before` in every console's _HTML body,
    skipping any whose body already contains `marker`.

    Args:
        file_path: file containing the `*_HTML = r-string` constants
        content: text to insert (should include `marker` somewhere
                  inside it, so re-runs are detectable)
        before: regex pattern OR literal substring to anchor the
                insertion before. If literal, it's the first occurrence
                of that exact substring.
        marker: idempotency marker. If a constant already contains
                this string in its body, that constant is left alone.
        exempt: set of constant names to never modify. Defaults to
                DEFAULT_EXEMPT.
    Returns:
        {"modified": int, "skipped": int, "file": str}
    """
    if exempt is None:
        exempt = set(DEFAULT_EXEMPT)
    p = Path(file_path)

    # If a directory: iterate over its .py files (post-split flow).
    # Aggregate stats. Skip __init__.py (no constants there).
    if p.is_dir():
        total_modified = 0
        total_skipped = 0
        for py in sorted(p.glob("*.py")):
            if py.name == "__init__.py":
                continue
            sub = insert(py, content, before=before,
                          marker=marker, exempt=exempt)
            total_modified += sub["modified"]
            total_skipped += sub["skipped"]
        return {"modified": total_modified, "skipped": total_skipped,
                "file": str(p)}

    text = p.read_text()

    # `before` may be a regex or a literal. Use literal-first for
    # predictability; only fall back to regex if the literal isn't
    # found and the string contains regex metacharacters that the
    # caller likely meant. Keep it simple: literal only for now.
    # (Callers can pass a literal that matches their target exactly.)

    modified = 0
    skipped = 0

    def _transform(match: re.Match) -> str:
        nonlocal modified, skipped
        head, name, body, tail = (
            match.group(1), match.group(2), match.group(3), match.group(4),
        )
        if name in exempt:
            skipped += 1
            return match.group(0)
        if marker in body:
            skipped += 1
            return match.group(0)
        if before in body:
            new_body = body.replace(before, content + before, 1)
            modified += 1
            return head + new_body + tail
        # Anchor not in this constant's body — append at end as
        # fallback (rare; usually the anchor is `</body>` which all
        # consoles have)
        skipped += 1
        return match.group(0)

    new_text = HTML_CONSTANT_RE.sub(_transform, text)
    if modified > 0:
        p.write_text(new_text)
    return {"modified": modified, "skipped": skipped, "file": str(p)}


def replace_between_markers(
    file_path: Path | str,
    open_marker: str,
    close_marker: str,
    new_content: str,
    *,
    exempt: set[str] = None,
) -> dict:
    """Replace whatever's between `open_marker` and `close_marker`
    in each console's _HTML body with `new_content`. Both markers
    must be string literals (not regex). The replacement region is
    *inclusive* of the markers themselves — i.e., open_marker and
    close_marker are removed and replaced with new_content (which
    typically contains its own fresh open and close markers).

    Used to update an already-injected block (e.g., refresh the
    UI defense prelude in every console after the constant has
    been edited).
    """
    if exempt is None:
        exempt = set(DEFAULT_EXEMPT)
    p = Path(file_path)

    # Directory mode for the post-split layout
    if p.is_dir():
        total_modified = 0
        total_skipped = 0
        for py in sorted(p.glob("*.py")):
            if py.name == "__init__.py":
                continue
            sub = replace_between_markers(
                py, open_marker, close_marker, new_content, exempt=exempt,
            )
            total_modified += sub["modified"]
            total_skipped += sub["skipped"]
        return {"modified": total_modified, "skipped": total_skipped,
                "file": str(p)}

    text = p.read_text()

    modified = 0
    skipped = 0

    def _transform(match: re.Match) -> str:
        nonlocal modified, skipped
        head, name, body, tail = (
            match.group(1), match.group(2), match.group(3), match.group(4),
        )
        if name in exempt:
            skipped += 1
            return match.group(0)
        oi = body.find(open_marker)
        if oi < 0:
            skipped += 1
            return match.group(0)
        ci = body.find(close_marker, oi + len(open_marker))
        if ci < 0:
            # Open marker found but close marker missing — don't
            # mangle the file; skip and let the caller see the
            # mismatch in the stats
            skipped += 1
            return match.group(0)
        ce = ci + len(close_marker)
        new_body = body[:oi] + new_content + body[ce:]
        modified += 1
        return head + new_body + tail

    new_text = HTML_CONSTANT_RE.sub(_transform, text)
    if modified > 0:
        p.write_text(new_text)
    return {"modified": modified, "skipped": skipped, "file": str(p)}


def list_constants(file_path: Path | str) -> list[str]:
    """Return the names of all `*_HTML = r-string` constants in
    the given file. If `file_path` is a directory, recursively
    scan every .py file inside it (returns the union, deduped,
    sorted) — supports the post-split layout where each constant
    lives in its own `scripts/templates/<name>.py` module.

    Useful for sanity-checking exempt sets and for the `--list`
    CLI mode."""
    p = Path(file_path)
    if p.is_dir():
        # Scan every .py inside (non-recursive: templates/ is flat)
        names: set[str] = set()
        for py in sorted(p.glob("*.py")):
            text = py.read_text(encoding="utf-8", errors="ignore")
            for m in HTML_CONSTANT_RE.finditer(text):
                names.add(m.group(2))
        return sorted(names)
    text = p.read_text(encoding="utf-8", errors="ignore")
    return [m.group(2) for m in HTML_CONSTANT_RE.finditer(text)]


def find_template_files(repo_root: Path | str) -> list[Path]:
    """Locate every Python file in the project that defines an
    `*_HTML` constant. Post-split, this is `scripts/templates/*.py`;
    pre-split fallback to `scripts/web.py`. Used by callers that
    want to operate on every console's template (the scaffolder's
    nav-rollout step is the canonical example).

    Returns a sorted list of Path objects."""
    root = Path(repo_root)
    templates_dir = root / "scripts" / "templates"
    if templates_dir.is_dir():
        return sorted(p for p in templates_dir.glob("*.py")
                       if p.name != "__init__.py")
    # Pre-split fallback
    web_py = root / "scripts" / "web.py"
    return [web_py] if web_py.is_file() else []


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Two modes: --insert and --replace.
    See module docstring for semantics."""
    parser = argparse.ArgumentParser(
        description="Bulk-modify *_HTML constants in a Python file.",
    )
    parser.add_argument(
        "file", type=Path,
        help="Python file containing the *_HTML constants",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_insert = sub.add_parser("insert", help="Insert content idempotently")
    p_insert.add_argument("--content-file", type=Path, required=True,
                           help="path to file whose contents are the snippet to insert")
    p_insert.add_argument("--before", required=True,
                           help="literal substring to anchor before (e.g. '</body>')")
    p_insert.add_argument("--marker", required=True,
                           help="idempotency marker (must be inside the snippet)")
    p_insert.add_argument("--exempt", action="append", default=[],
                           help="constant names to skip (repeatable)")

    p_replace = sub.add_parser("replace", help="Replace between markers")
    p_replace.add_argument("--content-file", type=Path, required=True)
    p_replace.add_argument("--open-marker", required=True)
    p_replace.add_argument("--close-marker", required=True)
    p_replace.add_argument("--exempt", action="append", default=[])

    p_list = sub.add_parser("list", help="List *_HTML constants in the file")

    args = parser.parse_args(argv)

    if args.cmd == "list":
        for name in list_constants(args.file):
            print(name)
        return 0

    exempt = set(DEFAULT_EXEMPT) | set(args.exempt or [])

    if args.cmd == "insert":
        content = args.content_file.read_text()
        if args.marker not in content:
            print(
                f"WARNING: marker {args.marker!r} not found in content; "
                f"re-running this command will re-inject (not idempotent).",
                file=sys.stderr,
            )
        result = insert(
            args.file, content,
            before=args.before, marker=args.marker, exempt=exempt,
        )
        print(f"insert: modified={result['modified']} skipped={result['skipped']}")
        return 0

    if args.cmd == "replace":
        new_content = args.content_file.read_text()
        result = replace_between_markers(
            args.file,
            args.open_marker, args.close_marker, new_content,
            exempt=exempt,
        )
        print(f"replace: modified={result['modified']} skipped={result['skipped']}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
