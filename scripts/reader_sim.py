#!/usr/bin/env python3
"""Reader Simulation Lab orchestrator — build + gate per e-reader profile.

Post-audit phase: one entry point per reader (Apple · Kobo · Kindle · Play).
See docs/superpowers/plans/2026-06-18-reader-simulation-lab.md and dev/reader_sim/README.md.

Usage:
    py -3 scripts/reader_sim.py --list
    py -3 scripts/reader_sim.py --gate kobo --artifact path/to.kepub.epub
    py -3 scripts/reader_sim.py --gate all --artifact-dir dev/.audit-build
    py -3 scripts/reader_sim.py --build apple --edition ethiopian-tewahedo --version 0.1.0
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO / "build" / "reader-sim"
DEFAULT_EDITION = "ethiopian-tewahedo"
DEFAULT_VERSION = "0.1.0"


@dataclass(frozen=True)
class ReaderProfile:
    id: str
    label: str
    target_reader: str
    packaging: str  # epub | kepub.epub
    lane: str
    checklist: str


READERS: dict[str, ReaderProfile] = {
    "apple": ReaderProfile(
        "apple",
        "Apple Books",  # term-ref-ok: free-catalog platform label
        "tablet",
        "epub",
        "mac",
        "dev/reader_sim/apple/qa-checklist.md",
    ),
    "kobo": ReaderProfile(
        "kobo",
        "Kobo e-ink",
        "eink",
        "kepub.epub",
        "win",
        "dev/reader_sim/kobo/qa-checklist.md",
    ),
    "kindle": ReaderProfile(
        "kindle",
        "Kindle (Send-to-Kindle)",
        "everywhere",
        "epub",
        "mac",
        "dev/reader_sim/kindle/qa-checklist.md",
    ),
    "play": ReaderProfile(
        "play",
        "Google Play Books",  # term-ref-ok: free-catalog platform label
        "everywhere",
        "epub",
        "win",
        "dev/reader_sim/play/qa-checklist.md",
    ),
}


def _run(cmd: list[str], *, cwd: Path = REPO) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out


def _epubcheck(artifact: Path) -> tuple[bool, str]:
    code, out = _run([sys.executable, str(REPO / "scripts" / "epubcheck.py"), "--require", "--strict", str(artifact)])
    return code == 0, out.strip() or ("epubcheck OK" if code == 0 else "epubcheck FAIL")


def _verify_kr2(artifact: Path) -> tuple[bool, str]:
    code, out = _run([sys.executable, str(REPO / "dev" / "verify_kr2_build.py"), str(artifact)])
    return code == 0, out.strip() or ("verify_kr2 OK" if code == 0 else "verify_kr2 FAIL")


def _audit_structure(artifact: Path) -> tuple[bool, str]:
    code, out = _run([sys.executable, "-m", "scripts.audit_epub_structure", str(artifact)])
    return code == 0, out.strip() or ("structure OK" if code == 0 else "structure FAIL")


def _kindle_gates(artifact: Path, *, m4b: bool) -> list[tuple[str, bool, str]]:
    from scripts.core.kindle_post import verify_kindle_m4b, verify_kindle_safe

    results: list[tuple[str, bool, str]] = []
    safe = verify_kindle_safe(artifact)
    results.append(("verify_kindle_safe", not safe, "; ".join(safe) or "OK"))
    if m4b:
        m4b_fails = verify_kindle_m4b(artifact)
        results.append(("verify_kindle_m4b", not m4b_fails, "; ".join(m4b_fails) or "OK"))
    return results


def gate_reader(reader_id: str, artifact: Path, *, m4b: bool = False) -> dict:
    """Run automated gates for one reader profile on an existing artifact."""
    profile = READERS[reader_id]
    if not artifact.is_file():
        return {
            "reader": reader_id,
            "artifact": str(artifact),
            "ok": False,
            "checks": [{"name": "exists", "pass": False, "detail": "missing file"}],
        }

    checks: list[tuple[str, bool, str]] = []
    suffix = artifact.suffix.lower()
    if profile.packaging == "kepub.epub" and not artifact.name.endswith(".kepub.epub"):
        checks.append(("packaging", False, f"expected .kepub.epub for {reader_id}"))

    ok_ec, msg_ec = _epubcheck(artifact)
    checks.append(("epubcheck", ok_ec, msg_ec))

    if reader_id in ("apple", "kobo", "play"):
        ok_kr, msg_kr = _verify_kr2(artifact)
        checks.append(("verify_kr2_build", ok_kr, msg_kr[:500]))

    if reader_id == "play":
        ok_st, msg_st = _audit_structure(artifact)
        checks.append(("audit_epub_structure", ok_st, msg_st[:500]))

    if reader_id == "kindle":
        checks.extend(_kindle_gates(artifact, m4b=m4b))

    if reader_id == "kobo" and artifact.name.endswith(".kepub.epub"):
        code, out = _run([sys.executable, str(REPO / "dev" / "audit_popup_formula.py"), str(artifact)])
        checks.append(("audit_popup_formula", code == 0, out.strip()[:500] or ("OK" if code == 0 else "FAIL")))

    ok = all(passed for _, passed, _ in checks)
    return {
        "reader": reader_id,
        "artifact": str(artifact),
        "ok": ok,
        "checks": [{"name": n, "pass": p, "detail": d} for n, p, d in checks],
    }


def build_reader(
    reader_id: str,
    edition: str,
    version: str,
    out_dir: Path,
    *,
    m4b: bool = False,
) -> Path:
    """Build one reader-sim artifact (heavy — post-audit / explicit invoke only)."""
    profile = READERS[reader_id]
    out_dir.mkdir(parents=True, exist_ok=True)

    if reader_id == "kindle":
        cmd = [
            sys.executable,
            str(REPO / "scripts" / "build_kindle.py"),
            edition,
            "--version",
            version,
            "--output-dir",
            str(out_dir),
        ]
        if m4b:
            cmd.append("--m4b")
        code, out = _run(cmd)
        if code != 0:
            raise RuntimeError(f"build_kindle failed:\n{out}")
        built = sorted(out_dir.glob("*.epub"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not built:
            raise FileNotFoundError(f"no kindle artifact in {out_dir}")
        return built[0]

    cmd = [
        sys.executable,
        str(REPO / "scripts" / "build_edition.py"),
        edition,
        "--target-reader",
        profile.target_reader,
        "--version",
        version,
        "--output-dir",
        str(out_dir),
        "--force",
    ]
    code, out = _run(cmd)
    if code != 0:
        raise RuntimeError(f"build_edition failed:\n{out}")

    epubs = sorted(out_dir.glob("*.epub"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not epubs:
        raise FileNotFoundError(f"no epub in {out_dir}")
    base = epubs[0]

    if reader_id == "kobo":
        kepub = out_dir / f"{base.stem}.kepub.epub"
        from scripts.build_format_matrix import _apply_kepubify

        _apply_kepubify(base, kepub)
        return kepub

    return base


def _find_artifacts(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    out: list[Path] = []
    for pat in ("*.kepub.epub", "*.epub"):
        out.extend(directory.glob(pat))
    return sorted(out, key=lambda p: p.stat().st_mtime, reverse=True)


def _guess_reader(artifact: Path) -> str | None:
    name = artifact.name.lower()
    if name.endswith(".kepub.epub"):
        return "kobo"
    if "kindle-m4b" in name or "-kindle" in name:
        return "kindle"
    if "tablet" in name or "apple" in name:
        return "apple"
    if "everywhere" in name or "eink" in name:
        return "play"  # everywhere proxy for play gate sweep
    return None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Reader Simulation Lab — build and gate per reader profile.")
    p.add_argument("--list", action="store_true", help="list reader profiles")
    p.add_argument("--gate", metavar="READER", help="gate one reader (apple|kobo|kindle|play|all)")
    p.add_argument("--build", metavar="READER", help="build one reader artifact")
    p.add_argument("--artifact", type=Path, help="artifact path for --gate")
    p.add_argument("--artifact-dir", type=Path, help="directory to scan for --gate all")
    p.add_argument("--edition", default=DEFAULT_EDITION)
    p.add_argument("--version", default=DEFAULT_VERSION)
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    p.add_argument("--m4b", action="store_true", help="kindle M4b fork (build + m4b gate)")
    args = p.parse_args(argv)

    if args.list:
        for rid, prof in READERS.items():
            print(f"{rid:8} {prof.label:28} target={prof.target_reader:12} lane={prof.lane}")
            print(f"         checklist: {prof.checklist}")
        return 0

    if args.gate:
        reader = args.gate
        if reader == "all":
            directory = args.artifact_dir or (REPO / "dev" / ".audit-build")
            artifacts = _find_artifacts(directory)
            if not artifacts:
                print(f"No artifacts in {directory}", file=sys.stderr)
                return 1
            any_fail = False
            for art in artifacts[:4]:
                rid = _guess_reader(art) or "play"
                rep = gate_reader(rid, art, m4b=args.m4b or "m4b" in art.name.lower())
                status = "PASS" if rep["ok"] else "FAIL"
                print(f"\n[{status}] {rid} ← {art.name}")
                for c in rep["checks"]:
                    mark = "ok" if c["pass"] else "FAIL"
                    print(f"  {mark:4} {c['name']}")
                any_fail = any_fail or not rep["ok"]
            return 1 if any_fail else 0

        if not args.artifact:
            print("--artifact required for --gate", file=sys.stderr)
            return 2
        rep = gate_reader(reader, args.artifact, m4b=args.m4b)
        status = "PASS" if rep["ok"] else "FAIL"
        print(f"{status}: {reader} @ {args.artifact}")
        for c in rep["checks"]:
            mark = "ok" if c["pass"] else "FAIL"
            print(f"  {mark:4} {c['name']}: {c['detail'][:200]}")
        return 0 if rep["ok"] else 1

    if args.build:
        print(
            f"Building {args.build} edition={args.edition} version={args.version} → {args.output_dir / args.build}",
            flush=True,
        )
        path = build_reader(
            args.build,
            args.edition,
            args.version,
            args.output_dir / args.build,
            m4b=args.m4b,
        )
        print(f"Built: {path}")
        rep = gate_reader(args.build, path, m4b=args.m4b)
        print("Gate:", "PASS" if rep["ok"] else "FAIL")
        return 0 if rep["ok"] else 1

    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
