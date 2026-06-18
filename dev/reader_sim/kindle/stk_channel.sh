#!/usr/bin/env bash
# Kindle STK-channel sim — Send-to-Kindle → Kindle-for-Mac arrival (Mac lane).
#
# Without Kindle-for-Mac: --gate-only (auto) runs structural gate and exits 0.
# With Kindle installed: snapshot library → user/agent sends → poll for arrival.
#
# Usage:
#   bash dev/reader_sim/kindle/stk_channel.sh <path/to.epub> [--gate-only]
#   bash dev/reader_sim/kindle/stk_channel.sh <epub> --wait 3600
set -euo pipefail

ARTIFACT="${1:?usage: stk_channel.sh <epub> [--gate-only] [--wait SECS]}"
shift || true

GATE_ONLY=0
WAIT_SECS=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --gate-only) GATE_ONLY=1 ;;
    --wait) WAIT_SECS="${2:-3600}"; shift ;;
    --send|--send=*) ;; # accepted for compat; STK send is manual/UI
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STAGE="${HOME}/Desktop/YHWH-reader-sim/kindle"
mkdir -p "$STAGE"
ARTIFACT_ABS="$(cd "$(dirname "$ARTIFACT")" && pwd)/$(basename "$ARTIFACT")"
STAGE_ABS="$(cd "$STAGE" && pwd)"
BASENAME="$(basename "$ARTIFACT_ABS")"
if [[ "$(dirname "$ARTIFACT_ABS")" != "$STAGE_ABS" ]]; then
  cp -f "$ARTIFACT_ABS" "$STAGE_ABS/"
fi

# Modern Kindle.app = com.amazon.Lassen; legacy = com.amazon.Kindle (see kindle_library.py).
KINDLE_ROOT=""
KINDLE_CID=""
for CID in com.amazon.Lassen com.amazon.Kindle; do
  if [[ -d "${HOME}/Library/Containers/${CID}/Data" ]]; then
    KINDLE_ROOT="${HOME}/Library/Containers/${CID}/Data"
    KINDLE_CID="$CID"
    break
  fi
done
LIBRARY_DIRS=()
if [[ -n "$KINDLE_ROOT" ]]; then
  while IFS= read -r -d '' d; do
    LIBRARY_DIRS+=("$d")
  done < <(find "$KINDLE_ROOT" -type d \( -name Library -o -name Documents \) -print0 2>/dev/null || true)
fi

if [[ ${#LIBRARY_DIRS[@]} -eq 0 ]]; then
  GATE_ONLY=1
fi

if [[ "$GATE_ONLY" -eq 1 ]]; then
  echo "STK channel sim: gate-only (Kindle-for-Mac library not found or --gate-only)"
  echo "  staged: $STAGE/$BASENAME"
  if [[ "$BASENAME" == *m4b* ]]; then
    M4B=1 bash "$SCRIPT_DIR/gate.sh" "$STAGE/$BASENAME"
  else
    bash "$SCRIPT_DIR/gate.sh" "$STAGE/$BASENAME"
  fi
  echo "PASS: structural gate (STK delivery poll skipped)"
  exit 0
fi

SNAP="$(mktemp)"
find "${LIBRARY_DIRS[@]}" -type f \( -name '*.azw' -o -name '*.kfx' -o -name '*.mbp' -o -name '*.epub' \) -print 2>/dev/null \
  | sort >"$SNAP" || true
BEFORE=$(wc -l <"$SNAP" | tr -d ' ')

echo "STK channel sim: Kindle library snapshot ($BEFORE files, container=$KINDLE_CID)"
echo "  staged EPUB: $STAGE/$BASENAME"
echo "  Send via Kindle for Mac, then this script polls for a new library file."
echo "  (Upload: agent runs Send-to-Kindle via Chrome/Playwright MCP — RULES guard #6; then re-run with --wait.)"

if [[ "$WAIT_SECS" -le 0 ]]; then
  echo "PASS: inventory snapshot OK (use --wait SECS to poll after send)"
  rm -f "$SNAP"
  exit 0
fi

DEADLINE=$(( $(date +%s) + WAIT_SECS ))
while [[ $(date +%s) -lt $DEADLINE ]]; do
  AFTER_LIST="$(mktemp)"
  find "${LIBRARY_DIRS[@]}" -type f \( -name '*.azw' -o -name '*.kfx' -o -name '*.mbp' -o -name '*.epub' \) -print 2>/dev/null \
    | sort >"$AFTER_LIST" || true
  NEW=$(comm -13 "$SNAP" "$AFTER_LIST" | head -1 || true)
  rm -f "$AFTER_LIST"
  if [[ -n "$NEW" ]]; then
    echo "PASS: new Kindle library file: $NEW"
    ARRIVAL_LOG="$REPO/build/reader-sim/kindle/stk-last-arrival.txt"
    mkdir -p "$(dirname "$ARRIVAL_LOG")"
    {
      echo "arrived_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
      echo "source_epub=$STAGE/$BASENAME"
      echo "library_file=$NEW"
    } >"$ARRIVAL_LOG"
    rm -f "$SNAP"
    if [[ "$BASENAME" == *m4b* ]]; then
      M4B=1 bash "$SCRIPT_DIR/gate.sh" "$STAGE/$BASENAME"
    else
      bash "$SCRIPT_DIR/gate.sh" "$STAGE/$BASENAME"
    fi
    exit 0
  fi
  sleep 30
done

rm -f "$SNAP"
echo "FAIL: STK poll timeout (${WAIT_SECS}s) — no new library file" >&2
exit 1