#!/usr/bin/env python3
"""ω.25 — Bulk rename / refactor tool.

Atomic project-wide rename of a kind code. The kind appears in five
distinct file shapes, each requiring different rewrite logic:

    1. content/kinds.yaml                — record `code: <old>`
    2. content/notes/<book>.py           — note tuple position [3]
    3. content/editions.yaml             — list items in
                                            `enabled_kinds:` /
                                            `disabled_kinds:`
    4. content/edition_templates/*.yaml  — same shape as editions
    5. content/scenarios/*.yaml          — same shape

YAML files use targeted line-anchored regex (`^(\\s+- )<old>\\s*$`,
`^(\\s+code:\\s*)<old>\\s*$`). Python notes files use AST-walk
(parse → find NOTES list → tuple by tuple, replace position [3]
when it equals the old kind string) — mirrors the
`scripts/attribute.py` rewriter pattern so kind codes that happen
to appear in body text or attribution don't get touched.

All-or-nothing semantics: every touched file gets a
`notes_io.ensure_backup` snapshot BEFORE its first mutation. If
any subsequent write fails, the runner restores from those
snapshots and aborts. Audit trail appended to
``content/.refactor_log.yaml`` — separate from the ω.22 migration
ledger because runtime renames don't need migration MODULES, just
an auditable record.

CLI::

    python scripts/refactor.py rename-kind comm-evangelical comm-evangelical-broad
    python scripts/refactor.py rename-kind <old> <new> --dry-run
    python scripts/refactor.py rename-kind <old> <new> --apply
    python scripts/refactor.py rename-kind <old> <new> --json

Per CLAUDE_PROJECT_RULES §10 (standard library only on the
backend): ``ast``, ``re``, ``shutil``, ``yaml`` (already a
project dep). No new external deps.

v1 scope: kind-rename only. Category-rename = ω.25.1 (same
framework, different target file set).
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


_REPO = Path(__file__).resolve().parent.parent
_CONTENT = _REPO / "content"
_REFACTOR_LOG = _CONTENT / ".refactor_log.yaml"


# ----------------------------------------------------------------------
# Pure helpers — discovery + plan computation
# ----------------------------------------------------------------------


def kind_target_files(content_dir: Path | None = None) -> list[Path]:
    """Every file that may contain a kind reference. Order is
    deterministic for reproducible audit logs."""
    base = content_dir or _CONTENT
    files: list[Path] = []
    if (base / "kinds.yaml").is_file():
        files.append(base / "kinds.yaml")
    if (base / "editions.yaml").is_file():
        files.append(base / "editions.yaml")
    templates = base / "edition_templates"
    if templates.is_dir():
        files.extend(sorted(templates.glob("*.yaml")))
    scenarios = base / "scenarios"
    if scenarios.is_dir():
        files.extend(sorted(scenarios.glob("*.yaml")))
    notes = base / "notes"
    if notes.is_dir():
        files.extend(sorted(notes.glob("*.py")))
    return files


def discover_kind_usage(
    old_code: str,
    *,
    content_dir: Path | None = None,
) -> dict:
    """Walk every target file; return a per-file count of references
    to ``old_code``. Pure read; no side effects."""
    base = content_dir or _CONTENT
    patterns = list(_yaml_kind_patterns(old_code))
    usage: dict[str, int] = {}
    total = 0
    for path in kind_target_files(base):
        rel = str(path.relative_to(base.parent)).replace("\\", "/")
        if path.suffix == ".yaml":
            count = _count_yaml_refs(path, patterns)
        elif path.suffix == ".py":
            count = _count_python_kind_refs(path, old_code)
        else:
            count = 0
        if count:
            usage[rel] = count
            total += count
    return {"old_code": old_code, "usage": usage, "total": total}


def compute_kind_rename_plan(
    old_code: str,
    new_code: str,
    *,
    content_dir: Path | None = None,
) -> dict:
    """Compute the file-level rewrite plan. Returns per-file
    `{path, kind, count, mutations: [...]}` records ready for
    `apply_kind_rename`. Pure — no writes."""
    base = content_dir or _CONTENT
    patterns = list(_yaml_kind_patterns(old_code))
    plan: list[dict] = []
    for path in kind_target_files(base):
        rel = str(path.relative_to(base.parent)).replace("\\", "/")
        if path.suffix == ".yaml":
            mutations = _plan_yaml_rewrite(path, patterns, new_code)
            if mutations:
                plan.append(
                    {
                        "path": str(path),
                        "rel": rel,
                        "kind": "yaml",
                        "count": len(mutations),
                        "mutations": mutations,
                    }
                )
        elif path.suffix == ".py":
            mutations = _plan_python_rewrite(path, old_code, new_code)
            if mutations:
                plan.append(
                    {
                        "path": str(path),
                        "rel": rel,
                        "kind": "py",
                        "count": len(mutations),
                        "mutations": mutations,
                    }
                )
    return {
        "old_code": old_code,
        "new_code": new_code,
        "files": plan,
        "summary": {
            "files": len(plan),
            "total_mutations": sum(p["count"] for p in plan),
        },
    }


def validate_kind_rename(
    old_code: str,
    new_code: str,
    plan: dict,
    *,
    content_dir: Path | None = None,
) -> list[str]:
    """Sanity-check the rename. Returns a list of error strings;
    empty means safe to apply."""
    errors: list[str] = []
    if not old_code or not isinstance(old_code, str):
        errors.append("old_code must be a non-empty string")
    if not new_code or not isinstance(new_code, str):
        errors.append("new_code must be a non-empty string")
    if old_code == new_code:
        errors.append("old_code and new_code are identical")
    if errors:
        return errors  # short-circuit; the rest depends on these being OK
    if not _is_valid_kind_code(old_code):
        errors.append(
            f"old_code {old_code!r} is not a valid kind-code shape "
            "(expected lowercase letters, digits, hyphens; non-empty)"
        )
    if not _is_valid_kind_code(new_code):
        errors.append(
            f"new_code {new_code!r} is not a valid kind-code shape "
            "(expected lowercase letters, digits, hyphens; non-empty)"
        )
    if errors:
        return errors
    base = content_dir or _CONTENT
    # Old must exist somewhere; new must NOT already exist as a kind
    # in kinds.yaml.
    usage = discover_kind_usage(old_code, content_dir=base)
    if usage["total"] == 0:
        errors.append(f"old_code {old_code!r} has zero references — nothing to rename")
    new_usage = discover_kind_usage(new_code, content_dir=base)
    if new_usage["total"] > 0:
        errors.append(
            f"new_code {new_code!r} already appears "
            f"{new_usage['total']} time(s) — would collide; pick a "
            f"different new code or remove the existing one first"
        )
    if not plan["files"]:
        errors.append("plan is empty; nothing to do")
    return errors


# ----------------------------------------------------------------------
# Apply
# ----------------------------------------------------------------------


def apply_kind_rename(
    plan: dict,
    *,
    dry_run: bool = False,
    refactor_log_path: Path | None = None,
    now: datetime | None = None,
) -> dict:
    """Apply the rename plan atomically.

    Each touched file gets a backup BEFORE its first mutation.
    If any mutation fails, the runner restores all backups and
    aborts. On success, appends an audit entry to
    ``content/.refactor_log.yaml``.

    Returns ``{ok, applied_files, errors, dry_run, audit_id}``.
    """
    from scripts.core import notes_io

    if dry_run:
        return {
            "ok": True,
            "applied_files": [],
            "errors": [],
            "dry_run": True,
            "audit_id": None,
            "summary": plan["summary"],
        }

    backups: list[tuple[Path, Path]] = []  # (original, backup)
    applied: list[str] = []
    errors: list[str] = []

    try:
        for entry in plan["files"]:
            src = Path(entry["path"])
            backup = notes_io.ensure_backup(src)
            backups.append((src, backup))
            if entry["kind"] == "yaml":
                _write_yaml_rewrite(src, entry["mutations"])
            elif entry["kind"] == "py":
                _write_python_rewrite(src, entry["mutations"])
            else:
                raise ValueError(f"unknown plan kind: {entry['kind']}")
            applied.append(entry["rel"])
    except Exception as e:
        # Roll back every successful write so the tree is untouched.
        for src, backup in backups:
            if backup is not None and backup.is_file():
                try:
                    notes_io.atomic_write_bytes(src, backup.read_bytes())
                except Exception:
                    errors.append(
                        f"rollback failed for {src.name}: state may be inconsistent — restore manually from {backup}"
                    )
        return {
            "ok": False,
            "applied_files": [],
            "errors": [f"apply failed: {e}"] + errors,
            "dry_run": False,
            "audit_id": None,
            "summary": plan["summary"],
        }

    audit_id = _append_refactor_log(
        action="rename-kind",
        old=plan["old_code"],
        new=plan["new_code"],
        files=applied,
        log_path=refactor_log_path,
        now=now,
    )
    return {
        "ok": True,
        "applied_files": applied,
        "errors": [],
        "dry_run": False,
        "audit_id": audit_id,
        "summary": plan["summary"],
    }


# ----------------------------------------------------------------------
# YAML rewrite primitives
# ----------------------------------------------------------------------


def _yaml_kind_patterns(old_code: str) -> tuple[re.Pattern, re.Pattern]:
    """Two regexes pinned to specific YAML positions:
      - record code (kinds.yaml): `<spaces>- code: <old>` at EOL.
        The leading list-item dash is part of the prefix because
        in this project's kinds.yaml shape, ``code:`` is always
        the first field of a kind record.
      - list item: `<spaces>- <old>` at EOL (covers
        `enabled_kinds:` / `disabled_kinds:` items in editions /
        templates / scenarios).

    Both anchored to start-of-line whitespace + a known prefix to
    avoid false positives in random text fields."""
    escaped = re.escape(old_code)
    code_re = re.compile(
        rf"^(?P<prefix>\s+-\s+code:\s*){escaped}(?P<suffix>\s*(?:#.*)?)$",
    )
    item_re = re.compile(
        rf"^(?P<prefix>\s+-\s+){escaped}(?P<suffix>\s*(?:#.*)?)$",
    )
    return code_re, item_re


def _count_yaml_refs(
    path: Path,
    patterns: list[re.Pattern],
) -> int:
    """Count lines in ``path`` matching any of ``patterns``.
    ω.25.1 extracted this from the kind-specific helper so both
    kind and category rewriters share the line-scan loop."""
    count = 0
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return 0
    for line in text.splitlines():
        if any(p.match(line) for p in patterns):
            count += 1
    return count


def _plan_yaml_rewrite(
    path: Path,
    patterns: list[re.Pattern],
    new_value: str,
) -> list[dict]:
    """Return a list of `{line_num, old_line, new_line}` records.
    line_num is 1-indexed, matching how editors display them.

    Each pattern must capture two named groups (``prefix`` and
    ``suffix``) bracketing the value to be replaced. The
    replacement is `prefix + new_value + suffix`."""
    mutations: list[dict] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return mutations
    for i, line in enumerate(text.splitlines(), start=1):
        for pat in patterns:
            m = pat.match(line)
            if not m:
                continue
            new_line = f"{m.group('prefix')}{new_value}{m.group('suffix')}"
            mutations.append(
                {
                    "line_num": i,
                    "old_line": line,
                    "new_line": new_line,
                }
            )
            break
    return mutations


def _write_yaml_rewrite(
    path: Path,
    mutations: list[dict],
) -> None:
    """Apply YAML-line mutations and atomic-write."""
    from scripts.core import notes_io

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    by_line = {m["line_num"]: m for m in mutations}
    for i, raw in enumerate(lines, start=1):
        if i not in by_line:
            continue
        m = by_line[i]
        # Preserve whether the original line ended with a newline.
        trailing = "\n" if raw.endswith("\n") else ""
        if raw.rstrip("\n") != m["old_line"]:
            raise RuntimeError(
                f"{path.name}:{i}: line drifted between plan + apply (expected {m['old_line']!r}, got {raw.rstrip()!r})"
            )
        lines[i - 1] = m["new_line"] + trailing
    notes_io.atomic_write(path, "".join(lines))


# ----------------------------------------------------------------------
# Python notes-file rewrite primitives (AST-walk)
# ----------------------------------------------------------------------


def _walk_kind_string_nodes(
    text: str,
    old_code: str,
) -> list[ast.Constant]:
    """Find every `ast.Constant` node whose value is the kind string,
    sitting at position [4] of a tuple inside the top-level NOTES
    list. The note-tuple format (per the docstring at the top of
    every ``content/notes/<book>.py``) is::

        (chapter, verse, suffix, anchor, kind, title, label,
         body_html [, attribution])

    Position 4 = ``kind``. Skipping tuples shorter than 5 elements
    (legacy / partial seeds); skipping anything outside this exact
    shape so kind codes appearing in body text or attribution
    don't match."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    notes_list: ast.List | None = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id in ("NOTES", "notes"):
                    if isinstance(node.value, ast.List):
                        notes_list = node.value
                        break
        if notes_list is not None:
            break
    if notes_list is None:
        return []
    matches: list[ast.Constant] = []
    for tup in notes_list.elts:
        if not isinstance(tup, ast.Tuple):
            continue
        if len(tup.elts) < 5:
            continue
        kind_node = tup.elts[4]
        if isinstance(kind_node, ast.Constant) and isinstance(kind_node.value, str) and kind_node.value == old_code:
            matches.append(kind_node)
    return matches


