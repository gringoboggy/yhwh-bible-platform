#!/usr/bin/env python3
"""lane_watcher.py — poll for the other lane's pushes and react automatically.

WHY: overnight / long sessions need WIN to notice when Mac (or vice versa) has
pushed, pull immediately, and queue the next assignment without a human saying
"pull".  Complements ``lane_ping.py`` (cheap radar) with an optional loop that
also syncs and updates ``dev/LANE_HANDOFF.md``.

Usage (Windows lane, from repo root)::

    py -3 scripts/lane_watcher.py --once          # one check; pull if BEHIND
    py -3 scripts/lane_watcher.py --loop 120      # poll every 120s (background OK)
    py -3 scripts/lane_watcher.py --loop 120 --assign-mac

``--assign-mac`` (WIN only): after pulling a Mac push, bump the board with the
next Mac task from ``dev/MAC_WORK_QUEUE.md`` (first unchecked line).

State: ``dev/.lane_watcher_state.json`` (gitignored via dev/.lane* pattern).
Log:   ``dev/.lane_watcher.log`` (append-only).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STATE_PATH = REPO / "dev" / ".lane_watcher_state.json"
LOG_PATH = REPO / "dev" / ".lane_watcher.log"
QUEUE_PATH = REPO / "dev" / "MAC_WORK_QUEUE.md"


def _log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}\n"
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line)
    print(line.rstrip())


def _git(*args: str, timeout: int = 120) -> tuple[int, str, str]:
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


def _py(*args: str) -> tuple[int, str, str]:
    try:
        p = subprocess.run(
            [sys.executable, *args],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(REPO),
        )
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except (OSError, subprocess.SubprocessError) as e:
        return 1, "", str(e)


def _load_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"last_remote_tip": "", "last_pull_at": "", "polls": 0}


def _save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _radar() -> dict:
    rc, out, err = _py(str(REPO / "scripts" / "lane_ping.py"), "--json")
    if rc != 0 or not out:
        return {"status": "OFFLINE", "error": err or out}
    return json.loads(out)


def _detect_lane() -> str:
    rc, out, _ = _py(str(REPO / "scripts" / "lane_handoff.py"), "status")
    m = re.search(r"lane=(\w+)", out)
    return m.group(1) if m else "windows"


def _other_lane(lane: str) -> str:
    return "mac" if lane == "windows" else "windows"


def _sync_if_behind() -> tuple[bool, str]:
    """Fetch + pull --rebase when BEHIND. Returns (did_pull, summary)."""
    _git("fetch", "origin", timeout=60)
    _git("fetch", "github", timeout=60)
    info = _radar()
    status = info.get("status", "OFFLINE")
    if status != "BEHIND":
        tip = ""
        for r in ("origin", "github"):
            d = info.get("remotes", {}).get(r, {})
            if d.get("remote_tip"):
                tip = d["remote_tip"]
                break
        return False, f"status={status} tip={tip[:7] if tip else '?'}"
    rc, out, err = _git("pull", "--rebase", "origin", "main", timeout=300)
    if rc != 0:
        return False, f"pull FAILED rc={rc}: {err or out}"
    _, head, _ = _git("rev-parse", "HEAD")
    return True, f"pulled -> {head[:7]}"


def _changelog_headline() -> str:
    p = REPO / "dev" / "CHANGELOG.md"
    if not p.is_file():
        return ""
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("## "):
            return line[3:].strip()
    return ""


def _baton_from() -> str:
    p = REPO / "dev" / "LANE_HANDOFF.md"
    if not p.is_file():
        return ""
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("from:"):
            return line.split(":", 1)[1].strip()
    return ""


def _next_mac_queue_item() -> str | None:
    """First unchecked ``- [ ]`` line in MAC_WORK_QUEUE.md."""
    if not QUEUE_PATH.is_file():
        return None
    for line in QUEUE_PATH.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^- \[ \] (.+)$", line.strip())
        if m:
            return m.group(1).strip()
    return None


def _mark_queue_done(prefix: str) -> bool:
    if not QUEUE_PATH.is_file():
        return False
    lines = QUEUE_PATH.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = False
    out: list[str] = []
    for ln in lines:
        m = re.match(r"^- \[ \] (.+)$", ln.strip())
        if m and not changed and m.group(1).strip().startswith(prefix[:40]):
            out.append(ln.replace("- [ ]", "- [x]", 1))
            changed = True
        else:
            out.append(ln)
    if changed:
        QUEUE_PATH.write_text("".join(out), encoding="utf-8")
    return changed


def _assign_mac(task: str, note: str = "") -> int:
    rc, out, err = _py(
        str(REPO / "scripts" / "lane_handoff.py"),
        "assign",
        "--mac",
        task,
        *(["--note", note] if note else []),
    )
    if rc != 0:
        _log(f"assign FAILED: {err or out}")
    else:
        _log(f"assign mac: {task[:80]}")
    return rc


def _assign_windows(task: str) -> int:
    rc, out, err = _py(
        str(REPO / "scripts" / "lane_handoff.py"),
        "assign",
        "--windows",
        task,
    )
    if rc != 0:
        _log(f"assign windows FAILED: {err or out}")
    else:
        _log(f"assign windows: {task[:80]}")
    return rc


def do_once(*, assign_mac: bool, assign_windows_idle: bool) -> int:
    lane = _detect_lane()
    state = _load_state()
    state["polls"] = state.get("polls", 0) + 1

    info = _radar()
    tip = ""
    for r in ("origin", "github"):
        d = info.get("remotes", {}).get(r, {})
        if d.get("remote_tip"):
            tip = d["remote_tip"]
            break

    pulled, summary = _sync_if_behind()
    if pulled:
        who = _baton_from() or _other_lane(lane)
        headline = _changelog_headline()
        _log(f"PULL by watcher ({who}): {summary} | CHANGELOG: {headline}")

        if assign_mac and lane == "windows" and who == "mac":
            nxt = _next_mac_queue_item()
            if nxt:
                note = f"Auto-queued by lane_watcher after Mac push ({summary})."
                if _assign_mac(nxt, note=note) == 0:
                    _mark_queue_done(nxt)
            else:
                _log("Mac queue empty — no auto-assign")

        state["last_remote_tip"] = tip
        state["last_pull_at"] = datetime.now(timezone.utc).isoformat()
    else:
        if tip and tip != state.get("last_remote_tip"):
            state["last_remote_tip"] = tip
        if state["polls"] % 10 == 1:
            _log(f"poll ok: {summary}")

    _save_state(state)

    if assign_windows_idle and lane == "windows" and not pulled:
        pass  # idle heartbeat only on pull events

    return 0 if info.get("status") != "OFFLINE" else 2


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Poll lane radar; pull on BEHIND; optional auto-assign.")
    ap.add_argument("--once", action="store_true", help="single poll (default if --loop omitted)")
    ap.add_argument("--loop", type=int, metavar="SECS", help="poll every SECS seconds until interrupted")
    ap.add_argument(
        "--assign-mac",
        action="store_true",
        help="after a Mac push on WIN, assign next item from dev/MAC_WORK_QUEUE.md",
    )
    args = ap.parse_args(argv)

    interval = args.loop
    if interval is None:
        return do_once(assign_mac=args.assign_mac, assign_windows_idle=False)

    _log(f"lane_watcher loop start interval={interval}s assign_mac={args.assign_mac}")
    try:
        while True:
            do_once(assign_mac=args.assign_mac, assign_windows_idle=False)
            time.sleep(interval)
    except KeyboardInterrupt:
        _log("lane_watcher stopped")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
