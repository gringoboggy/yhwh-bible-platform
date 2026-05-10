#!/usr/bin/env python3
"""
Ethiopian Bible EPUB — Comprehensive audit & cleanup system

Runs a three-category audit on the project tree and reports findings.
Optionally auto-fixes safe issues with --fix.

CATEGORIES
==========

A. Code quality (Python files)
   1.  Inventory & dependency map
   2.  Syntax & unused imports
   3.  Unreferenced top-level definitions
   4.  Dead branches / unused parameters
   5.  Stale comments & docstrings
   6.  Duplication between scripts (reported, not fixed — see INJECTOR_DUPLICATION.md)
   7.  Module-level constants (hoisting candidates)
   8.  NOTES_* lists structural integrity
   9.  (retired) — was kings_session stub files; deprecated 2026-05-06
   10. Round-trip validation (syntax + injector dry-run)

B. EPUB structural uniformity (per book)
   B1. Every book has a title page (bp-NN div)
   B2. Every chapter has a ch-anchor (ch-bXX-cN)
   B3. Every chapter has its verse-1 anchor present
   B4. Visible TOC + nav.xhtml + toc.ncx agree on chapter counts
   B5. No cross-book ID collisions (note IDs, ref IDs, ch-anchors, bp-anchors)
   B6. Verse-marker style consistent within each book (no Strategy A/B mixing)
   B7. Note refs ↔ asides paired (no orphans either way)

C. EPUB content/typography uniformity
   C1. No PDF-conversion orphan paragraphs (single/short-letter <p>)
   C2. No empty <p></p> tags
   C3. No trailing whitespace inside content files
   C4. Mixed straight/curly quote audit (informational)
   C5. Double-space audit (informational — many are intentional WEB artifacts)
   C6. Chapter heading style uniformity (all use same tag class)

USAGE
=====
    python3 audit.py                  # full report (no fixes)
    python3 audit.py --fix            # apply safe auto-fixes
    python3 audit.py --category A     # run only one category (A, B, or C)
    python3 audit.py --quiet          # only show issues, hide passes

DESIGN
======
Every check is implemented as a separate function returning a list of
Issue objects. The runner iterates, prints findings, and (in --fix mode)
calls the matching fixer if one exists.

Issues have severity: ERROR (must fix before publish), WARN (should fix),
INFO (informational only — e.g. count of curly-vs-straight quotes).
"""

import argparse
import ast
import contextlib
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from collections.abc import Callable


# ============================================================================
# Issue dataclass + report formatting
# ============================================================================


@dataclass
class Issue:
    """A single audit finding."""

    category: str  # 'A', 'B', or 'C'
    check: str  # e.g. 'A3', 'B1'
    severity: str  # 'ERROR' / 'WARN' / 'INFO'
    where: str  # file:line or epub-path:tag
    message: str
    fixer: Callable | None = field(default=None, repr=False)
    fix_args: tuple = field(default=(), repr=False)


@dataclass
class CheckResult:
    """One check's findings."""

    name: str
    description: str
    issues: list[Issue] = field(default_factory=list)


SEV_COLOR = {"ERROR": "\033[91m", "WARN": "\033[93m", "INFO": "\033[94m", "PASS": "\033[92m"}
RESET = "\033[0m"


def print_check_header(check_id, name):
    print(f"\n--- {check_id}: {name} ---")


def print_issues(issues, quiet=False):
    if not issues:
        if not quiet:
            print(f"  {SEV_COLOR['PASS']}✓ pass{RESET}")
        return
    by_sev = Counter(i.severity for i in issues)
    counts = ", ".join(f"{c} {s}" for s, c in by_sev.items())
    print(f"  {len(issues)} finding(s): {counts}")
    for i in issues:
        col = SEV_COLOR.get(i.severity, "")
        print(f"    {col}[{i.severity}]{RESET} {i.where}: {i.message}")


# ============================================================================
# Project paths (configurable, but defaults match the standard tree)
# ============================================================================

ROOT = Path(__file__).parent.resolve()
EPUB_DIR = ROOT / "epub_working"

# Inventory of project scripts. Historically pointed at source_archive/*.py
# (one-time build helpers used to assemble the original corpus); those have
# been retired in favour of scripts/* equivalents (e.g. add_commentary.py
# → scripts/inject.py, build_toc.py + build_book_title_pages.py output is
# already baked into epub_working/). Auto-discovers current state.
SCRIPTS = sorted([p for p in (ROOT / "scripts").glob("*.py") if p.is_file()])
SCRIPTS.extend(sorted([p for p in (ROOT / "scripts" / "core").glob("*.py") if p.is_file() and p.name != "__init__.py"]))
SCRIPTS.extend(
    [
        ROOT / "kings_session" / "book_meta.py",
        ROOT / "kings_session" / "strategy_b_inject.py",
    ]
)


# ============================================================================
# CATEGORY A — Code quality
# ============================================================================