def _count_python_kind_refs(path: Path, old_code: str) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return 0
    return len(_walk_kind_string_nodes(text, old_code))


def _plan_python_rewrite(
    path: Path,
    old_code: str,
    new_code: str,
) -> list[dict]:
    """Compute one mutation per matching tuple-position-3 string
    literal. Each carries the AST node's source range so the writer
    can do precise text-slice replacement."""
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    nodes = _walk_kind_string_nodes(text, old_code)
    if not nodes:
        return []
    return [
        {
            "lineno": n.lineno,
            "col_offset": n.col_offset,
            "end_lineno": n.end_lineno,
            "end_col_offset": n.end_col_offset,
            "old": old_code,
            "new": new_code,
        }
        for n in nodes
    ]


def _write_python_rewrite(
    path: Path,
    mutations: list[dict],
) -> None:
    """Apply position-precise text-slice replacements + verify the
    file still parses, then atomic-write. Raises on parse failure
    so the caller can roll back."""
    from scripts.core import notes_io

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    # Apply in reverse order so earlier mutations' positions don't
    # shift before they're written.
    by_position = sorted(
        mutations,
        key=lambda m: (m["lineno"], m["col_offset"]),
        reverse=True,
    )
    new_code: str = mutations[0]["new"]
    for m in by_position:
        # ast.Constant for a string literal sits between
        # (lineno, col_offset) and (end_lineno, end_col_offset).
        # Single-line strings (the common case) are easy:
        # replace the slice on `lines[lineno - 1]`.
        if m["lineno"] != m["end_lineno"]:
            raise RuntimeError(
                f"{path.name}:{m['lineno']}: multi-line kind string is not expected; refusing to rewrite"
            )
        idx = m["lineno"] - 1
        line = lines[idx]
        # The literal includes the surrounding quotes — safest to
        # match the literal text and replace it as a whole. We
        # extract the quoted substring then replace with the new
        # quoted form using the same quote character.
        original = line[m["col_offset"] : m["end_col_offset"]]
        # original looks like `"comm-evangelical"` or
        # `'comm-evangelical'`. Replace just the inner portion.
        if not (len(original) >= 2 and original[0] == original[-1] and original[0] in ("'", '"')):
            raise RuntimeError(
                f"{path.name}:{m['lineno']}:{m['col_offset']}: unexpected literal shape {original!r}; refusing"
            )
        quote = original[0]
        if original[1:-1] != m["old"]:
            raise RuntimeError(
                f"{path.name}:{m['lineno']}:{m['col_offset']}: AST said {m['old']!r} but text shows {original[1:-1]!r}"
            )
        replacement = f"{quote}{m['new']}{quote}"
        lines[idx] = line[: m["col_offset"]] + replacement + line[m["end_col_offset"] :]
    new_text = "".join(lines)
    # Verify the file still parses before committing.
    try:
        ast.parse(new_text)
    except SyntaxError as e:
        raise RuntimeError(f"{path.name}: rewrite produced invalid Python: {e}")
    notes_io.atomic_write(path, new_text)


