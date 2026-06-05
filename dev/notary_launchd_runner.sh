#!/bin/bash
# launchd wrapper for the notarization auto-finisher.
#
# Fired every 30 min (+ at load/login) by
#   ~/Library/LaunchAgents/com.yhwhyaway.notary-autofinish.plist
# Runs ONE check. When the check reaches a terminal state — DONE (rc 0) or
# FAILED (rc 1) — it stops the agent firing, deletes its own plist, AND kills any
# in-session `notary_autofinish.sh 180` bash poller loop, so the whole mechanism
# removes itself the moment the work is finished. rc 2 = still pending
# (Apple hasn't answered) -> leave the agent armed for the next interval.
REPO="/Volumes/MacHD2/yhwh-bible-platform"
LABEL="com.yhwhyaway.notary-autofinish"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

bash "$REPO/dev/notary_autofinish.sh" 0
rc=$?

if [ "$rc" -eq 0 ] || [ "$rc" -eq 1 ]; then
  # Apple returned a terminal verdict -> erase the whole mechanism: this agent
  # AND any in-session `notary_autofinish.sh 180` bash poller loop.
  pkill -f "notary_autofinish.sh 180" 2>/dev/null
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || launchctl unload "$PLIST" 2>/dev/null
  rm -f "$PLIST"
fi
exit 0
