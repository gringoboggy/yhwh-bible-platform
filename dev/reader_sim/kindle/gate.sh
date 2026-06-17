#!/usr/bin/env bash
# Kindle sim pack — structural gates (verify_kindle_safe + optional m4b). No Previewer.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$REPO"
PY="$(command -v py >/dev/null 2>&1 && echo "py -3" || echo "python3")"
ARTIFACT="${1:?usage: gate.sh <path/to.epub>}"
M4B="${M4B:-}"
EXTRA=()
[[ -n "$M4B" ]] && EXTRA+=(--m4b)
exec $PY scripts/reader_sim.py --gate kindle --artifact "$ARTIFACT" "${EXTRA[@]}"