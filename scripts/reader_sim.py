#!/usr/bin/env python3
"""Reader Simulation Lab orchestrator — build + gate per e-reader profile.

Post-audit phase: one entry point per reader (Apple · Kobo · Kindle · Play).
See docs/superpowers/plans/2026-06-18-reader-simulation-lab.md and dev/reader_sim/README.md.

Build policy (user 2026-06-17): no EPUB builds until each reader's sim pack exists.
Test policy: agents run reader QA via sim harnesses — not the user tapping four devices.
Full agent sim suite (`--sim all`) runs once all four sim packs exist. Gate-only on cached artifacts is always allowed.

Usage:
    py -3 scripts/reader_sim.py --list
    py -3 scripts/reader_sim.py --gate kobo --artifact path/to.kepub.epub
    py -3 scripts/reader_sim.py --gate all --artifact-dir dev/.audit-build
    py -3 scripts/reader_sim.py --build kobo --edition ethiopian-tewahedo --version 0.1.0
        # blocked until sim pack ready; maintainer override: --force-build
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if __package__ is None:
    sys.path.insert(0, str(REPO))
DEFAULT_OUT = REPO / "build" / "reader-sim"
DEFAULT_EDITION = "ethiopian-tewahedo"
DEFAULT_VERSION = "0.1.0"

# Sim-pack readiness — True when dev/reader_sim/<id>/ scripts exist on disk.
_SIM_PACK_FILES: dict[str, tuple[str, ...]] = {
    "kobo": ("build.sh", "gate.sh", "sim.sh"),
    "play": ("build.sh", "gate.sh", "sim.sh"),
    "kindle": ("build.sh", "gate.sh", "sim.sh", "stk_channel.sh"),
    "apple": ("build.sh", "gate.sh", "sim.sh"),
}


def sim_pack_ready(reader_id: str) -> bool:
    """True when the reader's sim pack shell scripts are present."""
    names = _SIM_PACK_FILES.get(reader_id, ())
    if not names:
        return False
    d = REPO / "dev" / "reader_sim" / reader_id
    return all((d / name).is_file() for name in names)


DISPLAY_ORDER = ("kobo", "play", "kindle", "apple")


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


def all_sim_packs_ready() -> bool:
    return all(sim_pack_ready(rid) for rid in READERS)


def agent_sim_ready() -> tuple[bool, str]:
    """Full cross-reader agent sim suite waits until every sim pack exists."""
    if all_sim_packs_ready():
        return True, "all sim packs ready — agent sim suite unlocked"
    pending = [r for r in DISPLAY_ORDER if not sim_pack_ready(r)]
    return (
        False,
        f"agent sim suite frozen until all sim packs exist. Pending: {', '.join(pending)}.",
    )


# Per-reader agent-runnable sim layers (beyond structural gates). Flip True when wired.
SIM_LAYERS_READY: dict[str, bool] = {
    "kobo": True,  # kobo_tap_calibration + audit_popup_formula
    "play": True,  # thorium_cdp structural proxy (gate-only until Thorium/CDP)
    "kindle": True,  # stk_channel.sh — Lassen library poll when signed in
    "apple": True,  # thorium_cdp structural proxy (tablet popup/ToC taps)
}


def _thorium_sim(artifact: Path, profile: str) -> tuple[bool, str]:
    script = REPO / "dev" / "reader_sim" / "thorium_cdp.py"
    cmd = [sys.executable, str(script), str(artifact), "--profile", profile]
    if os.environ.get("YHWH_THORIUM_LIVE") == "1":
        cmd.append("--live")
    else:
        cmd.append("--gate-only")
    code, out = _run(cmd)
    return code == 0, out.strip()[:500] or ("OK" if code == 0 else "thorium_cdp FAIL")


def _stk_channel_sim(artifact: Path) -> tuple[bool, str]:
    script = REPO / "dev" / "reader_sim" / "kindle" / "stk_channel.sh"
    cmd = ["bash", str(script), str(artifact)]
    if os.environ.get("YHWH_STK_GATE_ONLY") == "1":
        cmd.append("--gate-only")
    code, out = _run(cmd)
    return code == 0, out.strip()[:500] or ("OK" if code == 0 else "stk_channel FAIL")


