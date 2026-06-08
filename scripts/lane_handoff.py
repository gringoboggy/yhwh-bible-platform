#!/usr/bin/env python3
"""Lane-coordination core — deterministic engine for the Windows<->Mac two-lane git flow.

v2 (2026-06-08): the committed board ``dev/LANE_HANDOFF.md`` no longer models a
single exclusive "baton holder = sole worker = sole pusher". Under the
bandwidth-first cadence (RULES s4) BOTH lanes commit locally and push at their own
milestones (gated by ``scripts/lane_ping.py``), so the board is a *task assignment*
+ *truth-record ownership* token, not a work-mutex. Frontmatter::

    mode: parallel        # parallel (default) | exclusive
    turn: N               # monotonic
    from: <lane>          # who wrote this update
    updated: <iso>
    status: working | handing-off
    mac: <one-line task or "idle">       # each lane's current assignment
    windows: <one-line task or "idle">
    truth_owner: <lane>   # owns SESSION_STATE/IN_FLIGHT/CHANGELOG + merge-commits this period
    holder: <lane>        # back-compat alias of truth_owner (exclusive mode: sole shared-file worker)

- **parallel** (default): lanes work FILE-DISJOINT; each does its own ``<lane>:`` task;
  both push at milestones. ``truth_owner`` edits the shared truth-records + does merges.
- **exclusive**: the old mutex — ``holder`` is the sole worker on SHARED files; the
  other lane idles / does disjoint side-work. Use only when both would touch the SAME files.

Spec: ``docs/superpowers/specs/2026-06-08-lane-coordination-v2-design.md`` (supersedes
the 2026-06-03 single-baton spec). No git side effects (the slash commands run git).

CLI::

    status                      print mode/turn + both lanes' tasks + whether work is addressed to YOU
    handoff --to <lane> [--mode m] [--mac t] [--windows t] --done .. --next .. [--watch ..] [--force]
                                transfer truth-ownership to <lane> + set assignments; preserves history
    assign  [--mode m] [--mac t] [--windows t] [--note ..]
                                update the board IN PLACE (no ownership transfer; no refusal) — parallel coord
    incoming                    exit 0 + banner iff turn>last-seen AND work is addressed to this lane
    mark-seen                   record the current turn as seen (called by /resume)
    prune [--keep N]            trim old turn sections to dev/archive/LANE_HANDOFF_LOG.md (keeps STANDING + recent N)

Lane identity: ``dev/.lane`` (gitignored) -> ``windows``|``mac``; fallback ``$YHWH_LANE``;
fallback hostname heuristic (default ``windows``).
"""

from __future__ import annotations

import argparse
import datetime
import os
import socket
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LANES = ("windows", "mac")
MODES = ("parallel", "exclusive")
_IDLE = ("", "idle", "-", "none")


def baton_path(repo: Path = REPO) -> Path:
    return repo / "dev" / "LANE_HANDOFF.md"


def _archive_log(repo: Path = REPO) -> Path:
    return repo / "dev" / "archive" / "LANE_HANDOFF_LOG.md"


def _lane_file(repo: Path = REPO) -> Path:
    return repo / "dev" / ".lane"


def _seen_file(repo: Path = REPO) -> Path:
    return repo / "dev" / ".lane_seen"


def detect_lane(repo: Path = REPO) -> str:
    f = _lane_file(repo)
    if f.exists():
        v = f.read_text(encoding="utf-8").strip().lower()
        if v in LANES:
            return v
    env = os.environ.get("YHWH_LANE", "").strip().lower()
    if env in LANES:
        return env
    host = socket.gethostname().lower()
    if "mac" in host or "imac" in host or host.endswith(".local"):
        return "mac"
    return "windows"


def parse(text: str) -> tuple[dict, str]:
    """Split ``---\\n<frontmatter>\\n---\\n<body>`` -> (header dict, body str)."""
    if not text.startswith("---"):
        raise ValueError("LANE_HANDOFF.md missing YAML frontmatter")
    _, fm, body = text.split("---", 2)
    header: dict[str, str] = {}
    for line in fm.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            header[k.strip()] = v.strip()
    return header, body.lstrip("\n")


def render(header: dict, body: str) -> str:
    order = ["mode", "turn", "from", "updated", "status", "mac", "windows", "truth_owner", "holder"]
    keys = order + [k for k in header if k not in order]
    fm = "\n".join(f"{k}: {header[k]}" for k in keys if k in header)
    return f"---\n{fm}\n---\n\n{body.strip()}\n"


def load(repo: Path = REPO) -> tuple[dict, str]:
    return parse(baton_path(repo).read_text(encoding="utf-8"))


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _owner(header: dict) -> str | None:
    """Current truth-record owner (== merge-commit owner). truth_owner, falling back to holder."""
    return header.get("truth_owner") or header.get("holder")


