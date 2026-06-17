#!/usr/bin/env python3
"""lane_watcher.py — compatibility shim for ``scripts/lane_watch.py``.

Older sessions and ``dev/lane_watch_mac.sh`` referenced this name. All logic
lives in ``lane_watch.py`` (push radar + remote board + incoming + optional
``--assign-mac``). This module forwards argv and always enables ``--auto-pull``.
"""

from __future__ import annotations

import sys

from scripts import lane_watch as _lw


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if "--auto-pull" not in args:
        args.append("--auto-pull")
    return _lw.main(args)


if __name__ == "__main__":
    raise SystemExit(main())
