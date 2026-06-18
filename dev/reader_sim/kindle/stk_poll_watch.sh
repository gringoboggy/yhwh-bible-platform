#!/usr/bin/env bash
# Background STK arrival watcher — poll com.amazon.Lassen library for new files.
#
# Run alongside other work after staging an EPUB and opening Send-to-Kindle in Chrome.
# Exits 0 when a new library file appears; 1 on timeout.
#
# Usage:
#   bash dev/reader_sim/kindle/stk_poll_watch.sh [--interval SECS] [--timeout SECS] [--epub PATH]
set -euo pipefail

INTERVAL=300
TIMEOUT=7200
EPUB=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --interval) INTERVAL="${2:-300}"; shift 2 ;;
    --timeout) TIMEOUT="${2:-7200}"; shift 2 ;;
    --epub) EPUB="${2:-}"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
LOG="$REPO/build/reader-sim/kindle/stk-poll-watch.log"
ARRIVAL_LOG="$REPO/build/reader-sim/kindle/stk-last-arrival.txt"
PY="${REPO}/.venv/bin/python"

mkdir -p "$(dirname "$LOG")"

log() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"
}

snapshot_files() {
  "$PY" - <<'PY'
from pathlib import Path
from dev.reader_sim.kindle_library import iter_library_files, kindle_container_id, kindle_data_root

root = kindle_data_root()
if root is None:
    raise SystemExit(1)
for p in iter_library_files(root):
    print(p)
PY
}

if ! snapshot_files >/dev/null 2>&1; then
  log "FAIL: no Kindle library container (com.amazon.Lassen)"
  exit 1
fi

SNAP="$(mktemp)"
snapshot_files | sort >"$SNAP" || true
BEFORE=$(wc -l <"$SNAP" | tr -d ' ')
CID=$("$PY" -c "from dev.reader_sim.kindle_library import kindle_container_id; print(kindle_container_id() or '')")

log "STK poll watch start container=$CID before=$BEFORE interval=${INTERVAL}s timeout=${TIMEOUT}s"
[[ -n "$EPUB" ]] && log "staged_epub=$EPUB"

DEADLINE=$(( $(date +%s) + TIMEOUT ))
while [[ $(date +%s) -lt $DEADLINE ]]; do
  AFTER="$(mktemp)"
  snapshot_files | sort >"$AFTER" || true
  NEW=$(comm -13 "$SNAP" "$AFTER" | head -1 || true)
  NOW=$(wc -l <"$AFTER" | tr -d ' ')
  if [[ -n "$NEW" ]]; then
    log "PASS: new library file: $NEW (inventory $BEFORE -> $NOW)"
    {
      echo "arrived_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
      echo "container=$CID"
      echo "library_file=$NEW"
      [[ -n "$EPUB" ]] && echo "source_epub=$EPUB"
    } >"$ARRIVAL_LOG"
    rm -f "$SNAP" "$AFTER"
    exit 0
  fi
  log "poll: still $NOW files — check Kindle app / Send-to-Kindle; next in ${INTERVAL}s"
  rm -f "$AFTER"
  sleep "$INTERVAL"
done

rm -f "$SNAP"
log "FAIL: timeout ${TIMEOUT}s — no new library file"
exit 1