#!/usr/bin/env python3
"""lane_watch.py — unified cross-lane poll: git pushes + handoff board + incoming work.

One engine for both boxes. Replaces the split ``lane_watcher.py`` / ad-hoc fetch
logic with a single cycle that answers three questions each poll:

  1. Did the other lane **push** new commits?  (``lane_ping`` BEHIND radar)
  2. Is the **remote board** ahead of our local copy?  (``origin/main:LANE_HANDOFF``)
  3. Is there **incoming work** for this box?  (``lane_handoff incoming``)

Handoffs travel **only via git push** — a local board edit the other lane cannot
see is flagged as ``unpushed_handoff`` so the authoring lane knows to milestone-push.

Usage::

    py -3 scripts/lane_watch.py --once --auto-pull
    py -3 scripts/lane_watch.py --loop 120 --auto-pull
    py -3 scripts/lane_watch.py --loop 120 --auto-pull --assign-mac   # WIN only
    py -3 scripts/lane_watch.py --json

Mac wrapper: ``bash dev/lane_watch_mac.sh [--bg|--once]``
WIN wrapper: ``pwsh -File dev/lane_watch_win.ps1 [-LoopSec 120] [-AssignMac]``

Log: ``dev/.lane_watch.log`` (append). State: ``dev/.lane_watch_state.json``.

Exit codes (--once): 0 CLEAR · 2 OFFLINE · 10 BEHIND · 20 INCOMING · 30 BOTH.
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
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
REMOTES = ("origin", "github")
STATE_PATH = REPO / "dev" / ".lane_watch_state.json"
LOG_PATH = REPO / "dev" / ".lane_watch.log"
QUEUE_PATH = REPO / "dev" / "MAC_WORK_QUEUE.md"


def _log(msg: str, *, also_print: bool = True) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    if also_print:
        print(line, flush=True)


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


def _py(*args: str, timeout: int = 60) -> tuple[int, str, str]:
    try:
        p = subprocess.run(
            [sys.executable, *args],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
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
    return {"polls": 0, "last_remote_tip": "", "last_pull_at": "", "last_seen_turn": 0}


def _save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _fetch() -> bool:
    ok = True
    for remote in REMOTES:
        rc, _, _ = _git("fetch", remote, "--quiet", "--prune")
        ok = ok and rc == 0
    return ok


def _auto_pull() -> tuple[bool, str]:
    rc, out, err = _git("pull", "--rebase", "origin", "main", timeout=300)
    msg = out or err or ("ok" if rc == 0 else "pull failed")
    return rc == 0, msg


def _handoff_header_from_text(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    header: dict[str, str] = {}
    for line in text.splitlines()[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            k, v = line.split(":", 1)
            header[k.strip()] = v.strip()
    return header


def _remote_handoff_header() -> dict[str, str]:
    rc, out, _ = _git("show", "origin/main:dev/LANE_HANDOFF.md", timeout=15)
    if rc != 0 or not out:
        return {}
    return _handoff_header_from_text(out)


def _local_handoff_header() -> dict[str, str]:
    path = REPO / "dev" / "LANE_HANDOFF.md"
    if not path.is_file():
        return {}
    return _handoff_header_from_text(path.read_text(encoding="utf-8", errors="replace"))


def _int_turn(header: dict[str, str]) -> int:
    try:
        return int(header.get("turn", "0"))
    except ValueError:
        return 0


def _incoming_check() -> tuple[int, str]:
    rc, out, _ = _py(str(REPO / "scripts" / "lane_handoff.py"), "incoming")
    return rc, out


def _detect_lane() -> str:
    rc, out, _ = _py(str(REPO / "scripts" / "lane_handoff.py"), "status")
    m = re.search(r"lane=(\w+)", out)
    return m.group(1) if m else "windows"


def _changelog_headline() -> str:
    p = REPO / "dev" / "CHANGELOG.md"
    if not p.is_file():
        return ""
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("## "):
            return line[3:].strip()
    return ""


def _next_mac_queue_item() -> str | None:
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
    args = [str(REPO / "scripts" / "lane_handoff.py"), "assign", "--mac", task]
    if note:
        args.extend(["--note", note])
    return _py(*args)[0]


def check(*, auto_pull: bool = False, quiet_log: bool = False) -> dict:
    """One poll cycle. Mutates repo on auto_pull when behind or remote board ahead."""
    from scripts import lane_handoff as lh
    from scripts import lane_ping as lp

    state = _load_state()
    state["polls"] = state.get("polls", 0) + 1

    fetch_ok = _fetch()
    ping = lp.gather()
    status = ping["status"]
    unpushed = ping.get("unpushed", 0)

    local_h = _local_handoff_header()
    remote_h = _remote_handoff_header() if fetch_ok else {}
    local_turn = _int_turn(local_h)
    remote_turn = _int_turn(remote_h)
    remote_ahead = fetch_ok and remote_turn > local_turn
    unpushed_handoff = local_turn > remote_turn and unpushed > 0

    pulled = False
    pull_msg = ""
    should_pull = auto_pull and fetch_ok and (status == "BEHIND" or remote_ahead)
    if should_pull:
        pulled, pull_msg = _auto_pull()
        if pulled:
            ping = lp.gather()
            status = ping["status"]
            local_h = _local_handoff_header()
            local_turn = _int_turn(local_h)
            remote_h = _remote_handoff_header()
            remote_turn = _int_turn(remote_h)
            remote_ahead = remote_turn > local_turn

    incoming_rc, incoming_out = _incoming_check()
    incoming = incoming_rc == 0

    lane = lh.detect_lane(REPO)
    tip = ""
    for r in REMOTES:
        d = ping.get("remotes", {}).get(r, {})
        if d.get("remote_tip"):
            tip = d["remote_tip"]
            break

    info = {
        "fetch_ok": fetch_ok,
        "lane": lane,
        "ping_status": status,
        "behind": status == "BEHIND",
        "offline": status == "OFFLINE",
        "unpushed_commits": unpushed,
        "unpushed_handoff": unpushed_handoff,
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
        "polls": state["polls"],
    }

    if not quiet_log:
        _emit_cycle_log(info, state, tip)

    if pulled:
        state["last_pull_at"] = datetime.now(timezone.utc).isoformat()
        state["last_seen_turn"] = local_turn
    if tip:
        state["last_remote_tip"] = tip
    _save_state(state)

    return info


def _emit_cycle_log(info: dict, state: dict, tip: str) -> None:
    if info["auto_pulled"]:
        who = info["remote_from"] or info["baton"].get("from") or "other lane"
        _log(f"PULL ({who}): {info['pull_msg']} | CHANGELOG: {_changelog_headline()}")
        if info["incoming"] and info["incoming_banner"]:
            for ln in info["incoming_banner"].splitlines():
                _log(ln)
        return

    if info["unpushed_handoff"]:
        _log(
            f"UNPUSHED HANDOFF: local board turn {info['local_turn']} > "
            f"remote {info['remote_turn']} with {info['unpushed_commits']} local commit(s) — "
            "milestone-push so the other lane can see your assignment"
        )

    if info["remote_ahead"] and not info["auto_pulled"]:
        _log(
            f"REMOTE BOARD turn {info['remote_turn']} > local {info['local_turn']} "
            f"(from {info['remote_from'] or '?'}) — run with --auto-pull"
        )
        if info["remote_windows"]:
            _log(f"  windows (remote): {info['remote_windows'][:140]}")
        if info["remote_mac"]:
            _log(f"  mac (remote): {info['remote_mac'][:140]}")

    if info["behind"] and not info["auto_pulled"]:
        _log("BEHIND — other lane pushed; run with --auto-pull or git pull --rebase origin main")

    if info["incoming"] and not info["auto_pulled"] and info["incoming_banner"]:
        for ln in info["incoming_banner"].splitlines():
            _log(ln)

    if (
        not info["behind"]
        and not info["remote_ahead"]
        and not info["incoming"]
        and not info["unpushed_handoff"]
        and info["polls"] % 10 == 1
    ):
        short_tip = tip[:7] if tip else "?"
        _log(f"poll ok: ping={info['ping_status']} tip={short_tip} turn={info['local_turn']} lane={info['lane']}")


def post_pull_actions(info: dict, *, assign_mac: bool) -> None:
    """WIN-only queue assign after pulling a Mac-origin update."""
    if not info.get("auto_pulled"):
        return
    lane = info["lane"]
    who = info.get("remote_from") or info.get("baton", {}).get("from", "")
    if assign_mac and lane == "windows" and who == "mac":
        nxt = _next_mac_queue_item()
        if nxt:
            note = f"Auto-queued by lane_watch after Mac push ({info.get('pull_msg', '')})."
            if _assign_mac(nxt, note=note) == 0:
                _mark_queue_done(nxt)
                _log(f"assign mac: {nxt[:100]}")
        else:
            _log("Mac queue empty — no auto-assign")


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
    if info["unpushed_handoff"]:
        print(
            f"  UNPUSHED HANDOFF: local turn {info['local_turn']} not on remote — push to reach other lane",
            flush=True,
        )
    if info["auto_pulled"]:
        print(f"  auto-pull: {info['pull_msg']}", flush=True)
    if info["remote_ahead"]:
        print(
            f"  remote board turn {info['remote_turn']} > local {info['local_turn']} "
            f"(from {info['remote_from'] or '?'})",
            flush=True,
        )
    if info["behind"]:
        print("  BEHIND — other lane pushed", flush=True)
    if info["incoming"] and info["incoming_banner"]:
        print(info["incoming_banner"], flush=True)
    if not info["behind"] and not info["remote_ahead"] and not info["incoming"]:
        print("  no new pushes or incoming handoffs", flush=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Poll for cross-lane pushes and incoming handoffs.")
    ap.add_argument("--interval", type=float, default=120.0, help="seconds between polls in --loop mode")
    ap.add_argument("--loop", type=float, nargs="?", const=120.0, help="poll loop (default 120s)")
    ap.add_argument("--once", action="store_true", help="single check then exit")
    ap.add_argument("--auto-pull", action="store_true", help="pull --rebase when BEHIND or remote board ahead")
    ap.add_argument(
        "--assign-mac",
        action="store_true",
        help="WIN only: after Mac push pull, assign next dev/MAC_WORK_QUEUE.md item",
    )
    ap.add_argument("--json", action="store_true", help="machine-readable output (implies --once)")
    args = ap.parse_args(argv)

    if args.json:
        args.once = True

    loop_sec = args.loop
    if loop_sec is not None:
        args.once = False

    def _cycle(*, quiet: bool = False) -> int:
        info = check(auto_pull=args.auto_pull, quiet_log=quiet)
        post_pull_actions(info, assign_mac=args.assign_mac)
        if args.json:
            print(json.dumps(info, indent=2))
        elif not quiet:
            _print_human(info)
        return _exit_code(info)

    if args.once or loop_sec is None:
        return _cycle()

    _log(
        f"lane_watch loop start interval={loop_sec:.0f}s auto_pull={args.auto_pull} "
        f"assign_mac={args.assign_mac} lane={_detect_lane()}",
        also_print=True,
    )
    try:
        while True:
            try:
                rc = _cycle(quiet=not args.json)
                if rc != 0 and not args.json:
                    _log(f"actionable: exit {rc} (10=behind 20=incoming 30=both)")
            except Exception as e:
                _log(f"poll ERROR (continuing): {e!r}")
            time.sleep(max(5.0, loop_sec if loop_sec else args.interval))
    except KeyboardInterrupt:
        _log("lane_watch stopped")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
