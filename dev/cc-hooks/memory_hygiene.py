#!/usr/bin/env python3
"""Claude memory self-maintenance — audit · backup · propose-prune · archive.

A LOCAL, dependency-free tool that keeps Claude's out-of-repo auto-memory
(`~/.claude/projects/<proj>/memory/`) clean, accurate, and durable across
sessions. Built 2026-06-02 for the [[automate_claude_operating_doctrine]] ask
("a self-updating + self-pruning/auto-declutter memory system, secure with
securities in place").

DESIGN — security & safety first (the memory dir lives OUTSIDE the git repo, so
the 5-leg save does NOT back it up; a bad prune or disk loss is otherwise
unrecoverable):
  * `audit`         — READ-ONLY. Validates index<->file consistency, dead
                      [[wikilinks]], orphan files, and size/line budgets.
  * `backup`        — snapshots the whole memory dir to the external drives
                      (E:/F:, never C:), verified. The durability leg.
  * `propose-prune` — READ-ONLY. Lists archive/delete CANDIDATES (superseded
                      markers · old + unreferenced). Never mutates.
  * `archive <f>`   — REVERSIBLE: moves a memory into `_archive/` and drops its
                      MEMORY.md line. Never a hard delete. Refuses PROTECTED
                      memories and auto-backs-up first unless --no-backup.

NO external/API calls; honors the no-external-hooks stance. Pure text parsing
(never eval/exec a memory file). Operates only within the memory dir + the
whitelisted backup drives.

Usage:
  py -3 dev/cc-hooks/memory_hygiene.py audit [--json] [--quiet]
  py -3 dev/cc-hooks/memory_hygiene.py backup [--drives E F]
  py -3 dev/cc-hooks/memory_hygiene.py propose-prune
  py -3 dev/cc-hooks/memory_hygiene.py archive <file.md>
  (all accept --memory-dir <path>; default = the YHWH project memory dir)
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
import zipfile
from pathlib import Path

# --- configuration -----------------------------------------------------------


def _resolve_default_memory_dir() -> Path:
    """Resolve Claude's out-of-repo auto-memory dir per-platform — it lives at
    ``~/.claude/projects/<proj-slug>/memory`` and the slug differs per box, so a
    single hardcoded path can only ever work on one machine. Resolution order:
    explicit ``CLAUDE_MEMORY_DIR`` env override > known per-OS default > the
    Windows path. ADDITIVE: the Windows fallback is byte-identical to the
    original hardcoded literal, so the N95 lane is unaffected; only macOS (the
    2nd lane) and an env override are new. Callers can still pass --memory-dir."""
    env = os.environ.get("CLAUDE_MEMORY_DIR")
    if env:
        return Path(env)
    if sys.platform == "darwin":  # 2nd lane: the 2017 iMac (repo under /Volumes/MacHD2)
        return Path.home() / ".claude" / "projects" / "-Volumes-MacHD2-yhwh-bible-platform" / "memory"
    # Windows (primary N95 lane) + any other OS — UNCHANGED from the original hardcode.
    return Path(r"C:\Users\bogda\.claude\projects\C--Users-bogda-Documents-YHWH-v2-4-full\memory")


DEFAULT_MEMORY_DIR = _resolve_default_memory_dir()
INDEX_FILE = "MEMORY.md"
ARCHIVE_DIR = "_archive"
DEFAULT_BACKUP_DRIVES = ["E", "F"]
BACKUP_SUBPATH = Path("YHWH-v2.4-backups") / "memory"

# Budgets (advisory warnings, not hard failures).
MEMORY_INDEX_LINE_BUDGET = 85  # MEMORY.md one-line-per-memory index
MEMORY_FILE_BYTES_BUDGET = 6000  # a single memory should be one fact, not an essay

# PROTECTED: never proposed for prune / refused by `archive`. Load-bearing or
# identity memories whose loss would degrade collaboration or safety.
PROTECTED_STEMS = {
    "automate_claude_operating_doctrine",
    "project_deadline",  # the quality/cost-over-speed doctrine (filename kept)
    "reference_save",
    "reference_backup_drives",
    "reference_bootstrap",
    "reference_ssh_git_remotes",
    "feedback_no_external_hooks",
    "reference_deep_audit_tool",
    "feedback_audit_cadence",
    "feedback_verify_commit_backup_truth",
    "feedback_proper_clean_correct",
    "feedback_extensive_answers",
}
PROTECTED_PREFIXES = ("user_",)  # who-the-user-is memories

# Markers that hint a memory is spent (propose-prune heuristic only).
SUPERSEDED_MARKERS = ("SUPERSEDED", "OBSOLETE", "RETIRED", "DELETE THIS", "no longer relevant")

# Meta-tokens: memories that DISCUSS the memory format itself legitimately write
# [[name]] / [[their-name]] / [[wikilinks]] as placeholders, not real links.
IGNORED_LINK_TOKENS = {"wikilinks", "name", "theirname", "filename", "slug"}

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
INDEX_LINK_RE = re.compile(r"\]\(([^)]+\.md)\)")
NAME_RE = re.compile(r"^name:\s*(.+?)\s*$", re.MULTILINE)


# --- helpers -----------------------------------------------------------------


def _norm(s: str) -> str:
    """Lowercase, strip everything but [a-z0-9] — so feedback_save / save-is /
    'Save workflow' collapse to comparable tokens for fuzzy link matching."""
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _memory_files(memory_dir: Path) -> list[Path]:
    return sorted(p for p in memory_dir.glob("*.md") if p.name != INDEX_FILE and not p.name.startswith("_"))


def _frontmatter_name(text: str) -> str | None:
    # Only look inside a leading --- frontmatter block.
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    block = text[: end if end != -1 else len(text)]
    m = NAME_RE.search(block)
    return m.group(1).strip() if m else None


def _is_protected(stem: str) -> bool:
    return stem in PROTECTED_STEMS or stem.startswith(PROTECTED_PREFIXES)


def _index_lines(memory_dir: Path) -> str:
    idx = memory_dir / INDEX_FILE
    return idx.read_text(encoding="utf-8") if idx.is_file() else ""


# --- audit -------------------------------------------------------------------


def audit(memory_dir: Path) -> dict:
    """READ-ONLY structural + link + budget validation. Returns a report dict
    with a list of {severity, kind, file, message}."""
    issues: list[dict] = []
    files = _memory_files(memory_dir)
    stems = {p.stem for p in files}
    index_text = _index_lines(memory_dir)

    # Build the set of resolvable identifiers (filename stems + name slugs),
    # normalized, for fuzzy [[wikilink]] resolution.
    valid_ids: set[str] = set()
    for p in files:
        valid_ids.add(_norm(p.stem))
        nm = _frontmatter_name(p.read_text(encoding="utf-8"))
        if nm:
            valid_ids.add(_norm(nm))

    def _link_is_live(link: str) -> bool:
        n = _norm(link)
        if not n or n in IGNORED_LINK_TOKENS:
            return True  # empty/odd, or a meta-placeholder — don't nag
        # live iff the link EXACTLY matches a known identifier (filename stem or
        # name-slug), or is a SUFFIX of a filename stem (the common prefix-
        # omission case: [[save-is-local-commit]] -> feedback_save_is_local_commit).
        # NOT arbitrary substring — that silently passed genuinely-dead links.
        if n in valid_ids:
            return True
        return any(v.endswith(n) for v in valid_ids)

    # 1. index <-> files consistency
    linked = INDEX_LINK_RE.findall(index_text)
    linked_stems = {Path(t).stem for t in linked}
    for t in linked:
        target = Path(t).name
        if target == INDEX_FILE:
            continue
        # index links may be relative (../.. plan paths); only check memory-local ones
        if "/" not in t and "\\" not in t and Path(t).stem not in stems:
            issues.append(
                {
                    "severity": "warn",
                    "kind": "index_points_to_missing",
                    "file": INDEX_FILE,
                    "message": f"MEMORY.md links ({t}) but no such memory file exists",
                }
            )
    for stem in stems:
        if stem not in linked_stems:
            issues.append(
                {
                    "severity": "warn",
                    "kind": "orphan_no_index",
                    "file": f"{stem}.md",
                    "message": f"{stem}.md has no one-line entry in MEMORY.md",
                }
            )

    # 2. dead [[wikilinks]] in bodies
    for p in files:
        body = p.read_text(encoding="utf-8")
        seen: set[str] = set()
        for link in WIKILINK_RE.findall(body):
            link = link.strip()
            if link in seen:
                continue
            seen.add(link)
            if not _link_is_live(link):
                issues.append(
                    {
                        "severity": "warn",
                        "kind": "dead_wikilink",
                        "file": p.name,
                        "message": f"[[{link}]] resolves to no existing memory",
                    }
                )

    # 3. budgets (advisory)
    n_index = sum(1 for ln in index_text.splitlines() if ln.strip().startswith("- ["))
    if n_index > MEMORY_INDEX_LINE_BUDGET:
        issues.append(
            {
                "severity": "info",
                "kind": "index_budget",
                "file": INDEX_FILE,
                "message": f"MEMORY.md has {n_index} entries (budget {MEMORY_INDEX_LINE_BUDGET}) — consider consolidating/archiving",
            }
        )
    for p in files:
        size = p.stat().st_size
        if size > MEMORY_FILE_BYTES_BUDGET:
            issues.append(
                {
                    "severity": "info",
                    "kind": "file_budget",
                    "file": p.name,
                    "message": f"{p.name} is {size} bytes (budget {MEMORY_FILE_BYTES_BUDGET}) — a memory should be one fact",
                }
            )

    warn = sum(1 for i in issues if i["severity"] == "warn")
    info = sum(1 for i in issues if i["severity"] == "info")
    return {
        "memory_dir": str(memory_dir),
        "file_count": len(files),
        "index_entries": n_index,
        "issues": issues,
        "summary": {"warn": warn, "info": info, "clean": warn == 0},
    }


# --- backup ------------------------------------------------------------------


def write_memory_zip(memory_dir: Path, dest: Path) -> str | None:
    """Write a verified .zip snapshot of `memory_dir` to `dest`. Returns the
    name of the first corrupt entry if zip verification fails, else None.
    Testable seam used by `backup` (and the test-suite)."""
    files = sorted(memory_dir.rglob("*"))
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            if f.is_file():
                zf.write(f, f.relative_to(memory_dir.parent))
    with zipfile.ZipFile(dest) as zf:
        return zf.testzip()


def backup(memory_dir: Path, drives: list[str], now: _dt.datetime | None = None) -> dict:
    """Snapshot the whole memory dir into a verified .zip on each external
    drive. Skips (with a warning) any drive that isn't mounted. Never C:."""
    now = now or _dt.datetime.now()
    stamp = now.strftime("%Y-%m-%d-%H%M%S")
    name = f"claude-memory-{stamp}.zip"
    results: list[dict] = []

    for d in drives:
        d = d.rstrip(":\\/").upper()
        if d == "C":
            results.append({"drive": d, "ok": False, "message": "refused: never back up to C:"})
            continue
        root = Path(f"{d}:\\")
        if not root.exists():
            results.append({"drive": d, "ok": False, "message": f"{d}: not mounted — skipped"})
            continue
        dest_dir = root / BACKUP_SUBPATH
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / name
            bad = write_memory_zip(memory_dir, dest)
            if bad is not None:
                results.append({"drive": d, "ok": False, "message": f"zip verify failed on {bad}", "path": str(dest)})
            else:
                results.append({"drive": d, "ok": True, "path": str(dest), "bytes": dest.stat().st_size})
        except OSError as e:
            results.append({"drive": d, "ok": False, "message": f"{type(e).__name__}: {e}"})

    landed = [r for r in results if r.get("ok")]
    return {"name": name, "results": results, "landed": len(landed), "ok": len(landed) > 0}


