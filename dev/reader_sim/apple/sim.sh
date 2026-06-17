#!/usr/bin/env bash
# Apple sim pack — agent sim via Thorium popup/ToC protocol (tablet proxy).
#
# Mac turn 124+ prep: wire Chrome DevTools MCP or Thorium CLI to assert:
#   - Gen 1:1 vn-link popup readable
#   - verse-end study badge → verse-notes popup
#   - collapsible ToC <details> expand + navigate
#   - Hebrew/Greek sample renders in body + popup
#
# Until wired, falls back to reader_sim.py --sim (marks thorium_popup_sim pending).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$REPO"
PY="$(command -v py >/dev/null 2>&1 && echo "py -3" || echo "python3")"
ARTIFACT="${1:?usage: sim.sh <path/to.epub>}"
exec $PY scripts/reader_sim.py --sim apple --artifact "$ARTIFACT"