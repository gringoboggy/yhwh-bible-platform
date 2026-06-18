#!/usr/bin/env bash
# Upload to Send-to-Kindle using the ALREADY-OPEN signed-in Chrome (Mac lane).
# Does NOT quit or relaunch Chrome — use when the user has finished signing in.
#
# Usage: bash dev/reader_sim/kindle/stk_upload_open_chrome.sh <path/to.epub>
set -euo pipefail

EPUB="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
[[ -f "$EPUB" ]] || { echo "missing epub: $EPUB" >&2; exit 2; }

osascript <<APPLESCRIPT
tell application "Google Chrome" to activate
delay 0.8
tell application "Google Chrome"
  set js to "(() => { const i = document.querySelector('input[type=file]'); if (!i) return 'no-input'; i.click(); return 'clicked'; })()"
  set r to execute active tab of front window javascript js
end tell
if r is not "clicked" then error "Send-to-Kindle file input not found (on sendtokindle page?): " & r
delay 0.5
tell application "System Events"
  tell process "Google Chrome"
    set frontmost to true
    keystroke "g" using {command down, shift down}
    delay 0.6
    keystroke "$EPUB"
    delay 0.3
    keystroke return
    delay 0.8
    keystroke return
  end tell
end tell
APPLESCRIPT

echo "STK upload submitted via open Chrome: $EPUB"
echo "Next: end-task Chrome, then open Kindle to confirm (RAM cycle)."