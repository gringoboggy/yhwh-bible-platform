#!/usr/bin/env bash
# lane_watch_mac.sh — Mac-side cross-lane poll (pull when Windows pushes).
#
# Wraps scripts/lane_watcher.py (shared with WIN). On Mac, run WITHOUT
# --assign-mac (that flag is WIN-only: queues the next Mac task from
# dev/MAC_WORK_QUEUE.md after a Mac push lands on WIN).
#
# Usage:
#   bash dev/lane_watch_mac.sh              # loop every 90s (foreground)
#   bash dev/lane_watch_mac.sh --bg         # detach → dev/.lane_watcher.log
#   bash dev/lane_watch_mac.sh --once       # single check + pull if BEHIND
#
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY="python3"

BG=0
EXTRA=()
for arg in "$@"; do
  case "$arg" in
    --bg) BG=1 ;;
    *) EXTRA+=("$arg") ;;
  esac
done

if [ "$BG" = 1 ]; then
  nohup "$PY" "$REPO/scripts/lane_watcher.py" --loop 90 >>"$REPO/dev/.lane_watcher.log" 2>&1 &
  echo "lane_watcher: background pid $! — log $REPO/dev/.lane_watcher.log"
  exit 0
fi

if printf '%s\n' "${EXTRA[@]}" | grep -qx -- '--once'; then
  exec "$PY" "$REPO/scripts/lane_watcher.py" --once
fi

exec "$PY" "$REPO/scripts/lane_watcher.py" --loop 90 "${EXTRA[@]}"