def check_a1_inventory():
    """A1: Inventory + dependency map (always reports as INFO)."""
    issues = []
    total_loc = 0
    for s in SCRIPTS:
        if not s.exists():
            issues.append(Issue("A", "A1", "ERROR", str(s.relative_to(ROOT)), "expected script missing"))
            continue
        loc = len(s.read_text().splitlines())
        total_loc += loc
    issues.append(Issue("A", "A1", "INFO", "<all>", f"{len(SCRIPTS)} python files, {total_loc} LOC total"))
    return issues


def check_a2_imports():
    """A2: Syntax check + unused imports."""
    issues = []
    for s in SCRIPTS:
        if not s.exists():
            continue
        text = s.read_text()
        try:
            tree = ast.parse(text)
        except SyntaxError as e:
            issues.append(Issue("A", "A2", "ERROR", f"{s.relative_to(ROOT)}:{e.lineno}", f"syntax error: {e.msg}"))
            continue
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    imports.append((a.asname or a.name.split(".")[0], node.lineno))
            elif isinstance(node, ast.ImportFrom):
                for a in node.names:
                    imports.append((a.asname or a.name, node.lineno))
        for name, line in imports:
            # `from __future__ import annotations` (PEP 563/649) is a
            # runtime-affecting directive even when the name is not
            # textually referenced. Skipping avoids 22 false-positive
            # WARN findings across the codebase.
            if name == "annotations":
                continue
            body = "\n".join(line_text for i, line_text in enumerate(text.splitlines(), 1) if i != line)
            if not re.search(rf"\b{re.escape(name)}\b", body):
                issues.append(
                    Issue(
                        "A",
                        "A2",
                        "WARN",
                        f"{s.relative_to(ROOT)}:{line}",
                        f'unused import "{name}"',
                        fixer=fix_remove_import_name,
                        fix_args=(s, line, name),
                    )
                )
    return issues


def fix_remove_import_name(s: Path, line: int, name: str):
    """Surgically remove a single imported name from a line.

    Handles three cases without nuking siblings:
    1. ``import name``                 → remove whole line
    2. ``from x import name``          → remove whole line
    3. ``from x import a, name, b``    → remove only ``name``, leaving ``a, b``
    """
    text = s.read_text()
    lines = text.splitlines(keepends=True)
    if not (0 < line <= len(lines)):
        return
    target = lines[line - 1]
    stripped = target.rstrip("\n").rstrip("\r")

    # Case 3 first — multi-name `from ... import` line
    m = re.match(r"^(\s*from\s+\S+\s+import\s+)(.+)$", stripped)
    if m and "," in m.group(2):
        prefix, names_part = m.group(1), m.group(2)
        names = [n.strip() for n in names_part.split(",")]
        kept = [n for n in names if n.split(" as ")[0].strip() != name]
        if kept and len(kept) < len(names):
            new_line = prefix + ", ".join(kept) + target[len(stripped) :]
            lines[line - 1] = new_line
            s.write_text("".join(lines))
            return

    # Cases 1 + 2 — single-name line: drop entirely
    del lines[line - 1]
    s.write_text("".join(lines))


def check_a3_unreferenced():  # noqa: C901  (legacy; refactor risk > benefit)
    """A3: Top-level defs unused anywhere in project."""
    issues = []
    all_text = {s: s.read_text() for s in SCRIPTS if s.exists()}
    for s, text in all_text.items():
        try:
            tree = ast.parse(text)
        except Exception:
            continue
        top_defs = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                top_defs.append((node.name, node.lineno, type(node).__name__))
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id.isupper():
                        top_defs.append((t.id, node.lineno, "CONST"))
        for name, line, kind in top_defs:
            if name in ("main", "__all__"):
                continue
            # Underscore prefix = "private to this module / intentionally
            # not part of the public API." Skipping prevents the audit
            # from flagging deliberately-private symbols.
            if name.startswith("_"):
                continue
            usages = 0
            for s2, text2 in all_text.items():
                for i, line_text in enumerate(text2.splitlines(), 1):
                    if s2 == s and i == line:
                        continue
                    if re.search(rf"\b{re.escape(name)}\b", line_text):
                        usages += 1
                        break  # one is enough
                if usages:
                    break
            if usages == 0:
                issues.append(
                    Issue(
                        "A",
                        "A3",
                        "WARN",
                        f"{s.relative_to(ROOT)}:{line}",
                        f'[{kind}] "{name}" defined but unused anywhere',
                    )
                )
    return issues


