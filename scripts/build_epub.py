#!/usr/bin/env python3
"""
build_epub.py — Build a valid EPUB 3 from epub_working/.

Replaces the legacy build.sh. Produces an EPUB-compliant zip:
  - mimetype is FIRST, uncompressed (store-only)
  - Everything else compressed (deflate level 9)
  - .DS_Store / __pycache__ / backups excluded

Optionally refreshes ``content.opf`` metadata before packaging:
  - ``<dc:date>`` -> today's date (UTC)
  - ``<meta property="dcterms:modified">`` -> current UTC ISO timestamp

Examples:
    python3 scripts/build_epub.py                       # default name
    python3 scripts/build_epub.py out/MyBible.epub      # custom path
    python3 scripts/build_epub.py --no-bump out.epub    # skip date refresh
    python3 scripts/build_epub.py --check               # validate only
"""

import argparse
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EPUB_DIR = REPO_ROOT / "epub_working"
DEFAULT_OUT = REPO_ROOT / "Ethiopian_Bible.epub"

# Filenames / patterns excluded from the package.
EXCLUDE_NAMES = {".DS_Store", "Thumbs.db"}
# "onix": build_onix.py writes commercial ONIX sales metadata to  term-ref-ok
# epub_working/onix/. The Ω.0 free-public pivot makes the EPUB a free  term-ref-ok
# give-away that must not carry sales metadata, so it is dropped here at the
# packaging chokepoint — covering both a direct build_epub.py run and the
# per-edition build_one path (which copies the whole working tree to a temp dir).
EXCLUDE_DIR_NAMES = {"__pycache__", "onix"}  # term-ref-ok
EXCLUDE_PREFIXES = ("notes.backup_",)


def err(msg: str) -> None:
    """Print to stderr and exit non-zero."""
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def info(msg: str) -> None:
    print(msg)


def validate_working_dir(epub_dir: Path) -> None:
    """Sanity-check the working dir before touching it."""
    if not epub_dir.is_dir():
        err(f"epub working dir not found: {epub_dir}")
    must_have = ["mimetype", "content.opf", "META-INF/container.xml"]
    for rel in must_have:
        if not (epub_dir / rel).exists():
            err(f"missing required file: {epub_dir / rel}")
    mimetype = (epub_dir / "mimetype").read_text().strip()
    if mimetype != "application/epub+zip":
        err(f"mimetype contents wrong: {mimetype!r}")


def bump_metadata(opf_path: Path) -> tuple[str, str]:
    """Refresh dc:date and dcterms:modified in content.opf.

    Returns (new_date, new_modified_iso) actually written.
    """
    now = datetime.now(timezone.utc)
    new_date = now.strftime("%Y-%m-%d")
    new_modified = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    text = opf_path.read_text(encoding="utf-8")
    new_text = re.sub(
        r"<dc:date>[^<]*</dc:date>",
        f"<dc:date>{new_date}</dc:date>",
        text,
        count=1,
    )
    new_text = re.sub(
        r'<meta property="dcterms:modified">[^<]*</meta>',
        f'<meta property="dcterms:modified">{new_modified}</meta>',
        new_text,
        count=1,
    )
    if new_text == text:
        info("  (no metadata change — patterns not found)")
    else:
        opf_path.write_text(new_text, encoding="utf-8")
    return new_date, new_modified


def should_skip(rel: Path) -> bool:
    """Return True if this file should be excluded from the package."""
    if rel.name in EXCLUDE_NAMES:
        return True
    if any(part in EXCLUDE_DIR_NAMES for part in rel.parts):
        return True
    return any(part.startswith(EXCLUDE_PREFIXES) for part in rel.parts)


def collect_files(epub_dir: Path) -> tuple[list[Path], int, int]:
    """Walk epub_dir; return (files_to_pack, total_bytes, n_skipped)."""
    files = []
    total = 0
    skipped = 0
    for path in sorted(epub_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(epub_dir)
        if rel.name == "mimetype":
            continue  # written first, separately
        if should_skip(rel):
            skipped += 1
            continue
        files.append(path)
        total += path.stat().st_size
    return files, total, skipped


def build(epub_dir: Path, out_path: Path, *, bump: bool) -> None:
    """Package epub_dir into out_path as a valid EPUB 3."""
    validate_working_dir(epub_dir)

    if bump:
        info("Refreshing OPF metadata...")
        new_date, new_modified = bump_metadata(epub_dir / "content.opf")
        info(f"  dc:date            -> {new_date}")
        info(f"  dcterms:modified   -> {new_modified}")

    files, total_bytes, n_skipped = collect_files(epub_dir)
    info(
        f"Packaging {len(files)} files ({total_bytes / 1024 / 1024:.1f} MB)"
        + (f", skipping {n_skipped}" if n_skipped else "")
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()

    with zipfile.ZipFile(out_path, "w", allowZip64=False) as zf:
        # mimetype must be first AND uncompressed for EPUB validation.
        # Pin date_time to the zip epoch minimum (1980-01-01) so the
        # central directory is reproducible across checkouts regardless
        # of each file's on-disk mtime (M14).
        mz = zipfile.ZipInfo("mimetype")
        mz.date_time = (1980, 1, 1, 0, 0, 0)
        mz.compress_type = zipfile.ZIP_STORED
        mz.external_attr = 0o644 << 16
        zf.writestr(mz, (epub_dir / "mimetype").read_bytes())
        for path in files:
            arcname = str(path.relative_to(epub_dir)).replace("\\", "/")
            zi = zipfile.ZipInfo(arcname)
            zi.date_time = (1980, 1, 1, 0, 0, 0)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            zf.writestr(zi, path.read_bytes(), compresslevel=9)

    out_size = out_path.stat().st_size
    info(f"\nBuilt: {out_path}  ({out_size / 1024 / 1024:.2f} MB)")


def check(epub_dir: Path) -> None:
    """Validate the working dir without building."""
    validate_working_dir(epub_dir)
    files, total, skipped = collect_files(epub_dir)
    info(f"OK: {epub_dir}")
    info(f"  mimetype + {len(files)} files ({total / 1024 / 1024:.1f} MB)")
    info(f"  excluded: {skipped}")


def main() -> None:
    p = argparse.ArgumentParser(description="Build EPUB 3 from epub_working/.")
    p.add_argument(
        "output",
        nargs="?",
        type=Path,
        default=DEFAULT_OUT,
        help=f"output .epub path (default: {DEFAULT_OUT.relative_to(REPO_ROOT)})",
    )
    p.add_argument(
        "--epub-dir",
        type=Path,
        default=EPUB_DIR,
        help=f"working EPUB dir (default: {EPUB_DIR.relative_to(REPO_ROOT)})",
    )
    p.add_argument(
        "--no-bump",
        action="store_true",
        help="skip refreshing dc:date / dcterms:modified",
    )
    p.add_argument(
        "--check",
        action="store_true",
        help="validate the working dir without building",
    )
    args = p.parse_args()

    if args.check:
        check(args.epub_dir)
        return
    build(args.epub_dir, args.output, bump=not args.no_bump)


if __name__ == "__main__":
    main()
