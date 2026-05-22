#!/usr/bin/env python3
"""
cleanup.py — Repeatable project cruft cleanup.

Removes auto-generated artifacts (Python bytecode caches, stale npm
debug logs) and prunes the auto-generated `.backups/` directories down
to a small recent window. Does NOT touch user-intentional content
(source_archive utilities, candidate queues, reference materials).

Defaults are conservative:
  - dry-run mode is DEFAULT — pass --apply to actually delete
  - backup pruning keeps the N most recent per "stem" (default 5)
  - only auto-generated cruft is in scope; intentional retirements are
    your call

Usage:
    python3 scripts/cleanup.py                    # dry-run, all tiers
    python3 scripts/cleanup.py --apply            # actually delete
    python3 scripts/cleanup.py --keep 3 --apply   # keep only 3 most-recent backups
    python3 scripts/cleanup.py --no-backups       # skip backup pruning
    python3 scripts/cleanup.py --pycache-only     # only __pycache__ + *.pyc

Exit code: 0 if everything is clean (nothing to do), 0 if changes
applied successfully, 1 on any deletion error.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core.ui import GREEN, RED, YELLOW, DIM, BOLD, RESET  # noqa: E402

# ----------------------------------------------------------------------
# Discovery helpers
# ----------------------------------------------------------------------


def find_pycache(root: Path) -> tuple[list[Path], list[Path]]:
    """Return (cache_dirs, pyc_files) under root.

    Pyc files inside a __pycache__ directory are EXCLUDED from the file
    list because the directory deletion handles them — listing them
    separately would cause double-delete errors during apply.
    """
    # Skip the giant system-level dirs we never want to touch
    skip = {".cache", ".local", ".npm", ".npm-global", ".tools", ".config", "node_modules"}
    cache_dirs: list[Path] = []
    pyc_files: list[Path] = []
    for p in root.rglob("*"):
        # Filter out anything under skipped tops
        try:
            top = p.relative_to(root).parts[0]
        except (ValueError, IndexError):
            continue
        if top in skip:
            continue
        if p.is_dir() and p.name == "__pycache__":
            cache_dirs.append(p)
        elif p.is_file() and p.suffix == ".pyc":
            # Only count .pyc files that are NOT inside a __pycache__ dir
            # we're already deleting (avoid double-delete on rmtree).
            if not any(part == "__pycache__" for part in p.parts):
                pyc_files.append(p)
    return cache_dirs, pyc_files


def find_npm_logs(root: Path) -> list[Path]:
    """Return debug logs in .npm/_logs/."""
    logs_dir = root / ".npm" / "_logs"
    if not logs_dir.is_dir():
        return []
    return sorted(logs_dir.glob("*.log"))


def find_backup_files(root: Path) -> dict[Path, list[Path]]:
    """Return {backup_dir: [backup_files]} grouped by parent .backups/.

    Files within each .backups/ are further grouped by 'stem' — the
    original filename minus the timestamp+ext suffix — so we can keep
    the N most recent per stem.
    """
    backups: dict[Path, list[Path]] = defaultdict(list)
    for p in root.rglob(".backups"):
        if not p.is_dir():
            continue
        # Skip system-level paths (defensive)
        if any(part.startswith(".") and part not in (".backups",) for part in p.relative_to(root).parts[:-1]):
            continue
        for f in p.iterdir():
            if f.is_file():
                backups[p].append(f)
    return dict(backups)


def stem_of(backup_file: Path) -> str:
    """Strip the ISO-like timestamp + .bak suffix to recover the original
    filename stem. Backups follow `<name>.<ISO_TS>.<ext>.bak`.
    Examples:
        index_split_000.20260506T180334Z.html.bak  →  index_split_000.html
        gen.20260506T173712Z.py.bak                 →  gen.py
    """
    name = backup_file.name
    # Strip trailing .bak
    if name.endswith(".bak"):
        name = name[:-4]
    # Strip the ISO-like timestamp segment .YYYYMMDDTHHMMSSZ.
    name = re.sub(r"\.\d{8}T\d{6}Z(?=\.\w+$)", "", name)
    return name


# ----------------------------------------------------------------------
# ω.28 — Per-pattern backup retention policy
# ----------------------------------------------------------------------
#
# Today cleanup.py keeps 5 revisions per stem uniformly across the tree.
# That's right for low-volume stems (.backups/editions.20260509T*.bak)
# but too aggressive for high-volume stems (every notes-rewrite touches
# .backups/<book>.<ts>.py.bak; 5 revisions disappears in one batch
# attribution run).
#
# `content/.backup_retention.yaml` overrides per file pattern. Each
# rule has either `keep_revisions: N` (count-based) OR `keep_days: N`
# (time-based). First matching rule wins; default applies otherwise.
# Defaults preserve the current 5-revision behavior so absence of the
# config file is a no-op shift.
#
# Pattern matching uses `pathlib.PurePath.match(pattern)` against the
# ORIGINAL file path (recovered from each backup via `stem_of(file)`
# joined to `backup_dir.parent`). PurePath.match is right-anchored,
# so `Path("content/editions.yaml").match("editions.yaml")` returns
# True without needing the full path.


_DEFAULT_RETENTION = {
    "rules": [
        {"pattern": "content/notes/*.py", "keep_revisions": 10},
        {"pattern": "editions.yaml", "keep_days": 30},
        {"pattern": "kinds.yaml", "keep_days": 30},
        {"pattern": "categories.yaml", "keep_days": 30},
        {"pattern": "epub_working/**", "keep_revisions": 3},
    ],
    "default": {"keep_revisions": 5},
}


def load_retention_policy(
    config_path: Path | None = None,
) -> dict:
    """Load `content/.backup_retention.yaml` (or another location for
    tests) and merge over `_DEFAULT_RETENTION`. Missing file or
    corrupt YAML → defaults; the runner is opinionated about not
    failing the cleanup just because the config drifted.

    Returns ``{rules: [...], default: {...}}`` where each rule has a
    ``pattern`` plus exactly one of ``keep_revisions`` /
    ``keep_days``.
    """
    path = config_path or (REPO_ROOT / "content" / ".backup_retention.yaml")
    if not path.is_file():
        return _DEFAULT_RETENTION
    try:
        import yaml
    except ImportError:
        return _DEFAULT_RETENTION
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return _DEFAULT_RETENTION
    if not isinstance(raw, dict):
        return _DEFAULT_RETENTION
    rules = raw.get("rules") if isinstance(raw.get("rules"), list) else []
    default = raw["default"] if isinstance(raw.get("default"), dict) else _DEFAULT_RETENTION["default"]
    # Filter rules to ones with a pattern + exactly one of the two
    # retention keys; corrupt entries silently dropped.
    clean_rules: list[dict] = []
    for r in rules:
        if not isinstance(r, dict) or not isinstance(r.get("pattern"), str):
            continue
        has_revs = isinstance(r.get("keep_revisions"), int)
        has_days = isinstance(r.get("keep_days"), int)
        if has_revs ^ has_days:  # exactly one
            clean_rules.append(
                {
                    "pattern": r["pattern"],
                    **({"keep_revisions": r["keep_revisions"]} if has_revs else {}),
                    **({"keep_days": r["keep_days"]} if has_days else {}),
                }
            )
    return {"rules": clean_rules, "default": default}


def select_rule(file_path: Path, policy: dict) -> dict:
    """Return the first rule whose pattern matches ``file_path``, or
    the policy's default. ``file_path`` is the original (non-backup)
    file path, relative to repo root."""
    for rule in policy.get("rules") or []:
        pat = rule.get("pattern")
        if not pat:
            continue
        try:
            if file_path.match(pat):
                return rule
        except (ValueError, OSError):
            continue
    return policy.get("default") or _DEFAULT_RETENTION["default"]


def _backups_to_prune(
    backup_files: list[Path],
    rule: dict,
    *,
    now: float | None = None,
) -> list[Path]:
    """Apply one rule to a list of backup files (already filtered to
    one stem). Returns the subset that should be deleted.

    `keep_revisions: N` — sort newest-first; delete past index N.
    `keep_days: N` — delete files older than ``now - N*86400``.
    """
    if not backup_files:
        return []
    if "keep_revisions" in rule:
        n = max(0, int(rule["keep_revisions"]))
        sorted_files = sorted(
            backup_files,
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return sorted_files[n:]
    if "keep_days" in rule:
        days = max(0, int(rule["keep_days"]))
        cutoff = (now if now is not None else time.time()) - days * 86400
        return [f for f in backup_files if f.stat().st_mtime < cutoff]
    return []


def human_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024
    return f"{n:.1f} TB"


# ----------------------------------------------------------------------
# Plan construction
# ----------------------------------------------------------------------


def plan_pycache(cache_dirs: list[Path], pyc_files: list[Path]) -> tuple[list[Path], int]:
    bytes_total = 0
    targets: list[Path] = []
    for d in cache_dirs:
        try:
            sz = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
            bytes_total += sz
            targets.append(d)
        except (OSError, FileNotFoundError):
            pass
    for f in pyc_files:
        try:
            bytes_total += f.stat().st_size
            targets.append(f)
        except (OSError, FileNotFoundError):
            pass
    return targets, bytes_total


def plan_npm_logs(logs: list[Path]) -> tuple[list[Path], int]:
    bytes_total = 0
    targets: list[Path] = []
    for f in logs:
        try:
            bytes_total += f.stat().st_size
            targets.append(f)
        except (OSError, FileNotFoundError):
            pass
    return targets, bytes_total


def plan_backups(
    grouped: dict[Path, list[Path]],
    keep: int | None = None,
    *,
    policy: dict | None = None,
    now: float | None = None,
) -> tuple[list[Path], int]:
    """For each .backups/ dir, group files by stem, mark old/excess
    backups for deletion.

    Two modes:
      - ``keep`` (legacy/CLI override): single ``keep_revisions`` rule
        applied uniformly to every stem. Back-compat with the
        original signature.
      - ``policy`` (ω.28): per-pattern dispatch via
        ``load_retention_policy`` shape. Each stem's original file
        path picks a rule via ``select_rule``; the rule is then
        applied via ``_backups_to_prune``.

    When both are provided, ``keep`` wins (CLI override). When
    neither is provided, fall back to ``_DEFAULT_RETENTION``.
    """
    if keep is not None:
        effective_policy = {
            "rules": [],
            "default": {"keep_revisions": int(keep)},
        }
    else:
        effective_policy = policy or _DEFAULT_RETENTION

    bytes_total = 0
    targets: list[Path] = []
    for bdir, files in grouped.items():
        per_stem: dict[str, list[Path]] = defaultdict(list)
        for f in files:
            per_stem[stem_of(f)].append(f)
        for stem, group in per_stem.items():
            # Recover the original (non-backup) file path so we can
            # match it against policy patterns. The backups live at
            # `<original_dir>/.backups/<stem>.<ts>.<ext>.bak`, so the
            # original is `<original_dir>/<stem>` — i.e. `bdir.parent
            # / stem`. NOTE: we do NOT `.resolve()` here. On
            # case-insensitive filesystems (Windows) and inside test
            # tmp_paths, .resolve() can canonicalize the path in ways
            # that don't match REPO_ROOT, breaking relative_to.
            original = bdir.parent / stem
            try:
                rel = original.relative_to(REPO_ROOT)
            except ValueError:
                rel = Path(stem)
            rule = select_rule(rel, effective_policy)
            for f in _backups_to_prune(group, rule, now=now):
                try:
                    bytes_total += f.stat().st_size
                    targets.append(f)
                except (OSError, FileNotFoundError):
                    pass
    return targets, bytes_total


# ----------------------------------------------------------------------
# Execution
# ----------------------------------------------------------------------


def delete(targets: list[Path]) -> tuple[int, list[str]]:
    """Delete each target (file or dir). Returns (deleted_count, errors)."""
    n = 0
    errors: list[str] = []
    for t in targets:
        try:
            if t.is_dir():
                shutil.rmtree(t)
            else:
                t.unlink()
            n += 1
        except (OSError, FileNotFoundError) as e:
            errors.append(f"{t}: {e}")
    return n, errors


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(
        description="Repeatable project cruft cleanup. Dry-run by default.",
    )
    p.add_argument("--apply", action="store_true", help="actually delete (default is dry-run)")
    p.add_argument(
        "--keep",
        type=int,
        default=None,
        help=(
            "legacy: keep N most-recent backups per stem uniformly; "
            "overrides per-pattern policy. Default: use the policy "
            "in content/.backup_retention.yaml (or the built-in "
            "defaults if absent — ω.28)."
        ),
    )
    p.add_argument("--pycache-only", action="store_true", help="only clean __pycache__ + *.pyc")
    p.add_argument("--no-backups", action="store_true", help="skip backup pruning")
    p.add_argument("--no-npm-logs", action="store_true", help="skip npm debug log pruning")
    args = p.parse_args()

    if args.keep is not None and args.keep < 0:
        print(f"{RED}✗ --keep must be ≥ 0{RESET}", file=sys.stderr)
        sys.exit(2)

    # ω.28 — load policy from disk unless --keep overrides it.
    if args.keep is not None:
        retention_label = f"keep={args.keep} per stem (CLI override)"
        policy_for_plan = None
    else:
        policy = load_retention_policy()
        n_rules = len(policy.get("rules") or [])
        retention_label = f"per-pattern policy ({n_rules} rule(s) + default)"
        policy_for_plan = policy

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"\n{BOLD}cleanup{RESET}  {DIM}{mode} · {retention_label}{RESET}\n")

    # Build the plan
    sections: list[tuple[str, list[Path], int]] = []

    cache_dirs, pyc_files = find_pycache(REPO_ROOT)
    targets, bytes_ = plan_pycache(cache_dirs, pyc_files)
    sections.append((f"__pycache__/ + *.pyc  ({len(cache_dirs)} dirs, {len(pyc_files)} files)", targets, bytes_))

    if not args.pycache_only:
        if not args.no_npm_logs:
            logs = find_npm_logs(REPO_ROOT)
            targets, bytes_ = plan_npm_logs(logs)
            sections.append((f"npm debug logs  ({len(logs)} files)", targets, bytes_))
        if not args.no_backups:
            grouped = find_backup_files(REPO_ROOT)
            targets, bytes_ = plan_backups(
                grouped,
                args.keep,
                policy=policy_for_plan,
            )
            total_backup_files = sum(len(v) for v in grouped.values())
            label_suffix = f"keep {args.keep} per stem" if args.keep is not None else "per-pattern policy"
            sections.append(
                (
                    f"backup pruning  ({total_backup_files} backup files across {len(grouped)} dir(s); {label_suffix})",
                    targets,
                    bytes_,
                )
            )

    # Render plan
    grand_targets: list[Path] = []
    grand_bytes = 0
    for label, targets, bytes_ in sections:
        if not targets:
            print(f"  {GREEN}✓{RESET} {label}  {DIM}— nothing to remove{RESET}")
            continue
        print(f"  {YELLOW}→{RESET} {label}")
        print(f"      {DIM}{len(targets)} item(s), {human_bytes(bytes_)} to reclaim{RESET}")
        grand_targets.extend(targets)
        grand_bytes += bytes_

    print()
    if not grand_targets:
        print(f"  {GREEN}{BOLD}✓ nothing to clean — already tidy.{RESET}\n")
        sys.exit(0)

    print(f"  {BOLD}TOTAL: {len(grand_targets)} item(s), {human_bytes(grand_bytes)} to reclaim{RESET}\n")

    if not args.apply:
        print(f"  {DIM}Dry-run only. Re-run with {BOLD}--apply{RESET}{DIM} to actually delete.{RESET}\n")
        sys.exit(0)

    n, errors = delete(grand_targets)
    if errors:
        print(f"  {RED}✗ {len(errors)} error(s):{RESET}")
        for e in errors[:5]:
            print(f"    {DIM}{e}{RESET}")
        if len(errors) > 5:
            print(f"    {DIM}... and {len(errors) - 5} more{RESET}")
        print()
        sys.exit(1)
    print(f"  {GREEN}{BOLD}✓ deleted {n} item(s), reclaimed {human_bytes(grand_bytes)}{RESET}\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
