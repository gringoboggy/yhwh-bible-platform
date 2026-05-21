#!/usr/bin/env python3
"""Repository-structure tracer + anti-rot check for ``dev/REPO_MAP.md``.

Read-only, re-runnable (mirrors ``dev/trace_matrix.py``'s posture). Walks the
repo, prints the current top-level inventory (file counts + extension mix), and
**flags any non-hidden top-level directory that is NOT documented in
``dev/REPO_MAP.md``** — so the map cannot silently rot as the tree grows. This is
the "find anything" guarantee: every folder is either in the map or surfaced here.

Hidden dirs (``.git``, ``.claude``, ``.sonar`` …) and build/cache scaffolding are
tooling, not project content, and are intentionally excluded.

Usage:
    py dev/trace_repo.py            # human inventory + undocumented-dir check
    py dev/trace_repo.py --full     # also second-level subdir counts
    py dev/trace_repo.py --json     # machine-readable inventory (no DB needed)
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REPO_MAP = REPO / "dev" / "REPO_MAP.md"
SKIP = {
    ".git",
    "__pycache__",
    "node_modules",
    ".backups",
    ".pytest_cache",
    ".venv",
    "venv",
    ".ruff_cache",
    ".mypy_cache",
    ".sonar",
    ".scannerwork",
}


def _walk_counts(d: Path) -> tuple[int, Counter]:
    nf = 0
    exts: Counter = Counter()
    for dp, dns, fns in os.walk(d):
        dns[:] = [x for x in dns if x not in SKIP]
        nf += len(fns)
        for f in fns:
            exts[Path(f).suffix or "(noext)"] += 1
    return nf, exts


def top_level_dirs() -> list[Path]:
    """Non-hidden, non-tooling top-level directories — the ones the map must cover."""
    return sorted(p for p in REPO.iterdir() if p.is_dir() and not p.name.startswith(".") and p.name not in SKIP)


def inventory() -> list[dict]:
    text = REPO_MAP.read_text(encoding="utf-8") if REPO_MAP.is_file() else ""
    rows = []
    for d in top_level_dirs():
        nf, exts = _walk_counts(d)
        rows.append(
            {
                "dir": d.name,
                "files": nf,
                "ext": dict(exts.most_common()),
                "documented": (d.name + "/") in text,
            }
        )
    return rows


def main() -> int:
    rows = inventory()
    if "--json" in sys.argv[1:]:
        print(json.dumps(rows, indent=2))
        return 0
    full = "--full" in sys.argv[1:]
    print("Top-level directories (vs dev/REPO_MAP.md):")
    for r in rows:
        ext_str = " ".join(f"{e}×{c}" for e, c in list(r["ext"].items())[:6])
        flag = "" if r["documented"] else "   <== NOT in REPO_MAP.md"
        print(f"  {r['dir']:30} files={r['files']:<6} {ext_str}{flag}")
        if full:
            for sub in sorted(p for p in (REPO / r["dir"]).iterdir() if p.is_dir() and p.name not in SKIP):
                snf, _ = _walk_counts(sub)
                print(f"      {sub.name:26} files={snf}")
    undoc = [r["dir"] for r in rows if not r["documented"]]
    print(f"\ntop-level dirs: {len(rows)}   undocumented: {len(undoc)}")
    if undoc:
        print("UNDOCUMENTED — add to dev/REPO_MAP.md:", ", ".join(undoc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
