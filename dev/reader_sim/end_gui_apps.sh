#!/usr/bin/env bash
# Quit reader-sim GUI apps (Thorium, Chrome, Kindle) — Mac RAM guard (8 GB box).
# Poll scripts (stk_poll_watch) need no GUI; leave them running.
set -euo pipefail

APPS=(Thorium "Google Chrome" Kindle)

for app in "${APPS[@]}"; do
  osascript -e "tell application \"${app}\" to quit" 2>/dev/null || true
done
sleep 2
killall Thorium 2>/dev/null || true
killall "Google Chrome" 2>/dev/null || true
killall Kindle 2>/dev/null || true

remaining=$(pgrep -fl "Thorium|Google Chrome|Kindle" 2>/dev/null || true)
if [[ -n "${remaining}" ]]; then
  echo "WARN: some GUI processes still running:" >&2
  echo "${remaining}" >&2
  exit 1
fi
echo "OK: Thorium, Chrome, Kindle quit"