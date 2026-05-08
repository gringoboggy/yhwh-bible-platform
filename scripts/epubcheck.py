#!/usr/bin/env python3
"""
epubcheck.py — Wrapper around the W3C/IDPF ``epubcheck`` validator.

Most retailers (Apple Books, Kobo, Google Play Books) run epubcheck
themselves before listing — failing there means rejection. This wrapper
runs it locally and reports a compact summary in the same style as
``verify.py``. It catches:

  * MIME-type bugs (``mimetype`` file must be first, uncompressed)
  * Manifest errors (referenced-but-missing or present-but-unmanifested)
  * Navigation issues (broken ``nav.xhtml`` / ``toc.ncx`` references)
  * Broken hrefs across the whole book
  * Malformed CSS
  * Accessibility blockers

The script **fails soft**: if Java is missing, or the epubcheck JAR
cannot be located, it prints clear install instructions and exits 0,
so it can sit in CI without blocking anyone who hasn't installed it
yet. Pass ``--require`` to turn that into a hard failure (exit 2).

Examples:
    python3 scripts/epubcheck.py
        # auto-find latest .epub in repo root, run epubcheck

    python3 scripts/epubcheck.py path/to/My.epub
        # check a specific file

    python3 scripts/epubcheck.py --jar /opt/epubcheck.jar Some.epub
        # explicit JAR path

    python3 scripts/epubcheck.py --strict
        # also fail on warnings (default fails on errors only)

    python3 scripts/epubcheck.py --require
        # fail (exit 2) if epubcheck not installed, instead of skipping

    python3 scripts/epubcheck.py --verbose
        # show all findings, not just the first 20

Exit codes:
    0  passed (or skipped without --require)
    1  epubcheck found errors (or warnings, with --strict)
    2  setup error: file not found, parse failure, or missing tool with --require

Discovery order for the validator:
    1. ``--jar`` argument
    2. ``EPUBCHECK_JAR`` environment variable
    3. ``epubcheck`` executable on PATH (Homebrew / Debian wrappers)
    4. ``<repo>/.tools/epubcheck*/epubcheck.jar``
    5. ``~/.local/share/epubcheck*/epubcheck.jar``

Install hints (printed when nothing is found):
    macOS:    brew install epubcheck
    Debian:   apt-get install epubcheck
    Manual:   https://github.com/w3c/epubcheck/releases
              unzip into ``<repo>/.tools/`` so this script can find it.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# ----------------------------------------------------------------------
# Tool discovery
# ----------------------------------------------------------------------


def find_epubcheck(explicit_jar: str | None = None) -> tuple[str | None, str | None]:
    """Locate epubcheck. Returns (kind, path) or (None, None).

    kind is "wrapper" (an executable on PATH) or "jar" (path to a .jar).
    """
    # 1. Explicit --jar
    if explicit_jar:
        p = Path(explicit_jar)
        if p.is_file():
            return ("jar", str(p))
        return (None, None)

    # 2. Env var
    env = os.environ.get("EPUBCHECK_JAR")
    if env:
        p = Path(env)
        if p.is_file():
            return ("jar", str(p))

    # 3. PATH wrapper (`epubcheck` from Homebrew / apt)
    wrapper = shutil.which("epubcheck")
    if wrapper:
        return ("wrapper", wrapper)

    # 4. Repo-local .tools/
    for cand in sorted((REPO_ROOT / ".tools").glob("epubcheck*/epubcheck.jar")):
        return ("jar", str(cand))

    # 5. User-local
    user_local = Path.home() / ".local" / "share"
    if user_local.is_dir():
        for cand in sorted(user_local.glob("epubcheck*/epubcheck.jar")):
            return ("jar", str(cand))

    return (None, None)


def has_java() -> bool:
    return shutil.which("java") is not None


INSTALL_HINT = """\
epubcheck not found. Install one of these ways:

  macOS:    brew install epubcheck
  Debian:   sudo apt-get install epubcheck
  Manual:   https://github.com/w3c/epubcheck/releases
            unzip into ``<repo>/.tools/`` (so e.g. .tools/epubcheck-5.1.0/epubcheck.jar)
            or set EPUBCHECK_JAR=/path/to/epubcheck.jar in your environment.
