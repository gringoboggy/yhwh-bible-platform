#!/usr/bin/env bash
# Kindle STK-channel sim — Send-to-Kindle → Kindle-for-Mac arrival (Mac lane).
#
# Mac turn 124+ prep: implement poll + ingest-OK check. Previewer is NOT this script.
#
# Usage:
#   bash dev/reader_sim/kindle/stk_channel.sh <path/to.epub> [--send mac-app|email|web]
#
# Spike checklist (Mac agent):
#   1. Stage EPUB to ~/Desktop/YHWH-reader-sim/kindle/
#   2. Record pre-send library mtime inventory under:
#        ~/Library/Containers/com.amazon.Kindle/Data/
#      (exact subpath varies — find newest .azw/.kfx after send)
#   3. Send via Kindle for Mac "Send to Kindle" or drag-to-app / @kindle.com email
#   4. Poll until new book id appears (timeout 3600s — STK can be slow)
#   5. Exit 0 on arrival; re-run gate.sh on source EPUB as structural floor
#
# TODO(Mac): replace this stub with working poll loop; flip SIM_LAYERS_READY["kindle"].
set -euo pipefail

ARTIFACT="${1:?usage: stk_channel.sh <epub> [--send mac-app|email|web]}"
SEND_MODE="${2:---send}"
SEND_MODE="${SEND_MODE#--send=}"
SEND_MODE="${SEND_MODE#--send }"
if [[ "$SEND_MODE" == "--send" ]]; then
  SEND_MODE="mac-app"
fi

REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
STAGE="${HOME}/Desktop/YHWH-reader-sim/kindle"
mkdir -p "$STAGE"
cp -f "$ARTIFACT" "$STAGE/"
BASENAME="$(basename "$ARTIFACT")"

echo "STK channel sim (STUB) — staged: $STAGE/$BASENAME"
echo "Send mode target: $SEND_MODE"
echo ""
echo "Mac agent: implement library poll here, then:"
echo "  bash dev/reader_sim/kindle/gate.sh \"$STAGE/$BASENAME\""
echo ""
echo "FAIL: stk_channel automation not wired yet (exit 2)"
exit 2