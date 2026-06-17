#!/usr/bin/env bash
# lane_watch_mac.sh — background-friendly cross-lane poll (Mac).
#
# Watches for Windows pushes + incoming LANE_HANDOFF instructions while this
# box is idle between tasks. Wraps scripts/lane_watch.py.
#
# Usage:
#   bash dev/lane_watch_mac.sh              # loop every 120s (foreground)
#   bash dev/lane_watch_mac.sh --bg         # detach to dev/.lane_watch.log
#   bash dev/lane_watch_mac.sh --once       # single check
#   bash dev/lane_watch_mac.sh --auto-pull  # pull --rebase when BEHIND
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
  LOG="$REPO/dev/.lane_watch.log"
  nohup "$PY" "$REPO/scripts/lane_watch.py" --interval 90 "${EXTRA[@]}" >>"$LOG" 2>&1 &
  echo "lane_watch: background pid $! — log $LOG"
  exit 0
fi

exec "$PY" "$REPO/scripts/lane_watch.py" "${EXTRA[@]}"