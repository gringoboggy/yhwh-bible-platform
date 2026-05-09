#!/usr/bin/env python3
"""Phase ω.5 — one-shot migration helper: copy in-tree ``content/``
into the platform user-data dir.

When the platform ships as a desktop binary (θ.1 / θ.2), the
bundled ``content/`` template is a read-only resource inside the
.app/.exe. The user's mutable copy needs to live in
``user_data_root() / content`` instead. This script is what the
launcher (or the user, manually) runs once to bootstrap that
location:

    python3 scripts/migrate_to_user_data.py --dry-run    # see what would copy
    python3 scripts/migrate_to_user_data.py              # actually copy
    python3 scripts/migrate_to_user_data.py --force      # overwrite existing

Idempotent: a second run without ``--force`` reports "already
migrated" and exits 0 without re-copying. Safe to wire into the
launcher's first-run flow.

What gets copied: every file and directory under the in-tree
``content/`` (notes, candidates, sources, translations, covers,
audio, plus the YAML config files). Nothing under ``scripts/``,
``tests/``, ``dev/`` — those stay in the read-only repo bundle.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.core import paths  # noqa: E402

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
DIM = "\033[2m"
RESET = "\033[0m"


def _src_content() -> Path:
    """The in-tree (bundled) content/ directory — the migration source."""
    return paths.repo_root() / "content"


def _dst_content() -> Path:
    """The user-data content/ directory — the migration destination."""
    return paths.user_data_root() / "content"


def _is_already_migrated() -> bool:
    """Heuristic: destination exists AND has the editions.yaml marker."""
    dst = _dst_content()
    return (dst / "editions.yaml").is_file()


def _walk_files(root: Path):
    """Yield every regular file under ``root`` (recursive)."""
    for p in root.rglob("*"):
        if p.is_file():
            yield p


def plan_migration(src: Path, dst: Path) -> dict:
    """Compute the set of files to copy and stat the volume. Pure
    function — no I/O writes. Returns a stats dict the CLI prints."""
    if not src.is_dir():
        return {
            "src_exists": False, "files": [], "total_bytes": 0,
            "dst_exists": dst.exists(),
        }
    files = sorted(_walk_files(src))
    total_bytes = sum(f.stat().st_size for f in files)
    return {
        "src_exists": True,
        "files": files,
        "total_bytes": total_bytes,
        "dst_exists": dst.exists(),
    }


def perform_migration(src: Path, dst: Path, *, force: bool = False) -> dict:
    """Execute the copy. Skips files that already exist in ``dst``
    unless ``force`` is set. Creates ``dst`` if absent."""
    if not src.is_dir():
        return {"copied": 0, "skipped": 0, "errors": ["source missing"]}
    dst.mkdir(parents=True, exist_ok=True)
    copied = 0
    skipped = 0
    errors: list[str] = []
    for src_file in _walk_files(src):
        rel = src_file.relative_to(src)
        dst_file = dst / rel
        if dst_file.exists() and not force:
            skipped += 1
            continue
        try:
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)
            copied += 1
        except OSError as e:
            errors.append(f"{rel}: {e}")
    return {"copied": copied, "skipped": skipped, "errors": errors}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=("Bootstrap content/ into the user-data dir for "
                     "installed-binary deployments. Idempotent."),
    )
    p.add_argument("--dry-run", action="store_true",
                   help="show what would be copied; no writes.")
    p.add_argument("--force", action="store_true",
                   help="overwrite existing files in the destination.")
    args = p.parse_args(argv)

    src = _src_content()
    dst = _dst_content()

    print(f"Source:      {src}")
    print(f"Destination: {dst}")
    print()

    if not src.is_dir():
        print(f"{RED}REFUSING:{RESET} source content/ does not exist "
              f"at {src}.")
        return 1

    if _is_already_migrated() and not args.force and not args.dry_run:
        print(f"{GREEN}Already migrated{RESET} — destination has "
              f"editions.yaml marker.")
        print(f"  Re-run with {YELLOW}--force{RESET} to overwrite.")
        return 0

    plan = plan_migration(src, dst)
    n_files = len(plan["files"])
    mb = plan["total_bytes"] / (1024 * 1024)
    print(f"Plan: {n_files} files · {mb:.1f} MB total")
    if plan["dst_exists"]:
        print(f"  {DIM}(destination exists; existing files will be "
              f"{'overwritten' if args.force else 'skipped'}){RESET}")
    print()

    if args.dry_run:
        print(f"{DIM}--dry-run: nothing copied.{RESET}")
        return 0

    result = perform_migration(src, dst, force=args.force)
    print(f"{GREEN}✓{RESET} Copied:  {result['copied']:5d}")
    print(f"{DIM}-{RESET} Skipped: {result['skipped']:5d} "
          f"(already present)")
    if result["errors"]:
        print(f"{RED}✗{RESET} Errors:  {len(result['errors'])}")
        for err in result["errors"][:5]:
            print(f"    {err}")
        if len(result["errors"]) > 5:
            print(f"    {DIM}... {len(result['errors']) - 5} more "
                  f"errors omitted{RESET}")
        return 1
    print()
    print(f"{DIM}Next: set YHWH_CONTENT_ROOT to use the new location, "
          f"or simply delete the in-tree content/ directory and the "
          f"user-data dir wins automatically.{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
