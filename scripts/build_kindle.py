"""Build the Send-to-Kindle-safe EPUB for an edition (the proven june10 recipe).

A STANDARD (everywhere) build via the canonical CLI + the deterministic
post-process in ``scripts.core.kindle_post`` (strip hidden content, single
``dc:language``, OCF re-zip). This is the *productized* form of what the Mac
proved by hand on 2026-06-14 (user-confirmed delivered via Send-to-Kindle); it
does NOT use the dormant, Previewer-oracle-tuned ``--target-reader kindle`` variant.

    py -3 scripts/build_kindle.py catholic-study --version 0.1.0 \
        --output-dir build/kindle

The 9 KJV editions, the everywhere build, and the dormant kindle target are
untouched — this is a pure post-pass over a standard artifact.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))


def build_kindle(
    edition_id: str, version: str, out_dir: Path, *, force: bool = True, m4b: bool = False
) -> tuple[Path, dict]:
    """Build ``edition_id`` standard, then post-process to a kindle-safe EPUB.

    Returns ``(artifact_path, post_process_stats)``. The intermediate standard
    base is built under a private subdir and removed afterwards."""
    out_dir = Path(out_dir)
    base_dir = out_dir / "_kindle_base"
    base_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(REPO / "scripts" / "build_edition.py"),
        edition_id,
        "--version",
        version,
        "--output-dir",
        str(base_dir),
    ]
    if force:
        cmd.append("--force")
    print(f"  $ {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True, stdin=subprocess.DEVNULL, cwd=str(REPO))

    bases = sorted(base_dir.glob("*.epub"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not bases:
        raise FileNotFoundError(f"standard build produced no .epub in {base_dir}")
    base = bases[0]

    from scripts.core.kindle_post import make_kindle_m4b, make_kindle_safe, verify_kindle_m4b, verify_kindle_safe

    suffix = "-kindle-m4b" if m4b else "-kindle"
    dst = out_dir / f"{base.stem}{suffix}.epub"
    if m4b:
        stats = make_kindle_m4b(base, dst)
        fails = verify_kindle_m4b(dst)
    else:
        stats = make_kindle_safe(base, dst)
        fails = verify_kindle_safe(dst)
    if fails:
        raise ValueError(f"kindle verification failed: {fails}")
    shutil.rmtree(base_dir, ignore_errors=True)
    return dst, stats


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build the Send-to-Kindle-safe EPUB for an edition.")
    p.add_argument("edition", help="edition id (e.g. catholic-study)")
    p.add_argument("--version", default="0.0.0", help="release version (bare or v-prefixed)")
    p.add_argument("--output-dir", type=Path, default=REPO / "build" / "kindle")
    p.add_argument(
        "--m4b",
        action="store_true",
        help="apply M4b fork (suppress study badges + chapter-tail study blocks)",
    )
    args = p.parse_args(argv)

    version = args.version.removeprefix("v")
    artifact, stats = build_kindle(args.edition, version, args.output_dir, m4b=args.m4b)
    print(f"STAGED: {artifact}  ({artifact.stat().st_size:,} bytes)")
    print(f"  post-process: {stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
