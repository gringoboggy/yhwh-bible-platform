#!/usr/bin/env python3
"""ω.30 — cache invalidation audit.

AST-walks `scripts/` for `@lru_cache` (or `@functools.lru_cache`)
decorators on top-level functions; for each cache, searches the
codebase for `<func>.cache_clear()` call sites that would
invalidate it. Reports caches without a clear path so the
developer can verify each is intentional.

A cache without a clear path isn't automatically wrong — some are
deliberately one-shot resolvers that only depend on the
environment (`paths.user_data_root`, `desktop_shell.detect_*`).
The whitelist at `scripts/.cache_audit_whitelist.py` documents
those; everything else needs an explicit clear site or the
audit fails.

Per CLAUDE_PROJECT_RULES §10 ("Standard library only on the
backend") this uses only `ast` + `re` — no external deps.

Usage::

    python scripts/audit_caches.py
    python scripts/audit_caches.py --json
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path


_REPO = Path(__file__).resolve().parent.parent
_SCRIPTS = _REPO / "scripts"
_WHITELIST_PATH = _REPO / "scripts" / ".cache_audit_whitelist.py"


# ----------------------------------------------------------------------
# Discovery
# ----------------------------------------------------------------------


def _is_lru_cache_decorator(node: ast.expr) -> bool:
    """True if `node` is `@lru_cache` or `@functools.lru_cache` (or a
    call form of either)."""
    target = node.func if isinstance(node, ast.Call) else node
    if isinstance(target, ast.Name) and target.id == "lru_cache":
        return True
    if (
        isinstance(target, ast.Attribute)
        and target.attr == "lru_cache"
        and isinstance(target.value, ast.Name)
        and target.value.id == "functools"
    ):
        return True
    return False


def discover_lru_caches(
    root: Path | None = None,
) -> list[dict]:
    """Walk every .py under `root` (default: scripts/). For each
    top-level `@lru_cache`-decorated function, return a record:

        {
            "file":  "scripts/.../module.py",
            "line":  <int>,
            "func":  <function name>,
            "module": "scripts.....module",  # importable qualname
        }

    Sorted by (file, line) for stable output.
    """
    base = root or _SCRIPTS
    found: list[dict] = []
    for py in sorted(base.rglob("*.py")):
        # Skip cache / backup directories — vulture's whitelist
        # convention applies here too.
        if any(part.startswith(".") for part in py.relative_to(base).parts):
            continue
        if "__pycache__" in py.parts:
            continue
        try:
            text = py.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        try:
            tree = ast.parse(text, filename=str(py))
        except SyntaxError:
            continue
        # Compute rel-paths against repo when possible; fall back to
        # rel-against-base when called with a synthetic root (tests).
        try:
            rel = str(py.relative_to(_REPO)).replace("\\", "/")
            module_qual = ".".join(py.relative_to(_REPO).with_suffix("").parts)
        except ValueError:
            rel = str(py.relative_to(base)).replace("\\", "/")
            module_qual = ".".join(py.relative_to(base).with_suffix("").parts)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if _is_lru_cache_decorator(dec):
                    found.append(
                        {
                            "file": rel,
                            "line": node.lineno,
                            "func": node.name,
                            "module": module_qual,
                        }
                    )
                    break
    return sorted(found, key=lambda r: (r["file"], r["line"]))


# ----------------------------------------------------------------------
# Clear-path detection
# ----------------------------------------------------------------------


def find_clear_sites(
    func_name: str,
    *,
    root: Path | None = None,
) -> list[dict]:
    """Search the codebase for ``<func_name>.cache_clear()`` calls.
    Returns a list of `{file, line, snippet}` records.

    Pure regex scan — fast enough on a 600-file repo and sufficient
    since `cache_clear()` is always called as a method on the cached
    function reference (`load_editions.cache_clear()`).
    """
    base = root or _SCRIPTS
    pattern = re.compile(rf"\b{re.escape(func_name)}\.cache_clear\s*\(\s*\)")
    sites: list[dict] = []
    # When called against the production scripts/ tree, also search
    # tests/ (tests often clear caches to set up fixture state, which
    # proves the surface exists). When called with a synthetic root
    # (unit tests of THIS module), only search the synthetic tree.
    search_roots = [base]
    if root is None:
        # Default-call invocation; widen to tests/ for production audit.
        search_roots.append(_REPO / "tests")
    for search_root in search_roots:
        if not search_root.is_dir():
            continue
        for py in search_root.rglob("*.py"):
            if "__pycache__" in py.parts:
                continue
            try:
                text = py.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for i, line in enumerate(text.splitlines(), start=1):
                if pattern.search(line):
                    try:
                        rel = str(py.relative_to(_REPO)).replace("\\", "/")
                    except ValueError:
                        rel = str(py.relative_to(search_root)).replace("\\", "/")
                    sites.append(
                        {
                            "file": rel,
                            "line": i,
                            "snippet": line.strip()[:120],
                        }
                    )
    return sites


# ----------------------------------------------------------------------
# Whitelist
# ----------------------------------------------------------------------


_WHITELIST_RE = re.compile(r"^_\.([a-zA-Z_][a-zA-Z0-9_]*)\b")


def load_whitelist(
    path: Path | None = None,
) -> set[str]:
    """Read the whitelist file. Each non-comment line beginning with
    `_.<name>` adds `<name>` to the whitelist. Same convention as
    vulture's whitelist (ω.26)."""
    p = path or _WHITELIST_PATH
    if not p.is_file():
        return set()
    names: set[str] = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        m = _WHITELIST_RE.match(line.strip())
        if m:
            names.add(m.group(1))
    return names


