#!/usr/bin/env python3
"""Round-14 WS1 158-verse re-split — all-edition BUILD byte-proof (Mac deterministic task).

WIN proved the BASE diff (epub_working/index_split_*.html) is 38/38 pure relocation. This proves
what happens at the BUILT-EPUB level across the 9 KJV byte-stable cells (which WIN cannot build on its
box until A2's empirical confirm).

The re-split is a USER-RATIFIED base change — it is NOT build-output-neutral: filling the 158 empty
verse anchors with their correct WEB text (a) RELOCATES WEB body across anchor boundaries and
(b) REMOVES the KJV empty-anchor "fill" the build injects into a body-less anchor (the `¶ And God
spake...` KJV-bleed = the WS1 "weird symbol" defect). So a non-zero char delta is EXPECTED and correct;
the real question is whether the change is CONFINED and EXPLICABLE. The proof verdict (per cell):

  INV-1 structural   : no inner member added or dropped (only_pre / only_post both empty).
  INV-2 confinement  : every differing member is EITHER a descendant of one of the 38 re-split base
                       files (content change = relocation + KJV-fill removal) OR a TOC/xref file whose
                       ONLY change is cross-file href piece-number retargeting (href-normalized
                       pre == post) — i.e. `rewrite_links` correctly tracking content that shifted
                       across a ~0.4 MB sub-piece boundary.
  INV-3 link-integrity: 0 dead cross-file links in the POST build (every `index_split_*.html#frag`
                       resolves to an id in the named piece).
  INV-4 feasibility  : both builds succeed (rc 0/0).

PASS = all four. A char-multiset delta is reported as INFO (expected for a ratified re-split).

Run from the MAIN repo with the main .venv. Builds shell out to each worktree's own build_edition.py
so each side uses its own epub_working/ base.
    .venv/bin/python dev/audit/round14_ws1_byteproof.py            # full: 18 builds (~90 min)
    .venv/bin/python dev/audit/round14_ws1_byteproof.py --reuse    # re-analyze existing builds in OUT/
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
RESPLIT_COMMIT = "6b690361"
VENV_PY = MAIN / ".venv/bin/python"
OUT = Path("/Volumes/MacHD2/yhwh-byteproof-out")  # build outputs (MacHD2 has room)
REPORT = MAIN / "dev/audit/round14-ws1-byteproof.md"
JSON_OUT = MAIN / "dev/audit/round14-ws1-byteproof.json"
REUSE = "--reuse" in sys.argv

EDITIONS = ["catholic-study", "evangelical-reformed", "eastern-orthodox"]
TARGETS = ["everywhere", "tablet", "kindle"]
# everywhere-first ordering so the cleanest signal lands first
CELLS = [(ed, t) for t in TARGETS for ed in EDITIONS]

_URN_RE = re.compile(r"urn:yhwh:edition:[^<\"']+")
_MODIFIED_RE = re.compile(r"<meta[^>]*dcterms:modified[^>]*>[^<]*</meta>")
_DATE_RE = re.compile(r"<dc:date>[^<]*</dc:date>")
_RIGHTS_YEAR_RE = re.compile(r"(Copyright . )\d{4}")
_TEXT_EXT = (".opf", ".xhtml", ".html", ".ncx", ".css", ".svg", ".xml")
# collapse a cross-file href's TARGET piece-number so 033_02.html#frag == 033_01.html#frag
_HREF_PIECE_RE = re.compile(r"index_split_\d+(?:_\d+)?\.html#")
_HREF_LINK_RE = re.compile(r"(index_split_[0-9_]+\.html)#([^\"'> ]+)")
_ID_RE = re.compile(r'id="([^"]+)"')


def _resplit_base_stems() -> set[str]:
    """The base index_split_NNN stems the re-split commit touched (the 38)."""
    r = subprocess.run(
        [
            "git",
            "-C",
            str(MAIN),
            "show",
            RESPLIT_COMMIT,
            "--stat",
            "--format=",
            "--",
            "epub_working/index_split_*.html",
        ],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    return set(re.findall(r"index_split_\d+", r.stdout))


def _base_stem(member: str) -> str:
    """index_split_033_02.html / index_split_033.html -> index_split_033."""
    m = re.match(r"index_split_(\d+)", member.split("/")[-1])
    return f"index_split_{m.group(1)}" if m else ""


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
    existing = sorted(out_dir.glob("*.epub"))
    if REUSE and existing:
        return existing[0], 0, ""
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


def _href_norm(text: str) -> str:
    """Collapse cross-file href target piece-numbers so only the fragment distinguishes a link."""
    return _HREF_PIECE_RE.sub("index_split_PIECE.html#", text)


def _dead_links(files: dict[str, bytes]) -> tuple[int, int]:
    """(dead, total) cross-file index_split_*.html#frag links that fail to resolve in POST."""
    id_index: dict[str, set[str]] = {}
    for n, d in files.items():
        if n.endswith((".html", ".xhtml")):
            id_index[n.split("/")[-1]] = set(_ID_RE.findall(d.decode("utf-8", "replace")))
    dead = total = 0
    for n, d in files.items():
        if not n.endswith((".html", ".xhtml")):
            continue
        for tgt, frag in _HREF_LINK_RE.findall(d.decode("utf-8", "replace")):
            total += 1
            if frag not in id_index.get(tgt, set()):
                dead += 1
    return dead, total


