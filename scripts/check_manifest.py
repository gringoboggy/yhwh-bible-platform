#!/usr/bin/env python3
"""
check_manifest.py — Verify ``content.opf`` manifest matches the filesystem.

The OPF manifest must list every file the EPUB ships with (except ``mimetype``
itself and ``META-INF/container.xml``, which are EPUB-special). Drift between
manifest and disk causes silent failures: e.g., a new chapter file added by
hand but not registered in the manifest will simply be missing in the reader.

Examples:
    python3 scripts/check_manifest.py            # report only
    python3 scripts/check_manifest.py --fix      # auto-add missing items
    python3 scripts/check_manifest.py --strict   # exit 1 on any drift

Exits 0 on success, 1 on drift (in --strict mode), 2 on parse failure.
"""

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EPUB_DIR = REPO_ROOT / "epub_working"

# Files that intentionally live in epub_working/ but are NOT manifest entries.
# (mimetype is EPUB-magic, container.xml is meta-information.)
NON_MANIFEST_FILES = {"mimetype", "content.opf", "META-INF/container.xml"}

# Heuristic media-type lookup for --fix.
MEDIA_TYPE = {
    ".html": "application/xhtml+xml",
    ".xhtml": "application/xhtml+xml",
    ".css": "text/css",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".ncx": "application/x-dtbncx+xml",
    ".otf": "application/vnd.ms-opentype",
    ".ttf": "application/x-font-ttf",
    ".woff": "application/font-woff",
    ".woff2": "font/woff2",
}


def err(msg: str, code: int = 2) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def parse_manifest(opf_text: str) -> dict[str, dict]:
    """Return {href: {id, media_type, properties}} for each manifest item."""
    items = {}
    item_re = re.compile(r"<item\b([^>]*?)/>", re.DOTALL)
    attr_re = re.compile(r'(\w[\w:-]*)="([^"]*)"')
    for m in item_re.finditer(opf_text):
        attrs = dict(attr_re.findall(m.group(1)))
        href = attrs.get("href")
        if href:
            items[href] = {
                "id": attrs.get("id", ""),
                "media_type": attrs.get("media-type", ""),
                "properties": attrs.get("properties", ""),
            }
    return items


def walk_disk(epub_dir: Path) -> set[str]:
    """Return the set of relative paths that should appear in the manifest."""
    on_disk = set()
    for path in epub_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = str(path.relative_to(epub_dir)).replace("\\", "/")
        if rel in NON_MANIFEST_FILES:
            continue
        if any(part.startswith("notes.backup_") for part in path.parts):
            continue
        if "__pycache__" in path.parts:
            continue
        on_disk.add(rel)
    return on_disk


def make_id(href: str, used: set[str]) -> str:
    """Generate a stable manifest id from an href, avoiding collisions."""
    base = re.sub(r"\W+", "_", Path(href).stem) or "item"
    candidate = base
    n = 1
    while candidate in used:
        n += 1
        candidate = f"{base}_{n}"
    used.add(candidate)
    return candidate


def fix_manifest(opf_path: Path, missing: list[str]) -> int:
    """Add manifest entries for missing files. Returns number added."""
    text = opf_path.read_text(encoding="utf-8")
    items = parse_manifest(text)
    used_ids = {item["id"] for item in items.values() if item["id"]}

    new_lines = []
    for href in sorted(missing):
        ext = Path(href).suffix.lower()
        media = MEDIA_TYPE.get(ext)
        if not media:
            print(f"  SKIP {href}: unknown extension {ext!r}, please add manually")
            continue
        item_id = make_id(href, used_ids)
        new_lines.append(f'    <item id="{item_id}" href="{href}" media-type="{media}"/>')

    if not new_lines:
        return 0

    # Insert before </manifest>. Find the closing tag and inject above it.
    insertion = "\n".join(new_lines) + "\n  "
    new_text, n = re.subn(r"(\s*</manifest>)", "\n" + insertion + r"\1", text, count=1)
    if n != 1:
        err("could not locate </manifest> tag")
    opf_path.write_text(new_text, encoding="utf-8")
    return len(new_lines)


def main() -> None:
    p = argparse.ArgumentParser(description="Verify content.opf manifest matches filesystem.")
    p.add_argument("--epub-dir", type=Path, default=EPUB_DIR)
    p.add_argument("--fix", action="store_true", help="auto-add missing files to manifest")
    p.add_argument("--strict", action="store_true", help="exit non-zero on any drift")
    args = p.parse_args()

    opf_path = args.epub_dir / "content.opf"
    if not opf_path.exists():
        err(f"no content.opf at {opf_path}")

    text = opf_path.read_text(encoding="utf-8")
    items = parse_manifest(text)
    if not items:
        err("could not parse any <item> entries from content.opf")

    on_disk = walk_disk(args.epub_dir)
    in_manifest = set(items.keys())

    only_in_manifest = sorted(in_manifest - on_disk)
    only_on_disk = sorted(on_disk - in_manifest)

    print(f"Manifest: {len(in_manifest)} items, Disk: {len(on_disk)} files")

    if not only_in_manifest and not only_on_disk:
        print("✓ manifest in sync with filesystem")
        sys.exit(0)

    if only_in_manifest:
        print(f"\n✗ {len(only_in_manifest)} BROKEN (in manifest but not on disk):")
        for href in only_in_manifest:
            print(f"    {href}")

    if only_on_disk:
        print(f"\n✗ {len(only_on_disk)} ORPHANED (on disk but not in manifest):")
        for href in only_on_disk:
            print(f"    {href}")

    if args.fix and only_on_disk:
        print(f"\n--fix: adding {len(only_on_disk)} entries to manifest…")
        n_added = fix_manifest(opf_path, only_on_disk)
        print(f"  added {n_added} <item> entries to {opf_path.name}")

    if args.strict and (only_in_manifest or only_on_disk):
        sys.exit(1)


if __name__ == "__main__":
    main()
