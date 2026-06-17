#!/usr/bin/env bash
# Play/Apple Thorium render spike — structural probes + optional CDP when Thorium present.
#
# Usage: bash dev/reader_sim/play/thorium_spike.sh <path/to.epub> [apple|play]
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$REPO"
PY="$(command -v py >/dev/null 2>&1 && echo "py -3" || echo "python3")"
ARTIFACT="${1:?usage: thorium_spike.sh <epub> [apple|play]}"
PROFILE="${2:-play}"
exec $PY dev/reader_sim/thorium_cdp.py "$ARTIFACT" --profile "$PROFILE" --gate-only