# ----------------------------------------------------------------------
# ω.25.1 — Category-rename surface
#
# Categories appear in three YAML positions (none in notes/*.py):
#   1. content/categories.yaml      — `- id: <category>` (the registry)
#   2. content/kinds.yaml           — `category: <category>` field on
#                                      each kind record (continuation
#                                      line, NOT a list-item)
#   3. editions / templates /       — `- <category>` items in
#      scenarios YAML files          `enabled_categories:` lists
#
# Reuses the generic `_count_yaml_refs` / `_plan_yaml_rewrite` helpers
# from the kind path; only the patterns list and target file list
# differ.
# ----------------------------------------------------------------------


def category_target_files(
    content_dir: Path | None = None,
) -> list[Path]:
    """Every file that may contain a category reference. No
    notes/*.py — categories don't appear in note tuples."""
    base = content_dir or _CONTENT
    files: list[Path] = []
    if (base / "categories.yaml").is_file():
        files.append(base / "categories.yaml")
    if (base / "kinds.yaml").is_file():
        files.append(base / "kinds.yaml")
    if (base / "editions.yaml").is_file():
        files.append(base / "editions.yaml")
    templates = base / "edition_templates"
    if templates.is_dir():
        files.extend(sorted(templates.glob("*.yaml")))
    scenarios = base / "scenarios"
    if scenarios.is_dir():
        files.extend(sorted(scenarios.glob("*.yaml")))
    return files