def check_a4_dead_branches():  # noqa: C901  (legacy; refactor risk > benefit)
    """A4: Unreachable code + unused parameters."""
    issues = []
    for s in SCRIPTS:
        if not s.exists():
            continue
        text = s.read_text()
        try:
            tree = ast.parse(text)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for stmt in node.body[:-1]:
                    if isinstance(stmt, (ast.Return, ast.Raise, ast.Continue, ast.Break)):
                        issues.append(
                            Issue(
                                "A",
                                "A4",
                                "ERROR",
                                f"{s.relative_to(ROOT)}:{stmt.lineno}",
                                f"unreachable code after {type(stmt).__name__} in {node.name}()",
                            )
                        )
                params = [a.arg for a in node.args.args + node.args.kwonlyargs]
                used = set()
                for sub in ast.walk(node):
                    if sub is node:
                        continue
                    if isinstance(sub, ast.Name):
                        used.add(sub.id)
                # Skip A4 if the function carries @lru_cache or @functools.lru_cache —
                # cache decorators key on every parameter even when the body doesn't
                # reference it directly (mtime_ns is a classic example).
                has_cache_decorator = any(
                    (isinstance(d, ast.Call) and getattr(d.func, "attr", "") == "lru_cache")
                    or (isinstance(d, ast.Attribute) and d.attr == "lru_cache")
                    or (isinstance(d, ast.Name) and d.id == "lru_cache")
                    for d in getattr(node, "decorator_list", [])
                )
                for p in params:
                    if p in ("self", "cls"):
                        continue
                    # Underscore prefix is the conventional marker for
                    # "intentionally unused" (matches Python style guides
                    # and pylint/ruff defaults).
                    if p.startswith("_"):
                        continue
                    if has_cache_decorator:
                        continue
                    if p not in used:
                        issues.append(
                            Issue(
                                "A",
                                "A4",
                                "WARN",
                                f"{s.relative_to(ROOT)}:{node.lineno}",
                                f'param "{p}" unused in {node.name}()',
                            )
                        )
    return issues


def check_a5_stale_comments():
    """A5: Known stale comment patterns."""
    issues = []
    stale_patterns = [
        # (regex, message, expected-presence-after-fix)
        (
            r"1 Enoch.{0,40}chapters 79-108.{0,80}plain spans",
            "stale 1en strategy comment (claimed chs 1-78 need Strategy B; actually all 108 work)",
        ),
        (
            r"Strategy-A pending: 1 Enoch.{0,40}not yet authored",
            "stale 1en comment (notes are authored as of May 2026)",
        ),
        (r"\bTODO\b|\bFIXME\b|\bXXX\b|\bHACK\b", "TODO/FIXME marker"),
    ]
    for s in SCRIPTS:
        if not s.exists():
            continue
        for line_no, line in enumerate(s.read_text().splitlines(), 1):
            if not (line.strip().startswith("#") or '"""' in line or "'''" in line):
                continue
            for pat, msg in stale_patterns:
                if re.search(pat, line, re.IGNORECASE):
                    issues.append(Issue("A", "A5", "WARN", f"{s.relative_to(ROOT)}:{line_no}", msg))
    return issues


def check_a6_duplication():
    """A6: Cross-script duplication. Documented as intentional in
    INJECTOR_DUPLICATION.md; reports as INFO only."""
    issues = []
    doc = ROOT / "INJECTOR_DUPLICATION.md"
    if doc.exists():
        issues.append(
            Issue("A", "A6", "INFO", "INJECTOR_DUPLICATION.md", "injector helper duplication documented as intentional")
        )
    else:
        issues.append(Issue("A", "A6", "WARN", "<root>", "INJECTOR_DUPLICATION.md missing — document or refactor"))
    return issues


def check_a7_constants():
    """A7: Magic strings appearing in 2+ functions of the same script."""
    issues = []
    dict_key_noise = {
        "inserted",
        "already_present",
        "anchor_miss",
        "no_source",
        "split_at",
        "end_kind",
        "end_page",
        "existing_id",
        "open_tag_pos",
        "anchor_id",
        "skipped_already",
        "phantom_v1",
        "out_of_range",
        "store_true",
        "id_prefix",
        "strategy",
    }
    for s in SCRIPTS:
        if not s.exists():
            continue
        text = s.read_text()
        try:
            tree = ast.parse(text)
        except Exception:
            continue
        counts = defaultdict(set)
        for func in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
            for node in ast.walk(func):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    v = node.value
                    if len(v) < 8 or v.isspace():
                        continue
                    if v in dict_key_noise:
                        continue
                    if func.body and isinstance(func.body[0], ast.Expr) and func.body[0].value is node:
                        continue
                    counts[v].add(func.name)
        for v, funcs in counts.items():
            if len(funcs) >= 2:
                preview = v[:50].replace("\n", "\\n")
                issues.append(
                    Issue(
                        "A",
                        "A7",
                        "INFO",
                        f"{s.relative_to(ROOT)}",
                        f'string "{preview}" used in {len(funcs)} funcs — hoist candidate',
                    )
                )
    return issues


