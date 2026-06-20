#!/usr/bin/env python3
"""Anti-idle radar — never wait for user input; always surface the next work item.

"YOU ALREADY HAVE ALL THE ANSWERS" — dig deep into the project's folders, rules,
backlogs, plans, REPO_MAP, SESSION_PLAYBOOK, STANDING sections, and specs before
ever considering asking the user. The project is built to be self-contained so
work can continue autonomously even while the maintainer is away.

The agent (WIN or Mac) must NEVER end a turn idle. If blocked on user input
(or tempted to ask a question), pick a disjoint backlog item instead. This script:

  1. Records activity heartbeats (``--ping``).
  2. Scores repo signals (pytest reds, unpushed commits, stale audit, sim gaps).
  3. Merges auto-discovered work with ``dev/AGENT_WORK_BACKLOG.md``.
  4. Prints the highest-priority next tasks (``--next``).

Wrappers:
  WIN: ``pwsh -File dev/agent_idle_radar.ps1 [-LoopSec 120] [-Background]``
  Mac: ``bash dev/agent_idle_radar_mac.sh [--bg|--once]``

State: ``dev/.agent_activity.json`` (gitignored). Log: ``dev/.agent_idle_radar.log``.

Also runs **strategic replan pings** (``--replan`` / ``--replan-done``): periodic big
step-back to re-read PLAN + backlog + release gate and reorder work for optimal
efficiency — without ever going idle afterward.

Exit codes (--check): 0 active/recent · 10 IDLE (no ping in ``--stale-sec``) · 20 work queued.
  · 30 REPLAN DUE (--replan when triggers fire).
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
BACKLOG = REPO / "dev" / "AGENT_WORK_BACKLOG.md"
REPLAN_CHECKLIST = REPO / "dev" / "STRATEGIC_REPLAN_CHECKLIST.md"
PLAN_PATH = REPO / "dev" / "PLAN_2026-05-29-roadmap.md"
RELEASE_PLAN = REPO / "docs" / "superpowers" / "plans" / "2026-06-14-v1.0.0-release-plan.md"
STATE_PATH = REPO / "dev" / ".agent_activity.json"
LOG_PATH = REPO / "dev" / ".agent_idle_radar.log"
DEFAULT_STALE_SEC = 180
REPLAN_COMMIT_THRESHOLD = 15
REPLAN_HOURS_THRESHOLD = 24


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log(msg: str, *, also_print: bool = True) -> None:
    line = f"[{_now()}] {msg}"
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    if also_print:
        print(line, flush=True)


def _load_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "last_ping": "",
        "pings": 0,
        "last_task": "",
        "last_replan": "",
        "last_replan_commit": "",
        "last_replan_note": "",
    }


def _save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _git(*args: str, timeout: int = 30) -> tuple[int, str]:
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


def _lane() -> str:
    lane_file = REPO / "dev" / ".lane"
    if lane_file.is_file():
        v = lane_file.read_text(encoding="utf-8").strip().lower()
        if v in ("windows", "mac"):
            return v
    return "windows"


def _parse_backlog_items() -> list[tuple[int, str, str]]:
    """Return (priority, lane_tag, text) from unchecked ``- [ ]`` lines."""
    if not BACKLOG.is_file():
        return []
    items: list[tuple[int, str, str]] = []
    section_pri = 50
    for line in BACKLOG.read_text(encoding="utf-8").splitlines():
        if line.startswith("## P"):
            m = re.match(r"## P(\d+)", line)
            if m:
                section_pri = int(m.group(1))
        if line.startswith("- [ ]"):
            text = line[5:].strip()
            lane = "both"
            if text.upper().startswith("WIN:"):
                lane = "windows"
                text = text[4:].strip()
            elif text.upper().startswith("MAC:"):
                lane = "mac"
                text = text[4:].strip()
            items.append((section_pri, lane, text))
    return items


def _parse_iso(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _replan_triggers(state: dict) -> list[str]:
    """Return human-readable reasons strategic replan is due."""
    reasons: list[str] = []
    last_replan = _parse_iso(state.get("last_replan", ""))
    if last_replan is None:
        reasons.append("never replanned since radar installed")
    else:
        hours = (datetime.now(timezone.utc) - last_replan).total_seconds() / 3600
        if hours >= REPLAN_HOURS_THRESHOLD:
            reasons.append(f"{int(hours)}h since last replan (threshold {REPLAN_HOURS_THRESHOLD}h)")

    anchor = state.get("last_replan_commit", "")
    if not anchor:
        code, head = _git("rev-parse", "HEAD")
        if code == 0:
            code2, n = _git("rev-list", "--count", head)
            if code2 == 0 and n.isdigit() and int(n) >= REPLAN_COMMIT_THRESHOLD:
                reasons.append(f"{n} total commits (no replan anchor yet)")
    else:
        code, count = _git("rev-list", "--count", f"{anchor}..HEAD")
        if code == 0 and count.isdigit() and int(count) >= REPLAN_COMMIT_THRESHOLD:
            reasons.append(f"{count} commits since last replan (threshold {REPLAN_COMMIT_THRESHOLD})")

    replan_ts = last_replan.timestamp() if last_replan else 0.0
    for label, path in (("PLAN", PLAN_PATH), ("release-plan", RELEASE_PLAN)):
        if path.is_file() and path.stat().st_mtime > replan_ts:
            reasons.append(f"{label} changed since last replan ({path.name})")

    changelog = REPO / "dev" / "CHANGELOG.md"
    if changelog.is_file() and changelog.stat().st_mtime > replan_ts and len(reasons) < 2:
        # Nudge when changelog moved but no other trigger yet — scope drift signal.
        code, n = _git("log", "-5", "--oneline")
        if code == 0 and n.count("\n") >= 4:
            reasons.append("5 recent ships — verify backlog ordering still optimal")

    return reasons


def _replan_due(state: dict | None = None) -> tuple[bool, list[str]]:
    state = state if state is not None else _load_state()
    reasons = _replan_triggers(state)
    return bool(reasons), reasons


def _auto_signals() -> list[tuple[int, str, str]]:
    """Repo-derived work items. Lower priority number = higher urgency."""
    lane = _lane()
    out: list[tuple[int, str, str]] = []
    state = _load_state()
    due, replan_reasons = _replan_due(state)
    if due:
        summary = "; ".join(replan_reasons[:2])
        out.append((3, "both", f"STRATEGIC REPLAN due ({summary}) — run --replan then --replan-done"))

    code, status = _git("status", "-b", "--porcelain")
    if code == 0 and status:
        first = status.splitlines()[0]
        if "ahead" in first:
            m = re.search(r"ahead (\d+)", first)
            n = m.group(1) if m else "?"
            out.append((5, lane, f"Milestone save: {n} unpushed commit(s) — run save-all.ps1 / save_mac.sh"))
        dirty = [ln for ln in status.splitlines()[1:] if ln.strip()]
        if dirty:
            out.append((8, lane, f"Commit WIP: {len(dirty)} unstaged/staged path(s)"))

    code, log = _git("log", "-1", "--format=%ct", "dev/archive")
    if code == 0 and log.isdigit():
        last_audit = int(log)
        code2, head_ct = _git("log", "-1", "--format=%ct")
        if code2 == 0 and head_ct.isdigit():
            commits_since = 0
            code3, count = _git("rev-list", "--count", f"{last_audit}..HEAD")
            if code3 == 0 and count.isdigit():
                commits_since = int(count)
            if commits_since >= 25:
                out.append((15, "both", f"DEEP audit due: {commits_since} commits since last dev/archive audit"))

    if lane == "windows":
        out.append((10, "windows", "pytest --lf triage → drive ci.py GREEN"))
        out.append((12, "windows", "Kobo reader-sim: verify_kr2 + gate-only --sim kobo (skip 40MB epubcheck hang)"))
        out.append((14, "windows", "rx-surfaces tail after pytest cluster green"))
        staging = REPO / "dev" / "reader_sim" / "STAGING_MANIFEST.md"
        if staging.is_file() and "SIM_LAYERS_READY" in staging.read_text(encoding="utf-8"):
            if '"kobo": false' in staging.read_text(encoding="utf-8") or "kobo: false" in staging.read_text(
                encoding="utf-8"
            ):
                out.append((13, "windows", "Flip kobo SIM_LAYERS_READY after K-R2 + tap calibration"))
    else:
        out.append((10, "mac", "STK live poll: kindle_library Lassen + stk_channel.sh"))
        out.append((11, "mac", "Reader-sim --sim apple + thorium CDP taps"))
        out.append((12, "mac", "Esther Patrologia transcription: extract_patrologia_pdf --book est (side lane)"))

    dist = REPO / "website" / "dist" / "index.html"
    catalog = REPO / "scripts" / "gen_release_catalog.py"
    if catalog.is_file():
        cat_mtime = catalog.stat().st_mtime
        if not dist.is_file() or dist.stat().st_mtime < cat_mtime:
            out.append((18, "both", "Regen website/dist: gen_release_catalog + node website/build.mjs"))

    return out


def _merged_tasks(lane: str) -> list[tuple[int, str, str]]:
    tasks = _auto_signals()
    for pri, task_lane, text in _parse_backlog_items():
        if task_lane in ("both", lane):
            tasks.append((pri, task_lane, text))
    tasks.sort(key=lambda t: (t[0], t[2]))
    seen: set[str] = set()
    deduped: list[tuple[int, str, str]] = []
    for item in tasks:
        if item[2] not in seen:
            seen.add(item[2])
            deduped.append(item)
    return deduped


def cmd_replan() -> int:
    state = _load_state()
    due, reasons = _replan_due(state)
    _log("STRATEGIC REPLAN ping" + (" — DUE" if due else " — not due yet"))
    if due:
        for r in reasons:
            print(f"  ! {r}")
    else:
        print("  (no triggers — continue execution; replan again when --next shows P03 replan)")
    print("")
    print("  Checklist: dev/STRATEGIC_REPLAN_CHECKLIST.md")
    if REPLAN_CHECKLIST.is_file():
        for line in REPLAN_CHECKLIST.read_text(encoding="utf-8").splitlines():
            if line.startswith("- [ ]") or line.startswith("## "):
                print(f"  {line}")
    print("")
    print('  After replan: py -3 scripts/agent_idle_radar.py --replan-done --note "…"')
    print("  Then immediately: py -3 scripts/agent_idle_radar.py --next")
    return 30 if due else 0


def cmd_replan_done(note: str = "") -> int:
    state = _load_state()
    state["last_replan"] = _now()
    code, head = _git("rev-parse", "HEAD")
    if code == 0:
        state["last_replan_commit"] = head
    if note:
        state["last_replan_note"] = note
    _save_state(state)
    _log(f"STRATEGIC REPLAN marked done{f': {note}' if note else ''}")
    return 0


def cmd_ping(note: str = "") -> int:
    state = _load_state()
    state["last_ping"] = _now()
    state["pings"] = int(state.get("pings", 0)) + 1
    if note:
        state["last_task"] = note
    _save_state(state)
    return 0


def cmd_next(n: int = 3, lane: str | None = None) -> int:
    lane = lane or _lane()
    tasks = _merged_tasks(lane)
    if not tasks:
        _log(f"IDLE-RADAR [{lane}]: backlog empty — add items to dev/AGENT_WORK_BACKLOG.md")
        return 20
    _log(f"IDLE-RADAR [{lane}]: next {min(n, len(tasks))} task(s)")
    for pri, task_lane, text in tasks[:n]:
        print(f"  P{pri:02d} [{task_lane}] {text}")
    return 0


def cmd_check(stale_sec: int) -> int:
    state = _load_state()
    last = state.get("last_ping", "")
    if not last:
        _log("IDLE-RADAR: no heartbeat yet — agent should --ping and pick work from --next")
        return 10
    try:
        then = datetime.strptime(last, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - then).total_seconds()
    except ValueError:
        return 10
    if age > stale_sec:
        _log(f"IDLE-RADAR: STALE {int(age)}s > {stale_sec}s — surfacing next work")
        cmd_next()
        return 10
    return 0


def cmd_loop(interval: int) -> int:
    _log(f"IDLE-RADAR: loop every {interval}s (Ctrl+C to stop)")
    try:
        while True:
            due, reasons = _replan_due()
            if due:
                _log("STRATEGIC REPLAN DUE: " + "; ".join(reasons[:2]))
                cmd_replan()
            if cmd_check(DEFAULT_STALE_SEC) == 10:
                pass
            time.sleep(interval)
    except KeyboardInterrupt:
        return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Anti-idle work radar for YHWH lanes")
    p.add_argument("--ping", action="store_true", help="record agent heartbeat")
    p.add_argument("--note", default="", help="optional task note with --ping")
    p.add_argument("--next", action="store_true", help="print next work items")
    p.add_argument("-n", type=int, default=3, help="how many tasks for --next")
    p.add_argument("--check", action="store_true", help="exit 10 if stale")
    p.add_argument("--stale-sec", type=int, default=DEFAULT_STALE_SEC)
    p.add_argument("--loop", type=int, metavar="SEC", help="background stale checker")
    p.add_argument("--lane", choices=("windows", "mac"), help="override lane detection")
    p.add_argument("--replan", action="store_true", help="strategic step-back replan ping")
    p.add_argument("--replan-done", action="store_true", help="mark replan complete")
    args = p.parse_args(argv)

    if args.replan_done:
        return cmd_replan_done(args.note)
    if args.replan:
        return cmd_replan()
    if args.ping:
        return cmd_ping(args.note)
    if args.next:
        return cmd_next(args.n, args.lane)
    if args.check:
        return cmd_check(args.stale_sec)
    if args.loop:
        return cmd_loop(args.loop)
    return cmd_next(args.n, args.lane)


if __name__ == "__main__":
    raise SystemExit(main())