def sim_reader(reader_id: str, artifact: Path, *, m4b: bool = False) -> dict:
    """Agent-runnable sim: structural gates + reader-specific behavioral proxies."""
    rep = gate_reader(reader_id, artifact, m4b=m4b)
    sim_checks: list[tuple[str, bool, str]] = []

    if reader_id == "kobo" and artifact.is_file() and artifact.name.endswith(".kepub.epub"):
        code, out = _run([sys.executable, str(REPO / "dev" / "kobo_tap_calibration.py"), str(artifact)])
        sim_checks.append(("kobo_tap_calibration", code == 0, out.strip()[:500] or ("OK" if code == 0 else "FAIL")))

    if reader_id == "kindle":
        if SIM_LAYERS_READY.get("kindle"):
            if artifact.is_file():
                ok_stk, msg_stk = _stk_channel_sim(artifact)
                sim_checks.append(("stk_channel_sim", ok_stk, msg_stk))
            else:
                sim_checks.append(("stk_channel_sim", False, "artifact missing"))
        else:
            sim_checks.append(
                (
                    "stk_channel_sim",
                    False,
                    "pending — Send-to-Kindle → Kindle-for-Mac arrival + ingest check (not Previewer)",
                )
            )

    if reader_id in ("apple", "play"):
        layer = "thorium_popup_sim" if reader_id == "apple" else "play_render_sim"
        if SIM_LAYERS_READY.get(reader_id):
            if artifact.is_file():
                ok_th, msg_th = _thorium_sim(artifact, reader_id)
                sim_checks.append((layer, ok_th, msg_th))
            else:
                sim_checks.append((layer, False, "artifact missing"))
        else:
            proxy = (
                "Thorium MCP tap protocol (tablet popup + ToC)"
                if reader_id == "apple"
                else "Thorium or Android-emulator sideload"
            )
            sim_checks.append((layer, False, f"pending — wire {proxy}"))

    if sim_checks:
        rep["sim_checks"] = [{"name": n, "pass": p, "detail": d} for n, p, d in sim_checks]
        rep["sim_ok"] = all(p for _, p, _ in sim_checks)
        rep["ok"] = rep["ok"] and rep["sim_ok"]
    else:
        rep["sim_ok"] = rep["ok"]
    rep["agent_runnable"] = SIM_LAYERS_READY.get(reader_id, False) and rep.get("sim_ok", False)
    return rep


def build_allowed(reader_id: str, *, force: bool = False) -> tuple[bool, str]:
    """Return (allowed, reason). Per-reader builds frozen until that sim pack ships."""
    if reader_id not in READERS:
        return False, f"unknown reader: {reader_id}"
    if force:
        return True, "force-build override"
    if not sim_pack_ready(reader_id):
        return (
            False,
            f"build frozen — sim pack not ready for {reader_id}. "
            "See docs/superpowers/plans/2026-06-18-reader-simulation-lab.md. "
            "Gate cached artifacts with --gate (no rebuild).",
        )
    if not SIM_LAYERS_READY.get(reader_id, False):
        return (
            False,
            f"build frozen — agent sim layer pending for {reader_id}. "
            "Gate/sim cached artifacts; wire sim layer before --build.",
        )
    return True, "sim pack + agent layer ready"


def build_reader(
    reader_id: str,
    edition: str,
    version: str,
    out_dir: Path,
    *,
    m4b: bool = False,
    force: bool = False,
) -> Path:
    """Build one reader-sim artifact (heavy — post-audit / explicit invoke only)."""
    allowed, reason = build_allowed(reader_id, force=force)
    if not allowed:
        raise RuntimeError(reason)
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
    for pat in ("*.kepub.epub", "*.epub", "*/*.kepub.epub", "*/*.epub"):
        out.extend(directory.glob(pat))
    seen: set[Path] = set()
    unique = [p for p in out if p not in seen and not seen.add(p)]  # type: ignore[func-returns-value]
    return sorted(unique, key=lambda p: p.stat().st_mtime, reverse=True)


