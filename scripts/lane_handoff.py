#!/usr/bin/env python3
"""Lane-handoff baton — deterministic core for the Windows<->Mac two-lane git flow.

The committed baton file ``dev/LANE_HANDOFF.md`` names the holder (= active
worker + sole pusher this turn). This module reads/writes/validates it with NO
git side effects (the slash commands run git). Spec:
``docs/superpowers/specs/2026-06-03-lane-handoff-baton-system-design.md``.

CLI::

    status        print holder/turn + whether THIS lane holds the baton
    handoff --to <windows|mac> --done .. --next .. [--watch ..] [--force]
    incoming      exit 0 + banner iff baton is addressed to this lane & turn>last-seen
    mark-seen     record the current turn as seen (called by /resume)

Lane identity: ``dev/.lane`` (gitignored) -> ``windows``|``mac``; fallback
``$YHWH_LANE``; fallback hostname heuristic (default ``windows``).
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


def baton_path(repo: Path = REPO) -> Path:
    return repo / "dev" / "LANE_HANDOFF.md"


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
    order = ["holder", "from", "turn", "updated", "status"]
    keys = order + [k for k in header if k not in order]
    fm = "\n".join(f"{k}: {header[k]}" for k in keys if k in header)
    return f"---\n{fm}\n---\n\n{body.strip()}\n"


def load(repo: Path = REPO) -> tuple[dict, str]:
    return parse(baton_path(repo).read_text(encoding="utf-8"))


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def do_handoff(
    repo: Path,
    *,
    to: str,
    done: str = "",
    next: str = "",
    watch: str = "",
    force: bool = False,
) -> int:
    header, _ = load(repo)
    lane = detect_lane(repo)
    if header.get("holder") != lane and not force:
        print(
            f"REFUSED: this lane is '{lane}' but the baton is held by "
            f"'{header.get('holder')}'. Use --force only if the other lane is idle.",
            file=sys.stderr,
        )
        return 1
    if to not in LANES:
        print(f"--to must be one of {LANES}", file=sys.stderr)
        return 2
    try:
        turn = int(header.get("turn", "0")) + 1
    except ValueError:
        turn = 1
    header.update(
        {
            "holder": to,
            "from": lane,
            "turn": str(turn),
            "updated": _now(),
            "status": "handing-off",
        }
    )
    body = (
        f"## Done (turn {turn - 1}, {lane} -> {to})\n{done or '- (none recorded)'}\n\n"
        f"## Next (turn {turn}, {to} picks up)\n{next or '- (see truth-record)'}\n\n"
        f"## Watch-outs\n{watch or '- (none)'}\n"
    )
    baton_path(repo).write_text(render(header, body), encoding="utf-8")
    print(f"baton {lane} -> {to} (turn {turn}). Commit + push both remotes next.")
    return 0


def do_incoming(repo: Path = REPO) -> int:
    header, _ = load(repo)
    lane = detect_lane(repo)
    if header.get("holder") != lane:
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
    print(f"⮕ INCOMING HANDOFF from {header.get('from')} (turn {turn}) -- run /resume to pull + combine.")
    return 0


def do_mark_seen(repo: Path = REPO) -> int:
    header, _ = load(repo)
    _seen_file(repo).write_text(str(header.get("turn", "0")), encoding="utf-8")
    return 0


def do_status(repo: Path = REPO) -> int:
    header, _ = load(repo)
    lane = detect_lane(repo)
    print(
        f"lane={lane} holder={header.get('holder')} turn={header.get('turn')} "
        f"from={header.get('from')} updated={header.get('updated')} "
        f"status={header.get('status')}"
    )
    print("YOU HOLD THE BATON" if header.get("holder") == lane else f"baton is with {header.get('holder')}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Lane-handoff baton core")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    h = sub.add_parser("handoff")
    h.add_argument("--to", required=True)
    h.add_argument("--done", default="")
    h.add_argument("--next", default="")
    h.add_argument("--watch", default="")
    h.add_argument("--force", action="store_true")
    sub.add_parser("incoming")
    sub.add_parser("mark-seen")
    args = p.parse_args(argv)
    if args.cmd == "status":
        return do_status()
    if args.cmd == "handoff":
        return do_handoff(REPO, to=args.to, done=args.done, next=args.next, watch=args.watch, force=args.force)
    if args.cmd == "incoming":
        return do_incoming()
    if args.cmd == "mark-seen":
        return do_mark_seen()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
