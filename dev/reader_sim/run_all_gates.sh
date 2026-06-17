#!/usr/bin/env bash
# Gate-only sweep — no rebuild. Safe during audit / while ci.py runs.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO"
PY="$(command -v py >/dev/null 2>&1 && echo "py -3" || echo "python3")"
DIR="${1:-dev/.audit-build}"
exec $PY scripts/reader_sim.py --gate all --artifact-dir "$DIR"