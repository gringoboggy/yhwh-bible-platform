#!/bin/bash
# Auto-finish macOS notarization the instant Apple returns a verdict.
#
# Polls the pending notarytool submission(s) for this dmg. On the first "Accepted":
#   staple the dmg -> regenerate dist/SHA256SUMS.txt (AFTER stapling, since
#   stapling changes the dmg bytes) -> verify -> flip dev/NOTARIZATION_STATUS.md
#   to DONE. On a hard Apple failure (every discovered submission terminal &
#   non-Accepted): capture the log -> flip status to FAILED.
#
# Submissions are AUTO-DISCOVERED from `xcrun notarytool history` (matched by the
# dmg's file name) -> no hardcoded submission IDs, so ANY resubmit is picked up
# automatically with no edit to this script. Because the dmg bytes never change
# between resubmits, an Accepted ticket from any matching submission staples this
# exact artifact.
#
# Idempotent + safe under launchd or a bootup hook. Two modes:
#   notary_autofinish.sh        # loop, poll every 180s until terminal (session lane)
#   notary_autofinish.sh 0      # single check; finish if ready else exit 2 quietly
#                               # (use from launchd StartInterval / a bootup hook)
set -u
REPO="/Volumes/MacHD2/yhwh-bible-platform"
DMG="$REPO/dist/YHWH-1.0.0-beta.1.dmg"
DMG_NAME="$(basename "$DMG")"
PROFILE="yhwh-notary"
STATUS="$REPO/dev/NOTARIZATION_STATUS.md"
LOG="$REPO/dev/notary_autofinish.log"
INTERVAL="${1:-180}"

cd "$REPO" || exit 3
now() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
status_of() { xcrun notarytool info "$1" --keychain-profile "$PROFILE" 2>/dev/null \
                | awk -F': ' '/^[[:space:]]*status:/{print $2; exit}'; }

# Every submission ID in Apple's history whose artifact name matches our dmg
# (history lists newest first). Empty output = none found OR a transient query
# failure -> the caller treats that as "still pending", never as FAILED.
discover_ids() {
  xcrun notarytool history --keychain-profile "$PROFILE" 2>/dev/null | awk -v want="$DMG_NAME" '
    /^[[:space:]]*id:/   { cid=$2 }
    /^[[:space:]]*name:/ { if ($2==want && cid!="") { print cid; cid="" } }
  '
}

# Already finished? never re-do work.
if grep -q "STATE: DONE" "$STATUS" 2>/dev/null; then exit 0; fi

while true; do
  ids=(); while IFS= read -r line; do [ -n "$line" ] && ids+=("$line"); done < <(discover_ids)

  if [ "${#ids[@]}" -eq 0 ]; then
    echo "$(now) no submissions discovered for $DMG_NAME (transient or none) -> pending" >> "$LOG"
    if [ "$INTERVAL" = "0" ]; then exit 2; fi
    sleep "$INTERVAL"; continue
  fi

  accepted=""; all_terminal_bad=1
  for id in "${ids[@]}"; do
    s="$(status_of "$id")"
    echo "$(now) $id -> ${s:-<none>}" >> "$LOG"
    if [ "$s" = "Accepted" ]; then accepted="$id"; break; fi
    # anything not-yet-terminal keeps us from declaring FAILED
    if [ "$s" = "In Progress" ] || [ -z "$s" ]; then all_terminal_bad=0; fi
  done

  if [ -n "$accepted" ]; then
    xcrun stapler staple "$DMG" >> "$LOG" 2>&1; rc=$?
    "$REPO/.venv/bin/python" "$REPO/scripts/gen_checksums.py" dist --out dist/SHA256SUMS.txt >> "$LOG" 2>&1
    xcrun stapler validate "$DMG" >> "$LOG" 2>&1
    spctl -a -vv -t open --context context:primary-signature "$DMG" >> "$LOG" 2>&1
    {
      echo "# Notarization status — single source of truth"
      echo
      echo "**STATE: DONE** — auto-stapled $(now)"
      echo
      echo "- Accepted submission: \`$accepted\`"
      echo "- Stapler rc: $rc  (0 = ok)"
      echo "- Checksums regenerated AFTER stapling -> dist/SHA256SUMS.txt"
      echo "- Artifact: $DMG"
      echo
      echo "Full trace: dev/notary_autofinish.log"
    } > "$STATUS"
    exit 0
  fi

  if [ "$all_terminal_bad" -eq 1 ]; then
    xcrun notarytool log "${ids[0]}" --keychain-profile "$PROFILE" "$REPO/dev/notary_log.json" >> "$LOG" 2>&1
    {
      echo "# Notarization status — single source of truth"
      echo
      echo "**STATE: FAILED** — every discovered submission returned a non-Accepted verdict ($(now))"
      echo
      echo "- See dev/notary_log.json + dev/notary_autofinish.log"
      echo "- Re-build + re-submit: dev/build_dmg.sh with CODESIGN_IDENTITY + NOTARIZE_KEYCHAIN_PROFILE set."
    } > "$STATUS"
    exit 1
  fi

  if [ "$INTERVAL" = "0" ]; then exit 2; fi   # single-check mode: still pending, leave status untouched
  sleep "$INTERVAL"
done