def _yaml_category_patterns(
    old_id: str,
) -> tuple[
    re.Pattern,
    re.Pattern,
    re.Pattern,
]:
    """Three regexes pinned to specific YAML positions:
      - registry record (categories.yaml):
        `<spaces>- id: <old>` at EOL.
      - kind's category field (kinds.yaml):
        `<spaces>category: <old>` at EOL (continuation line; NO
        leading list-item dash).
      - list item (editions/templates/scenarios):
        `<spaces>- <old>` at EOL — same shape as kind list-items.

    All anchored to start-of-line whitespace + a known prefix to
    avoid matching arbitrary text fields."""
    escaped = re.escape(old_id)
    registry_re = re.compile(
        rf"^(?P<prefix>\s+-\s+id:\s*){escaped}(?P<suffix>\s*(?:#.*)?)$",
    )
    field_re = re.compile(
        rf"^(?P<prefix>\s+category:\s*){escaped}(?P<suffix>\s*(?:#.*)?)$",
    )
    item_re = re.compile(
        rf"^(?P<prefix>\s+-\s+){escaped}(?P<suffix>\s*(?:#.*)?)$",
    )
    return registry_re, field_re, item_re


def discover_category_usage(
    old_id: str,
    *,
    content_dir: Path | None = None,
) -> dict:
    """Walk every category target file; return per-file ref counts.
    Note: the list-item pattern (`^\\s+- <id>$`) overlaps with the
    kind list-item pattern, so a category id that also happens to
    be a kind code (rare but possible) would over-report. Validation
    surfaces this as a collision before apply.
    """
    base = content_dir or _CONTENT
    patterns = list(_yaml_category_patterns(old_id))
    usage: dict[str, int] = {}
    total = 0
    for path in category_target_files(base):
        rel = str(path.relative_to(base.parent)).replace("\\", "/")
        # All category targets are YAML — no python path.
        count = _count_yaml_refs(path, patterns)
        if count:
            usage[rel] = count
            total += count
    return {"old_id": old_id, "usage": usage, "total": total}


