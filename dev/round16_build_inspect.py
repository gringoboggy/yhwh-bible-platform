#!/usr/bin/env python3
"""Round-16 WIN build-inspect harness — build the full catalog, scan every artifact.

FINDINGS-ONLY (rounds 14/15 pattern): builds each distinct (edition × base-target)
artifact + the Kindle post-process + the two standalones in a RAM-safe staging ladder
(lightest→heaviest; the ethiopian-tewahedo eink flagship LAST and SOLO), scanning each
with the round-16 gate suite, **build → scan → free**. Results stream to one JSON after
EVERY asset so an OOM mid-run loses at most the in-flight build.

Staging ladder (one build at a time; never build‖build, never build‖pytest):
  1-4  everywhere base (+ derived Kindle asset)  — cath, evan, east, ethi
  5-8  tablet base (Apple)                        — cath, evan, east, ethi
  9-11 eink base (+ kepub)                        — cath, evan, east   (filtered)
  12   eink base (+ kepub)  FLAGSHIP, SOLO        — ethiopian-tewahedo (RAM ceiling)
  13-14 standalone                                — geez, amharic

Per asset the scan suite runs (as isolated subprocesses; the new + reused gates):
  epubcheck --require --strict · audit_idmap_frags (G3) · audit_badge_conservation (G4)
  · audit_canonical_order (G6) · audit_output_hygiene (R16 hygiene; covers built-output
  nested-<a>) · [eink only] audit_glossary_contract (G5) + verify_kr2_build (kobo).
(check_nested_anchors scans loose epub_working/*.html, not a built zip — built-output
nested-<a> is covered by audit_output_hygiene family A, so it is not re-run per asset.)

Usage:
  py -3 dev/round16_build_inspect.py --version 0.1.0 --out build/r16 \
      [--only EDITION:TARGET] [--skip-flagship] [--skip-standalones] \
      [--min-commit-gb 8] [--results build/r16/round16-harness-results.json]
Exit 0 = every asset built + every gate green; 1 = any build fail or gate FAIL.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Gate subprocesses that import scripts.* (audit_canonical_order, audit_glossary_contract)
# need the repo root on PYTHONPATH — running `python dev/foo.py` puts dev/ on sys.path[0],
# not the repo root (memory reference_pytest_basetemp). UTF-8 for the Geʽez/Ethiopic output.
_GATE_ENV = {**os.environ, "PYTHONPATH": str(REPO_ROOT), "PYTHONUTF8": "1"}

# Catalog order: filtered study editions first, the 87-book flagship LAST.
EDITIONS = ["catholic-study", "evangelical-reformed", "eastern-orthodox", "ethiopian-tewahedo"]
FLAGSHIP = "ethiopian-tewahedo"
STANDALONES = ["standalone-geez", "standalone-amharic"]


def _commit_free_gb() -> float:
    """Windows COMMIT headroom (the binding constraint for the flagship build —
    memory reference-hardware-box-and-mac / the round-14 AppXSvc leak incident)."""
    try:
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        m = MEMORYSTATUSEX()
        m.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        return m.ullAvailPageFile / (1024**3)
    except Exception:
        return float("inf")  # non-Windows / unknown → don't block


def _run(cmd: list[str], json_out: Path | None = None) -> dict:
    """Run a gate subprocess; return {exit, tail, json?}. Never raises."""
    try:
        p = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=1800,
            env=_GATE_ENV,
        )
        out = (p.stdout or "") + (p.stderr or "")
        rec: dict = {"exit": p.returncode, "tail": out.strip().splitlines()[-6:]}
    except subprocess.TimeoutExpired:
        rec = {"exit": 124, "tail": ["TIMEOUT (1800s)"]}
    if json_out and json_out.is_file():
        with contextlib.suppress(Exception):
            rec["json"] = json.loads(json_out.read_text(encoding="utf-8"))
    return rec


def _gate(name: str, args: list[str], jdir: Path, tag: str) -> tuple[str, dict]:
    jout = jdir / f"{tag}.{name}.json"
    cmd = [sys.executable, str(REPO_ROOT / "dev" / f"{name}.py"), *args]
    if name == "epubcheck":
        cmd = [sys.executable, str(REPO_ROOT / "scripts" / "epubcheck.py"), *args]
    return name, _run(cmd, jout if "--json" in args else None)


def scan_asset(asset: Path, jdir: Path, *, is_eink: bool, tag: str) -> dict:
    """Run the round-16 scan suite over one built asset; return per-gate results."""
    jdir.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict] = {}

    # zip integrity first (cheap, catches a truncated/corrupt build)
    try:
        with zipfile.ZipFile(asset) as z:
            bad = z.testzip()
        results["zip"] = {"exit": 1 if bad else 0, "tail": [f"bad member: {bad}"] if bad else ["ok"]}
    except Exception as e:
        results["zip"] = {"exit": 1, "tail": [f"open failed: {e}"]}
        return results  # a broken zip → skip the rest

    name, rec = (
        "epubcheck",
        _run([sys.executable, str(REPO_ROOT / "scripts" / "epubcheck.py"), "--require", "--strict", str(asset)]),
    )
    results[name] = rec
    hygiene_args = [str(asset), "--json", str(jdir / f"{tag}.audit_output_hygiene.json")]
    if is_eink:
        hygiene_args.append("--eink")  # mid-chapter spine breaks are a real defect only on eink
    for name, gate_args in [
        ("audit_idmap_frags", [str(asset), "--json", str(jdir / f"{tag}.audit_idmap_frags.json")]),
        ("audit_badge_conservation", [str(asset), "--json", str(jdir / f"{tag}.audit_badge_conservation.json")]),
        ("audit_canonical_order", [str(asset), "--json", str(jdir / f"{tag}.audit_canonical_order.json")]),
        ("audit_output_hygiene", hygiene_args),
    ]:
        _, results[name] = _gate(name, gate_args, jdir, tag)
    if is_eink:
        _, results["audit_glossary_contract"] = _gate(
            "audit_glossary_contract",
            [str(asset), "--json", str(jdir / f"{tag}.audit_glossary_contract.json")],
            jdir,
            tag,
        )
        results["verify_kr2_build"] = _run([sys.executable, str(REPO_ROOT / "dev" / "verify_kr2_build.py"), str(asset)])
    return results


def _build_base(edition: str, target: str, version: str, work: Path) -> Path:
    from scripts.build_format_matrix import _build_base as bfm_build_base

    return bfm_build_base(edition, version, target, work)


def _asset_record(edition: str, target: str, fmt: str, asset: Path, jdir: Path, *, is_eink: bool) -> dict:
    tag = f"{edition}__{fmt}"
    scans = scan_asset(asset, jdir, is_eink=is_eink, tag=tag)
    fails = [g for g, r in scans.items() if r.get("exit", 0) != 0]
    return {
        "edition": edition,
        "target": target,
        "format": fmt,
        "asset": asset.name,
        "size": asset.stat().st_size if asset.is_file() else 0,
        "gate_fails": fails,
        "scans": scans,
    }


def run_job(edition: str, target: str, version: str, out: Path, jdir: Path) -> list[dict]:
    """Build one (edition, target) and its derivatives; scan each; free the work tree."""
    work = out / f"_work_{edition}_{target}"
    records: list[dict] = []
    try:
        base = _build_base(edition, target, version, work)
        if target == "eink":
            from scripts.build_format_matrix import _apply_kepubify

            records.append(_asset_record(edition, target, "eink-epub", base, jdir, is_eink=True))
            kepub = work / f"{edition}.kepub.epub"
            _apply_kepubify(base, kepub)
            records.append(_asset_record(edition, target, "kobo-kepub", kepub, jdir, is_eink=True))
        elif target == "everywhere":
            records.append(_asset_record(edition, target, "everywhere", base, jdir, is_eink=False))
            from scripts.build_format_matrix import _apply_kindle_post

            kindle = work / f"{edition}.kindle.epub"
            shutil.copyfile(base, kindle)
            _apply_kindle_post(edition, {"id": "kindle"}, kindle)
            records.append(_asset_record(edition, target, "kindle", kindle, jdir, is_eink=False))
        else:  # tablet (Apple)
            records.append(_asset_record(edition, target, "apple-tablet", base, jdir, is_eink=False))
    except Exception as e:
        records.append(
            {
                "edition": edition,
                "target": target,
                "format": target,
                "asset": None,
                "build_error": repr(e),
                "gate_fails": ["BUILD"],
            }
        )
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return records


def run_standalone(edition: str, version: str, out: Path, jdir: Path) -> list[dict]:
    from scripts.build_standalone import build_standalone

    work = out / f"_work_{edition}"
    work.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    try:
        res = build_standalone(edition, work, version)
        epubs = sorted(work.glob("*.epub"))
        if res.get("status") == "error" or not epubs:
            records.append(
                {
                    "edition": edition,
                    "target": "standalone",
                    "format": "standalone",
                    "asset": None,
                    "build_error": res.get("message", "no epub"),
                    "gate_fails": ["BUILD"],
                }
            )
        else:
            records.append(_asset_record(edition, "standalone", "standalone", epubs[-1], jdir, is_eink=False))
    except Exception as e:
        records.append(
            {
                "edition": edition,
                "target": "standalone",
                "format": "standalone",
                "asset": None,
                "build_error": repr(e),
                "gate_fails": ["BUILD"],
            }
        )
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return records


def _ladder(skip_flagship: bool, skip_standalones: bool, only: str | None) -> list[tuple[str, str]]:
    if only:
        ed, _, tgt = only.partition(":")
        return [(ed, tgt or "everywhere")]
    jobs: list[tuple[str, str]] = []
    for tgt in ("everywhere", "tablet"):
        jobs += [(ed, tgt) for ed in EDITIONS]
    jobs += [(ed, "eink") for ed in EDITIONS if ed != FLAGSHIP]
    if not skip_flagship:
        jobs.append((FLAGSHIP, "eink"))  # LAST + SOLO (RAM ceiling)
    if not skip_standalones:
        jobs += [(ed, "standalone") for ed in STANDALONES]
    return jobs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Round-16 full-catalog build-inspect harness.")
    ap.add_argument("--version", default="0.1.0")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "build" / "r16")
    ap.add_argument("--only", help="run a single EDITION:TARGET job (e.g. catholic-study:everywhere)")
    ap.add_argument("--skip-flagship", action="store_true", help="skip the ethiopian-tewahedo eink (RAM ceiling)")
    ap.add_argument("--skip-standalones", action="store_true")
    ap.add_argument(
        "--min-commit-gb", type=float, default=8.0, help="abort the flagship if COMMIT headroom is below this"
    )
    ap.add_argument("--results", type=Path, default=None)
    args = ap.parse_args(argv)

    version = args.version.removeprefix("v")
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    jdir = out / "scans"
    results_path = args.results or (out / "round16-harness-results.json")

    jobs = _ladder(args.skip_flagship, args.skip_standalones, args.only)
    all_records: list[dict] = []
    print(f"[r16-harness] {len(jobs)} job(s); results → {results_path}", flush=True)
    for i, (edition, target) in enumerate(jobs, 1):
        if edition == FLAGSHIP and target == "eink":
            free = _commit_free_gb()
            print(f"[r16-harness] flagship pre-flight: CommitFree={free:.1f}GB (min {args.min_commit_gb})", flush=True)
            if free < args.min_commit_gb:
                all_records.append(
                    {
                        "edition": edition,
                        "target": target,
                        "format": "eink",
                        "asset": None,
                        "build_error": f"ABORTED: CommitFree {free:.1f}GB < {args.min_commit_gb}GB",
                        "gate_fails": ["RAM-PREFLIGHT"],
                    }
                )
                results_path.write_text(json.dumps(all_records, indent=1), encoding="utf-8")
                print("[r16-harness] flagship skipped (low COMMIT) — rerun on a fresh session", flush=True)
                continue
        print(f"[r16-harness] ({i}/{len(jobs)}) build+scan {edition} {target}", flush=True)
        recs = (
            run_standalone(edition, version, out, jdir)
            if target == "standalone"
            else run_job(edition, target, version, out, jdir)
        )
        all_records.extend(recs)
        results_path.write_text(json.dumps(all_records, indent=1), encoding="utf-8")  # incremental
        for r in recs:
            fl = r.get("gate_fails") or []
            print(f"    {r.get('format')}: {r.get('asset')} → {'FAIL ' + ','.join(fl) if fl else 'clean'}", flush=True)

    bad = [r for r in all_records if r.get("gate_fails")]
    print(
        f"\n[r16-harness] DONE: {len(all_records) - len(bad)}/{len(all_records)} asset(s) clean; "
        f"{len(bad)} with gate FAIL/build error",
        flush=True,
    )
    print(f"[r16-harness] results: {results_path}", flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