# --- propose-prune (read-only) -----------------------------------------------


def propose_prune(memory_dir: Path, max_age_days: int = 30) -> dict:
    """READ-ONLY. Surface archive CANDIDATES: memories carrying a superseded
    marker, or old AND unreferenced by any other memory's [[wikilinks]] (and not
    PROTECTED). Never deletes — a human reviews + runs `archive`."""
    files = _memory_files(memory_dir)
    # which stems are referenced by some OTHER memory's wikilinks?
    referenced: set[str] = set()
    norm_to_stem = {}
    for p in files:
        norm_to_stem[_norm(p.stem)] = p.stem
        nm = _frontmatter_name(p.read_text(encoding="utf-8"))
        if nm:
            norm_to_stem.setdefault(_norm(nm), p.stem)
    for p in files:
        for link in WIKILINK_RE.findall(p.read_text(encoding="utf-8")):
            n = _norm(link.strip())
            if not n:
                continue
            for vid, stem in norm_to_stem.items():
                if (n == vid or vid.endswith(n)) and stem != p.stem:
                    referenced.add(stem)

    candidates: list[dict] = []
    for p in files:
        if _is_protected(p.stem):
            continue
        text = p.read_text(encoding="utf-8")
        reasons = []
        upper = text.upper()
        for mk in SUPERSEDED_MARKERS:
            if mk.upper() in upper:
                reasons.append(f"carries marker '{mk}'")
                break
        # unreferenced is a soft signal only (don't propose solely on age)
        if p.stem not in referenced:
            reasons.append("not referenced by any other memory")
        if reasons and any("marker" in r for r in reasons):
            candidates.append({"file": p.name, "reasons": reasons})
    return {"candidates": candidates, "note": "READ-ONLY — review then run `archive <file>` (reversible)"}