def compute_category_rename_plan(
    old_id: str,
    new_id: str,
    *,
    content_dir: Path | None = None,
) -> dict:
    """Compute per-file rewrite plan for a category rename. Same
    shape as `compute_kind_rename_plan` but with `old_id` / `new_id`
    keys."""
    base = content_dir or _CONTENT
    patterns = list(_yaml_category_patterns(old_id))
    plan: list[dict] = []
    for path in category_target_files(base):
        rel = str(path.relative_to(base.parent)).replace("\\", "/")
        mutations = _plan_yaml_rewrite(path, patterns, new_id)
        if mutations:
            plan.append(
                {
                    "path": str(path),
                    "rel": rel,
                    "kind": "yaml",
                    "count": len(mutations),
                    "mutations": mutations,
                }
            )
    return {
        "old_id": old_id,
        "new_id": new_id,
        "files": plan,
        "summary": {
            "files": len(plan),
            "total_mutations": sum(p["count"] for p in plan),
        },
    }


_CATEGORY_ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")


def _is_valid_category_id(cid: str) -> bool:
    """Project convention: category ids share the same shape as
    kind codes — lowercase, hyphenated, alphanumeric."""
    return bool(cid) and bool(_CATEGORY_ID_RE.match(cid))


def validate_category_rename(
    old_id: str,
    new_id: str,
    plan: dict,
    *,
    content_dir: Path | None = None,
) -> list[str]:
    """Sanity-check the category rename. Same shape as
    `validate_kind_rename` with id-vs-code labelling."""
    errors: list[str] = []
    if not old_id or not isinstance(old_id, str):
        errors.append("old_id must be a non-empty string")
    if not new_id or not isinstance(new_id, str):
        errors.append("new_id must be a non-empty string")
    if old_id == new_id:
        errors.append("old_id and new_id are identical")
    if errors:
        return errors
    if not _is_valid_category_id(old_id):
        errors.append(
            f"old_id {old_id!r} is not a valid category-id shape "
            "(expected lowercase letters, digits, hyphens; non-empty)"
        )
    if not _is_valid_category_id(new_id):
        errors.append(
            f"new_id {new_id!r} is not a valid category-id shape "
            "(expected lowercase letters, digits, hyphens; non-empty)"
        )
    if errors:
        return errors
    base = content_dir or _CONTENT
    usage = discover_category_usage(old_id, content_dir=base)
    if usage["total"] == 0:
        errors.append(f"old_id {old_id!r} has zero references — nothing to rename")
    new_usage = discover_category_usage(new_id, content_dir=base)
    if new_usage["total"] > 0:
        errors.append(
            f"new_id {new_id!r} already appears "
            f"{new_usage['total']} time(s) — would collide; pick a "
            f"different new id or remove the existing one first"
        )
    if not plan["files"]:
        errors.append("plan is empty; nothing to do")
    return errors