def _artifact_for_reader(directory: Path, reader_id: str) -> Path | None:
    """Pick one artifact for a reader — prefers ``<dir>/<reader_id>/`` (turn 125 layout)."""
    sub = directory / reader_id
    if sub.is_dir():
        candidates = _find_artifacts(sub)
        if reader_id == "kindle":
            eth = sorted(a for a in candidates if "ethiopian-tewahedo" in a.name.lower())
            if eth:
                return eth[0]
        if candidates:
            return candidates[0]
    return next((a for a in _find_artifacts(directory) if _guess_reader(a) == reader_id), None)


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
    p.add_argument("--sim", metavar="READER", help="agent sim one reader (gates + behavioral proxies; all)")
    p.add_argument("--build", metavar="READER", help="build one reader artifact")
    p.add_argument("--artifact", type=Path, help="artifact path for --gate")
    p.add_argument("--artifact-dir", type=Path, help="directory to scan for --gate all")
    p.add_argument("--edition", default=DEFAULT_EDITION)
    p.add_argument("--version", default=DEFAULT_VERSION)
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    p.add_argument("--m4b", action="store_true", help="kindle M4b fork (build + m4b gate)")
    p.add_argument(
        "--force-build",
        action="store_true",
        help="bypass sim-pack build freeze (maintainer only)",
    )
    args = p.parse_args(argv)

    if args.list:
        for rid in DISPLAY_ORDER:
            prof = READERS[rid]
            ready = "ready" if sim_pack_ready(rid) else "FROZEN"
            print(f"{rid:8} {prof.label:28} target={prof.target_reader:12} lane={prof.lane}  [{ready}]")
            print(f"         checklist: {prof.checklist}")
        ok_sim, sim_msg = agent_sim_ready()
        print(f"\nAgent sim suite: {'UNLOCKED' if ok_sim else 'FROZEN'} — {sim_msg}")
        for rid in DISPLAY_ORDER:
            layer = "wired" if SIM_LAYERS_READY.get(rid) else "pending"
            print(f"  {rid:8} sim layer: {layer}")
        return 0

    if args.sim:
        reader = args.sim
        if reader == "all":
            ok_suite, suite_msg = agent_sim_ready()
            if not ok_suite:
                print(suite_msg, file=sys.stderr)
                return 2
            directory = args.artifact_dir or (REPO / "build" / "reader-sim")
            if not directory.is_dir() or not any(_artifact_for_reader(directory, rid) for rid in DISPLAY_ORDER):
                print(f"No artifacts in {directory}", file=sys.stderr)
                return 1
            skip_kobo = os.environ.get("YHWH_SKIP_KOBO_SIM") == "1"
            any_fail = False
            for rid in DISPLAY_ORDER:
                if rid == "kobo" and skip_kobo:
                    print(f"\n[SKIP] {rid} — WIN lane (YHWH_SKIP_KOBO_SIM=1)")
                    continue
                art = _artifact_for_reader(directory, rid)
                if art is None:
                    print(f"\n[SKIP] {rid} — no artifact in {directory}")
                    any_fail = True
                    continue
                rep = sim_reader(rid, art, m4b=args.m4b or "m4b" in art.name.lower())
                status = "PASS" if rep["ok"] else "FAIL"
                print(f"\n[{status}] {rid} sim ← {art.name}")
                for c in rep["checks"]:
                    mark = "ok" if c["pass"] else "FAIL"
                    print(f"  gate {mark:4} {c['name']}")
                for c in rep.get("sim_checks", []):
                    mark = "ok" if c["pass"] else "FAIL"
                    print(f"  sim  {mark:4} {c['name']}: {c['detail'][:120]}")
                any_fail = any_fail or not rep["ok"]
            return 1 if any_fail else 0

        if not args.artifact:
            print("--artifact required for --sim", file=sys.stderr)
            return 2
        rep = sim_reader(reader, args.artifact, m4b=args.m4b)
        status = "PASS" if rep["ok"] else "FAIL"
        print(f"{status}: {reader} sim @ {args.artifact}")
        for c in rep["checks"]:
            mark = "ok" if c["pass"] else "FAIL"
            print(f"  gate {mark:4} {c['name']}: {c['detail'][:200]}")
        for c in rep.get("sim_checks", []):
            mark = "ok" if c["pass"] else "FAIL"
            print(f"  sim  {mark:4} {c['name']}: {c['detail'][:200]}")
        return 0 if rep["ok"] else 1

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
        allowed, reason = build_allowed(args.build, force=args.force_build)
        if not allowed:
            print(reason, file=sys.stderr)
            return 2
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
            force=args.force_build,
        )
        print(f"Built: {path}")
        rep = gate_reader(args.build, path, m4b=args.m4b)
        print("Gate:", "PASS" if rep["ok"] else "FAIL")
        return 0 if rep["ok"] else 1

    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