def _analyze(pre_epub: Path, post_epub: Path, resplit: set[str]) -> dict:
    pf = _load_normalized(pre_epub)
    qf = _load_normalized(post_epub)
    pre_n, post_n = set(pf), set(qf)
    common = pre_n & post_n
    differ = sorted(n for n in common if pf[n] != qf[n])
    only_pre, only_post = sorted(pre_n - post_n), sorted(post_n - pre_n)

    # classify each differing member
    resplit_files, linkonly_files, unexplained = [], [], []
    for n in differ:
        if _base_stem(n) in resplit:
            resplit_files.append(n)
        elif _href_norm(pf[n].decode("utf-8", "replace")) == _href_norm(qf[n].decode("utf-8", "replace")):
            linkonly_files.append(n)  # only change = cross-file href piece-number retarget
        else:
            unexplained.append(n)

    dead, total_links = _dead_links(qf)
    mp, mq = _multiset(pf), _multiset(qf)
    eq = mp == mq
    delta = ((mq - mp) + (mp - mq)) if not eq else collections.Counter()

    inv1 = (not only_pre) and (not only_post)
    inv2 = not unexplained
    inv3 = dead == 0
    return {
        "verdict_pass": inv1 and inv2 and inv3,
        "INV1_no_add_drop": inv1,
        "INV2_confined": inv2,
        "INV3_no_dead_links": inv3,
        "multiset_equal": eq,
        "char_delta_total": sum(delta.values()),
        "n_members_pre": len(pre_n),
        "n_members_post": len(post_n),
        "n_differ": len(differ),
        "n_resplit_files": len(resplit_files),
        "n_linkonly_files": len(linkonly_files),
        "unexplained_files": unexplained,
        "only_pre_files": only_pre,
        "only_post_files": only_post,
        "dead_links": dead,
        "total_cross_file_links": total_links,
        "differ_files": differ,
    }


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def main() -> int:
    for t in (PRE, POST, VENV_PY):
        if not t.exists():
            print(f"MISSING: {t}", file=sys.stderr)
            return 2
    resplit = _resplit_base_stems()
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    overall_ok = True
    REPORT.write_text(
        "# Round-14 WS1 158-verse re-split — all-edition BUILD byte-proof\n\n"
        f"Run {_now()} · PRE=5039cda0 (pre re-split) · POST={RESPLIT_COMMIT} (re-split applied) · "
        f"9 KJV byte-stable cells · {len(resplit)} re-split base files.\n\n"
        "The re-split is a USER-RATIFIED base change, NOT build-output-neutral — it fills 158 empty "
        "verse anchors, removing the build's KJV empty-anchor fill (`¶ And God spake…` = the WS1 "
        "weird-symbol/KJV-bleed) and restoring correct WEB body. So a char delta is EXPECTED. The "
        "verdict checks the change is CONFINED + EXPLICABLE:\n\n"
        "- **INV-1** no inner member added/dropped · **INV-2** every differing member is a re-split "
        "descendant OR a link-only (href piece-retarget) TOC/xref file · **INV-3** 0 dead cross-file "
        "links in POST · **INV-4** both builds rc 0.\n\n"
        "| # | edition | target | verdict | INV1 | INV2 | INV3 | dead/total links "
        "| differ (resplit/linkonly/?) | char Δ | rc |\n"
        "|---|---------|--------|---------|------|------|------|------------------"
        "|------------------------------|--------|----|\n",
        encoding="utf-8",
    )
    for i, (ed, target) in enumerate(CELLS, 1):
        pre_epub, rc_pre, tail_pre = _build(PRE, ed, target, OUT / f"pre/{ed}_{target}")
        post_epub, rc_post, tail_post = _build(POST, ed, target, OUT / f"post/{ed}_{target}")
        row = {"n": i, "edition": ed, "target": target, "rc_pre": rc_pre, "rc_post": rc_post}
        if rc_pre or rc_post or not pre_epub or not post_epub:
            overall_ok = False
            row.update({"verdict_pass": False, "status": "BUILD_FAIL", "tail_pre": tail_pre, "tail_post": tail_post})
            line = f"| {i} | {ed} | {target} | ❌ BUILD FAIL | — | — | — | — | — | — | {rc_pre}/{rc_post} |\n"
        else:
            a = _analyze(pre_epub, post_epub, resplit)
            row.update(a)
            inv4 = rc_pre == 0 and rc_post == 0
            ok = a["verdict_pass"] and inv4
            overall_ok = overall_ok and ok
            mark = "✅ PASS" if ok else "❌ FAIL"
            line = (
                f"| {i} | {ed} | {target} | {mark} | {'✓' if a['INV1_no_add_drop'] else '✗'} "
                f"| {'✓' if a['INV2_confined'] else '✗'} | {'✓' if a['INV3_no_dead_links'] else '✗'} "
                f"| {a['dead_links']}/{a['total_cross_file_links']} "
                f"| {a['n_differ']} ({a['n_resplit_files']}/{a['n_linkonly_files']}/{len(a['unexplained_files'])}) "
                f"| {a['char_delta_total']} | {rc_pre}/{rc_post} |\n"
            )
        results.append(row)
        with REPORT.open("a", encoding="utf-8") as f:
            f.write(line)
        JSON_OUT.write_text(json.dumps({"cells": results}, indent=1), encoding="utf-8")
        print(f"[{i}/9] {ed} {target}: verdict_pass={row.get('verdict_pass')}")

    with REPORT.open("a", encoding="utf-8") as f:
        f.write("\n## Verdict\n\n")
        if overall_ok:
            f.write(
                "**PASS** — across all 9 KJV byte-stable cells the 158-verse re-split's built-EPUB delta "
                "is fully CONFINED + EXPLICABLE: no member added/dropped (INV-1), every differing member "
                "is a re-split-file descendant (WEB relocation + KJV empty-anchor-fill removal) or a "
                "link-only TOC/xref retarget (INV-2), and 0 dead cross-file links remain (INV-3); both "
                "builds succeed (INV-4). The 9 cells get a NEW byte-baseline (ratified) — G1's golden must "
                "be stamped from POST.\n"
            )
        else:
            f.write(
                "**FAIL** — at least one cell breaks INV-1/2/3/4 (an added/dropped member, an unexplained "
                "differing file, a dead link, or a build failure). See `unexplained_files` in the JSON.\n"
            )
        f.write(f"\nFinished {_now()}.\n")
        f.write("\n## Per-cell differing files (diagnostic)\n\n")
        for r in results:
            if "differ_files" not in r:
                continue
            extra = f" · ⚠ unexplained: {r['unexplained_files']}" if r.get("unexplained_files") else ""
            addrop = (
                f" · +{len(r['only_post_files'])} only-post/+{len(r['only_pre_files'])} only-pre"
                if (r["only_post_files"] or r["only_pre_files"])
                else ""
            )
            f.write(
                f"- **{r['edition']} {r['target']}** — {r['n_differ']} differ "
                f"({r['n_resplit_files']} re-split, {r['n_linkonly_files']} link-only){addrop}{extra}\n"
            )
    print(f"\nOVERALL: {'PASS' if overall_ok else 'FAIL'} — report at {REPORT}")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