def apply_category_rename(
    plan: dict,
    *,
    dry_run: bool = False,
    refactor_log_path: Path | None = None,
    now: datetime | None = None,
) -> dict:
    """Apply a category-rename plan atomically. Mirrors
    `apply_kind_rename`'s contract: backup-before-mutation +
    rollback-on-failure + audit-log-on-success. Audit log entry's
    ``action`` is ``rename-category``."""
    from scripts.core import notes_io

    if dry_run:
        return {
            "ok": True,
            "applied_files": [],
            "errors": [],
            "dry_run": True,
            "audit_id": None,
            "summary": plan["summary"],
        }

    backups: list[tuple[Path, Path]] = []
    applied: list[str] = []
    errors: list[str] = []

    try:
        for entry in plan["files"]:
            src = Path(entry["path"])
            backup = notes_io.ensure_backup(src)
            backups.append((src, backup))
            _write_yaml_rewrite(src, entry["mutations"])
            applied.append(entry["rel"])
    except Exception as e:
        for src, backup in backups:
            if backup is not None and backup.is_file():
                try:
                    notes_io.atomic_write_bytes(src, backup.read_bytes())
                except Exception:
                    errors.append(
                        f"rollback failed for {src.name}: state may be inconsistent — restore manually from {backup}"
                    )
        return {
            "ok": False,
            "applied_files": [],
            "errors": [f"apply failed: {e}"] + errors,
            "dry_run": False,
            "audit_id": None,
            "summary": plan["summary"],
        }

    audit_id = _append_refactor_log(
        action="rename-category",
        old=plan["old_id"],
        new=plan["new_id"],
        files=applied,
        log_path=refactor_log_path,
        now=now,
    )
    return {
        "ok": True,
        "applied_files": applied,
        "errors": [],
        "dry_run": False,
        "audit_id": audit_id,
        "summary": plan["summary"],
    }


