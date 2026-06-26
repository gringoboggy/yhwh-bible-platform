#!/usr/bin/env python3
"""Round-14 WS1 158-verse re-split — all-edition BUILD byte-proof (Mac deterministic task).

WIN proved the BASE diff (epub_working/index_split_*.html) is 38/38 pure relocation. This proves
the same holds at the BUILT-EPUB level across the 9 KJV byte-stable cells (the thing WIN cannot build
on its box until A2's empirical confirm): building from the re-split base produces output that differs
from the pre-re-split base ONLY by relocation — no character added, removed, or altered.

Method: build each cell from the PRE tree (5039cda0, pre re-split) and the POST tree (6b690361,
re-split applied) — both off the main .git via `git worktree`. Compare two ways:
  (1) STRONG: the normalized whole-epub character MULTISET (Counter over every text member, OPF
      volatile fields neutralized exactly like tests/test_byte_stability_gate._content_digest) must be
      IDENTICAL pre vs post. Equal => zero chars added/dropped/changed => pure relocation.
  (2) DIAGNOSTIC: the per-member normalized diff — which inner files changed (expected: only the
      scripture spine pieces derived from the 38 re-split base files; never OPF/nav/ncx/css/fonts).

Run from the MAIN repo with the main .venv: builds shell out to each worktree's own build_edition.py
so each side uses its own epub_working/ base.
    .venv/bin/python dev/audit/round14_ws1_byteproof.py
"""

from __future__ import annotations

import collections
import json
import os
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

MAIN = Path("/Volumes/MacHD2/yhwh-bible-platform")
PRE = Path("/Volumes/MacHD2/yhwh-wt-pre")  # 5039cda0 — pre re-split
POST = Path("/Volumes/MacHD2/yhwh-wt-post")  # 6b690361 — re-split applied
VENV_PY = MAIN / ".venv/bin/python"
OUT = Path("/Volumes/MacHD2/yhwh-byteproof-out")  # build outputs (MacHD2 has room)
REPORT = MAIN / "dev/audit/round14-ws1-byteproof.md"
JSON_OUT = MAIN / "dev/audit/round14-ws1-byteproof.json"

EDITIONS = ["catholic-study", "evangelical-reformed", "eastern-orthodox"]
TARGETS = ["everywhere", "tablet", "kindle"]
# everywhere-first ordering so the cleanest signal lands first
CELLS = [(ed, t) for t in TARGETS for ed in EDITIONS]

_URN_RE = re.compile(r"urn:yhwh:edition:[^<\"']+")
_MODIFIED_RE = re.compile(r"<meta[^>]*dcterms:modified[^>]*>[^<]*</meta>")
_DATE_RE = re.compile(r"<dc:date>[^<]*</dc:date>")
_RIGHTS_YEAR_RE = re.compile(r"(Copyright . )\d{4}")
_TEXT_EXT = (".opf", ".xhtml", ".html", ".ncx", ".css", ".svg", ".xml")


def _normalize(name: str, data: bytes) -> bytes:
    if name.endswith(".opf"):
        t = data.decode("utf-8", "replace")
        t = _URN_RE.sub("urn:yhwh:edition:NORMALIZED", t)
        t = _MODIFIED_RE.sub("", t)
        t = _DATE_RE.sub("<dc:date>NORMALIZED</dc:date>", t)
        t = _RIGHTS_YEAR_RE.sub(r"\g<1>YYYY", t)
        data = t.encode("utf-8")
    return data


