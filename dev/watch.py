#!/usr/bin/env python3
"""ω.21 — Watch mode (dev-loop file watcher).

Polls the project's load-bearing files for mtime changes and re-runs
the rules linter on every detected change. Optional `--build` mode
also subprocesses `scripts/build_edition.py` for the active edition,
which now hits the ω.20 content-addressable cache when nothing
load-bearing for that edition has actually changed (~ms vs
30-90s).

Pairs with the ω.20 chain: the cache makes rebuilds cheap; this
tool makes the rebuild trigger automatic. The result is a tight
edit-save-lint-(build) dev loop where the only manual step is the
edit itself.

Per CLAUDE_PROJECT_RULES §10 (standard library only on the
backend), this ships **without** the `watchdog` external dep the
original PLAN sketch suggested. mtime-polling is adequate for a
dev tool — a filesystem walk every couple of seconds is cheap
relative to the lint/build it triggers.

Usage::

    python dev/watch.py                       # lint on every change
    python dev/watch.py --interval 5          # poll every 5 seconds
    python dev/watch.py --build               # also rebuild active edition
    python dev/watch.py --build --edition catholic-study
    python dev/watch.py --once                # one pass, then exit (CI-friendly)

Exit on Ctrl+C. Exit code reflects the most recent action's verdict:
0 on success, non-zero on lint or build failure.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


_REPO = Path(__file__).resolve().parent.parent

# Ensure `scripts.*` imports resolve when this file is invoked as a
# CLI from any cwd (e.g. `python dev/watch.py` from a sibling shell).
# Without this, `from scripts.lint_rules import run_all` fails with
# ModuleNotFoundError because Python's auto-prepend uses the script's
# own parent (`dev/`) rather than the repo root.
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


# ----------------------------------------------------------------------
# Pure helpers (testable without a real filesystem watcher)
# ----------------------------------------------------------------------


def default_targets() -> list[Path]:
    """Curated set of paths watch mode polls by default.

    Touching any of these is *load-bearing* — it could affect a
    build, a console render, or a linter check. Touching anything
    else (CHANGELOG.md, README.md, the various dev/SCOPE_*.md
    addenda) does NOT trigger a rebuild because nothing downstream
    consumes those automatically.
    """
    return [
        _REPO / "content" / "editions.yaml",
        _REPO / "content" / "kinds.yaml",
        _REPO / "content" / "categories.yaml",
        _REPO / "content" / "books.yaml",
        _REPO / "content" / "canons.yaml",
        _REPO / "content" / "notes",
        _REPO / "content" / "translations",
        _REPO / "content" / "reading_plans",
        _REPO / "scripts" / "web.py",
        _REPO / "scripts" / "build_edition.py",
        _REPO / "scripts" / "lint_rules.py",
        _REPO / "scripts" / "templates",
        _REPO / "scripts" / "core",
    ]


def compute_signature(paths: list[Path]) -> dict[str, float]:
    """Walk ``paths`` (files OR directories) and return
    ``{relative_path_string: mtime}`` for every regular file found.

    Skips dotfile dirs (`.backups`, `.cache`, `__pycache__`) and
    `.bak` / `.tmp` artifacts so editor swap files and the project's
    own backup machinery don't trigger spurious rebuilds.

    Path keys are POSIX-normalised relative-to-repo strings so the
    same change produces the same key on Windows + macOS + Linux.
    """
    sig: dict[str, float] = {}
    for p in paths:
        if not p.exists():
            continue
        if p.is_file():
            if _watchable(p):
                sig[_rel(p)] = p.stat().st_mtime
            continue
        # Directory walk
        for root, dirs, files in os.walk(p):
            # Prune dotfile + cache directories.
            dirs[:] = [d for d in dirs if not _skip_dir(d)]
            for name in files:
                fp = Path(root) / name
                if _watchable(fp):
                    try:
                        sig[_rel(fp)] = fp.stat().st_mtime
                    except OSError:
                        # File vanished between dirent listing and stat
                        # (rare race — OK to skip).
                        continue
    return sig


def detect_changes(
    old: dict[str, float],
    new: dict[str, float],
) -> dict[str, list[str]]:
    """Diff two signatures. Returns ``{added, modified, removed}``
    with sorted relative-path lists. Empty lists when nothing
    changed in that bucket; an all-empty result means no work."""
    old_keys = set(old.keys())
    new_keys = set(new.keys())
    added = sorted(new_keys - old_keys)
    removed = sorted(old_keys - new_keys)
    modified = sorted(k for k in old_keys & new_keys if old[k] != new[k])
    return {"added": added, "modified": modified, "removed": removed}


def has_changes(diff: dict[str, list[str]]) -> bool:
    """True when any of the three buckets is non-empty."""
    return any(diff.values())


# ----------------------------------------------------------------------
# Action runners
# ----------------------------------------------------------------------


def run_lint() -> dict:
    """Compose `scripts.lint_rules.run_all()` in-process. No
    subprocess startup cost. Returns the same shape as the linter
    itself: ``{checks: [...], summary: {...}}``.

    Wrapped in try/except so a linter import error / programming
    bug doesn't kill the watch loop — caller renders a friendly
    error and keeps polling.
    """
    try:
        from scripts.lint_rules import run_all

        return run_all()
    except Exception as e:
        return {
            "checks": [],
            "summary": {
                "total": 0,
                "pass": 0,
                "warn": 0,
                "fail": 1,
                "clean": False,
            },
            "error": f"lint_rules.run_all() raised: {e}",
        }


def run_build(
    edition_id: str,
    *,
    version: str = "v28a",
    output_dir: Path | None = None,
) -> int:
    """Subprocess to `scripts/build_edition.py` for ``edition_id``.
    Returns the subprocess exit code (0 on success).

    No `--force`: the ω.20-B integration means an unchanged edition
    serves from cache (~ms). The whole point of pairing watch mode
    with the cache is that repeated builds during a dev loop are
    cheap when nothing relevant changed.
    """
    if output_dir is None:
        output_dir = _REPO / "exports"
    cmd = [
        sys.executable,
        str(_REPO / "scripts" / "build_edition.py"),
        edition_id,
        "--output-dir",
        str(output_dir),
        "--version",
        version,
    ]
    proc = subprocess.run(cmd, cwd=str(_REPO), stdin=subprocess.DEVNULL)  # W-W1: Windows pytest/PowerShell guard
    return proc.returncode


# ----------------------------------------------------------------------
# Internal helpers
# ----------------------------------------------------------------------


_SKIP_DIRS = {".backups", ".cache", "__pycache__", ".pytest_cache", ".git", ".hg", "node_modules"}
_SKIP_SUFFIXES = (".bak", ".tmp", ".pyc", ".pyo", ".swp", ".swo")


def _skip_dir(name: str) -> bool:
    return name in _SKIP_DIRS or name.startswith(".")


def _watchable(path: Path) -> bool:
    if path.name.startswith("."):
        return False
    if any(path.name.endswith(s) for s in _SKIP_SUFFIXES):
        return False
    return True


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(_REPO)).replace("\\", "/")
    except ValueError:
        return str(path)


def _format_diff_summary(diff: dict[str, list[str]]) -> str:
    parts = []
    for key, prefix in (("added", "+"), ("modified", "~"), ("removed", "-")):
        for p in diff[key][:5]:
            parts.append(f"  {prefix} {p}")
        if len(diff[key]) > 5:
            parts.append(f"    … and {len(diff[key]) - 5} more {key}")
    return "\n".join(parts) if parts else "  (no changes)"


# ----------------------------------------------------------------------
# CLI entrypoint
# ----------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="watch",
        description=("ω.21 — watch project files; re-run lint (and optionally rebuild) on every change."),
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="seconds between polls (default: 2.0)",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help=(
            "after each lint pass, rebuild the active edition via scripts/build_edition.py (cache-aware since ω.20-B)"
        ),
    )
    parser.add_argument(
        "--edition",
        default="ethiopian-tewahedo",
        help=("edition id to rebuild when --build is set (default: ethiopian-tewahedo)"),
    )
    parser.add_argument(
        "--version",
        default="v28a",
        help="version label passed to build_edition.py (default: v28a)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help=(
            "do one signature snapshot + lint pass, then exit. CI-friendly; useful for confirming the watch surface."
        ),
    )
    args = parser.parse_args(argv)

    targets = default_targets()
    print(f"watching {len(targets)} target paths under {_REPO}", flush=True)

    last_sig = compute_signature(targets)
    print(f"  initial signature: {len(last_sig)} files", flush=True)

    last_exit = _do_one_pass(args)

    if args.once:
        return last_exit

    try:
        while True:
            time.sleep(args.interval)
            new_sig = compute_signature(targets)
            diff = detect_changes(last_sig, new_sig)
            if has_changes(diff):
                print("\n--- change detected ---", flush=True)
                print(_format_diff_summary(diff), flush=True)
                last_sig = new_sig
                last_exit = _do_one_pass(args)
    except KeyboardInterrupt:
        print("\n  watch stopped (Ctrl+C)", flush=True)
        return last_exit


def _do_one_pass(args) -> int:
    """Run the per-change action set: lint, optionally build.
    Returns the worst exit code seen (0 = all good)."""
    print("  running lint…", flush=True)
    lint_result = run_lint()
    summary = lint_result.get("summary", {})
    if lint_result.get("error"):
        print(f"  lint ERROR: {lint_result['error']}", flush=True)
        return 1
    if summary.get("clean"):
        print(
            f"  ✓ lint clean ({summary.get('pass', 0)}/{summary.get('total', 0)} checks)",
            flush=True,
        )
        lint_exit = 0
    else:
        print(
            f"  ✗ lint fail ({summary.get('fail', 0)} fail, {summary.get('warn', 0)} warn)",
            flush=True,
        )
        lint_exit = 1

    if not args.build:
        return lint_exit

    print(f"  rebuilding {args.edition!r}…", flush=True)
    build_exit = run_build(args.edition, version=args.version)
    if build_exit == 0:
        print("  ✓ build ok", flush=True)
    else:
        print(f"  ✗ build failed (exit {build_exit})", flush=True)

    return max(lint_exit, build_exit)


if __name__ == "__main__":
    sys.exit(main())