# ----------------------------------------------------------------------
# Audit log
# ----------------------------------------------------------------------


def _append_refactor_log(
    *,
    action: str,
    old: str,
    new: str,
    files: list[str],
    log_path: Path | None = None,
    now: datetime | None = None,
) -> str:
    """Append an entry to ``content/.refactor_log.yaml``. Returns
    the entry's id ("refactor-NNNN"). Creates the file on first
    use."""
    from scripts.core import notes_io
    import yaml

    path = log_path or _REFACTOR_LOG
    if path.is_file():
        notes_io.ensure_backup(path)
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            data = {}
    else:
        data = {}
    if not isinstance(data, dict):
        data = {}
    entries = data.get("entries") or []
    if not isinstance(entries, list):
        entries = []
    next_n = len(entries) + 1
    entry_id = f"refactor-{next_n:04d}"
    timestamp = (now or datetime.now(timezone.utc)).strftime(
        "%Y-%m-%dT%H:%M:%SZ",
    )
    entry = {
        "id": entry_id,
        "action": action,
        "old": old,
        "new": new,
        "files": list(files),
        "applied_at": timestamp,
    }
    entries.append(entry)
    data["entries"] = entries
    text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    notes_io.atomic_write(path, text)
    return entry_id


# ----------------------------------------------------------------------
# Internal validation helpers
# ----------------------------------------------------------------------


_KIND_CODE_RE = re.compile(r"^[a-z][a-z0-9-]*$")


