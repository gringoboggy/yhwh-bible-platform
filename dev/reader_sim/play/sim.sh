#!/usr/bin/env bash
# Play sim pack — agent sim (gates + Thorium/emulator layer when wired).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$REPO"
PY="$(command -v py >/dev/null 2>&1 && echo "py -3" || echo "python3")"
ARTIFACT="${1:?usage: sim.sh <path/to.epub>}"
exec $PY scripts/reader_sim.py --sim play --artifact "$ARTIFACT"