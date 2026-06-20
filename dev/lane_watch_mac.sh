#!/usr/bin/env bash
# lane_watch_mac.sh — Mac-side cross-lane poll (pull when Windows pushes + handoff board).
#
# Uses scripts/lane_watch.py (unified engine; lane_watcher.py is a compat shim).
# Logs append to dev/.lane_watch.log (and stdout when foreground).
#
# Usage:
#   bash dev/lane_watch_mac.sh              # loop every 60s (foreground)
#   bash dev/lane_watch_mac.sh --bg         # detach → dev/.lane_watch.log
#   bash dev/lane_watch_mac.sh --once       # single check + auto-pull
#
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY="python3"

BG=0
ONCE=0
for arg in "$@"; do
  case "$arg" in
    --bg) BG=1 ;;
    --once) ONCE=1 ;;
  esac
done

# Always pass --auto-pull. This is required by the STANDING "Auto-pull on BEHIND"
# rule (never make the user say "pull" when the branch is behind + tree clean).
# See LANE_HANDOFF STANDING + CLAUDE_PROJECT_RULES.md guard #8 ("always just do
# the logical automation").
ARGS=("$PY" "$REPO/scripts/lane_watch.py" "--auto-pull")
if [ "$ONCE" = 1 ]; then
  ARGS+=("--once")
else
  ARGS+=("--loop" "60")
fi

if [ "$BG" = 1 ]; then
  nohup "${ARGS[@]}" >>"$REPO/dev/.lane_watch.log" 2>&1 &
  echo "lane_watch: background pid $! — log $REPO/dev/.lane_watch.log"
  exit 0
fi

exec "${ARGS[@]}"