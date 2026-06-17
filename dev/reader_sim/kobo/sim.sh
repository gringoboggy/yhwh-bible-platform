#!/usr/bin/env bash
# Kobo sim pack — agent sim (gates + kobo_tap_calibration bracket).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$REPO"
PY="$(command -v py >/dev/null 2>&1 && echo "py -3" || echo "python3")"
ARTIFACT="${1:?usage: sim.sh <path/to.kepub.epub>}"
exec $PY scripts/reader_sim.py --sim kobo --artifact "$ARTIFACT"