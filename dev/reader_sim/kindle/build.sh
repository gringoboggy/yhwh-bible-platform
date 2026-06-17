#!/usr/bin/env bash
# Kindle sim pack — kindle_post artifact (Mac lane). Use --m4b for M4b fork.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$REPO"
PY="$(command -v py >/dev/null 2>&1 && echo "py -3" || echo "python3")"
EDITION="${1:-ethiopian-tewahedo}"
VERSION="${2:-0.1.0}"
OUT="${3:-build/reader-sim/kindle}"
M4B="${M4B:-}"
EXTRA=()
[[ -n "$M4B" ]] && EXTRA+=(--m4b)
exec $PY scripts/reader_sim.py --build kindle --edition "$EDITION" --version "$VERSION" --output-dir "$OUT" "${EXTRA[@]}"