def _mode(header: dict) -> str:
    m = (header.get("mode") or "").strip().lower()
    return m if m in MODES else "parallel"


def _task(header: dict, lane: str) -> str:
    return (header.get(lane) or "").strip()


def _is_idle(task: str) -> bool:
    return task.strip().lower() in _IDLE


def _addressed_to(header: dict, lane: str) -> bool:
    """Is there work addressed to THIS lane? (v2 fix: not gated on holder.)"""
    return (not _is_idle(_task(header, lane))) or (_owner(header) == lane)


def _bump_turn(header: dict) -> int:
    try:
        turn = int(header.get("turn", "0")) + 1
    except ValueError:
        turn = 1
    header["turn"] = str(turn)
    return turn


def _set_common(header: dict, lane: str, mode: str | None, mac: str | None, windows: str | None) -> None:
    if mode is not None:
        if mode not in MODES:
            raise ValueError(f"--mode must be one of {MODES}")
        header["mode"] = mode
    elif "mode" not in header:
        header["mode"] = "parallel"
    if mac is not None:
        header["mac"] = mac
    if windows is not None:
        header["windows"] = windows
    header["from"] = lane
    header["updated"] = _now()


def _prepend(body: str, block: str) -> str:
    return f"{block.strip()}\n\n---\n\n{body.strip()}\n"


def do_handoff(
    repo: Path,
    *,
    to: str,
    done: str = "",
    next: str = "",
    watch: str = "",
    mode: str | None = None,
    mac: str | None = None,
    windows: str | None = None,
    force: bool = False,
) -> int:
    header, body = load(repo)
    lane = detect_lane(repo)
    if _owner(header) != lane and not force:
        print(
            f"REFUSED: this lane is '{lane}' but truth-ownership is held by "
            f"'{_owner(header)}'. Use --force only if the other lane is idle.",
            file=sys.stderr,
        )
        return 1
    if to not in LANES:
        print(f"--to must be one of {LANES}", file=sys.stderr)
        return 2
    prev = int(header.get("turn", "0") or 0)
    try:
        _set_common(header, lane, mode, mac, windows)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2
    turn = _bump_turn(header)
    header["truth_owner"] = to
    header["holder"] = to  # back-compat alias
    header["status"] = "handing-off"
    block = (
        f"## ▶ {lane} → {to} (turn {turn}, {header['updated']}) — mode={header['mode']}\n\n"
        f"**Done (turn {prev}, {lane}):**\n{done or '- (none recorded)'}\n\n"
        f"**Next (turn {turn}, {to} picks up):**\n{next or '- (see truth-record)'}\n\n"
        f"**Assignments:** mac = {header.get('mac', '?')} · windows = {header.get('windows', '?')}\n\n"
        f"**Watch-outs:**\n{watch or '- (none)'}"
    )
    baton_path(repo).write_text(render(header, _prepend(body, block)), encoding="utf-8")
    print(f"handoff {lane} -> {to} (turn {turn}, mode={header['mode']}). Commit + milestone-push next.")
    return 0


def do_assign(
    repo: Path,
    *,
    mode: str | None = None,
    mac: str | None = None,
    windows: str | None = None,
    note: str = "",
) -> int:
    """Update the task board IN PLACE — no ownership transfer, no refusal (parallel coordination)."""
    header, body = load(repo)
    lane = detect_lane(repo)
    try:
        _set_common(header, lane, mode, mac, windows)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2
    turn = _bump_turn(header)
    header["status"] = "working"
    header.setdefault("truth_owner", header.get("holder", lane))
    header.setdefault("holder", header["truth_owner"])
    block = (
        f"## ◦ {lane} assign (turn {turn}, {header['updated']}) — mode={header['mode']}\n\n"
        f"**Assignments:** mac = {header.get('mac', '?')} · windows = {header.get('windows', '?')}"
    )
    if note:
        block += f"\n\n{note}"
    baton_path(repo).write_text(render(header, _prepend(body, block)), encoding="utf-8")
    print(f"assign by {lane} (turn {turn}, mode={header['mode']}). truth_owner stays {_owner(header)}.")
    return 0


def do_incoming(repo: Path = REPO) -> int:
    header, _ = load(repo)
    lane = detect_lane(repo)
    if not _addressed_to(header, lane):
        return 1
    try:
        turn = int(header.get("turn", "0"))
    except ValueError:
        turn = 0
    last = 0
    sf = _seen_file(repo)
    if sf.exists():
        try:
            last = int(sf.read_text(encoding="utf-8").strip() or "0")
        except ValueError:
            last = 0
    if turn <= last:
        return 1
    task = _task(header, lane)
    what = task if not _is_idle(task) else "owns the truth-records / merge"
    print(
        f"⮕ INCOMING HANDOFF (turn {turn}, from {header.get('from')}, mode={_mode(header)}): "
        f"YOU ({lane}) -> {what}. Run /resume to pull + pick up."
    )
    return 0