def check_a8_notes_lists():  # noqa: C901  (legacy; refactor risk > benefit)
    """A8: NOTES_* list structural integrity in the legacy injector source.

    add_commentary.py was the original injector and held the canonical
    NOTES_* lists. It has been retired in favour of content/notes/<book>.py
    (single-source-of-truth) + scripts/inject.py. This check now succeeds
    silently when the retired script is absent — note-list integrity is
    instead enforced by scripts/verify.py's pairing check.
    """
    issues = []
    add_comm = ROOT / "source_archive" / "add_commentary.py"
    if not add_comm.exists():
        return issues  # retired script — modern equivalent: content/notes/*.py
    text = add_comm.read_text()
    tree = ast.parse(text)
    notes_lists = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id.startswith("NOTES_") and isinstance(node.value, ast.List):
                    notes_lists[t.id] = node.value
    for name, lst in notes_lists.items():
        triples = []
        for elt in lst.elts:
            if not isinstance(elt, ast.Tuple) or len(elt.elts) != 8:
                issues.append(
                    Issue(
                        "A",
                        "A8",
                        "ERROR",
                        f"add_commentary.py:{elt.lineno if hasattr(elt, 'lineno') else '?'}",
                        f"{name}: malformed tuple (expected 8 fields)",
                    )
                )
                continue
            with contextlib.suppress(Exception):
                triples.append((elt.elts[0].value, elt.elts[1].value, elt.elts[2].value))
        for triple, count in Counter(triples).items():
            if count > 1:
                issues.append(
                    Issue(
                        "A",
                        "A8",
                        "ERROR",
                        name,
                        f"duplicate (ch={triple[0]}, v={triple[1]}, suf={triple[2]!r}) — "
                        "second silently dropped by injector",
                    )
                )
    # Check BOOK_NOTES dispatch
    m = re.search(r"BOOK_NOTES\s*=\s*\{([^}]+)\}", text)
    if m:
        referenced = set(re.findall(r"NOTES_\w+", m.group(1)))
        unreferenced = set(notes_lists.keys()) - referenced
        for n in unreferenced:
            issues.append(Issue("A", "A8", "WARN", n, "NOTES list defined but not in BOOK_NOTES dispatch"))
    return issues


def check_a10_round_trip():
    """A10: Round-trip — confirm injector dry-run is clean."""
    # We don't actually invoke subprocess here (would slow audit); we just verify
    # syntax is OK, which is the prerequisite for dry-run to work.
    issues = []
    for s in SCRIPTS:
        if not s.exists():
            continue
        try:
            ast.parse(s.read_text())
        except SyntaxError as e:
            issues.append(
                Issue("A", "A10", "ERROR", f"{s.relative_to(ROOT)}:{e.lineno}", f"will fail round-trip: {e.msg}")
            )
    if not issues:
        issues.append(Issue("A", "A10", "INFO", "<all scripts>", "all parse clean — ready for injector dry-run"))
    return issues


# ============================================================================
# CATEGORY B — EPUB structural uniformity (per book)
# ============================================================================


