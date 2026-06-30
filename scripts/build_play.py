"""Build the Play Books EPUB for an edition (device-QA round-2 A2).

A STANDARD (everywhere) build via the canonical CLI + the deterministic
post-process in ``scripts.core.play_post``: the Kindle-M4b backmatter relocation
that turns every hidden note and translation popup into a reachable ENDNOTE,
WITHOUT the Kindle-only display-strip / single-``dc:language`` collapse / Kindle
CSS (Play renders standard EPUB3). Play's location estimator counts the
per-chapter hidden ``notes-section`` husks as ~85 phantom pages each, so relocating
them to back-matter both removes the phantom pages and makes the notes reachable.

This is the single-artifact device-staging counterpart to ``build_kindle.py``
(the matrix builds the catalog Play column via ``build_format_matrix``'s
``play_safe`` post-process; this CLI stages ONE artifact for the user's phone QA).

    py -3 scripts/build_play.py ethiopian-tewahedo --version 1.0.0 \
        --output-dir build/play

The 9 KJV editions, the everywhere build, and the Kindle target are untouched —
this is a pure post-pass over a standard artifact.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))


def build_play(edition_id: str, version: str, out_dir: Path, *, force: bool = True) -> tuple[Path, dict]:
    """Build ``edition_id`` standard, then post-process to a Play-safe endnote EPUB.

    Returns ``(artifact_path, post_process_stats)``. The intermediate standard
    base is built under a private subdir and removed afterwards."""
    out_dir = Path(out_dir)
    base_dir = out_dir / "_play_base"
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

    from scripts.core.play_post import make_play_safe, verify_play_safe

    dst = out_dir / f"{base.stem}-play.epub"
    stats = make_play_safe(base, dst)
    fails = verify_play_safe(dst)
    if fails:
        raise ValueError(f"play verification failed: {fails}")
    shutil.rmtree(base_dir, ignore_errors=True)
    return dst, stats


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build the Play-Books endnote EPUB for an edition.")
    p.add_argument("edition", help="edition id (e.g. ethiopian-tewahedo)")
    p.add_argument("--version", default="0.0.0", help="release version (bare or v-prefixed)")
    p.add_argument("--output-dir", type=Path, default=REPO / "build" / "play")
    args = p.parse_args(argv)

    version = args.version.removeprefix("v")
    artifact, stats = build_play(args.edition, version, args.output_dir)
    print(f"STAGED: {artifact}  ({artifact.stat().st_size:,} bytes)")
    print(f"  post-process: {stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