def do_mark_seen(repo: Path = REPO) -> int:
    header, _ = load(repo)
    _seen_file(repo).write_text(str(header.get("turn", "0")), encoding="utf-8")
    return 0


def do_status(repo: Path = REPO) -> int:
    header, _ = load(repo)
    lane = detect_lane(repo)
    mode = _mode(header)
    owner = _owner(header)
    print(
        f"lane={lane} mode={mode} turn={header.get('turn')} from={header.get('from')} "
        f"truth_owner={owner} updated={header.get('updated')} status={header.get('status')}"
    )
    print(f"  mac     = {_task(header, 'mac') or '(unset)'}")
    print(f"  windows = {_task(header, 'windows') or '(unset)'}")
    my = _task(header, lane)
    line = f"YOU ({lane}): {my if not _is_idle(my) else 'idle'}"
    if owner == lane:
        line += "  [+truth-records owner]"
    print(line)
    if mode == "exclusive" and owner != lane:
        print(f"  EXCLUSIVE mode — '{owner}' holds the shared-file mutex; do disjoint side-work or wait.")
    return 0


def _split_sections(body: str) -> tuple[str, list[str]]:
    """Preamble + list of '## ...' sections (each starting at a '## ' header line)."""
    lines = body.splitlines(keepends=True)
    idx = [i for i, ln in enumerate(lines) if ln.startswith("## ")]
    if not idx:
        return body, []
    preamble = "".join(lines[: idx[0]])
    bounds = idx + [len(lines)]
    sections = ["".join(lines[a:b]) for a, b in zip(idx, bounds[1:], strict=True)]
    return preamble, sections


def do_prune(repo: Path = REPO, *, keep: int = 5) -> int:
    """Keep the STANDING block + the most recent `keep` turn sections; archive the rest."""
    header, body = load(repo)
    preamble, sections = _split_sections(body)
    if not sections:
        print("prune: no '## ' sections; nothing to do.")
        return 0
    pinned = [s for s in sections if "STANDING" in s.splitlines()[0]]
    rest = [s for s in sections if "STANDING" not in s.splitlines()[0]]
    keep_rest, archived = rest[:keep], rest[keep:]
    if not archived:
        print(f"prune: {len(rest)} turn section(s) <= keep={keep}; nothing archived.")
        return 0
    log = _archive_log(repo)
    log.parent.mkdir(parents=True, exist_ok=True)
    prior = log.read_text(encoding="utf-8") if log.exists() else "# LANE_HANDOFF archived log\n\n"
    log.write_text(prior + "\n" + "\n".join(s.strip() + "\n" for s in archived), encoding="utf-8")
    new_body = preamble + "\n".join(pinned + keep_rest)
    baton_path(repo).write_text(render(header, new_body), encoding="utf-8")
    print(f"prune: archived {len(archived)} section(s) to {log}; kept STANDING + {len(keep_rest)} recent.")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Lane-coordination core (v2)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    h = sub.add_parser("handoff")
    h.add_argument("--to", required=True)
    h.add_argument("--done", default="")
    h.add_argument("--next", default="")
    h.add_argument("--watch", default="")
    h.add_argument("--mode", default=None)
    h.add_argument("--mac", default=None)
    h.add_argument("--windows", default=None)
    h.add_argument("--force", action="store_true")
    a = sub.add_parser("assign")
    a.add_argument("--mode", default=None)
    a.add_argument("--mac", default=None)
    a.add_argument("--windows", default=None)
    a.add_argument("--note", default="")
    sub.add_parser("incoming")
    sub.add_parser("mark-seen")
    pr = sub.add_parser("prune")
    pr.add_argument("--keep", type=int, default=5)
    args = p.parse_args(argv)
    if args.cmd == "status":
        return do_status()
    if args.cmd == "handoff":
        return do_handoff(
            REPO,
            to=args.to,
            done=args.done,
            next=args.next,
            watch=args.watch,
            mode=args.mode,
            mac=args.mac,
            windows=args.windows,
            force=args.force,
        )
    if args.cmd == "assign":
        return do_assign(REPO, mode=args.mode, mac=args.mac, windows=args.windows, note=args.note)
    if args.cmd == "incoming":
        return do_incoming()
    if args.cmd == "mark-seen":
        return do_mark_seen()
    if args.cmd == "prune":
        return do_prune(REPO, keep=args.keep)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