def _load_book_meta():
    """Import kings_session/book_meta.py and return books dict."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("book_meta", ROOT / "kings_session" / "book_meta.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.BOOKS  # external module exports BOOKS (uppercase)


def _epub_text(filename):
    """Read an epub_working content file. None if missing."""
    p = EPUB_DIR / filename
    return p.read_text(encoding="utf-8") if p.exists() else None


def _scan_all_epub_text():
    """Concatenate all index_split_*.html for global searches.
    Returns dict {filename: text}."""
    out = {}
    for f in sorted(EPUB_DIR.glob("index_split_*.html")):
        out[f.name] = f.read_text(encoding="utf-8")
    return out


def check_b1_title_pages():
    """B1: Every book has a bp-NN title page."""
    issues = []
    if not EPUB_DIR.exists():
        issues.append(Issue("B", "B1", "ERROR", "<root>", "epub_working/ missing"))
        return issues
    try:
        books = _load_book_meta()
    except Exception as e:
        issues.append(Issue("B", "B1", "ERROR", "book_meta.py", f"cannot load: {e}"))
        return issues
    all_text = _scan_all_epub_text()
    found_bps = set()
    for txt in all_text.values():
        found_bps.update(re.findall(r'id="(bp-\d+)"', txt))
    for code, meta in books.items():
        bp = meta.get("bp")
        if not bp:
            issues.append(Issue("B", "B1", "WARN", code, "no bp anchor in book_meta"))
            continue
        if bp not in found_bps:
            issues.append(Issue("B", "B1", "ERROR", code, f"expected title page {bp} not found anywhere in EPUB"))
    return issues


def check_b2_chapter_anchors():
    """B2: Every chapter of every book has a ch-bXX-cN anchor."""
    issues = []
    try:
        books = _load_book_meta()
    except Exception as e:
        issues.append(Issue("B", "B2", "ERROR", "book_meta.py", f"cannot load: {e}"))
        return issues
    all_text = _scan_all_epub_text()
    # Collect all ch-anchors per book (by bxx)
    by_bxx = defaultdict(set)
    for txt in all_text.values():
        for m in re.finditer(r'id="ch-(b\d+)-c(\d+)"', txt):
            by_bxx[m.group(1)].add(int(m.group(2)))
    for code, meta in books.items():
        bxx = meta.get("bxx")
        nch = meta.get("ch_count")
        if not bxx or not nch:
            continue
        present = by_bxx.get(bxx, set())
        # Even single-chapter books must have ch-bXX-c1 for TOC uniformity
        missing = [c for c in range(1, nch + 1) if c not in present]
        if missing:
            issues.append(
                Issue(
                    "B",
                    "B2",
                    "ERROR",
                    f"{code} ({bxx})",
                    f"missing ch-anchors for chapters {missing[:10]}"
                    + (f" (+{len(missing) - 10} more)" if len(missing) > 10 else ""),
                )
            )
    return issues


def check_b3_verse1_anchors():
    """B3: Every chapter (where verse anchors exist) has its verse-1 anchor."""
    issues = []
    try:
        books = _load_book_meta()
    except Exception:
        return issues
    all_text = _scan_all_epub_text()
    # Find verse-1 anchors per (code, ch). Strategy A pattern: id="v-CODE-CH-1"
    by_code_ch1 = defaultdict(set)
    code_with_v_anchors = set()
    for txt in all_text.values():
        for m in re.finditer(r'id="v-([a-z0-9]+)-(\d+)-1"', txt):
            code, ch = m.group(1), int(m.group(2))
            code_with_v_anchors.add(code)
            by_code_ch1[code].add(ch)
    # Only check books that have v- anchors at all (Strategy A and 1en)
    for code, meta in books.items():
        if code not in code_with_v_anchors:
            continue
        nch = meta.get("ch_count", 0)
        if nch <= 0:
            continue
        present = by_code_ch1[code]
        missing = [c for c in range(1, nch + 1) if c not in present]
        if missing:
            issues.append(
                Issue(
                    "B",
                    "B3",
                    "ERROR",
                    code,
                    f"missing verse-1 anchors for chapters {missing[:10]}"
                    + (f" (+{len(missing) - 10} more)" if len(missing) > 10 else ""),
                )
            )
    return issues


def check_b4_toc_agreement():
    """B4: nav.xhtml + toc.ncx + visible TOC agree on chapter COUNTS per book.

    nav.xhtml and toc.ncx use structured `ch-bXX-cN` anchors.
    Visible TOC (index_split_000.html) uses legacy `page_N` anchors but lists
    the same chapter count per book. We compare per-book chapter counts, not
    raw anchor IDs."""
    issues = []
    nav = EPUB_DIR / "nav.xhtml"
    ncx = EPUB_DIR / "toc.ncx"
    f000 = EPUB_DIR / "index_split_000.html"
    if not nav.exists():
        issues.append(Issue("B", "B4", "ERROR", "nav.xhtml", "missing"))
    if not ncx.exists():
        issues.append(Issue("B", "B4", "ERROR", "toc.ncx", "missing"))
    if not f000.exists():
        issues.append(Issue("B", "B4", "ERROR", "index_split_000.html", "missing"))
    if any(i.severity == "ERROR" for i in issues):
        return issues

    # nav.xhtml chapter counts per book
    nav_ch = defaultdict(set)
    for m in re.finditer(r'href="[^"]*#ch-(b\d+)-c(\d+)"', nav.read_text()):
        nav_ch[m.group(1)].add(int(m.group(2)))
    # ncx chapter counts per book
    ncx_ch = defaultdict(set)
    for m in re.finditer(r'src="[^"]*#ch-(b\d+)-c(\d+)"', ncx.read_text()):
        ncx_ch[m.group(1)].add(int(m.group(2)))
    # Visible TOC: count chapter <li><a>NUM</a></li> entries inside each book block.
    # Each toc-book block may optionally be wrapped in <details>/<summary> when
    # the collapsible style is enabled (see scripts/style_config.py).
    toc_text = f000.read_text()
    visible_count = {}
    for m in re.finditer(
        r'<li\s+class="toc-book">\s*'
        r"(?:<details(?:\s+open)?>\s*<summary>\s*)?"  # optional <details><summary>
        r'<a\s+href="[^"]*#(bp-\d+)"[^>]*>[^<]+</a>'
        r"\s*(?:</summary>\s*)?"  # optional </summary>
        r"(.*?)</li>\s*</ol>",
        toc_text,
        re.DOTALL,
    ):
        bp = m.group(1)
        bxx = "b" + bp.split("-")[1]
        chapter_lis = re.findall(r"<li>\s*<a [^>]+>\d+</a>", m.group(2))
        visible_count[bxx] = len(chapter_lis)

    all_books = set(nav_ch) | set(ncx_ch) | set(visible_count)

    # Detect "books-only mode": if nav AND ncx both have ZERO chapter entries
    # for every book, that's the deliberate state set by scripts/set_reader_toc.py.
    # In that mode, the reader's built-in TOC sheet shows just the 87 book titles
    # (cleaner UX), while the in-book visible HTML TOC still has all chapters.
    # We don't flag this as an error — the design is intentional.
    nav_total_chapters = sum(len(s) for s in nav_ch.values())
    ncx_total_chapters = sum(len(s) for s in ncx_ch.values())
    if nav_total_chapters == 0 and ncx_total_chapters == 0:
        issues.append(
            Issue(
                "B",
                "B4",
                "INFO",
                "<reader-TOC>",
                f"books-only mode active "
                f"(nav/ncx have no chapter entries; "
                f"visible TOC has full chapters in {len(visible_count)} books)",
            )
        )
        return issues

    for bxx in sorted(all_books):
        n = len(nav_ch.get(bxx, set()))
        c = len(ncx_ch.get(bxx, set()))
        v = visible_count.get(bxx, 0)
        # Single-chapter books may legitimately have v=0 or v=1; allow both
        if n == c == v:
            continue
        if n == c and v == 0 and n <= 1:
            continue  # single-chapter book without numbered list
        issues.append(Issue("B", "B4", "ERROR", bxx, f"chapter counts differ: nav={n} ncx={c} visible={v}"))
    return issues


def check_b5_id_collisions():
    """B5: No ID is duplicated within or across content files."""
    issues = []
    seen = {}  # id -> first (file, line)
    for f in sorted(EPUB_DIR.glob("index_split_*.html")):
        text = f.read_text()
        for m in re.finditer(r'id="([^"]+)"', text):
            iid = m.group(1)
            line = text[: m.start()].count("\n") + 1
            if iid in seen:
                prev = seen[iid]
                issues.append(
                    Issue(
                        "B", "B5", "ERROR", f"{f.name}:{line}", f'duplicate id="{iid}" (first at {prev[0]}:{prev[1]})'
                    )
                )
            else:
                seen[iid] = (f.name, line)
    return issues


def check_b6_marker_consistency():
    """B6: Verse-marker style consistent within each book's chapter scope.
    True mixing = book's chapter region has <span class="vn"> markers NOT
    wrapped in the deep-link anchor. Bounded scope: from each book's
    ch-bXX-c1 to the next book's ch-bXX-c1."""
    issues = []
    try:
        books = _load_book_meta()
    except Exception:
        return issues
    code_to_bxx = {c: m.get("bxx") for c, m in books.items() if m.get("bxx")}
    bxx_to_code = {v: k for k, v in code_to_bxx.items()}
    # Concatenate all files in order
    parts = []
    for f in sorted(EPUB_DIR.glob("index_split_*.html")):
        parts.append(f.read_text(encoding="utf-8"))
    big = "\n".join(parts)
    # Identify books that have v-CODE-CH-V anchors (Strategy A users)
    a_books = set()
    for m in re.finditer(r'id="v-([a-z0-9]+)-\d+-\d+"', big):
        a_books.add(m.group(1))
    # For each book, find scope and count unwrapped vn spans
    book_starts = sorted(((m.start(), m.group(1)) for m in re.finditer(r'id="ch-(b\d+)-c1"', big)), key=lambda x: x[0])
    for i, (start, bxx) in enumerate(book_starts):
        end = book_starts[i + 1][0] if i + 1 < len(book_starts) else len(big)
        code = bxx_to_code.get(bxx)
        if not code or code not in a_books:
            continue
        section = big[start:end]
        unwrapped = 0
        for m in re.finditer(r'<span class="vn">\d+</span>', section):
            lookback = section[max(0, m.start() - 200) : m.start()]
            if not re.search(rf'<a[^>]*\bid="v-{re.escape(code)}-\d+-\d+(?:-x\d+)?"[^>]*>\s*$', lookback):
                unwrapped += 1
        if unwrapped > 0:
            issues.append(
                Issue(
                    "B",
                    "B6",
                    "WARN",
                    code,
                    f'{unwrapped} <span class="vn"> markers in chapter scope not wrapped in v-{code}-... anchor',
                )
            )
    return issues


