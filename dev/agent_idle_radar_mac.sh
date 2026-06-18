#!/usr/bin/env bash
# agent_idle_radar_mac.sh — Mac anti-idle companion to lane_watch.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"
PY="${PYTHON:-python3}"

run_next() { "$PY" scripts/agent_idle_radar.py --next "$@"; }
run_ping() { "$PY" scripts/agent_idle_radar.py --ping "$@"; }

case "${1:-}" in
  --ping)
    shift
    run_ping "$@"
    ;;
  --bg)
    LOOP="${2:-120}"
    nohup "$PY" scripts/agent_idle_radar.py --loop "$LOOP" >>dev/.agent_idle_radar.log 2>&1 &
    echo "agent_idle_radar: background loop ${LOOP}s — log dev/.agent_idle_radar.log"
    ;;
  --once|--next|"")
    run_next
    ;;
  *)
    echo "usage: $0 [--next|--ping [--note TEXT]|--bg [SEC]]" >&2
    exit 1
    ;;
esac