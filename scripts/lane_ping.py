#!/usr/bin/env python3
"""lane_ping.py — the two-lane sync radar (win <-> mac).

WHY: under the 2026-06-08 bandwidth-first save cadence (RULES s4) each lane
commits LOCALLY and only does the full push at a MAJOR milestone. So before a
lane pulls or pushes it must know whether the OTHER lane has pushed in the
meantime — otherwise a milestone push to the protected GitLab `main` is rejected
(non-fast-forward) or the lanes silently drift.

This is the "ping": a CHEAP remote-tip check. `git ls-remote` returns just the
remote `main` SHA (a few bytes, no object download) — ideal for the ~98%-weekly
bandwidth constraint. We compare it to the locally-cached `<remote>/main` ref:
  remote tip == cached  -> the other lane has NOT pushed since your last fetch  -> CLEAR
  remote tip != cached  -> the other lane PUSHED                               -> BEHIND
The fix for BEHIND is always the same and safe (lanes are file-disjoint):
  git pull --rebase origin main        # replays your unpushed local commits on top
then push. `save-all.ps1` does this automatically before its push legs; the
SessionStart hook runs `--quiet` so each session learns on boot if the other
lane moved. Read-only + non-fatal by design: a network failure never blocks work.

Usage:
  py -3 scripts/lane_ping.py                 # human report (both remotes)
  py -3 scripts/lane_ping.py --quiet         # print ONE line only if action is needed (hook)
  py -3 scripts/lane_ping.py --before-push   # exit 10 if BEHIND (so save-all gates the push)
  py -3 scripts/lane_ping.py --json          # machine-readable

Exit codes: 0 = CLEAR (safe to push) · 10 = BEHIND (pull --rebase first) ·
            2 = OFFLINE / git error (non-fatal — caller decides; hook ignores it).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REMOTES = ("origin", "github")  # origin = GitLab (code home), github = GitHub mirror
REPO = Path(__file__).resolve().parent.parent  # scripts/.. = repo root


def _git(*args: str, timeout: int = 20) -> tuple[int, str]:
    """Run a git command in the repo. stdin=DEVNULL is REQUIRED on Windows
    (pytest/PowerShell subprocess hits WinError 6 otherwise — memory w-w1)."""
    try:
        p = subprocess.run(
            ["git", "-C", str(REPO), *args],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return p.returncode, (p.stdout or "").strip()
    except (OSError, subprocess.SubprocessError):
        return 1, ""


def _ls_remote_main(remote: str) -> str | None:
    """The TRUE remote `main` tip (cheap — refs only, no objects). None if unreachable."""
    rc, out = _git("ls-remote", remote, "refs/heads/main")
    if rc != 0 or not out:
        return None
    return out.split()[0]  # "<sha>\trefs/heads/main"


def _rev(ref: str) -> str | None:
    rc, out = _git("rev-parse", "--verify", "--quiet", ref)
    return out if rc == 0 and out else None


def _count(rng: str) -> int:
    rc, out = _git("rev-list", "--count", rng)
    try:
        return int(out) if rc == 0 and out else 0
    except ValueError:
        return 0


def _baton() -> dict[str, str]:
    """Read who last held the baton from LANE_HANDOFF.md frontmatter (context only)."""
    info: dict[str, str] = {}
    fm = REPO / "dev" / "LANE_HANDOFF.md"
    try:
        lines = fm.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return info
    if not lines or lines[0].strip() != "---":
        return info
    for ln in lines[1:]:
        if ln.strip() == "---":
            break
        if ":" in ln:
            k, _, v = ln.partition(":")
            info[k.strip()] = v.strip()
    return info


def gather() -> dict:
    local_head = _rev("HEAD")
    remotes: dict[str, dict] = {}
    any_behind = False
    any_online = False
    for r in REMOTES:
        remote_tip = _ls_remote_main(r)
        cached = _rev(f"{r}/main")
        online = remote_tip is not None
        any_online = any_online or online
        behind = bool(online and cached is not None and remote_tip != cached)
        any_behind = any_behind or behind
        remotes[r] = {
            "online": online,
            "remote_tip": remote_tip,
            "cached": cached,
            "behind": behind,
        }
    # local commits committed-but-not-yet-pushed (the milestone backlog), vs cached origin/main
    unpushed = _count("origin/main..HEAD") if _rev("origin/main") else 0
    if not any_online:
        status = "OFFLINE"
    elif any_behind:
        status = "BEHIND"
    else:
        status = "CLEAR"
    return {
        "status": status,
        "head": local_head,
        "unpushed": unpushed,
        "remotes": remotes,
        "baton": _baton(),
    }


def _short(sha: str | None) -> str:
    return sha[:7] if sha else "-------"


def main() -> int:
    ap = argparse.ArgumentParser(description="Two-lane sync radar (win <-> mac).")
    ap.add_argument(
        "--quiet", action="store_true", help="print one line only when action is needed (for the SessionStart hook)"
    )
    ap.add_argument("--before-push", action="store_true", help="exit 10 if BEHIND so the saver gates the push")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    a = ap.parse_args()

    info = gather()
    status = info["status"]
    rc = {"CLEAR": 0, "BEHIND": 10, "OFFLINE": 2}[status]

    if a.json:
        print(json.dumps(info, indent=2))
        return rc

    if a.before_push:
        if status == "BEHIND":
            print("lane radar: BEHIND — the other lane pushed. Run `git pull --rebase origin main` before pushing.")
            return 10
        if status == "OFFLINE":
            print("lane radar: OFFLINE — could not reach the remote; proceeding (verify the push lands).")
            return 0  # don't block a milestone save just because the network blipped
        return 0

    if a.quiet:
        if status == "BEHIND":
            who = info["baton"].get("from") or info["baton"].get("holder") or "the other lane"
            print(
                f"⚠ lane radar: {who} has pushed since your last fetch — run `git pull --rebase origin main` before you start (and before any milestone push)."
            )
        # CLEAR / OFFLINE: stay silent in quiet mode
        return rc

    # full human report
    print("Lane radar (origin=GitLab · github=GitHub):")
    for r in REMOTES:
        d = info["remotes"][r]
        if not d["online"]:
            print(f"  {r:<7} OFFLINE — could not reach remote")
        elif d["behind"]:
            print(
                f"  {r:<7} remote {_short(d['remote_tip'])} | you have {_short(d['cached'])}  -> BEHIND (other lane pushed)"
            )
        else:
            print(f"  {r:<7} remote {_short(d['remote_tip'])} | you have {_short(d['cached'])}  -> in sync")
    if info["unpushed"]:
        print(f"  local:  {info['unpushed']} commit(s) committed locally, not yet pushed (sync at your next milestone)")
    b = info["baton"]
    if b:
        print(f"  baton:  holder={b.get('holder', '?')} from={b.get('from', '?')} turn={b.get('turn', '?')}")
    if status == "BEHIND":
        print("STATUS: BEHIND — run `git pull --rebase origin main` before you pull/push.")
    elif status == "OFFLINE":
        print("STATUS: OFFLINE — remote unreachable; cannot confirm the other lane's state.")
    else:
        print("STATUS: CLEAR — safe to pull/push.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
