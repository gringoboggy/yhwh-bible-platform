#!/usr/bin/env bash
# Kobo sim pack — structural gates on an existing .kepub.epub.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$REPO"
PY="$(command -v py >/dev/null 2>&1 && echo "py -3" || echo "python3")"
ARTIFACT="${1:?usage: gate.sh <path/to.kepub.epub>}"
exec $PY scripts/reader_sim.py --gate kobo --artifact "$ARTIFACT"