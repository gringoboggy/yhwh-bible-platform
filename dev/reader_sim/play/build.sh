#!/usr/bin/env bash
# Play sim pack — stage everywhere artifact (post sim-pack unlock).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$REPO"
PY="$(command -v py >/dev/null 2>&1 && echo "py -3" || echo "python3")"
EDITION="${1:-ethiopian-tewahedo}"
VERSION="${2:-0.1.0}"
OUT="${3:-build/reader-sim/play}"
exec $PY scripts/reader_sim.py --build play --edition "$EDITION" --version "$VERSION" --output-dir "$OUT"