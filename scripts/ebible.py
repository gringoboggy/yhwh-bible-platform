#!/usr/bin/env python3
"""
ebible — unified CLI for the YHWH Ya' Way platform.

Single entry point that wraps the 13 underlying scripts with named
workflows, a status dashboard, a "doctor" next-action advisor, a watch
mode, and a REPL pre-loaded with project helpers.

Usage:
    ebible status                          # health dashboard
    ebible doctor                          # what should I do next?
    ebible add gen 3 15 --kind comm-rabbinic --anchor "serpent"
    ebible inject [--book gen]             # source → master HTML
    ebible build [edition_id]              # inject + manifest + editions
    ebible ship [--epubcheck]              # full integrity gate
    ebible audit [--require-tools]         # code-quality CI gate (vulture/mypy/pip-audit/caches)
    ebible test                            # run pytest
    ebible repl                            # python -i with helpers loaded
    ebible watch                           # auto-rebuild on note changes
    ebible help [cmd]                      # show help with examples

Pass-through subcommands (exec the underlying script with remaining args):
    quality / search / diff / bulk-edit / dashboard / manifest /
    epubcheck / cleanup / fix-xrefs / verify / taxonomy
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
PYTHON = sys.executable

# round-7 O2: the literal "/tmp" resolved to <drive>:\tmp on Windows — builds
# landed in a surprising C:\tmp, `status` missed them, and `repl` crashed on a
# fresh box. One portable temp root for all three call sites.
TMP = Path(tempfile.gettempdir())

from scripts.core.ui import GREEN, RED, YELLOW, DIM, BOLD, RESET, BLUE  # noqa: E402


# ============================================================
# helpers
# ============================================================


def run_script(name: str, *extra_args: str, capture: bool = False) -> subprocess.CompletedProcess:
    """Run a scripts/*.py with extra args."""
    cmd = [PYTHON, str(REPO / "scripts" / name), *extra_args]
    if capture:
        return subprocess.run(cmd, capture_output=True, text=True, cwd=REPO, stdin=subprocess.DEVNULL)
    return subprocess.run(cmd, cwd=REPO, stdin=subprocess.DEVNULL)


def git(*args: str, capture: bool = True) -> str:
    try:
        r = subprocess.run(
            ["git", *args], cwd=REPO, capture_output=capture, text=True, timeout=10, stdin=subprocess.DEVNULL
        )
        return r.stdout.strip() if capture else ""
    except Exception:
        return ""


def find_latest_editions_dir() -> Path | None:
    """Return the most-recent <tempdir>/editions_v28a-* dir or REPO/editions if it exists."""
    candidates = sorted(TMP.glob("editions_v28a*"), key=lambda p: p.stat().st_mtime, reverse=True)
    for c in candidates:
        if c.is_dir() and any(c.glob("*.epub")):
            return c
    repo_eds = REPO / "editions"
    if repo_eds.is_dir() and any(repo_eds.glob("*.epub")):
        return repo_eds
    return None


# ============================================================
# subcommand: status
# ============================================================


def cmd_status(_args) -> int:
    """Print a one-screen health dashboard."""
    from scripts.core import notes_io

    print(f"\n{BOLD}YHWH Ya' Way status{RESET}  {DIM}{REPO}{RESET}\n")

    # Notes
    notes_dir = REPO / "content" / "notes"
    files = sorted(p for p in notes_dir.glob("*.py") if p.name != "__init__.py")
    total = 0
    kind_counts: Counter = Counter()
    for f in files:
        notes = notes_io.load_notes(f) or []
        total += len(notes)
        for tup in notes:
            if isinstance(tup, tuple) and len(tup) >= 5:
                kind_counts[tup[4]] += 1
    print(f"  {BOLD}Notes{RESET}      {total:,} attributed across {len(files)} books")
    top_kinds = kind_counts.most_common(5)
    for k, n in top_kinds:
        print(f"    {DIM}{k:<28}{RESET} {n}")

    # Editions
    print()
    eds_dir = find_latest_editions_dir()
    if eds_dir:
        epubs = sorted(eds_dir.glob("*.epub"))
        total_size = sum(p.stat().st_size for p in epubs) / 1024 / 1024
        latest = max(p.stat().st_mtime for p in epubs)
        age_min = (time.time() - latest) / 60
        age_str = f"{age_min:.0f}m ago" if age_min < 60 else f"{age_min / 60:.1f}h ago"
        print(f"  {BOLD}Editions{RESET}   {len(epubs)} EPUBs · {total_size:.2f} MB total · built {age_str}")
        print(f"    {DIM}{eds_dir}{RESET}")
    else:
        print(f"  {BOLD}Editions{RESET}   {YELLOW}none built{RESET}")

    # Git
    print()
    branch = git("branch", "--show-current") or "(detached)"
    last = git("log", "-1", "--format=%h %s")
    tag = git("describe", "--tags", "--abbrev=0")
    dirty = git("status", "--porcelain")
    dirty_count = len(dirty.splitlines()) if dirty else 0
    print(f"  {BOLD}Git{RESET}        branch={branch}  last-tag={tag or '(none)'}")
    if last:
        print(f"    {DIM}{last}{RESET}")
    if dirty_count:
        print(f"    {YELLOW}{dirty_count} uncommitted change(s){RESET}")
    else:
        print(f"    {GREEN}clean{RESET}")

    print()
    return 0


# ============================================================
# subcommand: doctor
# ============================================================


def cmd_doctor(_args) -> int:
    """Suggest the next action based on current project state."""
    print(f"\n{BOLD}ebible doctor{RESET}  {DIM}what should I do next?{RESET}\n")

    # 1. uncommitted changes? note them but don't block (they may be in progress)
    dirty = git("status", "--porcelain")
    notes_dirty = bool([line for line in dirty.splitlines() if "content/notes/" in line])

    # 2. Master HTML newer than editions?
    eds_dir = find_latest_editions_dir()
    eds_stale = False
    if eds_dir:
        epubs = list(eds_dir.glob("*.epub"))
        if epubs:
            latest_ep = max(p.stat().st_mtime for p in epubs)
            html_files = list((REPO / "epub_working").glob("*.html"))
            if html_files and max(p.stat().st_mtime for p in html_files) > latest_ep:
                eds_stale = True

    # 3. ship-check pass?
    print(f"  {DIM}running ship-check (this may take a moment) …{RESET}")
    r = run_script("ship-check.py", capture=True)
    sc_passed = r.returncode == 0
    sc_summary = (r.stdout or "").splitlines()
    fail_lines = [line for line in sc_summary if "✗" in line and "CHECK(S) FAILED" not in line]

    # Diagnosis & advice
    print()
    if notes_dirty:
        print(f"  {YELLOW}↻{RESET} You have uncommitted changes in content/notes/.")
        print(f"    {DIM}→ python3 scripts/inject.py --all-books{RESET}")
        print(f"    {DIM}→ python3 scripts/manifest.py --build{RESET}")
        return 0

    if eds_stale:
        print(f"  {YELLOW}↻{RESET} Master HTML is newer than your built editions.")
        print(f"    {DIM}→ ebible build{RESET}")
        return 0

    if not sc_passed:
        print(f"  {RED}✗{RESET} ship-check has {len(fail_lines)} failing gate(s):")
        for line in fail_lines[:5]:
            print(f"    {DIM}{line.strip()}{RESET}")
        print(f"    {DIM}→ ebible ship --verbose  (to see details){RESET}")
        return 1

    if dirty.strip():
        print(f"  {GREEN}✓{RESET} ship-check is clean. Ready to commit.")
        print(f"    {DIM}→ git add -A && git commit -m '...'{RESET}")
        return 0

    print(f"  {GREEN}{BOLD}✓ All gates green.{RESET}")
    print(f"    {DIM}→ ebible build   (inject notes → manifest → editions → epubcheck){RESET}")
    print(f"    {DIM}→ the built EPUB is the deliverable — a free download.{RESET}")
    return 0


# ============================================================
# subcommand: add
# ============================================================


def cmd_add(args) -> int:
    """Wrap new_note.py — scaffold a new note."""
    extras = [args.book, str(args.chapter), str(args.verse), "--kind", args.kind]
    if args.anchor:
        extras += ["--anchor", args.anchor]
    if args.suffix:
        extras += ["--suffix", args.suffix]
    if args.title:
        extras += ["--title", args.title]
    return run_script("new_note.py", *extras).returncode


# ============================================================
# subcommand: build (chained workflow)
# ============================================================


def cmd_build(args) -> int:
    """Inject + manifest + build_edition + epubcheck."""
    print(f"\n{BOLD}ebible build{RESET}  {DIM}full pipeline{RESET}\n")

    steps = [
        ("inject (source → HTML)", "inject.py", ["--all-books"]),
        ("manifest (corpus hash)", "manifest.py", ["--build"]),
    ]
    for label, script, sargs in steps:
        print(f"{BOLD}{label}{RESET}")
        r = run_script(script, *sargs)
        if r.returncode != 0:
            print(f"{RED}✗ {label} failed.{RESET}", file=sys.stderr)
            return r.returncode

    # build editions
    out_dir = args.output_dir or (TMP / f"editions_{args.version.replace('-', '')}")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    eargs = ["--all", "--version", args.version, "--output-dir", str(out_dir)]
    if args.no_parallel:
        eargs.append("--no-parallel")
    if args.force:
        eargs.append("--force")
    print(f"\n{BOLD}build editions{RESET}")
    r = run_script("build_edition.py", *eargs)
    if r.returncode != 0:
        return r.returncode

    # validate
    print(f"\n{BOLD}epubcheck{RESET}")
    r = run_script("epubcheck.py", "--editions-dir", str(out_dir))
    return r.returncode


# ============================================================
# subcommand: ship
# ============================================================


def cmd_ship(args) -> int:
    """Run ship-check (with the opt-in epubcheck gate if requested)."""
    sargs = []
    if args.epubcheck:
        sargs.append("--epubcheck")
        eds_dir = find_latest_editions_dir()
        if eds_dir:
            sargs += ["--editions-dir", str(eds_dir)]
    if args.verbose:
        sargs.append("--verbose")
    return run_script("ship-check.py", *sargs).returncode


# ============================================================
# subcommand: test
# ============================================================


def cmd_test(args) -> int:
    """Run pytest."""
    cmd = [PYTHON, "-m", "pytest", "tests/"]
    if args.verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    return subprocess.run(cmd, cwd=REPO, stdin=subprocess.DEVNULL).returncode


# ============================================================
# subcommand: audit  (code-quality CI gate)
# ============================================================

# Shared per-tool exit-code contract for the audit_*.main() wrappers:
#   0 = clean · 1 = real findings · 2/3 = tool or setup missing.
_AUDIT_FINDING_RC = 1
_AUDIT_MISSING_RCS = (2, 3)


def _default_audit_runners() -> list[tuple[str, object]]:
    """The off-dashboard code-quality audits, fast-first. Each entry is
    ``(label, () -> exit_code)``. These wrap dev tools (vulture/mypy/
    pip-audit) or shell out, which is exactly why they are kept OFF the
    live /preflight dashboard (see scripts/api/preflight.py — only the
    stdlib check_a11y is wired there). This is their automatic home."""
    from scripts import audit_caches, audit_dead_code, audit_deps, audit_types

    return [
        ("cache invalidation", lambda: audit_caches.main([])),
        ("dead code (vulture)", lambda: audit_dead_code.main([])),
        ("types (mypy)", lambda: audit_types.main([])),
        ("dependencies (pip-audit)", lambda: audit_deps.main([])),
    ]


def run_audit_suite(runners=None, *, require_tools: bool = False) -> dict:
    """Run each audit runner, classify its exit code, aggregate a CI verdict.

    Pure aggregator (no printing); ``runners`` is injectable for tests as a
    list of ``(label, () -> exit_code)``. A runner returning 1 is a real
    finding (fails the gate). A runner returning 2 or 3 means its tool/setup
    is missing — skipped, and it does NOT fail the gate unless
    ``require_tools`` is set (so CI can enforce full coverage).

    Returns ``{ok, exit_code, results, clean, findings, skipped}``.
    """
    if runners is None:
        runners = _default_audit_runners()
    results: list[tuple[str, int]] = []
    clean: list[str] = []
    findings: list[str] = []
    skipped: list[str] = []
    for label, fn in runners:
        rc = fn()
        results.append((label, rc))
        if rc == _AUDIT_FINDING_RC:
            findings.append(label)
        elif rc in _AUDIT_MISSING_RCS:
            skipped.append(label)
        else:
            clean.append(label)
    failed = bool(findings) or (require_tools and bool(skipped))
    return {
        "ok": not failed,
        "exit_code": 1 if failed else 0,
        "results": results,
        "clean": clean,
        "findings": findings,
        "skipped": skipped,
    }


def cmd_audit(args) -> int:
    """Run the off-dashboard code-quality audits as one CI gate."""
    print(f"\n{BOLD}ebible audit{RESET}  {DIM}code-quality gate (off-dashboard checks){RESET}")
    result = run_audit_suite(require_tools=getattr(args, "require_tools", False))

    print(f"\n{BOLD}audit summary{RESET}")
    print(
        f"  {len(result['clean'])} clean · {len(result['findings'])} with findings · {len(result['skipped'])} skipped"
    )
    if result["skipped"]:
        print(f"  {YELLOW}skipped (tool/setup missing):{RESET} {', '.join(result['skipped'])}")
        print(f"    {DIM}install dev tools for full coverage: pipx install vulture mypy pip-audit{RESET}")
    if result["findings"]:
        print(f"  {RED}✗ findings in:{RESET} {', '.join(result['findings'])}")
    elif result["ok"]:
        print(f"  {GREEN}✓ all audits clean{RESET}")
    else:
        print(f"  {RED}✗ --require-tools: failing because audit(s) were skipped{RESET}")
    print()
    return result["exit_code"]


# ============================================================
# subcommand: repl
# ============================================================


def cmd_repl(_args) -> int:
    """Drop into python -i with project helpers pre-loaded."""
    init_code = '''
import sys
sys.path.insert(0, ".")
from pathlib import Path
from scripts.core import config, notes_io, html_utils
from scripts.core.notes_io import load_notes, atomic_write, ensure_backup
from scripts.core.html_utils import strip_tags, word_count

# Convenience: loaded books
BOOKS = config.load_books()
EDITIONS = config.load_editions()
KINDS = config.load_kinds()

def all_notes():
    """Iterate every note across all books — yields (book_code, tuple)."""
    for f in sorted(Path("content/notes").glob("*.py")):
        if f.name == "__init__.py": continue
        for tup in (load_notes(f) or []):
            yield (f.stem, tup)

def book_notes(code):
    """Return list of notes for one book by code."""
    return load_notes(f"content/notes/{code}.py") or []

print()
print("ebible REPL — Python with YHWH Ya' Way helpers loaded.")
print("Available: config, BOOKS, EDITIONS, KINDS, load_notes(), all_notes(),")
print("           book_notes(code), strip_tags, word_count, atomic_write.")
print(f"Loaded {len(BOOKS)} books, {len(EDITIONS)} editions, {len(KINDS)} kinds.")
print()
'''
    init_path = TMP / ".ebible_repl_init.py"
    init_path.write_text(init_code)
    env = os.environ.copy()
    env["PYTHONSTARTUP"] = str(init_path)
    return subprocess.run([PYTHON], env=env, cwd=REPO).returncode


# ============================================================
# subcommand: watch
# ============================================================


def cmd_watch(_args) -> int:
    """Auto-rebuild on changes to content/notes/*.py."""
    notes_dir = REPO / "content" / "notes"
    files = [p for p in notes_dir.glob("*.py") if p.name != "__init__.py"]

    def snapshot() -> dict[Path, float]:
        return {p: p.stat().st_mtime for p in files if p.is_file()}

    last = snapshot()
    print(f"\n{BOLD}ebible watch{RESET}  {DIM}{len(files)} files in content/notes/{RESET}")
    print(f"  {DIM}auto-runs inject + manifest on save. Ctrl-C to stop.{RESET}\n")

    try:
        while True:
            time.sleep(1.5)
            current = snapshot()
            changed = [p for p, m in current.items() if last.get(p, 0) != m]
            if changed:
                print(f"{BLUE}↻{RESET} change detected:")
                for p in changed:
                    print(f"    {DIM}{p.relative_to(REPO)}{RESET}")
                # Fast path: only inject the affected book(s)
                for p in changed:
                    book = p.stem
                    if book == "__init__":
                        continue
                    print(f"  {DIM}injecting {book} …{RESET}")
                    run_script("inject.py", "--book", book)
                # Refresh manifest
                run_script("manifest.py", "--build")
                last = current
                print(f"  {GREEN}✓ ready{RESET}\n")
    except KeyboardInterrupt:
        print(f"\n  {DIM}stopping watch{RESET}\n")
        return 0


# ============================================================
# subcommand: web
# ============================================================


def cmd_web(args) -> int:
    """Launch the local web UI for note editing."""
    extras = ["--host", args.host, "--port", str(args.port)]
    if args.no_browser:
        extras.append("--no-browser")
    return run_script("web.py", *extras).returncode


# ============================================================
# subcommand: help
# ============================================================


HELP_EXAMPLES: dict[str, list[str]] = {
    "status": ["ebible status"],
    "doctor": ["ebible doctor"],
    "add": [
        "ebible add gen 3 15 --kind comm-rabbinic --anchor 'serpent'",
        "ebible add 1en 6 1 --kind comm-ethiopian --suffix a",
    ],
    "inject": ["ebible inject --all-books", "ebible inject --book gen --dry-run"],
    "build": ["ebible build", "ebible build --version v28a-26", "ebible build --force --no-parallel"],
    "ship": ["ebible ship", "ebible ship --epubcheck --verbose"],
    "audit": ["ebible audit", "ebible audit --require-tools  # strict CI: a missing dev tool fails"],
    "test": ["ebible test", "ebible test --verbose"],
    "repl": ["ebible repl  # then: book_notes('gen')[0]"],
    "watch": ["ebible watch  # edits to content/notes/*.py auto-rebuild"],
    "web": [
        "ebible web                          # localhost:8765",
        "ebible web --port 9000 --no-browser",
        "ebible web --host 0.0.0.0           # LAN access (be careful)",
    ],
    "manifest": ["ebible manifest --status", "ebible manifest --build"],
    "search": ["ebible search 'serpent' --kind comm-rabbinic", "ebible search --book gen --chapter 3"],
    "quality": ["ebible quality", "ebible quality --book gen --no-per-kind"],
    "epubcheck": ["ebible epubcheck --editions-dir <tempdir>/editions_v28a25"],
}


def cmd_help(args) -> int:
    """Print help with concrete examples for one or all subcommands."""
    if args.subcommand and args.subcommand in HELP_EXAMPLES:
        print(f"\n{BOLD}ebible {args.subcommand}{RESET}")
        for ex in HELP_EXAMPLES[args.subcommand]:
            print(f"  {ex}")
        print()
    else:
        print(f"\n{BOLD}ebible — unified CLI for the YHWH Ya' Way platform{RESET}\n")
        print(f"{DIM}Common workflows:{RESET}")
        for cmd in ("status", "doctor", "add", "build", "ship", "audit", "test", "repl", "watch"):
            ex = HELP_EXAMPLES[cmd][0]
            print(f"  {ex}")
        print()
        print(f"{DIM}Pass-through to underlying scripts:{RESET}")
        print("  ebible inject / manifest / quality / search / diff / bulk-edit")
        print("  ebible epubcheck / cleanup / fix-xrefs / verify / taxonomy / dashboard")
        print()
        print(f"{DIM}For per-command help: ebible help <command>{RESET}\n")
    return 0


# ============================================================
# pass-through dispatch
# ============================================================


PASS_THROUGHS: dict[str, str] = {
    "inject": "inject.py",
    "manifest": "manifest.py",
    "quality": "note_quality.py",
    "search": "note_search.py",
    "diff": "note_diff.py",
    "bulk-edit": "bulk_edit.py",
    "dashboard": "dashboard.py",
    "epubcheck": "epubcheck.py",
    "cleanup": "cleanup.py",
    "fix-xrefs": "fix_xref_targets.py",
    "verify": "verify.py",
    "taxonomy": "validate_taxonomy.py",
    "customize": "customize.py",
    # Discoverable wrappers for previously-orphan tools (λ.4)
    "add-kind": "add_kind.py",
    "bibliography": "bibliography.py",
    "a11y": "check_a11y.py",
    "check": "check_manifest.py",
    "preview": "preview_server.py",
    # Symbol-toggle dev tool data layer (μ.0)
    "matrix": "matrix.py",
}


# ============================================================
# main
# ============================================================


SUBCOMMAND_HANDLERS = {
    "status": cmd_status,
    "doctor": cmd_doctor,
    "add": cmd_add,
    "build": cmd_build,
    "ship": cmd_ship,
    "audit": cmd_audit,
    "test": cmd_test,
    "repl": cmd_repl,
    "watch": cmd_watch,
    "web": cmd_web,
    "help": cmd_help,
}


def main() -> int:
    p = argparse.ArgumentParser(prog="ebible", description="Unified CLI for the YHWH Ya' Way platform")
    subs = p.add_subparsers(dest="cmd", required=False)

    subs.add_parser("status", help="health dashboard")
    subs.add_parser("doctor", help="suggest next action")

    a = subs.add_parser("add", help="scaffold a new note (wraps new_note.py)")
    a.add_argument("book")
    a.add_argument("chapter", type=int)
    a.add_argument("verse", type=int)
    a.add_argument("--kind", required=True)
    a.add_argument("--anchor", default="")
    a.add_argument("--suffix", default="")
    a.add_argument("--title", default="")

    b = subs.add_parser("build", help="inject + manifest + editions + epubcheck")
    b.add_argument("--version", default="v28a-dev")
    b.add_argument("--output-dir", type=Path, default=None)
    b.add_argument("--no-parallel", action="store_true")
    b.add_argument("--force", action="store_true")

    s = subs.add_parser("ship", help="run ship-check")
    s.add_argument("--epubcheck", action="store_true")
    s.add_argument("--verbose", "-v", action="store_true")

    au = subs.add_parser("audit", help="code-quality audits (caches/vulture/mypy/pip-audit) — CI gate")
    au.add_argument(
        "--require-tools",
        action="store_true",
        help="fail if a dev tool (vulture/mypy/pip-audit) is not installed",
    )

    t = subs.add_parser("test", help="run pytest")
    t.add_argument("--verbose", "-v", action="store_true")

    subs.add_parser("repl", help="drop into Python with helpers loaded")
    subs.add_parser("watch", help="auto-rebuild on note changes")

    w = subs.add_parser("web", help="local web UI for editing notes")
    w.add_argument("--host", default="127.0.0.1")
    w.add_argument("--port", type=int, default=8765)
    w.add_argument("--no-browser", action="store_true")

    h = subs.add_parser("help", help="show help with examples")
    h.add_argument("subcommand", nargs="?")

    # Pass-through subcommands: forward ALL args after the subcommand
    # name straight to the underlying script. We can't use argparse for
    # this because mixing argparse.REMAINDER with optional flags drops
    # values (e.g. `ebible matrix --edition X` would lose X).
    # Instead: detect the pass-through subcommand from sys.argv directly.
    pass_through_cmd = None
    pass_through_args: list[str] = []
    if len(sys.argv) >= 2 and sys.argv[1] in PASS_THROUGHS:
        pass_through_cmd = sys.argv[1]
        pass_through_args = sys.argv[2:]

    # Register stub subparsers so --help still lists them
    for name, _ in PASS_THROUGHS.items():
        subs.add_parser(name, help=f"→ scripts/{PASS_THROUGHS[name]}", add_help=False)

    if pass_through_cmd is not None:
        return run_script(PASS_THROUGHS[pass_through_cmd], *pass_through_args).returncode

    args, _unknown = p.parse_known_args()

    if not args.cmd:
        return cmd_help(argparse.Namespace(subcommand=None))

    return SUBCOMMAND_HANDLERS[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
