#!/usr/bin/env python3
"""lane_watch.py — poll for cross-lane git pushes and incoming handoff instructions.

Use when a lane is idle or between tasks: keeps checking whether the other lane
(Windows) pushed new commits or updated ``dev/LANE_HANDOFF.md`` with work for
this box. Complements ``lane_ping.py`` (BEHIND radar) and ``lane_handoff.py
incoming`` (turn>last-seen banner).

Each cycle:
  1. ``git fetch`` origin + github (refs only)
  2. ``lane_ping.gather()`` — detect BEHIND vs CLEAR
  3. Optional ``git pull --rebase origin main`` when ``--auto-pull`` and BEHIND
  4. Compare remote vs local LANE_HANDOFF frontmatter (turn / from / windows task)
  5. ``lane_handoff incoming`` when local board may have new instructions

Usage:
  .venv/bin/python scripts/lane_watch.py                 # loop every 120s until Ctrl+C
  .venv/bin/python scripts/lane_watch.py --interval 60   # faster poll
  .venv/bin/python scripts/lane_watch.py --once          # single check, then exit
  .venv/bin/python scripts/lane_watch.py --once --auto-pull
  .venv/bin/python scripts/lane_watch.py --json          # machine-readable one-shot

Exit codes (--once):
  0 = CLEAR, no new incoming handoff for this lane
  2 = OFFLINE (fetch/ping unreachable — non-fatal)
  10 = BEHIND (other lane pushed; pull recommended)
  20 = INCOMING handoff addressed to this lane (turn > last-seen)
  30 = BEHIND + INCOMING (both actionable)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
REMOTES = ("origin", "github")


def _git(*args: str, timeout: int = 30) -> tuple[int, str, str]:
    try:
        p = subprocess.run(
            ["git", "-C", str(REPO), *args],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except (OSError, subprocess.SubprocessError) as e:
        return 1, "", str(e)


def _fetch() -> bool:
    ok = True
    for remote in REMOTES:
        rc, _, _ = _git("fetch", remote, "--quiet", "--prune")
        ok = ok and rc == 0
    return ok


def _auto_pull() -> tuple[bool, str]:
    rc, out, err = _git("pull", "--rebase", "origin", "main", timeout=120)
    msg = out or err or ("ok" if rc == 0 else "pull failed")
    return rc == 0, msg


def _remote_handoff_header() -> dict[str, str]:
    """Read LANE_HANDOFF frontmatter from origin/main without checking out."""
    rc, out, _ = _git("show", "origin/main:dev/LANE_HANDOFF.md", timeout=15)
    if rc != 0 or not out.startswith("---"):
        return {}
    header: dict[str, str] = {}
    for line in out.splitlines()[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            k, v = line.split(":", 1)
            header[k.strip()] = v.strip()
    return header


def _local_handoff_header() -> dict[str, str]:
    path = REPO / "dev" / "LANE_HANDOFF.md"
    if not path.is_file():
        return {}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    header: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            k, v = line.split(":", 1)
            header[k.strip()] = v.strip()
    return header


def _int_turn(header: dict[str, str]) -> int:
    try:
        return int(header.get("turn", "0"))
    except ValueError:
        return 0


def _incoming_check() -> tuple[int, str]:
    """Run lane_handoff incoming; return (exit_code, stdout)."""
    try:
        p = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "lane_handoff.py"), "incoming"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            cwd=str(REPO),
            timeout=15,
        )
        return p.returncode, (p.stdout or "").strip()
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e)


def check(*, auto_pull: bool = False) -> dict:
    from scripts import lane_handoff as lh
    from scripts import lane_ping as lp

    fetch_ok = _fetch()
    ping = lp.gather()
    status = ping["status"]
    pulled = False
    pull_msg = ""

    if auto_pull and status == "BEHIND":
        pulled, pull_msg = _auto_pull()
        if pulled:
            ping = lp.gather()
            status = ping["status"]

    local_h = _local_handoff_header()
    remote_h = _remote_handoff_header() if fetch_ok else {}
    local_turn = _int_turn(local_h)
    remote_turn = _int_turn(remote_h)
    remote_ahead = fetch_ok and remote_turn > local_turn

    incoming_rc, incoming_out = _incoming_check()
    incoming = incoming_rc == 0

    lane = lh.detect_lane(REPO)
    return {
        "fetch_ok": fetch_ok,
        "lane": lane,
        "ping_status": status,
        "behind": status == "BEHIND",
        "offline": status == "OFFLINE",
        "auto_pulled": pulled,
        "pull_msg": pull_msg,
        "local_turn": local_turn,
        "remote_turn": remote_turn,
        "remote_ahead": remote_ahead,
        "remote_from": remote_h.get("from", ""),
        "remote_windows": remote_h.get("windows", ""),
        "remote_mac": remote_h.get("mac", ""),
        "incoming": incoming,
        "incoming_banner": incoming_out,
        "baton": ping.get("baton", {}),
    }


def _exit_code(info: dict) -> int:
    if info["offline"] and not info["fetch_ok"]:
        return 2
    behind = info["behind"] or info["remote_ahead"]
    incoming = info["incoming"]
    if behind and incoming:
        return 30
    if behind:
        return 10
    if incoming:
        return 20
    return 0


def _print_human(info: dict) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[lane_watch {ts}] lane={info['lane']} ping={info['ping_status']}", flush=True)
    if info["auto_pulled"]:
        print(f"  auto-pull: {info['pull_msg']}", flush=True)
    if info["remote_ahead"]:
        print(
            f"  remote board turn {info['remote_turn']} > local {info['local_turn']} "
            f"(from {info['remote_from'] or '?'}) — pull to read new instructions",
            flush=True,
        )
        if info["remote_windows"]:
            print(f"  windows task (remote): {info['remote_windows']}", flush=True)
        if info["remote_mac"]:
            print(f"  mac task (remote): {info['remote_mac']}", flush=True)
    if info["behind"]:
        print("  BEHIND — other lane pushed; run: git pull --rebase origin main", flush=True)
    if info["incoming"] and info["incoming_banner"]:
        print(info["incoming_banner"], flush=True)
    if not info["behind"] and not info["remote_ahead"] and not info["incoming"]:
        print("  no new pushes or incoming handoffs", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Poll for cross-lane pushes and incoming handoffs.")
    ap.add_argument("--interval", type=float, default=120.0, help="seconds between polls (default 120)")
    ap.add_argument("--once", action="store_true", help="single check then exit")
    ap.add_argument("--auto-pull", action="store_true", help="git pull --rebase origin main when BEHIND")
    ap.add_argument("--json", action="store_true", help="machine-readable output (implies --once)")
    args = ap.parse_args()

    if args.json:
        args.once = True

    def _cycle() -> int:
        info = check(auto_pull=args.auto_pull)
        if args.json:
            print(json.dumps(info, indent=2))
        else:
            _print_human(info)
        return _exit_code(info)

    if args.once:
        return _cycle()

    print(
        f"lane_watch: polling every {args.interval:.0f}s (Ctrl+C to stop). "
        f"auto_pull={'on' if args.auto_pull else 'off'}",
        flush=True,
    )
    try:
        while True:
            rc = _cycle()
            if rc != 0:
                print(f"  actionable exit hint: {rc} (10=behind, 20=incoming, 30=both)", flush=True)
            time.sleep(max(5.0, args.interval))
    except KeyboardInterrupt:
        print("\nlane_watch stopped", flush=True)
        return 0


if __name__ == "__main__":
    sys.exit(main())