"""


# ----------------------------------------------------------------------
# Target EPUB resolution
# ----------------------------------------------------------------------


def find_latest_epub(root: Path) -> Path | None:
    """Return the most recently modified ``*.epub`` in the repo root, or None."""
    candidates = list(root.glob("*.epub"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


# ----------------------------------------------------------------------
# Run + parse
# ----------------------------------------------------------------------


# epubcheck text-output summary line:
#   Messages: 0 fatals / 0 errors / 1 warnings / 0 infos
SUMMARY_RE = re.compile(
    r"Messages:\s+(\d+)\s+fatals?\s*/\s*"
    r"(\d+)\s+errors?\s*/\s*"
    r"(\d+)\s+warnings?\s*/\s*"
    r"(\d+)\s+infos?",
    re.IGNORECASE,
)


def run_epubcheck(kind: str, path: str, epub_path: Path) -> subprocess.CompletedProcess:
    if kind == "wrapper":
        cmd = [path, str(epub_path)]
    else:  # jar
        cmd = ["java", "-jar", path, str(epub_path)]
    return subprocess.run(cmd, capture_output=True, text=True)


def parse_summary(text: str) -> tuple[int, int, int, int] | None:
    """Return (fatals, errors, warnings, infos) from the epubcheck summary line."""
    m = SUMMARY_RE.search(text)
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)))


def extract_findings(text: str) -> list[str]:
    """Return the per-message lines (ERROR / WARNING / FATAL / INFO)."""
    findings = []
    for ln in text.splitlines():
        # epubcheck prefixes each finding with one of these severity tokens.
        if re.match(r"^(FATAL|ERROR|WARNING|INFO|USAGE)\b", ln.strip()):
            findings.append(ln.rstrip())
    return findings


# ----------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_summary(epub_path: Path, fatals: int, errors: int, warns: int, infos: int, strict: bool) -> None:
    size_mb = epub_path.stat().st_size / (1024 * 1024)
    bad = fatals + errors > 0 or (strict and warns > 0)
    color = RED if bad else GREEN
    sym = "✗" if bad else "✓"
    print(
        f"\n{color}{sym} epubcheck: "
        f"fatals={fatals}  errors={errors}  warnings={warns}  infos={infos}  "
        f"{epub_path.name} ({size_mb:.2f} MB){RESET}"
    )


def print_skip(reason: str, require: bool) -> None:
    color = RED if require else YELLOW
    sym = "✗" if require else "○"
    print(f"\n{color}{sym} epubcheck: skipped — {reason}{RESET}")
    print(INSTALL_HINT, file=sys.stderr)


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(
        description="Run epubcheck against an EPUB and report a compact summary.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "epub",
        nargs="?",
        type=Path,
        help="path to .epub (default: most recent *.epub in repo root)",
    )
    p.add_argument("--editions-dir", type=Path,
                   help="run against every .epub in this directory")
    p.add_argument("--jar", help="explicit path to epubcheck.jar")
    p.add_argument("--strict", action="store_true", help="fail on warnings as well as errors")
    p.add_argument(
        "--require",
        action="store_true",
        help="fail (exit 2) if epubcheck unavailable, instead of skipping",
    )
    p.add_argument("--quiet", action="store_true", help="only print the summary line")
    p.add_argument("--verbose", action="store_true", help="show all findings, not just first 20")
    args = p.parse_args()

    # Batch mode — iterate over directory
    if args.editions_dir is not None:
        if not args.editions_dir.is_dir():
            print(f"{RED}ERROR: not a directory: {args.editions_dir}{RESET}", file=sys.stderr)
            sys.exit(2)
        epubs = sorted(args.editions_dir.glob("*.epub"))
        if not epubs:
            print(f"{RED}ERROR: no .epub files in {args.editions_dir}{RESET}", file=sys.stderr)
            sys.exit(2)
        if not has_java():
            print_skip("Java is not installed", args.require)
            sys.exit(2 if args.require else 0)
        kind, path = find_epubcheck(args.jar)
        if kind is None:
            print_skip("epubcheck JAR not found", args.require)
            sys.exit(2 if args.require else 0)
        total_e = total_w = 0
        for ep in epubs:
            cp = run_epubcheck(kind, path, ep)
            txt = (cp.stdout or "") + "\n" + (cp.stderr or "")
            summary = parse_summary(txt)
            if summary:
                # parse_summary returns (fatals, errors, warnings, infos)
                fatals, errors, warnings, _infos = summary
                total_e += errors + fatals
                total_w += warnings
        glyph = GREEN + "✓" if total_e == 0 else RED + "✗"
        print(f"{glyph} epubcheck (batch): {len(epubs)} edition(s) · "
              f"errors={total_e} · warnings={total_w}{RESET}")
        sys.exit(0 if total_e == 0 else 1)

    # Single-file mode (original behaviour)

    # Resolve target EPUB
    if args.epub is None:
        args.epub = find_latest_epub(REPO_ROOT)
    if args.epub is None:
        print(f"{RED}ERROR: no .epub specified and none found in {REPO_ROOT}{RESET}", file=sys.stderr)
        sys.exit(2)
    if not args.epub.is_file():
        print(f"{RED}ERROR: not a file: {args.epub}{RESET}", file=sys.stderr)
        sys.exit(2)

    # Tool discovery — fail-soft path
    if not has_java():
        print_skip("Java is not installed", args.require)
        sys.exit(2 if args.require else 0)

    kind, path = find_epubcheck(args.jar)
    if kind is None:
        msg = "epubcheck JAR not found"
        if args.jar:
            msg = f"--jar {args.jar} does not exist"
        print_skip(msg, args.require)
        sys.exit(2 if args.require else 0)

    # Run
    if not args.quiet:
        print(f"running epubcheck ({kind}: {path}) on {args.epub.name} …")
    cp = run_epubcheck(kind, path, args.epub)

    # epubcheck writes most output to stderr; stdout sometimes carries the summary.
    text = (cp.stdout or "") + "\n" + (cp.stderr or "")

    summary = parse_summary(text)
    if summary is None:
        # Couldn't parse — show raw output and bail.
        print(f"{RED}ERROR: could not parse epubcheck output{RESET}", file=sys.stderr)
        if cp.stdout:
            print("--- stdout ---", file=sys.stderr)
            print(cp.stdout, file=sys.stderr)
        if cp.stderr:
            print("--- stderr ---", file=sys.stderr)
            print(cp.stderr, file=sys.stderr)
        sys.exit(2)

    fatals, errors, warns, infos = summary

    # Show findings
    if not args.quiet and (fatals or errors or warns or args.verbose):
        findings = extract_findings(text)
        limit = None if args.verbose else 20
        shown = findings if limit is None else findings[:limit]
        for ln in shown:
            sev = ln.split("(", 1)[0].strip()
            color = RED if sev in ("FATAL", "ERROR") else (YELLOW if sev == "WARNING" else BLUE)
            print(f"  {color}{ln}{RESET}")
        if limit is not None and len(findings) > limit:
            print(f"  … {len(findings) - limit} more (re-run with --verbose to see all)")

    print_summary(args.epub, fatals, errors, warns, infos, args.strict)

    # Exit code
    if fatals or errors:
        sys.exit(1)
    if args.strict and warns:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