# --- archive (reversible mutation) -------------------------------------------


def archive(memory_dir: Path, filename: str, do_backup: bool = True) -> dict:
    """Move a memory into _archive/ and drop its MEMORY.md line. REVERSIBLE.
    Refuses PROTECTED memories. Backs up first unless do_backup=False."""
    target = memory_dir / filename
    if not target.is_file():
        return {"ok": False, "message": f"no such memory: {filename}"}
    if _is_protected(target.stem):
        return {"ok": False, "message": f"REFUSED: {target.stem} is PROTECTED"}

    if do_backup:
        b = backup(memory_dir, DEFAULT_BACKUP_DRIVES)
        if not b["ok"]:
            return {"ok": False, "message": "REFUSED: pre-archive backup did not land on any drive", "backup": b}

    arc = memory_dir / ARCHIVE_DIR
    arc.mkdir(exist_ok=True)
    dest = arc / filename
    target.rename(dest)

    # drop the MEMORY.md index line referencing this file (preserve the rest)
    idx = memory_dir / INDEX_FILE
    removed_line = None
    if idx.is_file():
        lines = idx.read_text(encoding="utf-8").splitlines(keepends=True)
        kept = []
        for ln in lines:
            if f"({filename})" in ln:
                removed_line = ln.strip()
                continue
            kept.append(ln)
        idx.write_text("".join(kept), encoding="utf-8")
    return {"ok": True, "archived_to": str(dest), "index_line_removed": removed_line}


