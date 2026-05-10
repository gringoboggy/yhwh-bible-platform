#!/usr/bin/env python3
"""
manifest.py — SHA-256 integrity manifest for content/notes/*.py.

Three commands:

    python3 scripts/manifest.py --build       # compute + write manifest
    python3 scripts/manifest.py --verify      # check current files vs manifest
    python3 scripts/manifest.py --status      # short summary, exit non-zero on drift

The manifest is stored at ``content/notes/.manifest.json`` and contains,
for each notes file, its SHA-256 hex digest, byte size, and last-modified
mtime. The integrity model is intentionally simple:

  - Build the manifest at the end of every save (snapshot of corpus state).
  - Verify on session start (catches silent corruption, accidental edits
    by external tools, partial restores from incomplete unzips).
  - Re-build (--build) whenever the user has knowingly modified the
    corpus — promote.py / add_note.py / attribute.py / bulk_edit.py
    don't re-build automatically because each call is one of many small
    edits; rebuilding once at save time is the right granularity.

This complements (does not replace) ``verify.py`` (anchor parity) and
``validate_taxonomy.py`` (schema soundness). Manifest catches *content*
corruption that those structural checks miss.

Phase β audit reference: finding S2 (no hash manifest / corruption
detection).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
NOTES_DIR = REPO_ROOT / "content" / "notes"
MANIFEST_PATH = NOTES_DIR / ".manifest.json"

sys.path.insert(0, str(REPO_ROOT))

from scripts.core.notes_io import atomic_write  # noqa: E402

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_manifest() -> dict:
    """Walk content/notes/*.py and return a manifest dict ready for serialisation."""
    files: dict = {}
    for p in sorted(NOTES_DIR.glob("*.py")):
        if p.name.startswith("__"):
            continue
        st = p.stat()
        files[p.name] = {
            "sha256": sha256_of_file(p),
            "size": st.st_size,
            "mtime": int(st.st_mtime),
        }
    return {
        "version": 1,
        "directory": str(NOTES_DIR.relative_to(REPO_ROOT)),
        "file_count": len(files),
        "files": files,
    }


def save_manifest(manifest: dict) -> None:
    text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    atomic_write(MANIFEST_PATH, text)


def load_manifest() -> dict | None:
    if not MANIFEST_PATH.is_file():
        return None
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def verify_manifest(stored: dict) -> dict:
    """Compare stored manifest to the current state of NOTES_DIR.

    Returns a report dict:
        {
            "ok": bool,
            "drift": [(filename, reason), ...],
            "added":   [filename, ...],   # present on disk, not in manifest
            "missing": [filename, ...],   # in manifest, gone from disk
            "checked": int,
        }
    """
    current = compute_manifest()
    stored_files = stored.get("files", {})
    current_files = current["files"]

    drift: list[tuple[str, str]] = []
    for name, meta in stored_files.items():
        if name not in current_files:
            continue  # tracked separately as "missing"
        cur = current_files[name]
        if meta.get("sha256") != cur["sha256"]:
            drift.append((name, f"sha256 mismatch (size: {meta.get('size')} → {cur['size']})"))

    added = sorted(set(current_files) - set(stored_files))
    missing = sorted(set(stored_files) - set(current_files))

    return {
        "ok": not drift and not missing,
        "drift": drift,
        "added": added,
        "missing": missing,
        "checked": len(stored_files),
    }


def main() -> None:
    p = argparse.ArgumentParser(
        description="SHA-256 integrity manifest for content/notes/.",
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--build", action="store_true", help="compute fresh manifest and write to .manifest.json")
    g.add_argument("--verify", action="store_true", help="verify current files against stored manifest (verbose)")
    g.add_argument("--status", action="store_true", help="quick verification summary, exits non-zero on drift")
    args = p.parse_args()

    if args.build:
        manifest = compute_manifest()
        save_manifest(manifest)
        print(f"{GREEN}✓{RESET} manifest: {manifest['file_count']} file(s) hashed")
        print(f"  {DIM}{MANIFEST_PATH.relative_to(REPO_ROOT)}{RESET}")
        sys.exit(0)

    stored = load_manifest()
    if not stored:
        print(f"{YELLOW}⚠{RESET} no manifest found at {MANIFEST_PATH.relative_to(REPO_ROOT)}")
        print(f"  run: python3 scripts/manifest.py --build")
        sys.exit(2)

    report = verify_manifest(stored)

    if args.status:
        if report["ok"] and not report["added"]:
            print(f"{GREEN}✓{RESET} manifest clean ({report['checked']} files match)")
            sys.exit(0)
        print(
            f"{RED}✗{RESET} manifest drift: "
            f"{len(report['drift'])} modified, "
            f"{len(report['missing'])} missing, "
            f"{len(report['added'])} new (not in manifest)"
        )
        sys.exit(1)

    # --verify: full report
    print(f"\n{BOLD}Manifest verification{RESET}\n")
    print(f"  {report['checked']} files in stored manifest")
    if report["drift"]:
        print(f"\n  {RED}drift ({len(report['drift'])}):{RESET}")
        for name, reason in report["drift"]:
            print(f"    {RED}✗{RESET} {name}: {reason}")
    if report["missing"]:
        print(f"\n  {RED}missing ({len(report['missing'])}):{RESET}")
        for name in report["missing"]:
            print(f"    {RED}–{RESET} {name}")
    if report["added"]:
        print(f"\n  {YELLOW}new (not in manifest, possibly legitimate addition):{RESET}")
        for name in report["added"]:
            print(f"    {YELLOW}+{RESET} {name}")
    print()
    if report["ok"] and not report["added"]:
        print(f"  {GREEN}✓ all files match{RESET}\n")
        sys.exit(0)
    if report["ok"]:
        print(f"  {YELLOW}⚠ no drift but new files present — rebuild manifest if these are intended{RESET}\n")
        sys.exit(0)
    print(f"  {RED}✗ drift detected. Investigate before saving.{RESET}\n")
    sys.exit(1)


if __name__ == "__main__":
    main()