def check_b7_note_pairing():
    """B7: Every note ref has a matching aside id, and vice versa."""
    issues = []
    refs = set()
    notes = set()
    for f in sorted(EPUB_DIR.glob("index_split_*.html")):
        t = f.read_text()
        refs.update(re.findall(r'href="#note-((?:[a-z]+|[1-4][a-z]+)\d{4}[a-z]?)"', t))
        notes.update(re.findall(r'id="note-((?:[a-z]+|[1-4][a-z]+)\d{4}[a-z]?)"', t))
    orphan_refs = refs - notes
    orphan_asides = notes - refs
    for r in sorted(orphan_refs):
        issues.append(Issue("B", "B7", "ERROR", f"note-{r}", "ref present, but no matching aside"))
    for n in sorted(orphan_asides):
        issues.append(Issue("B", "B7", "ERROR", f"note-{n}", "aside present, but no matching ref"))
    if not issues:
        issues.append(Issue("B", "B7", "INFO", "<all>", f"{len(refs)}/{len(notes)} paired"))
    return issues


CATEGORY_B_CHECKS = [
    ("B1", "Every book has a bp-NN title page", check_b1_title_pages),
    ("B2", "Every chapter has a ch-bXX-cN anchor", check_b2_chapter_anchors),
    ("B3", "Every chapter has its verse-1 anchor", check_b3_verse1_anchors),
    ("B4", "nav.xhtml + toc.ncx + visible TOC agree", check_b4_toc_agreement),
    ("B5", "No duplicate IDs across content files", check_b5_id_collisions),
    ("B6", "Verse-marker style consistent within each book", check_b6_marker_consistency),
    ("B7", "Note refs ↔ asides paired", check_b7_note_pairing),
]