def _is_valid_kind_code(code: str) -> bool:
    """Project convention: kind codes are lowercase, hyphenated,
    alphanumeric. Loose enough to allow new conventions; tight
    enough to reject obvious typos."""
    return bool(code) and bool(_KIND_CODE_RE.match(code))


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="refactor",
        description=(
            "ω.25 — atomic project-wide rename. v1: kind codes "
            "(content/notes/*.py + kinds.yaml + editions.yaml + "
            "edition_templates/*.yaml + scenarios/*.yaml)."
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_rk = sub.add_parser(
        "rename-kind",
        help="rename a kind code everywhere it appears",
    )
    p_rk.add_argument("old", help="existing kind code")
    p_rk.add_argument("new", help="new kind code")
    p_rk.add_argument(
        "--apply",
        action="store_true",
        help="actually write changes (default: dry-run preview)",
    )
    p_rk.add_argument(
        "--dry-run",
        action="store_true",
        help="print plan without writing (the default; explicit form)",
    )
    p_rk.add_argument("--json", action="store_true", help="machine-readable JSON output")

    p_rc = sub.add_parser(
        "rename-category",
        help="rename a category id everywhere it appears (ω.25.1)",
    )
    p_rc.add_argument("old", help="existing category id")
    p_rc.add_argument("new", help="new category id")
    p_rc.add_argument(
        "--apply",
        action="store_true",
        help="actually write changes (default: dry-run preview)",
    )
    p_rc.add_argument(
        "--dry-run",
        action="store_true",
        help="print plan without writing (the default; explicit form)",
    )
    p_rc.add_argument("--json", action="store_true", help="machine-readable JSON output")

    args = parser.parse_args(argv)

    if args.cmd == "rename-kind":
        return _run_rename_kind(args)
    if args.cmd == "rename-category":
        return _run_rename_category(args)
    return 2


def _run_rename_kind(args) -> int:
    plan = compute_kind_rename_plan(args.old, args.new)
    errors = validate_kind_rename(args.old, args.new, plan)
    if errors:
        if args.json:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "errors": errors,
                        "summary": plan["summary"],
                    },
                    indent=2,
                )
            )
        else:
            for e in errors:
                print(f"  ✗ {e}", file=sys.stderr)
        return 1
    dry_run = not args.apply
    result = apply_kind_rename(plan, dry_run=dry_run)
    if args.json:
        print(
            json.dumps(
                {
                    "ok": result["ok"],
                    "dry_run": result["dry_run"],
                    "summary": plan["summary"],
                    "applied_files": result["applied_files"],
                    "errors": result["errors"],
                    "audit_id": result["audit_id"],
                    "files": [{"rel": f["rel"], "kind": f["kind"], "count": f["count"]} for f in plan["files"]],
                },
                indent=2,
            )
        )
        return 0 if result["ok"] else 1
    label = "PLAN" if dry_run else "APPLIED"
    print(f"\n  {label}: rename {args.old!r} → {args.new!r}\n")
    for f in plan["files"]:
        print(f"    {f['count']:4d}  {f['rel']}")
    print(f"\n  total: {plan['summary']['total_mutations']} mutation(s) across {plan['summary']['files']} file(s)")
    if dry_run:
        print("\n  (dry-run — re-run with --apply to commit)")
    elif result["ok"]:
        print(f"\n  ✓ audit id {result['audit_id']}")
    else:
        for e in result["errors"]:
            print(f"  ✗ {e}", file=sys.stderr)
    return 0 if result["ok"] else 1


def _run_rename_category(args) -> int:
    """ω.25.1 — CLI route adapter for category rename. Mirrors
    `_run_rename_kind`'s shape; differs only in the helper functions
    + payload field names (old_id/new_id rather than
    old_code/new_code)."""
    plan = compute_category_rename_plan(args.old, args.new)
    errors = validate_category_rename(args.old, args.new, plan)
    if errors:
        if args.json:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "errors": errors,
                        "summary": plan["summary"],
                    },
                    indent=2,
                )
            )
        else:
            for e in errors:
                print(f"  ✗ {e}", file=sys.stderr)
        return 1
    dry_run = not args.apply
    result = apply_category_rename(plan, dry_run=dry_run)
    if args.json:
        print(
            json.dumps(
                {
                    "ok": result["ok"],
                    "dry_run": result["dry_run"],
                    "summary": plan["summary"],
                    "applied_files": result["applied_files"],
                    "errors": result["errors"],
                    "audit_id": result["audit_id"],
                    "files": [{"rel": f["rel"], "kind": f["kind"], "count": f["count"]} for f in plan["files"]],
                },
                indent=2,
            )
        )
        return 0 if result["ok"] else 1
    label = "PLAN" if dry_run else "APPLIED"
    print(f"\n  {label}: rename category {args.old!r} → {args.new!r}\n")
    for f in plan["files"]:
        print(f"    {f['count']:4d}  {f['rel']}")
    print(f"\n  total: {plan['summary']['total_mutations']} mutation(s) across {plan['summary']['files']} file(s)")
    if dry_run:
        print("\n  (dry-run — re-run with --apply to commit)")
    elif result["ok"]:
        print(f"\n  ✓ audit id {result['audit_id']}")
    else:
        for e in result["errors"]:
            print(f"  ✗ {e}", file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
