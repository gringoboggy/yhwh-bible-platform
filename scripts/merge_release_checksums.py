#!/usr/bin/env python3
"""Merge missing release assets into SHA256SUMS.txt.

Round-8 finding: assets can land on a GitHub release without a matching
checksum line. This script downloads only the gap, hashes them, merges into
the existing SHA256SUMS.txt, and optionally re-uploads (--upload).

Usage::

    py -3 scripts/merge_release_checksums.py --tag v0.1.0 --dry-run
    py -3 scripts/merge_release_checksums.py --tag v0.1.0 --upload
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts.gen_checksums import render, sha256_file  # noqa: E402
from scripts.gen_release_catalog import (  # noqa: E402
    DEFAULT_REPO,
    fetch_release_asset_names,
    fetch_release_sums,
    parse_sums,
)


def _gh(args: list[str]) -> None:
    subprocess.run(["gh", *args], check=True, stdin=subprocess.DEVNULL)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Merge missing GitHub release assets into SHA256SUMS.txt.")
    p.add_argument("--tag", required=True, help="release tag (e.g. v0.1.0)")
    p.add_argument("--repo", default=DEFAULT_REPO)
    p.add_argument("--upload", action="store_true", help="upload merged SHA256SUMS.txt to the release")
    p.add_argument("--dry-run", action="store_true", help="report gap only; do not download/hash/write")
    p.add_argument("-o", "--out", type=Path, help="write merged file here (default: temp dir only)")
    args = p.parse_args(argv)

    assets = fetch_release_asset_names(args.tag, args.repo)
    assets = [a for a in assets if a != "SHA256SUMS.txt"]
    existing = fetch_release_sums(args.tag, args.repo)
    missing = sorted(a for a in assets if a not in existing)

    print(f"release {args.tag}: {len(assets)} assets, {len(existing)} checksums, {len(missing)} missing")
    if missing:
        for name in missing[:10]:
            print(f"  missing: {name}")
        if len(missing) > 10:
            print(f"  ... and {len(missing) - 10} more")

    if not missing:
        print("nothing to merge")
        return 0

    if args.dry_run:
        return 0

    merged = dict(existing)
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        for name in missing:
            print(f"downloading {name}...")
            _gh(["release", "download", args.tag, "-p", name, "-D", str(td_path), "--repo", args.repo, "--clobber"])
            path = td_path / name
            if not path.is_file():
                print(f"error: download failed for {name}", file=sys.stderr)
                return 1
            merged[name] = sha256_file(path)

        rows = sorted(merged.items(), key=lambda kv: kv[0].lower())
        text = render([(digest, name) for name, digest in rows])
        upload_path = td_path / "SHA256SUMS.txt"
        upload_path.write_text(text, encoding="utf-8")
        if args.out:
            args.out.write_text(text, encoding="utf-8")
            print(f"wrote {args.out} ({len(rows)} entries)")
        print(f"merged {len(rows)} entries")

        if args.upload:
            print("uploading SHA256SUMS.txt...")
            _gh(["release", "upload", args.tag, str(upload_path), "--repo", args.repo, "--clobber"])
            print("upload complete")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
