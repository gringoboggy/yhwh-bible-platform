#!/usr/bin/env bash
# start_session_radars_mac.sh — idempotent dual-radar boot (Mac lane).
# Called by bootstrap-triad.sh SessionStart hook every session.
#
# Radars (both REQUIRED, both stay on until session ends):
#   1. lane_watch  — cross-lane push/handoff poll (60s)
#   2. agent_idle_radar — anti-idle work surfacing (120s)
#
# Usage:
#   bash dev/start_session_radars_mac.sh
#   bash dev/start_session_radars_mac.sh --quiet

set +e
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"
QUIET=0
[ "${1:-}" = "--quiet" ] && QUIET=1

say() { [ "$QUIET" = 0 ] && echo "$@"; }

running() { pgrep -f "$1" >/dev/null 2>&1; }

say "----- SESSION RADARS (bootstrap) -----"

# lane_watch is **always** started with --auto-pull to enforce the STANDING
# "Auto-pull on BEHIND" rule (LANE_HANDOFF + RULES guard #8):
#   clean tree + (git status behind origin/main or tracking ref lag) ⇒ immediate pull.
# The user never has to say the word "pull". This is a literal "always just do the
# logical thing" directive.
if running "scripts/lane_watch.py"; then
  say "  lane_watch: already running (with --auto-pull)"
else
  bash "$REPO/dev/lane_watch_mac.sh" --bg
  say "  lane_watch: started (60s loop, --auto-pull enforcing standing rule)"
fi

if running "scripts/agent_idle_radar.py"; then
  say "  agent_idle_radar: already running"
else
  bash "$REPO/dev/agent_idle_radar_mac.sh" --bg 120
  say "  agent_idle_radar: started (120s loop)"
fi

say "  STANDING: never wait for user input — py -3 scripts/agent_idle_radar.py --next"
say "--------------------------------------"