#!/bin/bash
# Bootup backstop for the notarization auto-finisher launchd agent.
#
# Wired as a Mac-local SessionStart hook (.claude/settings.local.json). Each
# Claude session on the Mac: make sure the com.yhwhyaway.notary-autofinish agent
# is still loaded (launchd's RunAtLoad only fires at login + the 30-min interval
# only fires while awake -> sleep/unplug leaves coverage gaps), then kick ONE
# immediate check so a verdict that landed while we were away is acted on now.
#
# Safe to run anywhere: it exits 0 and does nothing when it cannot apply
# (no launchctl, no plist, or the work is already DONE) -> harmless on Windows
# or after the mechanism has self-erased.
set -u
LABEL="com.yhwhyaway.notary-autofinish"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
STATUS="/Volumes/MacHD2/yhwh-bible-platform/dev/NOTARIZATION_STATUS.md"

# Not a Mac with launchd, or notarization already finished + self-erased -> no-op.
command -v launchctl >/dev/null 2>&1 || exit 0
grep -q "STATE: DONE" "$STATUS" 2>/dev/null && exit 0
[ -f "$PLIST" ] || exit 0

dom="gui/$(id -u)"

# Load the agent if it is not currently registered.
if ! launchctl print "$dom/$LABEL" >/dev/null 2>&1; then
  launchctl bootstrap "$dom" "$PLIST" 2>/dev/null || launchctl load "$PLIST" 2>/dev/null
fi

# Force one immediate check (don't wait up to 30 min for the next interval).
launchctl kickstart -k "$dom/$LABEL" 2>/dev/null

exit 0