def _build(tree: Path, ed: str, target: str, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONPATH": str(tree)}
    cmd = [
        str(VENV_PY),
        "scripts/build_edition.py",
        ed,
        "--target-reader",
        target,
        "--version",
        "0.1.0",
        "--output-dir",
        str(out_dir),
        "--force",
    ]
    r = subprocess.run(
        cmd,
        cwd=str(tree),
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    epubs = sorted(out_dir.glob("*.epub"))
    epub = epubs[0] if epubs else None
    tail = "" if r.returncode == 0 else (r.stdout + r.stderr)[-800:]
    return epub, r.returncode, tail


def _load_normalized(epub: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    with zipfile.ZipFile(epub) as z:
        for n in sorted(z.namelist()):
            files[n] = _normalize(n, z.read(n))
    return files


def _multiset(files: dict[str, bytes]) -> collections.Counter:
    c: collections.Counter = collections.Counter()
    for n, d in files.items():
        if n.endswith(_TEXT_EXT):
            c.update(d.decode("utf-8", "replace"))
    return c


def _analyze(pre_epub: Path, post_epub: Path) -> dict:
    pf = _load_normalized(pre_epub)
    qf = _load_normalized(post_epub)
    pre_n, post_n = set(pf), set(qf)
    common = pre_n & post_n
    differ = sorted(n for n in common if pf[n] != qf[n])
    mp, mq = _multiset(pf), _multiset(qf)
    eq = mp == mq
    delta = ((mq - mp) + (mp - mq)) if not eq else collections.Counter()
    return {
        "multiset_equal": eq,
        "char_delta_total": sum(delta.values()),
        "char_delta_sample": dict(list(delta.items())[:20]),
        "only_pre_files": sorted(pre_n - post_n),
        "only_post_files": sorted(post_n - pre_n),
        "n_members_pre": len(pre_n),
        "n_members_post": len(post_n),
        "differ_files": differ,
        "n_differ": len(differ),
    }


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def main() -> int:
    for t in (PRE, POST, VENV_PY):
        if not t.exists():
            print(f"MISSING: {t}", file=sys.stderr)
            return 2
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    overall_ok = True
    REPORT.write_text(
        f"# Round-14 WS1 158-verse re-split — all-edition BUILD byte-proof\n\n"
        f"Started {_now()} · PRE=5039cda0 (pre re-split) · POST=6b690361 (re-split applied) · "
        f"9 KJV byte-stable cells.\n\n"
        f"**Proof:** normalized whole-epub char MULTISET identical pre/post = pure relocation "
        f"(no char added/dropped/altered); per-member diff localizes the change to scripture spine "
        f"pieces only.\n\n"
        f"| # | edition | target | multiset== | char Δ | members pre/post | files differ | rc pre/post |\n"
        f"|---|---------|--------|-----------|-------|------------------|--------------|-------------|\n",
        encoding="utf-8",
    )
    for i, (ed, target) in enumerate(CELLS, 1):
        pre_epub, rc_pre, tail_pre = _build(PRE, ed, target, OUT / f"pre/{ed}_{target}")
        post_epub, rc_post, tail_post = _build(POST, ed, target, OUT / f"post/{ed}_{target}")
        row = {"n": i, "edition": ed, "target": target, "rc_pre": rc_pre, "rc_post": rc_post}
        if rc_pre or rc_post or not pre_epub or not post_epub:
            overall_ok = False
            row.update({"status": "BUILD_FAIL", "tail_pre": tail_pre, "tail_post": tail_post})
            line = f"| {i} | {ed} | {target} | — | — | — | BUILD FAIL | {rc_pre}/{rc_post} |\n"
        else:
            a = _analyze(pre_epub, post_epub)
            row.update(a)
            ok = a["multiset_equal"]
            overall_ok = overall_ok and ok
            mark = "✅" if ok else "❌"
            line = (
                f"| {i} | {ed} | {target} | {mark} {a['multiset_equal']} | {a['char_delta_total']} "
                f"| {a['n_members_pre']}/{a['n_members_post']} | {a['n_differ']} | {rc_pre}/{rc_post} |\n"
            )
        results.append(row)
        with REPORT.open("a", encoding="utf-8") as f:
            f.write(line)
        JSON_OUT.write_text(json.dumps({"cells": results}, indent=1), encoding="utf-8")
        print(f"[{i}/9] {ed} {target}: {row.get('status', 'multiset_equal=' + str(row.get('multiset_equal')))}")

    with REPORT.open("a", encoding="utf-8") as f:
        f.write("\n## Verdict\n\n")
        f.write(
            f"**{'PASS' if overall_ok else 'FAIL'}** — "
            + (
                "all 9 byte-stable cells: char multiset identical pre/post = the re-split moved "
                "boundaries only, zero content added/dropped/altered at the built-EPUB level.\n"
                if overall_ok
                else "at least one cell shows a char-multiset delta or build failure — see the rows above "
                "and the JSON for detail.\n"
            )
        )
        f.write(f"\nFinished {_now()}.\n")
        # per-cell differing-file lists (diagnostic)
        f.write("\n## Differing inner files per cell (diagnostic — expect scripture spine pieces only)\n\n")
        for r in results:
            if "differ_files" in r:
                f.write(
                    f"- **{r['edition']} {r['target']}** ({r['n_differ']} files"
                    + (
                        f", +{len(r['only_post_files'])} only-post, +{len(r['only_pre_files'])} only-pre"
                        if (r["only_post_files"] or r["only_pre_files"])
                        else ""
                    )
                    + "): "
                    + (", ".join(r["differ_files"][:30]) + (" …" if r["n_differ"] > 30 else "") or "(none)")
                    + "\n"
                )
    print(f"\nOVERALL: {'PASS' if overall_ok else 'FAIL'} — report at {REPORT}")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