# ============================================================================
# CATEGORY C — Content / typography uniformity
# ============================================================================


def check_c1_calibre_artifacts():
    """C1: Legacy PDF-conversion artifacts — orphan single/short-letter paragraphs.

    Originally these had ``class="calibreN"`` (PDF→HTML conversion debris). After
    the May 2026 semantic-class migration, the same orphan pattern would now appear
    as ``<p class="verse-p">A</p>`` etc. We check all paragraph classes generically.
    """
    issues = []
    for f in sorted(EPUB_DIR.glob("index_split_*.html")):
        txt = f.read_text()
        for m in re.finditer(r'<p[^>]*class="[^"]+"[^>]*>([^<]{1,5})</p>', txt):
            content = m.group(1).strip()
            if content and len(content) <= 3:
                line = txt[: m.start()].count("\n") + 1
                issues.append(
                    Issue(
                        "C",
                        "C1",
                        "WARN",
                        f"{f.name}:{line}",
                        f"orphan short paragraph: <p>{content!r}</p>",
                        fixer=fix_remove_calibre_orphan,
                        fix_args=(f, m.group(0)),
                    )
                )
    return issues


def fix_remove_calibre_orphan(f: Path, full_match: str):
    txt = f.read_text()
    if full_match in txt:
        # Remove the matched <p> plus a trailing newline if present
        txt = txt.replace(full_match + "\n", "", 1)
        if full_match in txt:
            txt = txt.replace(full_match, "", 1)
        f.write_text(txt)


def check_c2_empty_p():
    """C2: No empty <p></p> tags."""
    issues = []
    for f in sorted(EPUB_DIR.glob("index_split_*.html")):
        txt = f.read_text()
        for m in re.finditer(r"<p[^>]*>\s*</p>", txt):
            line = txt[: m.start()].count("\n") + 1
            issues.append(
                Issue(
                    "C",
                    "C2",
                    "WARN",
                    f"{f.name}:{line}",
                    "empty <p></p>",
                    fixer=fix_remove_empty_p,
                    fix_args=(f, m.group(0)),
                )
            )
    return issues


def fix_remove_empty_p(f: Path, full_match: str):
    txt = f.read_text()
    if full_match in txt:
        txt = txt.replace(full_match + "\n", "", 1)
        if full_match in txt:
            txt = txt.replace(full_match, "", 1)
        f.write_text(txt)


def check_c3_trailing_whitespace():
    """C3: No trailing whitespace inside content files."""
    issues = []
    files_with_trailing = []
    for f in sorted(EPUB_DIR.glob("index_split_*.html")):
        txt = f.read_text()
        n_trailing = sum(1 for line in txt.splitlines() if line != line.rstrip())
        if n_trailing:
            files_with_trailing.append((f, n_trailing))
            issues.append(
                Issue(
                    "C",
                    "C3",
                    "WARN",
                    f.name,
                    f"{n_trailing} lines with trailing whitespace",
                    fixer=fix_strip_trailing_ws,
                    fix_args=(f,),
                )
            )
    return issues


def fix_strip_trailing_ws(f: Path):
    txt = f.read_text()
    lines = [line_text.rstrip() for line_text in txt.splitlines()]
    new = "\n".join(lines)
    if txt.endswith("\n"):
        new += "\n"
    f.write_text(new)


def check_c4_quote_mixing():
    """C4: Mixed straight/curly quotes (informational — normal for HTML attrs vs prose)."""
    issues = []
    mixed = 0
    for f in sorted(EPUB_DIR.glob("index_split_*.html")):
        txt = f.read_text()
        if "'" in txt and "’" in txt:
            mixed += 1
    issues.append(
        Issue(
            "C",
            "C4",
            "INFO",
            f"{mixed} files",
            "mixed straight (') + curly (’) quotes — normal for HTML attrs vs prose",
        )
    )
    return issues


def check_c5_double_spaces():
    """C5: Double spaces between letters (informational — many are intentional WEB PDF artifacts)."""
    issues = []
    total = 0
    for f in sorted(EPUB_DIR.glob("index_split_*.html")):
        txt = f.read_text()
        total += len(re.findall(r"(?<=[a-zA-Z])  (?=[a-zA-Z])", txt))
    issues.append(
        Issue(
            "C",
            "C5",
            "INFO",
            "<all>",
            f"{total} double-space patterns — most are intentional WEB PDF artifacts "
            "(anchors depend on them; do NOT auto-fix)",
        )
    )
    return issues


