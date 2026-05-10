#!/usr/bin/env python3
"""ω.29 — content directory health checker.

Wholesale audit of `content/` for retail-grade integrity. Five
sub-checks run independently; each surfaces drift the existing
linters / validators don't catch:

  1. ``notes_parse``      — every ``content/notes/*.py`` is safely
                            decodable via ``ast.literal_eval``. A
                            note file that snuck a function call or
                            other arbitrary expression past code
                            review would not be caught by
                            validate_schemas (only YAML), notes_io
                            (which loads on-demand), or the runtime
                            (which would fail at first read).
  2. ``translations_meta`` — every ``content/translations/<id>/``
                            has a ``_meta.yaml`` parseable as YAML
                            with ``id`` + ``title`` + ``license``.
  3. ``cover_files``      — every ``cover_image`` / per-book cover
                            path referenced in editions.yaml
                            resolves to a real file under
                            ``content/covers/``. Path-traversal-safe
                            (paths must stay inside the safe root).
  4. ``candidates_json``  — every ``content/candidates/*.json``
                            parses as valid JSON and has the
                            top-level shape the promoter expects
                            (``book``, ``chapter``, ``candidates``).
  5. ``orphan_notes``     — every ``content/notes/*.py`` has a
                            matching book code in books.yaml.
                            Stray files (typo, leftover from a
                            renamed book) flag.

Per CLAUDE_PROJECT_RULES §10 ("Standard library only on the
backend") this uses only ``ast`` + ``json`` + ``re`` + ``yaml``
(yaml is already in the dev runtime via PyYAML). No new deps.

Exit codes:
  0 — every check passes
  1 — at least one check fails

Usage::

    python scripts/check_content.py
    python scripts/check_content.py --json
    python scripts/check_content.py --check notes_parse
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Optional

import yaml

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_CONTENT = _REPO / "content"


# ----------------------------------------------------------------------
# Sub-checks — each returns the standard
# ``{id, name, status, message, violations}`` shape so the aggregator
# can fold them into a uniform dashboard payload.
# ----------------------------------------------------------------------


def check_notes_parse(*, content_root: Optional[Path] = None) -> dict:
    """Every ``content/notes/*.py`` decodes cleanly via
    ``ast.literal_eval``. Flags files that snuck an arbitrary
    expression (function call, variable reference, comprehension)
    past review."""
    base = (content_root or _CONTENT) / "notes"
    violations: list[dict] = []
    n_total = 0
    if not base.is_dir():
        return _result(
            "notes_parse",
            "Notes files parse via ast.literal_eval",
            "pass",
            "no notes/ directory",
            [],
        )
    for py in sorted(base.glob("*.py")):
        if py.name == "__init__.py":
            continue
        n_total += 1
        try:
            text = py.read_text(encoding="utf-8")
        except OSError as e:
            violations.append({"file": py.name, "issue": f"unreadable: {e}"})
            continue
        try:
            tree = ast.parse(text, filename=str(py))
        except SyntaxError as e:
            violations.append({"file": py.name, "issue": f"syntax error: {e.msg} (line {e.lineno})"})
            continue
        notes_node = _find_module_assignment(tree, "NOTES")
        if notes_node is None:
            violations.append({"file": py.name, "issue": "no top-level `NOTES = ...` assignment"})
            continue
        try:
            ast.literal_eval(notes_node)
        except (ValueError, SyntaxError) as e:
            violations.append(
                {
                    "file": py.name,
                    "issue": f"NOTES is not literal-eval-safe: {e}",
                }
            )
    msg = (
        f"{len(violations)} note file(s) failed parse / literal-eval"
        if violations
        else f"all {n_total} note file(s) parse safely"
    )
    return _result(
        "notes_parse",
        "Notes files parse via ast.literal_eval",
        "fail" if violations else "pass",
        msg,
        violations,
    )


def check_translations_meta(*, content_root: Optional[Path] = None) -> dict:
    """Every translation directory has a parseable ``_meta.yaml``
    with the required fields."""
    base = (content_root or _CONTENT) / "translations"
    violations: list[dict] = []
    n_total = 0
    if not base.is_dir():
        return _result(
            "translations_meta",
            "Translation _meta.yaml integrity",
            "pass",
            "no translations/ directory",
            [],
        )
    REQUIRED_FIELDS = ("id", "title", "license")
    for tx_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        # Skip `sources/` — that's the input archive, not a translation
        if tx_dir.name == "sources":
            continue
        n_total += 1
        meta = tx_dir / "_meta.yaml"
        if not meta.is_file():
            violations.append({"translation": tx_dir.name, "issue": "_meta.yaml missing"})
            continue
        try:
            data = yaml.safe_load(meta.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            violations.append({"translation": tx_dir.name, "issue": f"YAML parse error: {e}"})
            continue
        if not isinstance(data, dict):
            violations.append({"translation": tx_dir.name, "issue": "top-level value is not a mapping"})
            continue
        missing = [f for f in REQUIRED_FIELDS if not isinstance(data.get(f), str) or not data.get(f).strip()]
        if missing:
            violations.append(
                {
                    "translation": tx_dir.name,
                    "issue": f"missing required field(s): {', '.join(missing)}",
                }
            )
    msg = (
        f"{len(violations)} translation(s) with _meta.yaml issues"
        if violations
        else f"all {n_total} translation(s) have valid _meta.yaml"
    )
    return _result(
        "translations_meta",
        "Translation _meta.yaml integrity",
        "fail" if violations else "pass",
        msg,
        violations,
    )


_BOOK_COVER_RE = re.compile(r"^([a-z0-9]+)=(.+)$")


def check_cover_files(*, content_root: Optional[Path] = None) -> dict:
    """Every ``cover_image`` and per-book cover path in editions.yaml
    resolves to a file under ``content/covers/``. Path-traversal-safe."""
    base = content_root or _CONTENT
    editions_path = base / "editions.yaml"
    violations: list[dict] = []
    if not editions_path.is_file():
        return _result(
            "cover_files",
            "Cover-image references resolve to real files",
            "pass",
            "no editions.yaml",
            [],
        )
    try:
        data = yaml.safe_load(editions_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        return _result(
            "cover_files",
            "Cover-image references resolve to real files",
            "fail",
            f"editions.yaml parse error: {e}",
            [{"file": "editions.yaml", "issue": str(e)}],
        )
    editions = data.get("editions") or []
    safe_root = (base / "covers").resolve()
    n_paths = 0
    for ed in editions:
        if not isinstance(ed, dict):
            continue
        ed_id = ed.get("id") or "<no-id>"
        # Main cover
        main = ed.get("cover_image")
        if isinstance(main, str) and main.strip():
            n_paths += 1
            if not _path_resolves_inside(base / main, safe_root):
                violations.append(
                    {"edition_id": ed_id, "kind": "main_cover", "path": main, "issue": "missing or unsafe"}
                )
        # Per-book covers
        per_book = ed.get("book_covers") or []
        if isinstance(per_book, list):
            for entry in per_book:
                if not isinstance(entry, str):
                    continue
                m = _BOOK_COVER_RE.match(entry.strip())
                if not m:
                    violations.append({"edition_id": ed_id, "kind": "book_cover", "entry": entry, "issue": "malformed"})
                    continue
                book_code, path = m.group(1), m.group(2)
                n_paths += 1
                if not _path_resolves_inside(base / path, safe_root):
                    violations.append(
                        {
                            "edition_id": ed_id,
                            "kind": "book_cover",
                            "book": book_code,
                            "path": path,
                            "issue": "missing or unsafe",
                        }
                    )
    msg = (
        f"{len(violations)} cover-path issue(s) across {n_paths} reference(s)"
        if violations
        else f"all {n_paths} cover-path reference(s) resolve cleanly"
    )
    return _result(
        "cover_files",
        "Cover-image references resolve to real files",
        "fail" if violations else "pass",
        msg,
        violations,
    )


def check_candidates_json(*, content_root: Optional[Path] = None) -> dict:
    """Every candidate JSON parses + has the top-level shape the
    promoter expects."""
    base = (content_root or _CONTENT) / "candidates"
    violations: list[dict] = []
    n_total = 0
    if not base.is_dir():
        return _result(
            "candidates_json",
            "Candidate JSON files well-formed",
            "pass",
            "no candidates/ directory",
            [],
        )
    REQUIRED_TOP = ("book", "chapter", "candidates")
    for jf in sorted(base.glob("*.json")):
        n_total += 1
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            violations.append({"file": jf.name, "issue": f"JSON parse error: {e}"})
            continue
        if not isinstance(data, dict):
            violations.append({"file": jf.name, "issue": "top-level value is not an object"})
            continue
        missing = [k for k in REQUIRED_TOP if k not in data]
        if missing:
            violations.append({"file": jf.name, "issue": f"missing top-level key(s): {', '.join(missing)}"})
            continue
        if not isinstance(data["candidates"], list):
            violations.append({"file": jf.name, "issue": "`candidates` is not a list"})
    msg = (
        f"{len(violations)} candidate file(s) malformed"
        if violations
        else f"all {n_total} candidate file(s) well-formed"
    )
    return _result(
        "candidates_json",
        "Candidate JSON files well-formed",
        "fail" if violations else "pass",
        msg,
        violations,
    )


def check_orphan_notes(*, content_root: Optional[Path] = None) -> dict:
    """Every ``content/notes/*.py`` file's basename matches a book
    code in books.yaml. Stray files surface as orphans."""
    base = content_root or _CONTENT
    notes_dir = base / "notes"
    books_path = base / "books.yaml"
    violations: list[dict] = []
    if not notes_dir.is_dir():
        return _result(
            "orphan_notes",
            "Notes files match books.yaml registry",
            "pass",
            "no notes/ directory",
            [],
        )
    if not books_path.is_file():
        return _result(
            "orphan_notes",
            "Notes files match books.yaml registry",
            "fail",
            "books.yaml missing — cannot verify orphans",
            [{"issue": "books.yaml missing"}],
        )
    try:
        books_text = books_path.read_text(encoding="utf-8")
    except OSError as e:
        return _result(
            "orphan_notes",
            "Notes files match books.yaml registry",
            "fail",
            f"books.yaml unreadable: {e}",
            [{"issue": str(e)}],
        )
    # The project's books.yaml uses the custom flat-list parser. A
    # cheap regex scan for `code: <id>` is sufficient — we don't need
    # full schema validation here, just the set of legal codes.
    book_codes = set(re.findall(r"^\s*-?\s*code:\s*([a-z0-9]+)\s*$", books_text, re.MULTILINE))
    n_total = 0
    for py in sorted(notes_dir.glob("*.py")):
        if py.name == "__init__.py":
            continue
        n_total += 1
        code = py.stem
        if code not in book_codes:
            violations.append({"file": py.name, "code": code, "issue": "code not in books.yaml"})
    msg = f"{len(violations)} orphan notes file(s)" if violations else f"all {n_total} notes file(s) match a book code"
    return _result(
        "orphan_notes",
        "Notes files match books.yaml registry",
        "fail" if violations else "pass",
        msg,
        violations,
    )


# ----------------------------------------------------------------------
# Aggregator
# ----------------------------------------------------------------------


_CHECKS: dict[str, Callable[..., dict]] = {
    "notes_parse": check_notes_parse,
    "translations_meta": check_translations_meta,
    "cover_files": check_cover_files,
    "candidates_json": check_candidates_json,
    "orphan_notes": check_orphan_notes,
}


def run_all(
    *,
    only: Optional[str] = None,
    content_root: Optional[Path] = None,
) -> dict:
    """Run every sub-check (or just the named one). Returns
    ``{checks, summary}`` per the §9 meta-tool convention.

    ``content_root`` is for tests; production reads ``content/``.
    """
    if only is not None and only not in _CHECKS:
        return {
            "status": "error",
            "code": "unknown_check",
            "message": f"unknown check {only!r}; valid: {sorted(_CHECKS.keys())}",
            "checks": [],
            "summary": {"total": 0, "pass": 0, "warn": 0, "fail": 0, "clean": False},
        }
    results: list[dict] = []
    for name, fn in _CHECKS.items():
        if only and name != only:
            continue
        results.append(fn(content_root=content_root))
    n_pass = sum(1 for r in results if r["status"] == "pass")
    n_warn = sum(1 for r in results if r["status"] == "warn")
    n_fail = sum(1 for r in results if r["status"] == "fail")
    return {
        "checks": results,
        "summary": {
            "total": len(results),
            "pass": n_pass,
            "warn": n_warn,
            "fail": n_fail,
            "clean": n_fail == 0 and n_warn == 0,
        },
    }


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _result(
    check_id: str,
    name: str,
    status: str,
    message: str,
    violations: list[dict],
) -> dict:
    return {
        "id": check_id,
        "name": name,
        "status": status,
        "message": message,
        "violations": violations,
    }


def _find_module_assignment(tree: ast.AST, target_name: str) -> Optional[ast.AST]:
    """Find ``<target_name> = <expr>`` at module level; return the
    RHS expression node, or None if not present."""
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == target_name:
                    return node.value
    return None


def _path_resolves_inside(candidate: Path, safe_root: Path) -> bool:
    """True iff ``candidate`` resolves to an existing file inside
    ``safe_root``. Rejects ``..`` traversal and absolute paths that
    escape the sandbox."""
    try:
        resolved = candidate.resolve()
    except OSError:
        return False
    if not resolved.is_file():
        return False
    try:
        resolved.relative_to(safe_root)
    except ValueError:
        return False
    return True


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check_content",
        description=(
            "ω.29 — wholesale audit of content/ for retail-grade integrity. "
            "Notes parse safely, translations have _meta.yaml, cover paths "
            "resolve, candidate JSONs are well-formed, no orphan notes files."
        ),
    )
    parser.add_argument("--json", action="store_true", help="machine-readable JSON output")
    parser.add_argument(
        "--check",
        default=None,
        choices=sorted(_CHECKS.keys()),
        help="run a single sub-check only",
    )
    args = parser.parse_args(argv)

    result = run_all(only=args.check)
    if result.get("status") == "error":
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"  ✗ {result.get('message')}")
        return 2

    if args.json:
        print(json.dumps(result, indent=2, default=str))
        return 0 if result["summary"]["clean"] else 1

    summary = result["summary"]
    if summary["clean"]:
        print(f"  ✓ all {summary['total']} content-health check(s) pass")
        for c in result["checks"]:
            print(f"    · {c['name']}: {c['message']}")
        return 0

    print(f"  ✗ {summary['fail']} check(s) failed, {summary['warn']} warned (of {summary['total']}):")
    for c in result["checks"]:
        if c["status"] == "pass":
            print(f"    ✓ {c['name']}: {c['message']}")
            continue
        tag = "✗" if c["status"] == "fail" else "⚠"
        print(f"    {tag} {c['name']}: {c['message']}")
        for v in c["violations"][:5]:
            print(f"        · {v}")
        if len(c["violations"]) > 5:
            print(f"        … and {len(c['violations']) - 5} more")
    return 1


if __name__ == "__main__":
    sys.exit(main())