# ----------------------------------------------------------------------
# Audit
# ----------------------------------------------------------------------


def audit(
    *,
    root: Path | None = None,
    whitelist: set[str] | None = None,
) -> dict:
    """Walk every cached function; classify each as:

      - ``"clear_path"``: at least one ``cache_clear()`` site found.
      - ``"whitelisted"``: in the whitelist file (intentionally
        no clear-path needed).
      - ``"no_clear_path"``: NEITHER — surfaces as an audit failure.

    Returns ``{ok, caches: [...], summary: {...}}``.
    """
    caches = discover_lru_caches(root=root)
    wl = whitelist if whitelist is not None else load_whitelist()
    classified: list[dict] = []
    for c in caches:
        sites = find_clear_sites(c["func"], root=root)
        if c["func"] in wl:
            status = "whitelisted"
        elif sites:
            status = "clear_path"
        else:
            status = "no_clear_path"
        classified.append(
            {
                **c,
                "status": status,
                "clear_sites": sites,
            }
        )
    n_total = len(classified)
    n_clear = sum(1 for c in classified if c["status"] == "clear_path")
    n_whitelist = sum(1 for c in classified if c["status"] == "whitelisted")
    n_no_clear = sum(1 for c in classified if c["status"] == "no_clear_path")
    return {
        "ok": n_no_clear == 0,
        "caches": classified,
        "summary": {
            "total": n_total,
            "clear_path": n_clear,
            "whitelisted": n_whitelist,
            "no_clear_path": n_no_clear,
        },
    }


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="audit_caches",
        description=(
            "ω.30 — audit @lru_cache sites in scripts/ for clear "
            "paths. Reports caches without a documented clear "
            "site as a failure (unless whitelisted)."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="machine-readable JSON output",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="show clear-call sites for every cache (default: only failures)",
    )
    args = parser.parse_args(argv)

    result = audit()
    summary = result["summary"]

    if args.json:
        print(json.dumps(result, indent=2, default=str))
        return 0 if result["ok"] else 1

    if result["ok"]:
        print(
            f"  ✓ all {summary['total']} cache(s) accounted for: "
            f"{summary['clear_path']} with clear-path, "
            f"{summary['whitelisted']} whitelisted"
        )
        if args.verbose:
            for c in result["caches"]:
                tag = {
                    "clear_path": "✓",
                    "whitelisted": "·",
                    "no_clear_path": "✗",
                }[c["status"]]
                print(f"  {tag}  {c['file']}:{c['line']}  {c['func']}()")
                for s in c["clear_sites"]:
                    print(f"      ↳ cleared at {s['file']}:{s['line']}")
        return 0

    print(f"  ✗ {summary['no_clear_path']} cache(s) without a clear path:")
    for c in result["caches"]:
        if c["status"] == "no_clear_path":
            print(f"    {c['file']}:{c['line']}  {c['func']}()")
    print(
        "\n  Triage:\n"
        "    real cache w/o invalidation → "
        "add a `<func>.cache_clear()` call to the relevant write path\n"
        "    intentionally one-shot (env-dependent / paths-only) → "
        "add to scripts/.cache_audit_whitelist.py\n"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