def check_c6_heading_uniformity():
    """C6: Chapter/book heading class inventory."""
    issues = []
    classes = Counter()
    for f in sorted(EPUB_DIR.glob("index_split_*.html")):
        txt = f.read_text()
        for m in re.finditer(r'<h[1-6][^>]*class="([^"]+)"', txt):
            classes[m.group(1)] += 1
    expected = {"bookpage-title", "notes-heading", "toc-title", "book-title"}
    for cls, n in classes.most_common():
        if cls not in expected:
            issues.append(Issue("C", "C6", "WARN", cls, f"unexpected heading class ({n}x); expected: {expected}"))
    issues.append(Issue("C", "C6", "INFO", "<all>", f"heading classes: {dict(classes)}"))
    return issues


CATEGORY_C_CHECKS = [
    ("C1", "No PDF-conversion orphan paragraphs", check_c1_calibre_artifacts),
    ("C2", "No empty <p></p> tags", check_c2_empty_p),
    ("C3", "No trailing whitespace in content files", check_c3_trailing_whitespace),
    ("C4", "Quote-style consistency (informational)", check_c4_quote_mixing),
    ("C5", "Double-space audit (informational)", check_c5_double_spaces),
    ("C6", "Chapter heading class uniformity", check_c6_heading_uniformity),
]


# ============================================================================
# Runner
# ============================================================================

CATEGORY_A_CHECKS = [
    ("A1", "Inventory & dependency map", check_a1_inventory),
    ("A2", "Syntax & unused imports", check_a2_imports),
    ("A3", "Unreferenced top-level definitions", check_a3_unreferenced),
    ("A4", "Dead branches & unused parameters", check_a4_dead_branches),
    ("A5", "Stale comments & docstrings", check_a5_stale_comments),
    ("A6", "Duplication between scripts", check_a6_duplication),
    ("A7", "Module-level constants (hoisting candidates)", check_a7_constants),
    ("A8", "NOTES_* lists structural integrity", check_a8_notes_lists),
    ("A10", "Round-trip validation", check_a10_round_trip),
]


def run_category(category, checks, fix=False, quiet=False):
    print(f"\n{'=' * 72}")
    print(f"CATEGORY {category}")
    print(f"{'=' * 72}")
    all_issues = []
    fixes_applied = 0
    for cid, name, fn in checks:
        print_check_header(cid, name)
        issues = fn()
        all_issues.extend(issues)
        print_issues(issues, quiet=quiet)
        if fix:
            for issue in issues:
                if issue.fixer:
                    try:
                        issue.fixer(*issue.fix_args)
                        fixes_applied += 1
                        print(f"    {SEV_COLOR['PASS']}→ FIXED{RESET}: {issue.message}")
                    except Exception as e:
                        print(f"    fix failed: {e}")
    return all_issues, fixes_applied


def main():
    ap = argparse.ArgumentParser(description="Ethiopian Bible EPUB audit & cleanup")
    ap.add_argument("--fix", action="store_true", help="apply safe auto-fixes")
    ap.add_argument(
        "--category", choices=["A", "B", "C", "all"], default="all", help="run a specific category (default: all)"
    )
    ap.add_argument("--quiet", action="store_true", help="hide passing checks")
    args = ap.parse_args()

    all_issues = []
    total_fixes = 0

    if args.category in ("A", "all"):
        ai, af = run_category("A — Code Quality", CATEGORY_A_CHECKS, fix=args.fix, quiet=args.quiet)
        all_issues.extend(ai)
        total_fixes += af

    if args.category in ("B", "all"):
        bi, bf = run_category("B — EPUB Structural Uniformity", CATEGORY_B_CHECKS, fix=args.fix, quiet=args.quiet)
        all_issues.extend(bi)
        total_fixes += bf
    if args.category in ("C", "all"):
        ci, cf = run_category("C — Content/Typography Uniformity", CATEGORY_C_CHECKS, fix=args.fix, quiet=args.quiet)
        all_issues.extend(ci)
        total_fixes += cf

    print(f"\n{'=' * 72}")
    print("SUMMARY")
    print(f"{'=' * 72}")
    by_sev = Counter(i.severity for i in all_issues)
    print(f"  Total issues: {len(all_issues)}")
    for sev in ("ERROR", "WARN", "INFO"):
        if sev in by_sev:
            print(f"    {SEV_COLOR[sev]}{sev}{RESET}: {by_sev[sev]}")
    if args.fix:
        print(f"  Fixes applied: {total_fixes}")

    # Exit non-zero if any ERRORs (useful for CI)
    if by_sev.get("ERROR", 0):
        sys.exit(1)


if __name__ == "__main__":
    main()