# --- cli ---------------------------------------------------------------------


def _print_audit(report: dict, quiet: bool) -> None:
    s = report["summary"]
    if quiet and s["warn"] == 0:
        return  # hook use: stay silent unless a real (warn) issue exists
    head = f"[memory-hygiene] {report['file_count']} memories · {report['index_entries']} index entries · {s['warn']} warn · {s['info']} info"
    print(head)
    for i in report["issues"]:
        if quiet and i["severity"] == "info":
            continue
        print(f"  {i['severity'].upper():4} {i['kind']:24} {i['file']}: {i['message']}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Claude memory self-maintenance.")
    ap.add_argument("--memory-dir", type=Path, default=DEFAULT_MEMORY_DIR)
    sub = ap.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser("audit", help="read-only structural/link/budget validation")
    pa.add_argument("--json", action="store_true")
    pa.add_argument("--quiet", action="store_true", help="only print on warnings (for hook use)")

    pb = sub.add_parser("backup", help="snapshot the memory dir to external drives")
    pb.add_argument("--drives", nargs="+", default=DEFAULT_BACKUP_DRIVES)

    sub.add_parser("propose-prune", help="read-only list of archive candidates")

    par = sub.add_parser("archive", help="reversibly move a memory to _archive/ + drop its index line")
    par.add_argument("file")
    par.add_argument("--no-backup", action="store_true")

    args = ap.parse_args(argv)
    md = args.memory_dir
    if not md.is_dir():
        print(f"memory dir not found: {md}", file=sys.stderr)
        return 2

    if args.cmd == "audit":
        rep = audit(md)
        if args.json:
            print(json.dumps(rep, indent=2))
        else:
            _print_audit(rep, args.quiet)
        return 0 if rep["summary"]["warn"] == 0 else 1
    if args.cmd == "backup":
        rep = backup(md, args.drives)
        for r in rep["results"]:
            tag = "OK  " if r.get("ok") else "MISS"
            print(f"  {tag} {r.get('drive', '?')}: {r.get('path') or r.get('message')}")
        print(f"[memory-backup] {rep['name']} → {rep['landed']} drive(s)")
        return 0 if rep["ok"] else 1
    if args.cmd == "propose-prune":
        rep = propose_prune(md)
        if not rep["candidates"]:
            print("[propose-prune] no archive candidates — memory is lean.")
        else:
            print(f"[propose-prune] {len(rep['candidates'])} candidate(s) — {rep['note']}")
            for c in rep["candidates"]:
                print(f"  {c['file']}: {'; '.join(c['reasons'])}")
        return 0
    if args.cmd == "archive":
        rep = archive(md, args.file, do_backup=not args.no_backup)
        print(json.dumps(rep, indent=2))
        return 0 if rep["ok"] else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
